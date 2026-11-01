import { useEffect, useState, useCallback } from 'react'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { api } from '../../api/client'

// [DÜZELTME] Artık pipeline çıktıları .xlsx (Türkçe karakter bozulmasını
// önlemek için) — bu yüzden düz CSV metin ayrıştırma yerine SheetJS
// kullanıyoruz, hem .xlsx hem .csv okuyabiliyor.
function dosyayiAyristir(dosya) {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.XLSX) {
      reject(new Error('Okuma kütüphanesi yüklenemedi. Sayfayı yenileyip tekrar deneyin.'))
      return
    }
    const okuyucu = new FileReader()
    okuyucu.onload = (e) => {
      try {
        const csvMi = dosya.name.toLowerCase().endsWith('.csv')
        const wb = window.XLSX.read(e.target.result, { type: csvMi ? 'string' : 'array' })
        const sayfa = wb.Sheets[wb.SheetNames[0]]
        const satirlar = window.XLSX.utils.sheet_to_json(sayfa, { header: 1, defval: '' })
        resolve(satirlar)
      } catch (err) {
        reject(err)
      }
    }
    okuyucu.onerror = () => reject(new Error('Dosya okunamadı.'))
    if (dosya.name.toLowerCase().endsWith('.csv')) okuyucu.readAsText(dosya, 'utf-8')
    else okuyucu.readAsArrayBuffer(dosya)
  })
}

function satirlariDondur(hamSatirlar) {
  const baslik = (hamSatirlar[0] || []).map((h) => String(h).trim())
  const beklenen = ['bolum_adi', 'degisken_kod', 'agirlik_degeri', 'yakinsama_skoru', 'agirlikli_varyans', 'etkin_meslek_sayisi']
  const idx = Object.fromEntries(beklenen.map((k) => [k, baslik.indexOf(k)]))

  return hamSatirlar.slice(1).map((hucreler) => {
    const say = (i) => (i >= 0 ? hucreler[i] : undefined)
    return {
      bolum_adi: String(say(idx.bolum_adi) ?? '').trim(),
      degisken_kod: String(say(idx.degisken_kod) ?? '').trim(),
      agirlik_degeri: parseFloat(say(idx.agirlik_degeri)),
      yakinsama_skoru: idx.yakinsama_skoru >= 0 ? (parseFloat(say(idx.yakinsama_skoru)) || null) : null,
      agirlikli_varyans: idx.agirlikli_varyans >= 0 ? (parseFloat(say(idx.agirlikli_varyans)) || null) : null,
      etkin_meslek_sayisi: idx.etkin_meslek_sayisi >= 0 ? (parseInt(say(idx.etkin_meslek_sayisi), 10) || null) : null,
    }
  }).filter((s) => s.bolum_adi && s.degisken_kod && !isNaN(s.agirlik_degeri))
}

const DURUM_ETIKET = { bekliyor: 'Onay Bekliyor', onaylandi: 'Canlıda', arsiv: 'Önceki sürüm', reddedildi: 'Reddedildi' }
const DURUM_RENK = { bekliyor: 'bdg-prog', onaylandi: 'bdg-done', arsiv: 'bdg-lock', reddedildi: 'bdg-lock' }

// ============================================================
// Meslek Verisi Toplu Yükleme (sonradan eklendi)
// ============================================================
function meslekSatirlariniDondur(hamSatirlar) {
  const baslik = (hamSatirlar[0] || []).map((h) => String(h).trim())
  const beklenen = ['esco_kodu', 'isco_grubu', 'ad', 'aciklama']
  const idx = Object.fromEntries(beklenen.map((k) => [k, baslik.indexOf(k)]))
  if (idx.esco_kodu < 0 || idx.ad < 0) return null  // gerekli sütunlar yok

  return hamSatirlar.slice(1).map((hucreler) => ({
    esco_kodu: String(hucreler[idx.esco_kodu] ?? '').trim(),
    ad: String(hucreler[idx.ad] ?? '').trim(),
    aciklama: idx.aciklama >= 0 ? String(hucreler[idx.aciklama] ?? '').trim() || null : null,
    isco_grubu: idx.isco_grubu >= 0 ? String(hucreler[idx.isco_grubu] ?? '').trim() || null : null,
  })).filter((m) => m.esco_kodu && m.ad)
}

