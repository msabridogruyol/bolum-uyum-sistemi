# Filizyol — Kaynakça

Sistemde elle hazırlanan her bileşen, ne yaptığı, nasıl hesaplandığı ve dayandığı akademik/resmî kaynaklar.

- Uygulamada: **Okul Paneli → Yardım → Kaynakça** ve **Yönetici Paneli → Sistem → Kaynakça**. Okul yetkilisi "nasıl hesaplanıyor" ayrıntılarını ve doğrulama notlarını görmez.
- Veri kaynağı: `backend/app/data/kaynakca.json` (bu dosya oradan üretilir).
- Kaynaklar bileşenin **kuramsal dayanağını** gösterir; Filizyol ölçekleri bu kaynaklardaki ölçeklerin birebir uyarlaması değildir ve ayrıca geçerlik-güvenirlik çalışması gerektirir.
- **Kurum içi** işaretli bileşenlerde eşik, ağırlık ve sayılar ürün tasarımı kararıdır.

Toplam: 68 bileşen, 152 kaynak.

## İçindekiler

- Öğrenci değerlendirmesi
- Uyum hesaplama
- Koçluk
- Meslek bilgisi ve simülasyon
- Rehberlik ve erken uyarı
- Anket ve tarama formları
- Akademik takip
- Tercih ve mezun
- Okul yönetimi ve raporlar
- Güvenlik ve veri koruma

- [Tüm kaynaklar (APA 7)](#tüm-kaynaklar-apa-7)

## Öğrenci değerlendirmesi

### Değerlendirme katmanları (K1–K5)

Öğrenciyi beş katmanda ölçen yapı: K1 Değerler/Motivasyon, K2 Kişilik & Çalışma Tarzı, K3 İş Ortamı & Profesyonel Yetkinlik, K4 Alan Eğilimi & Bilişsel Stil, K5 koşullu Derinleşme.

**Nasıl:** K1–K4 zorunlu ve sırasıyla 7, 8, 7, 9 değişken ölçer (toplam 31); K5 K1–K4 bittikten sonra koşullu açılır (kosullu_mu=TRUE). Ekranda katman başına tahmini süre ≈5 dk, K5 için ≈3 dk/alan yazılır.

**Dayanak:**

- [123] Schwartz, 1992 — Değerler/motivasyon katmanının (K1) kuramsal temeli olan evrensel değer tipleri modelini sunar.
- [30] Dawis ve Lofquist, 1984 — Birey–iş ortamı uyumunu değerler/ihtiyaçlar ve yeteneklerin eşleşmesiyle açıklayan TWA, K1 ve K3'ün birey–ortam uyumu mantığını destekler.
- [66] John ve Srivastava, 1999 — Beş Faktör modelini ve ölçümünü özetler; K2 kişilik & çalışma tarzı katmanına dayanak verir.
- [58] Holland, 1997 — RIASEC ilgi tipolojisi K4 alan eğilimi katmanının kuramsal temelidir.

> Katmanların kuramlara bağlanması kavramsal düzeydedir (esinlenme); K1–K4'teki değişken sayıları (7, 8, 7, 9), K5'in koşullu açılması ve süre tahminleri (≈5 dk, ≈3 dk/alan) kurum içi tasarım kararıdır.

### 31 değişkenin tanımları (D1–D7, P1–P8, I1–I7, A1–A9)

Ölçülen her özelliğin adı ve öğrenciye gösterilen açıklaması (ör. D1 Güvence, P3 Sorumluluk/disiplin, I3 Baskı altında karar verme, A1 Sayısal/veri eğilimi).

**Nasıl:** Tanımlar SONUÇ.xlsx'ten migration ile eklendi (Excel'deki K3/K4 etiket karışıklığı düzeltilerek I1–I7→K3, A1–A9→K4); 0019'da görünen adlar sadeleştirildi (kodlar ve puanlar değişmedi). K2'deki P1,P2,P3,P4,P5 Beş Faktör boyutlarına; P6 rutin↔dinamik, P7 belirsizlik/risk toleransı, P8 liderlik isteği ek boyutlardır; A7/A8 yapılandırılmış/sezgisel bilişsel stil.

**Dayanak:**

- [26] Costa ve McCrae, 1992 — Beş Faktör boyutlarının işlevsel tanımlarını verir; P1–P5'in Beş Faktör boyutlarına karşılık gelmesini destekler (maddeler NEO PI-R'den alınmamıştır).
- [10] Bateman ve Crant, 1993 — Proaktif kişiliği ayrı bir eğilim olarak tanımlayıp ölçen temel çalışmadır; K2/K3'teki proaktiflik/inisiyatif değişkenine kavramsal dayanak sağlar (madde içeriği uyarlama değildir).
- [22] Chan ve Drasgow, 2001 — Liderlik isteğini (motivation to lead) kişilik ve değerlerden ayrı bir bireysel farklılık değişkeni olarak kuramlaştırır; P8 liderlik isteği boyutunun ayrı tutulmasını destekler.
- [44] Goldberg, 1990 — K2 kişilik boyutlarının Beş Faktör yapısına dayandırılmasını destekler.

> P6 rutin↔dinamik, P7 belirsizlik/risk toleransı, A7/A8 bilişsel stil ve I1–I7 iş ortamı yetkinliklerinin tanımları kurum içinde yazılmıştır; bu değişkenler için ayrı kaynak eşlenmemiştir. Görünen adların sadeleştirilmesi (0019) bir sunum kararıdır.

### Soru bankası ve tur yönetimi

K1–K5 soru metinleri ve şıkları; öğrencinin değerlendirme turlarının açılması ve soru setinin dondurulması.

**Nasıl:** Soru metinleri repoda değil, veritabanında; admin panelinden tekil, Likert/SJT toplu ve kutup toplu (katman_kod, a/b değişken kodu, metin, uç etiketleri) yüklemeyle girilir, silinmez yalnızca pasife alınır. Katman başlarken aktif soru id'leri kilitlenir; iki tam tur arasında varsayılan 120 gün (parametre yeniden_degerlendirme_min_gun).

**Dayanak:**

- [2] American Educational Research Association, American Psych…, 2014 — Test içeriğinin kapsam geçerliği, madde geliştirme, belgeleme ve puanların yorumlanmasına ilişkin genel standartları ortaya koyar; bileşen bu ilkelerden esinlenir, standartların resmî bir uygunluk denetiminden geçmemiştir.
- [84] Low ve ark., 2005 — Mesleki ilgilerin ergenlikte görece daha az kararlı olduğunu ve yaşla kararlılığın arttığını gösterir; lise öğrencisinde belirli aralıklarla yeniden değerlendirme yapılmasına gerekçe verir, ancak 120 günlük aralığın kendisini belirlemez.

> Soru bankasının pasife alma (silmeme), soru setini kilitleme ve toplu yükleme mekanizmaları yazılım/ürün kararıdır. 120 günlük yeniden değerlendirme aralığı kurum içi bir parametredir; akademik bir test–tekrar test aralığına dayanmaz. Maddelerin madde yazım ilkelerine uygunluğu ayrıca belgelenmemiştir.

### Likert puanlama ve değişken puanı

Likert sorularında seçilen şıkkın 0–100 puana çevrilmesi ve bir değişkenin nihai puanının oluşturulması.

**Nasıl:** puan = (şık_sırası − 1) / (şık_sayısı − 1) × 100; ters kodlu maddede 100 − puan; tek şıklı soruda 50. Aynı değişkene katkı veren tüm cevapların (Likert, SJT, kutup) aritmetik ortalaması alınır ve 0–100'e kırpılır. Ekran metni 5'li ölçek kullanır.

**Dayanak:**

- [82] Likert, 1932 — Toplamalı derecelendirme (Likert) ölçeğinin özgün kaynağıdır; şık sırasının puana dönüştürülüp ortalanmasını destekler.
- [142] Weijters ve Baumgartner, 2012 — Ters kodlu maddelerdeki yanlış yanıtlama sorunlarını gözden geçirir; ters maddede 100 − puan dönüşümünün ve bu maddelerin dikkatle yazılması gerekliliğinin dayanağıdır.
- [25] Cohen ve ark., 1999 — Ham puanların olası en yüksek puana göre yüzde ölçeğine (POMP, 0–100) doğrusal dönüştürülmesini önerir; (şık_sırası − 1)/(şık_sayısı − 1) × 100 formülü bu yaklaşımla aynı mantıktadır.

> Likert, SJT ve kutup cevaplarının aynı değişkende eşit ağırlıkla aritmetik ortalamasının alınması ve tek şıklı soruda 50 verilmesi kurum içi tasarım kararıdır; farklı yanıt biçimlerinin aynı ölçekte birleştirilmesinin geçerliği ayrıca sınanmamıştır.

### SJT (durum sorusu) puanlama: tek seçim ve en çok/en az

Senaryo sorularında seçilen davranışın bir veya birden çok değişkene puan katması.

**Nasıl:** Tek seçimde seçilen şıkkın her değişken ağırlığı × 100 puan olarak eklenir (ağırlık negatif olabilir). 'En çok/en az' biçiminde en çok seçilen şık 100, en az seçilen 0, diğerleri 50 alır ve ağırlıkla 50'ye çekilir: 50 + (puan − 50) × w (w 0–1'e kırpılır); 'en az' boş veya 'en çok' ile aynı olamaz.

**Dayanak:**

- [88] McDaniel ve ark., 2001 — SJT'lerin iş performansını yordama geçerliğini meta-analizle gösterir; senaryo sorularının kullanılmasını destekler.
- [87] McDaniel ve ark., 2007 — 'Ne yapardınız' / 'en çok–en az' gibi yanıt talimatlarının SJT geçerliğini etkilediğini gösterir; en çok/en az biçimine dayanak verir.
- [81] Lievens ve ark., 2008 — SJT tasarımı, puanlama ve yanıt biçimlerine ilişkin araştırmaları özetler.
- [141] Weekley ve Ployhart, 2006 — SJT geliştirme ve puanlama anahtarı oluşturma yaklaşımlarını (uzman/ampirik anahtar, yanıt biçimleri) derleyen akademik kitaptır; şık–değişken ağırlıklı puanlamaya genel çerçeve verir, kullanılan formül kurum içidir.

> Şık–değişken ağırlıkları, negatif ağırlık kullanımı ve 'en çok 100 / en az 0 / diğerleri 50' ile 50 + (puan − 50) × w dönüşümü kurum içi puanlama kararıdır; literatürdeki standart bir puanlama anahtarının birebir uyarlaması değildir.

### Kutup (A mı B mi) soruları

İki değişkeni karşı karşıya koyan, 4 şıklı tercih sorusu (Kesinlikle A / Daha çok A / Daha çok B / Kesinlikle B).

**Nasıl:** A ucu puanı = (4 − şık_sırası) / 3 × 100 (1→100, 2→66,7, 3→33,3, 4→0); B ucu = 100 − A. Orta (kararsız) seçenek yoktur; 4 şık metni uç etiketlerinden otomatik üretilir.

**Dayanak:**

- [102] Osgood ve ark., 1957 — İki zıt uç etiketiyle tanımlanan iki kutuplu derecelendirme ölçeğinin (anlamsal farklılaşma) klasik kaynağıdır; 'Kesinlikle A … Kesinlikle B' biçimi bu yapıdan esinlenir, orta noktasız 4 şıklı uygulama ise kurum içi tercihtir.
- [15] Brown ve Maydeu-Olivares, 2011 — Zorunlu seçimli maddelerin ipsatif puanlama sorunlarını ve bunları aşan IRT modellemesini ele alır; A/B sorularının yorumunda dikkate alınacak sınırları belirtir.
- [56] Hicks, 1970 — İpsatif ve zorunlu seçimli ölçümün psikometrik sınırlarını (puanların birbirine bağımlılığı, bireyler arası karşılaştırma sorunları) ortaya koyar; A/B kutup sorularında B = 100 − A olduğundan bu sınırlamanın dikkate alınmasını destekler.

> Orta (kararsız) seçenek bulunmaması ve 4 şıkkın 100/66,7/33,3/0 olarak puanlanması kurum içi tasarım kararıdır; ipsatif yapının bireyler arası karşılaştırmaya etkisi sistemde ayrıca düzeltilmemektedir (Thurstonian IRT gibi bir model kullanılmıyor).

### Dikkat (kontrol) soruları

Öğrencinin soruları okuyup okumadığını yoklayan, puana değil güven puanına etki eden sorular.

**Nasıl:** soru_tipi='kontrol' sorular hiçbir değişkene puan katmaz; beklenen_secenek_sira ile karşılaştırılır, doğruluk oranı × 100 kontrol skoru olur (hiç kontrol sorusu yoksa 100).

**Dayanak:**

