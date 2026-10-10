// [2026-10-10] Net Takibi — denemelerim (net grafiği + ders özeti), konu takibi ve hedef programa göre net kıyası.
// Hedef netler YÖK Atlas Net Sihirbazı'ndan: geçen yıl o programa yerleşen SON öğrencinin netleri (+ önceki yıllar).
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

const OTURUM_RENK = { TYT: 'var(--kt-izleme)', AYT: 'var(--kt-kitap)', YDT: 'var(--kt-kurs)' }
const SEKMELER = [['denemeler', '📝 Denemelerim'], ['konular', '📚 Konu Takibi'], ['hedef', '🎯 Hedefe Göre']]
const KONU_DURUM = [
  { k: 'baslamadi', ad: 'Başlamadım', ikon: '○' },
  { k: 'calisiyor', ad: 'Çalışıyorum', ikon: '◐' },
  { k: 'bitti', ad: 'Bitti', ikon: '●' },
  { k: 'tekrar', ad: 'Tekrar', ikon: '↻' },
]
// Deneme testi → ilgili konu dersleri (açık olan derste hangi konuların bitmediğini göstermek için)
const TEST_KONU = {
  tyt_trk: ['tyt_turkce'], tyt_mat: ['tyt_matematik', 'tyt_geometri'], tyt_fen: ['tyt_fizik', 'tyt_kimya', 'tyt_biyoloji'],
  tyt_sos: ['tyt_tarih', 'tyt_cografya', 'tyt_felsefe', 'tyt_din'], ayt_mat: ['ayt_matematik', 'ayt_geometri'],
  ayt_fiz: ['ayt_fizik'], ayt_kim: ['ayt_kimya'], ayt_bio: ['ayt_biyoloji'], ayt_tde: ['ayt_edebiyat'],
  ayt_trh1: ['ayt_tarih'], ayt_trh2: ['ayt_tarih'], ayt_cog1: ['ayt_cografya'], ayt_cog2: ['ayt_cografya'], ayt_fel: ['ayt_felsefe'],
}
const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const kisaTarih = (t) => { const d = new Date(t); return `${d.getDate()} ${AY[d.getMonth()]}` }
const n2 = (x) => (x == null ? '—' : Number(x).toLocaleString('tr-TR', { maximumFractionDigits: 2 }))
const bugunISO = () => new Date().toISOString().slice(0, 10)

