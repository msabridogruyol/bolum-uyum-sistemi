import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import TemaAnahtari from './TemaAnahtari'

export default function AnaSayfaDuzeni() {
  const { cikisYap } = useAuth()
  const [ozet, setOzet] = useState(null)
  const [profil, setProfil] = useState(null)

  useEffect(() => {
    api.durumOzetiGetir().then(setOzet).catch(() => {})
    api.profilGetir().then(setProfil).catch(() => {})
  }, [])

  const ilkAd = profil?.ad_soyad?.trim().split(/\s+/)[0] || 'Öğrenci'

  return (
    <div className="app">
      <div className="sb">
        <div className="sb-logo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div className="nm">🌱 Bölüm Uyum Sistemi</div>
            <div className="su">Kendi yolunu filizlendir</div>
          </div>
          <TemaAnahtari sabit={false} />
        </div>
        <div className="sb-user">
          {profil?.profil_foto_base64 ? (
            <img
              src={profil.profil_foto_base64}
              alt=""
              className="av"
              style={{ objectFit: 'cover', width: 36, height: 36, borderRadius: '50%' }}
            />
          ) : (
            <div className="av">🎓</div>
          )}
          <div style={{ flex: 1 }}>
            <div className="u-nm">{ilkAd}</div>
            {ozet?.tur_no && <div className="u-id">Tur {ozet.tur_no}</div>}
          </div>
          <button className="back" onClick={cikisYap} title="Çıkış yap">Çıkış</button>
        </div>
        {ozet && (
          <div style={{ padding: '10px 18px', borderBottom: '1px solid var(--bor)', fontSize: 11, color: 'var(--tx2)' }}>
            <div>Katmanlar: <b>{ozet.tamamlanan_katman_sayisi}/{ozet.toplam_ana_katman_sayisi}</b></div>
            {ozet.k5_acilan_dal_sayisi > 0 && (
              <div style={{ marginTop: 3 }}>Derinleşme: <b>{ozet.k5_tamamlanan_dal_sayisi}/{ozet.k5_acilan_dal_sayisi}</b> tamamlandı</div>
            )}
            {ozet.sonraki_tur_tarihi && (
              <div style={{ marginTop: 3 }}>Sonraki tur: <b>{new Date(ozet.sonraki_tur_tarihi).toLocaleDateString('tr-TR')}</b></div>
            )}
          </div>
        )}
        <div className="ns">Genel</div>
        <NavLink to="/" end className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🏠 Ana Sayfa
        </NavLink>
        <NavLink to="/katmanlar" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🌱 Yol Haritam
        </NavLink>
        <div className="ns">Sonuç</div>
        <NavLink to="/sonuc" end className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🌟 Bölüm Uyumum
        </NavLink>
        <NavLink to="/sonuc/genel" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          📊 Genel Sonuçlar
        </NavLink>
        <NavLink to="/sonuc/K1" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🌱 K1 — Değerler
        </NavLink>
        <NavLink to="/sonuc/K2" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🌿 K2 — Kişilik
        </NavLink>
        <NavLink to="/sonuc/K3" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🍃 K3 — İş Ortamı
        </NavLink>
        <NavLink to="/sonuc/K4" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🌸 K4 — Alan Eğilimi
        </NavLink>
        <NavLink to="/sonuc/K5" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🌻 K5 — Derinleşme
        </NavLink>
        <NavLink to="/kesfet" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🔍 Tüm Bölümleri Keşfet
        </NavLink>
        <NavLink to="/koclugu" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🎯 Hedef Bölüm Koçluğu
        </NavLink>
        <NavLink to="/koclugu/asistan" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🧭 Kariyer Koçun (AI)
        </NavLink>
        <div style={{ flex: 1 }} />
        <div className="ns">Hesap</div>
        <NavLink to="/profil" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          ⚙️ Ayarlar
        </NavLink>
      </div>
      <div className="main">
        <Outlet />
      </div>
    </div>
  )
}
