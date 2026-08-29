import { useEffect, useState } from 'react'
import { api } from '../../api/client'

function csvSatirlariniAyristir(metin) {
  const satirlar = metin.split(/\r?\n/).filter((s) => s.trim().length > 0)
  if (satirlar.length < 2) return []
  const baslik = satirlar[0].split(',').map((s) => s.trim())
  const idx = Object.fromEntries(baslik.map((b, i) => [b, i]))

  return satirlar.slice(1).map((satir) => {
    const p = satir.split(',')
    const bul = (ad) => p[idx[ad]]?.trim()
    return {
      soru_id: parseInt(bul('soru_id'), 10),
      gercek_degisken_kod: bul('gercek_degisken_kod'),
      model_a_tahmin: bul('model_a_tahmin'),
      model_a_dogru: bul('model_a_dogru')?.toLowerCase() === 'true',
      model_a_benzerlik: parseFloat(bul('model_a_benzerlik')),
      model_b_tahmin: bul('model_b_tahmin'),
      model_b_dogru: bul('model_b_dogru')?.toLowerCase() === 'true',
      model_b_benzerlik: parseFloat(bul('model_b_benzerlik')),
      model_c_tahmin: bul('model_c_tahmin'),
      model_c_dogru: bul('model_c_dogru')?.toLowerCase() === 'true',
      model_c_benzerlik: parseFloat(bul('model_c_benzerlik')),
    }
  }).filter((s) => !isNaN(s.soru_id) && s.gercek_degisken_kod)
}

export default function SoruGecerlilikSayfasi() {
  const [ozet, setOzet] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [filtre, setFiltre] = useState('hepsi') // hepsi | sorunlu

  function yukle() {
    api.soruGecerlilikGetir().then(setOzet).catch(() => setOzet(null))
  }

  useEffect(() => { yukle() }, [])

  async function dosyaSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    setHata(null)
    setYukleniyor(true)
    try {
      const metin = await dosya.text()
      const satirlar = csvSatirlariniAyristir(metin)
      if (satirlar.length === 0) {
        throw new Error('CSV okunamadı — soru_gecerlilik_testi.py çıktısını yüklediğinizden emin olun.')
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

  const gosterilecekler = !ozet ? [] : (
    filtre === 'sorunlu' ? ozet.sonuclar.filter((s) => s.kac_model_dogru < 3) : ozet.sonuclar
  )

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Soru Geçerlilik Testi</div>
        <div className="ps">
          Her sorunun metni, hangi değişkene ait olduğu gizlenerek 3 bağımsız dil modeline veriliyor —
          model soruyu doğru değişkene mi bağlıyor? 3/3 uyuşma = yüksek güven, uyuşmazlık = revizyon adayı.
        </div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}

      <div className="card">
        <div className="ct">Yeni Test Sonucu Yükle</div>
        <div className="ps" style={{ margin: '0 0 12px' }}>
          Bilgisayarınızda <code>soru_gecerlilik_testi.py</code>'yi çalıştırıp ürettiği
          <code> soru_gecerlilik_sonuclari.csv</code> dosyasını seçin.
        </div>
        <label className="btn" style={{ cursor: yukleniyor ? 'not-allowed' : 'pointer', opacity: yukleniyor ? 0.6 : 1 }}>
          {yukleniyor ? <span className="spin" /> : '⬆ CSV Yükle'}
          <input type="file" accept=".csv" onChange={dosyaSecildi} disabled={yukleniyor} style={{ display: 'none' }} />
        </label>
      </div>

      {!ozet ? (
        <div className="bos-durum">Henüz hiç test sonucu yüklenmedi.</div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 18 }}>
            <div className="sc"><div className="sl">Toplam Soru</div><div className="sv">{ozet.toplam_soru}</div></div>
            <div className="sc"><div className="sl">Tam Doğru (3/3)</div><div className="sv gr">{ozet.tam_dogru}</div></div>
            <div className="sc"><div className="sl">Kısmi (1-2/3)</div><div className="sv" style={{ color: 'var(--am)' }}>{ozet.kismi_dogru}</div></div>
            <div className="sc"><div className="sl">Hiç Doğru Değil (0/3)</div><div className="sv" style={{ color: 'var(--re)' }}>{ozet.hic_dogru_degil}</div></div>
          </div>

          <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
            <button className={filtre === 'hepsi' ? 'btn' : 'btn sec'} onClick={() => setFiltre('hepsi')}>Tümü</button>
            <button className={filtre === 'sorunlu' ? 'btn' : 'btn sec'} onClick={() => setFiltre('sorunlu')}>
              Yalnızca Sorunlu ({ozet.kismi_dogru + ozet.hic_dogru_degil})
            </button>
          </div>

          <div className="ll">
            {gosterilecekler.map((s) => (
              <div key={s.soru_id} className="lc" style={{ flexDirection: 'column', alignItems: 'stretch', cursor: 'default' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                  <div style={{ flex: 1 }}>
                    <div className="lt">{s.soru_metni}</div>
                    <div className="ld">{s.katman_kod} · Gerçek değişken: <b>{s.gercek_degisken_kod}</b></div>
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
            {gosterilecekler.length === 0 && <div className="bos-durum">Bu filtreye uyan soru yok.</div>}
          </div>
        </>
      )}
    </div>
  )
}
