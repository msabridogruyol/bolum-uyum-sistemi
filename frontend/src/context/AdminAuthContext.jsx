import { createContext, useContext, useState, useCallback } from 'react'
import { api } from '../api/client'

const AdminAuthContext = createContext(null)

export function AdminAuthProvider({ children }) {
  const [girisYapildi, setGirisYapildi] = useState(api.adminGirisYapildiMi())
  const [rol, setRol] = useState(api.adminRolGetir())
  const [kendiId, setKendiId] = useState(api.adminIdGetir())

  const girisYap = useCallback(async (email, sifre) => {
    const sonuc = await api.adminGirisYap({ email, sifre })
    setGirisYapildi(true)
    setRol(api.adminRolGetir())
    setKendiId(api.adminIdGetir())
    return sonuc
  }, [])

  const cikisYap = useCallback(() => {
    api.adminCikisYap()
    setGirisYapildi(false)
    setRol(null)
    setKendiId(null)
  }, [])

  return (
    <AdminAuthContext.Provider value={{ girisYapildi, rol, kendiId, girisYap, cikisYap }}>
      {children}
    </AdminAuthContext.Provider>
  )
}

export function useAdminAuth() {
  const ctx = useContext(AdminAuthContext)
  if (!ctx) throw new Error('useAdminAuth, AdminAuthProvider içinde kullanılmalı')
  return ctx
}
