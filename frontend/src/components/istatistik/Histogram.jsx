// [2026-10-10] Histogram — puan dağılımı (ör. bir okulda bir özelliğin 0–100 puanları).
// Kovalar bitişiktir, aralarında 2px yüzey boşluğu. İsteğe bağlı arka plan bantları (ör. seviye bantları)
// ve ortalama çizgisi. Tek seri: tek renk, lejant yok.
import { useMemo } from 'react'
import { sayi, kisaSayi, eksenAdimlari, metinGenisligi, useGenislik, useEtkilesim, sutunYolu, ariaEtiketi } from './yardimci'
import { Ipucu, Bos, Cerceve } from './ortak'
import { KATEGORIK } from './palet'

const UST = 20, ALT = 28, BOSLUK = 2

/** Bantları [{alt, ust, ad, zemin}] biçimine getirir. seviye.js BANTLAR'ı (yalnız `alt`, büyükten küçüğe) doğrudan kabul eder. */
function bantlariHazirla(bantlar, [a, b]) {
  if (!bantlar?.length) return []
  const l = [...bantlar].sort((x, y) => x.alt - y.alt)
  return l.map((bt, i) => ({
    ...bt,
    alt: Math.max(a, bt.alt),
    ust: Math.min(b, bt.ust ?? (l[i + 1] ? l[i + 1].alt : b)),
  })).filter((bt) => bt.ust > bt.alt)
}

/**
 * Histogram({ degerler:number[], aralik:[0,100], kova:10, bantlar?, birim='öğrenci', ortalama=true, renk, yukseklik })
 * kova: KOVA SAYISI (aralık eşit parçalara bölünür; son kova üst sınırı da içerir).
 */
