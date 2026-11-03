import { useNavigate } from 'react-router-dom'

// [2026-10-10] Güven puanı eşiğin altında kalan turda öğrenci sonuçlarını görür; üstte bu uyarı çıkar.
// Geçersiz turdan sonra bekleme süresi uygulanmaz: öğrenci yalnızca güveni düşük bölümü aynı turda yeniden yanıtlar
// (katman_servisi; tüm değerlendirme baştan yapılmaz). [2026-11-03] metin bu akışa göre düzeltildi.
export default function GecersizTurUyarisi({ ozet }) {
  const navigate = useNavigate()
  if (!ozet || !ozet.tur_tamamlandi_mi || ozet.sonuc_gecerli !== false) return null
  return (
    <div role="status" style={{
      display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
      background: 'var(--aml, #FDF1DC)', border: '1.5px solid var(--am, #D9A441)', borderRadius: 16,
      padding: '14px 20px', marginBottom: 20,
    }}>
      <span style={{ fontSize: 22 }}>⚠️</span>
      <div style={{ flex: 1, minWidth: 220 }}>
        <div style={{ fontWeight: 800, color: 'var(--tx)' }}>Bu değerlendirme doğrulanamadı</div>
        <div style={{ fontSize: 13, color: 'var(--tx2)', marginTop: 2 }}>
          Bazı bölümlerde cevapların doğrulanamadı (ör. dikkat sorularında hata, sekme değiştirme ya da tam ekrandan
          çıkma). Sonuçlarını yine de görebilirsin. Tüm değerlendirmeyi baştan yapman gerekmez; sorun çıkan bölümü
          yeniden yanıtlaman yeterli.
        </div>
      </div>
      <button className="btn" onClick={() => navigate('/katmanlar')}>Sorunlu bölümü yeniden çöz →</button>
    </div>
  )
}
