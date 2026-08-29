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

  const [aramaMetni, setAramaMetni] = useState('')
  const [hedefFiltresi, setHedefFiltresi] = useState('hepsi') // hepsi | var | yok

  useEffect(() => {
    api.ogrencileriDetayliListele().then(setVeri).catch((e) => setHata(e.detail || 'Öğrenciler yüklenemedi.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!veri) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const filtrelenmis = veri.ogrenciler.filter((o) => {
    const aramaUyar = !aramaMetni ||
      o.ad_soyad.toLowerCase().includes(aramaMetni.toLowerCase()) ||
      o.email.toLowerCase().includes(aramaMetni.toLowerCase()) ||
      (o.okul || '').toLowerCase().includes(aramaMetni.toLowerCase())
    const hedefUyar = hedefFiltresi === 'hepsi' ||
      (hedefFiltresi === 'var' && o.hedef_bolum_adi) ||
      (hedefFiltresi === 'yok' && !o.hedef_bolum_adi)
    return aramaUyar && hedefUyar
  })

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Öğrenciler</div>
        <div className="ps">Sistemdeki öğrenci hesapları, okulları ve hedef bölüm uyum durumları.</div>
      </div>

      {/* --- KPI'lar --- */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 18 }}>
        <div className="sc"><div className="sl">Toplam Öğrenci</div><div className="sv">{veri.toplam_ogrenci}</div></div>
        <div className="sc"><div className="sl">Hedefi Olan</div><div className="sv pu">{veri.hedefi_olan_ogrenci}</div></div>
        <div className="sc">
          <div className="sl">Ortalama Hedef Uyum</div>
          <div className="sv gr">{veri.ortalama_hedef_uyum_orani !== null ? `%${veri.ortalama_hedef_uyum_orani}` : '—'}</div>
        </div>
      </div>

      {/* --- En çok okul / en çok hedeflenen bölüm --- */}
      <div className="two">
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="ct">En Çok Öğrencinin Geldiği Okullar</div>
          {veri.en_cok_okul.length === 0 ? (
            <div className="ps" style={{ margin: 0 }}>Henüz hiçbir öğrenci okul bilgisi girmedi.</div>
          ) : (
            veri.en_cok_okul.map((o) => (
              <div key={o.okul} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, padding: '6px 0', borderBottom: '1px solid var(--bor)' }}>
                <span style={{ color: 'var(--tx2)' }}>{o.okul}</span>
                <b>{o.sayi}</b>
              </div>
            ))
          )}
        </div>
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="ct">En Çok Hedeflenen Bölümler</div>
          {veri.en_cok_hedeflenen_bolum.length === 0 ? (
            <div className="ps" style={{ margin: 0 }}>Henüz hiçbir öğrenci hedef bölüm seçmedi.</div>
          ) : (
            veri.en_cok_hedeflenen_bolum.map((b) => (
              <div key={b.bolum_adi} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, padding: '6px 0', borderBottom: '1px solid var(--bor)' }}>
                <span style={{ color: 'var(--tx2)' }}>{b.bolum_adi}</span>
                <b>{b.sayi}</b>
              </div>
            ))
          )}
        </div>
      </div>

      {/* --- Filtreler --- */}
      <div style={{ display: 'flex', gap: 10, margin: '20px 0 14px', flexWrap: 'wrap' }}>
        <input
          className="auth-input"
          style={{ flex: '1 1 240px' }}
          value={aramaMetni}
          onChange={(e) => setAramaMetni(e.target.value)}
          placeholder="İsim, e-posta veya okula göre ara..."
        />
        <select className="auth-input" style={{ width: 200 }} value={hedefFiltresi} onChange={(e) => setHedefFiltresi(e.target.value)}>
          <option value="hepsi">Tüm Öğrenciler</option>
          <option value="var">Hedefi Olanlar</option>
          <option value="yok">Hedefi Olmayanlar</option>
        </select>
        <button
          className="btn sec"
          onClick={() => csvDisaAktar(
            'ogrenciler_disa_aktarim.csv',
            ['ad_soyad', 'email', 'okul', 'hedef_bolum_adi', 'hedef_bolum_uyum_orani', 'olusturulma_zamani'],
            filtrelenmis.map((o) => [o.ad_soyad, o.email, o.okul || '', o.hedef_bolum_adi || '', o.hedef_bolum_uyum_orani ?? '', o.olusturulma_zamani]),
          )}
          disabled={filtrelenmis.length === 0}
        >
          ⬇ CSV Dışa Aktar
        </button>
      </div>

      <div className="ps" style={{ marginBottom: 12, fontSize: 12 }}>{filtrelenmis.length} / {veri.ogrenciler.length} öğrenci gösteriliyor</div>

      <div className="ll">
        {filtrelenmis.map((o) => (
          <div key={o.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{o.ad_soyad}</div>
              <div className="ld">
                {o.email} · {o.okul || '— okul bilgisi yok'} · {new Date(o.olusturulma_zamani).toLocaleDateString('tr-TR')}
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
        {filtrelenmis.length === 0 && <div className="bos-durum">Filtrelere uyan öğrenci bulunamadı.</div>}
      </div>
    </div>
  )
}
