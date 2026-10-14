// [2026-10-11] Tanıtım turu — ilk açılışta sol menüyü tek tek tanıtır ("burada bu var").
// YETKİ: adımlar, kişinin ekranında GERÇEKTEN görünen menü bağlantılarından (.sb .ni) üretilir. Paket / rol nedeniyle
// gizli olan bir menü tura hiç girmez; başka role ait sayfa anlatılmaz. Süper admin menüsü uzun olduğu için grup grup.
// Mobil: menü kapalı çekmecede olduğundan adımlar ortada kart olarak gösterilir (ışık yok).
// Kontroller: İleri / Geri, "Turu atla", Esc = atla, ← → tuşları. Bitince / atlanınca onBitir() (görüldü işaretlenir).
// Yeniden başlatma: 'tur-baslat' olayı (öğrenci: Ayarlar → Tanıtımı Göster; yönetim: menüde "Tanıtımı başlat").
import { useCallback, useEffect, useLayoutEffect, useMemo, useState } from 'react'
import { OKUL_BOLUMLERI } from './yonetim/okulBolumleri'

export const turuBaslat = () => window.dispatchEvent(new CustomEvent('tur-baslat'))

// Öğrenci menüsü: bağlantı adresi → kısa açıklama (lise öğrencisinin dili)
const OGRENCI = {
  '/katmanlar': 'Değerlendirmen burada. Soruları cevapla; doğru ya da yanlış cevap yok, içten cevap ver.',
  '/': 'Ana sayfan: sıradaki adımın, bu haftanın görevleri ve sonuçlarının kısa özeti.',
  '/profilim': 'Değerlendirme sonuçların ve kısa yorumu: güçlü yönlerin, ilgi alanların, bu dönem neler yapabileceğin.',
  '/bolumler': 'Sana uygun bölümler, tüm bölümleri keşfetme, karşılaştırma ve kendi listen.',
  '/is-hayati': 'Bölümlerin iş hayatı: maaşlar, zor günler, CV, mülakat simülasyonu ve düşünme atölyesi.',
  '/tercih': 'Tercih listeni hazırla; rehber öğretmenin inceleyip onaylar.',
  '/portfolyo': 'Sertifika, yarışma ve etkinliklerini biriktirdiğin dosyan.',
  '/raporlarim': 'Raporlarını (PDF) ve sonuç tablonu (Excel) indir; velinle paylaşacağın rapor da burada.',
  '/koclugu': 'Hedef bölümün için adım adım yol haritan.',
  '/calisma': 'Çalışma programın, günlük çalışma süren ve çözdüğün sorular.',
  '/netlerim': 'Deneme netlerin, konu takibin ve hedefinle karşılaştırma.',
  '/gorevler': 'Her hafta sana özel 3 küçük görev; tamamladıkça serin uzar.',
  '/kutuphane': 'Okuduğun kitaplar, izlediklerin ve katıldığın etkinlikler.',
  filiz: 'Filiz, gelişim koçun. Aklına takılan her şeyi ona sorabilirsin.',
  '/takvim': 'Okulunun etkinlikleri, sınav tarihleri ve rehberlik randevuların.',
  '/anketler': 'Okulunun ve rehber öğretmeninin anketleri.',
  '/kulupler': 'Sana uygun kulüpler ve üyeliklerin.',
  '/koclar': 'Filizyol\'un anlaşmalı, okulun için onaylanmış eğitim koçları.',
  '/sozluk': 'Anlamadığın bir kelime mi var? Sistem Sözlüğü\'nde ara.',
  '/hakkinda': 'Filizyol nasıl çalışır, sonuçlar nasıl hesaplanır?',
  '/profil': 'Bilgilerin, şifren, dilin ve gizlilik ayarların. Bu tanıtımı da buradan tekrar izleyebilirsin.',
}
const YONETIM_EK = {
  '/admin/sss': 'Sistem nasıl çalışır, sık sorulan sorular ve kullanım ipuçları.',
  '/admin/kaynakca': 'Sistemin dayandığı kaynaklar ve yöntemler.',
}
const OKUL_ACIKLAMA = Object.fromEntries(OKUL_BOLUMLERI.map((b) => [b.k, b.aciklama]))
const SUPER_GRUP = {
  'Genel': 'Kontrol paneli: sistemin genel durumu, dikkat gerektirenler ve güvenlik kontrolü.',
  'Raporlar ve İstatistikler': 'Tüm okulların istatistikleri, raporları ve okul karşılaştırması.',
  'Okullar ve Kullanıcılar': 'Okullar, paketler, okul yetkilileri, eğitim koçları ve test hesapları.',
  'İçerik': 'Bölümler, iş hayatı verileri, sözlükler, konu listesi ve soru bankası.',
  'Ölçme ve Kalite': 'Soru geçerliliği, tutarlılık kontrolleri ve ağırlık yükleme süreci.',
  'Sistem': 'Parametreler, işlem kayıtları ve hata kayıtları.',
  'Yardım': 'Sistem hakkında bilgiler, SSS ve kaynakça.',
}

