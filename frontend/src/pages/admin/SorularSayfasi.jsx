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

export default function SorularSayfasi() {
  const [sorular, setSorular] = useState(null)
  const [katmanFiltre, setKatmanFiltre] = useState('')
  const [aktifFiltre, setAktifFiltre] = useState('') // '' | 'aktif' | 'pasif'
  const [aktifSekme, setAktifSekme] = useState(null) // null | 'tekli' | 'toplu'
  const [hata, setHata] = useState(null)
  const [secilenler, setSecilenler] = useState(new Set())
  const [topluIslemYukleniyor, setTopluIslemYukleniyor] = useState(false)

  const yukle = useCallback((kod, aktif) => {
    const aktifParam = aktif === 'aktif' ? true : aktif === 'pasif' ? false : undefined
    api.sorulariListele(kod || undefined, aktifParam).then((veri) => {
      setSorular(veri)
      setSecilenler(new Set()) // liste yenilenince seçim sıfırlanır
    }).catch((e) => setHata(e.detail || 'Sorular yüklenemedi.'))
  }, [])

  useEffect(() => { yukle(katmanFiltre, aktifFiltre) }, [yukle, katmanFiltre, aktifFiltre])

  // SheetJS kütüphanesini bir kez, sayfa açılınca yükle
  useEffect(() => {
    if (window.XLSX) return
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js'
    script.async = true
    document.body.appendChild(script)
  }, [])

  async function aktiflikDegistir(soruId, aktifMi) {
    try {
      await api.soruAktiflikGuncelle(soruId, !aktifMi)
      yukle(katmanFiltre, aktifFiltre)
    } catch (err) {
      setHata(err.detail || 'Güncellenemedi.')
    }
  }

  function secimDegistir(soruId) {
    setSecilenler((onceki) => {
      const yeni = new Set(onceki)
      if (yeni.has(soruId)) yeni.delete(soruId)
      else yeni.add(soruId)
      return yeni
    })
  }

  function hepsiniSec() {
    if (!sorular) return
    setSecilenler((onceki) =>
      onceki.size === sorular.length ? new Set() : new Set(sorular.map((s) => s.id))
    )
  }

  async function topluAktifDurumDegistir(aktifMi) {
    if (secilenler.size === 0) return
    setTopluIslemYukleniyor(true)
    try {
      await api.sorulariTopluAktifYap([...secilenler], aktifMi)
      yukle(katmanFiltre, aktifFiltre)
    } catch (err) {
      setHata(err.detail || 'Toplu güncelleme başarısız.')
    } finally {
      setTopluIslemYukleniyor(false)
    }
  }

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Soru Bankası</div>
        <div className="ps">Soruları pasife alabilirsiniz — geçmiş öğrenci oturumları bozulmasın diye kalıcı silme yoktur.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'center', flexWrap: 'wrap' }}>
        <select className="auth-input" style={{ width: 220 }} value={katmanFiltre} onChange={(e) => setKatmanFiltre(e.target.value)}>
          <option value="">Tüm katmanlar</option>
          {Object.keys(KATMAN_ADI).map((k) => <option key={k} value={k}>{KATMAN_ADI[k]}</option>)}
        </select>
        <select className="auth-input" style={{ width: 160 }} value={aktifFiltre} onChange={(e) => setAktifFiltre(e.target.value)}>
          <option value="">Aktif + Pasif</option>
          <option value="aktif">Yalnızca Aktif</option>
          <option value="pasif">Yalnızca Pasif</option>
        </select>
        <button className="btn sec" onClick={() => setAktifSekme((s) => (s === 'toplu' ? null : 'toplu'))}>
          {aktifSekme === 'toplu' ? 'Kapat' : '⬆ Toplu Yükle (Likert + SJT)'}
        </button>
        <button className="btn" onClick={() => setAktifSekme((s) => (s === 'tekli' ? null : 'tekli'))}>
          {aktifSekme === 'tekli' ? 'Kapat' : '+ Tek Tek Soru Ekle'}
        </button>
        <button
          className="btn sec"
          onClick={() => csvDisaAktar(
            'sorular.csv',
            ['id', 'katman_kod', 'degisken_kod', 'soru_tipi', 'soru_metni', 'aktif_mi'],
            (sorular || []).map((s) => [s.id, s.katman_kod, s.degisken_kod || '', s.soru_tipi, s.soru_metni, s.aktif_mi]),
          )}
          disabled={!sorular || sorular.length === 0}
        >
          ⬇ CSV Dışa Aktar
        </button>
      </div>

      {aktifSekme === 'toplu' && (
        <div style={{ marginBottom: 20 }}>
          <TopluYuklemeFormu onTamamlandi={() => yukle(katmanFiltre, aktifFiltre)} />
        </div>
      )}
      {aktifSekme === 'tekli' && (
        <div style={{ marginBottom: 20 }}>
          <YeniSoruFormu onEklendi={() => yukle(katmanFiltre, aktifFiltre)} />
        </div>
      )}

      {sorular && sorular.length > 0 && (
        <div style={{
          display: 'flex', gap: 10, alignItems: 'center', marginBottom: 12, padding: '10px 14px',
          background: secilenler.size > 0 ? 'var(--tll)' : 'var(--sur2)', borderRadius: 10,
        }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 600, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={sorular.length > 0 && secilenler.size === sorular.length}
              onChange={hepsiniSec}
            />
            Tümünü Seç
          </label>
          <span style={{ fontSize: 12.5, color: 'var(--tx2)' }}>
            {secilenler.size > 0 ? `${secilenler.size} soru seçildi` : ''}
          </span>
          {secilenler.size > 0 && (
            <div style={{ display: 'flex', gap: 8, marginLeft: 'auto' }}>
              <button className="btn sec" disabled={topluIslemYukleniyor} onClick={() => topluAktifDurumDegistir(true)}>
                Seçilenleri Aktif Yap
              </button>
              <button className="btn sec" disabled={topluIslemYukleniyor} onClick={() => topluAktifDurumDegistir(false)}>
                Seçilenleri Pasif Yap
              </button>
            </div>
          )}
        </div>
      )}

      {!sorular ? <div className="bos-durum">Yükleniyor…</div> : (
        <div className="ll">
          {sorular.map((s) => (
            <div key={s.id} className="lc" style={{ cursor: 'default', opacity: s.aktif_mi ? 1 : 0.5 }}>
              <input
                type="checkbox"
                checked={secilenler.has(s.id)}
                onChange={() => secimDegistir(s.id)}
                style={{ marginRight: 10 }}
              />
              <div className="lb-wrap">
                <div className="lt">{s.soru_metni}</div>
                <div className="ld">{KATMAN_ADI[s.katman_kod] || s.katman_kod} · {s.soru_tipi === 'likert' ? 'Likert' : 'SJT'}</div>
              </div>
              <span className={`bdg ${s.aktif_mi ? 'bdg-done' : 'bdg-lock'}`}>{s.aktif_mi ? 'Aktif' : 'Pasif'}</span>
              <button className="btn sec" onClick={() => aktiflikDegistir(s.id, s.aktif_mi)}>
                {s.aktif_mi ? 'Pasife Al' : 'Aktifleştir'}
              </button>
            </div>
          ))}
          {sorular.length === 0 && <div className="bos-durum">Bu filtreye uyan soru yok.</div>}
        </div>
      )}
    </div>
  )
}
