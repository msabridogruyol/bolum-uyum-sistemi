# -*- coding: utf-8 -*-
"""
Koçluk — detaylı gelişim içeriği (K1-K4, 31 değişken).                       [2026-10-03]

Her değişken için:
  nedir          : Bu özellik ne demek (öğrenci dilinde)
  gelisim_neden  : Öğrenci hedef bölümün beklentisinin ALTINDAYSA neden önemli ({bolum} = hedef bölüm adı)
  guclu_neden    : Öğrenci beklentinin ÜSTÜNDEYSE bu gücü nasıl değerlendirir
  gelisim        : 6 adım — her aşamada 2 adım (simdi = başlangıç, bu_donem = pratik ve deneyim, uzun_vadede = kalıcı alışkanlık; süre yok)
  guclu          : 2 adım — güçlü yönü hedef bölüm yolunda kullanma

Adım biçimi: (asama, baslik, aciklama, tur, olcut)
  [2026-11-05] Süre alanı kaldırıldı (kullanıcı kararı): gelişim genel bir süreçtir; süre vermek zorunluluk hissi doğurur.
  tur  : arastirma | gorusme | deneyim | proje | aliskanlik | okuma | kurs | yansitma
  olcut: "Bunu yaptığını nasıl anlarsın?" — somut, kontrol edilebilir bir işaret

Değerler (K1) bir "beceri" değildir: buradaki adımlar değeri değiştirmeyi değil, hedef bölümle
uyumunu sınamayı ve bilinçli karar vermeyi amaçlar.
P4 (duygusal hassasiyet) ters yönlüdür: "gelişim" = stres ve duygu yönetimi.

İçeriği değiştirmek için yalnızca bu dosyayı düzenlemek yeterlidir (veritabanı değişmez).
Adım kodu = "<değişken>-<G|U>-<sıra>" (ör. "P3-G-2"); öğrencinin ilerlemesi bu kodla saklanır,
bu yüzden mevcut adımların SIRASINI değiştirmeyin, yeni adımı sona ekleyin.
"""

