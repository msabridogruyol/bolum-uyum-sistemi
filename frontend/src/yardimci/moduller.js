// [2026-10-10] Paketler: öğrencinin okulunda açık modüller. Tek istek, bellekte saklanır; tüm bileşenler paylaşır.
// Yüklenene kadar (null) her şey açık sayılır — 'Tam' paketli okullarda menü titremesin; sunucu zaten 403 ile korur.
import { createContext, useContext, useEffect, useState } from 'react'
import { api } from '../api/client'

let onbellek = null
let istek = null
let hataOldu = false   // [2026-11-04] liste alınamadıysa "hazır" sayılır ve her şey açık kabul edilir (eski davranış)
const dinleyiciler = new Set()
const bildir = () => dinleyiciler.forEach((f) => f({ m: onbellek, hata: hataOldu }))

export function modulleriYukle(zorla = false) {
  if (zorla) { onbellek = null; istek = null; hataOldu = false }
  if (!istek) {
    istek = api.ogrenciModulleri()
      .then((v) => { onbellek = new Set(v.moduller || []); hataOldu = false })
      .catch(() => { istek = null; hataOldu = true })   // hata: bir sonraki çağrıda yeniden dene; o ana kadar her şey açık
      .finally(bildir)
  }
  return istek
}

// Yüklendikten sonra eşzamanlı sorgu (yüklenemediyse açık sayılır)
export const modulAcikMi = (kod) => !onbellek || onbellek.has(kod)

export function modulleriTemizle() { onbellek = null; istek = null; hataOldu = false }

// Dönen fonksiyon: acik(kod) → modül açık mı. acik.hazir → paket listesi geldi mi (ya da alınamadı mı).
// [2026-11-04] Ekran denetimi: liste gelene kadar her şey "açık" sayıldığından Temel/Gelişim paketli öğrencinin her sayfası
// kapalı modüllerin uçlarını çağırıp 403 alıyordu. Modüle bağlı istekler ve sayfalar acik.hazir olduktan sonra çalışır.
export function useModuller() {
  const [d, setD] = useState({ m: onbellek, hata: hataOldu })
  useEffect(() => {
    dinleyiciler.add(setD)
    if (!onbellek) modulleriYukle()
    else setD({ m: onbellek, hata: false })
    return () => dinleyiciler.delete(setD)
  }, [])
  const acik = (kod) => !d.m || d.m.has(kod)
  acik.hazir = !!d.m || d.hata
  return acik
}

// Öğrenci sayfa yolu → gereken modül
export const YOL_MODULU = {
  '/koclugu': 'kocluk', '/gelisim': 'kocluk', '/gorevler': 'kocluk', '/netlerim': 'net_takibi', '/kutuphane': 'kutuphane',
  '/takvim': 'takvim', '/calisma': 'calisma', '/portfolyo': 'portfolyo', '/anketler': 'anketler', '/tercih': 'tercih', '/raporlarim': 'ogrenci_raporlari', '/kulupler': 'kulupler', '/koclar': 'egitim_koclari',
  '/is-hayati': 'is_hayati',
}

export const MODUL_ADI = {
  kocluk: 'Kişisel Koçluk', takvim: 'Takvim', kutuphane: 'Kütüphane', kulupler: 'Kulüpler', filiz: 'Filiz',
  net_takibi: 'Net Takibi', akran: 'Şube ve Akran Analizi', egitim_koclari: 'Eğitim Koçları', ogrenci_raporlari: 'Raporlarım', rehberlik: 'Rehberlik', calisma: 'Çalışmam', portfolyo: 'Portfolyom', anketler: 'Anketler', tercih: 'Tercihlerim', mezun_takibi: 'Mezun takibi', gelismis_raporlar: 'Gelişmiş Raporlar', is_hayati: 'İş Hayatı',
}

// Yönetim tarafı: okul panelinde açık okulun modülleri (okul_ozeti.moduller). Sağlayıcı yoksa her şey açık.
export const OkulModulleriContext = createContext(null)
export function useOkulModulleri() {
  const m = useContext(OkulModulleriContext)
  return (kod) => !kod || !m || m.includes(kod)
}
