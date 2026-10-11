// [2026-10-11] Sözlük katmanı — öğrenci ekranlarında zor terimlerin altını noktalı çizer; dokununca kısa açıklama açar.
//
// Nasıl çalışır (React'in DOM'una dokunmadan):
//   1) Sayfadaki metin düğümleri taranır, sözlükteki terimlerin HER SAYFADA İLK geçtiği yer bulunur (çok çizgi göz yormasın).
//   2) Bulunan aralıklar CSS Custom Highlight API ile boyanır (::highlight(sozluk-terim)). DOM'a eleman EKLENMEZ;
//      böylece React'in güncellediği metinler bozulmaz.
//   3) Tıklama/dokunma noktası bu aralıklardan birinin içindeyse açıklama kutusu açılır.
// Hariç: bağlantılar, düğmeler, form alanları, Filiz balonu, grafikler (svg) ve data-sozluk-yok işaretli alanlar.
// Tarayıcı Highlight API'yi desteklemiyorsa katman sessizce devre dışı kalır (Sözlük sayfası yine çalışır).
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { SOZLUK } from '../yardimci/sozluk'

const AYAR = 'sozluk_ipuclari'
export const sozlukAcikMi = () => { try { return localStorage.getItem(AYAR) !== 'kapali' } catch { return true } }
export const sozlukAyarla = (acik) => {
  try { localStorage.setItem(AYAR, acik ? 'acik' : 'kapali') } catch { /* yoksay */ }
  window.dispatchEvent(new Event('sozluk-ayar'))
}

const HARIC = 'a, button, input, textarea, select, option, code, pre, svg, [contenteditable="true"], [data-sozluk-yok], .msk-kap, .sozluk-kutu, .auth-input, .ni, .tabs, .yp-sekmeler'
const HARF = /[\p{L}\p{N}]/u
const kucuk = (s) => s.toLocaleLowerCase('tr-TR')

// Biçimleri uzundan kısaya sırala: "belirsizlik ve risk toleransı" "tolerans"tan önce denensin
const BICIMLER = SOZLUK.flatMap((t) => (t.es || []).map((b) => ({ b: kucuk(b), t })))
  .sort((x, y) => y.b.length - x.b.length)