ICERIK = {
    # ============================ K1 — DEĞERLER / MOTİVASYON ============================
    "D1": {
        "nedir": "İş güvencesi, düzenli gelir ve öngörülebilir bir hayat düzenine verdiğin önem.",
        "gelisim_neden": "{bolum} alanında güvenceli, kurumsal yollar önemli bir yer tutuyor; sen ise güvenceye daha az önem veriyorsun. Bu bir eksiklik değil. Ama mezun olunca önüne çıkacak işler esneklik beklentinle çatışabilir. Bunu şimdiden sınamak, ileride hayal kırıklığı yaşamanı önler.",
        "guclu_neden": "Güvence ve düzen senin için önemli; {bolum} alanında da benzer ölçüde önemseniyor. Planlı ilerlemek istiyorsan sınav, staj ve kadro gibi adımları erkenden takvime bağlayabilirsin; yine de bu alandaki her kariyer yolunun aynı güvenceyi sunmadığını araştır.",
        "gelisim": [
            ("simdi", "Mezunlar nerede çalışıyor?", "{bolum} mezunlarının ilk 5 yılda hangi kurumlarda (kamu, özel, serbest) çalıştığını araştır. Üniversitelerin mezun takip sayfaları ve LinkedIn bu iş için iyi bir başlangıç.", "arastirma", "En az 5 mezunun kariyer yolunu bir tabloya not ettin."),
            ("simdi", "Kendine 3 soru", "Bir kâğıda yaz: \"İşimi kaybetme riski beni ne kadar rahatsız eder?\", \"Esnek ama belirsiz bir iş mi, sabit ama sıkıcı bir iş mi?\", \"5 yıl sonra nasıl bir düzende yaşamak isterim?\"", "yansitma", "Üç soruya da en az ikişer cümlelik cevap yazdın."),
            ("bu_donem", "Bir mezunla konuş", "{bolum} okumuş birine (aile çevresi, öğretmen, okulun mezunları) ailenin ya da öğretmeninin bilgisiyle ulaş ve işinin ne kadar istikrarlı olduğunu sor. Görüşmeyi okulda, ailenin yanında ya da görüntülü yap; görüşmeden önce 5 soru hazırla.", "gorusme", "Görüşmeyi yaptın ve en önemli 3 bilgiyi not ettin."),
            ("bu_donem", "İki kariyer yolunu karşılaştır", "{bolum} ile girilebilecek bir güvenceli (ör. kamu kadrosu) ve bir esnek (ör. serbest/girişim) yolu yan yana koy: gelir, istikrar, özgürlük ve sana uygunluk açısından puanla.", "arastirma", "İki yolu 1-5 arası puanladığın bir karşılaştırma tablon var."),
            ("uzun_vadede", "Kısa bir iş deneyimi", "Yaz tatilinde ya da hafta sonları kurumsal düzende kısa süreli bir deneyim edin. Bu, okulun yönlendirdiği bir staj, gönüllülük ya da ailenin onayıyla yaşına uygun, yasal izinli hafif bir iş olabilir. Düzenli mesainin sana nasıl hissettirdiğini gözlemle.", "deneyim", "Deneyim sonunda \"bu düzende mutlu olur muyum?\" sorusuna net bir cevabın var."),
            ("uzun_vadede", "B planı oluştur", "Bu bölümün güvenceli yolları sana dar gelirse diye esneklik sağlayacak yan beceriler (dil, sertifika, ikinci uzmanlık) belirle ve hangisine ne zaman başlayacağını planla.", "proje", "Yazılı bir B planın ve ilk adımın tarihi belli."),
        ],
        "guclu": [
            ("simdi", "Güvenceli yolları listele", "{bolum} ile ulaşılabilecek en istikrarlı kariyer yollarını (kamu sınavları, büyük kurumlar, akademi) ve bu yolların giriş şartlarını çıkar.", "arastirma", "En az 3 güvenceli yol ve şartlarını yazdın."),
            ("bu_donem", "Uzun vadeli takvim yap", "Planlı yapını kullan: lise sonundan mezuniyete kadar sınav, staj ve sertifika adımlarını yıllara böl.", "proje", "Yıl yıl adımların yer aldığı bir takvimin var."),
        ],
    },
    "D2": {
        "nedir": "Yüksek gelir, prim ve maddi imkânların kariyer kararlarındaki ağırlığı.",
        "gelisim_neden": "{bolum} alanında çalışanlar genellikle gelir beklentisi yüksek bir ortamda bulunuyor (performans primi, rekabet, kariyer basamağı). Sen maddi getiriyi daha az önemsiyorsun; bu, yoğun rekabet ve hedef baskısı olan ortamlarda motivasyonunu zorlayabilir.",
        "guclu_neden": "Gelir senin için önemli; {bolum} alanında da benzer ölçüde önemseniyor. Bölümün gerçek maaş aralıklarını araştırırsan beklentinle gerçeği karşılaştırıp bilerek karar verebilirsin.",
        "gelisim": [
            ("simdi", "Gerçek maaşları öğren", "{bolum} mezunlarının başlangıç ve 5. yıl maaş aralıklarını araştır (kariyer siteleri, sektör raporları). Ortalamayı ve uç değerleri ayrı not et.", "arastirma", "Başlangıç ve deneyimli maaş için birer aralık yazdın."),
            ("simdi", "Paranın senin için anlamı", "\"Ne kadar kazanırsam rahat ederim?\" sorusuna aylık gider listesi yaparak cevap ver. Bu, gelir beklentini gerçekçi kılar.", "yansitma", "Kendi tahmini aylık ihtiyaç rakamını hesapladın."),
            ("bu_donem", "Rekabetçi ortamı gözlemle", "Bu alanda çalışan birine (aile çevrenden ya da öğretmeninin aracılığıyla, ailenin bilgisiyle) performans hedeflerini, prim sistemini ve iş temposunu sor. Sonra bu temponun seni motive mi edeceğini, yoksa yoracağını mı düşün.", "gorusme", "Görüşmeyi yaptın ve \"Bu tempo bana uygun mu?\" sorusuna yazılı cevap verdin."),
            ("bu_donem", "Parasal olmayan kazanımları bul", "Bu alanda seni maaş dışında ne tatmin eder (öğrenme, itibar, insanlara yardım)? En az 3 madde çıkar ve bölümde bunların karşılığını ara.", "yansitma", "3 kazanım ve her birinin bölümdeki karşılığını yazdın."),
            ("uzun_vadede", "Finansal okuryazarlık", "Bütçe, birikim ve yatırımın temellerini anlatan ücretsiz bir çevrim içi kurs ya da video serisi seç (ör. BTK Akademi gibi ücretsiz platformlar ya da okul kütüphanesinden bir kaynak). Öğrendiklerinle kendi bütçe tablonu yap.", "kurs", "Kursu ya da seriyi bitirdin, öğrendiğin 3 kavramı kendi cümlelerinle yazdın ve bütçe tablonu oluşturdun."),
            ("uzun_vadede", "Değer–gelir dengesi kararı", "Önceki adımlarda bulduklarını gözden geçir: Bu bölümün gelir yapısı seninle uyumlu mu? Değilse hangi alt alan (ör. akademi, kamu, sivil toplum) daha uygun?", "yansitma", "Hedef alt alanını gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Yüksek kazançlı alt alanlar", "{bolum} içinde en yüksek gelir sağlayan uzmanlık ve sektörleri araştır; giriş şartlarını not et.", "arastirma", "En az 3 yüksek gelirli alt alan ve şartlarını listeledin."),
            ("bu_donem", "Değer katan beceriyi seç", "Gelirini artıracak bir ek beceri belirle (yabancı dil, veri analizi, sunum) ve öğrenmeye başla.", "kurs", "Seçtiğin beceride ilk modülü/seviyeyi tamamladın."),
        ],
    },
    "D3": {
        "nedir": "Toplumda saygın, adı bilinen bir meslekte ya da kurumda olma isteği.",
        "gelisim_neden": "{bolum} alanında saygınlık ve unvan, senin için olduğundan daha önemli bir yer tutuyor; bu alandaki bazı yollar (tanınmış kurumlar, unvanlar) bu yönde rekabet içerebilir. Sen statüyü daha az önemsiyorsun. Bu bir eksik değil; ama çevrenin beklentisiyle kendi motivasyonun arasında gerilim yaratabilir.",
        "guclu_neden": "Saygınlık ve tanınırlık senin için önemli; {bolum} alanında da benzer ölçüde önemseniyor. Unvanın yanında günlük işin kendisinin de sana uyup uymadığını sına.",
        "gelisim": [
            ("simdi", "Kimin beklentisi?", "Bu bölümü seçmende \"prestijli\" olmasının ne kadar etkisi var? Ailenin, öğretmenlerinin ve senin beklentini ayrı ayrı yaz.", "yansitma", "Üç tarafın beklentisini ayrı ayrı yazdın."),
            ("simdi", "Günlük işi öğren", "{bolum} mezunlarının sıradan bir iş gününü anlatan 2 video izle ya da 2 röportaj oku; unvanın arkasındaki gerçek işi gör.", "arastirma", "Bir iş gününün 5 ana görevini yazabiliyorsun."),
            ("bu_donem", "Aileyle açık konuşma", "Kendi motivasyonunu (prestijden çok neyi önemsediğini) ailene anlat; onların bu bölümden beklentisini dinle.", "gorusme", "Konuşmayı yaptın ve ortak noktaları not ettin."),
            ("bu_donem", "Prestij dışı kriterler", "Bölüm seçiminde kullanacağın 5 kriteri (ilgi, beceri, iş ortamı, gelir, şehir...) belirle ve hedef bölümü bunlara göre puanla.", "yansitma", "Hedef bölümü 5 kritere göre puanladın."),
            ("uzun_vadede", "Alternatif yol haritası", "Bu bölümün daha az görünür ama sana uygun olabilecek alt alanlarını (araştırma, danışmanlık, sivil toplum) incele.", "arastirma", "En az 2 alternatif alt alanı tanıdın ve not ettin."),
            ("uzun_vadede", "Kararını gözden geçir", "Önceki adımları tamamladıktan sonra tekrar değerlendir: Bu bölümü kendi kriterlerinle de seçer miydin?", "yansitma", "Kararını kendi 5 kriterinle gerekçelendirip yazdın."),
        ],
        "guclu": [
            ("simdi", "Rol modelini bul", "{bolum} alanında saygın bulduğun 2 kişiyi araştır: hangi adımlarla bu noktaya geldiler?", "arastirma", "İki rol modelin kariyer adımlarını not ettin."),
            ("bu_donem", "Görünür bir başarı", "Okulda bu alana yakın bir yarışma, olimpiyat ya da proje (ör. TÜBİTAK 2204) seç ve hazırlığa başla.", "proje", "Başvurunu yaptın ya da hazırlık takvimin hazır."),
        ],
    },
    "D4": {
        "nedir": "Yaptığın işin sana kişisel olarak anlamlı gelmesi ve içsel tatmin sağlaması.",
        "gelisim_neden": "{bolum} alanında çalışanlar işlerinden güçlü bir anlam ve amaç duygusu bekliyor. Senin için anlam şu an daha az belirleyici; uzun ve zorlu bir eğitim sürecinde \"neden bunu yapıyorum?\" sorusunun cevabını bilmek motivasyonunu korur.",
        "guclu_neden": "Yaptığın işin anlamlı olması senin için önemli; {bolum} alanında da benzer ölçüde önemseniyor. Bölümün hangi yönünün sana anlamlı geldiğini netleştirirsen uzmanlık seçerken bunu pusula olarak kullanabilirsin.",
        "gelisim": [
            ("simdi", "\"Neden\" cümleni yaz", "\"{bolum} okumak istiyorum çünkü...\" cümlesini 3 farklı şekilde tamamla. En samimi bulduğunu işaretle.", "yansitma", "Sana en doğru gelen bir \"neden\" cümlen var."),
            ("simdi", "Etkiyi gör", "Bu alanda çalışmış birinin hayat hikâyesini bul (biyografi, röportaj ya da TRT Belgesel gibi bir kanalda bir belgesel). İşinin insanlara ya da dünyaya etkisini ve bu işin ona ne anlam kattığını not et.", "okuma", "Bu kişinin yarattığı bir etkiyi ve işinin ona kattığı anlamı kendi cümlelerinle yazdın."),
            ("bu_donem", "Mezuna anlamı sor", "Bir {bolum} mezununa \"İşinde seni en çok ne tatmin ediyor?\" diye sor.", "gorusme", "Aldığın cevabı not ettin ve sana uyup uymadığını düşündün."),
            ("bu_donem", "Değer haritası", "Hayatta önemli bulduğun 5 şeyi sırala ve her birinin bu bölümde nasıl karşılık bulabileceğini yaz.", "yansitma", "5 değerin bölümdeki karşılığını eşleştirdin."),
            ("uzun_vadede", "Küçük bir anlamlı proje", "Bu alanla ilgili, birine faydası dokunacak küçük bir proje yap (ör. bir konuyu arkadaşlarına anlatan bir sunum, bir okul kulübü etkinliği).", "proje", "Projeyi tamamladın ve sana nasıl hissettirdiğini yazdın."),
            ("uzun_vadede", "Anlam günlüğü", "Bu alana dair seni heyecanlandıran ya da sıkan bir an yaşadığında kısa, tarihli bir not al. Birkaç not biriktiğinde notlarını okuyup tekrar eden şeyleri bul.", "aliskanlik", "En az 6 tarihli notun var ve tekrar eden bir örüntüyü bir cümleyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Anlamlı alt alanını seç", "{bolum} içinde sana en anlamlı gelen alt alanı (ör. çocuklar, çevre, adalet, teknoloji) belirle.", "yansitma", "Bir alt alan seçtin ve nedenini yazdın."),
            ("bu_donem", "Anlamı deneyime çevir", "Seçtiğin alt alanla ilgili, ailenin bilgisiyle yaşına uygun bir gönüllülük ya da gözlem fırsatı bul (ör. okul kulüpleri, belediye ya da yerel dernek etkinlikleri).", "deneyim", "En az bir etkinliğe katıldın ve sana ne kattığını yazdın."),
        ],
    },
    "D5": {
        "nedir": "İnsanlara, topluma ve dünyaya somut fayda sağlama isteği.",
        "gelisim_neden": "{bolum} alanında topluma katkı güçlü bir beklenti; çalışanlar işlerinin insanlara dokunmasından motivasyon alıyor. Senin için bu daha az belirleyici; bu yüzden bu alanın \"hizmet\" yönünün seni ne kadar tatmin edeceğini önceden görmen önemli.",
        "guclu_neden": "Topluma katkı senin için önemli; {bolum} alanında da benzer ölçüde önemseniyor. Bu isteğini küçük ve somut projelerle sınayabilirsin.",
        "gelisim": [
            ("simdi", "Toplumsal etkiyi araştır", "{bolum} mezunlarının topluma katkı sağladığı 3 örnek bul (proje, kurum, kişi).", "arastirma", "3 örneği kısaca not ettin."),
            ("simdi", "Kendi katkı tanımın", "\"Topluma katkı\" senin için ne demek: tek tek insanlara yardım mı, sistemleri iyileştirmek mi, bilgi üretmek mi? Birini seç.", "yansitma", "Sana uyan katkı biçimini seçtin."),
            ("bu_donem", "Tek günlük gönüllülük", "Ailenin bilgisiyle, yaşına uygun bir gönüllülük etkinliğine bir gün katıl (ör. okulun, belediyenin ya da yerel bir derneğin düzenlediği bir etkinlik). Sana nasıl hissettirdiğini gözlemle.", "deneyim", "Etkinliğe katıldın; ne yaptığını ve nasıl hissettiğini anlatan kısa bir değerlendirme yazdın."),
            ("bu_donem", "Hizmet yönünü konuş", "Bu alanda çalışan birine (aile çevrenden ya da öğretmeninin aracılığıyla) işinin \"insanlarla/toplumla\" ilgili kısmının günlük işin ne kadarını oluşturduğunu sor.", "gorusme", "Hizmet yönünün işteki oranını öğrendin."),
            ("uzun_vadede", "Okul içi sosyal proje", "Arkadaşlarınla okulda küçük bir sosyal sorumluluk projesi başlat (kitap toplama, akran mentorluğu, çevre temizliği).", "proje", "Proje en az bir kez hayata geçti."),
            ("uzun_vadede", "Uygunluk kararı", "Deneyimlerinden sonra değerlendir: Bu bölümün hizmet yönü seni tatmin ediyor mu, yoksa daha teknik/bağımsız bir alt alan mı sana uygun?", "yansitma", "Hangi alt alana yöneleceğini gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Etki alanını belirle", "{bolum} ile en çok fark yaratabileceğin toplumsal sorunu seç (ör. eğitim eşitsizliği, sağlık, çevre).", "yansitma", "Bir sorun seçtin ve neden önemli olduğunu yazdın."),
            ("bu_donem", "Düzenli gönüllülük", "Seçtiğin sorunla ilgili bir kurumda, ailenin bilgisiyle ve yaşına uygun şekilde düzenli olarak gönüllü ol.", "deneyim", "En az 3 kez katıldın ve her katılımı tarihiyle not ettin."),
        ],
    },
    "D6": {
        "nedir": "Kendi kararlarını verme, esnek çalışma ve kendi işini kurabilme isteği.",
        "gelisim_neden": "{bolum} alanında çalışanlar genellikle bağımsız karar verme, kendi işini yönetme ya da serbest çalışma bekliyor. Sen daha yapılandırılmış ve yönlendirilen ortamları tercih ediyorsun; bu alandaki bağımsız çalışma biçimlerinin sana uyup uymadığını şimdiden sınamak, kararını netleştirir.",
        "guclu_neden": "Özerklik senin için önemli; {bolum} alanında da benzer ölçüde önemseniyor. Bu alandaki serbest çalışma, danışmanlık ve girişim yollarını araştırıp sana uyanı seçebilirsin.",
        "gelisim": [
            ("simdi", "Kendi başına bir karar", "Normalde başkasına soracağın küçük bir konuda (ders planı, proje konusu) kararı kendin ver ve sonucunu gözlemle.", "aliskanlik", "Kendi verdiğin bir kararı ve sonucunu not ettin."),
            ("simdi", "Bağımsız çalışma biçimlerini öğren", "{bolum} alanında serbest çalışma, danışmanlık ve kurumsal çalışma arasındaki farkları araştır.", "arastirma", "Üç çalışma biçiminin farkını anlatabiliyorsun."),
            ("bu_donem", "Kendi kendine proje", "Kimsenin sana görev vermediği, tamamen kendi planladığın küçük bir proje yap (ör. bir konuda blog, mini araştırma).", "proje", "Projeyi baştan sona kendin planlayıp bitirdin."),
            ("bu_donem", "Çalışma planını kendin kur", "Ders çalışma planını kimseye sormadan kendin hazırla ve uygula. Her planın sonunda neyin işe yaradığını, neyi değiştireceğini yaz.", "aliskanlik", "Kendi hazırladığın en az 3 plan ve her biri için kısa bir değerlendirme var."),
            ("uzun_vadede", "Serbest çalışan biriyle görüş", "Bu alanda bağımsız çalışan biriyle (aile çevrenden ya da öğretmeninin aracılığıyla, ailenin bilgisiyle) konuş: Özgürlüğün getirdiği sorumluluklar neler?", "gorusme", "Bağımsız çalışmanın artı ve eksilerini yazdın."),
            ("uzun_vadede", "Uygun çalışma ortamını seç", "Deneyimlerine göre bu bölümde sana uygun ortamı belirle: yapılandırılmış kurum mu, yarı bağımsız rol mü?", "yansitma", "Tercih ettiğin çalışma ortamını gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Bağımsız yolları keşfet", "{bolum} ile serbest çalışma ya da girişim yapan 2 kişiyi araştır.", "arastirma", "İki bağımsız kariyer örneğini not ettin."),
            ("bu_donem", "Kendi küçük işin", "Ailenin onayıyla ve güvenli çevrende bu alana yakın küçük bir girişim ya da serbest iş dene (ör. küçüklere ders verme, okul için tasarım işi, içerik üretimi).", "deneyim", "İlk işini/müşterini tamamladın."),
        ],
    },
    "D7": {
        "nedir": "Güzellik, tasarım, sanat ve özgün üretimin hayatındaki önemi.",
        "gelisim_neden": "{bolum} alanında estetik ve yaratıcı üretim günlük işin önemli bir parçası. Bu değer senin için daha az belirleyici; görsel ve yaratıcı kısımlarla ne kadar keyifle uğraşabileceğini görmek, bölüm seçimini netleştirir.",
        "guclu_neden": "Estetik ve yaratıcılık senin için önemli; {bolum} alanında da benzer ölçüde önemseniyor. Bölümde yaratıcılığına yer açan alt alanları ve projeleri araştırabilirsin.",
        "gelisim": [
            ("simdi", "Alanın yaratıcı yüzünü gör", "{bolum} alanında yaratıcılığın kullanıldığı 3 örnek iş/proje incele.", "arastirma", "3 örneği kısaca not ettin."),
            ("simdi", "Küçük bir yaratıcı deneme", "Küçük bir yaratıcı iş yap: bir poster, kısa bir sunum tasarımı ya da bir fotoğraf serisi.", "deneyim", "Bir yaratıcı ürün ortaya koydun."),
            ("bu_donem", "Atölye ya da kurs", "Kısa bir tasarım/sanat atölyesine katıl (halk eğitim merkezleri, belediye atölyeleri, çevrim içi kurslar).", "kurs", "Atölyeyi tamamladın."),
            ("bu_donem", "Estetik gözlem alışkanlığı", "Bir süre boyunca sana güzel gelen tasarımları (uygulama, bina, afiş) fotoğrafla ve neden güzel bulduğunu bir cümleyle not et.", "aliskanlik", "En az 10 örnek ve kısa notların var."),
            ("uzun_vadede", "Bölümle ilgili mini tasarım projesi", "Bölümle ilgili bir konuyu görsel olarak anlatan bir ürün hazırla (infografik, maket, sunum).", "proje", "Projeyi bitirdin ve birine gösterdin."),
            ("uzun_vadede", "Uyum değerlendirmesi", "Deneyimlerin sonrasında, bu bölümün yaratıcı kısmından keyif alıp almadığını değerlendir.", "yansitma", "Bu bölümün yaratıcı kısmından keyif alıp almadığını, önceki adımlardan 2 örnekle gerekçelendirip yazdın."),
        ],
        "guclu": [
            ("simdi", "Portfolyo klasörü aç", "Yaptığın yaratıcı işleri bir klasörde topla; düzenli olarak yenilerini ekle.", "aliskanlik", "En az 5 işin bulunduğu bir klasörün var."),
            ("bu_donem", "Bölüme özel yaratıcı proje", "{bolum} ile ilgili bir konuyu yaratıcı bir ürünle anlat ve bir yarışmaya ya da sergiye gönder.", "proje", "Ürünü tamamladın ve bir yerde paylaştın."),
        ],
    },

    # ============================ K2 — KİŞİLİK & ÇALIŞMA TARZI ============================
    "P1": {
        "nedir": "İnsanlarla yüz yüze çalışma, ekipte olma ve sosyal ortamdan enerji alma eğilimi.",
        "gelisim_neden": "{bolum} alanında çalışanlar günün önemli kısmını insanlarla iletişim içinde geçiriyor (ekip toplantıları, sunumlar, müşteri/danışan görüşmeleri). Sen daha içe dönük bir tarza sahipsin; bu bir zayıflık değil ama sosyal durumlarda kendini rahat hissetmeni sağlayacak alışkanlıklar seni güçlendirir.",
        "guclu_neden": "Sosyal enerjin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Bu yönünü ekip çalışmalarında, sunumlarda ve yeni insanlarla tanışırken kullanabilirsin.",
        "gelisim": [
            ("simdi", "Bir sohbet başlat", "Okulda az tanıdığın biriyle ya da bir öğretmeninle ders dışı kısa bir sohbet başlat.", "aliskanlik", "En az 2 yeni sohbet başlattın ve nasıl geçtiğini kısaca not ettin."),
            ("simdi", "Enerji haritanı çıkar", "Hangi sosyal ortamlar seni yoruyor, hangileri dinlendiriyor? Bir sosyal ortamdan çıktığında nasıl hissettiğini kısa bir notla yaz.", "yansitma", "Seni yoran ve dinlendiren ortamları listeledin."),
            ("bu_donem", "Küçük grup sunumu", "Bir derste 3-5 kişilik bir gruba 5 dakikalık bir sunum yap; önceden prova et.", "deneyim", "Sunumu yaptın ve kendine geri bildirim verdin."),
            ("bu_donem", "Bir kulübe katıl", "İlgini çeken bir okul kulübüne katıl ve en az bir etkinlikte görev al.", "deneyim", "Kulüpte en az bir görev üstlendin."),
            ("uzun_vadede", "Düzenli ekip çalışması", "Grup projelerinde aktif bir rol üstlen (toplantı düzenleme, sözcülük) ve bu rolü proje boyunca sürdür.", "proje", "En az bir grup projesinde sözcülük ya da koordinasyon yaptın."),
            ("uzun_vadede", "Kendi tarzını bul", "İçe dönüklüğünü güce çevir: bire bir iletişim, yazılı iletişim ve dinleme gibi güçlü yanlarını bölümde nasıl kullanacağını planla.", "yansitma", "Güçlü iletişim yollarını ve kullanım alanlarını yazdın."),
            ("bu_donem", "İnsanlarla çalışan birini tanı", "{bolum} alanında insanlarla yoğun çalışan birinin röportajını ya da belgeselini izle; ya da aile çevrenden böyle biriyle konuş. İletişimi nasıl öğrendiğini ve onu nelerin yorduğunu öğren.", "gorusme", "Bu kişinin iletişimde kullandığı 3 yöntemi ve birini nasıl deneyeceğini yazdın."),
        ],
        "guclu": [
            ("simdi", "Ağını genişlet", "{bolum} okuyan ya da mezun 2 kişiyle ailenin ya da öğretmeninin bilgisiyle tanış (aile çevresi, okulun rehberlik servisi aracılığıyla okul mezunları).", "gorusme", "İki kişiyle konuştun ve her görüşmeden en az bir not aldın."),
            ("bu_donem", "Liderlik eden sunucu ol", "Okulda bir etkinlikte sunuculuk ya da tanıtım görevi üstlen.", "deneyim", "Bir etkinlikte sahne/sunum görevi yaptın."),
        ],
    },
    "P2": {
        "nedir": "Uzlaşma, empati ve ekip içinde uyum sağlama eğilimi.",
        "gelisim_neden": "{bolum} alanında uyumlu ve işbirlikçi çalışmak önemli bir beklenti; ekipler ortak karar alıyor ve insan ilişkileri işin merkezinde. Sen görüşünü net savunan birisin; bu değerli ama karşındakini anlama ve ortak zemin bulma becerin geliştikçe ekip içindeki etkin artar.",
        "guclu_neden": "İşbirliği ve empati, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Bu yönünle ekipte ortak zemin bulmaya yardım edebilirsin; gerektiğinde \"hayır\" diyebildiğinden de emin ol.",
        "gelisim": [
            ("simdi", "Aktif dinleme denemesi", "Bir tartışmada cevap vermeden önce karşındakinin söylediğini kendi cümlelerinle özetle (\"Yani sen ... diyorsun\").", "aliskanlik", "En az 3 konuşmada bu tekniği kullandın."),
            ("simdi", "Karşı tarafın gözünden", "Son yaşadığın bir anlaşmazlığı karşı tarafın bakış açısından yaz.", "yansitma", "Karşı tarafın gerekçelerini yazabildin."),
            ("bu_donem", "Ortak karar projesi", "Bir grup çalışmasında herkesin fikrini toplayıp ortak bir karar çıkarmayı üstlen.", "proje", "Grup senin yönettiğin bir süreçle karar aldı."),
            ("bu_donem", "Empati üzerine okuma", "Empati ve iletişim üzerine bir kitap ya da makale oku (ör. \"Şiddetsiz İletişim\" – M. Rosenberg).", "okuma", "Okuduğundan 3 uygulanabilir fikir çıkardın."),
            ("uzun_vadede", "Akran destek rolü", "Okulda akran mentorluğu ya da yeni öğrencilere rehberlik gibi bir role gönüllü ol.", "deneyim", "Destek verdiğin her buluşmayı tarihiyle not ettin ve en az 5 buluşmayı tamamladın."),
            ("uzun_vadede", "Dengeyi değerlendir", "Net duruşun ile uyumu nasıl dengelediğini değerlendir: hangi durumlarda esnedin, hangilerinde doğru şekilde direndin?", "yansitma", "İki örnek durum ve değerlendirmesini yazdın."),
            ("bu_donem", "Uzlaşmayı başaran birinin hikâyesi", "Farklı görüşteki insanları bir araya getirmeyi başarmış birinin (bir öğretmen, takım kaptanı, toplum önderi ya da {bolum} alanından biri) hikâyesini oku ya da izle. Zor anlarda nasıl davrandığını incele.", "okuma", "Bu kişinin uzlaşma için yaptığı 3 davranışı ve birini kendi hayatında nasıl deneyeceğini yazdın."),
        ],
        "guclu": [
            ("simdi", "Arabulucu ol", "Bir grup çalışmasında anlaşmazlık çıktığında ortak noktayı bulan kişi olmayı dene.", "deneyim", "Bir anlaşmazlığın çözümüne katkı sağladın."),
            ("bu_donem", "Sınır koyma pratiği", "Uyumlu insanlar bazen fazla yük alır: sana uygun olmayan bir isteğe kibarca \"hayır\" demeyi dene.", "aliskanlik", "En az bir kez gerekçesiyle hayır dedin."),
        ],
    },
    "P3": {
        "nedir": "Planlı çalışma, işleri zamanında bitirme ve görev bilinci.",
        "gelisim_neden": "{bolum} eğitimi ve iş hayatı düzenli, planlı ve sorumlu çalışmayı gerektiriyor (yoğun ders yükü, teslim tarihleri). Planlı çalışma eğilimin bölümün beklediğinden daha düşük; küçük planlama alışkanlıkları edinmek bu alanda işini kolaylaştırır.",
        "guclu_neden": "Planlı ve sorumlu çalışmak, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Bu yönünü uzun vadeli hedeflerine bağlarsan yoğun dönemleri daha rahat geçirebilirsin.",
        "gelisim": [
            ("simdi", "Yapılacaklar listesi", "Önündeki ödev ve çalışmaları bir listeye yaz ve her birine yapacağın günü ata.", "aliskanlik", "Listen hazır ve her işin yanında yapacağın gün yazıyor."),
            ("simdi", "25 dakika kuralı", "Pomodoro tekniğini dene: 25 dakika odaklı çalış, 5 dakika mola ver. Ders çalışırken bu turları kullan.", "aliskanlik", "En az 10 odak turu yaptın ve her çalışmada kaç tur yaptığını not ettin."),
            ("bu_donem", "Takip sistemi kur", "Bir ajanda, takvim ya da uygulama seç ve görevlerini düzenli olarak oraya yaz.", "aliskanlik", "Sistemini en az 15 farklı gün kullandın ve kaçırdığın görevleri işaretledin."),
            ("bu_donem", "Erken teslim hedefi", "Bir sonraki ödevini teslim tarihinden 1 gün önce bitirmeyi hedefle.", "proje", "En az bir ödevi erken teslim ettin."),
            ("uzun_vadede", "Hedeflerini adımlara böl", "3 akademik hedef belirle ve her birini küçük, somut adımlara böl. Bir adımı bitirdiğinde tarihini yaz.", "proje", "3 hedefin ve adımların yazılı; en az 2 hedefe ulaştın ve ulaştığın tarihi not ettin."),
            ("uzun_vadede", "Düzenli gözden geçirme", "Kendine düzenli bir gözden geçirme zamanı seç. 10 dakika ayırıp son günlerde neyi bitirdiğini, neyin aksadığını yaz ve sonraki adımı planla.", "yansitma", "En az 6 tarihli gözden geçirme notun var."),
            ("bu_donem", "Disiplinli birinin yöntemi", "Bir sporcunun, müzisyenin ya da {bolum} alanında başarılı birinin biyografisini ya da röportajını oku. Günlük düzenini nasıl kurduğunu ve isteksiz olduğu günlerde ne yaptığını not et.", "okuma", "Bu kişinin 2 yöntemini yazdın ve birini kendi çalışmana uyguladın."),
        ],
        "guclu": [
            ("simdi", "Uzun vadeli hedef", "{bolum} için YKS hedef netlerini ve bölüm hazırlığını içeren bir yıllık plan yap.", "proje", "Ay ay hedeflerin olan bir planın var."),
            ("bu_donem", "Başkalarına sistem kur", "Planlama becerini bir grup projesinde ekibin iş takvimini hazırlayarak kullan.", "deneyim", "Ekibin senin hazırladığın takvimle çalıştı."),
        ],
    },
    "P4": {
        "nedir": "Stres, kaygı ve duygusal iniş çıkışlara karşı hassasiyet düzeyi.",
        "gelisim_neden": "{bolum} alanında çalışanlar baskı altında sakin kalmayı gerektiren durumlarla sık karşılaşıyor (yoğun sınavlar, kritik kararlar, zor insanlar). Sen strese bölümün beklediğinden daha hassas olabilirsin; bunu yönetmeyi öğrenmek hem başarını hem de iyi oluşunu korur.",
        "guclu_neden": "Strese karşı hassasiyetin {bolum} için beklenen düzeyi aşmıyor. Yoğun dönemlerde sakin kalmanı sağlayan alışkanlıklarını fark edip sürdürmen yeterli.",
        "gelisim": [
            ("simdi", "Nefes tekniği", "Stresli anlarda 4-4-6 nefes tekniğini dene: 4 saniye nefes al, 4 saniye tut, 6 saniyede ver. Sakin anlarda da pratik yap.", "aliskanlik", "En az 7 kez pratik yaptın ve hangi anlarda işine yaradığını not ettin."),
            ("simdi", "Stres tetikleyicilerin", "Seni en çok strese sokan 3 durumu yaz ve her biri için \"o anda ne yapabilirim?\" sorusunu cevapla.", "yansitma", "3 tetikleyici ve çözüm fikrin var."),
            ("bu_donem", "Düzenli hareket", "Sevdiğin bir hareket türünü (yürüyüş, spor, dans) seç ve düzenli olarak 20 dakika yap. Hareketten önce ve sonra kendini nasıl hissettiğini kısaca not et.", "aliskanlik", "En az 10 kez hareket ettin ve her seferini tarihiyle not ettin."),
            ("bu_donem", "Sınav provası", "Deneme sınavlarını gerçek sınav koşullarında (süre, sessizlik) çöz; kaygı seviyeni 1-10 arası not et.", "deneyim", "En az 3 denemede kaygı puanını not ettin ve nasıl değiştiğine baktın."),
            ("uzun_vadede", "Uyku ve rutin", "Okul günlerinde aynı saatte yatıp kalkmayı hedefle; ekranı yatmadan 30 dakika önce bırak.", "aliskanlik", "Rutinine uyduğun geceleri işaretledin ve en az 20 gece uydun."),
            ("uzun_vadede", "Destek almaktan çekinme", "Kaygın günlük hayatını zorluyorsa okulunun rehberlik servisiyle konuş; bu güçlü bir adımdır.", "gorusme", "Gerekli gördüğünde bir rehber öğretmenle görüştün."),
            ("bu_donem", "Heyecanla başa çıkan biri", "Bir sporcunun, sanatçının ya da {bolum} alanında çalışan birinin büyük bir maç, sahne ya da sınav öncesi heyecanını nasıl yönettiğini anlattığı bir röportaj ya da biyografi bul. Ailenden ya da öğretmenlerinden birine de aynı soruyu sorabilirsin.", "okuma", "Bu kişinin kullandığı 2 yöntemi yazdın ve birini kendin denedin."),
        ],
        "guclu": [
            ("simdi", "Sakinliğini fark et", "Son zamanlarda baskı altında sakin kaldığın bir anı yaz: o an ne yaptın?", "yansitma", "Kendi sakin kalma yöntemini tarif edebiliyorsun."),
            ("bu_donem", "Baskılı rolleri dene", "Zaman baskısı olan bir rol üstlen (yarışma, münazara, etkinlik organizasyonu).", "deneyim", "Baskılı bir görevi başarıyla tamamladın."),
        ],
    },
    "P5": {
        "nedir": "Yeni fikirlere, farklı alanlara ve değişen koşullara merak ve açıklık.",
        "gelisim_neden": "{bolum} alanı sürekli gelişiyor; yeni yöntemler, teknolojiler ve bakış açıları öğrenmek işin bir parçası. Yeniliğe açıklığın bölümün beklediğinden daha düşük; merakını küçük adımlarla beslemek, hızla değişen bu alana ayak uydurmanı kolaylaştırır.",
        "guclu_neden": "Merakın ve yeniliğe açıklığın, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Merakını bir konuya odaklarsan yeni şeyleri daha derinlemesine öğrenebilirsin.",
        "gelisim": [
            ("simdi", "Yeni bir konu", "Hiç bilmediğin bir konuda 10 dakikalık bir video izle ya da bir yazı oku. Sonra seni neyin şaşırttığını 2-3 cümleyle yaz.", "okuma", "Seni şaşırtan şeyi yazdın ve yeni konuyu birine 2 cümleyle anlatabildin."),
            ("simdi", "Alandaki yenilikler", "{bolum} alanında son 2 yılda ortaya çıkan bir yeniliği araştır.", "arastirma", "Bir yeniliği ve etkisini not ettin."),
            ("bu_donem", "Meraklı birinin hayatı", "Bir bilim insanının, mucidin ya da {bolum} alanında yeni bir şey denemiş birinin biyografisini oku ya da belgeselini izle. Yeni fikirlere nasıl ulaştığını ve hangi engellerle karşılaştığını yaz.", "okuma", "Bu kişinin yeni fikirlere ulaşma yolunu ve karşılaştığı bir engeli kendi cümlelerinle yazdın."),
            ("bu_donem", "Farklı bir etkinlik", "Daha önce denemediğin bir etkinliğe katıl (bilim şenliği, müze, söyleşi).", "deneyim", "Yeni bir etkinliğe katıldın."),
            ("uzun_vadede", "Çevrim içi kurs", "Bölümle ilgili ama hiç bilmediğin bir konuda kısa bir çevrim içi kurs al.", "kurs", "Kursu tamamladın."),
            ("uzun_vadede", "Okuma alışkanlığı", "Düzenli kitap okumayı alışkanlık edin; alanının dışından da kitaplar seç.", "aliskanlik", "En az 3 kitap bitirdin (en az biri alanının dışından) ve her biri için kısa bir not yazdın."),
        ],
        "guclu": [
            ("simdi", "Merakını odakla", "{bolum} içinde seni en çok meraklandıran bir alt konuyu seç ve derinleş.", "arastirma", "Bir alt konu seçtin ve 3 kaynak buldun."),
            ("bu_donem", "Araştırma projesi", "Seçtiğin konuda küçük bir araştırma yap ve sonucu bir sunum/yazıyla paylaş (ör. TÜBİTAK 2204).", "proje", "Araştırmanı tamamlayıp paylaştın."),
        ],
    },
    "P6": {
        "nedir": "Sabit ve tekrarlayan işler mi, değişken ve sürprizli işler mi tercih ettiğin.",
        "gelisim_neden": "{bolum} alanında iş günü genellikle değişken: her gün farklı görevler, beklenmedik durumlar ve hızlı uyum gerekiyor. Sen rutini tercih ediyorsun; değişime uyum becerini kademeli olarak artırmak bu alanda rahat etmeni sağlar.",
        "guclu_neden": "Değişken ve hareketli işlerden keyif alman, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Hızlı tempolu işlerde bu yönünü kullanabilirsin; rutin ama gerekli işler için de küçük bir düzen kur.",
        "gelisim": [
            ("simdi", "Küçük bir değişiklik", "Rutininde bilinçli bir değişiklik yap (farklı bir çalışma yeri, farklı bir ders sırası) ve nasıl hissettiğini gözlemle.", "aliskanlik", "Değişikliği denedin ve gözlemini yazdın."),
            ("simdi", "Bir iş gününü incele", "{bolum} alanında çalışan birinin sıradan bir gününde ne kadar değişkenlik olduğunu araştır.", "arastirma", "Bir iş gününün sabit ve değişken kısımlarını ayırdın."),
            ("bu_donem", "Plan B alışkanlığı", "Önemli işlerinde \"bu olmazsa ne yaparım?\" sorusuna önceden cevap hazırla.", "aliskanlik", "En az 3 işte yedek planın vardı."),
            ("bu_donem", "Farklı görevler", "Grup çalışmalarında her seferinde farklı bir rol üstlen (araştırmacı, sunucu, tasarımcı).", "deneyim", "En az 2 farklı rol denedin."),
            ("uzun_vadede", "Değişken bir ortam deneyimi", "Etkinlik organizasyonu ya da yaz okulu gibi temposu değişken bir ortamda görev al.", "deneyim", "Değişken bir ortamda görev aldın."),
            ("uzun_vadede", "Uyum değerlendirmesi", "Deneyimlerinden sonra bölümün temposunun sana uygun olup olmadığını, hangi alt alanın daha düzenli olduğunu değerlendir.", "yansitma", "Sana uygun alt alanı gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Dinamik alt alanları bul", "{bolum} içinde en hareketli, proje bazlı çalışılan alt alanları araştır.", "arastirma", "En az 2 dinamik alt alan belirledin."),
            ("bu_donem", "Rutin işleri sisteme bağla", "Sıkıcı bulduğun ama gerekli işler (tekrar, ödev) için sabit bir zaman dilimi belirle.", "aliskanlik", "Rutin işler için belirlediğin zaman dilimini en az 15 kez korudun ve not ettin."),
        ],
    },
    "P7": {
        "nedir": "Kuralların net olmadığı, sonucu belirsiz durumlara tahammül ve risk alma isteği.",
        "gelisim_neden": "{bolum} alanında belirsizlikle çalışmak sık karşılaşılan bir durum: eksik bilgiyle karar vermek, sonucu belli olmayan projeler yürütmek gerekiyor. Belirsizliğe toleransın bölümün beklediğinden daha düşük; küçük ve güvenli risklerle bu kası geliştirebilirsin.",
        "guclu_neden": "Belirsizlikle başa çıkma rahatlığın, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Yeni ve keşfedilmemiş konularda bu yönünü kullanabilirsin; risk almadan önce kısa bir artı-eksi listesi yapmayı alışkanlık edin.",
        "gelisim": [
            ("simdi", "Risk alan birinin hikâyesi", "Belirsiz bir yola çıkmış birinin (bir girişimci, kâşif, sporcu ya da {bolum} alanından biri) biyografisini, röportajını ya da belgeselini incele. Neyi göze aldığını, nasıl hazırlandığını ve işler ters gidince ne yaptığını yaz.", "okuma", "Bu kişinin aldığı bir riski, hazırlığını ve ters giden bir anı nasıl yönettiğini yazdın."),
            ("simdi", "En kötü senaryo", "Seni kaygılandıran bir belirsizlik için \"en kötü ne olabilir, olursa ne yaparım?\" sorusunu yaz.", "yansitma", "En kötü senaryo ve planını yazdın."),
            ("bu_donem", "Cevabı belli olmayan proje", "Sonucu önceden bilinmeyen küçük bir araştırma ya da deney yap.", "proje", "Projeyi bitirdin ve beklenmedik bir sonuçla karşılaştın."),
            ("bu_donem", "Karar günlüğü", "Tüm bilgiye sahip olmadan verdiğin kararları ve sonuçlarını not et.", "aliskanlik", "En az 5 karar ve sonucunu tarihiyle kaydettin."),
            ("uzun_vadede", "Yeni bir ortam", "Hiç bilmediğin bir ortamda yer al: yeni bir kulüp, yeni bir spor, okulun düzenlediği bir gezi ya da ücretsiz bir yaz etkinliği.", "deneyim", "Yeni ortamda yer aldın ve ilk gün ile sonraki bir gün arasındaki rahatlık farkını kısaca yazdın."),
            ("uzun_vadede", "Belirsizlik değerlendirmesi", "Belirsizliğe karşı rahatlığının nasıl değiştiğini ve bölümde hangi alt alanların daha öngörülebilir olduğunu değerlendir.", "yansitma", "Değerlendirmeni yazdın."),
        ],
        "guclu": [
            ("simdi", "Yenilikçi alanları keşfet", "{bolum} içinde henüz yeni gelişen, belirsizliğin yüksek olduğu alanları araştır.", "arastirma", "En az 2 yeni gelişen alan buldun."),
            ("bu_donem", "Hesaplı risk alışkanlığı", "Büyük bir karar öncesi artı/eksi listesi yapmayı alışkanlık edin.", "aliskanlik", "En az 2 kararda artı/eksi listesi kullandın."),
        ],
    },
    "P8": {
        "nedir": "Sorumluluk alma, ekibe yön verme ve karar verici olma isteği.",
        "gelisim_neden": "{bolum} alanında ilerledikçe ekip yönetme, sorumluluk alma ve karar verme beklentisi artıyor. Liderlik isteğin bölümün beklediğinden daha düşük; liderliğin farklı biçimlerini (yönlendirme, örnek olma, organize etme) küçük ölçekte denemek seni hazırlar.",
        "guclu_neden": "Liderlik isteğin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Şimdiden küçük ekiplerde sorumluluk alarak bu yönünü deneyebilirsin.",
        "gelisim": [
            ("simdi", "Küçük bir sorumluluk", "Bir grup çalışmasında küçük bir koordinasyon görevi üstlen (toplantı saati belirlemek, görev dağıtmak).", "deneyim", "Bir koordinasyon görevini tamamladın."),
            ("simdi", "Liderlik türleri", "Farklı liderlik tarzlarını (yönlendiren, destekleyen, örnek olan) araştır. Sonra bir liderin (bir takım kaptanı, tarihî bir kişi ya da {bolum} alanında tanınmış biri) biyografisini ya da röportajını incele ve hangi tarzı kullandığını bul.", "okuma", "İncelediğin liderin tarzını bir örnekle yazdın ve sana en yakın tarzı gerekçesiyle seçtin."),
            ("bu_donem", "Bir etkinlik organize et", "Sınıfta ya da kulüpte küçük bir etkinlik organize et.", "proje", "Etkinlik gerçekleşti."),
            ("bu_donem", "Geri bildirim iste", "Grup arkadaşlarından liderlik ettiğin bir iş hakkında geri bildirim iste.", "gorusme", "En az 2 kişiden geri bildirim aldın."),
            ("uzun_vadede", "Kulüp görevi", "Bir kulüpte yönetim görevi üstlen (başkan yardımcısı, proje sorumlusu).", "deneyim", "Üstlendiğin yönetim görevini sürdürdün ve yaptığın işleri tarihleriyle not ettin."),
            ("uzun_vadede", "Kendi yolunu seç", "Bölümde yönetici mi yoksa uzman mı olarak ilerlemek istediğini değerlendir; ikisi de değerli yollar.", "yansitma", "Tercihini gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Liderlik fırsatı bul", "Okulda başkanlık, kaptanlık ya da proje liderliği gibi bir fırsata başvur.", "deneyim", "Bir liderlik rolüne başvurdun."),
            ("bu_donem", "Dinleyen lider ol", "Yönettiğin bir işte ekipten fikir toplayarak karar alma pratiği yap.", "aliskanlik", "En az bir kararı ekip fikirlerine dayanarak aldın."),
        ],
    },

    # ============================ K3 — İŞ ORTAMI & PROFESYONEL YETKİNLİK ============================
    "I1": {
        "nedir": "Birden fazla işi planlama, öncelik sıralama ve teslim tarihlerini yönetme becerisi.",
        "gelisim_neden": "{bolum} alanında aynı anda birçok iş (dersler, projeler, staj, sınavlar) yürütülüyor ve önceliklendirme başarının anahtarı. Bu becerin alanın beklentisinin altında; birkaç basit teknikle hızla gelişebilir.",
        "guclu_neden": "Zaman yönetimi, senin öne çıkan becerilerinden biri ve {bolum} için beklenen düzeyle uyumlu. Bu beceriyle yoğun dönemlerde bile proje, yarışma ya da kurs gibi fırsatlara yer açabilirsin.",
        "gelisim": [
            ("simdi", "Önemli–acil tablosu", "Önündeki işleri 4 kutuya ayır: önemli-acil, önemli-acil değil, acil-önemsiz, ikisi de değil. Önce ilk kutudan başla.", "aliskanlik", "İşlerini 4 kutuya ayırdığın bir sayfan var ve ilk kutudan bir işi bitirdin."),
            ("simdi", "Zaman takibi", "İki gün boyunca zamanını nereye harcadığını yarım saatlik dilimlerle not et.", "yansitma", "Zamanını en çok neyin aldığını gördün."),
            ("bu_donem", "Günün 3 önceliği", "Her sabah günün en önemli 3 işini seç ve önce onları bitir.", "aliskanlik", "En az 15 farklı gün 3 önceliğini yazdın ve kaçını bitirdiğini işaretledin."),
            ("bu_donem", "Büyük işi böl", "Büyük bir ödevi ya da projeyi küçük parçalara bölüp her parçaya tarih ver.", "proje", "Projeyi parçalara bölerek zamanında bitirdin."),
            ("uzun_vadede", "Sınav dönemi planı", "Bir sonraki sınav dönemi için geriye doğru çalışma takvimi hazırla.", "proje", "Sınav dönemini takvimine uyarak geçirdin."),
            ("uzun_vadede", "Dikkat dağıtıcıları azalt", "Çalışırken telefonu başka odaya koy ya da odak uygulaması kullan; etkisini ölç.", "aliskanlik", "İlk denemendeki ve sonraki bir denemendeki odaklı çalışma sürelerini yazıp karşılaştırdın."),
        ],
        "guclu": [
            ("simdi", "Ek bir hedef ekle", "Zaman yönetimi gücünü kullanarak planına {bolum} ile ilgili ek bir çalışma (kurs, okuma) ekle.", "proje", "Ek çalışmayı planına yerleştirdin ve ilk oturumunu yaptın."),
            ("bu_donem", "Ekibin zaman yöneticisi ol", "Bir grup projesinde iş takvimini sen hazırla ve takip et.", "deneyim", "Proje senin takviminle zamanında bitti."),
        ],
    },
    "I2": {
        "nedir": "Takım içi anlaşmazlıkları çözme ve farklı görüşleri yönetebilme yetkinliği.",
        "gelisim_neden": "{bolum} alanında ekipler farklı görüşlerden insanlarla çalışıyor; anlaşmazlıkları yapıcı şekilde çözmek önemli bir beklenti. Bu becerin bölümün beklediği düzeyin altında; çatışmayı büyümeden yönetmeyi öğrenmek ekip içindeki etkini artırır.",
        "guclu_neden": "Çatışma yönetimi, senin öne çıkan becerilerinden biri ve {bolum} için beklenen düzeyle uyumlu. Ekipte anlaşmazlık çıktığında bu beceriyle çözüme katkı verebilirsin.",
        "gelisim": [
            ("simdi", "Ben dili", "Bir anlaşmazlıkta \"sen hep...\" yerine \"ben ... hissediyorum, çünkü...\" kalıbını kullanmayı dene.", "aliskanlik", "En az 2 kez ben dili kullandın."),
            ("simdi", "Son çatışmayı çözümle", "Son yaşadığın bir anlaşmazlığı yaz: ne oldu, ne istendi, nasıl çözülebilirdi?", "yansitma", "Alternatif bir çözüm yolu yazdın."),
            ("bu_donem", "Kural koyan ekip", "Bir grup çalışmasının başında ekibe birlikte çalışma kuralları önerin (görev dağılımı, karar yöntemi).", "proje", "Ekip senin önerdiğin kurallarla çalıştı."),
            ("bu_donem", "Müzakere üzerine okuma", "Müzakere ve uzlaşma üzerine kısa bir kaynak oku (ör. \"Evet'e Ulaşmak\" – Fisher & Ury).", "okuma", "3 uygulanabilir fikir çıkardın."),
            ("uzun_vadede", "Münazara ya da model BM", "Münazara kulübü ya da Model Birleşmiş Milletler gibi farklı görüşleri yönetmeyi gerektiren bir etkinliğe katıl.", "deneyim", "En az bir etkinlikte aktif rol aldın."),
            ("uzun_vadede", "Arabuluculuk pratiği", "Arkadaşların arasındaki küçük bir anlaşmazlıkta tarafsız dinleyici ol.", "deneyim", "Bir anlaşmazlığın sakinleşmesine katkı sağladın."),
            ("bu_donem", "Bir uzlaşma hikâyesi incele", "İki tarafın anlaşmazlığını konuşarak çözdüğü gerçek bir örneği incele (haber, belgesel ya da biyografi; sporda, okulda ya da {bolum} alanında). Kimin ne istediğini ve orta yolun nasıl bulunduğunu yaz.", "okuma", "Tarafların istediklerini, bulunan çözümü ve senin kullanabileceğin bir dersi yazdın."),
        ],
        "guclu": [
            ("simdi", "Ekip kurallarını sen yaz", "Yeni bir grup çalışmasında ekip için anlaşmazlık çözüm yöntemi öner.", "deneyim", "Ekip önerini benimsedi."),
            ("bu_donem", "Akran arabuluculuğu", "Okulda akran arabuluculuğu (arkadaşlar arasındaki anlaşmazlığı çözmeye yardım etme) ya da öğrenci temsilciliği gibi bir rol üstlen.", "deneyim", "Bir rol üstlendin."),
        ],
    },
    "I3": {
        "nedir": "Stres altında ve eksik bilgiyle bile makul karar verebilme kapasitesi.",
        "gelisim_neden": "{bolum} alanında zaman baskısı altında, tüm bilgiler elinde olmadan karar vermek sık karşılaşılan bir durum. Bu becerin bölümün beklediği düzeyin altında; karar verme yöntemleri ve kontrollü baskı deneyimleriyle güçlenebilir.",
        "guclu_neden": "Baskı altında karar verme, senin öne çıkan becerilerinden biri ve {bolum} için beklenen düzeyle uyumlu. Verdiğin kararları sonradan gözden geçirirsen bu beceriyi daha da işleyebilirsin.",
        "gelisim": [
            ("simdi", "Hızlı karar kuralı", "Küçük kararlar için kendine süre sınırı koy (ör. 2 dakika) ve o sürede karar ver.", "aliskanlik", "En az 5 küçük kararı süre sınırıyla verdin ve not ettin."),
            ("simdi", "Karar sorusu", "Zor bir kararda kendine sor: \"Elimdeki bilgiyle en makul seçenek hangisi, yanılırsam ne olur?\"", "yansitma", "Bu soruyu bir kararında kullandın."),
            ("bu_donem", "Süreli deneme sınavları", "Deneme sınavlarında soru başına süre hedefi koy; takıldığın soruyu bırakıp devam etmeyi öğren.", "deneyim", "En az 3 denemede süreyi yetiştirip yetiştirmediğini ve boş bıraktığın soru sayısını not ettin."),
            ("bu_donem", "Strateji oyunları", "Satranç, zekâ oyunları ya da süreli bulmacalarla düzenli pratik yap. Süre baskısında nasıl karar verdiğine dikkat et.", "aliskanlik", "En az 10 süreli oyun ya da bulmaca oynadın ve süre baskısında nasıl karar verdiğini 2 cümleyle yazdın."),
            ("uzun_vadede", "Kriz senaryosu çalış", "{bolum} alanında yaşanabilecek bir kriz senaryosunu araştır ve \"ben olsam ne yapardım\" diye çözüm yaz.", "proje", "Bir senaryo ve çözüm planın var."),
            ("uzun_vadede", "Karar sonrası değerlendirme", "Verdiğin önemli kararları bir süre sonra gözden geçir: Neyi doğru yaptın, neyi farklı yapardın?", "aliskanlik", "En az 5 karar değerlendirmesi yaptın."),
            ("bu_donem", "Zor anda karar veren biri", "Bir pilotun, doktorun, hakemin ya da {bolum} alanında çalışan birinin zor bir anda nasıl karar verdiğini anlatan bir biyografi, röportaj ya da belgesel bul. Kararı hangi bilgiyle, ne kadar sürede verdiğini incele.", "okuma", "Kişinin kararını 3 adımda yazdın ve senin işine yarayacak bir dersi not ettin."),
        ],
        "guclu": [
            ("simdi", "Zaman baskılı rol", "Yarışma, münazara ya da etkinlik organizasyonu gibi hızlı karar gerektiren bir role gir.", "deneyim", "Bir baskılı rolde görev aldın."),
            ("bu_donem", "Kriz vakası incele", "{bolum} alanında gerçek bir kriz örneğini incele ve alınan kararları değerlendir.", "okuma", "Vakayı ve kendi değerlendirmeni yazdın."),
        ],
    },
    "I4": {
        "nedir": "Adalet, dürüstlük ve etik ilkelere bağlı kalma hassasiyeti.",
        "gelisim_neden": "{bolum} alanında etik ilkeler ve meslek kuralları işin temelinde yer alıyor; dürüstlük ve sorumluluk güçlü bir beklenti. Bu konudaki duyarlılığın bölümün beklediği düzeyin altında; mesleğin etik kurallarını tanımak ve gri durumları tartışmak bu farkındalığı artırır.",
        "guclu_neden": "Etik duyarlılığın, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Bu duyarlılık güvenilir bir meslek insanı olmanın temellerinden biri; ilkelerini esnek çözümlerle nasıl birleştireceğini de öğrenebilirsin.",
        "gelisim": [
            ("simdi", "Meslek etiği kuralları", "{bolum} alanının meslek etiği kurallarını (meslek örgütü yönetmelikleri) araştır ve 3 temel kuralı not et.", "arastirma", "3 etik kuralı kendi cümlelerinle yazdın."),
            ("simdi", "Gri durum düşün", "Doğru ile kolay olanın çatıştığı bir durum hayal et (ör. kopya, hatayı gizleme); ne yapardın ve neden?", "yansitma", "Bir gri durum ve kararını yazdın."),
            ("bu_donem", "Etik vaka tartışması", "Bu alanda yaşanmış bir etik ihlal haberini bul ve bir arkadaşınla ya da öğretmeninle tartış.", "gorusme", "Vakayı tartıştın ve farklı görüşleri not ettin."),
            ("bu_donem", "Söz–eylem tutarlılığı", "Verdiğin küçük sözleri (randevu, ödev, yardım) yaz ve tutup tutmadığını işaretle.", "aliskanlik", "En az 10 sözünü listeledin ve kaçını tuttuğunu işaretledin."),
            ("uzun_vadede", "Dürüstlüğüyle bilinen birinin hikâyesi", "Zor bir durumda doğruyu seçmiş birinin (bir bilim insanı, sporcu, gazeteci ya da {bolum} alanından biri) biyografisini oku ya da hakkındaki bir belgeseli izle. Neyi göze aldığını ve bunun bölümünle bağlantısını yaz.", "okuma", "Kişinin karşılaştığı ikilemi, verdiği kararı ve bölümünle bağlantısını yazdın."),
            ("uzun_vadede", "Kendi ilkelerin", "Meslekte asla yapmayacağın 3 şeyi ve her zaman yapacağın 3 şeyi yaz.", "yansitma", "Kişisel ilke listen hazır."),
        ],
        "guclu": [
            ("simdi", "Etik liderlik", "Grup çalışmalarında adil görev dağılımı ve kaynak gösterme gibi kuralları sen öner.", "deneyim", "Ekip önerdiğin kuralları uyguladı."),
            ("bu_donem", "Esnek ama ilkeli", "Kurallara bağlı kalarak yaratıcı çözüm bulunan bir vaka incele; ilkelerin seni kısıtlamadan nasıl yönlendirebileceğini gör.", "okuma", "Vakayı ve çıkarımını yazdın."),
        ],
    },
    "I5": {
        "nedir": "Beklemeden sorumluluk alma, sorun gördüğünde adım atma (proaktiflik).",
        "gelisim_neden": "{bolum} alanında başarılı olanlar fırsatları kendileri yaratıyor: staj arıyor, proje başlatıyor, soru soruyor. İnisiyatif alma eğilimin bölümün beklediği düzeyin altında; küçük ilk adımları alışkanlık haline getirmek büyük fark yaratır.",
        "guclu_neden": "İnisiyatif alman, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Bu yönünle fırsatları erken fark edebilirsin; enerjini en önemli hedeflerine yöneltmek için öncelik belirlemeyi unutma.",
        "gelisim": [
            ("simdi", "Bir soru sor", "Bir öğretmenine ders dışında, {bolum} hakkında merak ettiğin bir soru sor.", "gorusme", "Soruyu sordun ve cevabı not ettin."),
            ("simdi", "Gördüğün bir sorunu çöz", "Çevrende küçük bir sorun fark et (sınıf düzeni, grup iletişimi) ve çözmek için bir adım at.", "deneyim", "Bir sorunu çözmek için harekete geçtin."),
            ("bu_donem", "İlk adımı atan birinin hikâyesi", "Kimse istemeden bir işe girişmiş birinin (bir girişimci, gönüllü, bilim insanı ya da {bolum} alanından biri) biyografisini, röportajını ya da belgeselini incele. İlk adımı nasıl attığını ve hangi engellerle karşılaştığını yaz.", "okuma", "Kişinin attığı ilk adımı, karşılaştığı bir engeli ve senin deneyebileceğin bir şeyi yazdın."),
            ("simdi", "Seni ne durduruyor?", "Yapmak isteyip başlamadığın 3 şeyi yaz. Her biri için seni durduran şeyi (çekinmek, bilgi eksiği, birinin izin vermesini beklemek) ve atabileceğin en küçük ilk adımı yaz.", "yansitma", "3 iş, her birini durduran neden ve en küçük ilk adım yazılı; en az birinin ilk adımını attın."),
            ("uzun_vadede", "Kendi projeni başlat", "Kimse istemeden, {bolum} ile ilgili kendi projeni başlat (blog, araştırma, kulüp etkinliği).", "proje", "Projen hayata geçti."),
            ("uzun_vadede", "Fırsat listesi", "{bolum} ile ilgili fırsatları (kurs, yarışma, etkinlik) bir listede topla ve aralarından seçip değerlendir.", "aliskanlik", "Listende en az 5 fırsat var ve en az 2'sine başvurdun ya da katıldın."),
        ],
        "guclu": [
            ("simdi", "Büyük bir fırsata başvur", "{bolum} ile ilgili kapsamlı bir fırsata başvur (yaz okulu, bilim olimpiyatı, TÜBİTAK projesi, Teknofest).", "deneyim", "Başvurunu tamamladın."),
            ("bu_donem", "Başkalarını harekete geçir", "Arkadaşlarını da dahil ettiğin bir proje ya da etkinlik başlat.", "proje", "En az 3 kişiyle birlikte bir işi hayata geçirdin."),
        ],
    },
    "I6": {
        "nedir": "Yapıcı eleştiriyi kabul etme, hatadan öğrenme ve savunmaya geçmeme eğilimi.",
        "gelisim_neden": "{bolum} alanında gelişim büyük ölçüde geri bildirimle oluyor: hocalar, yöneticiler ve meslektaşlar işini sürekli değerlendiriyor. Eleştiriye açıklığın bölümün beklediği düzeyin altında; geri bildirimi kişisel algılamadan bir gelişim aracı olarak kullanmayı öğrenmek ilerlemeni hızlandırır.",
        "guclu_neden": "Geri bildirime açıklığın, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Geri bildirimi kendin isteyerek bu yönünü daha çok kullanabilirsin.",
        "gelisim": [
            ("simdi", "Teşekkür et ve dinle", "Bir eleştiri aldığında hemen cevap vermek yerine \"Teşekkürler, biraz düşüneyim\" de. Sonra eleştiride haklı olabilecek bir noktayı yaz.", "aliskanlik", "En az bir eleştiriye savunmaya geçmeden yanıt verdin ve haklı olabilecek bir noktayı not ettin."),
            ("simdi", "Hata günlüğü", "Bir sınavda yaptığın hataları türlerine göre ayır (bilgi eksiği, dikkat, süre).", "yansitma", "Hata türlerini ve en sık olanını belirledin."),
            ("bu_donem", "Geri bildirim iste", "Bir öğretmeninden bir ödevin ya da sunumun için özel geri bildirim iste: \"Neyi daha iyi yapabilirim?\"", "gorusme", "Geri bildirim aldın ve bir maddeyi uyguladın."),
            ("bu_donem", "Yeniden yap", "Geri bildirim aldığın bir çalışmayı düzeltip yeniden hazırla.", "proje", "Çalışmanın geliştirilmiş hâlini tamamladın."),
            ("bu_donem", "Bir otobiyografi oku", "Hayatında başarısızlık, ret ya da sert eleştiriyle karşılaşmış birinin otobiyografisini ya da biyografisini oku (okul ya da halk kütüphanesinden). Eleştiriye ilk tepkisini ve sonra ondan ne öğrendiğini not et.", "okuma", "Kitabı bitirdin; kişinin karşılaştığı bir eleştiriyi, ilk tepkisini ve sonra çıkardığı dersi yazdın."),
            ("uzun_vadede", "Farklı hayatlar, farklı yenilgiler", "Farklı alanlardan 3 kişinin (ör. bir bilim insanı, bir sporcu, bir sanatçı) hayatında yaşadığı bir başarısızlığı araştır. Her biri için ne olduğunu, kimin eleştirdiğini ve nasıl toparlandığını yaz. Sonra kendi hayatından benzer bir anı ekle.", "yansitma", "3 kişinin yenilgi ve toparlanma hikâyesi ile kendi örneğin yazılı."),
            ("bu_donem", "Meslekteki zorlukları incele", "{bolum} alanında tanınmış 2 kişinin kariyerinde yaşadığı ret, hata ya da eleştiri anlarını araştır (röportaj, belgesel, biyografi). İkisinin nasıl toparlandığını karşılaştır.", "arastirma", "İki kişinin yaşadığı zorluğu, aldığı eleştiriyi ve nasıl toparlandığını karşılaştırmalı olarak yazdın."),
        ],
        "guclu": [
            ("simdi", "Geri bildirim döngüsü kur", "Her önemli çalışmandan sonra bir kişiden kısa geri bildirim iste.", "aliskanlik", "En az 3 çalışmanda geri bildirim aldın."),
            ("bu_donem", "Mentor bul", "{bolum} alanında seni yönlendirebilecek bir mentor (üst sınıf öğrencisi, mezun, öğretmen) bul.", "gorusme", "Bir mentorla en az 2 kez görüştün."),
        ],
    },
    "I7": {
        "nedir": "Stratejik düşünme, süreç ve insan yönetimi, ticari ve pazar farkındalığı.",
        "gelisim_neden": "{bolum} alanında işlerin büyük resmini görmek (kurumun hedefleri, maliyet, müşteri, rekabet) önemli bir beklenti. Bu yetkinliğin bölümün beklediği düzeyin altında; iş dünyasını tanımak ve strateji düşüncesini küçük projelerle denemek seni bu alana hazırlar.",
        "guclu_neden": "Stratejik ve ticari farkındalığın, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Bu bakış, ileride yönetim, proje liderliği ya da girişim yollarını değerlendirirken işine yarayabilir.",
        "gelisim": [
            ("simdi", "Bir şirketi tanı", "{bolum} alanında faaliyet gösteren bir şirketin ne sattığını, kime sattığını ve rakiplerini araştır.", "arastirma", "Şirketin iş modelini 3 cümleyle anlatabiliyorsun."),
            ("simdi", "Ekonomi haberi", "Güvenilir bir haber kaynağından bir ekonomi ya da iş dünyası haberi seç. Bölümünle ilişkisini 2-3 cümleyle yaz.", "aliskanlik", "En az 3 haberi bölümünle ilişkilendirip not ettin."),
            ("bu_donem", "Mini iş planı", "Küçük bir iş fikri için basit bir plan hazırla: müşteri, maliyet, fiyat, rakip.", "proje", "Tek sayfalık bir iş planın var."),
            ("bu_donem", "Strateji oyunu ya da simülasyon", "İşletme simülasyonu, strateji oyunu ya da girişimcilik yarışmasına katıl.", "deneyim", "Bir simülasyon ya da yarışmayı tamamladın."),
            ("uzun_vadede", "İş dünyası kursu", "Temel işletme/yönetim üzerine kısa bir çevrim içi kurs al (ör. BTK Akademi).", "kurs", "Kursu tamamladın."),
            ("uzun_vadede", "Yöneticiyle görüş", "Bu alanda yönetici olan biriyle (aile çevrenden ya da öğretmeninin aracılığıyla) konuş: Kararlarını nasıl veriyor, nelere dikkat ediyor?", "gorusme", "Görüşmeden 3 strateji fikri çıkardın."),
            ("bu_donem", "Bir kararı strateji gözüyle yaz", "Okulda, ailende ya da bir kulüpte alınmış bir kararı seç (ör. bir etkinliğin bütçesi, bir kermesin fiyatları). Amacı, seçenekleri, maliyeti ve riskleri yaz. Sen olsan ne yapardın, gerekçesiyle ekle.", "yansitma", "Kararın amacı, en az 2 seçenek, maliyet ve riskler ile kendi tercihin gerekçesiyle yazılı."),
        ],
        "guclu": [
            ("simdi", "Sektör analizi", "{bolum} alanının bulunduğu sektörün geleceğini (fırsatlar, riskler) araştır.", "arastirma", "Kısa bir sektör analizi yazdın."),
            ("bu_donem", "Girişimcilik yarışması", "Bir girişimcilik ya da iş fikri yarışmasına ekip kurarak katıl.", "proje", "Başvurunu yaptın."),
        ],
    },

    # ============================ K4 — ALAN EĞİLİMİ & BİLİŞSEL STİL ============================
    "A1": {
        "nedir": "Matematik, istatistik, veri analizi ve sistem mantığına ilgi ve yatkınlık.",
        "gelisim_neden": "{bolum} eğitimi sayısal düşünme, veri yorumlama ve formül/sistem mantığına dayanıyor. Bu alandaki eğilimin bölümün beklentisinin altında; sayısal konularla düzenli pratik yapmak hem bu alana ilgini sınamanı sağlar hem de bölümdeki sayısal derslerde işini kolaylaştırır.",
        "guclu_neden": "Sayısal ve sistem odaklı düşünme eğilimin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Analitik derslerde bu eğilimini kullanabilir, veri ve programlamaya ilgini de keşfedebilirsin.",
        "gelisim": [
            ("simdi", "Eksik konu tespiti", "Son matematik sınavlarına bakıp en çok zorlandığın 3 konuyu belirle.", "yansitma", "3 öncelikli konun belli."),
            ("simdi", "Günlük 20 dakika", "Düzenli olarak matematik problemi çöz; kolaydan zora ilerle.", "aliskanlik", "En az 7 farklı gün problem çözdün ve her seferinde çözdüğün soru sayısını yazdın."),
            ("bu_donem", "Konu kapatma", "Belirlediğin 3 konuyu sırayla çalış (ör. Khan Academy Türkçe, okul kaynakları) ve her biri için 20 soruluk test çöz.", "kurs", "3 konunun testlerinde başarı oranın arttı."),
            ("bu_donem", "Veriyle küçük proje", "Kendi hayatından bir veri topla (uyku, çalışma süresi) ya da açık bir veri bul (TÜİK, YÖK Atlas). Veriyi tabloya aktar, bir grafik çiz ve grafiğin söylediğini 3 cümleyle yaz.", "proje", "Veri tablon, grafiğin ve 3 cümlelik yorumun hazır."),
            ("uzun_vadede", "Bölümün matematiğini tanı", "{bolum} programında hangi sayısal derslerin olduğunu araştır ve bir tanesinin giriş konusunu incele.", "arastirma", "Bölümün sayısal derslerini ve birinin konusunu biliyorsun."),
            ("uzun_vadede", "Programlamaya giriş", "Sayısal düşünmeyi destekleyecek temel bir programlama kursuna başla (ör. Python, BTK Akademi).", "kurs", "Kursun ilk modüllerini tamamladın."),
        ],
        "guclu": [
            ("simdi", "Olimpiyat ya da yarışma", "Matematik olimpiyatı ya da veri/kodlama yarışmalarını araştır ve birine hazırlanmaya başla.", "deneyim", "Hedef yarışmanı ve hazırlık planını belirledin."),
            ("bu_donem", "Veri bilimi temeli", "Python ile veri analizi üzerine kısa bir kurs al ve {bolum} ile ilgili bir veri seti incele.", "kurs", "Bir veri setini analiz ettin."),
        ],
    },
    "A2": {
        "nedir": "Okuma-yazma, kavramsal düşünme, tartışma ve ikna süreçlerine yatkınlık.",
        "gelisim_neden": "{bolum} alanında yoğun okuma, yazılı anlatım ve argüman kurma önemli bir yer tutuyor. Sözel eğilimin bölümün beklentisinin altında; düzenli okuma ve yazma denemeleri, bu tür çalışmaların sana ne kadar uyduğunu görmeni sağlar.",
        "guclu_neden": "Sözel düşünme ve argüman kurma eğilimin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Rapor yazarken, sunum yaparken ve bir görüşü savunurken bu eğilimini kullanabilirsin.",
        "gelisim": [
            ("simdi", "Günlük 15 sayfa", "Düzenli kitap okuma alışkanlığı edin; ilgini çeken bir türden başla.", "aliskanlik", "En az 7 farklı gün okudun ve okuduğun sayfa sayısını not ettin."),
            ("simdi", "Tek paragraf görüş", "Bir güncel konu hakkında tek paragraflık bir görüş yazısı yaz: iddia, gerekçe, örnek.", "proje", "İddia-gerekçe-örnek yapısında bir paragrafın var."),
            ("bu_donem", "Düzenli yazı", "Farklı konularda yaklaşık 300 kelimelik yazılar yaz. Yazılarından en az birine bir öğretmenden geri bildirim al ve düzelt.", "aliskanlik", "En az 4 yazı yazdın ve en az birini geri bildirimle düzelttin."),
            ("bu_donem", "Münazara ya da kitap kulübü", "Okulun münazara ya da kitap kulübüne katıl.", "deneyim", "En az 2 oturuma aktif katıldın."),
            ("uzun_vadede", "Alan metni oku", "{bolum} alanına ait bir giriş kitabı ya da makale oku ve özetini çıkar.", "okuma", "Bir alan metninin özetini yazdın."),
            ("uzun_vadede", "Kelime dağarcığı", "Okurken bilmediğin kelimeleri bir defterde topla ve düzenli olarak tekrar et.", "aliskanlik", "Defterinde en az 50 kelime ve her biri için bir örnek cümle var."),
            ("bu_donem", "İyi yazan birinin yolu", "Bir yazarın ya da {bolum} alanında iyi yazan/konuşan birinin otobiyografisini, röportajını ya da belgeselini incele. Yazmayı ya da konuşmayı nasıl geliştirdiğini öğren.", "okuma", "Bu kişinin kullandığı 2 yöntemi yazdın ve birini kendi yazında denedin."),
        ],
        "guclu": [
            ("simdi", "Yazı yarışması", "Bir deneme/kompozisyon yarışmasını araştır ve katılmaya karar ver.", "deneyim", "Bir yarışma seçtin."),
            ("bu_donem", "Alanında yaz", "{bolum} ile ilgili bir konuda blog ya da okul dergisi yazısı yayımla.", "proje", "Yazın yayımlandı."),
        ],
    },
    "A3": {
        "nedir": "İnsan davranışı, psikoloji, eğitim ve sosyal hizmet gibi insan merkezli alanlara ilgi.",
        "gelisim_neden": "{bolum} alanı insan davranışını anlamayı ve insanlarla doğrudan çalışmayı gerektiriyor. İnsan odaklı eğilimin bölümün beklentisinin altında; insanları gözlemleme, dinleme ve onlara destek olma deneyimleri bu alana ilgini denemeni ve sana uyup uymadığını görmeni sağlar.",
        "guclu_neden": "İnsan odaklı ilgin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Danışmanlık, eğitim ya da insan kaynakları gibi alt alanları keşfederken bu ilgin sana yol gösterebilir.",
        "gelisim": [
            ("simdi", "İnsan gözlemi", "Okul, kütüphane ya da aile ortamı gibi tanıdık bir yerde insanların nasıl iletişim kurduğunu gözlemle. Kimseyi rahatsız etme, fotoğraf çekme ve isim yazma; yalnızca davranışları not et.", "deneyim", "3 ilginç örüntüyü örnekleriyle not ettin."),
            ("simdi", "Psikolojiye giriş", "Psikoloji ya da insan davranışı üzerine kısa bir video/makale serisi izle.", "okuma", "Öğrendiğin bir kavramı birine anlattın."),
            ("bu_donem", "Akran desteği", "Bir arkadaşına ders konusunda düzenli yardım et.", "deneyim", "En az 4 kez destek verdin."),
            ("bu_donem", "İnsanlarla çalışan biriyle görüş", "Öğretmen, psikolog ya da sosyal hizmet uzmanı biriyle işinin insan yönünü konuş.", "gorusme", "Görüşmeden 3 not çıkardın."),
            ("uzun_vadede", "Gönüllü eğitim", "Ailenin bilgisiyle okulun, belediyenin ya da yerel bir derneğin çocuklara ya da gençlere yönelik bir etkinliğinde gönüllü ol (ör. küçüklere okuma saati, oyun etkinliği).", "deneyim", "En az 2 etkinlikte gönüllü oldun ve her biri hakkında kısa bir not yazdın."),
            ("uzun_vadede", "Uyum değerlendirmesi", "Deneyimlerinden sonra insanlarla yoğun çalışmanın sana enerji mi verdiğini yoksa seni yorduğunu mu değerlendir.", "yansitma", "Değerlendirmeni yazdın."),
        ],
        "guclu": [
            ("simdi", "İnsan odaklı alt alan", "{bolum} içinde insanla en çok temas eden alt alanları araştır.", "arastirma", "En az 2 alt alan belirledin."),
            ("bu_donem", "Akran mentorluğu", "Okulda alt sınıflara yönelik bir mentorluk ya da rehberlik programına katıl.", "deneyim", "Programa katıldın."),
        ],
    },
    "A4": {
        "nedir": "Tasarım, çizim, görsel üretim ve şekil ile konumu zihinde canlandırmaya dayalı (görsel-uzamsal) problem çözme eğilimi.",
        "gelisim_neden": "{bolum} alanında görsel düşünme, tasarım ve uzamsal (şekil ve konumla ilgili) problem çözme önemli bir yer tutuyor. Bu eğilimin bölümün beklentisinin altında; çizim, maket ve dijital tasarım denemeleriyle bu alana ilgini sınayabilirsin.",
        "guclu_neden": "Görsel düşünme ve tasarım eğilimin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Sunumlarda, projelerde ve portfolyonda bu eğilimini kullanabilirsin.",
        "gelisim": [
            ("simdi", "Günlük eskiz", "Düzenli olarak çevrendeki bir nesneyi kısa bir eskizle çiz.", "aliskanlik", "7 eskizin var."),
            ("simdi", "Uzamsal bulmacalar", "3D bulmaca, origami ya da uzamsal zeka (şekilleri zihinde canlandırma) oyunlarıyla pratik yap.", "aliskanlik", "En az 3 bulmaca tamamladın."),
            ("bu_donem", "Dijital tasarım aracı", "Ücretsiz bir tasarım aracı öğren (Canva, Figma, Tinkercad) ve basit bir tasarım yap.", "kurs", "Araçla bir tasarım tamamladın."),
            ("bu_donem", "Maket ya da model", "{bolum} ile ilgili bir yapının ya da nesnenin basit bir maketini yap.", "proje", "Maketin hazır."),
            ("uzun_vadede", "Bir tasarımcının süreci", "Bir mimarın, tasarımcının ya da {bolum} alanında çalışan birinin çalışma sürecini anlatan bir belgesel ya da röportaj izle. Bir fikri eskizden ürüne nasıl taşıdığını adım adım yaz ve bir adımı kendi çalışmanda dene.", "okuma", "Sürecin adımlarını yazdın ve birini kendi tasarımında denedin."),
            ("uzun_vadede", "Portfolyo başlangıcı", "Yaptığın tasarım çalışmalarını tek bir dosyada topla.", "proje", "En az 5 çalışmalık bir portfolyon var."),
        ],
        "guclu": [
            ("simdi", "Portfolyonu düzenle", "En iyi 5 tasarım çalışmanı seç ve açıklamalarıyla bir portfolyo hazırla.", "proje", "Portfolyon hazır."),
            ("bu_donem", "Tasarım yarışması", "{bolum} ile ilgili bir tasarım ya da maket yarışmasına katıl.", "deneyim", "Başvurunu yaptın."),
        ],
    },
    "A5": {
        "nedir": "Biyoloji, kimya, çevre, laboratuvar deneyleri ve saha çalışmalarına ilgi.",
        "gelisim_neden": "{bolum} alanında laboratuvar, deney ve canlılar/doğa üzerine çalışmak eğitimin önemli bir parçası. Bu eğilimin bölümün beklentisinin altında; uygulamalı deneyimler bu alanın sana ne kadar uygun olduğunu netleştirir.",
        "guclu_neden": "Doğa ve laboratuvar ilgin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Araştırma projelerinde ve uygulamalı derslerde bu ilgini değerlendirebilirsin.",
        "gelisim": [
            ("simdi", "Bir bilim insanının hikâyesi", "Doğa, biyoloji ya da kimya alanında çalışmış bir bilim insanının hayatını anlatan bir belgesel izle ya da biyografi oku. Seni şaşırtan 3 bilgiyi ve onun nasıl çalıştığını not et.", "okuma", "Seni şaşırtan 3 bilgiyi ve bu kişinin çalışma biçimini yazdın."),
            ("simdi", "Evde basit deney", "Ailenin gözetiminde, mutfak malzemeleriyle güvenli bir ev deneyi yap (ör. bitki büyütme, kırmızı lahana suyuyla pH deneyi) ve gözlemlerini kaydet.", "deneyim", "Deney günlüğün var."),
            ("bu_donem", "Okul laboratuvarı", "Fen öğretmeninden laboratuvar çalışmalarına daha fazla katılma ya da asistanlık fırsatı iste.", "deneyim", "En az 2 laboratuvar çalışmasına katıldın."),
            ("bu_donem", "Saha gezisi", "Bir botanik bahçesi, müze, araştırma merkezi ya da doğa gezisine katıl.", "deneyim", "Geziye katıldın ve notlarını yazdın."),
            ("uzun_vadede", "Araştırma projesi", "Fen alanında küçük bir araştırma projesi yap (ör. TÜBİTAK 2204 lise projeleri).", "proje", "Proje raporun hazır."),
            ("uzun_vadede", "Yaz bilim okulu", "Üniversitelerin lise öğrencilerine yönelik ücretsiz ya da burslu yaz bilim okullarını araştır ve ailenle birlikte birine başvur.", "deneyim", "Başvurunu yaptın."),
        ],
        "guclu": [
            ("simdi", "Araştırma konusu seç", "{bolum} ile ilgili merak ettiğin bir doğa/laboratuvar sorusunu seç.", "yansitma", "Bir araştırma sorun var."),
            ("bu_donem", "Bilim yarışması", "Seçtiğin soru üzerine bir bilim yarışması projesi hazırla.", "proje", "Proje başvurunu yaptın."),
        ],
    },
    "A6": {
        "nedir": "Spor, beden kullanımı ve sahada aktif olmayı gerektiren işlere yatkınlık.",
        "gelisim_neden": "{bolum} alanında fiziksel aktivite, sahada çalışma ya da beden kullanımı önemli bir yer tutuyor. Bu eğilimin bölümün beklentisinin altında; düzenli hareket ve sahada kısa deneyimler, bu çalışma biçiminin sana uyup uymadığını görmeni sağlar.",
        "guclu_neden": "Fiziksel ve sahaya yönelik eğilimin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Uygulamalı ve sahada geçen işleri keşfederken bu eğilimin sana yol gösterebilir.",
        "gelisim": [
            ("simdi", "Günlük hareket", "Düzenli olarak yürüyüş ya da hafif egzersiz yap.", "aliskanlik", "En az 7 farklı gün hareket ettin ve not ettin."),
            ("simdi", "Sahayı gör", "{bolum} alanında sahada çalışan birinin gününü anlatan bir video izle.", "arastirma", "Saha işinin fiziksel yönlerini not ettin."),
            ("bu_donem", "Bir spor dalı", "Bir spor dalına ya da okul takımına katıl.", "deneyim", "Düzenli antrenmanlara katıldın."),
            ("bu_donem", "Uygulamalı gönüllülük", "Fiziksel çaba gerektiren bir gönüllülük etkinliğine katıl (ağaç dikme, çevre temizliği).", "deneyim", "Etkinliğe katıldın."),
            ("uzun_vadede", "Kondisyon hedefi", "Kendine ulaşabileceğin bir kondisyon hedefi koy (ör. 5 km yürüyüş/koşu) ve küçük adımlarla ilerle.", "aliskanlik", "Hedefine ulaştın ve ulaştığın tarihi not ettin."),
            ("uzun_vadede", "Uyum değerlendirmesi", "Bölümün fiziksel/saha yönünün sana uygun olup olmadığını ve masa başı alt alanları değerlendir.", "yansitma", "Değerlendirmeni yazdın."),
        ],
        "guclu": [
            ("simdi", "Saha ağırlıklı alt alanlar", "{bolum} içinde sahada geçen ya da hareket gerektiren alt alanları araştır.", "arastirma", "En az 2 alt alan belirledin."),
            ("bu_donem", "Takım kaptanlığı", "Sporda ya da saha etkinliğinde sorumluluk al (kaptanlık, organizasyon).", "deneyim", "Bir sorumluluk üstlendin."),
        ],
    },
    "A7": {
        "nedir": "Kuralları net, aşamaları belli, planlı ve sistematik öğrenme/çalışma tarzı.",
        "gelisim_neden": "{bolum} alanında prosedürlere uygun, adım adım ve sistematik çalışmak önemli bir beklenti (protokoller, standartlar, sıralı işlemler). Bu tarza eğilimin bölümün beklentisinin altında; kontrol listeleri ve sıralı çalışma denemeleri, bu tarzın sana uyup uymadığını görmeni sağlar.",
        "guclu_neden": "Sistematik ve adım adım çalışma eğilimin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Dikkatli ve düzenli iş gereken durumlarda bu eğilimini kullanabilirsin.",
        "gelisim": [
            ("simdi", "Kontrol listesi", "Bir ödevi teslim etmeden önce kontrol listesi hazırla ve madde madde işaretle.", "aliskanlik", "Kontrol listesiyle bir iş teslim ettin."),
            ("simdi", "Hatanın kaynağını bul", "Son birkaç ödev ya da sınavında adım atlamaktan ya da dikkatsizlikten kaynaklanan hataları bul. Her birinin hangi adımda olduğunu ve bir dahaki sefere hangi kontrolü ekleyeceğini yaz.", "yansitma", "En az 3 hata, hangi adımda olduğu ve ekleyeceğin kontrol yazılı."),
            ("bu_donem", "Prosedür takibi", "Bir tarif, montaj talimatı ya da deney protokolünü adım atlamadan uygula.", "deneyim", "Bir protokolü eksiksiz uyguladın."),
            ("bu_donem", "Sabit çalışma şablonu", "Her ders için aynı sırayı izle: konu özeti → örnek → soru çözümü → tekrar.", "aliskanlik", "En az 8 çalışma oturumunda şablonu uyguladın ve işaretledin."),
            ("uzun_vadede", "Standartları tanı", "{bolum} alanında kullanılan standartları ve prosedürleri araştır.", "arastirma", "En az 2 standart/prosedürü tanıdın."),
            ("uzun_vadede", "Sistematik proje", "Aşamaları baştan planlanmış bir proje yap ve her aşamayı belgeleyerek ilerle.", "proje", "Aşamaları belgelenmiş bir projen var."),
            ("bu_donem", "Düzenle çalışan birini tanı", "{bolum} alanında ya da prosedürlerle çalışan bir meslekte (eczacı, laborant, muhasebeci gibi) çalışan birinin iş gününü anlatan bir röportaj ya da belgesel izle; ya da aile çevrenden böyle biriyle konuş. Kontrol listelerini neden ve nasıl kullandığını öğren.", "gorusme", "Bu kişinin kullandığı 2 düzen yöntemini yazdın ve birini kendi çalışmana uyarladın."),
        ],
        "guclu": [
            ("simdi", "Süreç tasarla", "Grup projelerinde iş akışını adım adım tasarlayan kişi ol.", "deneyim", "Ekibin senin iş akışınla çalıştı."),
            ("bu_donem", "Kalite kontrol rolü", "{bolum} ile ilgili bir projede kalite kontrol/son kontrol sorumluluğunu üstlen.", "deneyim", "Bir projede son kontrolü yaptın."),
        ],
    },
    "A8": {
        "nedir": "Önce büyük resmi görme, sezgiyle ilerleme ve görsellerle, şemalarla düşünme eğilimi.",
        "gelisim_neden": "{bolum} alanında ayrıntılara boğulmadan büyük resmi görmek, kavramlar arası bağlantı kurmak ve sezgisel çözümler üretmek önemli. Bu eğilimin bölümün beklentisinin altında; zihin haritaları ve bağlantı kurma alıştırmalarıyla bu düşünme biçimini deneyip sana uyup uymadığını görebilirsin.",
        "guclu_neden": "Büyük resmi görme ve sezgisel düşünme eğilimin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Yeni çözümler ararken ve konular arasında bağlantı kurarken bu eğilimini kullanabilirsin.",
        "gelisim": [
            ("simdi", "Zihin haritası", "Bir konuyu çalışmaya başlamadan önce tek sayfalık zihin haritası çıkar.", "aliskanlik", "En az 2 zihin haritası yaptın."),
            ("simdi", "Neden önemli?", "Çalıştığın her konunun başında \"bu konu neden var, neye yarıyor?\" sorusunu yanıtla.", "yansitma", "Konuların amacını tek cümleyle yazabiliyorsun."),
            ("bu_donem", "Bağlantı kur", "Farklı derslerden iki konu arasında bağlantı bul ve bir arkadaşına anlat.", "aliskanlik", "En az 3 disiplinler arası bağlantı kurdun."),
            ("bu_donem", "Şemalarla öğren", "Bir ünitenin tamamını tek bir şema/akış diyagramında özetle.", "proje", "Bir ünite şeman hazır."),
            ("uzun_vadede", "Sistem düşüncesi", "Sistem düşüncesi üzerine bir kaynak oku ve {bolum} ile ilgili bir sistemi çiz.", "okuma", "Bir sistem diyagramın var."),
            ("uzun_vadede", "Büyük soru projesi", "Bölümünle ilgili büyük bir soruya (ör. \"20 yıl sonra bu meslek nasıl olacak?\") yanıt arayan kısa bir yazı hazırla.", "proje", "Yazını tamamladın."),
            ("bu_donem", "Büyük resmi gören birini incele", "Farklı alanlardaki bilgileri birleştirerek yeni bir şey yapmış birinin (bir bilim insanı, girişimci ya da {bolum} alanından biri) hikâyesini oku ya da izle. Farklı bilgileri nasıl bir araya getirdiğini yaz.", "okuma", "Bu kişinin birleştirdiği alanları ve bundan çıkan sonucu bir şemayla ya da 3 cümleyle anlattın."),
        ],
        "guclu": [
            ("simdi", "Strateji rolü", "Grup projelerinde genel çerçeveyi kuran ve hedefi netleştiren kişi ol.", "deneyim", "Projenin çerçevesini sen çizdin."),
            ("bu_donem", "Ayrıntıyla dengele", "Büyük resim gücünü bir kontrol listesiyle dengele; teslimlerde ayrıntıları gözden kaçırma.", "aliskanlik", "Teslimlerinde ayrıntı hatası azaldı."),
        ],
    },
    "A9": {
        "nedir": "Fırsat görme, satış/pazarlık yapma ve risk alarak iş kurma isteği.",
        "gelisim_neden": "{bolum} alanında fırsatları görmek, fikirlerini ikna edici şekilde sunmak ve girişimci bakış önemli bir beklenti. Bu eğilimin bölümün beklentisinin altında; küçük satış/ikna deneyimleri ve girişimcilik etkinlikleri, bu alana ilgini denemeni ve sana uyup uymadığını görmeni sağlar.",
        "guclu_neden": "Girişimcilik ve ikna eğilimin, senin öne çıkan yönlerinden biri ve {bolum} için beklenen düzeyle uyumlu. Kendi işini kurma, satış ya da iş geliştirme yollarını keşfederken bu eğilimin sana yol gösterebilir.",
        "gelisim": [
            ("simdi", "Fikrini 1 dakikada anlat", "Bir fikrini 1 dakikada anlatan kısa bir konuşma hazırla ve bir arkadaşına sun.", "deneyim", "1 dakikalık sunumunu yaptın."),
            ("simdi", "Fırsat avı", "Çevrende çözülmemiş 3 problem bul ve her biri için bir çözüm fikri yaz.", "yansitma", "3 problem ve çözüm fikrin var."),
            ("bu_donem", "Küçük satış deneyimi", "Okul kermesinde ya da bir etkinlikte satış/tanıtım görevi üstlen.", "deneyim", "Satış/tanıtım görevini tamamladın."),
            ("bu_donem", "Girişimcilik kulübü", "Girişimcilik kulübüne ya da genç girişimci programlarına katıl.", "deneyim", "En az 2 etkinliğe katıldın."),
            ("uzun_vadede", "Mini girişim", "Ailenin onayıyla ve güvenli çevrende küçük bir girişim dene (el yapımı ürün, küçüklere ders verme, dijital içerik) ve gelir-gider tablosu tut.", "proje", "İlk satışını yaptın ve tablon hazır."),
            ("uzun_vadede", "İkna becerisi", "İkna ve sunum teknikleri üzerine bir kaynak oku ya da kurs al.", "kurs", "Öğrendiğin 3 tekniği bir sunumda kullandın."),
            ("bu_donem", "Bir girişimcinin hikâyesi", "Türkiye'den ya da dünyadan bir girişimcinin biyografisini, röportajını ya da belgeselini incele. İlk müşterisini nasıl bulduğunu ve hangi başarısızlıkları yaşadığını yaz.", "okuma", "Girişimcinin ilk müşteriyi bulma yolunu ve yaşadığı bir başarısızlıktan çıkardığı dersi yazdın."),
        ],
        "guclu": [
            ("simdi", "Bölümde fırsat", "{bolum} alanında girişim fırsatlarını (yeni şirketler, çözülmemiş sorunlar) araştır.", "arastirma", "En az 2 fırsat alanı belirledin."),
            ("bu_donem", "İş fikri yarışması", "Bir iş fikri ya da girişimcilik yarışmasına katıl.", "proje", "Başvurunu yaptın."),
        ],
    },
}