function MeslekYuklemeKarti() {
  const [mevcutSayi, setMevcutSayi] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [sonuc, setSonuc] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.meslekSayisiniGetir().then((v) => setMevcutSayi(v.meslek_sayisi)).catch(() => {})
  }, [sonuc])

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    setHata(null)
    setSonuc(null)
    setYukleniyor(true)
    try {
      const hamSatirlar = await dosyayiAyristir(dosya)  // aynı dosyada üstte tanımlı yardımcı
      const meslekler = meslekSatirlariniDondur(hamSatirlar)
      if (!meslekler || meslekler.length === 0) {
        throw new Error('Dosya okunamadı — sütunları kontrol edin: esco_kodu, ad, aciklama, isco_grubu.')
      }
      if (!window.confirm(
        `${meslekler.length} meslek yüklenecek. Bu işlem MEVCUT meslek listesini tamamen siler ve yeniden doldurur. Devam edilsin mi?`
      )) {
        setYukleniyor(false)
        return
      }
      const cevap = await api.meslekleriTopluYukle(meslekler)
      setSonuc(cevap)
    } catch (err) {
      setHata(err.detail || err.message || 'Yükleme başarısız.')
    } finally {
      setYukleniyor(false)
      e.target.value = ''
    }
  }

  return (
    <div className="card" style={{ borderColor: 'var(--tl)', background: 'var(--tll)' }}>
      <div className="ct">Meslek Verisi Yükle (Hedef Meslek Araması İçin)</div>
      <div className="ps" style={{ margin: '0 0 8px' }}>
        <code>meslekler_esco.csv</code> (ya da .xlsx) dosyasını yükler — öğrencinin profilindeki
        "hedef meslek" arama özelliğinin kullandığı veriyi besler. Mevcut listeyi tamamen değiştirir.
      </div>
      <div className="ps" style={{ margin: '0 0 12px', fontWeight: 600 }}>
        Şu an sistemde: {mevcutSayi === null ? '…' : `${mevcutSayi} meslek`}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <label className="btn" style={{ cursor: yukleniyor ? 'not-allowed' : 'pointer', opacity: yukleniyor ? 0.6 : 1 }}>
        {yukleniyor ? <span className="spin" /> : '⬆ Dosya Seç ve Yükle'}
        <input type="file" accept=".xlsx,.xls,.csv" onChange={dosyaSecildi} disabled={yukleniyor} style={{ display: 'none' }} />
      </label>
      {sonuc && (
        <div style={{ marginTop: 12, fontSize: 13, fontWeight: 700, color: 'var(--gr)' }}>
          ✓ {sonuc.yuklenen_sayisi} meslek yüklendi (önceki: {sonuc.onceki_sayisi}).
        </div>
      )}
    </div>
  )
}


