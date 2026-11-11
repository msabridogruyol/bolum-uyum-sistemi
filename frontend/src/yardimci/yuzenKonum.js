// [2026-11-11] Açılır panelin konumu: panel body'ye taşınır (portal) ve tetikleyicinin hemen altına sabitlenir. Kart içinde
// açılan liste, sonra gelen kartların / sekmelerin altında kalıyordu (her kartın kendi katmanı var). Kaydırma ve boyut
// değişince yeniden hesaplanır; aşağıda yer yoksa yukarı açılır.
import { useLayoutEffect, useState } from 'react'

export function useYuzenKonum(kapRef, acik, yukseklik = 340) {
  const [konum, setKonum] = useState(null)
  useLayoutEffect(() => {
    if (!acik) { setKonum(null); return undefined }
    const hesapla = () => {
      const r = kapRef.current?.getBoundingClientRect()
      if (!r) return
      const asagi = window.innerHeight - r.bottom
      const yukari = asagi < Math.min(yukseklik, 220) && r.top > asagi
      setKonum({
        position: 'fixed', left: Math.max(8, Math.min(r.left, window.innerWidth - 268)), minWidth: r.width, zIndex: 10000,
        ...(yukari ? { bottom: window.innerHeight - r.top + 4, top: 'auto', maxHeight: r.top - 12 }
                   : { top: r.bottom + 4, maxHeight: Math.max(160, asagi - 12) }),
      })
    }
    hesapla()
    window.addEventListener('resize', hesapla)
    window.addEventListener('scroll', hesapla, true)
    return () => { window.removeEventListener('resize', hesapla); window.removeEventListener('scroll', hesapla, true) }
  }, [acik, kapRef, yukseklik])
  return konum
}
