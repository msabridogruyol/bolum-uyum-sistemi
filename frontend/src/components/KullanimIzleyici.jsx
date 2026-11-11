// [2026-11-11] Kullanım süresi ölçümü (süper admin › Kullanım Analizi). Görünmez; tüm uygulamada bir kez çalışır.
// Aktif süre: sekme ekranda VE kişi son 2 dakikada dokundu / tıkladı / yazdı / kaydırdı. Açık süre: sekme ekranda.
// Süreler menü ve alt sekme başına biriktirilir; dakikada bir ve sekme gizlenirken / kapanırken sunucuya gönderilir.
// Oturum: aynı sekmede 30 dakikadan uzun etkinlik arası olursa yeni oturum başlar. Ad, puan ya da içerik gönderilmez.
import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { ekranCoz, isaretliDetay, kodYap, seciliSekmeAdlari } from '../yardimci/kullanimEkrani'

const TIK_MS = 5000
const BOSTA_MS = 2 * 60 * 1000
const GONDER_MS = 60 * 1000
const OTURUM_ARA_MS = 30 * 60 * 1000
const TAMPON_EN_FAZLA = 80

const d = {
  ekran: null, tampon: new Map(), sonEtkilesim: Date.now(), sonTik: Date.now(), sonGonderim: Date.now(),
  oturum: {}, baslatildi: false, cihaz: null, ziyaretBekliyor: false, sonAnahtar: null,
}

function jeton(kapsam) {
  try { return localStorage.getItem(`${kapsam}_erisim_tokeni`) } catch { return null }
}
function yuk(t) {
  try { return JSON.parse(atob(t.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))) } catch { return null }
}
function rastgeleKimlik() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID()
  const b = (window.crypto || {}).getRandomValues ? window.crypto.getRandomValues(new Uint8Array(16)) : Uint8Array.from({ length: 16 }, () => Math.random() * 256)
  b[6] = (b[6] & 0x0f) | 0x40; b[8] = (b[8] & 0x3f) | 0x80
  const h = [...b].map((x) => x.toString(16).padStart(2, '0')).join('')
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`
}
function cihaz() {
  try {
    const kaba = window.matchMedia('(pointer: coarse)').matches
    const kisa = Math.min(window.screen.width, window.screen.height)
    if (kaba && kisa < 600) return 'mobil'
    if (kaba && kisa < 1100) return 'tablet'
    return 'masaustu'
  } catch { return null }
}

/** Kişinin bu sekmedeki oturum kimliği; 30 dk'dan uzun etkinlik arası ya da başka kişi → yeni oturum.
 *  dokun: kişi şu an etkin (oturumun son etkinlik zamanı ilerler); etkin değilken açık süre mevcut oturuma yazılır. */
function oturumKimligi(kapsam, kisi, simdi, dokun) {
  const anahtar = `kullanim_oturum_${kapsam}`
  let o = d.oturum[kapsam]
  if (!o) { try { o = JSON.parse(sessionStorage.getItem(anahtar) || 'null') } catch { o = null } }
  if (!o || o.kisi !== kisi || (dokun && simdi - o.son > OTURUM_ARA_MS)) o = { id: rastgeleKimlik(), kisi, son: simdi }
  if (dokun) o.son = simdi
  d.oturum[kapsam] = o
  try { sessionStorage.setItem(anahtar, JSON.stringify(o)) } catch { /* gizli sekme */ }
  return o.id
}

function kayit(e) {
  const k = `${e.kapsam}|${e.oturum}|${e.menu_kod}|${e.alt_kod}|${e.detay_kod || ''}`
  let r = d.tampon.get(k)
  if (!r) {
    if (d.tampon.size >= TAMPON_EN_FAZLA) return null
    r = { kapsam: e.kapsam, oturum: e.oturum, menu_kod: e.menu_kod, menu_ad: e.menu_ad, alt_kod: e.alt_kod, alt_ad: e.alt_ad,
          detay_kod: e.detay_kod || '', detay_ad: e.detay_ad || null, aktif: 0, acik: 0, ziyaret: 0 }
    d.tampon.set(k, r)
  }
  if (!r.alt_ad && e.alt_ad) r.alt_ad = e.alt_ad
  if (!r.detay_ad && e.detay_ad) r.detay_ad = e.detay_ad
  return r
}

/** Adresle gelen ekranın kimliği + adreste alt sekme yoksa sayfadaki seçili sekme (Türkçe aslıyla, her dilde). */
function guncelEkran(simdi, dokun = true) {
  const e = d.ekran
  if (!e) return null
  const t = jeton(e.kapsam)
  const p = t && yuk(t)
  if (!p?.sub) return null
  // Üç düzey: menü (adres) › alt sekme (adres ya da sayfadaki ilk seçili sekme) › içerik (sayfanın bildirdiği içerik,
  // yoksa sayfadaki ikinci seçili sekme). Sekme adları çeviriden önceki Türkçe aslıyla okunur (dil.kaynakMetin).
  let { alt_kod, alt_ad } = e
  let detay_kod = '', detay_ad = null
  const sekmeler = seciliSekmeAdlari()   // Türkçe kaynak adlar: arayüz dili fark etmez
  if (sekmeler[0] && !alt_kod) { alt_kod = kodYap(sekmeler[0]); alt_ad = sekmeler[0] }
  else if (sekmeler[0] && !alt_ad) alt_ad = sekmeler[0]   // adresteki sekmenin ekrandaki adı
  const isaret = isaretliDetay()
  if (isaret) { detay_kod = isaret.kod; detay_ad = isaret.ad }
  else if (sekmeler[1]) { detay_kod = kodYap(sekmeler[1]); detay_ad = sekmeler[1] }
  if (!alt_kod) { detay_kod = ''; detay_ad = null }
  return { ...e, alt_kod: alt_kod || '', alt_ad, detay_kod, detay_ad, oturum: oturumKimligi(e.kapsam, p.sub, simdi, dokun) }
}

function gonder(kapanis = false) {
  d.sonGonderim = Date.now()
  const gruplar = new Map()
  for (const [k, r] of d.tampon) {
    const aktif = Math.floor(r.aktif / 1000), acik = Math.floor(r.acik / 1000)
    if (!aktif && !acik && !r.ziyaret) continue
    const g = `${r.kapsam}|${r.oturum}`
    if (!gruplar.has(g)) gruplar.set(g, { kapsam: r.kapsam, oturum: r.oturum, kayitlar: [], anahtarlar: [] })
    gruplar.get(g).kayitlar.push({ menu_kod: r.menu_kod, menu_ad: r.menu_ad || null, alt_kod: r.alt_kod || '', alt_ad: r.alt_ad || null,
      detay_kod: r.detay_kod || '', detay_ad: r.detay_ad || null,
      aktif_sn: Math.min(aktif, 3600), acik_sn: Math.min(Math.max(acik, aktif), 3600), ziyaret: r.ziyaret })
    gruplar.get(g).anahtarlar.push([k, aktif * 1000, acik * 1000, r.ziyaret])
  }
  for (const g of gruplar.values()) {
    const t = jeton(g.kapsam)
    if (!t) continue
    // gönderilen kısım tampondan düşülür (saniye altı artık kalır); başarısız olursa geri eklenir
    for (const [k, a, c, z] of g.anahtarlar) { const r = d.tampon.get(k); if (r) { r.aktif -= a; r.acik -= c; r.ziyaret -= z } }
    const geriAl = () => {
      for (const [k, a, c, z] of g.anahtarlar) {
        const r = d.tampon.get(k)
        if (r) { r.aktif += a; r.acik += c; r.ziyaret += z }
      }
    }
    try {
      fetch(`/api/${g.kapsam === 'admin' ? 'yonetim' : 'ogrenci'}/kullanim`, {
        method: 'POST', keepalive: kapanis,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}` },
        body: JSON.stringify({ oturum_id: g.oturum, cihaz: d.cihaz, kayitlar: g.kayitlar }),
      }).then((y) => { if (!y.ok && y.status !== 422 && y.status !== 403) geriAl() }).catch(geriAl)
    } catch { geriAl() }
  }
  // boşalan satırları at (ekrandaki satır kalır)
  for (const [k, r] of d.tampon) if (r.aktif < 1000 && r.acik < 1000 && !r.ziyaret) d.tampon.delete(k)
}

