import { useEffect, useState, useCallback, useRef } from 'react'
import { api } from '../../api/client'

const KATMAN_ID = { K1: 1, K2: 2, K3: 3, K4: 4, K5: 5 }
const KATMAN_ADI = {
  K1: 'Değerler / Motivasyon',
  K2: 'Kişilik & Çalışma Tarzı',
  K3: 'İş Ortamı & Profesyonel Yetkinlik',
  K4: 'Alan Eğilimi & Bilişsel Stil',
  K5: 'Derinleşme',
}

const DEGISKENLER = [
  { id: 1, kod: 'D1' }, { id: 2, kod: 'D2' }, { id: 3, kod: 'D3' }, { id: 4, kod: 'D4' },
  { id: 5, kod: 'D5' }, { id: 6, kod: 'D6' }, { id: 7, kod: 'D7' },
  { id: 8, kod: 'P1' }, { id: 9, kod: 'P2' }, { id: 10, kod: 'P3' }, { id: 11, kod: 'P4' },
  { id: 12, kod: 'P5' }, { id: 13, kod: 'P6' }, { id: 14, kod: 'P7' }, { id: 15, kod: 'P8' },
  { id: 16, kod: 'A1' }, { id: 17, kod: 'A2' }, { id: 18, kod: 'A3' }, { id: 19, kod: 'A4' },
  { id: 20, kod: 'A5' }, { id: 21, kod: 'A6' }, { id: 22, kod: 'A7' }, { id: 23, kod: 'A8' }, { id: 24, kod: 'A9' },
  { id: 25, kod: 'I1' }, { id: 26, kod: 'I2' }, { id: 27, kod: 'I3' }, { id: 28, kod: 'I4' },
  { id: 29, kod: 'I5' }, { id: 30, kod: 'I6' }, { id: 31, kod: 'I7' },
]
const DEGISKEN_ID_MAP = Object.fromEntries(DEGISKENLER.map((d) => [d.kod, d.id]))

const BOS_LIKERT_SECENEK = ['Kesinlikle Katılmıyorum', 'Katılmıyorum', 'Kararsızım', 'Katılıyorum', 'Kesinlikle Katılıyorum']

// ============================================================
// Birleşik toplu içe aktarma (Likert + SJT, tek dosya tek format)
// ============================================================
// Sütun sırası: soru_gecici_id, katman_kod, soru_tipi, degisken_kod,
// soru_metni, ters_kodlanmis_mi, secenek_sira, secenek_metni,
// sjt_degisken_kod, sjt_agirlik
// Likert satırlarında sjt_degisken_kod/sjt_agirlik boş bırakılır.
// SJT satırlarında degisken_kod boş bırakılır.
function SheetJSYukluMu() {
  return typeof window !== 'undefined' && window.XLSX
}

