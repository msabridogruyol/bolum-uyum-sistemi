// [2026-10-12] Çoklu dil — ekran çeviri katmanı.
// Yöntem: Türkçe arayüz metinleri kaynak koddan çıkarılıp (scripts/ceviri) dil paketlerine çevrildi: src/dil/<kod>.json = {"Türkçe": "çeviri"}.
// Türkçe dışı bir dil seçiliyse sayfadaki metin düğümleri ve placeholder/title/aria-label/alt öznitelikleri paketten çevrilir;
// React metni güncelledikçe MutationObserver yeniden çevirir. Bileşen kodu değişmeden tüm ekranlar çevrilir.
//  - Kalıplar: "{0} öğrenci" gibi değişken içeren metinler; değişken kısmı (ör. bölüm adı) ayrıca paketten çevrilir.
//  - Pakette olmayan metin Türkçe kalır (öğrenci adı, okul adı, kullanıcı yazıları hiç değiştirilmez).
//  - Bölüm açıklaması / sözlük gibi uzun içerik: paketten bulunamazsa sunucuya sorulur (POST /api/ceviri/icerik).
//    Sunucu yalnızca kendi içerik havuzunda bulunan metinleri çevirir (kişisel veri yapay zekâya gitmez), sonucu saklar.
//  - translate="no" ya da .ceviri-yok sınıfı olan bölgeler, input/textarea değerleri çevrilmez.
// Dil kişiye özeldir: localStorage 'dil' + hesap ayarı (giriş sonrası sunucudaki tercih uygulanır).

export const DILLER = [
  { kod: 'tr', ad: 'Türkçe', bayrak: '🇹🇷' },
  { kod: 'en', ad: 'English', bayrak: '🇬🇧' },
  { kod: 'de', ad: 'Deutsch', bayrak: '🇩🇪' },
  { kod: 'fr', ad: 'Français', bayrak: '🇫🇷' },
  { kod: 'ru', ad: 'Русский', bayrak: '🇷🇺' },
  { kod: 'es', ad: 'Español', bayrak: '🇪🇸' },
  { kod: 'it', ad: 'Italiano', bayrak: '🇮🇹' },
  { kod: 'ar', ad: 'العربية', bayrak: '🇸🇦' },
  { kod: 'zh', ad: '中文（简体）', bayrak: '🇨🇳' },
  { kod: 'hi', ad: 'हिन्दी', bayrak: '🇮🇳' },
  { kod: 'uz', ad: 'Oʻzbekcha', bayrak: '🇺🇿' },
  { kod: 'az', ad: 'Azərbaycanca', bayrak: '🇦🇿' },
  { kod: 'ko', ad: '한국어', bayrak: '🇰🇷' },
]
const SAG_SOL = new Set(['ar'])
const ANAHTAR = 'dil'
// Paketler ayrı dosya olarak yayımlanır (yalnızca seçilen dil indirilir; JSON.parse büyük JS nesnesinden hızlıdır)
const PAKETLER = import.meta.glob('../dil/*.json', { query: '?url', import: 'default' })

export function aktifDil() {
  try {
    const d = localStorage.getItem(ANAHTAR)
    return DILLER.some((x) => x.kod === d) ? d : 'tr'
  } catch { return 'tr' }
}

let paket = null            // Map tr → çeviri
let buyukHarf = null        // Map TÜRKÇE BÜYÜK HARF → çeviri (bölüm adları veritabanında büyük harfle durur, ekranda düzeltilir)
let kaliplar = []           // [{ rx, ceviri, parca }]
const bellek = new Map()    // tr → çeviri | null
const sunucuBekleyen = new Set()
const sunucuSorulan = new Set()
let dil = 'tr'

const normal = (s) => s.replace(/\s+/g, ' ').trim()
const kacis = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

function kalipHazirla(tr, ceviri) {
  const parcalar = tr.split(/\{\d+\}/)
  const sira = [...tr.matchAll(/\{(\d+)\}/g)].map((m) => Number(m[1]))
  const harf = parcalar.join('')
  if (harf.replace(/[^\p{L}]/gu, '').length < 2) return null
  const rx = new RegExp('^' + parcalar.map(kacis).join('(.+?)') + '$', 's')
  const enUzun = parcalar.reduce((a, b) => (b.length > a.length ? b : a), '')
  return { rx, ceviri, sira, enUzun, agirlik: (harf.match(/\p{L}/gu) || []).length }
}

