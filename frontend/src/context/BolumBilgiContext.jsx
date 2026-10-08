// [2026-10-08] Bölüm bilgi kartı: uygulamanın her yerinden useBolumBilgi().ac(bolumId) ile açılır.
import { createContext, useCallback, useContext, useState } from 'react'
import BolumBilgiPenceresi from '../components/BolumBilgiPenceresi'

const BolumBilgiContext = createContext({ ac: () => {} })

export function BolumBilgiProvider({ children }) {
  const [secim, setSecim] = useState(null) // { id, ad, sekme }
  const ac = useCallback((id, ad = null, sekme = 'genel') => setSecim({ id, ad, sekme }), [])
  const kapat = useCallback(() => setSecim(null), [])
  return (
    <BolumBilgiContext.Provider value={{ ac }}>
      {children}
      {secim && <BolumBilgiPenceresi secim={secim} onKapat={kapat} />}
    </BolumBilgiContext.Provider>
  )
}

export function useBolumBilgi() {
  return useContext(BolumBilgiContext)
}
