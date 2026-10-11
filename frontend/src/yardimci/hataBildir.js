// [2026-10-11] Tarayıcı hatalarını sunucuya bildirir: POST /api/istemci-hata (kimliksiz de çalışır).
// Aynı hata bir sayfa yüklemesinde bir kez, toplamda en çok 10 bildirim; sunucu ayrıca sıkı hız sınırı uygular.
// Gönderim hatası sessizce yutulur (hata bildirimi asla yeni hata üretmesin).

const EN_FAZLA = 10
const gonderilen = new Set()
let sayac = 0

const GURULTU = [
  /ResizeObserver loop/i,
  /^Script error\.?$/i,                 // başka kökenli betik (ayrıntı yok)
  /Non-Error promise rejection captured/i,
  /AbortError/i,
  /Load failed$/i,                      // Safari: kullanıcı sayfadan ayrıldığında iptal edilen fetch
  /Failed to fetch$/i,                  // ağ kesintisi — sunucu hatası değil
  /NetworkError when attempting to fetch/i,
]

function kirp(metin, n) {
  const s = String(metin ?? '')
  return s.length > n ? s.slice(0, n) : s
}

function tokenBul() {
  try {
    return localStorage.getItem('admin_erisim_tokeni') || localStorage.getItem('ogrenci_erisim_tokeni')
      || localStorage.getItem('rehber_erisim_tokeni') || null
  } catch { return null }
}

export function hataBildir(hata, tur = 'error', ek = {}) {
  try {
    const mesaj = kirp(hata?.message || (typeof hata === 'string' ? hata : '') || String(hata), 2000)
    if (!mesaj || GURULTU.some((d) => d.test(mesaj))) return
    // API hataları (ApiHatasi: 4xx/5xx) zaten sunucuda görülüyor — tekrar bildirme
    if (hata && typeof hata === 'object' && 'status' in hata && 'detail' in hata) return
    const yigin = kirp(hata?.stack || '', 8000)
    const anahtar = `${tur}|${mesaj}|${yigin.split('\n')[1] || ''}`
    if (gonderilen.has(anahtar) || sayac >= EN_FAZLA) return
    gonderilen.add(anahtar)
    sayac += 1
    const govde = JSON.stringify({
      mesaj, yigin, tur,
      sayfa: kirp(window.location.pathname, 500),   // sorgu metni (token vb. içerebilir) gönderilmez
      bilesen_yigini: ek.bilesenYigini ? kirp(ek.bilesenYigini, 4000) : undefined,
    })
    const headers = { 'Content-Type': 'application/json' }
    const token = tokenBul()
    if (token) headers.Authorization = `Bearer ${token}`
    fetch('/api/istemci-hata', { method: 'POST', headers, body: govde, keepalive: true }).catch(() => {})
  } catch { /* yoksay */ }
}

let kuruldu = false
export function hataYakalayicilariniKur() {
  if (kuruldu || typeof window === 'undefined') return
  kuruldu = true
  window.addEventListener('error', (e) => {
    // kaynak yükleme hataları (img/script) ErrorEvent değildir; yalnızca betik hataları
    if (e && e.error) hataBildir(e.error, 'error')
    else if (e && e.message) hataBildir({ message: e.message, stack: `${e.filename || ''}:${e.lineno || 0}:${e.colno || 0}` }, 'error')
  })
  window.addEventListener('unhandledrejection', (e) => {
    const r = e?.reason
    hataBildir(r instanceof Error ? r : { message: typeof r === 'string' ? r : JSON.stringify(r)?.slice(0, 500) }, 'unhandledrejection')
  })
}
