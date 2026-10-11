// [2026-10-10] İstatistik bileşenleri — bileşen olmayan yardımcılar: sayı biçimi, ölçek, metin ölçümü,
// genişlik ölçümü ve etkileşim (fare/dokunma/klavye) kancaları, CSV.
import { useEffect, useLayoutEffect, useRef, useState, useCallback } from 'react'

// ── Sayı biçimi (Türkçe) ─────────────────────────────────────────────
export function sayi(n, kesir = 1) {
  if (n == null || Number.isNaN(Number(n))) return '—'
  return Number(n).toLocaleString('tr-TR', { maximumFractionDigits: kesir })
}

/** Birimli değer: "%45", "1.250 öğrenci", "64". */
export function bicim(n, birim, kesir = 1) {
  if (n == null || Number.isNaN(Number(n))) return '—'
  const s = sayi(n, kesir)
  if (!birim) return s
  if (birim === '%') return `%${s}`
  return `${s} ${birim}`
}

const KOMPAKT = typeof Intl !== 'undefined' ? new Intl.NumberFormat('tr-TR', { notation: 'compact', maximumFractionDigits: 1 }) : null
/** Eksen için kısa sayı: 10.000 ve üstü "12,9 B" gibi. */
export function kisaSayi(n) {
  if (n == null) return ''
  if (Math.abs(n) >= 10000 && KOMPAKT) return KOMPAKT.format(n)
  return sayi(n, 1)
}
export const kisaBicim = (n, birim) => (birim === '%' ? `%${kisaSayi(n)}` : kisaSayi(n))

/** Okunur eksen adımları: [min..max] aralığını ~adet parçaya böler. */
export function eksenAdimlari(min, max, adet = 4) {
  if (!(max > min)) { max = min + 1 }
  const ham = (max - min) / adet
  const us = Math.pow(10, Math.floor(Math.log10(ham)))
  const kat = ham / us
  const adim = (kat <= 1 ? 1 : kat <= 2 ? 2 : kat <= 2.5 ? 2.5 : kat <= 5 ? 5 : 10) * us
  const bas = Math.floor(min / adim) * adim
  const son = Math.ceil(max / adim) * adim
  const l = []
  for (let v = bas; v <= son + adim / 2; v += adim) l.push(Math.round(v * 1e6) / 1e6)
  return l
}

// ── Metin ölçümü / kısaltma ──────────────────────────────────────────
let tuval = null
export function metinGenisligi(metin, px = 12, kalinlik = 600) {
  const s = String(metin ?? '')
  try {
    if (!tuval) tuval = document.createElement('canvas').getContext('2d')
    tuval.font = `${kalinlik} ${px}px "Nunito Sans", system-ui, sans-serif`
    return tuval.measureText(s).width
  } catch { return s.length * px * 0.56 }
}

/** Genişliğe sığmayan metni "…" ile kısaltır (tam ad title/ipucunda verilir). */
export function kisalt(metin, maks, px = 12, kalinlik = 600) {
  const s = String(metin ?? '')
  if (metinGenisligi(s, px, kalinlik) <= maks) return s
  let a = 0, b = s.length
  while (a < b) {
    const m = Math.ceil((a + b) / 2)
    if (metinGenisligi(s.slice(0, m) + '…', px, kalinlik) <= maks) a = m; else b = m - 1
  }
  return a > 0 ? s.slice(0, a).trimEnd() + '…' : '…'
}

