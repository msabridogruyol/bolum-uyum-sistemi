// [2026-10-10] Sütun grafik (tek seri) ve yığın sütun (parça-bütün, 2–8 seri).
// Sütunlar ≤24px, uçtan 4px yuvarlak, tabanda kare; ızgara 1px düz; değer sütun başında (sığarsa).
// Yığında: lejant HER ZAMAN; segment içi etiket yalnızca sığarsa (yoksa ipucu + tablo); toplam sütun başında.
import { useMemo } from 'react'
import { bicim, kisaBicim, eksenAdimlari, metinGenisligi, kisalt, useGenislik, useEtkilesim, sutunYolu, ariaEtiketi } from './yardimci'
import { Ipucu, Lejant, Bos, Cerceve } from './ortak'
import { KATEGORIK, kategorikRenk, kategorikUstRenk } from './palet'

const UST = 20, ALT = 30, BOSLUK = 2, MAKS_SUTUN = 24

function SutunIskelet({ kategoriler, yiginlar, birim, kesir, yukseklik, maks, toplamEtiketi, segmentEtiketi, ipucuSatirlari, aria }) {
  const [ref, W] = useGenislik()
  const n = kategoriler.length
  const toplamlar = yiginlar.map((y) => y.reduce((s, p) => s + Math.max(0, p.deger || 0), 0))
  const ust = maks ?? Math.max(0, ...toplamlar)
  const adimlar = eksenAdimlari(0, ust || 1, 4)
  const tepe = maks ?? adimlar[adimlar.length - 1]
  const solEksen = Math.ceil(Math.max(...adimlar.map((a) => metinGenisligi(kisaBicim(a, birim), 11, 600)))) + 10
  const pw = Math.max(40, W - solEksen - 4)
  const H = yukseklik
  const bant = pw / n
  const sw = Math.max(4, Math.min(MAKS_SUTUN, bant * 0.62))
  const yOl = (v) => UST + H - (v / (tepe || 1)) * H
  const xMerkez = (i) => solEksen + bant * i + bant / 2
  // X etiketi seyreltme: en az ~28px yer yoksa her k. etiket
  const k = Math.max(1, Math.ceil(30 / bant))
  const e = useEtkilesim(n)

  return (
    <div className="ist-cizim" ref={(el) => { ref.current = el; e.kapRef.current = el }}
      tabIndex={e.kapProps.tabIndex} onKeyDown={e.kapProps.onKeyDown} onPointerLeave={e.kapProps.onPointerLeave} onBlur={e.kapProps.onBlur}>
      <svg width="100%" height={UST + H + ALT} viewBox={`0 0 ${W} ${UST + H + ALT}`} role="img" aria-label={aria} className="ist-svg">
        {adimlar.map((a) => (
          <g key={a}>
            <line x1={solEksen} x2={W - 2} y1={yOl(a)} y2={yOl(a)} className={a === 0 ? 'ist-eksen' : 'ist-izgara'} />
            <text x={solEksen - 6} y={yOl(a)} dy="0.35em" textAnchor="end" className="ist-eksen-yazi">{kisaBicim(a, birim)}</text>
          </g>
        ))}
        {yiginlar.map((parcalar, i) => {
          const x = xMerkez(i) - sw / 2
          let taban = 0
          const gorunur = parcalar.filter((p) => p.deger > 0)
          const tepeSira = gorunur.length - 1
          const toplam = toplamlar[i]
          const tepeY = yOl(toplam)
          const etiket = toplamEtiketi ? (birim === '%' ? bicim(toplam, '%', kesir) : sayiKisa(toplam, kesir)) : null
          const etiketSigar = etiket && metinGenisligi(etiket, 11, 700) <= bant - 2
          return (
            <g key={i}>
              {e.aktif === i && <rect x={solEksen + bant * i + 1} y={UST - 4} width={bant - 2} height={H + 4} rx="6" className="ist-vurgu-bant" />}
              {gorunur.map((p, j) => {
                const y0 = yOl(taban), y1 = yOl(taban + p.deger)
                taban += p.deger
                const h = Math.max(0, y0 - y1 - (j > 0 ? BOSLUK : 0))
                const yUst = y1
                const segEt = segmentEtiketi ? sayiKisa(p.deger, kesir) : null
                const sigar = segEt && p.ustRenk && h >= 16 && metinGenisligi(segEt, 10.5, 700) + 6 <= sw
                return (
                  <g key={j}>
                    {j === tepeSira
                      ? <path d={sutunYolu(x, yUst, sw, h)} style={{ fill: p.renk }} />
                      : <rect x={x} y={yUst} width={sw} height={h} style={{ fill: p.renk }} />}
                    {sigar && <text x={x + sw / 2} y={yUst + h / 2} dy="0.35em" textAnchor="middle" className="ist-seg-yazi" style={{ fill: p.ustRenk }}>{segEt}</text>}
                  </g>
                )
              })}
              {etiketSigar && toplam > 0 && <text x={xMerkez(i)} y={tepeY - 6} textAnchor="middle" className="ist-deger-yazi">{etiket}</text>}
              {i % k === 0 && (
                <text x={xMerkez(i)} y={UST + H + 18} textAnchor="middle" className="ist-eksen-yazi">
                  <title>{kategoriler[i]}</title>
                  {kisalt(kategoriler[i], Math.max(bant * k - 6, 20), 11)}
                </text>
              )}
              <rect {...e.isaret(i)} x={solEksen + bant * i} y={UST - 10} width={bant} height={H + 10 + ALT} className="ist-isabet" />
            </g>
          )
        })}
      </svg>
      <Ipucu durum={e.durum} baslik={e.aktif != null ? kategoriler[e.aktif] : null}
        satirlar={e.aktif != null ? ipucuSatirlari(e.aktif) : []} />
    </div>
  )
}

