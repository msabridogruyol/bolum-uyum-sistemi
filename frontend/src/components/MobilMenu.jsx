// [2026-10-11] Telefon / dar ekran (≤ 900px): sol menü gizlenir; üstte ince bir çubuk (☰ + başlık + zil) çıkar,
// menü soldan kayan çekmece olarak açılır. Masaüstünde (> 900px) hiçbir şey değişmez: çubuk ve örtü çizilmez,
// .sb üzerine dialog özellikleri eklenmez.
import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'

const SORGU = '(max-width: 900px)'
const ODAKLANABILIR = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'

function ilkDurum() {
  try { return window.matchMedia(SORGU).matches } catch { return false }
}

export function useMobilMenu() {
  const [mobil, setMobil] = useState(ilkDurum)
  const [acik, setAcik] = useState(false)
  const dugme = useRef(null)
  const cekmece = useRef(null)
  const oncekiAcik = useRef(false)
  const konum = useLocation()

  useEffect(() => {
    const mq = window.matchMedia(SORGU)
    const degisti = () => setMobil(mq.matches)
    mq.addEventListener('change', degisti)
    return () => mq.removeEventListener('change', degisti)
  }, [])
  useEffect(() => { if (!mobil) setAcik(false) }, [mobil])
  // Rota değişince (menüden bir sayfaya geçince) çekmece kapanır
  useEffect(() => { setAcik(false) }, [konum.pathname, konum.search])

  useEffect(() => {
    const onceAcikti = oncekiAcik.current
    oncekiAcik.current = acik
    if (!acik) {
      if (onceAcikti) dugme.current?.focus()
      return undefined
    }
    // Açıkken: gövde kaydırması kilitli, odak çekmecede, Esc kapatır, Tab çekmece içinde döner
    const eskiTasma = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const kare = requestAnimationFrame(() => {
      const ilk = cekmece.current?.querySelector(ODAKLANABILIR)
      ;(ilk || cekmece.current)?.focus()
    })
    const tus = (e) => {
      if (e.key === 'Escape') { e.preventDefault(); setAcik(false); return }
      if (e.key !== 'Tab' || !cekmece.current) return
      const ogeler = [...cekmece.current.querySelectorAll(ODAKLANABILIR)].filter((o) => o.offsetParent !== null)
      if (!ogeler.length) return
      const ilk = ogeler[0], son = ogeler[ogeler.length - 1]
      if (e.shiftKey && (document.activeElement === ilk || !cekmece.current.contains(document.activeElement))) { e.preventDefault(); son.focus() }
      else if (!e.shiftKey && document.activeElement === son) { e.preventDefault(); ilk.focus() }
    }
    document.addEventListener('keydown', tus)
    return () => {
      cancelAnimationFrame(kare)
      document.body.style.overflow = eskiTasma
      document.removeEventListener('keydown', tus)
    }
  }, [acik])

  const kapat = useCallback(() => setAcik(false), [])
  // Menüde bir bağlantıya (veya menü öğesine) tıklanınca kapanır — aynı sayfaya tıklansa bile
  const cekmeceTikla = useCallback((e) => { if (e.target.closest('a, .ni')) setAcik(false) }, [])

  const cekmeceOzellikleri = mobil
    ? { id: 'ana-menu', ref: cekmece, role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Ana menü', tabIndex: -1, onClick: cekmeceTikla }
    : {}
  return { mobil, acik, setAcik, kapat, dugme, cekmeceOzellikleri, appSinifi: mobil && acik ? ' sb-acik' : '' }
}

// Üst çubuk + arka plan örtüsü (yalnızca dar ekranda çizilir)
export function MobilUstCubuk({ menu, baslik, sag }) {
  if (!menu.mobil) return null
  return (
    <>
      <header className="mobil-ust">
        <button ref={menu.dugme} type="button" className="mobil-menu-dugme"
          aria-label={menu.acik ? 'Menüyü kapat' : 'Menüyü aç'} aria-expanded={menu.acik} aria-controls="ana-menu"
          onClick={() => menu.setAcik((a) => !a)}>
          <span aria-hidden="true">☰</span>
        </button>
        <div className="mobil-baslik">{baslik}</div>
        <div className="mobil-sag">{sag}</div>
      </header>
      <div className="sb-ortu" onClick={menu.kapat} aria-hidden="true" />
    </>
  )
}
