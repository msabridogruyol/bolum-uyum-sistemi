// [2026-10-10] Okul denemeleri: Excel şablonu indir → doldur → önizle → kaydet; deneme sonuçları, şube ve ders ortalamaları.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere, base64Indir } from './ortak'

const SINIFLAR = ['9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf', 'Mezun']
const OTURUM_RENK = { TYT: 'var(--kt-izleme, #2a78d6)', AYT: 'var(--kt-kitap, #eb6834)', YDT: 'var(--kt-kurs, #1baf7a)' }
const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const tarihMetni = (t) => { const d = new Date(`${t}T12:00`); return `${d.getDate()} ${AY[d.getMonth()]} ${d.getFullYear()}` }
const n2 = (v) => (v == null ? '—' : Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 2 }))

function dosyayiOku(dosya) {
  return new Promise((coz, reddet) => {
    const r = new FileReader()
    r.onload = () => coz(String(r.result).split(',')[1] || '')
    r.onerror = () => reddet(new Error('Dosya okunamadı.'))
    r.readAsDataURL(dosya)
  })
}

// ----------------------------------------------------------------------------- yükleme sihirbazı
function Yukleme({ okulId, onBitti, onVazgec }) {
  const [oturum, setOturum] = useState('TYT')
  const [sinif, setSinif] = useState('12. Sınıf')
  const [ad, setAd] = useState('')
  const [tarih, setTarih] = useState(new Date().toISOString().slice(0, 10))
  const [dosya, setDosya] = useState(null)        // { ad, b64 }
  const [onizleme, setOnizleme] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)

  async function sablon() {
    setHata(null)
    try { const s = await api.denemeSablonu(okulId, oturum, sinif); base64Indir(s.dosya_adi, s.icerik_base64) } catch (e) { setHata(e.detail || 'Şablon indirilemedi.') }
  }
  async function sec(e) {
    const f = e.target.files?.[0]; e.target.value = ''
    if (!f) return
    setBekle(true); setHata(null); setOnizleme(null)
    try {
      const b64 = await dosyayiOku(f)
      setDosya({ ad: f.name, b64 })
      setOnizleme(await api.denemeOnizle(okulId, { oturum, dosya_adi: f.name, icerik_base64: b64 }))
    } catch (er) { setHata(er.detail || er.message || 'Dosya okunamadı.') } finally { setBekle(false) }
  }
  async function kaydet() {
    setBekle(true); setHata(null)
    try {
      const r = await api.okulDenemesiKaydet(okulId, { ad, tarih, oturum, dosya_adi: dosya.ad, icerik_base64: dosya.b64 })
      onBitti(r)
    } catch (er) { setHata(er.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  const oz = onizleme?.ozet
  return (
    <div className="card">
      <div className="ct">Yeni okul denemesi yükle</div>
      <div className="od-adimlar">
        <div className="od-adim">
          <div className="od-no">1</div>
          <div style={{ flex: 1 }}>
            <b>Şablonu indir</b>
            <div className="yp-ince">Öğrencileriniz şablonda hazır gelir; her ders için doğru ve yanlış sayısını yazın ya da yayınevi dosyanızdan kopyalayın.</div>
            <div className="od-satir">
              <div className="od-secim" role="radiogroup" aria-label="Oturum">
                {['TYT', 'AYT', 'YDT'].map((o) => (
                  <button key={o} type="button" className={oturum === o ? 'secili' : ''} onClick={() => { setOturum(o); setOnizleme(null); setDosya(null) }}
                    style={oturum === o ? { borderColor: OTURUM_RENK[o] } : undefined}>{o}</button>
                ))}
              </div>
              <select className="auth-input" style={{ width: 'auto' }} value={sinif} onChange={(e) => setSinif(e.target.value)}>
                {SINIFLAR.map((s) => <option key={s}>{s}</option>)}
                <option value="">Tüm okul</option>
              </select>
              <button className="btn sec" type="button" onClick={sablon}>📥 {oturum} şablonunu indir</button>
            </div>
          </div>
        </div>
        <div className="od-adim">
          <div className="od-no">2</div>
          <div style={{ flex: 1 }}>
            <b>Denemeyi adlandır ve dosyayı yükle</b>
            <div className="od-satir">
              <input className="auth-input" style={{ maxWidth: 280 }} maxLength={80} placeholder="Deneme adı (ör. 3D Yayınları TYT-2)" value={ad} onChange={(e) => setAd(e.target.value)} />
              <input className="auth-input" style={{ width: 'auto' }} type="date" value={tarih} onChange={(e) => setTarih(e.target.value)} />
              <label className="btn sec" style={{ cursor: 'pointer' }}>
                {bekle && !onizleme ? <span className="spin" /> : '📤 Dosya seç (.xlsx)'}
                <input type="file" accept=".xlsx,.xlsm,.csv" hidden onChange={sec} />
              </label>
              {dosya && <span className="yp-ince">{dosya.ad}</span>}
            </div>
          </div>
        </div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {onizleme && (
        <>
          <div className="od-ozet">
            <span><b>{oz.gecerli}</b> öğrenci kaydedilecek</span>
            {oz.hatali > 0 && <span className="kirmizi"><b>{oz.hatali}</b> satırda hata (atlanır)</span>}
            {oz.bos > 0 && <span><b>{oz.bos}</b> öğrenci sınava girmemiş</span>}
            {oz.ortalama != null && <span>Ortalama <b>{n2(oz.ortalama)}</b> net</span>}
            <span className="yp-ince">Tanınan dersler: {onizleme.taninan_dersler.join(', ')}</span>
          </div>
          <div className="od-tablo-kap">
            <table className="yp-tablo">
              <thead><tr><th>Satır</th><th>Öğrenci</th><th>Sınıf</th>{onizleme.testler.map((t) => <th key={t.kod}>{t.ad}</th>)}<th>Toplam</th><th>Durum</th></tr></thead>
              <tbody>
                {onizleme.satirlar.map((s) => (
                  <tr key={s.satir} className={s.hata ? 'od-hatali' : s.bos ? 'od-bos' : ''}>
                    <td className="yp-ince">{s.satir}</td>
                    <td>{s.eslesen_ad || s.ad_soyad || '—'}{s.ogrenci_no && <span className="yp-ince"> · {s.ogrenci_no}</span>}</td>
                    <td>{s.sinif_metni || '—'}</td>
                    {onizleme.testler.map((t) => <td key={t.kod}>{s.dersler[t.kod] ? n2(s.dersler[t.kod].net) : ''}</td>)}
                    <td><b>{s.bos ? '' : n2(s.toplam_net)}</b></td>
                    <td className="od-durum">{s.hata ? <span className="kirmizi">✕ {s.hata}</span> : s.bos ? <span className="yp-ince">Girmedi</span> : <span className="yesil">✓</span>}{s.uyari && !s.bos && <div className="yp-ince">{s.uyari}</div>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
        <button className="btn" disabled={bekle || !onizleme || !oz?.gecerli || ad.trim().length < 2} onClick={kaydet}>
          {bekle && onizleme ? <span className="spin" /> : `✓ ${oz?.gecerli || 0} öğrencinin sonucunu kaydet`}
        </button>
        <button className="btn sec" onClick={onVazgec}>Vazgeç</button>
        {onizleme && ad.trim().length < 2 && <span className="yp-ince" style={{ alignSelf: 'center' }}>Kaydetmek için deneme adını yazın.</span>}
      </div>
    </div>
  )
}

// ----------------------------------------------------------------------------- deneme detayı
function DenemeDetayi({ id, onKapat, onSilindi }) {
  const [v, setV] = useState(null)
  const [silOnay, setSilOnay] = useState(false)
  const [hata, setHata] = useState(null)
  useEffect(() => { api.okulDenemesi(id).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [id])
  async function sil() { try { await api.okulDenemesiSil(id); onSilindi() } catch (e) { setHata(e.detail || 'Silinemedi.') } }
  if (!v) return <Pencere baslik="Deneme" onKapat={onKapat}><div className="bos-durum">{hata || 'Yükleniyor…'}</div></Pencere>
  const d = v.deneme
  const enCok = Math.max(1, ...v.subeler.map((s) => s.ortalama || 0))
  return (
    <Pencere genis baslik={`${d.oturum} · ${d.ad}`} altBaslik={`${tarihMetni(d.tarih)} · ${v.okul.katilim} öğrenci · okul ortalaması ${n2(v.okul.ortalama)} net`} onKapat={onKapat}
      alt={silOnay
        ? <><span className="yp-ince" style={{ marginRight: 'auto' }}>Deneme ve öğrencilerin Net Takibi'ne düşen sonuçları silinecek.</span><button className="btn sec" onClick={() => setSilOnay(false)}>Vazgeç</button><button className="btn yp-tehlike" onClick={sil}>Evet, sil</button></>
        : <><button className="btn sec" style={{ marginRight: 'auto' }} onClick={() => setSilOnay(true)}>🗑 Denemeyi sil</button><button className="btn" onClick={onKapat}>Kapat</button></>}>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="yp-iki" style={{ marginBottom: 14 }}>
        <div className="yp-kutu">
          <div className="ct">Ders ortalamaları (okul)</div>
          {v.testler.map((t) => {
            const o = v.okul.dersler[t.kod]
            return o == null ? null : (
              <div key={t.kod} className="od-cubuk-satir">
                <span>{t.ad}</span>
                <div className="nt-cubuk"><div style={{ width: `${Math.max(2, (100 * o) / t.soru)}%`, background: OTURUM_RENK[d.oturum] }} /></div>
                <b>{n2(o)}</b><span className="yp-ince">/ {t.soru}</span>
              </div>
            )
          })}
        </div>
        <div className="yp-kutu">
          <div className="ct">Şube ortalamaları</div>
          {v.subeler.map((s) => (
            <div key={s.sube} className="od-cubuk-satir">
              <span>{s.sube} <small className="yp-ince">({s.katilim})</small></span>
              <div className="nt-cubuk"><div style={{ width: `${Math.max(2, (100 * (s.ortalama || 0)) / enCok)}%`, background: OTURUM_RENK[d.oturum] }} /></div>
              <b>{n2(s.ortalama)}</b><span />
            </div>
          ))}
        </div>
      </div>
      <div className="od-tablo-kap">
        <table className="yp-tablo">
          <thead><tr><th>#</th><th>Öğrenci</th><th>Sınıf</th>{v.testler.map((t) => <th key={t.kod}>{t.ad}</th>)}<th>Toplam</th></tr></thead>
          <tbody>
            {v.sonuclar.map((s) => (
              <tr key={s.ogrenci_id}>
                <td className="yp-ince">{s.sira}</td><td>{s.ad_soyad}</td><td>{s.sinif_metni}</td>
                {v.testler.map((t) => <td key={t.kod}>{n2(s.dersler[t.kod])}</td>)}
                <td><b>{n2(s.toplam_net)}</b></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Pencere>
  )
}

// ----------------------------------------------------------------------------- bölüm
export default function OkulDenemeleri({ okulId }) {
  const [v, setV] = useState(null)
  const [yukle, setYukle] = useState(false)
  const [detay, setDetay] = useState(null)
  const [bilgi, setBilgi] = useState(null)
  const [hata, setHata] = useState(null)
  const yenile = useCallback(() => api.okulDenemeleri(okulId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [okulId])
  useEffect(() => { yenile() }, [yenile])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  return (
    <>
      <div className="yp-ince" style={{ marginBottom: 12, lineHeight: 1.6 }}>
        Okulun yaptığı denemelerin sonuçlarını tek seferde yükleyin. Sonuçlar her öğrencinin <b>Net Takibi</b> ekranına “Okul denemesi” olarak düşer;
        öğrenci kendi netini okul ortalamasıyla karşılaştırır ve bu denemeyi silemez.
      </div>
      {bilgi && <div className="yp-basari" style={{ marginBottom: 12 }}>✓ {bilgi}</div>}
      {yukle
        ? <Yukleme okulId={okulId} onVazgec={() => setYukle(false)} onBitti={(r) => { setYukle(false); setBilgi(`${r.kaydedilen} öğrencinin sonucu kaydedildi${r.atlanan ? `, ${r.atlanan} satır atlandı` : ''}.`); yenile() }} />
        : <button className="btn" style={{ marginBottom: 14 }} onClick={() => { setYukle(true); setBilgi(null) }}>📤 Yeni deneme yükle</button>}
      <div className="card">
        <div className="ct">Yüklenen denemeler</div>
        {v.denemeler.length === 0 ? <div className="bos-durum">Henüz okul denemesi yüklenmedi.</div> : (
          <table className="yp-tablo">
            <thead><tr><th>Tarih</th><th>Deneme</th><th>Katılım</th><th>Ortalama</th><th>En yüksek</th><th>Yükleyen</th><th /></tr></thead>
            <tbody>
              {v.denemeler.map((d) => (
                <tr key={d.id}>
                  <td>{tarihMetni(d.tarih)}</td>
                  <td><span className="nt-oturum" style={{ color: OTURUM_RENK[d.oturum] }}>{d.oturum}</span> {d.ad}</td>
                  <td>{d.katilim}</td><td><b>{n2(d.ortalama)}</b></td><td>{n2(d.en_yuksek)}</td>
                  <td className="yp-ince">{d.olusturan}</td>
                  <td><button className="yp-mini" onClick={() => setDetay(d.id)}>Sonuçlar →</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {detay && <DenemeDetayi id={detay} onKapat={() => setDetay(null)} onSilindi={() => { setDetay(null); yenile() }} />}
    </>
  )
}
