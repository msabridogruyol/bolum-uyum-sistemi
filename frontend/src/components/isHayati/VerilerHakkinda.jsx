// [2026-10-10] "Veriler hakkında" açılır notu — İş Hayatı sayfasında ve sekmelerde kullanılabilir.
// kaynaklar: veri.veri_kaynaklari (GET /ogrenci/is-hayati/ozet veya /bolum/{id})
import { useState } from 'react'

export default function VerilerHakkinda({ kaynaklar = [] }) {
  const [acik, setAcik] = useState(false)
  return (
    <div className="card" style={{ marginTop: 16, padding: '12px 16px' }}>
      <button onClick={() => setAcik(!acik)} aria-expanded={acik}
        style={{ all: 'unset', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, fontWeight: 700, color: 'var(--tx2)', width: '100%' }}>
        <span aria-hidden="true">ℹ️</span> Veriler hakkında <span style={{ marginLeft: 'auto', color: 'var(--tx3)' }}>{acik ? '▴' : '▾'}</span>
      </button>
      {acik && (
        <div style={{ fontSize: 12, color: 'var(--tx2)', lineHeight: 1.55, marginTop: 10 }}>
          {kaynaklar.length > 0 ? (
            <ul style={{ margin: '0 0 8px', paddingLeft: 18 }}>
              {kaynaklar.map((k, i) => (
                <li key={i}><b>{k.ad}</b> — {k.kaynak}{k.yil ? ` (veri yılı / dönem: ${k.yil})` : ''}</li>
              ))}
            </ul>
          ) : <div style={{ marginBottom: 8 }}>Bu bölüm için henüz resmî veri yüklenmedi.</div>}
          <div>Değerler resmî kaynaklardan alınır ve <b>veri yılı</b> ile gösterilir. Yanında <b>“tahmini”</b> etiketi olan maaşlar,
            TÜİK'in meslek grubu ortalamasının o yılki asgari ücrete oranlanıp bugünkü asgari ücretle çarpılmasıyla hesaplanır; gerçek bir
            teklif değildir. İlk iş maaşı çoğu zaman ortalamanın altındadır; şehir, şirket ve deneyimle çok değişir.</div>
        </div>
      )}
    </div>
  )
}
