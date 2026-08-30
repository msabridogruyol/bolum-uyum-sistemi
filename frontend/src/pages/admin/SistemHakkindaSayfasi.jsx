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
        <Madde>Meslek veri kaynağı: <b>ESCO</b> (Avrupa Birliği'nin resmi meslek sınıflandırması) — 3.039 meslek, her biri için gerçek, uzmanlarca yazılmış açıklama içerir</Madde>
        <Madde>Bölüm veri kaynağı: sistemin kendi 301 bölümü, her biri için yazılmış kısa açıklama</Madde>
        <Madde>Her meslek, isim/tanım benzerliğine göre bölümlerle eşleştirilir (benzerlik skoru)</Madde>
        <Madde>Bir bölüme "yakın" mesleklerin puanları ağırlıklı ortalamayla birleştirilip o bölümün 31 değişkenlik profili çıkarılır</Madde>
        <Madde><b>etkin_meslek_sayisi</b> ve <b>agirlikli_varyans</b>, bu hesaplamanın ne kadar güvenilir olduğunun göstergesidir (admin-only, öğrenciye asla gösterilmez)</Madde>

        <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Eşleştirme Neden İsme Değil, Açıklamaya Dayanıyor</div>
          <p style={{ marginBottom: 8 }}>
            Meslek ve bölüm eşleştirmesi, yalnızca <b>isimlerin</b> karşılaştırılmasıyla değil, her ikisinin
            <b> tam açıklama metninin anlamsal (context/meaning) benzerliğiyle</b> yapılır. Bunun nedeni: yalnızca
            isim kullanıldığında, aralarında gerçek bir anlam ilişkisi olmayan ama harf/hece düzeyinde benzer
            görünen kelimeler (örn. ortak bir kökten gelen ama tamamen farklı anlamlara sahip iki sözcük) modelin
            kafasını karıştırabiliyor. Tam açıklama kullanıldığında model, kelimenin yüzeysel görünümü yerine
            <b> gerçekte ne anlama geldiğine</b> odaklanıyor — bu da isim benzerliğinden kaynaklanan yanlış
            eşleşmeleri büyük ölçüde ortadan kaldırıyor.
          </p>
        </div>

        <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Çeviri Süreci</div>
          <Madde>Modellerden biri (model_c) İngilizce çalışıyor — ESCO'nun orijinal İngilizce meslek açıklamaları <b>doğrudan</b> kullanılıyor, çeviri gerekmiyor</Madde>
          <Madde>Bölüm açıklamaları, aynı İngilizce model için Türkçe'den İngilizce'ye çevriliyor (Helsinki-NLP makine çeviri modeli, yerel/offline — dış API kullanılmıyor)</Madde>
          <Madde>Meslek adları ve açıklamaları ise ESCO'dan İngilizce'den Türkçe'ye çevrilip Türkçe çalışan iki model için kullanılıyor</Madde>
          <Madde>Çeviri kalitesi, isim ile açıklamanın anlamsal olarak tutarlı olup olmadığını ölçen otomatik bir kontrolden geçiriliyor — tutarsız çıkan meslekler bir listeye yazılıp elle gözden geçiriliyor</Madde>
        </div>

        <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Hangi Aşamada Hangi Model(ler) Kullanılıyor</div>
          <table style={{ width: '100%', fontSize: 12.5, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--bor)' }}>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>Aşama</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>Kullanılan Model(ler)</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>Neden</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['Ana eşleştirme (00 → A2 → A3 → A4)', '3 model (model_a, model_b, model_c)', 'Üretim skoru — konsensüs güvenilirlik sağlar'],
                ['Bölüm açıklaması çevirisi (TR→EN)', 'Helsinki-NLP MT modeli', 'Model C\'nin İngilizce girdisi için'],
                ['Meslek adı/açıklaması çevirisi (EN→TR)', 'Helsinki-NLP MT modeli (tc-big-en-tr)', 'ESCO kaynağı yalnızca İngilizce'],
                ['Çeviri tutarlılık kontrolü', 'Yalnızca model_a (1 model)', 'Hızlı ön tarama — üretim skoru değil, tanılama amaçlı'],
                ['Soru geçerlilik testi', '3 model (model_a, model_b, model_c)', 'Üretim kalite kontrolü — konsensüs önemli'],
              ].map((satir, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--bor)' }}>
                  {satir.map((hucre, j) => <td key={j} style={{ padding: '6px 8px', color: j === 0 ? 'var(--tx)' : 'var(--tx2)' }}>{hucre}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Veri Kalitesi Kontrolleri</div>
          <Madde><b>Güven eşiği (z-skoru):</b> bir mesleğin bir bölümle "ilişkili" sayılması için, o ilişkinin ortalamanın en az 1 standart sapma üstünde olması gerekir — rastgele/zayıf eşleşmeler bu şekilde elenir</Madde>
          <Madde><b>Model konsensüsü:</b> 3 bağımsız model kullanılır; bir eşleşme kaç modelde tutarlı çıktıysa, önceliği o kadar yüksektir</Madde>
          <Madde>Sözde bilim/akademik olmayan kategoriler (üniversite eğitimiyle ilgisi olmayan meslekler), kaynak veriden ayıklanır</Madde>
        </div>

        <p style={{ marginTop: 14, padding: '10px 12px', background: 'var(--aml)', borderRadius: 8, color: 'var(--am)' }}>
          ⚠️ Bu süreç istatistiksel bir yöntemdir, kesin/matematiksel sıfır hata garantisi vermez. Bu yüzden
          pipeline çıktısı, admin panelindeki <b>Pipeline Sonuçları</b> ekranında önce önizlenip onaylanmadan
          canlıya yansımaz.
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
