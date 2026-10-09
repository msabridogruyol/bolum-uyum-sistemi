// [2026-10-09] Okul rengi: sayfadaki ayırıcı ve vurgu çizgileri bu renkle çizilir (index.css → --okul).
// Butonlar ve yazılar okunurluk için Filizyol renklerinde kalır.
export const OKUL_PALETI = [
  { ad: 'Filizyol (varsayılan)', renk: null },
  { ad: 'Lacivert', renk: '#1F3A93' },
  { ad: 'Kraliyet mavisi', renk: '#2563EB' },
  { ad: 'Gök mavisi', renk: '#0284C7' },
  { ad: 'Turkuaz', renk: '#0E9AA7' },
  { ad: 'Zümrüt', renk: '#059669' },
  { ad: 'Orman yeşili', renk: '#2F6B3A' },
  { ad: 'Bordo', renk: '#8B1E3F' },
  { ad: 'Kırmızı', renk: '#C62828' },
  { ad: 'Turuncu', renk: '#EA580C' },
  { ad: 'Altın', renk: '#B8860B' },
  { ad: 'Mor', renk: '#6D28D9' },
  { ad: 'Antrasit', renk: '#374151' },
]

export const gecerliRenk = (r) => typeof r === 'string' && /^#[0-9a-f]{6}$/i.test(r)

export function okulRenginiUygula(renk) {
  const kok = document.documentElement
  if (gecerliRenk(renk)) kok.style.setProperty('--okul', renk)
  else kok.style.removeProperty('--okul')
}