# [2026-10-17] FAZLALIK açıklamaları: öğrenci bu özellikte hedef bölümün beklediğinden belirgin YÜKSEK.
# Uyum puanı farkın yönüne bakmaz (100 − |öğrenci − bölüm|); fazlalık da uyumu düşürür. Bu yüzden fazlalık
# "güçlü yön" ya da "avantaj" olarak sunulmaz: ne anlama geldiği ve tek bir yönlendirme verilir.
# Değerlerde (D) fazlalık = "bu değer senin için bu alanın tipik çalışanından daha önemli" (karar konusu).
# P4 (kaygı) ters yönlüdür; fazlası "gelişim" metniyle (gelisim_neden) anlatılır, burada yer almaz.
FAZLA_NEDEN = {
    "D1": "Güvence ve düzen senin için {bolum} alanında genellikle olduğundan daha önemli. Bu alandaki her kariyer yolu aynı güvenceyi sunmayabilir. Mezunların hangi kurumlarda, ne kadar güvenceli çalıştığını araştır ve bunun sana yetip yetmeyeceğine karar ver.",
    "D2": "Gelir senin için {bolum} alanında genellikle olduğundan daha önemli. Bu alanda gelir beklentin her zaman karşılanmayabilir. Gerçek maaş aralıklarını araştır ve bunun sana yetip yetmeyeceğine karar ver.",
    "D3": "Saygınlık ve tanınırlık senin için {bolum} alanında genellikle olduğundan daha önemli. Bu alan beklediğin görünürlüğü her zaman sağlamayabilir. Mezunların iş hayatındaki konumunu araştır ve bunun sana yetip yetmeyeceğine karar ver.",
    "D4": "Yaptığın işin anlamlı olması senin için {bolum} alanında genellikle olduğundan daha önemli. Günlük işin bir kısmı bu beklentiyi karşılamayabilir. Bu alanda sana anlamlı gelecek alt alanları araştır ve hangisinin sana uyduğuna karar ver.",
    "D5": "Topluma katkı senin için {bolum} alanında genellikle olduğundan daha önemli. Bu alanın her işi bu isteği doğrudan karşılamayabilir. Bölümün topluma dokunan alt alanlarını araştır ve bunun sana yetip yetmeyeceğine karar ver.",
    "D6": "Özerklik ve özgürlük senin için {bolum} alanında genellikle olduğundan daha önemli. Bu alanda işler çoğu zaman belli kurallar ve hiyerarşi içinde yürür. Serbest çalışma ve girişim yollarının bu alanda ne kadar mümkün olduğunu araştır ve karar ver.",
    "D7": "Estetik ve yaratıcılık senin için {bolum} alanında genellikle olduğundan daha önemli. Bu alanın günlük işi yaratıcılığına her zaman yer açmayabilir. Yaratıcılığını kullanabileceğin alt alanları araştır ve bunun sana yetip yetmeyeceğine karar ver.",
    "P1": "Sosyal enerjin {bolum} için beklenenden fazla. Bu alanda zamanının önemli bir kısmını tek başına ya da küçük gruplarla çalışarak geçirebilirsin. Bu çalışma düzeninin seni zorlayıp zorlamayacağını bir mezuna sorarak sına.",
    "P2": "İşbirliği ve uzlaşma eğilimin {bolum} için beklenenden fazla. Bu alanda zaman zaman net ve rekabetçi bir tutum alman gerekebilir. Fikrini açıkça savunman gereken durumlarda nasıl hissettiğini gözlemle.",
    "P3": "Planlı ve düzenli çalışma eğilimin {bolum} için beklenenden fazla. Bu alanda işler her zaman bir plana göre ilerlemeyebilir. Plan dışı gelişmelere esnek davranmayı küçük denemelerle sına.",
    "P5": "Merakın ve yeniliğe açıklığın {bolum} için beklenenden fazla. Bu alanda işin bir bölümü tekrar eden ve yerleşik yöntemlerle yürüyebilir. Rutin işlerin seni sıkıp sıkmayacağını bir mezuna sorarak sına.",
    "P6": "Dinamik ve değişken işlerden keyif alma eğilimin {bolum} için beklenenden fazla. Bu alanda iş temposu daha düzenli ve öngörülebilir olabilir. Düzenli bir tempoda motivasyonunu nasıl koruyacağını düşün.",
    "P7": "Belirsizliğe toleransın {bolum} için beklenenden fazla. Bu alanda işler çoğu zaman net kurallar ve prosedürlerle yürür. Kurallı bir ortamda kendini nasıl hissedeceğini bir mezuna sorarak sına.",
    "P8": "Liderlik isteğin {bolum} için beklenenden fazla. Bu alanda uzun süre ekibin bir üyesi olarak çalışman gerekebilir. Liderlik isteğini okul kulüpleri ve proje görevleriyle de karşılayabileceğini unutma.",
    "I1": "Zaman yönetimi becerin {bolum} için beklenenden fazla. Bu alanda işler daha esnek bir takvimle ve daha az sıkı planla yürüyebilir. Bu çalışma düzeninin sana uyup uymadığını bir mezuna sorarak sına.",
    "I2": "Çatışma yönetimi becerin {bolum} için beklenenden fazla. Bu alanda bu beceri günlük işin merkezinde olmayabilir. Ekip çalışması ve koordinasyon gerektiren alt alanların sana daha uygun olup olmadığını araştır.",
    "I3": "Baskı altında karar verme becerin {bolum} için beklenenden fazla. Bu alanda işler çoğu zaman hızlı karar gerektirmeyen, planlı bir tempoda yürür. Daha yavaş ve ayrıntılı ilerleyen işlerin seni sıkıp sıkmayacağını düşün.",
    "I4": "Etik duyarlılığın {bolum} için beklenenden fazla. Bu alanda etik ikilemler günlük işin merkezinde olmayabilir. Bu duyarlılığını kullanabileceğin denetim, uyum ya da kamu yararı odaklı alt alanları araştır.",
    "I5": "İnisiyatif alma eğilimin {bolum} için beklenenden fazla. Bu alanda işler çoğu zaman belli talimatlar ve sorumluluk zinciri içinde yürür. Kendi fikrini uygulayamadığın durumlarda nasıl hissedeceğini bir mezuna sorarak sına.",
    "I6": "Geri bildirime açıklığın {bolum} için beklenenden fazla. Bu alanda düzenli geri bildirim her zaman olmayabilir. Kendi gelişimini izlemek için kendine küçük ölçütler koymayı alışkanlık edin.",
    "I7": "Stratejik ve ticari farkındalığın {bolum} için beklenenden fazla. Bu alanda iş ve piyasa bakışı günlük işin merkezinde olmayabilir. Bu bakışını kullanabileceğin yönetim ya da girişim odaklı alt alanları araştır.",
    "A1": "Sayısal ve sistem odaklı düşünme eğilimin {bolum} için beklenenden fazla. Bu alanda bu eğilim günlük işin merkezinde olmayabilir. Sayısal eğilimini kullanabileceğin veri, analiz ya da ölçme odaklı alt alanları araştır.",
    "A2": "Sözel ve argüman kurma eğilimin {bolum} için beklenenden fazla. Bu alanda yazma ve konuşma günlük işin merkezinde olmayabilir. Bu eğilimini kullanabileceğin iletişim, eğitim ya da raporlama odaklı alt alanları araştır.",
    "A3": "İnsanlarla çalışma ilgin {bolum} için beklenenden fazla. Bu alanda insanlarla doğrudan çalışma sınırlı olabilir. Danışmanlık, eğitim ya da ekip yönetimi gibi insanla iç içe alt alanların sana daha uygun olup olmadığını araştır.",
    "A4": "Görsel ve tasarım eğilimin {bolum} için beklenenden fazla. Bu alanda tasarım günlük işin merkezinde olmayabilir. Bu eğilimini kullanabileceğin tasarım ya da görselleştirme odaklı alt alanları araştır.",
    "A5": "Doğa ve laboratuvar ilgin {bolum} için beklenenden fazla. Bu alanda laboratuvar ya da doğa çalışması sınırlı olabilir. Bu ilgini kullanabileceğin araştırma ya da saha odaklı alt alanları araştır.",
    "A6": "Fiziksel ve sahaya yönelik eğilimin {bolum} için beklenenden fazla. Bu alanda işin çoğu masa başında geçebilir. Uzun süre masa başında çalışmanın seni zorlayıp zorlamayacağını bir mezuna sorarak sına.",
    "A7": "Sistematik ve adım adım çalışma eğilimin {bolum} için beklenenden fazla. Bu alanda işler çoğu zaman esnek ve doğaçlama ilerleyebilir. Belirsiz ve değişken işlerde kendini nasıl hissedeceğini düşün.",
    "A8": "Büyük resmi görme ve sezgisel düşünme eğilimin {bolum} için beklenenden fazla. Bu alanda işin çoğu ayrıntılı ve adım adım ilerleyebilir. Ayrıntıya dayalı işlerin seni sıkıp sıkmayacağını bir mezuna sorarak sına.",
    "A9": "Girişimci ve ikna eğilimin {bolum} için beklenenden fazla. Bu alanda satış, ikna ya da iş geliştirme günlük işin merkezinde olmayabilir. Bu eğilimini kullanabileceğin yönetim ya da girişim odaklı alt alanları araştır.",
}

