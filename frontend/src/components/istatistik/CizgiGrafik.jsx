// [2026-10-10] Çizgi grafik — zaman serisi. TEK y ekseni (çift eksen yasak: farklı ölçekli iki ölçü
// → iki ayrı grafik ya da ortak tabana endeksleme). Dikey çizgi (crosshair) en yakın x'e oturur,
// ipucu o x'teki TÜM serileri listeler. 2+ seride lejant; ≤4 seride, çakışmıyorsa uçta seri adı.
import { useMemo } from 'react'
import { bicim, kisaBicim, eksenAdimlari, metinGenisligi, kisalt, useGenislik, useEtkilesim, ariaEtiketi } from './yardimci'
import { Ipucu, Lejant, Bos, Cerceve } from './ortak'
import { kategorikRenk } from './palet'

const UST = 14, ALT = 28

/**
 * CizgiGrafik({ x:[etiketler], seriler:[{ad, degerler:[sayı|null], renk?}], birim, yMin, yMaks, yukseklik, alan, kesir })
 * null değer çizgide boşluk bırakır. alan: tek seride %10 dolgu (vars. true).
 */
export default function CizgiGrafik({ x, seriler, birim, yMin, yMaks, yukseklik = 220, alan = true, kesir = 1, baslik, ariaEtiket }) {
  const etiketler = x || []
  const sr = useMemo(() => (seriler || []).map((s, i) => ({ ...s, renk: s.renk || kategorikRenk(i), degerler: (s.degerler || []).map((v) => (v == null || Number.isNaN(Number(v)) ? null : Number(v))) })), [seriler])
  const n = etiketler.length
  const tum = sr.flatMap((s) => s.degerler.slice(0, n)).filter((v) => v != null)
  const [ref, W] = useGenislik()

  const H = yukseklik
  const veriVar = n > 0 && tum.length > 0
  const enAz = veriVar ? Math.min(...tum) : 0, enCok = veriVar ? Math.max(...tum) : 1
  const adimlar = eksenAdimlari(yMin ?? (enAz >= 0 ? 0 : enAz), yMaks ?? enCok, 4)
  const alt = yMin ?? adimlar[0], ust = yMaks ?? adimlar[adimlar.length - 1]
  const solEksen = Math.ceil(Math.max(...adimlar.map((a) => metinGenisligi(kisaBicim(a, birim), 11, 600)))) + 10

  // Uç etiketleri: tek seride son değer; 2–4 seride seri adı (çakışma yoksa)
  const sonIndeks = (s) => { for (let i = n - 1; i >= 0; i--) if (s.degerler[i] != null) return i; return -1 }
  const ucMetin = sr.map((s) => (sr.length === 1 ? bicim(s.degerler[sonIndeks(s)], birim, kesir) : s.ad))
  const ucGenislik = Math.min(120, Math.max(0, ...ucMetin.map((m) => metinGenisligi(m, 11, 700))))
  let ucEtiket = sr.length <= 4 && W >= 360
  const sagAday = ucEtiket ? ucGenislik + 14 : 10
  const yOl = (v) => UST + H - ((v - alt) / (ust - alt || 1)) * H
  if (ucEtiket && sr.length > 1) {
    const ys = sr.map((s) => { const i = sonIndeks(s); return i < 0 ? null : yOl(s.degerler[i]) }).filter((v) => v != null).sort((a, b) => a - b)
    for (let i = 1; i < ys.length; i++) if (ys[i] - ys[i - 1] < 14) ucEtiket = false
  }
  const sag = ucEtiket ? sagAday : 10
  const pw2 = Math.max(40, W - solEksen - sag)
  const xOl2 = (i) => solEksen + (n <= 1 ? pw2 / 2 : (i / (n - 1)) * pw2)

  const konum = (i) => {
    const ys = sr.map((s) => s.degerler[i]).filter((v) => v != null).map(yOl)
    return { x: xOl2(i), y: ys.length ? Math.min(...ys) : UST + H / 2 }
  }
  const e = useEtkilesim(n, { konum })

  if (!veriVar) return <Cerceve baslik={baslik}><Bos /></Cerceve>

  const yol = (s) => {
    let d = '', kalem = false
    s.degerler.slice(0, n).forEach((v, i) => {
      if (v == null) { kalem = false; return }
      d += `${kalem ? 'L' : 'M'}${xOl2(i).toFixed(1)},${yOl(v).toFixed(1)}`
      kalem = true
    })
    return d
  }
  const alanYolu = (s) => {
    // yalnızca kesintisiz tek parça için
    const idx = s.degerler.slice(0, n).map((v, i) => (v == null ? null : i)).filter((i) => i != null)
    if (idx.length < 2 || idx.length !== idx[idx.length - 1] - idx[0] + 1) return ''
    const taban = yOl(alt <= 0 && ust >= 0 ? 0 : alt)
    return `${yol(s)}L${xOl2(idx[idx.length - 1])},${taban}L${xOl2(idx[0])},${taban}Z`
  }

  const etiketAdim = pw2 / Math.max(1, n - 1)
  const enUzun = Math.max(...etiketler.map((t) => metinGenisligi(t, 11, 600)))
  const k = Math.max(1, Math.ceil((Math.min(enUzun, 80) + 10) / (etiketAdim || 1)))

  const izle = (ev) => {
    const p = e.olayKonumu(ev)
    const i = n <= 1 ? 0 : Math.max(0, Math.min(n - 1, Math.round(((p.x - solEksen) / pw2) * (n - 1))))
    e.goster(i, xOl2(i), p.y)
  }

  const ilk = sr[0]
  const ozet = sr.length === 1
    ? `${etiketler[0]} – ${etiketler[n - 1]}: ${bicim(ilk.degerler.find((v) => v != null), birim, kesir)} → ${bicim(ilk.degerler[sonIndeks(ilk)], birim, kesir)}`
    : `${n} dönem, ${sr.length} seri (${sr.map((s) => s.ad).join(', ')})`

  return (
    <Cerceve baslik={baslik}>
      {sr.length > 1 && <Lejant ogeler={sr.map((s) => ({ ad: s.ad, renk: s.renk }))} tur="cizgi" />}
      <div className="ist-cizim" ref={(el) => { ref.current = el; e.kapRef.current = el }}
        tabIndex={e.kapProps.tabIndex} onKeyDown={e.kapProps.onKeyDown} onPointerLeave={e.kapProps.onPointerLeave} onBlur={e.kapProps.onBlur}>
        <svg width="100%" height={UST + H + ALT} viewBox={`0 0 ${W} ${UST + H + ALT}`} role="img" aria-label={ariaEtiketi(ariaEtiket, baslik, ozet)} className="ist-svg">
          {adimlar.map((a) => (
            <g key={a}>
              <line x1={solEksen} x2={W - sag + 4} y1={yOl(a)} y2={yOl(a)} className={a === adimlar[0] ? 'ist-eksen' : 'ist-izgara'} />
              <text x={solEksen - 6} y={yOl(a)} dy="0.35em" textAnchor="end" className="ist-eksen-yazi">{kisaBicim(a, birim)}</text>
            </g>
          ))}
          {etiketler.map((t, i) => {
            const sonSol = xOl2(n - 1) - Math.min(metinGenisligi(etiketler[n - 1], 11, 600), etiketAdim * k)
            const genis = Math.min(metinGenisligi(t, 11, 600), Math.max(etiketAdim * k - 8, 40))
            const sagUc = i === 0 ? xOl2(i) + genis : xOl2(i) + genis / 2
            const goster = i === n - 1 || (i % k === 0 && sagUc + 8 <= sonSol)
            return goster && (
            <text key={i} x={xOl2(i)} y={UST + H + 18} textAnchor={n > 1 && i === 0 ? 'start' : n > 1 && i === n - 1 ? 'end' : 'middle'} className="ist-eksen-yazi">
              {kisalt(t, Math.max(etiketAdim * k - 8, 40), 11)}
            </text>
          )})}
          {sr.length === 1 && alan && <path d={alanYolu(ilk)} style={{ fill: ilk.renk, opacity: 0.1 }} />}
          {e.aktif != null && <line x1={xOl2(e.aktif)} x2={xOl2(e.aktif)} y1={UST} y2={UST + H} className="ist-crosshair" />}
          {sr.map((s) => <path key={s.ad} d={yol(s)} className="ist-cizgi" style={{ stroke: s.renk }} />)}
          {sr.map((s, j) => {
            const i = sonIndeks(s)
            if (i < 0) return null
            const yy = yOl(s.degerler[i])
            return (
              <g key={`u${j}`}>
                <circle cx={xOl2(i)} cy={yy} r="4" className="ist-nokta" style={{ fill: s.renk }} />
                {ucEtiket && <text x={xOl2(i) + 9} y={yy} dy="0.35em" className="ist-deger-yazi" textAnchor="start">{kisalt(ucMetin[j], 120, 11, 700)}</text>}
              </g>
            )
          })}
          {e.aktif != null && sr.map((s, j) => s.degerler[e.aktif] != null && (
            <circle key={`a${j}`} cx={xOl2(e.aktif)} cy={yOl(s.degerler[e.aktif])} r="4.5" className="ist-nokta" style={{ fill: s.renk }} />
          ))}
          <rect x={solEksen - 8} y={0} width={pw2 + 16} height={UST + H + ALT} className="ist-isabet"
            onPointerMove={izle} onPointerDown={izle} />
        </svg>
        <Ipucu durum={e.durum} baslik={e.aktif != null ? etiketler[e.aktif] : null}
          satirlar={e.aktif != null ? sr.map((s) => ({ renk: s.renk, deger: bicim(s.degerler[e.aktif], birim, kesir), ad: sr.length > 1 ? s.ad : null })) : []} />
      </div>
    </Cerceve>
  )
}