function yukle(veri) {
  paket = new Map()
  buyukHarf = new Map()
  kaliplar = []
  for (const [tr, c] of Object.entries(veri)) {
    if (/\{\d+\}/.test(tr)) { const k = kalipHazirla(tr, c); if (k) kaliplar.push(k) }
    else { paket.set(tr, c); const u = tr.toLocaleUpperCase('tr'); if (!buyukHarf.has(u)) buyukHarf.set(u, c) }
  }
  // Ekranda parantezli açıklaması kısaltılan adlar: "İnsanlarla çalışma (dışadönüklük)" → "İnsanlarla çalışma"
  for (const [tr, c] of [...paket]) {
    const m = /^(.{3,}?)\s*\([^()]{2,40}\)$/.exec(tr), n = /^(.{2,}?)\s*\([^()]{2,60}\)$/.exec(c)
    if (m && n && !paket.has(m[1])) { paket.set(m[1], n[1]); const u = m[1].toLocaleUpperCase('tr'); if (!buyukHarf.has(u)) buyukHarf.set(u, n[1]) }
  }
  kaliplar.sort((a, b) => b.agirlik - a.agirlik)
}

// "Maden Mühendisliği" ↔ "MADEN MÜHENDİSLİĞİ": büyük/küçük harf farkıyla eşleşirse çeviriyi kaynağın harf düzenine uydur
const KUCUK_KELIME = new Set(['and', 'of', 'the', 'in', 'for', 'und', 'für', 'der', 'die', 'das', 'et', 'de', 'des', 'du', 'la', 'le', 'les', 'en', 'y', 'e', 'di', 'del', 'della', 'a', 'à', 'et', 'und'])
function harfDuzeniyle(s) {
  if (!buyukHarf || s.length > 160) return null
  const c = buyukHarf.get(s.toLocaleUpperCase('tr'))
  if (c == null) return null
  if (s === s.toLocaleUpperCase('tr')) return c.toLocaleUpperCase(dil)
  if (c !== c.toLocaleUpperCase(dil)) {
    // Kaynak büyük harfle başlıyor, çeviri küçükle: ilk harfi büyüt ("iş birliği…" → ekranda "İş birliği…")
    const ilkBuyuk = s.charAt(0) !== s.charAt(0).toLocaleLowerCase('tr')
    return ilkBuyuk ? c.charAt(0).toLocaleUpperCase(dil) + c.slice(1) : c
  }
  const k = c.toLocaleLowerCase(dil)
  if (dil === 'ru') return k.charAt(0).toLocaleUpperCase(dil) + k.slice(1)
  return k.split(' ').map((w, i) => (i > 0 && KUCUK_KELIME.has(w) ? w : w.charAt(0).toLocaleUpperCase(dil) + w.slice(1))).join(' ')
}

// "{0} çalışma" gibi kısa kalıplar ilgisiz metinlere ("İnsanlarla çalışma") yapışmasın: kalıbın sabit kısmı metnin
// harflerinin yarısından azını kapsıyorsa, değişken kısım sayı / bilinen bir terim / ad gibi görünmelidir.
function kalipGuvenilir(k, s, degerler, cevrilmis) {
  const harf = (x) => (x.match(/\p{L}/gu) || []).length
  const adGibi = (t) => /^\p{Lu}[\p{L}'’-]*(\s+\p{Lu}[\p{L}'’-]*)*[.!?]?$/u.test(t)
  const yuksek = harf(s) === 0 || k.agirlik / Math.max(1, harf(s)) >= 0.5
  return degerler.every((t, i) => {
    if (!/\p{L}/u.test(t) || cevrilmis[i] != null) return true
    // Çevrilemeyen değişken (ad, kullanıcı yazısı): kalıp metnin çoğunu kapsıyorsa kabul; azını kapsıyorsa ad gibi olmalı
    return yuksek || adGibi(t)
  })
}

// Bir metnin çevirisi (bulunamazsa null). Baş/son boşluklar korunur.
// Türkçede yüzde işareti sayıdan önce gelir ("%88"); diğer dillerde sonra ("88%")
const YUZDE_RX = /%(\d+(?:[.,]\d+)?)/g
const yuzdeDuzelt = (s) => s.replace(YUZDE_RX, (_, n) => (dil === 'fr' || dil === 'de' ? `${n} %` : `${n}%`))

