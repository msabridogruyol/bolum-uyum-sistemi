// [2026-10-10] Tercihlerim — 12. sınıf / mezun: tercih listesi (en çok 24), güvenli / dengeli / riskli, Filizyol uyumu, rehber onayı, sonucumu bildir.
import { useEffect, useState } from 'react'
import { api } from '../api/client'

export const RISK = {
  guvenli: { ad: 'Güvenli', ikon: '●', renk: 'var(--gr)', zemin: 'var(--grl)' },
  dengeli: { ad: 'Dengeli', ikon: '◐', renk: 'var(--am)', zemin: 'var(--aml)' },
  riskli: { ad: 'Riskli', ikon: '○', renk: 'var(--re)', zemin: 'var(--rel)' },
}
const DURUM_RENK = { taslak: 'var(--tx3)', incelemede: 'var(--am)', onaylandi: 'var(--gr)', duzeltme: 'var(--re)' }
const sayi = (v) => (v == null ? '—' : Number(v).toLocaleString('tr-TR'))

export function RiskCipi({ r }) {
  if (!r) return <span className="yp-ince" title="Taban sıralaması girilmedi">—</span>
  const x = RISK[r]
  return <span className="tr-risk" style={{ color: x.renk, background: x.zemin }}><span aria-hidden="true">{x.ikon}</span> {x.ad}</span>
}

