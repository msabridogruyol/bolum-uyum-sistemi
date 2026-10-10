// [2026-10-10] İstatistik bileşenleri — ortak küçük bileşenler: araç ipucu, lejant, boş durum, çerçeve.
// Bileşen olmayan yardımcılar ./yardimci.js içinde.

// ── Araç ipucu ───────────────────────────────────────────────────────
// Değer önde ve güçlü, ad ikincil; seri anahtarı kısa çizgi. İçerik React metni (HTML enjekte edilmez).
export function Ipucu({ durum, genislik, baslik, satirlar }) {
  if (!durum) return null
  const g = genislik ?? durum.w ?? 9999
  const sol = durum.x < 90 ? '0%' : durum.x > g - 90 ? '-100%' : '-50%'
  const alta = durum.y < 70
  return (
    <div className="ist-ipucu" aria-hidden="true"
      style={{ left: durum.x, top: durum.y, transform: `translate(${sol}, ${alta ? '18px' : 'calc(-100% - 12px)'})` }}>
      {baslik != null && <div className="ist-ipucu-bas">{baslik}</div>}
      {satirlar.map((s, k) => (
        <div key={k} className="ist-ipucu-satir">
          {s.renk && <i className="ist-ipucu-anahtar" style={{ background: s.renk }} />}
          <b>{s.deger}</b>
          {s.ad != null && <span>{s.ad}</span>}
        </div>
      ))}
    </div>
  )
}

// ── Lejant: çubuk/alan için kutu, çizgi için kısa çizgi; metin her zaman metin renginde ──
export function Lejant({ ogeler, tur = 'kutu' }) {
  if (!ogeler?.length) return null
  return (
    <ul className="ist-lejant">
      {ogeler.map((o) => (
        <li key={o.ad}><i className={tur === 'cizgi' ? 'ist-lej-cizgi' : 'ist-lej-kutu'} style={{ background: o.renk }} />{o.ad}</li>
      ))}
    </ul>
  )
}

export function Bos({ mesaj = 'Henüz veri yok' }) {
  return <div className="ist-bos" role="note">{mesaj}</div>
}

/** Grafik çerçevesi: isteğe bağlı küçük başlık (GrafikKarti içinde genelde verilmez). */
export function Cerceve({ baslik, children, className = '' }) {
  return (
    <div className={`ist-grafik ${className}`}>
      {baslik && <div className="ist-baslik">{baslik}</div>}
      {children}
    </div>
  )
}

