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
// Excel içe aktarma
// ============================================================
function SheetJSYukluMu() {
  return typeof window !== 'undefined' && window.XLSX
}

function satirlariAyristir(dosya) {
  return new Promise((resolve, reject) => {
    if (!SheetJSYukluMu()) {
      reject(new Error('Excel okuma kütüphanesi yüklenemedi. Sayfayı yenileyip tekrar deneyin.'))
      return
    }
    const okuyucu = new FileReader()
    okuyucu.onload = (e) => {
      try {
        const wb = window.XLSX.read(e.target.result, { type: 'array' })
        const sayfaAdi = wb.SheetNames.find((n) => n.toLowerCase().includes('soru')) || wb.SheetNames[0]
        const sayfa = wb.Sheets[sayfaAdi]
        const satirlar = window.XLSX.utils.sheet_to_json(sayfa, { header: 1, defval: '' })
        resolve(satirlar)
      } catch (err) {
        reject(err)
      }
    }
    okuyucu.onerror = () => reject(new Error('Dosya okunamadı.'))
    okuyucu.readAsArrayBuffer(dosya)
  })
}

function satiriDogrula(hucreler, satirNo) {
  const [katmanKod, soruTipi, degiskenKod, soruMetni, tersMi, ...secenekHam] = hucreler.map((h) => String(h ?? '').trim())

  if (!katmanKod && !soruMetni) return null // tamamen boş satır — yok say

  if (!['K1', 'K2', 'K3', 'K4'].includes(katmanKod)) {
    return { hata: `Satır ${satirNo}: katman_kod "K1-K4" dışında bir değer ("${katmanKod}") — atlandı.` }
  }
  if (!['likert', 'sjt'].includes(soruTipi)) {
    return { hata: `Satır ${satirNo}: soru_tipi "likert" veya "sjt" olmalı ("${soruTipi}" geçersiz) — atlandı.` }
  }
  if (soruMetni.length < 5) {
    return { hata: `Satır ${satirNo}: soru metni çok kısa veya boş — atlandı.` }
  }
  let degiskenId = null
  if (soruTipi === 'likert') {
    degiskenId = DEGISKEN_ID_MAP[degiskenKod]
    if (!degiskenId) {
      return { hata: `Satır ${satirNo}: likert soru için geçerli bir degisken_kod gerekli ("${degiskenKod}" tanınmadı) — atlandı.` }
    }
  }
  const secenekler = secenekHam.map((s) => s.trim()).filter((s) => s.length > 0)
  if (secenekler.length < 2) {
    return { hata: `Satır ${satirNo}: en az 2 seçenek gerekli — atlandı.` }
  }

  return {
    payload: {
      katman_id: KATMAN_ID[katmanKod],
      degisken_id: degiskenId,
      soru_tipi: soruTipi,
      soru_metni: soruMetni,
      ters_kodlanmis_mi: soruTipi === 'likert' && tersMi.toUpperCase() === 'EVET',
      secenekler,
    },
  }
}

