import { useEffect, useState, useRef, useCallback } from 'react'
import { AD_SOYAD_EN_FAZLA } from '../yardimci/sinirlar'
import DilSecici from '../components/DilSecici'   // [2026-10-12] çoklu dil
import { useNavigate, useOutletContext, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import OneriKutusu from '../components/OneriKutusu'
import SifreDegistirFormu from '../components/SifreDegistirFormu'
import { profilEksikMi } from '../components/AnaSayfaDuzeni'
import { GizlilikKarti } from '../components/KvkkBilesenleri'
import HedefBolumAyari from '../components/HedefBolumAyari'
import Secim from '../components/Secim'   // [2026-11-11] uzun açılır listeler yazarak aranır

// [2026-10-11] Çevrim içi görünürlük: okulundaki öğrencilerin sağ alttaki listesinde adın görünsün mü
function CevrimiciAyari() {
  const [gizli, setGizli] = useState(null)
  const [goster, setGoster] = useState(false)   // [2026-11-11] okul öğrencilerde çevrim içi listesini açmadıysa ayar gizli
  useEffect(() => { api.cevrimiciBuradayim().then((v) => { setGizli(!!v.gizli); setGoster(v.goster !== false) }).catch(() => {}) }, [])
  if (gizli === null || !goster) return null
  return (
    <div className="card" style={{ marginTop: 20 }}>
      <div className="ct">Çevrim İçi Görünürlük</div>
      <label style={{ display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13.5, cursor: 'pointer', lineHeight: 1.5 }}>
        <input type="checkbox" checked={!gizli} style={{ marginTop: 3 }}
          onChange={(e) => { const yeni = !e.target.checked; setGizli(yeni); api.cevrimiciGizlilik(yeni).catch(() => setGizli(!yeni)) }} />
        <span>
          Çevrim içiyken okulumdaki öğrencilerin listesinde görüneyim.
          <span style={{ display: 'block', fontSize: 12, color: 'var(--tx3)' }}>Yalnızca adın, soyadının baş harfi ve sınıfın görünür. Kapatırsan kimsenin listesinde görünmezsin.</span>
        </span>
      </label>
    </div>
  )
}

const CINSIYET_SECENEKLERI = [
  { deger: '', etiket: 'Belirtilmedi' },
  { deger: 'kadin', etiket: 'Kadın' },
  { deger: 'erkek', etiket: 'Erkek' },
  { deger: 'diger', etiket: 'Diğer' },
  { deger: 'belirtmek_istemiyorum', etiket: 'Belirtmek istemiyorum' },
]

export default function ProfilAyarlariSayfasi() {
  const [profil, setProfil] = useState(null)
  const [taslak, setTaslak] = useState(null)
  const [hata, setHata] = useState(null)
  const [basari, setBasari] = useState(null)
  const [kaydediliyor, setKaydediliyor] = useState(false)

  const [mesleklAramaMetni, setMesleklAramaMetni] = useState('')
  const [meslekSonuclari, setMeslekSonuclari] = useState(null)


  const fotoInputRef = useRef(null)
  const [fotoYukleniyor, setFotoYukleniyor] = useState(false)

  // [2026-10-03] İlk giriş akışı (?ilk=1): kaydedince ana sayfaya geçilir
  const [params] = useSearchParams()
  const ilkGiris = params.get('ilk') === '1'
  const navigate = useNavigate()
  const duzen = useOutletContext() || {}

  useEffect(() => {
    api.profilGetir().then((p) => { setProfil(p); setTaslak(p) }).catch((e) => setHata(e.detail || 'Profil yüklenemedi.'))
  }, [])

  function alanGuncelle(alan, deger) {
    setTaslak((t) => ({ ...t, [alan]: deger }))
  }

  async function kaydet(e) {
    e.preventDefault()
    setHata(null)
    setBasari(null)
    if (!profil?.okul && !taslak.sinif?.trim()) {
      setHata('Devam etmek için sınıfını seçmelisin.')
      return
    }
    setKaydediliyor(true)
    try {
      const guncellenmis = await api.profilGuncelle({
        ad_soyad: taslak.ad_soyad,
        sinif: taslak.sinif || null,
        dogum_tarihi: taslak.dogum_tarihi || null,
        cinsiyet: taslak.cinsiyet || null,
        ilgi_alanlari: taslak.ilgi_alanlari || null,
        hedef_universite: taslak.hedef_universite || null,
        hedef_meslek_id: taslak.hedef_meslek_id ?? null,
      })
      setProfil(guncellenmis)
      setTaslak(guncellenmis)
      duzen.profilYenile?.(guncellenmis)
      if (ilkGiris && !profilEksikMi(guncellenmis)) {
        navigate('/', { replace: true })
        return
      }
      setBasari('Profil bilgilerin kaydedildi.')
    } catch (err) {
      setHata(err.detail || 'Kaydedilemedi.')
    } finally {
      setKaydediliyor(false)
    }
  }

  async function meslekAra(e) {
    e.preventDefault()
    if (mesleklAramaMetni.trim().length < 2) return
    try {
      setMeslekSonuclari(await api.meslekAra(mesleklAramaMetni.trim()))
    } catch (err) {
      setHata(err.detail || 'Meslek aranamadı.')
    }
  }

  // [2026-11-11] yazarken öneri: sunucudaki meslek araması (200 ms bekleyerek)
  const meslekOnerisi = useCallback((q) => api.meslekAra(q).then((l) => (l || []).map((m) => ({ id: m.id, ad: m.ad }))), [])

  function meslekSec(meslek) {
    setTaslak((t) => ({ ...t, hedef_meslek_id: meslek.id, hedef_meslek_adi: meslek.ad }))
    setMeslekSonuclari(null)
    setMesleklAramaMetni('')
  }

  async function fotoSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    if (dosya.size > 2_000_000) {
      setHata('Fotoğraf çok büyük. En fazla 2 MB olabilir.')
      return
    }
    setFotoYukleniyor(true)
    setHata(null)
    try {
      const base64 = await new Promise((resolve, reject) => {
        const okuyucu = new FileReader()
        okuyucu.onload = () => resolve(okuyucu.result)
        okuyucu.onerror = () => reject(new Error('Dosya okunamadı.'))
        okuyucu.readAsDataURL(dosya)
      })
      const guncellenmis = await api.profilFotografiGuncelle(base64)
      setProfil(guncellenmis)
      setTaslak(guncellenmis)
      setBasari('Profil fotoğrafın güncellendi.')
    } catch (err) {
      setHata(err.detail || 'Fotoğraf yüklenemedi.')
    } finally {
      setFotoYukleniyor(false)
      if (fotoInputRef.current) fotoInputRef.current.value = ''
    }
  }

  if (hata && !profil) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!taslak) return <div className="pg"><div className="bos-durum yukleniyor">Yükleniyor…</div></div>

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Ayarlar</div>
        <div className="ps">Profilini, hedeflerini ve hesap güvenliğini buradan yönet.</div>
      </div>

      {(ilkGiris || profilEksikMi(profil)) && (
        <div className="card" style={{ borderColor: 'var(--pu)', background: 'var(--pul)' }}>
          <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4 }}>👋 Başlamadan önce profilini tamamla</div>
          <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5 }}>
            Ad soyadını ve sınıfını yaz, sonra <b>Kaydet</b> düğmesine bas. Ardından ana sayfadan ilk boyuta başlayabilirsin. Diğer alanları doldurmak zorunda değilsin.
          </div>
        </div>
      )}

      {hata && <div className="auth-error">{hata}</div>}
      {basari && <div style={{ background: 'var(--grl)', color: 'var(--gr)', fontSize: 12.5, fontWeight: 600, padding: '10px 13px', borderRadius: 8, marginBottom: 14 }}>{basari}</div>}

      {/* --- Fotoğraf --- */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
        <div className="av" style={{ width: 64, height: 64, fontSize: 28, overflow: 'hidden', flexShrink: 0 }}>
          {taslak.profil_foto_base64
            ? <img src={taslak.profil_foto_base64} alt="Profil" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : '🎓'}
        </div>
        <div style={{ flex: '1 1 140px', minWidth: 0 }}>
          <div style={{ fontSize: 15, fontWeight: 700 }}>{taslak.ad_soyad}</div>
          <div style={{ fontSize: 12.5, color: 'var(--tx2)', overflowWrap: 'anywhere' }}>{taslak.email}</div>
        </div>
        <label className="btn sec" style={{ cursor: fotoYukleniyor ? 'not-allowed' : 'pointer', opacity: fotoYukleniyor ? 0.6 : 1 }}>
          {fotoYukleniyor ? 'Yükleniyor...' : 'Fotoğraf Değiştir'}
          <input ref={fotoInputRef} type="file" accept="image/*" onChange={fotoSecildi} disabled={fotoYukleniyor} style={{ display: 'none' }} />
        </label>
      </div>

      {/* [2026-10-09] Hedef bölüm seçimi/değişikliği yalnızca burada (en fazla 3 değişiklik) */}
      {!ilkGiris && <HedefBolumAyari />}

      {/* --- Kişisel Bilgiler --- */}
      <form onSubmit={kaydet} className="profil-form">
        <div className="card">
          <div className="ct">Kişisel Bilgiler</div>

          <div className="auth-field">
            <label className="auth-label">Ad Soyad <span style={{ color: 'var(--re)' }}>*</span></label>
            <input maxLength={AD_SOYAD_EN_FAZLA} className="auth-input" value={taslak.ad_soyad} onChange={(e) => alanGuncelle('ad_soyad', e.target.value)} required minLength={2} />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Okul</label>
              {/* [2026-10-09] Okul yönetimden atanır; öğrenci değiştiremez */}
              <div className="auth-input okul-sabit" title="Okul bilgisini okulun girer, sen değiştiremezsin.">
                {profil?.okul || 'Okula bağlı değil (bireysel hesap)'}
              </div>
            </div>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Sınıf <span style={{ color: 'var(--re)' }}>*</span></label>
              {/* [2026-10-11] Okula bağlı öğrencinin sınıfını okul belirler (yanlış sınıf seçilirse raporlar ve şube listeleri bozulur) */}
              {profil?.okul ? (
                <div className="auth-input okul-sabit" title="Sınıfını okulun belirler. Yanlışsa rehber öğretmenine söyle.">
                  {[profil?.sinif, profil?.sube].filter(Boolean).join(' / ') || 'Okulun henüz girmedi'}
                </div>
              ) : (
                <Secim className="auth-input" value={taslak.sinif || ''} onChange={(e) => alanGuncelle('sinif', e.target.value)} required>
                  <option value="">Seç…</option>
                  {['9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf', 'Mezun'].concat(taslak.sinif && !['9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf', 'Mezun'].includes(taslak.sinif) ? [taslak.sinif] : []).map((s) => <option key={s} value={s}>{s}</option>)}
                </Secim>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Doğum Tarihi <span style={{ color: 'var(--tx3)', fontWeight: 500 }}>(isteğe bağlı)</span></label>
              <input className="auth-input" type="date" value={taslak.dogum_tarihi || ''} onChange={(e) => alanGuncelle('dogum_tarihi', e.target.value)} />
            </div>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Cinsiyet <span style={{ color: 'var(--tx3)', fontWeight: 500 }}>(isteğe bağlı)</span></label>
              <Secim className="auth-input" value={taslak.cinsiyet || ''} onChange={(e) => alanGuncelle('cinsiyet', e.target.value)}>
                {CINSIYET_SECENEKLERI.map((c) => <option key={c.deger} value={c.deger}>{c.etiket}</option>)}
              </Secim>
            </div>
          </div>

          <div className="auth-field">
            <label className="auth-label">Sevdiğin Şeyler / İlgi Alanların</label>
            <textarea
              className="auth-input"
              style={{ minHeight: 60, resize: 'vertical', fontFamily: 'var(--fn)' }}
              value={taslak.ilgi_alanlari || ''}
              maxLength={1000}
              onChange={(e) => alanGuncelle('ilgi_alanlari', e.target.value)}
              placeholder="Örn. resim yapmayı, satranç oynamayı ve bilim kurgu okumayı severim..."
            />
          </div>
        </div>

        {/* --- Hedefler --- */}
        <div className="card">
          <div className="ct">Hedeflerin</div>

          <div className="auth-field">
            <label className="auth-label">Hedef Üniversite <span style={{ color: 'var(--tx3)', fontWeight: 500 }}>(isteğe bağlı)</span></label>
            <input className="auth-input" value={taslak.hedef_universite || ''} onChange={(e) => alanGuncelle('hedef_universite', e.target.value)} placeholder="Örn. Boğaziçi Üniversitesi" />
          </div>

          <div className="auth-field">
            <label className="auth-label">Hedef Meslek</label>
            {taslak.hedef_meslek_adi && (
              <div className="bdg bdg-prog" style={{ marginBottom: 8, display: 'inline-flex' }}>
                {taslak.hedef_meslek_adi}
                <button type="button" onClick={() => alanGuncelle('hedef_meslek_id', null)} style={{ marginLeft: 6, background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}>✕</button>
              </div>
            )}
            <div style={{ display: 'flex', gap: 8 }}>
              <OneriKutusu kapStyle={{ flex: 1 }} value={mesleklAramaMetni} onChange={setMesleklAramaMetni} enAz={2}
                kaynak={meslekOnerisi} onSec={meslekSec} placeholder="Meslek ara... (örn. Yazılım Mühendisi)" />
              <button type="button" className="btn sec" onClick={meslekAra}>Ara</button>
            </div>
            {meslekSonuclari && (
              <div className="ll" style={{ marginTop: 8 }}>
                {meslekSonuclari.length === 0 && <div className="bos-durum" style={{ padding: 12 }}>Sonuç bulunamadı.</div>}
                {meslekSonuclari.map((m) => (
                  <div key={m.id} className="lc" onClick={() => meslekSec(m)}>
                    <div className="lb-wrap"><div className="lt">{m.ad}</div></div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="ps" style={{ margin: '10px 0 0' }}>
            Hedef bölümünü yukarıdaki <b>Hedef bölümüm</b> kartından seç. Gelişim planını <b>Koçluğum</b> sayfasından takip et.
          </div>
        </div>

        <button className="btn" type="submit" disabled={kaydediliyor}>
          {kaydediliyor ? <span className="spin" /> : ilkGiris ? 'Kaydet ve Başla →' : 'Bilgileri Kaydet'}
        </button>
      </form>

      {/* --- Şifre Değiştir --- */}
      <CevrimiciAyari />

      <div className="card" style={{ marginTop: 20 }}>
        <div className="ct">Şifreni Değiştir</div>
        {/* [2026-11-04] eski şifre + e-posta onay kodu */}
        <SifreDegistirFormu degistir={api.sifreDegistir} onayla={api.sifreDegisikliginiOnayla} />
      </div>

      {/* --- [2026-10-04] KVKK: isteğe bağlı izinler --- */}
      <GizlilikKarti />

      {/* --- Dil --- */}
      <DilSecici kapsam="ogrenci" gorunum="kart" />

      {/* --- Tanıtım --- */}
      {duzen.tanitimiAc && (
        <div className="card" style={{ marginTop: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
          <div>
            <div className="ct" style={{ marginBottom: 2 }}>Sistem Tanıtımı</div>
            <div className="ps" style={{ margin: 0, fontSize: 12 }}>Menüleri tek tek tanıtan kısa turu tekrar izle.</div>
          </div>
          <button className="btn sec" type="button" onClick={duzen.tanitimiAc}>Tanıtımı Göster</button>
        </div>
      )}

      {/* --- Hukuki not --- */}
      <div className="ps" style={{ marginTop: 16, color: 'var(--tx3)', fontSize: 11.5 }}>
        Doğum tarihi ve cinsiyet isteğe bağlı. Doldurmak zorunda değilsin.
      </div>
    </div>
  )
}
