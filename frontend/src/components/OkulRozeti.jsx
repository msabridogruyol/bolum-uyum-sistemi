// [2026-10-09] Sol menüde öğrencinin KENDİ okulunun adı + amblemi (okul yönetimden atanır; okul harici öğrencide görünmez).
import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function OkulRozeti() {
  const [okul, setOkul] = useState(null)

  useEffect(() => {
    let iptal = false
    api.okulBenim().then((o) => { if (!iptal) setOkul(o || null) }).catch(() => {})
    return () => { iptal = true }
  }, [])

  if (!okul) return null
  return (
    <div className="okul-rozeti" title={okul.ad}>
      {okul.logo
        ? <img src={okul.logo} alt={`${okul.ad} amblemi`} className="okul-amblem" />
        : <div className="okul-amblem okul-amblem-bos">🏫</div>}
      <div style={{ minWidth: 0 }}>
        <div className="okul-ad">{okul.ad}</div>
        {okul.alt_baslik && <div className="okul-alt">{okul.alt_baslik}</div>}
      </div>
    </div>
  )
}