export function cevir(ham) {
  if (!paket || ham == null) return null
  const s = normal(String(ham))
  const c = cevirIc(s, 0)
  if (c != null) return c
  // Harfsiz kısa metinler ("%0", "%61") ve çevrilemeyen metindeki yüzdeler
  if (/%\d/.test(s) && !/\p{L}{2,}/u.test(s)) return yuzdeDuzelt(s)
  return null
}

function cevirIc(s, derinlik) {
  if (!s || !/\p{L}/u.test(s)) return null
  if (bellek.has(s)) return bellek.get(s)
  let sonuc = paket.get(s) ?? harfDuzeniyle(s)
  // Türkçe ay adlı tarihler ("19 Haziran 2027") seçili dilde yazılır
  if (sonuc == null && AY_RX.test(s)) {
    const d = tarihleriCevir(s)
    if (d !== s) sonuc = cevirIc(d, derinlik + 1) ?? d
    else if (AY_RX.exec(s)?.[0] === s) sonuc = s   // ay adı hedef dilde de aynı yazılıyor ("Mar")
  }
  if (sonuc == null && derinlik < 3) sonuc = kaliptan(s, derinlik)
  // Birleştirilmiş cümleler ("Merhaba Elif! " + "Bugün 3 konu öne çıkıyor."): her cümle ayrı çevrilir
  if (sonuc == null && derinlik < 2) {
    // Her cümle sınırında "baş + kalan" olarak dene (kalan kendi içinde yine bölünebilir; "Bugün … çıkıyor. 🌱" bütün kalır)
    const sinirlar = [...s.matchAll(/(?<=[.!?…:])\s+(?=\S)/gu)].map((m) => [m.index, m.index + m[0].length])
    for (const [a, b] of sinirlar.slice(0, 6)) {
      const bas = s.slice(0, a), kalan = s.slice(b)
      const cb = cevirIc(bas, derinlik + 1) ?? (/\p{L}/u.test(bas) ? null : bas)
      if (cb == null) continue
      const ck = cevirIc(kalan, derinlik + 1) ?? (/\p{L}/u.test(kalan) ? null : kalan)
      if (ck != null) { sonuc = cb + ' ' + ck; break }
    }
  }
  // Baştaki / sondaki emoji ve işaretler: "🎁 Tahmin yerine …" → "🎁 " + çeviri
  if (sonuc == null) {
    const m = /^([^\p{L}\d"“'(«]+)?(.*?)([^\p{L}\d.!?…)"”'»]+)?$/su.exec(s)
    if (m && (m[1] || m[3]) && m[2] && m[2] !== s) {
      const ic = cevirIc(m[2], derinlik + 1)
      if (ic != null) sonuc = (m[1] || '') + ic + (m[3] || '')
    }
  }
  // Sonda sayı: "Temel Matematik 23,25" → çeviri + " 23,25"
  if (sonuc == null) {
    const m = /^(.*\p{L}[^\d]*?)(\s*\([^\p{L}()]*\)|\s+[\d.,%+\-–/]+)$/u.exec(s)
    if (m) { const ic = cevirIc(m[1], derinlik + 1); if (ic != null) sonuc = ic + yuzdeDuzelt(m[2]) }
  }
  // "48 yanıt", "2 görüşme": sayı + tek kelime (birim kalıbı yoksa kelimenin kendisi çevrilir)
  if (sonuc == null) {
    const m = /^([\d.,]+)\s+(\p{L}+)$/u.exec(s)
    if (m) { const ic = cevirIc(m[2], derinlik + 1); if (ic != null) sonuc = m[1] + ' ' + ic }
  }
  // Başta sınav / katman kodu: "TYT Temel Matematik", "K1 Değerler: …" → kod + çeviri
  if (sonuc == null) {
    const m = /^([A-ZÇĞİÖŞÜ]{1,4}\d?(?:-\d)?)\s+(.*\p{Ll}.*)$/u.exec(s)
    if (m) { const ic = cevirIc(m[2], derinlik + 1); if (ic != null) sonuc = m[1] + ' ' + ic }
  }
  // Liste gibi birleştirilmiş metinler: "A · B" (ad gibi parçalar olduğu gibi kalır), son çare "A, B" (her parça çevrilmeli)
  if (sonuc == null && derinlik < 2) sonuc = parcalarla(s, ' · ', derinlik, true) ?? parcalarla(s, ', ', derinlik, false)
  if (bellek.size > 20000) bellek.clear()
  // Derin özyinelemede bazı yollar kapalı olduğundan "bulunamadı" yalnızca en üst düzeyde hatırlanır
  if (sonuc != null || derinlik === 0) bellek.set(s, sonuc)
  return sonuc
}

const AYLAR = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
const AY_KISA = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const AY_ADI = `(${AYLAR.join('|')}|${AY_KISA.join('|')})`
// "19 Haziran 2027", "24 Ağu", "Mar 2026", tek başına "Eyl" (grafik eksenleri)
const AY_RX = new RegExp(`(?<![\\p{L}\\d])(?:(\\d{1,2}) )?${AY_ADI}(?: (\\d{4}|\\d{2}(?!\\d)))?(?![\\p{L}])`, 'u')
function ayNo(ad) { const i = AYLAR.indexOf(ad); return i >= 0 ? i : AY_KISA.indexOf(ad) }
function tarihleriCevir(s) {
  return s.replace(new RegExp(AY_RX.source, 'gu'), (tum, gun, ay, yil) => {
    const uzun = AYLAR.includes(ay)
    // Gün de yıl da yoksa yalnızca metnin tamamı ay adıysa çevir ("Mar" kelimesi başka bir şeyin parçası olabilir)
    if (!gun && !yil && tum !== s) return tum
    const yilSayi = yil ? (yil.length === 2 ? 2000 + Number(yil) : Number(yil)) : 2000
    const tarih = new Date(yilSayi, ayNo(ay), Number(gun || 1))
    const ayBicim = uzun ? 'long' : 'short'
    const sec = { month: ayBicim, ...(gun ? { day: 'numeric' } : {}), ...(yil ? { year: 'numeric' } : {}) }
    try { return new Intl.DateTimeFormat(dil, sec).format(tarih) } catch { return tum }
  })
}

const AD_GIBI = /^\p{Lu}[\p{L}'’.-]*(\s+\p{Lu}[\p{L}'’.-]*)*$/u
function parcalarla(s, ayrac, derinlik, adOlabilir) {
  if (!s.includes(ayrac)) return null
  const p = s.split(ayrac)
  if (p.length > 12) return null
  let cevrilen = 0
  const c = p.map((x) => {
    let y = cevirIc(x.trim(), derinlik + 1)
    // Kod içinde "…arttı, " + "düşen öğrenci yok." gibi birleştirilen parçalar katalogda virgülüyle durur
    if (y == null && ayrac === ', ') { const v = cevirIc(x.trim() + ',', derinlik + 1); if (v != null) y = v.replace(/[,，、]\s*$/, '') }
    if (y != null) { cevrilen++; return y }
    if (!/\p{L}/u.test(x) || (adOlabilir && AD_GIBI.test(x.trim()))) return x.trim()
    return null
  })
  return cevrilen > 0 && c.every((x) => x != null) ? c.join(ayrac) : null
}

function kaliptan(s, derinlik) {
  for (const k of kaliplar) {
    if (k.enUzun && !s.includes(k.enUzun)) continue
    const m = k.rx.exec(s)
    if (!m) continue
    const degerler = m.slice(1).map(normal)
    // Değişken kısımlar da çevrilir (bölüm adı, "5 giriş" gibi iç kalıplar); çevrilemeyen ad / sayı olduğu gibi kalır
    const cevrilmis = degerler.map((v) => cevirIc(v, derinlik + 1))
    if (!kalipGuvenilir(k, s, degerler, cevrilmis)) continue
    return k.ceviri.replace(/\{(\d+)\}/g, (_, n) => {
      const i = k.sira.indexOf(Number(n))
      return cevrilmis[i] ?? (degerler[i] != null ? yuzdeDuzelt(degerler[i]) : '')
    })
  }
  return null
}

// Bileşenlerde doğrudan kullanmak için: çeviri yoksa metnin kendisi
export const t = (s) => cevir(s) ?? s

function bosluklu(ham, c) {
  const bas = ham.match(/^\s*/)[0], son = ham.match(/\s*$/)[0]
  // Sağdan sola dillerde yön okları da döner ("İncele →" → "… ←")
  if (SAG_SOL.has(dil)) c = c.replace(/[→←]/g, (o) => (o === '→' ? '←' : '→'))
  return bas + c + son
}

// ---------- DOM ----------
const ORIJINAL = new WeakMap()   // metin düğümü → { tr, yazilan }
const OZNITELIK = ['placeholder', 'title', 'aria-label', 'alt']
const OZ_ORIJINAL = new WeakMap() // eleman → { ad: { tr, yazilan } }
const ATLA_ETIKET = new Set(['SCRIPT', 'STYLE', 'TEXTAREA', 'NOSCRIPT', 'CODE', 'PRE'])

function cevrilmezMi(el) {
  for (let e = el; e && e.nodeType === 1; e = e.parentElement) {
    if (ATLA_ETIKET.has(e.tagName)) return true
    if (e.getAttribute('translate') === 'no' || e.classList.contains('ceviri-yok') || e.isContentEditable) return true
  }
  return false
}

function metinDugumu(n) {
  const kayit = ORIJINAL.get(n)
  const simdi = n.nodeValue
  if (kayit && simdi === kayit.yazilan) return
  const tr = simdi
  const c = cevir(tr)
  if (c != null) {
    const yaz = bosluklu(tr, c)
    ORIJINAL.set(n, { tr, yazilan: yaz })
    if (yaz !== simdi) n.nodeValue = yaz
  } else {
    ORIJINAL.set(n, { tr, yazilan: simdi })
    sunucuyaSor(n, tr)
    cevrilmeyenKaydet(tr)
  }
}

// Eleman çocukları yalnızca metinse ("Hoş geldin, " + ad + "!") birleşik kalıp dene
// Bir cümle parçalara bölünmüş olabilir: "Hoş geldin, " + ad + "!" ya da "Değerlendirme " + <b>tam ekranda</b> + " yapılır."
// Elemanın çocukları yalnızca metin ve içinde yalnızca metin olan satır içi biçim etiketleriyse cümle bütün olarak çevrilir:
// çeviri ilk metin düğümüne yazılır, diğer parçalar boşaltılır (kalın yazı biçimi bu cümlelerde kaybolur, söz dizimi doğru olur).
// Bağlantı / buton içeren cümlelere dokunulmaz (tıklanabilir öğe kaybolmasın).
const SATIR_ICI = new Set(['B', 'STRONG', 'I', 'EM', 'SPAN', 'U', 'MARK', 'SMALL'])
function grupHedefi(el) {
  return el && SATIR_ICI.has(el.tagName) && el.parentElement ? el.parentElement : el
}
function karisikGrup(el) {
  const c = el.childNodes
  if (c.length < 2) return
  const dugumler = []
  let satirIci = false
  for (const x of c) {
    if (x.nodeType === 3) { dugumler.push(x); continue }
    if (x.nodeType !== 1 || !SATIR_ICI.has(x.tagName) || x.getAttribute('translate') === 'no') return
    for (const y of x.childNodes) { if (y.nodeType !== 3) return; dugumler.push(y) }
    satirIci = true
  }
  if (dugumler.length < 2) return
  const parcalar = dugumler.map((x) => { const k = ORIJINAL.get(x); return k && x.nodeValue === k.yazilan ? k.tr : x.nodeValue })
  // Parçaların hepsi zaten tek tek çevrildiyse (ya da harfsizse) birleştirme denenmez: "✏️" + "Çözülen soru" gibi ayrı etiketler bozulmasın
  if (dugumler.every((x, i) => !/\p{L}{2,}/u.test(parcalar[i]) || x.nodeValue !== parcalar[i])) return
  const tr = parcalar.join('')
  // Satır içi etiketli cümlelerde yalnızca katalogdaki bütün cümle ya da kalıp kabul edilir (rozet / ikon içeren menü öğeleri bozulmasın)
  const n = normal(tr)
  const ce = satirIci ? (paket.get(n) ?? (kaliplar.length ? kaliptan(n, 0) : null)) : cevir(tr)
  if (ce == null) return
  const yaz = bosluklu(tr, ce)
  dugumler.forEach((x, i) => {
    const v = i === 0 ? yaz : ''
    ORIJINAL.set(x, { tr: parcalar[i], yazilan: v })
    if (x.nodeValue !== v) x.nodeValue = v
  })
}

function oznitelikler(el) {
  let kayit = OZ_ORIJINAL.get(el)
  for (const ad of OZNITELIK) {
    const v = el.getAttribute(ad)
    if (!v) continue
    const k = kayit?.[ad]
    if (k && k.yazilan === v) continue
    const c = cevir(v)
    if (!kayit) { kayit = {}; OZ_ORIJINAL.set(el, kayit) }
    kayit[ad] = { tr: v, yazilan: c ?? v }
    if (c != null && c !== v) el.setAttribute(ad, c)
    else if (c == null) cevrilmeyenKaydet(v)
  }
}

function agacCevir(kok) {
  if (kok.nodeType === 3) {
    const p = kok.parentElement
    if (p && !cevrilmezMi(p)) { metinDugumu(kok); karisikGrup(grupHedefi(p)) }
    return
  }
  if (kok.nodeType !== 1 || cevrilmezMi(kok)) return
  const yurut = document.createTreeWalker(kok, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => {
      if (n.nodeType === 1 && (ATLA_ETIKET.has(n.tagName) || n.getAttribute('translate') === 'no' || n.classList.contains('ceviri-yok'))) return NodeFilter.FILTER_REJECT
      return NodeFilter.FILTER_ACCEPT
    },
  })
  const gruplar = new Set()
  oznitelikler(kok)
  for (let n = yurut.nextNode(); n; n = yurut.nextNode()) {
    if (n.nodeType === 3) { metinDugumu(n); if (n.parentElement) gruplar.add(grupHedefi(n.parentElement)) }
    else oznitelikler(n)
  }
  gruplar.forEach(karisikGrup)
}

