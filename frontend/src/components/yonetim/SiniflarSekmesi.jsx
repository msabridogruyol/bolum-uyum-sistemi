// [2026-10-10] Okul paneli → Sınıflar: şube bazında (12-A gibi) durum, sınıf öğretmeni ve sınıf raporları.
import { useState } from 'react'
import { api } from '../../api/client'
import RaporDugmeleri from '../RaporDugmeleri'

function OgretmenHucresi({ okulId, s, yenile }) {
  const [duzen, setDuzen] = useState(false)
  const [f, setF] = useState({ ad: s.ogretmen?.ad || '', eposta: s.ogretmen?.eposta || '' })
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const kaydet = async (e) => {
    e.preventDefault(); setBekle(true); setHata(null)
    try { await api.subeGuncelle(okulId, { sinif: s.sinif, sube: s.sube, ogretmen_ad: f.ad, ogretmen_eposta: f.eposta }); setDuzen(false); yenile() }
    catch (er) { setHata(er.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  if (!duzen) {
    return (
      <button className="sn-ogretmen" onClick={() => setDuzen(true)} title="Sınıf öğretmenini düzenle">
        {s.ogretmen?.ad ? <><b>{s.ogretmen.ad}</b>{s.ogretmen.eposta && <span className="yp-ince"> · {s.ogretmen.eposta}</span>}</> : <span className="yp-ince">+ Sınıf öğretmeni ekle</span>}
      </button>
    )
  }
  return (
    <form onSubmit={kaydet} className="sn-ogretmen-form">
      <input className="yp-sec" autoFocus value={f.ad} maxLength={80} onChange={(e) => setF({ ...f, ad: e.target.value })} placeholder="Ad soyad" />
      <input className="yp-sec" type="email" value={f.eposta} maxLength={120} onChange={(e) => setF({ ...f, eposta: e.target.value })} placeholder="E-posta (isteğe bağlı)" />
      <button className="yp-mini" disabled={bekle}>Kaydet</button>
      <button className="yp-mini" type="button" onClick={() => setDuzen(false)}>İptal</button>
      {hata && <span className="auth-error" style={{ margin: 0, padding: '2px 8px', fontSize: 12 }}>{hata}</span>}
    </form>
  )
}

const yuzde = (a, b) => (b ? Math.round((100 * a) / b) : 0)

export default function SiniflarSekmesi({ okulId, oz, yenile, onOgrenciler }) {
  const gruplar = []
  for (const s of oz.subeler || []) {
    let g = gruplar.find((x) => x.sinif === s.sinif)
    if (!g) { g = { sinif: s.sinif, subeler: [] }; gruplar.push(g) }
    g.subeler.push(s)
  }
  if (!gruplar.length) return <div className="bos-durum">Henüz öğrenci yok.</div>
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="yp-ince">
        Şube bilgisi öğrenci listesinden gelir (Öğrenciler → seç → "Sınıfı ata" ya da toplu yüklemede "12-A" / "12/A" yazmak yeterli).
        Her şube için sınıf öğretmeni ekleyebilir, şubeye özel rapor alabilirsiniz. <b>Toplu raporlar</b> şubedeki her öğrencinin bireysel raporunu tek PDF'te birleştirir (veli toplantısı için).
      </div>
      {gruplar.map((g) => {
        const top = g.subeler.reduce((a, s) => ({ o: a.o + s.ogrenci, t: a.t + s.tamamlayan }), { o: 0, t: 0 })
        const gercekSinif = !['Aday', 'Mezun', 'Belirtilmedi'].includes(g.sinif)
        return (
          <div key={g.sinif} className="card" style={{ margin: 0 }}>
            <div className="sn-baslik">
              <div><b>{g.sinif}</b> <span className="yp-ince">{top.o} öğrenci · %{yuzde(top.t, top.o)} tamamladı</span></div>
              {gercekSinif && g.subeler.length > 1 && (
                <RaporDugmeleri kucuk baslik={`${g.sinif} raporu`} secenekler={[
                  { anahtar: 'p', ad: 'PDF', ikon: '📄', aciklama: 'Sınıf düzeyi özeti: şube karşılaştırması, alanlar, ortak güçlü yönler', indir: () => api.sinifRaporuIndir(okulId, g.sinif, null) },
                  { anahtar: 'x', ad: 'Excel', ikon: '📊', aciklama: 'Şubeler ve öğrenciler tablo halinde', indir: () => api.sinifRaporuIndir(okulId, g.sinif, null, 'ozet', 'xlsx') },
                ]} />
              )}
            </div>
            <table className="yp-tablo">
              <thead><tr><th>Şube</th><th>Sınıf öğretmeni</th><th>Öğrenci</th><th>Giriş</th><th style={{ width: '18%' }}>Tamamlama</th><th>Hedef seçen</th><th>Raporlar</th></tr></thead>
              <tbody>
                {g.subeler.map((s) => (
                  <tr key={s.etiket}>
                    <td><button className="ak-link" onClick={() => onOgrenciler(s.sube ? `b:${s.sinif}|${s.sube}` : `s:${s.sinif}`)} title="Öğrencileri göster">{s.sube ? s.etiket : `${s.etiket} (şubesiz)`}</button></td>
                    <td>{s.sube && okulId > 0 && gercekSinif ? <OgretmenHucresi okulId={okulId} s={s} yenile={yenile} /> : <span className="yp-ince">—</span>}</td>
                    <td>{s.ogrenci}</td>
                    <td>{s.giris_yapan}</td>
                    <td><div className="yp-cubuk"><div style={{ width: `${Math.max(3, yuzde(s.tamamlayan, s.ogrenci))}%`, background: 'var(--okul-c, var(--gr))' }} /><span>{s.tamamlayan} · %{yuzde(s.tamamlayan, s.ogrenci)}</span></div></td>
                    <td>{s.hedef_secen}</td>
                    <td>
                      {s.sube ? (
                        <RaporDugmeleri kucuk baslik="" secenekler={[
                          { anahtar: 'p', ad: 'Özet', ikon: '📄', aciklama: `${s.etiket} sınıf raporu (PDF): durum, alanlar, okul ortalamasıyla karşılaştırma, öğrenci listesi`, indir: () => api.sinifRaporuIndir(okulId, s.sinif, s.sube) },
                          { anahtar: 'x', ad: 'Excel', ikon: '📊', aciklama: `${s.etiket} öğrenci tablosu`, indir: () => api.sinifRaporuIndir(okulId, s.sinif, s.sube, 'ozet', 'xlsx') },
                          { anahtar: 'v', ad: 'Veli', ikon: '👪', aciklama: `${s.etiket}: tüm öğrencilerin veli raporları tek PDF'te`, indir: () => api.sinifRaporuIndir(okulId, s.sinif, s.sube, 'toplu_veli') },
                          { anahtar: 'o', ad: 'Öğrenci', ikon: '📘', aciklama: `${s.etiket}: tüm öğrencilerin öğrenci raporları tek PDF'te`, indir: () => api.sinifRaporuIndir(okulId, s.sinif, s.sube, 'toplu_ogrenci') },
                          { anahtar: 'y', ad: 'Rehber', ikon: '🗂️', aciklama: `${s.etiket}: tüm öğrencilerin yönetici (ayrıntılı) raporları tek PDF'te`, indir: () => api.sinifRaporuIndir(okulId, s.sinif, s.sube, 'toplu_yonetici') },
                        ]} />
                      ) : gercekSinif ? (
                        <RaporDugmeleri kucuk baslik="" secenekler={[
                          { anahtar: 'p', ad: 'Özet', ikon: '📄', aciklama: `${s.sinif} raporu (PDF)`, indir: () => api.sinifRaporuIndir(okulId, s.sinif, null) },
                        ]} />
                      ) : <span className="yp-ince">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      })}
    </div>
  )
}
