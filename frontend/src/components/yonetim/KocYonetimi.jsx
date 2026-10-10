// [2026-10-10] Anlaşmalı eğitim koçları + öğrenci görüşme talepleri — YALNIZCA süper admin.
// Her koç okul okul atanır (aktif / okul onayı bekleniyor / okul reddetti); öğrenci yalnızca okulunda aktif olanı görür.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere, tarih } from './ortak'

const BOS = { ad_soyad: '', unvan: '', hakkinda: '', alanlar: [], konular: [], deneyim_yil: '', gorusme_sekli: 'online', ucret_bilgisi: '', eposta: '', telefon: '', aktif: true }
const yerelZaman = (t) => {
  if (!t) return ''
  const d = new Date(t); const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`
}

function KocFormu({ ilk, meta, onKaydet, onIptal }) {
  const [f, setF] = useState({ ...BOS, ...ilk, deneyim_yil: ilk.deneyim_yil ?? '' })
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const alan = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const sec = (k, v) => setF({ ...f, [k]: f[k].includes(v) ? f[k].filter((x) => x !== v) : [...f[k], v] })
  const kaydet = async (e) => {
    e.preventDefault(); setBekle(true); setHata(null)
    try { await onKaydet({ ...f, deneyim_yil: f.deneyim_yil === '' ? null : Number(f.deneyim_yil) }) } catch (er) { setHata(er.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  return (
    <form className="yp-kutu" style={{ marginBottom: 12 }} onSubmit={kaydet}>
      <div className="yp-kb">{ilk.id ? 'Koçu düzenle' : 'Yeni koç'}</div>
      <div className="kl-form">
        <input className="auth-input" required minLength={3} maxLength={80} value={f.ad_soyad} onChange={alan('ad_soyad')} placeholder="Ad soyad" />
        <input className="auth-input" maxLength={80} value={f.unvan || ''} onChange={alan('unvan')} placeholder="Unvan (ör. Kariyer koçu, Psikolojik danışman)" />
        <input className="auth-input" type="number" min={0} max={60} value={f.deneyim_yil} onChange={alan('deneyim_yil')} placeholder="Deneyim (yıl)" />
        <select className="auth-input" value={f.gorusme_sekli} onChange={alan('gorusme_sekli')}>{meta.gorusme.map((g) => <option key={g.kod} value={g.kod}>{g.ad}</option>)}</select>
        <input className="auth-input" maxLength={120} value={f.ucret_bilgisi || ''} onChange={alan('ucret_bilgisi')} placeholder="Ücret bilgisi (ör. Okul anlaşmalı, ücretsiz)" />
        <input className="auth-input" type="email" maxLength={120} value={f.eposta || ''} onChange={alan('eposta')} placeholder="E-posta (öğrenci görmez)" />
        <input className="auth-input" maxLength={40} value={f.telefon || ''} onChange={alan('telefon')} placeholder="Telefon (öğrenci görmez)" />
      </div>
      <textarea className="auth-input" rows={3} maxLength={1000} value={f.hakkinda || ''} onChange={alan('hakkinda')} placeholder="Hakkında (öğrenci görür): deneyimi, yaklaşımı…" style={{ marginTop: 8 }} />
      <div className="yp-ince" style={{ margin: '8px 0 4px' }}>Uzman olduğu alanlar (öğrencinin hedef bölümüyle eşleştirilir)</div>
      <div>{meta.alanlar.map((a) => <button type="button" key={a.kod} className={`kl-ilgi${f.alanlar.includes(a.kod) ? ' secili' : ''}`} onClick={() => sec('alanlar', a.kod)}>{a.ad}</button>)}</div>
      <div className="yp-ince" style={{ margin: '8px 0 4px' }}>Görüşme konuları</div>
      <div>{meta.konular.map((k) => <button type="button" key={k} className={`kl-ilgi${f.konular.includes(k) ? ' secili' : ''}`} onClick={() => sec('konular', k)}>{k}</button>)}</div>
      <label style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 8, fontSize: 13 }}>
        <input type="checkbox" checked={f.aktif} onChange={(e) => setF({ ...f, aktif: e.target.checked })} /> Aktif (öğrencilere görünsün)
      </label>
      {hata && <div className="auth-error" style={{ marginTop: 8 }}>{hata}</div>}
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
        <button className="btn" type="submit" disabled={bekle}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
        <button className="btn sec" type="button" onClick={onIptal}>İptal</button>
      </div>
    </form>
  )
}

function TalepSatiri({ t, durumlar, okulGoster, onKaydedildi }) {
  const [f, setF] = useState({ durum: t.durum, randevu_zamani: yerelZaman(t.randevu_zamani), ogrenciye_not: t.ogrenciye_not || '', ic_not: t.ic_not || '' })
  const [acik, setAcik] = useState(t.durum === 'beklemede')
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const kaydet = async () => {
    setBekle(true); setHata(null)
    try {
      await api.kocTalebiGuncelle(t.id, { ...f, randevu_zamani: f.randevu_zamani ? new Date(f.randevu_zamani).toISOString() : null })
      onKaydedildi()
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  return (
    <div className={`kc-yt${t.durum === 'beklemede' ? ' bekliyor' : ''}`}>
      <div className="kc-yt-ust" onClick={() => setAcik(!acik)} role="button" tabIndex={0}>
        <span className={`kc-durum kc-durum-${{ beklemede: 'am', onaylandi: 'gr', tamamlandi: 'pu' }[t.durum] || 'tx3'}`}>{t.durum_metni}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <b>{t.ogrenci_ad}</b> <span className="yp-ince">{t.ogrenci_sinif}{okulGoster && t.okul_ad ? ` · ${t.okul_ad}` : ''}</span> → <b>{t.koc_ad}</b>
          <div className="yp-ince">{t.konu} · {tarih(t.olusturulma_zamani)}{t.talep_eden === 'veli' ? ' · veli adına' : ''}</div>
        </div>
        <span className="yp-ince">{acik ? '▲' : '▼'}</span>
      </div>
      {acik && (
        <div className="kc-yt-govde">
          <div className="yp-bilgi-grid">
            {t.talep_eden === 'veli' && <div><span>Veli</span><b>{t.veli_ad} · {t.iletisim}</b></div>}
            <div><span>Öğrenci e-posta</span><b>{t.ogrenci_eposta}</b></div>
            <div><span>Tercih ettiği zaman</span><b>{t.tercih_zamani || '—'}</b></div>
            <div><span>Koç iletişim</span><b>{[t.koc_eposta, t.koc_telefon].filter(Boolean).join(' · ') || '—'}</b></div>
            {t.mesaj && <div style={{ gridColumn: '1 / -1' }}><span>Mesajı</span><b style={{ fontWeight: 500 }}>{t.mesaj}</b></div>}
          </div>
          {t.durum === 'iptal' ? <div className="yp-ince">Öğrenci bu talebi iptal etti.</div> : (
            <>
              <div className="kl-form" style={{ marginTop: 10 }}>
                <select className="auth-input" value={f.durum} onChange={(e) => setF({ ...f, durum: e.target.value })}>{durumlar.map((d) => <option key={d.kod} value={d.kod}>{d.ad}</option>)}</select>
                <input className="auth-input" type="datetime-local" value={f.randevu_zamani} onChange={(e) => setF({ ...f, randevu_zamani: e.target.value })} title="Randevu zamanı" />
                <input className="auth-input" maxLength={500} value={f.ogrenciye_not} onChange={(e) => setF({ ...f, ogrenciye_not: e.target.value })} placeholder="Öğrenciye not (öğrenci görür)" />
                <input className="auth-input" maxLength={1000} value={f.ic_not} onChange={(e) => setF({ ...f, ic_not: e.target.value })} placeholder="İç not (yalnızca yönetim görür)" />
              </div>
              {hata && <div className="auth-error" style={{ marginTop: 6 }}>{hata}</div>}
              <button className="btn" style={{ marginTop: 8 }} disabled={bekle} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
            </>
          )}
        </div>
      )}
    </div>
  )
}

// Koçun çalıştığı okullar: okul okul aktif / okul onayı bekleniyor / okul reddetti
function OkulAtamaPenceresi({ koc, meta, onKapat, onKaydedildi }) {
  const ilk = Object.fromEntries((koc.okullar || []).map((o) => [o.okul_id, { durum: o.durum, notlar: o.notlar || '' }]))
  const [secim, setSecim] = useState(ilk)
  const [ara, setAra] = useState('')
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const degistir = (id, alan, deger) => setSecim((s) => ({ ...s, [id]: { ...(s[id] || { durum: 'aktif', notlar: '' }), [alan]: deger } }))
  const ac = (id, acik) => setSecim((s) => { const y = { ...s }; if (acik) y[id] = y[id] || { durum: 'aktif', notlar: '' }; else delete y[id]; return y })
  const hepsi = (acik) => setSecim(acik ? Object.fromEntries(meta.okullar.map((o) => [o.id, secim[o.id] || { durum: 'aktif', notlar: '' }])) : {})
  const kaydet = async () => {
    setBekle(true); setHata(null)
    try {
      await api.kocOkullari(koc.id, Object.entries(secim).map(([id, v]) => ({ okul_id: Number(id), durum: v.durum, notlar: v.notlar || null })))
      onKaydedildi()
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  const liste = meta.okullar.filter((o) => !ara || o.ad.toLocaleLowerCase('tr-TR').includes(ara.toLocaleLowerCase('tr-TR')))
  const sayi = (d) => Object.values(secim).filter((v) => v.durum === d).length
  return (
    <Pencere baslik={`${koc.ad_soyad} — çalıştığı okullar`} altBaslik="Öğrenciler koçu yalnızca durumu 'Aktif' olan okullarda görür." onKapat={onKapat} genis
      alt={<div style={{ display: 'flex', gap: 8, alignItems: 'center', width: '100%' }}>
        <span className="yp-ince" style={{ marginRight: 'auto' }}>Aktif {sayi('aktif')} · Onay bekleyen {sayi('onay_bekliyor')} · Reddeden {sayi('reddedildi')}</span>
        {hata && <span className="auth-error" style={{ margin: 0, padding: '4px 10px' }}>{hata}</span>}
        <button className="btn sec" onClick={onKapat}>Vazgeç</button>
        <button className="btn" disabled={bekle} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
      </div>}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <input className="yp-sec" value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Okul ara…" style={{ flex: 1, minWidth: 180 }} />
        <button className="yp-mini" onClick={() => hepsi(true)}>Tüm okullara ekle</button>
        <button className="yp-mini" onClick={() => hepsi(false)}>Hepsini kaldır</button>
      </div>
      <table className="yp-tablo">
        <thead><tr><th style={{ width: 36 }} /><th>Okul</th><th style={{ width: 210 }}>Durum</th><th>Not (ör. okul neden reddetti)</th></tr></thead>
        <tbody>
          {liste.map((o) => {
            const v = secim[o.id]
            return (
              <tr key={o.id} className={v ? '' : 'kl-pasif'}>
                <td><input type="checkbox" checked={!!v} onChange={(e) => ac(o.id, e.target.checked)} aria-label={`${o.ad} ata`} /></td>
                <td><b>{o.ad}</b></td>
                <td>{v ? <select className="yp-sec" value={v.durum} onChange={(e) => degistir(o.id, 'durum', e.target.value)}>{meta.okul_durumlari.map((d) => <option key={d.kod} value={d.kod}>{d.ad}</option>)}</select> : <span className="yp-ince">Atanmadı</span>}</td>
                <td>{v ? <input className="yp-sec" style={{ width: '100%' }} maxLength={300} value={v.notlar} onChange={(e) => degistir(o.id, 'notlar', e.target.value)} placeholder="İsteğe bağlı" /> : null}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </Pencere>
  )
}

const OKUL_RENK = { aktif: 'gr', onay_bekliyor: 'am', reddedildi: 'tx3' }

export default function KocYonetimi() {
  const [koclar, setKoclar] = useState(null)
  const [talepler, setTalepler] = useState(null)
  const [form, setForm] = useState(null)
  const [atama, setAtama] = useState(null)
  const [filtre, setFiltre] = useState('acik')
  const [okulFiltre, setOkulFiltre] = useState('')
  const [hata, setHata] = useState(null)
  const yukle = () => {
    api.yonetimKoclar().then(setKoclar).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
    api.kocTalepleri().then(setTalepler).catch(() => {})
  }
  useEffect(() => { yukle() }, [])
  if (hata) return <div className="auth-error">{hata}</div>
  if (!koclar || !talepler) return <div className="bos-durum">Yükleniyor…</div>

  const kaydet = async (f) => {
    if (f.id) await api.kocDuzenle(f.id, f)
    else {
      const r = await api.kocEkle(f)
      setForm(null); await yukle()
      setAtama({ ...f, id: r.id, okullar: [] })   // yeni koç: hemen okul ataması
      return
    }
    setForm(null); yukle()
  }
  const sil = async (k) => {
    if (!window.confirm(`${k.ad_soyad} silinsin mi?`)) return
    try { await api.kocSil(k.id); yukle() } catch (e) { window.alert(e.detail || 'Silinemedi.') }
  }
  const gosterilen = talepler.talepler.filter((t) => (!okulFiltre || String(t.okul_id) === okulFiltre)
    && (filtre === 'hepsi' || (filtre === 'acik' ? ['beklemede', 'onaylandi'].includes(t.durum) : !['beklemede', 'onaylandi'].includes(t.durum))))
  const talepOkullari = [...new Map(talepler.talepler.filter((t) => t.okul_id).map((t) => [t.okul_id, t.okul_ad])).entries()]

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="card" style={{ margin: 0 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
          <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>Görüşme talepleri {talepler.bekleyen > 0 && <span className="kc-rozet">{talepler.bekleyen} bekleyen</span>}</div>
          {talepOkullari.length > 1 && (
            <select className="yp-sec" value={okulFiltre} onChange={(e) => setOkulFiltre(e.target.value)}>
              <option value="">Tüm okullar</option>{talepOkullari.map(([id, ad]) => <option key={id} value={id}>{ad}</option>)}
            </select>
          )}
          <div className="kc-filtre" style={{ margin: 0 }}>
            {[['acik', 'Açık'], ['kapali', 'Sonuçlanan'], ['hepsi', 'Tümü']].map(([k, ad]) => <button key={k} className={filtre === k ? 'aktif' : ''} onClick={() => setFiltre(k)}>{ad}</button>)}
          </div>
        </div>
        <div className="yp-ince" style={{ marginBottom: 10 }}>Öğrenci koçun iletişim bilgisini görmez. Talebi inceleyip koçla iletişime geçin, durumu ve randevu zamanını girin. Öğrenci durumu ve "öğrenciye not"u kendi ekranında görür.</div>
        {gosterilen.length === 0 ? <div className="bos-durum">Bu filtrede talep yok.</div>
          : gosterilen.map((t) => <TalepSatiri key={`${t.id}-${t.guncelleme_zamani}`} t={t} durumlar={talepler.durumlar} okulGoster onKaydedildi={yukle} />)}
      </div>

      <div className="card" style={{ margin: 0 }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 12 }}>
          <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>Anlaşmalı koçlar ({koclar.koclar.length})</div>
          <button className="btn" onClick={() => setForm(BOS)}>+ Koç ekle</button>
        </div>
        {form && <KocFormu key={form.id || 'yeni'} ilk={form} meta={koclar} onKaydet={kaydet} onIptal={() => setForm(null)} />}
        {koclar.koclar.length === 0 ? <div className="bos-durum">Henüz koç eklenmedi.</div> : (
          <table className="yp-tablo">
            <thead><tr><th>Koç</th><th>Alanlar</th><th>Okullar</th><th>İletişim</th><th>Talep</th><th /></tr></thead>
            <tbody>
              {koclar.koclar.map((k) => {
                const n = (d) => k.okullar.filter((o) => o.durum === d).length
                return (
                  <tr key={k.id} className={k.aktif ? '' : 'kl-pasif'}>
                    <td><b>{k.ad_soyad}</b>{!k.aktif && <span className="ak-uyari-cip">pasif</span>}<div className="yp-ince">{k.unvan || ''}{k.deneyim_yil != null ? ` · ${k.deneyim_yil} yıl` : ''} · {k.gorusme_metni}</div></td>
                    <td>{k.alan_adlari.map((a) => <span key={a} className="ak-cip">{a}</span>)}</td>
                    <td>
                      {k.okullar.length === 0 ? <span className="kc-durum kc-durum-am">Hiçbir okula atanmadı</span> : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                          {k.okullar.slice(0, 4).map((o) => <span key={o.okul_id} className={`kc-durum kc-durum-${OKUL_RENK[o.durum]}`} title={`${o.durum_adi}${o.notlar ? ` — ${o.notlar}` : ''}`}>{o.okul_ad}{o.durum !== 'aktif' ? ` · ${o.durum === 'reddedildi' ? 'reddetti' : 'onay bekliyor'}` : ''}</span>)}
                          {k.okullar.length > 4 && <span className="yp-ince">+{k.okullar.length - 4} okul ({n('aktif')} aktif)</span>}
                        </div>
                      )}
                      <button className="yp-mini" style={{ marginTop: 6 }} onClick={() => setAtama(k)}>🏫 Okulları düzenle</button>
                    </td>
                    <td className="yp-ince">{k.eposta || '—'}{k.telefon && <div>{k.telefon}</div>}</td>
                    <td>{k.bekleyen > 0 ? <b style={{ color: 'var(--am)' }}>{k.bekleyen} bekleyen</b> : <span className="yp-ince">{k.toplam_talep || '—'}</span>}</td>
                    <td style={{ whiteSpace: 'nowrap' }}><button className="yp-mini" onClick={() => setForm(k)}>Düzenle</button>{' '}<button className="yp-mini" onClick={() => sil(k)}>Sil</button></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      {atama && <OkulAtamaPenceresi koc={atama} meta={koclar} onKapat={() => setAtama(null)} onKaydedildi={() => { setAtama(null); yukle() }} />}
    </div>
  )
}
