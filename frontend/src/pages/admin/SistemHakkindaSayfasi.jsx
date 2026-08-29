import { useState } from 'react'

function Bolum({ baslik, ikon, children, varsayilanAcik }) {
  const [acik, setAcik] = useState(!!varsayilanAcik)
  return (
    <div className="card" style={{ cursor: 'pointer' }} onClick={() => setAcik((a) => !a)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: acik ? 14 : 0 }}>
        <span style={{ fontSize: 20 }}>{ikon}</span>
        <div className="ct" style={{ marginBottom: 0, flex: 1 }}>{baslik}</div>
        <span style={{ fontSize: 11, color: 'var(--tx3)' }}>{acik ? '▲' : '▼'}</span>
      </div>
      {acik && <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.7 }}>{children}</div>}
    </div>
  )
}

function Madde({ children }) {
  return <div style={{ display: 'flex', gap: 8, marginBottom: 6 }}><span style={{ color: 'var(--pu)', flexShrink: 0 }}>•</span><span>{children}</span></div>
}

export default function SistemHakkindaSayfasi() {
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Sistem Hakkında</div>
        <div className="ps">
          Bölüm Uyum Sistemi'nin uçtan uca nasıl çalıştığının teknik özeti — bu sayfa yalnızca bilgilendirme
          amaçlıdır, buradan hiçbir veri düzenlenemez.
        </div>
      </div>

      <Bolum ikon="🎯" baslik="1. Sistemin Genel Amacı" varsayilanAcik>
        <p style={{ marginBottom: 10 }}>
          Sistem, bir öğrencinin değerler, kişilik, iş ortamı tercihleri ve bilişsel eğilimlerini ölçüp,
          bunu 301 üniversite bölümünün "beklenen profili" ile karşılaştırarak kişiselleştirilmiş bölüm
          önerileri sunar. Süreç 5 ana aşamadan oluşur:
        </p>
        <Madde>Öğrenci Değerlendirmesi (K1-K5) — öğrenciden veri toplama</Madde>
        <Madde>Bölüm-Meslek Eşleştirme Pipeline'ı — bölümlerin "beklenen profilini" hesaplama (offline, periyodik)</Madde>
        <Madde>Uyum Hesaplama — öğrenci profilini bölüm profilleriyle karşılaştırma</Madde>
        <Madde>Sonuç Sunumu — sıralama, keşfet, gizlilik kuralları</Madde>
        <Madde>Koçluk — hedef bölüme özel gelişim takibi</Madde>
      </Bolum>

      <Bolum ikon="📝" baslik="2. Aşama 1 — Öğrenci Değerlendirmesi (K1-K5)">
        <p style={{ marginBottom: 10 }}>
          Öğrenci, sırasıyla 4 zorunlu katmanı ve (koşullu olarak açılan) 1 derinleşme katmanını tamamlar.
          Her katman, belirli sayıda <b>değişkeni</b> (31 tanesi K1-K4'te sabit) Likert (5'li ölçek) veya
          SJT (durumsal yargı) sorularıyla ölçer:
        </p>
        <Madde><b>K1 — Değerler/Motivasyon</b> (7 değişken, D1-D7): güvence, ekonomik getiri, statü, anlam, sosyal etki, özerklik, estetik/yaratıcılık</Madde>
        <Madde><b>K2 — Kişilik & Çalışma Tarzı</b> (8 değişken, P1-P8): dışadönüklük, uyumluluk, sorumluluk, nevrotiklik, deneyime açıklık, rutin/dinamik tercihi, risk toleransı, liderlik isteği</Madde>
        <Madde><b>K3 — İş Ortamı & Yetkinlik</b> (7 değişken, I1-I7): zaman yönetimi, çatışma yönetimi, kriz kararı, etik, inisiyatif, geri bildirime açıklık, yönetim/strateji yetkinliği</Madde>
        <Madde><b>K4 — Alan Eğilimi & Bilişsel Stil</b> (9 değişken, A1-A9): sayısal, sözel, sosyal, yaratıcı, doğa/laboratuvar, fiziksel, yapılandırılmış/sezgisel stil, girişimcilik eğilimi</Madde>
        <Madde><b>K5 — Dal Derinleşme</b> (koşullu): K4 sonucuna göre, belirli bir eşiği (%) geçen "dal"lar (örn. Sayısal Ağırlıklı Derinleşme) otomatik açılır, ek sorular sorulur</Madde>
        <p style={{ marginTop: 10 }}>
          Her katman tamamlandığında, o katmandaki her değişken için 0-100 arası bir puan hesaplanır ve
          <code> ogrenci_degisken_skorlari</code> tablosuna, o "tur"a (değerlendirme dönemi) bağlı olarak kaydedilir.
        </p>
      </Bolum>

      <Bolum ikon="🧬" baslik="2. Aşama 2 — Bölüm-Meslek Eşleştirme Pipeline'ı (Offline)">
        <p style={{ marginBottom: 10 }}>
          Bu aşama öğrenciden bağımsızdır — <b>periyodik olarak</b> (örn. 6 ayda bir), yöneticinin kendi
          bilgisayarında çalıştırdığı bir işlemdir. Amaç: 301 bölümün her birinin, 31 değişkende
          <b> "beklenen profilini"</b> (agirlik_degeri) hesaplamak.
        </p>
        <Madde>7.764 gerçek mesleğin her biri, <b>3 farklı embedding modeli</b> ile 31 değişkenin her birinde puanlanır</Madde>
        <Madde>Her meslek, isim/tanım benzerliğine göre bölümlerle eşleştirilir (benzerlik skoru)</Madde>
        <Madde>Bir bölüme "yakın" mesleklerin puanları ağırlıklı ortalamayla birleştirilip o bölümün 31 değişkenlik profili çıkarılır</Madde>
        <Madde><b>etkin_meslek_sayisi</b> ve <b>agirlikli_varyans</b>, bu hesaplamanın ne kadar güvenilir olduğunun göstergesidir (admin-only, öğrenciye asla gösterilmez)</Madde>
        <p style={{ marginTop: 10, padding: '10px 12px', background: 'var(--aml)', borderRadius: 8, color: 'var(--am)' }}>
          ⚠️ Bilinen kısıt: embedding modelleri bazen kelime <i>kökü</i> benzerliğini anlam benzerliği sanabiliyor
          (örn. "Hukuk" ↔ "Hakkak"). Bu yüzden pipeline çıktısı, admin panelindeki <b>Pipeline Sonuçları</b>
          ekranında önce önizlenip onaylanmadan canlıya yansımaz.
        </p>
      </Bolum>

      <Bolum ikon="⚖️" baslik="3. Aşama 3 — Uyum Hesaplama (10 Yöntemli Karar Motoru)">
        <p style={{ marginBottom: 10 }}>
          Bir öğrenci K1-K4'ün tamamını bitirdiğinde, 31 değişkenlik profili, <b>yayında olan her bölümün</b>
          profiliyle karşılaştırılır. Bu, klasik bir "en yakın olan kazanır" hesabı değil — <b>10 farklı
          Çok Kriterli Karar Verme (ÇKKV) yöntemi</b> aynı anda çalıştırılır:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 6, marginBottom: 10, fontSize: 11.5 }}>
          {['WSM', 'WPM', 'WASPAS', 'TOPSIS', 'VIKOR', 'GRA', 'MOORA', 'COPRAS', 'EDAS', 'MABAC'].map((y) => (
            <div key={y} style={{ background: 'var(--sur2)', borderRadius: 8, padding: '6px 4px', textAlign: 'center', fontWeight: 700 }}>{y}</div>
          ))}
        </div>
        <Madde>Her yöntem, (öğrenci puanı - bölüm beklentisi) farkına dayalı bir "performans matrisi" üzerinde çalışır</Madde>
        <Madde>10 yöntemin sonucu 0-100'e normalize edilip <b>ortalaması</b> alınır → nihai <b>toplam_uyum</b> puanı</Madde>
        <Madde><b>Kendall's W</b> hesaplanır — 10 yöntem ne kadar "hemfikir", bu bir güvenilirlik/sağlamlık kontrolüdür</Madde>
        <Madde>Bu ham skorlar (yontem_skorlari, kendall_w) yalnızca admin şemasında bulunur — öğrenciye asla gösterilmez</Madde>
      </Bolum>

      <Bolum ikon="📊" baslik="4. Aşama 4 — Sonuç Sunumu ve Gizlilik Kuralları">
        <p style={{ marginBottom: 10 }}>Öğrenciye üç farklı sonuç ekranı sunulur:</p>
        <Madde><b>Bölüm Uyumum</b> — yalnızca K1-K4'ün 4'ü de bitince, en yüksek uyumlu ilk 20 bölüm (yarım profille yanıltıcı sıralama üretilmez)</Madde>
        <Madde><b>Tüm Bölümleri Keşfet</b> — profil eksik olsa bile çalışır, bölüm bilgisi + katman ortalamaları gösterir</Madde>
        <Madde><b>Genel Sonuçlar</b> — K1-K4'ün özet profili, gerçek "öne çıkan güçler/gelişim alanları"</Madde>
        <p style={{ marginTop: 10, padding: '10px 12px', background: 'var(--rel, #fdecea)', borderRadius: 8, color: 'var(--re)' }}>
          🔒 Kritik kural: <code>yontem_skorlari</code>, <code>kendall_w</code>, <code>agirlikli_varyans</code>,
          <code> etkin_meslek_sayisi</code> gibi alanlar öğrenci API şemalarında hiç tanımlı değildir —
          kodda "gizlenmiyor", yapısal olarak <b>var olamaz</b>.
        </p>
      </Bolum>

      <Bolum ikon="🧭" baslik="5. Aşama 5 — Koçluk Modülü (Hedef Bölüm)">
        <p style={{ marginBottom: 10 }}>
          Öğrenci, herhangi bir bölümü (yalnızca 1 tanesini, odaklanma ilkesiyle) <b>hedef</b> olarak seçebilir.
        </p>
        <Madde><b>Gap Analizi:</b> her değişkende (öğrenci puanı − bölüm beklentisi) hesaplanır, 5 kademeye ayrılır (belirgin üstün → belirgin altında)</Madde>
        <Madde><b>Öncelik Skoru:</b> fark büyüklüğü × o değişkenin bölüm için ağırlığı — hangi boyutun geliştirilmesi en çok fark yaratır, onu öne çıkarır</Madde>
        <Madde><b>Gelişim Yol Haritası:</b> geliştirilmesi gereken boyutlar, tahmini efora göre "Şimdi / Bu Dönem / Uzun Vadede" olarak gruplanır</Madde>
        <Madde><b>Tur Karşılaştırması:</b> öğrenci yeniden değerlendirildiğinde (min. 120 gün sonra), önceki turla karşılaştırıp gerçek gelişimi gösterir</Madde>
      </Bolum>

      <Bolum ikon="🛠️" baslik="6. Admin Süreçleri — Veri Nasıl Yönetiliyor">
        <Madde><b>Bölümler:</b> Taslak → Test Ediliyor → Yayında akışı; her geçiş gerekçeli ve audit log'a yazılı</Madde>
        <Madde><b>Soru Bankası:</b> sorular hiç silinmez, yalnızca pasife alınır (geçmiş öğrenci oturumları bozulmasın diye)</Madde>
        <Madde><b>Katman Ağırlıkları:</b> K1-K4'ün toplam %100'lük ağırlık dağılımı; yeni versiyon eskisini otomatik pasife alır ama silmez</Madde>
        <Madde><b>Pipeline Sonuçları:</b> bilgisayarınızda üretilen bölüm profili çıktısı, önce taslak tabloya gider, istatistiksel önizleme sonrası yalnızca süper admin onayıyla canlıya (yeni bir versiyon olarak) yazılır</Madde>
        <Madde><b>Audit Log:</b> durum değişikliği, rol değişikliği, pipeline onayı gibi kritik her işlem kalıcı olarak kaydedilir</Madde>
      </Bolum>
    </div>
  )
}