// ---------------------------------------------------------------- grafik
function NetGrafigi({ denemeler, hedefler }) {
  const [ipucu, setIpucu] = useState(null)
  const oturumlar = ['TYT', 'AYT', 'YDT'].filter((o) => denemeler.some((d) => d.oturum === o))
  if (denemeler.length === 0) return null
  const G = 940, Y = 300, sol = 36, sag = 112, ust = 16, alt = 26
  const zamanlar = denemeler.map((d) => new Date(d.tarih).getTime())
  const t0 = Math.min(...zamanlar), t1 = Math.max(...zamanlar)
  const enCok = Math.max(10, ...denemeler.map((d) => d.toplam_net), ...Object.values(hedefler).filter((v) => v != null))
  const yMax = Math.ceil(enCok / 20) * 20
  const x = (t) => (t1 === t0 ? (sol + G - sag) / 2 : sol + ((t - t0) / (t1 - t0)) * (G - sol - sag))
  const y = (v) => ust + (1 - Math.max(0, v) / yMax) * (Y - ust - alt)
  const izgara = [0, 0.25, 0.5, 0.75, 1].map((k) => Math.round(yMax * k))
  return (
    <div className="ng-kap" onMouseLeave={() => setIpucu(null)}>
      <svg viewBox={`0 0 ${G} ${Y}`} className="ng-svg" role="img" aria-label="Deneme netlerinin zamana göre değişimi">
        {izgara.map((v) => (
          <g key={v}>
            <line x1={sol} x2={G - sag} y1={y(v)} y2={y(v)} className="ng-izgara" />
            <text x={sol - 6} y={y(v) + 4} className="ng-eksen" textAnchor="end">{v}</text>
          </g>
        ))}
        {oturumlar.map((o) => hedefler[o] != null && (
          <g key={`h-${o}`}>
            <line x1={sol} x2={G - sag} y1={y(hedefler[o])} y2={y(hedefler[o])} stroke={OTURUM_RENK[o]} className="ng-hedef" />
            <text x={G - sag + 6} y={y(hedefler[o]) + 4} className="ng-etiket-hedef">Hedef {o} {Math.round(hedefler[o])}</text>
          </g>
        ))}
        {oturumlar.map((o) => {
          const l = denemeler.filter((d) => d.oturum === o)
          const yol = l.map((d, i) => `${i ? 'L' : 'M'}${x(new Date(d.tarih).getTime())},${y(d.toplam_net)}`).join(' ')
          const son = l[l.length - 1]
          return (
            <g key={o}>
              <path d={yol} fill="none" stroke={OTURUM_RENK[o]} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
              {l.map((d) => (
                <g key={d.id}>
                  <circle cx={x(new Date(d.tarih).getTime())} cy={y(d.toplam_net)} r="4.5" fill={OTURUM_RENK[o]} stroke="var(--sur)" strokeWidth="2" />
                  <circle cx={x(new Date(d.tarih).getTime())} cy={y(d.toplam_net)} r="14" fill="transparent"
                    onMouseEnter={() => setIpucu({ d, px: x(new Date(d.tarih).getTime()) / G, py: y(d.toplam_net) / Y })} />
                </g>
              ))}
              <text x={x(new Date(son.tarih).getTime()) + 8} y={y(son.toplam_net) - 8} className="ng-etiket" fill={OTURUM_RENK[o]}>{o} {n2(son.toplam_net)}</text>
            </g>
          )
        })}
        {[...new Set(denemeler.map((d) => d.tarih))].map((t, i, a) => (i === 0 || i === a.length - 1 || a.length <= 6) && (
          <text key={t} x={x(new Date(t).getTime())} y={Y - 6} className="ng-eksen" textAnchor="middle">{kisaTarih(t)}</text>
        ))}
      </svg>
      {ipucu && (
        <div className="ng-ipucu" style={{ left: `${ipucu.px * 100}%`, top: `${ipucu.py * 100}%` }}>
          <b>{ipucu.d.ad || `${ipucu.d.oturum} denemesi`}</b>
          <span>{kisaTarih(ipucu.d.tarih)} · {ipucu.d.oturum}</span>
          <span>Toplam <b>{n2(ipucu.d.toplam_net)}</b> net</span>
        </div>
      )}
      <div className="ng-lejant">
        {oturumlar.map((o) => <span key={o}><i style={{ background: OTURUM_RENK[o] }} />{o} toplam net</span>)}
        {Object.values(hedefler).some((v) => v != null) && <span><i className="ng-lejant-kesik" />Hedef program (geçen yıl)</span>}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- deneme formu
function DenemeFormu({ yapi, onKaydet, onVazgec }) {
  const oturumlar = ['TYT', ...(yapi.testler.some((t) => t.oturum === 'AYT') ? ['AYT'] : []), ...(yapi.testler.some((t) => t.oturum === 'YDT') ? ['YDT'] : [])]
  const [f, setF] = useState({ tarih: bugunISO(), oturum: 'TYT', ad: '', dersler: {} })
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const testler = yapi.testler.filter((t) => t.oturum === f.oturum)
  const deger = (k, a) => f.dersler[k]?.[a] ?? ''
  const yaz = (k, a, v) => setF({ ...f, dersler: { ...f.dersler, [k]: { ...f.dersler[k], [a]: v === '' ? '' : Math.max(0, parseInt(v, 10) || 0) } } })
  const net = (k) => { const d = Number(f.dersler[k]?.d || 0), y = Number(f.dersler[k]?.y || 0); return d - y / 4 }
  const asim = (t) => Number(f.dersler[t.kod]?.d || 0) + Number(f.dersler[t.kod]?.y || 0) > t.soru
  const toplam = testler.reduce((a, t) => a + net(t.kod), 0)
  async function kaydet(e) {
    e.preventDefault(); setHata(null)
    const dersler = Object.fromEntries(testler.filter((t) => f.dersler[t.kod] && (f.dersler[t.kod].d !== '' || f.dersler[t.kod].y !== ''))
      .map((t) => [t.kod, { d: Number(f.dersler[t.kod].d || 0), y: Number(f.dersler[t.kod].y || 0) }]))
    if (!Object.keys(dersler).length) return setHata('En az bir dersin doğru/yanlış sayısını gir.')
    setBekle(true)
    try { await onKaydet({ tarih: f.tarih, oturum: f.oturum, ad: f.ad, dersler }) } catch (er) { setHata(er.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  return (
    <form className="card nt-form" onSubmit={kaydet}>
      <div className="ct">➕ Yeni deneme</div>
      <div className="nt-form-ust">
        <label>Tarih<input type="date" value={f.tarih} max={bugunISO()} onChange={(e) => setF({ ...f, tarih: e.target.value })} required /></label>
        <label>Oturum
          <div className="nt-secim">
            {oturumlar.map((o) => <button type="button" key={o} className={f.oturum === o ? 'secili' : ''} onClick={() => setF({ ...f, oturum: o, dersler: {} })}>{o}</button>)}
          </div>
        </label>
        <label style={{ flex: 1 }}>Deneme adı <span>(isteğe bağlı)</span><input maxLength={80} value={f.ad} placeholder="ör. 345 TYT Deneme 3" onChange={(e) => setF({ ...f, ad: e.target.value })} /></label>
      </div>
      <table className="nt-form-tablo">
        <thead><tr><th>Ders</th><th>Soru</th><th>Doğru</th><th>Yanlış</th><th>Boş</th><th>Net</th></tr></thead>
        <tbody>
          {testler.map((t) => {
            const d = Number(f.dersler[t.kod]?.d || 0), y = Number(f.dersler[t.kod]?.y || 0)
            return (
              <tr key={t.kod} className={asim(t) ? 'hatali' : ''}>
                <td>{t.ad}</td><td className="yp-ince">{t.soru}</td>
                <td><input type="number" min="0" max={t.soru} inputMode="numeric" value={deger(t.kod, 'd')} onChange={(e) => yaz(t.kod, 'd', e.target.value)} aria-label={`${t.ad} doğru`} /></td>
                <td><input type="number" min="0" max={t.soru} inputMode="numeric" value={deger(t.kod, 'y')} onChange={(e) => yaz(t.kod, 'y', e.target.value)} aria-label={`${t.ad} yanlış`} /></td>
                <td className="yp-ince">{asim(t) ? '!' : Math.max(0, t.soru - d - y)}</td>
                <td><b>{n2(net(t.kod))}</b></td>
              </tr>
            )
          })}
        </tbody>
        <tfoot><tr><td colSpan={5}>Toplam net</td><td><b>{n2(toplam)}</b></td></tr></tfoot>
      </table>
      {testler.some(asim) && <div className="auth-error">Doğru + yanlış, sorudan fazla olamaz.</div>}
      {hata && <div className="auth-error">{hata}</div>}
      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn" disabled={bekle || testler.some(asim)}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
        <button type="button" className="btn sec" onClick={onVazgec}>Vazgeç</button>
      </div>
      <div className="yp-ince">Net = doğru − yanlış ÷ 4. Boş bıraktığın dersler kaydedilmez.</div>
    </form>
  )
}

// ---------------------------------------------------------------- 1) Denemelerim
function DenemelerSekmesi({ yapi, denemeler, kiyas, yenile }) {
  const [formAcik, setFormAcik] = useState(false)
  const [silinecek, setSilinecek] = useState(null)
  const hedefler = useMemo(() => {
    const h = { TYT: null, AYT: null, YDT: null }
    for (const s of kiyas?.satirlar || []) if (s.hedef != null) h[s.oturum] = (h[s.oturum] || 0) + s.hedef
    return h
  }, [kiyas])
  const sonOturum = (o) => denemeler.filter((d) => d.oturum === o)
  const ozetKutu = (o) => {
    const l = sonOturum(o); if (!l.length) return null
    const son = l[l.length - 1], onceki = l[l.length - 2]
    const fark = onceki ? son.toplam_net - onceki.toplam_net : null
    return (
      <div key={o} className="nt-kutu" style={{ borderTopColor: OTURUM_RENK[o] }}>
        <span>Son {o} neti</span>
        <b>{n2(son.toplam_net)}</b>
        {fark != null && <small className={fark >= 0 ? 'arti' : 'eksi'}>{fark >= 0 ? '▲' : '▼'} {n2(Math.abs(fark))} önceki denemeye göre</small>}
      </div>
    )
  }
  // ders ders: son ve bir önceki deneme
  const dersSatirlari = yapi.testler.map((t) => {
    const l = denemeler.filter((d) => d.dersler[t.kod]).map((d) => d.dersler[t.kod].net)
    return { ...t, son: l[l.length - 1], onceki: l[l.length - 2], ort: l.length ? l.slice(-3).reduce((a, b) => a + b, 0) / Math.min(3, l.length) : null }
  }).filter((x) => x.son != null)

  async function sil() { await api.netDenemeSil(silinecek.id); setSilinecek(null); yenile() }

  return (
    <>
      <div className="nt-ust">
        <div className="nt-kutular">
          {['TYT', 'AYT', 'YDT'].map(ozetKutu)}
          <div className="nt-kutu"><span>Toplam deneme</span><b>{denemeler.length}</b></div>
        </div>
        {!formAcik && <button className="btn" onClick={() => setFormAcik(true)}>➕ Deneme ekle</button>}
      </div>
      {formAcik && <DenemeFormu yapi={yapi} onVazgec={() => setFormAcik(false)} onKaydet={async (v) => { await api.netDenemeEkle(v); setFormAcik(false); yenile() }} />}

      {denemeler.length === 0 ? (
        !formAcik && <div className="card bos-durum">Henüz deneme eklemedin. Çözdüğün ilk denemenin doğru / yanlış sayılarını gir; netlerin burada grafiğe dönüşür.</div>
      ) : (
        <>
          <div className="card"><div className="ct">📈 Netlerin zamanla</div><NetGrafigi denemeler={denemeler} hedefler={hedefler} /></div>
          <div className="card">
            <div className="ct">Ders ders</div>
            <table className="yp-tablo nt-ders-tablo">
              <thead><tr><th>Ders</th><th>Son</th><th>Değişim</th><th>Son 3 ortalama</th><th style={{ width: '32%' }}>Doluluk</th></tr></thead>
              <tbody>
                {dersSatirlari.map((x) => (
                  <tr key={x.kod}>
                    <td><span className="nt-oturum" style={{ color: OTURUM_RENK[x.oturum] }}>{x.oturum}</span> {x.ad}</td>
                    <td><b>{n2(x.son)}</b> <span className="yp-ince">/ {x.soru}</span></td>
                    <td>{x.onceki != null ? <span className={x.son - x.onceki >= 0 ? 'arti' : 'eksi'}>{x.son - x.onceki >= 0 ? '▲' : '▼'} {n2(Math.abs(x.son - x.onceki))}</span> : '—'}</td>
                    <td>{n2(x.ort)}</td>
                    <td><div className="nt-cubuk"><div style={{ width: `${Math.max(0, (100 * x.son) / x.soru)}%`, background: OTURUM_RENK[x.oturum] }} /></div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card">
            <div className="ct">Tüm denemeler</div>
            <table className="yp-tablo">
              <thead><tr><th>Tarih</th><th>Deneme</th><th>Dersler</th><th>Toplam</th><th /></tr></thead>
              <tbody>
                {[...denemeler].reverse().map((d) => (
                  <tr key={d.id}>
                    <td>{kisaTarih(d.tarih)}</td>
                    <td><span className="nt-oturum" style={{ color: OTURUM_RENK[d.oturum] }}>{d.oturum}</span> {d.ad || ''}</td>
                    <td className="yp-ince">{Object.entries(d.dersler).map(([k, v]) => `${(yapi.tum_testler.find((t) => t.kod === k) || {}).ad || k} ${n2(v.net)}`).join(' · ')}</td>
                    <td><b>{n2(d.toplam_net)}</b></td>
                    <td><button className="hg-link" onClick={() => setSilinecek(d)}>Sil</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {silinecek && (
              <div className="nt-sil-onay">
                “{silinecek.ad || `${silinecek.oturum} denemesi`}” ({kisaTarih(silinecek.tarih)}) silinsin mi?
                <button className="btn" onClick={sil}>Evet, sil</button><button className="btn sec" onClick={() => setSilinecek(null)}>Vazgeç</button>
              </div>
            )}
          </div>
        </>
      )}
    </>
  )
}

// ---------------------------------------------------------------- 2) Konu takibi
function KonularSekmesi({ yapi, durumlar, setDurumlar, baslangicDers }) {
  const [ders, setDers] = useState(baslangicDers || yapi.konu_dersleri[0]?.kod)
  useEffect(() => { if (baslangicDers) setDers(baslangicDers) }, [baslangicDers])
  const aktif = yapi.konu_dersleri.find((d) => d.kod === ders) || yapi.konu_dersleri[0]
  const sayac = (d) => { const m = durumlar[d.kod] || {}; return { bitti: d.konular.filter((k) => ['bitti', 'tekrar'].includes(m[k])).length, toplam: d.konular.length } }
  async function degistir(konu, durum) {
    const onceki = durumlar
    setDurumlar({ ...durumlar, [aktif.kod]: { ...(durumlar[aktif.kod] || {}), [konu]: durum } })
    try { await api.netKonuGuncelle(aktif.kod, konu, durum) } catch { setDurumlar(onceki) }
  }
  const tumu = yapi.konu_dersleri.reduce((a, d) => { const s = sayac(d); return { b: a.b + s.bitti, t: a.t + s.toplam } }, { b: 0, t: 0 })
  return (
    <div className="kt-duzen">
      <div className="kt-dersler">
        <div className="kt-genel">Genel: <b>{tumu.b}</b> / {tumu.t} konu bitti</div>
        {['TYT', 'AYT'].map((o) => yapi.konu_dersleri.some((d) => d.oturum === o) && (
          <div key={o}>
            <div className="ns" style={{ padding: '8px 4px 4px' }}>{o}</div>
            {yapi.konu_dersleri.filter((d) => d.oturum === o).map((d) => {
              const s = sayac(d)
              return (
                <button key={d.kod} className={`kt-ders${d.kod === aktif.kod ? ' secili' : ''}`} onClick={() => setDers(d.kod)}>
                  <span>{d.ad}</span><small>{s.bitti}/{s.toplam}</small>
                  <div className="nt-cubuk"><div style={{ width: `${(100 * s.bitti) / s.toplam}%`, background: OTURUM_RENK[o] }} /></div>
                </button>
              )
            })}
          </div>
        ))}
      </div>
      <div className="card" style={{ margin: 0 }}>
        <div className="ct">{aktif.oturum} · {aktif.ad}</div>
        <div className="yp-ince" style={{ marginBottom: 10 }}>Her konunun durumunu seç. “Bitti” ve “Tekrar” tamamlanmış sayılır.</div>
        <div className="kt-liste">
          {aktif.konular.map((k) => {
            const dur = (durumlar[aktif.kod] || {})[k] || 'baslamadi'
            return (
              <div key={k} className={`kt-konu d-${dur}`}>
                <span className="kt-konu-ad">{k}</span>
                <div className="kt-durumlar" role="radiogroup" aria-label={k}>
                  {KONU_DURUM.map((x) => (
                    <button key={x.k} role="radio" aria-checked={dur === x.k} className={dur === x.k ? 'secili' : ''} onClick={() => degistir(k, x.k)} title={x.ad}>
                      <span aria-hidden="true">{x.ikon}</span> {x.ad}
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- 3) Hedefe göre
function HedefSekmesi({ yapi, kiyas, durumlar, yenile, konuyaGit }) {
  const [liste, setListe] = useState(null)
  const [ara, setAra] = useState('')
  const [secimAcik, setSecimAcik] = useState(false)
  const [bekle, setBekle] = useState(false)
  useEffect(() => { api.netHedefProgramlar().then(setListe).catch(() => setListe({ durum: 'hata', programlar: [], mesaj: 'Liste yüklenemedi.' })) }, [])
  const hedef = kiyas?.hedef
  async function sec(p) { setBekle(true); try { await api.netHedefKaydet(p.kilavuz_kodu); setSecimAcik(false); yenile() } finally { setBekle(false) } }
  const filtre = (liste?.programlar || []).filter((p) => !ara || `${p.universite} ${p.program}`.toLocaleLowerCase('tr').includes(ara.toLocaleLowerCase('tr')))

  if (!yapi.hedef_bolum) return <div className="card bos-durum">Önce bir hedef bölüm seç (Ayarlar → Hedef bölüm). Sonra o bölümün üniversitelerinden birini seçip netlerini karşılaştırabilirsin.</div>

  const secimKutusu = (
    <div className="card">
      <div className="ct">🏛️ {liste?.bolum || yapi.hedef_bolum.ad} · hedef üniversiteni seç</div>
      {!liste ? <div className="bos-durum">YÖK Atlas'tan yükleniyor…</div> : liste.durum !== 'tamam' ? <div className="bos-durum">{liste.mesaj}</div> : (
        <>
          <input className="auth-input" placeholder="Üniversite ya da şehir ara…" value={ara} onChange={(e) => setAra(e.target.value)} style={{ marginBottom: 8 }} />
          <div className="nh-liste">
            {filtre.slice(0, 60).map((p) => (
              <button key={p.kilavuz_kodu} className={`nh-satir${liste.secili === p.kilavuz_kodu ? ' secili' : ''}`} disabled={bekle} onClick={() => sec(p)}>
                <span><b>{p.universite}</b><small>{p.program} · {p.universite_turu === 'VAKIF' ? 'Vakıf' : 'Devlet'}</small></span>
                <span className="nh-puan">{p.son?.taban_puan ? n2(Math.round(p.son.taban_puan * 100) / 100) : '—'}<small>{p.son?.yil} taban</small></span>
              </button>
            ))}
          </div>
          <div className="yp-ince" style={{ marginTop: 6 }}>{filtre.length} program · kaynak: YÖK Atlas Net Sihirbazı ({liste.yil})</div>
        </>
      )}
    </div>
  )

  if (!hedef || secimAcik) return secimKutusu

  const satirlar = kiyas.satirlar
  const acik = (kiyas.toplam_hedef ?? 0) - (kiyas.toplam_ben ?? 0)
  const enBuyuk = kiyas.en_buyuk_acik?.[0]
  const enBuyukTest = satirlar.find((s) => s.ad === enBuyuk?.ad)
  const bitmemis = enBuyukTest ? (TEST_KONU[enBuyukTest.kod] || []).flatMap((dk) => {
    const d = yapi.konu_dersleri.find((x) => x.kod === dk); if (!d) return []
    return d.konular.filter((k) => !['bitti', 'tekrar'].includes((durumlar[dk] || {})[k])).map((k) => ({ dk, k }))
  }) : []
  return (
    <>
      <div className="card nh-hedef">
        <div>
          <div className="nh-etiket">🎯 Hedef programın</div>
          <div className="nh-uni">{hedef.universite}</div>
          <div className="yp-ince">{hedef.program} · {hedef.son?.yil} taban puanı <b>{n2(hedef.son?.taban_puan)}</b></div>
        </div>
        <button className="btn sec" onClick={() => setSecimAcik(true)}>Değiştir</button>
      </div>

      {kiyas.toplam_ben == null ? (
        <div className="card bos-durum">Karşılaştırma için Denemelerim'e en az bir deneme ekle.</div>
      ) : (
        <>
          <div className="nh-ozet">
            <div className="nh-ozet-kutu"><span>Senin netin</span><b>{n2(kiyas.toplam_ben)}</b><small>son {Math.min(3, Math.max(...satirlar.map((s) => s.deneme_sayisi)))} deneme ortalaması</small></div>
            <div className="nh-ozet-kutu"><span>{kiyas.yil} son yerleşen</span><b>{n2(kiyas.toplam_hedef)}</b><small>{hedef.universite.split(' (')[0]}</small></div>
            <div className={`nh-ozet-kutu ${acik > 0 ? 'eksi' : 'arti'}`}><span>{acik > 0 ? 'Kapatman gereken' : 'Hedefin üstündesin'}</span><b>{n2(Math.abs(acik))} net</b><small>{acik > 0 && enBuyuk ? `en büyük açık: ${enBuyuk.ad}` : 'harika, korumaya devam'}</small></div>
          </div>
          <div className="card">
            <div className="ct">Ders ders karşılaştırma</div>
            <div className="nh-lejant"><span><i className="nh-l-ben" />Sen</span><span><i className="nh-l-hedef" />{kiyas.yil} son yerleşen</span><span><i className="nh-l-onceki" />{kiyas.onceki_yil || 'önceki yıl'}</span><span><i className="nh-l-ort" />yıllar ortalaması</span></div>
            {satirlar.map((s) => (
              <div key={s.kod} className="nh-satir-kiyas">
                <div className="nh-ders"><span className="nt-oturum" style={{ color: OTURUM_RENK[s.oturum] }}>{s.oturum}</span> {s.ad}</div>
                <div className="nh-iz" title={`Sen ${n2(s.ben)} · ${kiyas.yil}: ${n2(s.hedef)} · ${kiyas.onceki_yil || ''}: ${n2(s.hedef_onceki_yil)} · ortalama ${n2(s.hedef_ortalama)} (soru: ${s.soru})`}>
                  {s.ben != null && <div className="nh-ben" style={{ width: `${Math.max(0, (100 * s.ben) / s.soru)}%`, background: OTURUM_RENK[s.oturum] }} />}
                  {s.hedef_ortalama != null && <span className="nh-isaret ort" style={{ left: `${Math.max(0, (100 * s.hedef_ortalama) / s.soru)}%` }} />}
                  {s.hedef_onceki_yil != null && <span className="nh-isaret onceki" style={{ left: `${Math.max(0, (100 * s.hedef_onceki_yil) / s.soru)}%` }} />}
                  {s.hedef != null && <span className="nh-isaret hedef" style={{ left: `${Math.max(0, (100 * s.hedef) / s.soru)}%` }} />}
                </div>
                <div className="nh-sayilar">
                  <b>{n2(s.ben)}</b><span>/ {n2(s.hedef)}</span>
                  {s.fark != null && <em className={s.fark >= 0 ? 'arti' : 'eksi'}>{s.fark >= 0 ? '+' : ''}{n2(s.fark)}</em>}
                </div>
              </div>
            ))}
          </div>
          {enBuyukTest && enBuyukTest.fark < 0 && bitmemis.length > 0 && (
            <div className="card nh-oneri">
              <b>💡 {enBuyukTest.ad} açığını kapatmak için:</b> bu derste henüz bitirmediğin {bitmemis.length} konu var.
              {' '}Örneğin: {bitmemis.slice(0, 4).map((x) => x.k).join(', ')}{bitmemis.length > 4 ? '…' : ''}
              <button className="hg-link" onClick={() => konuyaGit(bitmemis[0].dk)}>Konu takibinde aç →</button>
            </div>
          )}
          <div className="card">
            <div className="ct">Yıllara göre bu programa son yerleşen</div>
            <table className="yp-tablo">
              <thead><tr><th>Yıl</th><th>Taban puan</th><th>TYT netleri</th><th>AYT / YDT netleri</th><th>OBP</th></tr></thead>
              <tbody>
                {[hedef.son, ...(hedef.gecmis || [])].filter(Boolean).map((y) => {
                  const t = (pre) => Object.entries(y.netler || {}).filter(([k]) => k.startsWith(pre)).reduce((a, [, v]) => a + v, 0)
                  return <tr key={y.yil}><td><b>{y.yil}</b></td><td>{n2(y.taban_puan)}</td><td>{n2(t('tyt'))}</td><td>{n2(t('ayt') + t('ydt'))}</td><td>{n2(y.obp)}</td></tr>
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
      <div className="nh-not">ℹ️ {kiyas.aciklama} Kaynak: YÖK Atlas Net Sihirbazı.</div>
    </>
  )
}

// ---------------------------------------------------------------- sayfa
export default function NetTakibiSayfasi() {
  const [params, setParams] = useSearchParams()
  const sekme = SEKMELER.some(([k]) => k === params.get('sekme')) ? params.get('sekme') : 'denemeler'
  const [yapi, setYapi] = useState(null)
  const [denemeler, setDenemeler] = useState([])
  const [kiyas, setKiyas] = useState(null)
  const [durumlar, setDurumlar] = useState({})
  const [konuDers, setKonuDers] = useState(null)
  const [hata, setHata] = useState(null)
  const yenile = useCallback(() => {
    api.netDenemeler().then((r) => setDenemeler(r.denemeler)).catch(() => {})
    api.netKiyas().then(setKiyas).catch(() => {})
  }, [])
  useEffect(() => {
    api.netYapi().then(setYapi).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
    api.netKonular().then((r) => setDurumlar(r.durumlar)).catch(() => {})
    yenile()
  }, [yenile])
  const git = (k) => setParams(k === 'denemeler' ? {} : { sekme: k }, { replace: true })

  if (hata) return <div className="pg"><div className="auth-error">{hata}</div></div>
  if (!yapi) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Net Takibi</div>
        <div className="ps">Denemelerini kaydet, konularını takip et ve netlerini hedef üniversitene geçen yıl yerleşen öğrenciyle karşılaştır. Alanın: <b>{yapi.puan_turu_ad}</b>{yapi.hedef_bolum ? ` · Hedef: ${yapi.hedef_bolum.ad}` : ''}</div>
      </div>
      <div className="koc-sekmeler" role="tablist">
        {SEKMELER.map(([k, ad]) => <button key={k} role="tab" aria-selected={sekme === k} className={sekme === k ? 'aktif' : ''} onClick={() => git(k)}>{ad}</button>)}
      </div>
      {sekme === 'denemeler' && <DenemelerSekmesi yapi={yapi} denemeler={denemeler} kiyas={kiyas} yenile={yenile} />}
      {sekme === 'konular' && <KonularSekmesi yapi={yapi} durumlar={durumlar} setDurumlar={setDurumlar} baslangicDers={konuDers} />}
      {sekme === 'hedef' && <HedefSekmesi yapi={yapi} kiyas={kiyas} durumlar={durumlar} yenile={yenile} konuyaGit={(dk) => { setKonuDers(dk); git('konular') }} />}
    </div>
  )
}
