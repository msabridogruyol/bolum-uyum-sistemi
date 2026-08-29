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
  const [veri, setVeri] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.ogrencileriDetayliListele().then(setVeri).catch((e) => setHata(e.detail || 'Öğrenciler yüklenemedi.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!veri) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Öğrenciler</div>
        <div className="ps">Sistemdeki öğrenci hesapları, okulları ve hedef bölüm uyum durumları.</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 18 }}>
        <div className="sc"><div className="sl">Toplam Öğrenci</div><div className="sv">{veri.toplam_ogrenci}</div></div>
        <div className="sc"><div className="sl">Hedefi Olan</div><div className="sv pu">{veri.hedefi_olan_ogrenci}</div></div>
        <div className="sc">
          <div className="sl">Ortalama Hedef Uyum</div>
          <div className="sv gr">{veri.ortalama_hedef_uyum_orani !== null ? `%${veri.ortalama_hedef_uyum_orani}` : '—'}</div>
        </div>
      </div>

      <button
        className="btn sec"
        style={{ marginBottom: 14 }}
        onClick={() => csvDisaAktar(
          'ogrenciler_disa_aktarim.csv',
          ['ad_soyad', 'email', 'okul', 'hedef_bolum_adi', 'hedef_bolum_uyum_orani', 'olusturulma_zamani'],
          veri.ogrenciler.map((o) => [o.ad_soyad, o.email, o.okul || '', o.hedef_bolum_adi || '', o.hedef_bolum_uyum_orani ?? '', o.olusturulma_zamani]),
        )}
        disabled={veri.ogrenciler.length === 0}
      >
        ⬇ CSV Dışa Aktar
      </button>

      <div className="ll">
        {veri.ogrenciler.map((o) => (
          <div key={o.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{o.ad_soyad}</div>
              <div className="ld">
                {o.email} · {o.okul || 'Okul bilgisi yok'} · {new Date(o.olusturulma_zamani).toLocaleDateString('tr-TR')}
              </div>
            </div>
            {o.hedef_bolum_adi ? (
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 12, fontWeight: 600 }}>{o.hedef_bolum_adi}</div>
                <div style={{ fontFamily: 'var(--fd)', fontWeight: 700, color: 'var(--gr)' }}>
                  {o.hedef_bolum_uyum_orani !== null ? `%${o.hedef_bolum_uyum_orani}` : '—'}
                </div>
              </div>
            ) : (
              <span className="bdg bdg-lock">Hedef yok</span>
            )}
          </div>
        ))}
        {veri.ogrenciler.length === 0 && <div className="bos-durum">Henüz öğrenci yok.</div>}
      </div>
    </div>
  )
}