# ============================ [2026-10-09] EK ADIMLAR ============================
# Öz yeterlik ve öz güven, merak ve soru sorma, odaklanma, dijital/bilgi/veri/görsel okuryazarlık,
# kültür ve vatandaşlık okuryazarlığı ile sürdürülebilirlik alanlarında ek adımlar.
# Kaynak: Türkiye Yüzyılı Maarif Modeli beceri çerçevesi (Eğilimler E1.4, E1.5, E2.3, E3.2, E3.4, E3.8, E3.9;
# Okuryazarlık becerileri OB1, OB2, OB4, OB5, OB6, OB7, OB8) ve SCCT öz yeterlik kaynakları (Lent ve ark. 1994).
# Mevcut adımların sırası değişmesin diye her değişkenin listesinin SONUNA eklenir (kodlar G-7, G-8).
_EK_GELISIM = {
    "P8": [
        ("simdi", "Başarı kanıtların", "Son bir yılda zorlanıp yine de başardığın 5 şeyi yaz ve her birinde senin hangi davranışının işe yaradığını belirt. Kendine güven, geçmiş başarılarını fark ettikçe artar.", "yansitma", "5 başarı ve her birinde işe yarayan davranışın yazılı."),
        ("bu_donem", "Gözlemle, sonra dene", "Liderliğini beğendiğin birini (öğretmen, kulüp başkanı, takım kaptanı) bir süre gözlemle. Yaptığı bir davranışı seç ve bir grup çalışmasında kendin dene.", "deneyim", "Gözlem notun ve denediğin davranışın sonucu yazılı."),
    ],
    "P7": [
        ("simdi", "Zorlandığında kendine ne diyorsun?", "Son zorlandığın bir anı hatırla ve o an kafandan geçen cümleyi yaz. Sonra aynı durumda bir arkadaşına söyleyeceğin cesaretlendirici cümleyi yanına yaz.", "yansitma", "İki cümle de yazılı ve ikincisini bir sonraki zorlukta kullanmaya karar verdin."),
        ("bu_donem", "Basamaklı meydan okuma", "Seni biraz zorlayan bir şeyi kolaydan zora 4 basamağa böl (ör. sınıfta soru sormak → kısa yorum yapmak → 1 dakikalık sunum → 5 dakikalık sunum). Bir basamakta rahatlayınca bir sonrakine geç.", "aliskanlik", "4 basamağı yazdın, en az 3'ünü tamamladın ve her birinin tarihini not ettin."),
    ],
    "I5": [
        ("bu_donem", "Okula bir öneri sun", "Okulda iyileştirilebilecek bir şey seç (kütüphane saatleri, kulüp etkinliği, geri dönüşüm), kısa bir öneri hazırla ve ilgili öğretmene ya da okul yönetimine sun.", "deneyim", "Önerini yazılı olarak hazırladın ve ilgili kişiye ilettin."),
    ],
    "P5": [
        ("simdi", "Sorgulayan okur", "Hedef bölümünle ilgili merak ettiğin bir konu seç, hakkında 5 \"neden?\" ya da \"nasıl?\" sorusu yaz ve cevapları en az iki farklı kaynaktan ara. Kaynakların birbirini tutmadığı noktayı not et.", "arastirma", "5 soru, cevapları ve kaynakların farklı şeyler söylediği en az 1 nokta yazılı."),
    ],
    "I1": [
        ("bu_donem", "Zamanını iyi yöneten birini incele", "{bolum} alanında çalışan birinin ya da aile çevrende yoğun işlerle uğraşan birinin gününü nasıl düzenlediğini öğren (röportaj, biyografi ya da yüz yüze kısa bir sohbet). İşine yarayacak 2 yöntemi seç ve dene.", "gorusme", "2 yöntemi yazdın, birini denedin ve nasıl gittiğini not ettin."),
    ],
    "A1": [
        ("bu_donem", "Sayılarla çalışan birini tanı", "{bolum} alanında sayısal düşünmeyi kullanan birinin hayatını anlatan bir biyografi, röportaj ya da belgesel incele; ya da aile çevrenden böyle biriyle konuş. İşinde matematiği nerede kullandığını öğren.", "gorusme", "Bu kişinin işinde matematiği kullandığı 3 örneği yazdın."),
        ("bu_donem", "Veriyle anlat", "Merak ettiğin bir konuda açık bir veri bul (TÜİK, YÖK Atlas, okul verisi), bir tabloya aktar, bir grafik çiz ve grafiğin söylediğini 3 cümleyle yaz.", "proje", "Tablon, grafiğin ve 3 cümlelik yorumun hazır."),
    ],
    "A4": [
        ("bu_donem", "Görseli çözümle", "Bir infografik, reklam afişi ya da veri grafiği seç. Göze ilk ne çarpıyor, hangi renk ve yerleşim seçilmiş, görsel neyi öne çıkarıp neyi gizliyor? Sonra aynı bilgiyi kendi tasarımınla daha açık anlat.", "proje", "Çözümleme notun ve kendi yeniden tasarımın hazır."),
    ],
    "I4": [
        ("simdi", "Dijital izini kontrol et", "Adını bir arama motorunda arat ve sosyal medya hesaplarının kimlere açık olduğunu kontrol et. Bir üniversite ya da işveren bakarsa neyi görür, düşün.", "yansitma", "Hesaplarının gizlilik ayarlarını gözden geçirdin ve değiştirmek istediğin en az 1 şeyi düzelttin."),
        ("bu_donem", "Bir toplumsal sorunu incele", "Çevrende bir sorunu seç (erişilebilirlik, trafik güvenliği, israf). Sorumlu kurumları, mevcut kuralları ve vatandaşların neler yapabileceğini araştır; {bolum} bu soruna nasıl katkı sağlayabilir, yaz.", "arastirma", "Sorun, sorumlu kurumlar, yapılabilecekler ve bölümünün katkısını içeren 1 sayfalık notun hazır."),
    ],
    "A3": [
        ("simdi", "Öteki tarafın gözünden", "Yakın zamanda biriyle anlaşamadığın bir durumu düşün. O kişinin bakış açısını onun ağzından, \"ben\" diliyle 5 cümleyle yaz.", "yansitma", "Karşı tarafın bakışını yargılamadan 5 cümleyle yazdın."),
        ("bu_donem", "Farklı bir hayatı dinle", "Senden farklı bir kültürden, kuşaktan ya da yaşam koşulundan biriyle (büyükanne-büyükbaba, başka şehirden gelen bir arkadaş, bir esnaf) konuş; hayatını, değerlerini ve gençliğini sor.", "gorusme", "Görüşmeyi yaptın; seni şaşırtan 3 şeyi ve ortak noktalarınızı yazdın."),
    ],
    "A5": [
        ("uzun_vadede", "Bu alan bana uyuyor mu?", "Laboratuvar, deney ve gezi deneyimlerinden sonra seni en çok neyin heyecanlandırdığını, neyin sıktığını yaz. Bunun {bolum} için ne anlama geldiğini düşün.", "yansitma", "Heyecanlandıran ve sıkan en az 2 şeyi ve {bolum} için çıkardığın sonucu yazdın."),
        ("bu_donem", "Okulun atık ölçümü", "Sınıfında ya da evinde çıkan atığı (kâğıt, plastik, yemek) türüne göre birkaç kez say ya da tart. Sonuçları tabloya dök ve azaltmak için uygulanabilir 2 öneri yaz.", "proje", "Ölçüm tablon ve 2 önerin hazır."),
    ],
}
for _kod, _adimlar in _EK_GELISIM.items():
    ICERIK[_kod]["gelisim"].extend(_adimlar)


