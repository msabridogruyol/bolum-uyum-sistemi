import { useEffect, useState, useCallback } from 'react'
import { api } from '../../api/client'

const DURUMLAR = ['taslak', 'guclu_kanitli', 'gozden_gecirilmeli']

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

function csvSatirlariniAyristir(metin) {
  const satirlar = metin.split(/\r?\n/).filter((s) => s.trim().length > 0)
  if (satirlar.length < 2) return []
  const baslik = satirlar[0].split(',').map((s) => s.trim().replace(/^"|"$/g, ''))
  const kodIdx = baslik.indexOf('kod')
  const adIdx = baslik.indexOf('ad')
  if (kodIdx === -1 || adIdx === -1) return []

  return satirlar.slice(1).map((satir) => {
    const parcalar = []
    let mevcut = ''
    let tirnakIci = false
    for (const karakter of satir) {
      if (karakter === '"') tirnakIci = !tirnakIci
      else if (karakter === ',' && !tirnakIci) { parcalar.push(mevcut); mevcut = '' }
      else mevcut += karakter
    }
    parcalar.push(mevcut)
    return { kod: parcalar[kodIdx]?.trim(), ad: parcalar[adIdx]?.trim() }
  }).filter((s) => s.kod && s.ad)
}

export default function DallarSayfasi() {
  const [dallar, setDallar] = useState(null)
  const [hata, setHata] = useState(null)
  const [yeniKod, setYeniKod] = useState('')
  const [yeniAd, setYeniAd] = useState('')
  const [topluYukleniyor, setTopluYukleniyor] = useState(false)
  const [topluSonuc, setTopluSonuc] = useState(null)

  const yukle = useCallback(() => {
    api.dallariListele().then(setDallar).catch((e) => setHata(e.detail || 'Dallar yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  async function dalEkle(e) {
    e.preventDefault()
    try {
      await api.dalEkle({ kod: yeniKod, ad: yeniAd })
      setYeniKod(''); setYeniAd('')
      yukle()
    } catch (err) {
      setHata(err.detail || 'Dal eklenemedi.')
    }
  }

  async function durumGuncelle(dalId, yeniDurum) {
    try {
      await api.dalDurumGuncelle(dalId, yeniDurum)
      yukle()
    } catch (err) {
      setHata(err.detail || 'Durum güncellenemedi.')
    }
  }

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    setHata(null)
    setTopluSonuc(null)
    setTopluYukleniyor(true)
    try {
      const metin = await dosya.text()
      const satirlar = csvSatirlariniAyristir(metin)
      if (satirlar.length === 0) {
        throw new Error('CSV okunamadı — "kod" ve "ad" sütunları gerekli.')
      }
      let eklenen = 0
      const hatalar = []
      for (const satir of satirlar) {
        try {
          await api.dalEkle(satir)
          eklenen++
        } catch (err) {
          hatalar.push(`${satir.kod}: ${err.detail || 'eklenemedi'}`)
        }
      }
      setTopluSonuc({ eklenen, hatalar })
      yukle()
    } catch (err) {
      setHata(err.detail || err.message || 'Toplu yükleme başarısız.')
    } finally {
      setTopluYukleniyor(false)
      e.target.value = ''
    }
  }

  if (!dallar) return <div className="pg pg-genis"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Derinleşme Alanları</div>
        <div className="ps">Öğrencinin son değerlendirme adımındaki sonucuna göre kendisine özel olarak açılabilecek ek inceleme alanları.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div className="card">
        <div className="ct">Toplu Yönetim</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            className="btn sec"
            onClick={() => csvDisaAktar(
              'dallar_disa_aktarim.csv',
              ['kod', 'ad', 'dogrulama_durumu'],
              dallar.map((d) => [d.kod, d.ad, d.dogrulama_durumu]),
            )}
            disabled={dallar.length === 0}
          >
            ⬇ CSV Dışa Aktar
          </button>
          <label className="btn" style={{ cursor: topluYukleniyor ? 'not-allowed' : 'pointer', opacity: topluYukleniyor ? 0.6 : 1 }}>
            {topluYukleniyor ? <span className="spin" /> : '⬆ CSV İçe Aktar (kod, ad)'}
            <input type="file" accept=".csv" onChange={dosyaSecildi} disabled={topluYukleniyor} style={{ display: 'none' }} />
          </label>
        </div>
        {topluSonuc && (
          <div style={{ marginTop: 12, fontSize: 12.5 }}>
            <b style={{ color: 'var(--gr)' }}>{topluSonuc.eklenen} dal eklendi.</b>
            {topluSonuc.hatalar.length > 0 && (
              <div style={{ color: 'var(--am)', marginTop: 4 }}>{topluSonuc.hatalar.slice(0, 5).join(', ')}</div>
            )}
          </div>
        )}
      </div>

      <form onSubmit={dalEkle} className="card" style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
        <div style={{ flex: '0 0 100px' }}>
          <label className="auth-label">Kod</label>
          <input className="auth-input" value={yeniKod} onChange={(e) => setYeniKod(e.target.value)} placeholder="D22" required />
        </div>
        <div style={{ flex: 1 }}>
          <label className="auth-label">Ad</label>
          <input className="auth-input" value={yeniAd} onChange={(e) => setYeniAd(e.target.value)} placeholder="Yeni alan adı" required />
        </div>
        <button className="btn" type="submit">Ekle</button>
      </form>

      <div className="ll">
        {dallar.map((d) => (
          <div key={d.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{d.ad}</div>
              <span className="bdg bdg-prog">{d.dogrulama_durumu}</span>
            </div>
            <select className="auth-input" style={{ width: 180 }} value={d.dogrulama_durumu} onChange={(e) => durumGuncelle(d.id, e.target.value)}>
              {DURUMLAR.map((du) => <option key={du} value={du}>{du}</option>)}
            </select>
          </div>
        ))}
        {dallar.length === 0 && <div className="bos-durum">Henüz tanımlı bir derinleşme alanı yok — yukarıdaki formdan ekleyebilirsiniz.</div>}
      </div>
    </div>
  )
}
