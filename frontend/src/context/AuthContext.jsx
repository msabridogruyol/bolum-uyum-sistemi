import { createContext, useContext, useState, useCallback } from 'react'
import { api } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [girisYapildi, setGirisYapildi] = useState(api.girisYapildiMi())

  const girisYap = useCallback(async (email, sifre) => {
    await api.girisYap({ email, sifre })
    setGirisYapildi(true)
  }, [])

  const kayitOl = useCallback(async (adSoyad, email, sifre) => {
    await api.kayitOl({ ad_soyad: adSoyad, email, sifre })
    await api.girisYap({ email, sifre })
    setGirisYapildi(true)
  }, [])

  const cikisYap = useCallback(() => {
    api.cikisYap()
    setGirisYapildi(false)
  }, [])

  return (
    <AuthContext.Provider value={{ girisYapildi, girisYap, kayitOl, cikisYap }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth, AuthProvider içinde kullanılmalı')
  return ctx
}