// ============================================================
// [2026-11-01] 2. ve 3. adım: K5 iş türü bağları ve örnek meslekler (önceden Supabase SQL ekranında çalıştırılıyordu).
// Dosya çalıştırılmaz; içindeki değerler okunur → önizleme → "Canlıya al". Önceki hâl yedeklenir, geri dönülebilir.
// ============================================================
function VeriAdimKarti({ no, tur, baslik, dosyaYolu, aciklama }) {
  const [dosyaAdi, setDosyaAdi] = useState(null)
  const [metin, setMetin] = useState(null)
  const [onizleme, setOnizleme] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [onay, setOnay] = useState(false)
  const [hata, setHata] = useState(null)
  const [sonuc, setSonuc] = useState(null)
  const [yedekler, setYedekler] = useState([])
  const [donus, setDonus] = useState(null)

  const yedekleriYukle = useCallback(() => {
    api.veriYuklemeYedekler(tur).then((v) => setYedekler(v.yedekler || [])).catch(() => {})
  }, [tur])
  useEffect(() => { yedekleriYukle() }, [yedekleriYukle])

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    e.target.value = ''
    if (!dosya) return
    setHata(null); setSonuc(null); setOnizleme(null); setOnay(false); setBekle(true)
    try {
      const m = await dosya.text()
      setDosyaAdi(dosya.name); setMetin(m)
      setOnizleme(await api.veriYuklemeOnizle(tur, m, dosya.name))
    } catch (err) {
      setHata(err.detail || err.message || 'Dosya okunamadı.')
    }
    setBekle(false)
  }

  async function canliyaAl() {
    if (!onay) { setOnay(true); return }
    setBekle(true); setHata(null)
    try {
      const r = await api.veriYuklemeUygula(tur, metin, dosyaAdi)
      setSonuc(r); setOnizleme(null); setMetin(null); setOnay(false); yedekleriYukle()
    } catch (err) {
      setHata(err.detail || 'Canlıya alınamadı.')
    }
    setBekle(false)
  }

  async function geriDon(id) {
    if (donus !== id) { setDonus(id); return }
    setBekle(true); setHata(null)
    try {
      const r = await api.veriYuklemeGeriYukle(id)
      setSonuc({ ...r, geri: id }); setDonus(null); yedekleriYukle()
    } catch (err) {
      setHata(err.detail || 'Geri dönülemedi.')
    }
    setBekle(false)
  }

  const o = onizleme
  return (
    <div className="card">
      <div className="ct">{no}. adım · {baslik}</div>
      <div className="ps" style={{ margin: '0 0 10px' }}>{aciklama}</div>
      <div className="yp-ince" style={{ marginBottom: 10 }}>Seçilecek dosya: <b>{dosyaYolu}</b></div>
      <label className="btn" style={{ cursor: bekle ? 'not-allowed' : 'pointer', opacity: bekle ? 0.6 : 1 }}>
        {bekle ? <span className="spin" /> : '⬆ Dosyayı seç'}
        <input type="file" accept=".sql,.csv,.txt" onChange={dosyaSecildi} disabled={bekle} style={{ display: 'none' }} />
      </label>
      {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}
      {sonuc && (
        <div className="kayit-ok" style={{ marginTop: 10, padding: 10, borderRadius: 8, background: 'var(--grl)', color: 'var(--gr)' }}>
          ✓ {sonuc.geri ? `${sonuc.geri} numaralı yedeğe dönüldü` : 'Canlıya alındı'}: {sonuc.yazilan} satır
          {sonuc.bolum_sayisi ? `, ${sonuc.bolum_sayisi} bölüm` : ''}. Önceki hâl yedek #{sonuc.yedek_id} olarak saklandı.
        </div>
      )}
      {o && (
        <div style={{ marginTop: 12 }}>
          <div className="sg" style={{ marginBottom: 10 }}>
            <div className="sc"><div className="sl">Dosyadaki satır</div><div className="sv">{o.satir}</div></div>
            <div className="sc"><div className="sl">Bölüm</div><div className="sv">{o.bolum_sayisi} / {o.yayindaki_bolum}</div></div>
            <div className="sc"><div className="sl">Şu an canlıda</div><div className="sv">{o.mevcut_satir}</div></div>
            <div className="sc"><div className="sl">Değişecek bölüm</div><div className="sv">{o.degisen_bolum}</div></div>
          </div>
          {o.eslesmeyen_bolumler.length > 0 && (
            <div className="auth-error">Sistemde olmayan bölüm adları ({o.eslesmeyen_bolumler.length}): {o.eslesmeyen_bolumler.slice(0, 8).join(', ')}
              {o.eslesmeyen_bolumler.length > 8 ? ' …' : ''}. Bu dosya canlıya alınamaz; pipeline'ın güncel bölüm listesiyle çalıştığından emin olun.</div>
          )}
          {o.eslesmeyen_kodlar.length > 0 && (
            <div className="auth-error">Sistemde olmayan iş türü kodları: {o.eslesmeyen_kodlar.slice(0, 8).join(', ')}. Bu dosya canlıya alınamaz.</div>
          )}
          {o.yayinda_olmayan_bolum > 0 && (
            <div className="yp-ince" style={{ marginBottom: 8 }}>
              ℹ Dosyada yayında olmayan (taslak / test ediliyor) {o.yayinda_olmayan_bolum} bölüm de var; onların verisi de yazılır, yayına alınınca hazır olur.
            </div>
          )}
          {o.kapsanmayan_bolumler.length > 0 && o.canliya_alinabilir && (
            <div className="yp-ince" style={{ color: 'var(--am)', marginBottom: 8 }}>
              ⚠ Dosyada olmayan {o.kapsanmayan_bolumler.length} yayındaki bölüm canlıya alınınca boş kalır: {o.kapsanmayan_bolumler.slice(0, 6).join(', ')}{o.kapsanmayan_bolumler.length > 6 ? ' …' : ''}
            </div>
          )}
          {o.ornek.length > 0 && (
            <table className="yp-tablo" style={{ marginBottom: 10 }}>
              <thead><tr><th>Değişen bölüm (örnek)</th><th>Şu an</th><th>Yeni</th></tr></thead>
              <tbody>{o.ornek.map((x) => <tr key={x.bolum}><td>{x.bolum}</td><td className="yp-ince">{x.eski}</td><td className="yp-ince">{x.yeni}</td></tr>)}</tbody>
            </table>
          )}
          <button className="btn" disabled={bekle || !o.canliya_alinabilir} onClick={canliyaAl}>
            {onay ? 'Eminim, canlıya al' : 'Canlıya al'}
          </button>
          {onay && <span className="yp-ince" style={{ marginLeft: 8 }}>Şu anki {o.mevcut_satir} satır yedeklenip yerine dosyadaki satırlar yazılacak.</span>}
        </div>
      )}
      {yedekler.length > 0 && (
        <details style={{ marginTop: 12 }}>
          <summary className="yp-ince" style={{ cursor: 'pointer', fontWeight: 700 }}>Önceki sürümler ({yedekler.length})</summary>
          {yedekler.map((y) => (
            <div key={y.id} className="yp-ince" style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 6, flexWrap: 'wrap' }}>
              <span>#{y.id} · {new Date(y.zaman).toLocaleString('tr-TR')} · {y.satir_sayisi} satır · {y.aciklama}{y.kaydeden ? ` · ${y.kaydeden}` : ''}</span>
              <button className="yp-mini" disabled={bekle} onClick={() => geriDon(y.id)}>{donus === y.id ? 'Eminim, bu sürüme dön' : 'Bu sürüme dön'}</button>
            </div>
          ))}
        </details>
      )}
    </div>
  )
}