# [2026-11-05] İçerik incelemesi: konusu özelliğe uymayan ya da başka bir adımla örtüşen adımlar listeden KALDIRILDI.
# Kodlar sıraya bağlı olduğu için tuple'lar silinmez (sonraki adımların kodu kaymasın, öğrenci kayıtları doğru adımda kalsın);
# plan bu kodları göstermez. Öğrenci kaldırılmadan önce bu adımla ilgili bir durum kaydetmişse adım onun listesinde kalır.
KALDIRILAN = frozenset({
    "P7-G-7",   # "Zorlandığında kendine ne diyorsun?" — öz konuşma P4'e daha yakın; P7'de yansıtma adımları var
    "P8-G-7",   # "Başarı kanıtların" — genel öz güven çalışması; P8'de yansıtma adımı var
    "I4-G-8",   # "Bir toplumsal sorunu incele" — etikten çok D5 (topluma katkı) konusu
    "A1-G-8",   # "Veriyle anlat" — içeriği A1-G-4 ile birleştirildi
    "A3-G-7",   # "Öteki tarafın gözünden" — P2-G-2 ile aynı alıştırma
    "A5-G-8",   # "Okulun atık ölçümü" — çevre projesi; A5'i G-2, G-3, G-5 daha doğrudan karşılıyor
})


TUR_ETIKET = {
    "arastirma": "Araştırma", "gorusme": "Görüşme", "deneyim": "Deneyim", "proje": "Proje",
    "aliskanlik": "Alışkanlık", "okuma": "Okuma", "kurs": "Kurs", "yansitma": "Kendini değerlendirme",
}
ASAMA_SIRASI = ("simdi", "bu_donem", "uzun_vadede")


def adim_kodu(degisken_kod: str, grup: str, sira: int) -> str:
    """grup: 'G' (gelişim) | 'U' (güçlü yön)"""
    return f"{degisken_kod}-{grup}-{sira}"
