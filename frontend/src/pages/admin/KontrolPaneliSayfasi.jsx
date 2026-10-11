// [2026-10-10] Kontrol Paneli sadeleştirildi: özet göstergeler, dikkat gerektirenler, hızlı bağlantılar, güvenlik denetimi.
// Ayrıntılı grafikler (kullanım istatistikleri, hedef bölüm / okul / sınıf kırılımları) İstatistikler sayfasına taşındı.
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { KpiKarti, KpiSatiri, sayi } from '../../components/istatistik'

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

const HIZLI = [
  ['/admin/istatistikler', '📊', 'İstatistikler', 'Katılım, sonuçlar, modül kullanımı'],
  ['/admin/raporlar', '📄', 'Rapor Merkezi', 'PDF / Excel raporların tamamı'],
  ['/admin/okullar', '🏫', 'Okullar', 'Okul, yetkili ve öğrenci yönetimi'],
  ['/admin/karsilastirma', '⚖️', 'Okul Karşılaştırması', 'Okulları yan yana kıyasla'],
  ['/admin/paketler', '📦', 'Paketler', 'Paket ve modüller'],
  ['/admin/pipeline', '⚙️', 'Pipeline Durumu', 'Bölüm ağırlığı yükleme ve onay'],
  ['/admin/guvenlik', '🛡️', 'Güvenlik / Tutarlılık', 'Geçersiz ve şüpheli turlar'],
  ['/admin/audit-log', '📜', 'Audit Log', 'Yönetim işlemleri kaydı'],
]

export default function KontrolPaneliSayfasi() {
  const git = useNavigate()
  const [veri, setVeri] = useState(null)
  const [dikkat, setDikkat] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.kontrolPaneli().then(setVeri).catch((e) => setHata(e.detail || 'Veri alınamadı.'))
    api.sistemDikkat().then(setDikkat).catch(() => setDikkat({ ozet: null, maddeler: null }))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!veri) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>
  const o = dikkat?.ozet

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Kontrol Paneli</div>
        <div className="ps">Sistemin genel durumu ve ilgilenilmesi gerekenler. Ayrıntılı grafikler için <Link to="/admin/istatistikler" className="ak-link">İstatistikler</Link>.</div>
      </div>

      <KpiSatiri min={165}>
        <KpiKarti etiket="Aktif okul" deger={o ? o.okul_aktif : '—'} ikon="🏫" alt={o ? `${sayi(o.okul_toplam)} okul kayıtlı` : undefined} onClick={() => git('/admin/okullar')} />
        <KpiKarti etiket="Öğrenci" deger={o ? o.ogrenci : veri.toplam_ogrenci_sayisi} ikon="🎓" alt={o ? 'Test hesapları hariç' : 'Tüm hesaplar'} onClick={() => git('/admin/istatistikler')} />
        <KpiKarti etiket="Son 7 günde aktif" deger={o ? o.aktif7 : '—'} ikon="⚡" onClick={() => git('/admin/istatistikler')} />
        <KpiKarti etiket="Testi tamamlayan" deger={o ? o.tamamlayan : '—'} ikon="✅" ton="iyi"
          alt={o?.tamamlama_orani != null ? `Öğrencilerin %${sayi(o.tamamlama_orani)}’i` : undefined} onClick={() => git('/admin/istatistikler')} />
        <KpiKarti etiket="Tamamlanan tur" deger={veri.tamamlanan_tur_sayisi} ikon="🔁"
          alt={`Yarıda bırakma: ${veri.yarida_birakma_orani !== null ? `%${sayi(veri.yarida_birakma_orani)}` : '—'}`} />
        <KpiKarti etiket="Yayında bölüm" deger={veri.yayinda_bolum_sayisi} ikon="📚"
          alt={`${sayi(veri.toplam_bolum_sayisi)} bölüm · ${sayi(veri.tanimli_dal_sayisi)} dal`} onClick={() => git('/admin/bolumler')} />
      </KpiSatiri>

      <div className="two">
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="ct">Dikkat gerektirenler</div>
          {!dikkat ? (
            <div className="yp-ince">Yükleniyor…</div>
          ) : dikkat.maddeler == null ? (
            <div className="yp-ince">Liste alınamadı.</div>
          ) : dikkat.maddeler.length === 0 ? (
            <div className="kp-yolunda">✓ Şu an ilgilenilmesi gereken bir şey yok.</div>
          ) : (
            <ul className="kp-dikkat">
              {dikkat.maddeler.map((m) => (
                <li key={m.k} className={`kp-d-${m.seviye}`}>
                  <Link to={m.link}>
                    <span className="kp-d-ikon" aria-hidden="true">{m.ikon}</span>
                    <span className="kp-d-metin"><b>{m.baslik}</b><small>{m.aciklama}</small></span>
                    <span className="kp-d-sayi" aria-label={`${m.sayi} adet`}>{sayi(m.sayi)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div className="ct">Hızlı bağlantılar</div>
          <div className="kp-hizli">
            {HIZLI.map(([yol, ikon, ad, aciklama]) => (
              <Link key={yol} to={yol} className="kp-hizli-oge">
                <span className="kp-d-ikon" aria-hidden="true">{ikon}</span>
                <span className="kp-d-metin"><b>{ad}</b><small>{aciklama}</small></span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <div className="ct">Güvenlik Durumu</div>
        <div className="ps" style={{ margin: '0 0 8px', fontSize: 11.5 }}>
          Elle yapılan kod denetiminin sonucu — canlı/otomatik tarama değildir.
        </div>
        <div className="kp-guvenlik">
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
      </div>
    </div>
  )
}
