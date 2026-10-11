// [2026-10-10] CV Atölyesi → ön yazı (motivasyon mektubu) şablonu: başvuru türüne göre paragraf paragraf yönlendirmeli doldurma.
// Metin CV ile birlikte (icerik.on_yazi) kaydedilir; okulla paylaşılan CV'ye ön yazı dahil edilmez.
import { useMemo, useState } from 'react'

const TURLER = {
  staj: { ad: 'Staj', ikon: '🧑‍💻', hedef: 'staj programına' },
  yari_zamanli: { ad: 'Yarı zamanlı iş', ikon: '☕', hedef: 'yarı zamanlı pozisyona' },
  burs: { ad: 'Burs', ikon: '🎓', hedef: 'burs programına' },
  gonullu: { ad: 'Gönüllülük', ikon: '🤝', hedef: 'gönüllü programına' },
}

const PARAGRAFLAR = [
  { kod: 'hitap', ad: 'Hitap', satir: 1,
    ipucu: { varsayilan: 'İlanda bir isim varsa kişiye adıyla seslen ("Sayın Ayşe Demir,"). Yoksa "Sayın Yetkili," yeterli. "Merhaba arkadaşlar" gibi samimi ifadeler kullanma.' },
    ornek: { varsayilan: 'Sayın Yetkili,' } },
  { kod: 'giris', ad: '1. Giriş — kimsin, neye başvuruyorsun?',
    ipucu: {
      varsayilan: 'Tek paragraf, 2–3 cümle yaz. Hangi okulda, kaçıncı sınıftasın? Hangi ilana ya da programa başvuruyorsun? İlanı nerede gördün?',
      burs: 'Hangi bursa başvurduğunu ve kısaca kim olduğunu yaz. Burs veren kurum seni tanımıyor. İlk cümlen net olsun.',
    },
    ornek: {
      varsayilan: '[Okul adı] 11. sınıf öğrencisiyim. Kurumunuzun web sitesinde yayımlanan yaz dönemi gözlem stajı ilanına başvurmak istiyorum.',
      burs: '[Okul adı] 12. sınıf öğrencisiyim ve [kurum] tarafından verilen lise öğrenci bursuna başvuruyorum.',
      gonullu: '[Okul adı] 10. sınıf öğrencisiyim. Kütüphanenizin hafta sonu çocuk atölyeleri için gönüllü arayışınızı okul panosunda gördüm.',
    } },
  { kod: 'neden', ad: '2. Neden burası?',
    ipucu: {
      varsayilan: 'Bu kurumu ya da ilanı neden seçtin? Kurumu araştırdığını göster. Yaptıkları bir işten, değerlerinden ya da programın içeriğinden söz et. Her başvuruda bu paragrafı yeniden yaz. Kopyala-yapıştır yaptığın hemen anlaşılır.',
      yari_zamanli: 'Bu işi neden istediğini dürüst ama olumlu bir dille yaz. Örneğin deneyim kazanmak, sorumluluk almak ya da kendi harçlığını çıkarmak. İş yerinin sana yakın olması ya da saatlerin okuluna uyması da geçerli bir nedendir.',
      burs: 'Bursun amacını oku ve kendi hedefinle bağla. Ailenin maddi durumundan söz edeceksen kısa, ölçülü ve doğru yaz. Acındırmaya çalışma; hedefini anlat.',
    },
    ornek: {
      varsayilan: 'Ekibinizin geliştirdiği eğitim uygulamalarını inceledim. Görme engelli öğrenciler için hazırladığınız sesli içerikler, yazılımın insanlara nasıl yardım edebileceğini bana gösterdi.',
      burs: 'Mühendislik okuyarak yenilenebilir enerji alanında çalışmak istiyorum. Bursunuzun öncelikle fen alanlarına yönelik olması bu hedefimle örtüşüyor.',
    } },
  { kod: 'katki', ad: '3. Ne getiriyorsun? (kanıtla)',
    ipucu: {
      varsayilan: 'CV\'ndeki en uygun 1–2 deneyimi seç ve somut anlat. Ne yaptın? Sonuç ne oldu (sayıyla)? "Çalışkan, dürüst" gibi sıfatları art arda yazma. İyi bir örnek bu özellikleri zaten gösterir.',
      yari_zamanli: 'İşte işine yarayacak özelliklerini bir örnekle göster. Örneğin dakiklik (okul nöbetleri), insanlarla iletişim (okul etkinliğinde misafir karşılama), yoğun tempoda sakin kalma.',
      burs: 'Ders başarını, sorumluluk aldığın işleri ve topluma katkını kısa örneklerle anlat. Burs verenler şu sorunun cevabını arar: "Bu öğrenciyi desteklersek ne olur?"',
      gonullu: 'Daha önce bir gruba yardım ettiğin, bir şey öğrettiğin ya da düzenli bir sorumluluk aldığın bir örnek ver.',
    },
    ornek: {
      varsayilan: 'Okul robotik takımında iki yıldır yazılım sorumlusuyum. Geçen yıl sensör kodunu yeniden yazarak robotun parkuru tamamlama süresini 40 saniyeden 28 saniyeye indirdik.',
      yari_zamanli: 'Okulumuzun bahar şenliğinde iki gün boyunca kermes standında çalıştım; yaklaşık 300 kişiye hizmet verdik ve kasa hesabını hatasız teslim ettim.',
    } },
  { kod: 'kapanis', ad: '4. Kapanış — ne zaman uygunsun, teşekkür',
    ipucu: {
      varsayilan: 'Uygun olduğun tarihleri ya da saatleri yaz. Görüşmeye hazır olduğunu söyle ve teşekkür et. Kısa tut.',
      yari_zamanli: 'Hangi gün ve saatlerde çalışabileceğini net yaz. Okul saatlerini ve sınav dönemlerini de hesaba kat. 18 yaşından küçüksen velinin onayıyla başvurduğunu da yazabilirsin.',
    },
    ornek: {
      varsayilan: 'Temmuz ve ağustos aylarında programa tam zamanlı katılabilirim. Başvurumu değerlendirdiğiniz için teşekkür eder, görüşme fırsatı için hazır olduğumu belirtmek isterim.',
      yari_zamanli: 'Cumartesi ve pazar günleri 09.00–18.00 arasında çalışabilirim. Velimin bilgisi ve onayıyla başvuruyorum. Değerlendirmeniz için teşekkür ederim.',
    } },
  { kod: 'imza', ad: 'İmza', satir: 2,
    ipucu: { varsayilan: '"Saygılarımla," yaz. Altına adını soyadını ve e-postanı ekle. Telefonunu yalnızca güvendiğin başvurularda ekle.' },
    ornek: { varsayilan: 'Saygılarımla,\n[Ad Soyad]\n[e-posta]' } },
]