// ============================================================
// [2026-11-01] Pipeline sayacı + "bu bilgisayara kur" + kayıtlı bilgisayarlar (süper admin)
// Kod sistemin deposunda, veri Supabase Storage'da; her bilgisayar buradan indirilen tek dosyayla kurulur.
// ============================================================
const tarih = (z) => (z ? new Date(z).toLocaleDateString('tr-TR') : '—')
const tarihSaat = (z) => (z ? new Date(z).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }) : '—')
const SAYAC_GORUNUM = {
  guncel: { etiket: 'Güncel', renk: 'var(--gr)', zemin: 'var(--grl)' },
  yaklasiyor: { etiket: 'Yaklaşıyor', renk: 'var(--am)', zemin: 'var(--aml)' },
  gerekli: { etiket: 'Pipeline çalıştırılmalı', renk: 'var(--re)', zemin: 'var(--rel)' },
  canliya_al: { etiket: 'Çıktılar canlıya alınmalı', renk: 'var(--am)', zemin: 'var(--aml)' },
}
const CALISTIR_KOMUTU = 'powershell -ExecutionPolicy Bypass -File C:\\pipeline\\pipeline_calistir.ps1'
const KURULUM_KOMUTU = 'powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\\Downloads\\pipeline_kurulum.ps1"'

function Komut({ metin }) {
  const [kopyalandi, setKopyalandi] = useState(false)
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', margin: '6px 0' }}>
      <code style={{ background: 'var(--bg)', border: '1px solid var(--bor)', borderRadius: 6, padding: '6px 8px', fontSize: 12, wordBreak: 'break-all', flex: '1 1 320px' }}>{metin}</code>
      <button className="yp-mini" onClick={() => { navigator.clipboard?.writeText(metin).then(() => { setKopyalandi(true); setTimeout(() => setKopyalandi(false), 1500) }).catch(() => {}) }}>
        {kopyalandi ? '✓ Kopyalandı' : 'Kopyala'}
      </button>
    </div>
  )
}

