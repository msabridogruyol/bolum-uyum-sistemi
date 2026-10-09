// [2026-10-09] Sol menüde öğrencinin KENDİ okulunun adı + amblemi. Tıklanınca okul tanıtım penceresi açılır
// (kuruluş yılı, öğrenci sayısı, tanıtım, kadro ve iletişim — okul yetkilisi / süper admin düzenler).
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Pencere } from './yonetim/ortak'
import OkulBilgiKarti from './OkulBilgiKarti'

export default function OkulRozeti() {
  const [okul, setOkul] = useState(null)
  const [acik, setAcik] = useState(false)

  useEffect(() => {
    let iptal = false
    api.okulBenim().then((o) => { if (!iptal) setOkul(o || null) }).catch(() => {})
    return () => { iptal = true }
  }, [])

  if (!okul) return null
  return (
    <>
      <button type="button" className="okul-rozeti okul-rozeti-btn" title={`${okul.ad} — okul hakkında`} onClick={() => setAcik(true)}>
        {okul.logo
          ? <img src={okul.logo} alt={`${okul.ad} amblemi`} className="okul-amblem" />
          : <div className="okul-amblem okul-amblem-bos">🏫</div>}
        <div style={{ minWidth: 0, flex: 1, textAlign: 'left' }}>
          <div className="okul-ad">{okul.ad}</div>
          {okul.alt_baslik && <div className="okul-alt">{okul.alt_baslik}</div>}
        </div>
        <span className="okul-rozeti-i" aria-hidden="true">i</span>
      </button>
      {acik && (
        <Pencere baslik="Okulum" onKapat={() => setAcik(false)}>
          <OkulBilgiKarti okul={okul} />
        </Pencere>
      )}
    </>
  )
}
