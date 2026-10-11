// [2026-10-10] Grafik kartı — başlık, açıklama, sağ köşe yuvası, "Tablo olarak gör" geçişi ve CSV indirme.
// Tablo görünümü grafiğin erişilebilir ikizidir (ekran okuyucu, renk körlüğü, kesin değer): veri varsa her zaman verin.
import { useId, useState } from 'react'
import { csvIndir } from './yardimci'

const hucreMetni = (v) => (typeof v === 'number' ? v.toLocaleString('tr-TR', { maximumFractionDigits: 2 }) : v ?? '—')

const dosyaAdiYap = (s) => String(s || 'veri').toLocaleLowerCase('tr-TR')
  .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ı/g, 'i').replace(/ö/g, 'o').replace(/ş/g, 's').replace(/ü/g, 'u')
  .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'veri'

/** Tablo görünümü (sayılar sağa hizalı, tabular rakam). */
export function VeriTablosu({ tablo, baslik }) {
  if (!tablo?.satirlar?.length) return <div className="ist-bos">Henüz veri yok</div>
  return (
    <div className="ist-tablo-kaydir">
      <table className="ist-tablo">
        {baslik && <caption className="ist-gizli">{baslik}</caption>}
        <thead><tr>{tablo.sutunlar.map((s, i) => <th key={i} scope="col">{s}</th>)}</tr></thead>
        <tbody>
          {tablo.satirlar.map((r, i) => (
            <tr key={i}>
              {r.map((v, j) => j === 0
                ? <th key={j} scope="row">{hucreMetni(v)}</th>
                : <td key={j} className={typeof v === 'number' ? 'sayi' : ''}>{hucreMetni(v)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/**
 * GrafikKarti({ baslik, aciklama, sag, children, tablo, csv, genis, className })
 * tablo: { sutunlar:[başlıklar], satirlar:[[...]] } — verilirse "Tablo olarak gör" düğmesi çıkar.
 * csv: true (vars., tablo varsa) | false | 'dosya-adi'. genis: ızgarada tam satır kaplasın.
 */
export default function GrafikKarti({ baslik, aciklama, sag, children, tablo, csv = true, genis = false, className = '' }) {
  const [tabloAcik, setTabloAcik] = useState(false)
  const id = useId()
  const tabloVar = !!tablo?.satirlar?.length
  return (
    <section className={`card ist-kart${genis ? ' ist-genis' : ''} ${className}`} aria-labelledby={baslik ? `${id}-b` : undefined}>
      <header className="ist-kart-ust">
        <div className="ist-kart-metin">
          {baslik && <h3 id={`${id}-b`} className="ist-kart-baslik">{baslik}</h3>}
          {aciklama && <p className="ist-kart-aciklama">{aciklama}</p>}
        </div>
        {(sag || tabloVar) && (
          <div className="ist-kart-sag">
            {sag}
            {tabloVar && (
              <button type="button" className="ist-dugme" aria-pressed={tabloAcik} onClick={() => setTabloAcik((x) => !x)}>
                {tabloAcik ? 'Grafiği gör' : 'Tablo olarak gör'}
              </button>
            )}
            {tabloVar && csv !== false && (
              <button type="button" className="ist-dugme" onClick={() => csvIndir(tablo, typeof csv === 'string' ? csv : dosyaAdiYap(baslik))}
                aria-label={`${baslik || 'Veri'} — CSV indir`}>
                CSV indir
              </button>
            )}
          </div>
        )}
      </header>
      <div className="ist-kart-govde">
        {tabloAcik && tabloVar ? <VeriTablosu tablo={tablo} baslik={baslik} /> : children}
      </div>
    </section>
  )
}
