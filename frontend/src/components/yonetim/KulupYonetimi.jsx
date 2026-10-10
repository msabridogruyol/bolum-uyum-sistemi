// [2026-10-10] Okul paneli → Kulüpler: okulun kulüp listesi (hazır listeden ekle / düzenle), öğrencilerin ilgi testi özeti,
// her kulübü ilk 3 önerisinde gören öğrenciler. Öğrenci detayında da ilgi profili gösterilir (OgrenciIlgi).
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere } from './ortak'
import { DuyurularPenceresi, KatilmaTalepleri, UyelerPenceresi } from './KulupUyelikYonetimi'

const BOS = { ad: '', aciklama: '', ilgiler: [], sorumlu: '', bulusma: '', aktif: true }

function KulupFormu({ ilk, boyutlar, onKaydet, onIptal }) {
  const [f, setF] = useState(ilk)
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const alan = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const ilgi = (kod) => setF({ ...f, ilgiler: f.ilgiler.includes(kod) ? f.ilgiler.filter((x) => x !== kod) : [...f.ilgiler, kod].slice(0, 3) })
  const kaydet = async (e) => {
    e.preventDefault(); setBekle(true); setHata(null)
    try { await onKaydet(f) } catch (er) { setHata(er.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  return (
    <form className="yp-kutu" style={{ marginBottom: 12 }} onSubmit={kaydet}>
      <div className="yp-kb">{ilk.id ? 'Kulübü düzenle' : 'Yeni kulüp'}</div>
      <div className="kl-form">
        <input className="auth-input" required minLength={2} maxLength={80} value={f.ad} onChange={alan('ad')} placeholder="Kulüp adı" />
        <input className="auth-input" maxLength={300} value={f.aciklama || ''} onChange={alan('aciklama')} placeholder="Kısa açıklama (ne yapılıyor?)" />
        <input className="auth-input" maxLength={80} value={f.sorumlu || ''} onChange={alan('sorumlu')} placeholder="Danışman öğretmen" />
        <input className="auth-input" maxLength={80} value={f.bulusma || ''} onChange={alan('bulusma')} placeholder="Buluşma (ör. Çarşamba 15:30, Lab-2)" />
      </div>
      <div className="yp-ince" style={{ margin: '8px 0 4px' }}>İlgi alanları (en fazla 3, ilk seçilen ana alan sayılır). Öneriler bu etiketlere göre yapılır.</div>
      <div>
        {boyutlar.map((b) => {
          const i = f.ilgiler.indexOf(b.kod)
          return <button type="button" key={b.kod} className={`kl-ilgi${i >= 0 ? ' secili' : ''}`} onClick={() => ilgi(b.kod)}>{b.ikon} {b.ad}{i >= 0 && <sup>{i + 1}</sup>}</button>
        })}
      </div>
      <label className="ak-kutu" style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 8, fontSize: 13 }}>
        <input type="checkbox" checked={f.aktif} onChange={(e) => setF({ ...f, aktif: e.target.checked })} /> Aktif (öğrencilere önerilsin)
      </label>
      {hata && <div className="auth-error" style={{ marginTop: 8 }}>{hata}</div>}
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <button className="btn" type="submit" disabled={bekle || !f.ilgiler.length}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
        <button className="btn sec" type="button" onClick={onIptal}>İptal</button>
      </div>
    </form>
  )
}

export default function KulupYonetimi({ okulId }) {
  const [v, setV] = useState(null)
  const [form, setForm] = useState(null)
  const [liste, setListe] = useState(null)
  const [uyePen, setUyePen] = useState(null)      // [2026-10-10] üyeler / duyurular pencereleri
  const [duyuruPen, setDuyuruPen] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [mesaj, setMesaj] = useState(null)
  const yukle = () => api.okulKulupleri(okulId).then(setV).catch((e) => setMesaj({ hata: true, metin: e.detail || 'Yüklenemedi.' }))
  useEffect(() => { yukle() }, [okulId])
  if (!v) return mesaj ? <div className="auth-error">{mesaj.metin}</div> : <div className="bos-durum">Yükleniyor…</div>

  const kaydet = async (f) => {
    const veri = { ...f, id: undefined, ilgi_listesi: undefined, oneri_sayisi: undefined, uye_sayisi: undefined, bekleyen_talep: undefined }
    if (f.id) await api.kulupDuzenle(f.id, veri); else await api.kulupEkle(okulId, veri)
    setForm(null); yukle()
  }
  const hazir = async () => {
    setBekle(true); setMesaj(null)
    try { const r = await api.hazirKulupleriEkle(okulId); setMesaj({ metin: r.eklenen ? `${r.eklenen} kulüp eklendi. Okulunuzda olmayanları silebilir ya da pasif yapabilirsiniz.` : 'Hazır listedeki tüm kulüpler zaten ekli.' }); yukle() } catch (e) { setMesaj({ hata: true, metin: e.detail || 'Eklenemedi.' }) }
    setBekle(false)
  }
  const sil = async (k) => {
    if (!window.confirm(`"${k.ad}" silinsin mi?`)) return
    try { await api.kulupSil(k.id); yukle() } catch (e) { setMesaj({ hata: true, metin: e.detail || 'Silinemedi.' }) }
  }
  const aktifDegistir = async (k) => {
    try { await api.kulupDuzenle(k.id, { ad: k.ad, aciklama: k.aciklama, ilgiler: k.ilgi_listesi, sorumlu: k.sorumlu, bulusma: k.bulusma, aktif: !k.aktif }); yukle() } catch (e) { setMesaj({ hata: true, metin: e.detail || 'Güncellenemedi.' }) }
  }
  const ad = Object.fromEntries(v.boyutlar.map((b) => [b.kod, b]))
  const enCok = Math.max(1, ...v.kulupler.map((k) => k.oneri_sayisi))

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <KatilmaTalepleri okulId={okulId} onDegisti={yukle} />
      <div className="yp-iki">
        <div className="card" style={{ margin: 0 }}>
          <div className="ct">İlgi testi</div>
          <div className="yp-kpi-grid" style={{ marginBottom: 10 }}>
            <div className="yp-kpi"><div className="yp-kpi-e">Testi çözen</div><div className="yp-kpi-d">{v.test_yapan}</div><div className="yp-kpi-a">/ {v.ogrenci_sayisi} öğrenci</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Aktif kulüp</div><div className="yp-kpi-d">{v.kulupler.filter((k) => k.aktif).length}</div></div>
          </div>
          <div className="yp-ince">Öğrenciler testi <b>Kulüplerim</b> sayfasından çözer (20 soru, ~3 dk). Sonuç bölüm önerilerini etkilemez.</div>
        </div>
        <div className="card" style={{ margin: 0 }}>
          <div className="ct">Okulun ilgi profili (ortalama)</div>
          {v.okul_ilgi.length === 0 ? <div className="bos-durum">Henüz testi çözen öğrenci yok.</div> : v.okul_ilgi.map((b) => (
            <div key={b.kod} className="yp-cubuk-satir"><span>{b.ikon} {b.ad}</span>
              <div className="yp-cubuk"><div style={{ width: `${Math.max(3, b.ort)}%`, background: 'var(--okul-c, var(--pu))' }} /><span>%{b.ort}</span></div></div>
          ))}
        </div>
      </div>

      <div className="card" style={{ margin: 0 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
          <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>Kulüpler ({v.kulupler.length})</div>
          <button className="btn sec" disabled={bekle} onClick={hazir}>{bekle ? <span className="spin" /> : `📋 Hazır listeden ekle (${v.hazir_sayisi})`}</button>
          <button className="btn" onClick={() => setForm(BOS)}>+ Kulüp ekle</button>
        </div>
        {mesaj && <div className={mesaj.hata ? 'auth-error' : 'yp-basari'} style={{ marginBottom: 10 }}>{mesaj.metin}</div>}
        {form && <KulupFormu key={form.id || 'yeni'} ilk={form} boyutlar={v.boyutlar} onKaydet={kaydet} onIptal={() => setForm(null)} />}
        {v.kulupler.length === 0 ? (
          <div className="bos-durum">Henüz kulüp yok. "Hazır listeden ekle" ile lise kulüplerinde yaygın 30 kulübü ekleyip okulunuzda olmayanları silebilirsiniz.</div>
        ) : (
          <table className="yp-tablo">
            <thead><tr><th>Kulüp</th><th>İlgi alanları</th><th>Danışman · buluşma</th><th style={{ width: '18%' }} title="Bu kulübü ilk 3 önerisinde gören öğrenci sayısı">Önerilen öğrenci</th><th>Üyeler</th><th /></tr></thead>
            <tbody>
              {v.kulupler.map((k) => (
                <tr key={k.id} className={k.aktif ? '' : 'kl-pasif'}>
                  <td><b>{k.ad}</b>{!k.aktif && <span className="ak-uyari-cip">pasif</span>}{k.aciklama && <div className="yp-ince">{k.aciklama}</div>}</td>
                  <td>{k.ilgi_listesi.map((x) => <span key={x} className="ak-cip">{ad[x]?.ikon} {ad[x]?.ad}</span>)}</td>
                  <td className="yp-ince">{k.sorumlu || '—'}{k.bulusma && <div>{k.bulusma}</div>}</td>
                  <td>{k.oneri_sayisi > 0 ? (
                    <button className="kl-sayi" onClick={() => api.kulupOgrencileri(k.id).then(setListe)}>
                      <div className="yp-cubuk"><div style={{ width: `${(100 * k.oneri_sayisi) / enCok}%`, background: 'var(--okul-c, var(--pu))' }} /><span>{k.oneri_sayisi} öğrenci</span></div>
                    </button>) : <span className="yp-ince">—</span>}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button className="yp-mini" onClick={() => setUyePen(k)}>👥 {k.uye_sayisi}</button>
                    {k.bekleyen_talep > 0 && <span className="kt-sayi" title="Bekleyen katılma talebi">{k.bekleyen_talep} talep</span>}
                  </td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button className="yp-mini" onClick={() => setDuyuruPen(k)}>📣 Duyurular</button>{' '}
                    <button className="yp-mini" onClick={() => setForm({ ...k, ilgiler: k.ilgi_listesi })}>Düzenle</button>{' '}
                    <button className="yp-mini" onClick={() => aktifDegistir(k)}>{k.aktif ? 'Pasif yap' : 'Aktif yap'}</button>{' '}
                    <button className="yp-mini" onClick={() => sil(k)}>Sil</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {uyePen && <UyelerPenceresi kulup={uyePen} onKapat={() => setUyePen(null)} onDegisti={yukle} />}
      {duyuruPen && <DuyurularPenceresi kulup={duyuruPen} onKapat={() => setDuyuruPen(null)} />}
      {liste && (
        <Pencere baslik={liste.kulup} altBaslik="Bu kulübü ilk 3 önerisinde gören öğrenciler" onKapat={() => setListe(null)}>
          <table className="yp-tablo">
            <thead><tr><th>Öğrenci</th><th>Sınıf</th><th>Öneri sırası</th><th>Uyum</th></tr></thead>
            <tbody>{liste.ogrenciler.map((o) => <tr key={o.id}><td><b>{o.ad_soyad}</b></td><td>{o.sinif || '—'}</td><td>{o.sira}.</td><td>%{o.uyum}</td></tr>)}</tbody>
          </table>
        </Pencere>
      )}
    </div>
  )
}

// Öğrenci detay penceresinde: ilgi profili + kulüp önerileri
export function OgrenciIlgi({ ogrenciId }) {
  const [v, setV] = useState(null)
  useEffect(() => { api.ogrenciIlgi(ogrenciId).then(setV).catch(() => setV({ hata: true })) }, [ogrenciId])
  if (!v) return <div className="bos-durum">Yükleniyor…</div>
  if (v.hata) return <div className="auth-error">Yüklenemedi.</div>
  if (!v.sonuc) return <div className="bos-durum">Öğrenci kısa ilgi testini henüz çözmedi (Kulüplerim sayfası).</div>
  const sirali = v.boyutlar.map((b) => ({ ...b, puan: v.sonuc.puanlar[b.kod] ?? 0 })).sort((a, b) => b.puan - a.puan)
  return (
    <div className="yp-iki">
      <div>
        <div className="yp-kb">İlgi profili</div>
        {sirali.map((b) => (
          <div key={b.kod} className="yp-cubuk-satir"><span>{b.ikon} {b.ad}</span>
            <div className="yp-cubuk"><div style={{ width: `${Math.max(3, b.puan)}%` }} /><span>%{b.puan}</span></div></div>
        ))}
      </div>
      <div>
        <div className="yp-kb">{v.okul_kulubu_var ? 'Okul kulüplerinden öneriler' : 'Uygun kulüp türleri (okul listesi girilmemiş)'}</div>
        {v.oneriler.map((k, i) => (
          <div key={k.id ?? k.ad} style={{ padding: '6px 0', borderBottom: '1px solid var(--bor)' }}>
            <b>{i + 1}. {k.ad}</b> <span className="yp-ince">%{k.uyum}</span>
            <div className="yp-ince">{k.neden}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
