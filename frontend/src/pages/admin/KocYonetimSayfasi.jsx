// [2026-10-10] Süper admin: tüm okulların anlaşmalı eğitim koçları ve görüşme talepleri
import KocYonetimi from '../../components/yonetim/KocYonetimi'

export default function KocYonetimSayfasi() {
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Eğitim Koçları</div>
        <div className="ps">Anlaşmalı koçları buradan ekler ve her koçu çalışacağı okullara atarsınız (okul reddederse durumunu 'Okul reddetti' yapın). Öğrenci yalnızca okulunda aktif olan koçları görür; tüm görüşme talepleri burada sonuçlandırılır. Okul yetkilileri bu bölümü görmez.</div>
      </div>
      <KocYonetimi />
    </div>
  )
}
