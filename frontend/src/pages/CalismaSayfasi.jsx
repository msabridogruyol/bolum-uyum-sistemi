// [2026-10-10] Çalışmam — haftalık ders programı, günlük çalışma süresi ve soru kaydı, ders bazında isabet.
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

const GUN_KISA = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const kisaTarih = (t) => { const d = new Date(`${t}T12:00`); return `${d.getDate()} ${AY[d.getMonth()]}` }
const saatMetni = (dk) => { const s = Math.floor(dk / 60), m = dk % 60; return s ? `${s} sa${m ? ` ${m} dk` : ''}` : `${m} dk` }
const bugunGun = () => (new Date().getDay() + 6) % 7   // 0 = Pazartesi
const RENK = 'var(--kt-izleme, #2a78d6)'

// ----------------------------------------------------------------------------- haftalık grafik (tek seri + plan çizgisi)
function HaftaGrafigi({ haftalar, plan }) {
  const [ip, setIp] = useState(null)
  const G = 960, Y = 230, sol = 44, alt = 26, ust = 12
  const enCok = Math.max(60, plan || 0, ...haftalar.map((h) => h.dk)) * 1.1
  const y = (v) => ust + (Y - ust - alt) * (1 - v / enCok)
  const genis = (G - sol - 10) / haftalar.length
  const cizgi = [0, 0.5, 1].map((o) => Math.round((enCok * o) / 60) * 60)
  return (
    <div style={{ position: 'relative' }}>
      <svg viewBox={`0 0 ${G} ${Y}`} width="100%" role="img" aria-label="Haftalık çalışma süresi">
        {cizgi.map((v) => (
          <g key={v}>
            <line x1={sol} x2={G - 6} y1={y(v)} y2={y(v)} stroke="var(--bor)" strokeWidth="1" />
            <text x={sol - 6} y={y(v) + 4} textAnchor="end" className="ng-eksen">{v / 60} sa</text>
          </g>
        ))}
        {haftalar.map((h, i) => {
          const x = sol + i * genis + genis * 0.3, w = genis * 0.4, bu = i === haftalar.length - 1
          return (
            <g key={h.hafta} onMouseEnter={() => setIp({ h, px: (x + w / 2) / G })} onMouseLeave={() => setIp(null)}>
              {h.dk > 0 && <path d={`M${x},${y(0)} V${y(h.dk) + 4} q0,-4 4,-4 h${w - 8} q4,0 4,4 V${y(0)} Z`} fill={RENK} opacity={bu ? 1 : 0.55} />}
              <rect x={sol + i * genis} y={ust} width={genis} height={Y - ust - alt} fill="transparent" />
              <text x={x + w / 2} y={Y - 6} textAnchor="middle" className="ng-eksen">{bu ? 'Bu hafta' : kisaTarih(h.hafta)}</text>
            </g>
          )
        })}
        {plan > 0 && <line x1={sol} x2={G - 6} y1={y(plan)} y2={y(plan)} stroke="var(--tx2)" strokeWidth="2" strokeDasharray="5 4" />}
      </svg>
      {ip && (
        <div className="ng-ipucu" style={{ left: `${ip.px * 100}%`, top: 70 }}>
          <b>{kisaTarih(ip.h.hafta)} haftası</b>
          <span>{saatMetni(ip.h.dk)} çalışma</span>
          <span>{ip.h.soru} soru</span>
        </div>
      )}
      <div className="cl-lejant">
        <span><i style={{ background: RENK }} />Çalışılan süre</span>
        {plan > 0 && <span><i className="cizgi" />Haftalık programın ({saatMetni(plan)})</span>}
      </div>
    </div>
  )
}