let kuyruk = new Set(), planli = false
function isle() {
  planli = false
  const k = kuyruk; kuyruk = new Set()
  gozlemci.disconnect()
  try { k.forEach((n) => { if (n.isConnected) agacCevir(n) }) } finally { gozle() }
}
const gozlemci = typeof MutationObserver !== 'undefined' ? new MutationObserver((kayitlar) => {
  for (const r of kayitlar) {
    if (r.type === 'childList') r.addedNodes.forEach((n) => kuyruk.add(n))
    else if (r.type === 'characterData') kuyruk.add(r.target)
    else if (r.type === 'attributes') kuyruk.add(r.target)
  }
  if (!planli) { planli = true; queueMicrotask(isle) }
}) : null
function gozle() {
  gozlemci.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: OZNITELIK })
  const baslik = document.querySelector('title')
  if (baslik) gozlemci.observe(baslik, { subtree: true, childList: true, characterData: true })
}

// ---------- Sunucudan içerik çevirisi (bölüm açıklamaları, sözlük, iş hayatı içerikleri) ----------
const BEKLEYEN_DUGUM = new Map() // tr → Set(düğüm)
let sunucuZamanlayici = null
// Tanılama: ekranda görülüp çevrilemeyen metinler (window.__filizCevrilmeyen()) — eksik çevirileri bulmak için
const CEVRILMEYEN = new Set()
function cevrilmeyenKaydet(tr) {
  const s = normal(tr)
  if (CEVRILMEYEN.size < 3000 && /\p{L}{2,}/u.test(s)) CEVRILMEYEN.add(s)
}

