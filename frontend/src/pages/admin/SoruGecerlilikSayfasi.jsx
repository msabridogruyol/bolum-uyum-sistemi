import { useEffect, useState } from 'react'
import { api } from '../../api/client'

// [DÜZELTME] Önceki sürüm script etiketini ekleyip HİÇ BEKLEMİYORDU — kullanıcı
// script tam inmeden butona basarsa "kütüphane yüklenemedi" hatası çıkıyordu
// (yarış durumu). Bu sürüm gerçek bir Promise ile yüklenmenin bitmesini bekliyor
// ve CDN başarısız olursa (ağ engeli vb.) bunu AÇIKÇA hata olarak bildiriyor.
let xlsxYuklemeSozu = null
function xlsxYukle() {
  if (typeof window !== 'undefined' && window.XLSX) return Promise.resolve()
  if (xlsxYuklemeSozu) return xlsxYuklemeSozu
  xlsxYuklemeSozu = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js'
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => {
      xlsxYuklemeSozu = null  // tekrar denenebilsin diye sıfırla
      reject(new Error('Excel kütüphanesi (cdnjs.cloudflare.com) yüklenemedi — ağ/güvenlik duvarı engelliyor olabilir.'))
    }
    document.body.appendChild(script)
  })
  return xlsxYuklemeSozu
}

function xlsxDisaAktar(dosyaAdi, basliklar, satirlar) {
  const XLSX = window.XLSX
  if (!XLSX) {
    throw new Error('Excel kütüphanesi henüz hazır değil — birkaç saniye bekleyip tekrar deneyin.')
  }
  const ws = XLSX.utils.aoa_to_sheet([basliklar, ...satirlar])
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Veri')
  XLSX.writeFile(wb, dosyaAdi)
}

function dosyayiAyristir(dosya) {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.XLSX) {
      reject(new Error('Excel kütüphanesi henüz hazır değil — birkaç saniye bekleyip tekrar deneyin.'))
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
  const idx = Object.fromEntries(baslik.map((b, i) => [b, i]))
  const bul = (hucreler, ad) => (idx[ad] >= 0 ? hucreler[idx[ad]] : undefined)

  return hamSatirlar.slice(1).map((hucreler) => {
    const secenekIdHam = bul(hucreler, 'secenek_id')
    return {
      birim_anahtari: String(bul(hucreler, 'birim_anahtari') ?? ''),
      kaynak_soru_id: parseInt(bul(hucreler, 'kaynak_soru_id'), 10),
      secenek_id: secenekIdHam !== undefined && secenekIdHam !== '' ? parseInt(secenekIdHam, 10) : null,
      gercek_degisken_kod: String(bul(hucreler, 'gercek_degisken_kod') ?? ''),
      model_a_tahmin: String(bul(hucreler, 'model_a_tahmin') ?? ''),
      model_a_dogru: String(bul(hucreler, 'model_a_dogru')).toLowerCase() === 'true',
      model_a_benzerlik: parseFloat(bul(hucreler, 'model_a_benzerlik')),
      model_b_tahmin: String(bul(hucreler, 'model_b_tahmin') ?? ''),
      model_b_dogru: String(bul(hucreler, 'model_b_dogru')).toLowerCase() === 'true',
      model_b_benzerlik: parseFloat(bul(hucreler, 'model_b_benzerlik')),
      model_c_tahmin: String(bul(hucreler, 'model_c_tahmin') ?? ''),
      model_c_dogru: String(bul(hucreler, 'model_c_dogru')).toLowerCase() === 'true',
      model_c_benzerlik: parseFloat(bul(hucreler, 'model_c_benzerlik')),
    }
  }).filter((s) => !isNaN(s.kaynak_soru_id) && s.gercek_degisken_kod)
}

