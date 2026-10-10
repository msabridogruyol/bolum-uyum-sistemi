// [2026-10-10] Sayfanın en altındaki şerit: © yıl · okul · kullanıcı. Üst çizgisi okul renginde.
export default function AltSerit({ okul, kisi, rol }) {
  const yil = new Date().getFullYear()
  return (
    <footer className="alt-serit">
      <span>© {yil} {okul || 'Filizyol'}</span>
      <span className="as-orta">🌱 Filizyol · Kendi yolunu filizlendir</span>
      {kisi && <span>{kisi}{rol ? ` · ${rol}` : ''}</span>}
    </footer>
  )
}
