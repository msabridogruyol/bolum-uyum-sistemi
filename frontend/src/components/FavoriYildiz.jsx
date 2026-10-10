// [2026-10-10] "Listem" — öğrencinin ★ ile işaretlediği bölümler. Tek bir paylaşılan depo:
// liste bir kez yüklenir; bir yerde yıldız değişince tüm yıldızlar ve Listem sekmesi birlikte güncellenir.
import { useEffect, useState } from 'react'
import { api } from '../api/client'

let liste = null            // [{bolum_id, bolum_adi, toplam_uyum, ...}] | null (yüklenmedi)
let yukleniyor = null
const dinleyiciler = new Set()
const yay = () => dinleyiciler.forEach((f) => f(liste))

export function listemiYukle(zorla = false) {
  if (yukleniyor && !zorla) return yukleniyor
  yukleniyor = api.listemGetir()
    .then((l) => { liste = Array.isArray(l) ? l : []; yay(); return liste })
    .catch(() => { liste = liste || []; yay(); return liste })
  return yukleniyor
}

export function useListem() {
  const [l, setL] = useState(liste)
  useEffect(() => {
    dinleyiciler.add(setL)
    if (liste === null) listemiYukle()
    return () => { dinleyiciler.delete(setL) }
  }, [])
  return l
}

export async function listemDegistir(bolumId, ad) {
  const varMi = (liste || []).some((x) => x.bolum_id === bolumId)
  const onceki = liste
  // iyimser güncelleme: yıldız anında dolsun/boşalsın
  liste = varMi ? (liste || []).filter((x) => x.bolum_id !== bolumId) : [{ bolum_id: bolumId, bolum_adi: ad, toplam_uyum: null }, ...(liste || [])]
  yay()
  try {
    if (varMi) await api.listedenCikar(bolumId)
    else { await api.listeyeEkle(bolumId); listemiYukle(true) }   // uyum/alan bilgisi sunucudan gelsin
    return null
  } catch (e) {
    liste = onceki; yay()
    return e.detail || 'Listen güncellenemedi.'
  }
}

export default function FavoriYildiz({ id, ad, buyuk = false, etiketli = false }) {
  const l = useListem()
  const [hata, setHata] = useState(null)
  if (!id) return null
  const secili = (l || []).some((x) => x.bolum_id === id)
  async function tikla(e) {
    e.stopPropagation(); e.preventDefault()
    const h = await listemDegistir(id, ad)
    setHata(h)
    if (h) setTimeout(() => setHata(null), 3500)
  }
  return (
    <button type="button" className={`fav-yildiz${secili ? ' secili' : ''}${buyuk ? ' buyuk' : ''}${etiketli ? ' etiketli' : ''}`}
      onClick={tikla} aria-pressed={secili} title={hata || (secili ? 'Listemden çıkar' : 'Listeme ekle')}>
      <span className="fy-ikon" aria-hidden="true">{secili ? '★' : '☆'}</span>
      {etiketli && <span>{secili ? 'Listemde' : 'Listeme ekle'}</span>}
      {hata && <span className="fav-hata">{hata}</span>}
    </button>
  )
}