- [91] Meade ve Craig, 2012 — Talimatlı/kontrol maddelerinin özensiz yanıtlayıcıları belirlemede etkili olduğunu gösterir; puana katılmayan dikkat sorularının kullanılmasını doğrudan destekler.
- [67] Kam ve Chan, 2018 — Talimatlı yanıt maddelerinin ('bu soruda X'i seçin') özensiz yanıtlayıcıları belirlemedeki geçerliğini sınar; beklenen şıkla karşılaştırılan kontrol soruları tasarımını doğrudan destekler.
- [59] Huang ve ark., 2012 — Yetersiz çabalı yanıtlamayı saptama göstergelerini (ör. yanıt süresi, tutarsızlık) ve caydırıcı yönergeleri inceler; dikkat soruları ve güven puanındaki davranış göstergelerine dayanak sağlar.

> Kontrol skorunun doğruluk oranı × 100 olarak hesaplanması ve hiç kontrol sorusu yoksa 100 kabul edilmesi kurum içi karardır.

### Güven puanı ve sonuç geçerliliği · _Kurum içi_

Bir değerlendirme turunun güvenilirliğini 0–100 puanla gösterir; eşik altı turlar 'geçersiz' etiketlenir (silinmez).

**Nasıl:** güven = 0,5 × kontrol_skoru + 0,5 × olay_skoru; olay_skoru = max(0, 100 − Σceza); cezalar: tam ekrandan çıkma 10, sekme değiştirme 10, pencere odağı kaybı 5, ikinci ekran 15, ekran görüntüsü tuşu 10, kopyalama 5, kamera kapandı 5; kamera iznini reddetmek ve 'geri dönüldü' olayları cezasız. Eşik parametre guven_skoru_esigi, varsayılan 50; akran analizinde <50 'düşük güven' sayılır.

**Dayanak:**

- [28] Curran, 2016 — Özensiz yanıtı saptama yöntemlerini gözden geçirir ve tek göstergeye değil birden çok göstergenin birlikte kullanılmasına dikkat çeker; birden fazla bileşeni birleştiren güven puanı fikrini destekler.
- [59] Huang ve ark., 2012 — Yetersiz çabalı yanıtlamayı saptama göstergelerini (ör. yanıt süresi, tutarsızlık) ve caydırıcı yönergeleri inceler; dikkat soruları ve güven puanındaki davranış göstergelerine dayanak sağlar.

> Güven puanının bileşimi (0,5 kontrol + 0,5 olay skoru), olay cezaları (10/10/5/15/10/5/5) ve 50 eşiği kurum içi tasarım kararıdır; akademik bir kesme noktasına dayanmaz. Kaynaklar yalnızca birden çok yanıt kalitesi göstergesinin birlikte kullanılması fikrini destekler; tarayıcı olaylarının (sekme değiştirme, tam ekrandan çıkma vb.) yanıt geçerliğiyle ilişkisi için doğrulanmış bir kaynak eşlenmemiştir.

### K5 alan açma kuralı · _Kurum içi_

K1–K4 sonrası öğrenciye hangi derinleşme alanlarının (en fazla 2) açılacağına karar verir.

**Nasıl:** İlk 15 bölüm (DAL_SECIM_UST_N) alanlarına göre gruplanır; 1. sıradaki bölümün alanı her zaman açılır, diğer alanlar en iyi 3 bölüm ortalaması ana alandan en çok 10 puan (IKINCI_ALAN_FARK) gerideyse açılır (k5_max_dal_sayisi = 2). Ana alanın tüm soruları, ikinci alanın yalnızca ilk 6 sorusu sorulur (toplam en fazla 14 + 6 = 20). Gösterilen alan puanı = ilk 15'teki toplam uyum payı (%). Eski K4 eşiği (k5_esik_puani 80→70) artık seçimde kullanılmıyor.

**Dayanak:**

- [42] Gati ve Asher, 2005 — Kariyer kararında önce geniş bir ön elemeyle seçenekleri daraltıp sonra az sayıda seçeneği derinlemesine incelemeyi öneren aşamalı modeldir; K1–K4 sonrası yalnızca en uygun 1–2 alanın K5 ile derinleştirilmesi bu huni mantığından esinlenir.
- [55] Hendrickson, 2007 — Önceki aşamadaki performansa göre sonraki modülün seçildiği çok aşamalı test tasarımını tanıtır; K5'in K1–K4 sonuçlarına göre dallanmasına genel yapısal dayanak verir, ancak K5 bir yetenek testi değildir.

> İlk 15 bölüm (DAL_SECIM_UST_N), en fazla 2 alan, 10 puanlık ikinci alan farkı ve 14 + 6 soru sınırı kurum içi tasarım kararıdır; akademik bir kesme noktasına dayanmaz.

### K5 üst alanlar, alan soruları ve dal içi uyum

17 üst alan (Mühendislik, Bilişim & Yazılım, Sağlık & Rehabilitasyon …) için iş türü eksenleri, bölüm–alan eşleşmeleri ve alan içi bölüm uyumu.

**Nasıl:** 301 bölüm elle gözden geçirilmiş bölüm_dal_eslesme ile bir üst alana bağlıdır (eski yapı: A1–A9'a göre K-Means ile 8 dal). Yeni yapıda dal içi uyum = öğrencinin eksen puanlarının bölüm–eksen bağlarıyla (bolum_k5_baglari, 0–1) ağırlıklı ortalaması; bölümler arası z-skoru alınır, güven = min(1, öğrenci K5 std / 15) ve skor = 50 + güven × 15 × z (0–100). Bağ yoksa eski yöntem (katman içi ölçekli 100 − |fark|) çalışır.

**Dayanak:**

- [137] UNESCO Institute for Statistics, 2015 — Eğitim alanlarının uluslararası hiyerarşik sınıflamasıdır; 301 bölümün 17 üst alana gruplanmasına referans çerçeve sunar, ancak 17 alanlık yapı ISCED-F ile birebir aynı değildir.
- [147] Yükseköğretim Kurulu, t.y. — Türkiye'deki lisans/önlisans programlarının resmî listesini ve alan bilgilerini sunar; 301 bölümün tanımlanması ve gruplanmasında başvuru kaynağıdır.
- [85] MacQueen, 1967 — K-ortalamalar kümeleme yöntemini tanımlar; eski yapıdaki A1–A9'a göre 8 dala kümelemenin yöntemsel dayanağıdır.
- [58] Holland, 1997 — Holland'ın profil farklılaşması kavramı, öğrencinin eksen puanlarının ne kadar ayrıştığına göre güven katsayısı uygulamasına kavramsal esin verir.
- [140] Ward, 1963 — Bölüm/meslek profillerinin benzerliğe göre hiyerarşik olarak kümelenmesini destekler.

> 17 üst alan, bölüm–alan eşleşmeleri ve bölüm–eksen bağları (0–1) elle hazırlanmıştır. Güven = min(1, std/15), 50 + güven × 15 × z skoru ve eski yöntemdeki 100 − |fark| hesabı kurum içi tasarım kararıdır.

### Gelişim yorum havuzu (sonuç yorumları)

Her değişken için puan aralığına göre öğrenciye gösterilen durum tespiti, öneri, kaynak türü ve tahmini efor cümleleri.

**Nasıl:** 31 değişken × 5 aralık = 155 elle yazılmış satır. Profil ekranında aralık ham puana göre seçilir: ≥80 belirgin üstün, ≥60 üstün, ≥40 beklenti, ≥20 altında, <20 belirgin altında; öneri yalnızca 'altında' aralıklarında yazılıdır, P4'te öneriler bilinçli olarak boş bırakıldı.

**Dayanak:**

- [32] Dickson ve Kelly, 1985 — Herkese uyabilecek genel kişilik yorumlarının kişiler tarafından yüksek doğrulukta algılandığını (Barnum etkisi) özetler; yorumların puan aralığına özgü ve somut yazılması gerekliliğine dikkat çeker (bileşenin bunu ne ölçüde başardığı ayrıca sınanmamıştır).

> 155 yorum cümlesi kurum içinde elle yazılmıştır; puan aralıkları (≥80, ≥60, ≥40, ≥20) akademik bir kesme noktasına dayanmaz. Önerilerin yalnızca 'altında' aralıklarında yazılması ve P4'te boş bırakılması içerik kararıdır. Güçlü yön temelli geri bildirim için doğrulanmış bir kaynak eşlenmemiştir.

### Seviye etiketleri ve 'Puan Rehberi' · _Kurum içi_

Puanların 'Çok güçlü / Güçlü / Orta / Gelişime açık' gibi etiketlerle ve 'bu bir not değil, eğilimdir' açıklamasıyla sunulması.

**Nasıl:** Puan Rehberi ve rapor: ≥75 Çok güçlü, 62–74 Güçlü, 40–61 Orta, <40 Gelişime açık; 'Neden bu bölüm' kartında öğrenci ≥75/≥62/≥50 ve bölüm yüzdeliği ≥85 Çok yüksek, ≥70 Yüksek; katman ekranında renk ≥70/≥40 ve 'güçlü' listesi ≥60; raporda güçlü ≥62, gelişim <45. Yorum ilkeleri metni (örüntüye bak, aşırı güçlü yön, sonuçlar değişebilir) elle yazılmıştır.

**Dayanak:**

- [150] Zenisky ve Hambleton, 2012 — Puan raporlarında açık etiketler, yorum rehberi ve kullanıcıya uygun dil kullanılmasını önerir; seviye etiketleri ve 'bu bir not değil, eğilimdir' açıklamalı Puan Rehberi'ni destekler.
- [2] American Educational Research Association, American Psych…, 2014 — Test içeriğinin kapsam geçerliği, madde geliştirme, belgeleme ve puanların yorumlanmasına ilişkin genel standartları ortaya koyar; bileşen bu ilkelerden esinlenir, standartların resmî bir uygunluk denetiminden geçmemiştir.

> Seviye eşikleri (≥75, 62–74, 40–61, <40; ≥85/≥70 yüzdelik; renk ≥70/≥40; güçlü ≥60/≥62; gelişim <45) kurum içi tasarım kararıdır, standart belirleme (standard setting) çalışmasıyla saptanmamıştır ve ekranlar arasında tutarlı değildir. 'Aşırı güçlü yön' ilkesi için doğrulanabilen bir kaynak bulunamadı.

### Değerlendirme yönergeleri ve ekran metinleri · _Kurum içi_

Soru tiplerinin nasıl cevaplanacağını anlatan metinler, ara motivasyon cümleleri ve mola ekranı.

**Nasıl:** 4 soru tipi açıklaması (Katılım, Tercih, Durum, Dikkat sorusu), 4 'filizlenme' mesajı; 8+ soruluk bölümde yarıda bir kez nefes molası önerilir; 'doğru ya da yanlış cevap yok, şu anki hâline göre cevap ver' yönergesi.

**Dayanak:**

- [109] Podsakoff ve ark., 2003 — Ortak yöntem yanlılığını azaltmak için yanıtlayıcılara doğru ya da yanlış cevap olmadığının belirtilmesini önerir; yönerge metnini doğrudan destekler.
- [107] Paulhus, 1991 — Sosyal beğenirlik dahil yanıt yanlılıklarını ve bunları azaltma yollarını (ör. yönergeler, anonimlik vurgusu) ele alır; 'doğru ya da yanlış cevap yok' yönergesine dayanak sağlar.
- [41] Galesic ve Bosnjak, 2009 — Uzun çevrim içi anketlerde ilerleyen sorularda yanıt kalitesinin düştüğünü gösterir; uzun bölümlerde mola önerilmesine ve katman başına süre bilgisinin verilmesine gerekçe sağlar (mola eşiği kurum içidir).

> Soru tipi açıklamaları, 'filizlenme' mesajları ve 8+ soruluk bölümde yarıda bir mola önerisi kurum içi metin/tasarım kararıdır.

### Soru geçerlilik testi (3 model kör sınıflama)

Her soru/şık metninin gerçekten bağlı olduğu değişkeni ölçüp ölçmediğini dil modelleriyle sınayan admin analizi.

**Nasıl:** Metin, değişkeni söylenmeden 3 embedding modeline verilir; adaylar yalnızca kendi değişken ailesi (aynı kod öneki); negatif ağırlıklı SJT şıkları hariç. Ölçüt: en az 2/3 modelin doğru değişkeni seçmesi; katman eşiği %70, genel eşik %80. Rastgele taban = C(3,2)·p²(1−p) + p³, p = 1/aday_sayısı; 'kaç kat üstü' oranı raporlanır.

**Dayanak:**

- [79] Lawshe, 1975 — Uzman panelinin maddeleri yapıya uygun bulma oranından kapsam geçerlik oranı (CVR) hesaplar; 'en az 2/3 değerlendiricinin doğru değişkeni seçmesi' ölçütü bu mantıktan esinlenir, ancak değerlendiriciler insan uzman değil dil modelleridir.
- [127] Stemler, 2004 — Uzlaşma (yüzde uyum) ve tutarlılık yaklaşımlarını karşılaştırır; modeller arası çoğunluk uyumunun bir uzlaşma ölçüsü olarak raporlanmasına dayanak verir.
- [49] Graham ve ark., 2012 — Değerlendiriciler arası uyumun ölçülmesi ve uygulamada kabul edilebilir uyum düzeylerinin belirlenmesini ele alır; yüzde uyum eşiği kullanılmasına genel dayanak verir, %70/%80 değerlerini ise doğrudan belirlemez.
- [112] Reimers ve Gurevych, 2019 — Cümle gömmelerini (embedding) anlamsal benzerlik için üreten yöntemi tanıtır; metinlerin değişken tanımlarıyla gömme benzerliği üzerinden sınıflanmasının teknik dayanağıdır.
- [78] Landis ve Koch, 1977 — Uyum katsayıları için "zayıf/orta/önemli/neredeyse tam" eşiklerinin kaynağıdır.
- [89] McHugh, 2012 — Sağlık ve eğitim bağlamında daha katı kappa yorum eşiklerinin kullanımını destekler.

> Dil modellerinin insan uzman yerine kullanılması bir esinlenmedir; Lawshe CVR veya kappa birebir hesaplanmaz. Katman %70 ve genel %80 eşikleri kurum içi karardır. Rastgele taban formülü (C(3,2)·p²(1−p) + p³) basit binom olasılığıdır, ayrı bir kaynak gerektirmez.

## Uyum hesaplama

### Meslek verisi (ESCO) ve çeviri

Bölüm profillerinin hesaplandığı meslek havuzu ve İngilizce–Türkçe çeviri adımı.

**Nasıl:** ESCO'dan 3.039 meslek (esco_kodu, ad, açıklama, isco_grubu) toplu yüklenir; eski 7.764 kayıtlık liste bırakıldı. Bölüm açıklamaları TR→EN, meslek ad/açıklamaları EN→TR Helsinki-NLP (opus-mt, tc-big-en-tr) yerel modelle çevrilir; ad–açıklama tutarsız çıkan çeviriler model_a ile taranıp elle gözden geçirilir; üniversiteyle ilgisi olmayan meslekler ayıklanır.

**Dayanak:**

- [38] European Commission, t.y. — Meslek havuzunun (3.039 meslek, kod, ad, açıklama) AB'nin resmî ESCO sınıflamasından alınmasının doğrudan dayanağıdır.
- [61] International Labour Organization, 2012 — Meslek kayıtlarındaki isco_grubu alanının ESCO'nun bağlandığı ISCO-08 hiyerarşisine dayandığını gösterir.
- [133] Tiedemann ve Thottingal, 2020 — İngilizce–Türkçe çeviride kullanılan Helsinki-NLP opus-mt modellerinin kaynağı olan OPUS-MT hizmetini tanıtır.
- [134] Tiedemann ve ark., 2024 — Kullanılan tc-big-en-tr dâhil Tatoeba Challenge OPUS-MT modellerinin eğitim ve değerlendirmesini anlatır; yerel açık kaynak modelle çeviri tercihini destekler.

> Çevirilerin model_a ile tutarsızlık taraması, elle gözden geçirme ve üniversiteyle ilgisiz mesleklerin ayıklanması kurum içi kalite kontrol kararlarıdır; yayımlanmış bir kalite tahmini yöntemine dayanmaz. TMSS/İŞKUR meslek sözlüğü pipeline'da kullanılmadığı için eklenmedi.

### Bölüm beklenen profili (embedding eşleştirme pipeline'ı)

301 bölümün 31 değişkendeki 'beklenen profilini' (agirlik_degeri) çıkaran, öğrenciden bağımsız offline hesaplama.

**Nasıl:** Meslek ve bölüm tam açıklamaları 3 modelle (turkce-embedding-bge-m3, bert-base-turkish-cased-mean-nli-stsb-tr, bge-large-en-v1.5) anlamsal benzerlikle eşleşir; ilişki ortalamanın en az 1 std üstündeyse sayılır, model konsensüsü önceliklendirir; yakın mesleklerin puanları ağırlıklı ortalamayla bölüm profiline dönüşür (agirlikli_varyans, etkin_meslek_sayisi, yakinsama_skoru güvenilirlik göstergeleri; yakinsama_esik_sigma 0,10). Çıktı taslak tabloya yüklenir, önizleme sonrası süper admin onayıyla yeni versiyon olur; veri yoksa nötr 50.

**Dayanak:**

- [112] Reimers ve Gurevych, 2019 — Meslek ve bölüm açıklamalarını cümle embedding'leriyle kosinüs benzerliği üzerinden eşleştirme yaklaşımının temel yöntemidir; kullanılan Türkçe NLI-STS BERT modeli bu mimariyle eğitilmiştir.
- [23] Chen ve ark., 2024 — Kullanılan turkce-embedding-bge-m3 modelinin temel aldığı çok dilli BGE-M3 embedding modelini tanıtır.
- [20] Cer ve ark., 2017 — Çok dilli ve diller arası anlamsal metin benzerliği (STS) görevini ve STS-B veri setini tanımlar; açıklamalar arası benzerlik puanlamasının ve stsb-tr modelinin dayandığı değerlendirme çerçevesidir.

> Embedding eşleştirmesi literatüre dayanır; ancak 'ortalama + 1 std' eşiği, 3 model konsensüsü, ağırlıklı ortalama ile bölüm profiline aktarma, yakinsama_esik_sigma = 0,10 ve veri yoksa nötr 50 kuralı kurum içi tasarım kararlarıdır; belirli bir yayındaki yöntemin uyarlaması değildir.

### Katman ve kriter ağırlıkları · _Kurum içi_

Her katmanın ve değişkenin toplam uyuma katkı payı.

**Nasıl:** Katman ağırlıkları veritabanındaki katman ayarından (normalizasyon_agirligi) okunur; mevcut kurulumda K1–K4 eşit (%25). Değişken ağırlığı = katman ağırlığı / katmandaki (eşleşmeye giren) değişken sayısı, toplam 1'e normalize. (0008 göçü ilk kurulumda 20/20/20/40 atamıştı.)

**Dayanak:**

- [29] Dawes, 1979 — Eşit/birim ağırlıklı doğrusal modellerin optimize edilmiş ağırlıklara yakın yordama sağladığını gösterir; katman içinde değişken ağırlığının eşit paylaştırılmasını destekler.
- [98] Nye ve ark., 2012 — İlgilerin akademik ve iş performansını anlamlı yordadığını gösterir; ilgi temelli katmana görece yüksek ağırlık verilmesine genel (sayısal olmayan) dayanak sağlar.
- [9] Barrick ve Mount, 1991 — Kişilik boyutlarının performansla ilişkisinin orta düzeyde olduğunu gösterir; kişilik katmanının sıfırdan büyük ama baskın olmayan bir ağırlık almasını destekler.

> Eşit ağırlık seçimi kurum içi tasarım kararıdır; AHP vb. bir ağırlıklandırma çalışmasına dayanmaz. Ağırlık bilgisinin güvenilir olmadığı durumda eşit ağırlıklandırma literatürde savunulan bir varsayımdır. Canlı veritabanındaki değerin %25 olduğu ayrıca kontrol edilmelidir.

### Katman içi göreli ölçekleme ve performans matrisi

Öğrenci ve bölüm profillerini düzeyden bağımsız 'şekil' olarak karşılaştırma.

**Nasıl:** Öğrenci vektörü ve her bölüm satırı her katman içinde kendi ortalama/std'sine göre 50 + 15·z'ye ölçeklenir (≤2 değişkenli katmanda ham değer); performans_ij = max(0, 100 − |öğrenci_j − bölüm_ij|). Bu matris 10 yöntemin ortak girdisidir; koçluk gap analizi ve K5 eski yöntemi de aynı ölçeği kullanır.

**Dayanak:**

- [27] Cronbach ve Gleser, 1953 — Profil benzerliğinin düzey, dağılım ve şekil bileşenlerine ayrıştırılabileceğini gösterir; katman içi z-ölçekleme ile düzey ve dağılımı ayıklayıp 'şekil' karşılaştırması yapılmasının kuramsal dayanağıdır.
- [35] Edwards, 1993 — Kişi–çevre uyumunda tek bir fark/benzerlik indeksinin düzey ve şekil bilgisini karıştırdığını eleştirir; mutlak fark temelli performans skorunun sınırlılığını belgelemek için uyarı niteliğinde kaynaktır.
- [76] Kristof-Brown ve ark., 2005 — Kişi–iş/kişi–çevre uyumunun anlamlı sonuçlarla ilişkili olduğunu gösterir; öğrenci–bölüm profil uyumunu hesaplama fikrini genel olarak destekler.

> 50 + 15·z ölçeklemesi, ≤2 değişkenli katmanda ham değer kullanımı ve performans_ij = max(0, 100 − |fark|) formülü kurum içi tasarım kararıdır; kaynaklardan esinlenilmiştir, birebir uyarlama değildir.

### 10 ÇKKV yöntemi ve Kendall W

Bölümleri 10 çok kriterli karar yöntemiyle puanlayıp ortalamasını 'toplam uyum' yapan motor.

**Nasıl:** WSM, WPM, WASPAS (0,5/0,5), TOPSIS (vektör normalizasyonu), VIKOR (v = 0,5, 1 − Q), GRA (ξ = 0,5), MOORA, COPRAS, EDAS, MABAC; tüm kriterler fayda yönlü. Her yöntem çıktısı min-max ile 0–100'e çekilir (eşitse 50), 10'unun aritmetik ortalaması alınır. Yöntemler arası sıralama uyumu Kendall W = 12S / (m²(n³ − n)) ile hesaplanır; yöntem skorları ve W yalnızca admin şemasında.

**Dayanak:**

- [60] Hwang ve Yoon, 1981 — TOPSIS'in ve WSM/WPM gibi temel çok nitelikli karar yöntemlerinin özgün kaynağıdır.
- [101] Opricovic ve Tzeng, 2004 — VIKOR'un (v = 0,5 uzlaşı ağırlığı dâhil) formülasyonunu verir ve TOPSIS ile karşılaştırır.
- [148] Zavadskas ve ark., 2012 — WSM ve WPM'yi λ ağırlığıyla birleştiren WASPAS yöntemini tanımlar; sistemdeki 0,5/0,5 birleşimin dayanağıdır.
- [68] Kendall ve Babington Smith, 1939 — Yöntemler arası sıralama uyumunun Kendall W ile ölçülmesinin özgün kaynağıdır.
- [11] Behzadian ve ark., 2012 — TOPSIS'in uygulama alanlarını ve yöntemsel varyantlarını özetleyerek yöntem seçimini gerekçelendirir.

> GRA, MOORA, COPRAS, EDAS ve MABAC için de özgün yayınlar mevcuttur, ancak bileşen başına 4 kaynak sınırı nedeniyle eklenmedi. 10 yöntemin min-max sonrası aritmetik ortalamayla birleştirilmesi (topluluk ÇKKV) kurum içi tasarım kararıdır; belirli bir sıralama birleştirme yöntemine dayanmaz.

### Kaygı (P4) eşleşme dışı ve ters yönlü değişken · _Kurum içi_

Duygusal hassasiyet puanının bölüm önerisine katılmaması ve koçlukta tersine yorumlanması.

**Nasıl:** Parametre eslesme_disi_degiskenler (varsayılan 'P4') bölüm eşleşmesinden çıkarılır (simülasyonda yalnız kaygı değişince ilk 10'da ~4 bölüm değişiyordu); P4 ters_yonlu işaretlidir: gap, öncelik, trend ve tekrar ölçümde fark işareti çevrilir.

**Dayanak:**

- [117] Saka ve ark., 2008 — Kaygı ve olumsuz duygulanımın meslek kararını zorlaştıran bir etken olduğunu gösterir; kaygının bölüm seçimi ölçütü değil koçlukta ele alınacak bir engel olarak yorumlanmasını destekler.
- [43] Gati ve ark., 1996 — Kariyer karar güçlüklerini sınıflandırır; kaygının uyum ölçütünden çok karar sürecinin bir güçlüğü olarak ele alınmasına çerçeve sağlar.
- [92] Mehrabi ve ark., 2021 — Algoritmik kararlarda hassas özelliklerin sonuçları çarpıtabileceğini tartışır; duygusal hassasiyet puanının öneri skorundan dışlanmasına genel etik dayanak sağlar.

> P4'ün eşleşmeden çıkarılması ve ters yönlü işaretlenmesi kurum içi tasarım kararıdır (gerekçe: kurum içi simülasyonda yalnız kaygı değişince ilk 10'da ~4 bölümün değişmesi); kaynaklar genel gerekçe sağlar, bu kuralı doğrudan önermez.

### Alan tutarlılığı cezası ve alan komşuluğu · _Kurum içi_

Öneri listesinde konu olarak alakasız bölümlerin (ör. Hukuk + Veterinerlik) yan yana çıkmasını engelleyen kurallar.

**Nasıl:** Alan gücü = alandaki en iyi 3 bölümün ortalaması; puan += katsayı × (alan_gücü − en_güçlü_alan), katsayı parametre alan_tutarlilik_katsayisi = 3 (0 = kapalı). Ardından 17 alan için elle yazılmış simetrik KOMSU tablosuyla liste gruplanır: grup 0 = en güçlü alan + komşuları, grup 1 = ana alana en çok 10 puan yakın ikinci alan, grup 2 = diğerleri (silinmez, sona iner).

**Dayanak:**

- [58] Holland, 1997 — Altıgen modelde komşu tiplerin daha tutarlı olduğu 'tutarlılık' kavramını tanımlar; alan komşuluğu ve tutarlılık cezasının esin kaynağıdır.
- [135] Tracey ve Rounds, 1993 — İlgi alanlarının dairesel (komşuluk) yapısını meta-analitik olarak destekler; alanlar arası yakınlık tablosu fikrine dayanak sağlar.
- [110] Prediger, 1982 — Veri/fikir ve insan/nesne boyutlarıyla alanlar arası uzaklığın tanımlanabileceğini gösterir; komşu alan gruplamasına kavramsal destek verir.
- [137] UNESCO Institute for Statistics, 2015 — Eğitim alanlarının hiyerarşik sınıflamasını verir; 17 alanın tanımlanmasına ve ilişkilendirilmesine resmî referans sağlar.

> Alan gücü (en iyi 3 ortalaması), alan_tutarlilik_katsayisi = 3, 10 puanlık ikinci alan eşiği ve 17 alanlık elle yazılmış KOMSU tablosu kurum içi tasarım kararlarıdır; Holland altıgeninden esinlenilmiştir, ampirik olarak türetilmiş bir uzaklık matrisi değildir.

### K5 etkisi, eşitlik bozma ve ilk 20 liste · _Kurum içi_

Alan sorularının nihai uyuma katılması ve gösterilen sıralamanın kuralları.

**Nasıl:** nihai = toplam_uyum + 0,50 × (dal_ici_uyum − 50), en fazla ±25, 0–100 (0,30→0,50 seçimi iki aşamalı doğrulama simülasyonuna dayanır: ilk 3 doğruluğu %75,5→%76,5). Sıralama: alan grubu, nihai uyum azalan, agirlikli_varyans artan, etkin_meslek_sayisi azalan, ad; öğrenciye ilk 20 bölüm gösterilir ve yalnızca K1–K4 tamamlanınca hesaplanır.

**Dayanak:** Akademik dayanak yok.

> K5 katkı katsayısı (0,50), ±25 sınırı, eşitlik bozma sırası ve ilk 20 gösterim kurum içi tasarım kararlarıdır; 0,30→0,50 seçimi yalnızca kurum içi sentetik yanıtlayıcı simülasyonuna (ilk 3 doğruluğu %75,5→%76,5) dayanır, akademik bir kesme noktasına veya yayımlanmış bir puan birleştirme yöntemine dayanmaz. Simülasyondaki küçük kazanç (~1 puan) dış örneklemle doğrulanmamıştır.

### 'Neden bu bölüm?' açıklamaları · _Kurum içi_

Her önerilen bölüm için örtüşen güçlü yönleri, öğrencinin kanıt cevaplarını, K5 notunu ve dikkat notunu üreten açıklama.

**Nasıl:** Örtüşen yön: bölümün o özellikteki bölümler arası yüzdeliği ≥60 ve öğrencinin ölçekli puanı ≥55; en fazla 3 yön, 30 kısa ad (KISA_AD). Dikkat notu: bölüm yüzdeliği ≥85 ve öğrenci ≤40, aynı not 3+ bölümde çıkıyorsa gösterilmez. K5 notu ana eksen puanı ≥60/≤40. Kanıtlar: SJT'de ağırlık ≥0,5 seçilen şık, Likert'te en güçlü katılım, kutupta 1. veya 4. şık; metinler 110 karakterle kısaltılır.

**Dayanak:**

- [151] Zhang ve Chen, 2020 — Öneri sistemlerinde özellik temelli ve şablon cümleli açıklamaların kullanıcı güvenini ve şeffaflığı artırdığını derler; 'Neden bu bölüm?' açıklamalarının genel dayanağıdır.

> Yüzdelik ≥60 / puan ≥55 örtüşme eşikleri, ≥85/≤40 dikkat notu kuralı, 3+ bölümde tekrar eden notun gizlenmesi, K5 ≥60/≤40 ve 110 karakter kısaltması kurum içi tasarım kararlarıdır; akademik bir kesme noktasına dayanmaz.

### Cevap analizi (süper admin) · _Kurum içi_

Bir öğrencinin her cevabının hangi özelliğe kaç puan kattığını ve ilk 5 öneriyi hangi özelliklerin yukarı/aşağı çektiğini gösteren inceleme ekranı.

**Nasıl:** Katkılar katman puanlamasıyla aynı fonksiyonla (cevaplari_puanla) hesaplanır; etki = kriter ağırlığı × (bölümün performansı − tüm bölümlerin ortalaması), ilk 5 yukarı ve 3 aşağı özellik; görüntüleme denetim kaydına yazılır, okul yetkilisi erişemez.

**Dayanak:**

- [118] Saltelli ve ark., 2008 — Model çıktısının girdilere duyarlılığını inceleme ilkelerini verir; özellik etkisinin 'ağırlık × ortalamadan sapma' ile gösterilmesi bu yaklaşımın basit, yerel bir biçimidir (esinlenme).
- [72] Kişisel Verilerin Korunması Kanunu, Kanun No. 6698, 2016 — Veri sorumlusunun kişisel verilere erişimi denetleme ve güvenlik önlemi alma yükümlülüğü, görüntülemenin denetim kaydına yazılması ve okul yetkilisinin erişiminin kısıtlanmasını destekler.

> İlk 5 yukarı / 3 aşağı özellik gösterimi ve etki formülü kurum içi tasarım kararıdır; SHAP gibi yerleşik bir açıklama yöntemi değildir.

## Koçluk

### Hedef bölüm seçimi ve değiştirme hakkı · _Kurum içi_

Öğrencinin koçluk planı için tek bir hedef bölüm seçmesi.

**Nasıl:** Aynı anda 1 aktif hedef; ilk seçim serbest, sonraki her değişiklik 1 hak harcar (varsayılan 3 hak), yönetici değişikliği hak harcamaz; eski hedefe dönülünce ilerleme korunur.

**Dayanak:**

- [83] Locke ve Latham, 2002 — Belirli ve bağlılık duyulan hedeflerin performansı artırdığını gösterir; aynı anda tek aktif hedef ve değişikliğin bedelli olması hedef bağlılığını korumaya yöneliktir.
- [63] Iyengar ve Lepper, 2000 — Çok seçenek arasında seçim yapmanın motivasyonu ve seçime bağlılığı düşürebildiğini gösterir; tek aktif hedef kısıtı bu bulgudan esinlenir.
- [121] Scheibehenne ve ark., 2010 — Seçenek fazlalığı etkisinin ortalamada küçük ve koşula bağlı olduğunu gösterir; tek hedef kuralının gerekçesi temkinli kurulmalıdır.
- [43] Gati ve ark., 1996 — Kariyer kararı güçlüklerinin (hazır olmama, bilgi eksikliği, tutarsız bilgi) sınıflamasını verir; hedef değiştirme hakkının kararsızlığı tümüyle engellemeden sınırlamasının gerekçesini destekler.

> Tek aktif hedef ilkesi kısmen hedef bağlılığı ve seçenek fazlalığı literatürüne dayanır; ancak varsayılan 3 değiştirme hakkı, ilk seçimin serbest olması ve yönetici değişikliğinin hak harcamaması kurum içi tasarım kararıdır, akademik bir sayıya dayanmaz.

### Gap analizi, öncelik ve bölüm ayırt ediciliği · _Kurum içi_

Öğrenci ile hedef bölüm arasındaki farkı özellik özellik sınıflayıp en önemli gelişim alanlarını bulma.

**Nasıl:** Göreli fark (katman/dal içi 50 ± 15 ölçekte öğrenci − bölüm) 5 kategoriye ayrılır: ≥15 belirgin üstün, ≥5 üstün, >−5 uyumlu, >−15 altında, ≤−15 belirgin altında. Öncelik = |fark| × bölüm ağırlığı/100 × katman ağırlığı (K4 40, diğerleri 20) × ayırt edicilik/100; ayırt edicilik = bölümün o özellikteki bölümler arası yüzdeliği (en az 20 yayındaki bölüm), <40 ise odak alanı olmaz, ≥75 ise 'bölüm talepkâr' cümlesi kullanılır.

**Dayanak:**

- [30] Dawis ve Lofquist, 1984 — Kişinin yetenek/ihtiyaçları ile çevrenin gereksinim/pekiştireçleri arasındaki uygunluğun (correspondence) karşılaştırılmasını kuramsal olarak temellendirir; özellik bazında öğrenci–bölüm farkı bu mantıktan esinlenir.
- [76] Kristof-Brown ve ark., 2005 — Kişi–iş uyumunun memnuniyet ve bağlılıkla ilişkisini meta-analitik olarak gösterir; uyum açıklarının gelişim alanı olarak ele alınmasını destekler.

> Fark kategorilerinin eşikleri (±5, ±15), öncelik formülü, K4 ağırlığının 40 diğerlerinin 20 olması, ayırt edicilik için en az 20 yayın, <40 ve ≥75 kesme noktaları kurum içi tasarım kararıdır; akademik bir kesme noktasına dayanmaz.

### Gelişim yol haritası yapısı

Gelişim alanlarını aşamalı bir plana dönüştürür.

**Nasıl:** İçeriği olan ilk 3 gelişim alanı odak olur (ODAK_ALAN_SAYISI), en belirgin 2 güçlü yön için 'gücünü kullan' adımları eklenir; adımlar 3 aşamaya dağılır: 'Bu hafta başla' (1–2 hafta), 'Önümüzdeki 1–3 ay', 6–12 ay. Önceki aşamanın %50'si bitmeden sonraki aşamada 'önce öncekine odaklan' uyarısı (kilit yok); sıradaki adım = en erken aşamadaki en öncelikli tamamlanmamış adım. Eski F4 sürümünde tahmini efor kısa/orta/uzun → şimdi/bu dönem/uzun vadede.

**Dayanak:**

- [83] Locke ve Latham, 2002 — Belirli, ulaşılabilir hedeflerin ve ilerleme geri bildiriminin performansı artırdığını gösterir; gelişim alanlarının somut adımlara dönüştürülmesini destekler.
- [7] Bandura ve Schunk, 1981 — Yakın (kısa vadeli) alt hedeflerin uzak hedeflere göre öz-yeterliği ve ilgiyi daha çok artırdığını gösterir; 'Bu hafta başla' aşaması bu ilkeye dayanır.
- [16] Brown ve Ryan Krane, 2000 — Kariyer müdahalelerinde yazılı hedef belirleme ve bireyselleştirilmiş planın etkili kritik bileşenler arasında olduğunu gösterir; yol haritasının bireyselleştirilmiş, yazılı bir plan olarak sunulmasını destekler.

> Odak alan sayısının 3, güçlü yön sayısının 2 olması, aşama süreleri ve %50 tamamlama uyarısı kurum içi tasarım kararıdır. 'Güçlü yön temelli koçluk' için ayrıca doğrulanmış bir kaynak eklenmedi.

### Gelişim adımları içeriği ve adım detayları

31 değişken için 'nedir', 'neden önemli' metinleri ve somut adımlar; her adım için 'Nasıl yaparsın?', 'Nasıl anlarsın?' ve ipucu.

**Nasıl:** gelisim_icerigi: her değişkende nedir, gelisim_neden, guclu_neden ({bolum} yer tutucusu) ve aşama başına 2 olmak üzere 6 gelişim + 2 güçlü yön adımı (toplam 202 gelişim, 62 güçlü adımı); 8 adım türü (araştırma, görüşme, deneyim, proje, alışkanlık, okuma, kurs, kendini değerlendirme), süre ve ölçüt. gelisim_detay: 264 adımın adım adım uygulaması, kontrol listesi ve ipucu; dosya başlığında Locke & Latham 2002, Harkin ve ark. 2016, Gollwitzer & Sheeran 2006, Lally ve ark. 2010, Brown & Ryan Krane 2000, OECD 2021 anılır. Değerler (K1) adımları değeri değiştirmeyi değil uyumu sınamayı hedefler.

**Dayanak:**

- [52] Harkin ve ark., 2016 — İlerlemeyi izlemenin (özellikle kayıt tutma ve raporlama) hedefe ulaşmayı artırdığını gösterir; her adımdaki 'Nasıl anlarsın?' ölçütü ve kontrol listesini destekler.
- [46] Gollwitzer ve Sheeran, 2006 — Ne zaman/nerede/nasıl sorularını yanıtlayan eğer–ise planlarının hedefe ulaşmayı orta-büyük düzeyde artırdığını gösterir; 'Nasıl yaparsın?' adım detayları bu yaklaşımdan esinlenir.
- [77] Lally ve ark., 2010 — Alışkanlık oluşumunun kişiden kişiye çok değişen, ortalama iki aydan uzun süre aldığını gösterir; alışkanlık türü adımların aylar süren aşamalara yayılmasını destekler.
- [16] Brown ve Ryan Krane, 2000 — Kariyer müdahalelerinde yazılı alıştırmalar, bireysel yorum/geri bildirim, meslek bilgisi edinme, model alma ve destek oluşturmanın etkili kritik bileşenler olduğunu gösterir; araştırma, görüşme ve deneyim adım türlerini destekler.
- [45] Gollwitzer, 1999 — Koçlukta "ne zaman, nerede, nasıl" biçimindeki eylem planlarının kullanılmasını destekler.

> Adım metinleri, süreler ve 8 adım türü kurum içi olarak elle yazılmıştır; kaynaklar ilkeleri destekler, metinler bu çalışmalardan birebir uyarlanmamıştır. Dosya başlığında anılan OECD (2021) ve SMART hedef formülü için doğrulanmış künye eklenmedi; Locke & Latham (2002) hedef belirleme için 26. bileşende kullanıldı.

### Koçluk motoru: alan türü, kazanım, geri bildirim ve uyarlama

Adımları alan türüne göre çerçeveleyen, adım sonrası geri bildirim alan ve sıradaki adıma öneri ekleyen döngü.

**Nasıl:** Alan türü kod önekinden: D değer ('değiştirmen gerekmiyor'), P kişilik ('yavaş değişir, esneyebilir'), I beceri ('çalıştıkça gelişir'), A ilgi ('deneyip gör'); 8 adım türü ve 4 alan türü için kazanım cümleleri. Geri bildirim: ne yaptım / ne öğrendim (600 karakter), fayda 1–5, zorluk kolay/uygun/zor. Uyarlama: 14 gündür adım yoksa '10 dakika, ilk madde'; son adım zor ya da fayda ≤2 ise 'adımı küçült, 15–20 dk'; kolay ve fayda ≥4 ise 'bir adım daha ekle'.

**Dayanak:**

- [114] Roberts ve ark., 2017 — Kişilik özelliklerinin müdahaleyle ölçülebilir ama sınırlı ölçüde değişebildiğini gösterir; P (kişilik) alanlarının 'yavaş değişir, esneyebilir' çerçevesini destekler.
- [116] Ryan ve Deci, 2000 — Özerklik, yeterlik ve ilişkililik ihtiyaçlarının desteklenmesinin içsel motivasyonu artırdığını gösterir; değer alanında 'değiştirmen gerekmiyor' çerçevesi ve zorlayıcı olmayan dil bu kuramla uyumludur.
- [75] Kolb, 1984 — Somut deneyimin yansıtma ile öğrenmeye dönüştüğü döngüyü tanımlar; adım sonrası 'ne yaptım / ne öğrendim' geri bildirimi bu döngüden esinlenir.
- [52] Harkin ve ark., 2016 — İlerleme izlemenin hedefe ulaşmayı artırdığını gösterir; adım sonrası fayda/zorluk geri bildiriminin toplanmasını ve buna göre öneri verilmesini destekler.

> Alan türü çerçeve cümleleri, 600 karakter sınırı ve uyarlama kuralları (14 gün hareketsizlik, fayda ≤2 ya da 'zor' ise küçült, 'kolay' ve fayda ≥4 ise ekle) kurum içi tasarım kararıdır; akademik bir eşiğe dayanmaz.

### Tekrar ölçüm (alan bazında önce/sonra)

Odak alanında belirli sayıda adım bitince aynı sorularla gelişimin yeniden ölçülmesi.

**Nasıl:** Değer (K1) dışındaki alanlarda her 3 tamamlanan adımda bir (OLCUM_ADIM_ARALIGI) açılır; öğrencinin ilk değerlendirmede o değişkene en çok etki eden en fazla 5 sorusu yeniden sorulur, aynı puanlama kuralıyla önce/sonra karşılaştırılır. Gelişim ≥5 'daha güçlü cevaplar', ≤−5 'düşüş normal', arası 'belirgin değişim yok' yorumu; ters yönlü değişkende işaret çevrilir.

**Dayanak:**

- [64] Jacobson ve Truax, 1991 — Önce/sonra farkının ölçme hatasını aşıp aşmadığını güvenilir değişim indeksiyle değerlendirmeyi önerir; sistemdeki sabit ±5 eşiği bu indeks değildir, kaynak yöntemsel bir referans ve iyileştirme önerisidir.
- [8] Barnett ve ark., 2005 — Ön testte uç puan alanların son testte kendiliğinden ortalamaya yaklaşabileceğini açıklar; en düşük alanların yeniden ölçümünde görülen artışın bir kısmının gerçek gelişim olmayabileceğini hatırlatır.

> Her 3 adımda bir ölçüm, en fazla 5 soru ve ±5 yorum eşiği kurum içi tasarım kararıdır; ±5 güvenilir değişim indeksine dayanmaz. Az sayıda maddeyle yapılan tekrar ölçümde ölçme hatası, tekrar test etkisi ve ortalamaya gerileme sonucu etkileyebilir; yorumlar bu nedenle temkinli tutulmalıdır.

### Tur karşılaştırması

Öğrenci yeniden değerlendirildiğinde iki tur arasındaki değişimi yorumlayan bölüm.

**Nasıl:** En az 2 tamamlanmış tur gerekir; değişim = yeni − eski (ters yönlüde çevrilir): ≥15 belirgin gelişim, ≥5 gelişim, >−5 durgun, >−15 gerileme, ≤−15 belirgin gerileme. 31 değişken × 5 trend = 155 elle yazılmış yorum cümlesi.

**Dayanak:**

- [64] Jacobson ve Truax, 1991 — Değişimin anlamlı sayılması için ölçme güvenirliğini hesaba katan bir ölçüt önerir; turlar arası ±5/±15 eşiklerinin istatistiksel bir dayanağı olmadığını ve RCI'ya geçişin değerlendirilebileceğini gösterir.
- [84] Low ve ark., 2005 — İlgilerin ergenlikte görece kararlı olmakla birlikte değişmeye açık olduğunu gösterir; tur karşılaştırmasında değişimin temkinli yorumlanmasını destekler.
- [113] Roberts ve DelVecchio, 2000 — Kişilik sıra-düzen tutarlılığının ergenlikte yetişkinliğe göre daha düşük olduğunu gösterir; turlar arası değişimin beklenebilir olduğunu destekler.

> Trend eşikleri (±5, ±15) ve 155 yorum cümlesi kurum içi tasarım kararıdır; akademik bir kesme noktasına dayanmaz.

### İlham kaynakları

Odak ve güçlü alanlara uygun kitap, film/belgesel, ilham veren kişi, psikolojik yaklaşım, aktivite ve önemli olay önerileri.

**Nasıl:** gelisim_kaynak_onerileri tablosu değişken × 5 aralık × 6 kaynak tipi olarak admin panelinden elle girilir (içerik repoda değil). 'Filiz'e sor' cevaplarında tip başına elle yazılmış 'nasıl başla' şablonu kullanılır (ör. kitapta günde 15–20 sayfa ve bölüm sonu not); AI koç değişken başına en fazla 2 kaynağı hedef bölüme göre çerçeveler.

**Dayanak:**

- [6] Bandura, 1977 — Gözlemsel öğrenme ve modelleme kuramını ortaya koyar; ilham veren kişi ve film/belgesel önerilerinin rol modeli işlevini kuramsal olarak destekler.

> İçerik (kitap, film, kişi vb.) repoda değil, admin panelinden elle girilir; seçim ölçütleri ve 'nasıl başla' şablonları (ör. günde 15–20 sayfa) kurum içi tasarım kararıdır. Biblioterapi ve kariyer eğitiminde film kullanımı için doğrulanmış künye eklenmedi; Gibson (2004) rol modeli makalesinin künyesi birincil kaynakta doğrulanamadığı için eklenmedi.

### Haftalık görevler, seri ve Filiz seviyesi

Öğrencinin her hafta düzenli dönmesi için 3 görev, haftalık seri ve büyüme seviyesi.

**Nasıl:** Her hafta: yolculuk görevi (sıradaki katman → K5 → hedef seçimi → yol haritasındaki sıradaki adım), keşif görevi (öneri listesinden daha önce verilmemiş bölüm; yoksa öğrenci+hafta özetiyle sabit seçim) ve 3 soruluk yansıtma (neyi iyi yaptın / nerede zorlandın / gelecek hafta tek hedefin). Seri: haftada en az 2 görev. Puan = 10 × görev + 5 × plan adımı + 15 × katman; seviyeler 0 Tohum, 30 Filiz, 80 Fidan, 160 Genç Ağaç, 280 Çiçek Açan Ağaç, 450 Ulu Çınar; özet grafiği 8 hafta.

**Dayanak:**

- [31] Deterding ve ark., 2011 — Oyunlaştırmayı oyun dışı bağlamda oyun tasarım öğelerinin kullanımı olarak tanımlar; görev, puan ve seviye mekaniklerinin kavramsal çerçevesidir.
- [51] Hamari ve ark., 2014 — Oyunlaştırmanın etkilerinin çoğunlukla olumlu ama bağlama ve kullanıcıya bağlı olduğunu gösterir; puan/seviye sisteminin etkisinin izlenmesi gerektiğini destekler.
- [152] Zimmerman, 2002 — Öz-düzenlemeli öğrenmede planlama, izleme ve öz-yansıtma döngüsünü tanımlar; 3 soruluk haftalık yansıtma bu döngüden esinlenir.

> Haftada 3 görev, seri için en az 2 görev, puan katsayıları (10/5/15) ve seviye eşikleri (30, 80, 160, 280, 450) kurum içi tasarım kararıdır; seri (streak) mekaniği için ayrıca akademik kaynak eklenmedi.

### Motivasyon: YKS sayacı, haftalık mesaj ve rozetler · _Kurum içi_

Sınıfa göre YKS'ye kalan gün, haftalık kısa motivasyon cümlesi ve 9 rozet.

**Nasıl:** YKS tarihi Genel Takvim'de 'sınav' türünde YKS/TYT kaydı varsa resmî, yoksa Haziran'ın 3. cumartesisi 'tahmini'. Mesaj grupları: erken (9–10), temel (11), uzun (≥200 gün), tempo (100–199), deneme (30–99), son (<30) — toplam 20 elle yazılmış cümle, ISO hafta numarasına göre döner. Rozetler: değerlendirme, hedef, ilk adım, son 4 haftanın 3'ü, 5 keşif, 3 kitap, 3 'ne öğrendim', ≥5 puan gelişim, 10 adım; modülü kapalı rozet gösterilmez.

**Dayanak:**

- [73] Kivetz ve ark., 2006 — Hedefe yaklaştıkça çabanın arttığını (hedef gradyanı) gösterir; YKS'ye kalan güne göre değişen mesaj gruplarının esinlendiği ilkedir, birebir uyarlama değildir.
- [50] Hamari, 2017 — Rozetlerin kullanıcı etkinliğini artırabildiğini saha deneyiyle gösterir; 9 rozetlik sistemi destekler.

> Resmî YKS tarihi ÖSYM sınav takviminden alınmalıdır; takvim kaydı yoksa kullanılan 'Haziran'ın 3. cumartesisi' tahmini kurum içi bir varsayımdır ve öğrenciye 'tahmini' olarak gösterilmelidir. Gün aralıkları (200/100/30), 20 mesaj cümlesi ve 9 rozet ölçütü kurum içi tasarım kararıdır. Büyüme zihniyeti mesajları için doğrulanmış künye eklenmedi.

### Filiz otomatik rehber (kural tabanlı sohbet)

Yapay zekâ bağlı değilken öğrencinin gerçek verileriyle anahtar kelimeye göre cevap veren sohbet botu.

**Nasıl:** Mesaj Türkçe karakterden arındırılıp 25 konu anahtar listesiyle eşlenir (net, YKS, motivasyon, kararsızlık, sınav kaygısı, kulüp, koç, takvim, güçlü yön…); 6 kategoride 26 örnek soru; eşleşme yoksa 3 rastgele örnek önerilir. Sabit cevap metinleri elle yazılmıştır (ör. sınav kaygısı: 25–30 dakikalık bloklar, deneme sınavlarını gerçek koşulda çözmek, uyku düzeni; kararsızlık: 2–3 bölümü Listem'e ekle, karşılaştır, meslek sahibiyle konuş).

**Dayanak:**

- [33] Dunlosky ve ark., 2013 — Aralıklı çalışma ve deneme/geri getirme pratiğinin en etkili öğrenme teknikleri arasında olduğunu gösterir; 'deneme sınavlarını gerçek koşulda çöz' ve planlı çalışma önerilerini destekler.
- [19] Cepeda ve ark., 2006 — Dağıtılmış çalışmanın yığılmış çalışmaya üstünlüğünü meta-analitik olarak gösterir; çalışmayı bloklara bölme önerisini kısmen destekler.
- [139] von der Embse ve Jester, 2018 — Sınav kaygısının performansla olumsuz ilişkisini ve yordayıcılarını özetler; sınav kaygısı konusunun rehberde ele alınmasının gerekçesidir.
- [43] Gati ve ark., 1996 — Kariyer kararsızlığının bilgi eksikliği ve tutarsız bilgi gibi kaynaklarını sınıflar; kararsızlık cevabındaki 'bölümleri karşılaştır, meslek sahibiyle konuş' önerilerini destekler.

> Anahtar kelime listesi, örnek sorular ve sabit cevap metinleri kurum içi olarak elle yazılmıştır. 25–30 dakikalık blok önerisi Pomodoro uygulamasından esinlenir; bu süre için hakemli bir kaynak eklenmedi. Uyku düzeni önerisi için ayrıca kaynak eklenmedi.

### AI koç (Filiz Gelişim Koçu) istem kuralları ve kriz protokolü

OpenAI modeline öğrencinin gerçek profiliyle giden sistem istemi, oturum/limit kuralları ve kendine zarar ifadelerinde sabit güvenli yanıt.

**Nasıl:** Sistem istemi 10 kural içerir: sohbet dili (liste yok), kişisel anı uydurmama, yalnızca profil verisine dayanma, sistemle çelişmeme, kariyer eksenli kalma, sıcak/yargısız ton, kaynakları hedef bölüme göre çerçeveleme (en fazla 1–2), reşit olmayan güvenliği (112, ALO 183, teşhis koymama), haftalık görevlere dayanma, 2–4 cümle. Model gpt-4o-mini, temperature 0,7, en çok 500 token; oturum 20 mesajda kapanır, 2–3 cümlelik özet sonraki oturuma taşınır; günlük 30 mesaj (filiz_gunluk_mesaj_limiti). 23 kriz ifadesi geçerse model çağrılmadan sabit yanıt verilir.

**Dayanak:**

- [145] World Health Organization, 2023 — Yardım kaynaklarına doğru yönlendirme yapılmasını, yöntem ayrıntısı verilmemesini ve sansasyonel dilden kaçınılmasını önerir; sabit kriz yanıtının içeriği bu ilkelerden esinlenir (yönerge medya için yazılmıştır, sohbet botu için değil).
- [97] National Action Alliance for Suicide Prevention, t.y. — İntiharla ilgili mesajların güvenli, umut ve yardım arama odaklı olmasını öngörür; kriz ifadesinde modelin devre dışı bırakılıp önceden onaylı sabit yanıt verilmesini destekler.
- [138] UNICEF Innocenti, 2025 — Çocuklara yönelik yapay zekâ sistemlerinde güvenlik ve iyi oluşun önceliklendirilmesini ister; reşit olmayan güvenliği kuralı ve teşhis koymama ilkesini kurumsal düzeyde destekler.
- [65] Ji ve ark., 2023 — Dil modellerinin kaynakta olmayan bilgi üretebildiğini ve dayandırmanın bunu azaltmadaki rolünü özetler; 'yalnızca profil verisine dayan, anı uydurma' kurallarını destekler.

> 23 kriz ifadesi listesi, sabit yanıt metni, 20 mesajlık oturum, günlük 30 mesaj sınırı ve model parametreleri (gpt-4o-mini, temperature 0,7, 500 token) kurum içi tasarım kararıdır. Güvenli mesajlaşma yönergeleri medya ve kamu iletişimi için yazılmıştır; sohbet botuna esinlenme olarak uygulanmıştır. Anahtar kelime eşleşmesi dolaylı ifadeleri kaçırabilir; liste ruh sağlığı uzmanı ve okul rehberlik servisiyle gözden geçirilmeli, 112 ve okul rehber öğretmenine yönlendirme öne çıkarılmalıdır. ALO 183, Aile ve Sosyal Hizmetler Bakanlığı'nın 7/24 hizmet veren sosyal destek ve şiddetle mücadele hattıdır (aile.gov.tr SSS sayfasında doğrulandı); intihar krizine özel bir hat değildir, yanıt metninde bu ayrım doğru ifade edilmelidir.

### Filiz maskotu metinleri · _Kurum içi_

Hedef mesleğe göre kıyafet değiştiren ve ara ara motivasyon cümlesi söyleyen animasyonlu karakter.

**Nasıl:** Bölüm/meslek adı anahtar kelimelerine göre kıyafet kuralları (KIYAFET_KURALLARI, MESLEK_KURALLARI), 65 kıyafete özel mesaj grubu ve 10 genel mesaj elle yazılmıştır; görünüm profildeki cinsiyete göre seçilir, ses varsayılan kapalı.

**Dayanak:**

- [80] Lester ve ark., 1997 — Animasyonlu pedagojik ajanların öğrenen deneyimini olumlu etkileyebildiğini (persona etkisi) gösterir; maskot kullanımını genel olarak destekler.
- [48] Gottfredson, 1981 — Çocukların meslek seçeneklerini erken yaşta cinsiyet uygunluğu algısıyla daralttığını açıklar; mesleğe göre kıyafet ve cinsiyete göre görünüm seçiminde kalıp yargıyı pekiştirmemeye dikkat edilmesi gerektiğini gösterir (destekten çok uyarı).

> Kıyafet ve meslek eşleme kuralları, 65 kıyafete özel mesaj grubu ve 10 genel mesaj kurum içi tasarım kararıdır. Görünümün profildeki cinsiyete göre seçilmesi meslekî cinsiyet kalıp yargılarını pekiştirme riski taşır (Gottfredson, 1981); bu tercih akademik bir dayanağa değil ürün kararına dayanır ve gözden geçirilmelidir.

## Meslek bilgisi ve simülasyon

### Bölüm açıklamaları, bölüm detayı ve Keşfet

301 bölümün kısa açıklaması, detaylı tanıtımı (özet, dersler, iş alanları, meslekler, günlük işler, çalışma ortamı, beceriler, nasıl olunur) ve tüm bölümleri arama ekranı.

**Nasıl:** Kısa açıklamalar Bölüm_Listesi.xlsx'ten 301 bölüm adıyla birebir eşlenerek eklendi; detay JSON'u bolumler.detay alanında (içerik repoda değil). Keşfet her bölüm için en yüksek ağırlıklı 5 değişkeni ve varsa uyum yüzdesini gösterir; arama Türkçe İ/ı kuralıyla Python'da yapılır.

**Dayanak:**

- [147] Yükseköğretim Kurulu, t.y. — Lisans programlarının resmî tanıtım ve istatistik bilgilerinin kaynağıdır; bölüm açıklamalarının ve detaylarının doğrulanacağı birincil resmî kaynaktır.
- [136] Türkiye İş Kurumu, t.y. — Türkiye'ye özgü meslek tanımları ve meslek bilgi dosyalarını sunar; detaydaki meslekler, günlük işler ve çalışma ortamı alanlarını destekler.
- [93] Mesleki Yeterlilik Kurumu, t.y. — Mesleklerin görev ve yeterliliklerini resmî olarak tanımlar; 'beceriler' ve 'nasıl olunur' alanlarına dayanak olabilir.
- [38] European Commission, t.y. — Meslek ve beceri tanımlarının Avrupa standart sınıflamasıdır; beceri listelerinin standart terimlerle eşlenmesini destekler.

> Kısa açıklamalar Bölüm_Listesi.xlsx'ten, detay içeriği veritabanındaki bolumler.detay alanından gelir; içerik repoda olmadığından hangi kaynaktan ve nasıl üretildiği doğrulanamadı. Keşfet'te 5 değişken gösterilmesi kurum içi tasarım kararıdır. O*NET ve NCDA yönergeleri için künye eklenmedi.

### Meslek dili (jargon) sözlüğü

Her bölümün mesleğinde sık kullanılan terimlerin anlamı ve örnek cümlesi.

**Nasıl:** meslek_jargonu.json: 301 bölüm × ortalama 10 terim (terim, anlam, örnek) elle yazılmış varsayılan içerik; öncelik okula özel sürüm → genel sürüm (süper admin) → varsayılan.

**Dayanak:**

- [93] Mesleki Yeterlilik Kurumu, t.y. — Ulusal meslek standartları mesleklerin görev ve terminolojisini resmî olarak tanımlar; jargon terimlerinin doğrulanabileceği bir kaynaktır.
- [38] European Commission, t.y. — ESCO meslek ve beceri tanımları çok dilli standart terimler sunar; terim anlamlarının tutarlılığını desteklemek için kullanılabilir.

> 301 bölüm × ortalama 10 terim elle yazılmış varsayılan içeriktir; terimlerin MYK/ESCO ile tek tek doğrulandığına dair kayıt yoktur. Meslekî sosyalleşme için akademik kaynak eklenmedi; bileşen büyük ölçüde içerik/ürün kararıdır.

### Meslek simülasyonu karar anları

Mesleklerde gerçekçi iki durumda öğrencinin karar verip geri bildirim aldığı senaryolar.

**Nasıl:** Python'da 16 meslek (+9 eş ad) elle yazılmış, JSON'da 1.010 meslek adı için toplam 2.020 karar anı; her karar anı 3 seçenek, sonuç geri bildirimi ve 9 yaklaşım etiketinden biri (güvenliği önceleyen, analitik, iletişimci, ekip oyuncusu, yaratıcı, planlı, empatik, ilkeli, hızlı karar veren). 627 seçenek güvenlik/etik durumlarında 'önerilen' işaretli; diğerlerinde doğru/yanlış yok. Kaynak notu: iş tanımları, MYK standartları ve İSG ilkeleri esas alınmış kurgusal durumlar.

**Dayanak:**

- [111] Premack ve Wanous, 1985 — Gerçekçi iş önizlemelerinin beklentileri gerçekçileştirdiğini meta-analitik olarak gösterir; mesleğin zorlu durumlarını karar anı olarak sunmayı destekler.
- [108] Phillips, 1998 — Gerçekçi iş önizlemesinin başlangıç beklentileri ve ayrılma üzerindeki etkisini meta-analitik olarak gösterir; simülasyonun gerekçesini güçlendirir.
- [88] McDaniel ve ark., 2001 — Durumsal yargı testlerinin iş performansını yordadığını gösterir; üç seçenekli karar anı biçimi bu test türünden esinlenir, ancak sistemdeki senaryolar geçerliliği sınanmış bir test değildir.
- [62] İş Sağlığı ve Güvenliği Kanunu, Kanun No. 6331, 2012 — İşveren ve çalışan iş güvenliği yükümlülüklerini düzenler; güvenlik içeren karar anlarında 'önerilen' seçeneğin yasal dayanağıdır.
- [86] Maden İşyerlerinde İş Sağlığı ve Güvenliği Yönetmeliği, 2013 — Maden mühendisliği simülasyonundaki güvenlik kararlarının yönetmelik dayanağıdır.
- [146] World Health Organization, 2026 — Eczacılık/tıp simülasyonundaki akılcı antibiyotik kullanımı kararlarının bilimsel dayanağıdır.

> 2.020 karar anı ve 9 yaklaşım etiketi kurum içi olarak yazılmış kurgusal durumlardır; durumsal yargı testi olarak psikometrik geçerlik çalışması yapılmamıştır. Maden ve sağlık senaryoları için kaynakca.json'daki Maden İşyerlerinde İSG Yönetmeliği (2013) ve WHO antimikrobiyal direnç bilgi notu (2026) da ilgili kaynaklardır.

### 'Bir günümü yaşa' akışı

Bölümün mesleklerinden birini sabahtan akşama bir iş günü olarak yaşatan, sonunda keyif yüzdesi veren simülasyon.

**Nasıl:** Günlük işler saat dilimlerine (09:00, 10:30, 13:30, 15:00, 16:30, 17:30) yerleştirilir; tepki 😍 2, 🙂 1, 😕 0; keyif = Σtepki / (2 × iş sayısı) × 100. Yorum: ≥70 'meslek sahibiyle konuş / kampüs gezisi', ≥40 orta, <40 'diğer meslekleri dene'; öğrencinin ilk 5 güçlü yönü mesleğin gerekli becerileriyle yan yana gösterilir.

**Dayanak:**

- [111] Premack ve Wanous, 1985 — Gerçekçi iş önizlemesinin meslek beklentilerini gerçekçileştirdiğini gösterir; bir iş gününü baştan sona yaşatma fikrinin dayanağıdır.
- [108] Phillips, 1998 — Gerçekçi iş önizlemesinin olumlu sonuçlarını meta-analitik olarak gösterir; simülasyon akışını destekler.
- [58] Holland, 1997 — Kişi–çevre uyumunda ilgilerin merkezî rolünü açıklar; günlük işlere verilen keyif tepkisinin ilgiye dayalı bir keşif sinyali olarak kullanılmasını destekler.

> Saat dilimleri, tepki puanları (2/1/0), keyif formülü ve ≥70/≥40 eşikleri kurum içi tasarım kararıdır; geçerliği sınanmış bir ilgi ölçümü değildir, keşif amaçlı yorumlanmalıdır.

## Rehberlik ve erken uyarı

### Erken uyarı kuralları ve rehberlik görüşme kayıtları · _Kurum içi_

Rehber öğretmene dikkat gerektiren öğrencileri kural bazlı listeleyen panel ve görüşme/randevu/takip kayıtları.

**Nasıl:** 8 kural: hiç giriş yok (hesap ≥7 gün; <21 orta, ≥21 yüksek), uzak kaldı (son giriş ≥14 gün; ≥30 yüksek), test yarıda (son giriş ≥7 gün, orta), teste başlamadı (giriş var, hesap ≥14 gün, düşük), net düşüşü (son deneme önceki en çok 3 denemenin ortalamasından %15+ düşük, ortalama ≥5; %25+ yüksek), görevleri bıraktı (son 3 haftada 0, önceki 5 haftada ≥2 görev), tarama formunda destek ihtiyacı (son 120 gün), hedef yok (12. sınıf/mezun, düşük). Seviye puanı yüksek 3, orta 2, düşük 1; 'görüştüm, N gün gösterme' ertelemesi 1–120 gün (varsayılan 14). Görüşme: 4 tür, 8 konu, 3 durum; notlar öğrenciye gösterilmez.

**Dayanak:**

- [4] Balfanz ve ark., 2007 — Devamsızlık/katılım düşüşü gibi erken göstergelerle risk altındaki öğrencinin erken belirlenip müdahaleye yönlendirilmesi fikrini destekler; panelin platform-içi göstergeleri (giriş, görev, deneme) bu çalışmadaki okul göstergelerinin uyarlaması değil, esinlenmesidir.
- [1] Allensworth ve Easton, 2007 — Basit, izlenebilir göstergelerin (ders başarısı, devam) yol üstünde kalmayı yordadığını göstererek kural bazlı erken uyarı yaklaşımını destekler.
- [95] Millî Eğitim Bakanlığı Rehberlik ve Psikolojik Danışma Hi…, 2020 — Rehber öğretmenin öğrenci izleme, görüşme ve kayıt tutma rolünün mevzuat çerçevesini sağlar.

> Kural eşikleri (7/14/21/30 gün, %15/%25 net düşüşü, 120 gün, 1–120 gün erteleme) ve seviye puanları kurum içi tasarım kararıdır; akademik bir kesme noktasına dayanmaz. Erken uyarı yaklaşımının kendisi literatüre dayanır.

### Akran benzerliği

Rehber öğretmene bir öğrencinin profilce en benzer akranlarını gösterir (öğrenciye gösterilmez).

**Nasıl:** Son geçerli turdaki K1–K4 puanları (K5 hariç) okul havuzuna göre z-standardize edilir, kosinüs benzerliği alınır; gösterilen = 50 + 50·cos; en az 6 ortak özellik; ortak güçlü yön = iki öğrencide de ≥62, en fazla 3; belirgin fark ≥25 puan, en fazla 2.

**Dayanak:**

- [27] Cronbach ve Gleser, 1953 — Profil benzerliğinin ölçümünde düzey/şekil ayrımını ve standardizasyonun etkisini tartışır; z-standardizasyon sonrası kosinüs benzerliğinin (şekil benzerliği) kuramsal dayanağıdır.
- [90] McPherson ve ark., 2001 — Benzer bireylerin birbirine yöneldiğini (homofili) belgeler; benzer akranların rehberlik amaçlı gösterilmesinin hem faydasını hem de grup içi kapanma riskini bağlamlandırır.

> 50 + 50·cos gösterimi, en az 6 ortak özellik, ≥62 ortak güçlü yön ve ≥25 puan belirgin fark eşikleri kurum içi tasarım kararlarıdır; akademik bir kesme noktasına dayanmaz.

### Şube dağılımı önerisi ve aday öğrenci şube uyumu

Öğrencileri profillerine göre şubelere dengeli ya da benzerlerine göre gruplayan karar destek aracı ve yeni kayıt adayının hangi şubeye yakın olduğu.

**Nasıl:** 'Dengeli' modda profil tipi sayısı = max(2, min(2k, n/3, 8)) ile k-ortalamalar (tohum 7, 8 tekrar), tip içinde PC1 sırası, her şubeye tipten eşit dağıtım, kapasite ⌈n/k⌉ ve isteğe bağlı cinsiyet dengesi; 'benzer' modda eşit kapasiteli k-ortalamalar (merkeze en net yakın önce yerleşir). Şubeler arası fark = şube merkezlerinin okul ortalamasına uzaklığı. Aday uyumu: şube merkeziyle kosinüs, 'yakın akran' cos ≥0,3.

**Dayanak:**

- [85] MacQueen, 1967 — Profil tiplerinin belirlenmesinde kullanılan k-ortalamalar algoritmasının özgün kaynağıdır.
- [14] Bradley ve ark., 2000 — Küme büyüklüğü kısıtlı k-ortalamaları tanımlar; 'benzer' moddaki eşit kapasiteli kümelemenin dayanağıdır (sistemdeki açgözlü yerleştirme bunun basitleştirilmiş biçimidir).
- [106] Papenberg ve Klau, 2021 — Grupları birbirine benzer kılmak için anti-kümelemeyi tanımlar; 'dengeli' moddaki şubeler arası denk dağılım hedefini destekler (sistem tip-içi sıralı dağıtım kullanır, anti-kümeleme algoritmasının kendisini değil).
- [126] Steenbergen-Hu ve ark., 2016 — Yetenek gruplamasının etkilerine ilişkin ikinci düzey meta-analizleri sunar; benzer/dengeli şube oluşturma seçeneklerinin pedagojik sonuçlarının bağlamını verir.

> Profil tipi sayısı formülü max(2, min(2k, n/3, 8)), tohum 7 / 8 tekrar, PC1 sırası, kapasite ⌈n/k⌉, cinsiyet dengesi ve 'yakın akran' cos ≥0,3 eşiği kurum içi tasarım kararlarıdır. Araç karar destek amaçlıdır; profil temelli şube atamasının öğrenci başarısına etkisi bu sistem için sınanmamıştır.

### Eğitim koçları · _Kurum içi_

Dışarıdan anlaşmalı koçların okul bazında öğrenciye görünmesi ve görüşme talebi akışı.

**Nasıl:** Süper admin koçu okul okul atar (aktif / onay bekliyor / reddedildi); öğrenci yalnızca okulunda aktif koçları görür, iletişim bilgisini görmez; koç alanları öğrencinin hedef + Listem bölümlerinin üst alanlarıyla eşleşirse 'uygun' işaretlenip üste sıralanır.

**Dayanak:**

- [12] Bettinger ve Baker, 2014 — Bireysel öğrenci koçluğunun öğrenci sonuçlarına olumlu etkisini rastgele deneyle gösterir; ancak üniversite öğrencileri üzerindedir, platformdaki lise koç eşleştirmesi için yalnızca genel dayanaktır.
- [95] Millî Eğitim Bakanlığı Rehberlik ve Psikolojik Danışma Hi…, 2020 — Okul dışı koçluk hizmetinin okul rehberlik hizmetinin yerini almayıp onu tamamlaması gerektiği çerçevesine dayanak olur.

> Koç atama/onay akışı, iletişim bilgisinin gizlenmesi ve alan eşleşmesine göre 'uygun' sıralaması kurum içi ürün kararıdır; akademik bir kaynağa dayanmaz.

## Anket ve tarama formları

### Sınav kaygısı tarama formu

Sınav öncesi ve sırasında yaşanan kaygıyı yoklayan, tanı koymayan isimli tarama formu.

**Nasıl:** Filizyol için yazılmış 10 madde (1 ters: 'Sınav günü kendimi sakin ve hazır hissederim'), 1–5 Likert; yüksek puan = destek ihtiyacı; ortalama <2,5 düşük, 2,5–3,5 orta, >3,5 yüksek; 3 seviye geri bildirim metni. Geçerlik/güvenirlik çalışması yok (dosya notu).

**Dayanak:**

- [149] Zeidner, 1998 — Sınav kaygısının bilişsel (endişe) ve duyuşsal (bedensel tepki) bileşenlerini tanımlayarak madde içeriğinin kuramsal çerçevesini sağlar.
- [139] von der Embse ve Jester, 2018 — Sınav kaygısının yaygınlığını ve başarıyla olumsuz ilişkisini 30 yıllık meta-analizle göstererek okulda tarama yapılmasını destekler; form yerleşik ölçeklerden (ör. TAI) esinlenmiştir, uyarlaması değildir.
- [54] Hembree, 1988 — Sınav kaygısının performansla olumsuz ilişkisini ve tedaviyle azaltılabildiğini meta-analizle göstererek yüksek kaygıda destek yönlendirmesini destekler.
- [17] Cassady ve Johnson, 2002 — Bilişsel sınav kaygısının sınav başarısını düşürdüğünü göstererek endişe odaklı maddelerin dahil edilmesini destekler.

> Maddeler Filizyol için yazılmıştır; geçerlik/güvenirlik çalışması yoktur. 2,5 ve 3,5 eşikleri kurum içi tasarım kararıdır, normlu bir kesme puanına dayanmaz; form tanı koymaz.

### Çalışma alışkanlıkları formu

Planlama, tekrar, yanlış analizi, mola ve uyku gibi çalışma alışkanlıklarını yoklayan form.

**Nasıl:** 10 madde (1 ters: 'Çalışmayı genellikle son ana bırakırım'), 1–5 Likert; düşük puan = destek ihtiyacı; <2,8 desteğe ihtiyaç var, 2,8–3,8 gelişmekte, >3,8 güçlü.

**Dayanak:**

- [33] Dunlosky ve ark., 2013 — Pratik test ve dağıtılmış çalışmanın en etkili teknikler olduğunu göstererek tekrar ve yanlış analizi maddelerinin seçimini destekler.
- [19] Cepeda ve ark., 2006 — Aralıklı tekrarın yığılmış çalışmaya üstünlüğünü göstererek düzenli tekrar ve son ana bırakmama maddelerini destekler.
- [115] Roediger ve Karpicke, 2006 — Kendini test etmenin kalıcı öğrenmeyi artırdığını göstererek soru çözme/deneme ile çalışma maddesini destekler.
- [125] Steel, 2007 — Ertelemenin yaygın ve başarıyla olumsuz ilişkili bir öz-düzenleme sorunu olduğunu göstererek ters kodlu erteleme maddesini destekler.

> Maddeler bu kaynaklardan esinlenerek yazılmıştır, standart bir ölçeğin (ör. MSLQ) uyarlaması değildir. 2,8 ve 3,8 eşikleri kurum içi tasarım kararıdır.

### Okul iklimi ve aidiyet anketi

Okulda güvenlik, kabul, öğretmen beklentisi, zorbalık ve katılımı yoklayan anonim anket.

**Nasıl:** 8 Likert madde (1 ters: zorbalık/dışlanma) + 1 isteğe bağlı açık uçlu öneri sorusu; anonim; <2,8 zayıf, 2,8–3,8 orta, >3,8 güçlü (öğrenciye yalnızca teşekkür metni).

**Dayanak:**

- [47] Goodenow, 1993 — Okul aidiyetini kabul, saygı ve destek görme algısı olarak tanımlayarak kabul ve öğretmen beklentisi maddelerini destekler; anket PSSM'nin uyarlaması değildir.
- [132] Thapa ve ark., 2013 — Okul ikliminin güvenlik, ilişkiler, öğretme-öğrenme ve kurumsal çevre boyutlarını özetleyerek madde alanlarının seçimini destekler.
- [100] Olweus, 1993 — Akran zorbalığı ve dışlanmanın okul ortamının temel bir göstergesi olarak yoklanmasını destekler.

> 2,8 ve 3,8 eşikleri kurum içi tasarım kararıdır; geçerlik/güvenirlik çalışması yoktur.

### Kariyer kararlılığı formu

Bölüm/meslek seçimine ne kadar hazır hissedildiğini yoklayan form.

**Nasıl:** 8 madde (1 ters: 'Kararsız olduğum için kaygı duyuyorum'), 1–5 Likert; düşük puan = destek ihtiyacı; <2,8 kararsız, 2,8–3,8 keşfediyor, >3,8 kararlı.

**Dayanak:**

- [43] Gati ve ark., 1996 — Hazır olmama, bilgi eksikliği ve tutarsız bilgi gibi karar güçlüklerinin taksonomisiyle madde içeriğini destekler.
- [103] Osipow ve ark., 1976–1987 — Kararlılık ve kararsızlığı kısa öz-bildirim maddeleriyle ölçen yerleşik bir aracı örnekler; form bu ölçeğin uyarlaması değildir.
- [130] Taylor ve Betz, 1983 — Kariyer kararı öz-yeterliğinin kararsızlıkla ilişkisini göstererek seçime hazır hissetme maddelerini destekler.
- [128] Super, 1980 — Kariyer gelişiminin evrelerini (keşif dahil) tanımlayarak 'keşfediyor' ara seviyesinin adlandırılmasına kuramsal zemin sağlar.

> 2,8 ve 3,8 eşikleri ile seviye adları kurum içi tasarım kararıdır; normlu bir kesme puanına dayanmaz.

### Anket puanlama, anonimlik ve en az 5 kuralı

Okul anketleri ve hazır şablonların puanlanması, anonim yanıtların korunması ve küçük grup gizleme.

**Nasıl:** Puan = Likert maddelerin ortalaması (ters madde 6 − cevap), iki eşikle 3 seviye; 5 soru türü (Likert, tek, çoklu, 1–10 puan, açık). EN_AZ = 5: anket en az 5 kişiye gönderilir, anonim sonuçlar 5'ten az yanıtla gösterilmez, 5'ten küçük sınıflar 'Diğer sınıflar'da birleşir (o da <5 ise gizlenir), anonim yanıtta öğrenci kimliği ve şube tutulmaz, zaman damgası gün düzeyinde; yanıt gelmiş anketin soruları/anonimliği değiştirilemez. İsimli taramalarda destek gerektiren sonuç son 120 gün erken uyarıya düşer. Rehberlik memnuniyet anketi: 4 Likert + 1 açık, anonim, puanlamasız.

**Dayanak:**

- [129] Sweeney, 2002 — Yanıtların en az k kişilik gruplarda gösterilmesiyle yeniden tanımlamanın önlenmesi ilkesini sağlar; 5'ten az yanıtı gizleme ve küçük sınıfları birleştirme bu ilkeden esinlenir.
- [72] Kişisel Verilerin Korunması Kanunu, Kanun No. 6698, 2016 — Anonim yanıtta kimlik ve şube tutulmaması, zaman damgasının gün düzeyine indirilmesi gibi veri en aza indirme uygulamalarının yasal dayanağıdır.
- [82] Likert, 1932 — Maddelerin ortalaması alınarak tutum puanı elde edilmesi yöntemini destekler.
- [142] Weijters ve Baumgartner, 2012 — Ters maddelerin yanıt hatası doğurabildiğini göstererek ters kodlamanın (6 − cevap) dikkatli ve az sayıda kullanılmasını destekler.

> EN_AZ = 5 değeri yaygın küçük hücre gizleme pratiğinden esinlenen kurum içi tasarım kararıdır; belirli bir resmî eşiğe dayanmaz. 120 günlük erken uyarı penceresi de kurum içi karardır.

### Kulüp ilgi testi ve kulüp önerisi

Okul kulüplerini öneren 20 maddelik kısa ilgi testi ve hazır lise kulübü listesi (bölüm önerisini etkilemez).

**Nasıl:** 10 ilgi boyutu × 2 madde = 20 madde, 1–5 ('Hiç hoşlanmam' … 'Çok hoşlanırım'), maddeler karışık sırada; boyut puanı = (ortalama − 1) × 25. 30 hazır kulüp ilgi etiketleriyle elle tanımlı; kulüp uyumu = etiket puanlarının ağırlıklı ortalaması (ilk etiket 1,0, diğerleri 0,7); 'İlgilerinle örtüşüyor' ≥60.

**Dayanak:**

- [34] Eccles ve Barber, 1999 — Ders dışı etkinliklere katılımın olumlu gelişimsel sonuçlarını göstererek öğrencileri kulüplere yönlendirmeyi destekler.
- [58] Holland, 1997 — İlgi alanlarına göre etkinlik/ortam eşleştirme fikrini destekler; 10 ilgi boyutu RIASEC'in uyarlaması değildir, esinlenmedir.
- [94] Millî Eğitim Bakanlığı Eğitim Kurumları Sosyal Etkinlikle…, 2017 — Okullarda öğrenci kulüplerinin kurulması ve öğrencinin isteğine göre kulübe yönlendirilmesinin mevzuat çerçevesini sağlar.

> 20 madde, (ortalama − 1) × 25 dönüşümü, 30 kulübün ilgi etiketleri, 1,0/0,7 ağırlıkları ve ≥60 eşiği kurum içi tasarım kararıdır; geçerlik çalışması yoktur.

## Akademik takip

### YKS sınav yapısı ve net hesabı

TYT/AYT/YDT testleri, soru sayıları, puan türü–test eşleşmesi ve net formülü.

**Nasıl:** 16 test: TYT Türkçe 40, Sosyal 20, Temel Matematik 40, Fen 20; AYT Matematik 40, Fizik 14, Kimya 13, Biyoloji 13, TDE 24, Tarih-1 10, Coğrafya-1 6, Tarih-2 11, Coğrafya-2 11, Felsefe Grubu 12, Din 6; YDT 80. Puan türleri SAY, EA, SÖZ, DİL, TYT; net = doğru − yanlış/4; alan adları YÖK Atlas Net Sihirbazı ile aynı.

**Dayanak:**

- [99] Ölçme, Seçme ve Yerleştirme Merkezi Başkanlığı, 2026 — Net = doğru − yanlış/4 hesabını ve TYT, SAY, EA, SÖZ, DİL puan türlerini doğrudan destekler.
- [147] Yükseköğretim Kurulu, t.y. — Alan adlarının YÖK Atlas Net Sihirbazı ile aynı tutulmasının kaynağıdır.

> Test ve soru sayıları ÖSYM yapısından alınmıştır; her yıl kılavuzla yeniden kontrol edilmelidir (2026-YKS kılavuz PDF'i doğrudan açılamadı).

### Konu takibi listeleri

Ders ders konu listesi ve öğrencinin her konu için durumu (başlamadı/çalışıyorum/bitti/tekrar).

**Nasıl:** 19 ders için elle yazılmış başlangıç konu listeleri ('ÖSYM/MEB müfredatındaki yaygın başlıklar'); 0039 ile veritabanına taşındı, süper admin genel listeyi, okul kendi konularını ekleyip genel konuları gizleyebilir.

**Dayanak:**

- [99] Ölçme, Seçme ve Yerleştirme Merkezi Başkanlığı, 2026 — Konu listelerinin YKS test kapsamıyla sınırlandırılmasına genel çerçeve sağlar.

> Konu listeleri ÖSYM/MEB müfredatındaki yaygın başlıklardan elle derlenmiştir; resmî bir konu listesinin birebir aktarımı değildir. MEB öğretim programı belgeleri ders bazında dağınık olduğundan tek bir künye eklenmedi. Durum etiketleri ürün kararıdır.

### Net takibi, hedef program kıyası ve okul denemeleri

Deneme netlerinin izlenmesi, hedef bölüm programına geçen yıl yerleşen son öğrencinin netleriyle ders ders kıyas ve okulun toplu deneme yüklemesi.

**Nasıl:** Kıyas: son 3 denemenin ortalaması (KIYAS_DENEME_SAYISI) − son yerleşen netleri; en büyük 3 açık gösterilir; veriler YÖK Atlas'tan 7 gün önbellekle (en çok 1.500 satır); 'taban puanla yerleşen tek kişiye aittir, OBP etkisi içerir' uyarısı. Okul denemeleri Excel şablonla yüklenir, öğrencinin Net Takibi'ne 'Okul denemesi' olarak düşer, okul/şube/ders ortalamaları ve sıra hesaplanır.

**Dayanak:**

- [147] Yükseköğretim Kurulu, t.y. — Hedef programa son yerleşen öğrencinin netleri ve taban puan/başarı sırası verilerinin kaynağıdır.
- [99] Ölçme, Seçme ve Yerleştirme Merkezi Başkanlığı, 2026 — Yerleştirme puanının ham puanlar ve OBP katkısıyla oluştuğunu belirterek 'OBP etkisi içerir' uyarısını destekler.
- [13] Black ve Wiliam, 1998 — Düzenli deneme sonuçlarının hedefle kıyaslanarak geri bildirime dönüştürülmesini biçimlendirici değerlendirme açısından destekler.
- [83] Locke ve Latham, 2002 — Somut ve ölçülebilir hedefle mevcut durum arasındaki farkın gösterilmesinin performansı yönlendirdiğini destekler.

> Son 3 deneme ortalaması, en büyük 3 açık, 7 gün önbellek ve 1.500 satır sınırı kurum içi tasarım kararıdır.

### Çalışma programı ve soru takibi · _Kurum içi_

Haftalık ders programı, günlük çalışma süresi ve çözülen soru kaydı.

**Nasıl:** En çok 80 programlı blok; özet: bu hafta plan uyumu = gerçekleşen dk / planlanan dk × 100, 6 haftalık seri grafik, son 28 günde ders bazında isabet = doğru / (doğru + yanlış) × 100 (en az 10 işaretli soruysa), art arda kayıt girilen gün serisi.

**Dayanak:**

- [152] Zimmerman, 2002 — Planlama, öz-izleme ve öz-değerlendirme döngüsüyle plan–gerçekleşen kıyası ve kayıt serisini destekler.
- [19] Cepeda ve ark., 2006 — Çalışmanın haftaya yayılmasını ve düzenli kayıt alışkanlığını destekler.
- [37] Ericsson ve ark., 1993 — Ders bazında isabet oranı gibi geri bildirimle yapılan bilinçli pratiğin önemini destekler; sistem bilinçli pratiği ölçmez, yalnızca esinlenir.

> 80 blok sınırı, 6 haftalık seri, 28 gün penceresi ve en az 10 soru koşulu kurum içi tasarım kararıdır.

### Kütüphanem ve takvim · _Kurum içi_

Öğrencinin okuduğu/izlediği/katıldığı şeylerin günlüğü ve genel–okul–kişisel–koç randevusu takvimi.

**Nasıl:** Kütüphane kategorileri: kitap, film/dizi/belgesel, kurs/sertifika, etkinlik/proje/yarışma; okul yetkilisi okur. Takvim kaynakları: genel (süper admin; YKS, tercih dönemi), okul (sınıf düzeyine göre), kişisel hatırlatma, eğitim koçu randevuları (otomatik); rehberlik randevusu notsuz görünür.

**Dayanak:**

- [99] Ölçme, Seçme ve Yerleştirme Merkezi Başkanlığı, 2026 — Genel takvimdeki YKS ve tercih dönemi tarihlerinin resmî kaynağı ÖSYM duyurularıdır.

> Kütüphane kategorileri ve takvim kaynakları kurum içi ürün kararıdır; akademik bir kaynağa dayanmaz.

## Tercih ve mezun

### Tercih listesi ve risk sınıfları · _Kurum içi_

12. sınıf ve mezunların tercih listesi hazırlaması, her tercihin güvenli/dengeli/riskli işaretlenmesi ve rehber onayı.

**Nasıl:** oran = öğrencinin başarı sırası / programın geçen yıl taban sırası: ≤0,85 güvenli, ≤1,10 dengeli, >1,10 riskli (taban sırasını öğrenci YÖK Atlas'tan yazar). En çok 24 tercih; 4 tür (devlet, vakıf, KKTC, yurt dışı), 7 burs seçeneği, 5 puan türü. Uyarılar: hiç güvenli yok; ilk 3 hep güvenli ve riskli yok; güvenli tercih riskli olanın üstünde; sıralama girilmemiş; taban sırası eksik; listedekilerin hiçbiri önerilerde değil. Durumlar: hazırlanıyor, incelemede, onaylandı, düzeltme istendi.

**Dayanak:**

- [147] Yükseköğretim Kurulu, t.y. — Programların geçen yıl taban başarı sırası verisinin kaynağıdır.
- [5] Balinski ve Sönmez, 1999 — Türkiye'deki merkezi sınavla öğrenci yerleştirmesini analiz ederek tercih sırasının sonucu nasıl belirlediğini ve dürüst sıralamanın önemini destekler.
- [40] Gale ve Shapley, 1962 — Kabul edilen yerleştirme mantığının (ertelenmiş kabul) kuramsal temelini sağlayarak listeye güvenli seçenek koymanın gerekçesini destekler.

> 0,85 ve 1,10 oran eşikleri, uyarı kuralları ve onay durumları kurum içi tasarım kararıdır; akademik bir kesme noktasına dayanmaz. 24 tercih sınırı ÖSYM kuralıdır ancak 2026 tercih kılavuzu ayrıca doğrulanmadı.

### Mezun takibi · _Kurum içi_

Mezunların yerleştiği bölümler ve bunun hedefle ve Filizyol önerileriyle uyumu.

**Nasıl:** Durumlar: yerleşti, yerleşemedi, tekrar hazırlanıyor, yurt dışında, çalışıyor, diğer; yıl bazında kayıt, yerleşme, hedefle aynı bölüme yerleşme ve öneri listesinin ilk 10'unda olma oranları; öğrenci 'Sonucumu bildir' ile ya da okul elle girer.

**Dayanak:**

- [122] Schomburg, 2016 — Mezunların sonraki durumlarının yıl bazında izlenmesi (mezun izleme) yöntemini destekler.
- [143] Whiston ve ark., 1998 — Kariyer müdahalelerinin etkisinin sonuç verisiyle değerlendirilmesi gerektiğini destekler; hedef/öneri uyum oranları bu amaçla tutulur.

> Durum kategorileri ve 'öneri listesinin ilk 10'u' ölçütü kurum içi tasarım kararıdır; bu oranlar öneri sisteminin geçerliğini tek başına kanıtlamaz (seçim ve yanıt yanlılığı).

### YÖK Atlas verisi

Bölümün üniversite/program bilgileri (kontenjan, taban puan, başarı sırası) ve son yerleşen netleri.

**Nasıl:** yokatlas-py kütüphanesiyle YÖK Atlas tercih kılavuzu JSON uç noktalarından (resmî/belgelenmiş API değil) çekilir; bölüm başına 7 gün önbellek, en çok 600 program, hata durumunda son başarılı veri; bölüm adına göre program grubu bulunur, gerektiğinde elle program grupları tanımlanır; yokatlas_aktif = false ile kapatılabilir.

**Dayanak:**

- [147] Yükseköğretim Kurulu, t.y. — Kontenjan, taban puan, başarı sırası ve son yerleşen netleri verisinin resmî kaynağıdır.

> Veri yokatlas-py ile YÖK Atlas'ın resmî/belgelenmiş olmayan JSON uç noktalarından çekilir; kullanım koşulları ayrıca doğrulanmadı. 7 gün önbellek ve 600 program sınırı kurum içi kararlardır.

## Okul yönetimi ve raporlar

### Öğrenci, veli, yönetici ve sınıf öğretmeni PDF raporları (SWOT dahil)

Bir öğrencinin sonuçlarını dört farklı kitleye göre dili ve içeriği değişen PDF olarak sunar.

**Nasıl:** Puanlar yeniden hesaplanmaz, ekrandakiyle aynı kaynaklar kullanılır (güçlü ≥62 en çok 6, gelişim <45 en çok 5). Kurallı SWOT: S ilk 5 güçlü yön; W hedef odakları + gelişim alanları (en çok 5); O ilk 3 bölüm, öne çıkan 2 alan, tekrar eden güçlü yönler, K5 alanı, Listem; T hedef ilk 10'da değil, belirgin açıklar, hiç adım yok, düşük güven, son 4 haftada görev yok vb. Veli raporunda 6 öneri ve 4 'öğretmene sorulacak soru'; her sayfada 'Kişisel veri içerir' altbilgisi; net bölümünde 'hedef netler tek kişiye aittir, OBP etkiler' notu.

**Dayanak:**

- [150] Zenisky ve Hambleton, 2012 — Rapor dilinin ve içeriğinin hedef kitleye (öğrenci, veli, yönetici, öğretmen) göre uyarlanması ve puanların ekranla tutarlı sunulması, etkili puan raporu tasarım ilkeleriyle desteklenir.
- [2] American Educational Research Association, American Psych…, 2014 — Puan raporlarının farklı kullanıcılar için anlaşılır yorum bilgisi ve sınırlılık notları (ör. 'hedef netler tek kişiye aittir') içermesi gerekliliği Standartların puan raporlama bölümüne dayanır.
- [36] Epstein, 1995 — Veli raporundaki öneriler ve 'öğretmene sorulacak sorular', Epstein'ın okul-aile iletişimi ve evde öğrenmeyi destekleme katılım türlerinden esinlenir; birebir uyarlama değildir.
- [53] Helms ve Nixon, 2010 — SWOT çerçevesinin kullanımı genel SWOT literatürüne dayanır; ancak kurallı kişisel SWOT'a eşleme (hangi verinin S/W/O/T'ye gittiği) bu kaynakta yoktur.

> Güçlü (≥62, en çok 6) ve gelişim (<45, en çok 5) eşikleri, SWOT madde eşleme kuralları ve 6 öneri/4 soru sayıları kurum içi tasarım kararıdır; akademik bir kesme noktasına dayanmaz. 'Kişisel veri içerir' altbilgisi KVKK'nın genel veri güvenliği yükümlülüğüyle uyumlu bir ürün kararıdır.

### Okul, sınıf ve şube raporları; okul karşılaştırması · _Kurum içi_

Okulun genel durumu, sınıf/şube özetleri (Excel/PDF) ve çok okullu kurumlar için okul karşılaştırması.

**Nasıl:** Okul raporu: katılım, 1. öneriye göre alan dağılımı (ilk 8), katman ortalamaları (şube raporunda okul ortalamasıyla), ortak en güçlü/en zayıf 6 özellik, geçersiz tur sayısı, öğrenci listesi ve son TYT/AYT netleri. Karşılaştırma 9 metrik: öğrenci, giriş yapan %, son 30 günde aktif %, testi tamamlayan %, hedef seçen %, ort. son TYT neti, 90 günde rehberlik görüşmesi, yüksek uyarılı öğrenci, son yıl yerleşme %. Kodda küçük grup gizleme eşiği yalnızca anketlerde var; okul/şube raporlarında yok.

**Dayanak:**

- [129] Sweeney, 2002 — Küçük grupların kimlik açığa çıkarma riskine karşı asgari grup büyüklüğü fikrini destekler; bu ilke kodda yalnızca anketlerde uygulanıyor, okul/şube raporlarında uygulanmıyor.
- [124] Seastrom, 2010 — Toplulaştırılmış eğitim verisi raporlarında küçük hücre gizleme (suppression) uygulamalarını tanımlar; okul/şube raporlarında bu tedbirin eksik olduğunu değerlendirmek için ölçüt sağlar.

> Okul karşılaştırmasındaki 9 metrik, ilk 8/ilk 6 sınırları ve 30/90 günlük pencereler kurum içi tasarım kararıdır; belirli bir okul performans göstergesi çerçevesine dayanmaz. Kaynaklar küçük hücre gizlemeyi önerir; mevcut kod okul/şube raporlarında gizleme yapmaz (bilinen boşluk).

### Paketler, modüller ve bildirimler · _Kurum içi_

Okulun hangi modülleri kullanacağını belirleyen paket yapısı ve uygulama içi/e-posta bildirimleri.

**Nasıl:** 19 modül; Temel (takvim), Gelişim (takvim, koçluk, kütüphane, kulüpler, Filiz), Tam (tüm modüller, filiz_ai yalnız Tam'da); etkin = paket ∪ ekle − çıkar; bağımlılık okul_denemeleri→net_takibi, filiz_ai→filiz; okulsuz öğrenci tüm modülleri görür. Bildirim e-postası günlük 300 sınırı (Gmail ~500), kişi e-postayı kapatabilir.

**Dayanak:** Akademik dayanak yok.

> Paket/modül yapısı, bağımlılıklar ve günlük 300 e-posta sınırı ürün ve işletim kararlarıdır; akademik dayanak gerektirmez ve aranmamıştır. Gmail ~500 sınırı sağlayıcı kuralıdır, akademik kaynak değildir.

### Sistem Hakkında ve SSS metinleri · _Kurum içi_

Öğrenciye, okul yetkilisine ve admine sistemi anlatan sayfalar ve sıkça sorulan sorular.

**Nasıl:** Öğrenci ve okul yetkilisi için adım adım anlatım ve sıkça sorulan sorular; süper admin için 10 bölümlük teknik anlatım (pipeline, uyum hesaplama yöntemleri, soru tipleri, geçerlik eşikleri, güvenlik). Kaynakça sayfası bu dosyadaki bileşen ve kaynakları gösterir.

**Dayanak:**

- [57] High-Level Expert Group on Artificial Intelligence, 2019 — Algoritmik sistemin kullanıcılara yetenekleri ve sınırlarıyla anlatılması (ör. 'sonuçlar karar destek amaçlıdır', '%85 uyum başarı tahmini değildir') güvenilir YZ şeffaflık gerekliliğiyle desteklenir.
- [74] Kizilcec, 2016 — Algoritmik çıktının nasıl üretildiğine dair uygun düzeyde açıklama vermenin kullanıcı güvenini etkilediğini gösterir; SSS ve sistem hakkında metinlerinin gerekçesini destekler.
- [2] American Educational Research Association, American Psych…, 2014 — Test kullanıcılarına puanların amacı, yorumu ve sınırlılıkları hakkında doğru bilgi verilmesi ilkesini destekler; yanlış bilgilendirme bu ilkeye aykırıdır.

> Kısmi dayanak: şeffaflık ilkesi kaynaklara dayanır, sayfa içerikleri (adım/SSS sayıları) kurum içi karardır. Bu tutarsızlık şeffaflık ilkesiyle çelişir ve metin düzeltilmelidir.

### Test hesapları ve senaryolu sentetik ilerleme · _Kurum içi_

Deneme/tanıtım için açılan hesaplarda öğrencinin yerine soruları gerçek akışla cevaplayan senaryo üreticisi.

**Nasıl:** Cevaplar bir 'eğilim' vektörüne göre seçilir: her şık puanlama kuralıyla değerlendirilip hedef profile en yakın olan (biraz rastgelelikle) seçilir; 'bölüme göre' eğilimde hedef profil bölümün özellik beklentileridir; 2 adımlı doğrulama istenmez, süreli giriş bağlantısı kullanılır.

**Dayanak:**

- [96] Morris ve ark., 2019 — Bilinen bir 'gerçek' profilden yapay veri üretip algoritmanın çıktısını kontrol etme yaklaşımı, istatistiksel yöntemlerin simülasyonla değerlendirilmesi ilkeleriyle uyumludur; senaryo üreticisi biçimsel bir simülasyon çalışması değildir, esinlenmedir.

> Senaryo üreticisi asıl olarak tanıtım/deneme amaçlı bir ürün özelliğidir; eğilim vektörü, rastgelelik miktarı ve 'bölüme göre' hedef profil kurum içi tasarım kararıdır. Test hesaplarında 2 adımlı doğrulamanın atlanması ve süreli giriş bağlantısı güvenlik açısından ürün kararıdır; akademik dayanağı yoktur.

## Güvenlik ve veri koruma

### KVKK aydınlatma metni ve onay maddeleri

Öğrenciye gösterilen kişisel veri aydınlatma metni ve girişte istenen rıza/beyan maddeleri.

**Nasıl:** Şablon metin (veri sorumlusu, adres, e-posta köşeli parantezli yer tutucu; hukukçu kontrolü notu), sürüm 2026-10-v2 (değişince herkesten yeniden onay). 7 bölüm: işlenen veriler, amaçlar, hukuki sebepler (md. 5/2-c, 5/2-f, açık rıza), aktarım (yurt dışı bulut ve OpenAI), toplama, saklama (kamera fotoğrafı en geç 6 ay), md. 11 hakları; 18 yaş altı veli bilgisi. 6 onay maddesi, 4'ü zorunlu (aydınlatma, analiz açık rızası, yurt dışı aktarım, veli beyanı), 2'si isteğe bağlı (rehberle paylaşım, kamera). 'rehber_paylasim' rızası kodda başka bir yerde kontrol edilmiyor.

**Dayanak:**

- [72] Kişisel Verilerin Korunması Kanunu, Kanun No. 6698, 2016 — Aydınlatma yükümlülüğü (md. 10), hukuki sebepler (md. 5/2-c, 5/2-f, açık rıza), yurt dışına aktarım (md. 9), özel nitelikli veri (md. 6) ve ilgili kişi hakları (md. 11, otomatik analiz sonucuna itiraz dahil) metnin yasal dayanağıdır.
- [3] Aydınlatma Yükümlülüğünün Yerine Getirilmesinde Uyulacak …, 2018 — Aydınlatma metninde bulunması gereken asgari unsurlar (veri sorumlusu kimliği, amaç, aktarım, toplama yöntemi, hukuki sebep, haklar) ve açık rızadan ayrı sunulma kuralını belirler.
- [69] Kişisel Verileri Koruma Kurulu, 2026 — Açık rıza metninin aydınlatma metninden ayrı düzenlenmesi ve ayrı beyan alınması gerektiğini söyler; 6 onay maddesinin aydınlatma teyidinden ayrı tutulmasını doğrudan destekler.
- [21] Ceza Muhakemesi Kanunu ile Bazı Kanunlarda Değişiklik Yap…, 2024 — KVKK md. 9'u değiştirerek yurt dışına aktarımı yeterlilik kararı/uygun güvence/arızi aktarım düzenine bağlamıştır; yurt dışı bulut ve OpenAI aktarımının yalnızca açık rızaya dayandırılmasının yeniden değerlendirilmesi gerektiğini gösterir.

> Kısmi dayanak: metnin yapısı mevzuata dayanır; sürümleme (2026-10-v2), 6 aylık fotoğraf saklama ifadesi ve maddelerin zorunlu/isteğe bağlı ayrımı kurum içi karardır. Metin yer tutuculu şablondur ve hukukçu kontrolü gerekir. 7499 sonrası yurt dışı aktarımda açık rıza yalnızca arızi aktarım için geçerli bir sebeptir; sürekli bulut aktarımı için standart sözleşme vb. güvence gerekebilir. 'rehber_paylasim' rızasının kodda kontrol edilmemesi açık rıza ilkesine aykırı bir boşluktur. Kodda kamera saklama 180 gün iken metin 'en geç 6 ay' diyor; tutarlı olmalıdır. GDPR md. 22 karşılaştırma için ilgili olsa da sistem Türkiye'de işletildiğinden ana dayanak KVKK'dır.

### Hesap güvenliği

Şifre, iki adımlı doğrulama, şifre sıfırlama, davet ve güvenilir cihaz kuralları.

**Nasıl:** bcrypt şifre özeti, JWT erişim+yenileme; şifre en az 8 karakter; e-posta kodu 10 dk geçerli, en çok 5 deneme, 60 sn yeniden gönderim beklemesi; sıfırlama bağlantısı 1 saat, saatte en çok 3; davet 3 gün; kod/token/cihaz tokenleri yalnızca SHA-256 özetiyle saklanır; 'şifremi unuttum' hep aynı cevabı verir.

**Dayanak:**

- [131] Temoshok ve ark., 2025 — Şifre için asgari uzunluk, bellek-sert/tuzlu özetle saklama, deneme sınırlama ve kısa ömürlü tek kullanımlık kod gibi kurallar NIST dijital kimlik yönergeleriyle desteklenir; e-posta OTP'nin NIST'te kısıtlı bir doğrulayıcı olduğu ayrıca not edilmelidir.
- [104] OWASP Foundation, 2025 — Kimlik doğrulama, oturum ve token yönetimi (JWT erişim/yenileme, token'ların özetle saklanması) için doğrulanabilir güvenlik gereksinimleri sağlar.
- [105] OWASP Foundation, t.y. — 'Şifremi unuttum'un hesap varlığından bağımsız aynı yanıtı vermesi, sıfırlama bağlantısının tek kullanımlık ve süreli olması ve hız sınırlaması önerilerini doğrudan destekler.
- [70] Kişisel Verileri Koruma Kurumu, 2018 — Şifreleme, kimlik doğrulama, erişim yetkilerinin gerekli ölçüde verilmesi ve işlem kayıtlarının tutulması gibi teknik tedbirler için KVKK'nın resmî rehberidir.

> Kısmi dayanak: ilkeler kaynaklara dayanır; 10 dk kod süresi, 5 deneme, 60 sn bekleme, 1 saat sıfırlama, saatte 3 istek ve 3 günlük davet süreleri kurum içi tasarım kararıdır (kaynaklar 'uygun süre' der, bu sayıları vermez).

### Değerlendirme sırasında izleme ve kamera

Tam ekran zorunluluğu, sekme/odak/ikinci ekran/ekran görüntüsü/kopyalama takibi ve rızaya bağlı kamera fotoğrafı.

**Nasıl:** İhlaller öğrenciye anında gösterilir ve güven puanına cezaya göre yansır; kamera izni verildiyse her 4 soruda bir fotoğraf (FOTOGRAF_ARALIGI_SORU); başlamadan 'ONAYLIYORUM' yazılı onay; reddetmek cezasız ve raporda 'kamerasız' görünür; 180 günden eski fotoğraflar uygulama her uyandığında silinir; admin turları ve fotoğrafları Güvenlik/Tutarlılık ekranında inceler.

**Dayanak:**

- [24] Coghlan ve ark., 2021 — Çevrim içi sınav gözetiminin mahremiyet, özerklik ve orantılılık açısından etik sorunlarını tartışır; kameranın isteğe bağlı ve cezasız reddedilebilir olmasını destekler.
- [144] Woldeab ve Brothen, 2019 — Çevrim içi gözetimli sınavlarda yüksek sınav kaygısı olan öğrencilerin daha düşük puan aldığını bulur; gözetimin kaygı etkisinin dikkate alınması gerektiğini destekler.
- [71] Kişisel Verileri Koruma Kurumu, 2021 — Yüz fotoğrafının ancak kimlik tespiti/doğrulaması için özel teknik işlemeye tabi tutulduğunda biyometrik (özel nitelikli) veri sayılacağını açıklar; kamera fotoğraflarının hukuki niteliğini belirlemeye yardım eder.
- [72] Kişisel Verilerin Korunması Kanunu, Kanun No. 6698, 2016 — Açık rıza, özel nitelikli veri (md. 6) ve verinin amaç için gerekli süre kadar saklanması (md. 4) ilkeleri kamera rızası ve 180 günlük silme kuralının yasal dayanağıdır.

> Kısmi dayanak: rıza, isteğe bağlılık ve saklama sınırlaması ilkeleri kaynaklara dayanır; her 4 soruda bir fotoğraf, 180 gün saklama ve ihlal ceza puanları kurum içi tasarım kararıdır. Fotoğraflar yüz tanıma ile işlenmediği sürece biyometrik veri sayılmayabilir; bu ayrım hukukçu tarafından teyit edilmelidir.

### Erişim kısıtları, gizlilik kuralları ve denetim kaydı

Kimin hangi veriyi görebileceğine dair yapısal kurallar ve kritik işlemlerin kaydı.

**Nasıl:** Öğrenci API şemalarında yontem_skorlari, kendall_w, agirlikli_varyans, etkin_meslek_sayisi alanları tanımlı değil; ham cevap analizi yalnızca süper admin; akran/şube sonuçları öğrenciye gösterilmez; rehberlik notları öğrenciye gösterilmez; koç iletişim bilgisi öğrenciden gizli; durum/rol değişikliği, pipeline onayı, cevap analizi görüntüleme gibi işlemler audit log'a yazılır; test hesapları erken uyarı listesinden ve okul karşılaştırmasından hariç tutulur.

**Dayanak:**

- [119] Saltzer ve Schroeder, 1975 — En az ayrıcalık ve varsayılan olarak reddetme (fail-safe defaults) ilkeleri, öğrenci şemalarında iç alanların hiç tanımlanmaması ve ham cevap analizinin yalnızca süper admine açılmasını destekler.
- [120] Sandhu ve ark., 1996 — Rol tabanlı erişim denetimi modeli, öğrenci/öğretmen/okul yetkilisi/süper admin rollerine göre veri görünürlüğü kurallarının kuramsal temelidir.
- [18] Cavoukian, 2011 — Gizliliğin varsayılan ayar olarak tasarıma gömülmesi ilkesi, hassas alanların API düzeyinde yapısal olarak dışlanmasını destekler.
- [70] Kişisel Verileri Koruma Kurumu, 2018 — Erişim yetki matrisi oluşturulması ve kullanıcı işlem kayıtlarının (log) düzenli tutulması önerileri audit log uygulamasını destekler.
- [39] Family Educational Rights and Privacy Act of 1974, 20 U.S…, 1974 — Eğitim kayıtlarına erişimin sınırlanması ilkesi için karşılaştırmalı bir örnektir; Türkiye'de bağlayıcı değildir, 'FERPA benzeri ilke' olarak esinlenme düzeyinde kullanılır.

> Kısmi dayanak: ilkeler kaynaklara dayanır; hangi alanların hangi role gizleneceği ve hangi işlemlerin audit log'a yazılacağı kurum içi tasarım kararıdır. Test hesaplarının erken uyarı ve okul karşılaştırmasından hariç tutulması veri kalitesi kararıdır.

## Tüm kaynaklar (APA 7)

1. Allensworth, E. M., & Easton, J. Q. (2007). What matters for staying on-track and graduating in Chicago public high schools: A close look at course grades, failures, and attendance in the freshman year. Consortium on Chicago School Research at the University of Chicago. <https://consortium.uchicago.edu/sites/default/files/2018-10/07%20What%20Matters%20Final.pdf>
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
2. American Educational Research Association, American Psychological Association, & National Council on Measurement in Education. (2014). Standards for educational and psychological testing. American Educational Research Association. <https://www.testingstandards.net/>
   - Doğrulama: AERA resmi sayfası (aera.net/Standards14): 2014 baskısı, üç kurum, ISBN 978-0-935302-35-6; Frontiers in Education (2019) kaynakçası: Washington, DC, AERA
3. Aydınlatma Yükümlülüğünün Yerine Getirilmesinde Uyulacak Usul ve Esaslar Hakkında Tebliğ. (2018, 10 Mart). Resmî Gazete (Sayı: 30356). <https://www.muhasebenews.com/?p=56110>
   - Doğrulama: muhasebenews.com: ana Tebliğ RG 10.03.2018/30356 (değişiklik RG 28.04.2019/30758).
4. Balfanz, R., Herzog, L., & Mac Iver, D. J. (2007). Preventing student disengagement and keeping students on the graduation path in urban middle-grades schools: Early identification and effective interventions. Educational Psychologist, 42(4), 223–235. https://doi.org/10.1080/00461520701621079
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
5. Balinski, M., & Sönmez, T. (1999). A tale of two mechanisms: Student placement. Journal of Economic Theory, 84(1), 73–94. https://doi.org/10.1006/jeth.1998.2469 <https://ideas.repec.org/a/eee/jetheo/v84y1999i1p73-94.html>
   - Doğrulama: RePEc/IDEAS kaydı (cilt 84, sayı 1, s. 73–94) ve SUFE akademik bülten kaydı (DOI)
6. Bandura, A. (1977). Social learning theory. Prentice Hall.
   - Doğrulama: CiNii Books kaydı (yazar, yıl, yayınevi)
7. Bandura, A., & Schunk, D. H. (1981). Cultivating competence, self-efficacy, and intrinsic interest through proximal self-motivation. Journal of Personality and Social Psychology, 41(3), 586–598.
   - Doğrulama: Makalenin PDF'i başlık sayfası (cilt 41, sayı 3, s. 586–598); DOI birincil kaynakta görülmediği için yazılmadı
8. Barnett, A. G., van der Pols, J. C., & Dobson, A. J. (2005). Regression to the mean: What it is and how to deal with it. International Journal of Epidemiology, 34(1), 215–220. https://doi.org/10.1093/ije/dyh299
   - Doğrulama: Ovid makale sayfası (yazarlar, cilt, sayı, sayfa) ve BibBase kaydı (DOI)
9. Barrick, M. R., & Mount, M. K. (1991). The Big Five personality dimensions and job performance: A meta-analysis. Personnel Psychology, 44(1), 1–26. https://doi.org/10.1111/j.1744-6570.1991.tb00688.x
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
10. Bateman, T. S., & Crant, J. M. (1993). The proactive component of organizational behavior: A measure and correlates. Journal of Organizational Behavior, 14(2), 103–118. https://doi.org/10.1002/job.4030140202
   - Doğrulama: Wikipedia 'Proactivity' kaynakçası (yazarlar, cilt/sayı, sayfa, DOI); web aramasında künye tutarlı
11. Behzadian, M., Khanmohammadi Otaghsara, S., Yazdani, M., & Ignatius, J. (2012). A state-of the-art survey of TOPSIS applications. Expert Systems with Applications, 39(17), 13051–13069. https://doi.org/10.1016/j.eswa.2012.05.056
   - Doğrulama: Universidad Europea bilimsel portal kaydı: yazarlar, cilt 39, sayı 17, s. 13051–13069, DOI.
12. Bettinger, E. P., & Baker, R. B. (2014). The effects of student coaching: An evaluation of a randomized experiment in student advising. Educational Evaluation and Policy Analysis, 36(1), 3–19. https://doi.org/10.3102/0162373713500523 <https://journals.sagepub.com/doi/abs/10.3102/0162373713500523>
   - Doğrulama: SAGE dergi sayfası (yazar, yıl, cilt/sayı, sayfa, DOI)
13. Black, P., & Wiliam, D. (1998). Assessment and classroom learning. Assessment in Education: Principles, Policy & Practice, 5(1), 7–74. https://doi.org/10.1080/0969595980050102 <https://www.gla.ac.uk/t4/learningandteaching/files/PGCTHE/BlackandWiliam1998.pdf>
   - Doğrulama: Makalenin yayıncı PDF'i (Glasgow Üniversitesi kopyası; künye ve DOI basılı)
14. Bradley, P. S., Bennett, K. P., & Demiriz, A. (2000). Constrained k-means clustering (Technical Report MSR-TR-2000-65). Microsoft Research. <https://www.microsoft.com/en-us/research/publication/constrained-k-means-clustering/>
   - Doğrulama: Microsoft Research yayın sayfası ve rapor PDF'i (yazar sırası PDF başlık sayfasından)
15. Brown, A., & Maydeu-Olivares, A. (2011). Item response modeling of forced-choice questionnaires. Educational and Psychological Measurement, 71(3), 460–502. https://doi.org/10.1177/0013164410375112
   - Doğrulama: Mevcut kaynakca.json (#11) kaydı
16. Brown, S. D., & Ryan Krane, N. E. (2000). Four (or five) sessions and a cloud of dust: Old assumptions and new observations about career counseling. In S. D. Brown & R. W. Lent (Eds.), Handbook of counseling psychology (3rd ed., pp. 740–766). Wiley.
   - Doğrulama: Auburn Üniversitesi COUN 7230 ders izlencesi kaynakçası (editörler, baskı, sayfa)
17. Cassady, J. C., & Johnson, R. E. (2002). Cognitive test anxiety and academic performance. Contemporary Educational Psychology, 27(2), 270–295. https://doi.org/10.1006/ceps.2001.1094
   - Doğrulama: College of Wooster ders sayfası ve Salud & Sociedad makale kaynakçası (DOI, cilt, sayfa); sayı (2) ikinci kaynaktan
18. Cavoukian, A. (2011). Privacy by design: The 7 foundational principles. Implementation and mapping of fair information practices. Information and Privacy Commissioner of Ontario. <https://student.cs.uwaterloo.ca/~cs492/papers/7foundationalprinciples_longer.pdf>
   - Doğrulama: Belgenin PDF'i (Waterloo ders arşivi) başlık/yazar; Wikipedia kaynakçası Ocak 2011 ve IPC Ontario yayıncısını gösteriyor.
19. Cepeda, N. J., Pashler, H., Vul, E., Wixted, J. T., & Rohrer, D. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. Psychological Bulletin, 132(3), 354–380. https://doi.org/10.1037/0033-2909.132.3.354
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
20. Cer, D., Diab, M., Agirre, E., Lopez-Gazpio, I., & Specia, L. (2017). SemEval-2017 Task 1: Semantic textual similarity multilingual and crosslingual focused evaluation. In Proceedings of the 11th International Workshop on Semantic Evaluation (SemEval-2017) (pp. 1–14). Association for Computational Linguistics. https://doi.org/10.18653/v1/S17-2001
   - Doğrulama: ACL Anthology BibTeX kaydı (S17-2001)
21. Ceza Muhakemesi Kanunu ile Bazı Kanunlarda Değişiklik Yapılmasına Dair Kanun, Kanun No. 7499. (2024, 12 Mart). Resmî Gazete (Sayı: 32487).
   - Doğrulama: Erdem & Erdem hukuk bürosu bilgi notu: Kanun no. 7499, RG 12.03.2024/32487; KVKK md. 9 yeni düzeni, yürürlük 01.06.2024.
22. Chan, K.-Y., & Drasgow, F. (2001). Toward a theory of individual differences and leadership: Understanding the motivation to lead. Journal of Applied Psychology, 86(3), 481–498. https://doi.org/10.1037//0021-9010.86.3.481
   - Doğrulama: SUFE akademik bülten kaydı (academicnewsletter.sufe.edu.cn): yazarlar, sayı 3, s. 481–498, DOI
23. Chen, J., Xiao, S., Zhang, P., Luo, K., Lian, D., & Liu, Z. (2024). M3-Embedding: Multi-linguality, multi-functionality, multi-granularity text embeddings through self-knowledge distillation. In Findings of the Association for Computational Linguistics: ACL 2024. Association for Computational Linguistics. <https://aclanthology.org/2024.findings-acl.137>
   - Doğrulama: arXiv:2402.03216 + ACL Anthology ID 2024.findings-acl.137 (sayfa ve DOI doğrulanamadı, boş bırakıldı)
24. Coghlan, S., Miller, T., & Paterson, J. (2021). Good proctor or "Big Brother"? Ethics of online exam supervision technologies. Philosophy & Technology. https://doi.org/10.1007/s13347-021-00476-1
   - Doğrulama: Melbourne Üniversitesi CAIDE yayın sayfası: yazarlar, 2021, başlık, dergi, DOI; cilt/sayfa birincil olarak teyit edilemediği için yazılmadı.
25. Cohen, P., Cohen, J., Aiken, L. S., & West, S. G. (1999). The problem of units and the circumstance for POMP. Multivariate Behavioral Research, 34(3), 315–346. https://doi.org/10.1207/S15327906MBR3403_2
   - Doğrulama: arXiv 2507.13695 kaynakçası (yazarlar, cilt 34(3), s. 315–346, DOI) ve tandfonline.com DOI sayfası (arama sonucu)
26. Costa, P. T., & McCrae, R. R. (1992). Revised NEO Personality Inventory (NEO PI-R) and NEO Five-Factor Inventory (NEO-FFI) professional manual. Psychological Assessment Resources.
   - Doğrulama: Mevcut kaynakca.json (#4) kaydı
27. Cronbach, L. J., & Gleser, G. C. (1953). Assessing similarity between profiles. Psychological Bulletin, 50(6), 456–473. https://doi.org/10.1037/h0057173
   - Doğrulama: Wikipedia (Goldine Gleser) kaynakçası + DeepDyve kaydı (Psychological Bulletin, Kasım 1953)
28. Curran, P. G. (2016). Methods for the detection of carelessly invalid responses in survey data. Journal of Experimental Social Psychology, 66, 4–19. https://doi.org/10.1016/j.jesp.2015.07.006
   - Doğrulama: transformativeworkdesign.com kaynakçası (yazar, cilt 66, s. 4–19, DOI); doi.org adresinin Elsevier'e (S0022103115000931) yönlendiği görüldü
29. Dawes, R. M. (1979). The robust beauty of improper linear models in decision making. American Psychologist, 34(7), 571–582. https://doi.org/10.1037/0003-066X.34.7.571
   - Doğrulama: CMU makale PDF'i (dergi, cilt/sayı, sayfa) + PhilPapers kaydı
30. Dawis, R. V., & Lofquist, L. H. (1984). A psychological theory of work adjustment: An individual-differences model and its applications. University of Minnesota Press. <https://vpr.psych.umn.edu/theory-work-adjustment>
   - Doğrulama: Mevcut kaynakca.json (#1) kaydı
31. Deterding, S., Dixon, D., Khaled, R., & Nacke, L. (2011). From game design elements to gamefulness: Defining "gamification". In Proceedings of the 15th International Academic MindTrek Conference: Envisioning Future Media Environments (pp. 9–15). ACM. https://doi.org/10.1145/2181037.2181040
   - Doğrulama: Zürih Üniversitesi GBL kaynakça kaydı (bildiri kitabı, s. 9–15, DOI)
32. Dickson, D. H., & Kelly, I. W. (1985). The 'Barnum effect' in personality assessment: A review of the literature. Psychological Reports, 57, 367–382. <https://cortecs.org/wp-content/uploads/2014/12/the-barnum-effect-in-personality-assessment-a-review-of-the-literature.pdf>
   - Doğrulama: Makalenin PDF'inin ilk sayfası (cortecs.org): yazarlar, yıl, başlık, Psychological Reports, cilt 57, s. 367–382; DOI doğrulanamadığı için yazılmadı
33. Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). Improving students' learning with effective learning techniques: Promising directions from cognitive and educational psychology. Psychological Science in the Public Interest, 14(1), 4–58. https://doi.org/10.1177/1529100612453266
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
34. Eccles, J. S., & Barber, B. L. (1999). Student council, volunteering, basketball, or marching band: What kind of extracurricular involvement matters? Journal of Adolescent Research, 14(1), 10–43.
   - Doğrulama: Wikipedia (Jacquelynne Eccles) yayın listesi ve Newswise haber kaydı (yıl, başlık, dergi, cilt/sayı, sayfa); DOI birincil kaynakta görülmediği için boş
35. Edwards, J. R. (1993). Problems with the use of profile similarity indices in the study of congruence in organizational research. Personnel Psychology, 46, 641–665.
   - Doğrulama: NCU kurumsal arşivindeki tez kaynakçası (cilt ve sayfa); sayı ve DOI doğrulanamadı, boş bırakıldı
36. Epstein, J. L. (1995). School/family/community partnerships: Caring for the children we share. Phi Delta Kappan, 76(9), 701–712. <https://www.cde.state.co.us/uip/epstein_ee3>
   - Doğrulama: Colorado Department of Education yeniden basım sayfası: Phi Delta Kappan 76(9), Mayıs 1995, s. 701–712.
37. Ericsson, K. A., Krampe, R. T., & Tesch-Römer, C. (1993). The role of deliberate practice in the acquisition of expert performance. Psychological Review, 100(3), 363–406. https://doi.org/10.1037/0033-295X.100.3.363
   - Doğrulama: Macnamara & Maitra (2019) PMC makalesi kaynakçası (tam künye ve DOI)
38. European Commission. (t.y.). ESCO: European Skills, Competences, Qualifications and Occupations. https://esco.ec.europa.eu/en
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
39. Family Educational Rights and Privacy Act of 1974, 20 U.S.C. § 1232g (1974). <https://studentprivacy.ed.gov/ferpa>
   - Doğrulama: ABD Eğitim Bakanlığı studentprivacy.ed.gov sayfası: 20 U.S.C. § 1232g, 34 CFR Part 99, 1974.
40. Gale, D., & Shapley, L. S. (1962). College admissions and the stability of marriage. The American Mathematical Monthly, 69(1), 9–15. <http://www.jstor.org/stable/2312726>
   - Doğrulama: Makalenin JSTOR PDF'i (Toronto Üniversitesi kopyası; cilt, sayı, sayfa, JSTOR kalıcı bağlantısı); DOI basılı değil
41. Galesic, M., & Bosnjak, M. (2009). Effects of questionnaire length on participation and indicators of response quality in a web survey. Public Opinion Quarterly, 73(2), 349–360.
   - Doğrulama: Survey Research Methods (ojs.ub.uni-konstanz.de, makale 8348) kaynakçası: yazarlar, cilt 73(2), s. 349–360; DOI doğrulanamadığı için yazılmadı
42. Gati, I., & Asher, I. (2005). The PIC model for career decision making: Prescreening, in-depth exploration, and choice. In Contemporary models in vocational psychology: A volume in honor of Samuel H. Osipow (pp. 7–54). Taylor and Francis. https://doi.org/10.4324/9781410600578-5
   - Doğrulama: Hebrew University CRIS kaydı (cris.huji.ac.il): yazarlar, bölüm başlığı, kitap, s. 7–54, Taylor and Francis, DOI; kitabın editörleri kayıtta yer almadığı için yazılmadı (ilk basım 2001 olarak atıf yapılmaktadır)
43. Gati, I., Krausz, M., & Osipow, S. H. (1996). A taxonomy of difficulties in career decision making. Journal of Counseling Psychology, 43(4), 510–526. https://doi.org/10.1037/0022-0167.43.4.510
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
44. Goldberg, L. R. (1990). An alternative "description of personality": The Big-Five factor structure. Journal of Personality and Social Psychology, 59(6), 1216–1229.
   - Doğrulama: UCL ConstructDB (cilt 59, sayı 6, başlangıç s. 1216) ve GESIS ZIS kaydı (s. 1216–1229). DOI birincil kaynakta doğrulanamadığı için boş bırakıldı.
45. Gollwitzer, P. M. (1999). Implementation intentions: Strong effects of simple plans. American Psychologist, 54(7), 493–503. https://doi.org/10.1037/0003-066X.54.7.493
   - Doğrulama: Universität Konstanz KOPS deposu: cilt 54, sayı 7, s. 493–503, DOI.
46. Gollwitzer, P. M., & Sheeran, P. (2006). Implementation intentions and goal achievement: A meta-analysis of effects and processes. Advances in Experimental Social Psychology, 38, 69–119. https://doi.org/10.1016/S0065-2601(06)38002-1
   - Doğrulama: Konstanz Üniversitesi yayın sayfası (cilt 38, s. 69–119, DOI)
47. Goodenow, C. (1993). The psychological sense of school membership among adolescents: Scale development and educational correlates. Psychology in the Schools, 30(1), 79–90. https://doi.org/10.1002/1520-6807(199301)30:1<79::AID-PITS2310300113>3.0.CO;2-X
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
48. Gottfredson, L. S. (1981). Circumscription and compromise: A developmental theory of occupational aspirations. Journal of Counseling Psychology, 28(6), 545–579. https://doi.org/10.1037/0022-0167.28.6.545
   - Doğrulama: BIBB repozitoryosu kaydı (cilt, sayı, sayfa, DOI)
49. Graham, M., Milanowski, A., & Miller, J. (2012). Measuring and promoting inter-rater agreement of teacher and principal performance ratings. Center for Educator Compensation Reform. <https://files.eric.ed.gov/fulltext/ED532068.pdf>
   - Doğrulama: Mevcut kaynakca.json (#27) kaydı
50. Hamari, J. (2017). Do badges increase user activity? A field experiment on the effects of gamification. Computers in Human Behavior, 71, 469–478. https://doi.org/10.1016/j.chb.2015.03.036
   - Doğrulama: Tampere Üniversitesi Gamification Group sayfası (cilt 71, s. 469–478, DOI)
51. Hamari, J., Koivisto, J., & Sarsa, H. (2014). Does gamification work? A literature review of empirical studies on gamification. In Proceedings of the 47th Hawaii International Conference on System Sciences (pp. 3025–3034). IEEE. https://doi.org/10.1109/HICSS.2014.377
   - Doğrulama: Aalto Üniversitesi araştırma portalı (bildiri, s. 3025–3034, DOI)
52. Harkin, B., Webb, T. L., Chang, B. P. I., Prestwich, A., Conner, M., Kellar, I., Benn, Y., & Sheeran, P. (2016). Does monitoring goal progress promote goal attainment? A meta-analysis of the experimental evidence. Psychological Bulletin, 142(2), 198–229. https://doi.org/10.1037/bul0000025
   - Doğrulama: White Rose eprints kaydı (cilt 142, sayı 2, s. 198–229, DOI)
53. Helms, M. M., & Nixon, J. (2010). Exploring SWOT analysis – where are we now? A review of academic research from the last decade. Journal of Strategy and Management, 3(3), 215–251. https://doi.org/10.1108/17554251011064837
   - Doğrulama: DOI çözümleme sayfası (Emerald): yazarlar, yıl, cilt 3, sayı 3, s. 215–251.
54. Hembree, R. (1988). Correlates, causes, effects, and treatment of test anxiety. Review of Educational Research, 58(1), 47–77. https://doi.org/10.3102/00346543058001047 <https://journals.sagepub.com/doi/10.3102/00346543058001047>
   - Doğrulama: SAGE dergi sayfası (yazar, yıl, cilt/sayı, sayfa, DOI)
55. Hendrickson, A. (2007). An NCME instructional module on multistage testing. Educational Measurement: Issues and Practice, 26, 44–52. https://doi.org/10.1111/j.1745-3992.2007.00093.x
   - Doğrulama: NCME'nin barındırdığı modül PDF'i (yazar, yıl, başlık, s. 44–52) ve Frontiers in Education (2019, feduc.2019.00001) kaynakçası (cilt 26, DOI); sayı numarası doğrulanamadı
56. Hicks, L. E. (1970). Some properties of ipsative, normative, and forced-choice normative measures. Psychological Bulletin, 74, 167–184.
   - Doğrulama: Frontiers in Psychology (2021, fpsyg.2021.573252) ve iResearchNet kaynakçaları: yazar, başlık, cilt 74, s. 167–184; DOI ve sayı numarası doğrulanamadığı için yazılmadı
57. High-Level Expert Group on Artificial Intelligence. (2019). Ethics guidelines for trustworthy AI. European Commission. <https://merlin.obs.coe.int/article/8608>
   - Doğrulama: Avrupa Konseyi IRIS Merlin kaydı: 8 Nisan 2019, Komisyonca kurulan HLEG tarafından yayımlandı; şeffaflık yedi temel gereklilikten biri.
58. Holland, J. L. (1997). Making vocational choices: A theory of vocational personalities and work environments (3rd ed.). Psychological Assessment Resources.
   - Doğrulama: Mevcut kaynakca.json (#6) kaydı
59. Huang, J. L., Curran, P. G., Keeney, J., Poposki, E. M., & DeShon, R. P. (2012). Detecting and deterring insufficient effort responding to surveys. Journal of Business and Psychology, 27, 99–114. https://doi.org/10.1007/s10869-011-9231-8
   - Doğrulama: Frontiers in Psychology (2019, fpsyg.2019.01258) kaynakçası (yazarlar, cilt 27, s. 99–114, DOI) ve ProQuest kaydı (ISSN 0889-3268, s. 99–114); sayı numarası doğrulanamadı
60. Hwang, C.-L., & Yoon, K. (1981). Multiple attribute decision making: Methods and applications. A state-of-the-art survey (Lecture Notes in Economics and Mathematical Systems, Vol. 186). Springer. https://doi.org/10.1007/978-3-642-48318-9
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
61. International Labour Organization. (2012). International Standard Classification of Occupations 2008 (ISCO-08): Structure, group definitions and correspondence tables. International Labour Organization. <https://www.ilo.org/publications/international-standard-classification-occupations-2008-isco-08-structure>
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
62. İş Sağlığı ve Güvenliği Kanunu, Kanun No. 6331. (2012, 30 Haziran). Resmî Gazete (Sayı: 28339). <https://www.mevzuat.gov.tr/MevzuatMetin/1.5.6331-20140910.pdf>
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
63. Iyengar, S. S., & Lepper, M. R. (2000). When choice is demotivating: Can one desire too much of a good thing? Journal of Personality and Social Psychology, 79(6), 995–1006. https://doi.org/10.1037/0022-3514.79.6.995
   - Doğrulama: Makalenin University of Washington ders PDF'i başlık sayfası (cilt, sayı, sayfa, DOI)
64. Jacobson, N. S., & Truax, P. (1991). Clinical significance: A statistical approach to defining meaningful change in psychotherapy research. Journal of Consulting and Clinical Psychology, 59(1), 12–19.
   - Doğrulama: Makalenin UCF'de barındırılan PDF'i başlık sayfası (cilt 59, sayı 1, s. 12–19); DOI birincil kaynakta görülmediği için yazılmadı
65. Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y., Chen, D., Dai, W., Chan, H. S., Madotto, A., & Fung, P. (2023). Survey of hallucination in natural language generation. ACM Computing Surveys, 55(12), Article 248. https://doi.org/10.1145/3571730
   - Doğrulama: arXiv 2202.03629 sayfası (yazarlar, DOI) ve dblp kaydı (cilt 55, sayı 12, makale 248)
66. John, O. P., & Srivastava, S. (1999). The Big Five trait taxonomy: History, measurement, and theoretical perspectives. In L. A. Pervin & O. P. John (Eds.), Handbook of personality: Theory and research (2nd ed., pp. 102–138). Guilford Press. <https://pages.uoregon.edu/sanjay/pubs/bigfive.pdf>
   - Doğrulama: Mevcut kaynakca.json (#3) kaydı
67. Kam, C. C. S., & Chan, H. H. (2018). Examination of the validity of instructed response items in identifying careless respondents. Personality and Individual Differences, 129, 83–87. https://doi.org/10.1016/j.paid.2018.03.022
   - Doğrulama: EdUHK Research Repository kaydı (yazarlar, cilt 129, s. 83–87, DOI) ve Frontiers in Psychology (2019) kaynakçası
68. Kendall, M. G., & Babington Smith, B. (1939). The problem of m rankings. The Annals of Mathematical Statistics, 10(3), 275–287. https://doi.org/10.1214/aoms/1177732186
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
69. Kişisel Verileri Koruma Kurulu. (2026, 24 Mart). Veri sorumluları tarafından açık rıza ve aydınlatma metinlerinin ayrı ayrı düzenlenmesi gerektiği hakkında ilke kararı (Karar No. 2026/347). Resmî Gazete (Sayı: 33203). <https://www.alomaliye.com/2026/03/24/kvkkdan-yeni-ilke-karari-acik-riza-metni-ile-aydinlatma-metni-artik-ayri-duzenlenmeli/>
   - Doğrulama: alomaliye.com: karar tarihi 18.02.2026, sayı 2026/347, RG 24.03.2026/33203 ve kararın özü.
70. Kişisel Verileri Koruma Kurumu. (2018). Kişisel veri güvenliği rehberi (teknik ve idari tedbirler). Kişisel Verileri Koruma Kurumu. <https://www.kvkk.gov.tr/>
   - Doğrulama: TÜRMOB arşivindeki rehber PDF'i (Ocak 2018, Ankara, KVKK yayını) ve alomaliye.com kaydı; yetki matrisi, log kaydı, şifreleme bölümleri teyit edildi.
71. Kişisel Verileri Koruma Kurumu. (2021). Biyometrik verilerin işlenmesinde dikkat edilecek hususlara ilişkin rehber. Kişisel Verileri Koruma Kurumu. <https://www.alomaliye.com/2021/09/16/biyometrik-verilerin-islenmesinde-dikkat-edilecek-hususlara-iliskin-rehber/>
   - Doğrulama: alomaliye.com yayını (16.09.2021, kaynak KVKK); fotoğrafın ancak özel teknik işlemeyle biyometrik veri sayılacağı ifadesi teyit edildi.
72. Kişisel Verilerin Korunması Kanunu, Kanun No. 6698. (2016, 7 Nisan). Resmî Gazete (Sayı: 29677). <https://mevzuat.gov.tr/MevzuatMetin/1.5.6698.pdf>
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
73. Kivetz, R., Urminsky, O., & Zheng, Y. (2006). The goal-gradient hypothesis resurrected: Purchase acceleration, illusionary goal progress, and customer retention. Journal of Marketing Research, 43(1), 39–58.
   - Doğrulama: Columbia Business School yayın sayfası ve makale PDF'i (cilt XLIII, Şubat 2006, s. 39–58); DOI görülmediği için yazılmadı
74. Kizilcec, R. F. (2016). How much information? Effects of transparency on trust in an algorithmic interface. In Proceedings of the 2016 CHI Conference on Human Factors in Computing Systems (pp. 2390–2395). Association for Computing Machinery. https://doi.org/10.1145/2858036.2858402
   - Doğrulama: Makalenin CHI 2016 PDF'i (McGill ders arşivi): yazar, başlık, s. 2390–2395, ACM DOI.
75. Kolb, D. A. (1984). Experiential learning: Experience as the source of learning and development. Prentice-Hall.
   - Doğrulama: WorldCat kaydı (OCLC 9555621: yazar, yıl, yayınevi)
76. Kristof-Brown, A. L., Zimmerman, R. D., & Johnson, E. C. (2005). Consequences of individuals' fit at work: A meta-analysis of person–job, person–organization, person–group, and person–supervisor fit. Personnel Psychology, 58(2), 281–342. https://doi.org/10.1111/j.1744-6570.2005.00672.x
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
77. Lally, P., van Jaarsveld, C. H. M., Potts, H. W. W., & Wardle, J. (2010). How are habits formed: Modelling habit formation in the real world. European Journal of Social Psychology, 40(6), 998–1009. https://doi.org/10.1002/ejsp.674
   - Doğrulama: Crossref API kaydı (cilt 40, sayı 6, s. 998–1009, DOI)
78. Landis, J. R., & Koch, G. G. (1977). The measurement of observer agreement for categorical data. Biometrics, 33(1), 159–174. https://doi.org/10.2307/2529310
   - Doğrulama: PubMed kaydı (PMID 843571; cilt 33, sayı 1, s. 159–174) ve Wikidata Q26778373 (yazarlar, DOI).
79. Lawshe, C. H. (1975). A quantitative approach to content validity. Personnel Psychology, 28(4), 563–575. https://doi.org/10.1111/j.1744-6570.1975.tb01393.x
   - Doğrulama: UCL constructDB yayın kaydı (verdi.cs.ucl.ac.uk): yazar, cilt 28(4), s. 563–575, DOI
80. Lester, J. C., Converse, S. A., Kahler, S. E., Barlow, S. T., Stone, B. A., & Bhogal, R. S. (1997). The persona effect: Affective impact of animated pedagogical agents. In Proceedings of the ACM SIGCHI Conference on Human Factors in Computing Systems (CHI '97) (pp. 359–366). ACM.
   - Doğrulama: CHI 97 elektronik bildiri sayfası (yazarlar) ve IxDF kaydı (s. 359–366); DOI görülmediği için yazılmadı
81. Lievens, F., Peeters, H., & Schollaert, E. (2008). Situational judgment tests: A review of recent research. Personnel Review, 37(4), 426–441. https://doi.org/10.1108/00483480810877598
   - Doğrulama: Mevcut kaynakca.json (#10) kaydı
82. Likert, R. (1932). A technique for the measurement of attitudes. Archives of Psychology, 140, 1–55.
   - Doğrulama: Mevcut kaynakca.json (#12) kaydı
83. Locke, E. A., & Latham, G. P. (2002). Building a practically useful theory of goal setting and task motivation: A 35-year odyssey. American Psychologist, 57(9), 705–717. https://doi.org/10.1037/0003-066X.57.9.705
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
84. Low, K. S. D., Yoon, M., Roberts, B. W., & Rounds, J. (2005). The stability of vocational interests from early adolescence to middle adulthood: A quantitative review of longitudinal studies. Psychological Bulletin, 131(5), 713–737. https://doi.org/10.1037/0033-2909.131.5.713
   - Doğrulama: Frontiers in Psychology (2025, fpsyg.2025.1498424) kaynakçası: yazarlar, cilt 131, s. 713–737, DOI (sayı DOI'den)
85. MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. In L. M. Le Cam & J. Neyman (Eds.), Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability (Vol. 1, pp. 281–297). University of California Press. <https://projecteuclid.org/proceedings/berkeley-symposium-on-mathematical-statistics-and-probability/proceedings-of-the-fifth-berkeley-symposium-on-mathematical-statistics-and-probability-volume-1-statistics/toc/bsmsp/1200512974>
   - Doğrulama: Mevcut kaynakca.json (#23) kaydı
86. Maden İşyerlerinde İş Sağlığı ve Güvenliği Yönetmeliği. (2013, 19 Eylül). Resmî Gazete (Sayı: 28770). <https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=18858&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5>
   - Doğrulama: mevzuat.gov.tr resmi PDF bağlantısı arama sonucunda yönetmelik başlığıyla doğrulandı; RG 19.09.2013/28770 bilgisi alomaliye.com'dan (sonraki değişiklikler dahil) teyit edildi.
87. McDaniel, M. A., Hartman, N. S., Whetzel, D. L., & Grubb, W. L. (2007). Situational judgment tests, response instructions, and validity: A meta-analysis. Personnel Psychology, 60, 63–91. https://doi.org/10.1111/j.1744-6570.2007.00065.x
   - Doğrulama: Mevcut kaynakca.json (#9) kaydı
88. McDaniel, M. A., Morgeson, F. P., Finnegan, E. B., Campion, M. A., & Braverman, E. P. (2001). Use of situational judgment tests to predict job performance: A clarification of the literature. Journal of Applied Psychology, 86(4), 730–740. https://doi.org/10.1037/0021-9010.86.4.730
   - Doğrulama: Mevcut kaynakca.json (#8) kaydı
89. McHugh, M. L. (2012). Interrater reliability: The kappa statistic. Biochemia Medica, 22(3), 276–282. https://doi.org/10.11613/BM.2012.031
   - Doğrulama: Hrčak kaydı (hrcak.srce.hr/89395; cilt 22, sayı 3, s. 276–282) ve Biochemia Medica yayıncı URL'si (biochemia-medica.com/en/journal/22/3/10.11613/BM.2012.031).
90. McPherson, M., Smith-Lovin, L., & Cook, J. M. (2001). Birds of a feather: Homophily in social networks. Annual Review of Sociology, 27, 415–444. https://doi.org/10.1146/annurev.soc.27.1.415
   - Doğrulama: Duke Scholars yayın kaydı
91. Meade, A. W., & Craig, S. B. (2012). Identifying careless responses in survey data. Psychological Methods, 17, 437–455. https://doi.org/10.1037/a0028085
   - Doğrulama: Frontiers in Psychology (2019, fpsyg.2019.01258) kaynakçası: yazarlar, cilt 17, s. 437–455, DOI; sayı numarası doğrulanamadığı için yazılmadı
92. Mehrabi, N., Morstatter, F., Saxena, N., Lerman, K., & Galstyan, A. (2021). A survey on bias and fairness in machine learning. ACM Computing Surveys, 54(6), 1–35. <https://arxiv.org/abs/1908.09635>
   - Doğrulama: USC ISI yayın kaydı (dergi, cilt/sayı, sayfa); DOI doğrulanamadı, boş bırakıldı
93. Mesleki Yeterlilik Kurumu. (t.y.). Ulusal meslek standartları. <https://www.myk.gov.tr/tr/page/18>
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
94. Millî Eğitim Bakanlığı Eğitim Kurumları Sosyal Etkinlikler Yönetmeliği. (2017, 8 Haziran). Resmî Gazete (Sayı: 30090). <https://www.memurlar.net/haber/673265/egitim-kurumlarindaki-sosyal-etkinliklere-duzenleme.html>
   - Doğrulama: Memurlar.net değişiklik haberi (RG 8/6/2017, sayı 30090) ve AA kaynaklı yayım haberi; mevzuat.gov.tr açılamadı
95. Millî Eğitim Bakanlığı Rehberlik ve Psikolojik Danışma Hizmetleri Yönetmeliği. (2020, 14 Ağustos). Resmî Gazete (Sayı: 31213). <https://www.mevzuat.gov.tr/File/GeneratePdf?mevzuatNo=34760&mevzuatTur=KurumVeKurulusYonetmeligi&mevzuatTertip=5>
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
96. Morris, T. P., White, I. R., & Crowther, M. J. (2019). Using simulation studies to evaluate statistical methods. Statistics in Medicine, 38(11), 2074–2102. https://doi.org/10.1002/sim.8086
   - Doğrulama: UCL Discovery kaydı ve Leicester figshare: yazarlar, yıl, cilt 38, sayı 11, s. 2074–2102, DOI.
97. National Action Alliance for Suicide Prevention. (t.y.). Framework for successful messaging. https://suicidepreventionmessaging.org/
   - Doğrulama: Action Alliance 'public messaging' sayfası ve SPRC duyurusu (2014): strateji, güvenlik, olumlu anlatı, yönergeler bileşenleri
98. Nye, C. D., Su, R., Rounds, J., & Drasgow, F. (2012). Vocational interests and performance: A quantitative summary of over 60 years of research. Perspectives on Psychological Science, 7(4), 384–403. https://doi.org/10.1177/1745691612449021
   - Doğrulama: SAGE yayıncı sayfası
99. Ölçme, Seçme ve Yerleştirme Merkezi Başkanlığı. (2026). 2026 Yükseköğretim Kurumları Sınavı (2026-YKS) sıkça sorulan sorular. <https://dokuman.osym.gov.tr/pdfdokuman/2026/YKS/sss_yksd19022026.pdf>
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
100. Olweus, D. (1993). Bullying at school: What we know and what we can do. Blackwell. <https://casbs.stanford.edu/bullying-school-what-we-know-and-what-we-can-do>
   - Doğrulama: Stanford CASBS yayın kaydı ve WorldCat/kütüphane katalogları (yazar, yıl, başlık, yayınevi)
101. Opricovic, S., & Tzeng, G.-H. (2004). Compromise solution by MCDM methods: A comparative analysis of VIKOR and TOPSIS. European Journal of Operational Research, 156(2), 445–455. https://doi.org/10.1016/S0377-2217(03)00020-1
   - Doğrulama: RePEc/IDEAS kaydı (cilt/sayı/sayfa); DOI, kayıttaki ScienceDirect PII'sinden
102. Osgood, C. E., Suci, G. J., & Tannenbaum, P. H. (1957). The measurement of meaning. University of Illinois Press. <https://www.gwern.net/doc/psychology/1957-osgood-themeasurementofmeaning.pdf>
   - Doğrulama: Kitabın tarama PDF'inin künye sayfası (yazarlar, başlık, University of Illinois Press, ilk basım 1957)
103. Osipow, S. H., Carney, C. G., Winer, J., Yanico, B., & Koschier, M. (1976–1987). Career Decision Scale. Psychological Assessment Resources. <https://marketplace.unl.edu/buros/test-reviews/alphabetical-list/career-decision-scale.html>
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
104. OWASP Foundation. (2025). OWASP Application Security Verification Standard (Version 5.0.0). https://owasp.org/www-project-application-security-verification-standard/
   - Doğrulama: OWASP ASVS GitHub README: son kararlı sürüm 5.0.0, Mayıs 2025.
105. OWASP Foundation. (t.y.). Forgot password cheat sheet. OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html
   - Doğrulama: OWASP Cheat Sheet Series sayfası doğrudan okundu (tutarlı yanıt, tek kullanımlık ve süreli token, hız sınırlama önerileri).
106. Papenberg, M., & Klau, G. W. (2021). Using anticlustering to partition data sets into equivalent parts. Psychological Methods, 26(2), 161–174. https://doi.org/10.1037/met0000301
   - Doğrulama: HeBIS/PsycINFO kaydı + CRAN anticlust vinyeti (DOI)
107. Paulhus, D. L. (1991). Measurement and control of response bias. In J. P. Robinson, P. R. Shaver, & L. S. Wrightsman (Eds.), Measures of personality and social psychological attitudes (pp. 17–59). Academic Press.
   - Doğrulama: GESIS ZIS kaydı (data.gesis.org, zis-Paulhus1991Measurement): yazar, editörler, kitap, s. 17–59, Academic Press
108. Phillips, J. M. (1998). Effects of realistic job previews on multiple organizational outcomes: A meta-analysis. Academy of Management Journal, 41(6), 673–690. https://doi.org/10.2307/256964
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
109. Podsakoff, P. M., MacKenzie, S. B., Lee, J.-Y., & Podsakoff, N. P. (2003). Common method biases in behavioral research: A critical review of the literature and recommended remedies. Journal of Applied Psychology, 88(5), 879–903. https://doi.org/10.1037/0021-9010.88.5.879
   - Doğrulama: Mevcut kaynakca.json (#14) kaydı
110. Prediger, D. J. (1982). Dimensions underlying Holland's hexagon: Missing link between interests and occupations? Journal of Vocational Behavior, 21, 259–287. https://doi.org/10.1016/0001-8791(82)90036-7
   - Doğrulama: Journal of Career Assessment (SAGE) makalesi kaynakçası (cilt, sayfa, DOI); sayı doğrulanamadı
111. Premack, S. L., & Wanous, J. P. (1985). A meta-analysis of realistic job preview experiments. Journal of Applied Psychology, 70, 706–719.
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
112. Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. In Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP) (pp. 3982–3992). Association for Computational Linguistics. https://doi.org/10.18653/v1/D19-1410
   - Doğrulama: Mevcut kaynakca.json (#17) kaydı
113. Roberts, B. W., & DelVecchio, W. F. (2000). The rank-order consistency of personality traits from childhood to old age: A quantitative review of longitudinal studies. Psychological Bulletin, 126(1), 3–25. https://doi.org/10.1037/0033-2909.126.1.3
   - Doğrulama: PMC2680603 makalesinin kaynakçası ve stafforini.com kaydı (cilt, sayı, sayfa, DOI)
114. Roberts, B. W., Luo, J., Briley, D. A., Chow, P. I., Su, R., & Hill, P. L. (2017). A systematic review of personality trait change through intervention. Psychological Bulletin, 143(2), 117–141. https://doi.org/10.1037/bul0000088
   - Doğrulama: Iowa Üniversitesi repozitoryosu ve PubMed kaydı (yazarlar, cilt, sayı, sayfa, DOI)
115. Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning: Taking memory tests improves long-term retention. Psychological Science, 17(3), 249–255. https://doi.org/10.1111/j.1467-9280.2006.01693.x
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
116. Ryan, R. M., & Deci, E. L. (2000). Self-determination theory and the facilitation of intrinsic motivation, social development, and well-being. American Psychologist, 55(1), 68–78. https://doi.org/10.1037/0003-066X.55.1.68
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
117. Saka, N., Gati, I., & Kelly, K. R. (2008). Emotional and personality-related aspects of career-decision-making difficulties. Journal of Career Assessment, 16(4), 403–424. https://doi.org/10.1177/1069072708318900
   - Doğrulama: Hebrew University CRIS kaydı
118. Saltelli, A., Ratto, M., Andres, T., Campolongo, F., Cariboni, J., Gatelli, D., Saisana, M., & Tarantola, S. (2008). Global sensitivity analysis: The primer. John Wiley & Sons. https://doi.org/10.1002/9780470725184
   - Doğrulama: Wikipedia kitap maddesi (yazarlar, yayınevi, ISBN, DOI) + Wiley ürün sayfası
119. Saltzer, J. H., & Schroeder, M. D. (1975). The protection of information in computer systems. Proceedings of the IEEE, 63(9), 1278–1308. <https://web.mit.edu/saltzer/www/publications/protection/>
   - Doğrulama: COIT Foro Histórico kaydı: Proceedings of the IEEE 63(9), Eylül 1975, s. 1278–1308; MIT yazar sayfası. DOI birincil olarak teyit edilemediği için yazılmadı.
120. Sandhu, R. S., Coyne, E. J., Feinstein, H. L., & Youman, C. E. (1996). Role-based access control models. Computer, 29(2), 38–47. <https://profsandhu.com/most_cited_papers.htm>
   - Doğrulama: Sandhu'nun kişisel yayın listesi (profsandhu.com) ve IxDF künyesi: yazarlar, IEEE Computer 29(2), Şubat 1996, s. 38–47; DOI teyit edilemediği için yazılmadı.
121. Scheibehenne, B., Greifeneder, R., & Todd, P. M. (2010). Can there ever be too many options? A meta-analytic review of choice overload. Journal of Consumer Research, 37(3), 409–425. https://doi.org/10.1086/651235
   - Doğrulama: IDEAS/RePEc kaydı (cilt 37, sayı 3, s. 409–425, DOI)
122. Schomburg, H. (2016). Carrying out tracer studies: Guide to anticipating and matching skills and jobs (Vol. 6). European Training Foundation, European Centre for the Development of Vocational Training & International Labour Office. <https://www.etf.europa.eu/en/node/1108>
   - Doğrulama: ETF yayın sayfası ve kılavuzun PDF'i (yazar, yıl, başlık, cilt, yayıncılar)
123. Schwartz, S. H. (1992). Universals in the content and structure of values: Theoretical advances and empirical tests in 20 countries. Advances in Experimental Social Psychology, 25, 1–65. https://doi.org/10.1016/S0065-2601(08)60281-6
   - Doğrulama: Mevcut kaynakca.json (#0) kaydı
124. Seastrom, M. (2010). Statistical methods for protecting personally identifiable information in aggregate reporting (SLDS Technical Brief 3, NCES 2011-603). National Center for Education Statistics. <https://nces.ed.gov/use-work/resource-library/report/technicalmethodological-report/statistical-methods-protecting-personally-identifiable-information-aggregate-reporting>
   - Doğrulama: NCES resmî yayın sayfası: yazar, Aralık 2010, başlık, yayın no. NCES 2011-603.
125. Steel, P. (2007). The nature of procrastination: A meta-analytic and theoretical review of quintessential self-regulatory failure. Psychological Bulletin, 133(1), 65–94. <https://prism.ucalgary.ca/handle/1880/47914>
   - Doğrulama: Calgary Üniversitesi PRISM deposu ve stafforini.com kaydı (yazar, yıl, başlık, cilt/sayı, sayfa); dergi DOI'si birincil kaynakta görülmediği için boş
126. Steenbergen-Hu, S., Makel, M. C., & Olszewski-Kubilius, P. (2016). What one hundred years of research says about the effects of ability grouping and acceleration on K–12 students' academic achievement: Findings of two second-order meta-analyses. Review of Educational Research, 86(4), 849–899. https://doi.org/10.3102/0034654316675417
   - Doğrulama: SAGE edge kaydı (cilt/sayı/sayfa) + Acceleration Institute bibliyografyası (DOI)
127. Stemler, S. E. (2004). A comparison of consensus, consistency, and measurement approaches to estimating interrater reliability. Practical Assessment, Research, and Evaluation. <https://openpublishing.library.umass.edu/pare/article/id/1540/>
   - Doğrulama: Mevcut kaynakca.json (#26) kaydı
128. Super, D. E. (1980). A life-span, life-space approach to career development. Journal of Vocational Behavior, 16(3), 282–298. https://doi.org/10.1016/0001-8791(80)90056-1
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
129. Sweeney, L. (2002). k-anonymity: A model for protecting privacy. International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, 10(5), 557–570. https://doi.org/10.1142/S0218488502001648
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
130. Taylor, K. M., & Betz, N. E. (1983). Applications of self-efficacy theory to the understanding and treatment of career indecision. Journal of Vocational Behavior, 22, 63–81. https://doi.org/10.1016/0001-8791(83)90006-4
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
131. Temoshok, D., Fenton, J., Choong, Y.-Y., Lefkovitz, N., Regenscheid, A., Galluzzo, R., & Richer, J. (2025). Digital identity guidelines: Authentication and authenticator management (NIST Special Publication 800-63B-4). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.SP.800-63b-4
   - Doğrulama: NIST CSRC resmî yayın sayfası: yazarlar, Temmuz 2025, başlık, DOI.
132. Thapa, A., Cohen, J., Guffey, S., & Higgins-D'Alessandro, A. (2013). A review of school climate research. Review of Educational Research, 83(3), 357–385. <https://eric.ed.gov/?id=EJ1164824>
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
133. Tiedemann, J., & Thottingal, S. (2020). OPUS-MT – Building open translation services for the World. In Proceedings of the 22nd Annual Conference of the European Association for Machine Translation (pp. 479–480). European Association for Machine Translation. <https://aclanthology.org/2020.eamt-1.61/>
   - Doğrulama: Mevcut kaynakca.json (doğrulanmış)
134. Tiedemann, J., Aulamo, M., Bakshandaeva, D., Boggia, M., Grönroos, S.-A., Nieminen, T., Raganato, A., Scherrer, Y., Vázquez, R., & Virpioja, S. (2024). Democratizing neural machine translation with OPUS-MT. Language Resources and Evaluation, 58(2), 713–755. https://doi.org/10.1007/s10579-023-09704-w
   - Doğrulama: BOA Unimib kurumsal arşiv kaydı (yazarlar, cilt/sayı, sayfa, DOI)
135. Tracey, T. J., & Rounds, J. (1993). Evaluating Holland's and Gati's vocational-interest models: A structural meta-analysis. Psychological Bulletin, 113(2), 229–246. https://doi.org/10.1037/0033-2909.113.2.229
   - Doğrulama: Journal of Career Assessment (SAGE) makalesi kaynakçası + DeepDyve kaydı
136. Türkiye İş Kurumu. (t.y.). Meslekleri tanıyalım. <https://esube.iskur.gov.tr/Meslek/MeslekleriTaniyalim.aspx>
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
137. UNESCO Institute for Statistics. (2015). International Standard Classification of Education: Fields of education and training 2013 (ISCED-F 2013) – Detailed field descriptions. UNESCO Institute for Statistics. https://doi.org/10.15220/978-92-9189-179-5-en
   - Doğrulama: VOCEDplus kaydı (ISBN, DOI)
138. UNICEF Innocenti. (2025). Guidance on AI and children (Version 3.0): Recommendations for AI policies and systems that uphold child rights. UNICEF. https://www.unicef.org/innocenti/reports/policy-guidance-ai-children
   - Doğrulama: UNICEF Innocenti rapor sayfası (Aralık 2025, sürüm 3.0, 10 gereksinim) ve UNRIC duyurusu
139. von der Embse, N., Jester, D., et al. (2018). Test anxiety effects, predictors, and correlates: A 30-year meta-analytic review. Journal of Affective Disorders, 227, 483–493. https://doi.org/10.1016/j.jad.2017.11.048
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
140. Ward, J. H., Jr. (1963). Hierarchical grouping to optimize an objective function. Journal of the American Statistical Association, 58(301), 236–244. https://doi.org/10.1080/01621459.1963.10500845
   - Doğrulama: Wikipedia 'Ward's method' kaynakçası (cilt 58, s. 236–244) ve Taylor & Francis yayıncı sayfası (tandfonline.com, Vol 58, No 301, DOI).
141. Weekley, J. A., & Ployhart, R. E. (Eds.). (2006). Situational judgment tests: Theory, measurement, and application. Lawrence Erlbaum Associates. <https://www.routledge.com/products/9780805852516>
   - Doğrulama: GESIS ZIS kaydı (data.gesis.org, zis-Weekley2006Situational): editörler, yıl, başlık, Erlbaum; Routledge ürün sayfası arama sonucu
142. Weijters, B., & Baumgartner, H. (2012). Misresponse to reversed and negated items in surveys: A review. Journal of Marketing Research, 49(5), 737–747. https://doi.org/10.1509/jmr.11.0368
   - Doğrulama: Mevcut kaynakca.json (#13) kaydı
143. Whiston, S. C., Sexton, T. L., & Lasoff, D. L. (1998). Career-intervention outcome: A replication and extension of Oliver and Spokane (1988). Journal of Counseling Psychology, 45(2), 150–165. https://doi.org/10.1037/0022-0167.45.2.150
   - Doğrulama: NCDA makalesi kaynakçası (yazarlar, dergi, sayfa) ve scite.ai kaydı (tam başlık, sayı, DOI)
144. Woldeab, D., & Brothen, T. (2019). 21st century assessment: Online proctoring, test anxiety, and student performance. International Journal of E-Learning & Distance Education, 34(1). <https://www.ijede.ca/index.php/jde/article/view/1106>
   - Doğrulama: Dergi (IJEDE) makale sayfası: yazarlar, cilt 34 sayı 1, 30 Ağustos 2019; DOI yok.
145. World Health Organization. (2023). Preventing suicide: A resource for media professionals, update 2023. https://www.who.int/publications/i/item/9789240076846
   - Doğrulama: WHO yayın sayfası (12 Eylül 2023, ISBN 978-92-4-007684-6) ve tam metin PDF'teki Dos/Don'ts listesi
146. World Health Organization. (2026, 16 Temmuz). Antimicrobial resistance [Fact sheet]. <https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance>
   - Doğrulama: who.int resmi bilgi notu açıldı: başlık 'Antimicrobial resistance', sayfada 16 Temmuz 2026 tarihi (yayın/güncelleme ayrımı belirtilmemiş); gereksiz ya da yanlış antimikrobiyal kullanımının direncin başlıca etkeni olduğu belirtiliyor.
147. Yükseköğretim Kurulu. (t.y.). YÖK Atlas: Yükseköğretim program atlası. <https://yokatlas.yok.gov.tr/>
   - Doğrulama: Mevcut kaynakca.json (#49) kaydı
148. Zavadskas, E. K., Turskis, Z., Antucheviciene, J., & Zakarevicius, A. (2012). Optimization of weighted aggregated sum product assessment. Elektronika ir Elektrotechnika, 122(6), 3–6. https://doi.org/10.5755/j01.eee.122.6.1810
   - Doğrulama: Dergi sayfası (eejournal.ktu.lt)
149. Zeidner, M. (1998). Test anxiety: The state of the art. Springer. https://doi.org/10.1007/b109548
   - Doğrulama: kaynakca.json'daki doğrulanmış kayıt
150. Zenisky, A. L., & Hambleton, R. K. (2012). Developing test score reports that work: The process and best practices for effective communication. Educational Measurement: Issues and Practice, 31(2), 21–26. https://doi.org/10.1111/j.1745-3992.2012.00231.x
   - Doğrulama: Frontiers in Education (2019) makale kaynakçası: yazarlar, yıl, başlık, cilt 31, s. 21–26, DOI; sayı (2) DOI'deki 2012 yayın numarasıyla tutarlı, ayrıca birincil olarak teyit edilemedi.
151. Zhang, Y., & Chen, X. (2020). Explainable recommendation: A survey and new perspectives. Foundations and Trends in Information Retrieval, 14(1), 1–101. https://doi.org/10.1561/1500000066
   - Doğrulama: now publishers yayıncı sayfası
152. Zimmerman, B. J. (2002). Becoming a self-regulated learner: An overview. Theory Into Practice, 41(2), 64–70.
   - Doğrulama: VDU ders kaynağı sayfası (cilt 41, sayı 2, s. 64–70); DOI birincil kaynakta görülmediği için yazılmadı

## Doğrulanamayan ve listeye alınmayan künyeler

- Türk Psikologlar Derneği Etik Yönetmeliği (2004) — resmî metne erişilemedi.
- Spielberger (1980) Test Anxiety Inventory el kitabı — katalog kaydı bulunamadı; yerine Zeidner (1998), Hembree (1988), von der Embse ve ark. (2018).
- Super (1970) Work Values Inventory — künye doğrulanamadı.
- Osipow (1987) Career Decision Scale el kitabı — yalnızca ölçeğin kendisi doğrulandı.
- ÖSYM 2026-YKS ana kılavuz PDF'i — sayfa açılamadı; ÖSYM SSS belgesi kullanıldı.
- Kaiser & Overfield (2011), Meade (2004), Gibson (2004), Yeager ve ark. (2019), Edwards (1991), Ong & Weiss (2000) — künye ayrıntıları doğrulanamadığı için eklenmedi.
- Bazı künyelerde DOI veya sayı numarası boş bırakıldı (birincil kaynakta görülemedi). doi.org, Crossref ve bazı resmî siteler çalışma sırasında doğrudan erişilemediği için teyit kütüphane kataloğu, yayıncı sayfası ve kurum kayıtlarından yapıldı.