const DESEN = new RegExp(BICIMLER.map(({ b }) => b.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')).join('|'), 'gu')

function tara(kok) {
  const gorulen = new Set()
  const bulunan = []   // { range, terim }
  const yuruyucu = document.createTreeWalker(kok, NodeFilter.SHOW_TEXT, {
    acceptNode(d) {
      if (!d.nodeValue || d.nodeValue.trim().length < 2) return NodeFilter.FILTER_REJECT
      const ust = d.parentElement
      if (!ust || ust.closest(HARIC)) return NodeFilter.FILTER_REJECT
      return NodeFilter.FILTER_ACCEPT
    },
  })
  let d
  while ((d = yuruyucu.nextNode())) {
    const ham = d.nodeValue
    const metin = kucuk(ham)
    if (metin.length !== ham.length) continue   // güvenlik: uzunluk değişirse konumlar kayar
    DESEN.lastIndex = 0
    let m
    while ((m = DESEN.exec(metin))) {
      const bas = m.index
      const son = bas + m[0].length
      const bicim = BICIMLER.find((x) => x.b === m[0])
      if (!bicim) continue
      const { t } = bicim
      const once = bas > 0 ? metin[bas - 1] : ''
      const sonra = metin[son] || ''
      if (once && HARF.test(once)) continue                        // kelimenin ortası
      if (t.tam && sonra && HARF.test(sonra)) continue             // kısaltma/kısa kelime: ek yalnızca kesmeyle
      if (t.bh && m[0].length <= 4) {                              // kısaltma büyük harfle yazılmalı ("SÖZ" ≠ "söz")
        const asil = ham.slice(bas, son)
        if (asil !== asil.toLocaleUpperCase('tr-TR')) continue
      }
      if (gorulen.has(t.k)) continue
      gorulen.add(t.k)
      // Eklerle birlikte kelimenin sonuna kadar boya ("katmanları" tümüyle)
      let bitis = son
      if (!t.tam) while (bitis < metin.length && HARF.test(metin[bitis])) bitis += 1
      const r = document.createRange()
      r.setStart(d, bas); r.setEnd(d, bitis)
      bulunan.push({ range: r, terim: t })
    }
  }
  return bulunan
}

export default function SozlukKatmani({ kokSecici = '.ogrenci-main' }) {
  const konum = useLocation()
  const [acik, setAcik] = useState(sozlukAcikMi)
  const [kutu, setKutu] = useState(null)           // { terim, x, y, ust }
  const bulunanRef = useRef([])
  const destek = typeof CSS !== 'undefined' && CSS.highlights && typeof Highlight !== 'undefined'

  useEffect(() => {
    const dinle = () => setAcik(sozlukAcikMi())
    window.addEventListener('sozluk-ayar', dinle)
    return () => window.removeEventListener('sozluk-ayar', dinle)
  }, [])

  const yenile = useCallback(() => {
    if (!destek) return
    const kok = document.querySelector(kokSecici)
    if (!acik || !kok) { CSS.highlights.delete('sozluk-terim'); bulunanRef.current = []; return }
    const b = tara(kok)
    bulunanRef.current = b
    CSS.highlights.set('sozluk-terim', new Highlight(...b.map((x) => x.range)))
  }, [acik, destek, kokSecici])

  // Sayfa ya da içerik değişince yeniden tara (gecikmeli; yazı makinesi gibi sık değişimlerde yorulmasın)
  useEffect(() => {
    if (!destek) return undefined
    setKutu(null)
    let zaman = null
    const planla = () => { window.clearTimeout(zaman); zaman = window.setTimeout(yenile, 350) }
    planla()
    const kok = document.querySelector(kokSecici)
    const gozcu = kok ? new MutationObserver(planla) : null
    gozcu?.observe(kok, { childList: true, subtree: true, characterData: true })
    return () => { window.clearTimeout(zaman); gozcu?.disconnect(); CSS.highlights.delete('sozluk-terim') }
  }, [konum.pathname, konum.search, yenile, destek, kokSecici])

  // Dokunma / tıklama: nokta bir terimin üstündeyse kutuyu aç
  useEffect(() => {
    if (!destek || !acik) return undefined
    const tikla = (e) => {
      if (e.target.closest?.('.sozluk-kutu')) return
      if (e.target.closest?.(HARIC)) { setKutu(null); return }
      const { clientX: x, clientY: y } = e
      for (const { range, terim } of bulunanRef.current) {
        for (const r of range.getClientRects()) {
          if (x >= r.left - 2 && x <= r.right + 2 && y >= r.top - 3 && y <= r.bottom + 3) {
            setKutu({ terim, x: r.left, y: r.bottom, ust: r.top })
            return
          }
        }
      }
      setKutu(null)
    }
    const kapat = (e) => { if (e.key === 'Escape') setKutu(null) }
    const kaydir = () => setKutu(null)
    document.addEventListener('click', tikla)
    document.addEventListener('keydown', kapat)
    window.addEventListener('scroll', kaydir, true)
    return () => {
      document.removeEventListener('click', tikla)
      document.removeEventListener('keydown', kapat)
      window.removeEventListener('scroll', kaydir, true)
    }
  }, [destek, acik])

  if (!kutu) return null
  const genislik = Math.min(320, window.innerWidth - 24)
  const sol = Math.max(12, Math.min(kutu.x, window.innerWidth - genislik - 12))
  const asagi = kutu.y + 220 < window.innerHeight
  const stil = asagi ? { top: kutu.y + 8, left: sol, width: genislik } : { bottom: window.innerHeight - kutu.ust + 8, left: sol, width: genislik }
  return (
    <div className="sozluk-kutu" role="dialog" aria-label={`${kutu.terim.ad} ne demek?`} style={stil}>
      <div className="sozluk-kutu-ust">
        <span className="sozluk-kutu-ad">📖 {kutu.terim.ad}</span>
        <button className="sozluk-kutu-kapat" onClick={() => setKutu(null)} aria-label="Kapat">✕</button>
      </div>
      <div className="sozluk-kutu-tanim">{kutu.terim.t}</div>
      {kutu.terim.o && <div className="sozluk-kutu-ornek">Örnek: {kutu.terim.o}</div>}
      <Link to={`/sozluk?t=${kutu.terim.k}`} className="sozluk-kutu-link" onClick={() => setKutu(null)}>Sözlüğün tamamı →</Link>
    </div>
  )
}