function PipelineSayacKarti({ durum }) {
  const s = durum.sayac
  const g = SAYAC_GORUNUM[s.durum] || SAYAC_GORUNUM.gerekli
  const kalan = s.kalan_gun
  return (
    <div className="card">
      <div className="ct">Pipeline sayacı · yılda bir güncelleme</div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap', marginBottom: 10 }}>
        <span style={{ background: g.zemin, color: g.renk, fontWeight: 800, borderRadius: 999, padding: '6px 14px' }}>{g.etiket}</span>
        <span className="ps" style={{ margin: 0 }}>
          {s.son_guncelleme
            ? <>Son güncelleme <b>{tarih(s.son_guncelleme)}</b> · sonraki <b>{tarih(s.sonraki_guncelleme)}</b>
              {' '}({kalan > 0 ? <><b>{kalan}</b> gün kaldı</> : <b>{-kalan} gün geçti</b>})</>
            : 'Bölüm profilleri henüz hiç canlıya alınmadı.'}
        </span>
      </div>
      {s.nedenler.length > 0 && (
        <ul style={{ margin: '0 0 8px', paddingLeft: 18, color: g.renk }}>
          {s.nedenler.map((n) => <li key={n} className="yp-ince" style={{ color: g.renk }}>{n}</li>)}
        </ul>
      )}
      {s.notlar.length > 0 && (
        <ul style={{ margin: '0 0 8px', paddingLeft: 18 }}>
          {s.notlar.map((n) => <li key={n} className="yp-ince">{n}</li>)}
        </ul>
      )}
      <div className="yp-ince" style={{ marginBottom: 6 }}>
        Canlıya alma: bölüm profilleri {tarih(s.canliya_alma.bolum_profili)} · K5 bağları {tarih(s.canliya_alma.k5_baglari)} ·
        örnek meslekler {tarih(s.canliya_alma.ornek_meslekler)}
      </div>
      {(s.durum === 'gerekli' || s.durum === 'yaklasiyor') && (
        <div className="yp-ince">Pipeline'ın kurulu olduğu bilgisayarda cmd'ye yapıştırın, bitince aşağıdaki 3 adımla canlıya alın:<Komut metin={CALISTIR_KOMUTU} /></div>
      )}
    </div>
  )
}