const sec = (obj, tur) => obj[tur] || obj.varsayilan

export default function OnYazi({ onYazi, setOnYazi, ad, eposta }) {
  const tur = onYazi?.tur && TURLER[onYazi.tur] ? onYazi.tur : 'staj'
  const alanlar = onYazi?.alanlar || {}
  const [kopyalandi, setKopyalandi] = useState(false)
  const degis = (kod, v) => setOnYazi({ tur, alanlar: { ...alanlar, [kod]: v } })
  const metin = useMemo(() => PARAGRAFLAR.map((p) => (alanlar[p.kod] || '').trim()).filter(Boolean).join('\n\n'), [alanlar])
  const kelime = metin.split(/\s+/).filter(Boolean).length
  async function kopyala() {
    try { await navigator.clipboard.writeText(metin); setKopyalandi(true); setTimeout(() => setKopyalandi(false), 1800) } catch { /* izin yok */ }
  }
  return (
    <div>
      <div className="card">
        <div className="ct">✉️ Ön yazı ne işe yarar?</div>
        <div className="yp-ince" style={{ lineHeight: 1.6, fontSize: 12.5 }}>
          CV <b>ne yaptığını</b> anlatır. Ön yazı ise <b>neden bu başvuruyu yaptığını</b> anlatır. Yarım sayfayı geçmesin (150–300 kelime). Her başvuruda
          "Neden burası?" paragrafını yeniden yaz. Aynı mektubu herkese gönderirsen bu hemen fark edilir.
        </div>
        <div className="eu-filtre" style={{ marginTop: 12, marginBottom: 0 }} role="radiogroup" aria-label="Başvuru türü">
          {Object.entries(TURLER).map(([k, t]) => <button key={k} className={tur === k ? 'secili' : ''} role="radio" aria-checked={tur === k} onClick={() => setOnYazi({ tur: k, alanlar })}>{t.ikon} {t.ad}</button>)}
        </div>
      </div>
      <div className="cva-onyazi-duzen">
        <div>
          {PARAGRAFLAR.map((p) => (
            <div key={p.kod} className="card cva-paragraf">
              <div style={{ fontWeight: 800, fontSize: 13.5, marginBottom: 4 }}>{p.ad}</div>
              <div className="yp-ince" style={{ lineHeight: 1.55, marginBottom: 8 }}>{sec(p.ipucu, tur)}</div>
              <textarea className="auth-input" rows={p.satir || 4} maxLength={1500} value={alanlar[p.kod] || ''} onChange={(e) => degis(p.kod, e.target.value)}
                placeholder={sec(p.ornek, tur).replace('[Ad Soyad]', ad || '[Ad Soyad]').replace('[e-posta]', eposta || '[e-posta]')} />
              {!alanlar[p.kod] && (
                <button type="button" className="hg-link" onClick={() => degis(p.kod, sec(p.ornek, tur).replace('[Ad Soyad]', ad || '[Ad Soyad]').replace('[e-posta]', eposta || '[e-posta]'))}>
                  Örnekle başla (sonra kendine göre değiştir)
                </button>
              )}
            </div>
          ))}
        </div>
        <div className="cva-yapiskan">
          <div className="card">
            <div className="ct" style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
              <span>Önizleme · {TURLER[tur].ad}</span>
              <span style={{ color: kelime > 300 ? 'var(--re)' : kelime >= 150 ? 'var(--gr)' : 'var(--tx3)', textTransform: 'none', letterSpacing: 0 }}>{kelime} kelime</span>
            </div>
            {metin ? <div className="cva-mektup">{metin}</div> : <div className="yp-ince">Paragrafları doldurdukça mektubun burada görünür.</div>}
            {/\[[^\]]+\]/.test(metin) && <div className="yp-uyari" style={{ marginTop: 10, marginBottom: 0 }}>Köşeli parantezli yerleri ([Okul adı] gibi) kendi bilgilerinle değiştirmeyi unutma.</div>}
            <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
              <button className="btn" disabled={!metin} onClick={kopyala}>{kopyalandi ? '✓ Kopyalandı' : '📋 Metni kopyala'}</button>
            </div>
            <div className="yp-ince" style={{ marginTop: 8 }}>Ön yazın CV'nle birlikte kaydedilir ve yalnızca sende kalır. CV'ni okulla paylaşsan bile ön yazın paylaşılmaz.</div>
          </div>
        </div>
      </div>
    </div>
  )
}
