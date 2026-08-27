import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function OgrencilerSayfasi() {
  const [ogrenciler, setOgrenciler] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.ogrencileriListele().then(setOgrenciler).catch((e) => setHata(e.detail || 'Öğrenciler yüklenemedi.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!ogrenciler) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Öğrenciler</div>
        <div className="ps">Sistemdeki öğrenci hesapları.</div>
      </div>
      <div className="ll">
        {ogrenciler.map((o) => (
          <div key={o.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{o.ad_soyad}</div>
              <div className="ld">{o.email} · {new Date(o.olusturulma_zamani).toLocaleDateString('tr-TR')}</div>
            </div>
          </div>
        ))}
        {ogrenciler.length === 0 && <div className="bos-durum">Henüz öğrenci yok.</div>}
      </div>
    </div>
  )
}
