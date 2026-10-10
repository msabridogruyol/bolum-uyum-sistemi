// [2026-10-10] Paketler: öğrencinin okulunda açık modüller. Tek istek, bellekte saklanır; tüm bileşenler paylaşır.
// Yüklenene kadar (null) her şey açık sayılır — 'Tam' paketli okullarda menü titremesin; sunucu zaten 403 ile korur.
import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

let onbellek = null
let istek = null
const dinleyiciler = new Set()

export function modulleriYukle(zorla = false) {
  if (zorla) { onbellek = null; istek = null }
  if (!istek) {
    istek = api.ogrenciModulleri()
      .then((v) => { onbellek = new Set(v.moduller || []) })
      .catch(() => { istek = null })   // hata: bir sonraki çağrıda yeniden dene; o ana kadar her şey açık
      .finally(() => dinleyiciler.forEach((f) => f(onbellek)))
  }
  return istek
}

// Yüklendikten sonra eşzamanlı sorgu (yüklenemediyse açık sayılır)
export const modulAcikMi = (kod) => !onbellek || onbellek.has(kod)

export function modulleriTemizle() { onbellek = null; istek = null }

export function useModuller() {
  const [m, setM] = useState(onbellek)
  useEffect(() => {
    dinleyiciler.add(setM)
    if (!onbellek) modulleriYukle()
    else setM(onbellek)
    return () => dinleyiciler.delete(setM)
  }, [])
  return (kod) => !m || m.has(kod)
}

// Öğrenci sayfa yolu → gereken modül
export const YOL_MODULU = {
  '/koclugu': 'kocluk', '/gorevler': 'kocluk', '/netlerim': 'net_takibi', '/kutuphane': 'kutuphane',
  '/takvim': 'takvim', '/calisma': 'calisma', '/raporlarim': 'ogrenci_raporlari', '/kulupler': 'kulupler', '/koclar': 'egitim_koclari',
}

export const MODUL_ADI = {
  kocluk: 'Kişisel Koçluk', takvim: 'Takvim', kutuphane: 'Kütüphane', kulupler: 'Kulüpler', filiz: 'Filiz',
  net_takibi: 'Net Takibi', akran: 'Şube ve Akran Analizi', egitim_koclari: 'Eğitim Koçları', ogrenci_raporlari: 'Raporlarım', rehberlik: 'Rehberlik', calisma: 'Çalışmam', gelismis_raporlar: 'Gelişmiş Raporlar',
}

// Yönetim tarafı: okul panelinde açık okulun modülleri (okul_ozeti.moduller). Sağlayıcı yoksa her şey açık.
export const OkulModulleriContext = createContext(null)
export function useOkulModulleri() {
  const m = useContext(OkulModulleriContext)
  return (kod) => !kod || !m || m.includes(kod)
}
