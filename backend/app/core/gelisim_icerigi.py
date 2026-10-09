# -*- coding: utf-8 -*-
"""
Koçluk — detaylı gelişim içeriği (K1-K4, 31 değişken).                       [2026-10-03]

Her değişken için:
  nedir          : Bu özellik ne demek (öğrenci dilinde)
  gelisim_neden  : Öğrenci hedef bölümün beklentisinin ALTINDAYSA neden önemli ({bolum} = hedef bölüm adı)
  guclu_neden    : Öğrenci beklentinin ÜSTÜNDEYSE bu gücü nasıl değerlendirir
  gelisim        : 6 adım — her aşamada 2 adım (simdi = bu hafta, bu_donem = 1-3 ay, uzun_vadede = 6-12 ay)
  guclu          : 2 adım — güçlü yönü hedef bölüm yolunda kullanma

Adım biçimi: (asama, baslik, aciklama, tur, sure, olcut)
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
        "gelisim_neden": "{bolum} mezunlarının çoğu güvenceli, kurumsal yollarda ilerliyor; sen ise güvenceyi pek öncelemiyorsun. Bu bir eksiklik değil ama okuduktan sonra önüne çıkacak iş seçenekleri senin esneklik beklentinle çatışabilir. Bunu şimdiden sınamak, ileride hayal kırıklığını önler.",
        "guclu_neden": "Güvence ve düzen senin için {bolum} alanının ortalamasından da önemli. Planlı ilerleyen biri olarak sınav, staj ve kadro gibi adımları erkenden takvime bağlayabilirsin; ama bu bölümün her kariyer yolunun aynı güvenceyi sunmadığını da bilmelisin.",
        "gelisim": [
            ("simdi", "Mezunlar nerede çalışıyor?", "{bolum} mezunlarının ilk 5 yılda hangi kurumlarda (kamu, özel, serbest) çalıştığını araştır. Üniversitelerin mezun takip sayfaları ve LinkedIn bu iş için iyi bir başlangıç.", "arastirma", "1 saat", "En az 5 mezunun kariyer yolunu bir tabloya not ettin."),
            ("simdi", "Kendine 3 soru", "Bir kâğıda yaz: \"İşimi kaybetme riski beni ne kadar rahatsız eder?\", \"Esnek ama belirsiz bir iş mi, sabit ama sıkıcı bir iş mi?\", \"5 yıl sonra nasıl bir düzende yaşamak isterim?\"", "yansitma", "20 dk", "Üç soruya da en az ikişer cümlelik cevap yazdın."),
            ("bu_donem", "Bir mezunla konuş", "{bolum} okumuş birine (aile çevresi, öğretmen, LinkedIn) ulaş ve işinin ne kadar istikrarlı olduğunu sor. Görüşmeden önce 5 soru hazırla.", "gorusme", "30-45 dk", "Görüşmeyi yaptın ve en önemli 3 bilgiyi not ettin."),
            ("bu_donem", "İki kariyer yolunu karşılaştır", "{bolum} ile girilebilecek bir güvenceli (ör. kamu kadrosu) ve bir esnek (ör. serbest/girişim) yolu yan yana koy: gelir, istikrar, özgürlük ve sana uygunluk açısından puanla.", "arastirma", "1-2 saat", "İki yolu 1-5 arası puanladığın bir karşılaştırma tablon var."),
            ("uzun_vadede", "Kısa bir iş deneyimi", "Yaz tatilinde ya da hafta sonları kurumsal düzende kısa süreli bir işte (staj, yarı zamanlı iş, gönüllülük) çalış ve düzenli mesai sana nasıl hissettiriyor, gözlemle.", "deneyim", "2-4 hafta", "Deneyim sonunda \"bu düzende mutlu olur muyum?\" sorusuna net bir cevabın var."),
            ("uzun_vadede", "B planı oluştur", "Bu bölümü okurken güvence ihtiyacını dengeleyecek yan beceriler (dil, sertifika, ikinci uzmanlık) belirle ve hangisine ne zaman başlayacağını planla.", "proje", "1 dönem", "Yazılı bir B planın ve ilk adımın tarihi belli."),
        ],
        "guclu": [
            ("simdi", "Güvenceli yolları listele", "{bolum} ile ulaşılabilecek en istikrarlı kariyer yollarını (kamu sınavları, büyük kurumlar, akademi) ve bu yolların giriş şartlarını çıkar.", "arastirma", "1 saat", "En az 3 güvenceli yol ve şartlarını yazdın."),
            ("bu_donem", "Uzun vadeli takvim yap", "Planlı yapını kullan: lise sonundan mezuniyete kadar sınav, staj ve sertifika adımlarını yıllara böl.", "proje", "1-2 saat", "Yıl yıl adımların yer aldığı bir takvimin var."),
        ],
    },
    "D2": {
        "nedir": "Yüksek gelir, prim ve maddi imkânların kariyer kararlarındaki ağırlığı.",
        "gelisim_neden": "{bolum} alanında çalışanlar genellikle gelir beklentisi yüksek bir ortamda bulunuyor (performans primi, rekabet, kariyer basamağı). Sen maddi getiriyi daha az önemsiyorsun; bu, yoğun rekabet ve hedef baskısı olan ortamlarda motivasyonunu zorlayabilir.",
        "guclu_neden": "Gelir hedefin {bolum} ortalamasının da üzerinde. Bu güçlü bir itici güç; ama bölümün gerçek maaş aralıklarını bilmezsen beklenti ile gerçek arasında fark oluşabilir. Hedefini rakamlarla netleştirmek seni daha kararlı yapar.",
        "gelisim": [
            ("simdi", "Gerçek maaşları öğren", "{bolum} mezunlarının başlangıç ve 5. yıl maaş aralıklarını araştır (kariyer siteleri, sektör raporları). Ortalamayı ve uç değerleri ayrı not et.", "arastirma", "45 dk", "Başlangıç ve deneyimli maaş için birer aralık yazdın."),
            ("simdi", "Paranın senin için anlamı", "\"Ne kadar kazanırsam rahat ederim?\" sorusuna aylık gider listesi yaparak cevap ver. Bu, gelir beklentini gerçekçi kılar.", "yansitma", "30 dk", "Kendi tahmini aylık ihtiyaç rakamını hesapladın."),
            ("bu_donem", "Rekabetçi ortamı gözlemle", "Bu alanda çalışan birine performans hedefleri, prim sistemi ve iş temposunu sor; bunun seni motive mi edeceğini yoksa yoracağını mı düşün.", "gorusme", "30 dk", "Görüşme sonrası \"bu tempo bana uygun mu\" sorusuna yazılı cevap verdin."),
            ("bu_donem", "Parasal olmayan kazanımları bul", "Bu alanda seni maaş dışında ne tatmin eder (öğrenme, itibar, insanlara yardım)? En az 3 madde çıkar ve bölümde bunların karşılığını ara.", "yansitma", "1 saat", "3 kazanım ve her birinin bölümdeki karşılığını yazdın."),
            ("uzun_vadede", "Finansal okuryazarlık", "Bütçe, birikim ve yatırım temelleri üzerine kısa bir çevrim içi kurs al (ör. BTK Akademi, Khan Academy Türkçe).", "kurs", "4-6 hafta", "Kursu bitirdin ve kendi bütçe tablonu oluşturdun."),
            ("uzun_vadede", "Değer–gelir dengesi kararı", "Bir dönem sonunda bulduklarını gözden geçir: Bu bölümün gelir yapısı seninle uyumlu mu? Değilse hangi alt alan (ör. akademi, kamu, sivil toplum) daha uygun?", "yansitma", "1 saat", "Hedef alt alanını gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Yüksek kazançlı alt alanlar", "{bolum} içinde en yüksek gelir sağlayan uzmanlık ve sektörleri araştır; giriş şartlarını not et.", "arastirma", "1 saat", "En az 3 yüksek gelirli alt alan ve şartlarını listeledin."),
            ("bu_donem", "Değer katan beceriyi seç", "Gelirini artıracak bir ek beceri belirle (yabancı dil, veri analizi, sunum) ve öğrenmeye başla.", "kurs", "1-3 ay", "Seçtiğin beceride ilk modülü/seviyeyi tamamladın."),
        ],
    },
    "D3": {
        "nedir": "Toplumda saygın, adı bilinen bir meslekte ya da kurumda olma isteği.",
        "gelisim_neden": "{bolum} toplumda prestijli görülen bir alan ve bu alandaki birçok yol (iyi kurumlar, unvanlar) prestij odaklı rekabet içeriyor. Sen statüyü daha az önemsiyorsun; bu sağlıklı bir bağımsızlık olabilir ama çevrenin beklentisiyle senin motivasyonun arasında gerilim yaratabilir.",
        "guclu_neden": "Saygınlık ve tanınırlık senin için güçlü bir motivasyon. {bolum} bu ihtiyacı karşılayabilecek bir alan; ama prestijin günlük iş içeriğini gölgelememesi için işin kendisini de sevdiğinden emin olmalısın.",
        "gelisim": [
            ("simdi", "Kimin beklentisi?", "Bu bölümü seçmende \"prestijli\" olmasının ne kadar etkisi var? Ailenin, öğretmenlerinin ve senin beklentini ayrı ayrı yaz.", "yansitma", "20 dk", "Üç tarafın beklentisini ayrı ayrı yazdın."),
            ("simdi", "Günlük işi öğren", "{bolum} mezunlarının sıradan bir iş gününü anlatan 2 video izle ya da 2 röportaj oku; unvanın arkasındaki gerçek işi gör.", "arastirma", "45 dk", "Bir iş gününün 5 ana görevini yazabiliyorsun."),
            ("bu_donem", "Aileyle açık konuşma", "Kendi motivasyonunu (prestijden çok neyi önemsediğini) ailene anlat; onların bu bölümden beklentisini dinle.", "gorusme", "30 dk", "Konuşmayı yaptın ve ortak noktaları not ettin."),
            ("bu_donem", "Prestij dışı kriterler", "Bölüm seçiminde kullanacağın 5 kriteri (ilgi, beceri, iş ortamı, gelir, şehir...) belirle ve hedef bölümü bunlara göre puanla.", "yansitma", "1 saat", "Hedef bölümü 5 kritere göre puanladın."),
            ("uzun_vadede", "Alternatif yol haritası", "Bu bölümün daha az görünür ama sana uygun olabilecek alt alanlarını (araştırma, danışmanlık, sivil toplum) incele.", "arastirma", "2-3 saat", "En az 2 alternatif alt alanı tanıdın ve not ettin."),
            ("uzun_vadede", "Kararını gözden geçir", "Dönem sonunda tekrar değerlendir: Bu bölümü kendi kriterlerinle de seçer miydin?", "yansitma", "30 dk", "Kararını kendi kriterlerinle gerekçelendirdin."),
        ],
        "guclu": [
            ("simdi", "Rol modelini bul", "{bolum} alanında saygın bulduğun 2 kişiyi araştır: hangi adımlarla bu noktaya geldiler?", "arastirma", "1 saat", "İki rol modelin kariyer adımlarını not ettin."),
            ("bu_donem", "Görünür bir başarı", "Okulda bu alana yakın bir yarışma, olimpiyat ya da proje (ör. TÜBİTAK 2204) seç ve hazırlığa başla.", "proje", "1-3 ay", "Başvurunu yaptın ya da hazırlık takvimin hazır."),
        ],
    },
    "D4": {
        "nedir": "Yaptığın işin sana kişisel olarak anlamlı gelmesi ve içsel tatmin sağlaması.",
        "gelisim_neden": "{bolum} alanında çalışanlar işlerinden güçlü bir anlam ve amaç duygusu bekliyor. Senin için anlam şu an daha az belirleyici; uzun ve zorlu bir eğitim sürecinde \"neden bunu yapıyorum?\" sorusunun cevabını bilmek motivasyonunu korur.",
        "guclu_neden": "Anlam arayışın {bolum} ortalamasının da üzerinde; bu, zor dönemlerde seni ayakta tutacak bir güç. Bölümün hangi yönünün sana anlamlı geldiğini netleştirirsen, uzmanlık seçiminde pusulan olur.",
        "gelisim": [
            ("simdi", "\"Neden\" cümleni yaz", "\"{bolum} okumak istiyorum çünkü...\" cümlesini 3 farklı şekilde tamamla. En samimi bulduğunu işaretle.", "yansitma", "15 dk", "Sana en doğru gelen bir \"neden\" cümlen var."),
            ("simdi", "Etkiyi gör", "Bu alanda çalışan birinin yaptığı işin insanlara/dünyaya etkisini anlatan bir hikâye, haber ya da belgesel bul.", "okuma", "30 dk", "Bu alanın yarattığı bir etkiyi kendi cümlelerinle anlatabiliyorsun."),
            ("bu_donem", "Mezuna anlamı sor", "Bir {bolum} mezununa \"İşinde seni en çok ne tatmin ediyor?\" diye sor.", "gorusme", "30 dk", "Aldığın cevabı not ettin ve seninle örtüşüp örtüşmediğini düşündün."),
            ("bu_donem", "Değer haritası", "Hayatta önemli bulduğun 5 şeyi sırala ve her birinin bu bölümde nasıl karşılık bulabileceğini yaz.", "yansitma", "45 dk", "5 değerin bölümdeki karşılığını eşleştirdin."),
            ("uzun_vadede", "Küçük bir anlamlı proje", "Bu alanla ilgili, birine faydası dokunacak küçük bir proje yap (ör. bir konuyu arkadaşlarına anlatan bir sunum, bir okul kulübü etkinliği).", "proje", "1-2 ay", "Projeyi tamamladın ve sana nasıl hissettirdiğini yazdın."),
            ("uzun_vadede", "Anlam günlüğü", "Bir ay boyunca, bu alana dair seni heyecanlandıran ya da sıkan anları haftada bir not et.", "aliskanlik", "4 hafta", "4 haftalık notun var ve bir örüntü fark ettin."),
        ],
        "guclu": [
            ("simdi", "Anlamlı alt alanını seç", "{bolum} içinde sana en anlamlı gelen alt alanı (ör. çocuklar, çevre, adalet, teknoloji) belirle.", "yansitma", "20 dk", "Bir alt alan seçtin ve nedenini yazdın."),
            ("bu_donem", "Anlamı deneyime çevir", "Seçtiğin alt alanla ilgili bir gönüllülük ya da gözlem fırsatı bul (ör. TEGV, TOG, yerel dernekler).", "deneyim", "1-3 ay", "En az bir etkinliğe katıldın."),
        ],
    },
    "D5": {
        "nedir": "İnsanlara, topluma ve dünyaya somut fayda sağlama isteği.",
        "gelisim_neden": "{bolum} alanında topluma katkı güçlü bir beklenti; çalışanlar işlerinin insanlara dokunmasından motivasyon alıyor. Senin için bu daha az belirleyici; bu yüzden bu alanın \"hizmet\" yönünün seni ne kadar tatmin edeceğini önceden görmen önemli.",
        "guclu_neden": "Topluma katkı isteğin {bolum} ortalamasının da üzerinde. Bu, bölümü okurken seni motive edecek; enerjini erken yaşta somut projelere dönüştürürsen hem deneyim hem de güçlü bir hikâye kazanırsın.",
        "gelisim": [
            ("simdi", "Toplumsal etkiyi araştır", "{bolum} mezunlarının topluma katkı sağladığı 3 örnek bul (proje, kurum, kişi).", "arastirma", "45 dk", "3 örneği kısaca not ettin."),
            ("simdi", "Kendi katkı tanımın", "\"Topluma katkı\" senin için ne demek: tek tek insanlara yardım mı, sistemleri iyileştirmek mi, bilgi üretmek mi? Birini seç.", "yansitma", "15 dk", "Sana uyan katkı biçimini seçtin."),
            ("bu_donem", "Tek günlük gönüllülük", "Bir sivil toplum etkinliğine bir gün katıl (ör. Kızılay, TEGV, LÖSEV, yerel belediye etkinlikleri) ve sana nasıl hissettirdiğini gözlemle.", "deneyim", "1 gün", "Etkinliğe katıldın ve kısa bir değerlendirme yazdın."),
            ("bu_donem", "Hizmet yönünü konuş", "Bu alanda çalışan birine işinin \"insanlarla/toplumla\" kısmının günlük işin ne kadarını oluşturduğunu sor.", "gorusme", "30 dk", "Hizmet yönünün işteki oranını öğrendin."),
            ("uzun_vadede", "Okul içi sosyal proje", "Arkadaşlarınla okulda küçük bir sosyal sorumluluk projesi başlat (kitap toplama, akran mentorluğu, çevre temizliği).", "proje", "2-3 ay", "Proje en az bir kez hayata geçti."),
            ("uzun_vadede", "Uygunluk kararı", "Deneyimlerinden sonra değerlendir: Bu bölümün hizmet yönü seni tatmin ediyor mu, yoksa daha teknik/bağımsız bir alt alan mı sana uygun?", "yansitma", "30 dk", "Hangi alt alana yöneleceğini gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Etki alanını belirle", "{bolum} ile en çok fark yaratabileceğin toplumsal sorunu seç (ör. eğitim eşitsizliği, sağlık, çevre).", "yansitma", "20 dk", "Bir sorun seçtin ve neden önemli olduğunu yazdın."),
            ("bu_donem", "Düzenli gönüllülük", "Seçtiğin sorunla ilgili bir kurumda ayda en az bir kez gönüllü ol.", "deneyim", "3 ay", "En az 3 kez katıldın."),
        ],
    },
    "D6": {
        "nedir": "Kendi kararlarını verme, esnek çalışma ve kendi işini kurabilme isteği.",
        "gelisim_neden": "{bolum} alanında çalışanlar genellikle bağımsız karar verme, kendi işini yönetme ya da serbest çalışma bekliyor. Sen daha yapılandırılmış ve yönlendirilen ortamları tercih ediyorsun; bu alanın bağımsızlık gerektiren anlarına hazırlanmak işini kolaylaştırır.",
        "guclu_neden": "Özerklik ihtiyacın {bolum} ortalamasının da üzerinde. Bu alanda serbest çalışma, danışmanlık ya da girişim yollarını erken keşfedersen bu gücünü kariyerine dönüştürebilirsin.",
        "gelisim": [
            ("simdi", "Kendi başına bir karar", "Bu hafta, normalde başkasına soracağın küçük bir konuda (ders planı, proje konusu) kararı kendin ver ve sonucunu gözlemle.", "aliskanlik", "1 hafta", "Kendi verdiğin bir kararın sonucunu not ettin."),
            ("simdi", "Bağımsız çalışma biçimlerini öğren", "{bolum} alanında serbest çalışma, danışmanlık ve kurumsal çalışma arasındaki farkları araştır.", "arastirma", "45 dk", "Üç çalışma biçiminin farkını anlatabiliyorsun."),
            ("bu_donem", "Kendi kendine proje", "Kimsenin sana görev vermediği, tamamen kendi planladığın küçük bir proje yap (ör. bir konuda blog, mini araştırma).", "proje", "1 ay", "Projeyi baştan sona kendin planlayıp bitirdin."),
            ("bu_donem", "Haftalık planını kendin kur", "Ders çalışma planını bir ay boyunca kendin hazırla; her hafta sonunda ne işe yaradığını değerlendir.", "aliskanlik", "4 hafta", "4 haftalık planın ve değerlendirmen var."),
            ("uzun_vadede", "Serbest çalışan biriyle görüş", "Bu alanda bağımsız çalışan biriyle konuş: Özgürlüğün getirdiği sorumluluklar neler?", "gorusme", "30 dk", "Bağımsız çalışmanın artı ve eksilerini yazdın."),
            ("uzun_vadede", "Uygun çalışma ortamını seç", "Deneyimlerine göre bu bölümde sana uygun ortamı belirle: yapılandırılmış kurum mu, yarı bağımsız rol mü?", "yansitma", "30 dk", "Tercih ettiğin çalışma ortamını gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Bağımsız yolları keşfet", "{bolum} ile serbest çalışma ya da girişim yapan 2 kişiyi araştır.", "arastirma", "1 saat", "İki bağımsız kariyer örneğini not ettin."),
            ("bu_donem", "Kendi küçük işin", "Bu alana yakın küçük bir girişim ya da serbest iş dene (ör. ders verme, tasarım işi, içerik üretimi).", "deneyim", "1-3 ay", "İlk işini/müşterini tamamladın."),
        ],
    },
    "D7": {
        "nedir": "Güzellik, tasarım, sanat ve özgün üretimin hayatındaki önemi.",
        "gelisim_neden": "{bolum} alanında estetik ve yaratıcı üretim günlük işin önemli bir parçası. Bu değer senin için daha az belirleyici; görsel ve yaratıcı kısımlarla ne kadar keyifle uğraşabileceğini görmek, bölüm seçimini netleştirir.",
        "guclu_neden": "Estetik ve yaratıcılık senin için {bolum} ortalamasından da önemli. Bu farkı bölümde öne çıkmak için kullanabilirsin: tasarım odaklı projeler ve portfolyo seni ayırt eder.",
        "gelisim": [
            ("simdi", "Alanın yaratıcı yüzünü gör", "{bolum} alanında yaratıcılığın kullanıldığı 3 örnek iş/proje incele.", "arastirma", "45 dk", "3 örneği kısaca not ettin."),
            ("simdi", "Küçük bir yaratıcı deneme", "Bu hafta küçük bir yaratıcı iş yap: bir poster, kısa bir sunum tasarımı ya da bir fotoğraf serisi.", "deneyim", "1-2 saat", "Bir yaratıcı ürün ortaya koydun."),
            ("bu_donem", "Atölye ya da kurs", "Kısa bir tasarım/sanat atölyesine katıl (halk eğitim merkezleri, belediye atölyeleri, çevrim içi kurslar).", "kurs", "1-2 ay", "Atölyeyi tamamladın."),
            ("bu_donem", "Estetik gözlem alışkanlığı", "İki hafta boyunca sana güzel gelen tasarımları (uygulama, bina, afiş) fotoğrafla ve nedenini not et.", "aliskanlik", "2 hafta", "En az 10 örnek ve kısa notların var."),
            ("uzun_vadede", "Bölümle ilgili mini tasarım projesi", "Bölümle ilgili bir konuyu görsel olarak anlatan bir ürün hazırla (infografik, maket, sunum).", "proje", "1-2 ay", "Projeyi bitirdin ve birine gösterdin."),
            ("uzun_vadede", "Uyum değerlendirmesi", "Deneyimlerin sonrasında, bu bölümün yaratıcı kısmından keyif alıp almadığını değerlendir.", "yansitma", "30 dk", "Kararını yazdın."),
        ],
        "guclu": [
            ("simdi", "Portfolyo klasörü aç", "Yaptığın yaratıcı işleri bir klasörde topla; düzenli olarak yenilerini ekle.", "aliskanlik", "30 dk", "En az 5 işin bulunduğu bir klasörün var."),
            ("bu_donem", "Bölüme özel yaratıcı proje", "{bolum} ile ilgili bir konuyu yaratıcı bir ürünle anlat ve bir yarışmaya ya da sergiye gönder.", "proje", "1-3 ay", "Ürünü tamamladın ve bir yerde paylaştın."),
        ],
    },

    # ============================ K2 — KİŞİLİK & ÇALIŞMA TARZI ============================
    "P1": {
        "nedir": "İnsanlarla yüz yüze çalışma, ekipte olma ve sosyal ortamdan enerji alma eğilimi.",
        "gelisim_neden": "{bolum} alanında çalışanlar günün önemli kısmını insanlarla iletişim içinde geçiriyor (ekip toplantıları, sunumlar, müşteri/danışan görüşmeleri). Sen daha içe dönük bir tarza sahipsin; bu bir zayıflık değil ama sosyal durumlarda kendini rahat hissetmeni sağlayacak alışkanlıklar seni güçlendirir.",
        "guclu_neden": "Sosyal enerjin {bolum} ortalamasının da üzerinde. Bu, ekip çalışmalarında, sunumlarda ve ağ kurmada sana avantaj sağlar.",
        "gelisim": [
            ("simdi", "Bir sohbet başlat", "Bu hafta okulda az tanıdığın biriyle ya da bir öğretmeninle ders dışı kısa bir sohbet başlat.", "aliskanlik", "1 hafta", "En az 2 yeni sohbet başlattın."),
            ("simdi", "Enerji haritanı çıkar", "Hangi sosyal ortamlar seni yoruyor, hangileri dinlendiriyor? Bir hafta boyunca not al.", "yansitma", "1 hafta", "Seni yoran ve dinlendiren ortamları listeledin."),
            ("bu_donem", "Küçük grup sunumu", "Bir derste 3-5 kişilik bir gruba 5 dakikalık bir sunum yap; önceden prova et.", "deneyim", "2-3 hafta", "Sunumu yaptın ve kendine geri bildirim verdin."),
            ("bu_donem", "Bir kulübe katıl", "İlgini çeken bir okul kulübüne katıl ve en az bir etkinlikte görev al.", "deneyim", "1-3 ay", "Kulüpte en az bir görev üstlendin."),
            ("uzun_vadede", "Düzenli ekip çalışması", "Bir dönem boyunca grup projelerinde aktif rol al (toplantı düzenleme, sözcülük).", "proje", "1 dönem", "En az bir grup projesinde sözcülük ya da koordinasyon yaptın."),
            ("uzun_vadede", "Kendi tarzını bul", "İçe dönüklüğünü güce çevir: bire bir iletişim, yazılı iletişim ve dinleme gibi güçlü yanlarını bölümde nasıl kullanacağını planla.", "yansitma", "30 dk", "Güçlü iletişim yollarını ve kullanım alanlarını yazdın."),
        ],
        "guclu": [
            ("simdi", "Ağını genişlet", "{bolum} okuyan ya da mezun 2 kişiyle tanış (aile çevresi, sosyal medya, okul mezunları).", "gorusme", "1-2 hafta", "İki kişiyle tanıştın ve iletişim bilgilerini kaydettin."),
            ("bu_donem", "Liderlik eden sunucu ol", "Okulda bir etkinlikte sunuculuk ya da tanıtım görevi üstlen.", "deneyim", "1-2 ay", "Bir etkinlikte sahne/sunum görevi yaptın."),
        ],
    },
    "P2": {
        "nedir": "Uzlaşma, empati ve ekip içinde uyum sağlama eğilimi.",
        "gelisim_neden": "{bolum} alanında uyumlu ve işbirlikçi çalışmak önemli bir beklenti; ekipler ortak karar alıyor ve insan ilişkileri işin merkezinde. Sen görüşünü net savunan birisin; bu değerli ama karşındakini anlama ve ortak zemin bulma becerin geliştikçe ekip içindeki etkin artar.",
        "guclu_neden": "İşbirliği ve empati gücün {bolum} ortalamasının da üzerinde. Bu, ekiplerde güvenilen bir arabulucu olmanı sağlar; yalnızca gerektiğinde \"hayır\" diyebildiğinden emin ol.",
        "gelisim": [
            ("simdi", "Aktif dinleme denemesi", "Bu hafta bir tartışmada cevap vermeden önce karşındakinin söylediğini kendi cümlelerinle özetle (\"Yani sen ... diyorsun\").", "aliskanlik", "1 hafta", "En az 3 konuşmada bu tekniği kullandın."),
            ("simdi", "Karşı tarafın gözünden", "Son yaşadığın bir anlaşmazlığı karşı tarafın bakış açısından yaz.", "yansitma", "20 dk", "Karşı tarafın gerekçelerini yazabildin."),
            ("bu_donem", "Ortak karar projesi", "Bir grup çalışmasında herkesin fikrini toplayıp ortak bir karar çıkarmayı üstlen.", "proje", "2-4 hafta", "Grup senin yönettiğin bir süreçle karar aldı."),
            ("bu_donem", "Empati üzerine okuma", "Empati ve iletişim üzerine bir kitap ya da makale oku (ör. \"Şiddetsiz İletişim\" – M. Rosenberg).", "okuma", "3-4 hafta", "Okuduğundan 3 uygulanabilir fikir çıkardın."),
            ("uzun_vadede", "Akran destek rolü", "Okulda akran mentorluğu ya da yeni öğrencilere rehberlik gibi bir role gönüllü ol.", "deneyim", "1 dönem", "Bir dönem boyunca düzenli destek verdin."),
            ("uzun_vadede", "Dengeyi değerlendir", "Net duruşun ile uyumu nasıl dengelediğini değerlendir: hangi durumlarda esnedin, hangilerinde doğru şekilde direndin?", "yansitma", "30 dk", "İki örnek durum ve değerlendirmesini yazdın."),
        ],
        "guclu": [
            ("simdi", "Arabulucu ol", "Bir grup çalışmasında anlaşmazlık çıktığında ortak noktayı bulan kişi olmayı dene.", "deneyim", "2-4 hafta", "Bir anlaşmazlığın çözümüne katkı sağladın."),
            ("bu_donem", "Sınır koyma pratiği", "Uyumlu insanlar bazen fazla yük alır: bu ay sana uygun olmayan bir isteğe kibarca \"hayır\" demeyi dene.", "aliskanlik", "1 ay", "En az bir kez gerekçesiyle hayır dedin."),
        ],
    },
    "P3": {
        "nedir": "Planlı çalışma, işleri zamanında bitirme ve görev bilinci.",
        "gelisim_neden": "{bolum} eğitimi ve iş hayatı düzenli, planlı ve sorumluluk bilinci yüksek çalışmayı gerektiriyor (yoğun ders yükü, teslim tarihleri, hata kabul etmeyen işler). Planlama alışkanlıkların geliştikçe bu alandaki başarın belirgin şekilde artar.",
        "guclu_neden": "Disiplin ve sorumluluk gücün {bolum} ortalamasının da üzerinde. Bu, yoğun bir eğitim sürecinde en büyük avantajlarından biri; bu gücü uzun vadeli hedeflere bağlarsan fark yaratırsın.",
        "gelisim": [
            ("simdi", "Haftalık plan", "Bu haftanın ödev ve çalışmalarını bir listeye yaz, her birine gün ata.", "aliskanlik", "15 dk", "Haftalık listen var ve her işin bir günü belli."),
            ("simdi", "25 dakika kuralı", "Pomodoro tekniğini dene: 25 dakika odaklı çalış, 5 dakika mola ver. Günde en az 2 tur yap.", "aliskanlik", "1 hafta", "5 gün boyunca günde en az 2 tur yaptın."),
            ("bu_donem", "Takip sistemi kur", "Bir ajanda, takvim ya da uygulama seç ve bir ay boyunca tüm görevlerini oraya yaz.", "aliskanlik", "4 hafta", "4 hafta boyunca sistemini aksatmadan kullandın."),
            ("bu_donem", "Erken teslim hedefi", "Bir sonraki ödevini teslim tarihinden 1 gün önce bitirmeyi hedefle.", "proje", "2-3 hafta", "En az bir ödevi erken teslim ettin."),
            ("uzun_vadede", "Dönemlik hedef planı", "Bu dönem için 3 akademik hedef belirle ve her birini aylık adımlara böl.", "proje", "1 dönem", "Dönem sonunda hedeflerinin en az 2'sine ulaştın."),
            ("uzun_vadede", "Haftalık gözden geçirme", "Her pazar 10 dakika ayırıp geçen haftayı değerlendir ve yeni haftayı planla.", "aliskanlik", "3 ay", "En az 10 haftalık gözden geçirme yaptın."),
        ],
        "guclu": [
            ("simdi", "Uzun vadeli hedef", "{bolum} için YKS hedef netlerini ve bölüm hazırlığını içeren bir yıllık plan yap.", "proje", "1 saat", "Ay ay hedeflerin olan bir planın var."),
            ("bu_donem", "Başkalarına sistem kur", "Planlama becerini bir grup projesinde ekibin iş takvimini hazırlayarak kullan.", "deneyim", "1 ay", "Ekibin senin hazırladığın takvimle çalıştı."),
        ],
    },
    "P4": {
        "nedir": "Stres, kaygı ve duygusal iniş çıkışlara karşı hassasiyet düzeyi.",
        "gelisim_neden": "{bolum} alanında çalışanlar baskı altında sakin kalmayı gerektiren durumlarla sık karşılaşıyor (yoğun sınavlar, kritik kararlar, zor insanlar). Sen strese bu alanın ortalamasına göre daha hassas olabilirsin; bunu yönetmeyi öğrenmek hem başarını hem de iyi oluşunu korur.",
        "guclu_neden": "Strese karşı dayanıklılığın {bolum} ortalamasının da üzerinde. Bu, yoğun ve baskılı dönemlerde sakin kalmanı sağlar; çevrendekilere de destek olabilirsin.",
        "gelisim": [
            ("simdi", "Nefes tekniği", "Stresli anlarda 4-4-6 nefes tekniğini dene: 4 saniye nefes al, 4 saniye tut, 6 saniyede ver. Günde bir kez pratik yap.", "aliskanlik", "1 hafta", "Bir hafta boyunca her gün pratik yaptın."),
            ("simdi", "Stres tetikleyicilerin", "Seni en çok strese sokan 3 durumu yaz ve her biri için \"o anda ne yapabilirim?\" sorusunu cevapla.", "yansitma", "20 dk", "3 tetikleyici ve çözüm fikrin var."),
            ("bu_donem", "Düzenli hareket", "Haftada en az 3 kez 20 dakikalık yürüyüş, spor ya da dans gibi bir hareket alışkanlığı edin.", "aliskanlik", "4 hafta", "4 hafta boyunca haftada 3 kez hareket ettin."),
            ("bu_donem", "Sınav provası", "Deneme sınavlarını gerçek sınav koşullarında (süre, sessizlik) çöz; kaygı seviyeni 1-10 arası not et.", "deneyim", "1-2 ay", "En az 3 denemede kaygı puanının düştüğünü gördün."),
            ("uzun_vadede", "Uyku ve rutin", "Hafta içi aynı saatte yatıp kalkmayı hedefle; ekranı yatmadan 30 dakika önce bırak.", "aliskanlik", "2-3 ay", "En az 6 hafta düzenli uyku rutini sürdürdün."),
            ("uzun_vadede", "Destek almaktan çekinme", "Kaygın günlük hayatını zorluyorsa okulunun rehberlik servisiyle konuş; bu güçlü bir adımdır.", "gorusme", "ihtiyaç halinde", "Gerekli gördüğünde bir rehber öğretmenle görüştün."),
        ],
        "guclu": [
            ("simdi", "Sakinliğini fark et", "Son zamanlarda baskı altında sakin kaldığın bir anı yaz: o an ne yaptın?", "yansitma", "15 dk", "Kendi sakin kalma yöntemini tarif edebiliyorsun."),
            ("bu_donem", "Baskılı rolleri dene", "Zaman baskısı olan bir rol üstlen (yarışma, münazara, etkinlik organizasyonu).", "deneyim", "1-2 ay", "Baskılı bir görevi başarıyla tamamladın."),
        ],
    },
    "P5": {
        "nedir": "Yeni fikirlere, farklı alanlara ve değişen koşullara merak ve açıklık.",
        "gelisim_neden": "{bolum} alanı sürekli gelişiyor; yeni yöntemler, teknolojiler ve bakış açıları öğrenmek işin bir parçası. Yeniliğe açıklığın bu alanın ortalamasının altında; merakını küçük adımlarla beslemek, hızla değişen bu alanda geride kalmamanı sağlar.",
        "guclu_neden": "Merakın ve yeniliğe açıklığın {bolum} ortalamasının da üzerinde. Bu seni hızlı öğrenen ve yeni fikirler üreten biri yapar; merakını derinleştirmek için bir konuya odaklanmayı da unutma.",
        "gelisim": [
            ("simdi", "Haftanın yeni konusu", "Bu hafta hiç bilmediğin bir konuda 10 dakikalık bir video izle ya da bir yazı oku.", "okuma", "10-15 dk", "Yeni konuyu birine 2 cümleyle anlatabildin."),
            ("simdi", "Alandaki yenilikler", "{bolum} alanında son 2 yılda ortaya çıkan bir yeniliği araştır.", "arastirma", "30 dk", "Bir yeniliği ve etkisini not ettin."),
            ("bu_donem", "Haftalık merak listesi", "Bir ay boyunca her hafta merak ettiğin bir soruyu yaz ve cevabını araştır.", "aliskanlik", "4 hafta", "4 soru ve cevabından oluşan bir listen var."),
            ("bu_donem", "Farklı bir etkinlik", "Daha önce denemediğin bir etkinliğe katıl (bilim şenliği, müze, söyleşi).", "deneyim", "1 ay", "Yeni bir etkinliğe katıldın."),
            ("uzun_vadede", "Çevrim içi kurs", "Bölümle ilgili ama hiç bilmediğin bir konuda kısa bir çevrim içi kurs al.", "kurs", "1-2 ay", "Kursu tamamladın."),
            ("uzun_vadede", "Okuma alışkanlığı", "Ayda bir kitap hedefle; alanın dışından da seç.", "aliskanlik", "3 ay", "3 kitap okudun."),
        ],
        "guclu": [
            ("simdi", "Merakını odakla", "{bolum} içinde seni en çok meraklandıran bir alt konuyu seç ve derinleş.", "arastirma", "1 saat", "Bir alt konu seçtin ve 3 kaynak buldun."),
            ("bu_donem", "Araştırma projesi", "Seçtiğin konuda küçük bir araştırma yap ve sonucu bir sunum/yazıyla paylaş (ör. TÜBİTAK 2204).", "proje", "2-3 ay", "Araştırmanı tamamlayıp paylaştın."),
        ],
    },
    "P6": {
        "nedir": "Sabit ve tekrarlayan işler mi, değişken ve sürprizli işler mi tercih ettiğin.",
        "gelisim_neden": "{bolum} alanında iş günü genellikle değişken: her gün farklı görevler, beklenmedik durumlar ve hızlı uyum gerekiyor. Sen rutini tercih ediyorsun; değişime uyum becerini kademeli olarak artırmak bu alanda rahat etmeni sağlar.",
        "guclu_neden": "Dinamik ve değişken işlerden keyif alma eğilimin {bolum} ortalamasının da üzerinde. Bu, hızlı tempolu ortamlarda sana avantaj sağlar; rutin ama gerekli işleri de aksatmamak için küçük sistemler kur.",
        "gelisim": [
            ("simdi", "Küçük bir değişiklik", "Bu hafta rutininde bilinçli bir değişiklik yap (farklı bir çalışma yeri, farklı bir ders sırası) ve nasıl hissettiğini gözlemle.", "aliskanlik", "1 hafta", "Değişikliği denedin ve gözlemini yazdın."),
            ("simdi", "Bir iş gününü incele", "{bolum} alanında çalışan birinin sıradan bir gününde ne kadar değişkenlik olduğunu araştır.", "arastirma", "30 dk", "Bir iş gününün sabit ve değişken kısımlarını ayırdın."),
            ("bu_donem", "Plan B alışkanlığı", "Önemli işlerinde \"bu olmazsa ne yaparım?\" sorusuna önceden cevap hazırla.", "aliskanlik", "4 hafta", "En az 3 işte yedek planın vardı."),
            ("bu_donem", "Farklı görevler", "Grup çalışmalarında her seferinde farklı bir rol üstlen (araştırmacı, sunucu, tasarımcı).", "deneyim", "1-2 ay", "En az 2 farklı rol denedin."),
            ("uzun_vadede", "Değişken bir ortam deneyimi", "Etkinlik organizasyonu ya da yaz okulu gibi temposu değişken bir ortamda görev al.", "deneyim", "1-2 hafta", "Değişken bir ortamda görev aldın."),
            ("uzun_vadede", "Uyum değerlendirmesi", "Deneyimlerinden sonra bölümün temposunun sana uygun olup olmadığını, hangi alt alanın daha düzenli olduğunu değerlendir.", "yansitma", "30 dk", "Sana uygun alt alanı gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Dinamik alt alanları bul", "{bolum} içinde en hareketli, proje bazlı çalışılan alt alanları araştır.", "arastirma", "45 dk", "En az 2 dinamik alt alan belirledin."),
            ("bu_donem", "Rutin işleri sisteme bağla", "Sıkıcı bulduğun ama gerekli işler (tekrar, ödev) için sabit bir zaman dilimi belirle.", "aliskanlik", "1 ay", "Rutin işler için sabit zaman dilimini 4 hafta korudun."),
        ],
    },
    "P7": {
        "nedir": "Kuralların net olmadığı, sonucu belirsiz durumlara tahammül ve risk alma isteği.",
        "gelisim_neden": "{bolum} alanında belirsizlikle çalışmak sık karşılaşılan bir durum: eksik bilgiyle karar vermek, sonucu belli olmayan projeler yürütmek gerekiyor. Belirsizliğe toleransın bu alanın ortalamasının altında; küçük ve güvenli risklerle bu kası geliştirebilirsin.",
        "guclu_neden": "Belirsizliğe toleransın {bolum} ortalamasının da üzerinde. Bu, yeni ve keşfedilmemiş alanlarda öncü olmanı sağlayabilir; risklerini hesaplı almak için küçük bir değerlendirme alışkanlığı edin.",
        "gelisim": [
            ("simdi", "Küçük risk", "Bu hafta sonucundan emin olmadığın küçük bir adım at (derste soru sormak, yeni bir yemek denemek, bir kulübe başvurmak).", "aliskanlik", "1 hafta", "En az bir küçük risk aldın ve sonucunu not ettin."),
            ("simdi", "En kötü senaryo", "Seni kaygılandıran bir belirsizlik için \"en kötü ne olabilir, olursa ne yaparım?\" sorusunu yaz.", "yansitma", "15 dk", "En kötü senaryo ve planını yazdın."),
            ("bu_donem", "Cevabı belli olmayan proje", "Sonucu önceden bilinmeyen küçük bir araştırma ya da deney yap.", "proje", "1 ay", "Projeyi bitirdin ve beklenmedik bir sonuçla karşılaştın."),
            ("bu_donem", "Karar günlüğü", "Bir ay boyunca eksik bilgiyle verdiğin kararları ve sonuçlarını not et.", "aliskanlik", "4 hafta", "En az 5 karar ve sonucunu kaydettin."),
            ("uzun_vadede", "Yeni bir ortam", "Hiç bilmediğin bir ortamda yer al: yaz kampı, değişim programı, yeni bir spor.", "deneyim", "1-2 hafta", "Yeni ortamda bir süre geçirdin."),
            ("uzun_vadede", "Belirsizlik değerlendirmesi", "Belirsizliğe karşı rahatlığının nasıl değiştiğini ve bölümde hangi alt alanların daha öngörülebilir olduğunu değerlendir.", "yansitma", "30 dk", "Değerlendirmeni yazdın."),
        ],
        "guclu": [
            ("simdi", "Yenilikçi alanları keşfet", "{bolum} içinde henüz yeni gelişen, belirsizliğin yüksek olduğu alanları araştır.", "arastirma", "45 dk", "En az 2 yeni gelişen alan buldun."),
            ("bu_donem", "Hesaplı risk alışkanlığı", "Büyük bir karar öncesi artı/eksi listesi yapmayı alışkanlık edin.", "aliskanlik", "1 ay", "En az 2 kararda artı/eksi listesi kullandın."),
        ],
    },
    "P8": {
        "nedir": "Sorumluluk alma, ekibe yön verme ve karar verici olma isteği.",
        "gelisim_neden": "{bolum} alanında ilerledikçe ekip yönetme, sorumluluk alma ve karar verme beklentisi artıyor. Liderlik isteğin bu alanın ortalamasının altında; liderliğin farklı biçimlerini (yönlendirme, örnek olma, organize etme) küçük ölçekte denemek seni hazırlar.",
        "guclu_neden": "Liderlik isteğin {bolum} ortalamasının da üzerinde. Bu, ileride ekip ve proje yönetiminde öne çıkmanı sağlar; şimdiden küçük ekiplerde deneyim kazanmaya başlayabilirsin.",
        "gelisim": [
            ("simdi", "Küçük bir sorumluluk", "Bu hafta bir grup çalışmasında küçük bir koordinasyon görevi üstlen (toplantı saati belirlemek, görev dağıtmak).", "deneyim", "1 hafta", "Bir koordinasyon görevini tamamladın."),
            ("simdi", "Liderlik türleri", "Farklı liderlik tarzlarını (yönlendiren, destekleyen, örnek olan) araştır ve sana en yakın olanı seç.", "okuma", "30 dk", "Sana uyan liderlik tarzını gerekçesiyle seçtin."),
            ("bu_donem", "Bir etkinlik organize et", "Sınıfta ya da kulüpte küçük bir etkinlik organize et.", "proje", "1 ay", "Etkinlik gerçekleşti."),
            ("bu_donem", "Geri bildirim iste", "Grup arkadaşlarından liderlik ettiğin bir iş hakkında geri bildirim iste.", "gorusme", "1 hafta", "En az 2 kişiden geri bildirim aldın."),
            ("uzun_vadede", "Kulüp görevi", "Bir kulüpte yönetim görevi üstlen (başkan yardımcısı, proje sorumlusu).", "deneyim", "1 dönem", "Bir dönem boyunca yönetim görevini sürdürdün."),
            ("uzun_vadede", "Kendi yolunu seç", "Bölümde yönetici mi yoksa uzman mı olarak ilerlemek istediğini değerlendir; ikisi de değerli yollar.", "yansitma", "30 dk", "Tercihini gerekçesiyle yazdın."),
        ],
        "guclu": [
            ("simdi", "Liderlik fırsatı bul", "Okulda başkanlık, kaptanlık ya da proje liderliği gibi bir fırsata başvur.", "deneyim", "1-2 hafta", "Bir liderlik rolüne başvurdun."),
            ("bu_donem", "Dinleyen lider ol", "Yönettiğin bir işte ekipten fikir toplayarak karar alma pratiği yap.", "aliskanlik", "1 ay", "En az bir kararı ekip fikirlerine dayanarak aldın."),
        ],
    },

    # ============================ K3 — İŞ ORTAMI & PROFESYONEL YETKİNLİK ============================
    "I1": {
        "nedir": "Birden fazla işi planlama, öncelik sıralama ve teslim tarihlerini yönetme becerisi.",
        "gelisim_neden": "{bolum} alanında aynı anda birçok iş (dersler, projeler, staj, sınavlar) yürütülüyor ve önceliklendirme başarının anahtarı. Bu becerin alanın beklentisinin altında; birkaç basit teknikle hızla gelişebilir.",
        "guclu_neden": "Zaman yönetimin {bolum} ortalamasının da üzerinde. Bu sayede yoğun dönemlerde bile ek fırsatlara (proje, yarışma, kurs) yer açabilirsin.",
        "gelisim": [
            ("simdi", "Önemli–acil tablosu", "Bu haftaki işlerini 4 kutuya ayır: önemli-acil, önemli-acil değil, acil-önemsiz, ikisi de değil. Önce ilk kutudan başla.", "aliskanlik", "20 dk", "Bu haftanın işlerini 4 kutuya ayırdın."),
            ("simdi", "Zaman takibi", "İki gün boyunca zamanını nereye harcadığını yarım saatlik dilimlerle not et.", "yansitma", "2 gün", "Zamanını en çok neyin aldığını gördün."),
            ("bu_donem", "Günün 3 önceliği", "Her sabah günün en önemli 3 işini seç ve önce onları bitir.", "aliskanlik", "4 hafta", "4 hafta boyunca her gün 3 öncelik belirledin."),
            ("bu_donem", "Büyük işi böl", "Büyük bir ödevi ya da projeyi küçük parçalara bölüp her parçaya tarih ver.", "proje", "2-4 hafta", "Projeyi parçalara bölerek zamanında bitirdin."),
            ("uzun_vadede", "Sınav dönemi planı", "Bir sonraki sınav dönemi için geriye doğru çalışma takvimi hazırla.", "proje", "1 dönem", "Sınav dönemini takvimine uyarak geçirdin."),
            ("uzun_vadede", "Dikkat dağıtıcıları azalt", "Çalışırken telefonu başka odaya koy ya da odak uygulaması kullan; etkisini ölç.", "aliskanlik", "1-2 ay", "Odaklı çalışma sürenin arttığını gördün."),
        ],
        "guclu": [
            ("simdi", "Ek bir hedef ekle", "Zaman yönetimi gücünü kullanarak programına {bolum} ile ilgili ek bir çalışma (kurs, okuma) ekle.", "proje", "30 dk", "Ek çalışmayı haftalık programına yerleştirdin."),
            ("bu_donem", "Ekibin zaman yöneticisi ol", "Bir grup projesinde iş takvimini sen hazırla ve takip et.", "deneyim", "1 ay", "Proje senin takviminle zamanında bitti."),
        ],
    },
    "I2": {
        "nedir": "Takım içi anlaşmazlıkları çözme ve farklı görüşleri yönetebilme yetkinliği.",
        "gelisim_neden": "{bolum} alanında ekipler farklı görüşlerden insanlarla çalışıyor; anlaşmazlıkları yapıcı şekilde çözmek önemli bir beklenti. Bu becerin alanın ortalamasının altında; çatışmayı büyümeden yönetmeyi öğrenmek ekip içindeki etkini artırır.",
        "guclu_neden": "Çatışma yönetimi becerin {bolum} ortalamasının da üzerinde. Bu, ekiplerde güvenilen ve sorun çözen kişi olmanı sağlar.",
        "gelisim": [
            ("simdi", "Ben dili", "Bir anlaşmazlıkta \"sen hep...\" yerine \"ben ... hissediyorum, çünkü...\" kalıbını kullanmayı dene.", "aliskanlik", "1 hafta", "En az 2 kez ben dili kullandın."),
            ("simdi", "Son çatışmayı çözümle", "Son yaşadığın bir anlaşmazlığı yaz: ne oldu, ne istendi, nasıl çözülebilirdi?", "yansitma", "20 dk", "Alternatif bir çözüm yolu yazdın."),
            ("bu_donem", "Kural koyan ekip", "Bir grup çalışmasının başında ekibe birlikte çalışma kuralları önerin (görev dağılımı, karar yöntemi).", "proje", "2-4 hafta", "Ekip senin önerdiğin kurallarla çalıştı."),
            ("bu_donem", "Müzakere üzerine okuma", "Müzakere ve uzlaşma üzerine kısa bir kaynak oku (ör. \"Evet'e Ulaşmak\" – Fisher & Ury).", "okuma", "3-4 hafta", "3 uygulanabilir fikir çıkardın."),
            ("uzun_vadede", "Münazara ya da model BM", "Münazara kulübü ya da Model Birleşmiş Milletler gibi farklı görüşleri yönetmeyi gerektiren bir etkinliğe katıl.", "deneyim", "1 dönem", "En az bir etkinlikte aktif rol aldın."),
            ("uzun_vadede", "Arabuluculuk pratiği", "Arkadaşların arasındaki küçük bir anlaşmazlıkta tarafsız dinleyici ol.", "deneyim", "ihtiyaç halinde", "Bir anlaşmazlığın sakinleşmesine katkı sağladın."),
        ],
        "guclu": [
            ("simdi", "Ekip kurallarını sen yaz", "Yeni bir grup çalışmasında ekip için anlaşmazlık çözüm yöntemi öner.", "deneyim", "1 hafta", "Ekip önerini benimsedi."),
            ("bu_donem", "Akran arabuluculuğu", "Okulda akran arabuluculuğu ya da öğrenci temsilciliği gibi bir rol üstlen.", "deneyim", "1 dönem", "Bir rol üstlendin."),
        ],
    },
    "I3": {
        "nedir": "Stres altında ve eksik bilgiyle bile makul karar verebilme kapasitesi.",
        "gelisim_neden": "{bolum} alanında zaman baskısı altında, tüm bilgiler elinde olmadan karar vermek sık karşılaşılan bir durum. Bu becerin alanın ortalamasının altında; karar verme yöntemleri ve kontrollü baskı deneyimleriyle güçlenebilir.",
        "guclu_neden": "Baskı altında karar verme becerin {bolum} ortalamasının da üzerinde. Bu, kriz anlarında güvenilen kişi olmanı sağlar; kararlarını sonradan değerlendirerek daha da keskinleştirebilirsin.",
        "gelisim": [
            ("simdi", "Hızlı karar kuralı", "Küçük kararlar için kendine süre sınırı koy (ör. 2 dakika) ve o sürede karar ver.", "aliskanlik", "1 hafta", "Bir hafta boyunca küçük kararları süre sınırıyla verdin."),
            ("simdi", "Karar sorusu", "Zor bir kararda kendine sor: \"Elimdeki bilgiyle en makul seçenek hangisi, yanılırsam ne olur?\"", "yansitma", "10 dk", "Bu soruyu bir kararında kullandın."),
            ("bu_donem", "Süreli deneme sınavları", "Deneme sınavlarında soru başına süre hedefi koy; takıldığın soruyu bırakıp devam etmeyi öğren.", "deneyim", "1-2 ay", "Süreyi yetiştirme oranın arttı."),
            ("bu_donem", "Strateji oyunları", "Satranç, zeka oyunları ya da zamanlı bulmacalarla düzenli pratik yap.", "aliskanlik", "1-2 ay", "Haftada en az 2 kez oynadın."),
            ("uzun_vadede", "Kriz senaryosu çalış", "{bolum} alanında yaşanabilecek bir kriz senaryosunu araştır ve \"ben olsam ne yapardım\" diye çözüm yaz.", "proje", "1-2 saat", "Bir senaryo ve çözüm planın var."),
            ("uzun_vadede", "Karar sonrası değerlendirme", "Verdiğin önemli kararları bir hafta sonra gözden geçir: neyi doğru yaptın, neyi farklı yapardın?", "aliskanlik", "2-3 ay", "En az 5 karar değerlendirmesi yaptın."),
        ],
        "guclu": [
            ("simdi", "Zaman baskılı rol", "Yarışma, münazara ya da etkinlik organizasyonu gibi hızlı karar gerektiren bir role gir.", "deneyim", "1-2 ay", "Bir baskılı rolde görev aldın."),
            ("bu_donem", "Kriz vakası incele", "{bolum} alanında gerçek bir kriz örneğini incele ve alınan kararları değerlendir.", "okuma", "1-2 saat", "Vakayı ve kendi değerlendirmeni yazdın."),
        ],
    },
    "I4": {
        "nedir": "Adalet, dürüstlük ve etik ilkelere bağlı kalma hassasiyeti.",
        "gelisim_neden": "{bolum} alanında etik ilkeler ve meslek kuralları işin temelinde yer alıyor; dürüstlük ve sorumluluk güçlü bir beklenti. Bu konudaki duyarlılığın alanın ortalamasının altında; mesleğin etik kurallarını tanımak ve gri durumları tartışmak bu farkındalığı artırır.",
        "guclu_neden": "Etik duyarlılığın {bolum} ortalamasının da üzerinde. Bu, güvenilir bir profesyonel olmanın temelidir; ilkelerini esnek çözümlerle nasıl birleştireceğini de öğrenmek seni güçlendirir.",
        "gelisim": [
            ("simdi", "Meslek etiği kuralları", "{bolum} alanının meslek etiği kurallarını (meslek örgütü yönetmelikleri) araştır ve 3 temel kuralı not et.", "arastirma", "45 dk", "3 etik kuralı kendi cümlelerinle yazdın."),
            ("simdi", "Gri durum düşün", "Doğru ile kolay olanın çatıştığı bir durum hayal et (ör. kopya, hatayı gizleme); ne yapardın ve neden?", "yansitma", "15 dk", "Bir gri durum ve kararını yazdın."),
            ("bu_donem", "Etik vaka tartışması", "Bu alanda yaşanmış bir etik ihlal haberini bul ve bir arkadaşınla ya da öğretmeninle tartış.", "gorusme", "1 saat", "Vakayı tartıştın ve farklı görüşleri not ettin."),
            ("bu_donem", "Söz–eylem tutarlılığı", "Bir ay boyunca verdiğin küçük sözleri (randevu, ödev, yardım) tutup tutmadığını takip et.", "aliskanlik", "4 hafta", "Sözlerinin büyük çoğunluğunu tuttun."),
            ("uzun_vadede", "Etik üzerine okuma", "Etik ve sorumluluk üzerine bir kitap oku ve bölümünle ilişkilendir.", "okuma", "1-2 ay", "Kitabı bitirdin ve 3 fikri bölümle ilişkilendirdin."),
            ("uzun_vadede", "Kendi ilkelerin", "Meslekte asla yapmayacağın 3 şeyi ve her zaman yapacağın 3 şeyi yaz.", "yansitma", "30 dk", "Kişisel ilke listen hazır."),
        ],
        "guclu": [
            ("simdi", "Etik liderlik", "Grup çalışmalarında adil görev dağılımı ve kaynak gösterme gibi kuralları sen öner.", "deneyim", "2-4 hafta", "Ekip önerdiğin kuralları uyguladı."),
            ("bu_donem", "Esnek ama ilkeli", "Kurallara bağlı kalarak yaratıcı çözüm bulunan bir vaka incele; ilkelerin seni kısıtlamadan nasıl yönlendirebileceğini gör.", "okuma", "1 saat", "Vakayı ve çıkarımını yazdın."),
        ],
    },
    "I5": {
        "nedir": "Beklemeden sorumluluk alma, sorun gördüğünde adım atma (proaktiflik).",
        "gelisim_neden": "{bolum} alanında başarılı olanlar fırsatları kendileri yaratıyor: staj arıyor, proje başlatıyor, soru soruyor. İnisiyatif alma eğilimin alanın ortalamasının altında; küçük ilk adımları alışkanlık haline getirmek büyük fark yaratır.",
        "guclu_neden": "İnisiyatif alma gücün {bolum} ortalamasının da üzerinde. Bu, fırsatları erken yakalamanı sağlar; enerjini en önemli hedeflerine yönlendirmek için öncelik belirlemeyi unutma.",
        "gelisim": [
            ("simdi", "Bir soru sor", "Bu hafta bir öğretmenine ders dışında, {bolum} hakkında merak ettiğin bir soru sor.", "gorusme", "10 dk", "Soruyu sordun ve cevabı not ettin."),
            ("simdi", "Gördüğün bir sorunu çöz", "Çevrende küçük bir sorun fark et (sınıf düzeni, grup iletişimi) ve çözmek için bir adım at.", "deneyim", "1 hafta", "Bir sorunu çözmek için harekete geçtin."),
            ("bu_donem", "İlk başvuru", "Bir etkinliğe, yarışmaya ya da yaz okuluna başvur.", "deneyim", "1 ay", "Bir başvuru yaptın."),
            ("bu_donem", "\"Hemen başla\" kuralı", "2 dakikadan kısa sürecek işleri ertelemeden hemen yap.", "aliskanlik", "4 hafta", "Ertelediğin küçük işlerin azaldığını gördün."),
            ("uzun_vadede", "Kendi projeni başlat", "Kimse istemeden, {bolum} ile ilgili kendi projeni başlat (blog, araştırma, kulüp etkinliği).", "proje", "2-3 ay", "Projen hayata geçti."),
            ("uzun_vadede", "Fırsat listesi", "Her ay bölümle ilgili yeni bir fırsat (kurs, yarışma, etkinlik) bul ve en az birini değerlendir.", "aliskanlik", "3 ay", "3 ay boyunca her ay en az bir fırsat değerlendirdin."),
        ],
        "guclu": [
            ("simdi", "Büyük bir fırsata başvur", "{bolum} ile ilgili kapsamlı bir fırsata başvur (yaz okulu, bilim olimpiyatı, TÜBİTAK projesi, Teknofest).", "deneyim", "1-2 hafta", "Başvurunu tamamladın."),
            ("bu_donem", "Başkalarını harekete geçir", "Arkadaşlarını da dahil ettiğin bir proje ya da etkinlik başlat.", "proje", "1-3 ay", "En az 3 kişiyle birlikte bir işi hayata geçirdin."),
        ],
    },
    "I6": {
        "nedir": "Yapıcı eleştiriyi kabul etme, hatadan öğrenme ve savunmaya geçmeme eğilimi.",
        "gelisim_neden": "{bolum} alanında gelişim büyük ölçüde geri bildirimle oluyor: hocalar, yöneticiler ve meslektaşlar işini sürekli değerlendiriyor. Eleştiriye açıklığın alanın ortalamasının altında; geri bildirimi kişisel algılamadan bir gelişim aracı olarak kullanmayı öğrenmek ilerlemeni hızlandırır.",
        "guclu_neden": "Geri bildirime açıklığın {bolum} ortalamasının da üzerinde. Bu, hızlı öğrenmeni sağlar; geri bildirimi aktif olarak istemek seni daha da öne çıkarır.",
        "gelisim": [
            ("simdi", "Teşekkür et ve dinle", "Bu hafta aldığın bir eleştiriye cevap vermeden önce \"Teşekkürler, biraz düşüneyim\" de.", "aliskanlik", "1 hafta", "En az bir eleştiriye savunmaya geçmeden yanıt verdin."),
            ("simdi", "Hata günlüğü", "Bir sınavda yaptığın hataları türlerine göre ayır (bilgi eksiği, dikkat, süre).", "yansitma", "30 dk", "Hata türlerini ve en sık olanını belirledin."),
            ("bu_donem", "Geri bildirim iste", "Bir öğretmeninden bir ödevin ya da sunumun için özel geri bildirim iste: \"Neyi daha iyi yapabilirim?\"", "gorusme", "15 dk", "Geri bildirim aldın ve bir maddeyi uyguladın."),
            ("bu_donem", "Yeniden yap", "Geri bildirim aldığın bir çalışmayı düzeltip yeniden hazırla.", "proje", "2-3 hafta", "Çalışmanın geliştirilmiş hâlini tamamladın."),
            ("uzun_vadede", "Düzenli değerlendirme", "Ayda bir, güvendiğin birinden genel bir geri bildirim iste.", "aliskanlik", "3 ay", "3 ay boyunca her ay geri bildirim aldın."),
            ("uzun_vadede", "Gelişim zihniyeti", "Gelişim zihniyeti üzerine bir kaynak oku (ör. Carol Dweck – \"Mindset\").", "okuma", "1 ay", "Okuduğundan 3 fikri hayatına uyguladın."),
        ],
        "guclu": [
            ("simdi", "Geri bildirim döngüsü kur", "Her önemli çalışmandan sonra bir kişiden kısa geri bildirim iste.", "aliskanlik", "1 ay", "En az 3 çalışmanda geri bildirim aldın."),
            ("bu_donem", "Mentor bul", "{bolum} alanında seni yönlendirebilecek bir mentor (üst sınıf öğrencisi, mezun, öğretmen) bul.", "gorusme", "1-3 ay", "Bir mentorla en az 2 kez görüştün."),
        ],
    },
    "I7": {
        "nedir": "Stratejik düşünme, süreç ve insan yönetimi, ticari ve pazar farkındalığı.",
        "gelisim_neden": "{bolum} alanında işlerin büyük resmini görmek (kurumun hedefleri, maliyet, müşteri, rekabet) önemli bir beklenti. Bu yetkinliğin alanın ortalamasının altında; iş dünyasını tanımak ve strateji düşüncesini küçük projelerle denemek seni bu alana hazırlar.",
        "guclu_neden": "Stratejik ve ticari farkındalığın {bolum} ortalamasının da üzerinde. Bu, ileride yönetim, proje liderliği ya da girişimcilik yollarında sana avantaj sağlar.",
        "gelisim": [
            ("simdi", "Bir şirketi tanı", "{bolum} alanında faaliyet gösteren bir şirketin ne sattığını, kime sattığını ve rakiplerini araştır.", "arastirma", "45 dk", "Şirketin iş modelini 3 cümleyle anlatabiliyorsun."),
            ("simdi", "Ekonomi haberi", "Haftada bir ekonomi/iş dünyası haberi oku ve bölümünle ilişkisini düşün.", "aliskanlik", "1 hafta", "Bir haberi bölümünle ilişkilendirdin."),
            ("bu_donem", "Mini iş planı", "Küçük bir iş fikri için basit bir plan hazırla: müşteri, maliyet, fiyat, rakip.", "proje", "2-4 hafta", "Tek sayfalık bir iş planın var."),
            ("bu_donem", "Strateji oyunu ya da simülasyon", "İşletme simülasyonu, strateji oyunu ya da girişimcilik yarışmasına katıl.", "deneyim", "1-2 ay", "Bir simülasyon ya da yarışmayı tamamladın."),
            ("uzun_vadede", "İş dünyası kursu", "Temel işletme/yönetim üzerine kısa bir çevrim içi kurs al (ör. BTK Akademi).", "kurs", "1-2 ay", "Kursu tamamladın."),
            ("uzun_vadede", "Yöneticiyle görüş", "Bu alanda yönetici olan biriyle konuş: kararlarını nasıl veriyor, nelere dikkat ediyor?", "gorusme", "30 dk", "Görüşmeden 3 strateji fikri çıkardın."),
        ],
        "guclu": [
            ("simdi", "Sektör analizi", "{bolum} alanının bulunduğu sektörün geleceğini (fırsatlar, riskler) araştır.", "arastirma", "1 saat", "Kısa bir sektör analizi yazdın."),
            ("bu_donem", "Girişimcilik yarışması", "Bir girişimcilik ya da iş fikri yarışmasına ekip kurarak katıl.", "proje", "2-3 ay", "Başvurunu yaptın."),
        ],
    },

    # ============================ K4 — ALAN EĞİLİMİ & BİLİŞSEL STİL ============================
    "A1": {
        "nedir": "Matematik, istatistik, veri analizi ve sistem mantığına ilgi ve yatkınlık.",
        "gelisim_neden": "{bolum} eğitimi sayısal düşünme, veri yorumlama ve formül/sistem mantığına dayanıyor. Bu alandaki eğilimin bölümün beklentisinin altında; sayısal temelini düzenli pratikle güçlendirmek bölümdeki zorlu derslerde sana büyük kolaylık sağlar.",
        "guclu_neden": "Sayısal ve sistem odaklı düşünme gücün {bolum} ortalamasının da üzerinde. Bu, bölümde analitik derslerde öne çıkmanı sağlar; veri ve programlama becerileriyle bu gücü katlayabilirsin.",
        "gelisim": [
            ("simdi", "Eksik konu tespiti", "Son matematik sınavlarına bakıp en çok zorlandığın 3 konuyu belirle.", "yansitma", "30 dk", "3 öncelikli konun belli."),
            ("simdi", "Günlük 20 dakika", "Her gün 20 dakika matematik problemi çöz; kolaydan zora ilerle.", "aliskanlik", "1 hafta", "Bir hafta boyunca her gün çözdün."),
            ("bu_donem", "Konu kapatma", "Belirlediğin 3 konuyu sırayla çalış (ör. Khan Academy Türkçe, okul kaynakları) ve her biri için 20 soruluk test çöz.", "kurs", "1-2 ay", "3 konunun testlerinde başarı oranın arttı."),
            ("bu_donem", "Veriyle küçük proje", "Kendi hayatından bir veri topla (uyku, çalışma süresi) ve tablo/grafikle yorumla.", "proje", "2-3 hafta", "Veri tablon ve grafiğin hazır."),
            ("uzun_vadede", "Bölümün matematiğini tanı", "{bolum} programında hangi sayısal derslerin olduğunu araştır ve bir tanesinin giriş konusunu incele.", "arastirma", "1-2 saat", "Bölümün sayısal derslerini ve birinin konusunu biliyorsun."),
            ("uzun_vadede", "Programlamaya giriş", "Sayısal düşünmeyi destekleyecek temel bir programlama kursuna başla (ör. Python, BTK Akademi).", "kurs", "2-3 ay", "Kursun ilk modüllerini tamamladın."),
        ],
        "guclu": [
            ("simdi", "Olimpiyat ya da yarışma", "Matematik olimpiyatı ya da veri/kodlama yarışmalarını araştır ve birine hazırlanmaya başla.", "deneyim", "1-2 hafta", "Hedef yarışmanı ve hazırlık planını belirledin."),
            ("bu_donem", "Veri bilimi temeli", "Python ile veri analizi üzerine kısa bir kurs al ve {bolum} ile ilgili bir veri seti incele.", "kurs", "1-3 ay", "Bir veri setini analiz ettin."),
        ],
    },
    "A2": {
        "nedir": "Okuma-yazma, kavramsal düşünme, tartışma ve ikna süreçlerine yatkınlık.",
        "gelisim_neden": "{bolum} alanında yoğun okuma, yazılı anlatım ve argüman kurma önemli bir yer tutuyor. Sözel eğilimin bölümün beklentisinin altında; düzenli okuma ve yazma alışkanlığıyla bu beceri belirgin şekilde gelişir.",
        "guclu_neden": "Sözel ve argüman kurma gücün {bolum} ortalamasının da üzerinde. Bu, raporlarda, sunumlarda ve ikna gerektiren durumlarda seni öne çıkarır.",
        "gelisim": [
            ("simdi", "Günlük 15 sayfa", "Her gün 15 sayfa kitap oku; ilgini çeken bir türden başla.", "aliskanlik", "1 hafta", "Bir hafta boyunca her gün okudun."),
            ("simdi", "Tek paragraf görüş", "Bir güncel konu hakkında tek paragraflık bir görüş yazısı yaz: iddia, gerekçe, örnek.", "proje", "30 dk", "İddia-gerekçe-örnek yapısında bir paragrafın var."),
            ("bu_donem", "Haftalık yazı", "Her hafta bir konuda 300 kelimelik yazı yaz ve bir öğretmenden geri bildirim al.", "aliskanlik", "4-6 hafta", "En az 4 yazı yazdın."),
            ("bu_donem", "Münazara ya da kitap kulübü", "Okulun münazara ya da kitap kulübüne katıl.", "deneyim", "1-3 ay", "En az 2 oturuma aktif katıldın."),
            ("uzun_vadede", "Alan metni oku", "{bolum} alanına ait bir giriş kitabı ya da makale oku ve özetini çıkar.", "okuma", "1-2 ay", "Bir alan metninin özetini yazdın."),
            ("uzun_vadede", "Kelime dağarcığı", "Okurken bilmediğin kelimeleri bir defterde topla; haftada bir tekrar et.", "aliskanlik", "3 ay", "En az 50 yeni kelime öğrendin."),
        ],
        "guclu": [
            ("simdi", "Yazı yarışması", "Bir deneme/kompozisyon yarışmasını araştır ve katılmaya karar ver.", "deneyim", "1-2 hafta", "Bir yarışma seçtin."),
            ("bu_donem", "Alanında yaz", "{bolum} ile ilgili bir konuda blog ya da okul dergisi yazısı yayımla.", "proje", "1-2 ay", "Yazın yayımlandı."),
        ],
    },
    "A3": {
        "nedir": "İnsan davranışı, psikoloji, eğitim ve sosyal hizmet gibi insan merkezli alanlara ilgi.",
        "gelisim_neden": "{bolum} alanı insan davranışını anlamayı ve insanlarla doğrudan çalışmayı gerektiriyor. İnsan odaklı eğilimin bölümün beklentisinin altında; insanları gözlemleme, dinleme ve onlara destek olma deneyimleri bu alana uyumunu test eder ve güçlendirir.",
        "guclu_neden": "İnsan odaklı ilgin {bolum} ortalamasının da üzerinde. Bu, danışmanlık, eğitim ya da insan kaynakları gibi alt alanlarda seni öne çıkarabilir.",
        "gelisim": [
            ("simdi", "İnsan gözlemi", "Bu hafta bir ortamda (sınıf, kafe) insanların davranışlarını gözlemle ve 3 ilginç örüntü not et.", "deneyim", "1 hafta", "3 gözlem notun var."),
            ("simdi", "Psikolojiye giriş", "Psikoloji ya da insan davranışı üzerine kısa bir video/makale serisi izle.", "okuma", "30-45 dk", "Öğrendiğin bir kavramı birine anlattın."),
            ("bu_donem", "Akran desteği", "Bir arkadaşına ders konusunda düzenli yardım et.", "deneyim", "1 ay", "En az 4 kez destek verdin."),
            ("bu_donem", "İnsanlarla çalışan biriyle görüş", "Öğretmen, psikolog ya da sosyal hizmet uzmanı biriyle işinin insan yönünü konuş.", "gorusme", "30 dk", "Görüşmeden 3 not çıkardın."),
            ("uzun_vadede", "Gönüllü eğitim", "TEGV, TOG gibi kurumlarda çocuklara ya da gençlere yönelik bir etkinlikte gönüllü ol.", "deneyim", "1-3 ay", "En az 2 etkinlikte gönüllü oldun."),
            ("uzun_vadede", "Uyum değerlendirmesi", "Deneyimlerinden sonra insanlarla yoğun çalışmanın sana enerji mi verdiğini yoksa seni yorduğunu mu değerlendir.", "yansitma", "30 dk", "Değerlendirmeni yazdın."),
        ],
        "guclu": [
            ("simdi", "İnsan odaklı alt alan", "{bolum} içinde insanla en çok temas eden alt alanları araştır.", "arastirma", "45 dk", "En az 2 alt alan belirledin."),
            ("bu_donem", "Akran mentorluğu", "Okulda alt sınıflara yönelik bir mentorluk ya da rehberlik programına katıl.", "deneyim", "1 dönem", "Programa katıldın."),
        ],
    },
    "A4": {
        "nedir": "Tasarım, çizim, görsel üretim ve görsel-uzamsal problem çözme eğilimi.",
        "gelisim_neden": "{bolum} alanında görsel düşünme, tasarım ve uzamsal problem çözme önemli bir yer tutuyor. Bu eğilimin bölümün beklentisinin altında; çizim, maket ve dijital tasarım pratikleriyle hem becerini geliştirip hem de bu alana uyumunu sınayabilirsin.",
        "guclu_neden": "Görsel ve tasarım gücün {bolum} ortalamasının da üzerinde. Bu, sunumlarda, projelerde ve portfolyoda seni ayırt eder.",
        "gelisim": [
            ("simdi", "Günlük eskiz", "Her gün 10 dakika çevrendeki bir nesneyi çiz.", "aliskanlik", "1 hafta", "7 eskizin var."),
            ("simdi", "Uzamsal bulmacalar", "3D bulmaca, origami ya da uzamsal zeka oyunlarıyla pratik yap.", "aliskanlik", "1 hafta", "En az 3 bulmaca tamamladın."),
            ("bu_donem", "Dijital tasarım aracı", "Ücretsiz bir tasarım aracı öğren (Canva, Figma, Tinkercad) ve basit bir tasarım yap.", "kurs", "2-4 hafta", "Araçla bir tasarım tamamladın."),
            ("bu_donem", "Maket ya da model", "{bolum} ile ilgili bir yapının ya da nesnenin basit bir maketini yap.", "proje", "1 ay", "Maketin hazır."),
            ("uzun_vadede", "Tasarım atölyesi", "Halk eğitim merkezi ya da üniversite yaz okulunda bir tasarım/çizim atölyesine katıl.", "kurs", "1-2 ay", "Atölyeyi tamamladın."),
            ("uzun_vadede", "Portfolyo başlangıcı", "Yaptığın tasarım çalışmalarını tek bir dosyada topla.", "proje", "3 ay", "En az 5 çalışmalık bir portfolyon var."),
        ],
        "guclu": [
            ("simdi", "Portfolyonu düzenle", "En iyi 5 tasarım çalışmanı seç ve açıklamalarıyla bir portfolyo hazırla.", "proje", "2-3 saat", "Portfolyon hazır."),
            ("bu_donem", "Tasarım yarışması", "{bolum} ile ilgili bir tasarım ya da maket yarışmasına katıl.", "deneyim", "1-3 ay", "Başvurunu yaptın."),
        ],
    },
    "A5": {
        "nedir": "Biyoloji, kimya, çevre, laboratuvar deneyleri ve saha çalışmalarına ilgi.",
        "gelisim_neden": "{bolum} alanında laboratuvar, deney ve canlılar/doğa üzerine çalışmak eğitimin önemli bir parçası. Bu eğilimin bölümün beklentisinin altında; uygulamalı deneyimler bu alanın sana ne kadar uygun olduğunu netleştirir.",
        "guclu_neden": "Doğa ve laboratuvar ilgin {bolum} ortalamasının da üzerinde. Bu, araştırma projelerinde ve uygulamalı derslerde seni öne çıkarır.",
        "gelisim": [
            ("simdi", "Belgesel izle", "Doğa, biyoloji ya da kimya üzerine bir belgesel izle ve seni şaşırtan 3 bilgiyi not et.", "okuma", "1 saat", "3 bilgi not ettin."),
            ("simdi", "Evde basit deney", "Güvenli bir ev deneyi yap (ör. bitki büyütme, pH deneyi) ve gözlemlerini kaydet.", "deneyim", "1 hafta", "Deney günlüğün var."),
            ("bu_donem", "Okul laboratuvarı", "Fen öğretmeninden laboratuvar çalışmalarına daha fazla katılma ya da asistanlık fırsatı iste.", "deneyim", "1-2 ay", "En az 2 laboratuvar çalışmasına katıldın."),
            ("bu_donem", "Saha gezisi", "Bir botanik bahçesi, müze, araştırma merkezi ya da doğa gezisine katıl.", "deneyim", "1 gün", "Geziye katıldın ve notlarını yazdın."),
            ("uzun_vadede", "Araştırma projesi", "Fen alanında küçük bir araştırma projesi yap (ör. TÜBİTAK 2204 lise projeleri).", "proje", "3-6 ay", "Proje raporun hazır."),
            ("uzun_vadede", "Yaz bilim okulu", "Üniversitelerin lise öğrencilerine yönelik yaz bilim okullarını araştır ve birine başvur.", "deneyim", "1-2 hafta", "Başvurunu yaptın."),
        ],
        "guclu": [
            ("simdi", "Araştırma konusu seç", "{bolum} ile ilgili merak ettiğin bir doğa/laboratuvar sorusunu seç.", "yansitma", "30 dk", "Bir araştırma sorun var."),
            ("bu_donem", "Bilim yarışması", "Seçtiğin soru üzerine bir bilim yarışması projesi hazırla.", "proje", "2-6 ay", "Proje başvurunu yaptın."),
        ],
    },
    "A6": {
        "nedir": "Spor, beden kullanımı ve sahada aktif olmayı gerektiren işlere yatkınlık.",
        "gelisim_neden": "{bolum} alanında fiziksel aktivite, sahada çalışma ya da beden kullanımı önemli bir yer tutuyor. Bu eğilimin bölümün beklentisinin altında; düzenli hareket alışkanlığı ve sahada deneyim bu alana uyumunu artırır.",
        "guclu_neden": "Fiziksel ve sahaya yönelik eğilimin {bolum} ortalamasının da üzerinde. Bu, uygulamalı ve sahada geçen işlerde sana avantaj sağlar.",
        "gelisim": [
            ("simdi", "Günlük hareket", "Her gün en az 20 dakika yürüyüş ya da hafif egzersiz yap.", "aliskanlik", "1 hafta", "7 gün boyunca hareket ettin."),
            ("simdi", "Sahayı gör", "{bolum} alanında sahada çalışan birinin gününü anlatan bir video izle.", "arastirma", "30 dk", "Saha işinin fiziksel yönlerini not ettin."),
            ("bu_donem", "Bir spor dalı", "Bir spor dalına ya da okul takımına katıl.", "deneyim", "1-3 ay", "Düzenli antrenmanlara katıldın."),
            ("bu_donem", "Uygulamalı gönüllülük", "Fiziksel çaba gerektiren bir gönüllülük etkinliğine katıl (ağaç dikme, çevre temizliği).", "deneyim", "1 gün", "Etkinliğe katıldın."),
            ("uzun_vadede", "Kondisyon hedefi", "3 ay sonra ulaşmak istediğin bir kondisyon hedefi koy (ör. 5 km yürüyüş/koşu).", "aliskanlik", "3 ay", "Hedefine ulaştın."),
            ("uzun_vadede", "Uyum değerlendirmesi", "Bölümün fiziksel/saha yönünün sana uygun olup olmadığını ve masa başı alt alanları değerlendir.", "yansitma", "30 dk", "Değerlendirmeni yazdın."),
        ],
        "guclu": [
            ("simdi", "Saha ağırlıklı alt alanlar", "{bolum} içinde sahada geçen ya da hareket gerektiren alt alanları araştır.", "arastirma", "45 dk", "En az 2 alt alan belirledin."),
            ("bu_donem", "Takım kaptanlığı", "Sporda ya da saha etkinliğinde sorumluluk al (kaptanlık, organizasyon).", "deneyim", "1-3 ay", "Bir sorumluluk üstlendin."),
        ],
    },
    "A7": {
        "nedir": "Kuralları net, aşamaları belli, planlı ve sistematik öğrenme/çalışma tarzı.",
        "gelisim_neden": "{bolum} alanında prosedürlere uygun, adım adım ve sistematik çalışmak önemli bir beklenti (protokoller, standartlar, sıralı işlemler). Bu tarza eğilimin bölümün beklentisinin altında; kontrol listeleri ve sıralı çalışma alışkanlıkları bu açığı kapatır.",
        "guclu_neden": "Sistematik ve adım adım çalışma gücün {bolum} ortalamasının da üzerinde. Bu, hata payı düşük ve güvenilir iş çıkarmanı sağlar.",
        "gelisim": [
            ("simdi", "Kontrol listesi", "Bu hafta bir ödevi teslim etmeden önce kontrol listesi hazırla ve madde madde işaretle.", "aliskanlik", "1 hafta", "Kontrol listesiyle bir iş teslim ettin."),
            ("simdi", "Adım adım not", "Bir konuyu çalışırken adımları numaralandırarak not al.", "aliskanlik", "1 hafta", "Numaralı adımlarla bir konu notun var."),
            ("bu_donem", "Prosedür takibi", "Bir tarif, montaj talimatı ya da deney protokolünü adım atlamadan uygula.", "deneyim", "1-2 hafta", "Bir protokolü eksiksiz uyguladın."),
            ("bu_donem", "Sabit çalışma şablonu", "Her ders için aynı sırayı izle: konu özeti → örnek → soru çözümü → tekrar.", "aliskanlik", "4 hafta", "4 hafta boyunca şablonu uyguladın."),
            ("uzun_vadede", "Standartları tanı", "{bolum} alanında kullanılan standartları ve prosedürleri araştır.", "arastirma", "1-2 saat", "En az 2 standart/prosedürü tanıdın."),
            ("uzun_vadede", "Sistematik proje", "Aşamaları baştan planlanmış bir proje yap ve her aşamayı belgeleyerek ilerle.", "proje", "2-3 ay", "Aşamaları belgelenmiş bir projen var."),
        ],
        "guclu": [
            ("simdi", "Süreç tasarla", "Grup projelerinde iş akışını adım adım tasarlayan kişi ol.", "deneyim", "2-4 hafta", "Ekibin senin iş akışınla çalıştı."),
            ("bu_donem", "Kalite kontrol rolü", "{bolum} ile ilgili bir projede kalite kontrol/son kontrol sorumluluğunu üstlen.", "deneyim", "1-2 ay", "Bir projede son kontrolü yaptın."),
        ],
    },
    "A8": {
        "nedir": "Önce büyük resmi görme, sezgiyle ilerleme ve görsel/şematik düşünme eğilimi.",
        "gelisim_neden": "{bolum} alanında ayrıntılara boğulmadan büyük resmi görmek, kavramlar arası bağlantı kurmak ve sezgisel çözümler üretmek önemli. Bu eğilimin bölümün beklentisinin altında; zihin haritaları ve bağlantı kurma alıştırmalarıyla gelişebilir.",
        "guclu_neden": "Büyük resmi görme ve sezgisel düşünme gücün {bolum} ortalamasının da üzerinde. Bu, yaratıcı çözümler ve stratejik bakış açısı üretmeni sağlar.",
        "gelisim": [
            ("simdi", "Zihin haritası", "Bir konuyu çalışmaya başlamadan önce tek sayfalık zihin haritası çıkar.", "aliskanlik", "1 hafta", "En az 2 zihin haritası yaptın."),
            ("simdi", "Neden önemli?", "Çalıştığın her konunun başında \"bu konu neden var, neye yarıyor?\" sorusunu yanıtla.", "yansitma", "1 hafta", "Konuların amacını tek cümleyle yazabiliyorsun."),
            ("bu_donem", "Bağlantı kur", "Farklı derslerden iki konu arasında bağlantı bul ve bir arkadaşına anlat.", "aliskanlik", "4 hafta", "En az 3 disiplinler arası bağlantı kurdun."),
            ("bu_donem", "Şemalarla öğren", "Bir ünitenin tamamını tek bir şema/akış diyagramında özetle.", "proje", "2-3 hafta", "Bir ünite şeman hazır."),
            ("uzun_vadede", "Sistem düşüncesi", "Sistem düşüncesi üzerine bir kaynak oku ve {bolum} ile ilgili bir sistemi çiz.", "okuma", "1-2 ay", "Bir sistem diyagramın var."),
            ("uzun_vadede", "Büyük soru projesi", "Bölümünle ilgili büyük bir soruya (ör. \"20 yıl sonra bu meslek nasıl olacak?\") yanıt arayan kısa bir yazı hazırla.", "proje", "1 ay", "Yazını tamamladın."),
        ],
        "guclu": [
            ("simdi", "Strateji rolü", "Grup projelerinde genel çerçeveyi kuran ve hedefi netleştiren kişi ol.", "deneyim", "2-4 hafta", "Projenin çerçevesini sen çizdin."),
            ("bu_donem", "Ayrıntıya dengele", "Büyük resim gücünü bir kontrol listesiyle dengele; teslimlerde ayrıntıları gözden kaçırma.", "aliskanlik", "1 ay", "Teslimlerinde ayrıntı hatası azaldı."),
        ],
    },
    "A9": {
        "nedir": "Fırsat görme, satış/pazarlık yapma ve risk alarak iş kurma isteği.",
        "gelisim_neden": "{bolum} alanında fırsatları görmek, fikirlerini ikna edici şekilde sunmak ve girişimci bakış önemli bir beklenti. Bu eğilimin bölümün beklentisinin altında; küçük satış/ikna deneyimleri ve girişimcilik etkinlikleri bu becerini geliştirir.",
        "guclu_neden": "Girişimci ve ikna gücün {bolum} ortalamasının da üzerinde. Bu, ileride kendi işini kurma, satış/pazarlama ya da iş geliştirme yollarında sana avantaj sağlar.",
        "gelisim": [
            ("simdi", "Fikrini 1 dakikada anlat", "Bir fikrini 1 dakikada anlatan kısa bir konuşma hazırla ve bir arkadaşına sun.", "deneyim", "30 dk", "1 dakikalık sunumunu yaptın."),
            ("simdi", "Fırsat avı", "Çevrende çözülmemiş 3 problem bul ve her biri için bir çözüm fikri yaz.", "yansitma", "30 dk", "3 problem ve çözüm fikrin var."),
            ("bu_donem", "Küçük satış deneyimi", "Okul kermesinde ya da bir etkinlikte satış/tanıtım görevi üstlen.", "deneyim", "1 gün", "Satış/tanıtım görevini tamamladın."),
            ("bu_donem", "Girişimcilik kulübü", "Girişimcilik kulübüne ya da genç girişimci programlarına katıl.", "deneyim", "1-3 ay", "En az 2 etkinliğe katıldın."),
            ("uzun_vadede", "Mini girişim", "Küçük bir girişim dene (el yapımı ürün, ders verme, dijital içerik) ve gelir-gider tablosu tut.", "proje", "2-3 ay", "İlk satışını yaptın ve tablon hazır."),
            ("uzun_vadede", "İkna becerisi", "İkna ve sunum teknikleri üzerine bir kaynak oku ya da kurs al.", "kurs", "1-2 ay", "Öğrendiğin 3 tekniği bir sunumda kullandın."),
        ],
        "guclu": [
            ("simdi", "Bölümde fırsat", "{bolum} alanında girişim fırsatlarını (yeni şirketler, çözülmemiş sorunlar) araştır.", "arastirma", "1 saat", "En az 2 fırsat alanı belirledin."),
            ("bu_donem", "İş fikri yarışması", "Bir iş fikri ya da girişimcilik yarışmasına katıl.", "proje", "2-3 ay", "Başvurunu yaptın."),
        ],
    },
}

# ============================ [2026-10-09] EK ADIMLAR ============================
# Öz yeterlik ve öz güven, merak ve soru sorma, odaklanma, dijital/bilgi/veri/görsel okuryazarlık,
# kültür ve vatandaşlık okuryazarlığı ile sürdürülebilirlik alanlarında ek adımlar.
# Kaynak: Türkiye Yüzyılı Maarif Modeli beceri çerçevesi (Eğilimler E1.4, E1.5, E2.3, E3.2, E3.4, E3.8, E3.9;
# Okuryazarlık becerileri OB1, OB2, OB4, OB5, OB6, OB7, OB8) ve SCCT öz yeterlik kaynakları (Lent ve ark. 1994).
# Mevcut adımların sırası değişmesin diye her değişkenin listesinin SONUNA eklenir (kodlar G-7, G-8).
_EK_GELISIM = {
    "P8": [
        ("simdi", "Başarı kanıtların", "Son bir yılda zorlanıp yine de başardığın 5 şeyi yaz ve her birinde senin hangi davranışının işe yaradığını belirt. Kendine güven, geçmiş başarılarını fark ettikçe artar.", "yansitma", "30 dk", "5 başarı ve her birinde işe yarayan davranışın yazılı."),
        ("bu_donem", "Gözlemle, sonra dene", "Liderliğini beğendiğin birini (öğretmen, kulüp başkanı, takım kaptanı) bir hafta gözlemle; yaptığı bir davranışı seç ve ertesi hafta kendin dene.", "deneyim", "2 hafta", "Gözlem notun ve denediğin davranışın sonucu yazılı."),
    ],
    "P7": [
        ("simdi", "Zorlandığında kendine ne diyorsun?", "Son zorlandığın bir anı hatırla ve o an kafandan geçen cümleyi yaz. Sonra aynı durumda bir arkadaşına söyleyeceğin cesaretlendirici cümleyi yanına yaz.", "yansitma", "15 dk", "İki cümle de yazılı ve ikincisini bir sonraki zorlukta kullanmaya karar verdin."),
        ("bu_donem", "Basamaklı meydan okuma", "Seni biraz zorlayan bir şeyi kolaydan zora 4 basamağa böl (ör. sınıfta soru sormak → kısa yorum yapmak → 1 dakikalık sunum → 5 dakikalık sunum) ve her hafta bir basamak çık.", "aliskanlik", "4 hafta", "4 basamağı yazdın ve en az 3'ünü tamamladın."),
    ],
    "I5": [
        ("bu_donem", "Okula bir öneri sun", "Okulda iyileştirilebilecek bir şey seç (kütüphane saatleri, kulüp etkinliği, geri dönüşüm), kısa bir öneri hazırla ve ilgili öğretmene ya da okul yönetimine sun.", "deneyim", "2-3 hafta", "Önerini yazılı olarak hazırladın ve ilgili kişiye ilettin."),
    ],
    "P5": [
        ("simdi", "Sorgulayan okur", "Hedef bölümünle ilgili merak ettiğin bir konu seç, hakkında 5 \"neden?\" ya da \"nasıl?\" sorusu yaz ve cevapları en az iki farklı kaynaktan ara. Kaynakların birbirini tutmadığı noktayı not et.", "arastirma", "1 saat", "5 soru, cevapları ve kaynakların ayrıştığı en az 1 nokta yazılı."),
    ],
    "I1": [
        ("simdi", "25 dakikalık odak bloğu", "Ders çalışırken 25 dakika boyunca tek bir işe odaklan, telefonu başka odaya koy, sonra 5 dakika ara ver. Her gün en az 2 odak bloğu yap ve kaç blok yaptığını işaretle.", "aliskanlik", "2 hafta", "2 hafta boyunca günlük blok sayını işaretledin ve günlerin çoğunda en az 2 blok var."),
    ],
    "A1": [
        ("simdi", "Bilgiyi doğrula", "İnternette {bolum} ya da meslekle ilgili bir iddia (haber, video, paylaşım) bul. Kimin yazdığını, tarihini ve kaynağını kontrol et; iddiayı güvenilir bir kaynaktan doğrula ya da çürüt.", "arastirma", "45 dk", "İddia, kontrol ettiğin 3 bilgi (yazar, tarih, kaynak) ve vardığın sonuç yazılı."),
        ("bu_donem", "Veriyle anlat", "Merak ettiğin bir konuda açık bir veri bul (TÜİK, YÖK Atlas, okul verisi), bir tabloya aktar, bir grafik çiz ve grafiğin söylediğini 3 cümleyle yaz.", "proje", "2-3 hafta", "Tablon, grafiğin ve 3 cümlelik yorumun hazır."),
    ],
    "A4": [
        ("bu_donem", "Görseli çözümle", "Bir infografik, reklam afişi ya da veri grafiği seç. Göze ilk ne çarpıyor, hangi renk ve yerleşim seçilmiş, görsel neyi öne çıkarıp neyi gizliyor? Sonra aynı bilgiyi kendi tasarımınla daha açık anlat.", "proje", "1-2 hafta", "Çözümleme notun ve kendi yeniden tasarımın hazır."),
    ],
    "I4": [
        ("simdi", "Dijital izini kontrol et", "Adını bir arama motorunda arat ve sosyal medya hesaplarının kimlere açık olduğunu kontrol et. Bir üniversite ya da işveren bakarsa neyi görür, düşün.", "yansitma", "30 dk", "Hesaplarının gizlilik ayarlarını gözden geçirdin ve değiştirmek istediğin en az 1 şeyi düzelttin."),
        ("bu_donem", "Bir toplumsal sorunu incele", "Çevrende bir sorunu seç (erişilebilirlik, trafik güvenliği, israf). Sorumlu kurumları, mevcut kuralları ve vatandaşların neler yapabileceğini araştır; {bolum} bu soruna nasıl katkı sağlayabilir, yaz.", "arastirma", "2-3 hafta", "Sorun, sorumlu kurumlar, yapılabilecekler ve bölümünün katkısını içeren 1 sayfalık notun hazır."),
    ],
    "A3": [
        ("simdi", "Öteki tarafın gözünden", "Yakın zamanda biriyle anlaşamadığın bir durumu düşün. O kişinin bakış açısını onun ağzından, \"ben\" diliyle 5 cümleyle yaz.", "yansitma", "20 dk", "Karşı tarafın bakışını yargılamadan 5 cümleyle yazdın."),
        ("bu_donem", "Farklı bir hayatı dinle", "Senden farklı bir kültürden, kuşaktan ya da yaşam koşulundan biriyle (büyükanne-büyükbaba, başka şehirden gelen bir arkadaş, bir esnaf) konuş; hayatını, değerlerini ve gençliğini sor.", "gorusme", "30-45 dk", "Görüşmeyi yaptın; seni şaşırtan 3 şeyi ve ortak noktalarınızı yazdın."),
    ],
    "A5": [
        ("simdi", "Bölümün sürdürülebilirlik bağlantısı", "{bolum} alanının çevre, enerji, su ya da iklimle nasıl bir ilişkisi olduğunu araştır; bu alanda çalışan bir kurum ya da proje bul.", "arastirma", "45 dk", "Bölümünün çevreyle 2 bağlantısını ve 1 örnek projeyi yazdın."),
        ("bu_donem", "Okulun atık ölçümü", "Bir hafta boyunca sınıfında ya da evinde çıkan atığı (kâğıt, plastik, yemek) türüne göre say ya da tart. Sonuçları tabloya dök ve azaltmak için uygulanabilir 2 öneri yaz.", "proje", "2 hafta", "1 haftalık ölçüm tablon ve 2 önerin hazır."),
    ],
}
for _kod, _adimlar in _EK_GELISIM.items():
    ICERIK[_kod]["gelisim"].extend(_adimlar)


TUR_ETIKET = {
    "arastirma": "Araştırma", "gorusme": "Görüşme", "deneyim": "Deneyim", "proje": "Proje",
    "aliskanlik": "Alışkanlık", "okuma": "Okuma", "kurs": "Kurs", "yansitma": "Kendini değerlendirme",
}
ASAMA_SIRASI = ("simdi", "bu_donem", "uzun_vadede")


def adim_kodu(degisken_kod: str, grup: str, sira: int) -> str:
    """grup: 'G' (gelişim) | 'U' (güçlü yön)"""
    return f"{degisken_kod}-{grup}-{sira}"
