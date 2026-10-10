import { useCallback, useEffect, useState } from 'react'
import { NavLink, Outlet, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import TemaAnahtari from './TemaAnahtari'
import TanitimPenceresi from './TanitimPenceresi'
import Maskot from './Maskot'
import OkulRozeti from './OkulRozeti'
import FilizSohbet from './FilizSohbet'
import AltSerit from './AltSerit'
import { KvkkOnayPenceresi } from './KvkkBilesenleri'
import { IlkSifrePenceresi } from './yonetim/ortak'

// [2026-10-03] İlk giriş akışı: tanıtım penceresi → profil (ad + sınıf zorunlu) → ana sayfa
// [2026-10-09] Okul öğrenciden alınmaz; yönetimdeki Okullar sayfasından atanır.
export const profilEksikMi = (p) => !p || !p.ad_soyad?.trim() || !p.sinif?.trim()
const tanitimAnahtari = (p) => `tanitim_goruldu_${p?.email || 'misafir'}`
function tanitimGorulduMu(p) {
  try { return localStorage.getItem(tanitimAnahtari(p)) === '1' } catch { return true }
}

export default function AnaSayfaDuzeni() {
  const { cikisYap } = useAuth()
  const [ozet, setOzet] = useState(null)
  const [profil, setProfil] = useState(null)
  const [kocVar, setKocVar] = useState(false)   // [2026-10-10] okulunda aktif koç yoksa menüde gösterilmez
  const [profilYuklendi, setProfilYuklendi] = useState(false)
  const [tanitimAcik, setTanitimAcik] = useState(false)
  const [kvkkGerekli, setKvkkGerekli] = useState(false) // [2026-10-04] eski hesap veya yeni metin sürümü
  const konum = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    if (konum.pathname.startsWith('/katmanlar')) api.durumOzetiGetir().then(setOzet).catch(() => {})
    api.kvkkDurumu().then((d) => setKvkkGerekli(!d.guncel)).catch(() => {})
    api.kocVarMi().then((d) => setKocVar(!!d.var)).catch(() => {})
    api.profilGetir()
      .then((p) => { setProfil(p); if (!tanitimGorulduMu(p)) setTanitimAcik(true) })
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
  const tanitimiAc = useCallback(() => setTanitimAcik(true), [])

  function tanitimiBitir() {
    try { localStorage.setItem(tanitimAnahtari(profil), '1') } catch { /* gizli sekme vb. */ }
    setTanitimAcik(false)
    // [2026-10-10] İlk girişte (tanıtımdan sonra) öğrenci her zaman profil sayfasına gelir: bilgilerini kontrol eder, fotoğraf/ilgi alanı ekler
    navigate('/profil?ilk=1')
  }

  // Profil tamamlanmadan diğer sayfalara geçilmez (tanıtım açıkken yönlendirme beklenir)
  const profilSayfasinda = konum.pathname.startsWith('/profil')
  // [2026-10-09] Okulun açtığı hesap geçici şifreyle başlar: önce öğrenci kendi şifresini belirler
  const sifreGerekli = !!profil?.sifre_degistirmeli
  if (profilYuklendi && profil && !sifreGerekli && !tanitimAcik && !kvkkGerekli && profilEksikMi(profil) && !profilSayfasinda) {
    return <Navigate to="/profil?ilk=1" replace />
  }

  const ilkAd = profil?.ad_soyad?.trim().split(/\s+/)[0] || 'Öğrenci'
  // Değerlendirme menüde yalnızca bitmemişse (K1-K4 veya açılan K5 dalları) ya da 90 günlük yeni tur zamanı geldiyse görünür
  const k5Bekliyor = !!ozet && ozet.k5_acilan_dal_sayisi > ozet.k5_tamamlanan_dal_sayisi
  const yeniTurHazir = !!ozet?.sonraki_tur_tarihi && new Date(ozet.sonraki_tur_tarihi) <= new Date()
  const degerlendirmeGoster = !ozet || !ozet.tur_tamamlandi_mi || k5Bekliyor || yeniTurHazir
  const degerlendirmeYuzde = ozet && !ozet.tur_tamamlandi_mi && ozet.toplam_ana_katman_sayisi
    ? Math.round((ozet.tamamlanan_katman_sayisi / ozet.toplam_ana_katman_sayisi) * 100) : null

  return (
    <div className="app">
      <div className="sb">
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
        <NavLink to="/koclugu" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🎯 Koçluğum
        </NavLink>
        <NavLink to="/bolumler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🌟 Bölümler
        </NavLink>
        <NavLink to="/profilim" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🧭 Profilim
        </NavLink>
        <NavLink to="/gorevler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          ✅ Görevlerim
        </NavLink>
        <NavLink to="/takvim" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🗓️ Takvim
        </NavLink>
        <NavLink to="/kulupler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          🎯 Kulüplerim
        </NavLink>
        <NavLink to="/kutuphane" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
          📚 Kütüphanem
        </NavLink>
        {kocVar && (
          <NavLink to="/koclar" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>
            👩‍🏫 Eğitim Koçları
          </NavLink>
        )}
        {/* [2026-10-04] Filiz sohbet paneli her sayfadan açılır */}
        <div className="ni" role="button" tabIndex={0} style={{ cursor: 'pointer' }}
          onClick={() => window.dispatchEvent(new CustomEvent('filiz-ac'))}
          onKeyDown={(e) => { if (e.key === 'Enter') window.dispatchEvent(new CustomEvent('filiz-ac')) }}>
          💬 Filiz
        </div>
        <div style={{ flex: 1 }} />
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
        <div className="main-icerik"><Outlet context={{ profilYenile, tanitimiAc }} /></div>
        <AltSerit okul={profil?.okul} kisi={profil?.ad_soyad} rol={[profil?.sinif, profil?.sube].filter(Boolean).join(' ') || null} />
      </div>
      {sifreGerekli && (
        <IlkSifrePenceresi kaydet={(s) => api.ilkSifreBelirle(s)} onCikis={cikisYap}
          onTamam={() => setProfil((p) => ({ ...p, sifre_degistirmeli: false }))} />
      )}
      {!sifreGerekli && kvkkGerekli && <KvkkOnayPenceresi onTamam={() => setKvkkGerekli(false)} onCikis={cikisYap} />}
      {!sifreGerekli && !kvkkGerekli && tanitimAcik && <TanitimPenceresi onBitir={tanitimiBitir} />}
      {!kvkkGerekli && !tanitimAcik && profil && <FilizSohbet />}
    </div>
  )
}
