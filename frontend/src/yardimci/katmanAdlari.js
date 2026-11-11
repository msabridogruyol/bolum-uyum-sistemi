// [2026-10-10] Katmanların öğrenciye gösterilen adları (veritabanında ad yalnızca "K1" olabilir).
// Adlar ve ikonlar değerlendirme ekranında zaten kullanılanlarla aynıdır.
export const KATMAN_BILGI = {
  K1: { ad: 'Değerler / Motivasyon', ikon: '🌱', soru: 'Bir işte senin için en önemli şey ne?', sure: '≈ 9 dk' },
  K2: { ad: 'Kişilik & Çalışma Tarzı', ikon: '🌿', soru: 'Nasıl bir ortamda rahat edersin?', sure: '≈ 9 dk' },
  K3: { ad: 'İş Ortamı & Profesyonel Yetkinlik', ikon: '🍃', soru: 'Zor bir durumda nasıl davranırsın?', sure: '≈ 9 dk' },
  K4: { ad: 'Alan Eğilimi & Bilişsel Stil', ikon: '🌸', soru: 'Hangi alanlar seni kendine çekiyor?', sure: '≈ 10 dk' },
  K5: { ad: 'İş türü tercihleri', ikon: '🌻', soru: 'Sana en uygun bölümlerdeki işlerden hangileri sana daha yakın?', sure: '≈ 3-5 dk' },
}
export function katmanAdi(kod, ad) {
  if (ad && ad.trim() && ad.trim().toUpperCase() !== (kod || '').toUpperCase()) return ad.trim()
  return KATMAN_BILGI[(kod || '').toUpperCase()]?.ad || boyutKodu(kod)
}

// [2026-11-11] Kullanıcı kararı: ekranda "Katman" yerine "Boyut"; kodlar K1–K5 yerine B1–B5 gösterilir.
// Sistemdeki kod (K1…K5, adres /katmanlar/K1, veritabanı) değişmez; yalnızca gösterilen metin çevrilir.
export function boyutKodu(kod) {
  return typeof kod === 'string' ? kod.replace(/^K([1-5])(?![0-9A-Za-z])/, 'B$1') : kod
}
