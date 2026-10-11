// [2026-10-11] Yeni sürüm yayınlandığında açık kalan eski sayfa, artık sunucuda olmayan eski parça dosyalarını
// (ör. AdminGirisSayfasi-XXXX.js) istiyor ve "Failed to fetch dynamically imported module" hatası alıyordu.
// Çözüm: bu hata gelince sayfa BİR KEZ kendiliğinden yenilenir ve yeni sürüm yüklenir.
// Sonsuz yenileme olmasın diye 30 saniye içinde ikinci kez yenilenmez; o durumda hata normal şekilde gösterilir.
import { lazy } from 'react'

const ANAHTAR = 'surum_yenileme_zamani'

export function surumHatasiMi(hata) {
  const m = String(hata?.message || hata || '')
  return /Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module|Unable to preload CSS|ChunkLoadError|Loading chunk \d+ failed/i.test(m)
}

export function yeniSurumIcinYenile() {
  try {
    const son = Number(sessionStorage.getItem(ANAHTAR) || 0)
    if (Date.now() - son < 30_000) return false
    sessionStorage.setItem(ANAHTAR, String(Date.now()))
  } catch { /* depolama yoksa yine de bir kez dene */ }
  window.location.reload()
  return true
}

// React.lazy yerine: parça yüklenemezse sayfayı yeniler (yenilenirken boş bekler)
export function tembel(yukleyici) {
  return lazy(() => yukleyici().catch((hata) => {
    if (surumHatasiMi(hata) && yeniSurumIcinYenile()) return new Promise(() => {})
    throw hata
  }))
}
