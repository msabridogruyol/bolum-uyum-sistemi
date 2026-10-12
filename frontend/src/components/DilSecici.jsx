// [2026-10-12] Dil seçici — giriş ekranları, öğrenci Ayarlar sayfası ve yönetim menüsü.
// Seçim kişiye özeldir: tarayıcıda saklanır, giriş yapılmışsa hesaba da yazılır (başka cihazda da aynı dil açılır).
// Dil adları kendi dillerinde yazılır ve çevrilmez (translate="no").
import { DILLER, aktifDil, dilDegistir } from '../yardimci/dil'
import { api } from '../api/client'

export default function DilSecici({ kapsam = null, gorunum = 'kucuk' }) {
  const dil = aktifDil()
  const degistir = (e) => {
    const kod = e.target.value
    const kaydet = kapsam ? (k) => api.dilKaydet(k, kapsam) : null
    dilDegistir(kod, kaydet)
  }
  const secici = (
    <select className={`dil-secici ${gorunum}`} value={dil} onChange={degistir} aria-label="Dil" translate="no">
      {DILLER.map((d) => <option key={d.kod} value={d.kod}>{d.bayrak} {d.ad}</option>)}
    </select>
  )
  if (gorunum !== 'kart') return secici
  return (
    <div className="card" style={{ marginTop: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
      <div style={{ flex: 1, minWidth: 220 }}>
        <div className="ct" style={{ marginBottom: 2 }}>🌐 Dil</div>
        <div className="yp-ince">Sistemin hangi dilde görüneceğini seç. Seçimin hesabına kaydedilir.</div>
        {dil !== 'tr' && (
          <div className="yp-ince" style={{ marginTop: 6 }}>
            Çeviriler yapay zekâ ile hazırlanmıştır; bazı ifadeler tam doğru olmayabilir. Değerlendirme sorularının geçerlilik çalışması Türkçe sürümle yapılmıştır.
          </div>
        )}
      </div>
      {secici}
    </div>
  )
}