function sunucuyaSor(n, tr) {
  const s = normal(tr)
  if (s.length < 12 || !/\p{L}{3,}/u.test(s) || sunucuSorulan.has(s)) return
  if (!BEKLEYEN_DUGUM.has(s)) BEKLEYEN_DUGUM.set(s, new Set())
  BEKLEYEN_DUGUM.get(s).add(n)
  sunucuBekleyen.add(s)
  clearTimeout(sunucuZamanlayici)
  sunucuZamanlayici = setTimeout(sunucuyaGonder, 350)
}
async function sunucuyaGonder() {
  const liste = [...sunucuBekleyen].slice(0, 200)
  liste.forEach((s) => { sunucuBekleyen.delete(s); sunucuSorulan.add(s) })
  if (!liste.length) return
  if (sunucuBekleyen.size) sunucuZamanlayici = setTimeout(sunucuyaGonder, 50)
  try {
    const yanit = await fetch('/api/ceviri/icerik', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dil, metinler: liste }),
    })
    if (!yanit.ok) return
    const { ceviriler } = await yanit.json()
    gozlemci.disconnect()
    try {
      liste.forEach((s, i) => {
        const c = ceviriler?.[i]
        if (!c) return
        paket.set(s, c); bellek.set(s, c)
        BEKLEYEN_DUGUM.get(s)?.forEach((n) => {
          if (!n.isConnected) return
          const k = ORIJINAL.get(n)
          if (k && n.nodeValue === k.yazilan && normal(k.tr) === s) {
            const yaz = bosluklu(k.tr, c)
            ORIJINAL.set(n, { tr: k.tr, yazilan: yaz })
            n.nodeValue = yaz
          }
        })
        BEKLEYEN_DUGUM.delete(s)
      })
    } finally { gozle() }
  } catch { /* çeviri alınamazsa Türkçe kalır */ }
}

