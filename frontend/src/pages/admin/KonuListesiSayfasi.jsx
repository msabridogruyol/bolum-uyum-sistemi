// [2026-10-10] Süper admin: Net Takibi genel konu listesi
import KonuListesiYonetimi from '../../components/yonetim/KonuListesiYonetimi'

export default function KonuListesiSayfasi() {
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Konu Listesi</div>
        <div className="ps">Net Takibi → Konu Takibi'nde öğrencilerin gördüğü TYT / AYT konuları (genel liste).</div>
      </div>
      <KonuListesiYonetimi />
    </div>
  )
}
