// [2026-10-11] Sunucu / bağlantı sorunu uyarı şeridi — ekranın üstünde, tüm sayfalarda (öğrenci, yönetim, giriş).
// Kod, HTML ya da teknik ayrıntı göstermez. api/client.js 'sunucu-durumu' olayını yayar:
//   sorunlu: true  → 5xx, bağlantı kopması ya da ağ katmanı sayfası (tekrar denemelerden sonra)
//   sorunlu: false → ilk başarılı yanıt (şerit kendiliğinden kapanır)
// Tarayıcının çevrim dışı olması ayrıca "internet bağlantısı" mesajıyla gösterilir.
import { useEffect, useState } from 'react'
import { SUNUCU_MESAJI } from '../api/client'

export default function SunucuUyarisi() {
  const [sunucu, setSunucu] = useState(false)
  const [cevrimdisi, setCevrimdisi] = useState(typeof navigator !== 'undefined' && navigator.onLine === false)
  const [kapatildi, setKapatildi] = useState(false)

  useEffect(() => {
    const durum = (e) => { setSunucu(!!e.detail?.sorunlu); if (e.detail?.sorunlu) setKapatildi(false) }
    const kopuk = () => { setCevrimdisi(true); setKapatildi(false) }
    const bagli = () => setCevrimdisi(false)
    window.addEventListener('sunucu-durumu', durum)
    window.addEventListener('offline', kopuk)
    window.addEventListener('online', bagli)
    return () => {
      window.removeEventListener('sunucu-durumu', durum)
      window.removeEventListener('offline', kopuk)
      window.removeEventListener('online', bagli)
    }
  }, [])

  if (kapatildi || (!sunucu && !cevrimdisi)) return null
  return (
    <div className="su-serit" role="alert">
      <span className="su-ikon" aria-hidden="true">{cevrimdisi ? '📶' : '🛠️'}</span>
      <span className="su-metin">
        {cevrimdisi
          ? 'İnternet bağlantınız kesildi. Bağlantı gelince sayfayı yenileyin.'
          : SUNUCU_MESAJI}
      </span>
      <button className="su-yenile" onClick={() => window.location.reload()}>Sayfayı yenile</button>
      <button className="su-kapat" onClick={() => setKapatildi(true)} aria-label="Uyarıyı kapat">✕</button>
    </div>
  )
}
