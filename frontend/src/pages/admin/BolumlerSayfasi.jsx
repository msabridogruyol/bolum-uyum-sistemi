import { useEffect, useState, useCallback } from 'react'
import { api } from '../../api/client'

const GECISLER = { taslak: ['test_ediliyor'], test_ediliyor: ['yayinda', 'taslak'], yayinda: [] }
const DURUM_ETIKET = { taslak: 'Taslak', test_ediliyor: 'Test Ediliyor', yayinda: 'Yayında' }
const DURUM_RENK = { taslak: 'bdg-lock', test_ediliyor: 'bdg-prog', yayinda: 'bdg-done' }

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
  const adIdx = baslik.indexOf('ad')
  const aciklamaIdx = baslik.indexOf('kisa_aciklama')
  if (adIdx === -1 || aciklamaIdx === -1) return []

  return satirlar.slice(1).map((satir) => {
    // basit CSV ayrıştırma — tırnak içindeki virgülleri koru
    const parcalar = []
    let mevcut = ''
    let tirnakIci = false
    for (const karakter of satir) {
      if (karakter === '"') tirnakIci = !tirnakIci
      else if (karakter === ',' && !tirnakIci) { parcalar.push(mevcut); mevcut = '' }
      else mevcut += karakter
    }
    parcalar.push(mevcut)
    return { ad: parcalar[adIdx]?.trim(), kisa_aciklama: parcalar[aciklamaIdx]?.trim() }
  }).filter((s) => s.ad && s.kisa_aciklama)
}

