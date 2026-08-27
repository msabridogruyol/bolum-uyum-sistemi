import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function SonucSayfasi() {
  const [siralama, setSiralama] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.siralamaGetir(20).then(setSiralama).catch((e) => setHata(e.detail || 'Sıralama alınamadı.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!siralama) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

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
        <div className="bos-durum">
          Sonuçların henüz hazır değil — önce K1-K4 katmanlarının tamamını bitirmelisin.
        </div>
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
