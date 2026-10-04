import { createContext, useContext, useState, useCallback } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

// [2026-10-04] girisYap / kayitOl artık sunucu cevabını döndürür:
//   { iki_adim_gerekli: true, gecici_token, maskeli_eposta }  → kod adımı gösterilir
//   { erisim_tokeni, kullanici_tipi }                         → giriş tamam ('rehber' ise rehber paneline)
export function AuthProvider({ children }) {
  const [girisYapildi, setGirisYapildi] = useState(api.girisYapildiMi())

  const sonucuIsle = useCallback((sonuc) => {
    if (sonuc?.erisim_tokeni && sonuc.kullanici_tipi !== 'rehber') setGirisYapildi(true)
    return sonuc
  }, [])

  const girisYap = useCallback(async (email, sifre) => sonucuIsle(await api.girisYap({ email, sifre })), [sonucuIsle])

  const ikiAdimDogrula = useCallback(
    async (geciciToken, kod, hatirla) => sonucuIsle(await api.ikiAdimDogrula(geciciToken, kod, hatirla)),
    [sonucuIsle],
  )

  const kayitOl = useCallback(async (adSoyad, email, sifre, kvkk) => {
    await api.kayitOl({ ad_soyad: adSoyad, email, sifre, kvkk })
    return sonucuIsle(await api.girisYap({ email, sifre }))
  }, [sonucuIsle])

  const cikisYap = useCallback(() => {
    api.cikisYap()
    setGirisYapildi(false)
  }, [])

  return (
    <AuthContext.Provider value={{ girisYapildi, girisYap, ikiAdimDogrula, kayitOl, cikisYap }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth, AuthProvider içinde kullanılmalı')
  return ctx
}
