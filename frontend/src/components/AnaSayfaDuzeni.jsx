import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import TemaAnahtari from './TemaAnahtari'

const MENU = [
  { yol: '/katmanlar', ikon: '🌱', ad: 'Yol Haritam' },
  { yol: '/sonuc', ikon: '🌟', ad: 'Uyumum' },
  { yol: '/kesfet', ikon: '🔍', ad: 'Keşfet' },
  { yol: '/koclugu', ikon: '🎯', ad: 'Koçluk' },
]

export default function AnaSayfaDuzeni() {
  const { cikisYap } = useAuth()
  const [ozet, setOzet] = useState(null)
  const location = useLocation()

  useEffect(() => {
    api.durumOzetiGetir().then(setOzet).catch(() => {})
  }, [])

  // /katmanlar/:kod veya /k5/:kod gibi alt rotalarda da "Yol Haritam" sekmesi aktif görünsün
  const aktifYol = (yol) => {
    if (yol === '/katmanlar') return location.pathname.startsWith('/katmanlar') || location.pathname.startsWith('/k5')
    return location.pathname.startsWith(yol)
  }

  return (
    <div className="app-alt">
      <div className="ust-cubuk">
        <div className="ust-logo">
          <span style={{ fontSize: 18 }}>🌱</span>
          <div>
            <div className="nm">Bölüm Uyum Sistemi</div>
            {ozet?.tur_no && <div className="su">Tur {ozet.tur_no}</div>}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <TemaAnahtari sabit={false} />
          <button className="back" onClick={cikisYap} title="Çıkış yap">Çıkış</button>
        </div>
      </div>

      <div className="main-alt">
        <Outlet />
      </div>

      <nav className="alt-menu">
        {MENU.map((m) => (
          <NavLink key={m.yol} to={m.yol} className={`am-item${aktifYol(m.yol) ? ' active' : ''}`}>
            <span className="am-ikon">{m.ikon}</span>
            <span className="am-ad">{m.ad}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