// ----------------------------------------------------------------------------- kayıt formu
function KayitFormu({ v, varsayilan, onKaydet }) {
  const bos = { tarih: v.bugun, ders: v.dersler[0].kod, sure_dk: 60, soru: '', dogru: '', yanlis: '', konu: '' }
  const [f, setF] = useState({ ...bos, ...varsayilan })
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  useEffect(() => { if (varsayilan) setF((x) => ({ ...x, ...varsayilan })) }, [varsayilan])
  const s = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const sayi = (x) => (x === '' || x == null ? null : Number(x))
  async function kaydet(e) {
    e.preventDefault(); setBekle(true); setHata(null)
    try {
      await onKaydet({ tarih: f.tarih, ders: f.ders, sure_dk: Number(f.sure_dk) || 0, soru: Number(f.soru) || 0, dogru: sayi(f.dogru), yanlis: sayi(f.yanlis), konu: f.konu || null })
      setF({ ...bos, ders: f.ders, tarih: f.tarih })
    } catch (er) { setHata(er.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  const konular = v.konular[f.ders] || []
  const enEski = new Date(Date.now() - 14 * 86400000).toISOString().slice(0, 10)
  return (
    <form className="card cl-form" onSubmit={kaydet}>
      <div className="ct">✍️ Çalışmanı kaydet</div>
      <div className="cl-alanlar">
        <label><span>Tarih</span><input className="auth-input" type="date" min={enEski} max={v.bugun} value={f.tarih} onChange={s('tarih')} /></label>
        <label className="genis"><span>Ders</span>
          <select className="auth-input" value={f.ders} onChange={(e) => setF({ ...f, ders: e.target.value, konu: '' })}>{v.dersler.map((d) => <option key={d.kod} value={d.kod}>{d.ad}</option>)}</select>
        </label>
        <label><span>Süre (dk)</span><input className="auth-input" type="number" min="0" max="720" step="5" value={f.sure_dk} onChange={s('sure_dk')} /></label>
        <label><span>Çözülen soru</span><input className="auth-input" type="number" min="0" max="1000" value={f.soru} onChange={s('soru')} placeholder="0" /></label>
        <label><span>Doğru <small>(isteğe bağlı)</small></span><input className="auth-input" type="number" min="0" value={f.dogru} onChange={s('dogru')} /></label>
        <label><span>Yanlış <small>(isteğe bağlı)</small></span><input className="auth-input" type="number" min="0" value={f.yanlis} onChange={s('yanlis')} /></label>
        <label className="genis"><span>Konu <small>(isteğe bağlı)</small></span>
          <input className="auth-input" list="cl-konular" maxLength={120} value={f.konu} onChange={s('konu')} placeholder={konular.length ? `ör. ${konular[0]}` : ''} />
          <datalist id="cl-konular">{konular.map((k) => <option key={k} value={k} />)}</datalist>
        </label>
      </div>
      <div className="cl-hizli">
        {[30, 45, 60, 90, 120].map((d) => <button type="button" key={d} className={Number(f.sure_dk) === d ? 'secili' : ''} onClick={() => setF({ ...f, sure_dk: d })}>{d} dk</button>)}
      </div>
      {hata && <div className="auth-error" style={{ margin: '8px 0 0' }}>{hata}</div>}
      <button className="btn" style={{ marginTop: 12 }} disabled={bekle}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
    </form>
  )
}

// ----------------------------------------------------------------------------- bugün
function BugunSekmesi({ v, setV }) {
  const [varsayilan, setVarsayilan] = useState(null)
  const oz = v.ozet
  const bugunku = v.program.filter((b) => b.gun === bugunGun())
  const bugunKayit = v.kayitlar.filter((k) => k.tarih === v.bugun)
  const yapildi = (b) => bugunKayit.some((k) => k.ders === b.ders)
  const ad = (kod) => v.dersler.find((d) => d.kod === kod)?.ad || kod
  async function sil(id) { setV(await api.calismaKayitSil(id)) }
  return (
    <>
      <div className="yp-kpi-grid" style={{ marginBottom: 14 }}>
        <div className="yp-kpi"><div className="yp-kpi-e">Bu hafta</div><div className="yp-kpi-d">{saatMetni(oz.bu_hafta.dk)}</div>{oz.bu_hafta.plan_dk > 0 && <div className="yp-kpi-a">Programın: {saatMetni(oz.bu_hafta.plan_dk)} · %{oz.bu_hafta.uyum}</div>}</div>
        <div className="yp-kpi"><div className="yp-kpi-e">Bu hafta soru</div><div className="yp-kpi-d">{oz.bu_hafta.soru}</div><div className="yp-kpi-a">{oz.bu_hafta.gun} gün çalıştın</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Seri</div><div className="yp-kpi-d">{oz.seri > 0 ? `🔥 ${oz.seri}` : '—'}</div><div className="yp-kpi-a">{oz.seri > 0 ? 'gün üst üste' : 'Bugün bir kayıt gir, seri başlasın'}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Son 28 gün</div><div className="yp-kpi-d">{oz.son_28_gun.soru}</div><div className="yp-kpi-a">soru · {saatMetni(oz.son_28_gun.dk)}</div></div>
      </div>
      <div className="cl-iki">
        <div>
          <div className="card">
            <div className="ct">📅 Bugünün programı · {['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'][bugunGun()]}</div>
            {bugunku.length === 0 ? <div className="yp-ince">Bugün için programında blok yok. <b>Haftalık program</b> sekmesinden ekleyebilirsin.</div> : bugunku.map((b) => (
              <div key={b.id} className={`cl-blok-satir${yapildi(b) ? ' tamam' : ''}`}>
                <span className="cl-saat">{b.baslangic}</span>
                <span style={{ flex: 1 }}><b>{ad(b.ders)}</b> <span className="yp-ince">{saatMetni(b.sure_dk)}{b.notlar ? ` · ${b.notlar}` : ''}</span></span>
                {yapildi(b) ? <span className="cl-tik">✓ Kaydedildi</span>
                  : <button className="yp-mini" onClick={() => setVarsayilan({ ders: b.ders, sure_dk: b.sure_dk, tarih: v.bugun })}>Çalıştım →</button>}
              </div>
            ))}
          </div>
          <div className="card">
            <div className="ct">Son kayıtların</div>
            {v.kayitlar.length === 0 ? <div className="yp-ince">Henüz kayıt yok.</div> : (
              <table className="yp-tablo">
                <thead><tr><th>Tarih</th><th>Ders</th><th>Süre</th><th>Soru</th><th>D / Y</th><th /></tr></thead>
                <tbody>
                  {v.kayitlar.slice(0, 20).map((k) => (
                    <tr key={k.id}>
                      <td>{kisaTarih(k.tarih)}</td>
                      <td>{k.ders_ad}{k.konu && <div className="yp-ince">{k.konu}</div>}</td>
                      <td>{k.sure_dk ? saatMetni(k.sure_dk) : '—'}</td>
                      <td>{k.soru || '—'}</td>
                      <td className="yp-ince">{k.dogru != null || k.yanlis != null ? `${k.dogru ?? 0} / ${k.yanlis ?? 0}` : '—'}</td>
                      <td><button className="hg-link" onClick={() => sil(k.id)}>Sil</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
        <KayitFormu v={v} varsayilan={varsayilan} onKaydet={async (x) => setV(await api.calismaKayitEkle(x))} />
      </div>
    </>
  )
}

// ----------------------------------------------------------------------------- program düzenleyici
function ProgramSekmesi({ v, setV }) {
  const [bloklar, setBloklar] = useState(() => v.program.map(({ gun, baslangic, sure_dk, ders, notlar }) => ({ gun, baslangic, sure_dk, ders, notlar })))
  const [yeni, setYeni] = useState(null)   // { gun, baslangic, sure_dk, ders }
  const [degisti, setDegisti] = useState(false)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [kaydedildi, setKaydedildi] = useState(false)
  const ad = (kod) => v.dersler.find((d) => d.kod === kod)?.ad || kod
  const gunluk = (g) => bloklar.map((b, i) => ({ ...b, i })).filter((b) => b.gun === g).sort((a, b) => a.baslangic.localeCompare(b.baslangic))
  const toplam = bloklar.reduce((a, b) => a + Number(b.sure_dk), 0)
  function ekle(e) {
    e.preventDefault()
    setBloklar([...bloklar, { ...yeni, sure_dk: Number(yeni.sure_dk) }]); setYeni(null); setDegisti(true); setKaydedildi(false)
  }
  const sil = (i) => { setBloklar(bloklar.filter((_, j) => j !== i)); setDegisti(true); setKaydedildi(false) }
  function gunuKopyala(kaynak) {
    const hedef = (kaynak + 1) % 7
    setBloklar([...bloklar.filter((b) => b.gun !== hedef), ...bloklar.filter((b) => b.gun === kaynak).map((b) => ({ ...b, gun: hedef }))]); setDegisti(true); setKaydedildi(false)
  }
  async function kaydet() {
    setBekle(true); setHata(null)
    try { setV(await api.calismaProgramKaydet(bloklar)); setDegisti(false); setKaydedildi(true) } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  return (
    <>
      <div className="cl-program-ust">
        <div className="yp-ince">Her hafta tekrar eden ders programın. Okul sonrası gerçekçi bloklar koy; Bugün sekmesinde o günün blokları seni bekler.</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span className="yp-ince">Haftalık toplam <b>{saatMetni(toplam)}</b></span>
          <button className="btn" disabled={!degisti || bekle} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Programı kaydet'}</button>
        </div>
      </div>
      {kaydedildi && <div className="yp-basari" style={{ marginBottom: 10 }}>✓ Programın kaydedildi.</div>}
      {hata && <div className="auth-error">{hata}</div>}
      <div className="cl-hafta">
        {GUN_KISA.map((g, gi) => (
          <div key={g} className={`cl-gun${gi === bugunGun() ? ' bugun' : ''}`}>
            <div className="cl-gun-ust"><b>{g}</b><span className="yp-ince">{saatMetni(gunluk(gi).reduce((a, b) => a + Number(b.sure_dk), 0))}</span></div>
            {gunluk(gi).map((b) => (
              <div key={b.i} className="cl-blok">
                <div className="cl-blok-saat">{b.baslangic} · {b.sure_dk} dk</div>
                <div className="cl-blok-ders">{ad(b.ders)}</div>
                {b.notlar && <div className="yp-ince">{b.notlar}</div>}
                <button className="cl-blok-sil" aria-label="Bloğu sil" onClick={() => sil(b.i)}>×</button>
              </div>
            ))}
            {yeni?.gun === gi ? (
              <form className="cl-yeni" onSubmit={ekle}>
                <input className="auth-input" type="time" required value={yeni.baslangic} onChange={(e) => setYeni({ ...yeni, baslangic: e.target.value })} />
                <select className="auth-input" value={yeni.ders} onChange={(e) => setYeni({ ...yeni, ders: e.target.value })}>{v.dersler.map((d) => <option key={d.kod} value={d.kod}>{d.ad}</option>)}</select>
                <select className="auth-input" value={yeni.sure_dk} onChange={(e) => setYeni({ ...yeni, sure_dk: e.target.value })}>{[30, 45, 60, 90, 120, 150, 180].map((d) => <option key={d} value={d}>{d} dk</option>)}</select>
                <input className="auth-input" maxLength={80} placeholder="Not (isteğe bağlı)" value={yeni.notlar || ''} onChange={(e) => setYeni({ ...yeni, notlar: e.target.value })} />
                <div style={{ display: 'flex', gap: 4 }}><button className="yp-mini">Ekle</button><button type="button" className="yp-mini" onClick={() => setYeni(null)}>Vazgeç</button></div>
              </form>
            ) : (
              <div className="cl-gun-alt">
                <button className="hg-link" onClick={() => setYeni({ gun: gi, baslangic: gi >= 5 ? '10:00' : '17:00', sure_dk: 60, ders: v.dersler[0].kod })}>+ Blok</button>
                {gunluk(gi).length > 0 && <button className="hg-link" title={`${GUN_KISA[(gi + 1) % 7]} gününe kopyala`} onClick={() => gunuKopyala(gi)}>⧉ Ertesi güne</button>}
              </div>
            )}
          </div>
        ))}
      </div>
    </>
  )
}

// ----------------------------------------------------------------------------- istatistik
function IstatistikSekmesi({ v }) {
  const oz = v.ozet
  const enCok = Math.max(1, ...oz.dersler.map((d) => d.soru))
  return (
    <>
      <div className="card"><div className="ct">⏱️ Haftalık çalışma süren</div><HaftaGrafigi haftalar={oz.haftalar} plan={oz.bu_hafta.plan_dk} /></div>
      <div className="card">
        <div className="ct">Ders ders · son 28 gün</div>
        {oz.dersler.length === 0 ? <div className="yp-ince">Kayıt girdikçe burada ders ders soru sayın ve isabetin görünür.</div> : (
          <table className="yp-tablo">
            <thead><tr><th>Ders</th><th>Süre</th><th style={{ width: '34%' }}>Çözülen soru</th><th>İsabet</th></tr></thead>
            <tbody>
              {oz.dersler.map((d) => (
                <tr key={d.ders}>
                  <td>{d.ad}</td>
                  <td>{saatMetni(d.dk)}</td>
                  <td><div className="cl-soru"><div className="nt-cubuk" style={{ flex: 1 }}><div style={{ width: `${(100 * d.soru) / enCok}%`, background: RENK }} /></div><b>{d.soru}</b></div></td>
                  <td>{d.isabet != null ? <><b>%{d.isabet}</b> <span className="yp-ince">({d.dogru}D {d.yanlis}Y)</span></> : <span className="yp-ince" title="Doğru / yanlış girilen en az 10 soru gerekir">—</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="yp-ince" style={{ marginTop: 8 }}>İsabet, doğru ve yanlışını girdiğin sorulardan hesaplanır (en az 10 soru). Boş bıraktıkların dahil edilmez.</div>
      </div>
    </>
  )
}

export default function CalismaSayfasi() {
  const [params, setParams] = useSearchParams()
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const sekme = params.get('sekme') || 'bugun'
  useEffect(() => { api.calisma().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [])
  const git = (k) => setParams(k === 'bugun' ? {} : { sekme: k }, { replace: true })
  const SEKMELER = useMemo(() => [['bugun', '✍️ Bugün'], ['program', '📅 Haftalık program'], ['istatistik', '📊 İstatistik']], [])
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Çalışmam</div>
        <div className="ps">Haftalık programını yap, her gün ne kadar çalıştığını ve kaç soru çözdüğünü kaydet; hangi derste ne kadar isabetli olduğunu gör.</div>
      </div>
      <div className="koc-sekmeler" role="tablist">
        {SEKMELER.map(([k, ad]) => <button key={k} role="tab" aria-selected={sekme === k} className={sekme === k ? 'aktif' : ''} onClick={() => git(k)}>{ad}</button>)}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v ? !hata && <div className="bos-durum">Yükleniyor…</div> : (
        <>
          {sekme === 'bugun' && <BugunSekmesi v={v} setV={setV} />}
          {sekme === 'program' && <ProgramSekmesi v={v} setV={setV} />}
          {sekme === 'istatistik' && <IstatistikSekmesi v={v} />}
        </>
      )}
    </div>
  )
}