export default function SoruGecerlilikSayfasi() {
  const [ozet, setOzet] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [disaAktariliyor, setDisaAktariliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [filtre, setFiltre] = useState('hepsi') // hepsi | sorunlu
  const [tipFiltre, setTipFiltre] = useState('hepsi') // hepsi | likert | sjt
  const [temizlemeYaziliOnay, setTemizlemeYaziliOnay] = useState('')
  const [temizlemeSekmesiAcik, setTemizlemeSekmesiAcik] = useState(false)
  const [temizleniyor, setTemizleniyor] = useState(false)
  const [analiz, setAnaliz] = useState(null)

  // [DÜZELTME] Artık burada arka planda "fire and forget" yüklemiyoruz —
  // her işlem (indirme/yükleme) kendi başında xlsxYukle()'yi bekliyor.
  // Yine de sayfa açılır açılmaz indirmeyi başlatmak için erken tetikleriz.
  useEffect(() => { xlsxYukle().catch(() => {}) }, [])

  function yukle() {
    api.soruGecerlilikGetir().then(setOzet).catch(() => setOzet(null))
    api.gecerlilikAnaliziniGetir().then(setAnaliz).catch(() => setAnaliz(null))
  }

  useEffect(() => { yukle() }, [])

  async function sonuclariTemizle() {
    if (temizlemeYaziliOnay.trim().toUpperCase() !== 'SİL') return
    setTemizleniyor(true)
    setHata(null)
    try {
      await api.gecerlilikSonuclariniTemizle()
      setTemizlemeYaziliOnay('')
      setTemizlemeSekmesiAcik(false)
      setAnaliz(null)
      yukle()
    } catch (err) {
      setHata(err.detail || 'Temizleme başarısız.')
    } finally {
      setTemizleniyor(false)
    }
  }

  async function testGirdisiniIndir() {
    setDisaAktariliyor(true)
    setHata(null)
    try {
      await xlsxYukle()
      const birimler = await api.gecerlilikTestGirdisiGetirV2()
      if (birimler.length === 0) {
        throw new Error('Test edilecek aktif soru/seçenek bulunamadı.')
      }
      xlsxDisaAktar(
        'gecerlilik_girdisi.xlsx',
        ['birim_anahtari', 'kaynak_soru_id', 'secenek_id', 'kaynak_tipi', 'katman_kod', 'metin', 'baglam', 'beklenen_degisken_kod'],
        birimler.map((b) => [b.birim_anahtari, b.kaynak_soru_id, b.secenek_id ?? '', b.kaynak_tipi, b.katman_kod, b.metin, b.baglam, b.beklenen_degisken_kod]),
      )
    } catch (err) {
      setHata(err.detail || err.message || 'Test girdisi alınamadı.')
    } finally {
      setDisaAktariliyor(false)
    }
  }

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    setHata(null)
    setYukleniyor(true)
    try {
      await xlsxYukle()
      const hamSatirlar = await dosyayiAyristir(dosya)
      const satirlar = satirlariDondur(hamSatirlar)
      if (satirlar.length === 0) {
        throw new Error('Dosya okunamadı — soru_gecerlilik_testi.py çıktısını yüklediğinizden emin olun.')
      }
      await api.soruGecerlilikYukle(satirlar)
      yukle()
    } catch (err) {
      setHata(err.detail || err.message || 'Yükleme başarısız.')
    } finally {
      setYukleniyor(false)
      e.target.value = ''
    }
  }

  const gosterilecekler = !ozet ? [] : ozet.sonuclar
    .filter((s) => filtre === 'hepsi' || s.kac_model_dogru < 3)
    .filter((s) => tipFiltre === 'hepsi' || s.kaynak_tipi === tipFiltre)

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Soru Geçerlilik Testi</div>
        <div className="ps">
          Her test biriminin (Likert sorusu ya da SJT seçeneği) metni, hangi değişkene ait olduğu gizlenerek
          3 bağımsız dil modeline veriliyor — model doğru değişkene mi bağlıyor?
        </div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}

      <div className="card">
        <div className="ct">1. Adım — Test Girdisini İndir</div>
        <div className="ps" style={{ margin: '0 0 12px' }}>
          Tüm aktif Likert sorularını ve SJT seçeneklerini (kaynak metinleriyle) CSV olarak indirir.
        </div>
        <button className="btn" onClick={testGirdisiniIndir} disabled={disaAktariliyor}>
          {disaAktariliyor ? <span className="spin" /> : '⬇ Test Girdisini İndir'}
        </button>
      </div>

      <div className="card">
        <div className="ct">2. Adım — Sonucu Yükle</div>
        <div className="ps" style={{ margin: '0 0 12px' }}>
          İndirdiğiniz dosyayı <code>C:\pipeline\veri\gecerlilik_girdisi.xlsx</code> olarak kaydedip
          <code> python soru_gecerlilik_testi.py</code> çalıştırın. Çıkan
          <code> soru_gecerlilik_sonuclari.xlsx</code>'i buradan yükleyin.
        </div>
        <label className="btn" style={{ cursor: yukleniyor ? 'not-allowed' : 'pointer', opacity: yukleniyor ? 0.6 : 1 }}>
          {yukleniyor ? <span className="spin" /> : '⬆ Sonuç CSV Yükle'}
          <input type="file" accept=".xlsx,.xls,.csv" onChange={dosyaSecildi} disabled={yukleniyor} style={{ display: 'none' }} />
        </label>
      </div>

      {ozet && (
        <div className="card" style={{ marginTop: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="ct" style={{ margin: 0 }}>Ekrandaki Sonuçları Temizle</div>
            <button
              className="btn sec"
              style={{ color: 'var(--re)', borderColor: 'var(--re)' }}
              onClick={() => setTemizlemeSekmesiAcik((a) => !a)}
            >
              {temizlemeSekmesiAcik ? 'Kapat' : '🗑 Temizle'}
            </button>
          </div>
          {temizlemeSekmesiAcik && (
            <div style={{ marginTop: 12 }}>
              <div className="ps" style={{ margin: '0 0 10px' }}>
                Bu, ekrandaki <b>{ozet.toplam_birim} sonucun tamamını</b> kalıcı olarak siler (sorulara dokunmaz,
                yalnızca test sonuçlarını temizler). Devam etmek için aşağıya <b>SİL</b> yazın:
              </div>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <input
                  className="auth-input"
                  style={{ width: 140 }}
                  value={temizlemeYaziliOnay}
                  onChange={(e) => setTemizlemeYaziliOnay(e.target.value)}
                  placeholder="SİL"
                  autoComplete="off"
                />
                <button
                  className="btn"
                  style={{ background: 'var(--re)', borderColor: 'var(--re)' }}
                  disabled={temizlemeYaziliOnay.trim().toUpperCase() !== 'SİL' || temizleniyor}
                  onClick={sonuclariTemizle}
                >
                  {temizleniyor ? <span className="spin" /> : 'Evet, Hepsini Sil'}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {!ozet ? (
        <div className="bos-durum">Henüz hiç test sonucu yüklenmedi.</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 18 }}>
            <div className="sc"><div className="sl">Toplam Birim</div><div className="sv">{ozet.toplam_birim}</div></div>
            <div className="sc"><div className="sl">Tam Doğru (3/3)</div><div className="sv gr">{ozet.tam_dogru}</div></div>
            <div className="sc"><div className="sl">Kısmi (1-2/3)</div><div className="sv" style={{ color: 'var(--am)' }}>{ozet.kismi_dogru}</div></div>
            <div className="sc"><div className="sl">Hiç Doğru Değil (0/3)</div><div className="sv" style={{ color: 'var(--re)' }}>{ozet.hic_dogru_degil}</div></div>
          </div>

          {analiz && (
            <div className="card" style={{ marginBottom: 18 }}>
              <div className="ct">Katman Bazlı Geçerlilik Analizi</div>
              <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.7, marginBottom: 12 }}>
                <p style={{ margin: '0 0 8px' }}>
                  <b>Ölçüt:</b> 3 bağımsız dil modelinden en az 2'sinin aynı değişkeni işaret etmesi
                  (tam 3/3 konsensüs aranmaz — topluluk/çoğunluk kararı yöntemi). Bu, üç bağımsız
                  "değerlendiricinin" (model) bir soruyu aynı kategoriye atamasını ölçen bir
                  <b> gözlemciler arası uyum (inter-rater agreement)</b> değerlendirmesidir.
                </p>
                <p style={{ margin: '0 0 8px' }}>
                  <b>Eşik değerlerin kaynağı:</b> Gözlemciler arası uyum literatüründe <b>%70</b>, kabul
                  edilebilir minimum eşik olarak önerilir (Stemler, 2004). <b>%75-80</b> aralığı ise
                  "tatmin edici/kabul edilebilir" uyum düzeyi olarak yaygın kabul görür (Graham,
                  Milanowski &amp; Miller, 2012; McHugh, 2012) ve Landis &amp; Koch'un (1977) kappa
                  sınıflandırmasında "önemli ölçüde – neredeyse mükemmel" uyum kategorisine karşılık
                  gelir. Bu nedenle her <b>katman</b> kendi içinde en az <b>%{analiz.katman_esigi_yuzde}</b>'e
                  (minimum kabul edilebilir eşik), sistemin <b>genel ortalaması</b> ise en az
                  <b> %{analiz.genel_esik_yuzde}</b>'e (tatmin edici düzey) ulaşmalıdır.
                </p>
                <p style={{ margin: 0 }}>
                  "Rastgele Baseline" sütunu, üç modelin şansla en az ikisinin aynı adayı seçme
                  ihtimalini, o katmandaki gerçek aday sayısına göre matematiksel olarak hesaplar —
                  gerçek oranın bu şans seviyesine ne kadar yakın ya da uzak olduğunu görmek için
                  referans noktasıdır.
                </p>
              </div>

              <div style={{
                display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14,
                padding: '10px 14px', borderRadius: 10,
                background: analiz.genel_gecerli_mi ? 'var(--grl)' : 'var(--rel)',
              }}>
                <span className={`bdg ${analiz.genel_gecerli_mi ? 'bdg-done' : 'bdg-lock'}`}>
                  {analiz.genel_gecerli_mi ? 'Sistem Geneli Geçerli' : 'Sistem Geneli Eşiğin Altında'}
                </span>
                <span style={{ fontSize: 12.5, fontWeight: 700 }}>
                  Genel ortalama: %{analiz.genel_en_az_2_3_orani} (eşik: %{analiz.genel_esik_yuzde})
                </span>
              </div>
              <table style={{ width: '100%', fontSize: 12.5, borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1.5px solid var(--bor)' }}>
                    <th style={{ textAlign: 'left', padding: '6px 8px' }}>Katman</th>
                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Birim</th>
                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>≥2/3 Doğru</th>
                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Rastgele Baseline</th>
                    <th style={{ textAlign: 'right', padding: '6px 8px' }}>Kaç Kat Üstü</th>
                    <th style={{ textAlign: 'center', padding: '6px 8px' }}>Durum</th>
                  </tr>
                </thead>
                <tbody>
                  {analiz.katmanlar.map((k) => (
                    <tr key={k.katman_kod} style={{ borderBottom: '1px solid var(--bor)' }}>
                      <td style={{ padding: '7px 8px', fontWeight: 700 }}>{k.katman_kod}</td>
                      <td style={{ padding: '7px 8px', textAlign: 'right', color: 'var(--tx2)' }}>{k.toplam_birim}</td>
                      <td style={{ padding: '7px 8px', textAlign: 'right', fontWeight: 700 }}>
                        {k.en_az_2_3_orani}% <span style={{ color: 'var(--tx3)', fontWeight: 400 }}>({k.en_az_2_3_sayisi}/{k.toplam_birim})</span>
                      </td>
                      <td style={{ padding: '7px 8px', textAlign: 'right', color: 'var(--tx3)' }}>{k.rastgele_baseline_orani}%</td>
                      <td style={{ padding: '7px 8px', textAlign: 'right', fontWeight: 700, color: 'var(--pu)' }}>{k.kac_kat_ustu}x</td>
                      <td style={{ padding: '7px 8px', textAlign: 'center' }}>
                        <span className={`bdg ${k.geçerli_mi ? 'bdg-done' : 'bdg-lock'}`}>{k.geçerli_mi ? 'Geçerli' : 'Geçersiz'}</span>
                      </td>
                    </tr>
                  ))}
                  <tr>
                    <td style={{ padding: '9px 8px', fontWeight: 800 }}>Genel</td>
                    <td style={{ padding: '9px 8px', textAlign: 'right', fontWeight: 700 }}>{analiz.genel_toplam_birim}</td>
                    <td style={{ padding: '9px 8px', textAlign: 'right', fontWeight: 800 }}>{analiz.genel_en_az_2_3_orani}%</td>
                    <td colSpan={3}></td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
            <button className={filtre === 'hepsi' ? 'btn' : 'btn sec'} onClick={() => setFiltre('hepsi')}>Tümü</button>
            <button className={filtre === 'sorunlu' ? 'btn' : 'btn sec'} onClick={() => setFiltre('sorunlu')}>
              Yalnızca Sorunlu ({ozet.kismi_dogru + ozet.hic_dogru_degil})
            </button>
            <select className="auth-input" style={{ width: 160 }} value={tipFiltre} onChange={(e) => setTipFiltre(e.target.value)}>
              <option value="hepsi">Tüm Tipler</option>
              <option value="likert">Yalnızca Likert</option>
              <option value="sjt">Yalnızca SJT</option>
            </select>
          </div>

          <div className="ll">
            {gosterilecekler.map((s) => (
              <div key={s.secenek_id ? `sec-${s.secenek_id}` : `soru-${s.soru_id}`} className="lc" style={{ flexDirection: 'column', alignItems: 'stretch', cursor: 'default' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <div style={{ flex: 1 }}>
                    <div className="lt">
                      {s.test_edilen_metin}
                      {s.kaynak_tipi === 'sjt' && <span className="bdg bdg-prog" style={{ marginLeft: 8, fontSize: 10 }}>SJT seçeneği</span>}
                    </div>
                    {s.kaynak_tipi === 'sjt' && (
                      <div className="ld" style={{ fontStyle: 'italic' }}>Senaryo: {s.soru_metni}</div>
                    )}
                    <div className="ld">{s.katman_kod} · Beklenen değişken: <b>{s.gercek_degisken_kod}</b></div>
                  </div>
                  <span className={`bdg ${s.kac_model_dogru === 3 ? 'bdg-done' : s.kac_model_dogru === 0 ? 'bdg-lock' : 'bdg-prog'}`}>
                    {s.kac_model_dogru}/3 model doğru
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                  {[
                    { ad: 'Model A', tahmin: s.model_a_tahmin, dogru: s.model_a_dogru },
                    { ad: 'Model B', tahmin: s.model_b_tahmin, dogru: s.model_b_dogru },
                    { ad: 'Model C', tahmin: s.model_c_tahmin, dogru: s.model_c_dogru },
                  ].map((m) => (
                    <div key={m.ad} style={{ fontSize: 11.5, padding: '6px 10px', borderRadius: 8, background: m.dogru ? 'var(--grl)' : 'var(--rel, #fdecea)' }}>
                      <b>{m.ad}:</b> {m.tahmin} {m.dogru ? '✓' : '✗'}
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {gosterilecekler.length === 0 && <div className="bos-durum">Bu filtreye uyan birim yok.</div>}
          </div>
        </>
      )}
    </div>
  )
}
