// [2026-10-09] Okullar (süper admin) — okul kaydı (ad + amblem) ve her okulun paneline geçiş.
// Öğrenci hesapları, okul yetkilileri, istatistik ve kayıtlar okulun panelinden yönetilir (OkulPaneliSayfasi).
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'

const BOS_FORM = { id: null, ad: '', alt_baslik: '', logo: null, aktif_mi: true }
const LOGO_PIKSEL = 256          // raster amblemler bu boyuta küçültülür
const SVG_EN_FAZLA = 300_000     // SVG dosyaları olduğu gibi saklanır

// Seçilen görseli tarayıcıda küçültüp data URL'e çevirir (PNG; şeffaflık korunur)
function amblemiHazirla(dosya) {
  return new Promise((coz, reddet) => {
    if (!/^image\/(png|jpe?g|webp|svg\+xml)$/.test(dosya.type)) {
      reddet(new Error('Yalnızca PNG, JPEG, WEBP veya SVG yükleyebilirsiniz.'))
      return
    }
    const okuyucu = new FileReader()
    okuyucu.onerror = () => reddet(new Error('Dosya okunamadı.'))
    if (dosya.type === 'image/svg+xml') {
      if (dosya.size > SVG_EN_FAZLA) { reddet(new Error('SVG dosyası çok büyük (en fazla 300 KB).')); return }
      okuyucu.onload = () => coz(okuyucu.result)
      okuyucu.readAsDataURL(dosya)
      return
    }
    okuyucu.onload = () => {
      const img = new Image()
      img.onerror = () => reddet(new Error('Görsel açılamadı.'))
      img.onload = () => {
        const oran = Math.min(1, LOGO_PIKSEL / Math.max(img.width, img.height))
        const tuval = document.createElement('canvas')
        tuval.width = Math.max(1, Math.round(img.width * oran))
        tuval.height = Math.max(1, Math.round(img.height * oran))
        tuval.getContext('2d').drawImage(img, 0, 0, tuval.width, tuval.height)
        coz(tuval.toDataURL('image/png'))
      }
      img.src = okuyucu.result
    }
    okuyucu.readAsDataURL(dosya)
  })
}

function Onizleme({ ad, alt_baslik, logo }) {
  return (
    <div className="okul-rozeti" style={{ margin: 0, maxWidth: 240, background: 'var(--sur)' }}>
      {logo
        ? <img src={logo} alt="" className="okul-amblem" />
        : <div className="okul-amblem okul-amblem-bos">🏫</div>}
      <div style={{ minWidth: 0 }}>
        <div className="okul-ad">{ad || 'Okul adı'}</div>
        {alt_baslik && <div className="okul-alt">{alt_baslik}</div>}
      </div>
    </div>
  )
}

