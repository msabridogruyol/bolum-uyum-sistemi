import { aktifDil, t as cevirT } from './dil'   // [2026-10-12] çoklu dil
// [2026-10-10] Filiz'in sesi.
// - Konuşma: tarayıcının sesli okuması, YALNIZCA doğal (sinirsel / "Natural", "Online", "Enhanced", Google) bir Türkçe ses varsa.
//   Robotik masaüstü sesleri (ör. Windows "Microsoft Tolga/Seda Desktop") kullanılmaz; o cihazda yalnızca efekt sesleri çalar.
// - Efektler: Web Audio ile üretilen kısa, yumuşak tonlar (dosya yok).
// - Varsayılan kapalı; tarayıcılar ses için bir kullanıcı tıklaması ister, açma düğmesi bunu sağlar.
// - [2026-10-11] Ses açıkken Filiz'in TÜM konuşmaları okunur: balon cümleleri, sayfa mesajları ve sohbet panelindeki cevaplar.

const ANAHTAR = 'filiz_ses'
const DOGAL = /(natural|neural|online|enhanced|premium|geli[sş]mi[sş]|google)/i
const ROBOTIK = /(desktop|espeak|e-speak|festival|pico)/i

export const sesAcikMi = () => { try { return localStorage.getItem(ANAHTAR) === '1' } catch { return false } }
export const sesAyarla = (v) => {
  try { localStorage.setItem(ANAHTAR, v ? '1' : '0') } catch { /* gizli sekme */ }
  // [2026-10-11] Filiz balonu ve sohbet panelleri aynı ayarı paylaşır
  try { window.dispatchEvent(new CustomEvent('filiz-ses', { detail: { acik: !!v } })) } catch { /* yoksay */ }
}

let ses = undefined   // undefined: aranmadı · null: yok · SpeechSynthesisVoice
function sesleriAra() {
  if (typeof window === 'undefined' || !window.speechSynthesis) { ses = null; return null }
  // [2026-10-12] seçili dilin sesi (Türkçe dışı dilde o dilin sesi aranır)
  const kod = aktifDil()
  const turkce = window.speechSynthesis.getVoices().filter((v) => new RegExp(`^${kod}(-|_|$)`, 'i').test(v.lang))
  if (!turkce.length) return undefined   // liste henüz yüklenmemiş olabilir
  const aday = turkce.filter((v) => DOGAL.test(v.name) && !ROBOTIK.test(v.name))
  // sırala: Natural/Neural > Online > Enhanced > Google > diğer
  const puan = (v) => (/(natural|neural)/i.test(v.name) ? 4 : /online/i.test(v.name) ? 3 : /(enhanced|premium|geli[sş]mi[sş])/i.test(v.name) ? 2 : 1)
  ses = aday.sort((a, b) => puan(b) - puan(a))[0] || null
  return ses
}
if (typeof window !== 'undefined' && window.speechSynthesis) {
  sesleriAra()
  window.speechSynthesis.addEventListener?.('voiceschanged', sesleriAra)
}

/** Doğal Türkçe ses var mı? (liste geç yüklenirse kısa süre bekler) */
export function dogalSesVarMi() {
  return new Promise((coz) => {
    if (ses !== undefined) { coz(!!ses); return }
    let n = 0
    const t = window.setInterval(() => {
      n += 1
      const s = sesleriAra()
      if (s !== undefined || n > 15) { window.clearInterval(t); if (s === undefined) ses = null; coz(!!ses) }
    }, 100)
  })
}

