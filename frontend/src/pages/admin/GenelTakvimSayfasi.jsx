// [2026-10-10] Süper admin: tüm okullara görünen genel takvim (YKS, tercih, özel yetenek sınavları…)
import TakvimYonetimi from '../../components/yonetim/TakvimYonetimi'

export default function GenelTakvimSayfasi() {
  return (
    <div className="pg pg-genis">
      <div className="ph"><div className="pt">Genel Takvim</div><div className="ps">Tüm okulların öğrencilerinin Takvim sayfasında görünen önemli tarihler.</div></div>
      <TakvimYonetimi okulId={null} />
    </div>
  )
}
