# -*- coding: utf-8 -*-
"""
[2026-10-09] Koçluk adımlarının detayı — öğrencinin anlayacağı düzeyde "Nasıl yaparsın?" (adım adım),
"Nasıl anlarsın?" (kontrol listesi) ve kısa bir ipucu. Anahtar = adım kodu (gelisim_icerigi.adim_kodu).

Kısa açıklama ve tek cümlelik ölçüt gelisim_icerigi.py'de durur; bu dosya onları DETAYLANDIRIR.
"{bolum}" yer tutucusu öğrencinin hedef bölüm adıyla değiştirilir. Bir adımın detayını değiştirmek için
yalnızca bu dosyayı düzenlemek yeterlidir (veritabanı değişmez).

Kanıt temeli (ayrıntı: docs "Filizyol — Kuramsal Temel ve Kaynakça"): yazılı ve ölçülebilir başarı ölçütü
(Locke & Latham 2002; Harkin ve ark. 2016), alışkanlık adımlarında "Eğer–o zaman" planı (Gollwitzer & Sheeran 2006)
ve ~2 aylık alışkanlık süresi (Lally ve ark. 2010), görüşme/deneyim adımları (Brown & Ryan Krane 2000; OECD 2021).
"""

DETAY: dict[str, dict] = {
    "D1-G-1": {
        "nasil": [
            "Bir kâğıda ya da tabloya 4 sütun çiz: Ad (ya da baş harfler), mezuniyet yılı, çalıştığı kurumlar, kurumun türü (kamu, özel, serbest).",
            "LinkedIn'de arama kutusuna \"{bolum}\" ve bir üniversite adını yaz, sonra \"Kişiler\" filtresini seç. LinkedIn, insanların okul ve iş geçmişini paylaştığı bir iş ağıdır.",
            "Profillerde \"Deneyim\" bölümüne bak; mezun olduktan sonraki ilk 5 yılda çalıştığı yerleri sırayla tabloya yaz.",
            "Bazı üniversitelerin kariyer merkezi ya da bölüm sayfasında mezun hikâyeleri bulunur; oradan da örnek ekle.",
            "5 kişiyi doldurunca tabloya bak ve en çok hangi kurum türünün tekrar ettiğini altına bir cümleyle yaz.",
        ],
        "kontrol": [
            "Tablonda en az 5 mezunun satırı dolu.",
            "Her mezun için çalıştığı kurumun türü (kamu, özel ya da serbest) yazılı.",
            "\"Bu bölümün mezunları en çok nerede çalışıyor?\" sorusuna bir cümleyle cevap verebiliyorsun.",
        ],
        "ipucu": "LinkedIn'e üye olmak istemiyorsan ya da yaşın uygun değilse aynı araştırmayı üniversitelerin mezun sayfaları ve röportajlarla yapabilirsin.",
    },
    "D1-G-2": {
        "nasil": [
            "Sessiz bir yerde 20 dakika ayır; telefonunu sessize al ve bir kâğıt ya da defter aç.",
            "Üç soruyu ayrı ayrı başlık olarak yaz: \"İşimi kaybetme riski beni ne kadar rahatsız eder?\", \"Esnek ama belirsiz bir iş mi, sabit ama sıkıcı bir iş mi?\", \"5 yıl sonra nasıl bir düzende yaşamak isterim?\"",
            "Her sorunun altına aklına gelen ilk cevabı yaz, sonra \"Neden?\" diye sorup ikinci bir cümle ekle.",
            "Cevap verirken somut düşün. Örneğin: \"Ay sonunu düşünmeden yaşamak beni rahatlatır çünkü ailemde bunun stresini gördüm.\"",
            "Bitirince cevaplarını oku ve güvenceye ne kadar önem verdiğini 1-5 arası bir puanla kenara not et.",
        ],
        "kontrol": [
            "Üç sorunun her birinin altında en az iki cümle var.",
            "Cevaplarında \"çünkü\" ile başlayan en az bir gerekçe bulunuyor.",
            "Güvenceye ne kadar önem verdiğini kendi sözlerinle söyleyebiliyorsun.",
        ],
        "ipucu": "\"Doğru cevap\" arama; burada amaç ne hissettiğini fark etmek, kimseye göstermek zorunda değilsin.",
    },
    "D1-G-3": {
        "nasil": [
            "Çevrende {bolum} okumuş birini bul: akrabalar, aile dostları, öğretmenler. Bulamazsan rehberlik servisinden yardım iste.",
            "Kime ulaşacağını ailene ya da öğretmenine söyle; tanımadığın biriyle yalnızca onların bilgisi dahilinde, okulda ya da görüntülü görüşmeyle konuş.",
            "Görüşmeden önce 5 soru yaz. Örneğin: \"İşinizi kaybetme riski hiç oldu mu?\", \"Geliriniz her ay aynı mı?\", \"Bu alanda kadrolu iş bulmak ne kadar zor?\"",
            "Kısa bir mesajla kendini tanıt, ne için yazdığını söyle ve 20-30 dakikalık bir görüşme rica et.",
            "Görüşmede cevapları kısaca not al; bitince en önemli 3 bilgiyi altını çizerek ayrı yaz ve teşekkür mesajı gönder.",
        ],
        "kontrol": [
            "Bir {bolum} mezunuyla görüşmeyi gerçekten yaptın.",
            "Hazırladığın 5 soru ve cevaplarına dair notların bir sayfada duruyor.",
            "Görüşmeden öğrendiğin en önemli 3 bilgiyi ayrı ayrı yazdın.",
        ],
        "ipucu": "İlk ulaştığın kişi cevap vermezse bu normaldir; birkaç gün bekleyip başka birine yaz.",
    },
    "D1-G-4": {
        "nasil": [
            "{bolum} ile girilebilecek bir güvenceli yol (ör. kamu kadrosu) ve bir esnek yol (ör. serbest çalışma ya da kendi işini kurma) seç.",
            "Bir karşılaştırma tablosu çiz: satırlara gelir, istikrar, özgürlük ve sana uygunluk; sütunlara iki yolu yaz. Karşılaştırma tablosu, seçenekleri aynı ölçütlerle yan yana gösterir.",
            "Her yol için bölüm sayfalarından, mezun röportajlarından ve İŞKUR'un meslek tanıtım bilgilerinden kısa notlar topla.",
            "Her hücreyi 1 (çok düşük) ile 5 (çok yüksek) arasında puanla ve yanına bir kelimelik gerekçe yaz.",
            "Puanları topla; ama son satıra \"Hangisi bana daha iyi hissettiriyor?\" sorusunun cevabını da yaz.",
        ],
        "kontrol": [
            "İki yolu dört ölçüte göre 1-5 arası puanladığın bir tablon var.",
            "Her puanın yanında kısa bir gerekçe yazılı.",
            "Hangi yolun sana daha uygun olduğunu bir cümleyle açıklayabiliyorsun.",
        ],
        "ipucu": "Puanları tahminle değil bulduğun bilgiyle ver; bilmediğin bir hücreyi \"?\" ile işaretleyip sonra araştırabilirsin.",
    },
    "D1-G-5": {
        "nasil": [
            "Yaşına uygun kısa bir deneyim seç: bir kurumda gönüllülük, okulun yönlendirdiği bir staj ya da bir iş yerinde gözlem. Ücretli bir iş düşünüyorsan yalnızca ailenin onayıyla, yasal izinleri ve sözleşmesi olan, okul saatleri dışında yapılan hafif bir iş olsun.",
            "Fırsat ararken rehberlik servisine, öğretmenlerine ve aile çevrene danış; çalışacağın yeri mutlaka ailenle birlikte değerlendir.",
            "Deneyim boyunca, çalıştığın günlerin sonunda 3 satır not al: Saat kaçta başladım, gün nasıl geçti, kendimi nasıl hissettim?",
            "Özellikle sabit mesai, belli kurallar ve tekrar eden işler hakkında ne hissettiğine dikkat et.",
            "Deneyim bitince notlarını oku ve \"Bu düzende mutlu olur muyum?\" sorusuna gerekçeli bir cevap yaz.",
        ],
        "kontrol": [
            "2-4 haftalık bir iş, staj ya da gönüllülük deneyimini tamamladın.",
            "Deneyim sırasında aldığın kısa günlük notların var.",
            "\"Bu düzende mutlu olur muyum?\" sorusuna evet, hayır ya da \"şu şartla\" diye net ve gerekçeli bir cevap yazdın.",
        ],
        "ipucu": "Yaşın ya da okul düzenin bir işe uygun değilse veya iş bulamazsan okul kulübü, kütüphane veya bir derneğe düzenli gönüllülük de aynı gözlemi yapmanı sağlar.",
    },
    "D1-G-6": {
        "nasil": [
            "B planı, ilk planın beklediğin gibi gitmezse elinde olacak yedek seçenektir. Bir sayfanın başına \"B planım\" yaz.",
            "{bolum} okurken işine yarayabilecek 3 yan beceri listele: bir yabancı dil, bir sertifika ya da ikinci bir uzmanlık alanı.",
            "Her biri için kısa bir not al: Bu beceri hangi işlere kapı açar, ne kadar sürede öğrenilir, nereden öğrenilir?",
            "En gerçekçi olanı seç ve ilk adımını tarihle yaz. Örneğin: \"15 Kasım'da İngilizce kelime çalışmasına başlayacağım.\"",
            "Bu sayfayı rehber öğretmeninle ya da ailenle paylaş ve ilk adımı attıktan sonra yeniden gözden geçir.",
        ],
        "kontrol": [
            "\"B planım\" başlıklı yazılı bir sayfan var.",
            "Sayfada en az bir yan beceri ve neden seçtiğin yazılı.",
            "İlk adımın için bir başlangıç tarihi belirledin.",
        ],
        "ipucu": "B planı \"vazgeçmek\" değil, güvence ihtiyacını rahatlatan bir sigortadır; çok fazla seçenek yerine bir tanesiyle başla.",
    },
    "D1-U-1": {
        "nasil": [
            "Bir sayfaya üç başlık aç: Kamu, Büyük kurumlar, Akademi.",
            "Kamu için {bolum} mezunlarının girebildiği kadroları araştır; çoğu kamu işine KPSS gibi merkezi sınavlarla girilir, hangi sınavın gerektiğini not et.",
            "Büyük kurumlar için bu alanda düzenli işe alım yapan sektörleri (ör. bankalar, hastaneler, büyük şirketler) bul ve aradıkları şartları yaz.",
            "Akademi için üniversitede araştırma görevlisi olmanın şartlarını (yüksek lisans, ALES, yabancı dil gibi) araştır.",
            "Her yolun yanına giriş şartlarını madde madde yaz ve sana en uygun görüneni işaretle.",
        ],
        "kontrol": [
            "En az 3 güvenceli kariyer yolunu yazdın.",
            "Her yolun yanında giriş şartları (sınav, diploma, dil vb.) yazılı.",
            "Sana en uygun görünen yolu işaretledin.",
        ],
        "ipucu": "Bilgiyi kurumların ve üniversitelerin kendi sayfalarından doğrula; forumlardaki yorumlar eski ya da yanlış olabilir.",
    },
    "D1-U-2": {
        "nasil": [
            "Bir kâğıda ya da tabloya yılları sırayla yaz: Lise son, Üniversite 1, 2, 3, 4 (bölüm süresi farklıysa ona göre).",
            "“Güvenceli yolları listele” adımında çıkardığın güvenceli yolların şartlarını hatırla; her şartı hangi yılda hazırlamaya başlaman gerektiğini düşün.",
            "Her yılın altına en fazla 2-3 adım yaz: sınav, staj, sertifika, dil. Örneğin: \"3. sınıf yaz: staj\", \"4. sınıf: KPSS hazırlığı\".",
            "Takvimi duvarına as ya da telefonuna kaydet; yeni bir okul yılına ya da sınava hazırlanırken yeniden kontrol et.",
        ],
        "kontrol": [
            "Lise sonundan mezuniyete kadar her yılın yazılı olduğu bir takvimin var.",
            "Her yılın altında en az bir somut adım (sınav, staj ya da sertifika) bulunuyor.",
            "Takvimi bir yere kaydettin ve ne zaman kontrol edeceğini belirledin.",
        ],
        "ipucu": "Takvim kesin değil, yön gösterir; ilerledikçe değiştirebileceğin için kurşun kalem ya da dijital dosya kullan.",
    },
    "D2-G-1": {
        "nasil": [
            "Bir sayfaya iki satır aç: \"Başlangıç maaşı\" ve \"5. yıl maaşı\". Her biri için en düşük, ortalama ve en yüksek değer sütunu ekle.",
            "Maaş karşılaştırması yapan kariyer sitelerinde ve sektör raporlarında {bolum} ile ilgili meslek adını arat.",
            "En az 2 farklı kaynağa bak; her rakamın yanına kaynağın adını ve tarihini yaz.",
            "Ortalama ile uç değerleri (çok düşük ya da çok yüksek maaşlar) ayrı not et; uç değerler genelde özel durumları gösterir.",
            "Sonuçları bir aralık olarak yaz. Örneğin: \"Başlangıç: şu kadar ile şu kadar arası\".",
        ],
        "kontrol": [
            "Başlangıç maaşı için bir aralık yazdın.",
            "5 yıllık deneyim sonrası maaş için bir aralık yazdın.",
            "Rakamların en az 2 kaynağa dayanıyor ve kaynak adları not edilmiş.",
        ],
        "ipucu": "Tek bir kişinin paylaştığı maaşa güvenme; maaşlar şehre, kuruma ve yıla göre çok değişir, bu yüzden aralık yazmak önemli.",
    },
    "D2-G-2": {
        "nasil": [
            "Kendini 25 yaşında, tek başına yaşarken düşün. Bir sayfaya aylık gider listesi başlığı at.",
            "Kalemleri yaz: kira, faturalar, mutfak, ulaşım, telefon-internet, giyim, sosyal hayat, birikim.",
            "Her kalemin bugünkü yaklaşık tutarını ailene sorarak ya da internetten araştırarak yanına yaz.",
            "Hepsini topla; bu senin \"rahat ederim\" dediğin aylık ihtiyaç rakamın olacak.",
            "Bu rakamı “Gerçek maaşları öğren” adımında bulduğun maaş aralıklarıyla karşılaştır ve bir cümleyle not düş.",
        ],
        "kontrol": [
            "En az 6 kalemden oluşan bir aylık gider listen var.",
            "Kendi tahmini aylık ihtiyaç rakamını hesaplayıp yazdın.",
            "Bu rakamın bölümün maaş aralığına göre nerede durduğunu söyleyebiliyorsun.",
        ],
        "ipucu": "Birikim kalemini unutma; sık yapılan hata, yalnızca zorunlu giderleri yazıp toplamı olduğundan düşük bulmaktır.",
    },
    "D2-G-3": {
        "nasil": [
            "Bu alanda, özellikle özel sektörde çalışan birini bul: aile çevresi, öğretmenler ya da rehberlik servisinin yönlendirmesi.",
            "Kime ulaşacağını ailene ya da öğretmenine söyle; tanımadığın biriyle yalnızca onların bilgisi dahilinde, okulda ya da görüntülü görüşmeyle konuş.",
            "Sorularını hazırla. Örneğin: \"Aylık hedefleriniz var mı?\", \"Prim nasıl hesaplanıyor?\", \"Haftada kaç saat çalışıyorsunuz?\"",
            "Görüşmede kısa notlar al; özellikle temponun ve baskının nasıl anlatıldığına dikkat et.",
            "Görüşmeden sonra \"Bu tempo bana uygun mu?\" sorusunu yaz ve altına gerekçeli bir cevap ver.",
        ],
        "kontrol": [
            "Bu alanda çalışan biriyle görüşmeyi yaptın.",
            "Performans hedefleri, prim sistemi ve iş temposu hakkında notların var.",
            "\"Bu tempo bana uygun mu?\" sorusuna yazılı ve gerekçeli bir cevap verdin.",
        ],
        "ipucu": "Kimseyi bulamazsan okulunun rehberlik servisinden ya da öğretmenlerinden bu alanda çalışan bir tanıdık önermelerini isteyebilirsin.",
    },
    "D2-G-4": {
        "nasil": [
            "Bir sayfanın başına şu soruyu yaz: \"Maaş dışında beni bir işte ne mutlu eder?\"",
            "Aklına gelenleri sırala ve en önemli 3 tanesini seç. Örneğin: sürekli öğrenmek, saygı görmek, insanlara yardım etmek.",
            "Her kazanımın karşısına {bolum} alanında buna nerede rastlanabileceğini araştırıp yaz. Örneğin: \"İnsanlara yardım → hasta ya da danışanla birebir çalışma\".",
            "Bunun için bölümün ders listesine, mezun röportajlarına ve meslek tanıtımlarına bak.",
            "Karşılık bulamadığın kazanım varsa yanına \"?\" koy; bu senin için önemli bir sinyal.",
        ],
        "kontrol": [
            "Maaş dışındaki 3 kazanımını yazdın.",
            "Her kazanımın bölümdeki somut bir karşılığını eşleştirdin.",
            "Karşılık bulamadığın bir kazanım varsa bunu işaretledin.",
        ],
        "ipucu": "",
    },
    "D2-G-5": {
        "nasil": [
            "Bütçe, birikim ve yatırımın temellerini anlatan ücretsiz bir çevrim içi kurs ya da video serisi seç; BTK Akademi gibi ücretsiz platformlara ya da okul kütüphanesindeki kaynaklara bakabilirsin.",
            "Kursu küçük oturumlara böl ve her oturumdan sonra tarihli kısa bir not al.",
            "Her oturumda öğrendiğin bir kavramı (ör. gelir-gider dengesi, faiz, acil durum fonu) kendi cümlenle defterine yaz.",
            "Kurs ya da seri bitince kendi bütçe tablonu yap: harçlığın ya da gelirin, harcamaların ve biriktirmek istediğin tutar.",
        ],
        "kontrol": [
            "Seçtiğin kursu ya da video serisini bitirdin.",
            "Öğrendiğin en az 3 kavramı kendi cümlelerinle yazdın.",
            "Kendi gelir, gider ve birikim kalemlerinin olduğu bir bütçe tablon var.",
        ],
        "ipucu": "Yatırım konusunda gerçek para kullanmadan önce mutlaka ailenle konuş; kursun amacı öğrenmek, risk almak değil.",
    },
    "D2-G-6": {
        "nasil": [
            "Bu konudaki önceki adımlarda topladığın notları (maaş aralıkları, gider listen, görüşme notların, parasal olmayan kazanımlar) önüne koy.",
            "Kendine sor: \"Bu bölümün gelir yapısı benim aylık ihtiyacımı ve beklentimi karşılıyor mu?\" Cevabını evet, hayır ya da kısmen olarak yaz.",
            "Cevabın \"hayır\" ya da \"kısmen\" ise bölüm içindeki alt alanları (ör. akademi, kamu, özel sektör, sivil toplum) gelir ve tatmin açısından karşılaştır.",
            "Sana en uygun alt alanı seç ve 2-3 cümlelik bir gerekçe yaz. Örneğin: \"Kamu daha az kazandırır ama düzenli gelir benim için yeterli.\"",
        ],
        "kontrol": [
            "Gelir yapısının seninle uyumlu olup olmadığına dair yazılı bir cevabın var.",
            "Hedef alt alanını seçip yazdın.",
            "Seçiminin gerekçesi en az iki cümleyle açıklanmış.",
        ],
        "ipucu": "Bu karar kesin değil; önemli olan parayı ve diğer değerlerini birlikte düşünerek bilinçli bir tercih yapmak.",
    },
    "D2-U-1": {
        "nasil": [
            "{bolum} içindeki uzmanlık alanlarını ve çalışılan sektörleri listele; bölüm sayfaları ve meslek tanıtımları iyi bir başlangıç.",
            "Maaş karşılaştırma kaynaklarında ve sektör raporlarında bu alt alanların gelirlerine bak; en yüksek görünen 3 tanesini seç.",
            "Her biri için giriş şartlarını yaz: ek eğitim, yabancı dil, sertifika, deneyim süresi, şehir.",
            "Listenin yanına \"Bu alan bana ilgi çekici geliyor mu?\" sorusuna kısa bir cevap ekle.",
        ],
        "kontrol": [
            "En az 3 yüksek gelirli alt alanı listeledin.",
            "Her birinin giriş şartlarını yazdın.",
            "Hangisinin sana daha uygun göründüğünü bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Yüksek gelirli alanlar genelde daha uzun hazırlık ister; şartları yazarken süreyi de not etmeyi unutma.",
    },
    "D2-U-2": {
        "nasil": [
            "Gelirini artırabilecek ek becerilerden birini seç: yabancı dil, veri analizi (sayılarla bilgi çıkarma) ya da sunum becerisi.",
            "Seçimini yaparken {bolum} alanındaki iş ilanlarında en sık istenen beceriye bak.",
            "Ücretsiz ya da okulunun sunduğu bir kaynak bul (ör. BTK Akademi gibi ücretsiz platformlar, okul kulüpleri) ve ilk modülü belirle.",
            "Kendine 30-45 dakikalık çalışma oturumları belirle ve her oturumun tarihini yaz.",
            "Her oturumdan sonra ne öğrendiğini 2 cümleyle not et; ilk modülü bitirdiğinde kendine küçük bir ödül ver.",
        ],
        "kontrol": [
            "Öğrenmek için bir ek beceri seçtin ve nedenini yazdın.",
            "Çalışma oturumlarının tarihli kaydı var.",
            "Seçtiğin becerinin ilk modülünü ya da ilk seviyesini tamamladın.",
        ],
        "ipucu": "Aynı anda birden fazla beceriye başlamak yaygın bir hatadır; birini bitirmeden ikincisine geçme.",
    },
    "D3-G-1": {
        "nasil": [
            "Bir kâğıdı üç sütuna böl: Ailem, Öğretmenlerim, Ben.",
            "Her sütuna o tarafın senden ne beklediğini düşündüğünü yaz. Örneğin: \"Ailem: Saygın bir meslek, iyi bir üniversite.\"",
            "Her sütunda \"prestij\" (toplumda saygın görülme) ile ilgili beklentilerin altını çiz.",
            "Son olarak kendine sor: \"Bu bölümü kimse bilmeseydi yine seçer miydim?\" Cevabını \"Ben\" sütununun altına yaz.",
        ],
        "kontrol": [
            "Ailenin, öğretmenlerinin ve kendi beklentin üç ayrı sütunda yazılı.",
            "Prestijle ilgili beklentileri işaretledin.",
            "Prestijin seçiminde ne kadar etkili olduğunu bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Ailenin beklentisini tahmin ettiğinden emin değilsen \"bilmiyorum\" yaz; bu, “Aileyle açık konuşma” adımındaki konuşma için iyi bir soru olur.",
    },
    "D3-G-2": {
        "nasil": [
            "{bolum} mezunlarının bir iş gününü anlatan 2 içerik bul: \"bir günüm\" tarzı videolar ya da meslek röportajları.",
            "İçerikleri izlerken ya da okurken bir sayfaya saat saat ne yaptıklarını not al.",
            "Notlarından en çok tekrar eden 5 ana görevi seç ve madde madde yaz. Örneğin: \"Rapor yazmak\", \"Toplantıya katılmak\".",
            "Her görevin yanına sana keyifli mi, sıkıcı mı geldiğini yaz.",
        ],
        "kontrol": [
            "2 video ya da röportajı tamamladın.",
            "Bir iş gününün 5 ana görevini yazabiliyorsun.",
            "Bu görevlerden hangilerinin sana uygun olduğunu söyleyebiliyorsun.",
        ],
        "ipucu": "Sosyal medyadaki içerikler işi olduğundan parlak gösterebilir; farklı kaynaklardan en az iki kişiye bakmanın sebebi bu.",
    },
    "D3-G-3": {
        "nasil": [
            "Konuşmadan önce 3 maddelik bir not hazırla: Bu bölümde beni ne çekiyor, prestijden önce neyi önemsiyorum, neyi merak ediyorum.",
            "Ailenle sakin bir zaman seç (ör. hafta sonu bir yemek sonrası) ve 30 dakika konuşmak istediğini söyle.",
            "Önce kendi motivasyonunu anlat, sonra onlara sor: \"Bu bölümden benim için ne bekliyorsunuz?\" ve sözlerini kesmeden dinle.",
            "Konuşmadan sonra ortak noktaları ve farklı düşündüğünüz konuları iki ayrı liste olarak yaz.",
        ],
        "kontrol": [
            "Ailenle bu konuyu konuştun.",
            "Kendi motivasyonunu ve ailenin beklentisini yazılı olarak not ettin.",
            "En az bir ortak noktayı yazdın.",
        ],
        "ipucu": "Konuşma gerilirse ara verip başka bir gün devam edebilirsin; rehber öğretmeninden de bu konuşmaya hazırlanmak için destek isteyebilirsin.",
    },
    "D3-G-4": {
        "nasil": [
            "Bölüm seçiminde senin için önemli olan 5 kriter seç. Örneğin: ilgi, beceri, iş ortamı, gelir, şehir.",
            "Bir tablo yap: satırlara kriterleri, yanına \"Önem (1-5)\" ve \"Bölümün puanı (1-5)\" sütunlarını ekle.",
            "Her kriter için hedef bölümü 1-5 arası puanla; puan verirken daha önce topladığın bilgileri ve YÖK Atlas'taki bölüm bilgilerini kullan.",
            "Prestijin bu listede olmadığını fark et ve tablonun altına \"Prestij olmadan bu bölüm bana ne kadar uygun?\" sorusuna bir cümle yaz.",
        ],
        "kontrol": [
            "Prestij dışındaki 5 kriterini yazdın.",
            "Hedef bölümü her kritere göre 1-5 arası puanladın.",
            "Puanlara bakarak bölümün sana uyumunu bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "",
    },
    "D3-G-5": {
        "nasil": [
            "{bolum} mezunlarının çalıştığı daha az bilinen alanları listele: araştırma, danışmanlık, sivil toplum gibi.",
            "Bu alanlardan 2 tanesini seç ve her biri için bir video, röportaj ya da meslek tanıtım yazısı bul.",
            "Her alan için 3 soruya cevap yaz: Bu alanda ne iş yapılır? Hangi becerileri ister? Bana neden uygun olabilir?",
            "İki alanı kısa bir karşılaştırmayla bitir: hangisi seni daha çok meraklandırdı ve neden?",
        ],
        "kontrol": [
            "En az 2 alternatif alt alanı inceledin.",
            "Her biri için ne iş yapıldığını ve hangi becerileri istediğini yazdın.",
            "Hangisinin sana daha uygun olduğunu bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Bölüm sayfalarındaki öğretim üyelerinin çalışma alanları da bu alt alanları keşfetmek için iyi bir ipucu verir.",
    },
    "D3-G-6": {
        "nasil": [
            "“Prestij dışı kriterler” adımında belirlediğin 5 kriteri ve verdiğin puanları önüne koy.",
            "Önceki adımlarda öğrendiklerine göre puanlarda bir değişiklik olduysa güncelle.",
            "Kendine sor: \"Bu bölümü kimse duymasa, sadece kendi kriterlerime bakarak seçer miydim?\" Cevabını yaz.",
            "Kararını 3-4 cümlelik bir gerekçeyle yaz. Örneğin: \"Evet, çünkü ilgi ve beceri puanlarım yüksek.\"",
        ],
        "kontrol": [
            "Kriter puanlarını tekrar gözden geçirdin.",
            "Kararını kendi 5 kriterinle gerekçelendirip yazdın.",
            "Kararındaki gerekçe prestije değil kendi kriterlerine dayanıyor.",
        ],
        "ipucu": "Kararın değiştiyse bu başarısızlık değil; bilinçli düşündüğünü gösterir.",
    },
    "D3-U-1": {
        "nasil": [
            "Rol model, kariyer yolunu örnek aldığın kişidir. {bolum} alanında saygın bulduğun 2 kişi seç: bilinen biri ya da çevrenden biri olabilir.",
            "Onlar hakkında röportaj, biyografi, üniversite sayfası ya da LinkedIn profili gibi kaynakları oku.",
            "Her biri için bir zaman çizelgesi çiz: lise, üniversite, ilk iş, önemli adımlar ve şu anki konumu.",
            "Her zaman çizelgesinin altına \"Bu kişiden öğrendiğim en önemli adım\" başlığıyla bir cümle yaz.",
        ],
        "kontrol": [
            "İki rol modelinin kariyer adımlarını sırasıyla not ettin.",
            "Her biri için en az 4 önemli kariyer adımı yazılı.",
            "Kendi yolunda örnek alabileceğin bir adımı söyleyebiliyorsun.",
        ],
        "ipucu": "Yalnızca ünlü isimlere bakma; çevrendeki bir {bolum} mezunu da sana daha gerçekçi bir yol gösterebilir. LinkedIn'e üye olmak istemiyorsan ya da yaşın uygun değilse (LinkedIn'de en düşük üyelik yaşı 16) aynı araştırmayı röportajlar ve üniversitelerin mezun sayfalarıyla yapabilirsin.",
    },
    "D3-U-2": {
        "nasil": [
            "Okulunda duyurulan yarışma, olimpiyat ve proje fırsatlarını rehberlik servisine ya da ilgili öğretmene sor.",
            "{bolum} alanına en yakın olanı seç (ör. TÜBİTAK 2204 Lise Öğrencileri Araştırma Projeleri) ve başvuru şartlarını oku.",
            "Bir danışman öğretmen bul; çoğu proje yarışmasında öğretmen desteği gerekir.",
            "Son başvuru tarihinden geriye doğru bir hazırlık takvimi yap: konu seçimi, araştırma, yazım ve kontrol aşamaları.",
            "Takvimi öğretmeninle paylaş ve ilk aşamanın işine başla.",
        ],
        "kontrol": [
            "Bölümüne yakın bir yarışma, olimpiyat ya da proje seçtin.",
            "Başvurunu yaptın ya da aşamalara bölünmüş bir hazırlık takvimin var.",
            "Bir danışman öğretmenle konuştun.",
        ],
        "ipucu": "Başvuru tarihleri her yıl değişebilir; tarihi her zaman yarışmayı düzenleyen kurumun resmî sayfasından kontrol et.",
    },
    "D4-G-1": {
        "nasil": [
            "Bir kâğıda aynı cümle başlangıcını 3 kez alt alta yaz: \"{bolum} okumak istiyorum çünkü...\"",
            "Her birini farklı bir yönden tamamla: biri ilgine, biri gelecekteki işine, biri insanlara ya da dünyaya etkisine dair olsun.",
            "Yazarken kendini sansürleme; ilk aklına geleni yaz.",
            "Üç cümleyi sesli oku ve sana en samimi geleni işaretle; yanına neden onu seçtiğini bir kelimeyle yaz.",
        ],
        "kontrol": [
            "\"{bolum} okumak istiyorum çünkü...\" cümlesini 3 farklı şekilde tamamladın.",
            "Sana en doğru gelen bir \"neden\" cümlesini işaretledin.",
            "Bu cümleyi birine sorulduğunda rahatça söyleyebiliyorsun.",
        ],
        "ipucu": "Üç cümleyi de doldurmakta zorlanıyorsan bu da bir bilgi; bölümle ilgili daha fazla keşif yapman gerektiğini gösterebilir.",
    },
    "D4-G-2": {
        "nasil": [
            "{bolum} alanında çalışmış birini seç: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir röportaj bul.",
            "Okurken ya da izlerken 3 soruyu not et: Ne yaptı? Kime ya da neye faydası oldu? Bu iş ona ne anlam kattı?",
            "İşinin insanlara ya da dünyaya etkisini gösteren somut bir örneği ayrıca yaz.",
            "Sonra kâğıda bakmadan bu etkiyi ve işin ona kattığı anlamı 3-4 cümleyle kendi sözlerinle yaz ya da birine anlat.",
        ],
        "kontrol": [
            "Bu alanda çalışmış birinin hayat hikâyesini okudun ya da izledin.",
            "Bu kişinin yarattığı bir etkiyi somut bir örnekle yazdın.",
            "İşin ona kattığı anlamı kendi cümlelerinle anlatabiliyorsun.",
        ],
        "ipucu": "Ünlü olmayan ama işini yıllarca özenle yapmış biri de iyi bir örnektir; yerel gazetelerin röportajlarına da bakabilirsin.",
    },
    "D4-G-3": {
        "nasil": [
            "Bir {bolum} mezunu bul: akrabalar, aile dostları, öğretmenler ya da rehberlik servisinin yönlendirdiği biri.",
            "Kime ulaşacağını ailene ya da öğretmenine söyle; tanımadığın biriyle yalnızca onların bilgisi dahilinde, okulda ya da görüntülü görüşmeyle konuş.",
            "Ana sorun hazır: \"İşinizde sizi en çok ne tatmin ediyor?\" Yanına 2 ek soru ekle. Örneğin: \"Hangi anlarda işinizden sıkılıyorsunuz?\"",
            "Cevabını mümkün olduğunca onun kelimeleriyle not al.",
            "Görüşmeden sonra kendine sor: \"Bu tatmin beni de mutlu eder mi?\" Cevabını 2 cümleyle yaz.",
        ],
        "kontrol": [
            "Bir {bolum} mezunuyla görüştün ve tatmin sorusunu sordun.",
            "Aldığın cevabı not ettin.",
            "Bu cevabın sana uyup uymadığını yazılı olarak değerlendirdin.",
        ],
        "ipucu": "Kimseyi bulamazsan okulunun rehberlik servisinden ya da öğretmenlerinden bu alanda çalışan bir tanıdık önermelerini isteyebilirsin.",
    },
    "D4-G-4": {
        "nasil": [
            "Değer haritası, önemli bulduğun şeyleri bölümle eşleştirdiğin bir şemadır. Kâğıdın soluna \"Değerlerim\", sağına \"{bolum}'deki karşılığı\" yaz.",
            "Hayatta önemli bulduğun 5 şeyi seç ve önem sırasına göre sola yaz. Örneğin: adalet, aile, öğrenmek, özgürlük, yardım etmek.",
            "Her değer için bölümde ya da meslekte buna nerede rastlanabileceğini sağ tarafa yaz ve okla bağla.",
            "Karşılık bulamadığın değerin yanına \"?\" koy ve bunu nasıl karşılayabileceğini (ör. hobi, gönüllülük) kısaca not et.",
        ],
        "kontrol": [
            "Önem sırasına göre dizilmiş 5 değerin var.",
            "5 değerin her birini bölümdeki bir karşılıkla eşleştirdin ya da karşılığı olmadığını işaretledin.",
            "Bölümün değerlerinle ne kadar uyuştuğunu bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Değer bulmakta zorlanırsan kendine \"Beni en çok ne kızdırır?\" diye sor; kızdığın şey çoğu zaman önemsediğin bir değerin çiğnenmesidir.",
    },
    "D4-G-5": {
        "nasil": [
            "Bu alanla ilgili, birine faydası dokunacak küçük bir proje fikri seç. Örneğin: arkadaşlarına bir konuyu anlatan sunum ya da bir kulüp etkinliği.",
            "Projeyi kimin için yaptığını ve onlara ne kazandıracağını bir cümleyle yaz.",
            "İşi 3-4 adıma böl (hazırlık, malzeme, uygulama, paylaşım) ve her birine tarih ver; okulda yapacaksan öğretmeninden onay al.",
            "Projeyi uygula; mümkünse katılanlardan kısa bir geri bildirim iste.",
            "Bitirince \"Bu proje bana nasıl hissettirdi?\" sorusuna en az 3 cümle yaz.",
        ],
        "kontrol": [
            "Birine faydası dokunan küçük bir projeyi tamamladın.",
            "Projenin kime ne kazandırdığını yazabiliyorsun.",
            "Projenin sana nasıl hissettirdiğini en az 3 cümleyle yazdın.",
        ],
        "ipucu": "Projeyi küçük tut; kısa sürede bitirebileceğin basit bir iş, yarım kalan büyük bir projeden daha çok şey öğretir.",
    },
    "D4-G-6": {
        "nasil": [
            "Bu iş için bir defter ya da telefonunda bir not dosyası aç ve adını \"Anlam günlüğü\" koy.",
            "Bu alana dair seni heyecanlandıran ya da sıkan bir an yaşadığında (bir ders, bir haber, bir sohbet) o gün kısa bir not al; tarihi yaz.",
            "Her notu iki başlıktan birine koy: \"Beni heyecanlandıran an\" ya da \"Beni sıkan an\". 2-3 cümle yeter.",
            "En az 6 not biriktiğinde hepsini oku ve tekrar eden durumların altını çiz.",
            "Fark ettiğin örüntüyü tek cümleyle yaz. Örneğin: \"İnsanlarla çalıştığım anlar beni heyecanlandırıyor, ezber kısmı sıkıyor.\"",
        ],
        "kontrol": [
            "Günlüğünde en az 6 tarihli not var.",
            "Notlarda hem heyecanlandıran hem sıkan anlar bulunuyor.",
            "Fark ettiğin bir örüntüyü tek cümleyle yazdın.",
        ],
        "ipucu": "Amaç bu alanın sana anlamlı gelip gelmediğini fark etmek; bir anı kaçırırsan hatırladığın kadarını sonradan yazman da olur.",
    },
    "D4-U-1": {
        "nasil": [
            "{bolum} alanında çalışılabilecek konuları listele. Örneğin: çocuklar, çevre, adalet, teknoloji, sağlık.",
            "Her konunun yanına 1-5 arası bir puan ver: \"Bu konuda çalışmak bana ne kadar anlamlı geliyor?\"",
            "En yüksek puanlı alt alanı seç.",
            "Neden seçtiğini 2-3 cümleyle yaz. Örneğin: \"Çocuklarla çalışmak bana anlamlı geliyor çünkü küçük kardeşime ders anlatırken mutlu oluyorum.\"",
        ],
        "kontrol": [
            "Bir alt alan seçtin.",
            "Seçiminin nedenini en az 2 cümleyle yazdın.",
        ],
        "ipucu": "Karar veremiyorsan iki alt alanı birlikte not et; “Anlamı deneyime çevir” adımındaki deneyim hangisinin sana uygun olduğunu netleştirebilir.",
    },
    "D4-U-2": {
        "nasil": [
            "Seçtiğin alt alanla ilgili gönüllülük ya da gözlem fırsatlarını araştır: okul kulüpleri, belediyenin gençlik etkinlikleri ya da yerel derneklerin açık etkinlikleri.",
            "Okulun rehberlik servisine danış; güvenilir ve yaşına uygun fırsatları bulmana yardım edebilir.",
            "Katılmadan önce ailenle konuş ve etkinliğin yaş şartını, gerekiyorsa veli iznini kontrol et.",
            "Bir etkinliğe katıl ve sonrasında 3 soruya cevap yaz: Ne yaptım? Ne gözlemledim? Bana anlamlı geldi mi?",
        ],
        "kontrol": [
            "Seçtiğin alt alanla ilgili en az bir etkinliğe ailenin bilgisiyle katıldın.",
            "Etkinliğin sana ne kattığını yazdın.",
            "Bu deneyimin alt alan seçimini destekleyip desteklemediğini söyleyebiliyorsun.",
        ],
        "ipucu": "İlk ulaştığın yerden hemen cevap gelmeyebilir; birkaç seçeneği birlikte değerlendirmek işini kolaylaştırır.",
    },
    "D5-G-1": {
        "nasil": [
            "Bir sayfayı 3 bölüme ayır: Proje, Kurum, Kişi.",
            "{bolum} mezunlarının topluma katkı sağladığı örnekleri ara: haberler, üniversitelerin bölüm sayfaları, sivil toplum kuruluşlarının çalışmaları.",
            "Her bölüme bir örnek yaz ve 2 soruyu cevapla: Ne yapıldı? Kime fayda sağladı?",
            "Bu 3 örnekten sana en çok dokunanı işaretle.",
        ],
        "kontrol": [
            "Topluma katkı sağlayan 3 örneği kısaca not ettin.",
            "Her örnek için ne yapıldığını ve kime fayda sağladığını yazdın.",
            "Sana en çok dokunan örneği seçtin.",
        ],
        "ipucu": "Haberlerde adı geçen projelerin resmî sayfalarına da bakarsan bilginin doğru olup olmadığını kontrol etmiş olursun.",
    },
    "D5-G-2": {
        "nasil": [
            "Bir kâğıda üç katkı biçimini yaz: tek tek insanlara yardım etmek, sistemleri iyileştirmek, bilgi üretmek.",
            "Her birine örnek düşün. Örneğin: hastayı tedavi etmek, hastane düzenini iyileştirmek, yeni bir tedavi yöntemi araştırmak.",
            "Kendine sor: \"Hangisini yaparken daha çok enerji hissederim?\" ve birini seç.",
            "Seçiminin yanına bir cümlelik neden yaz.",
        ],
        "kontrol": [
            "Sana uyan bir katkı biçimini seçtin.",
            "Seçiminin nedenini bir cümleyle yazdın.",
        ],
        "ipucu": "Üçü de iyi bir katkıdır; burada doğru-yanlış yok, sadece senin tarzını bulmaya çalışıyorsun.",
    },
    "D5-G-3": {
        "nasil": [
            "Yaşına uygun, tek günlük bir gönüllülük etkinliği ara: okulun sosyal sorumluluk kulübü, belediyenin ya da yerel bir derneğin düzenlediği bir etkinlik. Okul duyurularına ve rehberlik servisine bak.",
            "Katılmadan önce ailene bilgi ver ve etkinliğin yaş şartını kontrol et; mümkünse bir arkadaşınla ya da okul kulübüyle birlikte git.",
            "Etkinlik günü ne yaptığını, kimlerle tanıştığını ve nasıl hissettiğini aklında tut ya da telefonuna kısa notlar al.",
            "Eve dönünce 5-6 cümlelik bir değerlendirme yaz: Ne yaptım? Beni ne mutlu etti? Ne yordu? Tekrar yapar mıydım?",
        ],
        "kontrol": [
            "Ailenin bilgisiyle bir gönüllülük etkinliğine katıldın.",
            "Ne yaptığını ve nasıl hissettiğini anlatan kısa bir değerlendirme yazdın.",
            "Bu deneyimin sana nasıl hissettirdiğini birine anlatabiliyorsun.",
        ],
        "ipucu": "Uygun etkinlik bulamazsan okulunun rehberlik servisine ya da sosyal sorumluluk kulübüne sor.",
    },
    "D5-G-4": {
        "nasil": [
            "Bu alanda çalışan birini bul: aile çevresi, öğretmenler ya da rehberlik servisinin yönlendirdiği biri.",
            "Kime ulaşacağını ailene ya da öğretmenine söyle; tanımadığın biriyle yalnızca onların bilgisi dahilinde, okulda ya da görüntülü görüşmeyle konuş.",
            "Asıl sorunu sor: \"Bir iş gününüzün ne kadarı insanlarla ya da toplumla ilgili?\" Kabaca bir oran ya da saat iste.",
            "Ek sorular sor. Örneğin: \"Bu kısım size nasıl hissettiriyor?\", \"Geri kalan zamanda ne yapıyorsunuz?\"",
            "Görüşmeden sonra öğrendiğin oranı ve bunun sana uygun olup olmadığını yaz.",
        ],
        "kontrol": [
            "Bu alanda çalışan biriyle görüştün.",
            "Hizmet yönünün işteki oranını (ör. \"günün yarısı\") not ettin.",
            "Bu oranın sana uygun olup olmadığını yazdın.",
        ],
        "ipucu": "Kimseyi bulamazsan okulunun rehberlik servisinden ya da öğretmenlerinden bu alanda çalışan bir tanıdık önermelerini isteyebilirsin.",
    },
    "D5-G-5": {
        "nasil": [
            "2-3 arkadaşınla bir araya gel ve okulda çözmek istediğiniz küçük bir sorun seçin. Örneğin: kitap toplama, akran mentorluğu, çevre temizliği.",
            "Akran mentorluğu gibi bir fikir seçerseniz ne yapacağınızı netleştirin: örneğin üst sınıfların alt sınıflara ders çalışmada yardım etmesi.",
            "Projeyi bir öğretmene ya da okul idaresine anlatıp onay ve destek alın.",
            "Görev dağılımı ve tarih içeren basit bir plan yapın; ilk uygulama tarihini belirleyin.",
            "Projeyi en az bir kez hayata geçirin ve sonrasında neyin iyi gittiğini, neyin değişmesi gerektiğini birlikte konuşun.",
        ],
        "kontrol": [
            "Okul onayı alınmış bir sosyal sorumluluk projesi planınız var.",
            "Proje en az bir kez hayata geçti.",
            "Projede senin üstlendiğin görevi ve öğrendiklerini yazabiliyorsun.",
        ],
        "ipucu": "Okulunda zaten bir sosyal sorumluluk kulübü varsa sıfırdan başlamak yerine onunla birlikte çalışabilirsin.",
    },
    "D5-G-6": {
        "nasil": [
            "Bu konudaki önceki adımlarda aldığın notları (gönüllülük değerlendirmen, görüşme notların, proje deneyimin) önüne koy.",
            "İki soruya cevap yaz: \"İnsanlarla birebir çalışmak beni besledi mi, yordu mu?\" ve \"Hangi anlarda kendimi en iyi hissettim?\"",
            "{bolum} içindeki alt alanları hizmet yoğun ve daha teknik/bağımsız olarak ikiye ayır.",
            "Hangi alt alana yöneleceğini seç ve 2-3 cümlelik bir gerekçe yaz.",
        ],
        "kontrol": [
            "Deneyimlerini gözden geçirip iki soruya yazılı cevap verdin.",
            "Yöneleceğin alt alanı seçtin.",
            "Seçimini deneyimlerine dayanan bir gerekçeyle yazdın.",
        ],
        "ipucu": "",
    },
    "D5-U-1": {
        "nasil": [
            "Aklına gelen toplumsal sorunları listele. Örneğin: eğitim eşitsizliği, sağlık, çevre, yaşlı bakımı.",
            "Her birinin yanına \"{bolum} ile bu soruna nasıl katkı sağlanabilir?\" sorusuna kısa bir cevap yaz.",
            "Hem seni önemseyen hem de bölümle en çok bağlantılı olan sorunu seç.",
            "Bu sorunun neden önemli olduğunu 2-3 cümleyle yaz.",
        ],
        "kontrol": [
            "Bir toplumsal sorun seçtin.",
            "Bu sorunun neden önemli olduğunu yazdın.",
            "Bölümünün bu soruna nasıl katkı sağlayabileceğini bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "",
    },
    "D5-U-2": {
        "nasil": [
            "“Etki alanını belirle” adımında seçtiğin sorunla ilgili çalışan yerleri araştır: okul kulüpleri, belediye ya da yerel dernekler. Okulun rehberlik servisine de danış.",
            "Gönüllülük şartlarını ve yaş sınırını kontrol et; ailenle konuşarak yaşına uygun bir yer seç.",
            "Her katıldığında tarihi yaz ve 2-3 cümlelik not al: Ne yaptım, ne öğrendim?",
            "En az 3 katılım biriktiğinde notlarını oku ve bu işi sürdürmek isteyip istemediğini bir cümleyle yaz.",
        ],
        "kontrol": [
            "Seçtiğin sorunla ilgili bir yerde ailenin bilgisiyle gönüllü oldun.",
            "En az 3 katılımın tarihiyle kayıtlı.",
            "Her katılım için kısa notların var.",
        ],
        "ipucu": "Düzenli gitmek ilk katılımdan daha zordur; bir arkadaşla gitmek devam etmeyi kolaylaştırır.",
    },
    "D6-G-1": {
        "nasil": [
            "Normalde ailene, arkadaşına ya da öğretmenine soracağın küçük bir konu seç. Örneğin: hangi dersi önce çalışacağın ya da proje konun.",
            "Kararı vermeden önce seçenekleri ve artı-eksilerini kendin düşün; kimseye danışmadan kararını ver.",
            "Kararını ve neden öyle karar verdiğini bir cümleyle, tarihiyle yaz.",
            "Sonuç belli olunca not et: Ne oldu? Kendi kararımı vermek nasıl hissettirdi? Tekrar olsa yine öyle yapar mıydım?",
            "Bu bir deneme; amaç kendi kararını vermenin sana nasıl geldiğini görmek. Sonunda \"Kararları kendim vermek benim için ne kadar önemli?\" sorusuna 1-2 cümleyle cevap yaz.",
        ],
        "kontrol": [
            "Kendi verdiğin küçük bir kararı yazdın.",
            "Kararın sonucunu not ettin.",
            "Kendi kararını vermenin sana nasıl hissettirdiğini söyleyebiliyorsun.",
        ],
        "ipucu": "Önemli ya da riskli konularda değil, küçük konularda dene; amaç bağımsız karar vermenin sana nasıl geldiğini gözlemlemek.",
    },
    "D6-G-2": {
        "nasil": [
            "Bir tablo hazırla: sütunlara serbest çalışma, danışmanlık ve kurumsal çalışma; satırlara çalışma saatleri, gelir düzeni, kararları kim veriyor, risk.",
            "Serbest çalışma kendi müşterilerini bulmak, danışmanlık uzmanlığını başka kurumlara sunmak, kurumsal çalışma bir şirkette maaşlı çalışmaktır.",
            "{bolum} alanında bu üç biçimi anlatan meslek tanıtımları, röportajlar ya da videolar bul ve tabloyu doldur.",
            "Tablonun altına her biçimin en büyük farkını birer cümleyle yaz.",
        ],
        "kontrol": [
            "Üç çalışma biçimini karşılaştıran bir tablon var.",
            "Üç çalışma biçiminin farkını kendi sözlerinle anlatabiliyorsun.",
            "Hangisinin sana daha uygun göründüğünü söyleyebiliyorsun.",
        ],
        "ipucu": "",
    },
    "D6-G-3": {
        "nasil": [
            "Kimsenin sana görev olarak vermediği, ilgini çeken küçük bir proje seç. Örneğin: bir konuda kısa yazı dizisi ya da mini bir araştırma.",
            "Hedefini bir cümleyle yaz. Örneğin: \"Bu konuda 4 kısa yazı yazacağım.\"",
            "Projeyi aşamalara böl (ör. konu seçimi, araştırma, yazma, son okuma) ve her aşamada ne yapacağını kendin belirle.",
            "Her aşama bitince tarihli kısa bir not al; plan tutmadıysa kendin güncelle.",
            "Projeyi bitirince en zor ve en keyifli kısmı birer cümleyle not et.",
        ],
        "kontrol": [
            "Aşamaların ve her birinin tamamlanma tarihinin yazılı olduğu bir planın var.",
            "Projeyi baştan sona kendin planlayıp bitirdin.",
            "Bağımsız çalışmanın en zor ve en keyifli yanını yazabiliyorsun.",
        ],
        "ipucu": "İnternette bir şey paylaşacaksan kişisel bilgilerini (adres, okul, telefon) yazma ve paylaşımı ailenle konuş.",
    },
    "D6-G-4": {
        "nasil": [
            "Önündeki birkaç günün ders çalışma planını kimseye sormadan kendin hazırla: hangi gün, hangi ders, ne kadar süre.",
            "Plan yaparken Pomodoro tekniğini deneyebilirsin: 25 dakika odaklanıp çalış, 5 dakika mola ver; 4 turdan sonra uzun mola ver.",
            "Planı defterine ya da telefonuna yaz ve uyguladıkça yaptıklarını işaretle.",
            "Her planın sonunda 3 soruya cevap yaz: Planın ne kadarına uydum? Ne işe yaradı? Bir sonraki planda neyi değiştireceğim?",
            "En az 3 plan biriktiğinde değerlendirmelerini birlikte oku ve \"Kendi düzenimi kendim kurmak benim için ne kadar önemli?\" sorusuna 1-2 cümleyle cevap yaz.",
        ],
        "kontrol": [
            "Kendi hazırladığın en az 3 çalışma planın var.",
            "Her planın sonunda yazılmış kısa bir değerlendirmen var.",
            "Kendi planını yapmanın sana uyup uymadığını söyleyebiliyorsun.",
        ],
        "ipucu": "İlk planlar genelde çok yüklü olur; bir plan tutmadıysa sonrakini hafiflet, kendini suçlama.",
    },
    "D6-G-5": {
        "nasil": [
            "{bolum} alanında serbest ya da kendi işini yapan birini bul: aile çevresi, öğretmenler ya da rehberlik servisinin yönlendirdiği biri.",
            "Kime ulaşacağını ailene ya da öğretmenine söyle; tanımadığın biriyle yalnızca onların bilgisi dahilinde, okulda ya da görüntülü görüşmeyle konuş.",
            "Sorularını hazırla. Örneğin: \"Müşteri bulmak nasıl?\", \"Geliriniz her ay aynı mı?\", \"Tatile çıkınca iş ne oluyor?\"",
            "Görüşme sırasında artıları ve eksileri iki ayrı sütuna not al.",
            "Görüşmeden sonra listeyi temize çek ve en çok dikkatini çeken sorumluluğu işaretle.",
        ],
        "kontrol": [
            "Bağımsız çalışan biriyle görüştün.",
            "Bağımsız çalışmanın artılarını ve eksilerini iki ayrı liste olarak yazdın.",
            "Özgürlüğün getirdiği en az bir sorumluluğu söyleyebiliyorsun.",
        ],
        "ipucu": "Kimseyi bulamazsan okulunun rehberlik servisinden ya da öğretmenlerinden bu alanda çalışan bir tanıdık önermelerini isteyebilirsin.",
    },
    "D6-G-6": {
        "nasil": [
            "Bu konudaki önceki adımlarda aldığın notları (kendi kararın, kendi projen, çalışma planların, görüşme notların) önüne koy.",
            "Kendine sor: \"Kendi planımı yaparken mi, net görevler verildiğinde mi daha iyi çalıştım?\" Cevabını yaz.",
            "Üç seçenekten birini seç: yapılandırılmış kurum, yarı bağımsız rol ya da tamamen bağımsız çalışma.",
            "Seçimini deneyimlerinden en az bir örnekle gerekçelendir.",
        ],
        "kontrol": [
            "Tercih ettiğin çalışma ortamını yazdın.",
            "Seçimini deneyimlerinden bir örnekle gerekçelendirdin.",
        ],
        "ipucu": "Tek bir doğru ortam yoktur; aynı bölümde farklı ortamlarda çalışan insanlar bulunur.",
    },
    "D6-U-1": {
        "nasil": [
            "{bolum} alanında serbest çalışan ya da girişim (kendi işini kurmak) yapan 2 kişi bul; haber, röportaj, LinkedIn (yaşın uygunsa) ya da girişimcilik videoları iyi kaynaklardır.",
            "Her biri için not al: Ne iş yapıyor? Bu noktaya nasıl geldi? Ne zaman bağımsız çalışmaya başladı?",
            "İki kişinin yolunu karşılaştır: ortak yönleri neler, farkları neler?",
            "Sana en ilginç gelen ayrıntıyı bir cümleyle yaz.",
        ],
        "kontrol": [
            "İki bağımsız kariyer örneğini not ettin.",
            "Her birinin bu noktaya nasıl geldiğini yazdın.",
            "İki örnek arasındaki bir benzerliği ve bir farkı söyleyebiliyorsun.",
        ],
        "ipucu": "LinkedIn'e üye olmak istemiyorsan ya da yaşın uygun değilse (LinkedIn'de en düşük üyelik yaşı 16) aynı araştırmayı röportajlar ve üniversitelerin mezun sayfalarıyla yapabilirsin.",
    },
    "D6-U-2": {
        "nasil": [
            "Bu alana yakın, yaşına uygun küçük bir iş fikri seç. Örneğin: küçüklere ders vermek, tasarım yapmak, içerik üretmek.",
            "Ailenle konuş ve onay al; para alacaksan fiyatı, zamanı ve yeri birlikte belirleyin.",
            "İlk müşterini güvenli çevrende ara: aile dostları, komşular, okul çevresi. Tanımadığın kişilerle ailen olmadan buluşma.",
            "İşi tamamladıktan sonra müşterinden kısa bir geri bildirim iste.",
            "Ne kadar sürdüğünü, ne öğrendiğini ve bir dahakine neyi farklı yapacağını yaz.",
        ],
        "kontrol": [
            "Ailenin bilgisi dahilinde küçük bir iş ya da girişim başlattın.",
            "İlk işini ya da ilk müşterini tamamladın.",
            "Deneyimden öğrendiklerini yazdın.",
        ],
        "ipucu": "İlk işte mükemmel olmaya çalışma; amaç kendi işini yürütmenin sana nasıl geldiğini görmek.",
    },
    "D7-G-1": {
        "nasil": [
            "{bolum} alanında yaratıcılığın kullanıldığı örnekleri ara: tasarımlar, projeler, sunumlar, yarışma ödüllü işler.",
            "Arama yaparken \"{bolum}\" ile birlikte \"proje örnekleri\", \"tasarım\" ya da \"yaratıcı çalışma\" kelimelerini kullanabilirsin.",
            "3 örnek seç ve her biri için not al: Ne yapılmış? Yaratıcılık nerede kullanılmış? Beni neden etkiledi?",
            "En çok etkilendiğin örneği işaretle.",
        ],
        "kontrol": [
            "3 yaratıcı örneği kısaca not ettin.",
            "Her örnekte yaratıcılığın nerede kullanıldığını yazdın.",
            "Bu alanın yaratıcı yönünü bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "",
    },
    "D7-G-2": {
        "nasil": [
            "Yapacağın küçük yaratıcı işi seç: bir poster, kısa bir sunum tasarımı ya da 5-6 fotoğraflık bir seri.",
            "Konusunu belirle; mümkünse {bolum} ile ilgili bir konu seç. Örneğin: bölümün ne iş yaptığını anlatan bir poster.",
            "1-2 saatlik bir zaman ayır ve elindeki araçlarla (kâğıt-kalem, telefon, ücretsiz tasarım uygulamaları) üret.",
            "Bitirince ürünü kaydet ya da fotoğrafla ve yaparken ne hissettiğini bir cümleyle yaz.",
        ],
        "kontrol": [
            "Bitmiş bir yaratıcı ürünün var.",
            "Ürünü kaydettin ya da fotoğrafladın.",
            "Üretirken ne hissettiğini söyleyebiliyorsun.",
        ],
        "ipucu": "Mükemmel olmasına gerek yok; burada amaç üretme sürecinden keyif alıp almadığını görmek.",
    },
    "D7-G-3": {
        "nasil": [
            "Bölgendeki kısa tasarım ya da sanat atölyelerini araştır: halk eğitim merkezleri, belediye atölyeleri, okul kulüpleri ya da çevrim içi kurslar.",
            "Süresi 1-2 ayı aşmayan, ders programına uyan birini seç ve kayıt için ailenle konuş.",
            "Her dersten sonra öğrendiğin bir tekniği ya da fikri bir deftere yaz.",
            "Atölye boyunca yaptığın işleri saklayıp portfolyo klasörüne ekle.",
        ],
        "kontrol": [
            "Bir tasarım ya da sanat atölyesine kayıt oldun.",
            "Atölyeyi tamamladın.",
            "Atölyede öğrendiğin en az 2 tekniği söyleyebiliyorsun.",
        ],
        "ipucu": "Kayıt dönemlerini kaçırmamak için halk eğitim merkezlerinin dönem başı duyurularını takip et.",
    },
    "D7-G-4": {
        "nasil": [
            "Telefonunda \"Estetik gözlem\" adlı bir albüm ya da not dosyası aç.",
            "Sana güzel gelen tasarımları fotoğrafla: bir uygulama ekranı, bir bina, bir afiş, bir ürün ambalajı.",
            "Her fotoğrafın altına bir cümle yaz: \"Bunu güzel buldum çünkü…\" Örneğin: \"…renkler sade ve yazı kolay okunuyor.\"",
            "10 örnek toplayınca notlarını oku ve en çok tekrar eden beğeni nedenini bul.",
            "Sonunda \"Güzel ve özenli tasarlanmış şeylerle uğraşmak benim için ne kadar önemli?\" sorusuna 1-2 cümleyle cevap yaz.",
        ],
        "kontrol": [
            "En az 10 tasarım örneğinin fotoğrafı var.",
            "Her örneğin yanında neden güzel bulduğuna dair kısa bir not var.",
            "Neyi güzel bulduğuna dair ortak bir eğilimi söyleyebiliyorsun.",
        ],
        "ipucu": "Kişilerin yüzünü ya da özel alanları fotoğraflama; tasarıma, nesneye ve mekâna odaklan.",
    },
    "D7-G-5": {
        "nasil": [
            "Bölümle ilgili görsel olarak anlatmak istediğin bir konu seç.",
            "Ürün biçimini seç: infografik (bilgiyi kısa yazı, ikon ve grafikle anlatan görsel), maket ya da sunum.",
            "Önce kâğıda kaba bir taslak çiz; hangi bilgiler nerede olacak, karar ver.",
            "İşi aşamalara böl (araştırma, taslak, üretim, düzeltme) ve her aşama bitince tarihini yaz.",
            "Bitirince ürünü bir öğretmenine, ailene ya da arkadaşlarına göster ve bir geri bildirim not et.",
        ],
        "kontrol": [
            "Bölümle ilgili bir konuyu görsel olarak anlatan bir ürünü bitirdin.",
            "Ürünü en az bir kişiye gösterdin.",
            "Aldığın geri bildirimi not ettin.",
        ],
        "ipucu": "İnternetten aldığın görsel ya da bilgilerin kaynağını ürünün bir köşesine yazmayı unutma.",
    },
    "D7-G-6": {
        "nasil": [
            "Bu konudaki önceki adımlarda yaptığın işleri ve notlarını (yaratıcı deneme, atölye, gözlem albümü, mini proje) önüne koy.",
            "Kendine sor: \"Bu işlerin hangisinde zamanın nasıl geçtiğini anlamadım?\" ve cevabını yaz.",
            "Bölümün yaratıcı kısmından ne kadar keyif aldığını 1-5 arası puanla.",
            "Kararını 2-3 cümleyle yaz: bu bölümün yaratıcı yönü sana uygun mu, yoksa yaratıcılığı hobi olarak mı sürdürmek istersin?",
        ],
        "kontrol": [
            "Deneyimlerini gözden geçirip keyif puanını verdin.",
            "Kararını önceki adımlardan 2 örnekle gerekçelendirip yazdın.",
        ],
        "ipucu": "Yaratıcılığı meslek yapmasan da hobi olarak sürdürmek de geçerli ve değerli bir sonuçtur.",
    },
    "D7-U-1": {
        "nasil": [
            "Portfolyo, yaptığın işleri bir arada gösteren dosyadır. Bilgisayarında, telefonunda ya da bulut depolamada \"Portfolyo\" adlı bir klasör aç.",
            "Daha önce yaptığın yaratıcı işleri bul: çizimler, fotoğraflar, sunumlar, projeler. Kâğıt üzerindekilerin fotoğrafını çek.",
            "Her dosyayı tarih ve kısa adla kaydet. Örneğin: \"2026-10_bolum-posteri\".",
            "Klasöre en az 5 iş ekle; bundan sonra her yeni iş bitince onu da ekle.",
        ],
        "kontrol": [
            "\"Portfolyo\" adlı bir klasörün var.",
            "Klasörde en az 5 işin bulunuyor.",
            "Dosyalar tarih ve kısa adla düzenli şekilde kaydedilmiş.",
        ],
        "ipucu": "Önemli işlerin kaybolmaması için klasörün bir yedeğini de al.",
    },
    "D7-U-2": {
        "nasil": [
            "{bolum} ile ilgili, yaratıcı bir ürünle anlatmak istediğin bir konu seç: afiş, video, maket, infografik ya da fotoğraf serisi.",
            "Ürününü gönderebileceğin okul içi ya da okullar arası bir yarışma veya sergi bul; öğretmenlerine ve rehberlik servisine sor.",
            "Yarışmanın şartlarını (konu, boyut, son tarih) oku ve son tarihten geriye doğru bir hazırlık takvimi yap.",
            "Ürünü tamamla, bir öğretmenine göstererek son düzeltmeleri yap.",
            "Ürünü yarışmaya gönder ya da okul panosu, sergi gibi bir yerde paylaş.",
        ],
        "kontrol": [
            "{bolum} ile ilgili yaratıcı bir ürünü tamamladın.",
            "Ürünü bir yarışmaya gönderdin ya da bir yerde paylaştın.",
            "Ürünü portfolyo klasörüne ekledin.",
        ],
        "ipucu": "Uygun bir yarışma bulamazsan okulda bir sergi düzenlemeyi öğretmenine önerebilirsin.",
    },
    "P1-G-1": {
        "nasil": [
            "Okulda selamlaştığın ama pek konuşmadığın 3-4 kişiyi ya da ders dışında konuşmadığın bir öğretmenini düşün ve aralarından ikisini seç.",
            "Her biri için önceden bir açılış cümlesi hazırla. Örneğin: \"Dünkü matematik ödevini nasıl çözdün?\" ya da \"Hocam, bu konuyu neden seçtiniz?\"",
            "Teneffüste, kantinde ya da ders çıkışında, karşındakinin acelesi yokken yanına git ve cümleni söyle. Sohbeti uzatmak zorunda değilsin; 2-3 dakika yeterli. Karşındakine bir soru daha sor ve cevabını dinle.",
            "Akşam bir deftere kiminle konuştuğunu ve nasıl hissettiğini bir cümleyle yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 2 farklı kişiyle kendin başlattığın bir sohbet yaptın.",
            "Defterinde bu sohbetlerin kiminle olduğu ve nasıl geçtiği yazıyor.",
            "Bir sonraki sohbet için kullanabileceğin en az bir açılış cümlen hazır.",
        ],
        "ipucu": "İlk cümleyi söylemek en zor kısımdır; ortak bir dersi ya da ödevi konu almak işini kolaylaştırır.",
    },
    "P1-G-2": {
        "nasil": [
            "Enerji haritası, hangi ortamların seni yorduğunu, hangilerinin dinlendirdiğini gösteren basit bir listedir. Defterine iki sütun çiz: \"Beni yordu\" ve \"Beni dinlendirdi\".",
            "Her akşam 5 dakika ayır ve gün içinde bulunduğun sosyal ortamları düşün: sınıf, teneffüs, kalabalık bir grup, bir arkadaşla bire bir sohbet gibi.",
            "Her ortamı uygun sütuna yaz ve yanına enerjini 1 (çok yoruldum) ile 5 (çok dinlendim) arasında puanla.",
            "Birkaç günlük not birikince listeye bak ve tekrar eden ortamları işaretle. Örneğin: \"Kalabalık gruplar beni yoruyor, bire bir sohbetler dinlendiriyor.\"",
            "Bulduğun örüntüyü sayfanın altına 1-2 cümleyle özetle.",
        ],
        "kontrol": [
            "En az 5 akşam not aldığın iki sütunlu bir sayfan var.",
            "Seni yoran en az 2, dinlendiren en az 2 ortamı adıyla yazabiliyorsun.",
            "\"Hangi ortamda enerji topluyorum?\" sorusuna bir cümleyle cevap verebiliyorsun.",
        ],
        "ipucu": "Ortamları iyi ya da kötü diye yargılama; amaç yalnızca seni neyin nasıl etkilediğini görmek.",
    },
    "P1-G-3": {
        "nasil": [
            "Bir öğretmeninle konuşup derste 3-5 kişilik bir gruba 5 dakikalık bir sunum yapıp yapamayacağını sor; konuyu birlikte belirleyin.",
            "Sunumunu 3 bölüme ayır: giriş (konuyu tanıt), orta (2-3 ana fikir), kapanış (tek cümlelik özet). Her bölüm için kısa notlar al.",
            "En az 2 kez prova yap: telefonla süre tut ve aynanın karşısında ya da bir aile üyesine anlat. 5 dakikayı aşıyorsan kısalt.",
            "Sunum günü notlarına bakabilirsin; dinleyicilerle göz teması kurmaya ve yavaş konuşmaya çalış.",
            "Sunumdan sonra kendine geri bildirim ver: \"İyi giden 2 şey\" ve \"Bir dahakine değiştireceğim 1 şey\" başlıklarıyla yaz.",
        ],
        "kontrol": [
            "5 dakikalık sunumunu 3-5 kişilik bir gruba yaptın.",
            "Sunumdan önce en az 2 prova yaptın.",
            "Elinde iyi giden 2 şeyi ve geliştireceğin 1 şeyi yazdığın bir not var.",
        ],
        "ipucu": "Heyecanlanman çok normal; sunuma başlamadan önce yavaşça birkaç kez nefes alıp vermek işine yarayabilir.",
    },
    "P1-G-4": {
        "nasil": [
            "Okulundaki kulüplerin listesini rehberlik servisinden, okul panosundan ya da öğretmenlerinden öğren.",
            "İlgini çeken 2 kulübü seç ve her biri için \"Burada ne yapmak isterdim?\" sorusunu bir cümleyle cevapla.",
            "Seçtiğin kulübün danışman öğretmeniyle konuşup üye ol ve ilk toplantısına katıl.",
            "Planlanan bir etkinlikte üstlenebileceğin bir görev iste. Örneğin: afiş hazırlamak, katılımcıları karşılamak ya da malzeme listesi tutmak.",
            "Görevini tamamladıktan sonra ne yaptığını ve nasıl hissettiğini 2-3 cümleyle not et.",
        ],
        "kontrol": [
            "Bir okul kulübüne üyesin ve en az bir toplantısına katıldın.",
            "Bir etkinlikte adı belli bir görev üstlendin ve bitirdin.",
            "Bu görevde ne yaptığını birine 2-3 cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Büyük bir görevle başlamak zorunda değilsin; küçük ama net bir görev de çok değerli.",
    },
    "P1-G-5": {
        "nasil": [
            "Önündeki grup projelerini (ödev, performans görevi, kulüp projesi) bir listeye yaz.",
            "En az birinde koordinasyon ya da sözcülük rolünü iste. Koordinatör toplantıları ve iş takibini düzenler; sözcü grubun çalışmasını sınıfa anlatır.",
            "Koordinatörsen ilk toplantıda görevleri ve teslim tarihlerini yaz; sonra düzenli aralıklarla kısa bir kontrol toplantısı ya da mesajlaşması düzenle.",
            "Sözcüysen grubun ortak fikirlerini not al ve sunumdan önce arkadaşlarınla en az bir kez prova yap.",
            "Proje bitince \"Ekipte neyi iyi yaptım, neyi geliştirebilirim?\" sorusunu 3-4 cümleyle yaz.",
        ],
        "kontrol": [
            "En az bir grup projesinde sözcülük ya da koordinasyon görevi yaptın.",
            "Elinde toplantı notları, görev listesi ya da sunum notları gibi bir iz var.",
            "Ekipte ne yaptığını ve neyi geliştirebileceğini yazdığın bir değerlendirme var.",
        ],
        "ipucu": "Her işi tek başına yapmaya çalışma; koordinasyon, işi paylaştırıp takip etmek demektir.",
    },
    "P1-G-6": {
        "nasil": [
            "Bir sayfaya \"İletişimde güçlü yanlarım\" başlığı at. Bire bir sohbet, yazılı iletişim (mesaj, e-posta, metin), dikkatli dinleme gibi seni rahat ettiren yolları yaz.",
            "Her güçlü yanın için seni en iyi anlatan bir örnek yaz. Örneğin: \"Arkadaşım derdini anlattığında sözünü kesmeden dinledim.\"",
            "{bolum} alanında bu güçlerin nerede işe yarayacağını düşün: rapor yazma, bire bir görüşmeler, araştırma, ekipte dinleyici olma gibi.",
            "Her güçlü yanın yanına \"Bölümde nasıl kullanırım?\" sorusuna bir cümlelik cevap ekle.",
            "Sayfayı sakla; ileride staj ya da tercih dönemlerinde tekrar bakabilirsin.",
        ],
        "kontrol": [
            "En az 3 güçlü iletişim yolunu yazdığın bir sayfan var.",
            "Her güçlü yanın için {bolum} alanında bir kullanım alanı yazdın.",
            "\"İletişimde en rahat olduğum yol hangisi?\" sorusuna bir cümleyle cevap verebiliyorsun.",
        ],
        "ipucu": "İçe dönüklük bir eksiklik değil; dinlemek ve derin düşünmek birçok meslekte aranan becerilerdir.",
    },
    "P1-G-7": {
        "nasil": [
            "{bolum} alanında insanlarla yoğun çalışan birini seç (ör. öğretmen, hemşire, satış temsilcisi, avukat): bir röportaj ya da belgesel bul ya da aile çevrenden böyle biriyle konuş.",
            "Aile çevrenden biriyle konuşacaksan bunu ailenin bilgisiyle yap; tanımadığın biriyle yalnızca ailenin ya da öğretmeninin aracılığıyla, okulda ya da görüntülü görüşmeyle konuş.",
            "Okurken, izlerken ya da konuşurken 3 soruyu not et: İletişimi nasıl öğrendi? Zor bir insanla karşılaşınca ne yaptı? Onu en çok ne yoruyor?",
            "Bu kişinin iletişimde kullandığı 3 yöntemi listele. Örneğin: \"Önce dinliyor\", \"Karşısındakinin adını kullanıyor\".",
            "Birini seç ve nasıl deneyeceğini tek cümleyle yaz. Örneğin: \"Bir sonraki grup çalışmasında önce herkesi dinleyeceğim.\" Denediğinde tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Bu kişinin iletişimde kullandığı 3 yöntem yazılı.",
            "Onu yoran şeyleri de not ettin.",
            "Bir yöntemi nasıl deneyeceğini yazdın.",
        ],
        "ipucu": "İnsanlarla çalışmanın yorucu yanlarını da öğrenmek, bu işin sana uyup uymadığını daha gerçekçi gösterir.",
    },
    "P1-U-1": {
        "nasil": [
            "Aileni, akrabalarını, öğretmenlerini ve okulun mezunlarını düşün; {bolum} okuyan ya da bu bölümden mezun olan birini tanıyan var mı diye sor.",
            "Tanımadığın biriyle iletişime geçeceksen bunu ailenin ya da öğretmeninin bilgisi dahilinde yap. Okulun rehberlik servisi de mezunlarla bağlantı kurmana yardım edebilir.",
            "Kısa ve kibar bir mesaj hazırla. Örneğin: \"Merhaba, ben lise öğrencisiyim ve {bolum} okumayı düşünüyorum. Bölüm hakkında 10 dakika konuşabilir miyiz?\"",
            "Görüşmeden önce 3 soru yaz. Örneğin: \"Bölümde bir günün nasıl geçiyor?\", \"En zorlandığın ders hangisi?\"",
            "Görüştüğün kişinin adını, iletişim bilgisini (izin verdiyse) ve öğrendiğin 2 şeyi bir deftere ya da telefonundaki bir nota kaydet.",
        ],
        "kontrol": [
            "{bolum} okuyan ya da mezun 2 kişiyle ailenin ya da öğretmeninin bilgisiyle konuştun.",
            "İletişim bilgilerini yalnızca kişinin izniyle kaydettin.",
            "Her görüşmeden öğrendiğin en az bir bilgiyi yazdın.",
        ],
        "ipucu": "Kişisel bilgilerini (adres, okul dışı programın gibi) tanımadığın kişilerle paylaşma; görüşmeleri güvenli ortamlarda yap.",
    },
    "P1-U-2": {
        "nasil": [
            "Yaklaşan okul etkinliklerini öğren: tören, tanıtım günü, kulüp gösterisi, okul gezisi gibi.",
            "Etkinliği düzenleyen öğretmene giderek sunuculuk ya da tanıtım görevi almak istediğini söyle.",
            "Görevi aldığında akışı öğren ve söyleyeceklerini bir kâğıda yaz: açılış cümlesi, bölümler arası geçiş cümleleri, kapanış.",
            "Etkinlikten önce en az 3 kez sesli prova yap; mümkünse bir kez etkinlik yerinde, mikrofonla dene.",
            "Etkinlikten sonra iyi giden ve geliştirmek istediğin birer noktayı not et.",
        ],
        "kontrol": [
            "Bir okul etkinliğinde sunuculuk ya da tanıtım görevi aldın.",
            "Görevi etkinlik günü sahnede ya da kalabalık önünde yerine getirdin.",
            "Bu deneyimden iyi giden ve geliştireceğin birer noktayı yazdın.",
        ],
        "ipucu": "Kâğıttan okumak hata değildir; birçok deneyimli sunucu da notlarını kullanır.",
    },
    "P2-G-1": {
        "nasil": [
            "Aktif dinleme, karşındakini sözünü kesmeden dinleyip ne dediğini anladığını göstermektir. En basit yolu, cevap vermeden önce onun söylediğini kendi cümlelerinle özetlemektir.",
            "Bir fikir ayrılığı yaşadığında hemen cevap verme; önce \"Yani sen ... diyorsun, doğru mu anladım?\" de. Karşındaki \"evet\" derse kendi fikrini söyle; \"hayır\" derse ne demek istediğini tekrar sor.",
            "Konuşma sırasında telefonu bırak, ona dön ve göz teması kur.",
            "Her denemeden sonra telefonundaki bir nota kiminle konuştuğunu ve konuşmanın nasıl ilerlediğini bir cümleyle yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. İşe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 3 konuşmada karşındakini kendi cümlelerinle özetledin.",
            "Notunda bu 3 konuşmanın kısa kaydı var.",
            "Özetlemenin konuşmayı nasıl etkilediğini bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Özetlerken karşındakinin söylediğini değiştirme ya da alay eder gibi tekrarlama; amaç gerçekten anlamak.",
    },
    "P2-G-2": {
        "nasil": [
            "Son zamanlarda biriyle yaşadığın bir anlaşmazlığı seç: bir arkadaş, kardeş ya da grup arkadaşı olabilir.",
            "Önce olayı 2-3 cümleyle, sadece olanları anlatarak yaz.",
            "Sonra kendini onun yerine koy ve \"Ben\" diye başlayarak onun gözünden yaz. Örneğin: \"Ben o gün çok yorgundum ve ...\"",
            "Onun ne hissetmiş ve neyi önemsemiş olabileceğini 2 maddeyle yaz.",
            "Son olarak bu yazının senin bakışını değiştirip değiştirmediğini bir cümleyle not et.",
        ],
        "kontrol": [
            "Bir anlaşmazlığı karşı tarafın gözünden anlatan bir yazın var.",
            "Karşı tarafın en az 2 gerekçesini yazabildin.",
            "Bu bakış açısının senin düşünceni nasıl etkilediğini bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Onun bakışını anlamak, ona hak vermek zorunda olduğun anlamına gelmez.",
    },
    "P2-G-3": {
        "nasil": [
            "Bir grup çalışmasında karar verilmesi gereken bir konu seç (proje konusu, görev dağılımı ya da sunum biçimi) ve bu süreci yönetmeyi üstlen.",
            "Toplantıda herkese sırayla 1-2 dakika söz ver ve fikirleri bir kâğıda ya da tahtaya yaz; bu sırada kimseyi eleştirme.",
            "Benzer fikirleri birleştir ve 2-3 seçeneğe indir.",
            "Her seçeneğin artı ve eksilerini birlikte konuşun; sonra oylama ya da herkesin kabul edebileceği bir orta yol ile karar verin.",
            "Alınan kararı ve kimin ne yapacağını yazıp gruba gönder.",
        ],
        "kontrol": [
            "Grubun herkesin fikrini dinlediğin bir toplantı sonunda karar aldı.",
            "Elinde toplanan fikirler ve verilen karar yazılı olarak var.",
            "Kararın nasıl alındığını bir arkadaşına adım adım anlatabiliyorsun.",
        ],
        "ipucu": "Sessiz kalan arkadaşlarına doğrudan \"Sen ne düşünüyorsun?\" diye sormak, herkesin katılmasını sağlar.",
    },
    "P2-G-4": {
        "nasil": [
            "Empati ve iletişim üzerine bir kaynak seç; örneğin Marshall Rosenberg'in \"Şiddetsiz İletişim\" kitabı ya da okul kütüphanesinden bu konuda bir kitap veya makale.",
            "Kitapsa bölümlere ayırarak oku; her oturumda bir bölüm ya da 10-15 sayfa yeterli.",
            "Okurken sana ilginç gelen fikirlerin altını çiz ya da defterine kısa notlar al.",
            "Bitirdiğinde notlarından günlük hayatta deneyebileceğin 3 fikir seç ve her birini \"Bunu ... durumunda deneyeceğim\" diye yaz.",
            "Bu fikirlerden en az birini bir sonraki uygun durumda dene ve tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Empati ya da iletişim üzerine bir kitabı veya makaleyi okudun.",
            "Defterinde okuduğundan çıkardığın 3 uygulanabilir fikir var.",
            "Her fikrin hangi durumda işe yarayacağını açıklayabiliyorsun.",
        ],
        "ipucu": "Kitabın tamamını bitiremezsen, okuduğun bölümlerden 3 fikir çıkarman da değerlidir.",
    },
    "P2-G-5": {
        "nasil": [
            "Akran mentorluğu, bir öğrencinin başka bir öğrenciye ders, uyum ya da okul hayatı konusunda destek olmasıdır. Rehberlik servisine okulda böyle bir program olup olmadığını sor.",
            "Program yoksa yeni gelen öğrencilere okulu tanıtmak ya da alt sınıflara ders desteği vermek gibi bir öneriyi rehber öğretmeninle konuş.",
            "Destek vereceğin kişi ya da grupla düzenli bir buluşma zamanı belirleyin; 30 dakika yeterli.",
            "Her görüşmede önce onu dinle, sonra birlikte bir sonraki buluşma için küçük bir hedef koyun.",
            "Görüşmeleri tarih ve kısa notla bir defterde kaydet; zorlandığın konularda öğretmeninden destek iste.",
        ],
        "kontrol": [
            "Bir dönem boyunca düzenli olarak bir akran destek rolünde bulundun.",
            "Görüşme tarihlerini ve kısa notlarını içeren bir kaydın var.",
            "Desteğinin karşı tarafa nasıl yardımcı olduğunu bir örnekle anlatabiliyorsun.",
        ],
        "ipucu": "Çözemeyeceğin ciddi sorunlarla karşılaşırsan bunu tek başına taşımaya çalışma; rehber öğretmenine ilet.",
    },
    "P2-G-6": {
        "nasil": [
            "Bir sayfayı ikiye böl: \"Esnediğim durumlar\" ve \"Fikrimde durduğum durumlar\".",
            "Son aylardan her iki sütun için birer gerçek örnek yaz. Örneğin: \"Grup sunumunda arkadaşımın fikrini kabul ettim.\"",
            "Her örnek için şu soruları cevapla: \"Neden böyle davrandım?\", \"Sonuç nasıl oldu?\", \"Tekrar olsa aynısını yapar mıydım?\"",
            "Son olarak, ne zaman esnemenin, ne zaman fikrinde durmanın sana doğru geldiğini 2-3 cümleyle özetle.",
        ],
        "kontrol": [
            "Esnediğin ve fikrinde durduğun en az birer örnek durumu yazdın.",
            "Her örnek için sonucun nasıl olduğunu değerlendirdin.",
            "\"Ne zaman esnerim, ne zaman dururum?\" sorusuna 2-3 cümleyle cevap verebiliyorsun.",
        ],
        "ipucu": "Hiçbiri tek başına doğru değil; amaç hangi durumda hangisinin sana iyi geldiğini fark etmek.",
    },
    "P2-G-7": {
        "nasil": [
            "Farklı görüşteki insanları bir araya getirmeyi başarmış birini seç: bir öğretmen, takım kaptanı, toplum önderi ya da {bolum} alanından biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Ne yaşadı? Nasıl tepki verdi? Bundan ne öğrendi?",
            "Bu kişinin uzlaşma için yaptığı 3 davranışı yaz. Örneğin: \"Önce iki tarafı ayrı ayrı dinledi\", \"Ortak hedefi hatırlattı\".",
            "Bir davranışı seç ve kendi hayatında nasıl deneyeceğini tek cümleyle yaz; denediğinde tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Bu kişinin uzlaşma için yaptığı 3 davranış yazılı.",
            "Kendine uyarlayacağın bir davranışı ve onu hangi durumda deneyeceğini yazdın.",
        ],
        "ipucu": "Hikâyeyi okurken \"Ben o durumda ne yapardım?\" diye sormak, okuduğunu kendi hayatına taşımanı kolaylaştırır.",
    },
    "P2-U-1": {
        "nasil": [
            "Bir grup çalışmasında anlaşmazlık çıktığında hemen taraf tutma; önce iki tarafı da dinle.",
            "Her iki tarafın ne istediğini kendi cümlelerinle özetle. Örneğin: \"Ali sunumun kısa olmasını, Ece ise görsel olmasını istiyor.\"",
            "Ortak noktayı bul ve söyle: \"İkiniz de iyi bir not almak istiyorsunuz.\"",
            "Her iki isteği birleştiren bir öneri sun ya da gruba \"İkisini nasıl birleştirebiliriz?\" diye sor.",
            "Anlaşmazlık çözüldükten sonra ne yaptığını ve işe yarayan şeyi bir cümleyle not et.",
        ],
        "kontrol": [
            "Bir grup anlaşmazlığında iki tarafı da dinleyip özetledin.",
            "Ortak bir nokta ya da birleştirici bir öneri sundun.",
            "Anlaşmazlığın çözümüne katkını bir örnekle anlatabiliyorsun.",
        ],
        "ipucu": "Tartışma çok gerilirse kısa bir ara vermeyi önermek de iyi bir arabuluculuk adımıdır.",
    },
    "P2-U-2": {
        "nasil": [
            "Sınır koymak, gücünün ya da zamanının yetmediği bir isteği kibarca geri çevirmektir. Sana gelen istekler karşısında bir an durup \"Buna gerçekten vaktim var mı?\" diye düşün.",
            "Hayır demek için kısa bir cümle hazırla. Örneğin: \"Bu hafta sınavlarım var, bu işi alamayacağım ama gelecek hafta yardım edebilirim.\"",
            "Ben-dili kullan: suçlayıcı \"sen\" cümleleri yerine kendi durumunu anlatan \"ben\" cümleleri kur (\"Ben şu an yetişemiyorum\").",
            "Hayır dedikten sonra uzun açıklama yapma ya da özür dilemeye devam etme; gerekçeni bir kez söylemen yeterli.",
            "Deneyimini not et: Ne istendi, ne dedin, karşı taraf nasıl tepki verdi, sen nasıl hissettin?",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "En az bir isteğe gerekçesini söyleyerek kibarca hayır dedin.",
            "Bu durumu ve nasıl hissettiğini not ettin.",
            "Bir sonraki sefer kullanabileceğin bir hayır cümlen hazır.",
        ],
        "ipucu": "İlk denemelerde suçluluk hissetmen olağan; bu his zamanla azalabilir.",
    },
    "P3-G-1": {
        "nasil": [
            "Bir kâğıt ya da defter sayfası al ve önündeki ödevleri, sınavları ve çalışmaları alt alta yaz.",
            "Her işin yanına teslim ya da sınav tarihini ekle.",
            "Her işe yapacağın günü ata; tarihi en yakın olanlarla başla. Bir güne 3-4'ten fazla iş düşerse bazılarını boş günlere kaydır.",
            "Listeyi her gün göreceğin bir yere as ya da telefonunun fotoğraflarına kaydet; biten işin üstünü çiz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Önündeki işleri içeren bir listen var.",
            "Listedeki her işin yanında hangi gün yapılacağı yazıyor.",
            "Listeyi gün içinde kolayca görebileceğin bir yerde tutuyorsun.",
        ],
        "ipucu": "Plan kaydığında onu çöpe atma; işi bir sonraki boş güne taşıman yeterli.",
    },
    "P3-G-2": {
        "nasil": [
            "Pomodoro, 25 dakika tek bir işe odaklanıp ardından 5 dakika mola vermeye dayanan bir çalışma yöntemidir. Bir tur 25+5 dakikadır.",
            "Çalışmadan önce yapacağın tek bir işi seç. Örneğin: \"Fizik testinden 15 soru çöz.\"",
            "Telefonunu sessize al ve başka odaya koy ya da ters çevir; zamanlayıcıyı 25 dakikaya kur. Zil çalana kadar sadece o işe odaklan. Aklına başka bir şey gelirse bir kâğıda yazıp işine dön.",
            "5 dakikalık molada kalk, su iç ya da biraz yürü; sonra ikinci tura başla. Her günün sonunda kaç tur yaptığını bir tabloya işaretle.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "5 gün boyunca her gün en az 2 Pomodoro turu yaptın.",
            "Tabloda her gün için kaç tur yaptığın işaretli.",
            "Pomodoronun sana uyup uymadığını bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "25 dakika uzun gelirse 15 dakikayla başlayıp süreyi yavaş yavaş artırabilirsin.",
    },
    "P3-G-3": {
        "nasil": [
            "Kullanacağın sistemi seç: kâğıt ajanda, duvar takvimi ya da telefonundaki takvim veya yapılacaklar uygulaması. Sana en kolay gelen ve her gün göreceğin bir şey olsun.",
            "Tüm ödev, sınav ve önemli işlerini teslim tarihleriyle birlikte bu sisteme gir.",
            "Akşamları 5 dakika ayırıp ertesi günün işlerini kontrol et; yeni gelen görevleri hemen ekle, biten işleri işaretle, yapılamayanları yeni bir güne taşı.",
            "Sistemi kullanmadığın günleri de işaretle; birkaç gün kullandıktan sonra işe yarayıp yaramadığını düşün ve gerekirse küçük bir değişiklik yap.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Sistemini en az 15 gün kullandın.",
            "Kaçırdığın günler işaretli.",
            "Tüm görevlerin tek bir sistemde duruyor.",
        ],
        "ipucu": "Birden fazla sistem kullanma; her şeyin tek bir yerde olması işini kolaylaştırır.",
    },
    "P3-G-4": {
        "nasil": [
            "Teslim tarihi 2-3 hafta içinde olan bir ödev seç ve takvimine yeni hedef tarih olarak teslimden 1 gün öncesini yaz.",
            "Ödevi 3-4 küçük parçaya böl. Örneğin: araştırma, taslak yazma, düzeltme, son kontrol.",
            "Her parçaya hedef tarihinden geriye doğru sayarak bir gün ata.",
            "Her parçayı bitirdiğinde işaretle; bir parça kayarsa ertesi gün telafi et.",
            "Ödevi hedef gününde bitir; teslim edince bu yöntemin işe yarayıp yaramadığını bir cümleyle not et.",
        ],
        "kontrol": [
            "En az bir ödevi teslim tarihinden önce bitirip teslim ettin.",
            "Ödevi parçalara ayırdığın ve günlere dağıttığın bir planın vardı.",
            "Erken bitirmenin sana ne hissettirdiğini bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Son günü \"kontrol ve düzeltme\" için boş bırakmak, son dakika telaşını azaltır.",
    },
    "P3-G-5": {
        "nasil": [
            "3 akademik hedef yaz; ölçülebilir olsun. Örneğin: \"Matematik ortalamamı 70'ten 80'e çıkarmak\".",
            "Her hedefi 3-4 küçük, somut adıma böl. Örneğin: \"Türev konusunda 50 soru çözmek\", \"Yanlışlarımı öğretmenime sormak\".",
            "Hedeflerini ve adımlarını bir sayfaya yazıp ajandanın ya da defterinin başına koy.",
            "Bir adımı bitirdiğinde yanına tarihini yaz; bir adım tıkanırsa onu daha küçük bir adıma çevir.",
            "Bir hedefe ulaştığında ya da vazgeçtiğinde yanına \"ulaştım\" ya da \"ulaşamadım\" yaz, tarihini ve nedenini bir cümleyle not et.",
        ],
        "kontrol": [
            "3 hedefin ve her birinin küçük adımları yazılı.",
            "Bitirdiğin adımların yanında tarihleri var.",
            "En az 2 hedefe ulaştın ve ulaştığın tarihi not ettin.",
        ],
        "ipucu": "Ulaşamadığın bir hedef başarısızlık değildir; nedenini anlamak bir sonraki planı güçlendirir.",
    },
    "P3-G-6": {
        "nasil": [
            "Kendine uygun bir gözden geçirme zamanı seç; ödevlerin biriktiği ya da yeni bir sınav dönemine girdiğin anlar iyi bir fırsattır.",
            "10 dakika ayır ve 3 soruyu cevapla: \"Son günlerde neyi bitirdim?\", \"Ne kaldı ya da aksadı?\", \"Beni ne zorladı?\"",
            "Kalan işleri ve yeni ödev ve sınavları listeye yaz, her birine bir gün ata.",
            "Sonraki adım için tek bir odak hedefi seç. Örneğin: \"Önümüzdeki 5 çalışmada önce İngilizceye 30 dakika ayıracağım.\"",
            "Her gözden geçirmeyi tarihiyle defterine kaydet; böylece kaç kez yaptığını görürsün.",
        ],
        "kontrol": [
            "En az 6 tarihli gözden geçirme notun var.",
            "Her notta neyin bittiği, neyin aksadığı ve sonraki adım yazılı.",
            "Gözden geçirmelerinden sonra bir odak hedefiyle devam ettin.",
        ],
        "ipucu": "Planladığın zamanı kaçırırsan bir sonraki boş anında yapman da sayılır; önemli olan gözden geçirmeyi tamamen bırakmamak.",
    },
    "P3-G-7": {
        "nasil": [
            "Disipliniyle bilinen birini seç: bir sporcu, müzisyen ya da {bolum} alanında başarılı biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Günlük düzenini nasıl kurdu? İsteksiz olduğu günlerde ne yaptı? Bundan ne öğrendi?",
            "Bu kişinin 2 yöntemini kendi cümlelerinle yaz. Örneğin: \"Her işe aynı saatte başlıyor\", \"Canı istemese de 10 dakikayla başlıyor\".",
            "Bir yöntemi seç ve kendi çalışmana uyarla; her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Bu kişinin 2 yöntemi yazılı.",
            "Bir yöntemi kendi çalışmana uyguladın ve tarihli notun var.",
        ],
        "ipucu": "Başarılı insanların da isteksiz günleri vardır; farkı, o günlerde nasıl başladıklarıdır.",
    },
    "P3-U-1": {
        "nasil": [
            "{bolum} için hedef sıralamanı ya da puanını öğren; bunun için ÖSYM'nin yayımladığı verilere ve YÖK Atlas'a bakabilirsin. Bu bilgilerden yola çıkarak hedef netlerini belirle.",
            "Ders ders hedef netlerini ve şu anki deneme ortalamalarını bir tabloya yaz; aradaki farkı gör.",
            "Önündeki ayları alt alta yaz ve her ay için 1-2 hedef ekle. Örneğin: \"Kasım: TYT matematikte 3 net artış, 2 deneme.\"",
            "Bölüm hazırlığı için de birkaç adım ekle: bölüm tanıtım günleri, {bolum} okuyan biriyle görüşme, ilgili bir kitap.",
            "Planını rehber öğretmeninle ya da bir aile büyüğünle paylaşıp gerçekçi olup olmadığını konuş.",
        ],
        "kontrol": [
            "Ay ay hedeflerin yazılı olan bir yıllık planın var.",
            "Planında hem YKS net hedeflerin hem de bölüm hazırlığı adımların bulunuyor.",
            "Bu ayın hedefini birine bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Planı çok sıkı yapma; her ay biraz boşluk bırakmak aksaklıkları telafi etmeni sağlar.",
    },
    "P3-U-2": {
        "nasil": [
            "Bir grup projesinde takvimi hazırlamayı üstlen ve önce projenin son teslim tarihini öğren.",
            "Projeyi parçalara ayır (araştırma, yazma, tasarım, prova gibi) ve her parçanın kaç gün süreceğini tahmin et.",
            "Son tarihten geriye doğru sayarak her parçaya bir tarih ve bir sorumlu yaz; bunu bir tablo hâlinde hazırla.",
            "Takvimi grupla paylaş ve herkesin onayını al; itiraz olursa tarihleri birlikte düzenleyin.",
            "Düzenli aralıklarla kısa bir mesajla ilerlemeyi sor ve gerekirse takvimi güncelle.",
        ],
        "kontrol": [
            "Ekibin senin hazırladığın takvim ve görev dağılımıyla çalıştı.",
            "Elinde tarihlerin ve sorumluların yazılı olduğu bir tablo var.",
            "Takvimi en az bir kez grubun ihtiyacına göre güncelledin.",
        ],
        "ipucu": "Görevleri dağıtırken arkadaşlarına neyi yapmak istediklerini sormak, takvime uymayı kolaylaştırır.",
    },
    "P4-G-1": {
        "nasil": [
            "Nefes egzersizi, nefesini bilinçli olarak yavaşlattığın kısa bir uygulamadır. 4-4-6'da 4 saniye burnundan nefes alır, 4 saniye tutar, 6 saniyede ağzından yavaşça verirsin.",
            "Sakin bir anda, rahat bir şekilde otur ve bir elini karnına koy. Nefes alırken karnının şiştiğini hissetmeye çalış. Saniyeleri içinden sayarak bu döngüyü 5 kez tekrarla; toplam yaklaşık 1-2 dakika sürer.",
            "Her gün aynı saatte, örneğin yatmadan önce ya da ders çalışmaya başlamadan, bir kez pratik yap.",
            "Bir takvimde ya da notta her pratik yaptığın günü işaretle; stresli bir anda (sınav öncesi gibi) da kullanmayı dene.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 7 gün pratik yaptın ve her pratiği tarihiyle işaretledin.",
            "Tekniğin hangi anlarda işine yaradığını not ettin.",
            "Tekniği bir arkadaşına adım adım tarif edebiliyorsun.",
        ],
        "ipucu": "Başın döner ya da rahatsız olursan nefesi tutma kısmını kısalt ya da normal nefesine dön; bu teknik herkese aynı şekilde iyi gelmeyebilir.",
    },
    "P4-G-2": {
        "nasil": [
            "Tetikleyici, seni strese sokan durum ya da olaydır. Bir sayfaya \"Beni en çok strese sokan 3 durum\" başlığı at.",
            "Son zamanları düşün ve 3 somut durum yaz. Örneğin: \"Tahtaya kaldırılmak\", \"Deneme sonuçlarının açıklanması\".",
            "Her durumun altına o anda ne hissettiğini ve bedeninde neyi fark ettiğini kısaca yaz (kalp çarpıntısı, el terlemesi gibi).",
            "Her biri için \"O anda ne yapabilirim?\" sorusuna 1-2 küçük fikir yaz. Örneğin: \"Yavaş nefes almak\", \"Kendime 'hazırlandım' demek\".",
            "Sayfayı sakla; bu durumlardan biri yaşandığında bir fikrini deneyebilirsin.",
        ],
        "kontrol": [
            "Seni strese sokan 3 durumu yazdığın bir sayfan var.",
            "Her durum için en az bir \"o anda ne yapabilirim?\" fikri yazdın.",
            "Bu fikirlerden birini gerektiğinde nasıl uygulayacağını söyleyebiliyorsun.",
        ],
        "ipucu": "Stresin uzun süre devam ediyor ve günlük hayatını zorluyorsa okulunun rehber öğretmeniyle ya da güvendiğin bir yetişkinle konuş.",
    },
    "P4-G-3": {
        "nasil": [
            "Sana keyifli gelen bir hareket türü seç: tempolu yürüyüş, bisiklet, dans, ip atlama, okul takımında spor ya da evde bir egzersiz videosu.",
            "Her seferinde yaklaşık 20 dakika hareket et; zorlanmadan konuşabileceğin bir tempoyla başla.",
            "Hareketten önce ve sonra kendini nasıl hissettiğini tek kelimeyle not et (\"gergin\", \"rahat\", \"yorgun\", \"enerjik\" gibi).",
            "Her hareketin tarihini ve süresini bir tabloya yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Tablonda en az 10 tarihli hareket kaydı var.",
            "Kayıtların çoğunda hareket öncesi ve sonrası hissin yazılı.",
            "Hareketin sana nasıl hissettirdiğini bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Bir sağlık sorunun varsa ya da hareket ederken ağrı hissedersen dur ve bir yetişkinle ya da doktorla konuş.",
    },
    "P4-G-4": {
        "nasil": [
            "Deneme sınavı için evde ya da okulda sessiz bir yer ayarla; telefonunu kapat ve gerçek sınav süresini zamanlayıcıya kur.",
            "Sınava başlamadan önce kaygını 1 (hiç kaygılı değilim) ile 10 (çok kaygılıyım) arasında puanla ve kâğıdın köşesine yaz.",
            "Sınavı süre bitene kadar ara vermeden çöz; takıldığın soruyu işaretleyip geç.",
            "Sınav bitince kaygı puanını tekrar yaz ve bir tabloya tarih, sınav öncesi ve sonrası puanı işle.",
            "Bu provayı en az 3-4 kez tekrarla ve puanlarının nasıl değiştiğine bak.",
        ],
        "kontrol": [
            "En az 3 denemeyi gerçek sınav koşullarında çözdün.",
            "Her deneme için kaygı puanlarının yazılı olduğu bir tablon var.",
            "Tablona bakarak kaygı puanının denemeler boyunca nasıl değiştiğini bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Puanın her seferinde düşmeyebilir; bu normaldir, genel eğilime bak.",
    },
    "P4-G-5": {
        "nasil": [
            "Okul günleri için bir yatış ve kalkış saati belirle; okul saatine göre gerçekçi olsun. Örneğin: 23.00'te yat, 07.00'de kalk.",
            "Telefonuna yatıştan 30 dakika önce çalacak bir hatırlatıcı kur; bu saatten sonra ekranı (telefon, tablet, bilgisayar) bırak.",
            "Bu 30 dakikayı sakin bir işle geçir: kitap okumak, ertesi günün çantasını hazırlamak, hafif müzik dinlemek gibi.",
            "Bir uyku tablosu çiz; her sabah yattığın ve kalktığın saati yaz, rutinine uyduğun geceyi işaretle.",
            "Birkaç gece sonra tabloya bak; hangi gecelerde uyamadığını ve nedenini gör, gerekirse saati biraz düzenle.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Uyku tablonda rutinine uyduğun geceler işaretli.",
            "En az 20 gece rutinine uydun.",
            "Çoğu akşam ekranı yatmadan 30 dakika önce bıraktın.",
        ],
        "ipucu": "Telefonunu yatağından uzakta şarj etmek, ekranı bırakmayı kolaylaştırır.",
    },
    "P4-G-6": {
        "nasil": [
            "Kendine şu soruyu sor: \"Kaygım uykumu, ders çalışmamı ya da arkadaşlarımla ilişkimi uzun süredir zorluyor mu?\" Cevabın evetse destek almanın zamanı gelmiş olabilir.",
            "Okulunun rehberlik servisinin nerede olduğunu ve hangi saatlerde açık olduğunu öğren.",
            "Rehber öğretmenine gidip görüşmek istediğini söyle. Ne diyeceğini bilmiyorsan şöyle başlayabilirsin: \"Son zamanlarda çok kaygılı hissediyorum, konuşmak istiyorum.\"",
            "Görüşmeye gitmeden önce seni zorlayan 2-3 durumu bir kâğıda yazabilirsin; konuşurken işine yarar.",
            "Okulda konuşmak zor geliyorsa önce ailenden ya da güvendiğin başka bir yetişkinden destek iste.",
        ],
        "kontrol": [
            "Kaygın seni zorluyorsa rehber öğretmenle görüştün; zorlamıyorsa gerektiğinde nasıl görüşeceğini biliyorsun.",
            "Görüşmeye gitmek için bir adım attın: saatini öğrendin ya da randevu istedin.",
            "Gerektiğinde kime başvurabileceğini biliyor ve söyleyebiliyorsun.",
        ],
        "ipucu": "Destek istemek zayıflık değildir; birçok kişi zor dönemlerde bir yetişkinle konuşmanın işe yaradığını görür.",
    },
    "P4-G-7": {
        "nasil": [
            "Büyük bir maç, sahne ya da sınav öncesi heyecanını nasıl yönettiğini anlatmış birini seç: bir sporcu, sanatçı ya da {bolum} alanında çalışan biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Heyecanı ne zaman hissetti? O an ne yaptı? Bundan ne öğrendi?",
            "İstersen ailenden ya da öğretmenlerinden birine de sor: \"Önemli bir şeyden önce heyecanını nasıl yönetiyorsun?\"",
            "Bu kişinin kullandığı 2 yöntemi yaz (ör. hazırlık rutini, kendine söylediği bir cümle) ve birini bir sonraki heyecanlı anında dene; denediğinde tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Bu kişinin heyecanla başa çıkmak için kullandığı 2 yöntem yazılı.",
            "Bir yöntemi kendin denedin ve nasıl gittiğini not ettin.",
        ],
        "ipucu": "Biraz heyecan çoğu zaman performansı artırır; ama heyecanın günlük hayatını uzun süre zorluyorsa rehber öğretmeninle konuş.",
    },
    "P4-U-1": {
        "nasil": [
            "Son birkaç ayı düşün ve baskı altında sakin kaldığın bir anı seç: bir sınav, maç, sunum ya da aile içinde gergin bir an olabilir.",
            "O anı 3-4 cümleyle yaz: ne oldu, ortam nasıldı, senden ne bekleniyordu?",
            "Sonra o anda ne yaptığını madde madde yaz. Örneğin: \"Derin nefes aldım\", \"İşi küçük parçalara böldüm\", \"Kendime 'yapabilirim' dedim\".",
            "Bu maddelerden yola çıkarak kendi sakin kalma yöntemini bir cümleyle tarif et.",
        ],
        "kontrol": [
            "Baskı altında sakin kaldığın bir anı yazdın.",
            "O anda yaptığın en az 2 şeyi madde madde yazdın.",
            "Kendi sakin kalma yöntemini bir cümleyle tarif edebiliyorsun.",
        ],
        "ipucu": "Bu çalışma bir üstünlük ölçümü değil; amaç zor anlarda sana neyin iyi geldiğini fark etmek ve gerektiğinde yeniden kullanabilmek.",
    },
    "P4-U-2": {
        "nasil": [
            "Merak ediyorsan okulda zaman baskısı olan bir rolü deneyebilirsin: bilgi yarışması, münazara (iki grubun bir konuyu karşılıklı tartıştığı yarışma) ya da etkinlik organizasyonu gibi. Amaç bu tür ortamların sana uyup uymadığını gözlemlemek.",
            "Danışman öğretmenle konuşup bir görev al ve görevin teslim tarihini ve senden beklenenleri yaz.",
            "Hazırlığı küçük hedeflere böl ve her birini bitirince tarihiyle işaretle.",
            "Görev anında baskıyı hissedersen sakin kalma yöntemini (yavaş nefes, işi parçalara bölmek) kullan.",
            "Görev bittikten sonra baskı altında neyi iyi yaptığını ve neyi geliştirebileceğini 2-3 cümleyle yaz.",
        ],
        "kontrol": [
            "Zaman baskısı olan bir görevi üstlendin ve tamamladın.",
            "Hazırlık sürecine ait bir planın ya da notların var.",
            "Baskılı bir ortamda çalışmanın sana nasıl geldiğini bir örnekle anlatabiliyorsun.",
        ],
        "ipucu": "Sonucun ilk denemede mükemmel olması gerekmiyor; görevi tamamlamak da önemli bir başarı.",
    },
    "P5-G-1": {
        "nasil": [
            "Hiç bilmediğin bir konu seç. Fikir bulamazsan kendine sor: \"Hep merak edip hiç araştırmadığım şey ne?\" Örneğin: kara delikler, arıların iletişimi.",
            "Bu konuda yaklaşık 10 dakikalık güvenilir bir video izle ya da bir yazı oku; örneğin bir müze, üniversite ya da bilim kanalının içeriği.",
            "İzlerken ya da okurken en ilginç gelen 2 bilgiyi bir kâğıda yaz.",
            "Seni en çok neyin şaşırttığını ve nedenini 2-3 cümleyle yaz.",
            "Yeni konuyu bir arkadaşına ya da ailene 2 cümleyle anlat.",
        ],
        "kontrol": [
            "Hiç bilmediğin bir konuda 10 dakikalık bir içerik izledin ya da okudun.",
            "Seni şaşırtan şeyi 2-3 cümleyle yazdın.",
            "Yeni konuyu birine 2 cümleyle anlattın.",
        ],
        "ipucu": "Bir konu sıkıcı gelirse yarıda bırakıp başka bir konu seçmen sorun değil.",
    },
    "P5-G-2": {
        "nasil": [
            "Arama motoruna \"{bolum} yenilikler\" ya da \"{bolum} son gelişmeler\" gibi ifadeler yaz ve son 2 yıla ait haberleri incele.",
            "Güvenilir kaynakları tercih et: üniversite siteleri, bilim dergileri, tanınmış haber kuruluşlarının bilim-teknoloji bölümleri.",
            "Seni en çok ilgilendiren bir yenilik seç ve şu üç soruyu cevapla: \"Bu yenilik ne?\", \"Ne zaman ortaya çıktı?\", \"Kimin işine yarar?\"",
            "Cevaplarını bir deftere 4-5 cümleyle yaz ve kaynağın adını ekle.",
        ],
        "kontrol": [
            "{bolum} alanından son 2 yılda ortaya çıkan bir yeniliği seçtin.",
            "Bu yeniliği ve etkisini kaynağıyla birlikte not ettin.",
            "Bu yeniliğin neden önemli olduğunu bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Tek bir kaynağa güvenme; aynı bilgiyi ikinci bir kaynakta da görmeye çalış.",
    },
    "P5-G-3": {
        "nasil": [
            "Merakıyla yeni bir şey bulmuş birini seç: bir bilim insanı, mucit ya da {bolum} alanında yeni bir şey denemiş biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Neyi merak etti? Yeni fikrine nasıl ulaştı? Hangi engelle karşılaştı ve ne yaptı?",
            "Bu kişinin yeni fikirlere ulaşma yolunu ve karşılaştığı bir engeli kendi cümlelerinle 4-5 cümleyle yaz.",
            "Kendine uyarlayacağın bir davranışı tek cümleyle yaz. Örneğin: \"Merak ettiğim bir soruyu hemen not alıp sonra araştıracağım.\"",
        ],
        "kontrol": [
            "Bu kişinin yeni fikirlere ulaşma yolu yazılı.",
            "Karşılaştığı bir engeli ve ne yaptığını kendi cümlelerinle yazdın.",
            "Kendine uyarlayacağın bir davranışı yazdın.",
        ],
        "ipucu": "Belgesel izliyorsan ilginç bir yerde durdurup not almak, sonradan hatırlamanı kolaylaştırır.",
    },
    "P5-G-4": {
        "nasil": [
            "Yakın zamanda gidebileceğin etkinlikleri araştır: bilim şenliği, müze, söyleşi, sergi ya da atölye. Okul panosu ve belediyenin duyuruları iyi bir başlangıçtır.",
            "Daha önce denemediğin türde bir etkinlik seç ve aileni ya da öğretmenini bilgilendirerek bir tarih belirle.",
            "Etkinlikten önce merak ettiğin bir soruyu yaz; orada bu sorunun cevabını aramaya çalış.",
            "Etkinlik sırasında ilgini çeken 2-3 şeyi not al ya da (izin varsa) fotoğrafını çek.",
            "Dönüşte bu deneyimin sana ne kattığını 2-3 cümleyle yaz.",
        ],
        "kontrol": [
            "Daha önce katılmadığın türde bir etkinliğe katıldın.",
            "Etkinlikte gördüğün ya da öğrendiğin en az 2 şeyi not ettin.",
            "Bu etkinlikte seni neyin şaşırttığını bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Ücretsiz etkinlikler de çok değerli; okul ve belediye duyurularını takip et.",
    },
    "P5-G-5": {
        "nasil": [
            "{bolum} ile ilgili ama hiç bilmediğin bir konu seç. Örneğin bölümün temel bir kavramı ya da kullanılan bir yöntem.",
            "Ücretsiz ve tanınmış platformlarda bu konuda kısa bir kurs ara; örneğin Khan Academy, BTK Akademi ya da Coursera'daki giriş düzeyi kurslar (Coursera'da çoğu kurs ücretsiz \"denetleyici/audit\" seçeneğiyle izlenebilir).",
            "Kursu oturumlara böl; her oturumdan sonra tarihli kısa bir not al.",
            "Her dersten sonra en önemli 1-2 bilgiyi bir deftere yaz.",
            "Kursu bitirince öğrendiklerini 3-4 cümleyle özetle ve konunun seni ilgilendirip ilgilendirmediğini not et.",
        ],
        "kontrol": [
            "Bölümle ilgili kısa bir çevrim içi kursu tamamladın.",
            "Her dersten aldığın kısa notların var.",
            "Kursta öğrendiklerini 3-4 cümleyle özetleyebiliyorsun.",
        ],
        "ipucu": "Kaydolmak için hesap açman gerekiyorsa ailenden yardım iste; ücretli seçeneklere geçmeden önce onlara danış.",
    },
    "P5-G-6": {
        "nasil": [
            "3 kitap seç: biri {bolum} ile ilgili, en az biri tamamen farklı bir alandan (roman, tarih, bilim, biyografi gibi) olsun.",
            "Kendine uygun bir okuma zamanı seç; örneğin yatmadan önce 20 dakika. Kısa ama sık okumak, uzun ve seyrek okumaktan daha kolay sürer.",
            "Bir okuma listesi tut: kitabın adı, bitirdiğin tarih ve kitaptan aklında kalan bir cümle.",
            "Bir kitabı bitirince 2-3 cümlelik kısa bir not yaz: Ne anlatıyor, bana ne kattı?",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 3 kitap bitirdin.",
            "Bu kitaplardan en az biri alanının dışından.",
            "Okuma listende her kitabın bitiş tarihi ve kısa notu var.",
        ],
        "ipucu": "Kütüphaneler, kitap almadan okumak için iyi bir seçenek; bir kitap seni sıkıyorsa değiştirmekte sakınca yok.",
    },
    "P5-U-1": {
        "nasil": [
            "{bolum} içindeki alt konuları listele; bunun için üniversitelerin ders listelerine ya da bölüm tanıtım sayfalarına bakabilirsin.",
            "Listeden seni en çok meraklandıran bir alt konu seç ve neden seçtiğini bir cümleyle yaz.",
            "Bu alt konuda 3 kaynak bul: örneğin bir tanıtım videosu, bir makale ya da yazı ve bir kitap veya kitap bölümü.",
            "Kaynakların adlarını bir sayfaya yaz ve her birinin yanına ne anlattığını bir cümleyle not et.",
        ],
        "kontrol": [
            "{bolum} içinden bir alt konu seçtin ve nedenini yazdın.",
            "Bu alt konuyla ilgili 3 kaynağın adı listende var.",
            "Her kaynağın ne anlattığını bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Çok geniş bir konu seçersen daralt; örneğin \"yapay zekâ\" yerine \"yapay zekâ ile görüntü tanıma\".",
    },
    "P5-U-2": {
        "nasil": [
            "Seçtiğin alt konuda cevaplamak istediğin küçük bir araştırma sorusu yaz. Örneğin: \"Okulumuzda öğrencilerin ders çalışma süresi kaç saat?\"",
            "Bir danışman öğretmen bul ve sorunu onunla konuş; TÜBİTAK 2204 Lise Öğrencileri Araştırma Projeleri yarışmasına uygun olup olmadığını da sorabilirsin.",
            "Yöntemini planla: kaynak taraması, anket, gözlem ya da basit bir deney. Anket ya da gözlem yapacaksan öğretmeninin bilgisi ve gerekli izinlerle yap.",
            "Bulgularını topla ve basit bir tablo ya da grafikle göster.",
            "Sonucu 5 dakikalık bir sunum ya da 1-2 sayfalık bir yazıyla sınıfta, kulüpte ya da okul panosunda paylaş.",
        ],
        "kontrol": [
            "Küçük bir araştırmayı baştan sona tamamladın.",
            "Elinde soru, yöntem ve bulguları içeren bir yazı ya da sunum var.",
            "Araştırmanı en az bir grupla (sınıf, kulüp, okul) paylaştın.",
        ],
        "ipucu": "Yarışmaya katılmak zorunlu değil; asıl amaç bir araştırmayı baştan sona deneyimlemek.",
    },
    "P6-G-1": {
        "nasil": [
            "Rutinin, her gün benzer şekilde yaptığın işlerin düzenidir. Değiştireceğin tek bir şey seç. Örneğin: farklı bir odada çalışmak ya da derslerin sırasını değiştirmek.",
            "Değişikliği birkaç gün (ör. 3 gün) dene.",
            "Denediğin her günün sonunda 2 soruyu cevapla: \"Kendimi nasıl hissettim?\" ve \"Verimim arttı mı, azaldı mı, aynı mı kaldı?\"",
            "Deneme bitince gözlemlerini 2-3 cümleyle özetle: değişiklik sana iyi geldi mi, rahatsız etti mi?",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Rutininde bilinçli bir değişikliği birkaç gün denedin.",
            "Denediğin günler için kısa gözlem notların var.",
            "Değişikliğin sana nasıl geldiğini 2-3 cümleyle yazdın.",
        ],
        "ipucu": "Değişiklik seni rahatsız ettiyse bu da değerli bir bilgidir; doğru ya da yanlış bir sonuç yok.",
    },
    "P6-G-2": {
        "nasil": [
            "{bolum} mezunlarının çalıştığı bir meslek seç ve \"bir günüm\" ya da \"meslek tanıtımı\" türünden video, röportaj veya yazılar ara.",
            "Mümkünse bu meslekte çalışan bir tanıdığına, ailenin bilgisi dahilinde, \"Sıradan bir günün nasıl geçiyor?\" diye sor.",
            "Bir sayfayı ikiye böl: \"Her gün aynı olanlar\" (toplantı, rapor gibi) ve \"Günden güne değişenler\" (yeni müşteri, acil durum gibi).",
            "Öğrendiklerini bu iki sütuna yerleştir ve hangisinin daha ağır bastığını bir cümleyle not et.",
        ],
        "kontrol": [
            "{bolum} alanında bir iş gününü inceledin.",
            "Elinde sabit ve değişken işlerin ayrıldığı iki sütunlu bir sayfa var.",
            "Bu işin daha çok rutin mi, daha çok değişken mi olduğunu bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Aynı bölümün farklı işlerinde günler çok farklı geçebilir; tek bir örnekle genelleme yapma.",
    },
    "P6-G-3": {
        "nasil": [
            "Plan B, asıl planın işlemezse uygulayacağın yedek plandır. Önündeki önemli işleri yaz (sınav, proje teslimi, maç, etkinlik).",
            "Her iş için \"Bu olmazsa ne yaparım?\" sorusunu sor ve olası bir aksaklık yaz. Örneğin: \"Grup arkadaşım gelmezse.\"",
            "Her aksaklık için bir yedek plan yaz. Örneğin: \"Onun kısmını önceden paylaşmasını isterim, gerekirse ben sunarım.\"",
            "İş tamamlandığında yedek plana ihtiyaç olup olmadığını ve işe yarayıp yaramadığını kısaca not et.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. İşe yaradıysa her önemli iş için yedek plan yazmayı sürdür ve her yedek planı tarihiyle not et.",
        ],
        "kontrol": [
            "En az 3 önemli iş için yazılı bir yedek planın vardı.",
            "Her yedek plan, belirli bir aksaklığa karşı hazırlandı.",
            "Yedek planlardan en az birinin işe yarayıp yaramadığını değerlendirdin.",
        ],
        "ipucu": "Yedek plan kaygı listesi değildir; her iş için bir olası sorun ve bir çözüm yeterli.",
    },
    "P6-G-4": {
        "nasil": [
            "Grup çalışmalarında olabilecek rolleri yaz: araştırmacı (bilgi toplar), sunucu (sınıfa anlatır), tasarımcı (görselleri hazırlar), koordinatör (işleri takip eder).",
            "Bir sonraki grup çalışmasında genelde üstlenmediğin bir rolü iste.",
            "Bu rolde ne yapacağını grupla netleştir ve görevini yap.",
            "Sonraki grup çalışmasında yine farklı bir rol seç.",
            "Her rol için kısa bir not al: \"Bu rolde neyi sevdim, neyi zor buldum?\"",
        ],
        "kontrol": [
            "Grup çalışmalarında en az 2 farklı rol üstlendin.",
            "Her rol için neyi sevdiğini ve neyi zor bulduğunu yazdın.",
            "Hangi rolde kendini daha rahat hissettiğini söyleyebiliyorsun.",
        ],
        "ipucu": "Hiç denemediğin bir rol başta zor gelebilir; bu, o rolün sana uymadığı anlamına gelmez.",
    },
    "P6-G-5": {
        "nasil": [
            "Temposu değişken ortamlara örnekler: okul etkinliği organizasyonu, bir okul şenliğinde görev, okulun düzenlediği bir gezi ya da belediyenin ücretsiz bir etkinliği. Okulun rehberlik servisinden bu tür fırsatları sorabilirsin.",
            "Ailenin izniyle sana uygun bir fırsat seç ve görev almak için başvur.",
            "Görev günlerinin sonunda 2-3 dakika ayırıp günün nasıl geçtiğini ve plansız gelişmeleri nasıl karşıladığını not et.",
            "Plansız bir şey olduğunda önce durumu anla, sonra sorumlu kişiye danışarak bir çözüm öner.",
            "Deneyim bitince bu ortamda kendini nasıl hissettiğini 3-4 cümleyle yaz.",
        ],
        "kontrol": [
            "Temposu değişken bir ortamda görev aldın.",
            "Görev günlerine ait tarihli notların var.",
            "Değişken bir ortamda kendini nasıl hissettiğini anlatabiliyorsun.",
        ],
        "ipucu": "Yeni ve kalabalık ortamlarda iletişim bilgilerini ailenle paylaş ve sorumlu yetişkinlerin yönlendirmesine uy.",
    },
    "P6-G-6": {
        "nasil": [
            "Önceki adımlarda aldığın notları (rutin değişikliği, farklı roller, değişken ortam) önüne koy ve yeniden oku.",
            "Kendine sor: \"Düzenli işlerde mi daha rahatım, değişken işlerde mi, yoksa ikisinin karışımında mı?\" Cevabını bir cümleyle yaz.",
            "{bolum} içindeki alt alanları listele ve her birinin daha düzenli mi daha değişken mi olduğunu araştırarak yanına not et.",
            "Sana en uygun görünen alt alanı seç ve bunu neden seçtiğini 2-3 gerekçeyle yaz.",
        ],
        "kontrol": [
            "Tempo tercihini bir cümleyle yazdın.",
            "{bolum} içindeki alt alanları düzenli ve değişken olarak karşılaştırdın.",
            "Sana uygun alt alanı en az 2 gerekçesiyle yazdın.",
        ],
        "ipucu": "Bu değerlendirme kesin bir karar değil; yeni deneyimlerle değişebilir.",
    },
    "P6-U-1": {
        "nasil": [
            "Proje bazlı çalışma, işin belli bir başı ve sonu olan, her seferinde farklı görevlerle yürüyen işlerde çalışmaktır. {bolum} içindeki alt alanları ve meslekleri listele.",
            "Her alt alan için \"Bu işte her gün yeni bir sorun ya da proje var mı?\" sorusunu araştır; meslek tanıtım videoları, üniversite sayfaları ve röportajlar işine yarar.",
            "En hareketli görünen 2-3 alt alanı seç ve her biri için neden dinamik olduğunu bir cümleyle yaz.",
            "Bu alanlarda çalışan birine (ailenin ya da öğretmeninin bilgisi dahilinde) soru sorabilirsen not ettiklerini doğrulayabilirsin.",
        ],
        "kontrol": [
            "{bolum} içinde en az 2 dinamik alt alan belirledin.",
            "Her alt alanın neden dinamik olduğunu bir cümleyle yazdın.",
            "Bu bilgileri hangi kaynaklardan bulduğunu söyleyebiliyorsun.",
        ],
        "ipucu": "",
    },
    "P6-U-2": {
        "nasil": [
            "Sıkıcı bulduğun ama gerekli olan işleri listele: konu tekrarı, ödev, kelime ezberi, oda düzeni gibi.",
            "Bu işler için sabit bir zaman dilimi belirle. Örneğin: \"Okuldan gelince 17.00-17.45 ödev.\"",
            "Bu zamanı telefonuna tekrarlayan bir hatırlatıcı olarak ekle; bu sürede yalnızca listedeki işleri yap ve telefonunu uzaklaştır.",
            "Zaman dilimini koruduğun her günü tarihiyle bir tabloya işaretle.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Rutin işler için yazılı bir sabit zaman dilimin var.",
            "Tablonda bu zaman dilimini koruduğun en az 15 gün işaretli.",
        ],
        "ipucu": "Sıkıcı işi keyifli bir şeyin hemen öncesine koymak, ona başlamayı kolaylaştırır.",
    },
    "P7-G-1": {
        "nasil": [
            "Belirsiz bir yola çıkmış birini seç: bir girişimci, kâşif, sporcu ya da {bolum} alanından biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Neyi göze aldı? Nasıl hazırlandı? İşler ters gidince ne yaptı?",
            "Bu kişinin aldığı riski, hazırlığını ve ters giden bir anı nasıl yönettiğini 4-5 cümleyle yaz.",
            "Kendine uyarlayacağın bir davranışı tek cümleyle yaz. Örneğin: \"Yeni bir şeye başlamadan önce ters gidebilecek bir şeyi ve ne yapacağımı yazacağım.\"",
        ],
        "kontrol": [
            "Bu kişinin aldığı risk ve nasıl hazırlandığı yazılı.",
            "Ters giden bir anı nasıl yönettiğini yazdın.",
            "Kendine uyarlayacağın bir davranışı yazdın.",
        ],
        "ipucu": "Risk almak düşünmeden atılmak değildir; hikâyelerde en çok hazırlık kısmına dikkat et.",
    },
    "P7-G-2": {
        "nasil": [
            "Seni şu an kaygılandıran bir belirsizlik seç. Örneğin: \"Sınav sonucum ne olacak?\" ya da \"Yeni okulda arkadaş edinebilecek miyim?\"",
            "Bir kâğıda \"En kötü ne olabilir?\" sorusunu yaz ve gerçekçi bir cevap ver.",
            "Altına \"Bu olursa ne yaparım?\" sorusunu yaz ve 2-3 somut adım ekle. Örneğin: \"Öğretmenimle konuşurum, bir sonraki sınava farklı hazırlanırım.\"",
            "Son olarak bu en kötü durumun olma ihtimalinin ne kadar yüksek olduğunu ve neyin daha olası olduğunu bir cümleyle yaz.",
        ],
        "kontrol": [
            "Bir belirsizlik için en kötü senaryoyu yazdın.",
            "Bu senaryo olursa uygulayacağın en az 2 adımlık bir planın var.",
            "Daha olası sonucu bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Bu kaygı uzun süre aklından çıkmıyor ve seni çok zorluyorsa rehber öğretmeninle ya da güvendiğin bir yetişkinle konuş.",
    },
    "P7-G-3": {
        "nasil": [
            "Cevabını henüz bilmediğin küçük bir soru seç. Örneğin: \"Bitkiler müzikle daha hızlı büyür mü?\" ya da \"Sınıfımızda en çok hangi uygulama kullanılıyor?\"",
            "Başlamadan önce tahminini yaz; buna hipotez denir, yani sonucun ne olacağına dair önceden yaptığın tahmin.",
            "Basit ve güvenli bir yöntem planla (gözlem, küçük bir anket, evde basit bir deney). Gerekirse öğretmeninden ya da ailenden yardım iste.",
            "Her ölçümü ya da gözlemi tarihiyle bir tabloya kaydet.",
            "Sonuçları tahmininle karşılaştır ve seni şaşırtan bir bulguyu 2-3 cümleyle yaz.",
        ],
        "kontrol": [
            "Sonucu önceden bilinmeyen küçük bir projeyi bitirdin.",
            "Elinde tahminin, verilerin ve sonucun olan bir tablo ya da yazı var.",
            "Beklenmedik bir sonucu ve bunun ne anlama geldiğini anlatabiliyorsun.",
        ],
        "ipucu": "Tahminin tutmaması hata değildir; beklenmedik sonuçlar çoğu zaman en çok şey öğreten sonuçlardır.",
    },
    "P7-G-4": {
        "nasil": [
            "Karar günlüğü, verdiğin kararları ve sonuçlarını yazdığın bir defter ya da nottur. Bir sayfaya 4 sütun çiz: Tarih, Karar, Neyi bilmiyordum?, Sonuç.",
            "Tüm bilgilere sahip olmadan verdiğin kararları yaz. Örneğin: \"Hangi konuyu önce çalışacağımı seçtim.\"",
            "Kararın sonucu belli olduğunda \"Sonuç\" sütununu doldur.",
            "5 karar biriktiğinde hepsine geri dön ve bir cümle ekle: \"Eksik bilgiyle karar verirken neyi fark ettim?\"",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Karar günlüğünde en az 5 karar ve sonucu tarihiyle kayıtlı.",
            "Her karar için neyi bilmediğini yazdın.",
            "Eksik bilgiyle karar verirken neyi fark ettiğini bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Küçük kararları da yazabilirsin; önemli olan her kararı tarihiyle kaydetmek.",
    },
    "P7-G-5": {
        "nasil": [
            "Daha önce hiç bulunmadığın, ücretsiz ve yakın bir ortam seç: okulda yeni bir kulüp, yeni bir spor, okulun düzenlediği bir gezi ya da belediyenin ücretsiz bir gençlik etkinliği. Rehberlik servisinden bilgi alabilirsin.",
            "Seçimini ailenle konuş ve gerekiyorsa izinlerini al.",
            "Gitmeden önce bu ortamdan beklentini ve seni endişelendiren bir şeyi yaz.",
            "İlk gün kendini ne kadar rahat hissettiğini 1-10 arası puanla; sonraki bir günde aynı puanı yeniden ver.",
            "Bitince başlangıçtaki endişeni yeniden oku ve iki puan arasındaki farkı 2-3 cümleyle yaz.",
        ],
        "kontrol": [
            "Daha önce bulunmadığın bir ortamda yer aldın.",
            "İlk gün ile sonraki bir gün arasındaki rahatlık puanların yazılı.",
            "Bu farkı ve deneyimin sende neyi değiştirdiğini kısaca yazdın.",
        ],
        "ipucu": "Yeni bir ortamda kendini güvende hissetmezsen hemen sorumlu yetişkine ve ailene haber ver.",
    },
    "P7-G-6": {
        "nasil": [
            "Önceki adımlarda aldığın notları (risk alan birinin hikâyesi, karar günlüğü, yeni ortam, basamaklı meydan okuma) yeniden oku.",
            "Belirsizliğe karşı rahatlığını şu an ve birkaç ay önce için 1-10 arasında puanla; farkı ve nedenini bir cümleyle yaz.",
            "{bolum} içindeki alt alanları listele ve her birinin ne kadar öngörülebilir (önceden tahmin edilebilir, kuralları net) olduğunu araştırarak not et.",
            "Sana uygun görünen alt alanı ve nedenini 3-4 cümlelik bir değerlendirme olarak yaz.",
        ],
        "kontrol": [
            "Belirsizliğe karşı rahatlığının nasıl değiştiğini yazdın.",
            "{bolum} içindeki alt alanları, ne kadar önceden tahmin edilebilir olduklarına göre karşılaştırdın.",
            "3-4 cümlelik yazılı bir değerlendirmen var.",
        ],
        "ipucu": "Belirsizliğe karşı rahatlığın artmadıysa bu bir başarısızlık değil; daha öngörülebilir bir alt alan seçmek de bilinçli bir karardır.",
    },
    "P7-U-1": {
        "nasil": [
            "Yeni gelişen alan, son yıllarda ortaya çıkan ve kuralları henüz tam oturmamış iş ya da araştırma alanıdır. Arama motorunda \"{bolum} yeni alanlar\" ya da \"{bolum} geleceğin meslekleri\" gibi ifadeler ara.",
            "Güvenilir kaynakları tercih et: üniversite sayfaları, bilim dergileri, tanınmış haber kuruluşlarının teknoloji bölümleri.",
            "En az 2 yeni gelişen alan seç ve her biri için şu soruları cevapla: \"Ne yapılıyor?\", \"Neden yeni?\", \"Belirsizlik nereden kaynaklanıyor?\"",
            "Cevaplarını kaynak adlarıyla birlikte bir sayfaya yaz.",
        ],
        "kontrol": [
            "{bolum} içinde en az 2 yeni gelişen alan buldun.",
            "Her alan için ne yapıldığını ve neden belirsiz olduğunu yazdın.",
            "Kullandığın kaynakların adları not edilmiş.",
        ],
        "ipucu": "Bir alan çok fazla \"gelecekte her şeyi değiştirecek\" diye anlatılıyorsa başka kaynaklarla da karşılaştır.",
    },
    "P7-U-2": {
        "nasil": [
            "Artı/eksi listesi, bir kararın iyi ve kötü yanlarını yan yana yazdığın basit bir tablodur. Yaklaşan önemli kararlarını düşün (kulüp seçimi, kurs, yarışmaya katılmak gibi).",
            "Bir sayfayı ikiye böl: \"Artılar\" ve \"Eksiler\". Her seçenek için en az 3'er madde yaz.",
            "Her maddenin yanına önemini 1-3 arasında puanla; böylece sadece sayıya değil ağırlığa da bakarsın.",
            "Kararını ver ve listenin altına neden bu kararı verdiğini bir cümleyle yaz.",
            "Sonuç belli olduğunda listene dön ve tahminlerinin ne kadar doğru çıktığını not et.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "En az 2 kararda yazılı bir artı/eksi listesi kullandın.",
            "Her listenin altında verdiğin karar ve gerekçesi yazılı.",
            "Bir kararın sonucunu listenle karşılaştırdın.",
        ],
        "ipucu": "Önemli kararlarda listeni bir aile büyüğünle ya da öğretmeninle paylaşmak farklı bakış açıları kazandırır.",
    },
    "P8-G-1": {
        "nasil": [
            "Yaklaşan bir grup çalışması seç ve grubuna küçük bir koordinasyon görevini üstlenebileceğini söyle.",
            "Koordinasyon, işlerin düzenli yürümesini sağlamaktır. Örneğin herkese uygun bir toplantı saatini sor ve ortak saati belirle.",
            "Ya da yapılacak işleri listele ve kimin hangi işi yapacağını grupla birlikte belirle.",
            "Kararı (saat ya da görev listesi) gruba yazılı olarak gönder.",
            "Görev bitince neyin kolay, neyin zor olduğunu bir cümleyle not et.",
        ],
        "kontrol": [
            "Bir grup çalışmasında koordinasyon görevini tamamladın.",
            "Gruba gönderdiğin bir toplantı saati ya da görev listesi var.",
            "Bu görevde neyin kolay, neyin zor olduğunu söyleyebiliyorsun.",
        ],
        "ipucu": "Görevleri dağıtırken arkadaşlarına ne yapmak istediklerini sormak işi kolaylaştırır.",
    },
    "P8-G-2": {
        "nasil": [
            "Üç liderlik tarzını tanı: yönlendiren lider net talimat verir ve kararları kendisi alır; destekleyen lider ekibini dinler ve yardım eder; örnek olan lider işi kendisi yaparak yol gösterir.",
            "Bir lider seç: bir takım kaptanı, tarihî bir kişi ya da {bolum} alanında tanınmış biri. Okul ya da halk kütüphanesinin biyografi rafına, TRT Belgesel gibi bir kanala ya da güvenilir bir röportaja bak.",
            "Okurken ya da izlerken not et: Zor bir anda ne yaptı? Ekibine nasıl davrandı? Bu üç tarzdan hangisini kullandı?",
            "Bu liderin tarzını bir örnek olayla 2-3 cümleyle yaz.",
            "Bir grupta yer aldığın bir anı hatırla; sana en yakın tarzı seç ve nedenini 2-3 cümleyle yaz.",
        ],
        "kontrol": [
            "Üç liderlik tarzının farkını bir cümleyle anlatabiliyorsun.",
            "İncelediğin liderin tarzını bir örnek olayla yazdın.",
            "Sana en yakın tarzı kendi deneyiminden bir örnekle gerekçelendirdin.",
        ],
        "ipucu": "Çoğu kişi duruma göre farklı tarzları birlikte kullanır; tek bir kalıba sığman gerekmez.",
    },
    "P8-G-3": {
        "nasil": [
            "Sınıfında ya da kulübünde yapılabilecek küçük bir etkinlik seç: bilgi yarışması, film gösterimi, kitap değişimi ya da kısa bir turnuva gibi.",
            "Fikrini sınıf öğretmenine ya da kulüp danışmanına anlat ve izin al; tarih ve yer belirleyin.",
            "Yapılacakları listele (duyuru, malzeme, program) ve görevleri gönüllü arkadaşlarınla paylaş.",
            "Etkinlikten birkaç gün önce hazırlıkları kontrol et; eksik olan bir şey varsa planını güncelle.",
            "Etkinlikten sonra neyin iyi gittiğini ve neyi farklı yapacağını 2-3 cümleyle yaz.",
        ],
        "kontrol": [
            "Organize ettiğin etkinlik gerçekleşti.",
            "Elinde görevlerin ve tarihlerin yazılı olduğu bir plan var.",
            "Etkinlikten sonra kısa bir değerlendirme yazdın.",
        ],
        "ipucu": "Etkinliği küçük tutmak, ilk deneyimin için işini çok kolaylaştırır.",
    },
    "P8-G-4": {
        "nasil": [
            "Liderlik ettiğin ya da koordine ettiğin bir işi seç ve o işte seninle çalışan 2-3 arkadaşını belirle.",
            "Onlara 2 kısa soru sor: \"Bu işte neyi iyi yaptım?\" ve \"Neyi daha iyi yapabilirdim?\" Yüz yüze ya da yazılı sorabilirsin.",
            "Cevapları dinlerken araya girmeden ve savunmaya geçmeden dinle; sonunda teşekkür et.",
            "Aldığın geri bildirimleri bir sayfaya yaz ve tekrar eden noktaları işaretle.",
            "Bir sonraki işte deneyeceğin bir değişikliği bir cümleyle yaz.",
        ],
        "kontrol": [
            "En az 2 kişiden liderlik ettiğin işle ilgili geri bildirim aldın.",
            "Geri bildirimler bir sayfada yazılı.",
            "Bir sonraki sefer deneyeceğin bir değişikliği söyleyebiliyorsun.",
        ],
        "ipucu": "Eleştiri duymak zor gelebilir; bunu kişiliğine değil, yaptığın işe dair bir bilgi olarak düşün.",
    },
    "P8-G-5": {
        "nasil": [
            "Üye olduğun ya da katılmak istediğin bir kulüpte hangi yönetim görevlerinin olduğunu öğren (başkan yardımcısı, proje sorumlusu, sekreter gibi).",
            "Kulüp danışmanıyla konuşup bir göreve aday ol; seçim varsa neden bu görevi istediğini 2-3 cümleyle anlat.",
            "Görevi aldığında görev süren için 2-3 hedef belirle ve bunları ekiple paylaş.",
            "Görev boyunca düzenli aralıklarla kısa bir toplantı ya da mesajla hedeflere ne kadar yaklaştığınızı kontrol et.",
            "Görev bitince neleri başardığınızı ve neyi öğrendiğini bir sayfada değerlendir.",
        ],
        "kontrol": [
            "Bir kulüpte yönetim görevini bir dönem boyunca sürdürdün.",
            "Başta yazdığın 2-3 hedef ve tarihli kontrol notların var.",
            "Görev bitince yazdığın bir değerlendirme sayfan var.",
        ],
        "ipucu": "Okul derslerinle dengeyi korumak için kulüp işlerine sabit bir zaman ayır.",
    },
    "P8-G-6": {
        "nasil": [
            "İki yolu tanı: yönetici ekipleri ve işleri yönetir, planlar ve kararlar alır; uzman bir konuda derinleşir ve o işin en iyi yapanlarından olur. İkisi de değerli yollardır.",
            "Bir sayfayı ikiye böl ve her yol için {bolum} alanından bir iş örneği yaz.",
            "Her yol için kendine sor: \"Bu işte en çok neyi severim? Beni ne zorlar?\" Cevaplarını yaz.",
            "Önceki liderlik deneyimlerine bak: ekibi yönetmek mi, işi derinlemesine yapmak mı sana daha çok enerji verdi?",
            "Tercihini ve en az 2 gerekçesini yaz; tercihinin ileride değişebileceğini unutma.",
        ],
        "kontrol": [
            "Yönetici ve uzman yolları için {bolum} alanından birer örnek yazdın.",
            "Tercihini en az 2 gerekçesiyle yazdın.",
            "Tercihini birine bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Kararsız kalırsan ikisinin karışımını seçebilirsin; birçok kişi önce uzmanlaşıp sonra yönetime geçer.",
    },
    "P8-U-1": {
        "nasil": [
            "Okulundaki liderlik fırsatlarını öğren: sınıf başkanlığı, okul meclisi, takım kaptanlığı, kulüp ya da proje liderliği gibi.",
            "Sana en uygun olanı seç ve başvuru tarihini ve şartlarını öğretmeninden ya da rehberlik servisinden öğren.",
            "Neden bu rolü istediğini ve ne yapmak istediğini 3-4 cümleyle yaz; seçim varsa bu metni kısa bir konuşmaya çevir.",
            "Başvurunu zamanında yap; gerekirse arkadaşlarından ya da öğretmeninden destek iste.",
            "Sonuç ne olursa olsun bu deneyimden ne öğrendiğini bir cümleyle not et.",
        ],
        "kontrol": [
            "Bir liderlik rolüne başvurdun.",
            "Neden bu rolü istediğini anlatan yazılı bir metnin var.",
            "Başvuru deneyiminden öğrendiğin bir şeyi söyleyebiliyorsun.",
        ],
        "ipucu": "Seçilmemek başarısızlık değildir; başvurmak bu adımın asıl hedefi.",
    },
    "P8-U-2": {
        "nasil": [
            "Yönettiğin bir işte vermen gereken bir karar seç: proje konusu, görev dağılımı ya da sunum biçimi gibi.",
            "Karar vermeden önce ekibe sor: \"Bu konuda ne düşünüyorsunuz?\" Herkese konuşma fırsatı ver ve fikirleri yaz.",
            "Fikirleri dinlerken aktif dinleme kullan, yani söyleneni kendi cümlelerinle özetle: \"Yani sen ... öneriyorsun.\"",
            "Fikirleri karşılaştır ve ekip önerilerine dayanan bir karar al.",
            "Kararı açıklarken hangi önerilerden yararlandığını söyle; ekibin tepkisini not et.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "En az bir kararı ekibin fikirlerine dayanarak aldın.",
            "Ekipten gelen fikirlerin yazılı olduğu bir notun var.",
            "Kararında hangi önerilerden yararlandığını açıklayabiliyorsun.",
        ],
        "ipucu": "Her fikri uygulamak zorunda değilsin; önemli olan herkesin dinlendiğini hissetmesi.",
    },
    "I1-G-1": {
        "nasil": [
            "Önündeki işleri (ödevler, sınavlar, kurslar, ev işleri, sosyal planlar) bir kâğıda alt alta yaz; 10 madde civarı yeterli.",
            "Kâğıdı bir dikey, bir yatay çizgiyle 4 kutuya böl. Bu, Eisenhower matrisidir: işleri önemine ve aciliyetine göre ayıran basit bir tablodur. Kutulara yaz: 1) Önemli ve acil, 2) Önemli ama acil değil, 3) Acil ama önemsiz, 4) Ne önemli ne acil.",
            "Her işi kendine sorarak bir kutuya taşı: \"Bunu yapmazsam hedefime zarar verir mi?\" (önem) ve \"Teslimi 1–2 gün içinde mi?\" (aciliyet). Örneğin: yarınki sınav 1. kutuya girer.",
            "1. kutudaki işlerden başla; 2. kutudakilere de plan içinde yer aç, 4. kutudakileri azaltmayı dene.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. İşe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Önündeki işleri 4 kutuya ayırdığın bir sayfan var.",
            "Her kutuda en az bir iş yazıyor ya da boş kutunun nedenini biliyorsun.",
            "1. kutudan bir işi bitirdin.",
        ],
        "ipucu": "Her şeyi 1. kutuya koymak sık yapılan bir hatadır; sadece gerçekten 1–2 gün içinde yapılması gerekenleri oraya yaz.",
    },
    "I1-G-2": {
        "nasil": [
            "Defterine ya da telefonuna iki gün için uyanma saatinden yatma saatine kadar yarım saatlik satırlar aç (07.00, 07.30, 08.00 …).",
            "Gün boyunca her yarım saatin sonunda o sürede ne yaptığını tek kelimeyle yaz: okul, ders çalışma, telefon, yol, yemek, sohbet gibi.",
            "Unutursan en geç öğle ve akşam olmak üzere günde iki kez dur ve boşlukları hatırladığın kadarıyla doldur.",
            "İki günün sonunda her etkinliğin kaç yarım saat sürdüğünü say ve en çok zaman alan 3 etkinliği yuvarlak içine al.",
            "Altına bir cümle yaz: \"Zamanımı en çok … alıyor, bunu beklemiyordum / bekliyordum.\"",
        ],
        "kontrol": [
            "İki günü yarım saatlik dilimlerle gösteren bir kayıt var elinde.",
            "Zamanını en çok alan 3 etkinliği ve kabaca kaç saat sürdüklerini söyleyebiliyorsun.",
            "Bu kayıttan çıkardığın bir sonucu bir cümleyle yazdın.",
        ],
        "ipucu": "Kaydı sonradan tamamen tahminle doldurmak sonucu yanıltır; telefona alarm kurup gün içinde not almayı dene.",
    },
    "I1-G-3": {
        "nasil": [
            "Her sabah (ya da bir önceki akşam) 3 dakika ayır ve o günkü işlerini aklından geçir.",
            "İçlerinden en önemli 3 tanesini seç ve bir kâğıda ya da not uygulamasına tarihle birlikte \"Bugünün 3'ü\" başlığıyla yaz. Örneğin: fizik ödevi, 20 paragraf sorusu, kursa kayıt formu.",
            "Okuldan sonraki boş zamanında telefona ve diğer işlere geçmeden önce bu 3 işi bitirmeye çalış.",
            "Akşam yaptıklarının yanına tik at; bitmeyen olduysa nedenini tek kelimeyle not et (süre, unuttum, zor geldi). Her 7 kayıtta bir kaç gün 3 işi de bitirdiğini say.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 15 gün için tarihli \"Bugünün 3'ü\" listen var.",
            "Her listede kaç işi bitirdiğin işaretli.",
            "Hangi tür işlerin genelde yarım kaldığını söyleyebiliyorsun.",
        ],
        "ipucu": "3'ten fazla iş yazma; liste uzadıkça hiçbiri öncelik olmaktan çıkar.",
    },
    "I1-G-4": {
        "nasil": [
            "Önünde 2–4 haftalık süren bir ödev ya da proje seç ve teslim tarihini bir kâğıdın en üstüne yaz.",
            "İşi 4–8 küçük parçaya böl; her parça en fazla 1–2 saatte bitebilecek kadar küçük olsun. Örneğin: konu seç, kaynak bul, taslak yaz, görselleri hazırla, son kontrol.",
            "Teslim tarihinden geriye doğru giderek her parçaya bir bitiş tarihi ver; en sona 1–2 günlük yedek süre bırak.",
            "Bu tarihleri takvimine ya da ajandana işle ve her parçayı bitirdiğinde üstünü çiz.",
            "Bir parça gecikirse sonraki tarihleri hemen güncelle ki teslim tarihi kaymasın.",
        ],
        "kontrol": [
            "Parçaları ve her birinin tarihini gösteren bir liste ya da takvim var.",
            "Parçaların çoğunu kendi verdiğin tarihlerde bitirdin.",
            "Proje teslim tarihinde ya da öncesinde teslim edildi.",
        ],
        "ipucu": "İlk parçayı \"araştır\" gibi belirsiz bırakma; \"3 kaynak bul ve linklerini kaydet\" gibi net yaz.",
    },
    "I1-G-5": {
        "nasil": [
            "Bir sonraki sınav döneminin tarihlerini öğren ve bir takvimde her sınavı işaretle.",
            "Geriye doğru plan yap: Sınav gününden başlayıp geriye sayarak her ders için tekrar günlerini yerleştir. Örneğin: sınav 20'sinde ise 19'u genel tekrar, 15–18 arası konu çalışması.",
            "Her dersin konularını listele ve konuları bu günlere dağıt; günde en fazla 2–3 ders olsun.",
            "Takvimde birkaç boş gün bırak; yetişmeyen konuları o günlere kaydır.",
            "Her akşam o günün planına uyup uymadığını takvime işaretle (tik ya da çarpı) ve sınavlar bitince kaç gün uyduğunu say.",
        ],
        "kontrol": [
            "Sınav tarihlerinden geriye doğru hazırlanmış bir çalışma takvimin var.",
            "Takvimdeki günlerin çoğunda tik işareti var.",
            "Sınavlara son gece konu yetiştirmeden, planladığın tekrarları yapmış olarak girdin.",
        ],
        "ipucu": "Planı çok sıkı yaparsan ilk aksaklıkta bırakırsın; mutlaka boş gün ve yedek saat koy.",
    },
    "I1-G-6": {
        "nasil": [
            "İlk 5 çalışma oturumunda normal şekilde çalış ve her oturumda kaç dakika dikkatin dağılmadan çalışabildiğini not et; bu senin başlangıç ölçümün.",
            "Sonraki oturumlarda telefonu başka odaya koy ya da sessize alıp ters çevir; istersen bir odak uygulaması kullan.",
            "Pomodoro tekniğini dene: 25 dakika tek bir işe odaklan, sonra 5 dakika mola ver. 4 turdan sonra 15–20 dakikalık uzun mola ver.",
            "Her oturumun tarihini ve odaklı çalışma süreni bir tabloya yaz.",
            "Birkaç hafta sonra ilk 5 oturumun ortalamasıyla son 5 oturumun ortalamasını karşılaştır.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Başlangıç oturumları ve sonraki oturumlar için tarihli odak sürelerini gösteren bir tablon var.",
            "İlk 5 oturumun ortalamasını son 5 oturumunkiyle karşılaştırıp yazdın.",
            "Seni en çok hangi dikkat dağıtıcının etkilediğini söyleyebiliyorsun.",
        ],
        "ipucu": "Telefonu sadece \"bakmayacağım\" diye yanında tutmak çoğu zaman işe yaramaz; fiziksel olarak uzaklaştırmak daha etkilidir.",
    },
    "I1-U-1": {
        "nasil": [
            "{bolum} ile ilgili bir ek çalışma seç: ücretsiz bir çevrim içi kurs dersi, bir kitap bölümü ya da bir belgesel.",
            "Mevcut planına bak; okul, ödev ve kurs gibi sabit işlerinin dışında kalan boşlukları bul.",
            "Ek çalışma için 2–3 tane 30–45 dakikalık zaman dilimi seç ve planına yaz; istersen telefonuna hatırlatıcı kur.",
            "İlk oturumu yap ve tarihli kısa bir not al: Ne çalıştım, nasıl gitti?",
        ],
        "kontrol": [
            "Ek çalışma planında yazılı.",
            "İlk oturumu yaptın ve tarihli notun var.",
            "Hangi ek çalışmayı neden seçtiğini bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Ek çalışmayı yorgun olduğun gece saatlerine koyma; enerjinin yerinde olduğu bir saati seç.",
    },
    "I1-U-2": {
        "nasil": [
            "Bir grup projesinin başında ekibe takvimi hazırlamayı ve takip etmeyi önerebileceğini söyle.",
            "İşi parçalara böl, her parçaya bir sorumlu ve bir bitiş tarihi yaz; teslimden önce 2–3 günlük yedek süre bırak.",
            "Takvimi herkesin görebileceği bir yere koy: ortak bir belge, mesaj grubu ya da basılı bir kâğıt.",
            "Düzenli aralıklarla ekibe kısa bir durum sorusu sor: \"Son konuşmamızdan beri biten neler var, takılan bir şey var mı?\"",
            "Gecikme olursa suçlamadan, birlikte yeni tarih belirle ve takvimi güncelle.",
        ],
        "kontrol": [
            "Görevleri, sorumluları ve tarihleri gösteren bir proje takvimin var.",
            "Proje boyunca en az 2–3 kez ekiple ilerleme kontrolü yaptın.",
            "Proje teslim tarihinde tamamlandı.",
        ],
        "ipucu": "Takvimi tek başına hazırlayıp ekibe dayatma; tarihleri herkesle konuşarak kesinleştir.",
    },
    "I2-G-1": {
        "nasil": [
            "Ben-dilini öğren: Karşındakini suçlamak yerine kendi duygunu ve nedenini anlatırsın. Kalıp: \"Ben … hissediyorum, çünkü … . … olursa sevinirim.\"",
            "Bir kâğıda \"sen-dili\" ile söylediğin bir cümle yaz ve ben-diline çevir. Örneğin: \"Sen hep geç kalıyorsun\" yerine \"Beklediğimde endişeleniyorum, çünkü planlarımız kayıyor.\"",
            "Bir sonraki gergin konuşmada konuşmaya başlamadan önce bir nefes al ve kalıbı kullan.",
            "Her kullanımdan sonra tarihli kısa bir not al: Kime söyledin, ne dedin, karşındaki nasıl tepki verdi?",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. İşe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 2 kez ben-dili kullandın.",
            "Bu kullanımları ve karşındakinin tepkisini yazdığın notların var.",
            "Bir sen-dili cümlesini ben-diline çevirebildiğini gösteren bir örneğin var.",
        ],
        "ipucu": "\"Ben senin hep geç kaldığını hissediyorum\" gibi cümleler gizli sen-dilidir; kendi duygunu söylemeye odaklan.",
    },
    "I2-G-2": {
        "nasil": [
            "Son yaşadığın bir anlaşmazlığı seç (arkadaş, aile, grup ödevi) ve 3–4 cümleyle ne olduğunu yaz.",
            "İki başlık aç: \"Ben ne istiyordum?\" ve \"Karşımdaki ne istiyordu?\" Her birine 1–2 cümle yaz.",
            "Konuşmada işleri zorlaştıran bir anı işaretle. Örneğin: ses yükseldiğinde ya da biri sözü kestiğinde.",
            "\"Nasıl çözülebilirdi?\" başlığı altına en az bir alternatif yol yaz. Örneğin: önce karşımı dinleyip sonra kendi isteğimi söylemek.",
        ],
        "kontrol": [
            "Anlaşmazlığı, iki tarafın isteklerini ve olayı yazdığın bir sayfan var.",
            "En az bir alternatif çözüm yolu yazdın.",
            "Bir sonraki benzer durumda farklı yapacağın bir şeyi söyleyebiliyorsun.",
        ],
        "ipucu": "Yazarken haklı kim sorusuna takılma; amaç iki tarafın isteğini görebilmek.",
    },
    "I2-G-3": {
        "nasil": [
            "Yeni bir grup çalışması başlarken ilk toplantıda 5–10 dakikayı ekip kurallarına ayırmayı öner.",
            "3–5 kuraldan oluşan bir taslak hazırla: Görev dağılımı (kim ne yapıyor), karar yöntemi (oylama mı, oy birliği mi), iletişim (hangi kanaldan, kaç saat içinde cevap), gecikme olursa ne yapılacağı.",
            "Taslağı ekiple konuş, herkesin önerisini ekle ve son hâlini herkesin göreceği bir yere yaz.",
            "Proje boyunca bir sorun çıktığında kurallara geri dön: \"Kuralımıza göre bunu oylamayla karar veriyorduk.\"",
        ],
        "kontrol": [
            "Ekiple birlikte yazılmış bir kural listesi var.",
            "Proje boyunca ekibin bu kurallara göre görev paylaştığını ya da karar verdiğini gördün.",
            "En az bir durumda kurallar bir tartışmayı çözmeye yardım etti.",
        ],
        "ipucu": "Kuralları çok uzun tutma; 5'ten fazla kural genelde unutulur.",
    },
    "I2-G-4": {
        "nasil": [
            "Müzakere ve uzlaşma üzerine kısa bir kaynak seç; örneğin Fisher ve Ury'nin \"Evet'e Ulaşmak\" kitabı ya da bu konuda bir özet. Okul kütüphanesine de sorabilirsin.",
            "Kaynağı bölümlere ayırarak oku; her oturumda bir bölüm yeterli.",
            "Her oturumdan sonra defterine aklında kalan bir fikri bir cümleyle yaz. Örneğin: \"Kişiyle sorunu ayır.\"",
            "Okuma bitince bu fikirlerden günlük hayatında uygulayabileceğin 3 tanesini seç ve her birinin yanına nerede kullanacağını yaz; birini bir sonraki uygun durumda dene.",
        ],
        "kontrol": [
            "Okuduğun kaynağın adını ve bitirdiğin bölümleri söyleyebiliyorsun.",
            "3 uygulanabilir fikri yazdığın bir listen var.",
            "Her fikrin yanında onu kullanabileceğin somut bir durum yazıyor.",
        ],
        "ipucu": "Kitap ağır gelirse önce bölüm özetlerini oku, sonra ilgini çeken bölümlere dön.",
    },
    "I2-G-5": {
        "nasil": [
            "Okulunda münazara kulübü ya da Model Birleşmiş Milletler (MUN) olup olmadığını öğren. MUN, öğrencilerin ülkeleri temsil ederek bir sorunu tartıştığı bir canlandırma etkinliğidir.",
            "Okulunda yoksa rehberlik servisine ya da bir öğretmenine yakın okullardaki etkinlikleri sor; katılım için ailenin onayını al.",
            "Kayıt olduktan sonra sana verilen konu ya da ülke hakkında hazırlan: temel görüşleri ve karşı görüşleri birkaç maddede yaz.",
            "Etkinlikte en az bir kez söz al, bir öneri sun ya da bir karşı görüşe saygılı şekilde cevap ver.",
            "Etkinlikten sonra farklı görüşleri yönetirken neyin zor geldiğini 2–3 cümleyle not et.",
        ],
        "kontrol": [
            "En az bir münazara ya da MUN etkinliğine katıldın.",
            "Etkinlikte söz aldın ya da bir görev üstlendin.",
            "Etkinlikten sonra yazdığın kısa bir değerlendirme notun var.",
        ],
        "ipucu": "İlk etkinlikte konuşmak zor gelebilir; önceden yazdığın bir açılış cümlesi işini kolaylaştırır.",
    },
    "I2-G-6": {
        "nasil": [
            "Arkadaşların arasında küçük bir anlaşmazlık olduğunda, taraf tutmadan dinlemeyi teklif et: \"İsterseniz ikinizi de dinleyeyim.\"",
            "Her iki tarafın da sözünü kesmeden konuşmasına izin ver; sırayla konuşmalarını sağla.",
            "Duyduğunu özetle: \"Yani sen … istiyorsun, sen de … istiyorsun, doğru mu anladım?\" Bu, iki tarafın da anlaşıldığını hissetmesine yardım eder.",
            "Çözümü sen söyleme; \"Sizce ikinizin de kabul edebileceği bir yol ne olabilir?\" diye sor.",
            "Kavga büyükse ya da biri zarar görüyorsa araya girme, bir öğretmene ya da rehberlik servisine haber ver.",
        ],
        "kontrol": [
            "Bir anlaşmazlıkta iki tarafı da dinlediğin bir durum yaşadın.",
            "Konuşmanın sonunda gerginliğin azaldığını gözlemledin.",
            "Hangi sorunun ya da cümlenin işe yaradığını söyleyebiliyorsun.",
        ],
        "ipucu": "Arkadaşlarından birine yakınsan tarafsız kalmak zordur; bu durumda başka birinin arabulucu olmasını önermek daha doğru olabilir.",
    },
    "I2-G-7": {
        "nasil": [
            "İki tarafın anlaşmazlığını konuşarak çözdüğü gerçek bir örnek bul: sporda, okulda ya da {bolum} alanında. Güvenilir bir haber, TRT Belgesel gibi bir kanaldaki bir belgesel ya da kütüphaneden bir biyografi kullanabilirsin.",
            "Bir kâğıdı ikiye böl ve her tarafın ne istediğini ayrı ayrı yaz.",
            "Orta yolun nasıl bulunduğunu yaz: Kim neyden vazgeçti, ne kazandı? Arada aracılık yapan biri var mıydı?",
            "Bu hikâyeden senin kullanabileceğin bir dersi tek cümleyle yaz. Örneğin: \"Önce ortak hedefi bulmak, tartışmayı yumuşatıyor.\"",
        ],
        "kontrol": [
            "İki tarafın istedikleri ayrı ayrı yazılı.",
            "Bulunan çözümü kendi cümlelerinle anlattın.",
            "Kullanabileceğin bir dersi yazdın.",
        ],
        "ipucu": "Haberlerde çoğu zaman tek tarafın sesi duyulur; mümkünse iki tarafı da anlatan bir kaynak seç.",
    },
    "I2-U-1": {
        "nasil": [
            "Yeni bir grup çalışması başladığında anlaşmazlık çıkarsa ne yapılacağını konuşmayı öner.",
            "Basit bir çözüm yöntemi yaz. Örneğin: 1) Herkes görüşünü 2 dakikada anlatır, 2) Artı ve eksiler konuşulur, 3) Uzlaşma olmazsa oylama yapılır.",
            "Yöntemi ekibe sun ve değiştirmek istedikleri bir şey olup olmadığını sor.",
            "Kabul edilen hâlini ekibin mesaj grubuna ya da ortak belgesine yaz.",
        ],
        "kontrol": [
            "Yazılı bir anlaşmazlık çözüm yöntemi önerdin.",
            "Ekip yöntemi kabul etti ya da küçük değişikliklerle benimsedi.",
        ],
        "ipucu": "Yöntemi bir anlaşmazlık çıkmadan önce konuşmak, sonradan konuşmaktan çok daha kolaydır.",
    },
    "I2-U-2": {
        "nasil": [
            "Okulunda akran arabuluculuğu (arkadaşlar arasındaki anlaşmazlığı çözmeye yardım etme), öğrenci temsilciliği ya da sınıf başkanlığı gibi hangi rollerin olduğunu rehberlik servisine ya da sınıf öğretmenine sor.",
            "Sana uygun olan rolün görevlerini ve seçim ya da başvuru tarihlerini öğren.",
            "Başvur ya da aday ol; gerekiyorsa neden bu rolü istediğini anlatan 3–4 cümlelik kısa bir konuşma hazırla.",
            "Rolü aldığında dönem boyunca yaşadığın önemli bir durumu ve nasıl yönettiğini defterine not et.",
        ],
        "kontrol": [
            "Okulda resmî ya da yarı resmî bir rol üstlendin.",
            "Bu rolde yaptığın en az bir görevi örnek olarak anlatabiliyorsun.",
        ],
        "ipucu": "Seçilemesen bile kulüp ya da etkinlikte gönüllü bir görev almak da aynı beceriyi geliştirir.",
    },
    "I3-G-1": {
        "nasil": [
            "Küçük kararlar için kendine 2 dakikalık bir süre sınırı koy. Küçük kararlar: ne giyeceğin, ne yiyeceğin, hangi dersle başlayacağın gibi geri dönüşü kolay seçimler.",
            "Karar anında telefonun saatini başlat; 2 dakika içinde seçeneklerden birini seç ve geri dönme.",
            "Her kararı tarihli kısa bir notla kaydet: Karar neydi, süreyi aştın mı?",
            "5 karar biriktiğinde notlarına bak: Pişman olduğun var mı? Çoğu zaman olmadığını fark edeceksin.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Süre sınırıyla verdiğin en az 5 küçük kararın tarihli notu var.",
            "Kararların çoğunda 2 dakikayı aşmadın.",
            "Hızlı karar vermenin sana ne kazandırdığını bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Bu kural küçük kararlar içindir; okul seçimi gibi büyük kararları aceleye getirme.",
    },
    "I3-G-2": {
        "nasil": [
            "Önünde zor gelen bir karar seç (ör. hangi kursa yazılacağın, bir etkinliğe katılıp katılmayacağın).",
            "Bir kâğıda seçeneklerini yaz ve şu soruyu sor: \"Elimdeki bilgiyle en makul seçenek hangisi?\"",
            "Her seçenek için ikinci soruyu cevapla: \"Yanılırsam ne olur, bunu düzeltebilir miyim?\"",
            "Cevaplarına bakarak bir seçenek seç ve neden seçtiğini bir cümleyle yaz.",
        ],
        "kontrol": [
            "Bir kararında bu iki soruyu yazılı olarak kullandın.",
            "Seçtiğin seçeneği ve nedenini bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Tüm bilgiyi beklemek kararı sonsuza erteleyebilir; \"yeterince bilgim var mı?\" diye sor, \"her şeyi biliyor muyum?\" diye değil.",
    },
    "I3-G-3": {
        "nasil": [
            "Bir deneme sınavının toplam süresini soru sayısına bölerek soru başına ortalama süreyi hesapla ve kâğıdın köşesine yaz.",
            "Kendine bir kural koy: Bir soruda bu sürenin iki katını geçersen soruyu işaretle ve sonrakine geç.",
            "Sınavın sonunda kalan süreyle işaretli sorulara geri dön.",
            "Her denemeden sonra kaç soruyu süresi yetmediği için boş bıraktığını bir tabloya yaz.",
            "En az 3 denemeden sonra bu sayının nasıl değiştiğine bak.",
        ],
        "kontrol": [
            "En az 3 deneme için süreyi yetiştirip yetiştirmediğin ve boş bıraktığın soru sayısı tablonda yazılı.",
            "İlk ve son denemeni karşılaştırıp süre kullanımında neyin değiştiğini söyleyebiliyorsun.",
            "Takıldığın bir soruyu bırakıp devam ettiğin en az birkaç örnek hatırlıyorsun.",
        ],
        "ipucu": "Bıraktığın soruyu yanlış bildiğinden değil, zaman kazanmak için bıraktın; geri dönmeyi unutma.",
    },
    "I3-G-4": {
        "nasil": [
            "Kendine uygun bir strateji oyunu seç: satranç, Sudoku, zekâ oyunları ya da süreli bulmacalar.",
            "Her oyunda kendine bir süre sınırı koy (ör. 15 dakika ya da süreli satranç).",
            "Oynarken her hamleden önce kısa bir an dur ve kendine sor: \"Bu hamlenin sonucu ne olabilir?\"",
            "Her oyundan sonra takip tablona tarihi, süreyi ve sonucu yaz.",
            "10 oyun biriktiğinde süre baskısında nasıl karar verdiğini 2 cümleyle yaz: Acele ettiğimde ne oluyor, sakin kaldığımda ne oluyor?",
        ],
        "kontrol": [
            "Takip tablonda en az 10 süreli oyun ya da bulmaca tarihiyle yazılı.",
            "Süre baskısında nasıl karar verdiğine dair 2 cümlelik notun var.",
        ],
        "ipucu": "Sadece eğlencesine hızlı hızlı oynamak yerine bazı oyunlarda hamleni düşünmek için kendine süre ver.",
    },
    "I3-G-5": {
        "nasil": [
            "{bolum} alanında yaşanabilecek bir kriz düşün. Örneğin: bir sistemin çökmesi, bir projede bütçenin bitmesi, acil bir hasta durumu. Gerekirse internette \"{bolum} kriz örneği\" diye ara.",
            "Kriz senaryosunu 4–5 cümleyle yaz: ne oluyor, kim etkileniyor, ne kadar zaman var?",
            "\"Ben olsam ne yapardım?\" başlığı altına ilk 3 adımını sırayla yaz.",
            "Her adım için olası bir riski ve buna karşı bir yedek planı (B planı) bir cümleyle not et.",
        ],
        "kontrol": [
            "Yazılı bir kriz senaryon var.",
            "Bu senaryo için sıralı adımlardan oluşan bir çözüm planın var.",
            "Planındaki en az bir adım için yedek planın da yazılı.",
        ],
        "ipucu": "Gerçek dışı ve abartılı senaryolar yerine o mesleğin günlük hayatında olabilecek bir durumu seç.",
    },
    "I3-G-6": {
        "nasil": [
            "Bir defter ya da dosya aç ve adını \"Karar günlüğü\" koy.",
            "Önemli bir karar verdiğinde (ör. bir kursa yazılma, bir arkadaşla konuşma) tarihini ve neyi neden seçtiğini 2–3 cümleyle yaz.",
            "Birkaç gün sonra aynı sayfaya dön ve iki soruyu cevapla: \"Neyi doğru yaptım?\" ve \"Neyi farklı yapardım?\"",
            "En az 5 kararı bu şekilde değerlendir.",
            "Sonunda tüm değerlendirmelere bakıp sık tekrar eden bir alışkanlığını bir cümleyle yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Karar günlüğünde en az 5 kararın değerlendirmesi var.",
            "Her değerlendirmede \"doğru yaptıklarım\" ve \"farklı yapardım\" kısmı dolu.",
            "Karar verirken sık yaptığın bir hatayı ya da güçlü yanını söyleyebiliyorsun.",
        ],
        "ipucu": "Birkaç gün beklemek önemlidir; kararın hemen ardından yapılan değerlendirme genelde duygusal olur.",
    },
    "I3-G-7": {
        "nasil": [
            "Zor bir anda karar vermek zorunda kalmış birini seç: bir pilot, doktor, hakem ya da {bolum} alanında çalışan biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Ne yaşadı? Nasıl tepki verdi? Bundan ne öğrendi?",
            "Kişinin kararını 3 adımda yaz: 1) Elinde hangi bilgi vardı? 2) Ne kadar sürede karar verdi? 3) Ne seçti ve sonuç ne oldu?",
            "Senin işine yarayacak bir dersi tek cümleyle yaz. Örneğin: \"Önce en önemli tek bilgiye bakıyor.\"",
        ],
        "kontrol": [
            "Kişinin kararı 3 adımda yazılı.",
            "Kararın hangi bilgiyle ve ne kadar sürede verildiğini yazdın.",
            "Kendine uyarlayacağın bir dersi not ettin.",
        ],
        "ipucu": "Zor anda hızlı karar verenlerin çoğu önceden çok çalışmıştır; hikâyede hazırlık kısmına da dikkat et.",
    },
    "I3-U-1": {
        "nasil": [
            "Hızlı karar gerektiren bir rol seç: bir yarışma ekibinde yer almak, münazaraya katılmak ya da okuldaki bir etkinliğin organizasyonunda görev almak.",
            "Rehberlik servisine ya da kulüp öğretmenine yakın tarihte hangi etkinliklerde görev alabileceğini sor.",
            "Sorumluluk alabileceğin bir görev iste. Örneğin: etkinlik günü zaman akışını takip etmek, sahne arkası koordinasyonu.",
            "Görev sırasında hızlı karar verdiğin anları kısa notlarla kaydet ve etkinlikten sonra en zorlayıcı anı 2–3 cümleyle yaz.",
        ],
        "kontrol": [
            "Zaman baskısı olan bir rolde görev aldın.",
            "Görev sırasında verdiğin en az bir hızlı kararı anlatabiliyorsun.",
        ],
        "ipucu": "İlk seferde küçük bir görevle başlamak normaldir; deneyim kazandıkça daha büyük roller iste.",
    },
    "I3-U-2": {
        "nasil": [
            "{bolum} alanında yaşanmış gerçek bir kriz örneği bul; güvenilir haber sitelerinden ya da öğretmeninin önereceği bir kaynaktan yararlan.",
            "Vaka analizi yap: Yaşanmış bir olayı adım adım inceleyip ne olduğunu, hangi kararların alındığını ve sonuçlarını değerlendirmektir.",
            "Bir kâğıda üç başlık aç: \"Ne oldu?\", \"Hangi kararlar alındı?\", \"Sonuç ne oldu?\" ve her birine 2–3 cümle yaz.",
            "Son olarak \"Benim değerlendirmem\" başlığı altına kararların hangisini doğru bulduğunu, hangisini farklı yapardın, yaz.",
        ],
        "kontrol": [
            "Vakayı üç başlık altında özetleyen bir yazın var.",
            "Kendi değerlendirmeni en az 3 cümleyle yazdın.",
            "Vakadan çıkardığın bir dersi bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Tek bir habere dayanma; mümkünse olayı en az iki farklı kaynaktan oku.",
    },
    "I4-G-1": {
        "nasil": [
            "{bolum} mezunlarının çalıştığı mesleği ve bu mesleğin bağlı olduğu meslek örgütünü (oda, birlik, dernek) bul. Emin değilsen \"{bolum} meslek etiği\" diye ara.",
            "Meslek örgütünün resmî sitesinde \"etik kurallar\", \"meslek ilkeleri\" ya da \"yönetmelik\" bölümüne bak.",
            "Okuduğun kurallar arasından sana en önemli gelen 3 tanesini seç.",
            "Her kuralı kendi cümlelerinle bir satırda yaz ve yanına neden önemli olduğunu kısa bir notla ekle.",
        ],
        "kontrol": [
            "{bolum} alanına ait 3 etik kuralı kendi cümlelerinle yazdığın bir listen var.",
            "Bu kuralları hangi kaynaktan bulduğunu söyleyebiliyorsun.",
            "Kurallardan birini bir örnekle açıklayabiliyorsun.",
        ],
        "ipucu": "Resmî metin ağır gelirse bir öğretmeninden ya da o meslekten tanıdığın birinden bir kuralı açıklamasını iste.",
    },
    "I4-G-2": {
        "nasil": [
            "Gri durum, doğru olanla kolay olanın çatıştığı, cevabın hemen belli olmadığı bir durumdur. Kendine bir tane seç. Örneğin: arkadaşın kopya istiyor ya da grupta yaptığın bir hatayı fark eden yok.",
            "Durumu 3–4 cümleyle yaz.",
            "İki seçeneği yan yana yaz: \"Kolay olan\" ve \"Doğru olan\"; her birinin sana ve başkalarına etkisini bir cümleyle ekle.",
            "Ne yapacağına karar ver ve \"Ben … yapardım, çünkü …\" kalıbıyla nedenini yaz.",
        ],
        "kontrol": [
            "Bir gri durum ve iki seçeneğini yazdığın bir sayfan var.",
            "Kararını ve nedenini bir cümleyle yazdın.",
        ],
        "ipucu": "Kendini çok iyi gösteren bir cevap yerine gerçekten ne yapacağını yaz; bu çalışma sadece senin için.",
    },
    "I4-G-3": {
        "nasil": [
            "Bu alanda yaşanmış bir etik ihlal haberi bul; güvenilir haber kaynaklarını tercih et ya da öğretmeninden öneri iste.",
            "Haberi okuyup 3 soruyu cevapla: Ne oldu? Hangi kural ya da ilke çiğnendi? Kim zarar gördü?",
            "Bu vakayı tanıdığın bir arkadaşınla ya da öğretmeninle 20–30 dakika konuş. Başlangıç sorusu: \"Sen bu kişinin yerinde olsan ne yapardın?\"",
            "Konuşma sonunda kendi görüşünü ve karşındakinin farklı görüşlerini iki ayrı başlık altında not et.",
        ],
        "kontrol": [
            "Bir etik ihlal vakasını özetleyen notun var.",
            "Vakayı en az bir kişiyle tartıştın.",
            "Senin görüşünden farklı en az bir görüşü yazdın.",
        ],
        "ipucu": "Tartışmada haklı çıkmaya değil, farklı bakış açılarını anlamaya odaklan.",
    },
    "I4-G-4": {
        "nasil": [
            "Bir defterde ya da telefonda \"Sözlerim\" adlı bir liste aç ve üç sütun yap: tarih, verdiğin söz, tuttun mu?",
            "Verdiğin küçük sözleri buraya ekle. Örneğin: \"Ahmet'e notlarımı yarın getireceğim\", \"Saat 6'da evde olacağım.\"",
            "Söz tarihi geldiğinde yanına tik (tuttum) ya da çarpı (tutmadım) koy.",
            "10 söz biriktiğinde tutamadıklarına bak ve nedenini bir kelimeyle yaz: unuttum, zaman, fazla söz. Sonra tuttuğun sözleri say.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Listende en az 10 söz tarihiyle yazılı.",
            "Her sözün yanında tuttun ya da tutmadın işareti var.",
            "Söz tutmanı en çok neyin zorlaştırdığını söyleyebiliyorsun.",
        ],
        "ipucu": "Tutamayacağın sözü vermemek de söz tutmanın bir parçasıdır; \"Bakarım, sana haber vereyim\" diyebilirsin.",
    },
    "I4-G-5": {
        "nasil": [
            "Zor bir durumda doğruyu seçmiş birini seç: bir bilim insanı, sporcu, gazeteci ya da {bolum} alanından biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Hangi ikilemle karşılaştı? Neyi göze alarak hangi kararı verdi? Bundan ne öğrendi?",
            "Kişinin karşılaştığı ikilemi ve verdiği kararı 3-4 cümleyle yaz.",
            "Bu hikâyenin {bolum} ile bağlantısını yaz: Bu alanda benzer bir ikilemle nasıl karşılaşabilirsin?",
        ],
        "kontrol": [
            "Kişinin karşılaştığı ikilem ve verdiği karar yazılı.",
            "Neyi göze aldığını not ettin.",
            "Hikâyenin {bolum} ile bağlantısını en az 2 cümleyle yazdın.",
        ],
        "ipucu": "Uzun bir biyografide takılırsan önce kısa bir belgesel ya da röportajla başlamak sorun değil.",
    },
    "I4-G-6": {
        "nasil": [
            "Sessiz bir ortamda 30 dakika ayır ve bir kâğıdı ortadan ikiye böl.",
            "Sol tarafa \"Meslekte asla yapmayacağım 3 şey\" yaz. Örneğin: \"Hatamı gizlemem\", \"Başkasının emeğini kendim gibi sunmam.\"",
            "Sağ tarafa \"Meslekte her zaman yapacağım 3 şey\" yaz. Örneğin: \"Bilmediğim konuda soru sorarım.\"",
            "Her maddenin yanına neden önemli olduğunu bir cümleyle ekle ve listeyi kolayca görebileceğin bir yere koy.",
        ],
        "kontrol": [
            "3 \"asla\" ve 3 \"her zaman\" maddesinden oluşan kişisel ilke listen hazır.",
            "Her maddenin nedenini bir cümleyle açıklayabiliyorsun.",
        ],
        "ipucu": "Önceki etik adımlarında yazdığın notlar (meslek kuralları, gri durum) bu listeyi yazmana yardım edebilir.",
    },
    "I4-U-1": {
        "nasil": [
            "Yeni bir grup çalışmasının başında adil çalışma için birkaç kural önermeyi kendine görev edin.",
            "2–4 kuraldan oluşan bir öneri yaz. Örneğin: \"Görevleri herkesin iş yükü eşit olacak şekilde paylaşırız\", \"Kullandığımız her kaynağı sonda belirtiriz.\"",
            "Kaynak göstermeyi açıkla: Başkasından aldığın bilgi, görsel ya da cümlenin nereden geldiğini (kitap, site adı, yazar) çalışmanın sonuna yazmaktır.",
            "Kuralları ekiple konuş, ortak belgeye ekle ve proje boyunca bu kurallara uyulup uyulmadığını izle.",
        ],
        "kontrol": [
            "Ekibe adil çalışma ve kaynak gösterme kuralları önerdin.",
            "Ekip görevleri bu kurallara göre paylaştı.",
            "Teslim edilen çalışmada kaynakça ya da kaynak listesi var.",
        ],
        "ipucu": "Kurallara uymayan biri olursa onu suçlamadan, \"Kuralımız şuydu, nasıl çözelim?\" diye konuyu açabilirsin.",
    },
    "I4-U-2": {
        "nasil": [
            "Kurallara uyarak yaratıcı bir çözüm bulunmuş bir vaka ara; bir öğretmenine örnek sorabilir ya da {bolum} alanındaki haberlere bakabilirsin.",
            "Vakayı oku ve 3 soruyu cevapla: Hangi kural ya da ilke vardı? Sorun neydi? Kurala uyarak nasıl yaratıcı bir çözüm bulundu?",
            "Bu cevapları 1 sayfayı geçmeyecek şekilde yaz.",
            "Altına \"Benim çıkarımım\" başlığıyla ilkelerin seni nasıl yönlendirebileceğini 2–3 cümleyle ekle.",
        ],
        "kontrol": [
            "Vakanın özetini yazdığın bir sayfan var.",
            "\"Benim çıkarımım\" kısmında kendi düşünceni yazdın.",
        ],
        "ipucu": "Bulduğun vakada kurallar çiğnenmişse başka bir vaka seç; burada önemli olan kuralın içinde kalınarak bulunan çözüm.",
    },
    "I5-G-1": {
        "nasil": [
            "{bolum} hakkında merak ettiğin bir soruyu yaz. Örneğin: \"Bu bölümde en zorlanılan ders hangisi?\" ya da \"Bu alanda çalışanlar günde ne yapıyor?\"",
            "Bu konuya en yakın öğretmenini seç ve ders arası ya da ders sonu gibi uygun bir zaman bul.",
            "Kısa bir giriş yap: \"Hocam, {bolum} ile ilgileniyorum, size bir şey sorabilir miyim?\" ve sorunu sor.",
            "Cevabı hemen ardından defterine 2–3 cümleyle not et ve öğretmenine teşekkür et.",
        ],
        "kontrol": [
            "Bir öğretmenine ders dışında soru sordun.",
            "Aldığın cevabı yazdığın bir notun var.",
        ],
        "ipucu": "Öğretmen o anda müsait değilse \"Ne zaman uygun olursunuz?\" diye sormak da inisiyatif almaktır.",
    },
    "I5-G-2": {
        "nasil": [
            "Çevrende küçük bir sorun fark et ve not al. Örneğin: sınıfta ödev duyuruları karışıyor, grup mesajlarında önemli bilgiler kayboluyor.",
            "Sorunu bir cümleyle yaz ve çözmek için atabileceğin küçük bir adım düşün. Örneğin: ödev tarihlerini tahtanın köşesine yazmayı önermek.",
            "Gerekirse sınıf öğretmenine ya da ilgili kişiye fikrini kısaca anlat.",
            "Adımı at ve birkaç gün sonra durumun değişip değişmediğine bak.",
        ],
        "kontrol": [
            "Fark ettiğin bir sorunu ve attığın adımı yazdığın bir notun var.",
            "Sorunu çözmek için en az bir somut adım attın.",
        ],
        "ipucu": "Büyük bir sorunu tek başına çözmeye çalışma; küçük ve senin elinde olan bir adımla başla.",
    },
    "I5-G-3": {
        "nasil": [
            "Kimse istemeden bir işe girişmiş birini seç: bir girişimci, gönüllü, bilim insanı ya da {bolum} alanından biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: İlk adımı nasıl attı? Hangi engelle karşılaştı? Bundan ne öğrendi?",
            "Kişinin attığı ilk adımı ve karşılaştığı bir engeli 3-4 cümleyle yaz.",
            "Senin deneyebileceğin küçük bir ilk adımı tek cümleyle yaz. Örneğin: \"Kulüp danışmanına bir etkinlik fikri sunacağım.\"",
        ],
        "kontrol": [
            "Kişinin attığı ilk adım yazılı.",
            "Karşılaştığı bir engeli ve ne yaptığını yazdın.",
            "Senin deneyebileceğin bir şeyi yazdın.",
        ],
        "ipucu": "Büyük işlerin çoğu küçük bir ilk adımla başlar; hikâyede o ilk adımın ne kadar küçük olduğuna dikkat et.",
    },
    "I5-G-4": {
        "nasil": [
            "Yapmak isteyip bir türlü başlamadığın 3 şeyi alt alta yaz. Örneğin: bir kulübe katılmak, öğretmenine soru sormak, bir projeye başlamak.",
            "Her birinin yanına seni durduran şeyi yaz: çekinmek, bilgi eksiği, birinin izin vermesini beklemek, nereden başlayacağını bilmemek gibi.",
            "Her biri için atabileceğin en küçük ilk adımı yaz; 10 dakikadan kısa sürmeli. Örneğin: \"Kulüp danışmanının hangi gün okulda olduğunu öğrenmek.\"",
            "En az birinin ilk adımını at ve tarihiyle not et.",
        ],
        "kontrol": [
            "3 iş ve her birini durduran neden yazılı.",
            "Her iş için en küçük ilk adım yazılı.",
            "En az birinin ilk adımını attın ve tarihini not ettin.",
        ],
        "ipucu": "\"Çekiniyorum\" yazmak zayıflık değildir; neyin seni durdurduğunu bilmek onu aşmanın ilk adımıdır.",
    },
    "I5-G-5": {
        "nasil": [
            "{bolum} ile ilgili, küçük ve bitirilebilir bir proje fikri seç: bir blog, küçük bir araştırma, bir kulüp etkinliği ya da sosyal medya sayfası.",
            "Projenin amacını, hedef kitlesini ve ilk 3 adımını bir sayfaya yaz.",
            "Projeyi aşamalara böl. Örneğin: 1. aşama konu listesi, 2. aşama ilk yazı, 3. aşama yayın. Her aşama bitince tarihini yaz.",
            "İnternette paylaşacaksan kişisel bilgilerini (adres, okul, telefon) paylaşma ve ailene haber ver.",
            "İlk somut ürünü (ilk yazı, ilk etkinlik, ilk bulgu) ortaya çıkar ve birine göster.",
        ],
        "kontrol": [
            "Projenin amacını ve adımlarını yazdığın bir plan var.",
            "Projenin en az bir somut çıktısı ortaya çıktı (yayınlanan yazı, yapılan etkinlik vb.).",
            "Projeni bir cümleyle başkasına anlatabiliyorsun.",
        ],
        "ipucu": "Mükemmel olmasını bekleyip başlamamak sık yapılan bir hatadır; ilk versiyon basit olabilir.",
    },
    "I5-G-6": {
        "nasil": [
            "Bir \"Fırsat listesi\" aç ve {bolum} ile ilgili fırsatları topla: kurs, yarışma, seminer, okul etkinliği.",
            "Fırsatları bulmak için okul duyurularına, rehberlik servisine ve TÜBİTAK, Teknofest gibi bilinen kurumların resmî sitelerine bak.",
            "Her fırsat için ad, son tarih ve nasıl katılacağını tek satırda yaz.",
            "Listeden sana en uygun olanları seç ve ailenin bilgisiyle değerlendir: başvur, katıl ya da kaydol; yaptığın her başvuru ya da katılımın tarihini yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Listende en az 5 fırsat var.",
            "En az 2'sine başvurdun ya da katıldın ve tarihleri yazılı.",
        ],
        "ipucu": "Fırsatı bulduğun gün son tarihini takvimine yaz; çoğu fırsat son tarih kaçtığı için kaçar.",
    },
    "I5-U-1": {
        "nasil": [
            "{bolum} ile ilgili kapsamlı bir fırsat seç: yaz okulu, bilim olimpiyatı, TÜBİTAK lise proje yarışmaları ya da Teknofest yarışmaları gibi.",
            "Başvuru şartlarını ve son tarihi resmî siteden oku ve bir kontrol listesi yap: istenen belgeler, danışman öğretmen gerekiyor mu, ekip mi bireysel mi?",
            "Danışman öğretmen gerekiyorsa bir öğretmenine fikrini anlatıp destek iste; okulun rehberlik servisi de yol gösterebilir.",
            "Başvurunun son tarihini öğren ve belgeleri ondan önce tamamla; ailenin bilgisiyle başvuruyu gönder ve onay belgesini sakla.",
        ],
        "kontrol": [
            "Kapsamlı bir fırsata başvurunu tamamladın.",
            "Başvuru onayı ya da kayıt numarası gibi bir kanıtın var.",
        ],
        "ipucu": "Proje yarışmaları genelde uzun süreçtir; başvuru tarihlerini birkaç ay önceden öğrenmek işini kolaylaştırır.",
    },
    "I5-U-2": {
        "nasil": [
            "Arkadaşlarınla yapabileceğin bir proje ya da etkinlik fikri seç. Örneğin: okulda bir bilgi yarışması, bir kitap kulübü, bir yardım kampanyası.",
            "Fikri bir sayfada yaz: amaç, ne zaman, kaç kişi, hangi görevler var.",
            "En az 3 arkadaşına fikrini anlat ve her birine bir görev öner; okul içi bir etkinlikse bir öğretmeninden onay al.",
            "Düzenli aralıklarla kısa buluşmalar yaparak ilerlemeyi takip et.",
            "Etkinliği ya da projeyi gerçekleştir ve sonunda ekiple neyin iyi gittiğini konuş.",
        ],
        "kontrol": [
            "En az 3 kişiyle birlikte çalıştığın bir proje ya da etkinlik gerçekleşti.",
            "Ekipteki herkesin bir görevi vardı.",
            "Projenin sonucunu gösteren bir kanıt var (fotoğraf, duyuru, ürün).",
        ],
        "ipucu": "İnsanları harekete geçirmenin en kolay yolu onlara net ve küçük bir görev vermektir.",
    },
    "I6-G-1": {
        "nasil": [
            "Bir eleştiri aldığında hemen cevap vermek yerine şu cümleyi söyle: \"Teşekkürler, biraz düşüneyim.\"",
            "Eleştiriyi dinlerken sözü kesme; karşındakinin ne söylediğini anlamaya çalış.",
            "Gün içinde 5 dakika ayır ve eleştiriyi yaz; altına \"Bunda haklı olduğu bir kısım var mı?\" sorusunun cevabını ekle.",
            "Uygun bir anda istersen karşındakine dönüp ne düşündüğünü sakin bir şekilde söyle.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. İşe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az bir eleştiriye savunmaya geçmeden yanıt verdin.",
            "Aldığın eleştiriyi ve üzerine düşündüklerini yazdığın bir notun var.",
        ],
        "ipucu": "Her eleştiri doğru olmak zorunda değil; amaç hemen kabul etmek değil, düşünmeden savunmaya geçmemek.",
    },
    "I6-G-2": {
        "nasil": [
            "Son sınav kâğıdını ya da deneme sınavını önüne al ve yanlış ya da boş bıraktığın soruları işaretle.",
            "Bir kâğıda 3 sütun aç: Bilgi eksiği (konuyu bilmiyordum), Dikkat (biliyordum ama yanlış okudum/hesapladım), Süre (yetiştiremedim).",
            "Her hatayı bir sütuna yaz; hangi sorunun hangi türe girdiğini kısaca not et.",
            "Her sütundaki hata sayısını say ve en çok hatanın olduğu sütunu yuvarlak içine al.",
            "Altına bu hata türünü azaltmak için yapabileceğin bir şeyi yaz. Örneğin: dikkat hatası için soruyu okurken altını çizmek.",
        ],
        "kontrol": [
            "Hatalarını 3 türe göre ayırdığın bir tablon var.",
            "En sık yaptığın hata türünü söyleyebiliyorsun.",
            "Bu hata türü için bir çözüm önerisi yazdın.",
        ],
        "ipucu": "Tüm hataları \"dikkatsizlik\" diye geçmek kolaydır; soruyu tekrar çöz ve gerçekten bilip bilmediğini kontrol et.",
    },
    "I6-G-3": {
        "nasil": [
            "Yakın zamanda teslim ettiğin bir ödevi ya da sunumu seç.",
            "Geri bildirim isteme cümlesini hazırla: Genel \"Nasıldı?\" yerine özel bir soru sor. Örneğin: \"Hocam, bu ödevde neyi daha iyi yapabilirim?\"",
            "Öğretmeninin müsait olduğu bir zamanda 5–10 dakika ayırmasını rica et ve sorunu sor.",
            "Söylediklerini not al, teşekkür et ve itiraz etmeden önce dinle.",
            "Önerilerden birini seç ve bir sonraki çalışmanda uygula.",
        ],
        "kontrol": [
            "Bir öğretmeninden özel geri bildirim aldın ve notunu yazdın.",
            "Önerilerden en az birini bir sonraki çalışmanda uyguladın.",
        ],
        "ipucu": "Geri bildirimi teslimden hemen sonra istemek, konu öğretmenin aklında tazeyken daha verimli olur.",
    },
    "I6-G-4": {
        "nasil": [
            "Geri bildirim aldığın bir çalışmayı (ödev, sunum, yazı) ve aldığın notları önüne koy.",
            "Geri bildirimleri madde madde liste yap ve her birinin yanına nasıl düzelteceğini bir cümleyle yaz.",
            "Düzeltmeleri maddelere ayır; her oturumda 1–2 maddeyi ele al.",
            "Çalışmanın yeni hâlini hazırla ve listedeki maddelerin üstünü çiz.",
            "İstersen yeni hâli aynı kişiye göster ve \"Şimdi nasıl olmuş?\" diye sor.",
        ],
        "kontrol": [
            "Geri bildirimleri ve düzeltme planını gösteren bir listen var.",
            "Çalışmanın geliştirilmiş hâlini tamamladın.",
            "Eski ve yeni hâl arasındaki farkları 2–3 maddeyle söyleyebiliyorsun.",
        ],
        "ipucu": "Tüm geri bildirimleri aynı anda uygulamaya çalışma; önce en önemli olandan başla.",
    },
    "I6-G-5": {
        "nasil": [
            "Hayatında başarısızlık, ret ya da sert eleştiriyle karşılaşmış birinin otobiyografisini ya da biyografisini seç; okul ya da halk kütüphanesinin biyografi rafına bak, kütüphane görevlisinden öneri iste.",
            "Kitabı bölümlere ayırarak oku; her bölümden sonra aklında kalan bir cümleyi tarihle yaz.",
            "Okurken 3 soruyu not et: Hangi eleştiriyle ya da retle karşılaştı? İlk tepkisi ne oldu? Sonra bundan ne öğrendi?",
            "Kitap bitince bu üç cevabı 4-5 cümleyle bir sayfada topla.",
            "Kendine uyarlayacağın bir davranışı tek cümleyle yaz. Örneğin: \"Eleştiri aldığımda hemen cevap vermek yerine bir gün düşüneceğim.\"",
        ],
        "kontrol": [
            "Kitabı bitirdin.",
            "Kişinin karşılaştığı bir eleştiri, ilk tepkisi ve sonra çıkardığı ders yazılı.",
            "Kendine uyarlayacağın bir davranışı yazdın.",
        ],
        "ipucu": "Otobiyografide kişi kendi hikâyesini anlatır; mümkünse onun hakkında başka birinin yazdığı bir kaynağa da göz at.",
    },
    "I6-G-6": {
        "nasil": [
            "Farklı alanlardan 3 kişi seç: örneğin bir bilim insanı, bir sporcu ve bir sanatçı. Kütüphanedeki biyografilere, TRT Belgesel gibi kanallara ya da güvenilir röportajlara bak.",
            "Her biri için 3 soruyu cevapla: Hangi başarısızlığı yaşadı? Kim ya da ne onu eleştirdi? Nasıl toparlandı?",
            "Üç hikâyeyi yan yana koy ve ortak olan bir şeyi bul.",
            "Kendi hayatından benzer bir anı ekle: Ne oldu, nasıl hissettin, nasıl toparlandın ya da şimdi olsa nasıl toparlanırdın?",
        ],
        "kontrol": [
            "3 kişinin yenilgi ve toparlanma hikâyesi yazılı.",
            "Üç hikâyedeki ortak bir noktayı buldun.",
            "Kendi hayatından bir örnek ekledin.",
        ],
        "ipucu": "Gelişim zihniyeti, yeteneklerin çabayla gelişebileceği inancıdır; \"Yapamıyorum\" yerine \"Henüz yapamıyorum\" demek bu bakışın kısa hâlidir. İstersen Carol Dweck'in \"Mindset\" kitabını ek kaynak olarak okuyabilirsin.",
    },
    "I6-G-7": {
        "nasil": [
            "{bolum} alanında tanınmış 2 kişi seç; bölümün ya da meslek kuruluşlarının tanıttığı isimlere, güvenilir röportajlara, belgesellere ya da biyografilere bak.",
            "Her biri için kariyerinde yaşadığı bir ret, hata ya da eleştiri anını bul.",
            "İkisi için aynı 3 soruyu cevapla: Ne yaşadı? Nasıl tepki verdi? Nasıl toparlandı?",
            "Cevapları iki sütunlu bir tabloda yan yana yaz ve benzerlik ile farkı birer cümleyle not et.",
            "Bu meslekte zorluklarla karşılaşırsan işine yarayacak bir davranışı tek cümleyle yaz.",
        ],
        "kontrol": [
            "İki kişinin yaşadığı zorluk ve aldığı eleştiri yazılı.",
            "İkisinin nasıl toparlandığını karşılaştırmalı olarak yazdın.",
            "Kendine uyarlayacağın bir davranışı not ettin.",
        ],
        "ipucu": "Başarılı insanların zor anlarını bilmek, kendi hatalarını \"bu iş bana göre değil\" diye yorumlamanı önler.",
    },
    "I6-U-1": {
        "nasil": [
            "Önündeki önemli çalışmaları listele: proje, sunum, yazılı ödev gibi.",
            "Her çalışmayı bitirdiğinde bir kişiye (öğretmen, arkadaş, aile) kısa bir soru sor: \"Bu çalışmada en iyi olan ve geliştirilebilecek bir şey ne?\"",
            "Cevapları bir tabloda tut: tarih, çalışma, kimden, geri bildirim.",
            "Bir sonraki çalışmaya başlamadan önce tabloya bak ve önceki geri bildirimden birini uygula. Bu, geri bildirim döngüsüdür: iste, uygula, tekrar iste.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "En az 3 çalışman için geri bildirim aldığın bir tablon var.",
            "Bir geri bildirimi sonraki çalışmanda uyguladığını gösterebiliyorsun.",
        ],
        "ipucu": "Kısa ve özel bir soru sormak, \"Nasıl olmuş?\" demekten çok daha işe yarar cevap getirir.",
    },
    "I6-U-2": {
        "nasil": [
            "Mentor, deneyimini paylaşarak sana yol gösteren kişidir. {bolum} alanında olabilecek adayları listele: üst sınıf öğrencisi, okulunun mezunu, bir öğretmenin.",
            "Mezunlara ya da tanımadığın kişilere ulaşmak için ailenin ya da öğretmeninin bilgisi dahilinde hareket et; okulun rehberlik servisinden de yardım isteyebilirsin.",
            "Kısa bir mesaj yaz: Kendini tanıt, {bolum} ile ilgilendiğini söyle ve 20–30 dakikalık bir görüşme rica et.",
            "Görüşmeye 3–5 soru hazırla. Örneğin: \"Bu bölümü seçerken nelere dikkat ettiniz?\" Görüşmeyi okulda ya da çevrim içi gibi güvenli bir ortamda yap.",
            "Görüşmeden sonra notlarını yaz, teşekkür et ve ikinci görüşme için birlikte bir tarih belirleyin.",
        ],
        "kontrol": [
            "{bolum} alanında seninle görüşmeyi kabul eden bir mentorun var.",
            "Bu kişiyle en az 2 kez görüştün.",
            "Her görüşmeden aldığın notların var.",
        ],
        "ipucu": "Herkes cevap vermeyebilir; birkaç kişiye yazmak ve olumsuz cevabı kişisel algılamamak önemli.",
    },
    "I7-G-1": {
        "nasil": [
            "{bolum} alanında faaliyet gösteren, adını bildiğin bir şirket seç; aklına gelmiyorsa \"{bolum} alanındaki şirketler\" diye ara.",
            "Şirketin resmî sitesinde \"Hakkımızda\" ve \"Ürünler/Hizmetler\" bölümlerine bak.",
            "Bir kâğıda 3 başlık aç: Ne satıyor? Kime satıyor? Rakipleri kimler? Her başlığa 1–2 madde yaz.",
            "İş modelini 3 cümleyle özetle; iş modeli, şirketin nasıl para kazandığının kısa anlatımıdır. Örneğin: \"X şirketi … üretip … ye satarak kazanıyor.\"",
        ],
        "kontrol": [
            "Şirketin ürünlerini, müşterilerini ve rakiplerini yazdığın bir sayfan var.",
            "Şirketin iş modelini 3 cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Çok büyük ve karmaşık şirketlerde zorlanırsan daha küçük ve tek ürünlü bir şirketle başla.",
    },
    "I7-G-2": {
        "nasil": [
            "Güvenilir bir haber kaynağının ekonomi ya da iş dünyası bölümünden bir haber seç.",
            "Haberi oku ve bir cümleyle özetle: Ne oldu, kimi etkiliyor?",
            "Kendine sor: \"Bu haber {bolum} ya da o alanda çalışanlar için ne anlama gelir?\" Cevabını 2–3 cümleyle defterine yaz ve tarihi ekle.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. İşe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 3 tarihli haber notun var.",
            "Her notta haberin özeti ve bölümünle ilişkisi 2–3 cümleyle yazılı.",
        ],
        "ipucu": "Haberde anlamadığın bir terim olursa önce onu ara; bu, iş dünyası dilini öğrenmenin en kolay yolu.",
    },
    "I7-G-3": {
        "nasil": [
            "Küçük ve gerçekçi bir iş fikri seç. Örneğin: okul kantininde satılabilecek bir ürün ya da özel ders hizmeti.",
            "Bir sayfayı 4 bölüme ayır: Müşteri (kim alacak?), Maliyet (bir ürünü yapmak kaça mal olur?), Fiyat (kaça satarsın?), Rakip (benzerini kim yapıyor?).",
            "Maliyet ve fiyat için gerçek fiyatları araştır (market, internet) ve basit bir hesap yap: Fiyat – maliyet = birim başına kâr.",
            "Rakiplerine göre seni farklı kılan bir özelliği yaz.",
            "Planı tek sayfaya sığacak şekilde temize çek ve bir arkadaşına ya da öğretmenine göster.",
        ],
        "kontrol": [
            "Müşteri, maliyet, fiyat ve rakip bölümleri dolu tek sayfalık bir iş planın var.",
            "Birim başına ne kadar kâr edeceğini hesapladın.",
            "Fikrinin rakiplerden farkını bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Maliyeti hesaplarken ambalaj, ulaşım gibi küçük giderleri unutmak sık yapılan bir hatadır.",
    },
    "I7-G-4": {
        "nasil": [
            "Katılabileceğin bir işletme simülasyonu, strateji oyunu ya da girişimcilik yarışması ara; rehberlik servisine ve okul kulüplerine sor.",
            "Seçeneğin kurallarını ve süresini oku; ekip gerekiyorsa arkadaşlarından ekip kur.",
            "Ailenin bilgisiyle kayıt ol ve takvimindeki önemli tarihleri işaretle.",
            "Simülasyon ya da yarışma sırasında verdiğin önemli kararları kısa notlarla kaydet.",
            "Tamamladığında neyi iyi yaptığını ve neyi farklı yapacağını 2–3 cümleyle yaz.",
        ],
        "kontrol": [
            "Bir simülasyon ya da yarışmayı sonuna kadar tamamladın.",
            "Süreçte verdiğin kararları ve değerlendirmeni gösteren notların var.",
        ],
        "ipucu": "Kazanmak değil, sonuna kadar katılmak hedef; bir strateji bilgisayar oyunu da başlangıç olabilir.",
    },
    "I7-G-5": {
        "nasil": [
            "Temel işletme ya da yönetim üzerine ücretsiz, kısa bir çevrim içi kurs seç; örneğin BTK Akademi'deki kurslara bakabilirsin.",
            "Kursu oturumlara böl; her oturumdan sonra tarihli kısa bir not al.",
            "Notlarına 2–3 madde ekle ve öğrendiğin bir kavramı kendi cümlelerinle yaz.",
            "Kursu tamamla; varsa bitirme sınavına gir ve tamamlama belgesini sakla.",
        ],
        "kontrol": [
            "Kursu tamamladın ve varsa belgen elinde.",
            "Kurstan aldığın notların var.",
            "Kursta öğrendiğin bir kavramı bir arkadaşına anlatabiliyorsun.",
        ],
        "ipucu": "Kursa kayıt olmak için ailenin onayı gerekebilir; kişisel bilgilerini yalnızca resmî sitede paylaş.",
    },
    "I7-G-6": {
        "nasil": [
            "Bu alanda yönetici olarak çalışan birini düşün: tanıdığın bir aile büyüğü, bir öğretmenin tanıdığı ya da okulunun mezunu.",
            "Tanımadığın biriyle iletişim kuracaksan ailenin ya da öğretmeninin bilgisi dahilinde hareket et; okulun rehberlik servisinden de yardım isteyebilirsin.",
            "Görüşme için 4–5 soru hazırla. Örneğin: \"Önemli bir kararı nasıl veriyorsunuz?\", \"Bir ekibi yönetirken nelere dikkat ediyorsunuz?\"",
            "30 dakikalık görüşmeyi yüz yüze ya da çevrim içi yap; izin alarak not tut.",
            "Görüşmeden sonra notlarından 3 strateji fikri çıkar ve her birini bir cümleyle yaz.",
        ],
        "kontrol": [
            "Bir yöneticiyle görüşme yaptın.",
            "Görüşmeden çıkardığın 3 strateji fikrini yazdığın bir listen var.",
        ],
        "ipucu": "Görüşmenin sonunda teşekkür mesajı göndermek ilişkiyi devam ettirmeni kolaylaştırır.",
    },
    "I7-G-7": {
        "nasil": [
            "Okulda, ailende ya da bir kulüpte alınmış bir karar seç. Örneğin: bir etkinliğin bütçesi, bir kermesin fiyatları, bir gezi yerinin seçimi.",
            "Kararın amacını tek cümleyle yaz: Bu kararla ne elde edilmek istendi?",
            "En az 2 seçeneği yaz ve her birinin maliyetini (para, zaman, emek) ve risklerini not et; bilmediğin bilgileri kararı verenlere kibarca sorabilirsin.",
            "Sen olsan hangi seçeneği tercih ederdin? Gerekçeni 2-3 cümleyle yaz.",
        ],
        "kontrol": [
            "Kararın amacı ve en az 2 seçenek yazılı.",
            "Her seçeneğin maliyeti ve riskleri not edilmiş.",
            "Kendi tercihini gerekçesiyle yazdın.",
        ],
        "ipucu": "Strateji, hedefe ulaşmak için seçenekleri karşılaştırmaktır; küçük kararlarda pratik yapmak büyük kararları kolaylaştırır.",
    },
    "I7-U-1": {
        "nasil": [
            "{bolum} alanının bulunduğu sektörü belirle (ör. sağlık, yazılım, enerji, eğitim).",
            "Güvenilir kaynaklardan bu sektörün geleceğiyle ilgili 2–3 haber ya da rapor oku.",
            "SWOT analizinin bir kısmını kullan: Fırsatlar (sektörde büyüyen alanlar) ve Riskler (tehditler, zorluklar) başlıklarını aç. Her başlığa 2–3 madde yaz.",
            "Altına \"Bu benim için ne anlama geliyor?\" başlığıyla 2–3 cümle ekle.",
            "Kullandığın kaynakların adlarını sayfanın sonuna yaz.",
        ],
        "kontrol": [
            "Fırsatlar ve riskler başlıklarını içeren kısa bir sektör analizi yazdın.",
            "Analizinde kullandığın kaynakları belirttin.",
            "Sektörün geleceğiyle ilgili bir sonucunu bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Tek bir kaynağa dayanmak yanıltıcı olabilir; en az iki farklı kaynaktan bilgi topla.",
    },
    "I7-U-2": {
        "nasil": [
            "Lise öğrencilerine açık bir girişimcilik ya da iş fikri yarışması bul; rehberlik servisine, öğretmenlerine ve okul duyurularına sor.",
            "Yarışmanın şartlarını, ekip sayısını ve son başvuru tarihini yaz.",
            "İlgili 2–4 arkadaşınla ekip kur ve herkese bir rol ver: araştırma, sunum, hesaplama gibi.",
            "Fikrinizi müşteri, maliyet, fiyat ve rakip başlıklarından oluşan tek sayfalık bir planla hazırlayın.",
            "Ailelerinizin bilgisiyle başvuruyu son tarihten önce gönderin ve onay belgesini saklayın.",
        ],
        "kontrol": [
            "Bir ekip kurdun ve görevleri paylaştınız.",
            "Yarışmaya başvurunuzu yaptınız ve bunun bir kanıtı var.",
        ],
        "ipucu": "Yarışmanın başvuru tarihi yakınsa ekibi küçük tutmak karar almayı hızlandırır.",
    },
    "A1-G-1": {
        "nasil": [
            "Son 2–3 matematik sınav kâğıdını ya da deneme sonuçlarını önüne koy; yoksa okul sisteminden veya öğretmeninden sonuçlarını iste.",
            "Deneme analizi yap: Yanlış ve boş bıraktığın her soruyu tek tek incele ve sorunun hangi konudan olduğunu (ör. fonksiyonlar, olasılık) bir kâğıda yaz.",
            "Her konunun yanına kaç soru kaçırdığını çentik atarak say. Örneğin: \"Problemler: |||| \", \"Üslü sayılar: ||\".",
            "En çok çentik alan 3 konuyu seç ve yanlarına neden zorlandığını tek kelimeyle yaz: \"bilmiyorum\", \"karıştırıyorum\" ya da \"dikkatsizlik\".",
            "Bu 3 konuyu öncelik sırasıyla defterinin ilk sayfasına ya da telefonundaki bir nota yaz.",
        ],
        "kontrol": [
            "Elinde konu konu yanlış sayılarını gösteren bir liste var.",
            "Öncelikli 3 konunu sırasıyla yazılı olarak gösterebiliyorsun.",
            "Her konu için neden zorlandığını bir kelimeyle söyleyebiliyorsun.",
        ],
        "ipucu": "Sınav kâğıdın yoksa son çözdüğün test kitabındaki yanlışlarını da kullanabilirsin.",
    },
    "A1-G-2": {
        "nasil": [
            "Her gün için sabit bir 20 dakika seç (ör. akşam yemeğinden sonra) ve telefonunda zamanlayıcı kur.",
            "Ders kitabından ya da bir soru bankasından bir konu seç; ilk 5–10 dakika kolay, sonra orta, en son zor sorulara geç. Takıldığın soruyu 3–4 dakikadan fazla zorlama; yanına yıldız koyup geç, süre bitince çözümüne bak.",
            "Hata defteri tut: Yanlış yaptığın her sorunun kısa bir kopyasını, doğru çözümünü ve hatanın nedenini ayrı bir deftere yaz.",
            "Bir kâğıda tarih ve soru sayısı sütunları aç; her çalıştığın gün tarihi ve kaç soru çözdüğünü yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 7 günün tarihi ve o gün çözdüğün soru sayısı yazılı.",
            "Hata defterinde bu çalışmalardan en az birkaç soru ve çözümü var.",
            "Her gün kolaydan zora doğru soru çözdüğünü örneklerle gösterebiliyorsun.",
        ],
        "ipucu": "Bir günü kaçırırsan bırakma; ertesi gün kaldığın yerden devam et ve seriyi yeniden başlat.",
    },
    "A1-G-3": {
        "nasil": [
            "Eksik konu tespitinde seçtiğin 3 konuyu sıraya koy ve başladığın tarihleri yaz.",
            "Her konuya önce bir 20 soruluk test çöz ve doğru sayını not et; bu senin başlangıç puanın.",
            "Konuyu Khan Academy Türkçe videolarından, ders kitabından ya da öğretmeninin önerdiği kaynaktan çalış; her konu için birkaç oturum ayır ve her oturumdan sonra tarihli kısa bir not al.",
            "Konuyu bitirince aynı zorlukta yeni bir 20 soruluk test çöz ve doğru sayını başlangıç puanının yanına yaz.",
            "Yanlışlarını hata defterine ekle, sonra sıradaki konuya geç.",
        ],
        "kontrol": [
            "3 konunun her biri için \"önce\" ve \"sonra\" test sonuçların yazılı.",
            "En az 2 konuda \"sonra\" puanın \"önce\" puanından yüksek.",
            "Her konuda hâlâ zorlandığın alt başlığı söyleyebiliyorsun.",
        ],
        "ipucu": "Puanın artmadıysa o konunun bir alt başlığına odaklanıp kısa bir test daha çöz.",
    },
    "A1-G-4": {
        "nasil": [
            "Bir soru seç ve verini nereden alacağına karar ver: kendi hayatından toplayacağın bir veri (uyku, çalışma süresi) ya da TÜİK, YÖK Atlas gibi açık bir kaynak. Örneğin: \"Son 5 yılda {bolum} kontenjanları nasıl değişti?\"",
            "Kendi verini topluyorsan her ölçümü tarihiyle yaz; açık veri kullanıyorsan verinin kaynağını ve yılını not et.",
            "Veriyi bir tabloya aktar (kareli kâğıt, Google E-Tablolar ya da Excel); satır ve sütunlar net etiketli olsun.",
            "Verine uygun bir grafik çiz: zaman içindeki değişim için çizgi, karşılaştırma için çubuk grafik. Eksenleri adlandır.",
            "Grafiğin altına 3 cümle yaz: Ne görüyorsun, en dikkat çekici nokta ne, bu veri neyi söylemiyor?",
        ],
        "kontrol": [
            "Verinin ve kaynağının yazılı olduğu bir tablon var.",
            "Eksenleri ve başlığı etiketli bir grafiğin var.",
            "Grafiğin söylediğini anlatan 3 cümlelik yorumun hazır.",
        ],
        "ipucu": "\"Bu veri neyi söylemiyor?\" sorusu iyi bir veri okurunu sıradan bir okurdan ayırır.",
    },
    "A1-G-5": {
        "nasil": [
            "İlgilendiğin bir üniversitenin web sitesinde {bolum} programını bul ve \"ders planı\", \"müfredat\" ya da \"Bologna bilgi paketi\" bölümünü aç; hangi üniversitelerde bu programın olduğunu YÖK Atlas'tan bulabilirsin.",
            "1. ve 2. sınıf derslerine bak; içinde matematik, istatistik, fizik, programlama gibi sayısal derslerin adlarını bir kâğıda listele.",
            "Listeden bir dersi seç ve ders içeriğine (ders tanıtım formu) bak; ilk haftalarda işlenen giriş konusunu yaz.",
            "Bu giriş konusunu internette kısa bir video ya da yazıyla araştır ve lisede öğrendiğin hangi konuya dayandığını not et.",
        ],
        "kontrol": [
            "{bolum} programındaki sayısal derslerin listesi elinde.",
            "Seçtiğin bir dersin giriş konusunu bir iki cümleyle anlatabiliyorsun.",
            "Bu konunun lisedeki hangi konuyla bağlantılı olduğunu söyleyebiliyorsun.",
        ],
        "ipucu": "Ders planını bulamazsan farklı bir üniversitenin aynı bölümüne bak; dersler genelde benzerdir.",
    },
    "A1-G-6": {
        "nasil": [
            "Ücretsiz bir başlangıç kursu seç; örneğin BTK Akademi'deki Python kursları ya da Khan Academy'deki programlama dersleri.",
            "Kendine düzenli 30–45 dakikalık çalışma zamanları seç; her oturumu tarihiyle işaretle.",
            "Her dersi izledikten sonra örnek kodu kendin yeniden yaz ve çalıştır; sadece izlemek yetmez.",
            "Öğrendiğin her yeni kavramı (değişken, döngü, koşul gibi) defterine bir cümle ve kısa bir kod örneğiyle not et.",
            "İlk modülleri bitirince küçük bir program yaz. Örneğin: girilen sayıların ortalamasını hesaplayan bir program.",
        ],
        "kontrol": [
            "Kursun ilk modüllerini tamamladığını gösteren ilerleme ekranın ya da notların var.",
            "Kendi yazdığın ve çalışan en az bir küçük programın var.",
            "Değişken ve döngünün ne olduğunu bir arkadaşına anlatabiliyorsun.",
        ],
        "ipucu": "Hata aldığında hata mesajını dikkatle oku; çoğu zaman hangi satırda sorun olduğunu söyler.",
    },
    "A1-U-1": {
        "nasil": [
            "Matematik öğretmenine ya da rehberlik servisine okulunun katılabileceği yarışmaları sor; TÜBİTAK Bilim Olimpiyatları ve Teknofest gibi bilinen organizasyonları da araştır.",
            "Bulduğun 2–3 yarışma için başvuru tarihi, sınav tarihi ve konu kapsamını bir tabloya yaz.",
            "Sana en uygun ve tarihi yetişebilecek bir yarışmayı seç.",
            "Hazırlık planı yap: Sınav tarihine kadar kalan süreyi bölümlere ayır ve her bölüme bir konu ya da geçmiş yıl soru seti ata.",
            "Geçmiş yıllardan bir soru seti çözerek başla ve seviyeni not et.",
        ],
        "kontrol": [
            "Seçtiğin yarışmanın adı ve tarihleri yazılı.",
            "Bölümlere ayrılmış bir hazırlık planın var.",
            "Plandaki ilk bölümün çalışmasını yaptın.",
        ],
        "ipucu": "Olimpiyat soruları zor gelebilir; ilk denemede az soru çözmen normal.",
    },
    "A1-U-2": {
        "nasil": [
            "Python'da veri analizi için ücretsiz, kısa bir başlangıç kursu seç (ör. BTK Akademi; İngilizcen yeterliyse ailenle birlikte hesap açarak Kaggle Learn'in ücretsiz dersleri) ve her oturumdan sonra tarihli kısa bir not al.",
            "Kursta temel araçları öğren: Tabloyu okuma, sütun seçme, ortalama alma ve basit grafik çizme.",
            "{bolum} ile ilgili hazır ve açık bir veri seti bul. Örneğin: hava durumu, nüfus ya da spor istatistikleri; öğretmeninden öneri isteyebilirsin.",
            "Veri setine 2–3 soru sor. Örneğin: \"Hangi yıl en yüksek değer var?\" ve kodla cevapla.",
            "Bulduğun sonuçları 1 grafik ve 4–5 cümlelik bir özetle bir sayfada topla.",
        ],
        "kontrol": [
            "Kursun temel bölümlerini bitirdin.",
            "Bir veri setini Python ile açıp en az 2 soruyu cevapladın.",
            "Analizini gösteren bir grafik ve kısa bir özet yazın var.",
        ],
        "ipucu": "Çok büyük veri setleriyle başlama; birkaç yüz satırlık bir veri yeterli.",
    },
    "A2-G-1": {
        "nasil": [
            "İlgini çeken bir türde kitap seç (roman, bilim kurgu, polisiye, biyografi); okul ya da halk kütüphanesinden ödünç alabilirsin.",
            "Her gün için sabit bir okuma zamanı belirle (ör. yatmadan önce) ve telefonunu sessize al.",
            "15 sayfayı okuyunca kaldığın sayfaya ayraç koy ve bir kâğıda tarihi ve sayfa aralığını yaz.",
            "Okuduğun bölümden aklında kalan bir cümleyi ya da olayı kısaca not et.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Okuma kâğıdında en az 7 günün tarihi ve okuduğun sayfa sayısı yazılı.",
            "Toplamda en az 100 sayfa okudun.",
            "Okuduğun bölümleri birine birkaç cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Kitap seni sıkıyorsa 50 sayfa sonra değiştirmekte sakınca yok.",
    },
    "A2-G-2": {
        "nasil": [
            "Okulda ya da haberlerde konuşulan güncel bir konu seç. Örneğin: \"Okullarda telefon yasağı olmalı mı?\"",
            "İddia yaz: Konu hakkındaki görüşünü tek ve net bir cümleyle söyle. Örneğin: \"Ders saatlerinde telefon kullanımı sınırlanmalı.\"",
            "Gerekçe yaz: Neden böyle düşündüğünü 1–2 cümleyle açıkla.",
            "Örnek ekle: Gerekçeni destekleyen somut bir durum ya da deneyim yaz.",
            "Hepsini 5–7 cümlelik tek bir paragrafta birleştir ve son cümlede iddiayı kısaca tekrar et.",
        ],
        "kontrol": [
            "Elinde 5–7 cümlelik tek bir paragraf var.",
            "Paragrafta iddia, gerekçe ve örneğin hangi cümleler olduğunu gösterebiliyorsun.",
            "Birisi \"Neden böyle düşünüyorsun?\" diye sorduğunda paragrafındaki gerekçeyle cevap verebiliyorsun.",
        ],
        "ipucu": "Gerekçe ile örneği karıştırma: Gerekçe \"neden\", örnek \"nerede görüyoruz\" sorusuna cevaptır.",
    },
    "A2-G-3": {
        "nasil": [
            "Yazacağın konulardan bir liste yap: güncel olaylar, okuduğun bir kitap ya da merak ettiğin bir soru olabilir.",
            "Her yazı için yaklaşık 300 kelimelik (bir A4 sayfasının yarısı ile tamamı arası) bir metin yaz: giriş, iki gelişme paragrafı, sonuç. Her yazının tarihini ekle.",
            "Yazılarından en az birini Türk Dili ve Edebiyatı öğretmenine ya da güvendiğin başka bir öğretmene ver ve kısa bir geri bildirim iste.",
            "Aldığın geri bildirimle o yazıyı düzelt ve bir sonraki yazında en az bir öneriyi uygula.",
            "Tüm yazılarını tek bir dosya ya da klasörde sırayla sakla.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Klasöründe en az 4 tarihli yazı var.",
            "En az bir yazıyı aldığın geri bildirimle düzelttin.",
            "Geri bildirime göre neyi değiştirdiğini bir örnekle gösterebiliyorsun.",
        ],
        "ipucu": "Öğretmenin her yazı için vakit bulamazsa iki yazıyı birlikte götürebilirsin.",
    },
    "A2-G-4": {
        "nasil": [
            "Okulunda münazara ya da kitap kulübü olup olmadığını rehberlik servisine ya da edebiyat öğretmenine sor.",
            "Kulübe kaydol ve ilk toplantının tarihini takvimine yaz.",
            "Münazara: İki grubun bir konuda karşıt görüşleri savunduğu kurallı tartışmadır; kitap kulübünde ise herkes aynı kitabı okuyup konuşur. Toplantıdan önce konuyu ya da kitabı hazırla.",
            "Her oturumda en az bir kez söz al; bir görüş belirt, bir soru sor ya da bir örnek ver.",
            "Oturumdan sonra neler konuşulduğunu ve kendi katkını 2–3 cümleyle not et.",
        ],
        "kontrol": [
            "En az 2 oturuma katıldın.",
            "Her oturumda en az bir kez söz aldığını notlarından gösterebiliyorsun.",
            "Oturumlarda tartışılan konuları kısaca anlatabiliyorsun.",
        ],
        "ipucu": "Okulunda kulüp yoksa birkaç arkadaşınla küçük bir kitap grubu kurabilirsin.",
    },
    "A2-G-5": {
        "nasil": [
            "Öğretmenine ya da bir üniversite öğrencisine {bolum} alanına giriş için okunabilecek bir kitap ya da makale sor; kütüphanede \"giriş\" kelimesiyle arama da yapabilirsin.",
            "Metni bölümlere ayır; her bölümün sonunda ana fikri bir cümleyle not et.",
            "Bilmediğin terimleri ayrı bir listede topla ve anlamlarını araştır.",
            "Özet çıkar: Bölüm notlarını birleştirerek metnin ana fikirlerini kendi cümlelerinle 1 sayfayı geçmeyecek şekilde yaz.",
            "Özetin sonuna metinden öğrendiğin en ilginç şeyi ve aklına takılan bir soruyu ekle.",
        ],
        "kontrol": [
            "{bolum} alanından bir metni bitirdin.",
            "Kendi cümlelerinle yazılmış en fazla 1 sayfalık bir özetin var.",
            "Metindeki en önemli fikri birine bir iki cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Özet yazarken metinden cümle kopyalamak yerine kitabı kapatıp hatırladığını yaz.",
    },
    "A2-G-6": {
        "nasil": [
            "Küçük bir defter ayır ya da telefonunda bir not aç; adını \"Kelime Defterim\" koy.",
            "Okurken bilmediğin her kelimenin altını çiz ya da not al; okumayı bitirince sözlükten (ör. TDK sözlüğü) anlamına bak.",
            "Deftere kelimeyi, anlamını ve onunla kurduğun kendi cümleni yaz.",
            "Her 10 yeni kelimede bir 10–15 dakika ayırıp son kelimeleri tekrar et; anlamı kapatıp hatırlamaya çalış.",
            "Hatırladığın kelimelerin yanına tik koy, hatırlamadıklarını bir sonraki tekrarda yeniden çalış.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Defterinde en az 50 kelime, anlamı ve örnek cümlesiyle yazılı.",
            "Rastgele seçilen 10 kelimeden çoğunun anlamını söyleyebiliyorsun.",
            "Yeni kelimelerden birkaçını yazılarında ya da konuşmalarında kullandın.",
        ],
        "ipucu": "Az ama sık tekrar etmek, bir anda çok kelime ezberlemekten daha kalıcıdır.",
    },
    "A2-G-7": {
        "nasil": [
            "İyi yazan ya da konuşan birini seç: bir yazar, gazeteci ya da {bolum} alanında açık anlatımıyla tanınan biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Yazmaya ya da konuşmaya nasıl başladı? Nasıl geliştirdi? Zorlandığında ne yaptı?",
            "Bu kişinin kullandığı 2 yöntemi yaz. Örneğin: \"Her gün biraz yazıyor\", \"Yazdığını sesli okuyup düzeltiyor\".",
            "Bir yöntemi bir sonraki yazında dene ve tarihli kısa bir not ekle: Ne değişti?",
        ],
        "kontrol": [
            "Bu kişinin kullandığı 2 yöntem yazılı.",
            "Bir yöntemi kendi yazında denedin ve notun var.",
        ],
        "ipucu": "İyi yazarların çoğu ilk taslağı beğenmez; asıl iş, yeniden okuyup düzeltmektir.",
    },
    "A2-U-1": {
        "nasil": [
            "Edebiyat öğretmenine ve rehberlik servisine lise öğrencilerine açık deneme, hikâye ya da kompozisyon yarışmalarını sor; okul panosunu da kontrol et.",
            "Bulduğun 2–3 yarışma için konu, kelime sınırı ve son başvuru tarihini bir tabloya yaz.",
            "Yarışmanın resmî şartnamesini (kurallarını anlatan belgeyi) oku: Yaş sınırı, kimlerin katılabileceği ve nasıl gönderileceği yazılı olmalı.",
            "İlgi alanına ve tarihine en uygun olanı seç ve yazmaya başlayacağın tarihi takvimine not et.",
        ],
        "kontrol": [
            "Seçtiğin yarışmanın adı, konusu ve son tarihi yazılı.",
            "Yarışmanın şartnamesini okudun ve şartları sağladığını biliyorsun.",
            "Yazmaya ne zaman başlayacağın belli.",
        ],
        "ipucu": "Yarışmanın gerçekten bilinen bir kurum tarafından düzenlendiğini öğretmeninle kontrol et.",
    },
    "A2-U-2": {
        "nasil": [
            "{bolum} ile ilgili seni heyecanlandıran bir konu seç. Örneğin: alandaki yeni bir gelişme ya da bir mesleğin günlük hayatı.",
            "Nerede yayımlayacağına karar ver: okul dergisi, okul panosu ya da ailenin bilgisi dahilinde açtığın bir blog.",
            "400–700 kelimelik bir taslak yaz; dikkat çekici bir başlık, net bir giriş ve kaynak gösterdiğin bilgiler olsun.",
            "Taslağı bir öğretmene okut, önerilerine göre düzelt ve yazım hatalarını kontrol et.",
            "Yazını teslim et ya da yayımla; okul dergisinde ise editör öğretmenle çıkış tarihini öğren.",
        ],
        "kontrol": [
            "Yazın okul dergisinde, panoda ya da blogda yayımlandı.",
            "Yazıda kullandığın bilgilerin kaynakları belli.",
            "Yazının ana fikrini birine bir iki cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "İnternette yayımlarken adres, okul adı gibi kişisel bilgilerini paylaşma.",
    },
    "A3-G-1": {
        "nasil": [
            "Rahatça gözlem yapabileceğin tanıdık bir ortam seç: sınıf, okul bahçesi, okul kütüphanesi ya da aile ortamı. Gözlem, olanları yorum katmadan dikkatle izleyip not almaktır.",
            "3 farklı gözlem oturumu yap, her biri 10–15 dakika olsun; kimsenin adını yazma, kimseyi fotoğraflama.",
            "Ne gördüğünü olduğu gibi yaz. Örneğin: \"Teneffüste çoğu öğrenci aynı köşede toplanıyor.\"",
            "Notlarında birden fazla kez tekrar eden davranışları işaretle; örüntü, sık tekrar eden bir davranış biçimidir.",
            "En ilginç 3 örüntüyü seç ve her birinin yanına \"Bunun nedeni ne olabilir?\" sorusuna bir tahmin yaz.",
        ],
        "kontrol": [
            "3 farklı gözlem oturumundan notun var.",
            "Notlarında tekrar eden 3 örüntü örnekleriyle yazılı.",
            "Notlarında isim ya da fotoğraf yok.",
        ],
        "ipucu": "İnsanları rahatsız edecek kadar yakından izleme; uzaktan ve doğal davran.",
    },
    "A3-G-2": {
        "nasil": [
            "Psikolojiye giriş niteliğinde kısa bir video serisi ya da makale seç; Khan Academy'de ya da üniversitelerin açık ders sayfalarında bulabilirsin.",
            "30–45 dakika ayır ve izlerken ya da okurken yeni öğrendiğin kavramları not et. Örneğin: \"onay yanlılığı\", \"iç motivasyon\".",
            "En ilgini çeken bir kavramı seç ve onu günlük hayattan bir örnekle açıklayan 2–3 cümle yaz.",
            "Bu kavramı bir arkadaşına ya da aile bireyine anlat ve ona örnek vermesini iste.",
        ],
        "kontrol": [
            "Öğrendiğin kavramların listesi elinde.",
            "Bir kavramı birine anlattın ve o da bir örnek verebildi.",
            "Bu kavramı kendi örneğinle açıklayabiliyorsun.",
        ],
        "ipucu": "Kaynağın güvenilir olmasına dikkat et; bilimsel kaynak gösteren içerikleri tercih et.",
    },
    "A3-G-3": {
        "nasil": [
            "İyi bildiğin bir derste zorlanan bir arkadaşını belirle ve ona yardım etmeyi teklif et.",
            "Arkadaşınla düzenli buluşma zamanları belirleyin (30–45 dakika yeterli); okul kütüphanesi ya da sınıf uygun bir yer olabilir.",
            "Her buluşmada önce arkadaşına neyi anlamadığını sor, sonra konuyu adım adım ve örnekle anlat; cevabı vermek yerine soruyu birlikte çözün.",
            "Buluşmadan sonra tarihi, çalıştığınız konuyu ve neyin işe yaradığını bir deftere yaz.",
        ],
        "kontrol": [
            "Defterinde en az 4 destek oturumunun tarihi ve konusu yazılı.",
            "Arkadaşın en az bir konuyu daha iyi anladığını söylüyor.",
            "Anlatırken hangi yöntemin işe yaradığını söyleyebiliyorsun.",
        ],
        "ipucu": "Arkadaşın anlamadığında aynı cümleyi tekrar etmek yerine farklı bir örnek dene.",
    },
    "A3-G-4": {
        "nasil": [
            "Tanıdığın bir öğretmen, okul psikolojik danışmanı ya da ailenin tanıdığı bir uzman belirle; ailenin ya da öğretmeninin bilgisi dahilinde görüşme iste.",
            "Görüşme öncesi 5 soru hazırla. Örneğin: \"İşinizin en zor insan ilişkisi yönü ne?\", \"Bu işe en çok hangi beceri lazım?\"",
            "Görüşme için 30 dakika ayır ve tanıdık bir ortamda (okul, rehberlik odası ya da çevrim içi) buluş.",
            "Konuşurken kısa notlar al ya da izin alarak ses kaydı yap.",
            "Görüşmeden sonra öğrendiğin en önemli 3 şeyi yaz ve kişiye kısa bir teşekkür mesajı gönder.",
        ],
        "kontrol": [
            "Görüşmeden çıkardığın 3 not yazılı.",
            "Bu kişinin işinde insanlarla nasıl çalıştığını birkaç cümleyle anlatabiliyorsun.",
            "Hazırladığın sorular ve aldığın cevaplar bir sayfada duruyor.",
        ],
        "ipucu": "Tanıdık yoksa okulunun rehberlik servisinden görüşebileceğin biri için yardım isteyebilirsin.",
    },
    "A3-G-5": {
        "nasil": [
            "Çocuklara ya da gençlere yönelik etkinlikleri araştır: okulunun sosyal sorumluluk kulübü, alt sınıflara okuma saati, belediyenin ya da yerel bir derneğin oyun ve okuma etkinlikleri.",
            "Ailenle konuş; etkinliğin yaş şartını ve gereken izinleri birlikte öğrenin. 18 yaşından küçüksen veli izni gerekebilir.",
            "Katılacağın etkinliği seç ve varsa önceden yapılan tanıtım ya da eğitime katıl.",
            "Etkinlikte sana verilen görevi yap ve çocuklarla çalışırken sorumlu yetişkinin yönlendirmelerine uy.",
            "Her etkinlikten sonra tarihi yaz ve ne yaptığını, nasıl hissettiğini 3–4 cümleyle not et.",
        ],
        "kontrol": [
            "Ailenin bilgisiyle en az 2 etkinlikte gönüllü oldun.",
            "Her etkinlik için tarih ve kısa bir not yazılı.",
            "Bu deneyimin sana neler hissettirdiğini anlatabiliyorsun.",
        ],
        "ipucu": "Yer seçerken öğretmenine ya da rehberlik servisine danışmak güvenli bir başlangıçtır.",
    },
    "A3-G-6": {
        "nasil": [
            "Akran desteği, görüşme ve gönüllülük gibi insanlarla çalıştığın deneyimlerinin notlarını önüne koy.",
            "Her deneyim için 1 ile 5 arasında puan ver: Sonrasında ne kadar enerjik (5) ya da yorgun (1) hissettin?",
            "Kendine şu soruları sor ve cevaplarını yaz: \"En çok neyden keyif aldım?\", \"Beni en çok ne yordu?\", \"Bunu her gün yapmak ister miydim?\"",
            "Sonuç olarak 4–5 cümlelik bir değerlendirme yaz ve bunun {bolum} seçimin için ne anlama geldiğini ekle.",
        ],
        "kontrol": [
            "Her deneyim için verdiğin enerji puanı yazılı.",
            "4–5 cümlelik değerlendirme yazın var.",
            "\"İnsanlarla yoğun çalışmak bana enerji veriyor mu?\" sorusuna bir cümleyle cevap verebiliyorsun.",
        ],
        "ipucu": "Yorulmak her zaman uygun olmadığın anlamına gelmez; yorgunluğun nedenini de düşün.",
    },
    "A3-U-1": {
        "nasil": [
            "\"{bolum} alt alanları\" ya da \"{bolum} uzmanlık alanları\" diye arama yap; üniversite sayfalarına ve meslek tanıtım yazılarına bak.",
            "Bulduğun alt alanları bir listeye yaz.",
            "Her alt alanın yanına günün ne kadarının insanlarla yüz yüze geçtiğini tahmin et: az, orta ya da çok.",
            "\"Çok\" işaretlediğin en az 2 alt alanı seç ve her biri için o alanda çalışan birinin insanlarla ne yaptığını bir cümleyle yaz.",
        ],
        "kontrol": [
            "{bolum} alt alanlarını içeren bir listen var.",
            "İnsanla en çok temas eden en az 2 alt alan işaretli.",
            "Bu alt alanlarda insanlarla nasıl çalışıldığını bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Emin olamadığın alt alanları bir öğretmene ya da o alanda okuyan birine sorabilirsin.",
    },
    "A3-U-2": {
        "nasil": [
            "Okulunda alt sınıflara yönelik akran mentorluğu, akran rehberliği ya da \"abla-ağabey\" programı olup olmadığını rehberlik servisine sor.",
            "Mentorluk, deneyimli birinin daha yeni birine düzenli olarak yol göstermesidir; programın sorumluluklarını ve ne kadar zaman gerektirdiğini öğren.",
            "Başvuru formunu doldur ya da rehberlik öğretmenine katılmak istediğini ilet.",
            "Programa katıldıktan sonra her görüşmede ne konuştuğunu ve hangi konuda yardım ettiğini kısaca not et.",
            "Okulunda böyle bir program yoksa rehberlik servisiyle küçük bir program başlatmayı öner.",
        ],
        "kontrol": [
            "Bir mentorluk ya da rehberlik programına kaydın var.",
            "Program kapsamında en az birkaç görüşme yaptın ve notların var.",
            "Mentorluk yaptığın öğrenciye hangi konuda yardım ettiğini anlatabiliyorsun.",
        ],
        "ipucu": "Çözemediğin ciddi bir sorunla karşılaşırsan bunu mutlaka rehberlik öğretmenine ilet.",
    },
    "A4-G-1": {
        "nasil": [
            "Bir eskiz defteri ya da birkaç boş kâğıt ve bir kurşun kalem hazırla. Eskiz, bir şeyin ana hatlarını hızlıca çizdiğin taslak çizimdir.",
            "Her gün çevrende bir nesne seç (bardak, ayakkabı, saksı) ve zamanlayıcıyı 10 dakikaya kur.",
            "Önce nesnenin genel şeklini daire, kare gibi basit şekillerle çiz, sonra ayrıntıları ve gölgeleri ekle.",
            "Mükemmel olmasını bekleme; süre bitince çizimi bırak ve köşesine tarihi yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Defterinde tarihli 7 eskiz var.",
            "Her eskizde nesnenin ana şekli tanınabiliyor.",
            "İlk ve son eskizini karşılaştırıp fark ettiğin bir gelişmeyi söyleyebiliyorsun.",
        ],
        "ipucu": "Silgiyi az kullan; hatalı çizgileri bırakıp üzerine doğrusunu çizmek daha hızlı öğretir.",
    },
    "A4-G-2": {
        "nasil": [
            "Uzamsal düşünme, nesneleri zihninde döndürme ve parçaların nasıl birleştiğini hayal etme becerisidir; bunu çalıştıracak bir etkinlik seç.",
            "Seçeneklerden birini dene: Bir origami modeli (kâğıt katlama), 3D yapboz, tangram ya da Rubik küpü; ücretsiz origami çizimlerini internette bulabilirsin.",
            "Her oturumda 15–20 dakika ayır; kolay bir modelle başla ve tamamladıkça zorluğu artır.",
            "Bitirdiğin her bulmacanın adını ve sana zor gelen adımı kısaca not et; istersen fotoğrafını çek.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "En az 3 bulmaca ya da origami modeli tamamladın.",
            "Tamamladıklarının listesi ya da fotoğrafları elinde.",
            "Hangi adımda zorlandığını ve nasıl çözdüğünü anlatabiliyorsun.",
        ],
        "ipucu": "Origamide bir adımı anlamazsan kâğıdı çizimdeki gibi çevirip tekrar bak.",
    },
    "A4-G-3": {
        "nasil": [
            "Amacına göre ücretsiz bir araç seç: afiş ve sunum için Canva, ekran ve uygulama tasarımı için Figma, 3D modelleme için Tinkercad.",
            "Hesap açmak gerekiyorsa ailenin bilgisi dahilinde aç; aracın kendi başlangıç eğitimlerini ya da kısa video dersleri izle.",
            "Birkaç kısa pratik oturumu yap; her birinde bir özelliği öğren (yazı ekleme, renk, hizalama, katman gibi).",
            "Basit bir tasarım yap. Örneğin: okul etkinliği için bir afiş, bir uygulama giriş ekranı ya da bir anahtarlık modeli.",
            "Tasarımını kaydet ve bir arkadaşından ya da öğretmeninden görüş al.",
        ],
        "kontrol": [
            "Seçtiğin araçla yaptığın tamamlanmış bir tasarımın var.",
            "Aracın en az 3 temel özelliğini kullanabiliyorsun.",
            "Tasarımını dosya ya da ekran görüntüsü olarak gösterebiliyorsun.",
        ],
        "ipucu": "Hazır şablonlarla başlamak normal; sonra kendi değişikliklerini ekle.",
    },
    "A4-G-4": {
        "nasil": [
            "{bolum} ile ilgili maketini yapacağın bir yapı ya da nesne seç. Örneğin: bir köprü, bir oda planı, bir hücre ya da bir makine parçası.",
            "Maket, bir şeyin küçültülmüş üç boyutlu modelidir; önce kâğıda farklı yönlerden görünüşünü ve yaklaşık ölçülerini gösteren bir eskiz çiz.",
            "Ucuz ve güvenli malzemeler kullan: karton, mukavva, kürdan, oyun hamuru, yapıştırıcı; maket bıçağı kullanacaksan bir yetişkinden yardım iste.",
            "Maketi parça parça yap; her oturumda bir parçayı bitir: önce taban ve ana gövde, sonra ayrıntılar.",
            "Bitirince fotoğrafını çek ve maketin neyi gösterdiğini anlatan kısa bir açıklama yaz.",
        ],
        "kontrol": [
            "Bitmiş maketin ve fotoğrafı var.",
            "Maketin başlangıç eskizi elinde.",
            "Maketin {bolum} ile bağlantısını iki cümleyle açıklayabiliyorsun.",
        ],
        "ipucu": "Çok büyük ya da ayrıntılı başlama; küçük ve bitirilebilir bir model seç.",
    },
    "A4-G-5": {
        "nasil": [
            "Bir mimar, tasarımcı ya da {bolum} alanında çalışan birini seç; TRT Belgesel gibi bir kanalda bir belgesel ya da güvenilir bir röportaj bul.",
            "İzlerken ya da okurken bir fikrin eskizden ürüne nasıl taşındığını adım adım not et: fikir, taslak, deneme, düzeltme, son hâl.",
            "Bu kişinin zorlandığı ya da fikrini değiştirdiği bir anı ayrıca yaz.",
            "Sürecin bir adımını seç ve kendi küçük tasarımında dene. Örneğin: aynı fikir için 3 farklı taslak çizmek.",
            "Denediğin adımın sana ne kattığını 2-3 cümleyle tarihiyle yaz.",
        ],
        "kontrol": [
            "Tasarım sürecinin adımları sırasıyla yazılı.",
            "Bir adımı kendi tasarımında denedin.",
            "Bu denemenin sana ne kattığını yazdın.",
        ],
        "ipucu": "Tasarımcıların çoğu ilk fikirde durmaz; birden fazla taslak çizmek en iyi fikri bulmayı kolaylaştırır.",
    },
    "A4-G-6": {
        "nasil": [
            "Portfolyo, yaptığın çalışmaları düzenli olarak bir araya topladığın dosyadır; bir klasör ya da bilgisayarda bir dosya aç.",
            "Eskizlerini, dijital tasarımlarını, maketlerinin fotoğraflarını ve atölye çalışmalarını bu klasörde topla.",
            "Her çalışmanın yanına tarih, kullandığın malzeme ya da araç ve bir cümlelik açıklama ekle.",
            "Her yeni çalışmanı bitirdiğinde tarihiyle klasöre ekle.",
        ],
        "kontrol": [
            "Klasöründe en az 5 çalışma var.",
            "Her çalışmanın tarihi ve kısa açıklaması yazılı.",
            "Çalışmalarını birine sırayla gösterip anlatabiliyorsun.",
        ],
        "ipucu": "Beğenmediğin çalışmaları da sakla; gelişimini görmek için işe yarar.",
    },
    "A4-U-1": {
        "nasil": [
            "Daha önce yaptığın tasarım çalışmalarını (çizim, maket, dijital tasarım) bir klasörde topla, en iyi 5 tanesini seç; farklı teknikleri gösterenleri tercih et.",
            "Her çalışmanın net, iyi ışıklı bir fotoğrafını ya da ekran görüntüsünü al.",
            "Her biri için 2–3 cümlelik bir açıklama yaz: Ne yaptın, neden yaptın, hangi araç ya da malzemeyi kullandın?",
            "Çalışmaları tek bir dosyada (sunum, PDF ya da düzenli bir klasör) sırala; başa adını ve kısa bir tanıtım cümlesi ekle.",
        ],
        "kontrol": [
            "5 çalışmadan oluşan tek bir portfolyo dosyan var.",
            "Her çalışmanın açıklaması yazılı.",
            "Portfolyonu bir öğretmene ya da arkadaşına baştan sona sunabiliyorsun.",
        ],
        "ipucu": "En güçlü çalışmanı ilk sıraya koy; ilk izlenim önemlidir.",
    },
    "A4-U-2": {
        "nasil": [
            "Görsel sanatlar öğretmenine ve rehberlik servisine lise öğrencilerine açık tasarım, afiş ya da maket yarışmalarını sor; Teknofest gibi bilinen organizasyonların kategorilerini de incele.",
            "{bolum} ile en uyumlu yarışmayı seç ve şartnamesini (kurallarını anlatan belgeyi) dikkatle oku: konu, boyut, teslim biçimi, son tarih.",
            "Takvime geriye doğru plan yaz: fikir, eskiz, üretim ve teslim için ayrı tarihler belirle.",
            "Çalışmanı hazırla, gerekirse öğretmeninden görüş al ve başvuruyu ailenin ya da öğretmeninin bilgisi dahilinde yap.",
        ],
        "kontrol": [
            "Yarışmaya başvurunu tamamladın; onay mesajı ya da teslim belgen var.",
            "Çalışman şartnamedeki kurallara uygun.",
            "Başvurduğun çalışmayı ve fikrini birkaç cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Son güne bırakma; teslimden en az birkaç gün önce bitirmeyi hedefle.",
    },
    "A5-G-1": {
        "nasil": [
            "Doğa, biyoloji ya da kimya alanında çalışmış bir bilim insanı seç.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Ne üzerinde çalıştı? Nasıl çalışıyordu (gözlem, deney, saha çalışması)? Hangi zorlukla karşılaştı?",
            "Seni şaşırtan 3 bilgiyi kendi cümlenle yaz.",
            "Bu kişinin çalışma biçiminden kendine uyarlayacağın bir davranışı tek cümleyle yaz. Örneğin: \"Gözlemlerimi her seferinde tarihiyle not edeceğim.\"",
        ],
        "kontrol": [
            "Seni şaşırtan 3 bilgi yazılı.",
            "Bu kişinin nasıl çalıştığını kendi cümlelerinle anlattın.",
            "Kendine uyarlayacağın bir davranışı yazdın.",
        ],
        "ipucu": "Belgeselde ilginç bir yerde videoyu durdurup not almak, sonradan hatırlamanı kolaylaştırır.",
    },
    "A5-G-2": {
        "nasil": [
            "Güvenli bir deney seç. Örneğin: ıslak pamukta fasulye çimlendirmek ya da kırmızı lahana suyuyla limon, sirke ve karbonatlı suyun rengini karşılaştırmak (pH, bir maddenin asitlik ya da bazlık derecesidir).",
            "Deneyi ailenin gözetiminde yap ve yalnızca mutfakta bulunan zararsız malzemeler kullan; ocak ya da sıcak su gerekiyorsa o kısmı bir yetişkin yapsın.",
            "Deney günlüğü aç: Tarih, kullandığın malzemeler, yaptıkların ve gözlemlerin için bir sayfa ayır.",
            "7 gün boyunca her gün aynı saatte gözlem yap; bitkinin boyunu ölç ya da renk değişimini yaz, istersen fotoğrafla.",
            "Gözlemler bitince ne beklediğini ve ne olduğunu karşılaştıran 3–4 cümlelik bir sonuç yaz.",
        ],
        "kontrol": [
            "Tarihli gözlemlerin olduğu bir deney günlüğün var.",
            "Günlüğünde kullandığın malzemeler ve adımlar yazılı.",
            "Deneyin sonucunu ve beklentinle farkını açıklayabiliyorsun.",
        ],
        "ipucu": "Kullandığın malzemeleri ağzına alma ve deneyden sonra ellerini yıka.",
    },
    "A5-G-3": {
        "nasil": [
            "Fen öğretmeninle ders sonrası kısa bir görüşme ayarla ve laboratuvar çalışmalarına daha fazla katılmak istediğini söyle.",
            "Yapabileceklerini öner: deney malzemesini hazırlamak, toplamak, deney sırasında öğretmene yardım etmek ya da fen kulübüne katılmak.",
            "Laboratuvarda her zaman öğretmen gözetiminde çalış; güvenlik kurallarına uy, gözlük ve önlük kullan.",
            "Katıldığın her çalışmadan sonra kısa bir deney raporu yaz: amaç, kullanılan malzemeler, yapılanlar, gözlem ve sonuç başlıklarıyla birer iki cümle.",
        ],
        "kontrol": [
            "En az 2 laboratuvar çalışmasına katıldın.",
            "Her çalışma için kısa bir deney raporun var.",
            "Laboratuvar güvenlik kurallarından en az 3 tanesini sayabiliyorsun.",
        ],
        "ipucu": "Öğretmeninin vakti yoksa okul fen kulübünü sor; laboratuvara oradan da girebilirsin.",
    },
    "A5-G-4": {
        "nasil": [
            "Yakınında gidebileceğin bir yer seç: botanik bahçesi, doğa tarihi ya da bilim müzesi, bilim merkezi ya da doğa yürüyüşü; okul gezilerini de takip et.",
            "Ailenle ya da okul grubuyla birlikte git ve açılış saatlerini önceden kontrol et.",
            "Gitmeden önce 3 soru yaz. Örneğin: \"Bu bitki neden bu iklimde yaşıyor?\"",
            "Gezide not al ya da izin verilen yerlerde fotoğraf çek; sorularının cevaplarını aramaya çalış.",
            "Döndüğün gün yarım sayfalık bir gezi notu yaz: ne gördün, ne öğrendin, neyi merak ettin?",
        ],
        "kontrol": [
            "Geziye katıldın.",
            "Yarım sayfalık gezi notun yazılı.",
            "Gezide öğrendiğin bir bilgiyi birine anlatabiliyorsun.",
        ],
        "ipucu": "Doğa yürüyüşüne giderken mutlaka bir yetişkinle git ve işaretli parkurlardan ayrılma.",
    },
    "A5-G-5": {
        "nasil": [
            "Fen öğretmeninden danışman olmasını iste; TÜBİTAK 2204 Lise Öğrencileri Araştırma Projeleri gibi yarışmalar danışman öğretmenle yürütülür.",
            "Bir araştırma sorusu belirle ve hipotez yaz: Hipotez, sorunun cevabı hakkındaki test edebileceğin tahmindir. Örneğin: \"Işık süresi artarsa fasulye daha hızlı büyür.\"",
            "Öğretmeninle deney planı yap: neyi değiştireceksin, neyi ölçeceksin, neyi sabit tutacaksın; yalnızca güvenli yöntemler ve öğretmen gözetimi.",
            "Verilerini düzenli olarak tabloya yaz, grafiğe dök ve her ölçümden sonra kısa, tarihli not tut.",
            "Proje raporu yaz: amaç, yöntem, bulgular (tablo ve grafik), sonuç ve kaynaklar başlıklarıyla öğretmenine kontrol ettir.",
        ],
        "kontrol": [
            "Başlıkları tamamlanmış bir proje raporun var.",
            "Raporunda verilerin tablo ve grafikle gösterilmiş.",
            "Hipotezinin doğrulanıp doğrulanmadığını bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Hipotezin tutmazsa proje başarısız sayılmaz; neden tutmadığını açıklaman da bir bulgudur.",
    },
    "A5-G-6": {
        "nasil": [
            "Üniversitelerin lise öğrencilerine yönelik ücretsiz ya da burslu yaz bilim okullarını, kamplarını ve TÜBİTAK destekli bilim okulu programlarını araştır; rehberlik servisine ve fen öğretmenine de sor.",
            "Bulduğun 2–3 program için tarih, yer, konu, yaş şartı ve son başvuru tarihini bir tabloya yaz.",
            "İlgine ve ailenin uygun bulduğu tarih ve yere göre bir program seç.",
            "Başvuru formunu ailenle birlikte doldur; motivasyon yazısı istenirse neden katılmak istediğini anlatan kısa bir paragraf yaz ve öğretmenine okut.",
            "Başvurunu gönder ve onay mesajını sakla.",
        ],
        "kontrol": [
            "En az bir yaz bilim okuluna başvurdun.",
            "Başvuru onay mesajın ya da e-postan elinde.",
            "Programın tarihini ve içeriğini söyleyebiliyorsun.",
        ],
        "ipucu": "Başvuruların çoğu bahar aylarında kapanır; tarihleri erkenden kontrol et.",
    },
    "A5-U-1": {
        "nasil": [
            "{bolum} ile ilgili seni meraklandıran 5 soru yaz. Örneğin: \"Okul bahçesindeki toprağın nemi bitkilerin boyunu etkiliyor mu?\"",
            "Her sorunun yanına şunları işaretle: Okulda ya da evde güvenle test edebilir miyim? Malzemesi kolay bulunur mu? Birkaç ayda bitebilir mi?",
            "Üç soruya da \"evet\" diyebildiğin soruyu seç.",
            "Seçtiğin soruyu tek, net bir cümleye dönüştür ve ne ölçeceğini yaz.",
        ],
        "kontrol": [
            "Bir araştırma sorun yazılı.",
            "Sorunun ne ölçeceğini ve nasıl test edileceğini söyleyebiliyorsun.",
            "Sorunun {bolum} ile bağlantısını bir cümleyle açıklayabiliyorsun.",
        ],
        "ipucu": "\"Neden?\" ile başlayan geniş sorular yerine ölçülebilir \"… etkiler mi?\" soruları seç.",
    },
    "A5-U-2": {
        "nasil": [
            "Seçtiğin araştırma sorusunu fen öğretmenine götür ve danışman olmasını iste; TÜBİTAK 2204 gibi yarışmaların takvimine birlikte bakın.",
            "Yarışmanın şartnamesini (kurallarını anlatan belgeyi) okuyun ve son başvuru tarihini takvime yazın.",
            "Proje planı hazırla: araştırma sorusu, hipotez, yöntem, gerekli malzemeler ve aşamalara bölünmüş bir takvim. Deneyleri yalnızca öğretmen gözetiminde ve güvenli yöntemlerle yap.",
            "Deneylerini yap, verilerini tabloya yaz ve öğretmeninle düzenli olarak gözden geçir.",
            "Başvuru formunu ve proje raporunu öğretmeninle birlikte hazırla ve süresi içinde gönder.",
        ],
        "kontrol": [
            "Proje başvurun gönderildi ve onayın var.",
            "Proje planın ve verilerin yazılı.",
            "Projenin amacını ve yöntemini bir dakikada anlatabiliyorsun.",
        ],
        "ipucu": "Başvuru tarihleri genellikle erken kapanır; projeye erkenden başla.",
    },
    "A6-G-1": {
        "nasil": [
            "Bir sağlık sorunun varsa başlamadan önce ailene ve doktoruna danış.",
            "Her gün için 20 dakikalık bir zaman seç; yürüyüş, ip atlama, bisiklet ya da evde hafif egzersiz (esneme, squat, şınav) yapabilirsin.",
            "Yavaş başla: İlk 5 dakika ısın, son 5 dakika yavaşlayıp esneme yap; ağrı ya da baş dönmesi olursa dur. Rahat ayakkabı giy, yanında su bulundur ve yürüyüşü güvenli, aydınlık yerlerde yap.",
            "Bir kâğıda 7 kutu çiz; her gün ne yaptığını ve kaç dakika sürdüğünü kutuya yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "7 kutunun hepsinde etkinlik ve süre yazılı.",
            "Her gün en az 20 dakika hareket ettin.",
            "7 günün sonunda kendini nasıl hissettiğini bir cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Hava kötüyse evde müzik açıp hareket etmek de sayılır.",
    },
    "A6-G-2": {
        "nasil": [
            "\"{bolum} sahada bir gün\" ya da \"{bolum} meslek tanıtımı\" diye arama yap; meslek tanıtım videolarını ya da üniversitelerin tanıtım içeriklerini tercih et.",
            "10–20 dakikalık bir video seç ve izlerken bir kâğıdı ikiye böl: solda \"fiziksel işler\", sağda \"masa başı işler\".",
            "Videoda gördüğün işleri ilgili sütuna yaz. Örneğin: \"Gün boyu ayakta\", \"Arazide ölçüm\", \"Rapor yazma\".",
            "Sonunda bu işin fiziksel yönünün sana uygun olup olmadığını 2–3 cümleyle yaz.",
        ],
        "kontrol": [
            "Fiziksel ve masa başı işleri ayıran bir not sayfan var.",
            "Saha işinin en az 3 fiziksel yönünü sayabiliyorsun.",
            "Bu işin sana uygunluğu hakkında kısa bir yorumun yazılı.",
        ],
        "ipucu": "",
    },
    "A6-G-3": {
        "nasil": [
            "Okulundaki takımlar ve spor kulüpleri için beden eğitimi öğretmenine sor; ilçendeki gençlik merkezlerinin ya da belediyenin spor kurslarına da bak.",
            "İlgini çeken bir dal seç ve kayıt şartlarını öğren; bazı kulüpler sağlık raporu ya da veli izni isteyebilir.",
            "Bir sağlık sorunun varsa başlamadan önce doktoruna danış; ilk haftalarda kendini zorlama, antrenörün temposuna uy.",
            "Antrenman günlerini takvimine yaz ve her antrenmandan sonra katıldığını işaretle.",
        ],
        "kontrol": [
            "Bir spor dalına ya da okul takımına kayıtlısın.",
            "Takviminde düzenli antrenmanlara katıldığını gösteren işaretler var.",
            "Bu sporda öğrendiğin bir tekniği ya da kuralı anlatabiliyorsun.",
        ],
        "ipucu": "İlk dalı sevmezsen bir süre denedikten sonra başka bir dalı denemek de olur.",
    },
    "A6-G-4": {
        "nasil": [
            "Okulunun, belediyenin ya da bilinen bir gönüllülük kuruluşunun ağaç dikme, çevre temizliği gibi etkinliklerini araştır; öğretmenine ve rehberlik servisine sor.",
            "Etkinliğe ailenin ya da öğretmeninin bilgisi dahilinde, tercihen okul grubuyla ya da bir yetişkinle katıl.",
            "Hava durumuna uygun giysi, rahat ayakkabı, eldiven ve su al; ağır yükleri tek başına kaldırma.",
            "Etkinlik bittikten sonra ne yaptığını, nasıl hissettiğini ve bedenini nasıl kullandığını 3–4 cümleyle yaz.",
        ],
        "kontrol": [
            "Etkinliğe katıldın.",
            "Etkinlik hakkında kısa bir notun yazılı.",
            "Bu tür fiziksel çalışmaktan hoşlanıp hoşlanmadığını söyleyebiliyorsun.",
        ],
        "ipucu": "",
    },
    "A6-G-5": {
        "nasil": [
            "Sağlık durumunu bilen bir doktora ya da beden eğitimi öğretmenine danışarak gerçekçi bir hedef seç. Örneğin: \"5 km'yi durmadan yürümek ya da koşmak.\"",
            "Başlangıç noktanı ölç: Bugün kaç dakika ya da kaç km rahatça yürüyebiliyor ya da koşabiliyorsun? Bunu tarihiyle bir deftere yaz.",
            "Düzenli çalış ve her birkaç antrenmanda bir mesafeyi ya da süreyi yalnızca biraz artır; yavaş ilerlemek sakatlanmayı önler.",
            "Her antrenmanda tarihi, mesafeyi ve süreyi defterine yaz.",
            "Ağrı, nefes darlığı ya da baş dönmesi olursa dur ve ailenle birlikte doktora danış.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Defterinde tarihli antrenman kayıtların var.",
            "Hedefine ulaştın ve ulaştığın tarihi not ettin.",
            "İlk ve son ölçümünü karşılaştırıp gelişimini söyleyebiliyorsun.",
        ],
        "ipucu": "Hasta ya da çok yorgun olduğun günlerde dinlenmek de planın bir parçasıdır.",
    },
    "A6-G-6": {
        "nasil": [
            "Saha videosu, spor ve gönüllülük deneyimlerinden aldığın notları önüne koy.",
            "Bir kâğıdı ikiye böl: \"Sahada çalışmak bana uyuyor çünkü…\" ve \"Masa başı çalışmak bana uyuyor çünkü…\" başlıklarının altına maddeler yaz.",
            "{bolum} içinde masa başında geçen alt alanları da araştır ve listeye ekle.",
            "Sonuçta hangi çalışma biçiminin sana daha uygun olduğunu 4–5 cümlelik bir değerlendirmeyle yaz.",
        ],
        "kontrol": [
            "İki sütunlu karşılaştırma sayfan var.",
            "4–5 cümlelik değerlendirme yazın var.",
            "{bolum} içinde sana uygun bir saha ya da masa başı alt alanı söyleyebiliyorsun.",
        ],
        "ipucu": "",
    },
    "A6-U-1": {
        "nasil": [
            "\"{bolum} alt alanları\" ve \"{bolum} saha çalışması\" diye arama yap; üniversite tanıtım sayfalarına ve meslek tanıtım yazılarına bak.",
            "Bulduğun alt alanları bir listeye yaz.",
            "Her alt alanın yanına çalışma ortamını yaz: arazi, şantiye, hastane, spor alanı, ofis gibi.",
            "Sahada geçen ya da hareket gerektiren en az 2 alt alanı işaretle ve her biri için orada yapılan bir işi bir cümleyle açıkla.",
        ],
        "kontrol": [
            "{bolum} alt alanlarının listesi elinde.",
            "Saha ağırlıklı en az 2 alt alan işaretli.",
            "Bu alt alanlarda yapılan bir işi bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "",
    },
    "A6-U-2": {
        "nasil": [
            "Takımında ya da katıldığın bir etkinlikte üstlenebileceğin bir görev seç: kaptan yardımcılığı, malzeme sorumluluğu, antrenman takvimi ya da etkinlik organizasyonu.",
            "Antrenörüne ya da öğretmenine bu sorumluluğu almak istediğini söyle ve beklentilerini sor.",
            "Görevin için basit bir plan yaz: ne yapacaksın, ne zaman, kiminle?",
            "Görevini düzenli yap ve her antrenman ya da etkinlikten sonra neyi iyi yaptığını, neyi geliştirebileceğini kısaca not et.",
        ],
        "kontrol": [
            "Takımında ya da bir etkinlikte resmî bir sorumluluk üstlendin.",
            "Bu görevle ilgili planın ve tarihli notların var.",
            "Sorumluluk alırken yaşadığın bir zorluğu ve nasıl çözdüğünü anlatabiliyorsun.",
        ],
        "ipucu": "Kaptan seçilmesen bile küçük bir organizasyon görevi almak aynı beceriyi geliştirir.",
    },
    "A7-G-1": {
        "nasil": [
            "Yakında teslim edeceğin bir ödev seç.",
            "Kontrol listesi hazırla: Ödevin tamam sayılması için gereken her şeyi alt alta madde madde yaz. Örneğin: \"Kapakta adım var\", \"Kaynakları ekledim\", \"İmla kontrolü yaptım\".",
            "Ödevin şartlarını (sayfa sayısı, biçim, teslim tarihi) öğretmeninin yönergesinden kontrol edip listeye ekle.",
            "Teslimden önce listeyi baştan sona oku ve tamamladığın her maddenin yanına tik koy; eksik varsa tamamla. Listeyi sakla; bir sonraki ödevde tekrar kullanabilirsin.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ödev bir başlangıç denemesi. İşe yaradıysa sonraki ödevlerinde de listeyi kullan ve kaç ödevde kullandığını say (ör. 4 ödevden 3'ü).",
        ],
        "kontrol": [
            "Tüm maddeleri tikli bir kontrol listen var.",
            "Bu listeyle hazırladığın ödevi teslim ettin.",
            "Liste sayesinde fark ettiğin bir eksikliği söyleyebiliyorsun.",
        ],
        "ipucu": "Listeyi kısa tut; 5–10 madde genellikle yeterli.",
    },
    "A7-G-2": {
        "nasil": [
            "Son birkaç ödevini ya da sınav kâğıdını önüne koy.",
            "Bilgi eksiğinden değil, adım atlamaktan ya da dikkatsizlikten kaynaklanan hataları bul. Örneğin: işareti yanlış taşımak, birimi yazmamak, soruyu yarım okumak.",
            "Her hatanın yanına hangi adımda olduğunu yaz: soruyu okuma, işlem, kontrol ya da cevabı yazma.",
            "Her hata için bir dahaki sefere ekleyeceğin kontrolü tek cümleyle yaz. Örneğin: \"Cevabı yazmadan önce soruyu bir kez daha okuyacağım.\"",
            "Bu kontrolleri bir kâğıda toplayıp çalışma masana as.",
        ],
        "kontrol": [
            "En az 3 hata ve her birinin hangi adımda olduğu yazılı.",
            "Her hata için ekleyeceğin kontrol yazılı.",
        ],
        "ipucu": "Aynı tür hata tekrar ediyorsa bu bir şanssızlık değil, bir alışkanlıktır; tek bir kontrol çoğu zaman yeter.",
    },
    "A7-G-3": {
        "nasil": [
            "Uygulayacağın bir talimat seç: bir yemek tarifi, bir mobilya ya da oyuncak montaj kılavuzu, ya da öğretmen gözetiminde bir deney protokolü (deneyin adım adım yazılı yapılış talimatı).",
            "Başlamadan önce talimatı baştan sona bir kez oku ve gereken malzemelerin hepsini hazırla.",
            "Her adımı tamamladığında talimattaki o adımın yanına tik koy; bir adımı atlama ya da sırasını değiştirme.",
            "Ocak, bıçak ya da alet kullanman gerekiyorsa bir yetişkinden yardım al.",
            "Bitince sonucu kontrol et ve zorlandığın ya da belirsiz bulduğun bir adımı not et.",
        ],
        "kontrol": [
            "Tüm adımları işaretli bir talimat kâğıdın var.",
            "İş beklendiği gibi sonuçlandı (yemek, montaj ya da deney tamam).",
            "Hangi adımın en çok dikkat gerektirdiğini söyleyebiliyorsun.",
        ],
        "ipucu": "Talimatta anlamadığın bir adım varsa tahmin etmek yerine sor ya da araştır.",
    },
    "A7-G-4": {
        "nasil": [
            "Ders çalışırken izleyeceğin şablonu bir kâğıda yaz ve masana as: 1) Konu özeti, 2) Örnek, 3) Soru çözümü, 4) Tekrar.",
            "Konu özeti: Konunun ana fikirlerini kitaptan okuyup 5–6 satırla kendi cümlelerinle yaz.",
            "Örnek: Kitaptaki ya da öğretmeninin çözdüğü bir örneği adım adım incele; sonra kendi başına 5–10 soru çöz.",
            "Tekrar: 1–2 gün sonra özetini 5 dakika gözden geçir ve yanlış yaptığın soruları tekrar çöz. Şablonu her uyguladığında tarihini ve çalıştığın konuyu işaretle.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Şablonu uyguladığın en az 8 oturum tarihiyle işaretli.",
            "Defterinde aynı sırayla (özet, örnek, soru, tekrar) çalışılmış konular var.",
            "Bu şablonun çalışmanı nasıl etkilediğini bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "Şablon ilk oturumlarda yavaş gelebilir; birkaç uygulamadan sonra sıra kendiliğinden oturur.",
    },
    "A7-G-5": {
        "nasil": [
            "\"{bolum} standartları\", \"{bolum} yönetmelik\" ya da \"{bolum} meslek ilkeleri\" diye arama yap; meslek odalarının ve resmî kurumların sayfalarını tercih et.",
            "Standart, bir işin nasıl yapılması gerektiğini belirleyen ortak kurallardır; prosedür ise bir işin adım adım yapılış sırasıdır. Bulduklarını bir listeye yaz.",
            "En az 2 standart ya da prosedür seç ve her biri için ne işe yaradığını 2–3 cümleyle yaz.",
            "Bu kuralların uyulmadığında ne olabileceğini bir örnekle düşün ve not et.",
        ],
        "kontrol": [
            "En az 2 standart ya da prosedürün adı ve kısa açıklaması yazılı.",
            "Bunların neden önemli olduğunu bir örnekle anlatabiliyorsun.",
            "Hangi kaynaklardan öğrendiğini gösterebiliyorsun.",
        ],
        "ipucu": "Metinler çok teknik gelirse bir öğretmenine ya da o alanda okuyan birine sor.",
    },
    "A7-G-6": {
        "nasil": [
            "Yapacağın projeyi seç. Örneğin: bir okul etkinliği, bir maket, bir web sayfası ya da bir araştırma.",
            "Başlamadan önce projeyi aşamalara böl ve her aşamaya bir bitiş tarihi koy. Örneğin: \"1. Araştırma, 2. Tasarım, 3. Üretim, 4. Sunum\"; her aşamanın yanına hedef tarihini yaz.",
            "Bir proje defteri aç ve her aşamada ne yaptığını, ne kadar sürdüğünü ve karşılaştığın sorunları yaz.",
            "Her aşamanın sonunda fotoğraf, taslak ya da dosya gibi bir kanıt ekle.",
            "Proje bitince planlanan ve gerçekleşen tarihleri karşılaştır ve kısa bir değerlendirme yaz.",
        ],
        "kontrol": [
            "Aşamaları ve tarihleri baştan yazılmış bir planın var.",
            "Proje defterinde her aşamanın notu ve kanıtı var.",
            "Planla gerçekleşen arasındaki farkı açıklayabiliyorsun.",
        ],
        "ipucu": "Plan kayarsa sorun değil; nedenini yazmak bir sonraki planı daha iyi yapar.",
    },
    "A7-G-7": {
        "nasil": [
            "{bolum} alanında ya da prosedürlerle çalışan bir meslekte (eczacı, laborant, muhasebeci gibi) çalışan birini seç.",
            "Bu kişinin iş gününü anlatan bir röportaj ya da TRT Belgesel gibi bir kanalda bir belgesel izle; ya da aile çevrenden böyle biriyle ailenin bilgisiyle konuş.",
            "3 soruyu not et ya da sor: \"Hangi işlerde kontrol listesi kullanıyorsun?\", \"Neden?\", \"Bir adımı atlarsan ne olur?\"",
            "Bu kişinin kullandığı 2 düzen yöntemini yaz.",
            "Birini kendi çalışmana uyarla (ör. ödev teslim listesi) ve uyguladığında tarihli kısa bir not ekle.",
        ],
        "kontrol": [
            "Bu kişinin kullandığı 2 düzen yöntemi yazılı.",
            "Birini kendi çalışmana uyarladın ve notun var.",
        ],
        "ipucu": "Hata yapmanın pahalı olduğu mesleklerde düzen bir tercih değil, gerekliliktir; bu, o işin sana uyup uymadığını düşünmen için iyi bir ipucudur.",
    },
    "A7-U-1": {
        "nasil": [
            "Bir grup projesinde ekibe iş akışını hazırlamayı teklif et. İş akışı, işin hangi sırayla ve kim tarafından yapılacağını gösteren plandır.",
            "Projeyi küçük görevlere böl ve sırala; her göreve bir sorumlu ve bir tarih yaz.",
            "Planı bir tabloya ya da paylaşılan bir belgeye koy ve ilk toplantıda ekibe sun; önerileri al ve gerekirse güncelle.",
            "Her aşama sonrasında kısa bir kontrol yap: hangi görev bitti, hangisi gecikti?",
        ],
        "kontrol": [
            "Görevleri, sorumluları ve tarihleri gösteren bir iş akışı planın var.",
            "Ekip bu planla çalıştı ve görevler plana göre ilerledi.",
            "Planın işe yarayan ve yaramayan yönünü anlatabiliyorsun.",
        ],
        "ipucu": "Planı ekibe dayatma; birlikte karar vermek planın uygulanmasını kolaylaştırır.",
    },
    "A7-U-2": {
        "nasil": [
            "{bolum} ile ilgili bir okul ya da kulüp projesinde ekibe son kontrol görevini üstlenmek istediğini söyle.",
            "Kalite kontrol, bir işin teslimden önce belirlenen kurallara uyup uymadığını kontrol etmektir; projenin şartlarına göre bir kontrol listesi hazırla.",
            "Teslimden birkaç gün önce işi listeyle madde madde incele ve bulduğun hataları bir tabloya yaz.",
            "Hataları ekibe nazikçe ilet ve düzeltildiğini tekrar kontrol et.",
        ],
        "kontrol": [
            "Projenin kontrol listesini sen hazırladın.",
            "Teslimden önce son kontrolü yaptın ve bulduğun hatalar düzeltildi.",
            "Bulduğun en önemli hatayı ve nasıl düzeltildiğini anlatabiliyorsun.",
        ],
        "ipucu": "",
    },
    "A8-G-1": {
        "nasil": [
            "Boş bir A4 kâğıdı al ve yan çevir. Zihin haritası, bir konunun ana fikrini ortaya koyup alt başlıkları dallar halinde çizdiğin tek sayfalık bir şemadır.",
            "Kâğıdın ortasına konunun adını yaz ve etrafına daire çiz. Örneğin: \"Hücre\".",
            "Ortadan dışarıya ana dallar çiz ve her dala bir alt başlık yaz (ör. \"Organeller\", \"Hücre zarı\", \"Bölünme\"); her ana dal için farklı renk kullan.",
            "Ana dallardan daha ince dallar çıkar ve her birine 1–3 kelimelik anahtar bilgiler ekle; uzun cümle yazma.",
            "Konuyu çalışırken haritanı yanında tut ve öğrendikçe yeni dallar ekle.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu bir başlangıç denemesi. İşe yaradıysa yeni konularda da zihin haritası çiz ve kaç konuda yaptığını say.",
        ],
        "kontrol": [
            "En az 2 farklı konu için tek sayfalık zihin haritan var.",
            "Her haritada ortada konu, etrafında en az 3 ana dal bulunuyor.",
            "Haritaya bakarak konunun ana başlıklarını birine anlatabiliyorsun.",
        ],
        "ipucu": "Haritayı ilk seferde güzel yapmaya çalışma; karışık olsa da ana fikirleri görmen yeterli.",
    },
    "A8-G-2": {
        "nasil": [
            "Bir konuyu çalışmaya başlamadan önce defterine şu soruyu yaz: \"Bu konu neden var, neye yarıyor?\"",
            "Kitabın konu girişini, öğretmeninin açıklamasını ya da kısa bir araştırmayı kullanarak cevabı bul.",
            "Cevabı tek cümleyle yaz. Örneğin: \"Türev, bir şeyin ne hızla değiştiğini hesaplamaya yarar.\"",
            "Çalıştığın sonraki 5 konunun başına bu cümleyi ekle.",
        ],
        "kontrol": [
            "En az 5 konu için tek cümlelik amaç yazın var.",
            "Bir konunun ne işe yaradığı sorulduğunda tek cümleyle cevap verebiliyorsun.",
            "Konunun gerçek hayatta kullanıldığı bir yer söyleyebiliyorsun.",
        ],
        "ipucu": "Cevabı bulamazsan öğretmenine \"Bu konu nerede kullanılıyor?\" diye sor.",
    },
    "A8-G-3": {
        "nasil": [
            "Farklı derslerden iki konu seç ve aralarında ortak bir nokta ara. Örneğin: fizikteki hız ve matematikteki türev, ya da tarih ve coğrafyadaki göç yolları.",
            "Bağlantıyı 2–3 cümleyle yaz: Bu iki konu nasıl birbirine bağlı?",
            "Bu bağlantıyı bir arkadaşına anlat ve ona mantıklı gelip gelmediğini sor.",
            "Her yeni bağlantıyı defterinde \"Bağlantılarım\" başlıklı bir sayfaya tarihiyle yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
            "Bu bir başlangıç. İşe yaradıysa bağlantı aramayı sürdür ve her yeni bağlantıyı tarihiyle not et.",
        ],
        "kontrol": [
            "Defterinde en az 3 disiplinler arası bağlantı yazılı.",
            "Bu bağlantılardan en az birini bir arkadaşına anlattın.",
            "Her bağlantıyı bir iki cümleyle açıklayabiliyorsun.",
        ],
        "ipucu": "En şaşırtıcı bağlantılar genelde birbirinden en uzak görünen dersler arasında çıkar.",
    },
    "A8-G-4": {
        "nasil": [
            "Özetleyeceğin bir üniteyi seç ve ünitenin konu başlıklarını kitabın içindekiler kısmından bir listeye yaz.",
            "Akış diyagramı ya da şema, kavramları kutular içine yazıp aralarını oklarla bağladığın bir çizimdir; oklar sebep-sonuç ya da sıra gösterir.",
            "Büyük bir kâğıtta her alt konuyu bir kutuya yaz ve kutuları ilişkilerine göre oklarla bağla; okların üstüne kısa açıklamalar ekle (ör. \"neden olur\", \"sonra\").",
            "Her kutuya en önemli 1–2 bilgiyi ya da formülü ekle.",
            "Şemanı kullanarak üniteyi baştan sona kendine ya da bir arkadaşına anlat; eksik kalan yerleri tamamla.",
        ],
        "kontrol": [
            "Bir ünitenin tamamını gösteren tek bir şeman var.",
            "Şemadaki kutular oklarla anlamlı biçimde bağlanmış.",
            "Şemaya bakarak üniteyi baştan sona anlatabiliyorsun.",
        ],
        "ipucu": "Önce kurşun kalemle taslak çiz; yerleşim oturunca renklendir.",
    },
    "A8-G-5": {
        "nasil": [
            "Sistem düşüncesi, bir şeyi parçalarıyla ve parçaların birbirini nasıl etkilediğiyle birlikte görmektir; bu konuda giriş düzeyinde bir kitap, makale ya da video seç.",
            "Kaynağı bölümlere ayırarak oku ve öğrendiğin temel kavramları not et (ör. \"geri besleme döngüsü\": bir sonucun başlangıçtaki nedeni yeniden etkilemesi).",
            "{bolum} ile ilgili bir sistem seç. Örneğin: bir hastanenin işleyişi, bir şehrin ulaşımı ya da bir ekosistem.",
            "Sistemin parçalarını kutulara yaz ve birbirini etkileyenleri oklarla bağla; en az bir geri besleme döngüsü göstermeye çalış.",
            "Diyagramın altına sistemin nasıl işlediğini anlatan 3–4 cümle yaz.",
        ],
        "kontrol": [
            "Okuduğun kaynaktan aldığın notlar var.",
            "{bolum} ile ilgili bir sistem diyagramın hazır.",
            "Diyagramındaki bir parçayı değiştirince başka nelerin etkileneceğini açıklayabiliyorsun.",
        ],
        "ipucu": "Diyagramı ilk seferde düzgün çizmek zorunda değilsin; kurşun kalemle başlayıp okları sonradan düzeltebilirsin.",
    },
    "A8-G-6": {
        "nasil": [
            "Bölümünle ilgili büyük bir soru seç. Örneğin: \"20 yıl sonra bu meslek nasıl olacak?\" ya da \"Yapay zekâ bu alanı nasıl değiştirecek?\"",
            "Bu soruyla ilgili en az 3 güvenilir kaynak bul (haber, makale, uzman görüşü) ve her birinden önemli bilgileri not et.",
            "Yazının planını yap: giriş (soru ve neden önemli), gelişme (2–3 farklı görüş ya da bilgi), sonuç (senin cevabın).",
            "600–1000 kelimelik bir yazı yaz ve kullandığın kaynakları sona ekle.",
            "Yazını bir öğretmene okut ve önerilerine göre son halini ver.",
        ],
        "kontrol": [
            "Tamamlanmış yazın ve kaynak listen var.",
            "Yazında soruna verdiğin cevap açıkça yazılı.",
            "Büyük sorunun cevabını bir dakikada özetleyebiliyorsun.",
        ],
        "ipucu": "Kesin bir cevap bulamaman normal; farklı olasılıkları karşılaştırmak da güçlü bir sonuçtur.",
    },
    "A8-G-7": {
        "nasil": [
            "Farklı alanlardaki bilgileri birleştirerek yeni bir şey yapmış birini seç: bir bilim insanı, girişimci ya da {bolum} alanından biri.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: Hangi alanlardan bilgi topladı? Bunları nasıl bir araya getirdi? Ortaya ne çıktı?",
            "Birleştirdiği alanları ve sonucu basit bir şemayla çiz (alanlar kutularda, sonuç ortada) ya da 3 cümleyle anlat.",
            "Kendi derslerinden birleştirebileceğin iki alanı ve bundan ne çıkabileceğini tek cümleyle yaz.",
        ],
        "kontrol": [
            "Bu kişinin birleştirdiği alanlar ve ortaya çıkan sonuç şemayla ya da 3 cümleyle yazılı.",
            "Kendi birleştirebileceğin iki alanı yazdın.",
        ],
        "ipucu": "Yeni fikirlerin çoğu iki eski fikrin yan yana gelmesinden doğar; farklı derslere ilgi duymak bu yüzden değerlidir.",
    },
    "A8-U-1": {
        "nasil": [
            "Bir grup projesinin başında ekibe genel çerçeveyi çizmeyi teklif et.",
            "Ekip toplantısında projenin amacını tek cümleyle netleştirmeye öncülük et. Örneğin: \"Bu projede okulumuzdaki atık miktarını azaltacak bir öneri sunacağız.\"",
            "Projenin ana bölümlerini ve beklenen sonucu kısa bir taslakta topla; bir zihin haritası ya da şema kullanabilirsin.",
            "Taslağı ekibe sun, fikirlerini al ve son halini herkesin görebileceği bir yere koy.",
            "Proje boyunca ekip yolundan saparsa bu çerçeveyi hatırlat.",
        ],
        "kontrol": [
            "Projenin amacını ve ana bölümlerini gösteren bir çerçeve taslağın var.",
            "Ekip bu çerçeveye göre çalıştı.",
            "Projenin hedefini tek cümleyle söyleyebiliyorsun.",
        ],
        "ipucu": "Çerçeveyi kurduktan sonra ayrıntıları ekip arkadaşlarına bırakmak işi hızlandırır.",
    },
    "A8-U-2": {
        "nasil": [
            "Son birkaç teslimine bak ve en sık yaptığın ayrıntı hatalarını yaz. Örneğin: isim yazmayı unutmak, birim yazmamak, imla hatası.",
            "Bu hatalardan bir kontrol listesi hazırla: Teslimden önce kontrol edeceğin 5–8 maddeyi alt alta yaz.",
            "Her ödev ve sınav teslimin öncesinde 5 dakika ayırıp listeyi madde madde kontrol et.",
            "Her teslimden sonra bulduğun ve düzelttiğin hataları say ve bir kâğıda tarihiyle yaz.",
            "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\"",
        ],
        "kontrol": [
            "Kendi hatalarına göre hazırlanmış bir kontrol listen var.",
            "En az 5 teslimde bu listeyi kullandın.",
            "Son teslimlerindeki ayrıntı hatası sayısı ilk teslimlerine göre azaldı.",
        ],
        "ipucu": "Listeyi kalemliğine ya da defterinin kapağına yapıştırırsan unutmazsın.",
    },
    "A9-G-1": {
        "nasil": [
            "Anlatmak istediğin bir fikir seç. Örneğin: okulda bir geri dönüşüm köşesi kurmak ya da bir uygulama fikri.",
            "1 dakikalık konuşmanı 3 bölümde yaz: Sorun ne? Senin çözümün ne? Neden işe yarar ya da kimin işine yarar?",
            "Dikkat çekici bir açılış cümlesi ekle. Örneğin: \"Her gün kantinde kaç plastik bardak çöpe gidiyor, hiç düşündünüz mü?\"",
            "Telefonundaki kronometreyle 3–4 kez prova yap; 1 dakikayı aşarsan gereksiz cümleleri çıkar.",
            "Bir arkadaşına sun ve ondan anladığı fikri bir cümleyle tekrar etmesini iste.",
        ],
        "kontrol": [
            "Yazılı bir 1 dakikalık konuşma metnin var.",
            "Sunumunu bir arkadaşına 1 dakika içinde yaptın.",
            "Arkadaşın fikrini doğru şekilde tekrar edebildi.",
        ],
        "ipucu": "Metni ezberleme; ana noktaları hatırlayıp kendi sözlerinle anlat.",
    },
    "A9-G-2": {
        "nasil": [
            "Okulda, evde ya da mahallende seni ya da başkalarını rahatsız eden durumları düşün ve 5–6 tanesini yaz. Örneğin: \"Kantinde sıra çok uzun.\"",
            "Bunlardan en çok kişiyi etkileyen 3 tanesini seç.",
            "Her biri için \"Bu sorun kimi, nasıl etkiliyor?\" sorusunu bir cümleyle cevapla.",
            "Her soruna gerçekçi bir çözüm fikri yaz. Örneğin: \"Kantine önceden sipariş verilebilecek bir liste.\"",
        ],
        "kontrol": [
            "3 problem ve her biri için bir çözüm fikri yazılı.",
            "Her problemin kimi etkilediğini söyleyebiliyorsun.",
            "Çözüm fikirlerinden birini neden işe yarayacağıyla birlikte anlatabiliyorsun.",
        ],
        "ipucu": "Çok büyük sorunlar yerine yakın çevrende gördüğün küçük sorunlarla başla.",
    },
    "A9-G-3": {
        "nasil": [
            "Okulundaki kermes, bilim şenliği ya da kulüp etkinliklerinde satış veya tanıtım masası görevini almak istediğini öğretmenine söyle.",
            "Satacağın ya da tanıtacağın ürünü iyi tanı ve 2–3 cümlelik bir tanıtım hazırla. Örneğin: \"Bu kurabiyeler el yapımı, gelirimiz kütüphaneye gidecek.\"",
            "Etkinlik günü gelen kişileri güler yüzle karşıla, ürünü anlat ve sorularını cevapla; para alışverişinde dikkatli ol ve sayarak ver.",
            "Etkinlik sonunda kaç ürün sattığını ya da kaç kişiyle konuştuğunu ve en etkili bulduğun cümleyi not et.",
        ],
        "kontrol": [
            "Satış ya da tanıtım görevini baştan sona tamamladın.",
            "Satış ya da tanıtım sayın not edilmiş.",
            "İnsanları ikna etmede neyin işe yaradığını söyleyebiliyorsun.",
        ],
        "ipucu": "İlk birkaç kişiyle konuşmak zor gelebilir; birkaç denemeden sonra rahatlarsın.",
    },
    "A9-G-4": {
        "nasil": [
            "Okulunda girişimcilik kulübü olup olmadığını rehberlik servisine ya da öğretmenlerine sor.",
            "Kulüp yoksa gençlere yönelik girişimcilik programlarını öğretmeninin önerisiyle araştır; Teknofest gibi bilinen organizasyonların girişimcilik kategorilerine de bakabilirsin.",
            "Katılmak istediğin programa ailenin ya da öğretmeninin bilgisi dahilinde başvur.",
            "Katıldığın her etkinlikte en az bir soru sor ve öğrendiğin en önemli fikri bir deftere yaz.",
        ],
        "kontrol": [
            "En az 2 kulüp ya da program etkinliğine katıldın.",
            "Her etkinlikten öğrendiğin bir fikir yazılı.",
            "Girişimcilikle ilgili öğrendiğin bir kavramı açıklayabiliyorsun.",
        ],
        "ipucu": "Kulüp yoksa öğretmeninle birlikte kurmayı önerebilirsin.",
    },
    "A9-G-5": {
        "nasil": [
            "Ailenle konuşarak küçük ve güvenli bir girişim fikri seç: el yapımı takı ya da kart, küçük öğrencilere ders desteği ya da dijital içerik üretmek gibi.",
            "Kime satacağını ve ürününün fiyatını belirle; satışları ailenin bilgisi dahilinde, yalnızca tanıdığın çevrede ya da okul etkinliklerinde yap.",
            "Gelir-gider tablosu aç: Bir tabloya tarih, açıklama, gider (malzeme vb.) ve gelir (satış) sütunları koy ve her parayı kaydet.",
            "İlk ürününü hazırla ve ilk satışını yap.",
            "Birkaç satıştan sonra toplam geliri ve gideri hesapla, kâr ya da zarar ettiğini gör ve neyi değiştireceğini yaz.",
        ],
        "kontrol": [
            "İlk satışını yaptın.",
            "Tarih, gelir ve gider sütunları dolu bir gelir-gider tablon var.",
            "Kâr ya da zarar ettiğini ve nedenini açıklayabiliyorsun.",
        ],
        "ipucu": "İnternetten satış yapacaksan mutlaka ailenle birlikte yap ve kişisel bilgilerini paylaşma.",
    },
    "A9-G-6": {
        "nasil": [
            "İkna ve sunum üzerine bir kaynak seç: kütüphaneden bir kitap, ücretsiz bir çevrim içi kurs ya da güvenilir eğitim videoları.",
            "Okurken ya da izlerken öğrendiğin teknikleri bir listeye yaz. Örneğin: hikâyeyle başlamak, karşı görüşü önceden cevaplamak, sayı ve örnek kullanmak, göz teması.",
            "Listeden en çok işine yarayacak 3 tekniği seç.",
            "Bir sunum hazırla (sınıf ödevi ya da kulüp sunumu olabilir) ve bu 3 tekniği bilerek kullan; notlarında her tekniği nerede kullandığını işaretle.",
            "Sunumdan sonra bir öğretmen ya da arkadaşından bu teknikler hakkında geri bildirim iste.",
        ],
        "kontrol": [
            "Öğrendiğin tekniklerin listesi elinde.",
            "Bir sunumda 3 tekniği kullandığını notlarında gösterebiliyorsun.",
            "Her tekniğin ne işe yaradığını bir cümleyle açıklayabiliyorsun.",
        ],
        "ipucu": "",
    },
    "A9-G-7": {
        "nasil": [
            "Türkiye'den ya da dünyadan bir girişimci seç.",
            "Hakkında bir kaynak bul: okul ya da halk kütüphanesinin biyografi rafına bak, TRT Belgesel gibi bir kanalda bir belgesel ara ya da güvenilir bir gazete veya dergideki bir röportajı bul. Kütüphane görevlisinden ya da bir öğretmeninden öneri isteyebilirsin.",
            "Okurken ya da izlerken 3 soruyu not et: İlk müşterisini nasıl buldu? Hangi başarısızlığı yaşadı? Bundan ne öğrendi?",
            "Girişimcinin ilk müşteriyi bulma yolunu 2-3 cümleyle yaz.",
            "Yaşadığı bir başarısızlıktan çıkardığı dersi ve senin kendine uyarlayacağın bir davranışı birer cümleyle yaz.",
        ],
        "kontrol": [
            "Girişimcinin ilk müşteriyi bulma yolu yazılı.",
            "Yaşadığı bir başarısızlık ve çıkardığı ders yazılı.",
            "Kendine uyarlayacağın bir davranışı yazdın.",
        ],
        "ipucu": "Girişim hikâyeleri çoğu zaman başarıyı öne çıkarır; başarısızlık kısmını dikkatle okumak daha çok şey öğretir.",
    },
    "A9-U-1": {
        "nasil": [
            "\"{bolum} girişim\", \"{bolum} alanında yeni şirketler\" ya da \"{bolum} sorunları\" gibi aramalar yap; haber sitelerine ve sektör dergilerine bak.",
            "Bulduğun yeni şirketlerin ya da projelerin hangi soruna çözüm getirdiğini bir tabloya yaz.",
            "Alanda hâlâ çözülmemiş görünen sorunları ayrı bir listeye ekle.",
            "Bunlardan en az 2 fırsat alanı seç ve her biri için \"Burada neden fırsat var?\" sorusunu bir iki cümleyle cevapla.",
        ],
        "kontrol": [
            "Araştırdığın şirketler ve çözdükleri sorunlar bir tabloda yazılı.",
            "En az 2 fırsat alanı belirledin.",
            "Her fırsat alanının neden önemli olduğunu bir cümleyle anlatabiliyorsun.",
        ],
        "ipucu": "",
    },
    "A9-U-2": {
        "nasil": [
            "Rehberlik servisine ve öğretmenlerine lise öğrencilerine açık iş fikri ya da girişimcilik yarışmalarını sor; Teknofest gibi bilinen organizasyonların kategorilerini de incele.",
            "Bir yarışma seç ve şartnamesini (kurallarını anlatan belgeyi) oku: kimler katılabilir, ne teslim ediliyor, son tarih ne?",
            "İş fikrini hazırla: Sorun, çözüm, hedef kitle (ürünü kim kullanacak), nasıl gelir elde edeceğin ve ekip başlıklarıyla bir sayfa yaz.",
            "Gerekirse kısa bir sunum ya da video hazırla ve bir öğretmene danışarak geliştir.",
            "Başvurunu ailenin ya da öğretmeninin bilgisi dahilinde süresi içinde gönder ve onay mesajını sakla.",
        ],
        "kontrol": [
            "Yarışmaya başvurunu gönderdin ve onayın var.",
            "İş fikrin sorun, çözüm, hedef kitle ve gelir başlıklarıyla yazılı.",
            "İş fikrini 1 dakikada anlatabiliyorsun.",
        ],
        "ipucu": "Yarışmaya ekip olarak katılmak hem işi bölüştürür hem de fikri güçlendirir.",
    },
}

# ============================ [2026-10-09] EK ADIMLARIN DETAYI ============================
# gelisim_icerigi._EK_GELISIM ile eklenen adımlar (Maarif Modeli eğilim ve okuryazarlık becerileri; SCCT öz yeterlik).
_EGER_O_ZAMAN = "Planını tek cümleyle yaz ve görünür bir yere as: \"Eğer [ne zaman / nerede], o zaman [ne yapacağım].\" Örneğin: \"Eğer okuldan gelip çantamı bırakırsam, o zaman hemen bu adımı yapacağım.\""
_IKI_AY = "Bu ilk deneme bir başlangıç. Yeni bir davranışın alışkanlığa dönüşmesi zaman alır ve kişiden kişiye değişir; acele etme, işe yaradıysa sürdür ve her uyguladığında tarihli kısa bir not ekle."

_EK_DETAY = {
    "P8-G-7": {
        "nasil": [
            "Bir kâğıdı ikiye böl: sol sütuna \"Başardığım şey\", sağ sütuna \"Bunu başarmamı sağlayan davranışım\" yaz.",
            "Son bir yılı düşün: okulda, sporda, evde, arkadaşlıkta başta zorlandığın ama sonunda üstesinden geldiğin 5 durumu sol sütuna yaz. Küçük şeyler de sayılır (ör. korktuğun bir sınavdan iyi not almak).",
            "Her birinin karşısına senin ne yaptığını yaz: \"Her gün 20 dakika çalıştım\", \"Yardım istedim\", \"Vazgeçmedim, ikinci kez denedim\" gibi.",
            "Sağ sütunda tekrar eden davranışların altını çiz; bunlar senin güçlü yanların.",
            "Listeyi telefonunda ya da defterinde sakla; yeni bir sorumluluk almadan önce bir kez oku.",
        ],
        "kontrol": [
            "Listende 5 başarı var.",
            "Her başarının yanında senin yaptığın somut bir davranış yazılı (\"şanslıydım\" değil).",
            "Tekrar eden en az 1 güçlü davranışını söyleyebiliyorsun.",
        ],
        "ipucu": "\"Ben yapabilirim\" duygusu en çok geçmişte gerçekten yaptıklarını hatırlayınca güçlenir; bu yüzden somut örnekler yaz.",
    },
    "P8-G-8": {
        "nasil": [
            "Liderliğini beğendiğin bir kişi seç: bir öğretmen, kulüp başkanı, takım kaptanı ya da grup ödevindeki bir arkadaşın.",
            "Onu bir süre gözlemle ve 3 davranışını not et: Gruba nasıl yön veriyor, anlaşmazlıkta ne yapıyor, nasıl karar veriyor?",
            "Bu davranışlardan sana en uygun olanı seç (ör. \"Herkesin fikrini sırayla soruyor\").",
            "Sonra bir grup çalışmasında, sınıfta ya da ailende bu davranışı en az bir kez dene.",
            "Denedikten sonra 3 cümle yaz: Ne yaptın, insanlar nasıl tepki verdi, bir dahaki sefere neyi farklı yaparsın?",
        ],
        "kontrol": [
            "Gözlem notunda en az 3 davranış var.",
            "Seçtiğin davranışı en az bir kez gerçekten denedin.",
            "Denemenin sonucunu ve bir sonraki adımını yazdın.",
        ],
        "ipucu": "Birinin bir şeyi başardığını görmek, \"ben de yapabilirim\" duygusunu güçlendirir; özellikle sana benzeyen birini seçersen.",
    },
    "P7-G-7": {
        "nasil": [
            "Son zamanlarda zorlandığın bir anı hatırla: sınav, yeni bir ortam, bir tartışma ya da başarısız olduğun bir deneme.",
            "O an kafandan geçen cümleyi olduğu gibi yaz. Örneğin: \"Ben bunu asla beceremem.\"",
            "Şimdi aynı durumda olan yakın bir arkadaşını düşün. Ona ne söylerdin? Bu cümleyi de yaz. Örneğin: \"İlk denemede zorlanmak normal, geçen sefer de zorlanmıştın ama başardın.\"",
            "İkinci cümleyi kısa bir hâle getir ve telefon notlarına kaydet.",
            "Bir sonraki zorlukta bu cümleyi kendine sessizce söyle ve ne hissettiğini not et.",
        ],
        "kontrol": [
            "İki cümle de yazılı: zorlandığında kendine söylediğin ve arkadaşına söyleyeceğin.",
            "Cesaretlendirici cümlen kolayca hatırlanacak kadar kısa.",
            "Bir sonraki zorlukta bu cümleyi kullandın ya da kullanacağın anı belirledin.",
        ],
        "ipucu": "Kendine bir arkadaşına davrandığın kadar adil davranmak, risk almayı kolaylaştırır.",
    },
    "P7-G-8": {
        "nasil": [
            "Seni biraz zorlayan ama gerçekten yapmak istediğin bir şeyi seç: sınıfta konuşmak, yeni biriyle tanışmak, bir kulübe katılmak gibi.",
            "Bunu kolaydan zora 4 basamağa böl. Örneğin: 1) Sınıfta bir soru sor, 2) Bir konuda kısa yorum yap, 3) 1 dakikalık sunum yap, 4) 5 dakikalık sunum yap.",
            "Bir basamak rahat gelince sonrakine geç ve her basamağın tarihini yaz; bir basamak çok zor gelirse arasına daha küçük bir basamak ekle.",
            "Her basamaktan sonra 1'den 10'a kadar ne kadar gergin olduğunu yaz; çoğu kişide puan zamanla düşer, düşmese de hangi basamağın zor geldiğini görmüş olursun.",
            _EGER_O_ZAMAN,
            "Bu basamaklar bir başlangıç. İşe yaradıysa yeni bir hedefle aynı yöntemi sürdür ve her basamağın tarihini yaz.",
        ],
        "kontrol": [
            "4 basamağın kolaydan zora yazılı.",
            "En az 3 basamağı tamamladın ve her birinin tarihi yazılı.",
            "Gerginlik puanların kayıtlı ve ilk basamakla son basamağı karşılaştırabiliyorsun.",
        ],
        "ipucu": "Basamakları atlamak yerine küçük tutmak daha iyi çalışır; her başarı bir sonrakini kolaylaştırır.",
    },
    "I5-G-7": {
        "nasil": [
            "Okulda iyileştirilebileceğini düşündüğün bir şey seç: kütüphane saatleri, kantin, kulüp etkinlikleri, geri dönüşüm, ders arası düzeni gibi.",
            "Sorunu bir cümleyle yaz, sonra 3-4 arkadaşına sorup onların da aynı şeyi düşünüp düşünmediğini öğren.",
            "Yarım sayfalık bir öneri hazırla: Sorun ne, önerin ne, bunun için ne gerekiyor, kimler yardımcı olabilir?",
            "Önerini sınıf öğretmenine, rehber öğretmene ya da öğrenci meclisine ilet.",
            "Cevap ne olursa olsun, ne öğrendiğini 2-3 cümleyle not et.",
        ],
        "kontrol": [
            "Sorun ve önerin yazılı olarak hazır.",
            "En az 3 arkadaşının fikrini aldın.",
            "Önerini ilgili kişiye ilettin.",
        ],
        "ipucu": "Önerin kabul edilmese bile girişimde bulunmak başlı başına bir beceri; bir dahaki öneri daha kolay gelir.",
    },
    "P5-G-7": {
        "nasil": [
            "{bolum} ile ilgili merak ettiğin bir konu seç. Örneğin bir tıp adayı için \"Aşılar nasıl geliştirilir?\".",
            "Bu konu hakkında 5 soru yaz; soruların \"neden\" ya da \"nasıl\" ile başlasın.",
            "Her sorunun cevabını en az iki farklı kaynakta ara: bir ders kitabı, bir üniversite sayfası, güvenilir bir bilim sitesi ya da bir uzman röportajı.",
            "Cevapları yan yana yaz. Kaynakların birbirini tutmadığı ya da birinin daha eksik anlattığı noktayı işaretle.",
            "Son olarak cevabını hâlâ bilmediğin yeni bir soru yaz; merak bir sonraki soruyu doğurur.",
        ],
        "kontrol": [
            "5 sorunun her birinin cevabı yazılı.",
            "Her soru için en az 2 kaynak kullandın.",
            "Kaynakların farklı şeyler söylediği en az 1 noktayı ve yeni bir soru not ettin.",
        ],
        "ipucu": "Bir bilgiye iki kaynaktan bakmak, hem merakını hem de doğruyu yanlıştan ayırma becerini geliştirir.",
    },
    "I1-G-7": {
        "nasil": [
            "Zamanını iyi yöneten birini seç: {bolum} alanında çalışan biri ya da aile çevrende okul, iş ve ev işlerini birlikte yürüten biri.",
            "Röportaj ya da biyografi kullanabilirsin; yüz yüze konuşacaksan aile çevrenden birini ailenin bilgisiyle seç ya da öğretmeninden aracı olmasını iste.",
            "3 soru sor ya da not et: \"Gününü nasıl planlıyorsun?\", \"Çok iş birikince önce neyi yapıyorsun?\", \"Seni en çok ne oyalıyor?\"",
            "Cevaplardan işine yarayacak 2 yöntemi kendi cümlelerinle yaz. Örneğin: \"Akşamdan yarının 3 işini yazıyor.\"",
            "Bir yöntemi dene ve her uyguladığında tarihli kısa bir not ekle: Nasıl gitti?",
        ],
        "kontrol": [
            "Bu kişinin 2 zaman yönetimi yöntemi yazılı.",
            "Birini denedin ve nasıl gittiğini not ettin.",
        ],
        "ipucu": "Herkesin yöntemi herkese uymaz; denediğin yöntem işe yaramazsa ikinciyi dene.",
    },
    "A1-G-7": {
        "nasil": [
            "{bolum} alanında sayısal düşünmeyi kullanan birini seç: bir mühendis, ekonomist, doktor, mimar ya da istatistikçi olabilir.",
            "Okul ya da halk kütüphanesindeki bir biyografiye, TRT Belgesel gibi bir kanaldaki bir belgesele ya da güvenilir bir röportaja bak; ya da aile çevrenden böyle biriyle ailenin bilgisiyle konuş.",
            "3 soruyu not et ya da sor: \"İşinde matematiği nerede kullanıyorsun?\", \"Lisede öğrendiğin hangi konu işine yarıyor?\", \"Sayılarla zorlandığın bir an oldu mu?\"",
            "Bu kişinin işinde matematiği kullandığı 3 örneği kendi cümlelerinle yaz.",
            "Bu örneklerden birinin lisedeki hangi konuya dayandığını bul ve not et.",
        ],
        "kontrol": [
            "Bu kişinin işinde matematiği kullandığı 3 örnek yazılı.",
            "Örneklerden birini lisedeki bir konuyla ilişkilendirdin.",
        ],
        "ipucu": "Matematiğin işte nasıl kullanıldığını görmek, okulda çalıştığın konulara bir amaç kazandırır.",
    },
    "A1-G-8": {
        "nasil": [
            "Merak ettiğin bir soru seç. Örneğin \"Son 5 yılda {bolum} kontenjanları nasıl değişti?\" ya da \"Sınıfımızda en çok hangi meslek isteniyor?\".",
            "Veriyi bul ya da kendin topla: YÖK Atlas, TÜİK ya da sınıfında yapacağın kısa bir anket.",
            "Veriyi bir tabloya aktar (Excel, Google E-Tablolar ya da kâğıt). Satırlar ve sütunlar net etiketli olsun.",
            "Verine uygun bir grafik seç: zaman içindeki değişim için çizgi, karşılaştırma için çubuk grafik.",
            "Grafiğin altına 3 cümle yaz: Ne görüyorsun, en dikkat çekici nokta ne, bu veri neyi söylemiyor?",
        ],
        "kontrol": [
            "Tablon ve grafiğin hazır, eksenler ve başlık etiketli.",
            "Verinin kaynağı yazılı.",
            "3 cümlelik yorumunda verinin sınırını da belirttin.",
        ],
        "ipucu": "\"Bu veri neyi söylemiyor?\" sorusu iyi bir veri okurunu sıradan bir okurdan ayırır.",
    },
    "A4-G-7": {
        "nasil": [
            "Bir infografik, reklam afişi ya da haberdeki bir grafik seç ve ekran görüntüsünü al.",
            "Şu soruları yaz ve cevapla: Göze ilk ne çarpıyor? Hangi renkler, yazı tipleri ve yerleşim kullanılmış? Görsel neyi öne çıkarıyor, neyi küçük ya da gizli bırakıyor?",
            "Görselin amacını bir cümleyle yaz: bilgi vermek mi, ikna etmek mi, satmak mı?",
            "Aynı bilgiyi kendin daha açık ya da daha dürüst anlatacak şekilde yeniden tasarla; kâğıt-kalem ya da Canva gibi bir araç kullanabilirsin.",
            "İki görseli yan yana koy ve neyi değiştirdiğini 2-3 cümleyle açıkla.",
        ],
        "kontrol": [
            "Çözümleme sorularının hepsine cevap yazdın.",
            "Görselin amacını bir cümleyle belirttin.",
            "Kendi yeniden tasarımın ve değişikliklerin açıklaması hazır.",
        ],
        "ipucu": "Tasarımcılar görsellerle düşünür; bir görseli çözebilmek, onu iyi tasarlamanın ilk adımıdır.",
    },
    "I4-G-7": {
        "nasil": [
            "Adını ve soyadını bir arama motorunda (tırnak içinde) arat; görsel sonuçlara da bak.",
            "Kullandığın her sosyal medya hesabını aç ve gizlilik ayarlarına bak: Paylaşımların herkese mi, yalnızca arkadaşlarına mı açık?",
            "Kendine sor: Bir üniversite, burs komisyonu ya da ileride bir işveren bu hesaplara baksa ne görür, beni nasıl tanır?",
            "Değiştirmek istediğin en az bir şeyi düzelt: gizlilik ayarı, eski bir paylaşım ya da profil bilgisi.",
            "Bundan sonra paylaşım yapmadan önce soracağın bir kural yaz. Örneğin: \"5 yıl sonra görsem utanır mıyım?\"",
        ],
        "kontrol": [
            "Adını aratıp sonuçları gözden geçirdin.",
            "Tüm hesaplarının gizlilik ayarlarını kontrol ettin.",
            "En az bir şeyi düzelttin ve paylaşım kuralını yazdın.",
        ],
        "ipucu": "Dijital izin, yüz yüze tanışmadan önce seni tanıtan ilk izlenimdir; onu sen yönet.",
    },
    "I4-G-8": {
        "nasil": [
            "Çevrende gördüğün bir sorunu seç: engelli erişimi, okul önündeki trafik güvenliği, yemek israfı, sokak hayvanları gibi.",
            "Araştır: Bu sorundan hangi kurum sorumlu (belediye, okul, bakanlık)? Bununla ilgili bir kural ya da yasa var mı?",
            "Vatandaşların ve gençlerin neler yapabileceğini listele: dilekçe, gönüllülük, farkındalık çalışması, resmî başvuru yolları (ör. belediyenin çözüm masası ya da CİMER).",
            "{bolum} mezunlarının bu soruna nasıl katkı sağlayabileceğini düşün ve yaz.",
            "Hepsini bir sayfalık bir notta topla; istersen rehber öğretmenine ya da sınıf öğretmenine göster.",
        ],
        "kontrol": [
            "Sorun ve sorumlu kurumlar yazılı.",
            "İlgili bir kural ya da başvuru yolunu buldun.",
            "Bölümünün bu soruna katkısını en az 2 cümleyle açıkladın.",
        ],
        "ipucu": "Bir mesleğin topluma katkısını somut bir sorun üzerinden görmek, o mesleği seçme nedenini de netleştirir.",
    },
    "A3-G-7": {
        "nasil": [
            "Yakın zamanda biriyle (arkadaş, kardeş, aile) anlaşamadığın bir durumu seç.",
            "O kişinin yerine geçtiğini düşün ve olayı onun ağzından, \"ben\" diliyle yaz: \"Ben o gün yorgundum ve…\"",
            "En az 5 cümle yaz: Ne hissetti, neyi önemsedi, senin hangi davranışını nasıl algıladı?",
            "Yazarken yargılamamaya dikkat et; amacın haklı çıkmak değil, onu anlamak.",
            "Bitirince kendi bakışınla karşılaştır ve ikinizin de haklı olduğu bir noktayı bul.",
        ],
        "kontrol": [
            "Karşı tarafın bakışından en az 5 cümle yazdın.",
            "Metinde suçlayan ya da alaycı bir ifade yok.",
            "İkinizin de haklı olduğu en az bir noktayı buldun.",
        ],
        "ipucu": "İnsanlarla çalışan mesleklerde başkasının yerine geçebilmek, en sık kullanılan beceridir.",
    },
    "A3-G-8": {
        "nasil": [
            "Senden farklı bir hayat yaşamış birini seç: büyükanne ya da büyükbaban, başka bir şehirden ya da ülkeden gelen biri, uzun yıllardır çalışan bir esnaf.",
            "Önceden 5 soru hazırla. Örneğin: \"Benim yaşımdayken günün nasıl geçerdi?\", \"Hayatta en çok neyi önemsersin?\", \"Gençlere ne tavsiye edersin?\"",
            "Görüşmede dinlemeye odaklan; araya girmeden, merakla ek sorular sor.",
            "Görüşmeden sonra seni şaşırtan 3 şeyi ve ortak noktalarınızı yaz.",
        ],
        "kontrol": [
            "Görüşmeyi yaptın ve 5 sorunu sordun.",
            "Seni şaşırtan 3 şeyi yazdın.",
            "En az 1 ortak noktanızı not ettin.",
        ],
        "ipucu": "Farklı hayatları dinlemek, hem empatini hem de dünyaya bakışını genişletir.",
    },
    "A5-G-7": {
        "nasil": [
            "Laboratuvar, deney, gezi ya da belgesel gibi bu alandaki deneyimlerinin notlarını önüne koy.",
            "İki sütun aç: \"Beni heyecanlandıran\" ve \"Beni sıkan\". Her sütuna en az 2 şey yaz. Örneğin: \"Sonucu beklemek heyecanlı\", \"Uzun ölçüm tabloları sıkıcı\".",
            "Her maddenin yanına bunun hangi deneyimde ortaya çıktığını yaz.",
            "Kendine sor: \"Bu heyecan ve sıkılma {bolum} okurken ve çalışırken ne kadar karşıma çıkar?\" Cevabını 3-4 cümleyle yaz.",
        ],
        "kontrol": [
            "Heyecanlandıran ve sıkan en az 2'şer şey yazılı.",
            "Her birinin hangi deneyimden geldiği belli.",
            "{bolum} için çıkardığın sonucu yazdın.",
        ],
        "ipucu": "Sıkıldığın şeyler de değerli bir bilgidir; bir alanın her parçasını sevmek gerekmez, çoğunu sevmek yeterli olabilir.",
    },
    "A5-G-8": {
        "nasil": [
            "Sınıfında ya da evinde 7 gün boyunca atıkları ölçeceğini ailene ya da öğretmenine söyle.",
            "Atıkları türlerine ayır: kâğıt, plastik, cam, yemek artığı. Her gün sayısını ya da yaklaşık ağırlığını (mutfak tartısıyla) not et.",
            "Ölçüm bitince verileri bir tabloya aktar ve her türün toplamını hesapla.",
            "En çok atık hangi türden çıkıyor? Bunu azaltmak için gerçekten uygulanabilir 2 öneri yaz.",
            "Önerilerini sınıfınla ya da ailenle paylaş ve birini uygulamaya koy.",
        ],
        "kontrol": [
            "7 günlük ölçüm tablon dolu.",
            "Her atık türünün toplamı hesaplı.",
            "2 öneri yazdın ve en az birini paylaştın.",
        ],
        "ipucu": "Ölçmeden yönetemezsin: önce saymak, en etkili değişikliğin nerede olduğunu gösterir.",
    },
}
DETAY.update(_EK_DETAY)
