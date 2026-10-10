// [2026-10-10] Katmanların öğrenciye gösterilen adları (veritabanında ad yalnızca "K1" olabilir).
export const KATMAN_BILGI = {
  K1: { ad: 'Değerlerin', ikon: '🧭', soru: 'Bir işte senin için en önemli şey ne?', sure: '≈ 5 dk' },
  K2: { ad: 'Kişiliğin', ikon: '🌀', soru: 'Nasıl bir ortamda rahat edersin?', sure: '≈ 5 dk' },
  K3: { ad: 'İş becerilerin', ikon: '🛠️', soru: 'Zor bir durumda nasıl davranırsın?', sure: '≈ 5 dk' },
  K4: { ad: 'İlgi ve eğilimlerin', ikon: '🔭', soru: 'Hangi alanlar seni kendine çekiyor?', sure: '≈ 5 dk' },
  K5: { ad: 'Sana özel alanlar', ikon: '🌻', soru: 'İlgi alanında hangi yöne gitmelisin?', sure: '≈ 3 dk / alan' },
}
export function katmanAdi(kod, ad) {
  if (ad && ad.trim() && ad.trim().toUpperCase() !== (kod || '').toUpperCase()) return ad.trim()
  return KATMAN_BILGI[(kod || '').toUpperCase()]?.ad || kod
}
