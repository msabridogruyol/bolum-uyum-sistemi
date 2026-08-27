import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function KontrolPaneliSayfasi() {
  const [veri, setVeri] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.kontrolPaneli().then(setVeri).catch((e) => setHata(e.detail || 'Veri alınamadı.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!veri) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const kartlar = [
    { baslik: 'Toplam Bölüm', deger: veri.toplam_bolum_sayisi },
    { baslik: 'Yayında Bölüm', deger: veri.yayinda_bolum_sayisi },
    { baslik: 'Tanımlı Dal', deger: veri.tanimli_dal_sayisi },
    { baslik: 'Toplam Öğrenci', deger: veri.toplam_ogrenci_sayisi },
    { baslik: 'Tamamlanan Tur', deger: veri.tamamlanan_tur_sayisi },
    { baslik: 'Yarıda Bırakma Oranı', deger: veri.yarida_birakma_orani !== null ? `%${veri.yarida_birakma_orani}` : '—' },
  ]

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Kontrol Paneli</div>
        <div className="ps">Sistemin genel durumuna ilişkin özet metrikler.</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
        {kartlar.map((k) => (
          <div key={k.baslik} className="card" style={{ marginBottom: 0 }}>
            <div className="ct">{k.baslik}</div>
            <div style={{ fontSize: 26, fontWeight: 600 }}>{k.deger}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