function tik() {
  const simdi = Date.now()
  let dt = simdi - d.sonTik
  d.sonTik = simdi
  if (dt > TIK_MS * 3) dt = TIK_MS   // bilgisayar uyudu / zamanlayıcı kısıldı: aradaki boşluk sayılmaz
  if (document.visibilityState === 'visible') {
    const aktifMi = simdi - d.sonEtkilesim < BOSTA_MS
    const e = guncelEkran(simdi, aktifMi)
    const r = e && kayit(e)
    if (r) {
      r.acik += dt
      if (aktifMi) r.aktif += dt
      // ziyaret: menüye girildi ya da sayfa içinde başka sekmeye geçildi (sekme adresle değil sayfadan okunuyorsa)
      const anahtar = `${e.kapsam}|${e.menu_kod}|${e.alt_kod}|${e.detay_kod}`
      if (d.ziyaretBekliyor || (d.sonAnahtar && d.sonAnahtar !== anahtar)) r.ziyaret += 1
      d.ziyaretBekliyor = false
      d.sonAnahtar = anahtar
    }
  }
  if (simdi - d.sonGonderim >= GONDER_MS) gonder()
}

function baslat() {
  if (d.baslatildi) return
  d.baslatildi = true
  d.cihaz = cihaz()   // sayfa kapanırken (pagehide) ortam sorguları güvenilir değil: baştan ve boyut değişince ölçülür
  window.addEventListener('resize', () => { d.cihaz = cihaz() }, { passive: true })
  const etkin = () => { d.sonEtkilesim = Date.now() }
  for (const o of ['pointerdown', 'keydown', 'wheel', 'touchstart', 'mousemove', 'scroll', 'input']) {
    window.addEventListener(o, etkin, { passive: true, capture: true })
  }
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') { tik(); gonder(true) } else { d.sonTik = Date.now(); etkin() }
  })
  window.addEventListener('pagehide', () => { tik(); gonder(true) })
  setInterval(tik, TIK_MS)
}

export default function KullanimIzleyici() {
  const konum = useLocation()
  useEffect(() => { baslat() }, [])
  useEffect(() => {
    const admin = konum.pathname.startsWith('/admin')
    const t = jeton(admin ? 'admin' : 'ogrenci')
    const rol = admin ? yuk(t || '')?.rol : null
    tik()   // önceki ekranın süresi kapanır
    const yeni = t ? ekranCoz(konum.pathname, konum.search, rol) : null
    const eski = d.ekran
    d.ekran = yeni
    if (yeni && (!eski || eski.menu_kod !== yeni.menu_kod || eski.alt_kod !== yeni.alt_kod || eski.kapsam !== yeni.kapsam)
        && document.visibilityState === 'visible') {
      d.ziyaretBekliyor = true   // sayfa çizilince (sekme adı okunabilince) ilk tikte yazılır
      d.sonAnahtar = null
      const z = setTimeout(tik, 1500)
      return () => clearTimeout(z)
    }
  }, [konum.pathname, konum.search])
  return null
}
