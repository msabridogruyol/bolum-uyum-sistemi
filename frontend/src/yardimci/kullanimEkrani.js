// [2026-11-11] Kullanım analizi: adres → hangi menü / alt sekme. Menü adları kenar menüsündekiyle aynıdır (Türkçe kaynak metin;
// arayüz başka dilde olsa da rapor Türkçe ad gösterir). Alt sekme: adresteki ?sekme / ikinci yol parçası; adreste yoksa
// sayfadaki seçili sekmenin (role="tab") adı. Sekme adı çeviri katmanından Türkçe aslıyla okunur (dil.kaynakMetin):
// İngilizce arayüzdeki "Cover letter" de raporda "Ön yazı" satırına yazılır.
import { OKUL_BOLUMLERI } from '../components/yonetim/okulBolumleri'
import { kaynakMetin } from './dil'
import { SUPER_MENU } from '../components/yonetim/superMenu'

const OGRENCI_MENU = [
  ['/katmanlar', 'degerlendirme', 'Değerlendirme'], ['/k5', 'degerlendirme', 'Değerlendirme'],
  ['/bolumler', 'bolumler', 'Bölümler'], ['/karsilastir', 'karsilastir', 'Bölüm karşılaştırma'],
  ['/koclugu', 'koclugu', 'Koçluğum'], ['/profilim', 'profilim', 'Profilim'], ['/is-hayati', 'is-hayati', 'İş Hayatı'],
  ['/tercih', 'tercih', 'Tercihlerim'], ['/gelisim', 'gelisim', 'Gelişim listem'], ['/calisma', 'calisma', 'Çalışmam'],
  ['/netlerim', 'netlerim', 'Net Takibi'], ['/kutuphane', 'kutuphane', 'Kütüphanem'], ['/portfolyo', 'portfolyo', 'Portfolyom'],
  ['/raporlarim', 'raporlarim', 'Raporlarım'], ['/takvim', 'takvim', 'Takvim'], ['/anketler', 'anketler', 'Anketler'],
  ['/kulupler', 'kulupler', 'Kulüplerim'], ['/koclar', 'koclar', 'Eğitim Koçları'], ['/sozluk', 'sozluk', 'Sözlük'],
  ['/hakkinda', 'hakkinda', 'Sistem Hakkında'], ['/profil', 'ayarlar', 'Ayarlar'],
]
const OKUL_AD = Object.fromEntries(OKUL_BOLUMLERI.map((b) => [b.k, b.ad]))
const SUPER_AD = Object.fromEntries(SUPER_MENU.flatMap((g) => g.baglantilar.map(([yol, , ad]) => [yol, ad])))

// Kullanıcının hiç bir menüde sayılmayacağı (oturum açmadan görülen) sayfalar
const ACIK_SAYFA = /^\/(giris|sifremi-unuttum|sifre-sifirla|test-giris)(\/|$)|^\/admin\/(giris|sifremi-unuttum|sifre-sifirla)(\/|$)/

export const kodYap = (s) => String(s || '').toLocaleLowerCase('tr-TR')
  .replace(/ç/g, 'c').replace(/ğ/g, 'g').replace(/ı/g, 'i').replace(/ö/g, 'o').replace(/ş/g, 's').replace(/ü/g, 'u')
  .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60)

const sekmeMetni = (el) => {
  // arayüz başka dilde olsa da Türkçe kaynak ad (rapor her dilde aynı satıra yazar)
  const m = kaynakMetin(el).replace(/^[^\p{L}\p{N}]+/u, '').replace(/\s*\(?\d+\)?\s*$/, '').replace(/\s+/g, ' ').trim()
  return m ? m.slice(0, 120) : null
}

/** Sayfadaki seçili sekmelerin adları, dıştan içe: önce bağlantı sekmeleri (adres değiştiren), sonra sayfa içi
 *  sekmeler (role="tab"). [0] alt sekme, [1] içerik düzeyi için kullanılır. Simge ve sayaç rozeti atılır:
 *  "🔍 Tüm bölümler" → "Tüm bölümler", "Bekleyen (3)" → "Bekleyen". */