const temizle = (m) => String(m || '')
  .replace(/\*\*|__|`|#+\s|^\s*[-•]\s/gm, '')   // markdown işaretleri okunmasın
  .replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}]/gu, '')   // emoji
  .replace(/[“”"]/g, '').replace(/\s+/g, ' ').trim()

// [2026-10-11] Tarayıcılar, kullanıcı sayfaya hiç dokunmadan sesli okumaya izin vermez (sayfa yenilenince ilk selam
// sessiz kalıyordu). Böyle bir durumda son cümle bekletilir ve kullanıcının ilk tıklamasında / tuşunda okunur.
const EN_UZUN = 600   // uzun sohbet cevapları: ilk ~600 karakter (cümle sonunda kesilir)
let bekleyen = null
function etkilesimVarMi() {
  const ua = typeof navigator !== 'undefined' ? navigator.userActivation : null
  return ua ? ua.hasBeenActive : true
}
if (typeof window !== 'undefined') {
  const ilkEtkilesim = () => { if (bekleyen) { const m = bekleyen; bekleyen = null; soyle(m) } }
  window.addEventListener('pointerdown', ilkEtkilesim, true)
  window.addEventListener('keydown', ilkEtkilesim, true)
}
function kisalt(t) {
  if (t.length <= EN_UZUN) return t
  const kes = t.slice(0, EN_UZUN)
  const son = Math.max(kes.lastIndexOf('. '), kes.lastIndexOf('! '), kes.lastIndexOf('? '))
  return son > 200 ? kes.slice(0, son + 1) : kes
}

export function soyle(metin) {
  if (!sesAcikMi()) return false
  if (!ses || !window.speechSynthesis) { efekt('konus'); return false }
  const t = kisalt(temizle(cevirT(metin)))
  if (!t) return false
  if (!etkilesimVarMi()) { bekleyen = t; return false }
  window.speechSynthesis.cancel()
  const u = new SpeechSynthesisUtterance(t)
  u.voice = ses
  u.lang = ses.lang
  u.rate = 1.02
  u.pitch = 1.12
  u.volume = 0.9
  window.speechSynthesis.speak(u)
  return true
}

export function sus() { try { window.speechSynthesis?.cancel() } catch { /* yok */ } }

// ----------------------------------------------------------------------------- efekt sesleri
let ctx = null
function baglam() {
  if (!ctx) {
    const C = window.AudioContext || window.webkitAudioContext
    if (!C) return null
    ctx = new C()
  }
  if (ctx.state === 'suspended') ctx.resume()
  return ctx
}

function ton(c, frekans, bas, sure, { tip = 'sine', ses: hacim = 0.07, kayma = 0 } = {}) {
  const o = c.createOscillator()
  const g = c.createGain()
  o.type = tip
  o.frequency.setValueAtTime(frekans, bas)
  if (kayma) o.frequency.exponentialRampToValueAtTime(frekans * kayma, bas + sure)
  g.gain.setValueAtTime(0.0001, bas)
  g.gain.exponentialRampToValueAtTime(hacim, bas + 0.015)
  g.gain.exponentialRampToValueAtTime(0.0001, bas + sure)
  o.connect(g).connect(c.destination)
  o.start(bas)
  o.stop(bas + sure + 0.02)
}

const EFEKTLER = {
  konus: (c, t) => { ton(c, 660, t, 0.09); ton(c, 880, t + 0.07, 0.12) },
  kalp: (c, t) => { ton(c, 988, t, 0.22, { tip: 'triangle', ses: 0.05 }) },
  zipla: (c, t) => { ton(c, 330, t, 0.22, { kayma: 2.2, ses: 0.06 }) },
  don: (c, t) => { ton(c, 520, t, 0.3, { kayma: 1.5, tip: 'triangle', ses: 0.05 }) },
  kutla: (c, t) => { [523, 659, 784, 1047].forEach((f, i) => ton(c, f, t + i * 0.09, 0.28, { tip: 'triangle', ses: 0.06 })) },
  uyan: (c, t) => { ton(c, 440, t, 0.12); ton(c, 587, t + 0.1, 0.16) },
  ac: (c, t) => { ton(c, 587, t, 0.1); ton(c, 784, t + 0.09, 0.18) },
}

export function efekt(tur, zorla = false) {
  if (!zorla && !sesAcikMi()) return
  try {
    const c = baglam()
    if (!c) return
    ;(EFEKTLER[tur] || EFEKTLER.konus)(c, c.currentTime + 0.01)
  } catch { /* ses desteklenmiyor */ }
}