// ---------- Başlatma ve dil değiştirme ----------
export async function dilBaslat() {
  dil = aktifDil()
  document.documentElement.lang = dil
  document.documentElement.dir = SAG_SOL.has(dil) ? 'rtl' : 'ltr'
  if (dil === 'tr') return
  const yukleyici = PAKETLER[`../dil/${dil}.json`]
  if (!yukleyici) return
  try {
    const adres = await yukleyici()
    const yanit = await fetch(adres)
    if (!yanit.ok) throw new Error('paket')
    yukle(await yanit.json())
  } catch { dil = 'tr'; document.documentElement.lang = 'tr'; return }
  const sar = (ad) => {
    const asil = window[ad]?.bind(window)
    if (asil) window[ad] = (mesaj, ...g) => asil(mesaj == null ? mesaj : t(String(mesaj)), ...g)
  }
  sar('alert'); sar('confirm'); sar('prompt')
  // Kod 'tr-TR' biçiminde tarih / sayı yazıyorsa seçili dilin biçimi kullanılır (ay ve gün adları dahil)
  const yerel = (l) => (l == null || /^tr\b/i.test(String(l)) ? dil : l)
  for (const [nesne, adlar] of [[Date.prototype, ['toLocaleDateString', 'toLocaleString', 'toLocaleTimeString']], [Number.prototype, ['toLocaleString']]]) {
    for (const ad of adlar) {
      const asil = nesne[ad]
      nesne[ad] = function (l, o) { return asil.call(this, yerel(l), o) }
    }
  }
  window.__filizCevir = cevir   // tanılama: tarayıcı konsolunda çeviri denemek için
  window.__filizCevrilmeyen = () => [...CEVRILMEYEN]
  const basla = () => { agacCevir(document.body); gozle() }
  if (document.body) basla(); else document.addEventListener('DOMContentLoaded', basla)
}

