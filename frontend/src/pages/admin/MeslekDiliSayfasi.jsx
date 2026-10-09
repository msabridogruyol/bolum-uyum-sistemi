// [2026-10-09] Süper admin: GENEL meslek dili sözlüğü (tüm okullar). Okula özel sürümler Okul Paneli → Meslek Dili sekmesinde.
import MeslekDiliDuzenleyici from '../../components/yonetim/MeslekDiliDuzenleyici'

export default function MeslekDiliSayfasi() {
  return (
    <div className="pg pg-genis">
      <div className="pt">Meslek Dili Sözlüğü</div>
      <div className="ps">Her bölümün sahada kullanılan terimleri, anlamları ve örnek cümleleri. Okullar kendi sürümlerini Okul Paneli → Meslek Dili sekmesinden oluşturabilir.</div>
      <MeslekDiliDuzenleyici okulId={0} />
    </div>
  )
}