function dosyayiAyristir(dosya) {
  return new Promise((resolve, reject) => {
    if (!SheetJSYukluMu()) {
      reject(new Error('Okuma kütüphanesi yüklenemedi. Sayfayı yenileyip tekrar deneyin.'))
      return
    }
    const okuyucu = new FileReader()
    okuyucu.onload = (e) => {
      try {
        const tur = dosya.name.toLowerCase().endsWith('.csv') ? 'string' : 'array'
        const veri = tur === 'string' ? e.target.result : e.target.result
        const wb = window.XLSX.read(veri, { type: tur })
        const sayfaAdi = wb.SheetNames.find((n) => n.toLowerCase().includes('soru')) || wb.SheetNames[0]
        const sayfa = wb.Sheets[sayfaAdi]
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

function birlesikSatirlariDondur(hamSatirlar) {
  const veriSatirlari = hamSatirlar.slice(1) // başlık satırını atla
  const satirlar = []
  const hatalar = []

  veriSatirlari.forEach((hucreler, i) => {
    const satirNo = i + 2
    const [gecidiId, katmanKod, soruTipi, degiskenKod, soruMetni, tersMi, secenekSira, secenekMetni, sjtDegiskenKod, sjtAgirlik] =
      hucreler.map((h) => String(h ?? '').trim())

    if (!gecidiId && !soruMetni) return // tamamen boş satır

    if (!['K1', 'K2', 'K3', 'K4', 'K5'].includes(katmanKod)) {
      hatalar.push(`Satır ${satirNo}: geçersiz katman_kod "${katmanKod}"`)
      return
    }
    if (!['likert', 'sjt'].includes(soruTipi)) {
      hatalar.push(`Satır ${satirNo}: soru_tipi "likert" veya "sjt" olmalı ("${soruTipi}")`)
      return
    }
    const sira = parseInt(secenekSira, 10)
    if (isNaN(sira)) {
      hatalar.push(`Satır ${satirNo}: secenek_sira sayı olmalı`)
      return
    }

    satirlar.push({
      soru_gecici_id: gecidiId,
      katman_kod: katmanKod,
      soru_tipi: soruTipi,
      degisken_kod: degiskenKod || null,
      soru_metni: soruMetni,
      ters_kodlanmis_mi: tersMi.toUpperCase() === 'EVET' || tersMi.toUpperCase() === 'TRUE',
      secenek_sira: sira,
      secenek_metni: secenekMetni,
      sjt_degisken_kod: sjtDegiskenKod || null,
      sjt_agirlik: sjtAgirlik ? parseFloat(sjtAgirlik) : null,
    })
  })

  return { satirlar, hatalar }
}

function TopluYuklemeFormu({ onTamamlandi }) {
  const [durum, setDurum] = useState('bekliyor') // bekliyor | okunuyor | yukleniyor | bitti
  const [sonuc, setSonuc] = useState(null)
  const dosyaInputRef = useRef(null)

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    setDurum('okunuyor')
    setSonuc(null)

    try {
      const hamSatirlar = await dosyayiAyristir(dosya)
      const { satirlar, hatalar } = birlesikSatirlariDondur(hamSatirlar)

      if (satirlar.length === 0) {
        setSonuc({ basarili: false, mesaj: null, hatalar: hatalar.length ? hatalar : ['Dosyada geçerli satır bulunamadı.'] })
        setDurum('bitti')
        return
      }

      setDurum('yukleniyor')
      const cevap = await api.sorulariTopluYukle(satirlar)
      setSonuc({
        basarili: true,
        mesaj: `${cevap.eklenen_soru_sayisi} soru, ${cevap.eklenen_secenek_sayisi} seçenek, ${cevap.eklenen_agirlik_sayisi} SJT ağırlığı eklendi.`,
        hatalar: [...hatalar, ...cevap.hatalar],
      })
      setDurum('bitti')
      onTamamlandi()
    } catch (err) {
      setSonuc({ basarili: false, mesaj: null, hatalar: [err.detail || err.message || 'Dosya işlenemedi.'] })
      setDurum('bitti')
    } finally {
      if (dosyaInputRef.current) dosyaInputRef.current.value = ''
    }
  }

  return (
    <div className="card" style={{ borderColor: 'var(--tl)', background: 'var(--tll)' }}>
      <div className="ct">Toplu Soru Yükle (Likert + SJT, Tek Dosya)</div>
      <div className="ps" style={{ margin: '0 0 12px' }}>
        Sütunlar: <code>soru_gecici_id, katman_kod, soru_tipi, degisken_kod, soru_metni, ters_kodlanmis_mi,
        secenek_sira, secenek_metni, sjt_degisken_kod, sjt_agirlik</code>. Aynı <code>soru_gecici_id</code>'ye
        sahip satırlar tek soruya gruplanır. Likert satırlarında son iki sütun boş bırakılır;
        SJT satırlarında <code>degisken_kod</code> boş bırakılır. CSV veya Excel (.xlsx) kabul edilir.
      </div>
      <label className="btn" style={{ cursor: durum === 'yukleniyor' || durum === 'okunuyor' ? 'not-allowed' : 'pointer', opacity: durum === 'yukleniyor' || durum === 'okunuyor' ? 0.6 : 1 }}>
        {durum === 'okunuyor' ? 'Okunuyor...' : durum === 'yukleniyor' ? <span className="spin" /> : '⬆ Dosya Seç ve Yükle'}
        <input
          ref={dosyaInputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          onChange={dosyaSecildi}
          disabled={durum === 'yukleniyor' || durum === 'okunuyor'}
          style={{ display: 'none' }}
        />
      </label>

      {sonuc && (
        <div style={{ marginTop: 14 }}>
          {sonuc.mesaj && (
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--gr)', marginBottom: 6 }}>{sonuc.mesaj}</div>
          )}
          {sonuc.hatalar.length > 0 && (
            <div style={{ fontSize: 12, color: 'var(--tx2)', background: 'var(--sur)', borderRadius: 10, padding: '10px 12px', maxHeight: 180, overflowY: 'auto' }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>{sonuc.hatalar.length} sorun:</div>
              {sonuc.hatalar.slice(0, 30).map((h, i) => <div key={i}>{h}</div>)}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ============================================================
// Tekil soru ekleme formu (mevcut)
// ============================================================
function YeniSoruFormu({ onEklendi }) {
  const [katmanKod, setKatmanKod] = useState('K1')
  const [soruTipi, setSoruTipi] = useState('likert')
  const [degiskenId, setDegiskenId] = useState(DEGISKENLER[0].id)
  const [soruMetni, setSoruMetni] = useState('')
  const [tersKodlanmisMi, setTersKodlanmisMi] = useState(false)
  // Likert: string[]. SJT: { metin, agirliklar: [{degisken_id, agirlik}] }[]
  const [secenekler, setSecenekler] = useState([...BOS_LIKERT_SECENEK])
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [basari, setBasari] = useState(false)

  function tipDegistir(yeniTip) {
    setSoruTipi(yeniTip)
    setSecenekler(yeniTip === 'likert'
      ? [...BOS_LIKERT_SECENEK]
      : [{ metin: '', agirliklar: [] }, { metin: '', agirliklar: [] }])
  }

  function likertMetniGuncelle(i, deger) {
    setSecenekler((onceki) => onceki.map((s, idx) => (idx === i ? deger : s)))
  }

  function sjtMetniGuncelle(i, deger) {
    setSecenekler((onceki) => onceki.map((s, idx) => (idx === i ? { ...s, metin: deger } : s)))
  }

  function sjtSecenekEkle() {
    setSecenekler((onceki) => [...onceki, { metin: '', agirliklar: [] }])
  }

  function sjtSecenekSil(i) {
    setSecenekler((onceki) => onceki.filter((_, idx) => idx !== i))
  }

  function sjtAgirlikEkle(secenekIdx) {
    setSecenekler((onceki) => onceki.map((s, idx) =>
      idx === secenekIdx ? { ...s, agirliklar: [...s.agirliklar, { degisken_id: DEGISKENLER[0].id, agirlik: 0 }] } : s
    ))
  }

  function sjtAgirlikGuncelle(secenekIdx, agirlikIdx, alan, deger) {
    setSecenekler((onceki) => onceki.map((s, idx) => {
      if (idx !== secenekIdx) return s
      const yeniAgirliklar = s.agirliklar.map((a, ai) => (ai === agirlikIdx ? { ...a, [alan]: deger } : a))
      return { ...s, agirliklar: yeniAgirliklar }
    }))
  }

  function sjtAgirlikSil(secenekIdx, agirlikIdx) {
    setSecenekler((onceki) => onceki.map((s, idx) =>
      idx === secenekIdx ? { ...s, agirliklar: s.agirliklar.filter((_, ai) => ai !== agirlikIdx) } : s
    ))
  }

  async function gonder(e) {
    e.preventDefault()
    setHata(null)
    setBasari(false)

    if (soruMetni.trim().length < 5) {
      setHata('Soru metni en az 5 karakter olmalı.')
      return
    }

    let secenekPayload
    if (soruTipi === 'likert') {
      const temiz = secenekler.map((s) => s.trim())
      if (temiz.some((s) => s.length === 0)) {
        setHata('Tüm seçenek alanları doldurulmalı.')
        return
      }
      secenekPayload = temiz.map((metin) => ({ metin, sjt_agirliklari: [] }))
    } else {
      if (secenekler.some((s) => s.metin.trim().length === 0)) {
        setHata('Tüm seçenek metinleri doldurulmalı.')
        return
      }
      if (secenekler.length < 2) {
        setHata('En az 2 seçenek gerekli.')
        return
      }
      secenekPayload = secenekler.map((s) => ({
        metin: s.metin.trim(),
        sjt_agirliklari: s.agirliklar.map((a) => ({ degisken_id: a.degisken_id, agirlik: Number(a.agirlik) })),
      }))
    }

    setGonderiliyor(true)
    try {
      await api.soruEkle({
        katman_id: KATMAN_ID[katmanKod],
        degisken_id: soruTipi === 'likert' ? degiskenId : null,
        soru_tipi: soruTipi,
        soru_metni: soruMetni.trim(),
        ters_kodlanmis_mi: soruTipi === 'likert' ? tersKodlanmisMi : false,
        secenekler: secenekPayload,
      })
      setBasari(true)
      setSoruMetni('')
      setSecenekler(soruTipi === 'likert' ? [...BOS_LIKERT_SECENEK] : [{ metin: '', agirliklar: [] }, { metin: '', agirliklar: [] }])
      setTersKodlanmisMi(false)
      onEklendi()
    } catch (err) {
      setHata(err.detail || 'Soru eklenemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  return (
    <div className="card">
      <div className="ct">Tek Tek Soru Ekle</div>

      {hata && <div className="auth-error">{hata}</div>}
      {basari && <div style={{ background: 'var(--grl)', color: 'var(--gr)', fontSize: 12.5, fontWeight: 600, padding: '10px 13px', borderRadius: 8, marginBottom: 14 }}>Soru eklendi ✓</div>}

      <form onSubmit={gonder}>
        <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
          <div style={{ flex: 1 }}>
            <label className="auth-label">Katman</label>
            <select className="auth-input" value={katmanKod} onChange={(e) => setKatmanKod(e.target.value)}>
              {Object.keys(KATMAN_ID).map((k) => <option key={k} value={k}>{KATMAN_ADI[k]}</option>)}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label className="auth-label">Soru Tipi</label>
            <select className="auth-input" value={soruTipi} onChange={(e) => tipDegistir(e.target.value)}>
              <option value="likert">Likert (5'li ölçek)</option>
              <option value="sjt">SJT (durumsal yargı)</option>
            </select>
          </div>
        </div>

        {soruTipi === 'likert' && (
          <div style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label className="auth-label">Ölçtüğü Değişken</label>
              <select className="auth-input" value={degiskenId} onChange={(e) => setDegiskenId(Number(e.target.value))}>
                {DEGISKENLER.map((d) => <option key={d.id} value={d.id}>{d.kod}</option>)}
              </select>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 600, color: 'var(--tx2)', paddingBottom: 11 }}>
              <input type="checkbox" checked={tersKodlanmisMi} onChange={(e) => setTersKodlanmisMi(e.target.checked)} />
              Ters kodlanmış (puan = 100 − puan)
            </label>
          </div>
        )}

        <div className="auth-field">
          <label className="auth-label">Soru Metni</label>
          <textarea
            className="auth-input"
            style={{ minHeight: 70, resize: 'vertical', fontFamily: 'var(--fn)' }}
            value={soruMetni}
            onChange={(e) => setSoruMetni(e.target.value)}
            placeholder={soruTipi === 'likert' ? 'Örn: İşimde en çok değer verdiğim şey...' : 'Senaryo metnini yazın...'}
          />
        </div>

        {soruTipi === 'likert' ? (
          <>
            <label className="auth-label">Seçenekler (sabit 5'li ölçek)</label>
            {secenekler.map((s, i) => (
              <div key={i} style={{ marginBottom: 8 }}>
                <input className="auth-input" style={{ width: '100%' }} value={s} onChange={(e) => likertMetniGuncelle(i, e.target.value)} disabled />
              </div>
            ))}
          </>
        ) : (
          <>
            <label className="auth-label">Seçenekler ve Değişken Ağırlıkları</label>
            <div className="ps" style={{ margin: '0 0 12px', fontSize: 11.5 }}>
              Her seçeneğe, o seçeneği işaretleyen öğrencinin hangi değişkenlerde ne kadar puan alacağını ekleyin.
              Ağırlık -1.000 ile 1.000 arasında olmalı (negatif = o değişkende düşük/ters katkı).
            </div>
            {secenekler.map((s, i) => (
              <div key={i} className="card" style={{ marginBottom: 10, background: 'var(--sur2)' }}>
                <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
                  <input
                    className="auth-input"
                    style={{ flex: 1 }}
                    value={s.metin}
                    onChange={(e) => sjtMetniGuncelle(i, e.target.value)}
                    placeholder={`Seçenek ${i + 1} metni`}
                  />
                  {secenekler.length > 2 && (
                    <button type="button" className="btn sec" onClick={() => sjtSecenekSil(i)}>Seçeneği Sil</button>
                  )}
                </div>

                {s.agirliklar.map((a, ai) => (
                  <div key={ai} style={{ display: 'flex', gap: 8, marginBottom: 6, alignItems: 'center' }}>
                    <select
                      className="auth-input"
                      style={{ width: 100 }}
                      value={a.degisken_id}
                      onChange={(e) => sjtAgirlikGuncelle(i, ai, 'degisken_id', Number(e.target.value))}
                    >
                      {DEGISKENLER.map((d) => <option key={d.id} value={d.id}>{d.kod}</option>)}
                    </select>
                    <input
                      className="auth-input"
                      type="number" step="0.05" min="-1" max="1"
                      style={{ width: 90 }}
                      value={a.agirlik}
                      onChange={(e) => sjtAgirlikGuncelle(i, ai, 'agirlik', e.target.value)}
                    />
                    <button type="button" className="btn sec" style={{ padding: '6px 10px' }} onClick={() => sjtAgirlikSil(i, ai)}>✕</button>
                  </div>
                ))}
                <button type="button" className="btn sec" style={{ fontSize: 11.5, padding: '5px 10px' }} onClick={() => sjtAgirlikEkle(i)}>
                  + Değişken Ağırlığı Ekle
                </button>
              </div>
            ))}
            <button type="button" className="btn sec" style={{ marginBottom: 14 }} onClick={sjtSecenekEkle}>+ Seçenek Ekle</button>
          </>
        )}

        <button className="btn full" type="submit" disabled={gonderiliyor} style={{ marginTop: 6 }}>
          {gonderiliyor ? <span className="spin" /> : 'Soruyu Kaydet'}
        </button>
      </form>
    </div>
  )
}

// ============================================================
// Ana sayfa
// ============================================================
function csvDisaAktar(dosyaAdi, basliklar, satirlar) {
  const kacisla = (deger) => `"${String(deger ?? '').replace(/"/g, '""')}"`
  const icerik = [basliklar.join(','), ...satirlar.map((s) => s.map(kacisla).join(','))].join('\r\n')
  const blob = new Blob(['\uFEFF' + icerik], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = dosyaAdi
  a.click()
  URL.revokeObjectURL(url)
}


// ============================================================
// Düzenlenebilir metin — tıklayınca input'a döner, blur/enter'da kaydeder
// ============================================================
function DuzenlenebilirMetin({ deger, onKaydet, coklu = false, stil = {} }) {
  const [duzenleniyor, setDuzenleniyor] = useState(false)
  const [taslak, setTaslak] = useState(deger)
  const [kaydediliyor, setKaydediliyor] = useState(false)

  useEffect(() => { setTaslak(deger) }, [deger])

  async function kaydet() {
    if (taslak.trim() === deger.trim()) { setDuzenleniyor(false); return }
    setKaydediliyor(true)
    try {
      await onKaydet(taslak.trim())
      setDuzenleniyor(false)
    } catch (err) {
      alert(err.detail || 'Kaydedilemedi.')
    } finally {
      setKaydediliyor(false)
    }
  }

  if (!duzenleniyor) {
    return (
      <div
        onClick={() => setDuzenleniyor(true)}
        style={{ cursor: 'text', padding: '2px 4px', borderRadius: 6, ...stil }}
        title="Düzenlemek için tıkla"
        onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--sur2)')}
        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
      >
        {deger}
      </div>
    )
  }

  const OrtakProps = {
    value: taslak,
    autoFocus: true,
    disabled: kaydediliyor,
    onChange: (e) => setTaslak(e.target.value),
    onBlur: kaydet,
    onKeyDown: (e) => {
      if (e.key === 'Enter' && !coklu) kaydet()
      if (e.key === 'Escape') { setTaslak(deger); setDuzenleniyor(false) }
    },
    style: { width: '100%', fontFamily: 'inherit', fontSize: 'inherit', padding: '4px 6px', border: '1.5px solid var(--pu)', borderRadius: 6, ...stil },
  }

  return coklu ? <textarea rows={2} {...OrtakProps} /> : <input type="text" {...OrtakProps} />
}

// ============================================================
// Tek bir soru kartı — numaralı, tüm şıklarıyla, düzenlenebilir
// ============================================================
function SoruKarti({ soru, sira, onGuncelle }) {
  return (
    <div className="card" style={{ marginBottom: 10, opacity: soru.aktif_mi ? 1 : 0.55 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 10 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 8, background: 'var(--sur2)', color: 'var(--tx2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, flexShrink: 0,
        }}>
          {sira}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
            <span className="bdg bdg-prog">{soru.katman_kod}</span>
            {soru.dal_adi && <span className="bdg" style={{ background: 'var(--tll)', color: 'var(--tl)' }}>{soru.dal_adi}</span>}
            <span className="bdg bdg-lock">{soru.soru_tipi === 'likert' ? 'Likert' : 'SJT'}</span>
            {soru.degisken_kod && <span className="bdg bdg-lock">{soru.degisken_kod}</span>}
            {soru.ters_kodlanmis_mi && <span className="bdg" style={{ background: 'var(--aml)', color: 'var(--am)' }}>Ters Kodlanmış</span>}
            <span className={`bdg ${soru.aktif_mi ? 'bdg-done' : 'bdg-lock'}`}>{soru.aktif_mi ? 'Aktif' : 'Pasif'}</span>
          </div>
          <DuzenlenebilirMetin
            deger={soru.soru_metni}
            coklu
            stil={{ fontSize: 14.5, fontWeight: 700 }}
            onKaydet={(yeniMetin) => onGuncelle('soru', soru.id, yeniMetin)}
          />
        </div>
      </div>

      <div style={{ paddingLeft: 40, display: 'flex', flexDirection: 'column', gap: 6 }}>
        {soru.secenekler.map((sec) => (
          <div key={sec.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <span style={{ width: 18, color: 'var(--tx3)', fontWeight: 700, flexShrink: 0 }}>{sec.secenek_sirasi}.</span>
            <div style={{ flex: 1 }}>
              <DuzenlenebilirMetin
                deger={sec.secenek_metni}
                onKaydet={(yeniMetin) => onGuncelle('secenek', sec.id, yeniMetin)}
              />
            </div>
            {sec.sjt_agirliklar.length > 0 && (
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', flexShrink: 0 }}>
                {sec.sjt_agirliklar.map((a, i) => (
                  <span key={i} style={{ fontSize: 10, background: 'var(--pul)', color: 'var(--pud)', padding: '2px 7px', borderRadius: 10, fontWeight: 700 }}>
                    {a.degisken_kod}: {a.agirlik}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

const KATMANLAR = ['K1', 'K2', 'K3', 'K4', 'K5']

function OzetKartlari({ ozet }) {
  if (!ozet) return null
  return (
    <div className="sg" style={{ marginBottom: 16 }}>
      <div className="sc"><div className="sl">Toplam</div><div className="sv">{ozet.toplam}</div></div>
      <div className="sc"><div className="sl">Likert</div><div className="sv pu">{ozet.likert_sayisi}</div></div>
      <div className="sc"><div className="sl">SJT</div><div className="sv pu">{ozet.sjt_sayisi}</div></div>
      <div className="sc"><div className="sl">Aktif</div><div className="sv gr">{ozet.aktif_sayisi}</div></div>
      <div className="sc"><div className="sl">Pasif</div><div className="sv">{ozet.pasif_sayisi}</div></div>
    </div>
  )
}

export default function SorularSayfasi() {
  const [aktifKatman, setAktifKatman] = useState('K1')
  const [veri, setVeri] = useState(null)
  const [ozet, setOzet] = useState(null)
  const [dallar, setDallar] = useState([])
  const [degiskenler, setDegiskenler] = useState([])
  const [dalFiltre, setDalFiltre] = useState('')
  const [degiskenFiltre, setDegiskenFiltre] = useState('')
  const [tipFiltre, setTipFiltre] = useState('')
  const [aktifFiltre, setAktifFiltre] = useState('')
  const [arama, setArama] = useState('')
  const [aramaGecikmeli, setAramaGecikmeli] = useState('')
  const [sayfa, setSayfa] = useState(1)
  const [aktifSekme, setAktifSekme] = useState(null)
  const [hata, setHata] = useState(null)

  // Arama kutusuna yazarken 400ms bekleyip sorguyu tetikle (her tuş vuruşunda değil)
  useEffect(() => {
    const zamanlayici = setTimeout(() => setAramaGecikmeli(arama), 400)
    return () => clearTimeout(zamanlayici)
  }, [arama])

  const yukle = useCallback((katman, dal, degisken, tip, aktif, sayfaNo, aramaMetni) => {
    const aktifParam = aktif === 'aktif' ? true : aktif === 'pasif' ? false : undefined
    api.sorularDetayliListele(katman, dal || undefined, aktifParam, sayfaNo, degisken || undefined, tip || undefined, aramaMetni || undefined)
      .then(setVeri)
      .catch((e) => setHata(e.detail || 'Sorular yüklenemedi.'))
    api.katmanOzetiGetir(katman, dal || undefined).then(setOzet).catch(() => setOzet(null))
  }, [])

  // Katman değişince tüm alt filtreleri sıfırla
  useEffect(() => {
    setDalFiltre(''); setDegiskenFiltre(''); setTipFiltre(''); setAktifFiltre(''); setArama(''); setSayfa(1)
  }, [aktifKatman])

  useEffect(() => { setSayfa(1) }, [dalFiltre, degiskenFiltre, tipFiltre, aktifFiltre, aramaGecikmeli])

  useEffect(() => {
    yukle(aktifKatman, dalFiltre, degiskenFiltre, tipFiltre, aktifFiltre, sayfa, aramaGecikmeli)
  }, [yukle, aktifKatman, dalFiltre, degiskenFiltre, tipFiltre, aktifFiltre, sayfa, aramaGecikmeli])

  useEffect(() => {
    if (aktifKatman === 'K5') api.dalFiltreListesiGetir().then(setDallar).catch(() => setDallar([]))
    else setDallar([])
  }, [aktifKatman])

  useEffect(() => {
    api.katmanDegiskenleriGetir(aktifKatman, dalFiltre || undefined).then(setDegiskenler).catch(() => setDegiskenler([]))
  }, [aktifKatman, dalFiltre])

  useEffect(() => {
    if (window.XLSX) return
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js'
    script.async = true
    document.body.appendChild(script)
  }, [])

  async function alanGuncelle(tip, id, yeniMetin) {
    if (tip === 'soru') await api.soruMetniGuncelle(id, yeniMetin)
    else await api.secenekMetniGuncelle(id, yeniMetin)
    yukle(aktifKatman, dalFiltre, degiskenFiltre, tipFiltre, aktifFiltre, sayfa, aramaGecikmeli)
  }

  function yenidenYukle() {
    yukle(aktifKatman, dalFiltre, degiskenFiltre, tipFiltre, aktifFiltre, sayfa, aramaGecikmeli)
  }

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Soru Bankası</div>
        <div className="ps">Her katmanın kendi sekmesi altında; arayıp, filtreleyip, doğrudan düzenleyebilirsiniz.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      {/* Katman sekmeleri */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 18, borderBottom: '1.5px solid var(--bor)', paddingBottom: 0 }}>
        {KATMANLAR.map((k) => (
          <button
            key={k}
            onClick={() => setAktifKatman(k)}
            style={{
              padding: '10px 20px', border: 'none', background: 'none', cursor: 'pointer',
              fontFamily: 'var(--fd)', fontSize: 13.5, fontWeight: 700,
              color: aktifKatman === k ? 'var(--pu)' : 'var(--tx3)',
              borderBottom: aktifKatman === k ? '2.5px solid var(--pu)' : '2.5px solid transparent',
              marginBottom: -1.5, transition: 'all .12s',
            }}
          >
            {k} — {KATMAN_ADI[k]}
          </button>
        ))}
      </div>

      <OzetKartlari ozet={ozet} />

      {/* Filtre satırı */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          className="auth-input"
          style={{ width: 240 }}
          placeholder="🔍 Soru metninde ara…"
          value={arama}
          onChange={(e) => setArama(e.target.value)}
        />
        {aktifKatman === 'K5' && (
          <select className="auth-input" style={{ width: 220 }} value={dalFiltre} onChange={(e) => setDalFiltre(e.target.value)}>
            <option value="">Tüm dallar</option>
            {dallar.map((d) => <option key={d.kod} value={d.kod}>{d.ad}</option>)}
          </select>
        )}
        <select className="auth-input" style={{ width: 170 }} value={degiskenFiltre} onChange={(e) => setDegiskenFiltre(e.target.value)}>
          <option value="">Tüm değişkenler</option>
          {degiskenler.map((d) => <option key={d.kod} value={d.kod}>{d.kod} — {d.ad}</option>)}
        </select>
        <select className="auth-input" style={{ width: 140 }} value={tipFiltre} onChange={(e) => setTipFiltre(e.target.value)}>
          <option value="">Tüm tipler</option>
          <option value="likert">Yalnızca Likert</option>
          <option value="sjt">Yalnızca SJT</option>
        </select>
        <select className="auth-input" style={{ width: 150 }} value={aktifFiltre} onChange={(e) => setAktifFiltre(e.target.value)}>
          <option value="">Aktif + Pasif</option>
          <option value="aktif">Yalnızca Aktif</option>
          <option value="pasif">Yalnızca Pasif</option>
        </select>
        <div style={{ flex: 1 }} />
        <button className="btn sec" onClick={() => setAktifSekme((s) => (s === 'toplu' ? null : 'toplu'))}>
          {aktifSekme === 'toplu' ? 'Kapat' : '⬆ Toplu Yükle'}
        </button>
        <button className="btn" onClick={() => setAktifSekme((s) => (s === 'tekli' ? null : 'tekli'))}>
          {aktifSekme === 'tekli' ? 'Kapat' : '+ Soru Ekle'}
        </button>
      </div>

      {aktifSekme === 'toplu' && (
        <div style={{ marginBottom: 20 }}>
          <TopluYuklemeFormu onTamamlandi={yenidenYukle} />
        </div>
      )}
      {aktifSekme === 'tekli' && (
        <div style={{ marginBottom: 20 }}>
          <YeniSoruFormu onEklendi={yenidenYukle} />
        </div>
      )}

      {!veri ? <div className="bos-durum">Yükleniyor…</div> : (
        <>
          <div style={{ fontSize: 12, color: 'var(--tx3)', fontWeight: 600, marginBottom: 10 }}>
            {veri.toplam_soru_sayisi} soru bulundu — Sayfa {veri.su_anki_sayfa} / {veri.toplam_sayfa_sayisi}
          </div>

          {veri.sorular.length === 0 ? (
            <div className="bos-durum">Bu filtreye uyan soru yok.</div>
          ) : (
            veri.sorular.map((s, i) => (
              <SoruKarti
                key={s.id}
                soru={s}
                sira={(veri.su_anki_sayfa - 1) * 8 + i + 1}
                onGuncelle={alanGuncelle}
              />
            ))
          )}

          {veri.toplam_sayfa_sayisi > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 6, marginTop: 20 }}>
              <button className="btn sec" disabled={sayfa <= 1} onClick={() => setSayfa((p) => p - 1)}>‹ Önceki</button>
              {Array.from({ length: veri.toplam_sayfa_sayisi }, (_, i) => i + 1)
                .filter((n) => n === 1 || n === veri.toplam_sayfa_sayisi || Math.abs(n - sayfa) <= 2)
                .reduce((acc, n, idx, arr) => {
                  if (idx > 0 && n - arr[idx - 1] > 1) acc.push('...')
                  acc.push(n)
                  return acc
                }, [])
                .map((n, i) => n === '...' ? (
                  <span key={`b${i}`} style={{ color: 'var(--tx3)', padding: '0 4px' }}>…</span>
                ) : (
                  <button
                    key={n}
                    onClick={() => setSayfa(n)}
                    className={n === sayfa ? 'btn' : 'btn sec'}
                    style={{ minWidth: 36, padding: '8px 12px' }}
                  >
                    {n}
                  </button>
                ))}
              <button className="btn sec" disabled={sayfa >= veri.toplam_sayfa_sayisi} onClick={() => setSayfa((p) => p + 1)}>Sonraki ›</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