export default function Histogram({
  degerler, aralik = [0, 100], kova = 10, bantlar, birim = 'öğrenci', ortalama = true,
  renk = KATEGORIK[0], yukseklik = 200, baslik, ariaEtiket,
}) {
  const [a, b] = aralik
  const hesap = useMemo(() => {
    const v = (degerler || []).map(Number).filter((x) => !Number.isNaN(x))
    const ic = v.filter((x) => x >= a && x <= b)
    const w = (b - a) / kova
    const sayim = Array(kova).fill(0)
    ic.forEach((x) => { sayim[Math.min(kova - 1, Math.floor((x - a) / w))] += 1 })
    const ort = ic.length ? ic.reduce((s, x) => s + x, 0) / ic.length : null
    return { sayim, w, toplam: ic.length, disarida: v.length - ic.length, ort }
  }, [degerler, a, b, kova])
  const [ref, W] = useGenislik()
  const e = useEtkilesim(kova)

  if (!hesap.toplam) return <Cerceve baslik={baslik}><Bos /></Cerceve>

  const { sayim, w, toplam, disarida, ort } = hesap
  const H = yukseklik
  const adimlar = eksenAdimlari(0, Math.max(1, ...sayim), 4).filter((x) => Number.isInteger(x))
  const tepe = adimlar[adimlar.length - 1]
  const solEksen = Math.ceil(Math.max(...adimlar.map((x) => metinGenisligi(kisaSayi(x), 11, 600)))) + 10
  const pw = Math.max(40, W - solEksen - 6)
  const xOl = (v) => solEksen + ((v - a) / (b - a)) * pw
  const yOl = (v) => UST + H - (v / tepe) * H
  const kw = pw / kova
  const bt = bantlariHazirla(bantlar, aralik)
  const kenarAdim = Math.max(1, Math.ceil(28 / kw))
  const kovaAdi = (i) => {
    const alt = a + i * w, ust = a + (i + 1) * w
    const tam = Number.isInteger(w) && Number.isInteger(a)
    return tam ? `${sayi(alt)}–${sayi(i === kova - 1 ? ust : ust - 1)}` : `${sayi(alt, 1)}–${sayi(ust, 1)}`
  }
  const enCok = sayim.indexOf(Math.max(...sayim))
  const ozet = `${sayi(toplam)} ${birim}; en kalabalık aralık ${kovaAdi(enCok)} (${sayi(sayim[enCok])})${ort != null ? `, ortalama ${sayi(ort, 1)}` : ''}`

  return (
    <Cerceve baslik={baslik}>
      <div className="ist-cizim" ref={(el) => { ref.current = el; e.kapRef.current = el }}
        tabIndex={e.kapProps.tabIndex} onKeyDown={e.kapProps.onKeyDown} onPointerLeave={e.kapProps.onPointerLeave} onBlur={e.kapProps.onBlur}>
        <svg width="100%" height={UST + H + ALT} viewBox={`0 0 ${W} ${UST + H + ALT}`} role="img" aria-label={ariaEtiketi(ariaEtiket, baslik, ozet)} className="ist-svg">
          {bt.map((x, i) => {
            const x0 = xOl(x.alt), x1 = xOl(x.ust)
            return (
              <g key={`b${i}`}>
                <rect x={x0} y={UST} width={x1 - x0} height={H} style={{ fill: x.zemin || 'var(--sur2)' }} className="ist-bant" />
                {metinGenisligi(x.ad, 10, 700) <= x1 - x0 - 6 && <text x={x0 + 4} y={UST - 6} className="ist-bant-yazi">{x.ad}</text>}
              </g>
            )
          })}
          {adimlar.map((x) => (
            <g key={x}>
              <line x1={solEksen} x2={solEksen + pw} y1={yOl(x)} y2={yOl(x)} className={x === 0 ? 'ist-eksen' : 'ist-izgara'} />
              <text x={solEksen - 6} y={yOl(x)} dy="0.35em" textAnchor="end" className="ist-eksen-yazi">{kisaSayi(x)}</text>
            </g>
          ))}
          {sayim.map((c, i) => {
            const x = solEksen + kw * i + BOSLUK / 2
            const y = yOl(c)
            return (
              <g key={i}>
                {e.aktif === i && <rect x={solEksen + kw * i} y={UST} width={kw} height={H} className="ist-vurgu-bant" />}
                {c > 0 && <path d={sutunYolu(x, y, Math.max(1, kw - BOSLUK), UST + H - y)} style={{ fill: renk }} />}
              </g>
            )
          })}
          {Array.from({ length: kova + 1 }, (_, i) => i)
            .filter((i) => i === kova || (i % kenarAdim === 0 && kova - i >= kenarAdim * 0.75))
            .map((i) => (
              <text key={`x${i}`} x={solEksen + kw * i} y={UST + H + 18} textAnchor={i === 0 ? 'start' : i === kova ? 'end' : 'middle'} className="ist-eksen-yazi">
                {sayi(a + i * w, 1)}
              </text>
            ))}
          {ortalama && ort != null && (
            <g>
              <line x1={xOl(ort)} x2={xOl(ort)} y1={UST} y2={UST + H} className="ist-referans" />
              <text x={xOl(ort) + (xOl(ort) > solEksen + pw - 70 ? -5 : 5)} y={UST + 12} textAnchor={xOl(ort) > solEksen + pw - 70 ? 'end' : 'start'} className="ist-deger-yazi">
                Ort. {sayi(ort, 1)}
              </text>
            </g>
          )}
          {sayim.map((_, i) => (
            <rect key={`h${i}`} {...e.isaret(i)} x={solEksen + kw * i} y={UST} width={kw} height={H + ALT} className="ist-isabet" />
          ))}
        </svg>
        <Ipucu durum={e.durum} baslik={e.aktif != null ? kovaAdi(e.aktif) : null}
          satirlar={e.aktif != null ? [
            { deger: `${sayi(sayim[e.aktif])} ${birim}` },
            { deger: `%${sayi((sayim[e.aktif] / toplam) * 100, 1)}`, ad: 'toplamın' },
            ...(bt.length ? [{ deger: bt.filter((x) => x.alt < a + (e.aktif + 1) * w && x.ust > a + e.aktif * w).map((x) => x.ad).join(' / '), ad: 'bant' }] : []),
          ] : []} />
      </div>
      {disarida > 0 && <div className="ist-not">{sayi(disarida)} değer {sayi(a)}–{sayi(b)} aralığı dışında olduğu için gösterilmedi.</div>}
    </Cerceve>
  )
}
