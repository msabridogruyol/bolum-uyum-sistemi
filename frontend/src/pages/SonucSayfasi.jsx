import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

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
    <div className="pg">
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
              {[94, 88, 82, 77, 71].map((genislik, i) => (
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
        <div className="ob-grid">
          {siralama.map((s, i) => (
            <div key={s.bolum_id} className="ob-card">
              <div className="ob-top">
                <div className={`ob-rank${i < 3 ? ' top' : ''}`}>{i + 1}</div>
                <div className="ob-body">
                  <div className="ob-name">{s.bolum_adi}</div>
                </div>
                <div className="ob-score">%{Math.round(s.toplam_uyum)}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
