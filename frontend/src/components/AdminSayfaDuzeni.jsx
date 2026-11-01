import { Fragment, useCallback, useEffect, useState } from 'react'
import { hesapDiliniUygula } from '../yardimci/dil'   // [2026-10-12] hesaptaki dil tercihi
import DilSecici from './DilSecici'   // [2026-10-12] çoklu dil
import TanitimTuru, { turuBaslat } from './TanitimTuru'   // [2026-10-11] menü tanıtım turu
import AcilisAmblemi, { acilisGosterilsinMi } from './AcilisAmblemi'   // [2026-10-11] açılış amblemi
import { Link, NavLink, Navigate, Outlet, useLocation } from 'react-router-dom'
import { okulBolumleri } from './yonetim/okulBolumleri'
import { useAdminAuth } from '../context/AdminAuthContext'
import { api } from '../api/client'
import { IlkSifrePenceresi, ROL_ADI } from './yonetim/ortak'
import { okulRenginiUygula } from '../tema'
import AltSerit from './AltSerit'
import BildirimZili from './BildirimZili'
import { MobilUstCubuk, useMobilMenu } from './MobilMenu'
import MaskotYonetim from './MaskotYonetim'
import FilizYonetimSohbet from './FilizYonetimSohbet'
import CevrimiciPanel from './CevrimiciPanel'   // [2026-10-11] sağ altta çevrim içi öğrenciler

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
    ['/admin/veri-kaynaklari', '🗂️', 'Veri Kaynakları'],   // [2026-11-01]
    ['/admin/parametreler', '🎛️', 'Parametreler'],
    ['/admin/audit-log', '📜', 'Audit Log'],
    ['/admin/hata-kayitlari', '🐞', 'Hata Kayıtları'],
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
  const menu = useMobilMenu()   // [2026-10-11] dar ekranda çekmece menü
  // [2026-10-10] Bekleyen kulüp katılma talebi sayısı (menüde Kulüpler'in yanında)
  const [bekleyenTalep, setBekleyenTalep] = useState(0)
  const [riskSayisi, setRiskSayisi] = useState(0)   // [2026-10-10] erken uyarı: yüksek seviyeli öğrenci sayısı
  useEffect(() => {
    if (okulYetkilisi && ben?.okul_id && (!ben.moduller || ben.moduller.includes('rehberlik'))) api.erkenUyari(ben.okul_id).then((v) => setRiskSayisi(v.ozet.yuksek || 0)).catch(() => {})
  }, [okulYetkilisi, ben?.okul_id, ben?.moduller, konum.search])
  useEffect(() => {
    if (okulYetkilisi && ben?.okul_id && (!ben.moduller || ben.moduller.includes('kulupler'))) api.kulupTalepleri(ben.okul_id).then((v) => setBekleyenTalep(v.bekleyen || 0)).catch(() => {})
  }, [okulYetkilisi, ben?.okul_id, konum.pathname, konum.search])
  // [2026-10-11] Açılış amblemi (oturumda bir kez) + ilk girişte menü tanıtım turu (rol ve pakete göre menüden üretilir)
  const [acilis, setAcilis] = useState(acilisGosterilsinMi)
  const [turAcik, setTurAcik] = useState(false)
  // [2026-10-12] Hesaptaki dil tercihi (giriş ekranında seçildiyse hesaba yazılır)
  useEffect(() => { if (ben) hesapDiliniUygula(ben.dil, (k) => api.dilKaydet(k, 'admin')) }, [ben])
  const turAnahtari = ben ? `tur_goruldu_yonetim_${ben.id || ben.email || ben.ad_soyad}` : null
  useEffect(() => {
    if (!turAnahtari || ben?.sifre_degistirmeli) return
    try { if (localStorage.getItem(turAnahtari) !== '1') setTurAcik(true) } catch { /* gizli sekme */ }
  }, [turAnahtari, ben?.sifre_degistirmeli])
  useEffect(() => {
    const ac = () => setTurAcik(true)
    window.addEventListener('tur-baslat', ac)
    return () => window.removeEventListener('tur-baslat', ac)
  }, [])
  const turuBitir = useCallback(() => {
    try { if (turAnahtari) localStorage.setItem(turAnahtari, '1') } catch { /* yoksay */ }
    setTurAcik(false)
  }, [turAnahtari])
  const acilisBitti = useCallback(() => setAcilis(false), [])
  // [2026-10-09] Okul yetkilisinin paneli okulun renginde; süper admin Filizyol renginde
  useEffect(() => {
    okulRenginiUygula(okulYetkilisi ? ben?.okul_renk : null)
    return () => okulRenginiUygula(null)
  }, [okulYetkilisi, ben?.okul_renk])

  if (okulYetkilisi && ben?.okul_id) {
    const okulYolu = `/admin/okul/${ben.okul_id}`
    if (!konum.pathname.startsWith(okulYolu) && konum.pathname !== '/admin/sss' && konum.pathname !== '/admin/kaynakca') return <Navigate to={okulYolu} replace />
  }

  const zilVar = !okulYetkilisi || !ben?.moduller || ben.moduller.includes('bildirimler')
  // [2026-10-11] Filiz panel asistanı: süper adminde her zaman; okul yetkilisinde paketinde 'filiz' modülü açıksa
  const filizVar = !!ben && !ben.sifre_degistirmeli && (!okulYetkilisi || (ben.okul_id && (!ben.moduller || ben.moduller.includes('filiz'))))
  return (
    <div className={`app${menu.appSinifi}`}>
      <MobilUstCubuk menu={menu} sag={zilVar && <BildirimZili kapsam="yonetim" />}
        baslik={okulYetkilisi ? (
          <>
            {ben?.okul_logo ? <img src={ben.okul_logo} alt="" className="mobil-logo" /> : <span aria-hidden="true">🏫</span>}
            <span className="mobil-baslik-ad">{ben?.okul_ad || 'Okul Paneli'}</span>
          </>
        ) : <span className="mobil-baslik-ad">Yönetici Paneli</span>} />
      <div className="sb" {...menu.cekmeceOzellikleri}>
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
          {zilVar && !menu.mobil && <BildirimZili kapsam="yonetim" />}
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
            <button type="button" className="ni ni-btn" onClick={turuBaslat}><span className="ni-ikon">🎬</span>Tanıtımı başlat</button>
            <div className="ni-dil"><span className="ni-ikon">🌐</span><DilSecici kapsam="admin" /></div>
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
            <button type="button" className="ni ni-btn" onClick={turuBaslat}><span className="ni-ikon">🎬</span>Tanıtımı başlat</button>
            <div className="ni-dil"><span className="ni-ikon">🌐</span><DilSecici kapsam="admin" /></div>
          </>
        )}
      </div>

      <div className={`main yonetim-main${filizVar ? ' filiz-var' : ''}`}>
        {filizVar && <MaskotYonetim rol={rol} ad={ben.ad_soyad} okulId={ben.okul_id} moduller={ben.moduller} />}
        <div className="main-icerik">{okulYetkilisi && !ben ? <div className="pg"><div className="bos-durum yukleniyor">Yükleniyor…</div></div> : <Outlet />}</div>
        <AltSerit okul={ben?.okul_ad || (okulYetkilisi ? null : 'Filizyol Yönetim')} kisi={ben?.ad_soyad} rol={ROL_ADI[rol]} />
      </div>

      {filizVar && <FilizYonetimSohbet rol={rol} okulId={ben.okul_id} moduller={ben.moduller} />}
      {acilis && ben && <AcilisAmblemi ad={(ben.ad_soyad || '').trim().split(/\s+/)[0]} okulAd={okulYetkilisi ? ben.okul_ad : null} okulLogo={okulYetkilisi ? ben.okul_logo : null} onBitti={acilisBitti} />}
      {turAcik && !acilis && ben && !ben.sifre_degistirmeli && <TanitimTuru kapsam={okulYetkilisi ? 'yonetim' : 'super'} onBitir={turuBitir} />}
      {/* [2026-10-11] Çevrim içi öğrenciler: yetkili kendi okulunu; süper admin açık okul panelini ya da okul başına sayıları görür */}
      {ben && !ben.sifre_degistirmeli && (
        <CevrimiciPanel kapsam="yonetim" okulId={okulYetkilisi ? ben.okul_id : (Number(/^\/admin\/okul\/(\d+)/.exec(konum.pathname)?.[1]) || null)} />
      )}
      {ben?.sifre_degistirmeli && (
        <IlkSifrePenceresi rolMetni="yönetim hesabı" kaydet={(s) => api.yonetimIlkSifre(s)} onTamam={benYenile} onCikis={cikisYap} />
      )}
    </div>
  )
}
