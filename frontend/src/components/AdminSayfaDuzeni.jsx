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
            <div className="ns">Genel</div>
            <NavLink to="/admin" end className={ni}>Kontrol Paneli</NavLink>
            <NavLink to="/admin/pipeline" className={ni}>Pipeline Durumu</NavLink>

            <div className="ns">Okullar ve Hesaplar</div>
            <NavLink to="/admin/okullar" className={ni}>Okullar</NavLink>
            <NavLink to="/admin/karsilastirma" className={ni}>📊 Okul Karşılaştırması</NavLink>
            <NavLink to="/admin/okul/0" className={ni}>Okul Harici Öğrenciler</NavLink>
            <NavLink to="/admin/yoneticiler" className={ni}>Süper Adminler</NavLink>
            <NavLink to="/admin/test-hesaplari" className={ni}>🧪 Test Hesapları</NavLink>
            <NavLink to="/admin/koclar" className={ni}>Eğitim Koçları</NavLink>
            <NavLink to="/admin/takvim" className={ni}>Genel Takvim</NavLink>
            <NavLink to="/admin/paketler" className={ni}>📦 Paketler</NavLink>
            <NavLink to="/admin/sss" className={ni}>Okul Yetkilisi SSS</NavLink>

            <div className="ns">İçerik Yönetimi</div>
            <NavLink to="/admin/bolumler" className={ni}>Bölümler</NavLink>
            <NavLink to="/admin/yokatlas" className={ni}>YÖK Atlas Eşleştirme</NavLink>
            <NavLink to="/admin/meslek-dili" className={ni}>Meslek Dili Sözlüğü</NavLink>
            <NavLink to="/admin/konular" className={ni}>Konu Listesi (Net Takibi)</NavLink>
            <NavLink to="/admin/dallar" className={ni}>Dallar (K5)</NavLink>
            <NavLink to="/admin/sorular" className={ni}>Soru Bankası</NavLink>

            <div className="ns">Sistem</div>
            <NavLink to="/admin/parametreler" className={ni}>Parametreler</NavLink>
            <NavLink to="/admin/soru-gecerlilik" className={ni}>Soru Geçerlilik Testi</NavLink>
            <NavLink to="/admin/anket-psikometri" className={ni}>Anket Psikometrisi</NavLink>
            <NavLink to="/admin/audit-log" className={ni}>Audit Log</NavLink>
            <NavLink to="/admin/sistem-hakkinda" className={ni}>Sistem Hakkında</NavLink>
            <NavLink to="/admin/kaynakca" className={ni}>📚 Kaynakça</NavLink>
            <NavLink to="/admin/guvenlik" className={ni}>Güvenlik / Tutarlılık</NavLink>
            <NavLink to="/admin/gelisim-kaynak" className={ni}>Gelişim Kaynak Havuzu</NavLink>
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
