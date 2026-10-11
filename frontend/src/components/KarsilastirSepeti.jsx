// [2026-10-11] Karşılaştırma sepeti — "Karşılaştır" eylemi (Sonuçlar, Tüm bölümler, bölüm bilgi penceresi).
// En fazla 3 bölüm; tarayıcıda (localStorage) tutulur, tüm düğmeler ve alt çubuk birlikte güncellenir.
// /karsilastir sayfası seçimi URL'den (?b=1,2,3) okur; sepetten açılınca URL sepetle doldurulur.
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

export const SEPET_SINIRI = 3
const ANAHTAR = 'filizyol_karsilastir_sepeti'
let sepet = oku()
const dinleyiciler = new Set()

function oku() {
  try {
    const l = JSON.parse(localStorage.getItem(ANAHTAR) || '[]')
    return Array.isArray(l) ? l.filter((x) => x && Number.isInteger(x.id)).slice(0, SEPET_SINIRI) : []
  } catch { return [] }
}
function yaz(l) {
  sepet = l.slice(0, SEPET_SINIRI)
  try { localStorage.setItem(ANAHTAR, JSON.stringify(sepet)) } catch { /* gizli pencere vb. */ }
  dinleyiciler.forEach((f) => f(sepet))
}

export function useSepet() {
  const [l, setL] = useState(sepet)
  useEffect(() => { dinleyiciler.add(setL); setL(sepet); return () => { dinleyiciler.delete(setL) } }, [])
  return l
}
export const sepetAyarla = (l) => yaz(l)
export const sepetTemizle = () => yaz([])
/** true: eklendi / çıkarıldı · false: sepet dolu */
export function sepetDegistir(id, ad) {
  if (sepet.some((x) => x.id === id)) { yaz(sepet.filter((x) => x.id !== id)); return true }
  if (sepet.length >= SEPET_SINIRI) return false
  yaz([...sepet, { id, ad }])
  return true
}
export const karsilastirYolu = (l) => `/karsilastir${l.length ? `?b=${l.map((x) => x.id).join(',')}` : ''}`

export function KarsilastirDugmesi({ id, ad, etiketli = false }) {
  const l = useSepet()
  const [uyari, setUyari] = useState(false)
  if (!id) return null
  const secili = l.some((x) => x.id === id)
  function tikla(e) {
    e.stopPropagation(); e.preventDefault()
    if (!sepetDegistir(id, ad)) { setUyari(true); setTimeout(() => setUyari(false), 3000) }
  }
  const baslik = uyari ? `En fazla ${SEPET_SINIRI} bölüm karşılaştırılabilir — birini çıkar.` : secili ? 'Karşılaştırmadan çıkar' : 'Karşılaştırmaya ekle'
  return (
    <span className="ks-dugme-kap">
      <button type="button" className={`ks-dugme${secili ? ' secili' : ''}${etiketli ? ' etiketli' : ''}`} onClick={tikla}
        aria-pressed={secili} title={baslik} aria-label={baslik}>
        <span aria-hidden="true">⚖️</span>
        {etiketli && <span>{secili ? `Karşılaştırmada (${l.length}/${SEPET_SINIRI})` : 'Karşılaştır'}</span>}
      </button>
      {etiketli && secili && l.length >= 2 && <Link className="ks-ac" to={karsilastirYolu(l)}>Aç →</Link>}
      {uyari && <span className="fav-hata" role="status">{baslik}</span>}
    </span>
  )
}

/** Sayfa altında yapışkan çubuk: sepette bölüm varsa görünür. */
export function KarsilastirCubugu() {
  const l = useSepet()
  const navigate = useNavigate()
  if (!l.length) return null
  return (
    <div className="ks-cubuk" role="region" aria-label="Karşılaştırma sepeti">
      <span className="ks-cubuk-ikon" aria-hidden="true">⚖️</span>
      <div className="ks-cubuk-liste">
        {l.map((x) => (
          <span key={x.id} className="ks-cubuk-cip">
            <span>{x.ad || `#${x.id}`}</span>
            <button type="button" aria-label={`${x.ad || 'Bölümü'} çıkar`} onClick={() => sepetDegistir(x.id)}>×</button>
          </span>
        ))}
        {l.length < SEPET_SINIRI && <span className="yp-ince ks-cubuk-ipucu">{l.length < 2 ? 'bir bölüm daha ekle' : `${SEPET_SINIRI - l.length} yer daha var`}</span>}
      </div>
      <button type="button" className="btn ks-cubuk-git" disabled={l.length < 2} onClick={() => navigate(karsilastirYolu(l))}>Karşılaştır</button>
    </div>
  )
}