function PipelineKurulumKarti({ durum, yenile }) {
  const [ad, setAd] = useState('')
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const [indirildi, setIndirildi] = useState(null)
  const [kaldir, setKaldir] = useState(null)

  async function indir() {
    setBekle(true); setHata(null); setIndirildi(null)
    try {
      await api.pipelineKurulumDosyasi(ad.trim(), `${window.location.origin}/api`)
      setIndirildi(ad.trim()); setAd(''); yenile()
    } catch (err) {
      setHata(err.detail || 'Kurulum dosyası hazırlanamadı.')
    }
    setBekle(false)
  }

  async function cihazKaldir(id) {
    if (kaldir !== id) { setKaldir(id); return }
    setBekle(true); setHata(null)
    try { await api.pipelineCihazKaldir(id); setKaldir(null); yenile() } catch (err) { setHata(err.detail || 'Kaldırılamadı.') }
    setBekle(false)
  }

  return (
    <div className="card">
      <div className="ct">Pipeline'ı bir bilgisayara kur</div>
      <div className="ps" style={{ margin: '0 0 10px' }}>
        Pipeline'ın kodu sistemde, verisi sistemin deposunda durur. Herhangi bir Windows bilgisayara buradan indirilen tek dosyayla
        kurulur. Her çalıştırmada güncel kodu ve en son veriyi kendisi alır, bitince sonuçları depoya gönderir.
        Canlıya alma yine aşağıdaki 3 adımla yapılır.
      </div>
      {!durum.depo_hazir && (
        <div className="auth-error" style={{ marginBottom: 10 }}>
          <b>Pipeline deposu henüz bağlı değil.</b> Kurulum dosyası indirilebilir, ancak veri gönderip almak için bir kez şunlar yapılmalı:
          <ol style={{ margin: '6px 0 0', paddingLeft: 18 }}>
            <li>Supabase → projeniz → <b>Project Settings → API</b>: <b>Project URL</b> ve <b>service_role</b> anahtarını kopyalayın.</li>
            <li>Render → backend servisi → <b>Environment</b>: <code>SUPABASE_URL</code> = Project URL, <code>SUPABASE_SERVICE_KEY</code> = service_role anahtarı → <b>Save</b> (servis yeniden başlar).</li>
          </ol>
        </div>
      )}
      <div className="yp-ince" style={{ marginBottom: 6 }}>
        <b>1.</b> Bilgisayarda <b>Python 3.14</b> kurulu olmalı. Kurulu değilse <a href="https://www.python.org/downloads/" target="_blank" rel="noreferrer">python.org</a>'dan
        kurun ve "Add python.exe to PATH" kutusunu işaretleyin.
      </div>
      <div className="yp-ince" style={{ marginBottom: 6 }}><b>2.</b> Bilgisayara bir ad verin ve kurulum dosyasını indirin. Dosya 24 saat geçerlidir ve tek kullanımlıktır.</div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 6 }}>
        <input className="auth-input" style={{ flex: "1 1 220px", marginBottom: 0 }} placeholder="Bilgisayar adı (ör. Ofis bilgisayarı)" value={ad} maxLength={60}
          onChange={(e) => setAd(e.target.value)} />
        <button className="btn" disabled={bekle || ad.trim().length < 2} onClick={indir}>{bekle ? <span className="spin" /> : '⬇ Kurulum dosyasını indir'}</button>
      </div>
      {indirildi && <div className="yp-ince" style={{ color: 'var(--gr)' }}>✓ "{indirildi}" için <b>pipeline_kurulum.ps1</b> indirildi.</div>}
      <div className="yp-ince"><b>3.</b> İndirdiğiniz dosyayı o bilgisayarda çalıştırın (cmd'ye yapıştırın):<Komut metin={KURULUM_KOMUTU} /></div>
      <div className="yp-ince"><b>4.</b> Kurulum bitince pipeline'ı çalıştırmak için:<Komut metin={CALISTIR_KOMUTU} /></div>
      {hata && <div className="auth-error" style={{ marginTop: 8 }}>{hata}</div>}

      <div style={{ fontWeight: 700, margin: '14px 0 6px' }}>Kayıtlı bilgisayarlar ({durum.cihazlar.length})</div>
      {durum.cihazlar.length === 0 ? <div className="yp-ince">Henüz kurulum yapılmadı.</div> : (
        <table className="yp-tablo">
          <thead><tr><th>Bilgisayar</th><th>Kuran</th><th>Kurulum</th><th>Son bağlantı</th><th /></tr></thead>
          <tbody>{durum.cihazlar.map((c) => (
            <tr key={c.id}>
              <td>{c.cihaz_adi}</td><td className="yp-ince">{c.olusturan || '—'}</td>
              <td className="yp-ince">{tarihSaat(c.olusturma_zamani)}</td><td className="yp-ince">{tarihSaat(c.son_kullanim)}</td>
              <td><button className="yp-mini" disabled={bekle} onClick={() => cihazKaldir(c.id)}>{kaldir === c.id ? 'Eminim, erişimi kaldır' : 'Erişimi kaldır'}</button></td>
            </tr>
          ))}</tbody>
        </table>
      )}
      <div style={{ fontWeight: 700, margin: '14px 0 6px' }}>Depodaki veri sürümleri</div>
      {durum.surumler.length === 0 ? <div className="yp-ince">Henüz gönderilmiş veri yok. İlk çalıştırmanın sonunda gönderilir.</div> : (
        <table className="yp-tablo">
          <thead><tr><th>Sürüm</th><th>Tarih</th><th>Bilgisayar</th><th>Dosya</th><th>Boyut</th></tr></thead>
          <tbody>{durum.surumler.map((v) => (
            <tr key={v.id}><td>#{v.id}</td><td className="yp-ince">{tarihSaat(v.zaman)}</td><td>{v.cihaz_adi || '—'}</td>
              <td className="yp-ince">{v.dosya_sayisi}</td><td className="yp-ince">{Math.round((v.toplam_bayt || 0) / 1e6)} MB</td></tr>
          ))}</tbody>
        </table>
      )}
      <div className="yp-ince" style={{ marginTop: 8 }}>Kod sürümü {durum.kod_surumu} · {durum.kod_dosya_sayisi} dosya · son 5 veri sürümü saklanır.</div>
    </div>
  )
}

