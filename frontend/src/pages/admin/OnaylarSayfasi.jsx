// [2026-11-05] Süper admin › Onay Formları: okul okul KVKK onayı ve 18 yaş altı veli onay formu tamamlanma durumu.
// Ayrıntı ve işaretleme okulun panelinde (Onay Formları bölümü); okul harici öğrenciler için satır 0.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { KpiKarti } from '../../components/istatistik/KpiKarti'

export default function OnaylarSayfasi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [eksikler, setEksikler] = useState(true)
  useEffect(() => { api.onaylarOkullar().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [])
  if (hata) return <div className="pg"><div className="auth-error">{hata}</div></div>
  if (!v) return <div className="pg"><div className="bos-durum yukleniyor">Yükleniyor…</div></div>
  const t = v.toplam
  const satirlar = v.okullar.filter((o) => o.ogrenci > 0 && (!eksikler || o.tamam < o.ogrenci))
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Onay Formları</div>
        <div className="ps">Okullara göre KVKK onayı ve 18 yaş altı veli onay formu tamamlanma durumu. Veli onayı tamamlanmayan öğrenci değerlendirmeye başlayamaz.</div>
      </div>
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
          <KpiKarti etiket="Tamamlanma" deger={t.yuzde} birim="%" ikon="✍️" ton="okul" alt={`${t.tamam} / ${t.ogrenci} öğrenci`} />
          <KpiKarti etiket="KVKK onayı" deger={t.kvkk} ikon="🔒" alt={`${t.ogrenci - t.kvkk} eksik`} />
          <KpiKarti etiket="Veli formu alındı" deger={t.veli_alindi} ikon="📄" alt={`${t.resit} öğrenci 18 yaşını doldurmuş`} />
          <KpiKarti etiket="Veli formu bekleyen" deger={t.veli_bekleyen} ikon="⏳" ton={t.veli_bekleyen ? 'uyari' : undefined} alt="değerlendirmeye başlayamaz" />
        </div>
      </div>
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
          <div className="ct" style={{ margin: 0, flex: 1 }}>Okullar</div>
          <label className="yp-ince" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" checked={eksikler} onChange={(e) => setEksikler(e.target.checked)} /> Yalnızca eksiği olanlar
          </label>
        </div>
        {satirlar.length === 0 ? <div className="bos-durum">Eksik onayı olan okul yok.</div> : (
          <div className="tablo-kap">
            <table className="yp-tablo">
              <thead><tr><th>Okul</th><th>Öğrenci</th><th>KVKK onayı</th><th>Veli formu</th><th>18 yaş üstü</th><th>Bekleyen</th><th>Tamamlanma</th><th /></tr></thead>
              <tbody>
                {satirlar.map((o) => (
                  <tr key={o.okul_id}>
                    <td><b>{o.ad}</b>{!o.aktif && <span className="yp-ince"> · pasif</span>}</td>
                    <td>{o.ogrenci}</td><td>{o.kvkk}</td><td>{o.veli_alindi}</td><td>{o.resit}</td>
                    <td>{o.veli_bekleyen ? <b style={{ color: 'var(--am)' }}>{o.veli_bekleyen}</b> : 0}</td><td>%{o.yuzde}</td>
                    <td><Link className="hg-link" to={`/admin/okul/${o.okul_id}?sekme=onaylar`}>Aç →</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
