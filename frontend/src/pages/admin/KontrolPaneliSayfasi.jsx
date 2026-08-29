import { useEffect, useState } from 'react'
import { api } from '../../api/client'

// Güvenlik denetim listesi — STATİK, elle yapılmış bir kod denetiminin
// sonucunu yansıtır. Canlı/otomatik tarayan bir sistem DEĞİLDİR.
const GUVENLIK_DENETIMI = [
  { baslik: 'Uç nokta yetki kontrolü', durum: 'iyi', detay: '26/26 admin uç noktası korunuyor' },
  { baslik: 'SQL enjeksiyonu riski', durum: 'iyi', detay: 'Tüm sorgular parametreli, metin birleştirme yok' },
  { baslik: 'Hassas veri sızıntısı', durum: 'iyi', detay: 'Şifre hash\'i hiçbir yanıtta dönmüyor' },
  { baslik: 'Audit log kapsamı', durum: 'iyi', detay: 'Kritik işlemler (onay, rol, durum değişikliği) kayıt altında' },
  { baslik: 'Toplu yükleme boyut sınırı', durum: 'dikkat', detay: 'CSV/Excel yüklemelerinde satır sayısı sınırı yok' },
  { baslik: 'İstek sıklığı sınırlaması', durum: 'dikkat', detay: 'Hiçbir uç noktada rate limiting yok' },
]

const DURUM_RENK = { iyi: 'var(--gr)', dikkat: 'var(--am)', kritik: 'var(--re)' }
const DURUM_IKON = { iyi: '✓', dikkat: '⚠️', kritik: '✕' }

export default function KontrolPaneliSayfasi() {
  const [veri, setVeri] = useState(null)
  const [kullanim, setKullanim] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.kontrolPaneli().then(setVeri).catch((e) => setHata(e.detail || 'Veri alınamadı.'))
    api.kullanimIstatistikleriGetir().then(setKullanim).catch(() => setKullanim(null))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!veri) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const kartlar = [
    { baslik: 'Toplam Bölüm', deger: veri.toplam_bolum_sayisi },
    { baslik: 'Yayında Bölüm', deger: veri.yayinda_bolum_sayisi },
    { baslik: 'Tanımlı Dal', deger: veri.tanimli_dal_sayisi },
    { baslik: 'Toplam Öğrenci', deger: veri.toplam_ogrenci_sayisi },
    { baslik: 'Tamamlanan Tur', deger: veri.tamamlanan_tur_sayisi },
    { baslik: 'Yarıda Bırakma', deger: veri.yarida_birakma_orani !== null ? `%${veri.yarida_birakma_orani}` : '—' },
  ]

  const enYuksekGunlukSayi = kullanim?.gunluk_dagilim?.length
    ? Math.max(...kullanim.gunluk_dagilim.map((g) => g.sayi), 1)
    : 1

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Kontrol Paneli</div>
        <div className="ps">Sistemin genel durumuna ilişkin özet metrikler.</div>
      </div>

      {/* --- KPI'lar, tek satırda --- */}
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${kartlar.length}, 1fr)`, gap: 8, marginBottom: 24 }}>
        {kartlar.map((k) => (
          <div key={k.baslik} className="card" style={{ marginBottom: 0, padding: '12px 10px', textAlign: 'center' }}>
            <div style={{ fontSize: 9.5, color: 'var(--tx3)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '.03em', marginBottom: 6 }}>
              {k.baslik}
            </div>
            <div style={{ fontFamily: 'var(--fd)', fontSize: 20, fontWeight: 700 }}>{k.deger}</div>
          </div>
        ))}
      </div>

      {/* --- Performans Ölçümü --- */}
      <div className="ct">Performans Ölçümü</div>
      <div className="two">
        {/* Güvenlik durumu */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="ct">Güvenlik Durumu</div>
          <div className="ps" style={{ margin: '0 0 12px', fontSize: 11.5 }}>
            Elle yapılan kod denetiminin sonucu — canlı/otomatik tarama değildir.
          </div>
          {GUVENLIK_DENETIMI.map((d) => (
            <div key={d.baslik} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 0', borderBottom: '1px solid var(--bor)' }}>
              <span style={{ color: DURUM_RENK[d.durum], fontWeight: 700, fontSize: 13, flexShrink: 0 }}>{DURUM_IKON[d.durum]}</span>
              <div>
                <div style={{ fontSize: 12.5, fontWeight: 600 }}>{d.baslik}</div>
                <div style={{ fontSize: 11, color: 'var(--tx3)', marginTop: 1 }}>{d.detay}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Kullanım istatistikleri */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="ct">Kullanım İstatistikleri</div>
          {!kullanim ? (
            <div className="veri-yok-grafik" style={{ padding: '20px 10px' }}>
              <div className="vg-ikon">📈</div>
              <div className="vg-metin">Veri toplanmaya yeni başladı, henüz gösterilecek bir şey yok.</div>
            </div>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
                <div className="sc" style={{ padding: '10px 12px' }}>
                  <div className="sl">Bugün</div>
                  <div className="sv">{kullanim.bugun_toplam}</div>
                </div>
                <div className="sc" style={{ padding: '10px 12px' }}>
                  <div className="sl">Son 7 Gün</div>
                  <div className="sv">{kullanim.son_7_gun_toplam}</div>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 14, marginBottom: 14, fontSize: 11.5 }}>
                <div><span style={{ color: 'var(--gr)', fontWeight: 700 }}>●</span> Öğrenci: <b>{kullanim.ogrenci_ziyaret}</b></div>
                <div><span style={{ color: 'var(--pu)', fontWeight: 700 }}>●</span> Admin: <b>{kullanim.admin_ziyaret}</b></div>
                <div><span style={{ color: 'var(--tx3)', fontWeight: 700 }}>●</span> Anonim: <b>{kullanim.anonim_ziyaret}</b></div>
              </div>

              {kullanim.gunluk_dagilim.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 6, height: 60, marginBottom: 14 }}>
                  {kullanim.gunluk_dagilim.map((g) => (
                    <div key={g.tarih} style={{ flex: 1, textAlign: 'center' }}>
                      <div
                        style={{
                          height: `${Math.max((g.sayi / enYuksekGunlukSayi) * 50, 3)}px`,
                          background: 'var(--pu)', borderRadius: '3px 3px 0 0', marginBottom: 4,
                        }}
                        title={`${g.tarih}: ${g.sayi} istek`}
                      />
                      <div style={{ fontSize: 8.5, color: 'var(--tx3)' }}>{g.tarih.slice(5)}</div>
                    </div>
                  ))}
                </div>
              )}

              {kullanim.en_cok_ziyaret_edilen.length > 0 && (
                <div>
                  <div style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--tx3)', marginBottom: 6 }}>EN ÇOK ZİYARET EDİLEN</div>
                  {kullanim.en_cok_ziyaret_edilen.map((e) => (
                    <div key={e.yol} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11.5, padding: '3px 0' }}>
                      <span style={{ color: 'var(--tx2)', fontFamily: 'monospace' }}>{e.yol}</span>
                      <span style={{ fontWeight: 700 }}>{e.sayi}</span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
