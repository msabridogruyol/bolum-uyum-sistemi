// [2026-10-10] CV içeriğinin sade (PDF'e benzer) önizlemesi — öğrencinin CV Atölyesi'nde ve okul panelinde (paylaşılan CV) ortak.
// icerik: { kisisel{ad,eposta,sehir}, profil, bolumler[{kod,baslik,gizli,ogeler}] } — liste öğelerinde onayli sunucudan gelir.
const TIP = { egitim: 'liste', deneyim: 'liste', projeler: 'liste', gonulluluk: 'liste', oduller: 'liste', sertifikalar: 'liste', beceriler: 'etiket', diller: 'dil', ilgi: 'etiket' }

export const gorunenOgeler = (b) => (b.gizli ? [] : (b.ogeler || []).filter((o) => !(o && typeof o === 'object' && o.gizli)))

export default function CvOnizleme({ icerik, kucuk }) {
  if (!icerik) return null
  const k = icerik.kisisel || {}
  return (
    <div className={`cva-onizleme${kucuk ? ' kucuk' : ''}`} aria-label="CV önizlemesi">
      <div className="cva-on-ad">{k.ad || 'Ad Soyad'}</div>
      <div className="cva-on-iletisim">{[k.eposta, k.sehir].filter(Boolean).join(' | ') || 'e-posta | şehir'}</div>
      {icerik.profil && (<><div className="cva-on-baslik">Profil</div><p>{icerik.profil}</p></>)}
      {icerik.bolumler.map((b) => {
        const og = gorunenOgeler(b).filter((o) => (typeof o === 'string' ? o : o.baslik || o.dil))
        if (!og.length) return null
        const tip = TIP[b.kod]
        return (
          <div key={b.kod}>
            <div className="cva-on-baslik">{b.baslik}</div>
            {tip === 'liste' && og.map((o) => (
              <div key={o.id} className="cva-on-oge">
                <div><b>{o.baslik}</b>{o.kurum ? `, ${o.kurum}` : ''}{o.donem ? ` | ${o.donem}` : ''}
                  {o.onayli && <span className="cva-onay" title={o.onaylayan ? `Onaylayan: ${o.onaylayan}` : undefined}>OKUL ONAYLI</span>}</div>
                {(o.aciklama || '').split('\n').map((s) => s.replace(/^[\s\-•]+/, '').trim()).filter(Boolean).map((s, i) => <div key={i} className="cva-on-madde">• {s}</div>)}
              </div>
            ))}
            {tip === 'etiket' && <p>{og.join(', ')}</p>}
            {tip === 'dil' && <p>{og.map((d) => `${d.dil} (${d.seviye})`).join(', ')}</p>}
          </div>
        )
      })}
    </div>
  )
}