const gorunurMu = (el) => {
  if (!el) return false
  const r = el.getBoundingClientRect()
  const s = getComputedStyle(el)
  return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && r.right > 0 && r.left < window.innerWidth
}
// Görünmeyen (mobil çekmecedeki) öğede innerText boş döner ve CSS büyük harfi uygular; bu yüzden textContent + rozetler çıkarılır
const metin = (el) => {
  if (!el) return ''
  const k = el.cloneNode(true)
  k.querySelectorAll('.ni-rozet').forEach((r) => r.remove())
  return (k.textContent || '').replace(/\s+/g, ' ').trim()
}

function adimlariTopla(kapsam) {
  const sb = document.querySelector('.sb')
  if (!sb) return []
  const adimlar = []
  if (kapsam === 'super') {
    sb.querySelectorAll('.ns').forEach((ns) => {
      const grup = metin(ns)
      const ilk = ns.nextElementSibling
      if (ilk && ilk.classList.contains('ni')) adimlar.push({ el: ilk, baslik: grup, aciklama: SUPER_GRUP[grup] || `${grup} sayfaları.` })
    })
    return adimlar
  }
  sb.querySelectorAll('.ni').forEach((el) => {
    const href = el.getAttribute('href') || ''
    let aciklama
    if (kapsam === 'ogrenci') aciklama = OGRENCI[el.dataset.tur || href]
    else {
      const m = /\/admin\/okul\/\d+(?:\?sekme=([a-z_]+))?$/.exec(href)
      aciklama = m ? OKUL_ACIKLAMA[m[1] || 'ozet'] : YONETIM_EK[href]
    }
    if (aciklama) adimlar.push({ el, baslik: metin(el), aciklama })
  })
  return adimlar
}

const GIRIS = {
  ogrenci: { baslik: 'Filizyol\'a hoş geldin! 🌱', aciklama: 'Filizyol sana en uygun üniversite bölümlerini bulmana ve o bölüme hazırlanmana yardım eder. Kısaca menüleri tanıtalım.',
    maddeler: ['Doğru ya da yanlış cevap yok, içten cevap ver', 'Sonuçlar yol gösterir, son kararı sen verirsin', 'İstersen turu şimdi atlayabilirsin'] },
  yonetim: { baslik: 'Okul panelinize hoş geldiniz', aciklama: 'Öğrencilerinizin katılımını, sonuçlarını ve rehberlik süreçlerini buradan yönetirsiniz. Menüleri kısaca tanıtalım.',
    maddeler: ['Yalnızca kendi okulunuzun bilgilerini görürsünüz', 'Menüde yalnızca okulunuzun paketindeki bölümler yer alır', 'İsterseniz turu şimdi atlayabilirsiniz'] },
  super: { baslik: 'Yönetici paneline hoş geldiniz', aciklama: 'Tüm okulları, içeriği ve sistemi buradan yönetirsiniz. Menü gruplarını kısaca tanıtalım.',
    maddeler: ['Menü grup grup anlatılır', 'İsterseniz turu şimdi atlayabilirsiniz'] },
}
const SON = {
  ogrenci: { baslik: 'Hazırsın! 🎉', aciklama: 'Takıldığın her yerde sağ alttaki Filiz\'e sorabilir, bilmediğin kelimeyi Sözlük\'te arayabilirsin. Bu tanıtımı Ayarlar\'dan tekrar izleyebilirsin.' },
  yonetim: { baslik: 'Hazırsınız', aciklama: 'Sağ üstteki Filiz\'e "Bana sor" ile panel hakkında soru sorabilirsiniz. Bu tanıtımı menüdeki "Tanıtımı başlat" ile tekrar izleyebilirsiniz.' },
  super: { baslik: 'Hazırsınız', aciklama: 'Bu tanıtımı menüdeki "Tanıtımı başlat" ile tekrar izleyebilirsiniz.' },
}

