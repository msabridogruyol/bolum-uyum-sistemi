// [2026-10-10] Takvim — genel (sınav, başvuru, tercih), okul etkinlikleri, eğitim koçu randevuları ve kişisel notlar.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

const AY = (d) => new Date(d).toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' })
const GUN = (d) => new Date(d).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', weekday: 'short' })
const KAYNAK = { genel: 'Genel', okul: 'Okulun', kisisel: 'Notum', koc: 'Koç' }

function kalanGun(bas, bugun) {
  const g = Math.round((new Date(bas) - new Date(bugun)) / 86400000)
  if (g === 0) return 'Bugün'
  if (g === 1) return 'Yarın'
  if (g > 1) return `${g} gün kaldı`
  return null
}

export default function TakvimSayfasi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [form, setForm] = useState(null)
  const [gecmis, setGecmis] = useState(false)
  const [bekle, setBekle] = useState(false)
  const yukle = () => api.takvim().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [])

  const gruplar = useMemo(() => {
    if (!v) return []
    const m = new Map()
    v.etkinlikler.filter((e) => gecmis || (e.bitis || e.baslangic) >= v.bugun).forEach((e) => {
      const k = AY(e.baslangic); if (!m.has(k)) m.set(k, []); m.get(k).push(e)
    })
    return [...m.entries()]
  }, [v, gecmis])

  const kaydet = async (e) => {
    e.preventDefault(); setBekle(true); setHata(null)
    try { await api.takvimEkle({ ...form, bitis: form.bitis || null, saat: form.saat || null }); setForm(null); yukle() }
    catch (er) { setHata(er.detail || 'Eklenemedi.') }
    setBekle(false)
  }
  const sil = async (e) => { if (window.confirm('Bu not silinsin mi?')) { await api.takvimSil(e.id).catch(() => {}); yukle() } }

  if (!v) return <div className="pg"><div className={hata ? 'auth-error' : 'bos-durum'}>{hata || 'Yükleniyor…'}</div></div>
  const yaklasan = v.etkinlikler.find((e) => e.baslangic >= v.bugun && e.kaynak !== 'kisisel')
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Takvim</div>
        <div className="ps">Sınav ve tercih tarihleri, okulunun etkinlikleri, koç görüşmelerin ve kendi notların tek yerde.</div>
      </div>
      {yaklasan && (
        <div className="tk-yaklasan">
          <span className="tk-ikon">{yaklasan.ikon}</span>
          <div style={{ flex: 1 }}><small>Sıradaki</small><b>{yaklasan.baslik}</b><div className="yp-ince">{GUN(yaklasan.baslangic)}{yaklasan.saat ? ` · ${yaklasan.saat}` : ''}</div></div>
          <span className="tk-kalan">{kalanGun(yaklasan.baslangic, v.bugun)}</span>
        </div>
      )}
      <div className="kc-filtre">
        <button className="btn" style={{ padding: '8px 14px', fontSize: 13 }} onClick={() => setForm({ baslik: '', baslangic: v.bugun, bitis: '', saat: '', aciklama: '' })}>+ Not / hatırlatma ekle</button>
        <label className="yp-ince" style={{ display: 'flex', gap: 6, alignItems: 'center', marginLeft: 'auto' }}>
          <input type="checkbox" checked={gecmis} onChange={(e) => setGecmis(e.target.checked)} /> Geçmiş etkinlikleri de göster
        </label>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {form && (
        <form className="card tk-form" onSubmit={kaydet}>
          <input className="auth-input" required minLength={2} maxLength={120} autoFocus value={form.baslik} onChange={(e) => setForm({ ...form, baslik: e.target.value })} placeholder="ör. Deneme sınavı, kitap bitirme hedefi, üniversite gezisi" />
          <div className="tk-form-satir">
            <label>Tarih<input className="auth-input" type="date" required value={form.baslangic} onChange={(e) => setForm({ ...form, baslangic: e.target.value })} /></label>
            <label>Bitiş (isteğe bağlı)<input className="auth-input" type="date" value={form.bitis} min={form.baslangic} onChange={(e) => setForm({ ...form, bitis: e.target.value })} /></label>
            <label>Saat (isteğe bağlı)<input className="auth-input" type="time" value={form.saat} onChange={(e) => setForm({ ...form, saat: e.target.value })} /></label>
          </div>
          <input className="auth-input" maxLength={600} value={form.aciklama} onChange={(e) => setForm({ ...form, aciklama: e.target.value })} placeholder="Not (isteğe bağlı)" />
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn" disabled={bekle}>{bekle ? <span className="spin" /> : 'Ekle'}</button>
            <button type="button" className="btn sec" onClick={() => setForm(null)}>Vazgeç</button>
          </div>
        </form>
      )}
      {gruplar.length === 0 ? (
        <div className="card"><div className="bos-durum">Yaklaşan etkinlik yok. Okulun ve sistem yöneticisi önemli tarihleri ekledikçe burada görünecek.</div></div>
      ) : gruplar.map(([ay, liste]) => (
        <div key={ay} className="card">
          <div className="ct">{ay}</div>
          <ul className="tk-liste">
            {liste.map((e) => {
              const gecti = (e.bitis || e.baslangic) < v.bugun
              return (
                <li key={e.id} className={`tk-${e.kaynak}${gecti ? ' gecti' : ''}`}>
                  <div className="tk-tarih"><b>{new Date(e.baslangic).getDate()}</b><span>{new Date(e.baslangic).toLocaleDateString('tr-TR', { weekday: 'short' })}</span></div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div className="tk-bas"><span>{e.ikon}</span> <b>{e.baslik}</b> <span className="tk-kaynak">{KAYNAK[e.kaynak]}</span></div>
                    <div className="yp-ince">
                      {e.tur_adi}{e.saat ? ` · ${e.saat}` : ''}{e.bitis && e.bitis !== e.baslangic ? ` · ${GUN(e.baslangic)} – ${GUN(e.bitis)}` : ''}
                    </div>
                    {e.aciklama && <div className="tk-ac">{e.aciklama}</div>}
                    {e.link && (e.link.startsWith('/') ? <a href={e.link} className="tk-link">Ayrıntı →</a> : <a href={e.link} target="_blank" rel="noreferrer" className="tk-link">Resmî duyuru ↗</a>)}
                  </div>
                  {!gecti && kalanGun(e.baslangic, v.bugun) && <span className="tk-kalan">{kalanGun(e.baslangic, v.bugun)}</span>}
                  {e.duzenlenebilir && <button className="yp-mini" onClick={() => sil(e)} title="Notu sil">🗑</button>}
                </li>
              )
            })}
          </ul>
        </div>
      ))}
    </div>
  )
}
