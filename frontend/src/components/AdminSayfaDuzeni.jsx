import { Fragment, useEffect, useState } from 'react'
import { Link, NavLink, Navigate, Outlet, useLocation } from 'react-router-dom'
import { okulBolumleri } from './yonetim/okulBolumleri'
import { useAdminAuth } from '../context/AdminAuthContext'
import { api } from '../api/client'
import { IlkSifrePenceresi, ROL_ADI } from './yonetim/ortak'
import { okulRenginiUygula } from '../tema'
import AltSerit from './AltSerit'
import BildirimZili from './BildirimZili'

const ni = ({ isActive }) => `ni${isActive ? ' active' : ''}`

// [2026-10-10] Süper admin menüsü: [yol, ikon, ad]. Sayfa adları değişmez; yalnızca gruplama.
const SUPER_MENU = [
  { grup: 'Genel', baglantilar: [['/admin', '🏠', 'Kontrol Paneli']] },
  { grup: 'Raporlar ve İstatistikler', baglantilar: [
    ['/admin/istatistikler', '📊', 'İstatistikler'],
    ['/admin/raporlar', '📄', 'Rapor Merkezi'],
    ['/admin/karsilastirma', '⚖️', 'Okul Karşılaştırması'],
    ['/admin/anket-psikometri', '📐', 'Anket Psikometrisi'],
  ] },
  { grup: 'Okullar ve Kullanıcılar', baglantilar: [
    ['/admin/okullar', '🏫', 'Okullar'],
    ['/admin/okul/0', '🎒', 'Okul Harici Öğrenciler'],
    ['/admin/paketler', '📦', 'Paketler'],
    ['/admin/koclar', '👩‍🏫', 'Eğitim Koçları'],
    ['/admin/yoneticiler', '🛠️', 'Süper Adminler'],
    ['/admin/test-hesaplari', '🧪', 'Test Hesapları'],
  ] },
  { grup: 'İçerik', baglantilar: [
    ['/admin/bolumler', '🎓', 'Bölümler'],
    ['/admin/yokatlas', '🔗', 'YÖK Atlas Eşleştirme'],
    ['/admin/is-hayati-verileri', '💼', 'İş Hayatı Verileri'],
    ['/admin/meslek-dili', '🗣️', 'Meslek Dili Sözlüğü'],
    ['/admin/konular', '📝', 'Konu Listesi (Net Takibi)'],
    ['/admin/dallar', '🌿', 'Dallar (K5)'],
    ['/admin/sorular', '❔', 'Soru Bankası'],
    ['/admin/gelisim-kaynak', '🌱', 'Gelişim Kaynak Havuzu'],
    ['/admin/takvim', '🗓️', 'Genel Takvim'],
  ] },
  { grup: 'Ölçme ve Kalite', baglantilar: [
    ['/admin/soru-gecerlilik', '🎯', 'Soru Geçerlilik Testi'],
    ['/admin/guvenlik', '🛡️', 'Güvenlik / Tutarlılık'],
    ['/admin/pipeline', '⚙️', 'Pipeline Durumu'],
  ] },
  { grup: 'Sistem', baglantilar: [
    ['/admin/parametreler', '🎛️', 'Parametreler'],
    ['/admin/audit-log', '📜', 'Audit Log'],
  ] },
  { grup: 'Yardım', baglantilar: [
    ['/admin/sistem-hakkinda', 'ℹ️', 'Sistem Hakkında'],
    ['/admin/sss', '❓', 'Okul Yetkilisi SSS'],
    ['/admin/kaynakca', '📚', 'Kaynakça'],
  ] },
]

