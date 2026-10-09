// [2026-10-09] Okullar — öğrenci sayfalarının sol menüsünde gösterilen okul adı + amblemi.
// Birden fazla okul kaydedilebilir; aynı anda yalnızca biri "gösterilen" olur.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

const BOS_FORM = { id: null, ad: '', alt_baslik: 'iş birliğiyle', logo: null, aktif_mi: true }
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
  const [form, setForm] = useState(null)          // null = form kapalı
  const [hata, setHata] = useState(null)
  const [bilgi, setBilgi] = useState(null)
  const [isleniyor, setIsleniyor] = useState(false)

  function yukle() {
    api.okullariListele().then(setOkullar).catch((e) => setHata(e.detail || 'Okullar yüklenemedi.'))
  }
  useEffect(yukle, [])

  function mesaj(m) { setBilgi(m); setHata(null); setTimeout(() => setBilgi(null), 3500) }

  async function amblemSecildi(e) {
    const dosya = e.target.files?.[0]
    e.target.value = ''
    if (!dosya) return
    try {
      const logo = await amblemiHazirla(dosya)
      setForm((f) => ({ ...f, logo }))
    } catch (err) {
      setHata(err.message)
    }
  }

  async function kaydet(e) {
    e.preventDefault()
    if (!form.ad.trim()) { setHata('Okul adı boş olamaz.'); return }
    setIsleniyor(true); setHata(null)
    try {
      const veri = { ad: form.ad, alt_baslik: form.alt_baslik, logo: form.logo ?? '', aktif_mi: form.aktif_mi }
      if (form.id) await api.okulGuncelle(form.id, veri)
      else await api.okulEkle(veri)
      setForm(null)
      yukle()
      mesaj('Kaydedildi. Öğrenciler sayfayı yenilediğinde yeni hali görür.')
    } catch (err) {
      setHata(err.detail || 'Kaydedilemedi.')
    } finally {
      setIsleniyor(false)
    }
  }

  async function goster(o) {
    try { await api.okulAktifYap(o.id); yukle(); mesaj(`"${o.ad}" artık öğrenci sayfalarında gösteriliyor.`) }
    catch (err) { setHata(err.detail || 'İşlem başarısız.') }
  }

  async function hicbiriniGosterme() {
    try { await api.okulGizle(); yukle(); mesaj('Öğrenci sayfalarında okul gösterilmiyor.') }
    catch (err) { setHata(err.detail || 'İşlem başarısız.') }
  }

  async function sil(o) {
    if (!window.confirm(`"${o.ad}" kalıcı olarak silinsin mi?`)) return
    try { await api.okulSil(o.id); yukle(); mesaj('Okul silindi.') }
    catch (err) { setHata(err.detail || 'Silinemedi.') }
  }

  const gosterilen = okullar?.find((o) => o.aktif_mi)

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Okullar</div>
        <div className="ps">
          Öğrenci sayfalarının sol menüsünde görünen okul adı ve amblemi. Birden fazla okul kaydedebilirsiniz;
          aynı anda yalnızca biri gösterilir.
        </div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {bilgi && <div className="card" style={{ background: 'var(--grl)', borderColor: 'var(--gr)', padding: '12px 16px', fontSize: 13 }}>{bilgi}</div>}

      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 220 }}>
          <div className="ct" style={{ marginBottom: 4 }}>Şu an gösterilen</div>
          <div style={{ fontSize: 12.5, color: 'var(--tx2)' }}>
            {gosterilen ? 'Öğrenciler sol menüde bunu görüyor.' : 'Hiçbir okul gösterilmiyor.'}
          </div>
        </div>
        {gosterilen && <Onizleme {...gosterilen} />}
        <div style={{ display: 'flex', gap: 8 }}>
          {!form && <button className="btn" onClick={() => { setForm({ ...BOS_FORM }); setHata(null) }}>+ Yeni Okul</button>}
          {gosterilen && <button className="btn sec" onClick={hicbiriniGosterme}>Okul gösterme</button>}
        </div>
      </div>

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
                Öğrenci sayfalarında bu okulu göster
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
              <label className="auth-label">Önizleme (sol menüde böyle görünür)</label>
              <Onizleme {...form} />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 18 }}>
            <button className="btn" type="submit" disabled={isleniyor}>{isleniyor ? <span className="spin" /> : 'Kaydet'}</button>
            <button className="btn sec" type="button" onClick={() => setForm(null)}>İptal</button>
          </div>
        </form>
      )}

      <div className="ct" style={{ marginTop: 20 }}>Kayıtlı Okullar</div>
      {!okullar ? (
        <div className="bos-durum">Yükleniyor…</div>
      ) : okullar.length === 0 ? (
        <div className="bos-durum">Henüz okul eklenmedi.</div>
      ) : (
        <div className="ll">
          {okullar.map((o) => (
            <div key={o.id} className="lc" style={{ cursor: 'default' }}>
              {o.logo
                ? <img src={o.logo} alt="" className="okul-amblem" />
                : <div className="okul-amblem okul-amblem-bos">🏫</div>}
              <div className="lb-wrap" style={{ flex: 1 }}>
                <div className="lt">{o.ad}</div>
                <div className="ld">{o.alt_baslik || '—'}</div>
                {o.aktif_mi && <span className="bdg bdg-done">Gösteriliyor</span>}
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {!o.aktif_mi && <button className="btn" onClick={() => goster(o)}>Göster</button>}
                <button className="btn sec" onClick={() => { setForm({ ...o }); setHata(null); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>Düzenle</button>
                <button className="btn sec" onClick={() => sil(o)}>Sil</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
