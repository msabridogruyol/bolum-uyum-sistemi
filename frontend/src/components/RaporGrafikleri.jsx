// [2026-10-11] Raporlarım — "Raporunda neler var?" grafik özeti (indirilen PDF'teki bilgilerin kısa önizlemesi).
//  1) Güç dağılımın (güçlü / orta / gelişime açık sayısı)  2) Gelişime açık alanların (en düşük 5)
//  3) En uyumlu 5 bölüm  4) Net gelişimin (TYT / AYT toplam net; net takibi açık ve en az 2 deneme varsa)
// Tüm değerler öğrencinin kendi sonuçlarından; eşikler yardimci/seviye.js (Puan Rehberi ve PDF ile aynı).
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { YatayCubuklar } from './AnaSayfaGrafikleri'
import { GRUP_ADLARI, GUCLU_ESIK, ORTA_ESIK, gelisimeAcikMi, gucluMu } from '../yardimci/seviye'

const ANA_KATMANLAR = ['K1', 'K2', 'K3', 'K4']
const OTURUM_RENK = { TYT: 'var(--pu)', AYT: 'var(--gr)' }
const kisaTarih = (t) => { const d = new Date(t); return `${d.getDate()}.${d.getMonth() + 1}` }

function GucDagilimi({ guclu, orta, gelisim }) {
  const toplam = guclu + orta + gelisim || 1
  const parca = [
    { ad: `${GRUP_ADLARI.guclu} (${GUCLU_ESIK}+)`, sayi: guclu, renk: 'var(--gr)' },
    { ad: `${GRUP_ADLARI.orta} (${ORTA_ESIK}–${GUCLU_ESIK - 1})`, sayi: orta, renk: 'var(--pu)' },
    { ad: `${GRUP_ADLARI.gelisim} (<${ORTA_ESIK})`, sayi: gelisim, renk: 'var(--am)' },
  ]
  return (
    <>
      <div className="rg-yigin" role="img" aria-label={parca.map((p) => `${p.ad}: ${p.sayi}`).join(', ')}>
        {parca.filter((p) => p.sayi > 0).map((p) => (
          <span key={p.ad} style={{ width: `${(p.sayi / toplam) * 100}%`, background: p.renk }} title={`${p.ad}: ${p.sayi} özellik`} />
        ))}
      </div>
      <div className="rg-lejant">
        {parca.map((p) => (
          <div key={p.ad} className="rg-lejant-satir">
            <span className="rg-nokta" style={{ background: p.renk }} />
            <span className="rg-lejant-ad">{p.ad}</span>
            <b>{p.sayi}</b>
            <span className="rg-yuzde">%{Math.round((p.sayi / toplam) * 100)}</span>
          </div>
        ))}
      </div>
      <div className="gr-not">Toplam {guclu + orta + gelisim} özellik · K1–K4</div>
    </>
  )
}

export function NetCizgisi({ denemeler }) {
  const [aktif, setAktif] = useState(null)
  const seriler = ['TYT', 'AYT'].map((o) => ({ o, n: denemeler.filter((d) => d.oturum === o) })).filter((s) => s.n.length > 0)
  const tumu = [...denemeler].sort((a, b) => a.tarih.localeCompare(b.tarih))
  const tarihler = [...new Set(tumu.map((d) => d.tarih))]
  const enCok = Math.max(10, ...tumu.map((d) => d.toplam_net))
  const ust = Math.ceil(enCok / 20) * 20
  const G = 300, Y = 150, sol = 26, alt = 20, ustB = 12
  const x = (t) => sol + (tarihler.length === 1 ? (G - sol) / 2 : (tarihler.indexOf(t) / (tarihler.length - 1)) * (G - sol - 10))
  const y = (v) => ustB + (1 - v / ust) * (Y - ustB - alt)
  return (
    <>
      <div className="rg-lejant yatay">
        {seriler.map((s) => {
          const ilk = s.n[0].toplam_net, son = s.n[s.n.length - 1].toplam_net, fark = Math.round((son - ilk) * 100) / 100
          return (
            <div key={s.o} className="rg-lejant-satir">
              <span className="rg-nokta" style={{ background: OTURUM_RENK[s.o] }} />
              <span className="rg-lejant-ad">{s.o}</span>
              <b>{son}</b>
              {s.n.length > 1 && <span className="rg-yuzde">{fark >= 0 ? '+' : ''}{fark} net</span>}
            </div>
          )
        })}
      </div>
      <svg className="rg-cizgi" viewBox={`0 0 ${G} ${Y}`} role="img" aria-label="Deneme netlerinin zamana göre değişimi" onMouseLeave={() => setAktif(null)}>
        {[0, ust / 2, ust].map((v) => (
          <g key={v}>
            <line x1={sol} x2={G} y1={y(v)} y2={y(v)} className="rg-eksen-cizgi" />
            <text x={sol - 4} y={y(v) + 3} className="rg-eksen" textAnchor="end">{v}</text>
          </g>
        ))}
        {tarihler.map((t, i) => (i === 0 || i === tarihler.length - 1 || tarihler.length <= 6) && (
          <text key={t} x={x(t)} y={Y - 5} className="rg-eksen" textAnchor="middle">{kisaTarih(t)}</text>
        ))}
        {seriler.map((s) => (
          <g key={s.o}>
            {s.n.length > 1 && <polyline fill="none" stroke={OTURUM_RENK[s.o]} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"
              points={s.n.map((d) => `${x(d.tarih)},${y(d.toplam_net)}`).join(' ')} />}
            {s.n.map((d) => (
              <circle key={d.id} cx={x(d.tarih)} cy={y(d.toplam_net)} r={aktif === d.id ? 5 : 4} fill={OTURUM_RENK[s.o]}
                stroke="var(--bg)" strokeWidth="2" onMouseEnter={() => setAktif(d.id)}>
                <title>{`${d.ad || d.oturum} · ${kisaTarih(d.tarih)} · ${d.toplam_net} net`}</title>
              </circle>
            ))}
          </g>
        ))}
      </svg>
      <div className="gr-not">{aktif ? (() => { const d = denemeler.find((z) => z.id === aktif); return `${d.ad || d.oturum} · ${kisaTarih(d.tarih)} · ${d.toplam_net} net` })() : 'Noktanın üzerine gel: deneme adı ve neti'}</div>
    </>
  )
}

