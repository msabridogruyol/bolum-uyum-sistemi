// [2026-10-09] Sayı animasyonu: değer 0'dan hedefe yumuşakça sayarak yükselir (hareket azaltma tercihinde direkt gösterir).
import { useEffect, useRef, useState } from 'react'

export default function Sayac({ deger, sure = 900, ondalik = 0 }) {
  const hedef = Number(deger)
  const [gosterilen, setGosterilen] = useState(Number.isFinite(hedef) ? 0 : deger)
  const kare = useRef(null)
  useEffect(() => {
    if (!Number.isFinite(hedef)) { setGosterilen(deger); return }
    const azalt = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (azalt || hedef === 0) { setGosterilen(hedef); return }
    const basla = performance.now()
    const adim = (simdi) => {
      const t = Math.min(1, (simdi - basla) / sure)
      const e = 1 - Math.pow(1 - t, 3)
      setGosterilen(hedef * e)
      if (t < 1) kare.current = requestAnimationFrame(adim)
    }
    kare.current = requestAnimationFrame(adim)
    return () => cancelAnimationFrame(kare.current)
  }, [hedef, sure, deger])
  if (!Number.isFinite(hedef)) return <>{deger}</>
  return <>{Number(gosterilen).toLocaleString('tr-TR', { minimumFractionDigits: ondalik, maximumFractionDigits: ondalik })}</>
}