// ── Genişlik ölçümü: SVG gerçek piksel genişliğinde çizilir (yazılar telefonda küçülmez) ──
const useIzoEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect
export function useGenislik(varsayilan = 560) {
  const ref = useRef(null)
  const [w, setW] = useState(varsayilan)
  useIzoEffect(() => {
    const el = ref.current
    if (!el) return
    const olc = () => { const g = Math.floor(el.getBoundingClientRect().width); if (g > 0) setW(g) }
    olc()
    if (typeof ResizeObserver === 'undefined') return
    const ro = new ResizeObserver(olc)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return [ref, w]
}

// ── Etkileşim: fare/dokunma + klavye (ok tuşları) ile tek araç ipucu ─────────
// n: işaret sayısı; satirAdimi: ↑/↓ tuşlarının atlayacağı işaret sayısı (ısı haritası için sütun sayısı);
// konum(i): klavye ile seçilince ipucunun konumu (verilmezse [data-i] öğesinin üst ortası).
export function useEtkilesim(n, { satirAdimi = 1, konum } = {}) {
  const kapRef = useRef(null)
  const [durum, setDurum] = useState(null)
  const kapat = useCallback(() => setDurum(null), [])

  const olayKonumu = (e) => {
    const a = kapRef.current?.getBoundingClientRect()
    return a ? { x: e.clientX - a.left, y: e.clientY - a.top } : { x: 0, y: 0 }
  }
  const goster = useCallback((i, x, y) => setDurum({ i, x, y, w: kapRef.current?.clientWidth }), [])

  const isarettenGoster = (i) => {
    const w = kapRef.current?.clientWidth
    if (konum) { const k = konum(i); setDurum({ i, w, ...k }); return }
    const kap = kapRef.current
    const el = kap?.querySelector(`[data-i="${i}"]`)
    if (!kap || !el) { setDurum({ i, w, x: 0, y: 0 }); return }
    const a = kap.getBoundingClientRect(), b = el.getBoundingClientRect()
    setDurum({ i, w, x: b.left - a.left + b.width / 2, y: b.top - a.top })
  }

  const onKeyDown = (e) => {
    if (!n) return
    const simdi = durum?.i ?? -1
    let i = null
    if (e.key === 'ArrowRight') i = simdi + 1
    else if (e.key === 'ArrowLeft') i = simdi < 0 ? n - 1 : simdi - 1
    else if (e.key === 'ArrowDown') i = simdi < 0 ? 0 : simdi + satirAdimi
    else if (e.key === 'ArrowUp') i = simdi < 0 ? 0 : simdi - satirAdimi
    else if (e.key === 'Home') i = 0
    else if (e.key === 'End') i = n - 1
    else if (e.key === 'Escape') { kapat(); return }
    if (i == null) return
    e.preventDefault()
    isarettenGoster(Math.max(0, Math.min(n - 1, i)))
  }

  /** Her işarete (çubuk, hücre, dilim) yayılacak özellikler. */
  const isaret = (i) => ({
    'data-i': i,
    onPointerMove: (e) => { const k = olayKonumu(e); goster(i, k.x, k.y) },
    onPointerDown: (e) => { const k = olayKonumu(e); goster(i, k.x, k.y) },
  })

  const kapProps = {
    ref: kapRef,
    tabIndex: n ? 0 : undefined,
    onKeyDown,
    onPointerLeave: (e) => { if (e.pointerType !== 'touch') kapat() },
    onBlur: kapat,
  }
  return { kapRef, durum, aktif: durum?.i ?? null, goster, kapat, isaret, kapProps, olayKonumu }
}

/** Alttan kare, uçtan 4px yuvarlak sütun yolu (taban y+h'de). */
export function sutunYolu(x, y, w, h, r = 4) {
  if (h <= 0 || w <= 0) return ''
  r = Math.min(r, w / 2, h)
  return `M${x},${y + h}V${y + r}Q${x},${y} ${x + r},${y}H${x + w - r}Q${x + w},${y} ${x + w},${y + r}V${y + h}Z`
}

/** Erişilebilir etiket: verilen etiket yoksa başlık + otomatik özet. */
export const ariaEtiketi = (etiket, baslik, ozet) => etiket || [baslik, ozet].filter(Boolean).join(': ')

/** CSV (Türkçe Excel uyumlu: ';' ayraç, ondalık virgül, UTF-8 BOM). */
export function csvMetni({ sutunlar, satirlar }) {
  const kac = (v) => {
    if (v == null) return ''
    const s = typeof v === 'number' ? String(v).replace('.', ',') : String(v)
    return /[";\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  return [sutunlar, ...satirlar].map((r) => r.map(kac).join(';')).join('\r\n')
}

export function csvIndir(tablo, dosyaAdi = 'veri') {
  const blob = new Blob(['﻿' + csvMetni(tablo)], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = /\.csv$/i.test(dosyaAdi) ? dosyaAdi : `${dosyaAdi}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}


/** Histogram tablo görünümü için yardımcı: [[aralık, sayı, yüzde]] satırları. */
export function histogramTablosu(degerler, { aralik = [0, 100], kova = 10, birim = 'öğrenci' } = {}) {
  const [a, b] = aralik
  const w = (b - a) / kova
  const v = (degerler || []).map(Number).filter((x) => !Number.isNaN(x) && x >= a && x <= b)
  const s = Array(kova).fill(0)
  v.forEach((x) => { s[Math.min(kova - 1, Math.floor((x - a) / w))] += 1 })
  return {
    sutunlar: ['Aralık', `Sayı (${birim})`, 'Yüzde'],
    satirlar: s.map((c, i) => [`${sayi(a + i * w, 1)}–${sayi(a + (i + 1) * w, 1)}`, c, v.length ? `%${sayi((c / v.length) * 100, 1)}` : '—']),
  }
}