export default function RaporGrafikleri({ netAcik }) {
  const [sonuclar, setSonuclar] = useState(null)
  const [siralama, setSiralama] = useState(null)
  const [denemeler, setDenemeler] = useState([])

  useEffect(() => {
    Promise.all(ANA_KATMANLAR.map((k) => api.katmanSonucuGetir(k).then((r) => (r?.tamamlandi_mi ? r.sonuclar : [])).catch(() => [])))
      .then((l) => setSonuclar(l.flat()))
    api.siralamaGetir(5).then(setSiralama).catch(() => setSiralama([]))
  }, [])
  useEffect(() => { if (netAcik) api.netDenemeler().then((r) => setDenemeler(r.denemeler || [])).catch(() => {}) }, [netAcik])

  const dagilim = useMemo(() => {
    if (!sonuclar) return null
    const guclu = sonuclar.filter((s) => gucluMu(s.puan)).length
    const gelisim = sonuclar.filter((s) => gelisimeAcikMi(s.puan)).length
    return { guclu, gelisim, orta: sonuclar.length - guclu - gelisim }
  }, [sonuclar])
  if (!sonuclar || !siralama) return null
  if (!sonuclar.length) return null

  const gelisimAlanlari = [...sonuclar].sort((a, b) => a.puan - b.puan).slice(0, 5).map((s) => ({ ad: s.degisken_adi, deger: Math.round(s.puan) }))
  const uyum = siralama.slice(0, 5).map((s) => ({ ad: s.bolum_adi, deger: Math.round(s.toplam_uyum) }))
  const netVar = netAcik && denemeler.length >= 2

  return (
    <div className="card gr-rapor" style={{ marginTop: 18 }}>
      <div className="gr-rapor-bas">
        <div className="ct" style={{ margin: 0 }}>📊 Raporunda neler var?</div>
        <span className="yp-ince">İndireceğin raporun kısa özeti</span>
      </div>
      <div className={`rg-izgara${netVar ? " dort" : ""}`}>
        <div className="gr-panel">
          <div className="gr-baslik">Güç dağılımın</div>
          <div className="gr-alt">Özelliklerinin kaçı güçlü, kaçı gelişime açık</div>
          <GucDagilimi {...dagilim} />
        </div>
        <div className="gr-panel">
          <div className="gr-baslik">Gelişime açık alanların</div>
          <div className="gr-alt">En düşük puanlı 5 özelliğin (0–100)</div>
          <YatayCubuklar satirlar={gelisimAlanlari} renk="var(--am)" />
        </div>
        <div className="gr-panel">
          <div className="gr-baslik">Sana en uygun 5 bölüm</div>
          <div className="gr-alt">Bölüm uyum yüzden</div>
          {uyum.length ? <YatayCubuklar satirlar={uyum} renk="var(--pu)" /> : <div className="gr-bos">Bölüm uyumların hazır olunca burada görünecek</div>}
        </div>
        {netVar && (
          <div className="gr-panel">
            <div className="gr-baslik">Net gelişimin</div>
            <div className="gr-alt">Denemelerdeki toplam netin (son değer ve ilk denemeden bu yana fark)</div>
            <NetCizgisi denemeler={denemeler} />
          </div>
        )}
      </div>
    </div>
  )
}
