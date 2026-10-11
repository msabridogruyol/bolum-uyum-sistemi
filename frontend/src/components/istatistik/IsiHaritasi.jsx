// [2026-10-10] Isı haritası — iki kategorik boyutta büyüklük (ör. şube × katman ortalaması).
// SIRALI tek ton (az = açık, çok = koyu; koyu temada ters), 7 adım, ölçek lejantı her zaman.
// Hücre yazısı dolgunun parlaklığına göre beyaz/mürekkep (CSS .ist-s0..s6). Boş hücre "—".
import { bicim as bicimle, sayi, useEtkilesim, ariaEtiketi } from './yardimci'
import { Bos, Cerceve, Ipucu } from './ortak'
import { SIRALI_ADIM, siraliAdim } from './palet'

/**
 * IsiHaritasi({ satirlar:[ad], sutunlar:[ad], degerler:[[sayı|null]], bicim, aralik, kesir, satirBasligi })
 * bicim: birim metni ('%', 'puan') ya da (v) => metin. aralik: [min, maks] renk ölçeği (vars. verinin min–maks'ı;
 * 0–100 puanlarda [0,100] vermek okullar arası karşılaştırmayı tutarlı kılar).
 */
export default function IsiHaritasi({ satirlar, sutunlar, degerler, bicim, aralik, kesir = 1, satirBasligi = '', baslik, ariaEtiket }) {
  const R = satirlar || [], C = sutunlar || []
  const hucre = (r, c) => { const v = degerler?.[r]?.[c]; return v == null || Number.isNaN(Number(v)) ? null : Number(v) }
  const tum = R.flatMap((_, r) => C.map((_, c) => hucre(r, c))).filter((v) => v != null)
  const e = useEtkilesim(R.length * C.length, { satirAdimi: C.length })
  if (!R.length || !C.length || !tum.length) return <Cerceve baslik={baslik}><Bos /></Cerceve>

  const yaz = (v) => (v == null ? '—' : typeof bicim === 'function' ? bicim(v) : bicimle(v, bicim, kesir))
  const [mn, mx] = aralik || [Math.min(...tum), Math.max(...tum)]
  const adim = (v) => siraliAdim(mx > mn ? (v - mn) / (mx - mn) : 0.5)
  let enUst = { v: -Infinity }
  R.forEach((_, r) => C.forEach((_, c) => { const v = hucre(r, c); if (v != null && v > enUst.v) enUst = { v, r, c } }))
  const ozet = `${R.length} satır × ${C.length} sütun; en yüksek ${R[enUst.r]} / ${C[enUst.c]}: ${yaz(enUst.v)}`
  const ar = e.aktif != null ? Math.floor(e.aktif / C.length) : null
  const ac = e.aktif != null ? e.aktif % C.length : null

  return (
    <Cerceve baslik={baslik}>
      <div className="ist-isi-kaydir">
        <div className="ist-cizim" {...e.kapProps} role="img" aria-label={ariaEtiketi(ariaEtiket, baslik, ozet)}>
          <div className="ist-isi" style={{ gridTemplateColumns: `minmax(72px, max-content) repeat(${C.length}, minmax(46px, 1fr))` }}>
            <div className="ist-isi-kose">{satirBasligi}</div>
            {C.map((c, j) => <div key={`c${j}`} className={`ist-isi-sutun${ac === j ? ' aktif' : ''}`} title={c}>{c}</div>)}
            {R.map((r, i) => [
              <div key={`r${i}`} className={`ist-isi-satir${ar === i ? ' aktif' : ''}`} title={r}>{r}</div>,
              ...C.map((_, j) => {
                const v = hucre(i, j)
                const k = i * C.length + j
                return (
                  <div key={`h${i}-${j}`} {...e.isaret(k)}
                    className={`ist-isi-hucre ${v == null ? 'ist-isi-bos' : `ist-s${adim(v)}`}${e.aktif === k ? ' aktif' : ''}`}>
                    {yaz(v)}
                  </div>
                )
              }),
            ])}
          </div>
          <Ipucu durum={e.durum} baslik={e.aktif != null ? `${R[ar]} · ${C[ac]}` : null}
            satirlar={e.aktif != null ? [{ deger: yaz(hucre(ar, ac)) }] : []} />
        </div>
      </div>
      <div className="ist-isi-olcek" aria-hidden="true">
        <span>{yaz(mn)}</span>
        <span className="ist-isi-olcek-serit">{Array.from({ length: SIRALI_ADIM }, (_, i) => <i key={i} className={`ist-s${i}`} />)}</span>
        <span>{yaz(mx)}</span>
        {aralik && <small>· sabit ölçek {sayi(mn)}–{sayi(mx)}</small>}
      </div>
    </Cerceve>
  )
}
