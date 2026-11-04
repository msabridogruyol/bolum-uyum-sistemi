// [2026-10-10] Sayfanın en altındaki şerit: © yıl · okul · kullanıcı. Üst çizgisi okul renginde.
// [2026-11-04] Ortada sistemin son güncellenme zamanı (gün.ay.yıl saat:dakika:saniye).
import { tarihSaniye, useSonGuncelleme } from '../yardimci/guncelleme'

export default function AltSerit({ okul, kisi, rol }) {
  const yil = new Date().getFullYear()
  const { son } = useSonGuncelleme()
  return (
    <footer className="alt-serit">
      <span>© {yil} <span translate="no">{okul || 'Filizyol'}</span></span>
      <span className="as-orta">🌱 Filizyol · Kendi yolunu filizlendir</span>
      {son && <span className="as-guncelleme" title="Sistemin son güncellenme zamanı">Son güncelleme: {tarihSaniye(son)}</span>}
      {kisi && <span>{kisi}{rol ? ` · ${rol}` : ''}</span>}
    </footer>
  )
}
