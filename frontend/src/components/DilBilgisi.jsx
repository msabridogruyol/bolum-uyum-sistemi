// [2026-10-12] Sistem Hakkında — dil desteği ve çeviri uyarısı (öğrenci, okul yetkilisi ve süper admin "Hakkında" sayfalarında).
// Değerlendirme sorularının çeviri uyarısı soru ekranında değil, burada gösterilir.
import { DILLER } from '../yardimci/dil'

export default function DilBilgisi() {
  return (
    <div className="card gl-kart">
      <div className="gl-amblem" aria-hidden="true">🌐</div>
      <div style={{ minWidth: 0 }}>
        <div className="gl-ust">Dil desteği</div>
        <div className="gl-metin">Filizyol Türkçe dışında 12 dilde kullanılabilir. Dil, giriş ekranından ya da Ayarlar sayfasından seçilir.</div>
        <div className="dl-diller" translate="no">{DILLER.map((d) => <span key={d.kod}>{d.bayrak} {d.ad}</span>)}</div>
        <ul className="dl-liste">
          <li>Çeviriler yapay zekâ ile hazırlanmıştır; bazı ifadeler tam olarak doğru olmayabilir.</li>
          <li>Değerlendirme soruları anlamları korunarak çevrilmiştir. Soruların geçerlilik ve güvenilirlik çalışması Türkçe sürümle yapılmıştır; bu nedenle başka bir dilde verilen cevaplarla elde edilen sonuçlar daha az kesin olabilir.</li>
          <li>KVKK metinleri hukuken bağlayıcı Türkçe asıllarıyla gösterilir. PDF raporlar şimdilik Türkçe hazırlanır.</li>
        </ul>
      </div>
    </div>
  )
}
