// [2026-10-10] Paketler — süper admin paketlerin içeriğini (modüllerini) belirler; okullara paket Okullar → okul → Paket'ten atanır.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'

const bosForm = { ad: '', aciklama: '', moduller: [] }

export default function PaketlerSayfasi() {
  const [v, setV] = useState(null)
  const [duzen, setDuzen] = useState(null)     // { kod?: string, ad, aciklama, moduller: [] }
  const [silOnay, setSilOnay] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const yukle = () => api.paketler().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [])

  async function islem(f) {
    setBekle(true); setHata(null)
    try { await f(); await yukle(); setDuzen(null); setSilOnay(null) } catch (e) { setHata(e.detail || 'İşlem yapılamadı.') } finally { setBekle(false) }
  }
  const kaydet = (e) => {
    e.preventDefault()
    const veri = { ad: duzen.ad, aciklama: duzen.aciklama, moduller: duzen.moduller }
    islem(() => (duzen.kod ? api.paketDuzenle(duzen.kod, veri) : api.paketEkle(veri)))
  }
  const modulDegistir = (kod) => setDuzen((d) => ({ ...d, moduller: d.moduller.includes(kod) ? d.moduller.filter((m) => m !== kod) : [...d.moduller, kod] }))

  if (!v) return <div className="pg pg-genis"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Paketler</div>
        <div className="ps">Her paketin içerdiği modülleri belirleyin. Okula paket <Link to="/admin/okullar">Okullar</Link> → okul → <b>Paket</b> bölümünden atanır; orada okula özel modül de eklenip çıkarılabilir.</div>
      </div>
      <div className="yp-uyari" style={{ marginBottom: 14 }}>
        <b>Her pakette olanlar:</b> değerlendirme (testler), bölüm önerileri, profil, hedef bölüm seçimi, okul paneli (öğrenciler, sınıflar, okul ayarları) ve temel raporlar (öğrenci / veli / yönetim, sınıf ve okul raporu).
        Kapalı modüller öğrencinin ve okul yetkilisinin menüsünde görünmez, sunucu tarafında da erişilemez.
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="yp-tablo pk-tablo">
          <thead>
            <tr>
              <th>Modül</th>
              {v.paketler.map((p) => (
                <th key={p.kod} className="pk-sutun">
                  <div className="pk-sutun-ad">{p.ad}</div>
                  <div className="yp-ince">{p.okul_sayisi} okul</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {v.moduller.map((m) => (
              <tr key={m.kod}>
                <td><b>{m.ikon} {m.ad}</b><div className="yp-ince">{m.aciklama}</div></td>
                {v.paketler.map((p) => (
                  <td key={p.kod} className="pk-hucre">{p.moduller.includes(m.kod) ? <span className="pk-var" aria-label="var">✓</span> : <span className="pk-yok" aria-label="yok">—</span>}</td>
                ))}
              </tr>
            ))}
            <tr>
              <td />
              {v.paketler.map((p) => (
                <td key={p.kod} className="pk-hucre">
                  {silOnay === p.kod ? (
                    <div style={{ display: 'grid', gap: 4 }}>
                      <button className="yp-mini yp-tehlike" disabled={bekle} onClick={() => islem(() => api.paketSil(p.kod))}>Evet, sil</button>
                      <button className="yp-mini" onClick={() => setSilOnay(null)}>Vazgeç</button>
                    </div>
                  ) : (
                    <div style={{ display: 'grid', gap: 4 }}>
                      <button className="yp-mini" onClick={() => setDuzen({ kod: p.kod, ad: p.ad, aciklama: p.aciklama || '', moduller: [...p.moduller] })}>✎ Düzenle</button>
                      <button className="yp-mini" disabled={p.okul_sayisi > 0} title={p.okul_sayisi > 0 ? 'Bu paketi kullanan okul var' : ''} onClick={() => setSilOnay(p.kod)}>Sil</button>
                    </div>
                  )}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
        {!duzen && <button className="btn" style={{ marginTop: 12 }} onClick={() => setDuzen({ ...bosForm })}>+ Yeni paket</button>}
      </div>

      {duzen && (
        <form className="card" onSubmit={kaydet}>
          <div className="ct">{duzen.kod ? `${duzen.ad} paketini düzenle` : 'Yeni paket'}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'minmax(160px, 1fr) 2fr', gap: 10, marginBottom: 12 }}>
            <input className="auth-input" required minLength={2} maxLength={40} placeholder="Paket adı" value={duzen.ad} onChange={(e) => setDuzen({ ...duzen, ad: e.target.value })} />
            <input className="auth-input" maxLength={300} placeholder="Kısa açıklama (isteğe bağlı)" value={duzen.aciklama} onChange={(e) => setDuzen({ ...duzen, aciklama: e.target.value })} />
          </div>
          <div className="pk-moduller">
            {v.moduller.map((m) => (
              <label key={m.kod} className={`pk-modul${duzen.moduller.includes(m.kod) ? ' acik' : ''}`}>
                <input type="checkbox" checked={duzen.moduller.includes(m.kod)} onChange={() => modulDegistir(m.kod)} />
                <span><b>{m.ikon} {m.ad}</b><small>{m.aciklama}</small></span>
              </label>
            ))}
          </div>
          {duzen.kod && <div className="yp-ince" style={{ marginTop: 10 }}>Değişiklik bu paketi kullanan tüm okullara hemen yansır.</div>}
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button className="btn" disabled={bekle || duzen.ad.trim().length < 2}>Kaydet</button>
            <button type="button" className="btn sec" onClick={() => setDuzen(null)}>Vazgeç</button>
          </div>
        </form>
      )}
    </div>
  )
}