export default function BolumlerSayfasi() {
  const [bolumler, setBolumler] = useState(null)
  const [hata, setHata] = useState(null)
  const [gerekceModal, setGerekceModal] = useState(null)
  const [gerekceMetni, setGerekceMetni] = useState('')
  const [aramaMetni, setAramaMetni] = useState('')

  const [duzenlemeId, setDuzenlemeId] = useState(null)
  const [duzenlemeMetni, setDuzenlemeMetni] = useState('')
  const [kaydediliyor, setKaydediliyor] = useState(false)

  const [topluYukleniyor, setTopluYukleniyor] = useState(false)
  const [topluSonuc, setTopluSonuc] = useState(null)

  const yukle = useCallback(() => {
    api.bolumleriListele().then(setBolumler).catch((e) => setHata(e.detail || 'Bölümler yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  async function gecisiOnayla() {
    try {
      await api.bolumDurumDegistir(gerekceModal.bolumId, gerekceModal.yeniDurum, gerekceMetni)
      setGerekceModal(null)
      setGerekceMetni('')
      yukle()
    } catch (err) {
      setHata(err.detail || 'Durum değiştirilemedi.')
    }
  }

  function duzenlemeyeBasla(b) {
    setDuzenlemeId(b.id)
    setDuzenlemeMetni(b.kisa_aciklama || '')
  }

  async function aciklamayiKaydet(bolumId) {
    if (!duzenlemeMetni.trim()) {
      setHata('Açıklama boş olamaz.')
      return
    }
    setKaydediliyor(true)
    try {
      await api.bolumAciklamaGuncelle(bolumId, duzenlemeMetni.trim())
      setDuzenlemeId(null)
      yukle()
    } catch (err) {
      setHata(err.detail || 'Açıklama kaydedilemedi.')
    } finally {
      setKaydediliyor(false)
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
        throw new Error('CSV okunamadı — "ad" ve "kisa_aciklama" sütunları gerekli.')
      }
      const sonuc = await api.bolumAciklamalariniTopluGuncelle(satirlar)
      setTopluSonuc(sonuc)
      yukle()
    } catch (err) {
      setHata(err.detail || err.message || 'Toplu yükleme başarısız.')
    } finally {
      setTopluYukleniyor(false)
      e.target.value = ''
    }
  }

  if (hata && !bolumler) return <div className="pg pg-genis"><div className="bos-durum">{hata}</div></div>
  if (!bolumler) return <div className="pg pg-genis"><div className="bos-durum">Yükleniyor…</div></div>

  const filtrelenmis = bolumler.filter((b) => b.ad.toLowerCase().includes(aramaMetni.toLowerCase()))

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Bölümler</div>
        <div className="ps">Taslak → Test Ediliyor → Yayında akışı ve öğrenciye gösterilen kısa açıklamalar buradan yönetilir.</div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}

      <div className="card">
        <div className="ct">Toplu Açıklama Yönetimi</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button
            className="btn sec"
            onClick={() => csvDisaAktar(
              'bolumler_disa_aktarim.csv',
              ['ad', 'durum', 'kisa_aciklama'],
              bolumler.map((b) => [b.ad, b.durum, b.kisa_aciklama || '']),
            )}
          >
            ⬇ CSV Dışa Aktar
          </button>
          <label className="btn" style={{ cursor: topluYukleniyor ? 'not-allowed' : 'pointer', opacity: topluYukleniyor ? 0.6 : 1 }}>
            {topluYukleniyor ? <span className="spin" /> : '⬆ CSV İçe Aktar (ad, kisa_aciklama)'}
            <input type="file" accept=".csv" onChange={dosyaSecildi} disabled={topluYukleniyor} style={{ display: 'none' }} />
          </label>
        </div>
        {topluSonuc && (
          <div style={{ marginTop: 12, fontSize: 12.5 }}>
            <b style={{ color: 'var(--gr)' }}>{topluSonuc.guncellenen} bölüm güncellendi.</b>
            {topluSonuc.eslesmeyenler.length > 0 && (
              <div style={{ color: 'var(--am)', marginTop: 4 }}>
                Eşleşmeyen {topluSonuc.eslesmeyenler.length} ad: {topluSonuc.eslesmeyenler.slice(0, 5).join(', ')}
                {topluSonuc.eslesmeyenler.length > 5 && '...'}
              </div>
            )}
          </div>
        )}
      </div>

      <input
        className="auth-input"
        style={{ marginBottom: 14 }}
        value={aramaMetni}
        onChange={(e) => setAramaMetni(e.target.value)}
        placeholder="Bölüm ara..."
      />

      {gerekceModal && (
        <div className="card" style={{ borderColor: 'var(--pu)', background: 'var(--pul)' }}>
          <div className="ct">Gerekçe Gerekli</div>
          <textarea
            className="auth-input"
            style={{ width: '100%', minHeight: 70, marginBottom: 10 }}
            value={gerekceMetni}
            onChange={(e) => setGerekceMetni(e.target.value)}
            placeholder="Bu geçişin gerekçesini yaz..."
          />
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn" onClick={gecisiOnayla} disabled={!gerekceMetni.trim()}>Onayla</button>
            <button className="btn sec" onClick={() => setGerekceModal(null)}>Vazgeç</button>
          </div>
        </div>
      )}

      <div className="ll">
        {filtrelenmis.map((b) => (
          <div key={b.id} className="lc" style={{ cursor: 'default', alignItems: 'flex-start' }}>
            <div className="lb-wrap">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <div className="lt">{b.ad}</div>
                <span className={`bdg ${DURUM_RENK[b.durum]}`}>{DURUM_ETIKET[b.durum]}</span>
              </div>

              {duzenlemeId === b.id ? (
                <div style={{ marginTop: 4 }}>
                  <textarea
                    className="auth-input"
                    style={{ width: '100%', minHeight: 60, fontFamily: 'var(--fn)' }}
                    value={duzenlemeMetni}
                    onChange={(e) => setDuzenlemeMetni(e.target.value)}
                    placeholder="Öğrenciye Keşfet ekranında gösterilecek kısa açıklama..."
                  />
                  <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <button className="btn" onClick={() => aciklamayiKaydet(b.id)} disabled={kaydediliyor}>
                      {kaydediliyor ? <span className="spin" /> : 'Kaydet'}
                    </button>
                    <button className="btn sec" onClick={() => setDuzenlemeId(null)}>Vazgeç</button>
                  </div>
                </div>
              ) : (
                <div
                  onClick={() => duzenlemeyeBasla(b)}
                  style={{ fontSize: 12.5, color: b.kisa_aciklama ? 'var(--tx2)' : 'var(--tx3)', cursor: 'pointer', fontStyle: b.kisa_aciklama ? 'normal' : 'italic' }}
                >
                  {b.kisa_aciklama || 'Açıklama yok — eklemek için tıkla'} <span style={{ color: 'var(--pu)', fontSize: 11 }}>✏️ düzenle</span>
                </div>
              )}

              {b.test_notu && duzenlemeId !== b.id && (
                <div className="ld" style={{ marginTop: 6 }}>Not: {b.test_notu}</div>
              )}
            </div>

            {duzenlemeId !== b.id && (
              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                {GECISLER[b.durum].map((yeniDurum) => (
                  <button
                    key={yeniDurum}
                    className="btn sec"
                    onClick={() => { setGerekceModal({ bolumId: b.id, yeniDurum }); setGerekceMetni('') }}
                  >
                    → {DURUM_ETIKET[yeniDurum]}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {filtrelenmis.length === 0 && <div className="bos-durum">Sonuç bulunamadı.</div>}
      </div>
    </div>
  )
}
