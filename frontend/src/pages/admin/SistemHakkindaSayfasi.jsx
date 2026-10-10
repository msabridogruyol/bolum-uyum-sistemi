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
          Filizyol'un uçtan uca nasıl çalıştığının teknik özeti — bu sayfa yalnızca bilgilendirme
          amaçlıdır, buradan hiçbir veri düzenlenemez. Her bileşenin kaynakları ve hangi sayıların kurum içi
          karar olduğu <b>Kaynakça</b> sayfasındadır.
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
        <p style={{ marginTop: 10 }}>
          Bunların çevresinde okul bazında paketlerle açılan modüller (rehberlik, net takibi, anketler, tercih,
          portfolyo, Filiz vb.) çalışır — bkz. 11. bölüm.
        </p>
      </Bolum>

      <Bolum ikon="📝" baslik="2. Aşama 1 — Öğrenci Değerlendirmesi (K1-K5)">
        <p style={{ marginBottom: 10 }}>
          Öğrenci, sırasıyla 4 zorunlu katmanı (K1-K4) tamamlar; K1-K4 bitince kendisine 1 veya 2 derinleşme alanı
          (K5) açılır ve açılan alanlar bitmeden sonuç listesi gösterilmez. K1-K4 toplam <b>31 değişken</b> ölçer;
          sorular 4 tipten biridir (Likert, SJT/durum, kutup, kontrol — bkz. 7. bölüm):
        </p>
        <Madde><b>K1 — Değerler/Motivasyon</b> (7 değişken, D1-D7): güvence, ekonomik getiri, statü, anlam, sosyal etki, özerklik, estetik/yaratıcılık</Madde>
        <Madde><b>K2 — Kişilik & Çalışma Tarzı</b> (8 değişken, P1-P8): dışadönüklük, uyumluluk, sorumluluk, duygusal hassasiyet (P4), deneyime açıklık, rutin/dinamik tercihi, risk toleransı, liderlik isteği. P4 varsayılan olarak bölüm eşleşmesine girmez (parametre <code>eslesme_disi_degiskenler</code>, varsayılan "P4")</Madde>
        <Madde><b>K3 — İş Ortamı & Yetkinlik</b> (7 değişken, I1-I7): zaman yönetimi, çatışma yönetimi, kriz kararı, etik, inisiyatif, geri bildirime açıklık, yönetim/strateji yetkinliği</Madde>
        <Madde><b>K4 — Alan Eğilimi & Bilişsel Stil</b> (9 değişken, A1-A9): sayısal, sözel, sosyal, yaratıcı, doğa/laboratuvar, fiziksel, yapılandırılmış stil, sezgisel stil, girişimcilik eğilimi</Madde>
        <Madde><b>K5 — Alan Derinleşme</b> (koşullu): <b>17 üst alan</b> (Mühendislik, Bilişim & Yazılım, Sağlık & Rehabilitasyon … Turizm & Hizmet; kod U01-U17). Alan, öğrencinin K1-K4 sonrası bölüm listesine göre açılır: ilk 15 bölüm alanlarına göre gruplanır, 1. sıradaki bölümün alanı her zaman açılır; ikinci alan, en iyi 3 bölüm ortalaması ana alandan en çok 10 puan gerideyse açılır (en fazla <code>k5_max_dal_sayisi</code> = 2). Ana alanın tüm soruları, ikinci alanın yalnızca ilk 6 sorusu sorulur (en fazla 14 + 6 = 20). Eski K4 eşiği (<code>k5_esik_puani</code>) artık seçimde kullanılmıyor</Madde>
        <Madde>K5'te her alanın kendi iş türü eksenleri vardır (alan başına 4-11, toplam 129 değişken; ör. U01_M). Yerel veritabanında 187 aktif K5 sorusu var (alan başına 6-14)</Madde>
        <p style={{ marginTop: 10 }}>
          Her katman tamamlandığında, o katmandaki her değişken için 0-100 arası bir puan hesaplanır (aynı değişkene
          katkı veren tüm cevapların aritmetik ortalaması) ve <code> ogrenci_degisken_skorlari</code> tablosuna, o
          "tur"a (değerlendirme dönemi) bağlı olarak kaydedilir. Katman başlarken aktif soru listesi kilitlenir.
          İki tam tur arasındaki süre <code>yeniden_degerlendirme_min_gun</code> parametresinden okunur (varsayılan ve
          başlangıç verisi <b>120 gün</b>).
        </p>
      </Bolum>

      <Bolum ikon="🧬" baslik="3. Aşama 2 — Bölüm-Meslek Eşleştirme Pipeline'ı (Offline)">
        <p style={{ marginBottom: 10 }}>
          Bu aşama öğrenciden bağımsızdır — <b>periyodik olarak</b> (örn. 6 ayda bir), yöneticinin kendi
          bilgisayarında çalıştırdığı bir işlemdir. Amaç: 301 bölümün her birinin, 31 değişkende
          <b> "beklenen profilini"</b> (agirlik_degeri) hesaplamak. Pipeline betikleri bu kod deposunda değildir;
          sunucu yalnızca çıktıyı (xlsx/csv) alır. Admin panelindeki "pipeline durumu" uç noktası yer tutucudur
          (iş kuyruğu kurulmadı).
        </p>
        <Madde>Meslek veri kaynağı: <b>ESCO</b> (Avrupa Birliği'nin resmi meslek sınıflandırması) — 3.039 meslek, her biri için gerçek, uzmanlarca yazılmış açıklama içerir</Madde>
        <Madde>Bölüm veri kaynağı: sistemin kendi 301 bölümü, her biri için yazılmış kısa açıklama</Madde>
        <Madde>Her meslek, tam açıklama metninin anlamsal benzerliğine göre bölümlerle eşleştirilir (benzerlik skoru)</Madde>
        <Madde>Bir bölüme "yakın" mesleklerin puanları ağırlıklı ortalamayla birleştirilip o bölümün 31 değişkenlik profili çıkarılır; bir değişkende veri yoksa skor motoru nötr 50 kullanır</Madde>
        <Madde><b>etkin_meslek_sayisi</b> ve <b>agirlikli_varyans</b>, bu hesaplamanın ne kadar güvenilir olduğunun göstergesidir (admin-only, öğrenciye asla gösterilmez); sıralamada eşitlik bozucu olarak da kullanılır</Madde>

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
          <div className="ct" style={{ fontSize: 13 }}>3 Modelin Teknik Detayları</div>
          <table style={{ width: '100%', fontSize: 12.5, borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--bor)' }}>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>Model</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>Hugging Face Adı</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>Temel Mimari</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>Boyut</th>
                <th style={{ textAlign: 'left', padding: '6px 8px' }}>Yayın</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['model_a', 'nezahatkorkmaz/turkce-embedding-bge-m3', "BAAI/bge-m3'ün Türkçe fine-tune'u (XLM-RoBERTa)", '~568M parametre, 1024 boyut', 'Temel model 2024 (BGE-M3)'],
                ['model_b', 'emrecan/bert-base-turkish-cased-mean-nli-stsb-tr', 'BERT-base Türkçe (NLI+STS-b ile fine-tune)', '~110M parametre, 768 boyut', 'Ocak 2022'],
                ['model_c', 'BAAI/bge-large-en-v1.5', 'BERT tabanlı, İngilizce', '335M parametre, 1024 boyut', 'Eylül 2023'],
              ].map((satir, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--bor)' }}>
                  {satir.map((hucre, j) => <td key={j} style={{ padding: '6px 8px', color: j === 0 ? 'var(--tx)' : 'var(--tx2)', fontWeight: j === 0 ? 700 : 400 }}>{hucre}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ fontSize: 11.5, color: 'var(--tx3)', marginTop: 8 }}>
            model_a ve model_c aynı temel mimariden (BGE) türetildiği için birbirine yakın sonuçlar üretme eğiliminde
            olabilir — bu yüzden model_b'nin (tamamen farklı, düz BERT tabanlı bir aile) üçüncü bağımsız kaynak olarak
            sistemde bulunması, konsensüsün gerçekten çeşitli yöntemlerden geldiğinden emin olmak için önemlidir.
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
                ['Bölüm–alan eşleşmesi (K5, 17 üst alan)', 'Model yok — elle gözden geçirilmiş bolum_dal_eslesme + bölüm–eksen bağları (bolum_k5_baglari, 0–1)', 'Eski yapıda 8 dal A1-A9 profiline K-Means ile bulunuyordu; artık kullanılmıyor'],
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

      <Bolum ikon="⚖️" baslik="4. Aşama 3 — Uyum Hesaplama (10 Yöntemli Karar Motoru)">
        <p style={{ marginBottom: 10 }}>
          Bir öğrenci K1-K4'ün tamamını bitirdiğinde, profili (31 değişkenden eşleşme dışı bırakılanlar çıkarılınca —
          varsayılan P4 hariç 30), <b>yayında olan her bölümün</b> profiliyle karşılaştırılır. Bu, klasik bir "en yakın
          olan kazanır" hesabı değil — <b>10 farklı Çok Kriterli Karar Verme (ÇKKV) yöntemi</b> aynı anda çalıştırılır:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 6, marginBottom: 10, fontSize: 11.5 }}>
          {['WSM', 'WPM', 'WASPAS', 'TOPSIS', 'VIKOR', 'GRA', 'MOORA', 'COPRAS', 'EDAS', 'MABAC'].map((y) => (
            <div key={y} style={{ background: 'var(--sur2)', borderRadius: 8, padding: '6px 4px', textAlign: 'center', fontWeight: 700 }}>{y}</div>
          ))}
        </div>
        <Madde><b>Katman içi göreli ölçekleme:</b> öğrenci vektörü ve her bölüm satırı her katman içinde kendi ortalama/std'sine göre 50 + 15·z'ye çekilir (düzey değil "şekil" karşılaştırılır)</Madde>
        <Madde>Performans matrisi: hücre = max(0, 100 − |öğrenci − bölüm|) (ölçekli değerlerle); 10 yöntemin ortak girdisi budur, tüm kriterler fayda yönlüdür</Madde>
        <Madde>10 yöntemin sonucu min-max ile 0-100'e normalize edilip <b>aritmetik ortalaması</b> alınır → <b>toplam_uyum</b></Madde>
        <Madde><b>Alan tutarlılığı:</b> her üst alanın gücü = alandaki en iyi 3 bölümün ortalaması; puan += katsayı × (alan gücü − en güçlü alan) (parametre <code>alan_tutarlilik_katsayisi</code>, varsayılan 3; 0 = kapalı). Liste ayrıca elle yazılmış alan komşuluk tablosuyla gruplanır; alakasız alanların bölümleri silinmez, sona iner</Madde>
        <Madde><b>K5 etkisi:</b> tamamlanan alanın bölümleri için nihai = toplam_uyum + 0,50 × (dal_ici_uyum − 50), 0-100'e kırpılır (en fazla ±25). Veritabanındaki toplam_uyum değişmez; birleştirme okunurken yapılır</Madde>
        <Madde><b>Kendall's W</b> hesaplanır — 10 yöntem ne kadar "hemfikir", bu bir güvenilirlik/sağlamlık kontrolüdür</Madde>
        <Madde>Bu ham skorlar (yontem_skorlari, kendall_w) yalnızca admin şemasında bulunur — öğrenciye asla gösterilmez</Madde>
        <Madde><b>Katman ağırlıkları:</b> veritabanındaki <code>katmanlar.normalizasyon_agirligi</code> sütunundan okunur; değişken ağırlığı = katman ağırlığı / katmandaki (eşleşmeye giren) değişken sayısı, toplam 1'e normalize. Kayıtlı göçlere göre değer K1-K3 %20, K4 %40'tır (0008; ilk kurulum 0002: 20/15/25/40). Yerel test veritabanında K1-K4 %25'er; %25'i atayan bir göç yok — canlıdaki değer ayrıca kontrol edilmeli</Madde>
      </Bolum>

      <Bolum ikon="📊" baslik="5. Aşama 4 — Sonuç Sunumu ve Gizlilik Kuralları">
        <p style={{ marginBottom: 10 }}>Öğrenciye üç farklı sonuç ekranı sunulur:</p>
        <Madde><b>Bölüm Uyumum</b> — yalnızca K1-K4'ün 4'ü de bitince ve açılan K5 alanları tamamlanınca (yoksa 409 döner), en yüksek uyumlu <b>en fazla 10</b> bölüm (API üst sınırı 10; arayüz 20 istese de 10 döner). Her bölüm için "Neden bu bölüm?" açıklaması: en fazla 3 örtüşen güçlü yön + öğrencinin bunu gösteren seçimleri, K5 notu ve bölüme özgü bir dikkat notu</Madde>
        <Madde><b>Tüm Bölümleri Keşfet</b> — profil eksik olsa bile çalışır; bölümün en yüksek ağırlıklı 5 değişkenini ve (hesaplandıysa) uyum yüzdesini gösterir</Madde>
        <Madde><b>Genel Sonuçlar</b> — K1-K4'ün özet profili, gerçek "öne çıkan güçler/gelişim alanları"</Madde>
        <p style={{ marginTop: 10, padding: '10px 12px', background: 'var(--rel, #fdecea)', borderRadius: 8, color: 'var(--re)' }}>
          🔒 Kritik kural: <code>yontem_skorlari</code>, <code>kendall_w</code>, <code>agirlikli_varyans</code>,
          <code> etkin_meslek_sayisi</code> gibi alanlar öğrenci API şemalarında hiç tanımlı değildir —
          kodda "gizlenmiyor", yapısal olarak <b>var olamaz</b>. Ham cevap analizi yalnızca süper admindedir;
          akran/şube sonuçları ve rehberlik notları öğrenciye gösterilmez.
        </p>
      </Bolum>

      <Bolum ikon="🧭" baslik="6. Aşama 5 — Koçluk Modülü (Hedef Bölüm)">
        <p style={{ marginBottom: 10 }}>
          Öğrencinin aynı anda <b>yalnızca 1 aktif hedef</b> bölümü olur (odaklanma ilkesi). İlk seçim serbesttir;
          sonraki her değişiklik 1 hak harcar (öğrenci başına varsayılan <b>3 değiştirme hakkı</b>,
          <code> hedef_degisim_hakki</code>). Okul yetkilisi/süper admin değişikliği hak harcamaz ve ek hak verebilir;
          eski bir hedefe dönülünce ilerleme korunur.
        </p>
        <Madde><b>Gap Analizi:</b> her değişkende göreli fark (katman içi 50 ± 15 ölçekte öğrenci − bölüm) hesaplanır, 5 kademeye ayrılır: ≥15 belirgin üstün, ≥5 üstün, uyumlu, altında, ≤−15 belirgin altında</Madde>
        <Madde><b>Öncelik Skoru:</b> fark büyüklüğü × bölüm ağırlığı × katman ağırlığı × bölümün o özellikteki ayırt ediciliği (bölümler arası yüzdelik) — hangi boyutun geliştirilmesi en çok fark yaratır, onu öne çıkarır</Madde>
        <Madde><b>Gelişim Yol Haritası:</b> içeriği olan en öncelikli 3 gelişim alanı + en belirgin 2 güçlü yön; adımlar 3 aşamaya dağılır: "Bu hafta başla" (1-2 hafta) / "Önümüzdeki 1-3 ay" / "6-12 ay". Kaynak önerileri (kitap, film, kişi, aktivite…) admin panelinden elle girilir</Madde>
        <Madde><b>Tekrar ölçüm:</b> değer (K1) dışındaki odak alanında her 3 tamamlanan adımda bir, o değişkene en çok etki eden en fazla 5 soru yeniden sorulur</Madde>
        <Madde><b>Tur Karşılaştırması:</b> öğrenci yeniden değerlendirildiğinde (varsayılan en erken 120 gün sonra), önceki turla karşılaştırıp gerçek gelişimi gösterir</Madde>
        <Madde><b>Haftalık görevler:</b> her hafta 3 görev (yolculuk, keşif, yansıtma), seri ve Filiz seviyesi (Tohum → Ulu Çınar)</Madde>
      </Bolum>

      <Bolum ikon="❓" baslik="7. Soru Tipleri ve Puanlama Mantığı">
        <p style={{ marginBottom: 10 }}>
          Veritabanı 4 soru tipine izin verir (<code>likert</code>, <code>sjt</code>, <code>kutup</code>,
          <code> kontrol</code>); SJT'nin ayrıca 2 cevap biçimi vardır (tek seçim / en çok–en az). Her biri farklı bir
          puanlama formülüne dayanır. Yerel veritabanında K1-K5'teki tüm aktif sorular en çok/en az biçimli 4 şıklı SJT'dir
          (K1-K4 15'er, K5 187); canlıdaki dağılım soru bankasından görülmelidir.
        </p>

        <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Likert (5'li Ölçek)</div>
          <Madde>"Kesinlikle Katılmıyorum" → "Kesinlikle Katılıyorum" arası 5 seçenek</Madde>
          <Madde>Doğrudan bir değişkeni ölçer; puan = (şık sırası − 1) / (şık sayısı − 1) × 100</Madde>
          <Madde><code>ters_kodlanmis_mi</code> işaretliyse skala tersine çevrilir (örn. "Rutin işler beni sıkar" sorusuna "Katılıyorum" demek, aslında düşük "rutin tercihi" puanı demektir)</Madde>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>SJT (Durumsal Yargı Testi)</div>
          <Madde>Bir senaryo anlatılır, öğrenci birden fazla davranış seçeneğinden seçim yapar</Madde>
          <Madde>Her seçenek, bir veya birden fazla değişkene <b>ağırlıklı</b> bağlanabilir (örn. bir seçenek hem D1'e 0.6 hem D2'ye 0.7 ağırlıkla katkı verebilir)</Madde>
          <Madde><b>Tek seçim:</b> seçilen seçeneğin ağırlığı × 100, ilgili değişkenin puan listesine eklenir. Ağırlık <b>negatif</b> de olabilir — "bu seçeneği seçmek, o değişkenin DÜŞÜK olduğunu gösterir" (örn. "Karışmam, kendi işime odaklanırım" → çatışma yönetimi −0.7)</Madde>
          <Madde><b>En çok / en az:</b> öğrenci sana en çok ve en az uyan şıkkı seçer (ikisi aynı olamaz). En çok seçilen şık 100, en az seçilen 0, diğerleri 50 alır; ağırlıkla 50'ye çekilir: 50 + (puan − 50) × w (w 0–1'e kırpılır, bu biçimde negatif ağırlık etkisizdir)</Madde>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Kutup (A-mı-B-mi, 4'lü Ölçek)</div>
          <Madde>İki değişkeni doğrudan birbirine karşı konumlandıran, hikayeleştirilmiş bir tercih sorusu (örn. "Güvenceli bir kurum mu, esnek/bağımsız bir düzen mi?")</Madde>
          <Madde>4 seçenek: Kesinlikle A / Daha Çok A / Daha Çok B / Kesinlikle B</Madde>
          <Madde>A ucu puanı, seçilen seçeneğe göre lineer enterpole edilir: 1→100, 2→66.7, 3→33.3, 4→0. B ucu puanı bunun tamamlayanıdır (100 − A puanı) — iki uç matematiksel olarak birbirinin simetrik zıttıdır</Madde>
          <Madde>Kavramsal olarak birbirine yakın/karışabilecek iki değişkeni (örn. "Deneyime Açıklık" ile "Rutin/Dinamik Tercihi") ayrı ayrı Likert yerine <b>doğrudan karşılaştırarak</b> ölçmek, hem daha az soru gerektirir hem de aralarındaki ayrımı daha net ortaya çıkarır</Madde>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Kontrol (Dikkat) Soruları</div>
          <Madde>Hiçbir değişkene puan katmaz; <code>beklenen_secenek_sira</code> ile karşılaştırılır, doğruluk oranı × 100 güven puanının kontrol bileşeni olur (hiç kontrol sorusu yoksa 100)</Madde>
        </div>
      </Bolum>

      <Bolum ikon="🔬" baslik="8. Soru Geçerlilik Testi — Metodoloji">
        <p style={{ marginBottom: 10 }}>
          Bir sorunun "iyi yazılmış" sayılması için, sorunun metni ile hangi değişkeni ölçtüğü arasında
          <b> anlamsal olarak net bir bağ</b> olmalı — aksi halde öğrenci soruyu doğru yorumlasa bile
          puanlama sistemi yanlış bir sinyal almış olabilir. Bunu <b>insan gözüyle değil, 3 bağımsız dil
          modeliyle "kör" test ederek</b> ölçüyoruz. Test, sunucudan dışa aktarılan girdiyle yerel bir betikte
          çalışır (betik bu depoda değil); sonuçlar admin paneline yüklenir.
        </p>

        <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Nasıl Çalışıyor</div>
          <Madde>Her sorunun (Likert) veya seçeneğin (SJT, Kutup) metni, hangi değişkene ait olduğu <b>modele söylenmeden</b> 3 modele veriliyor</Madde>
          <Madde>Her model, metni tüm aday değişkenlerin açıklamalarıyla karşılaştırıp en yakın olanı "tahmin" ediyor</Madde>
          <Madde>Adaylar, sorunun <b>kendi ailesiyle</b> (değişken kodunun rakamsız öneki) sınırlı tutulur — K1 sorusu yalnızca D1-D7 arasından. Tüm 160 değişken (31 + 129 K5) arasından seçtirmek görevi yapay olarak zorlaştırır. Not: K5'in yeni kodlarında (U01_M gibi) önek "U_M" olur, yani aile alan değil eksen harfi bazında oluşur; admin ekranındaki rastgele taban K5 için bu gruplamayla hesaplanır</Madde>
          <Madde><b>En yüksek ağırlığı ≤ 0 olan SJT seçenekleri teste dahil edilmez</b> — böyle bir seçenek metni değişkenin "tersini" ifade eder (örn. "Karışmam, kendi işime odaklanırım"), bu metnin değişkene semantik olarak yakın çıkması zaten beklenmez; bunu test etmek modele haksız bir başarısızlık yükler</Madde>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Kabul Ölçütü — Neden "En Az 2/3", Tam 3/3 Değil</div>
          <p style={{ marginBottom: 8 }}>
            Ölçüt, 3 modelden <b>tamamının</b> hemfikir olmasını değil, <b>en az ikisinin</b> aynı değişkeni
            işaret etmesini arar — bu, topluluk/çoğunluk kararı (ensemble/majority voting) yöntemidir ve
            gözlemciler arası uyum (inter-rater agreement) literatüründeki yerleşik pratiklerle örtüşür.
          </p>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Eşik Değerlerin Akademik Kaynağı</div>
          <Madde><b>%70</b> — her katmanın kendi içinde ulaşması gereken minimum eşik. Stemler (2004)'in gözlemciler arası uyum için önerdiği "kabul edilebilir minimum eşik" ile birebir örtüşür</Madde>
          <Madde><b>%80</b> — sistemin genel ortalamasının ulaşması gereken eşik. Graham, Milanowski &amp; Miller (2012) ve McHugh (2012)'un "tatmin edici/kabul edilebilir" uyum düzeyi olarak kabul ettiği eşik; Landis &amp; Koch (1977) kappa sınıflandırmasında bu aralık "önemli ölçüde – neredeyse mükemmel" uyum kategorisine karşılık gelir</Madde>
          <Madde>Katman bazında minimum kabul edilebilir (%70), sistemin bütünü ise daha yüksek bir tatmin edicilik standardında (%80) tutulur. Eşiklerin bu kaynaklara bağlanması bir uyarlamadır; kappa/CVR birebir hesaplanmaz</Madde>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Rastgele Baseline — Sonucun Anlamlı Olduğunu Nasıl Kanıtlıyoruz</div>
          <p style={{ marginBottom: 8 }}>
            Yalnızca "%77 doğru" demek yeterli bir kanıt değil — bu sayının şansla ulaşılabilecek seviyeden
            ne kadar uzak olduğunu göstermek gerekir. Bu yüzden her katman için, 3 modelin <b>tamamen rastgele
            tahmin etseydi</b> en az 2'sinin aynı adayı seçme ihtimali hesaplanır: C(3,2)·p²(1−p) + p³, p = 1/aday
            sayısı (K1'de 7 aday, K4'te 9 aday gibi). Ekranda her katman için "şans seviyesinin kaç katı" raporlanır;
            oran yüklenen test sonuçlarına göre değişir.
          </p>
        </div>

        <p style={{ marginTop: 14, padding: '10px 12px', background: 'var(--tll)', borderRadius: 8, color: 'var(--tl)' }}>
          📊 Bu analiz, admin panelindeki <b>Soru Geçerlilik Testi</b> sayfasında katman bazında canlı olarak
          görülebilir — hangi katmanın eşiği geçtiği, hangisinin geliştirilmesi gerektiği orada işaretlenir.
        </p>
      </Bolum>

      <Bolum ikon="🛡️" baslik="9. Güvenlik & Tutarlılık Sistemi">
        <p style={{ marginBottom: 10 }}>
          Değerlendirme sırasında, sonucun güvenilirliğini artırmak için çok katmanlı bir izleme sistemi çalışır:
        </p>
        <Madde><b>Tam ekran zorunluluğu:</b> değerlendirme tam ekran modunda yapılır; çıkılırsa uyarı gösterilir ve olay kaydedilir</Madde>
        <Madde><b>Kamera:</b> yalnızca öğrenci KVKK'da kamera iznini verdiyse ve başlamadan "ONAYLIYORUM" yazdıysa açılır; başlangıçtan kısa süre sonra ve <b>her 4 soruda bir</b> fotoğraf çekilir (yüz tanıma yapılmaz). İzni reddetmek cezasızdır, raporda "kamerasız" görünür. 180 günden eski fotoğraflar açılışta ve sunucu açıkken 6 saatte bir silinir</Madde>
        <Madde><b>Davranış izleme:</b> tam ekrandan çıkma, sekme değiştirme, pencere odağı kaybı, ikinci ekran, ekran görüntüsü tuşu, kopyalama denemesi ve kameranın kapanması zaman damgalı kaydedilir; ihlal öğrenciye anında gösterilir</Madde>
        <Madde><b>Güven Skoru:</b> 0,5 × kontrol soru skoru + 0,5 × olay skoru; olay skoru = max(0, 100 − Σceza). Cezalar: tam ekrandan çıkma 10, sekme 10, odak kaybı 5, ikinci ekran 15, ekran görüntüsü tuşu 10, kopyalama 5, kamera kapandı 5; "geri dönüldü" olayları ve kamera reddi cezasız</Madde>
        <Madde>Eşik <code>guven_skoru_esigi</code> parametresinden okunur (varsayılan <b>50</b>); altında kalan tur "geçersiz" etiketlenir (silinmez). Geçersiz turda öğrenci sonuçlarını görür; Ana Sayfa ve sonuç ekranlarında "Bu değerlendirme doğrulanamadı" uyarısı çıkar ve yeniden değerlendirme bekleme süresi uygulanmaz (öğrenci hemen yeni tur başlatabilir). Etiket okul paneli, raporlar ve Güvenlik / Tutarlılık ekranında da görünür.</Madde>
        <Madde>Tüm bu veriler admin panelindeki <b>Güvenlik / Tutarlılık</b> sayfasından, tur bazında incelenebilir</Madde>
      </Bolum>

      <Bolum ikon="🛠️" baslik="10. Admin Süreçleri — Veri Nasıl Yönetiliyor">
        <Madde><b>Bölümler:</b> Taslak → Test Ediliyor → Yayında akışı; her geçiş gerekçeli ve audit log'a yazılı</Madde>
        <Madde><b>Soru Bankası:</b> katman bazlı sekmeler, arama ve çoklu filtrelerle yönetilir; sorular normalde pasife alınır (geçmiş oturumlar bozulmasın diye). Ancak tekil/toplu silme API'leri ve arayüzde "katmanı komple sil" (sorular, şıklar ve o sorulara verilmiş öğrenci cevapları kalıcı silinir) vardır; katman silme normal admin rolüyle yapılabilir ve audit log'a yazılmaz</Madde>
        <Madde><b>Katman Ağırlıkları:</b> yönetim ekranı yoktur; skor motoru <code>katmanlar.normalizasyon_agirligi</code> değerini okur (bkz. 4. bölüm). <code>/admin/katman-agirliklari</code> API'si ayrı bir <code>katman_agirliklari</code> tablosuna yazar ama hesaplamayı etkilemez</Madde>
        <Madde><b>Sistem Parametreleri:</b> eşikler ve süreler (yeniden değerlendirme, güven eşiği, K5 alan sayısı, alan tutarlılığı, Filiz mesaj limiti vb.) veritabanındaki satırdan okunur, satır yoksa koddaki varsayılan kullanılır; yalnızca süper admin değiştirebilir</Madde>
        <Madde><b>Derinleşme Alanları (K5):</b> her alan "Taslak", "Güçlü Kanıtlı" ya da "Gözden Geçirilmeli" olarak işaretlenir. Bu etiketlerin açıklamaları eski kümeleme yapısından kalmadır; yerel veritabanında 17 üst alan "Güçlü Kanıtlı", eski D01 "Taslak"</Madde>
        <Madde><b>Pipeline Sonuçları:</b> bilgisayarınızda üretilen bölüm profili çıktısı, önce taslak tabloya gider, istatistiksel önizleme sonrası yalnızca süper admin onayıyla canlıya (yeni bir versiyon olarak) yazılır</Madde>
        <Madde><b>Dosya formatları:</b> soru, pipeline ve geçerlilik yüklemeleri .xlsx (.xls/.csv de kabul); bölüm ve dal toplu yüklemesi hâlâ yalnızca .csv; okul yüklemeleri .xlsx/.csv (.xls desteklenmez)</Madde>
        <Madde><b>Audit Log:</b> durum değişikliği, rol değişikliği, pipeline onayı, parametre değişikliği, cevap analizi görüntüleme gibi kritik işlemler kalıcı olarak kaydedilir</Madde>
        <Madde><b>Şema güncelleme:</b> sunucu her açılışta 0024-0051 göçlerinin tekrar çalıştırılabilir SQL'ini uygular (<code>sema_guncelleme.py</code>); daha eski göçler elle uygulanmış kabul edilir</Madde>
      </Bolum>

      <Bolum ikon="🧩" baslik="11. Okul Modülleri ve Paketler">
        <Madde><b>Paketler:</b> 19 modül; okulun paketi (Temel / Gelişim / Tam) + okula özel ekle/çıkar ile açılır (etkin = paket ∪ ekle − çıkar). Paket içerikleri veritabanındaki <code>paketler</code> tablosundadır (yerelde Temel 3, Gelişim 11, Tam 19 modül). Bağımlılık: okul denemeleri → net takibi, Filiz AI → Filiz. Okulsuz öğrenci tüm modülleri görür</Madde>
        <Madde><b>Rehberlik ve erken uyarı:</b> görüşme/randevu/takip kayıtları (notlar öğrenciye gösterilmez) ve 8 kurallı dikkat listesi (giriş yok, uzak kaldı, test yarıda, teste başlamadı, net düşüşü, görevleri bıraktı, tarama formunda destek ihtiyacı, hedef yok); "görüştüm, N gün gösterme" ertelemesi</Madde>
        <Madde><b>Net takibi ve okul denemeleri:</b> deneme netleri, konu takibi, hedef programa son yerleşenin netleriyle kıyas (YÖK Atlas, 7 gün önbellek); okul denemeleri Excel şablonla toplu yüklenir, öğrencinin net takibine düşer, okul/şube/ders ortalamaları hesaplanır</Madde>
        <Madde><b>Çalışma programı:</b> haftalık ders programı (en çok 80 blok), günlük çalışma süresi, çözülen soru kaydı ve ders bazında isabet</Madde>
        <Madde><b>Bildirimler:</b> uygulama içi bildirim zili; önemli olaylarda e-posta kuyruğu (günlük 300 sınırı), kişi e-postayı kapatabilir</Madde>
        <Madde><b>e-Portfolyo:</b> sertifika, yarışma, gönüllülük, proje ve kulüp geçmişi; okul yetkilisi doğrular; PDF özgeçmiş</Madde>
        <Madde><b>Anketler ve tarama formları:</b> okulun kendi anketleri + hazır formlar (sınav kaygısı, çalışma alışkanlıkları, okul iklimi, kariyer kararlılığı). En az 5 kuralı: anket en az 5 kişiye gönderilir, anonim sonuçlar 5'ten az yanıtla ve 5'ten küçük gruplarla gösterilmez. Anonim yanıtta öğrenci kimliği ve şube tutulmaz; yanıt gelmiş anketin soruları/anonimliği değiştirilemez. İsimli taramada destek gerektiren sonuç erken uyarıya düşer. Bilinen eksik: okul/şube raporlarında küçük grup gizlemesi yok</Madde>
        <Madde><b>Tercih ve mezun takibi:</b> 12. sınıf/mezun için en çok 24 tercihlik liste; oran = başarı sırası / geçen yıl taban sırası (≤0,85 güvenli, ≤1,10 dengeli, üstü riskli); rehber onayı. Mezun yerleşmeleri ve hedefle / öneri listesiyle uyum oranları</Madde>
        <Madde><b>Filiz ve Filiz AI:</b> Filiz modülü açıksa kural tabanlı otomatik rehber çalışır; <code>filiz_ai</code> modülü (yalnız Tam pakette) açık ve anahtar tanımlıysa OpenAI (varsayılan gpt-4o-mini) ile konuşur — öğrenci başına günlük mesaj limiti (varsayılan 30) ve kriz ifadelerinde model çağrılmadan sabit güvenli yanıt</Madde>
        <Madde><b>Ses:</b> Filiz yalnızca cihazda doğal Türkçe ses varsa sesli okur (varsayılan kapalı, yalnızca öğrencinin eylemine karşılık); yoksa yalnızca yumuşak efekt sesleri</Madde>
        <Madde><b>Meslek simülasyonu:</b> "Bölümünü Tanı" ve "Bir günümü yaşa": bölüm detayındaki mesleğin günlük işleri saat saat yaşatılır, sonunda keyif yüzdesi verilir. Bölüm detaylarındaki 1.054 meslek adının tamamı için karar anı var (her meslekte 2 karar anı, 3'er seçenek; 16 meslek elle, 1.010 meslek JSON'dan); güvenlik/etik durumlar dışında doğru/yanlış yok, kurgusal olduğu belirtilir</Madde>
        <Madde><b>Okul karşılaştırması:</b> yalnızca süper admin; 9 gösterge (öğrenci, giriş %, son 30 gün aktif %, testi tamamlayan %, hedef seçen %, ort. son TYT, rehberlik görüşmesi, yüksek uyarılı öğrenci, yerleşme %), grafik ve Excel; test hesapları hariç</Madde>
        <Madde><b>Kaynakça sayfası:</b> sistemin 68 bileşeni gruplar hâlinde, her biri için ne/nasıl, kaynakları ve hangi sayıların kurum içi karar olduğu notuyla (152 kaynak kaydı, <code>kaynakca.json</code>)</Madde>
        <Madde>Ayrıca: öğrenci/veli/yönetici/sınıf öğretmeni PDF raporları, kulüpler ve ilgi testi, eğitim koçları, akran/şube analizi, takvim ve kütüphane modülleri</Madde>
      </Bolum>

      <Bolum ikon="🕓" baslik="12. Son Güncellemeler">
        <Madde><b>KVKK metni v3:</b> ayrı "rehber öğretmenle paylaşım" onayı kaldırıldı; sonuçların okul yetkililerine gösterilmesi zorunlu analiz rızasının kapsamına alındı (kod zaten her durumda gösteriyordu). Sürüm değiştiği için tüm kullanıcılar bir sonraki girişte yeniden onay verir</Madde>
        <Madde><b>Geçersiz tur:</b> öğrenciye "doğrulanamadı" uyarısı gösterilir; geçersiz turdan sonra yeniden değerlendirme bekleme süresi uygulanmaz</Madde>
        <Madde><b>ESCO geçişi:</b> meslek veri kaynağı 7.764 kayıtlı eski listeden, AB'nin resmi 3.039 kayıtlı ESCO sınıflandırmasına taşındı — hatalı eşleşmeler büyük ölçüde ortadan kalktı</Madde>
        <Madde><b>K5 yeniden kuruldu (2026-10-08, göç 0013):</b> eski 8 dallık yapı (A1-A9'a göre kümeleme, dal başına 7 değişken) yerine 17 üst alan, alan başına 4-11 iş türü ekseni (toplam 129) ve elle hazırlanmış bölüm–eksen bağları; alan açma kuralı K4 eşiğinden bölüm listesine geçti</Madde>
        <Madde><b>En çok / en az biçimi (0012):</b> SJT sorularında öğrenci en çok ve en az uyan şıkkı seçiyor</Madde>
        <Madde><b>Uyum motoru düzeltmeleri:</b> katman içi göreli ölçekleme (10-03), P4 eşleşme dışı (10-07), K5 etkisi 0,30 → 0,50 (10-08), alan tutarlılığı ve alan komşuluğu, "Neden bu bölüm?" açıklamaları (10-09); öğrenci listesi en fazla 10 bölüm</Madde>
        <Madde><b>Güvenlik/Tutarlılık altyapısı:</b> tam ekran zorunluluğu, kamera, davranış izleme ve güven skoru; 10-10'da olay türüne göre ceza, ikinci ekran/ekran görüntüsü/kopyalama takibi ve cezasız kamera reddi eklendi</Madde>
        <Madde><b>Hedef değiştirme hakkı (0022):</b> 1 aktif hedef, varsayılan 3 değiştirme hakkı, yönetim ek hak verebilir</Madde>
        <Madde><b>Katman ağırlıkları:</b> kayıtlı göçler 20/20/20/40 diyor (0008); bazı kurulumlarda %25'er görülüyor ama bunu yapan bir göç yok — canlı değer kontrol edilmeli</Madde>
        <Madde><b>Soru Bankası yeniden tasarlandı:</b> katman bazlı sekmeler, arama, değişken/tip filtreleri, sayfa sayfa görünüm ve doğrudan düzenleme eklendi</Madde>
        <Madde><b>Dosya formatı:</b> pipeline, soru ve geçerlilik yüklemeleri .xlsx'e geçti (.csv hâlâ kabul); bölüm ve dal toplu yüklemesi hâlâ .csv</Madde>
        <Madde><b>Yeniden değerlendirme süresi:</b> varsayılan 120 gün (parametre <code>yeniden_degerlendirme_min_gun</code>); 90 güne indiren bir göç yok</Madde>
        <Madde><b>3. soru tipi eklendi (Kutup):</b> A-mı-B-mi tarzı, 4'lü ölçekli, iki değişkeni doğrudan karşılaştıran yeni bir soru tipi kuruldu</Madde>
        <Madde><b>Soru geçerlilik testi metodolojisi düzeltildi:</b> adaylar artık yalnızca sorunun kendi değişken ailesiyle sınırlı tutuluyor, negatif ağırlıklı SJT seçenekleri teste dahil edilmiyor, akademik kaynaklara dayalı %70/%80 eşikleri ve rastgele baseline karşılaştırması eklendi</Madde>
        <Madde><b>Okul modülleri (0041-0051):</b> paketler, rehberlik/erken uyarı, öğrenci raporları, okul denemeleri, çalışma programı, bildirimler, portfolyo, anketler, tercih/mezun, Filiz AI, okul karşılaştırması, meslek simülasyonu, Filiz sesi ve Kaynakça sayfası (bkz. 11. bölüm)</Madde>
      </Bolum>
    </div>
  )
}
