import { useEffect } from 'react'
import { NavLink, Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAdminAuth } from '../context/AdminAuthContext'
import { api } from '../api/client'
import { IlkSifrePenceresi, ROL_ADI } from './yonetim/ortak'
import { okulRenginiUygula } from '../tema'
import AltSerit from './AltSerit'

const ni = ({ isActive }) => `ni${isActive ? ' active' : ''}`

// [2026-10-09] 3 yetki seviyesi: Süper Admin tüm menüyü görür; Okul Yetkilisi yalnızca kendi okulunun panelini.
export default function AdminSayfaDuzeni() {
  const { cikisYap, rol, ben, benYenile } = useAdminAuth()
  const konum = useLocation()
  const okulYetkilisi = rol === 'okul_yetkilisi'
  // [2026-10-09] Okul yetkilisinin paneli okulun renginde; süper admin Filizyol renginde
  useEffect(() => {
    okulRenginiUygula(okulYetkilisi ? ben?.okul_renk : null)
    return () => okulRenginiUygula(null)
  }, [okulYetkilisi, ben?.okul_renk])

  if (okulYetkilisi && ben?.okul_id) {
    const okulYolu = `/admin/okul/${ben.okul_id}`
    if (!konum.pathname.startsWith(okulYolu)) return <Navigate to={okulYolu} replace />
  }

  return (
    <div className="app">
      <div className="sb">
        <div className="sb-logo">
          <div className="nm">Filizyol</div>
          <div className="su">{okulYetkilisi ? 'Okul Paneli' : 'Yönetici Paneli'}</div>
        </div>
        {okulYetkilisi && ben && (
          <div className="okul-rozeti" title={ben.okul_ad}>
            {ben.okul_logo ? <img src={ben.okul_logo} alt="" className="okul-amblem" /> : <div className="okul-amblem okul-amblem-bos">🏫</div>}
            <div style={{ minWidth: 0 }}><div className="okul-ad">{ben.okul_ad}</div></div>
          </div>
        )}
        <div className="sb-user">
          <div className="av">{okulYetkilisi ? '🏫' : '🛠️'}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div className="u-nm" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{ben?.ad_soyad || 'Yönetici'}</div>
            <div className="u-id">{ROL_ADI[rol] || rol}</div>
          </div>
          <button className="back" onClick={cikisYap} title="Çıkış yap">Çıkış</button>
        </div>

        {okulYetkilisi ? (
          <>
            <div className="ns">Okulum</div>
            {ben?.okul_id && <NavLink to={`/admin/okul/${ben.okul_id}`} className={ni}>Okul Paneli</NavLink>}
          </>
        ) : (
          <>
            <div className="ns">Genel</div>
            <NavLink to="/admin" end className={ni}>Kontrol Paneli</NavLink>
            <NavLink to="/admin/pipeline" className={ni}>Pipeline Durumu</NavLink>

            <div className="ns">Okullar ve Hesaplar</div>
            <NavLink to="/admin/okullar" className={ni}>Okullar</NavLink>
            <NavLink to="/admin/okul/0" className={ni}>Okul Harici Öğrenciler</NavLink>
            <NavLink to="/admin/yoneticiler" className={ni}>Süper Adminler</NavLink>
            <NavLink to="/admin/test-hesaplari" className={ni}>🧪 Test Hesapları</NavLink>
            <NavLink to="/admin/koclar" className={ni}>Eğitim Koçları</NavLink>

            <div className="ns">İçerik Yönetimi</div>
            <NavLink to="/admin/bolumler" className={ni}>Bölümler</NavLink>
            <NavLink to="/admin/meslek-dili" className={ni}>Meslek Dili Sözlüğü</NavLink>
            <NavLink to="/admin/dallar" className={ni}>Dallar (K5)</NavLink>
            <NavLink to="/admin/sorular" className={ni}>Soru Bankası</NavLink>

            <div className="ns">Sistem</div>
            <NavLink to="/admin/parametreler" className={ni}>Parametreler</NavLink>
            <NavLink to="/admin/soru-gecerlilik" className={ni}>Soru Geçerlilik Testi</NavLink>
            <NavLink to="/admin/audit-log" className={ni}>Audit Log</NavLink>
            <NavLink to="/admin/sistem-hakkinda" className={ni}>Sistem Hakkında</NavLink>
            <NavLink to="/admin/guvenlik" className={ni}>Güvenlik / Tutarlılık</NavLink>
            <NavLink to="/admin/gelisim-kaynak" className={ni}>Gelişim Kaynak Havuzu</NavLink>
          </>
        )}
      </div>

      <div className="main">
        {okulYetkilisi && !ben ? <div className="pg"><div className="bos-durum">Yükleniyor…</div></div> : <Outlet />}
        <AltSerit okul={ben?.okul_ad || (okulYetkilisi ? null : 'Filizyol Yönetim')} kisi={ben?.ad_soyad} rol={ROL_ADI[rol]} />
      </div>

      {ben?.sifre_degistirmeli && (
        <IlkSifrePenceresi rolMetni="yönetim hesabı" kaydet={(s) => api.yonetimIlkSifre(s)} onTamam={benYenile} onCikis={cikisYap} />
      )}
    </div>
  )
}