const sayiKisa = (v, kesir) => Number(v).toLocaleString('tr-TR', { maximumFractionDigits: kesir })

/**
 * SutunGrafik({ veri:[{ad, deger}], birim, renk, maks, yukseklik, kesir, baslik, ariaEtiket })
 * Tek seri: sıralanmış/zamana bağlı kategorilerde büyüklük karşılaştırma. Lejant yok.
 */
export function SutunGrafik({ veri, birim, renk = KATEGORIK[0], maks, yukseklik = 200, kesir = 1, degerEtiketi = true, baslik, ariaEtiket }) {
  const satirlar = useMemo(() => (veri || []).filter((v) => v && v.deger != null && !Number.isNaN(Number(v.deger))), [veri])
  if (!satirlar.length) return <Cerceve baslik={baslik}><Bos /></Cerceve>
  const enUst = satirlar.reduce((a, b) => (b.deger > a.deger ? b : a))
  const ozet = `${satirlar.length} sütun, en yüksek ${enUst.ad} ${bicim(enUst.deger, birim, kesir)}`
  return (
    <Cerceve baslik={baslik}>
      <SutunIskelet
        kategoriler={satirlar.map((s) => s.ad)}
        yiginlar={satirlar.map((s) => [{ deger: Number(s.deger), renk }])}
        birim={birim} kesir={kesir} yukseklik={yukseklik} maks={maks}
        toplamEtiketi={degerEtiketi} segmentEtiketi={false}
        ipucuSatirlari={(i) => [{ deger: bicim(satirlar[i].deger, birim, kesir) }]}
        aria={ariaEtiketi(ariaEtiket, baslik, ozet)} />
    </Cerceve>
  )
}

/**
 * YiginSutun({ kategoriler:[...], seriler:[{ad, degerler:[...], renk?}], birim, oransal, ... })
 * Parça-bütün. Seri rengi verilmezse dizin sırasıyla kategorik palet (dönmez; 8'den fazlası gri "Diğer").
 * oransal: true → her sütun %100'e ölçeklenir (birim '%' olur).
 */
export function YiginSutun({ kategoriler, seriler, birim, oransal = false, maks, yukseklik = 220, kesir = 1, segmentEtiketi = true, baslik, ariaEtiket }) {
  const kat = kategoriler || []
  const sr = (seriler || []).map((s, i) => ({ ...s, renk: s.renk || kategorikRenk(i), ustRenk: s.ustRenk || (s.renk ? null : kategorikUstRenk(i)) }))
  const toplamHam = kat.map((_, i) => sr.reduce((t, s) => t + Math.max(0, Number(s.degerler?.[i]) || 0), 0))
  const bos = !kat.length || !sr.length || toplamHam.every((t) => t === 0)
  if (bos) return <Cerceve baslik={baslik}><Bos /></Cerceve>
  const b = oransal ? '%' : birim
  const deger = (s, i) => {
    const v = Math.max(0, Number(s.degerler?.[i]) || 0)
    return oransal ? (toplamHam[i] ? (v / toplamHam[i]) * 100 : 0) : v
  }
  const yiginlar = kat.map((_, i) => sr.map((s) => ({ deger: deger(s, i), renk: s.renk, ustRenk: s.ustRenk, ad: s.ad })))
  const ozet = `${kat.length} kategori, ${sr.length} seri (${sr.map((s) => s.ad).join(', ')})`
  return (
    <Cerceve baslik={baslik}>
      <Lejant ogeler={sr.map((s) => ({ ad: s.ad, renk: s.renk }))} />
      <SutunIskelet
        kategoriler={kat} yiginlar={yiginlar}
        birim={b} kesir={kesir} yukseklik={yukseklik} maks={oransal ? 100 : maks}
        toplamEtiketi={!oransal} segmentEtiketi={segmentEtiketi}
        ipucuSatirlari={(i) => [
          ...sr.map((s) => ({
            renk: s.renk, ad: s.ad,
            deger: oransal ? `${bicim(deger(s, i), '%', 0)} (${bicim(Number(s.degerler?.[i]) || 0, birim, kesir)})` : bicim(Number(s.degerler?.[i]) || 0, birim, kesir),
          })).reverse(),
          { ad: 'Toplam', deger: bicim(toplamHam[i], birim, kesir) },
        ]}
        aria={ariaEtiketi(ariaEtiket, baslik, ozet)} />
    </Cerceve>
  )
}

export default SutunGrafik
