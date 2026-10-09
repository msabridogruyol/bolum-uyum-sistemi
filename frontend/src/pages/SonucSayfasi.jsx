import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import BolumAdi from '../components/BolumAdi'

// [2026-10-09] "Neden bu bölüm?" — madde madde: örtüşen yönler (sende / bölümde düzeyi + seçtiğin cevaplar),
// alan sorularındaki iş türü uyumu ve varsa dikkat edilecek nokta.
function NedenDetay({ d }) {
  const ortusen = d.ortusen || []
  if (!ortusen.length && !d.k5 && !d.dikkat) return null
  return (
    <div className="neden-kutu">
      <div className="neden-baslik">Neden bu bölüm?</div>
      {ortusen.length > 0 && (
        <ul className="neden-liste">
          {ortusen.map((x, k) => (
            <li key={k}>
              <div className="neden-satir">
                <span className="neden-ozellik">{x.ozellik}</span>
                <span className="neden-etiket sen">Sende: {x.sen}</span>
                <span className="neden-etiket bolum">Bölüm: {x.bolum}</span>
              </div>
              {x.kanitlar && x.kanitlar.length > 0 && (
                <div className="neden-kanit">
                  Bu yönü öne çıkaran seçimlerin:{' '}
                  {x.kanitlar.map((m, i) => <q key={i}>{m}</q>)}
                  {x.kanit_sayisi > x.kanitlar.length && <span className="neden-ek"> +{x.kanit_sayisi - x.kanitlar.length} seçim daha</span>}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      {d.k5 && (
        <div className={`neden-not ${d.k5.durum === 'uyumlu' ? 'iyi' : 'zayif'}`}>
          🌻 {d.k5.durum === 'uyumlu'
            ? <>Alan sorularında <b>{d.k5.is_turu}</b> işlerini öne çıkardın — bu bölümün ana uğraşı.</>
            : <>Bu bölümün ana uğraşı <b>{d.k5.is_turu}</b>; alan sorularında bu işleri daha az seçtin. Bölüm bilgisine göz atmanı öneririz.</>}
          {d.k5.kanit && <div className="neden-kanit" style={{ marginTop: 4 }}>Seçimin: <q>{d.k5.kanit}</q></div>}
        </div>
      )}
      {d.dikkat && <div className="neden-not zayif">⚠️ {d.dikkat.metin}</div>}
    </div>
  )
}

export default function SonucSayfasi() {
  const [siralama, setSiralama] = useState(null)
  const [ozet, setOzet] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.durumOzetiGetir().then(setOzet).catch(() => {})
    api.siralamaGetir(20).then(setSiralama).catch((e) => setHata(e.detail || 'Sıralama alınamadı.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!siralama || !ozet) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Bölüm Uyum Sonuçların</div>
        <div className="ps">
          Şu anki cevaplarına göre en güçlü uyum gösterdiğin bölümler — bu bir kehanet değil, anlık bir
          yansıtma; profilin zamanla değişebilir.
        </div>
      </div>

      {siralama.length === 0 ? (
        <>
          <div className="taslak-onizleme">
            <div className="taslak-onizleme-icerik ob-grid">
              {[94, 88, 82, 77, 71, 66, 60, 55, 50, 46, 42, 38].map((genislik, i) => (
                <div key={i} className="ob-card">
                  <div className="ob-top">
                    <div className={`ob-rank${i < 3 ? ' top' : ''}`}>{i + 1}</div>
                    <div className="ob-body"><div className="iskelet-satir" style={{ width: '65%' }} /></div>
                    <div className="ob-score">%{genislik}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="taslak-onizleme-overlay">
              <div className="to-ikon">🌟</div>
              <div className="to-metin">
                Sonuçların, K1-K4'ün tamamı bitince burada görünecek — şu an {ozet.tamamlanan_katman_sayisi}/{ozet.toplam_ana_katman_sayisi} katman tamamlandı.
              </div>
            </div>
          </div>
          <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/katmanlar')}>
            {ozet.tamamlanan_katman_sayisi === 0 ? 'Yolculuğuna Başla' : 'Kaldığın Yerden Devam Et'} →
          </button>
        </>
      ) : (
        <div className="ob-grid sonuc-grid">
          {siralama.map((s, i) => (
            <div key={s.bolum_id} className="ob-card">
              <div className="ob-top">
                <div className={`ob-rank${i < 3 ? ' top' : ''}`}>{i + 1}</div>
                <div className="ob-body">
                  <div className="ob-name"><BolumAdi id={s.bolum_id} ad={s.bolum_adi} /></div>
                  {s.alan && <div style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>{s.alan}</div>}
                </div>
                <div className="ob-score">%{Math.round(s.toplam_uyum)}</div>
              </div>
              {s.neden_detay ? (
                <NedenDetay d={s.neden_detay} />
              ) : s.neden && s.neden.length > 0 && (
                <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(127,127,127,0.18)' }}>
                  <div style={{ fontSize: 12, fontWeight: 600, opacity: 0.75, marginBottom: 4 }}>Neden bu bölüm?</div>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.45 }}>
                    {s.neden.map((c, k) => <li key={k}>{c}</li>)}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
