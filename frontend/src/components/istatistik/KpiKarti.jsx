// [2026-10-10] KPI kartı (stat tile) ve KPI satırı.
// Tek bir güncel sayı için grafik değil bu kart kullanılır (tek çubuklu grafik / 2 dilimli pasta yerine).
import { sayi } from './yardimci'

const TONLAR = ['notr', 'okul', 'iyi', 'uyari', 'kotu', 'bilgi']

/**
 * degisim: sayı (ör. +4.2) ya da { deger, birim?: '%'|'puan'|..., donem?: 'geçen aya göre', iyiYon?: 'yukari'|'asagi'|'yok' }
 * Renk = yön × iyi mi. Varsayılan iyiYon 'yukari'. Ok + işaret her zaman yazılır (renk tek başına anlam taşımaz).
 */
function Degisim({ degisim }) {
  if (degisim == null) return null
  const d = typeof degisim === 'number' ? { deger: degisim } : degisim
  if (d.deger == null || Number.isNaN(Number(d.deger))) return null
  const v = Number(d.deger)
  const iyiYon = d.iyiYon || 'yukari'
  const yon = v > 0 ? 'yukari' : v < 0 ? 'asagi' : 'sabit'
  const ton = yon === 'sabit' || iyiYon === 'yok' ? 'notr' : yon === iyiYon ? 'iyi' : 'kotu'
  const ok = yon === 'yukari' ? '▲' : yon === 'asagi' ? '▼' : '■'
  const isaret = v > 0 ? '+' : v < 0 ? '−' : ''
  const mutlak = sayi(Math.abs(v))
  const metin = d.birim === '%' ? `${isaret}%${mutlak}` : `${isaret}${mutlak}${d.birim ? ` ${d.birim}` : ''}`
  const yonAdi = yon === 'yukari' ? 'artış' : yon === 'asagi' ? 'azalış' : 'değişim yok'
  return (
    <div className={`ist-kpi-degisim ist-d-${ton}`} aria-label={`${yonAdi} ${metin}${d.donem ? `, ${d.donem}` : ''}`}>
      <span aria-hidden="true">{ok} {metin}</span>
      {d.donem && <span className="ist-kpi-donem" aria-hidden="true">{d.donem}</span>}
    </div>
  )
}

/** İsteğe bağlı küçük seyir çizgisi (sparkline): gri, son nokta vurgulu. */
function Seyir({ degerler }) {
  const v = (degerler || []).filter((x) => x != null)
  if (v.length < 2) return null
  const W = 100, H = 28, min = Math.min(...v), max = Math.max(...v), r = max - min || 1
  const p = v.map((x, i) => [(i / (v.length - 1)) * (W - 4) + 2, H - 3 - ((x - min) / r) * (H - 6)])
  const son = p[p.length - 1]
  return (
    <svg className="ist-kpi-seyir" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
      <polyline points={p.map((q) => q.join(',')).join(' ')} style={{ fill: 'none', stroke: 'var(--ist-diger)', strokeWidth: 1.5, vectorEffect: 'non-scaling-stroke', strokeLinejoin: 'round', strokeLinecap: 'round' }} />
      <circle cx={son[0]} cy={son[1]} r="2.5" style={{ fill: 'var(--ist-k1)' }} />
    </svg>
  )
}

/**
 * KpiKarti({ etiket, deger, alt, degisim, ikon, ton, birim, seyir, onClick })
 * deger sayıysa Türkçe biçimlenir; metin de verilebilir ("—", "4,2 / 5").
 */
export function KpiKarti({ etiket, deger, alt, degisim, ikon, ton = 'notr', birim, seyir, onClick }) {
  const t = TONLAR.includes(ton) ? ton : 'notr'
  const gosterim = typeof deger === 'number'
    ? (birim === '%' ? `%${sayi(deger)}` : sayi(deger))
    : (deger ?? '—')
  const Etiket = onClick ? 'button' : 'div'
  return (
    <Etiket className={`ist-kpi ist-ton-${t}`} onClick={onClick} type={onClick ? 'button' : undefined}>
      <div className="ist-kpi-ust">
        {ikon && <span className="ist-kpi-ikon" aria-hidden="true">{ikon}</span>}
        <span className="ist-kpi-etiket">{etiket}</span>
      </div>
      <div className="ist-kpi-deger">
        {gosterim}
        {birim && birim !== '%' && typeof deger === 'number' && <small> {birim}</small>}
      </div>
      <Degisim degisim={degisim} />
      {alt && <div className="ist-kpi-alt">{alt}</div>}
      <Seyir degerler={seyir} />
    </Etiket>
  )
}

/** KpiSatiri — kartları ızgarada dizer, dar ekranda otomatik sarar. min: kart en dar genişliği (px). */
export function KpiSatiri({ children, min = 170 }) {
  return <div className="ist-kpi-satiri" style={{ '--ist-kpi-min': `${min}px` }}>{children}</div>
}

export default KpiKarti