export default function OkullarSayfasi() {
  const [okullar, setOkullar] = useState(null)
  const [haric, setHaric] = useState(0)
  const [form, setForm] = useState(null)          // null = form kapalı
  const [silme, setSilme] = useState(null)        // { okul, hedef }
  const [hata, setHata] = useState(null)
  const [bilgi, setBilgi] = useState(null)
  const [isleniyor, setIsleniyor] = useState(false)

  function yukle() {
    api.okullariListele().then(setOkullar).catch((e) => setHata(e.detail || 'Okullar yüklenemedi.'))
    api.yonetimOkullar().then((l) => setHaric(l.find((x) => x.id === 0)?.ogrenci_sayisi || 0)).catch(() => {})
  }
  useEffect(yukle, [])

  function mesaj(m) { setBilgi(m); setHata(null); setTimeout(() => setBilgi(null), 3500) }

  async function amblemSecildi(e) {
    const dosya = e.target.files?.[0]
    e.target.value = ''
    if (!dosya) return
    try { setForm((f) => ({ ...f, logo: null })); const logo = await amblemiHazirla(dosya); setForm((f) => ({ ...f, logo })) }
    catch (err) { setHata(err.message) }
  }

  async function kaydet(e) {
    e.preventDefault()
    if (!form.ad.trim()) { setHata('Okul adı boş olamaz.'); return }
    setIsleniyor(true); setHata(null)
    try {
      const veri = { ad: form.ad, alt_baslik: form.alt_baslik, logo: form.logo ?? '', aktif_mi: form.aktif_mi }
      if (form.id) await api.okulGuncelle(form.id, veri)
      else await api.okulEkle(veri)
      setForm(null); yukle(); mesaj('Kaydedildi.')
    } catch (err) { setHata(err.detail || 'Kaydedilemedi.') } finally { setIsleniyor(false) }
  }

  async function sil() {
    setIsleniyor(true); setHata(null)
    try {
      await api.okulSil(silme.okul.id, silme.okul.ogrenci_sayisi ? Number(silme.hedef) : undefined)
      setSilme(null); yukle(); mesaj(`"${silme.okul.ad}" silindi.`)
    } catch (err) { setHata(err.detail || 'Silinemedi.') } finally { setIsleniyor(false) }
  }

  return (
    <div className="pg pg-genis">
      <div className="ph" style={{ display: 'flex', alignItems: 'flex-end', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <div className="pt">Okullar</div>
          <div className="ps">
            Her okulun öğrenci hesapları, okul yetkilileri, istatistikleri ve kayıtları kendi panelinden yönetilir.
            Öğrenciler sol menüde kendi okullarının amblemini görür.
          </div>
        </div>
        {!form && <button className="btn" onClick={() => { setForm({ ...BOS_FORM }); setHata(null) }}>+ Yeni Okul</button>}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {bilgi && <div className="card" style={{ background: 'var(--grl)', borderColor: 'var(--gr)', padding: '12px 16px', fontSize: 13 }}>{bilgi}</div>}

      {form && (
        <form className="card" onSubmit={kaydet}>
          <div className="ct">{form.id ? 'Okulu Düzenle' : 'Yeni Okul'}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 18, alignItems: 'start' }}>
            <div>
              <label className="auth-label">Okul adı</label>
              <input className="auth-input" style={{ width: '100%' }} value={form.ad} maxLength={80}
                     onChange={(e) => setForm({ ...form, ad: e.target.value })} placeholder="Örn: Atatürk Anadolu Lisesi" required />
              <label className="auth-label" style={{ marginTop: 12 }}>Alt başlık (isteğe bağlı)</label>
              <input className="auth-input" style={{ width: '100%' }} value={form.alt_baslik || ''} maxLength={40}
                     onChange={(e) => setForm({ ...form, alt_baslik: e.target.value })} placeholder="Örn: iş birliğiyle" />
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 14, fontSize: 13, cursor: 'pointer' }}>
                <input type="checkbox" checked={!!form.aktif_mi} onChange={(e) => setForm({ ...form, aktif_mi: e.target.checked })} />
                Amblemi bu okulun öğrencilerine göster
              </label>
            </div>
            <div>
              <label className="auth-label">Amblem</label>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                <label className="btn sec" style={{ cursor: 'pointer' }}>
                  {form.logo ? 'Amblemi değiştir' : 'Amblem yükle'}
                  <input type="file" accept="image/png,image/jpeg,image/webp,image/svg+xml" onChange={amblemSecildi} style={{ display: 'none' }} />
                </label>
                {form.logo && <button type="button" className="btn sec" onClick={() => setForm({ ...form, logo: null })}>Amblemi kaldır</button>}
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginBottom: 12 }}>
                PNG, JPEG, WEBP veya SVG. Şeffaf arka planlı kare görseller en iyi sonucu verir; büyük görseller otomatik küçültülür.
              </div>
              <label className="auth-label">Önizleme (öğrencinin sol menüsünde)</label>
              <Onizleme {...form} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 18 }}>
            <button className="btn" type="submit" disabled={isleniyor}>{isleniyor ? <span className="spin" /> : 'Kaydet'}</button>
            <button className="btn sec" type="button" onClick={() => setForm(null)}>İptal</button>
          </div>
        </form>
      )}

      {!okullar ? <div className="bos-durum">Yükleniyor…</div> : (
        <div className="yp-okul-grid">
          {okullar.map((o) => (
            <div key={o.id} className="yp-okul-kart">
              <Link to={`/admin/okul/${o.id}`} className="yp-okul-kart-ust">
                {o.logo ? <img src={o.logo} alt="" className="yp-okul-logo" /> : <div className="yp-okul-logo yp-okul-logo-bos">🏫</div>}
                <div style={{ minWidth: 0 }}>
                  <div className="lt">{o.ad}</div>
                  <div className="yp-ince">{o.alt_baslik || (o.aktif_mi ? 'Amblem gösteriliyor' : 'Amblem gizli')}</div>
                </div>
              </Link>
              <div className="yp-okul-sayilar">
                <div><b>{o.ogrenci_sayisi}</b><span>öğrenci</span></div>
                <div><b>{o.yetkili_sayisi}</b><span>okul yetkilisi</span></div>
                {/* [2026-10-10] Paket — tıklayınca okulun Paket bölümü */}
                <Link to={`/admin/okul/${o.id}?sekme=paket`} className="pk-okul-rozet" title="Paketi değiştir"><b>📦 {o.paket_ad || '—'}</b><span>paket</span></Link>
              </div>
              {silme?.okul.id === o.id ? (
                <div className="yp-okul-sil">
                  {o.ogrenci_sayisi > 0 ? (
                    <>
                      <span>{o.ogrenci_sayisi} öğrenci şuraya aktarılsın:</span>
                      <select className="yp-sec" value={silme.hedef} onChange={(e) => setSilme({ ...silme, hedef: e.target.value })}>
                        <option value={0}>Okul harici</option>
                        {okullar.filter((x) => x.id !== o.id).map((x) => <option key={x.id} value={x.id}>{x.ad}</option>)}
                      </select>
                    </>
                  ) : <span>Okul silinsin mi?</span>}
                  {o.yetkili_sayisi > 0 && <span style={{ color: 'var(--re)' }}>{o.yetkili_sayisi} okul yetkilisi hesabı da silinir.</span>}
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn yp-tehlike" disabled={isleniyor} onClick={sil}>Sil</button>
                    <button className="btn sec" onClick={() => setSilme(null)}>Vazgeç</button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="yp-okul-kisayol">
                    <Link to={`/admin/okul/${o.id}?sekme=bilgiler`}>📝 Okul bilgileri</Link>
                    <Link to={`/admin/okul/${o.id}?sekme=yetkililer`}>👤 Okul yetkilisi ekle</Link>
                    <Link to={`/admin/okul/${o.id}?sekme=ogrenciler`}>🎒 Öğrenci hesapları</Link>
                  </div>
                  <div className="yp-okul-aksiyon">
                    <Link to={`/admin/okul/${o.id}`} className="btn">Paneli aç →</Link>
                    <button className="btn sec" onClick={() => { setForm({ ...o }); setHata(null); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>Ad / amblem</button>
                    <button className="yp-mini" title="Sil" onClick={() => setSilme({ okul: o, hedef: 0 })}>🗑</button>
                  </div>
                </>
              )}
            </div>
          ))}
          <div className="yp-okul-kart yp-okul-kart-haric">
            <Link to="/admin/okul/0" className="yp-okul-kart-ust">
              <div className="yp-okul-logo yp-okul-logo-bos">👤</div>
              <div><div className="lt">Okul harici öğrenciler</div><div className="yp-ince">Bir okula bağlı olmayan bireysel hesaplar (yalnızca süper admin)</div></div>
            </Link>
            <div className="yp-okul-sayilar"><div><b>{haric}</b><span>öğrenci</span></div></div>
            <div className="yp-okul-aksiyon"><Link to="/admin/okul/0" className="btn">Paneli aç →</Link></div>
          </div>
        </div>
      )}
    </div>
  )
}