export function seciliSekmeAdlari() {
  try {
    const l = [...document.querySelectorAll('.pg .sayfa-sekmeleri [aria-current="page"], .pg .sayfa-sekmeleri .aktif'),
      ...document.querySelectorAll('.pg [role="tab"][aria-selected="true"], main [role="tab"][aria-selected="true"]')]
    return [...new Set(l)].map(sekmeMetni).filter(Boolean)
  } catch { return [] }
}

/** Sayfanın kendisinin bildirdiği içerik (ör. açık ders): <KullanimDetayi kod ad />. En içteki geçerlidir. */
export function isaretliDetay() {
  try {
    const l = document.querySelectorAll('[data-kullanim-detay]')
    const el = l[l.length - 1]
    const kod = el && kodYap(el.getAttribute('data-kullanim-detay'))
    return kod ? { kod, ad: (el.getAttribute('data-kullanim-detay-ad') || '').slice(0, 120) || null } : null
  } catch { return null }
}

/**
 * Adres → { kapsam: 'ogrenci'|'admin', menu_kod, menu_ad, alt_kod, alt_ad } ya da null (sayılmaz).
 * rol: yönetim jetonundaki rol ('okul_yetkilisi' | 'super_admin').
 */
export function ekranCoz(pathname, search, rol) {
  if (ACIK_SAYFA.test(pathname)) return null
  const q = new URLSearchParams(search || '')
  const parca = pathname.split('/').filter(Boolean)
  if (parca[0] === 'admin') {
    if (!rol) return null
    if (parca[1] === 'okul') {
      const sekme = kodYap(q.get('sekme') || 'ozet') || 'ozet'
      const ogrenci = sekme === 'ogrenciler' && q.get('ogrenci')
      if (rol === 'okul_yetkilisi') {
        return { kapsam: 'admin', menu_kod: sekme, menu_ad: OKUL_AD[sekme] || sekme, alt_kod: ogrenci ? 'ogrenci-detayi' : '', alt_ad: ogrenci ? 'Öğrenci detayı' : null }
      }
      const harici = parca[2] === '0'
      return { kapsam: 'admin', menu_kod: harici ? 'okul-harici' : 'okul-paneli', menu_ad: harici ? 'Okul Harici Öğrenciler' : 'Okul paneli',
               alt_kod: ogrenci ? 'ogrenci-detayi' : sekme, alt_ad: ogrenci ? 'Öğrenci detayı' : (OKUL_AD[sekme] || sekme) }
    }
    if (parca[1] === 'sss') return { kapsam: 'admin', menu_kod: 'sss', menu_ad: rol === 'okul_yetkilisi' ? 'Sistem Hakkında & SSS' : 'Okul Yetkilisi SSS', alt_kod: '', alt_ad: null }
    const yol = parca.length > 1 ? `/admin/${parca[1]}` : '/admin'
    const kod = parca[1] ? kodYap(parca[1]) : 'kontrol-paneli'
    return { kapsam: 'admin', menu_kod: kod, menu_ad: SUPER_AD[yol] || (parca[1] ? parca[1].replace(/-/g, ' ') : 'Kontrol Paneli'),
             alt_kod: kodYap(q.get('sekme') || parca[2] || ''), alt_ad: null }
  }
  if (pathname === '/' || pathname === '') return { kapsam: 'ogrenci', menu_kod: 'ana-sayfa', menu_ad: 'Ana Sayfa', alt_kod: '', alt_ad: null }
  const sekme = q.get('sekme')
  if (parca[0] === 'koclugu' && sekme === 'karsilastirma') return { kapsam: 'ogrenci', menu_kod: 'sen-ve-bolumun', menu_ad: 'Sen ve Bölümün', alt_kod: '', alt_ad: null }
  const m = OGRENCI_MENU.find(([y]) => pathname === y || pathname.startsWith(`${y}/`))
  const menu_kod = m ? m[1] : kodYap(parca[0]) || 'diger'
  return { kapsam: 'ogrenci', menu_kod, menu_ad: m ? m[2] : parca[0], alt_kod: kodYap(sekme || parca[1] || ''), alt_ad: null }
}
