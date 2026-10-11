// [2026-10-11] Sözlük penceresi — "sozluk-ac" olayıyla açılır (Filiz'in altındaki "📖 Sözlük" düğmesi).
// Filiz sohbeti açıksa (okulda Filiz modülü varsa) sözlük Filiz panelinin "Sözlük" sekmesinde açılır;
// yoksa bu küçük pencere açılır. Sayfadaki metinlere hiçbir işaret konmaz.
import { useEffect, useState } from 'react'
import SozlukArama from './SozlukArama'

export const sozluguAc = (kelime = '') => window.dispatchEvent(new CustomEvent('sozluk-ac', { detail: { kelime } }))

export default function SozlukPenceresi({ filizVar = false }) {
  const [acik, setAcik] = useState(false)
  const [kelime, setKelime] = useState('')

  useEffect(() => {
    const ac = (e) => {
      if (filizVar) {   // Filiz paneli kendi Sözlük sekmesini açar
        window.dispatchEvent(new CustomEvent('filiz-ac', { detail: { sekme: 'sozluk', kelime: e.detail?.kelime || '' } }))
        return
      }
      setKelime(e.detail?.kelime || ''); setAcik(true)
    }
    window.addEventListener('sozluk-ac', ac)
    return () => window.removeEventListener('sozluk-ac', ac)
  }, [filizVar])

  useEffect(() => {
    if (!acik) return undefined
    const kapat = (e) => { if (e.key === 'Escape') setAcik(false) }
    document.addEventListener('keydown', kapat)
    return () => document.removeEventListener('keydown', kapat)
  }, [acik])

  if (!acik) return null
  return (
    <div className="sz-pencere" role="dialog" aria-label="Sistem sözlüğü">
      <div className="sz-pencere-ust">
        <b>📖 Sistem Sözlüğü</b>
        <button className="cv-kapat" onClick={() => setAcik(false)} aria-label="Kapat">✕</button>
      </div>
      <div className="sz-pencere-icerik">
        <SozlukArama baslangic={kelime} kompakt onSayfayaGit={() => setAcik(false)} />
      </div>
    </div>
  )
}