export default function PipelineDurumuSayfasi() {
  const { rol } = useAdminAuth()
  const suAdminMi = rol === 'super_admin'

  const [taslaklar, setTaslaklar] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)

  // [DÜZELTME] SheetJS kütüphanesi bu sayfaya doğrudan gelindiğinde yüklü
  // olmuyordu — .xlsx okuma/yazma "kütüphane yüklenemedi" hatası veriyordu.
  useEffect(() => {
    if (window.XLSX) return
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js'
    script.async = true
    document.body.appendChild(script)
  }, [])
  const [sonYukleme, setSonYukleme] = useState(null)
  const [hata, setHata] = useState(null)
  const [islemGrubu, setIslemGrubu] = useState(null)
  const [paket, setPaket] = useState(null)
  const paketiYenile = useCallback(() => {
    if (!suAdminMi) return
    api.pipelinePaketDurumu().then(setPaket).catch(() => setPaket(null))
  }, [suAdminMi])
  useEffect(() => { paketiYenile() }, [paketiYenile])

  const listeyiYenile = useCallback(() => {
    api.pipelineTaslaklariListele().then(setTaslaklar).catch((e) => setHata(e.detail || 'Liste alınamadı.'))
  }, [])

  useEffect(() => { listeyiYenile() }, [listeyiYenile])

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    setHata(null)
    setSonYukleme(null)
    setYukleniyor(true)
    try {
      const hamSatirlar = await dosyayiAyristir(dosya)
      const satirlar = satirlariDondur(hamSatirlar)
      if (satirlar.length === 0) {
        throw new Error('Dosya okunamadı — sütun başlıklarını kontrol edin (bolum_adi, degisken_kod, agirlik_degeri gerekli).')
      }
      const sonuc = await api.pipelineCiktisiYukle(satirlar)
      setSonYukleme(sonuc)
      listeyiYenile()
    } catch (err) {
      setHata(err.detail || err.message || 'Yükleme başarısız.')
    } finally {
      setYukleniyor(false)
      e.target.value = ''
    }
  }

  async function onayla(grup) {
    setIslemGrubu(grup)
    try {
      await api.pipelineTaslaginiOnayla(grup)
      listeyiYenile()
    } catch (err) {
      setHata(err.detail || 'Onaylanamadı.')
    } finally {
      setIslemGrubu(null)
    }
  }

  async function reddet(grup) {
    setIslemGrubu(grup)
    try {
      await api.pipelineTaslaginiReddet(grup)
      listeyiYenile()
    } catch (err) {
      setHata(err.detail || 'Reddedilemedi.')
    } finally {
      setIslemGrubu(null)
    }
  }

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Pipeline Sonuçları</div>
        <div className="ps">
          Bölüm verileri bilgisayarınızdaki pipeline'da üretilir. Çıktıları buradan <b>üç adımda</b> canlıya alırsınız; Supabase SQL
          ekranı gerekmez. Her adımda önce önizleme görürsünüz, canlıya almadan önceki hâl saklanır.
        </div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}

      {paket && <PipelineSayacKarti durum={paket} />}
      {paket && <PipelineKurulumKarti durum={paket} yenile={paketiYenile} />}

      <div className="card">
        <div className="ct">1. adım · Bölüm profilleri</div>
        <div className="ps" style={{ margin: '0 0 10px' }}>
          Uyum hesabının bölüm tarafı (31 özellik). Yüklemek canlıya dokunmaz: dosya taslak olarak gelir, aşağıdaki
          "Geçmiş Yüklemeler"de <b>Yayına Al</b> deyince canlıya geçer ve tüm öğrencilerin sonuçları yeniden hesaplanır.
          Önceki sürümler silinmez.
        </div>
        <div className="yp-ince" style={{ marginBottom: 10 }}>Seçilecek dosya: <b>C:\pipeline\cikti\bolum_agirliklari.xlsx</b></div>
        <label className="btn" style={{ cursor: yukleniyor ? 'not-allowed' : 'pointer', opacity: yukleniyor ? 0.6 : 1 }}>
          {yukleniyor ? <span className="spin" /> : '⬆ Dosyayı seç'}
          <input type="file" accept=".xlsx,.xls,.csv" onChange={dosyaSecildi} disabled={yukleniyor} style={{ display: 'none' }} />
        </label>
      </div>

      {sonYukleme && (
        <div className="card" style={{ borderColor: 'var(--pu)', background: 'var(--pul)' }}>
          <div className="ct">Yükleme Sonucu — Onay Bekliyor</div>
          <div className="sg" style={{ marginBottom: 14 }}>
            <div className="sc"><div className="sl">Eşleşen Satır</div><div className="sv gr">{sonYukleme.eslesen_satir}</div></div>
            <div className="sc"><div className="sl">Eşleşmeyen</div><div className="sv" style={{ color: sonYukleme.eslesmeyen_satirlar.length ? 'var(--re)' : undefined }}>{sonYukleme.eslesmeyen_satirlar.length}</div></div>
            <div className="sc"><div className="sl">Bölüm Sayısı</div><div className="sv">{sonYukleme.bolum_sayisi}</div></div>
            <div className="sc"><div className="sl">Ortalama Aralık</div><div className="sv" style={{ color: sonYukleme.ortalama_aralik < 15 ? 'var(--re)' : 'var(--gr)' }}>{sonYukleme.ortalama_aralik}</div></div>
          </div>

          {sonYukleme.ortalama_aralik < 15 && (
            <div className="auth-error" style={{ marginBottom: 14 }}>
              ⚠️ Ortalama aralık çok düşük (&lt;15) — bölümler birbirinden yeterince ayrışmıyor olabilir.
              Onaylamadan önce pipeline çıktısını gözden geçirmenizi öneririz.
            </div>
          )}

          {sonYukleme.eslesmeyen_satirlar.length > 0 && (
            <div style={{ fontSize: 12, color: 'var(--tx2)', marginBottom: 14 }}>
              <b>Eşleşmeyenler (ilk birkaçı):</b> {sonYukleme.eslesmeyen_satirlar.slice(0, 8).join(', ')}
              {sonYukleme.eslesmeyen_satirlar.length > 8 && ` +${sonYukleme.eslesmeyen_satirlar.length - 8} tane daha`}
            </div>
          )}

          <div className="ct">En "Düz" (En Az Ayrışık) 10 Bölüm</div>
          <div className="ll">
            {sonYukleme.en_duz_10.map((b) => (
              <div key={b.bolum_adi} className="lc" style={{ cursor: 'default' }}>
                <div className="lb-wrap"><div className="lt">{b.bolum_adi}</div></div>
                <div style={{ fontFamily: 'var(--fd)', fontWeight: 700, color: b.aralik < 10 ? 'var(--re)' : 'var(--am)' }}>{b.aralik.toFixed(1)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="ct" style={{ marginTop: 20 }}>1. adım · Geçmiş Yüklemeler</div>
      {!taslaklar ? (
        <div className="bos-durum yukleniyor">Yükleniyor…</div>
      ) : taslaklar.length === 0 ? (
        <div className="bos-durum">Henüz hiç pipeline çıktısı yüklenmedi.</div>
      ) : (
        <div className="ll">
          {taslaklar.map((g) => (
            <div key={g.yukleme_grubu} className="lc" style={{ cursor: 'default' }}>
              <div className="lb-wrap">
                <div className="lt">{new Date(g.yuklenme_zamani).toLocaleString('tr-TR')}</div>
                <div className="ld">{g.toplam_satir} satır · {g.bolum_sayisi} bölüm · ortalama aralık: {g.ortalama_aralik}</div>
                <span className={`bdg ${DURUM_RENK[g.durum]}`}>{DURUM_ETIKET[g.durum]}</span>
              </div>
              {g.durum === 'bekliyor' && (
                <div style={{ display: 'flex', gap: 6 }}>
                  {suAdminMi ? (
                    <button className="btn" onClick={() => onayla(g.yukleme_grubu)} disabled={islemGrubu === g.yukleme_grubu}>
                      {islemGrubu === g.yukleme_grubu ? <span className="spin" /> : 'Yayına Al'}
                    </button>
                  ) : (
                    <span style={{ fontSize: 11, color: 'var(--tx3)' }}>Yalnızca süper admin onaylayabilir</span>
                  )}
                  <button className="btn sec" onClick={() => reddet(g.yukleme_grubu)} disabled={islemGrubu === g.yukleme_grubu}>
                    Reddet
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 20 }}>
        <VeriAdimKarti no={2} tur="k5_baglari" baslik="K5 iş türü bağları" dosyaYolu="C:\pipeline\cikti\k5_baglari_veri.sql"
          aciklama="Her bölümün hangi iş türlerine bağlı olduğu (K5 soruları ve küme içi sıralama bu bağlarla çalışır)." />
        <VeriAdimKarti no={3} tur="ornek_meslekler" baslik="Örnek meslekler" dosyaYolu="C:\pipeline\cikti\ornek_meslekler_veri.sql"
          aciklama="Bölüm sayfasında ve Karşılaştır'da görünen örnek meslek listeleri (bölüm başına en fazla 5)." />
      </div>

      <details style={{ marginTop: 20 }}>
        <summary className="yp-ince" style={{ cursor: 'pointer', fontWeight: 700 }}>Gelişmiş: meslek listesi (yalnızca meslek listesi değiştiyse)</summary>
        <div style={{ marginTop: 10 }}><MeslekYuklemeKarti /></div>
      </details>
    </div>
  )
}