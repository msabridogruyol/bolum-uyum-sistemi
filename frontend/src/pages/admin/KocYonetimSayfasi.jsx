// [2026-10-10] Süper admin: tüm okulların anlaşmalı eğitim koçları ve görüşme talepleri
import KocYonetimi from '../../components/yonetim/KocYonetimi'

export default function KocYonetimSayfasi() {
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Eğitim Koçları</div>
        <div className="ps">Tüm okullara açık ya da tek bir okula özel anlaşmalı koçlar ve öğrencilerin görüşme talepleri. Okul yetkilileri kendi okullarının taleplerini Okul Paneli → Koçlar sekmesinden yönetir.</div>
      </div>
      <KocYonetimi okulId={null} />
    </div>
  )
}
