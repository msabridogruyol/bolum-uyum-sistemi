// [2026-10-10] İstatistik bileşenleri — renk paleti (TEK KAYNAK).
// Bileşenler renkleri CSS değişkeni olarak kullanır (index.css → "İstatistik bileşenleri" bölümü);
// açık/koyu değerler orada tanımlıdır. Buradaki HEX tabloları belge + doğrulama içindir;
// CSS ile birlikte güncellenmelidir.
//
// Renk işleri (dataviz yönergesi):
//  - KATEGORİK: kimlik (hangi seri). Sabit sırayla atanır, ASLA dönmez; 8'den fazlası "Diğer"e katlanır.
//    Renk varlığa bağlıdır, sırasına değil: filtre seri sayısını değiştirince kalanlar boyanmamalı
//    → seri rengini varlık için sabitle (ör. renk: KATEGORIK[2]).
//  - SIRALI (sequential): büyüklük (ısı haritası). Tek ton, açık→koyu; koyu temada çapa ters döner.
//  - SIRASAL (ordinal): sıralı adımlar (huni). Tek ton, ≤5 adım; yüzeye en yakın adım ≥2:1.
//  - DURUM: iyi / uyarı / ciddi / kritik. Sabittir (temaya göre değişmez), seri rengi olarak kullanılmaz,
//    her zaman ikon + etiketle birlikte.
//
// ── Doğrulama (dataviz/scripts/validate_palette.js, 2026-10-10) ──────────────────────────────
// Yüzeyler uygulamanın kart yüzeyi: açık --sur #FFFFFF, koyu --sur #2B261D.
// Kategorik, açık (#FFFFFF):
//   [PASS] Lightness band  [PASS] Chroma floor
//   [PASS] CVD separation  en kötü komşu #eda100↔#1baf7a ΔE 9.1 (protan)
//   [PASS] Normal-vision   en kötü komşu #e87ba4↔#eda100 ΔE 19.6
//   [WARN] Contrast        3:1 altı: #1baf7a 2.82, #eda100 2.17, #e87ba4 2.69
//          → rahatlama kanalı zorunlu: lejant + doğrudan etiket + "Tablo olarak gör" (GrafikKarti) sağlanıyor.
//   → ALL CHECKS PASS
// Kategorik, koyu (#2B261D):
//   [PASS] Lightness band  [PASS] Chroma floor
//   [PASS] CVD separation  en kötü komşu #c98500↔#199e70 ΔE 8.4 (protan)
//   [PASS] Normal-vision   en kötü komşu #d55181↔#c98500 ΔE 19.3
//   [PASS] Contrast        8 rengin hepsi ≥ 3:1
//   → ALL CHECKS PASS
// Sırasal (--ordinal), açık: #86b6ef,#5598e7,#2a78d6,#1c5cab,#104281 → ALL PASS (açık uç 2.11:1)
// Sırasal (--ordinal), koyu: #256abf,#3987e5,#6da7ec,#9ec5f4,#cde2fb → ALL PASS (koyu uç 2.78:1)
// Saçılım/harita gibi "tüm çiftler" biçimlerinde yalnızca ilk 3 kategorik renk geçer (--pairs all).
// Metin kontrastı (WCAG): artış-iyi metni açık #006300 7.54, koyu #0ca30c 4.48; azalış-kötü metni
// var(--re) açık 4.84, koyu 5.28; eksen yazısı var(--tx2) açık 4.85, koyu 6.75.
// ─────────────────────────────────────────────────────────────────────────────────────────────

/** Kategorik renkler (CSS değişkeni) — sırası CVD güvenliğinin parçasıdır, değiştirme. */
export const KATEGORIK = Array.from({ length: 8 }, (_, i) => `var(--ist-k${i + 1})`)

/** Belge/doğrulama için HEX değerleri (CSS ile aynı). */
export const KATEGORIK_HEX = {
  acik: ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'],
  koyu: ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
}
export const KATEGORIK_ADLAR = ['mavi', 'turuncu', 'su yeşili', 'sarı', 'pembe', 'yeşil', 'mor', 'kırmızı']

/** Katlanan kuyruk ("Diğer") ve vurgu dışı (gölgede kalan) seriler için gri. */
export const DIGER = 'var(--ist-diger)'

/** i. kategorik renk; 8'i aşan dizin DÖNMEZ, "Diğer" grisi döner. */
export const kategorikRenk = (i) => (i >= 0 && i < KATEGORIK.length ? KATEGORIK[i] : DIGER)

/** Segment içine yazılacak etiket rengi (dolgunun parlaklığına göre beyaz/mürekkep). */
export const kategorikUstRenk = (i) => (i >= 0 && i < KATEGORIK.length ? `var(--ist-k${i + 1}-u)` : 'var(--tx)')

/** Sıralı (büyüklük) rampa: 7 adım (--ist-s0..s6), 0 = en az. HEX açık tema içindir; koyu temada CSS sırayı ters çevirir (çok = açık ton). */
export const SIRALI_ADIM = 7
export const SIRALI_HEX = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
/** 0..1 arası oranı sıralı adıma (0..6) çevirir. */
export const siraliAdim = (oran) => Math.max(0, Math.min(SIRALI_ADIM - 1, Math.round(oran * (SIRALI_ADIM - 1))))

/** Sırasal (huni adımları) rampa: --ist-o0..o4, o4 = yüzeye göre en belirgin ton (her iki temada). */
export const SIRASAL_ADIM = 5
export const SIRASAL_HEX = {
  acik: ['#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#104281'],
  koyu: ['#256abf', '#3987e5', '#6da7ec', '#9ec5f4', '#cde2fb'],
}
/** n adımlı sırada i. adımın rengi: ilk adım en belirgin ton (--ist-o4). n > 5 ise tek renge (k1) düşer. */
export function sirasalRenk(i, n) {
  if (n > SIRASAL_ADIM) return KATEGORIK[0]
  return `var(--ist-o${Math.max(0, SIRASAL_ADIM - 1 - i)})`
}

/** Durum renkleri — sabit, temadan bağımsız; daima ikon + etiketle. */
export const DURUM = {
  iyi: { renk: 'var(--ist-iyi)', hex: '#0ca30c', ikon: '✓', ad: 'İyi' },
  uyari: { renk: 'var(--ist-uyari)', hex: '#fab219', ikon: '!', ad: 'Uyarı' },
  ciddi: { renk: 'var(--ist-ciddi)', hex: '#ec835a', ikon: '▲', ad: 'Ciddi' },
  kritik: { renk: 'var(--ist-kritik)', hex: '#d03b3b', ikon: '✕', ad: 'Kritik' },
}

/** Değişim (delta) metin renkleri: yön × iyi mi. */
export const DEGISIM_METIN = { iyi: 'var(--ist-arti-iyi)', kotu: 'var(--re)', notr: 'var(--tx2)' }
