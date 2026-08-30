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

const DURUM_ETIKET = { bekliyor: 'Onay Bekliyor', onaylandi: 'Canlıda', reddedildi: 'Reddedildi' }
const DURUM_RENK = { bekliyor: 'bdg-prog', onaylandi: 'bdg-done', reddedildi: 'bdg-lock' }

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

export default function PipelineDurumuSayfasi() {
  const { rol } = useAdminAuth()
  const suAdminMi = rol === 'super_admin'

  const [taslaklar, setTaslaklar] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [sonYukleme, setSonYukleme] = useState(null)
  const [hata, setHata] = useState(null)
  const [islemGrubu, setIslemGrubu] = useState(null)

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
          Meslek↔bölüm eşleştirme pipeline'ı kendi bilgisayarınızda çalışır. Çıktı CSV'sini buradan yükleyin —
          canlıya yansımadan önce burada önizleyip onaylarsınız.
        </div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}

      <div style={{ marginBottom: 20 }}>
        <MeslekYuklemeKarti />
      </div>

      <div className="card">
        <div className="ct">Yeni Çıktı Yükle</div>
        <div className="ps" style={{ margin: '0 0 12px' }}>
          bolum_agirliklari.csv dosyasını (bolum_adi, degisken_kod, agirlik_degeri, yakinsama_skoru,
          agirlikli_varyans, etkin_meslek_sayisi sütunlarıyla) seçin. Bu adım canlı veriye hiç dokunmaz.
        </div>
        <label className="btn" style={{ cursor: yukleniyor ? 'not-allowed' : 'pointer', opacity: yukleniyor ? 0.6 : 1 }}>
          {yukleniyor ? <span className="spin" /> : '⬆ CSV Seç ve Yükle'}
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

      <div className="ct" style={{ marginTop: 20 }}>Geçmiş Yüklemeler</div>
      {!taslaklar ? (
        <div className="bos-durum">Yükleniyor…</div>
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
    </div>
  )
}
