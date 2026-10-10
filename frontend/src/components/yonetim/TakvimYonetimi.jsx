// [2026-10-10] Takvim yönetimi: süper admin genel tarihleri (sınav, başvuru, tercih), okul yetkilisi okul etkinliklerini girer.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

const BOS = { baslik: '', aciklama: '', tur: 'okul', baslangic: '', bitis: '', saat: '', hedef_sinif: '', link: '' }
const GUN = (d) => new Date(d).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })

export default function TakvimYonetimi({ okulId }) {
  const [v, setV] = useState(null)
  const [form, setForm] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const yukle = () => api.yonetimTakvim(okulId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [okulId])
  if (!v) return <div className={hata ? 'auth-error' : 'bos-durum'}>{hata || 'Yükleniyor…'}</div>

  const kaydet = async (e) => {
    e.preventDefault(); setBekle(true); setHata(null)
    const veri = { ...form, bitis: form.bitis || null, saat: form.saat || null, hedef_sinif: form.hedef_sinif || null, link: form.link || null, okul_id: okulId || null }
    try { if (form.id) await api.yonetimTakvimDuzenle(form.id, veri); else await api.yonetimTakvimEkle(veri); setForm(null); yukle() }
    catch (er) { setHata(er.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  const sil = async (e) => { if (window.confirm(`"${e.baslik}" silinsin mi?`)) { try { await api.yonetimTakvimSil(e.id); yukle() } catch (er) { setHata(er.detail || 'Silinemedi.') } } }
  const tur = Object.fromEntries(v.turler.map((t) => [t.kod, t]))

  return (
    <div className="card" style={{ margin: 0 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10 }}>
        <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>{okulId ? 'Okul takvimi' : 'Genel takvim (tüm okullar)'}</div>
        <button className="btn" onClick={() => setForm({ ...BOS, tur: okulId ? 'okul' : 'sinav' })}>+ Etkinlik ekle</button>
      </div>
      <div className="yp-ince" style={{ marginBottom: 10 }}>
        {okulId
          ? 'Okulunuzun etkinlikleri (veli toplantısı, kulüp günü, üniversite gezisi…) yalnızca bu okulun öğrencilerine görünür. "Genel" etiketli tarihleri süper admin girer.'
          : 'Buradaki tarihler tüm okulların öğrencilerine görünür (YKS başvuru / sınav, tercih dönemi, özel yetenek sınavları). Resmî tarihleri ÖSYM / üniversite duyurularından kontrol ederek girin.'}
        {' '}Hedef sınıf seçilirse yalnızca o sınıftaki öğrenciler görür.
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {form && (
        <form className="yp-kutu" style={{ marginBottom: 12 }} onSubmit={kaydet}>
          <div className="kl-form">
            <input className="auth-input" required minLength={2} maxLength={120} value={form.baslik} onChange={(e) => setForm({ ...form, baslik: e.target.value })} placeholder="Başlık" />
            <select className="auth-input" value={form.tur} onChange={(e) => setForm({ ...form, tur: e.target.value })}>{v.turler.map((t) => <option key={t.kod} value={t.kod}>{t.ikon} {t.ad}</option>)}</select>
            <input className="auth-input" type="date" required value={form.baslangic} onChange={(e) => setForm({ ...form, baslangic: e.target.value })} title="Başlangıç" />
            <input className="auth-input" type="date" value={form.bitis || ''} min={form.baslangic} onChange={(e) => setForm({ ...form, bitis: e.target.value })} title="Bitiş (isteğe bağlı)" />
            <input className="auth-input" type="time" value={form.saat || ''} onChange={(e) => setForm({ ...form, saat: e.target.value })} title="Saat (isteğe bağlı)" />
            <select className="auth-input" value={form.hedef_sinif || ''} onChange={(e) => setForm({ ...form, hedef_sinif: e.target.value })}>
              <option value="">Tüm sınıflar</option>{v.siniflar.map((s) => <option key={s}>{s}</option>)}
            </select>
            <input className="auth-input" maxLength={300} value={form.link || ''} onChange={(e) => setForm({ ...form, link: e.target.value })} placeholder="Duyuru bağlantısı (isteğe bağlı)" />
            <input className="auth-input" maxLength={600} value={form.aciklama || ''} onChange={(e) => setForm({ ...form, aciklama: e.target.value })} placeholder="Açıklama (isteğe bağlı)" />
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <button className="btn" disabled={bekle}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
            <button type="button" className="btn sec" onClick={() => setForm(null)}>İptal</button>
          </div>
        </form>
      )}
      {v.etkinlikler.length === 0 ? <div className="bos-durum">Henüz etkinlik yok.</div> : (
        <table className="yp-tablo">
          <thead><tr><th>Tarih</th><th>Etkinlik</th><th>Kimler görür</th><th>Kaynak</th><th /></tr></thead>
          <tbody>
            {v.etkinlikler.map((e) => (
              <tr key={e.id}>
                <td style={{ whiteSpace: 'nowrap' }}>{GUN(e.baslangic)}{e.bitis && e.bitis !== e.baslangic && <div className="yp-ince">→ {GUN(e.bitis)}</div>}{e.saat && <div className="yp-ince">{e.saat}</div>}</td>
                <td><b>{tur[e.tur]?.ikon} {e.baslik}</b><div className="yp-ince">{e.tur_adi}{e.aciklama ? ` · ${e.aciklama}` : ''}</div></td>
                <td className="yp-ince">{e.hedef_sinif || 'Tüm sınıflar'}</td>
                <td className="yp-ince">{e.kaynak === 'genel' ? 'Genel' : 'Okul'}</td>
                <td style={{ whiteSpace: 'nowrap' }}>
                  {e.duzenlenebilir ? <><button className="yp-mini" onClick={() => setForm({ ...BOS, ...e, bitis: e.bitis || '', saat: e.saat || '', hedef_sinif: e.hedef_sinif || '', link: e.link || '', aciklama: e.aciklama || '' })}>Düzenle</button>{' '}<button className="yp-mini" onClick={() => sil(e)}>Sil</button></> : <span className="yp-ince">—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