// [2026-10-09] 3 yetki seviyesi: Süper Admin tüm menüyü görür; Okul Yetkilisi yalnızca kendi okulunun panelini.
export default function AdminSayfaDuzeni() {
  const { cikisYap, rol, ben, benYenile } = useAdminAuth()
  const konum = useLocation()
  const okulYetkilisi = rol === 'okul_yetkilisi'
  // [2026-10-10] Bekleyen kulüp katılma talebi sayısı (menüde Kulüpler'in yanında)
  const [bekleyenTalep, setBekleyenTalep] = useState(0)
  const [riskSayisi, setRiskSayisi] = useState(0)   // [2026-10-10] erken uyarı: yüksek seviyeli öğrenci sayısı
  useEffect(() => {
    if (okulYetkilisi && ben?.okul_id && (!ben.moduller || ben.moduller.includes('rehberlik'))) api.erkenUyari(ben.okul_id).then((v) => setRiskSayisi(v.ozet.yuksek || 0)).catch(() => {})
  }, [okulYetkilisi, ben?.okul_id, ben?.moduller, konum.search])
  useEffect(() => {
    if (okulYetkilisi && ben?.okul_id && (!ben.moduller || ben.moduller.includes('kulupler'))) api.kulupTalepleri(ben.okul_id).then((v) => setBekleyenTalep(v.bekleyen || 0)).catch(() => {})
  }, [okulYetkilisi, ben?.okul_id, konum.pathname, konum.search])
  // [2026-10-09] Okul yetkilisinin paneli okulun renginde; süper admin Filizyol renginde
  useEffect(() => {
    okulRenginiUygula(okulYetkilisi ? ben?.okul_renk : null)
    return () => okulRenginiUygula(null)
  }, [okulYetkilisi, ben?.okul_renk])

  if (okulYetkilisi && ben?.okul_id) {
    const okulYolu = `/admin/okul/${ben.okul_id}`
    if (!konum.pathname.startsWith(okulYolu) && konum.pathname !== '/admin/sss' && konum.pathname !== '/admin/kaynakca') return <Navigate to={okulYolu} replace />
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
          {(!okulYetkilisi || !ben?.moduller || ben.moduller.includes('bildirimler')) && <BildirimZili kapsam="yonetim" />}
          <button className="back" onClick={cikisYap} title="Çıkış yap">Çıkış</button>
        </div>

        {okulYetkilisi ? (
          <>
            {/* [2026-10-10] Okul paneli bölümleri sol menüde gruplu; sayfada artık sekme çubuğu yok */}
            {ben?.okul_id && okulBolumleri(ben.okul_id, ben.moduller).map((b, i, l) => {
              const okulYolu = `/admin/okul/${ben.okul_id}`
              const aktif = konum.pathname === okulYolu && (new URLSearchParams(konum.search).get('sekme') || 'ozet') === b.k
              return (
                <Fragment key={b.k}>
                  {(i === 0 || l[i - 1].grup !== b.grup) && <div className="ns">{b.grup}</div>}
                  <Link to={b.k === 'ozet' ? okulYolu : `${okulYolu}?sekme=${b.k}`} className={`ni${aktif ? ' active' : ''}`}>
                    <span className="ni-ikon">{b.ikon}</span>{b.ad}
                    {b.k === 'kulupler' && bekleyenTalep > 0 && <span className="ni-rozet">{bekleyenTalep}</span>}
                    {b.k === 'rehberlik' && riskSayisi > 0 && <span className="ni-rozet" title="Yüksek seviyede uyarısı olan öğrenci">{riskSayisi}</span>}
                  </Link>
                </Fragment>
              )
            })}
            <div className="ns">Yardım</div>
            <NavLink to="/admin/sss" className={ni}><span className="ni-ikon">❓</span>Sistem Hakkında & SSS</NavLink>
            <NavLink to="/admin/kaynakca" className={ni}><span className="ni-ikon">📚</span>Kaynakça</NavLink>
          </>
        ) : (
          <>
            {/* [2026-10-10] Süper admin menüsü gruplu; her bağlantıda ikon (okul paneliyle tutarlı) */}
            {SUPER_MENU.map((g) => (
              <Fragment key={g.grup}>
                <div className="ns">{g.grup}</div>
                {g.baglantilar.map(([yol, ikon, ad]) => (
                  <NavLink key={yol} to={yol} end={yol === '/admin'} className={ni}><span className="ni-ikon">{ikon}</span>{ad}</NavLink>
                ))}
              </Fragment>
            ))}
          </>
        )}
      </div>

      <div className="main">
        <div className="main-icerik">{okulYetkilisi && !ben ? <div className="pg"><div className="bos-durum">Yükleniyor…</div></div> : <Outlet />}</div>
        <AltSerit okul={ben?.okul_ad || (okulYetkilisi ? null : 'Filizyol Yönetim')} kisi={ben?.ad_soyad} rol={ROL_ADI[rol]} />
      </div>

      {ben?.sifre_degistirmeli && (
        <IlkSifrePenceresi rolMetni="yönetim hesabı" kaydet={(s) => api.yonetimIlkSifre(s)} onTamam={benYenile} onCikis={cikisYap} />
      )}
    </div>
  )
}
