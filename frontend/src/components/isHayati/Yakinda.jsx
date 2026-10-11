// [2026-10-10] Henüz hazırlanmamış İş Hayatı sekmeleri için yer tutucu.
export default function Yakinda({ ikon, baslik, aciklama, bolum }) {
  return (
    <div className="card" style={{ padding: '28px 22px', textAlign: 'center' }}>
      <div style={{ fontSize: 34, marginBottom: 6 }} aria-hidden="true">{ikon}</div>
      <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 6 }}>{baslik}</div>
      <div className="ps" style={{ margin: '0 auto', maxWidth: 520 }}>{aciklama}</div>
      <div style={{ display: 'inline-block', marginTop: 14, fontSize: 11.5, fontWeight: 800, color: 'var(--pu)', background: 'var(--pul)', padding: '4px 12px', borderRadius: 999 }}>
        Yakında{bolum?.ad ? ` · ${bolum.ad}` : ''}
      </div>
    </div>
  )
}
