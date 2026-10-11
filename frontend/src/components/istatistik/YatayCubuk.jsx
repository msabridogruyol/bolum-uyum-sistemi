// [2026-10-10] Yatay çubuk — sıralı kategoriler (bölümler, okullar, özellikler...).
// Tek seri = tek renk (lejant yok, başlık neyin çizildiğini söyler). Değer çubuğun ucunda, metin renginde.
// Uzun adlar CSS ile "…" kesilir; tam ad title ve ipucunda.
import { useMemo } from 'react'
import { bicim, metinGenisligi, useEtkilesim, ariaEtiketi } from './yardimci'
import { Bos, Cerceve, Ipucu } from './ortak'
import { KATEGORIK, DIGER } from './palet'

/**
 * veri: [{ ad, deger, alt? }]  birim: '%' | 'öğrenci' | ...  maks: ölçek üst sınırı (vars. en büyük değer)
 * renk: tek seri rengi (vars. kategorik 1)  enFazla: gösterilecek en çok satır (kalanı not olarak)
 * vurgu: ad ya da ad dizisi → yalnızca bunlar renkli, diğerleri gri (vurgu biçimi)
 * sirala: true → büyükten küçüğe (vars.)  onTik(oge): satır tıklanınca
 */
export default function YatayCubuk({
  veri, birim, maks, renk = KATEGORIK[0], enFazla, vurgu, sirala = true, kesir = 1,
  baslik, ariaEtiket, onTik,
}) {
  const satirlar = useMemo(() => {
    const l = (veri || []).filter((v) => v && v.deger != null && !Number.isNaN(Number(v.deger)))
    return sirala ? [...l].sort((a, b) => b.deger - a.deger) : l
  }, [veri, sirala])
  const gorunen = enFazla ? satirlar.slice(0, enFazla) : satirlar
  const gizli = satirlar.length - gorunen.length
  const ust = maks ?? Math.max(0, ...satirlar.map((s) => s.deger))
  const vurgular = vurgu == null ? null : new Set([].concat(vurgu))
  const e = useEtkilesim(gorunen.length)

  if (!gorunen.length) return <Cerceve baslik={baslik}><Bos /></Cerceve>

  const enUst = gorunen[0]
  const degerYeri = Math.ceil(Math.max(...gorunen.map((s) => metinGenisligi(bicim(s.deger, birim, kesir), 12, 700)))) + 8
  const ozet = `${satirlar.length} kategori, en yüksek ${enUst.ad} ${bicim(enUst.deger, birim, kesir)}`
  const aktif = e.aktif != null ? gorunen[e.aktif] : null

  return (
    <Cerceve baslik={baslik}>
      <div className="ist-cizim" {...e.kapProps} role="img" aria-label={ariaEtiketi(ariaEtiket, baslik, ozet)}>
        <div className="ist-yc">
          {gorunen.map((s, i) => {
            const oran = ust > 0 ? Math.max(0, Math.min(1, s.deger / ust)) : 0
            const r = vurgular && !vurgular.has(s.ad) ? DIGER : renk
            return (
              <div key={`${s.ad}-${i}`} {...e.isaret(i)}
                className={`ist-yc-satir${e.aktif === i ? ' aktif' : ''}${onTik ? ' tiklanir' : ''}`}
                onClick={onTik ? () => onTik(s) : undefined}>
                <div className="ist-yc-ad">
                  <span title={s.ad}>{s.ad}</span>
                  {s.alt && <small>{s.alt}</small>}
                </div>
                <div className="ist-yc-iz">
                  <span className="ist-yc-cubuk" style={{ width: `calc((100% - ${degerYeri}px) * ${oran})`, background: r }} />
                  <span className="ist-yc-deger">{bicim(s.deger, birim, kesir)}</span>
                </div>
              </div>
            )
          })}
        </div>
        <Ipucu durum={e.durum}
          baslik={aktif?.ad}
          satirlar={aktif ? [{ deger: bicim(aktif.deger, birim, kesir), ad: aktif.alt }] : []} />
      </div>
      {gizli > 0 && <div className="ist-not">+{gizli.toLocaleString('tr-TR')} kategori daha (tablo görünümünde)</div>}
    </Cerceve>
  )
}
