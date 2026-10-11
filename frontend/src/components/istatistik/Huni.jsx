// [2026-10-10] Huni — adım adım dönüşüm (ör. davet edilen → kayıt olan → K1 bitiren → tüm katmanlar).
// Adımlar sıralı olduğundan renk SIRASAL tek ton rampadır (ilk adım en belirgin); 5'ten fazla adımda tek renk.
// Adımlar arasında "bir önceki adımdan geçiş %" yazılır; satır sonunda ilk adıma göre oran.
import { bicim, sayi, metinGenisligi, useEtkilesim, ariaEtiketi } from './yardimci'
import { Bos, Cerceve, Ipucu } from './ortak'
import { sirasalRenk } from './palet'

const yuzde = (a, b) => (b > 0 ? (a / b) * 100 : null)

/** Huni({ adimlar:[{ad, deger}], birim, baslik, ariaEtiket }) */
export default function Huni({ adimlar, birim, baslik, ariaEtiket }) {
  const l = (adimlar || []).filter((a) => a && a.deger != null && !Number.isNaN(Number(a.deger)))
  const e = useEtkilesim(l.length)
  if (!l.length || l.every((a) => !a.deger)) return <Cerceve baslik={baslik}><Bos /></Cerceve>

  const ilk = Number(l[0].deger)
  const maks = Math.max(...l.map((a) => Number(a.deger)))
  const son = l[l.length - 1]
  const degerYeri = Math.ceil(Math.max(...l.map((a) => metinGenisligi(bicim(a.deger, birim), 12, 700)))) + 8
  const ozet = `${l.length} adım; ${l[0].ad} ${bicim(ilk, birim)} → ${son.ad} ${bicim(son.deger, birim)} (%${sayi(yuzde(son.deger, ilk), 1)})`
  const aktif = e.aktif != null ? l[e.aktif] : null

  return (
    <Cerceve baslik={baslik}>
      <div className="ist-cizim" {...e.kapProps} role="img" aria-label={ariaEtiketi(ariaEtiket, baslik, ozet)}>
        <ol className="ist-huni">
          {l.map((a, i) => {
            const oran = maks > 0 ? Number(a.deger) / maks : 0
            const gecis = i > 0 ? yuzde(a.deger, l[i - 1].deger) : null
            const bastan = yuzde(a.deger, ilk)
            return (
              <li key={`${a.ad}-${i}`}>
                {i > 0 && (
                  <div className="ist-huni-gecis" aria-hidden="true">
                    <span>↓</span> {gecis == null ? '—' : `%${sayi(gecis, 1)}`} <small>devam etti</small>
                  </div>
                )}
                <div {...e.isaret(i)} className={`ist-huni-satir${e.aktif === i ? ' aktif' : ''}`}>
                  <div className="ist-huni-ad"><span className="ist-huni-no">{i + 1}</span><span title={a.ad}>{a.ad}</span></div>
                  <div className="ist-yc-iz">
                    <span className="ist-yc-cubuk" style={{ width: `calc((100% - ${degerYeri}px) * ${oran})`, background: sirasalRenk(i, l.length) }} />
                    <span className="ist-yc-deger">{bicim(a.deger, birim)}</span>
                  </div>
                  <div className="ist-huni-oran">{i === 0 ? '%100' : bastan == null ? '—' : `%${sayi(bastan, 1)}`}</div>
                </div>
              </li>
            )
          })}
        </ol>
        <Ipucu durum={e.durum} baslik={aktif?.ad}
          satirlar={aktif ? [
            { deger: bicim(aktif.deger, birim) },
            ...(e.aktif > 0 ? [{ deger: `%${sayi(yuzde(aktif.deger, l[e.aktif - 1].deger), 1)}`, ad: 'önceki adımdan' }] : []),
            { deger: `%${sayi(yuzde(aktif.deger, ilk), 1)}`, ad: 'ilk adıma göre' },
          ] : []} />
      </div>
      <div className="ist-not">Sağdaki oran ilk adıma göredir.</div>
    </Cerceve>
  )
}
