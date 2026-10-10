// [2026-10-10] Kütüphanem — öğrencinin okuduğu kitaplar, izlediği film/dizi/belgeseller, kurslar ve etkinlikler.
// Öğrenci kendisi girer; rehber öğretmeni öğrenci detayında görür.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

const BOS = (kategori) => ({ kategori, alt_tur: '', baslik: '', kisi: '', durum: 'bitti', puan: null, notlar: '', tarih: '' })

function Yildiz({ deger, onChange }) {
  return (
    <span className="kt-yildiz" role="radiogroup" aria-label="Puan">
      {[1, 2, 3, 4, 5].map((n) => (
        <button key={n} type="button" aria-checked={deger === n} role="radio" className={deger >= n ? 'dolu' : ''}
          onClick={() => onChange?.(deger === n ? null : n)} disabled={!onChange}>★</button>
      ))}
    </span>
  )
}

export function KutuphaneListesi({ v, onDuzenle, onSil, salt }) {
  const [filtre, setFiltre] = useState('hepsi')
  const liste = v.kayitlar.filter((x) => filtre === 'hepsi' || x.kategori === filtre)
  return (
    <>
      <div className="kt-ozet">
        {v.kategoriler.map((k) => (
          <button key={k.kod} className={`kt-ozet-kutu${filtre === k.kod ? ' aktif' : ''}`} onClick={() => setFiltre(filtre === k.kod ? 'hepsi' : k.kod)}>
            <span>{k.ikon}</span><b>{v.istatistik[k.kod]?.bitti || 0}</b><small>{k.ad}</small>
            {(v.istatistik[k.kod]?.toplam || 0) > (v.istatistik[k.kod]?.bitti || 0) && <em>+{v.istatistik[k.kod].toplam - v.istatistik[k.kod].bitti} listede</em>}
          </button>
        ))}
      </div>
      {liste.length === 0 ? <div className="bos-durum">{salt ? 'Öğrenci henüz kayıt eklemedi.' : 'Henüz kayıt yok. Okuduğun bir kitapla başlayabilirsin.'}</div> : (
        <div className="kt-liste">
          {liste.map((x) => (
            <div key={x.id} className={`kt-kayit kt-${x.durum}`}>
              <span className="kt-ikon">{x.ikon}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="kt-baslik"><b>{x.baslik}</b>{x.kisi && <span> · {x.kisi}</span>}</div>
                <div className="yp-ince">
                  <span className={`kt-durum kt-durum-${x.durum}`}>{x.durum_adi}</span>
                  {x.alt_tur && ` · ${x.alt_tur}`}{x.tarih && ` · ${new Date(x.tarih).toLocaleDateString('tr-TR', { month: 'long', year: 'numeric' })}`}
                </div>
                {x.puan && <Yildiz deger={x.puan} />}
                {x.notlar && <div className="kt-not">“{x.notlar}”</div>}
              </div>
              {!salt && (
                <div className="kt-islem">
                  <button className="yp-mini" onClick={() => onDuzenle({ ...x, alt_tur: x.alt_tur || '', kisi: x.kisi || '', notlar: x.notlar || '', tarih: x.tarih || '' })}>Düzenle</button>
                  <button className="yp-mini" onClick={() => onSil(x)}>Sil</button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  )
}

export default function KutuphanemSayfasi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [form, setForm] = useState(null)
  const [bekle, setBekle] = useState(false)
  const yukle = () => api.kutuphane().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [])
  const kat = useMemo(() => Object.fromEntries((v?.kategoriler || []).map((k) => [k.kod, k])), [v])

  const kaydet = async (e) => {
    e.preventDefault(); setBekle(true); setHata(null)
    const veri = { ...form, alt_tur: form.alt_tur || null, kisi: form.kisi || null, notlar: form.notlar || null, tarih: form.tarih || null }
    try { if (form.id) await api.kutuphaneDuzenle(form.id, veri); else await api.kutuphaneEkle(veri); setForm(null); yukle() }
    catch (er) { setHata(er.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  const sil = async (x) => { if (window.confirm(`"${x.baslik}" silinsin mi?`)) { await api.kutuphaneSil(x.id).catch(() => {}); yukle() } }

  if (!v) return <div className="pg"><div className={hata ? 'auth-error' : 'bos-durum'}>{hata || 'Yükleniyor…'}</div></div>
  const k = form ? kat[form.kategori] : null
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Kütüphanem</div>
        <div className="ps">Okuduğun kitapları, izlediğin film ve belgeselleri, aldığın kursları ve katıldığın etkinlikleri kaydet. Neler öğrendiğini birkaç cümleyle not al; rehber öğretmeninle görüşürken ve üniversite başvurularında işine yarar.</div>
      </div>
      <div className="kc-filtre">
        {v.kategoriler.map((c) => <button key={c.kod} className="btn sec" style={{ padding: '8px 12px', fontSize: 13 }} onClick={() => setForm(BOS(c.kod))}>+ {c.ikon} {c.tekil}</button>)}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {form && k && (
        <form className="card kt-form" onSubmit={kaydet}>
          <div className="ct">{form.id ? 'Düzenle' : `Yeni ${k.tekil.toLocaleLowerCase('tr-TR')}`}</div>
          <div className="kt-durumlar">
            {Object.entries(k.durum).map(([kod, ad]) => <button type="button" key={kod} className={form.durum === kod ? 'secili' : ''} onClick={() => setForm({ ...form, durum: kod })}>{ad}</button>)}
          </div>
          <div className="kl-form">
            <input className="auth-input" required maxLength={160} autoFocus value={form.baslik} onChange={(e) => setForm({ ...form, baslik: e.target.value })} placeholder="Adı" />
            <input className="auth-input" maxLength={120} value={form.kisi} onChange={(e) => setForm({ ...form, kisi: e.target.value })} placeholder={`${k.kisi} (isteğe bağlı)`} />
            <select className="auth-input" value={form.alt_tur} onChange={(e) => setForm({ ...form, alt_tur: e.target.value })}>
              <option value="">Türü (isteğe bağlı)</option>{k.alt.map((a) => <option key={a}>{a}</option>)}
            </select>
            {form.durum !== 'istek' && <input className="auth-input" type="date" max={new Date().toISOString().slice(0, 10)} value={form.tarih} onChange={(e) => setForm({ ...form, tarih: e.target.value })} title="Ne zaman?" />}
          </div>
          {form.durum !== 'istek' && <div className="kt-puan">Ne kadar beğendin? <Yildiz deger={form.puan} onChange={(p) => setForm({ ...form, puan: p })} /></div>}
          <textarea className="auth-input" rows={3} maxLength={1500} value={form.notlar} onChange={(e) => setForm({ ...form, notlar: e.target.value })}
            placeholder={form.durum === 'istek' ? 'Neden ilgini çekti? (isteğe bağlı)' : 'Sana ne kattı, ne öğrendin? (isteğe bağlı)'} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn" disabled={bekle}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
            <button type="button" className="btn sec" onClick={() => setForm(null)}>Vazgeç</button>
          </div>
        </form>
      )}
      <div className="card"><KutuphaneListesi v={v} onDuzenle={setForm} onSil={sil} /></div>
    </div>
  )
}
