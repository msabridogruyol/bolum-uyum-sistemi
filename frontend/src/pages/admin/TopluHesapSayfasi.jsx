// [2026-11-11] Süper admin › Toplu Hesap ve Hoş Geldin.
// 1) Excel ile toplu hesap: Ad Soyad · E-posta · Görev · Okul (· Sınıf · Şube). Görev "Öğrenci" → öğrenci hesabı, başka görev →
//    okul yetkilisi (görev unvan olur). Dosya → satır satır önizleme → hesaplar açılır → Filizyol markalı giriş bilgileri Excel'i
//    otomatik iner; istenirse herkese hoş geldin e-postası gider.
// 2) Hoş geldin e-postası: seçilen okulun tamamına tek tuşla (components/yonetim/HosgeldinKarti.jsx).
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { base64Indir } from '../../components/yonetim/ortak'
import HosgeldinKarti, { EpostaOnizleme, GonderimIlerlemesi } from '../../components/yonetim/HosgeldinKarti'
import Secim from '../../components/Secim'

function dosyayiOku(dosya) {
  return new Promise((coz, reddet) => {
    const r = new FileReader()
    r.onload = () => coz(String(r.result).split(',')[1] || '')
    r.onerror = () => reddet(new Error('Dosya okunamadı.'))
    r.readAsDataURL(dosya)
  })
}

const TUR_AD = { ogrenci: 'Öğrenci', yetkili: 'Okul yetkilisi' }

