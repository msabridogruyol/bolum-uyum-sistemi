// [2026-10-10] Kulüplerim — ilgi testi ve okul kulübü önerileri (eskiden Profilim içinde bir sekmeydi)
import IlgiKulupSekmesi from '../components/IlgiKulupSekmesi'

export default function KuluplerimSayfasi() {
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Kulüplerim</div>
        <div className="ps">İlgi alanlarını keşfet; okulundaki kulüplerden sana en uygun olanları gör.</div>
      </div>
      <IlgiKulupSekmesi />
    </div>
  )
}
