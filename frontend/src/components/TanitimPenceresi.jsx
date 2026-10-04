import { useState } from 'react'

// [2026-10-03] İlk girişte sistemi basitçe anlatan tanıtım penceresi (5 adım).
// Görülüp görülmediği tarayıcıda saklanır; Ayarlar'dan tekrar açılabilir.
const ADIMLAR = [
  {
    ikon: '🌱',
    baslik: 'Hoş geldin!',
    metin: 'Filizyol, sana en uygun üniversite bölümlerini bulmana ve o bölüme hazırlanmana yardım eder. Ben Filiz, gelişim koçun; bu yolda sana eşlik edeceğim.',
    maddeler: ['Doğru ya da yanlış cevap yok', 'Hızlı değil, samimi cevap ver', 'Her katman yaklaşık 4-6 dakika sürer'],
  },
  {
    ikon: '🧭',
    baslik: 'Adım adım ilerlersin',
    metin: 'Seni dört katmanda tanıyoruz. Katmanlar sırayla açılır; birini bitirince bir sonrakine geçersin.',
    maddeler: ['K1 · Değerlerin — neyi önemsersin?', 'K2 · Kişiliğin — nasıl çalışırsın?', 'K3 · İş ortamı — nasıl davranırsın?', 'K4 · Alan eğilimin — neye yatkınsın?', 'K5 · Sana özel alan soruları — K4 sonucuna göre açılır'],
  },
  {
    ikon: '⚖️',
    baslik: 'Uyumun nasıl hesaplanıyor?',
    metin: 'Cevaplarından senin profilini çıkarıyoruz. Her bölümün de, mezunlarının çalıştığı binlerce meslekten türetilmiş bir profili var. İki profili 10 farklı yöntemle karşılaştırıp bir uyum yüzdesi buluyoruz.',
    maddeler: ['301 bölüm, 3.000\'den fazla meslek', 'Seni başkalarıyla değil, kendi profilinle değerlendiririz', 'Sonuç bir tavsiyedir, kesin karar değil'],
  },
  {
    ikon: '🎯',
    baslik: 'Sonra ne olacak?',
    metin: 'Sonuçların hazır olunca sana en uygun 10 bölümü görürsün. Birini hedef seçersen, o bölüme göre güçlü yönlerini ve gelişim alanlarını gösteririz.',
    maddeler: ['Tüm bölümleri keşfedebilirsin', 'Hedef bölümün için adım adım yol haritası', 'İlerlemeni işaretleyip takip edebilirsin'],
  },
  {
    ikon: '📝',
    baslik: 'Önce seni tanıyalım',
    metin: 'Başlamadan önce profilini doldur: adın, okulun ve sınıfın yeterli. Ardından ana sayfaya geçip ilk katmana başlayabilirsin.',
    maddeler: ['Okul ve sınıf zorunlu', 'Doğum tarihi ve cinsiyet tamamen isteğe bağlı', 'Bilgilerini Ayarlar\'dan her zaman değiştirebilirsin'],
  },
]

export default function TanitimPenceresi({ onBitir }) {
  const [adim, setAdim] = useState(0)
  const a = ADIMLAR[adim]
  const son = adim === ADIMLAR.length - 1

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(20, 16, 10, 0.55)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div className="card" style={{ maxWidth: 480, width: '100%', margin: 0, padding: 28, boxShadow: '0 20px 60px rgba(0,0,0,.25)' }}>
        <div style={{ fontSize: 44, textAlign: 'center', marginBottom: 8 }}>{a.ikon}</div>
        <div style={{ fontSize: 20, fontWeight: 700, textAlign: 'center', marginBottom: 10 }}>{a.baslik}</div>
        <div style={{ fontSize: 13.5, color: 'var(--tx2)', lineHeight: 1.6, textAlign: 'center', marginBottom: 16 }}>{a.metin}</div>
        <div style={{ background: 'var(--sur2)', borderRadius: 12, padding: '12px 16px', marginBottom: 20 }}>
          {a.maddeler.map((m) => (
            <div key={m} style={{ fontSize: 12.5, color: 'var(--tx2)', padding: '3px 0' }}>✓ {m}</div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginBottom: 18 }}>
          {ADIMLAR.map((_, i) => (
            <div key={i} style={{ width: i === adim ? 20 : 8, height: 8, borderRadius: 4, background: i === adim ? 'var(--pu)' : 'var(--bor)', transition: 'all .2s' }} />
          ))}
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          {adim > 0 && <button className="btn sec" style={{ flex: 1 }} onClick={() => setAdim(adim - 1)}>← Geri</button>}
          <button className="btn" style={{ flex: 2 }} onClick={() => (son ? onBitir() : setAdim(adim + 1))}>
            {son ? 'Profilimi Doldur →' : 'Devam →'}
          </button>
        </div>
      </div>
    </div>
  )
}