function IceAktarPaneli({ onTamamlandi }) {
  const [durum, setDurum] = useState('bekliyor') // bekliyor | okunuyor | yukleniyor | bitti
  const [sonuc, setSonuc] = useState(null) // { basarili, hatalar }
  const dosyaInputRef = useRef(null)

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    setDurum('okunuyor')
    setSonuc(null)

    try {
      const satirlar = await satirlariAyristir(dosya)
      const veriSatirlari = satirlar.slice(1) // başlık satırını atla

      const gecerliler = []
      const hatalar = []
      veriSatirlari.forEach((hucreler, i) => {
        const sonucSatir = satiriDogrula(hucreler, i + 2) // Excel'de satır 2'den başlar
        if (!sonucSatir) return // tamamen boş satır
        if (sonucSatir.hata) hatalar.push(sonucSatir.hata)
        else gecerliler.push(sonucSatir.payload)
      })

      if (gecerliler.length === 0) {
        setSonuc({ basarili: 0, hatalar: hatalar.length ? hatalar : ['Dosyada geçerli bir soru satırı bulunamadı.'] })
        setDurum('bitti')
        return
      }

      setDurum('yukleniyor')
      let basarili = 0
      const yuklemeHatalari = [...hatalar]
      for (const payload of gecerliler) {
        try {
          await api.soruEkle(payload)
          basarili++
        } catch (err) {
          yuklemeHatalari.push(`"${payload.soru_metni.slice(0, 40)}..." eklenemedi: ${err.detail || 'bilinmeyen hata'}`)
        }
      }
      setSonuc({ basarili, hatalar: yuklemeHatalari })
      setDurum('bitti')
      onTamamlandi()
    } catch (err) {
      setSonuc({ basarili: 0, hatalar: [err.message || 'Dosya işlenemedi.'] })
      setDurum('bitti')
    } finally {
      if (dosyaInputRef.current) dosyaInputRef.current.value = ''
    }
  }

  return (
    <div className="card" style={{ borderColor: 'var(--tl)', background: 'var(--tll)' }}>
      <div className="ct">Excel İle Toplu Soru Ekle</div>
      <div className="ps" style={{ margin: '0 0 14px' }}>
        Önce şablonu indirip doldurun, sonra buradan yükleyin. Yalnızca K1-K4 sorularını destekler.
      </div>

      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <a href="/soru_bankasi_sablonu.xlsx" download className="btn sec">⬇ Şablonu İndir</a>

        <label className="btn" style={{ cursor: durum === 'yukleniyor' || durum === 'okunuyor' ? 'not-allowed' : 'pointer', opacity: durum === 'yukleniyor' || durum === 'okunuyor' ? 0.6 : 1 }}>
          {durum === 'okunuyor' ? 'Dosya okunuyor...' : durum === 'yukleniyor' ? 'Yükleniyor...' : '⬆ Doldurulmuş Dosyayı Yükle'}
          <input
            ref={dosyaInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={dosyaSecildi}
            disabled={durum === 'yukleniyor' || durum === 'okunuyor'}
            style={{ display: 'none' }}
          />
        </label>
      </div>

      {sonuc && (
        <div style={{ marginTop: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: sonuc.basarili > 0 ? 'var(--gr)' : 'var(--re)', marginBottom: 6 }}>
            {sonuc.basarili} soru başarıyla eklendi.
          </div>
          {sonuc.hatalar.length > 0 && (
            <div style={{ fontSize: 12, color: 'var(--tx2)', background: 'var(--sur)', borderRadius: 10, padding: '10px 12px', maxHeight: 180, overflowY: 'auto' }}>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>{sonuc.hatalar.length} satır atlandı / hata verdi:</div>
              {sonuc.hatalar.map((h, i) => <div key={i} style={{ marginBottom: 3 }}>• {h}</div>)}
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
  const [secenekler, setSecenekler] = useState([...BOS_LIKERT_SECENEK])
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [basari, setBasari] = useState(false)

  function tipDegistir(yeniTip) {
    setSoruTipi(yeniTip)
    setSecenekler(yeniTip === 'likert' ? [...BOS_LIKERT_SECENEK] : ['', ''])
  }

  function secenekMetniGuncelle(i, deger) {
    setSecenekler((onceki) => onceki.map((s, idx) => (idx === i ? deger : s)))
  }

  function secenekEkle() {
    setSecenekler((onceki) => [...onceki, ''])
  }

  function secenekSil(i) {
    setSecenekler((onceki) => onceki.filter((_, idx) => idx !== i))
  }

  async function gonder(e) {
    e.preventDefault()
    setHata(null)
    setBasari(false)

    if (soruMetni.trim().length < 5) {
      setHata('Soru metni en az 5 karakter olmalı.')
      return
    }
    const temizSecenekler = secenekler.map((s) => s.trim())
    if (temizSecenekler.some((s) => s.length === 0)) {
      setHata('Tüm seçenek alanları doldurulmalı (boş seçenek olamaz).')
      return
    }
    if (temizSecenekler.length < 2) {
      setHata('En az 2 seçenek gerekli.')
      return
    }

    setGonderiliyor(true)
    try {
      await api.soruEkle({
        katman_id: KATMAN_ID[katmanKod],
        degisken_id: soruTipi === 'likert' ? degiskenId : null,
        soru_tipi: soruTipi,
        soru_metni: soruMetni.trim(),
        ters_kodlanmis_mi: soruTipi === 'likert' ? tersKodlanmisMi : false,
        secenekler: temizSecenekler,
      })
      setBasari(true)
      setSoruMetni('')
      setSecenekler(soruTipi === 'likert' ? [...BOS_LIKERT_SECENEK] : ['', ''])
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

      {soruTipi === 'sjt' && (
        <div className="auth-error" style={{ background: 'var(--aml)', color: 'var(--am)' }}>
          Not: SJT sorularında seçenek başına değişken ağırlığı bu formdan girilemiyor — yalnızca soru ve
          seçenek metinleri kaydedilir. Ağırlıklandırma ayrıca yapılmalı.
        </div>
      )}
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
            placeholder="Örn: İşimde en çok değer verdiğim şey..."
          />
        </div>

        <label className="auth-label">Seçenekler</label>
        {secenekler.map((s, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <input
              className="auth-input"
              style={{ flex: 1 }}
              value={s}
              onChange={(e) => secenekMetniGuncelle(i, e.target.value)}
              placeholder={`Seçenek ${i + 1}`}
              disabled={soruTipi === 'likert'}
            />
            {soruTipi === 'sjt' && secenekler.length > 2 && (
              <button type="button" className="btn sec" onClick={() => secenekSil(i)}>Sil</button>
            )}
          </div>
        ))}
        {soruTipi === 'sjt' && (
          <button type="button" className="btn sec" style={{ marginBottom: 14 }} onClick={secenekEkle}>+ Seçenek Ekle</button>
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
  const [aktifSekme, setAktifSekme] = useState(null) // null | 'tekli' | 'toplu'
  const [hata, setHata] = useState(null)

  const yukle = useCallback((kod) => {
    api.sorulariListele(kod || undefined).then(setSorular).catch((e) => setHata(e.detail || 'Sorular yüklenemedi.'))
  }, [])

  useEffect(() => { yukle(katmanFiltre) }, [yukle, katmanFiltre])

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
      yukle(katmanFiltre)
    } catch (err) {
      setHata(err.detail || 'Güncellenemedi.')
    }
  }

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Soru Bankası</div>
        <div className="ps">Sorular silinmez, yalnızca pasife alınır — geçmiş öğrenci oturumları bozulmasın diye.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'center', flexWrap: 'wrap' }}>
        <select className="auth-input" style={{ width: 240 }} value={katmanFiltre} onChange={(e) => setKatmanFiltre(e.target.value)}>
          <option value="">Tüm katmanlar</option>
          {Object.keys(KATMAN_ADI).map((k) => <option key={k} value={k}>{KATMAN_ADI[k]}</option>)}
        </select>
        <button className="btn sec" onClick={() => setAktifSekme((s) => (s === 'toplu' ? null : 'toplu'))}>
          {aktifSekme === 'toplu' ? 'Kapat' : '⬆ Excel İle Toplu Ekle'}
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
          <IceAktarPaneli onTamamlandi={() => yukle(katmanFiltre)} />
        </div>
      )}
      {aktifSekme === 'tekli' && (
        <div style={{ marginBottom: 20 }}>
          <YeniSoruFormu onEklendi={() => yukle(katmanFiltre)} />
        </div>
      )}

      {!sorular ? <div className="bos-durum">Yükleniyor…</div> : (
        <div className="ll">
          {sorular.map((s) => (
            <div key={s.id} className="lc" style={{ cursor: 'default', opacity: s.aktif_mi ? 1 : 0.5 }}>
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
          {sorular.length === 0 && <div className="bos-durum">Bu katmanda soru yok.</div>}
        </div>
      )}
    </div>
  )
}
