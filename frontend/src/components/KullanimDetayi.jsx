// [2026-11-11] Kullanım analizi: sayfa, adreste görünmeyen bir içeriği açtığında (ör. İş Hayatı › Okulda Öğretilmeyenler
// içinde bir ders) bunu bildirir; süre o içeriğe yazılır (menü › alt sekme › içerik). Görünmez; ad Türkçe kaynak metindir.
export default function KullanimDetayi({ kod, ad }) {
  if (!kod) return null
  return <span hidden data-kullanim-detay={kod} data-kullanim-detay-ad={ad || ''} />
}
