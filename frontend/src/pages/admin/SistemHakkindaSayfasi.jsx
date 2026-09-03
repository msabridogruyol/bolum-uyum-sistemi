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
        <Madde><b>K5 — Dal Derinleşme</b> (koşullu): K4 sonucuna göre, öğrencinin profili kümeleme analiziyle bulunan 8 dandan (Sağlık & Hizmet, Mühendislik & Teknoloji, Sanat & Tasarım vb.) birine ya da birkaçına eşik değeri geçince otomatik açılır, o dala özel 7 yeni değişken ve ek sorular sorulur</Madde>
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
                ['Bölüm kümeleme (K5 dalları)', 'K-Means (dil modeli değil, klasik ML)', 'A1-A9 sayısal profiline dayalı matematiksel gruplama'],
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
        <Madde><b>Katman ağırlıkları:</b> K1-K4'ün her biri eşit ağırlıkla (%25) toplam uyuma katkı verir</Madde>
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
          Öğrenci, herhangi bir bölümü (en fazla 3 tane, odaklanma ilkesiyle) <b>hedef</b> olarak seçebilir.
        </p>
        <Madde><b>Gap Analizi:</b> her değişkende (öğrenci puanı − bölüm beklentisi) hesaplanır, 5 kademeye ayrılır (belirgin üstün → belirgin altında)</Madde>
        <Madde><b>Öncelik Skoru:</b> fark büyüklüğü × o değişkenin bölüm için ağırlığı — hangi boyutun geliştirilmesi en çok fark yaratır, onu öne çıkarır</Madde>
        <Madde><b>Gelişim Yol Haritası:</b> geliştirilmesi gereken boyutlar, tahmini efora göre "Şimdi / Bu Dönem / Uzun Vadede" olarak gruplanır, her biri için gerçek kaynak önerileri (kitap, aktivite) sunulur</Madde>
        <Madde><b>Tur Karşılaştırması:</b> öğrenci yeniden değerlendirildiğinde (min. 90 gün sonra), önceki turla karşılaştırıp gerçek gelişimi gösterir</Madde>
      </Bolum>

      <Bolum ikon="❓" baslik="6. Soru Tipleri ve Puanlama Mantığı">
        <p style={{ marginBottom: 10 }}>
          Sistemde 3 farklı soru tipi var; her biri farklı bir psikolojik ölçüm mantığına ve farklı bir
          puanlama formülüne dayanır:
        </p>

        <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Likert (5'li Ölçek)</div>
          <Madde>"Kesinlikle Katılmıyorum" → "Kesinlikle Katılıyorum" arası 5 seçenek</Madde>
          <Madde>Doğrudan bir değişkeni ölçer; seçilen seçeneğin sırası 0-100 aralığına ölçeklenir</Madde>
          <Madde><code>ters_kodlanmis_mi</code> işaretliyse skala tersine çevrilir (örn. "Rutin işler beni sıkar" sorusuna "Katılıyorum" demek, aslında düşük "rutin tercihi" puanı demektir)</Madde>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>SJT (Durumsal Yargı Testi)</div>
          <Madde>Bir senaryo anlatılır, öğrenci birden fazla davranış seçeneğinden birini seçer</Madde>
          <Madde>Her seçenek, bir veya birden fazla değişkene <b>ağırlıklı</b> bağlanabilir (örn. bir seçenek hem D1'e 0.6 hem D2'ye 0.7 ağırlıkla katkı verebilir)</Madde>
          <Madde>Ağırlık <b>negatif</b> de olabilir — bu, "bu seçeneği seçmek, o değişkenin DÜŞÜK olduğunu gösterir" anlamına gelir (örn. "Karışmam, kendi işime odaklanırım" seçeneği, çatışma yönetimi değişkenine -0.7 ağırlıkla bağlanır)</Madde>
          <Madde>Puana katkı: seçilen seçeneğin ağırlığı × 100, ilgili değişkenin puan listesine eklenir</Madde>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Kutup (A-mı-B-mi, 4'lü Ölçek)</div>
          <Madde>İki değişkeni doğrudan birbirine karşı konumlandıran, hikayeleştirilmiş bir tercih sorusu (örn. "Güvenceli bir kurum mu, esnek/bağımsız bir düzen mi?")</Madde>
          <Madde>4 seçenek: Kesinlikle A / Daha Çok A / Daha Çok B / Kesinlikle B</Madde>
          <Madde>A ucu puanı, seçilen seçeneğe göre lineer enterpole edilir: 1→100, 2→66.7, 3→33.3, 4→0. B ucu puanı bunun tamamlayanıdır (100 − A puanı) — iki uç matematiksel olarak birbirinin simetrik zıttıdır</Madde>
          <Madde>Kavramsal olarak birbirine yakın/karışabilecek iki değişkeni (örn. "Deneyime Açıklık" ile "Rutin/Dinamik Tercihi") ayrı ayrı Likert yerine <b>doğrudan karşılaştırarak</b> ölçmek, hem daha az soru gerektirir hem de aralarındaki ayrımı daha net ortaya çıkarır</Madde>
        </div>
      </Bolum>

      <Bolum ikon="🔬" baslik="7. Soru Geçerlilik Testi — Metodoloji">
        <p style={{ marginBottom: 10 }}>
          Bir sorunun "iyi yazılmış" sayılması için, sorunun metni ile hangi değişkeni ölçtüğü arasında
          <b> anlamsal olarak net bir bağ</b> olmalı — aksi halde öğrenci soruyu doğru yorumlasa bile
          puanlama sistemi yanlış bir sinyal almış olabilir. Bunu <b>insan gözüyle değil, 3 bağımsız dil
          modeliyle "kör" test ederek</b> ölçüyoruz.
        </p>

        <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Nasıl Çalışıyor</div>
          <Madde>Her sorunun (Likert) veya seçeneğin (SJT, Kutup) metni, hangi değişkene ait olduğu <b>modele söylenmeden</b> 3 modele veriliyor</Madde>
          <Madde>Her model, metni tüm aday değişkenlerin açıklamalarıyla karşılaştırıp en yakın olanı "tahmin" ediyor</Madde>
          <Madde>Adaylar, sorunun <b>kendi ailesiyle</b> sınırlı tutulur (K1 sorusu yalnızca D1-D7 arasından, Mühendislik dalı sorusu yalnızca kendi 7 değişkeni arasından) — tüm 87+ değişken arasından seçtirmek görevi yapay olarak zorlaştırır ve katmanlar arası anlamsız karışmalara yol açar</Madde>
          <Madde><b>Negatif ağırlıklı SJT seçenekleri teste dahil edilmez</b> — böyle bir seçenek metni değişkenin "tersini" ifade eder (örn. "Karışmam, kendi işime odaklanırım"), bu metnin değişkene semantik olarak yakın çıkması zaten beklenmez; bunu test etmek modele haksız bir başarısızlık yükler</Madde>
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
          <Madde>Katman bazında minimum kabul edilebilir (%70), sistemin bütünü ise daha yüksek bir tatmin edicilik standardında (%80) tutulur</Madde>
        </div>

        <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
          <div className="ct" style={{ fontSize: 13 }}>Rastgele Baseline — Sonucun Anlamlı Olduğunu Nasıl Kanıtlıyoruz</div>
          <p style={{ marginBottom: 8 }}>
            Yalnızca "%77 doğru" demek yeterli bir kanıt değil — bu sayının şansla ulaşılabilecek seviyeden
            ne kadar uzak olduğunu göstermek gerekir. Bu yüzden her katman için, 3 modelin <b>tamamen rastgele
            tahmin etseydi</b> en az 2'sinin aynı adayı seçme ihtimali matematiksel olarak hesaplanır (aday
            sayısına göre değişir — K1'de 7 aday, K4'te 9 aday gibi). Gerçek sonuçlarımız bu şans seviyesinin
            genellikle <b>10-20 kat üzerinde</b> çıkıyor; bu, soruların şans eseri değil, gerçekten anlamlı
            şekilde ayırt edilebilir olduğunun istatistiksel kanıtıdır.
          </p>
        </div>

        <p style={{ marginTop: 14, padding: '10px 12px', background: 'var(--tll)', borderRadius: 8, color: 'var(--tl)' }}>
          📊 Bu analiz, admin panelindeki <b>Soru Geçerlilik Testi</b> sayfasında katman bazında canlı olarak
          görülebilir — hangi katmanın eşiği geçtiği, hangisinin geliştirilmesi gerektiği orada işaretlenir.
        </p>
      </Bolum>

      <Bolum ikon="🛡️" baslik="8. Güvenlik & Tutarlılık Sistemi">
        <p style={{ marginBottom: 10 }}>
          Değerlendirme sırasında, sonucun güvenilirliğini artırmak için çok katmanlı bir izleme sistemi çalışır:
        </p>
        <Madde><b>Tam ekran zorunluluğu:</b> değerlendirme yalnızca tam ekran modunda yapılabilir; çıkılırsa uyarı gösterilir ve olay kaydedilir</Madde>
        <Madde><b>Kamera doğrulaması:</b> katman başında ve aralıklarla (izin verilirse) kimlik doğrulama fotoğrafı çekilir</Madde>
        <Madde><b>Davranış izleme:</b> sekme değiştirme, pencere odağı kaybı gibi olaylar zaman damgalı kaydedilir</Madde>
        <Madde><b>Güven Skoru:</b> kontrol (dikkat) sorularının doğruluk oranı + güvenlik olaylarının sayısı eşit ağırlıkla birleştirilip 0-100 arası bir skor üretir; eşiğin altında kalan sonuçlar "geçersiz" işaretlenir (silinmez, yalnızca etiketlenir)</Madde>
        <Madde>Tüm bu veriler admin panelindeki <b>Güvenlik / Tutarlılık</b> sayfasından, tur bazında incelenebilir</Madde>
      </Bolum>

      <Bolum ikon="🛠️" baslik="9. Admin Süreçleri — Veri Nasıl Yönetiliyor">
        <Madde><b>Bölümler:</b> Taslak → Test Ediliyor → Yayında akışı; her geçiş gerekçeli ve audit log'a yazılı</Madde>
        <Madde><b>Soru Bankası:</b> sorular hiç silinmez, yalnızca pasife alınır (geçmiş öğrenci oturumları bozulmasın diye); katman bazlı sekmeler, arama ve çoklu filtrelerle yönetilir</Madde>
        <Madde><b>Katman Ağırlıkları:</b> K1-K4 eşit (%25) sabitlenmiştir, ayrı bir yönetim ekranı yoktur</Madde>
        <Madde><b>Derinleşme Alanları (K5):</b> her dal, tek/çoklu yöntem kaynaklı olup olmadığına göre "Taslak", "Güçlü Kanıtlı" ya da "Gözden Geçirilmeli" olarak işaretlenir</Madde>
        <Madde><b>Pipeline Sonuçları:</b> bilgisayarınızda üretilen bölüm profili çıktısı, önce taslak tabloya gider, istatistiksel önizleme sonrası yalnızca süper admin onayıyla canlıya (yeni bir versiyon olarak) yazılır</Madde>
        <Madde><b>Audit Log:</b> durum değişikliği, rol değişikliği, pipeline onayı gibi kritik her işlem kalıcı olarak kaydedilir</Madde>
      </Bolum>

      <Bolum ikon="🕓" baslik="10. Son Güncellemeler">
        <Madde><b>ESCO geçişi:</b> meslek veri kaynağı 7.764 kayıtlı eski listeden, AB'nin resmi 3.039 kayıtlı ESCO sınıflandırmasına taşındı — hatalı eşleşmeler büyük ölçüde ortadan kalktı</Madde>
        <Madde><b>K5 dalları kuruldu:</b> 301 bölüm, A1-A9 profiline göre kümeleme analiziyle 8 dala ayrıldı; her dal için 7'şer yeni değişken ve toplam 186 soru (168 Likert + 18 SJT) yazıldı</Madde>
        <Madde><b>Güvenlik/Tutarlılık altyapısı:</b> tam ekran zorunluluğu, kamera doğrulaması, davranış izleme ve güven skoru sistemi kuruldu</Madde>
        <Madde><b>Katman ağırlıkları eşitlendi:</b> K1-K4 artık eşit (%25) ağırlıkla hesaba katılıyor</Madde>
        <Madde><b>Soru Bankası yeniden tasarlandı:</b> katman bazlı sekmeler, arama, değişken/tip filtreleri, sayfa sayfa görünüm ve doğrudan düzenleme eklendi</Madde>
        <Madde><b>Dosya formatı:</b> pipeline çıktıları ve admin yüklemeleri artık .csv yerine .xlsx — Türkçe karakter bozulması riski ortadan kalktı</Madde>
        <Madde><b>Yeniden değerlendirme süresi:</b> 120 günden 90 güne indirildi</Madde>
        <Madde><b>3. soru tipi eklendi (Kutup):</b> A-mı-B-mi tarzı, 4'lü ölçekli, iki değişkeni doğrudan karşılaştıran yeni bir soru tipi kuruldu</Madde>
        <Madde><b>Soru geçerlilik testi metodolojisi düzeltildi:</b> adaylar artık yalnızca sorunun kendi değişken ailesiyle sınırlı tutuluyor, negatif ağırlıklı SJT seçenekleri teste dahil edilmiyor, akademik kaynaklara dayalı %70/%80 eşikleri ve rastgele baseline karşılaştırması eklendi</Madde>
      </Bolum>
    </div>
  )
}
