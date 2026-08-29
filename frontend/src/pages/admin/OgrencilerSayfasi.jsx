import { useEffect, useState } from 'react'
import { api } from '../../api/client'

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

export default function OgrencilerSayfasi() {
  const [ogrenciler, setOgrenciler] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.ogrencileriListele().then(setOgrenciler).catch((e) => setHata(e.detail || 'Öğrenciler yüklenemedi.'))
  }, [])

  if (hata) return <div className="pg pg-genis"><div className="bos-durum">{hata}</div></div>
  if (!ogrenciler) return <div className="pg pg-genis"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Öğrenciler</div>
        <div className="ps">Sistemdeki öğrenci hesapları.</div>
      </div>

      <button
        className="btn sec"
        style={{ marginBottom: 14 }}
        onClick={() => csvDisaAktar(
          'ogrenciler_disa_aktarim.csv',
          ['ad_soyad', 'email', 'olusturulma_zamani'],
          ogrenciler.map((o) => [o.ad_soyad, o.email, o.olusturulma_zamani]),
        )}
        disabled={ogrenciler.length === 0}
      >
        ⬇ CSV Dışa Aktar
      </button>

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
