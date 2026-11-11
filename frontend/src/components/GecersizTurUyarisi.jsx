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
        <div style={{ fontWeight: 800, color: 'var(--tx)' }}>Bir bölümü yeniden çözmen gerekiyor</div>
        <div style={{ fontSize: 13, color: 'var(--tx2)', marginTop: 2 }}>
          Bir bölümü çözerken dikkatini dağıtan birkaç durum oldu (ör. sekme değiştirme ya da tam ekrandan çıkma). Bu
          sonuçlar şimdilik ön bilgi sayılır. Tüm değerlendirmeyi baştan yapman gerekmez; o bölümü sakin bir zamanda
          yeniden çözmen yeterli.
        </div>
      </div>
      <button className="btn" onClick={() => navigate('/katmanlar')}>Sorunlu bölümü yeniden çöz →</button>
    </div>
  )
}
