// [2026-10-11] Açılış amblemi — sistem açıldığında ana ekranda büyük, parlayan Filizyol amblemi ve "Hoş geldin".
// Her tarayıcı oturumunda bir kez (sessionStorage), ~2,4 sn sonra kendiliğinden kaybolur; tıklayınca / tuşa basınca hemen geçer.
// Okulun amblemi varsa altında küçük olarak görünür. Hareket azaltma tercihi olan kullanıcıda animasyon yok.
import { useEffect, useState } from 'react'

const ANAHTAR = 'acilis_goruldu'
export const acilisGosterilsinMi = () => { try { return sessionStorage.getItem(ANAHTAR) !== '1' } catch { return false } }

export default function AcilisAmblemi({ ad, okulAd, okulLogo, onBitti }) {
  const [cikiyor, setCikiyor] = useState(false)
  useEffect(() => {
    try { sessionStorage.setItem(ANAHTAR, '1') } catch { /* yoksay */ }
    const t1 = window.setTimeout(() => setCikiyor(true), 2200)
    const t2 = window.setTimeout(onBitti, 2650)
    const gec = () => { setCikiyor(true); window.setTimeout(onBitti, 300) }
    document.addEventListener('keydown', gec, { once: true })
    return () => { window.clearTimeout(t1); window.clearTimeout(t2); document.removeEventListener('keydown', gec) }
  }, [onBitti])

  return (
    <div className={`acilis${cikiyor ? ' cikiyor' : ''}`} onClick={() => { setCikiyor(true); window.setTimeout(onBitti, 300) }}
      role="status" aria-label={`Filizyol'a hoş geldin${ad ? `, ${ad}` : ''}`}>
      <div className="acilis-amblem" aria-hidden="true">
        <span className="acilis-halka h1" /><span className="acilis-halka h2" /><span className="acilis-halka h3" />
        <span className="acilis-isilti" />
        <span className="acilis-filiz">🌱</span>
      </div>
      <div className="acilis-hos">Hoş geldin{ad ? `, ${ad}` : ''}!</div>
      <div className="acilis-marka">Filizyol <span>· Kendi yolunu filizlendir</span></div>
      {(okulLogo || okulAd) && (
        <div className="acilis-okul">
          {okulLogo && <img src={okulLogo} alt="" />}
          {okulAd && <span>{okulAd}</span>}
        </div>
      )}
      <div className="acilis-gec">Geçmek için dokun</div>
    </div>
  )
}
