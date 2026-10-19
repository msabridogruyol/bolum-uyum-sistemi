import { useCallback, useEffect, useState } from 'react'
import { hesapDiliniUygula } from '../yardimci/dil'   // [2026-10-12] hesaptaki dil tercihi
import { NavLink, Outlet, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import TemaAnahtari from './TemaAnahtari'
import SozlukPenceresi from './SozlukPenceresi'   // [2026-10-11] Filiz'in yanından açılan sistem sözlüğü (arama)
import CevrimiciPanel from './CevrimiciPanel'   // [2026-10-11] sağ altta çevrim içi öğrenciler   // [2026-10-11] zor kelimeye dokununca anlamı
import TanitimTuru from './TanitimTuru'   // [2026-10-11] menüleri tek tek tanıtan tur (eski 5 adımlı pencerenin yerine)
import AcilisAmblemi, { acilisGosterilsinMi } from './AcilisAmblemi'   // [2026-10-11] açılışta parlayan amblem
import Maskot from './Maskot'
import OkulRozeti from './OkulRozeti'
import FilizSohbet from './FilizSohbet'
import AltSerit from './AltSerit'
import BildirimZili from './BildirimZili'
import SimulasyonKatmani from './MeslekSimulasyonu'
import { KvkkOnayPenceresi } from './KvkkBilesenleri'
import { MobilUstCubuk, useMobilMenu } from './MobilMenu'
import { IlkSifrePenceresi } from './yonetim/ortak'
import { MODUL_ADI, YOL_MODULU, modulleriYukle, useModuller } from '../yardimci/moduller'

// [2026-10-03] İlk giriş akışı: tanıtım penceresi → profil (ad + sınıf zorunlu) → ana sayfa
// [2026-10-09] Okul öğrenciden alınmaz; yönetimdeki Okullar sayfasından atanır.
export const profilEksikMi = (p) => !p || !p.ad_soyad?.trim() || !p.sinif?.trim()
const tanitimAnahtari = (p) => `tanitim_goruldu_${p?.email || 'misafir'}`
function tanitimGorulduMu(p) {
  try { return localStorage.getItem(tanitimAnahtari(p)) === '1' } catch { return true }
}

function PaketteYok({ ad }) {
  const navigate = useNavigate()
  return (
    <div className="pg">
      <div className="ph"><div className="pt">{ad}</div><div className="ps">Bu özellik şu an kapalı.</div></div>
      <div className="card bos-durum" style={{ padding: 32 }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>🔒</div>
        <b>{ad}</b> okulunun Filizyol paketinde yer almıyor.
        <div className="yp-ince" style={{ marginTop: 6 }}>Bu özelliği kullanmak istersen rehber öğretmenine söyleyebilirsin.</div>
        <button className="btn" style={{ marginTop: 14 }} onClick={() => navigate('/')}>Ana sayfaya dön</button>
      </div>
    </div>
  )
}

export default function AnaSayfaDuzeni() {
  const { cikisYap } = useAuth()
  const [ozet, setOzet] = useState(null)
  const [profil, setProfil] = useState(null)
  const [kocVar, setKocVar] = useState(false)   // [2026-10-10] okulunda aktif koç yoksa menüde gösterilmez
  const [profilYuklendi, setProfilYuklendi] = useState(false)
  const [tanitimAcik, setTanitimAcik] = useState(false)
  const [turTekrar, setTurTekrar] = useState(false)   // Ayarlar'dan yeniden başlatıldıysa bitince profil sayfasına gidilmez
  const [acilis, setAcilis] = useState(acilisGosterilsinMi)
  const [kvkkGerekli, setKvkkGerekli] = useState(false) // [2026-10-04] eski hesap veya yeni metin sürümü
  const konum = useLocation()
  const karsilastirmaAcik = konum.pathname === '/koclugu' && new URLSearchParams(konum.search).get('sekme') === 'karsilastirma'
  const navigate = useNavigate()
  const acik = useModuller()   // [2026-10-10] okulun paketindeki modüller
  const menu = useMobilMenu()   // [2026-10-11] dar ekranda çekmece menü
  const [bekleyenAnket, setBekleyenAnket] = useState(0)
  const anketAcik = acik('anketler')
  useEffect(() => { if (anketAcik) api.anketlerim().then((v) => setBekleyenAnket(v.bekleyen || 0)).catch(() => {}) }, [anketAcik, konum.pathname, konum.search])

  useEffect(() => { modulleriYukle(true) }, [])   // her girişte tazele (okulun paketi değişmiş olabilir)

  useEffect(() => {
    if (konum.pathname.startsWith('/katmanlar')) api.durumOzetiGetir().then(setOzet).catch(() => {})
    api.kvkkDurumu().then((d) => setKvkkGerekli(!d.guncel)).catch(() => {})
    api.kocVarMi().then((d) => setKocVar(!!d.var)).catch(() => {})   // modül kapalıysa 403 → menüde yok
    api.profilGetir()
      .then((p) => { setProfil(p); if (hesapDiliniUygula(p.dil, (k) => api.dilKaydet(k, 'ogrenci'))) return; if (!tanitimGorulduMu(p)) setTanitimAcik(true) })
      .catch(() => {})
      .finally(() => setProfilYuklendi(true))
  }, [])

  // [2026-10-10] Test ekranlarından çıkınca özet tazelenir: test bitince "Değerlendirme" menüden kalkar
  const testte = konum.pathname.startsWith('/katmanlar')
  useEffect(() => {
    if (!testte) api.durumOzetiGetir().then(setOzet).catch(() => {})
  }, [testte])

  // Profil sayfası kaydettiğinde menüdeki ad/foto ve zorunlu alan kontrolü hemen güncellensin
  const profilYenile = useCallback((p) => setProfil(p), [])
  const tanitimiAc = useCallback(() => { setTurTekrar(true); setTanitimAcik(true) }, [])
  useEffect(() => {   // [2026-10-11] 'tur-baslat' olayı (TanitimTuru.turuBaslat)
    window.addEventListener('tur-baslat', tanitimiAc)
    return () => window.removeEventListener('tur-baslat', tanitimiAc)
  }, [tanitimiAc])
  const acilisBitti = useCallback(() => setAcilis(false), [])

  function tanitimiBitir() {
    try { localStorage.setItem(tanitimAnahtari(profil), '1') } catch { /* gizli sekme vb. */ }
    setTanitimAcik(false)
    // [2026-10-10] İlk girişte (tanıtımdan sonra) öğrenci her zaman profil sayfasına gelir: bilgilerini kontrol eder, fotoğraf/ilgi alanı ekler
    if (!turTekrar) navigate('/profil?ilk=1')
    setTurTekrar(false)
  }

  // Profil tamamlanmadan diğer sayfalara geçilmez (tanıtım açıkken yönlendirme beklenir)
  const profilSayfasinda = konum.pathname.startsWith('/profil')
  // [2026-10-09] Okulun açtığı hesap geçici şifreyle başlar: önce öğrenci kendi şifresini belirler
  const sifreGerekli = !!profil?.sifre_degistirmeli
  if (profilYuklendi && profil && !sifreGerekli && !tanitimAcik && !kvkkGerekli && profilEksikMi(profil) && !profilSayfasinda) {
    return <Navigate to="/profil?ilk=1" replace />
  }

  // [2026-10-10] Paketinde olmayan bir sayfaya adresle gelinirse sayfa yerine bilgi kartı
  const yolModulu = YOL_MODULU['/' + konum.pathname.split('/')[1]]
  const kapaliModul = yolModulu && !acik(yolModulu) ? yolModulu : null

  const ilkAd = profil?.ad_soyad?.trim().split(/\s+/)[0] || 'Öğrenci'
  // Değerlendirme menüde yalnızca bitmemişse (K1-K4 veya açılan K5 dalları) ya da sınıfa göre yeni tur zamanı geldiyse görünür
  const k5Bekliyor = !!ozet && ozet.k5_acilan_dal_sayisi > ozet.k5_tamamlanan_dal_sayisi
  const yeniTurHazir = !!ozet?.sonraki_tur_tarihi && new Date(ozet.sonraki_tur_tarihi) <= new Date()
  const degerlendirmeGoster = !ozet || !ozet.tur_tamamlandi_mi || k5Bekliyor || yeniTurHazir
  const degerlendirmeYuzde = ozet && !ozet.tur_tamamlandi_mi && ozet.toplam_ana_katman_sayisi
    ? Math.round((ozet.tamamlanan_katman_sayisi / ozet.toplam_ana_katman_sayisi) * 100) : null

  return (
    <div className={`app${menu.appSinifi}`}>
      <MobilUstCubuk menu={menu} baslik={<span className="mobil-baslik-ad">🌱 Filizyol</span>}
        sag={acik('bildirimler') && <BildirimZili kapsam="ogrenci" />} />
      <div className="sb" {...menu.cekmeceOzellikleri}>
        <div className="sb-logo" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div className="nm">🌱 Filizyol</div>
            <div className="su">Kendi yolunu filizlendir</div>
          </div>
          <TemaAnahtari sabit={false} />
        </div>
        <OkulRozeti />
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
          {acik('bildirimler') && !menu.mobil && <BildirimZili kapsam="ogrenci" />}
          <button className="back" onClick={cikisYap} title="Çıkış yap">Çıkış</button>
        </div>
        {ozet?.sonraki_tur_tarihi && (
          <div style={{ padding: '10px 18px', borderBottom: '1px solid var(--bor)', fontSize: 11, color: 'var(--tx2)' }}>
            Sonraki tur: <b>{new Date(ozet.sonraki_tur_tarihi).toLocaleDateString('tr-TR')}</b>
          </div>
        )}
        {/* [2026-10-10] Sade menü: test bir kez çözülür, menüde yalnızca gerektiğinde görünür.
            Sonuç sayfaları "Bölümler" ve "Profilim" altında sekmelere toplandı. */}
        {degerlendirmeGoster && (
          <NavLink to="/katmanlar" className={({ isActive }) => `ni ni-vurgu${isActive ? ' active' : ''}`}>
            📝 {ozet?.tur_tamamlandi_mi ? 'Yeni Değerlendirme' : 'Değerlendirme'}
            {degerlendirmeYuzde !== null && <span className="ni-rozet">%{degerlendirmeYuzde}</span>}
          </NavLink>
        )}
        <NavLink to="/" end className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🏠 Ana Sayfa
        </NavLink>
        {/* [2026-10-17] Menü: önce sistemin ana işi (bölüm uyumu + hedef bölümle karşılaştırma / koçluk) belirgin grupta,
            diğer modüller "Ek araçlar" altında, okul modülleri "Okul" altında. */}
        <div className="ns ns-ana">Bölüm uyumu ve koçluk</div>
        <NavLink to="/bolumler" className={({ isActive }) => `ni ni-ana${isActive ? ' active' : ''}`}>
          🌟 Bölümler
        </NavLink>
        {acik('kocluk') && (<>
          <NavLink to="/koclugu" className={({ isActive }) => `ni ni-ana${isActive && !karsilastirmaAcik ? ' active' : ''}`}>
            🎯 Koçluğum
          </NavLink>
          <NavLink to="/koclugu?sekme=karsilastirma" className={() => `ni ni-alt${karsilastirmaAcik ? ' active' : ''}`}>
            📊 Sen ve Bölümün
          </NavLink>
        </>)}
        <NavLink to="/profilim" className={({ isActive }) => `ni ni-ana${isActive ? ' active' : ''}`}>
          🧭 Profilim
        </NavLink>
        {/* [2026-10-11] "Karşılaştır" menüden kaldırıldı: Bölümler sayfasındaki "Karşılaştır" sekmesinde (/bolumler/karsilastir) */}
        {['is_hayati', 'tercih', 'portfolyo', 'ogrenci_raporlari', 'calisma', 'net_takibi', 'kocluk', 'kutuphane', 'filiz'].some(acik) && <div className="ns">Ek araçlar</div>}
        {acik('is_hayati') && (
          <NavLink to="/is-hayati" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            💼 İş Hayatı
          </NavLink>
        )}
        {acik('tercih') && ['12. Sınıf', 'Mezun'].includes(profil?.sinif) && (
          <NavLink to="/tercih" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            🎓 Tercihlerim
          </NavLink>
        )}
        {acik('kocluk') && (
          <NavLink to="/gorevler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            ✅ Görevlerim
          </NavLink>
        )}
        {acik('calisma') && (
          <NavLink to="/calisma" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            ⏱️ Çalışmam
          </NavLink>
        )}
        {acik('net_takibi') && (
          <NavLink to="/netlerim" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            📈 Net Takibi
          </NavLink>
        )}
        {acik('kutuphane') && (
          <NavLink to="/kutuphane" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            📚 Kütüphanem
          </NavLink>
        )}
        {acik('portfolyo') && (
          <NavLink to="/portfolyo" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            🗂️ Portfolyom
          </NavLink>
        )}
        {acik('ogrenci_raporlari') && (
          <NavLink to="/raporlarim" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            📄 Raporlarım
          </NavLink>
        )}
        {acik('filiz') && (<>
        {/* [2026-10-04] Filiz sohbet paneli her sayfadan açılır */}
        <div className="ni" role="button" tabIndex={0} style={{ cursor: 'pointer' }}
          data-tur="filiz"
          onClick={() => window.dispatchEvent(new CustomEvent('filiz-ac'))}
          onKeyDown={(e) => { if (e.key === 'Enter') window.dispatchEvent(new CustomEvent('filiz-ac')) }}>
          💬 Filiz
        </div>
        </>)}
        {(['takvim', 'kulupler', 'anketler'].some(acik) || (kocVar && acik('egitim_koclari'))) && <div className="ns">Okul</div>}
        {acik('takvim') && (
        <NavLink to="/takvim" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            🗓️ Takvim
          </NavLink>
        )}
        {acik('anketler') && (
          <NavLink to="/anketler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            📋 Anketler{bekleyenAnket > 0 && <span className="ni-rozet">{bekleyenAnket}</span>}
          </NavLink>
        )}
        {acik('kulupler') && (
        <NavLink to="/kulupler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            🎭 Kulüplerim
          </NavLink>
        )}
        {kocVar && acik('egitim_koclari') && (
          <NavLink to="/koclar" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            👩‍🏫 Eğitim Koçları
          </NavLink>
        )}
        <div style={{ flex: 1 }} />
        <NavLink to="/sozluk" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          📖 Sözlük
        </NavLink>
        <NavLink to="/hakkinda" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          ℹ️ Sistem Hakkında
        </NavLink>
        <NavLink to="/profil" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          ⚙️ Ayarlar
        </NavLink>
      </div>
      <div className="main ogrenci-main">
        {/* [2026-10-09] Maskot ana içerik alanının sağ üstünde, başlık satırında durur (sayfayla birlikte kayar) */}
        {!kvkkGerekli && !tanitimAcik && profil && <Maskot profil={profil} ozet={ozet} />}
        <div className="main-icerik">
          {kapaliModul ? <PaketteYok ad={MODUL_ADI[kapaliModul]} /> : <Outlet context={{ profilYenile, tanitimiAc }} />}
        </div>
        <AltSerit okul={profil?.okul} kisi={profil?.ad_soyad} rol={[profil?.sinif, profil?.sube].filter(Boolean).join(' ') || null} />
      </div>
      {sifreGerekli && (
        <IlkSifrePenceresi kaydet={(s) => api.ilkSifreBelirle(s)} onCikis={cikisYap}
          onTamam={() => setProfil((p) => ({ ...p, sifre_degistirmeli: false }))} />
      )}
      {!sifreGerekli && kvkkGerekli && <KvkkOnayPenceresi onTamam={() => setKvkkGerekli(false)} onCikis={cikisYap} />}
      {!sifreGerekli && !kvkkGerekli && tanitimAcik && !acilis && <TanitimTuru kapsam="ogrenci" onBitir={tanitimiBitir} />}
      {acilis && profilYuklendi && <AcilisAmblemi ad={profil?.ad_soyad?.trim().split(/\s+/)[0]} okulAd={profil?.okul} onBitti={acilisBitti} />}
      {!kvkkGerekli && !tanitimAcik && profil && acik('filiz') && <FilizSohbet />}
      {acik('kocluk') && <SimulasyonKatmani />}
      <SozlukPenceresi filizVar={!kvkkGerekli && !tanitimAcik && !!profil && acik('filiz')} />
      {profil && !kvkkGerekli && <CevrimiciPanel kapsam="ogrenci" />}
    </div>
  )
}
