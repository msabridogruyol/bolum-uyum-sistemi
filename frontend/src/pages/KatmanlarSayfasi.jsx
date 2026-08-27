import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const DURUM_ETIKET = { baslamadi: null, devam_ediyor: 'Devam Ediyor', tamamlandi: 'Tamamlandı' }
const DURUM_RENK = { devam_ediyor: 'bdg-prog', tamamlandi: 'bdg-done' }

export default function KatmanlarSayfasi() {
  const [katmanlar, setKatmanlar] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail || 'Katmanlar yüklenemedi.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const tamamlanan = katmanlar.filter((k) => k.durum === 'tamamlandi').length

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Sınav Yol Haritan</div>
        <div className="ps">
          4 ana katmanı sırayla tamamla; son katman (Alan Eğilimi) sonucuna göre sana özel bir derinleşme bölümü açılabilir.
          {' '}<b>{tamamlanan}/{katmanlar.length} tamamlandı.</b>
        </div>
      </div>
      <div className="ll">
        {katmanlar.map((k) => (
          <div key={k.id} className={`lc${k.durum === 'tamamlandi' ? ' done' : k.durum === 'devam_ediyor' ? ' cur' : ''}`} onClick={() => navigate(`/katmanlar/${k.kod}`)}>
            <div className="ln">{k.durum === 'tamamlandi' ? '✓' : k.sira}</div>
            <div className="lb-wrap">
              <div className="lt">{k.ad}</div>
              <div className="ld">{k.kosullu_mu ? 'Koşullu / Dinamik — önceki katmana bağlı' : `Ağırlık: %${k.normalizasyon_agirligi}`}</div>
              {DURUM_ETIKET[k.durum] && <span className={`bdg ${DURUM_RENK[k.durum]}`}>{DURUM_ETIKET[k.durum]}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
