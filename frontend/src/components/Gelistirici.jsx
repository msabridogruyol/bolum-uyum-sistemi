// [2026-10-11] Sistem Hakkında — geliştirici bilgisi (öğrenci, okul yetkilisi ve süper admin "Hakkında" sayfalarında).
export const GELISTIRICI = { ad: 'Mustafa Sabri Doğruyol', yil: '2025–2026', eposta: 'info@msabridogruyol.com' }

export default function Gelistirici() {
  return (
    <div className="card gl-kart">
      <div className="gl-amblem" aria-hidden="true">🌱</div>
      <div style={{ minWidth: 0 }}>
        <div className="gl-ust">Filizyol hakkında</div>
        <div className="gl-metin">
          Filizyol, <b>{GELISTIRICI.ad}</b> tarafından <b>{GELISTIRICI.yil}</b> yıllarında geliştirilmiştir.
        </div>
        <div className="gl-iletisim">✉️ İletişim: <a href={`mailto:${GELISTIRICI.eposta}`}>{GELISTIRICI.eposta}</a></div>
      </div>
    </div>
  )
}
