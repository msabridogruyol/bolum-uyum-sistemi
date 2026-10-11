// [2026-10-10] Halka (donut) — YALNIZCA 2–5 parçalı parça-bütün, bir bakışta oran için.
// Yakın değerleri karşılaştırmak ya da 5'ten fazla parça → YatayCubuk kullan. 5'i aşan veride
// ilk 4 parça korunur, kalanı gri "Diğer"e katlanır (renk asla döndürülmez).
// Her parçanın değeri ve yüzdesi yanındaki listede yazılıdır (renk tek başına anlam taşımaz).
import { bicim, sayi, useEtkilesim, ariaEtiketi } from './yardimci'
import { Bos, Cerceve, Ipucu } from './ortak'
import { kategorikRenk, DIGER } from './palet'

const MAKS_PARCA = 5

function yay(cx, cy, r0, r1, a0, a1) {
  const p = (r, a) => [cx + r * Math.sin(a), cy - r * Math.cos(a)]
  const buyuk = a1 - a0 > Math.PI ? 1 : 0
  const [x0, y0] = p(r1, a0), [x1, y1] = p(r1, a1), [x2, y2] = p(r0, a1), [x3, y3] = p(r0, a0)
  return `M${x0},${y0}A${r1},${r1} 0 ${buyuk} 1 ${x1},${y1}L${x2},${y2}A${r0},${r0} 0 ${buyuk} 0 ${x3},${y3}Z`
}

/** Halka({ veri:[{ad, deger, renk?}], birim, merkezEtiket='toplam', kesir }) */
export default function Halka({ veri, birim, merkezEtiket = 'toplam', kesir = 1, baslik, ariaEtiket }) {
  let l = (veri || []).filter((v) => v && Number(v.deger) > 0).map((v, i) => ({ ...v, deger: Number(v.deger), renk: v.renk || kategorikRenk(i) }))
  if (l.length > MAKS_PARCA) {
    const kalan = l.slice(MAKS_PARCA - 1)
    l = [...l.slice(0, MAKS_PARCA - 1), { ad: `Diğer (${kalan.length})`, deger: kalan.reduce((s, v) => s + v.deger, 0), renk: DIGER }]
  }
  const e = useEtkilesim(l.length)
  if (!l.length) return <Cerceve baslik={baslik}><Bos /></Cerceve>

  const top = l.reduce((s, v) => s + v.deger, 0)
  const S = 160, c = S / 2, r1 = 76, r0 = 50
  let aci = 0
  const dilimler = l.map((v) => {
    const a0 = aci, a1 = aci + (v.deger / top) * Math.PI * 2
    aci = a1
    return { ...v, a0, a1 }
  })
  const ozet = l.map((v) => `${v.ad} %${sayi((v.deger / top) * 100, 1)}`).join(', ')
  const aktif = e.aktif != null ? l[e.aktif] : null

  return (
    <Cerceve baslik={baslik}>
      <div className="ist-cizim ist-halka" {...e.kapProps} role="img" aria-label={ariaEtiketi(ariaEtiket, baslik, ozet)}>
        <svg viewBox={`0 0 ${S} ${S}`} className="ist-halka-svg" aria-hidden="true">
          {dilimler.length === 1
            ? <circle {...e.isaret(0)} cx={c} cy={c} r={(r0 + r1) / 2} style={{ fill: 'none', stroke: dilimler[0].renk, strokeWidth: r1 - r0 }} />
            : dilimler.map((d, i) => (
              <path key={i} {...e.isaret(i)} d={yay(c, c, r0, r1, d.a0, d.a1)} className="ist-dilim"
                style={{ fill: d.renk, opacity: e.aktif != null && e.aktif !== i ? 0.45 : 1 }} />
            ))}
          <text x={c} y={c - 4} textAnchor="middle" className="ist-halka-toplam">{sayi(aktif ? aktif.deger : top, kesir)}</text>
          <text x={c} y={c + 14} textAnchor="middle" className="ist-eksen-yazi">{aktif ? `%${sayi((aktif.deger / top) * 100, 1)}` : merkezEtiket}</text>
        </svg>
        <ul className="ist-halka-liste">
          {l.map((v, i) => (
            <li key={v.ad} {...e.isaret(i)} className={e.aktif === i ? 'aktif' : ''}>
              <i className="ist-lej-kutu" style={{ background: v.renk }} />
              <span className="ist-halka-ad" title={v.ad}>{v.ad}</span>
              <b>%{sayi((v.deger / top) * 100, 1)}</b>
              <small>{bicim(v.deger, birim, kesir)}</small>
            </li>
          ))}
        </ul>
        <Ipucu durum={e.durum} baslik={aktif?.ad}
          satirlar={aktif ? [{ renk: aktif.renk, deger: `%${sayi((aktif.deger / top) * 100, 1)}`, ad: bicim(aktif.deger, birim, kesir) }] : []} />
      </div>
    </Cerceve>
  )
}