// Dili değiştir: yerelde sakla, giriş yapılmışsa hesaba kaydet, sayfayı yenile
export async function dilDegistir(kod, kaydet) {
  try {
    localStorage.setItem(ANAHTAR, kod)
    // Giriş ekranında seçildiyse girişten sonra hesaba yazılacak (hesaptaki eski tercih bunu ezmesin)
    if (!kaydet) localStorage.setItem('dil_bekleyen', '1'); else localStorage.removeItem('dil_bekleyen')
  } catch { /* yoksay */ }
  if (kaydet) { try { await kaydet(kod) } catch { /* sunucuya yazılamazsa yerel tercih yeter */ } }
  window.location.reload()
}

// Girişten sonra: giriş ekranında dil seçildiyse hesaba yaz; değilse hesaptaki tercih farklıysa onu uygula
export function hesapDiliniUygula(sunucuDili, kaydet) {
  let bekleyen = false
  try { bekleyen = localStorage.getItem('dil_bekleyen') === '1' } catch { /* yoksay */ }
  // Giriş ekranında seçildiyse ya da hesapta hiç dil seçilmemişse: tarayıcıdaki seçim hesaba yazılır
  if (bekleyen || !sunucuDili) {
    try { localStorage.removeItem('dil_bekleyen') } catch { /* yoksay */ }
    if (sunucuDili !== aktifDil() && kaydet && (sunucuDili || aktifDil() !== 'tr')) kaydet(aktifDil()).catch(() => {})
    return false
  }
  if (!sunucuDili || sunucuDili === aktifDil() || !DILLER.some((x) => x.kod === sunucuDili)) return false
  try {
    // Yenileme döngüsüne karşı: aynı oturumda 30 sn içinde ikinci kez dil yüzünden yenileme yapılmaz
    const son = Number(sessionStorage.getItem('dil_yenilendi') || 0)
    if (Date.now() - son < 30000) return false
    sessionStorage.setItem('dil_yenilendi', String(Date.now()))
    localStorage.setItem(ANAHTAR, sunucuDili)
  } catch { return false }
  window.location.reload()
  return true
}
