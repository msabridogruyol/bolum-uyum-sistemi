// [2026-10-10] Öğrenci özellik puanı (0–100) → düzey etiketi ve rengi: TEK KAYNAK.
// Backend karşılığı: backend/app/core/seviye.py — bantlar değişirse ikisi birlikte güncellenmelidir.
// Kapsam dışı (farklı kavramlar): anket kesme puanları, bölüm uyum yüzdesi, "Bölüm: Yüksek" yüzdelikleri,
// koçluk gap kategorileri (öğrenci − bölüm farkı), keyif / benzerlik yüzdeleri.

// Alt sınırlar dahil, yüksekten düşüğe. grup: guclu / orta / gelisim (sayım ve renk için).
export const BANTLAR = [
  { kod: 'cok_guclu', ad: 'Çok güçlü', alt: 75, grup: 'guclu', renk: 'var(--gr)', zemin: 'var(--grl)',
    aciklama: 'Bu eğilim sende belirgin; farklı sorularda tutarlı olarak öne çıktı.' },
  { kod: 'guclu', ad: 'Güçlü', alt: 62, grup: 'guclu', renk: 'var(--gr)', zemin: 'var(--grl)',
    aciklama: 'Çoğu durumda bu yönde tercih yapıyorsun.' },
  { kod: 'ortanin_ustu', ad: 'Ortanın üstü', alt: 50, grup: 'orta', renk: 'var(--pu)', zemin: 'var(--sur2)',
    aciklama: 'Duruma göre değişiyor, ama bu yöne biraz daha yatkınsın.' },
  { kod: 'orta', ad: 'Orta', alt: 40, grup: 'orta', renk: 'var(--pu)', zemin: 'var(--sur2)',
    aciklama: 'Duruma göre değişiyor; esnek kullanabildiğin bir alan.' },
  { kod: 'gelisime_acik', ad: 'Gelişime açık', alt: 0, grup: 'gelisim', renk: 'var(--am)', zemin: 'var(--aml)',
    aciklama: 'Şu an daha az tercih ettiğin bir yön; istersen çalışarak güçlenebilir.' },
]

const bant = (kod) => BANTLAR.find((b) => b.kod === kod)
export const COK_GUCLU_ESIK = bant('cok_guclu').alt // 75
export const GUCLU_ESIK = bant('guclu').alt // 62 — bu ve üstü "güçlü yön"
export const ORTA_ESIK = bant('orta').alt // 40 — bunun altı "gelişime açık"

export const GRUP_ADLARI = { guclu: 'Güçlü', orta: 'Orta', gelisim: 'Gelişime açık' }

export function seviyeBandi(puan) {
  if (puan == null || Number.isNaN(Number(puan))) return null
  const p = Number(puan)
  return BANTLAR.find((b) => p >= b.alt) || BANTLAR[BANTLAR.length - 1]
}

export const seviyeEtiketi = (puan) => seviyeBandi(puan)?.ad ?? '—'
export const seviyeRengi = (puan) => seviyeBandi(puan)?.renk ?? 'var(--tx3)'
export const seviyeZemini = (puan) => seviyeBandi(puan)?.zemin ?? 'var(--sur2)'
export const seviyeGrubu = (puan) => seviyeBandi(puan)?.grup ?? null
export const gucluMu = (puan) => puan != null && Number(puan) >= GUCLU_ESIK
export const gelisimeAcikMi = (puan) => puan != null && Number(puan) < ORTA_ESIK

// Bandın okunur aralığı: "75 ve üzeri", "62–74", "40'ın altı"
export function bantAraligi(b) {
  const i = BANTLAR.indexOf(b)
  if (i === 0) return `${b.alt} ve üzeri`
  if (b.alt === 0) return `${BANTLAR[i - 1].alt}'ın altı`
  return `${b.alt}–${BANTLAR[i - 1].alt - 1}`
}