export default function TopluHesapSayfasi() {
  const [okullar, setOkullar] = useState([])
  const [okulId, setOkulId] = useState('')
  const [dosya, setDosya] = useState(null)          // {dosya_adi, icerik_base64}
  const [onizleme, setOnizleme] = useState(null)    // {satirlar, ozet}
  const [eposta, setEposta] = useState(true)
  const [sonuc, setSonuc] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [epostaOrnek, setEpostaOrnek] = useState(null)
  const [hgOkul, setHgOkul] = useState('')

  useEffect(() => { api.yonetimOkullar().then((l) => setOkullar((Array.isArray(l) ? l : []).filter((o) => o.id > 0))).catch(() => {}) }, [])

  const onizle = useCallback(async (d, okul) => {
    setBekle(true); setHata(null)
    try { setOnizleme(await api.topluHesapOnizle({ ...d, okul_id: okul ? Number(okul) : null })) } catch (e) {
      setOnizleme(null); setHata(e.detail || e.message || 'Dosya okunamadı.')
    } finally { setBekle(false) }
  }, [])

  async function dosyaSecildi(e) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    setSonuc(null)
    try {
      const d = { dosya_adi: f.name, icerik_base64: await dosyayiOku(f) }
      setDosya(d)
      onizle(d, okulId)
    } catch (err) { setHata(err.message) }
  }

  function okulDegisti(v) {
    setOkulId(v)
    if (dosya) onizle(dosya, v)
  }

  async function sablonIndir() {
    try { const s = await api.topluHesapSablonu(); base64Indir(s.dosya_adi, s.icerik_base64) } catch (e) { setHata(e.detail || 'Şablon indirilemedi.') }
  }

  async function olustur() {
    setBekle(true); setHata(null)
    try {
      const r = await api.topluHesapOlustur({ ...dosya, okul_id: okulId ? Number(okulId) : null, eposta_gonder: eposta })
      setSonuc(r)
      base64Indir(r.dosya_adi, r.icerik_base64)   // şifreler kaybolmasın diye otomatik indir
      setOnizleme(null); setDosya(null)
    } catch (e) { setHata(e.detail || 'Hesaplar açılamadı.') } finally { setBekle(false) }
  }

  const oz = onizleme?.ozet
  const acilacak = oz ? oz.acilacak_ogrenci + oz.acilacak_yetkili : 0

  return (
    <div className="pg pg-genis">
      <div className="ph">
      <div className="pt">Toplu Hesap ve Hoş Geldin</div>
      <div className="ps">Excel'den öğrenci ve okul yetkilisi hesabı açın, geçici şifreleri Filizyol markalı Excel olarak alın, okullara tek tuşla hoş geldin e-postası gönderin.</div>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="yp-kb">📄 Excel ile toplu hesap aç</div>
        <ol className="yp-adimlar">
          <li>Şablonu indirin; her satıra bir kişi yazın: <b>Ad Soyad, E-posta, Görev, Okul</b> (öğrenciler için isteğe bağlı Sınıf, Şube).</li>
          <li>Görev <b>“Öğrenci”</b> ise öğrenci hesabı; başka bir görev (Rehber Öğretmen, Müdür Yardımcısı…) yazılırsa <b>okul yetkilisi</b> hesabı açılır.</li>
          <li>Okul sütunu boşsa aşağıda seçtiğiniz okul kullanılır. Dosyayı yükleyince her satır kontrol edilir; onaylayınca hesaplar açılır ve geçici şifreler Excel olarak iner.</li>
        </ol>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <button className="btn sec" onClick={sablonIndir}>⬇ Şablonu indir</button>
          <Secim className="yp-sec" value={okulId} onChange={(e) => okulDegisti(e.target.value)} aria-label="Varsayılan okul">
            <option value="">Okul sütunundan (varsayılan okul yok)</option>
            {okullar.map((o) => <option key={o.id} value={o.id}>{o.ad}</option>)}
          </Secim>
          <label className="btn" style={{ cursor: 'pointer' }}>
            {bekle && !onizleme ? <span className="spin" /> : 'Dosya yükle (.xlsx / .csv)'}
            <input type="file" accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv" onChange={dosyaSecildi} style={{ display: 'none' }} />
          </label>
        </div>
        {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}

        {onizleme && (
          <div style={{ marginTop: 14 }}>
            <div className="yp-ozet-satir">
              <span><b>{oz.toplam}</b> satır · {dosya?.dosya_adi}</span>
              <span className="yp-d-yesil yp-durum">{oz.acilacak_ogrenci} öğrenci</span>
              <span className="yp-d-yesil yp-durum">{oz.acilacak_yetkili} okul yetkilisi</span>
              {oz.kayitli > 0 && <span className="yp-d-mor yp-durum">{oz.kayitli} zaten kayıtlı</span>}
              {oz.hatali > 0 && <span className="yp-d-kirmizi yp-durum">{oz.hatali} hatalı</span>}
              {oz.okullar.length > 0 && <span className="yp-ince">Okullar: {oz.okullar.join(', ')}</span>}
            </div>
            <div className="yp-tablo-kap" style={{ maxHeight: 420 }}>
              <table className="yp-tablo">
                <thead><tr><th>#</th><th>Ad Soyad</th><th>Hesap</th><th>Okul</th><th>Sınıf</th><th>E-posta</th><th>Kontrol</th></tr></thead>
                <tbody>
                  {onizleme.satirlar.map((s) => (
                    <tr key={s.satir} className={s.hata ? 'yp-satir-hata' : ''}>
                      <td className="yp-ince">{s.satir}</td>
                      <td>{s.ad_soyad || '—'}</td>
                      <td>{TUR_AD[s.tur]}{s.unvan && <div className="yp-ince">{s.unvan}</div>}</td>
                      <td>{s.okul_ad || '—'}</td>
                      <td>{s.tur === 'ogrenci' ? [s.sinif, s.sube].filter(Boolean).join(' / ') || '—' : ''}</td>
                      <td className="yp-ince">{s.email || '—'}</td>
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
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center', marginTop: 12 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}>
                <input type="checkbox" checked={eposta} onChange={(e) => setEposta(e.target.checked)} />
                Açılan hesaplara hoş geldin e-postası gönder (giriş bilgileriyle)
              </label>
              <button className="yp-mini" onClick={() => setEpostaOrnek('ogrenci')}>öğrenci örneği</button>
              <button className="yp-mini" onClick={() => setEpostaOrnek('yetkili')}>yetkili örneği</button>
              <div style={{ flex: 1 }} />
              <button className="btn sec" onClick={() => { setOnizleme(null); setDosya(null) }}>Vazgeç</button>
              <button className="btn" disabled={!acilacak || bekle} onClick={olustur}>
                {bekle ? <span className="spin" /> : `${acilacak} hesabı aç`}
              </button>
            </div>
          </div>
        )}

        {sonuc && (
          <div style={{ marginTop: 14 }}>
            <div className="yp-uyari-yesil">
              ✓ <b>{sonuc.olusturulan}</b> hesap açıldı ({sonuc.ozet.acilacak_ogrenci} öğrenci, {sonuc.ozet.acilacak_yetkili} okul yetkilisi).
              Giriş bilgileri Excel'i indirildi.{' '}
              <button className="yp-mini" onClick={() => base64Indir(sonuc.dosya_adi, sonuc.icerik_base64)}>⬇ Tekrar indir</button>
            </div>
            {sonuc.atlanan.length > 0 && (
              <div className="yp-ince" style={{ marginTop: 6 }}>
                {sonuc.atlanan.length} satır atlandı: {sonuc.atlanan.slice(0, 6).map((s) => `${s.ad_soyad || s.email} (${s.hata || s.uyari})`).join(', ')}{sonuc.atlanan.length > 6 ? '…' : ''}
              </div>
            )}
            {sonuc.eposta_is_id && <div style={{ marginTop: 10 }}><GonderimIlerlemesi isId={sonuc.eposta_is_id} /></div>}
            <div className="yp-ince" style={{ marginTop: 8 }}>Excel dosyası şifre içerir: yalnızca ilgili kişilere iletin, iş bitince silin.</div>
          </div>
        )}
      </div>

      <div className="card">
        <div className="yp-kb">✉ Okulun tamamına hoş geldin e-postası</div>
        <div style={{ margin: '6px 0 12px' }}>
          <Secim className="yp-sec" value={hgOkul} onChange={(e) => setHgOkul(e.target.value)} aria-label="Okul">
            <option value="">Okul seçin…</option>
            {okullar.map((o) => <option key={o.id} value={o.id}>{o.ad}</option>)}
          </Secim>
        </div>
        {hgOkul ? <HosgeldinKarti key={hgOkul} okulId={Number(hgOkul)} baslik={false} /> : <div className="yp-ince">Önce okulu seçin; öğrenci ve yetkili sayıları ile gönderim seçenekleri görünür.</div>}
      </div>

      {epostaOrnek && <EpostaOnizleme tur={epostaOrnek} okulId={okulId ? Number(okulId) : null} onKapat={() => setEpostaOrnek(null)} />}
    </div>
  )
}
