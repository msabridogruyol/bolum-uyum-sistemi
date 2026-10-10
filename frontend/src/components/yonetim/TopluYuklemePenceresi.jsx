// [2026-10-09] Excel/CSV ile toplu öğrenci hesabı açma: dosya → önizleme (satır satır kontrol) → oluştur → geçici şifreler
import { useState } from 'react'
import { api } from '../../api/client'
import { Pencere, SifreListesi, base64Indir } from './ortak'

function dosyayiOku(dosya) {
  return new Promise((coz, reddet) => {
    const r = new FileReader()
    r.onload = () => coz(String(r.result).split(',')[1] || '')
    r.onerror = () => reddet(new Error('Dosya okunamadı.'))
    r.readAsDataURL(dosya)
  })
}

export default function TopluYuklemePenceresi({ okulId, okulAd, onKapat, onBitti }) {
  const [adim, setAdim] = useState('dosya')     // dosya | onizleme | sonuc
  const [satirlar, setSatirlar] = useState([])
  const [sonuc, setSonuc] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [tekForm, setTekForm] = useState({ ad_soyad: '', sinif: '', sube: '', email: '' })

  async function sablonIndir() {
    try { const s = await api.yuklemeSablonu(); base64Indir(s.dosya_adi, s.icerik_base64) } catch (e) { setHata(e.detail || 'Şablon indirilemedi.') }
  }

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    e.target.value = ''
    if (!dosya) return
    setBekle(true); setHata(null)
    try {
      const r = await api.ogrenciDosyasiOnizle(okulId, dosya.name, await dosyayiOku(dosya))
      setSatirlar(r.satirlar)
      setAdim('onizleme')
    } catch (err) {
      setHata(err.detail || err.message || 'Dosya okunamadı.')
    } finally { setBekle(false) }
  }

  async function olustur(liste) {
    setBekle(true); setHata(null)
    try {
      const r = await api.ogrencileriOlustur(okulId, liste.map(({ ad_soyad, email, sinif, sube, sifre, ogrenci_no }) => ({ ad_soyad, email, sinif, sube, sifre: sifre || null, ogrenci_no: ogrenci_no || null })))
      if (!r.olusturulan.length) {
        setHata(r.hatali.map((h) => `${h.ad_soyad || h.email}: ${h.hata}`).join(' · ') || 'Hesap açılamadı.')
        return
      }
      setSonuc(r)
      setAdim('sonuc')
      if (r.icerik_base64) base64Indir(r.dosya_adi, r.icerik_base64)  // şifreler kaybolmasın diye otomatik indir
      onBitti?.()
    } catch (err) {
      setHata(err.detail || 'Hesaplar oluşturulamadı.')
    } finally { setBekle(false) }
  }

  const gecerli = satirlar.filter((s) => !s.hata)
  const hatali = satirlar.length - gecerli.length

  return (
    <Pencere
      genis
      baslik={adim === 'sonuc' ? `${sonuc.olusturulan.length} hesap açıldı` : 'Öğrenci hesabı aç'}
      altBaslik={okulAd}
      onKapat={adim === 'sonuc' || !bekle ? onKapat : undefined}
      alt={adim === 'onizleme' ? (
        <>
          <button className="btn sec" onClick={() => { setAdim('dosya'); setSatirlar([]) }}>← Başka dosya</button>
          <div style={{ flex: 1 }} />
          {hatali > 0 && <span style={{ fontSize: 12, color: 'var(--re)' }}>{hatali} hatalı satır atlanacak</span>}
          <button className="btn" disabled={!gecerli.length || bekle} onClick={() => olustur(gecerli)}>
            {bekle ? <span className="spin" /> : `${gecerli.length} hesabı oluştur`}
          </button>
        </>
      ) : adim === 'sonuc' ? <button className="btn" onClick={onKapat}>Kapat</button> : null}
    >
      {hata && <div className="auth-error">{hata}</div>}

      {adim === 'dosya' && (
        <div className="yp-iki">
          <div className="yp-kutu">
            <div className="yp-kb">📄 Excel ile toplu</div>
            <ol className="yp-adimlar">
              <li>Şablonu indirin, her satıra bir öğrenci yazın (Ad Soyad, Sınıf, Şube, E-posta).</li>
              <li>Dosyayı yükleyin; sistem her satırı kontrol edip önizleme gösterir.</li>
              <li>Onaylayınca hesaplar açılır ve geçici şifreler Excel olarak iner.</li>
            </ol>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button className="btn sec" onClick={sablonIndir}>⬇ Şablonu indir</button>
              <label className="btn" style={{ cursor: 'pointer' }}>
                {bekle ? <span className="spin" /> : 'Dosya yükle (.xlsx / .csv)'}
                <input type="file" accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv" onChange={dosyaSecildi} style={{ display: 'none' }} />
              </label>
            </div>
            <div className="yp-ince" style={{ marginTop: 10 }}>E-posta zorunlu: öğrenci bu adresle giriş yapar ve doğrulama kodu bu adrese gider.</div>
          </div>
          <form className="yp-kutu" onSubmit={(e) => { e.preventDefault(); olustur([tekForm]) }}>
            <div className="yp-kb">👤 Tek öğrenci</div>
            <input className="auth-input" placeholder="Ad Soyad" value={tekForm.ad_soyad} onChange={(e) => setTekForm({ ...tekForm, ad_soyad: e.target.value })} required minLength={3} />
            <div style={{ display: 'flex', gap: 8, margin: '8px 0' }}>
              <select className="auth-input" value={tekForm.sinif} onChange={(e) => setTekForm({ ...tekForm, sinif: e.target.value })}>
                <option value="">Sınıf…</option>
                {['9', '10', '11', '12', 'Mezun'].map((s) => <option key={s} value={s}>{s === 'Mezun' ? s : `${s}. Sınıf`}</option>)}
              </select>
              <input className="auth-input" style={{ width: 90 }} placeholder="Şube" maxLength={2} value={tekForm.sube} onChange={(e) => setTekForm({ ...tekForm, sube: e.target.value })} />
            </div>
            <input className="auth-input" type="email" placeholder="E-posta" value={tekForm.email} onChange={(e) => setTekForm({ ...tekForm, email: e.target.value })} required />
            <button className="btn" style={{ marginTop: 10 }} type="submit" disabled={bekle}>{bekle ? <span className="spin" /> : 'Hesabı aç'}</button>
          </form>
        </div>
      )}

      {adim === 'onizleme' && (
        <>
          <div className="yp-ozet-satir">
            <span><b>{satirlar.length}</b> satır okundu</span>
            <span className="yp-d-yesil yp-durum">{gecerli.length} hazır</span>
            {hatali > 0 && <span className="yp-d-kirmizi yp-durum">{hatali} hatalı</span>}
          </div>
          <div className="yp-tablo-kap" style={{ maxHeight: 420 }}>
            <table className="yp-tablo">
              <thead><tr><th>#</th><th>Ad Soyad</th><th>No</th><th>Sınıf</th><th>Şube</th><th>E-posta</th><th>Şifre</th><th>Kontrol</th></tr></thead>
              <tbody>
                {satirlar.map((s) => (
                  <tr key={s.satir} className={s.hata ? 'yp-satir-hata' : ''}>
                    <td className="yp-ince">{s.satir}</td>
                    <td>{s.ad_soyad || '—'}{s.guncelle && <span className="yp-durum yp-d-mor" style={{ marginLeft: 6 }}>güncelleme</span>}</td>
                    <td className="yp-ince">{s.ogrenci_no || '—'}</td>
                    <td>{s.sinif || '—'}</td>
                    <td>{s.sube || '—'}</td>
                    <td className="yp-ince">{s.email || '—'}</td>
                    <td className="yp-ince">{s.sifre ? '••••••' : (s.guncelle ? 'değişmez' : 'otomatik')}</td>
                    <td style={{ fontSize: 11.5 }}>
                      {s.hata ? <span style={{ color: 'var(--re)' }}>✕ {s.hata}</span>
                        : s.uyari ? <span style={{ color: 'var(--am)' }}>⚠ {s.uyari}</span>
                          : <span style={{ color: 'var(--gr)' }}>✓</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {adim === 'sonuc' && (
        <>
          {sonuc.hatali.length > 0 && (
            <div className="auth-error">{sonuc.hatali.length} satır atlandı: {sonuc.hatali.slice(0, 5).map((h) => `${h.ad_soyad || h.email} (${h.hata})`).join(', ')}</div>
          )}
          <SifreListesi kayitlar={sonuc.olusturulan} dosya={sonuc} aciklama="Dosya otomatik indirildi; inmediyse aşağıdaki düğmeyi kullanın." />
        </>
      )}
    </Pencere>
  )
}
