// [2026-10-10] Portfolyom — sertifika, yarışma, gönüllülük, proje … kayıtları (okul onayı), hakkımda / yetenekler / diller, PDF özgeçmiş.
import { useEffect, useState } from 'react'
import { api } from '../api/client'

const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const ayYil = (t) => { if (!t) return ''; const [y, m] = t.split('-'); return `${AY[Number(m) - 1]} ${y}` }
export const donemMetni = (k) => {
  const a = ayYil(k.baslangic), b = ayYil(k.bitis)
  if (a && b) return a === b ? a : `${a} – ${b}`
  return a ? `${a} –` : b
}

function dosyaOku(f) {
  return new Promise((coz, red) => { const r = new FileReader(); r.onload = () => coz(String(r.result)); r.onerror = () => red(new Error('Dosya okunamadı.')); r.readAsDataURL(f) })
}

// ----------------------------------------------------------------------------- kayıt formu
function KayitFormu({ turler, mevcut, onKaydet, onVazgec }) {
  const [f, setF] = useState(() => mevcut
    ? { tur: mevcut.tur, baslik: mevcut.baslik, kurum: mevcut.kurum || '', baslangic: mevcut.baslangic || '', bitis: mevcut.bitis || '', aciklama: mevcut.aciklama || '', saat: mevcut.saat ?? '', derece: mevcut.derece || '', link: mevcut.link || '' }
    : { tur: 'sertifika', baslik: '', kurum: '', baslangic: '', bitis: '', aciklama: '', saat: '', derece: '', link: '' })
  const [belge, setBelge] = useState(null)   // { ad, veri } | '' (kaldır) | null (değiştirme)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const s = (k) => (e) => setF({ ...f, [k]: e.target.value })
  async function sec(e) {
    const d = e.target.files?.[0]; e.target.value = ''
    if (!d) return
    if (d.size > 1024 * 1024) { setHata('Belge en fazla 1 MB olabilir.'); return }
    setHata(null); setBelge({ ad: d.name, veri: await dosyaOku(d) })
  }
  async function kaydet(e) {
    e.preventDefault(); setBekle(true); setHata(null)
    try {
      await onKaydet({
        ...f, kurum: f.kurum || null, baslangic: f.baslangic || null, bitis: f.bitis || null, aciklama: f.aciklama || null,
        saat: f.tur === 'gonullu' && f.saat !== '' ? Number(f.saat) : null, derece: f.derece || null, link: f.link || null,
        belge: belge === null ? null : belge === '' ? '' : belge.veri, belge_adi: belge ? belge.ad : null,
      })
    } catch (er) { setHata(er.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  return (
    <form className="card pf-form" onSubmit={kaydet}>
      <div className="ct">{mevcut ? 'Kaydı düzenle' : 'Yeni kayıt'}</div>
      {mevcut?.dogrulandi && <div className="yp-uyari" style={{ marginBottom: 10 }}>Bu kayıt okul tarafından onaylandı. Değiştirirsen onay kalkar; rehber öğretmenin yeniden onaylaması gerekir.</div>}
      <div className="pf-turler" role="radiogroup" aria-label="Tür">
        {turler.map((t) => <button type="button" key={t.kod} className={f.tur === t.kod ? 'secili' : ''} onClick={() => setF({ ...f, tur: t.kod })}>{t.ikon} {t.ad}</button>)}
      </div>
      <div className="pf-alanlar">
        <label className="genis"><span>Başlık</span><input className="auth-input" required minLength={2} maxLength={140} value={f.baslik} onChange={s('baslik')} placeholder={f.tur === 'yarisma' ? 'ör. TÜBİTAK 2204-A Lise Araştırma Projeleri' : f.tur === 'sertifika' ? 'ör. Python ile Veri Analizi' : ''} /></label>
        <label className="genis"><span>Kurum / kuruluş <small>(isteğe bağlı)</small></span><input className="auth-input" maxLength={120} value={f.kurum} onChange={s('kurum')} /></label>
        <label><span>Başlangıç</span><input className="auth-input" type="date" value={f.baslangic} onChange={s('baslangic')} /></label>
        <label><span>Bitiş <small>(boşsa devam ediyor)</small></span><input className="auth-input" type="date" value={f.bitis} onChange={s('bitis')} /></label>
        {f.tur === 'yarisma' && <label><span>Derece / sonuç</span><input className="auth-input" maxLength={80} value={f.derece} onChange={s('derece')} placeholder="ör. Bölge 2.si, Finalist" /></label>}
        {f.tur === 'gonullu' && <label><span>Toplam saat</span><input className="auth-input" type="number" min="0" max="5000" value={f.saat} onChange={s('saat')} /></label>}
        <label className="genis"><span>Açıklama <small>(ne yaptın, ne öğrendin?)</small></span><textarea className="auth-input" rows={3} maxLength={1000} value={f.aciklama} onChange={s('aciklama')} /></label>
        <label className="genis"><span>Bağlantı <small>(sertifika doğrulama adresi, proje sayfası…)</small></span><input className="auth-input" maxLength={400} value={f.link} onChange={s('link')} placeholder="https://…" /></label>
        <div className="genis pf-belge">
          <label className="btn sec" style={{ cursor: 'pointer' }}>📎 {mevcut?.belge_var || belge ? 'Belgeyi değiştir' : 'Belge ekle'} (PDF / görsel, en çok 1 MB)<input type="file" hidden accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={sec} /></label>
          {belge && <span className="yp-ince">{belge.ad}</span>}
          {!belge && mevcut?.belge_var && belge !== '' && <button type="button" className="hg-link" onClick={() => setBelge('')}>Belgeyi kaldır</button>}
          {belge === '' && <span className="yp-ince">Belge kaldırılacak</span>}
          <span className="yp-ince">Belge, rehber öğretmeninin kaydı onaylamasını kolaylaştırır.</span>
        </div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <button className="btn" disabled={bekle}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
        <button type="button" className="btn sec" onClick={onVazgec}>Vazgeç</button>
      </div>
    </form>
  )
}

// ----------------------------------------------------------------------------- kayıt kartı (öğrenci ve yönetim ortak)
export function KayitKarti({ k, belgeIndir, children }) {
  return (
    <div className={`pf-kart${k.dogrulandi ? ' onayli' : ''}`}>
      <div className="pf-ikon" aria-hidden="true">{k.ikon}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="pf-ust">
          <b>{k.baslik}</b>
          {k.dogrulandi ? <span className="pf-rozet onay" title={`Onaylayan: ${k.dogrulayan || ''}`}>✓ Okul onaylı</span> : <span className="pf-rozet">Onay bekliyor</span>}
        </div>
        <div className="yp-ince">{[k.tur_ad, k.kurum, donemMetni(k), k.derece, k.saat ? `${k.saat} saat` : null].filter(Boolean).join(' · ')}</div>
        {k.aciklama && <div className="pf-aciklama">{k.aciklama}</div>}
        <div className="pf-alt">
          {k.link && <a href={k.link} target="_blank" rel="noopener noreferrer" className="hg-link">🔗 Bağlantı</a>}
          {k.belge_var && <button className="hg-link" onClick={() => belgeIndir(k)}>📎 {k.belge_adi || 'Belge'}</button>}
          {children}
        </div>
      </div>
    </div>
  )
}

// ----------------------------------------------------------------------------- hakkımda
function Profil({ v, setV }) {
  const [duzen, setDuzen] = useState(false)
  const [f, setF] = useState(v.profil)
  const [yeniYetenek, setYeniYetenek] = useState('')
  const [hata, setHata] = useState(null)
  const p = v.profil
  async function kaydet() {
    setHata(null)
    try { setV(await api.portfolyoProfil({ ...f, diller: f.diller.filter((d) => d.dil.trim()) })); setDuzen(false) } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
  }
  if (!duzen) {
    return (
      <div className="card">
        <div className="ct" style={{ display: 'flex', justifyContent: 'space-between' }}>👤 Hakkımda <button className="hg-link" onClick={() => { setF(p); setDuzen(true) }}>✎ Düzenle</button></div>
        {p.hakkimda ? <div className="pf-hakkimda">{p.hakkimda}</div> : <div className="yp-ince">Kendini 2-3 cümleyle anlat: neye ilgi duyuyorsun, neler yapmaktan hoşlanıyorsun, hangi alanda ilerlemek istiyorsun?</div>}
        {(p.yetenekler.length > 0 || p.diller.length > 0) && (
          <div className="pf-cipler">
            {p.diller.map((d) => <span key={d.dil} className="pf-cip dil">🌐 {d.dil} · {d.seviye}</span>)}
            {p.yetenekler.map((y) => <span key={y} className="pf-cip">{y}</span>)}
          </div>
        )}
      </div>
    )
  }
  return (
    <div className="card">
      <div className="ct">👤 Hakkımda</div>
      <textarea className="auth-input" rows={4} maxLength={1200} value={f.hakkimda} onChange={(e) => setF({ ...f, hakkimda: e.target.value })} placeholder="ör. Yer bilimlerine ve teknolojiye ilgi duyuyorum…" />
      <div className="pf-alt-baslik">Yetenekler</div>
      <div className="pf-cipler">
        {f.yetenekler.map((y) => <span key={y} className="pf-cip">{y} <button aria-label={`${y} sil`} onClick={() => setF({ ...f, yetenekler: f.yetenekler.filter((x) => x !== y) })}>×</button></span>)}
        <form onSubmit={(e) => { e.preventDefault(); const y = yeniYetenek.trim(); if (y && !f.yetenekler.includes(y)) setF({ ...f, yetenekler: [...f.yetenekler, y] }); setYeniYetenek('') }}>
          <input className="auth-input pf-cip-giris" maxLength={40} placeholder="+ yetenek (Enter)" value={yeniYetenek} onChange={(e) => setYeniYetenek(e.target.value)} />
        </form>
      </div>
      <div className="pf-alt-baslik">Diller</div>
      {f.diller.map((d, i) => (
        <div key={i} className="pf-dil">
          <input className="auth-input" maxLength={30} value={d.dil} placeholder="Dil" onChange={(e) => setF({ ...f, diller: f.diller.map((x, j) => j === i ? { ...x, dil: e.target.value } : x) })} />
          <select className="auth-input" value={d.seviye} onChange={(e) => setF({ ...f, diller: f.diller.map((x, j) => j === i ? { ...x, seviye: e.target.value } : x) })}>{v.dil_seviyeleri.map((s) => <option key={s}>{s}</option>)}</select>
          <button className="hg-link" onClick={() => setF({ ...f, diller: f.diller.filter((_, j) => j !== i) })}>Sil</button>
        </div>
      ))}
      <button className="hg-link" onClick={() => setF({ ...f, diller: [...f.diller, { dil: '', seviye: 'B1' }] })}>+ Dil ekle</button>
      <label className="pf-onay"><input type="checkbox" checked={f.eposta_goster} onChange={(e) => setF({ ...f, eposta_goster: e.target.checked })} /> E-posta adresim özgeçmişte görünsün</label>
      {hata && <div className="auth-error">{hata}</div>}
      <div style={{ display: 'flex', gap: 8, marginTop: 10 }}><button className="btn" onClick={kaydet}>Kaydet</button><button className="btn sec" onClick={() => setDuzen(false)}>Vazgeç</button></div>
    </div>
  )
}

export default function PortfolyoSayfasi() {
  const [v, setV] = useState(null)
  const [form, setForm] = useState(null)   // {} yeni · {mevcut}
  const [silOnay, setSilOnay] = useState(null)
  const [hata, setHata] = useState(null)
  const [pdf, setPdf] = useState(false)
  useEffect(() => { api.portfolyo().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [])
  async function pdfIndir() { setPdf(true); setHata(null); try { await api.portfolyoPdf() } catch (e) { setHata(e.detail || 'İndirilemedi.') } finally { setPdf(false) } }
  if (!v) return <div className="pg"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>
  const gruplar = v.turler.map((t) => ({ ...t, liste: v.kayitlar.filter((k) => k.tur === t.kod) })).filter((g) => g.liste.length)
  return (
    <div className="pg pg-genis">
      <div className="ph" style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div>
          <div className="pt">Portfolyom</div>
          <div className="ps">Sertifikalarını, yarışmalarını, gönüllü çalışmalarını ve projelerini bir yerde topla. Rehber öğretmenin onayladıkça özgeçmişinde “Okul onaylı” olarak görünür.</div>
        </div>
      </div>
      <div className="pf-ust-satir">
        <div className="yp-kpi-grid" style={{ flex: 1, margin: 0 }}>
          <div className="yp-kpi"><div className="yp-kpi-e">Kayıt</div><div className="yp-kpi-d">{v.ozet.toplam}</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Okul onaylı</div><div className="yp-kpi-d" style={{ color: 'var(--gr)' }}>{v.ozet.dogrulanan}</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Gönüllülük</div><div className="yp-kpi-d">{v.ozet.gonullu_saat}</div><div className="yp-kpi-a">saat</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Kulüp</div><div className="yp-kpi-d">{v.kulupler.length}</div></div>
        </div>
        <div className="pf-dugmeler">
          <button className="btn" disabled={pdf} onClick={pdfIndir}>{pdf ? <span className="spin" /> : '📄 Özgeçmişimi indir (PDF)'}</button>
          {!form && <button className="btn sec" onClick={() => setForm({})}>+ Kayıt ekle</button>}
        </div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {form && <KayitFormu turler={v.turler} mevcut={form.mevcut} onVazgec={() => setForm(null)}
        onKaydet={async (x) => { setV(form.mevcut ? await api.portfolyoKayitDuzenle(form.mevcut.id, x) : await api.portfolyoKayitEkle(x)); setForm(null) }} />}
      <div className="pf-duzen">
        <div>
          {gruplar.length === 0 && !form && (
            <div className="card bos-durum" style={{ padding: 28 }}>
              🗂️ Henüz kayıt yok. Bir kurs sertifikası, katıldığın bir yarışma ya da gönüllü bir çalışmayla başla.
              <div style={{ marginTop: 12 }}><button className="btn" onClick={() => setForm({})}>+ İlk kaydını ekle</button></div>
            </div>
          )}
          {gruplar.map((g) => (
            <div key={g.kod} className="card">
              <div className="ct">{g.ikon} {g.ad}</div>
              {g.liste.map((k) => (
                <KayitKarti key={k.id} k={k} belgeIndir={(x) => api.portfolyoBelge(x.id)}>
                  <button className="hg-link" onClick={() => { setForm({ mevcut: k }); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>✎ Düzenle</button>
                  {silOnay === k.id
                    ? <><button className="hg-link" style={{ color: 'var(--re)' }} onClick={async () => { setV(await api.portfolyoKayitSil(k.id)); setSilOnay(null) }}>Evet, sil</button><button className="hg-link" onClick={() => setSilOnay(null)}>Vazgeç</button></>
                    : <button className="hg-link" onClick={() => setSilOnay(k.id)}>Sil</button>}
                </KayitKarti>
              ))}
            </div>
          ))}
        </div>
        <div>
          <Profil v={v} setV={setV} />
          <div className="card">
            <div className="ct">🎭 Okul kulüplerim</div>
            {v.kulupler.length === 0 ? <div className="yp-ince">Onaylanan kulüp üyeliklerin burada ve özgeçmişinde kendiliğinden görünür.</div>
              : v.kulupler.map((k) => <div key={k.ad} className="pf-kulup"><b>{k.ad}</b><span className="yp-ince">{ayYil(k.baslangic)}’dan beri</span></div>)}
          </div>
        </div>
      </div>
    </div>
  )
}