export default function TanitimTuru({ kapsam = 'ogrenci', onBitir }) {
  const [adimlar, setAdimlar] = useState(null)
  const [i, setI] = useState(0)
  const [kutu, setKutu] = useState(null)

  useEffect(() => {   // menü çizildikten sonra topla
    const t = window.setTimeout(() => setAdimlar(adimlariTopla(kapsam)), 150)
    return () => window.clearTimeout(t)
  }, [kapsam])

  const tum = useMemo(() => (adimlar ? [{ giris: true, ...GIRIS[kapsam] }, ...adimlar, { son: true, ...SON[kapsam] }] : []), [adimlar, kapsam])
  const a = tum[i]
  const isikli = a && a.el && gorunurMu(a.el)

  const olc = useCallback(() => {
    if (!a?.el || !gorunurMu(a.el)) { setKutu(null); return }
    const r = a.el.getBoundingClientRect()
    setKutu({ top: r.top - 4, left: r.left - 4, width: r.width + 8, height: r.height + 8 })
  }, [a])
  useLayoutEffect(() => {
    if (a?.el && gorunurMu(a.el)) a.el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    olc()
    const t = window.setTimeout(olc, 320)   // yumuşak kaydırma bitince
    window.addEventListener('resize', olc)
    return () => { window.clearTimeout(t); window.removeEventListener('resize', olc) }
  }, [a, olc])

  const ileri = useCallback(() => (i >= tum.length - 1 ? onBitir() : setI(i + 1)), [i, tum.length, onBitir])
  const geri = useCallback(() => setI((x) => Math.max(0, x - 1)), [])
  useEffect(() => {
    const tus = (e) => {
      if (e.key === 'Escape') onBitir()
      else if (e.key === 'ArrowRight' || e.key === 'Enter') ileri()
      else if (e.key === 'ArrowLeft') geri()
    }
    document.addEventListener('keydown', tus)
    return () => document.removeEventListener('keydown', tus)
  }, [ileri, geri, onBitir])

  if (!a) return null
  const ortada = !isikli || !kutu
  const balonStil = ortada ? {} : (() => {
    const sag = kutu.left + kutu.width + 16
    const top = Math.min(Math.max(12, kutu.top + kutu.height / 2 - 90), window.innerHeight - 260)
    return sag + 340 < window.innerWidth ? { top, left: sag } : { top: Math.min(kutu.top + kutu.height + 12, window.innerHeight - 260), left: 16 }
  })()
  const sayac = tum.length > 2 ? `${i + 1} / ${tum.length}` : ''

  return (
    <div className="tt" role="dialog" aria-modal="true" aria-label="Tanıtım turu">
      {ortada ? <div className="tt-perde" /> : <div className="tt-isik" style={kutu} />}
      <div className={`tt-balon${ortada ? ' ortada' : ''}`} style={balonStil}>
        {!ortada && <span className="tt-ok" aria-hidden="true" />}
        <div className="tt-ust">
          <span className="tt-sayac">{sayac}</span>
          {!a.son && <button type="button" className="tt-atla" onClick={onBitir}>Turu atla ✕</button>}
        </div>
        <div className="tt-baslik">{a.baslik}</div>
        <div className="tt-metin">{a.aciklama}</div>
        {a.maddeler && <ul className="tt-maddeler">{a.maddeler.map((m) => <li key={m}>✓ {m}</li>)}</ul>}
        <div className="tt-noktalar" aria-hidden="true">
          {tum.map((_, k) => <i key={k} className={k === i ? 'aktif' : k < i ? 'gecti' : ''} />)}
        </div>
        <div className="tt-dugmeler">
          {i > 0 && <button type="button" className="btn sec" onClick={geri}>← Geri</button>}
          <button type="button" className="btn" onClick={ileri} autoFocus>{a.giris ? 'Tura başla →' : a.son ? 'Bitir' : 'İleri →'}</button>
        </div>
      </div>
    </div>
  )
}
