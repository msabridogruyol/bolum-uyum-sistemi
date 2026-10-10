// [2026-10-10] "Güçlü / çok güçlü" ve diğer düzey ifadelerinin nasıl okunacağı — öğrenci ve veli dilinde, açılır kapanır.
import { useState } from 'react'

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
            <div><b className="pr-g2">Çok güçlü</b><span>(75 ve üzeri) Bu eğilim sende belirgin; farklı sorularda tutarlı olarak öne çıktı.</span></div>
            <div><b className="pr-g1">Güçlü</b><span>(62–74) Çoğu durumda bu yönde tercih yapıyorsun.</span></div>
            <div><b className="pr-o">Ortanın üstü / Orta</b><span>(40–61) Duruma göre değişiyor; esnek kullanabildiğin bir alan.</span></div>
            <div><b className="pr-d">Gelişime açık</b><span>(40'ın altı) Şu an daha az tercih ettiğin bir yön; istersen çalışarak güçlenebilir.</span></div>
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
