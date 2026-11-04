// [2026-11-04] Kullanıcı kuralı: sistemin güncellenme tarihi gün.ay.yıl saat:dakika:saniye olarak görünmeli.
// Son güncelleme = arayüzün yayın anı (Vite derleme) ile sunucunun yeni sürümle ilk açıldığı andan yenisi.
import { useEffect, useState } from 'react'
import { api } from '../api/client'

/* global __YAYIN_ZAMANI__ */
export const ARAYUZ_YAYIN = typeof __YAYIN_ZAMANI__ !== 'undefined' ? __YAYIN_ZAMANI__ : null

export const tarihSaniye = (z) => (z ? new Date(z).toLocaleString('tr-TR', {
  day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
}) : '—')

let bekleyen = null
export function sistemSurumuGetir() {
  if (!bekleyen) bekleyen = api.sistemSurumu().catch(() => { bekleyen = null; return null })
  return bekleyen
}

export function sonGuncelleme(sunucu) {
  const z = [ARAYUZ_YAYIN, sunucu?.sunucu_guncelleme].filter(Boolean).map((x) => new Date(x).getTime())
  return z.length ? new Date(Math.max(...z)).toISOString() : null
}

export function useSonGuncelleme() {
  const [bilgi, setBilgi] = useState(null)
  useEffect(() => { let canli = true; sistemSurumuGetir().then((b) => canli && setBilgi(b)); return () => { canli = false } }, [])
  return { son: sonGuncelleme(bilgi), bilgi }
}
