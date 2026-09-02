import { useEffect, useState, useCallback } from 'react'
import { api } from '../../api/client'

const DURUMLAR = ['taslak', 'guclu_kanitli', 'gozden_gecirilmeli']

const DURUM_BILGI = {
  taslak: {
    etiket: 'Taslak — İncelenmeyi Bekliyor',
    renk: 'bdg-lock',
    aciklama: 'Yalnızca tek bir yöntemden (kümeleme analizi) geldi. Henüz farklı bir yöntemle çapraz doğrulanmadı.',
  },
  guclu_kanitli: {
    etiket: 'Güçlü Kanıtlı',
    renk: 'bdg-done',
    aciklama: 'Birden fazla bağımsız yöntem (dil modelleri + kümeleme) aynı sonuca ulaştı — güvenilirliği yüksek.',
  },
  gozden_gecirilmeli: {
    etiket: 'Gözden Geçirilmeli',
    renk: 'bdg-prog',
    aciklama: 'Yöntemler arasında çelişki var ya da veri sınırlı — admin tarafından elle kontrol edilmesi önerilir.',
  },
}

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

function DalKarti({ dal, onDurumGuncelle }) {
  const bilgi = DURUM_BILGI[dal.dogrulama_durumu] || DURUM_BILGI.taslak
  const [degistiriliyor, setDegistiriliyor] = useState(false)

  return (
    <div className="card" style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span style={{ fontSize: 14.5, fontWeight: 700 }}>{dal.ad}</span>
            <span className="bdg bdg-lock">{dal.kod}</span>
            <span className={`bdg ${bilgi.renk}`}>{bilgi.etiket}</span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--tx2)', lineHeight: 1.5, marginBottom: 8 }}>{bilgi.aciklama}</div>
          <div style={{ display: 'flex', gap: 16, fontSize: 11.5, color: 'var(--tx3)', fontWeight: 600 }}>
            <span>📚 {dal.bolum_sayisi} bölüm</span>
            <span>🧬 {dal.degisken_sayisi} değişken</span>
            <span>❓ {dal.soru_sayisi} soru</span>
            <span>{dal.coklu_kaynakli_mi ? '✅ Çoklu yöntem doğrulaması var' : '⚠️ Tek yöntemden geldi'}</span>
          </div>
        </div>

        {degistiriliyor ? (
          <select
            className="auth-input"
            style={{ width: 200 }}
            value={dal.dogrulama_durumu}
            onChange={(e) => { onDurumGuncelle(dal.id, e.target.value); setDegistiriliyor(false) }}
            onBlur={() => setDegistiriliyor(false)}
            autoFocus
          >
            {DURUMLAR.map((du) => <option key={du} value={du}>{DURUM_BILGI[du].etiket}</option>)}
          </select>
        ) : (
          <button className="btn sec" onClick={() => setDegistiriliyor(true)}>Durumu Değiştir</button>
        )}
      </div>
    </div>
  )
}

export default function DallarSayfasi() {
  const [dallar, setDallar] = useState(null)
  const [hata, setHata] = useState(null)
  const [yeniKod, setYeniKod] = useState('')
  const [yeniAd, setYeniAd] = useState('')
  const [topluYukleniyor, setTopluYukleniyor] = useState(false)
  const [topluSonuc, setTopluSonuc] = useState(null)
  const [durumFiltre, setDurumFiltre] = useState('')

  const yukle = useCallback(() => {
    api.dallariDetayliListele().then(setDallar).catch((e) => setHata(e.detail || 'Dallar yüklenemedi.'))
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

  const gosterilecekler = durumFiltre ? dallar.filter((d) => d.dogrulama_durumu === durumFiltre) : dallar
  const durumSayilari = DURUMLAR.reduce((acc, du) => ({ ...acc, [du]: dallar.filter((d) => d.dogrulama_durumu === du).length }), {})

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Derinleşme Alanları (K5)</div>
        <div className="ps">Öğrencinin K4 sonucuna göre kendisine özel açılabilecek ek inceleme alanları. "Taslak" durumu bir hata değil — yalnızca henüz tek yöntemle doğrulandığı anlamına gelir.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
        <button className={`btn ${durumFiltre === '' ? '' : 'sec'}`} onClick={() => setDurumFiltre('')}>
          Tümü ({dallar.length})
        </button>
        {DURUMLAR.map((du) => (
          <button key={du} className={`btn ${durumFiltre === du ? '' : 'sec'}`} onClick={() => setDurumFiltre(du)}>
            {DURUM_BILGI[du].etiket} ({durumSayilari[du] || 0})
          </button>
        ))}
      </div>

      <div className="card">
        <div className="ct">Toplu Yönetim</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            className="btn sec"
            onClick={() => csvDisaAktar(
              'dallar_disa_aktarim.csv',
              ['kod', 'ad', 'dogrulama_durumu', 'bolum_sayisi', 'degisken_sayisi', 'soru_sayisi'],
              dallar.map((d) => [d.kod, d.ad, d.dogrulama_durumu, d.bolum_sayisi, d.degisken_sayisi, d.soru_sayisi]),
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
          <input className="auth-input" value={yeniKod} onChange={(e) => setYeniKod(e.target.value)} placeholder="D09" required />
        </div>
        <div style={{ flex: 1 }}>
          <label className="auth-label">Ad</label>
          <input className="auth-input" value={yeniAd} onChange={(e) => setYeniAd(e.target.value)} placeholder="Yeni alan adı" required />
        </div>
        <button className="btn" type="submit">Ekle</button>
      </form>

      {gosterilecekler.length === 0 ? (
        <div className="bos-durum">Bu filtreye uyan dal yok.</div>
      ) : (
        gosterilecekler.map((d) => <DalKarti key={d.id} dal={d} onDurumGuncelle={durumGuncelle} />)
      )}
    </div>
  )
}
