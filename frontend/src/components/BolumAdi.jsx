// [2026-10-08] Tıklanınca bölüm bilgi kartını açan bölüm adı. Kart içine tıklama, dıştaki onClick'i tetiklemez.
import { useBolumBilgi } from '../context/BolumBilgiContext'

export default function BolumAdi({ id, ad, className, style }) {
  const { ac } = useBolumBilgi()
  if (!id && !ad) return null
  return (
    <span
      role="button"
      tabIndex={0}
      title="Bölüm hakkında bilgi"
      className={className}
      onClick={(e) => { e.stopPropagation(); ac(id, ad) }}
      onKeyDown={(e) => { if (e.key === 'Enter') { e.stopPropagation(); ac(id, ad) } }}
      style={{ cursor: 'pointer', textDecoration: 'underline dotted', textUnderlineOffset: 3, ...style }}
    >
      {ad}<span aria-hidden="true" style={{ marginLeft: 5, fontSize: '0.85em', color: 'var(--pu)', textDecoration: 'none', display: 'inline-block' }}>ⓘ</span>
    </span>
  )
}
