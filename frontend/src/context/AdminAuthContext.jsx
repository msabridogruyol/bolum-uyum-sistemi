import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { api } from '../api/client'

const AdminAuthContext = createContext(null)

export function AdminAuthProvider({ children }) {
  const [girisYapildi, setGirisYapildi] = useState(api.adminGirisYapildiMi())
  const [rol, setRol] = useState(api.adminRolGetir())
  const [kendiId, setKendiId] = useState(api.adminIdGetir())
  // [2026-10-09] Oturumdaki yönetim hesabı: rol (Süper Admin / Okul Yetkilisi), okulu, geçici şifre durumu
  const [ben, setBen] = useState(null)
  const benYenile = useCallback(() => api.yonetimBen().then(setBen).catch(() => setBen(null)), [])
  useEffect(() => { if (girisYapildi) benYenile(); else setBen(null) }, [girisYapildi, kendiId, benYenile])

  // [2026-10-04] 2 adımlı doğrulama gerekiyorsa sonuc.iki_adim_gerekli=true döner, giriş henüz tamamlanmaz
  const sonucuIsle = useCallback((sonuc) => {
    if (sonuc?.erisim_tokeni) {
      setGirisYapildi(true)
      setRol(api.adminRolGetir())
      setKendiId(api.adminIdGetir())
    }
    return sonuc
  }, [])

  const girisYap = useCallback(async (email, sifre) => sonucuIsle(await api.adminGirisYap({ email, sifre })), [sonucuIsle])

  const ikiAdimDogrula = useCallback(
    async (geciciToken, kod, hatirla) => sonucuIsle(await api.adminIkiAdimDogrula(geciciToken, kod, hatirla)),
    [sonucuIsle],
  )

  const cikisYap = useCallback(() => {
    api.adminCikisYap()
    setGirisYapildi(false)
    setRol(null)
    setKendiId(null)
    setBen(null)
  }, [])

  return (
    <AdminAuthContext.Provider value={{ girisYapildi, rol, kendiId, ben, benYenile, girisYap, ikiAdimDogrula, cikisYap }}>
      {children}
    </AdminAuthContext.Provider>
  )
}

export function useAdminAuth() {
  const ctx = useContext(AdminAuthContext)
  if (!ctx) throw new Error('useAdminAuth, AdminAuthProvider içinde kullanılmalı')
  return ctx
}
