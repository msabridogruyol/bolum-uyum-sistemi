// [2026-10-10] "Güçlü / çok güçlü" ve diğer düzey ifadelerinin nasıl okunacağı — öğrenci ve veli dilinde, açılır kapanır.
import { useState } from 'react'
import { BANTLAR, bantAraligi } from '../yardimci/seviye'

// Bantlar ve açıklamalar yardimci/seviye.js'ten gelir (tüm ekranlar ve PDF raporu aynı ölçeği kullanır).
const SINIF = { cok_guclu: 'pr-g2', guclu: 'pr-g1', ortanin_ustu: 'pr-o', orta: 'pr-o', gelisime_acik: 'pr-d' }

export default function PuanRehberi({ baslik = 'Bu ifadeler ne demek? Sonuçlarını nasıl okumalısın?', bolumlu = true }) {
  const [acik, setAcik] = useState(false)
  return (
    <div className={`puan-rehberi${acik ? ' acik' : ''}`}>
      <button type="button" className="pr-bas" onClick={() => setAcik(!acik)} aria-expanded={acik}>
        <span>ℹ️ {baslik}</span><span>{acik ? '▴' : '▾'}</span>
      </button>
      {acik && (
        <div className="pr-govde">
          <p><b>Bu bir not değil, eğilimdir.</b> Puanların, cevaplarına göre bir özelliğe ne kadar yatkın olduğunu gösterir. Yüksek ya da düşük olmak tek başına iyi veya kötü değildir.</p>
          <div className="pr-tablo">
            {BANTLAR.map((b) => (
              <div key={b.kod}><b className={SINIF[b.kod]}>{b.ad}</b><span>({bantAraligi(b)}) {b.aciklama}</span></div>
            ))}
            {bolumlu && <div><b className="pr-b">Bölüm: Yüksek / Çok yüksek</b><span>Bu bölüm bu özelliği, bölümlerin çoğundan daha fazla gerektiriyor.</span></div>}
          </div>
          <p><b>Yorumlarken dikkat:</b></p>
          <ul>
            <li><b>Örüntüye bak, tek puana değil.</b> Birkaç güçlü özelliğin aynı bölümde buluşması, tek bir yüksek puandan daha anlamlıdır.</li>
            <li><b>Çok güçlü her zaman “daha iyi” demek değil.</b> Aşırı kullanılan güçlü yön zorlanma alanına dönüşebilir. Örneğin çok yüksek rekabetçilik ekip çalışmasını zorlaştırabilir.</li>
            <li><b>Sonuçlar değişebilir.</b> Lise yıllarında ilgi ve eğilimler gelişir. Yeniden değerlendirme bu yüzden belirli aralıklarla açılır.</li>
            <li><b>Kesin hüküm değil, konuşma başlangıcı.</b> Sonuçlarını rehber öğretmeninle ve ailenle birlikte değerlendir.</li>
          </ul>
        </div>
      )}
    </div>
  )
}