// Liste tablosu — öğrenci (düzenlenebilir) ve rehber (salt okunur) ortak
export function TercihTablosu({ v, duzenle, tasi, sil }) {
  return (
    <div className="od-tablo-kap" style={{ maxHeight: 'none' }}>
      <table className="yp-tablo tr-tablo">
        <thead><tr><th>#</th><th>Üniversite</th><th>Program</th><th>Tür / burs</th><th>Geçen yıl taban sıra</th><th>Durum</th><th>Filizyol uyumu</th>{duzenle && <th />}</tr></thead>
        <tbody>
          {v.tercihler.map((t, i) => (
            <tr key={i}>
              <td><b>{i + 1}</b></td>
              <td>{t.universite}{t.sehir && <div className="yp-ince">{t.sehir}</div>}</td>
              <td>{t.bolum_ad}{t.hedef && <span className="tr-hedef" title="Hedef bölümün">🎯 Hedef</span>}{t.notlar && <div className="yp-ince">{t.notlar}</div>}</td>
              <td className="yp-ince">{[t.tur_ad, t.burs].filter(Boolean).join(' · ')}</td>
              <td>{sayi(t.taban_siralama)}</td>
              <td><RiskCipi r={t.risk} /></td>
              <td>{t.uyum != null ? <span title={`Önerilerinde ${t.oneri_sirasi}. sırada`}><b>%{t.uyum}</b> <span className="yp-ince">#{t.oneri_sirasi}</span></span> : <span className="yp-ince">—</span>}</td>
              {duzenle && (
                <td className="tr-islem">
                  <button className="yp-mini" disabled={i === 0} onClick={() => tasi(i, -1)} aria-label="Yukarı">↑</button>
                  <button className="yp-mini" disabled={i === v.tercihler.length - 1} onClick={() => tasi(i, 1)} aria-label="Aşağı">↓</button>
                  <button className="yp-mini" onClick={() => duzenle(i)} aria-label="Düzenle">✎</button>
                  <button className="yp-mini" onClick={() => sil(i)} aria-label="Sil">×</button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function RiskOzeti({ s }) {
  const toplam = s.guvenli + s.dengeli + s.riskli
  return (
    <div className="tr-ozet">
      <div className="tr-sayac"><b>{s.toplam}</b><span>/ {s.en_fazla} tercih</span></div>
      <div style={{ flex: 1, minWidth: 200 }}>
        {toplam > 0 && (
          <div className="an-yigin" style={{ height: 14 }}>
            {['guvenli', 'dengeli', 'riskli'].map((k) => s[k] > 0 && <div key={k} style={{ flex: s[k], background: RISK[k].renk }} title={`${RISK[k].ad}: ${s[k]}`} />)}
          </div>
        )}
        <div className="tr-lejant">
          {['guvenli', 'dengeli', 'riskli'].map((k) => <span key={k}><i style={{ background: RISK[k].renk }} />{RISK[k].ad} <b>{s[k]}</b></span>)}
          {s.toplam - toplam > 0 && <span className="yp-ince">Hesaplanamayan {s.toplam - toplam}</span>}
        </div>
      </div>
    </div>
  )
}

function SatirFormu({ v, mevcut, onTamam, onVazgec }) {
  const [f, setF] = useState(mevcut || { universite: '', bolum_ad: '', bolum_id: null, tur: 'devlet', burs: 'Ücretsiz', sehir: '', taban_siralama: '', notlar: '' })
  const s = (k) => (e) => setF({ ...f, [k]: e.target.value })
  function bolumSec(e) {
    const id = Number(e.target.value) || null
    const b = v.bolumler.find((x) => x.id === id)
    setF({ ...f, bolum_id: id, bolum_ad: b ? b.ad.charAt(0) + b.ad.slice(1).toLocaleLowerCase('tr') : f.bolum_ad })
  }
  return (
    <form className="card tr-form" onSubmit={(e) => { e.preventDefault(); onTamam({ ...f, taban_siralama: f.taban_siralama === '' ? null : Number(f.taban_siralama) }) }}>
      <div className="ct">{mevcut ? 'Tercihi düzenle' : 'Tercih ekle'}</div>
      <div className="pf-alanlar">
        <label className="genis"><span>Üniversite</span><input className="auth-input" required minLength={2} maxLength={140} value={f.universite} onChange={s('universite')} placeholder="ör. Orta Doğu Teknik Üniversitesi" /></label>
        <label><span>Bölüm (Filizyol listesinden)</span>
          <select className="auth-input" value={f.bolum_id || ''} onChange={bolumSec}>
            <option value="">— listede yok / seçme —</option>
            {v.bolumler.map((b) => <option key={b.id} value={b.id}>{b.ad}{b.uyum != null ? ` · %${b.uyum} uyum` : ''}</option>)}
          </select>
        </label>
        <label><span>Program adı</span><input className="auth-input" required minLength={2} maxLength={160} value={f.bolum_ad} onChange={s('bolum_ad')} placeholder="ör. Maden Mühendisliği (İngilizce)" /></label>
        <label><span>Üniversite türü</span><select className="auth-input" value={f.tur} onChange={s('tur')}>{Object.entries(v.secenekler.turler).map(([k, a]) => <option key={k} value={k}>{a}</option>)}</select></label>
        <label><span>Burs / ücret</span><select className="auth-input" value={f.burs || ''} onChange={s('burs')}><option value="">—</option>{v.secenekler.burslar.map((b) => <option key={b}>{b}</option>)}</select></label>
        <label><span>Şehir</span><input className="auth-input" maxLength={40} value={f.sehir || ''} onChange={s('sehir')} /></label>
        <label><span>Geçen yıl taban başarı sırası <small>(YÖK Atlas)</small></span><input className="auth-input" type="number" min="1" value={f.taban_siralama ?? ''} onChange={s('taban_siralama')} placeholder="ör. 88000" /></label>
        <label className="genis"><span>Not <small>(isteğe bağlı)</small></span><input className="auth-input" maxLength={200} value={f.notlar || ''} onChange={s('notlar')} /></label>
      </div>
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}><button className="btn">{mevcut ? 'Güncelle' : 'Listeye ekle'}</button><button type="button" className="btn sec" onClick={onVazgec}>Vazgeç</button></div>
    </form>
  )
}

function SonucumuBildir({ v, onKaydet }) {
  const y = v.yerlesme
  const [acik, setAcik] = useState(false)
  const [f, setF] = useState({ durum: y?.durum || 'yerlesti', universite: y?.universite || '', bolum_ad: y?.bolum_ad || '', bolum_id: y?.bolum_id || null, burs: y?.burs || '', siralama: y?.siralama || '' })
  const [hata, setHata] = useState(null)
  async function kaydet(e) {
    e.preventDefault(); setHata(null)
    try { await onKaydet({ ...f, siralama: f.siralama === '' ? null : Number(f.siralama), burs: f.burs || null }); setAcik(false) } catch (er) { setHata(er.detail || 'Kaydedilemedi.') }
  }
  return (
    <div className="card">
      <div className="ct">🎉 Sonucumu bildir</div>
      {y && !acik ? (
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <div><b>{v.secenekler.mezun_durumlari[y.durum]}</b>{y.universite ? ` — ${y.universite}` : ''}{y.bolum_ad ? `, ${y.bolum_ad}` : ''} <span className="yp-ince">({y.yil})</span></div>
          <button className="hg-link" onClick={() => setAcik(true)}>Değiştir</button>
        </div>
      ) : !acik ? (
        <div className="yp-ince">YKS sonuçları açıklandığında nereye yerleştiğini buraya yaz; okulun mezunlarının yolculuğunu böyle takip ediyor. <button className="hg-link" onClick={() => setAcik(true)}>Bildir →</button></div>
      ) : (
        <form onSubmit={kaydet}>
          <div className="pf-alanlar">
            <label><span>Durum</span><select className="auth-input" value={f.durum} onChange={(e) => setF({ ...f, durum: e.target.value })}>{Object.entries(v.secenekler.mezun_durumlari).map(([k, a]) => <option key={k} value={k}>{a}</option>)}</select></label>
            {f.durum === 'yerlesti' && <>
              <label><span>Üniversite</span><input className="auth-input" maxLength={140} value={f.universite} onChange={(e) => setF({ ...f, universite: e.target.value })} /></label>
              <label><span>Bölüm</span>
                <select className="auth-input" value={f.bolum_id || ''} onChange={(e) => { const id = Number(e.target.value) || null; const b = v.bolumler?.find((x) => x.id === id); setF({ ...f, bolum_id: id, bolum_ad: b ? b.ad : f.bolum_ad }) }}>
                  <option value="">— seç —</option>{(v.bolumler || []).map((b) => <option key={b.id} value={b.id}>{b.ad}</option>)}
                </select>
              </label>
              <label><span>Burs</span><select className="auth-input" value={f.burs} onChange={(e) => setF({ ...f, burs: e.target.value })}><option value="">—</option>{v.secenekler.burslar.map((b) => <option key={b}>{b}</option>)}</select></label>
            </>}
            <label><span>Başarı sıran <small>(isteğe bağlı)</small></span><input className="auth-input" type="number" min="1" value={f.siralama} onChange={(e) => setF({ ...f, siralama: e.target.value })} /></label>
          </div>
          {hata && <div className="auth-error">{hata}</div>}
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}><button className="btn">Kaydet</button><button type="button" className="btn sec" onClick={() => setAcik(false)}>Vazgeç</button></div>
        </form>
      )}
    </div>
  )
}

export default function TercihSayfasi() {
  const [v, setV] = useState(null)
  const [liste, setListe] = useState([])
  const [bilgi, setBilgi] = useState({ puan_turu: '', siralama: '', puan: '' })
  const [form, setForm] = useState(null)      // { i } | {}
  const [degisti, setDegisti] = useState(false)
  const [hata, setHata] = useState(null)
  const [mesaj, setMesaj] = useState(null)
  const [bekle, setBekle] = useState(false)
  function yukle(x) {
    setV(x); setListe(x.tercihler.map(({ universite, bolum_ad, bolum_id, tur, burs, sehir, taban_siralama, notlar }) => ({ universite, bolum_ad, bolum_id, tur, burs, sehir, taban_siralama, notlar })))
    setBilgi({ puan_turu: x.liste.puan_turu || '', siralama: x.liste.siralama ?? '', puan: x.liste.puan ?? '' }); setDegisti(false)
  }
  useEffect(() => { api.tercih().then(yukle).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [])
  if (!v) return <div className="pg"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>
  if (!v.uygun) return <div className="pg"><div className="card bos-durum">Tercih listesi 12. sınıf ve mezun öğrenciler içindir.</div></div>
  const degis = (l) => { setListe(l); setDegisti(true); setMesaj(null) }
  async function kaydet() {
    setBekle(true); setHata(null)
    try {
      const r = await api.tercihKaydet({ puan_turu: bilgi.puan_turu || null, siralama: bilgi.siralama === '' ? null : Number(bilgi.siralama), puan: bilgi.puan === '' ? null : Number(bilgi.puan), tercihler: liste })
      yukle(r); setMesaj(r.onay_dustu ? 'Kaydedildi. Liste değiştiği için rehber onayı kalktı; yeniden gönderebilirsin.' : 'Kaydedildi.')
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  async function gonder() { setHata(null); try { yukle(await api.tercihGonder()); setMesaj('Listen rehber öğretmenine gönderildi.') } catch (e) { setHata(e.detail || 'Gönderilemedi.') } }
  // tabloda kaydedilmemiş satırlar için önizleme (risk/uyum sunucudan gelir; yeni satırda boş görünür)
  const gorunum = { ...v, tercihler: liste.map((t, i) => ({ ...(v.tercihler[i] && v.tercihler[i].universite === t.universite && v.tercihler[i].bolum_ad === t.bolum_ad ? v.tercihler[i] : {}), ...t, tur_ad: v.secenekler.turler[t.tur] })) }
  const durum = v.liste.durum
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Tercihlerim</div>
        <div className="ps">YKS tercih listeni hazırla: her programın geçen yılki taban sırasıyla kendi sıranı karşılaştır, Filizyol uyumunu gör ve rehber öğretmenine onaya gönder.</div>
      </div>
      {v.tercihler.length > 0 && (
        <div className="tr-durum" style={{ borderColor: DURUM_RENK[durum] }}>
          <b style={{ color: DURUM_RENK[durum] }}>{v.liste.durum_adi}</b>
          {v.liste.rehber_notu && <div className="tr-not">💬 <i>{v.liste.rehber || 'Rehber öğretmenin'}:</i> {v.liste.rehber_notu}</div>}
        </div>
      )}
      <div className="card">
        <div className="ct">Puan ve sıralama bilgin</div>
        <div className="tr-bilgi">
          <label><span>Puan türü</span><select className="auth-input" value={bilgi.puan_turu} onChange={(e) => { setBilgi({ ...bilgi, puan_turu: e.target.value }); setDegisti(true) }}><option value="">—</option>{v.secenekler.puan_turleri.map((p) => <option key={p}>{p}</option>)}</select></label>
          <label><span>Başarı sıran</span><input className="auth-input" type="number" min="1" value={bilgi.siralama} onChange={(e) => { setBilgi({ ...bilgi, siralama: e.target.value }); setDegisti(true) }} placeholder="Sonuç açıklanınca ya da denemene göre tahmini" /></label>
          <label><span>Puanın <small>(isteğe bağlı)</small></span><input className="auth-input" type="number" step="0.001" value={bilgi.puan} onChange={(e) => { setBilgi({ ...bilgi, puan: e.target.value }); setDegisti(true) }} /></label>
        </div>
        <div className="yp-ince" style={{ marginTop: 8 }}>Güvenli: sıran programın geçen yılki taban sırasının %85'inden iyi · Dengeli: %85–110 · Riskli: daha geride. Taban sıraları her yıl değişir; bu bir tahmin değil, yön göstericidir.</div>
      </div>
      <RiskOzeti s={{ ...v.sayilar, toplam: liste.length }} />
      {v.uyarilar.length > 0 && !degisti && <div className="tr-uyarilar">{v.uyarilar.map((u) => <div key={u}>⚠️ {u}</div>)}</div>}
      {form && <SatirFormu v={v} mevcut={form.i != null ? liste[form.i] : null} onVazgec={() => setForm(null)}
        onTamam={(t) => { degis(form.i != null ? liste.map((x, j) => (j === form.i ? t : x)) : [...liste, t]); setForm(null) }} />}
      <div className="card">
        <div className="ct" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span>Tercih listem</span>
          {!form && liste.length < v.sayilar.en_fazla && <button className="btn sec" onClick={() => setForm({})}>+ Tercih ekle</button>}
        </div>
        {liste.length === 0 ? <div className="bos-durum">Henüz tercih eklemedin. En çok istediğin programdan başla; listenin sonuna güvenli seçenekler koymayı unutma.</div>
          : <TercihTablosu v={gorunum} duzenle={(i) => setForm({ i })} sil={(i) => degis(liste.filter((_, j) => j !== i))}
              tasi={(i, d) => { const l = [...liste]; const [x] = l.splice(i, 1); l.splice(i + d, 0, x); degis(l) }} />}
        {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}
        {mesaj && <div className="yp-basari" style={{ marginTop: 10 }}>✓ {mesaj}</div>}
        <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <button className="btn" disabled={!degisti || bekle} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
          <button className="btn sec" disabled={degisti || !v.tercihler.length || durum === 'incelemede'} onClick={gonder}>📤 Rehberime gönder</button>
          {degisti && <span className="yp-ince">Kaydedilmemiş değişiklik var.</span>}
          {durum === 'incelemede' && !degisti && <span className="yp-ince">Rehber öğretmenin inceliyor.</span>}
        </div>
      </div>
      <SonucumuBildir v={v} onKaydet={async (x) => { const r = await api.yerlesmeBildir(x); setV({ ...v, yerlesme: r.yerlesme }) }} />
    </div>
  )
}
