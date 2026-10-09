// [2026-10-08] Tıklanınca bölüm bilgi kartını açan bölüm adı. Kart içine tıklama, dıştaki onClick'i tetiklemez.
// [2026-10-09] Alt çizgi kaldırıldı: tıklanabilirlik hafif zemin, bilgi rozeti ve üzerine gelince büyüme ile gösterilir.
import { useBolumBilgi } from '../context/BolumBilgiContext'

export default function BolumAdi({ id, ad, className, style }) {
  const { ac } = useBolumBilgi()
  if (!id && !ad) return null
  return (
    <span
      role="button"
      tabIndex={0}
      title="Bölüm hakkında bilgi için tıkla"
      className={`bolum-adi-btn${className ? ' ' + className : ''}`}
      onClick={(e) => { e.stopPropagation(); ac(id, ad) }}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); ac(id, ad) } }}
      style={style}
    >
      <span className="bolum-adi-metin">{ad}</span>
      <span className="bolum-adi-rozet" aria-hidden="true">i</span>
    </span>
  )
}
