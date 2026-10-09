// [2026-10-09] Sol menüde gösterilen okul adı + amblemi (yönetim panelindeki "Okullar" sayfasından ayarlanır).
import { useEffect, useState } from 'react'
import { api } from '../api/client'

let onbellek = null   // sayfa geçişlerinde tekrar istek atılmasın

export default function OkulRozeti() {
  const [okul, setOkul] = useState(onbellek)

  useEffect(() => {
    if (onbellek) return
    api.okulAktif().then((o) => { onbellek = o || false; setOkul(onbellek) }).catch(() => {})
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
