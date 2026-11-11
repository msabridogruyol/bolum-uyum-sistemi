// [2026-11-11] Yazarak arama için ortak eşleştirme: büyük/küçük harf ve Türkçe karakter farkı gözetilmez
// ("muhendis" → "Mühendislik", "ISTANBUL" → "İstanbul"). Önce adı aranan metinle başlayanlar, sonra kelime başı, sonra içinde geçenler.
export function sadelestir(s) {
  return String(s ?? '').toLocaleLowerCase('tr-TR')
    .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ı/g, 'i').replace(/ö/g, 'o').replace(/ş/g, 's').replace(/ü/g, 'u')
    .replace(/[âà]/g, 'a').replace(/[îì]/g, 'i').replace(/[ûù]/g, 'u')
    .replace(/\s+/g, ' ').trim()
}

/** liste: [{ ad, ... }] → aranana uyanlar, en iyi eşleşme önce. */
export function suz(liste, aranan, enFazla = 8, alan = (x) => x.ad) {
  const q = sadelestir(aranan)
  if (!q) return liste.slice(0, enFazla)
  const puanli = []
  for (const x of liste) {
    const a = sadelestir(alan(x))
    const i = a.indexOf(q)
    if (i < 0) continue
    puanli.push([i === 0 ? 0 : a[i - 1] === ' ' || a[i - 1] === '(' ? 1 : 2, i, a.length, x])
  }
  puanli.sort((p, r) => p[0] - r[0] || p[1] - r[1] || p[2] - r[2])
  return puanli.slice(0, enFazla).map((p) => p[3])
}

/** Adın aranan kısmını kalın gösterir (React düğümleri). */
export function vurgula(ad, aranan) {
  const q = sadelestir(aranan)
  const s = String(ad ?? '')
  if (!q) return s
  const i = sadelestir(s).indexOf(q)
  // sadeleştirme harf sayısını değiştirmez (yalnızca harf eşlemesi ve boşluk daraltma); boşluk daraltma farkı olursa vurgulanmaz
  if (i < 0 || sadelestir(s).length !== s.toLocaleLowerCase('tr-TR').length) return s
  return [s.slice(0, i), <b key="v">{s.slice(i, i + q.length)}</b>, s.slice(i + q.length)]
}
