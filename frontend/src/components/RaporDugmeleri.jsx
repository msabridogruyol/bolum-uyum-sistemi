// [2026-10-10] Rapor indirme düğmeleri (PDF / Excel). Hata ve bekleme durumu düğmenin yanında gösterilir.
import { useState } from 'react'

export default function RaporDugmeleri({ secenekler, baslik = 'Raporlar', kucuk = false }) {
  const [bekle, setBekle] = useState(null)
  const [hata, setHata] = useState(null)
  async function indir(s) {
    setBekle(s.anahtar); setHata(null)
    try { await s.indir() } catch (e) { setHata(e.detail || 'Rapor indirilemedi.') } finally { setBekle(null) }
  }
  return (
    <div className={`rapor-dugmeleri${kucuk ? ' kucuk' : ''}`}>
      {baslik && <span className="rd-baslik">📄 {baslik}</span>}
      {secenekler.map((s) => (
        <button key={s.anahtar} type="button" className="rd-dugme" title={s.aciklama} disabled={!!bekle} onClick={() => indir(s)}>
          {bekle === s.anahtar ? <span className="spin" /> : s.ikon} {s.ad}
        </button>
      ))}
      {hata && <span className="auth-error" style={{ margin: 0, padding: '4px 10px', fontSize: 12 }}>{hata}</span>}
    </div>
  )
}
