# -*- coding: utf-8 -*-
"""
[2026-10-10] Meslek simülasyonu — karar anları.

Her meslek için 2 gerçekçi durum. Seçeneklerin "doğru / yanlış"ı yoktur (güvenlik ve etik sorular hariç: orada
"onerilen": True işaretli seçenek meslekte beklenen davranıştır ve geri bildirimde belirtilir). Her seçenek bir
"yaklaşım" etiketi taşır; simülasyon sonunda öğrencinin hangi yaklaşımlarla karar verdiği özetlenir.

Anahtar: meslek adının küçük harfli hâli (bolumler.detay.meslekler[].ad ile eşleşir). Aynı içerik birkaç ada bağlanabilir.
İçerik genel mesleki bilgiye dayanır; rehber öğretmen ve meslek sahipleriyle gözden geçirilmesi önerilir.
"""

YAKLASIMLAR = {
    "guvenlik": "Güvenliği önceleyen", "analitik": "Analitik", "iletisim": "İletişimci", "ekip": "Ekip oyuncusu",
    "yaratici": "Yaratıcı", "planli": "Planlı", "empati": "Empatik", "etik": "İlkeli", "hizli": "Hızlı karar veren",
}


def _k(saat, baslik, durum, secenekler):
    return {"saat": saat, "baslik": baslik, "durum": durum,
            "secenekler": [{"metin": m, "sonuc": s, "yaklasim": y, **({"onerilen": True} if o else {})} for m, s, y, o in secenekler]}


SENARYOLAR = {
    "maden mühendisi": [
        _k("07:45", "Vardiya başı gaz ölçümü",
           "Yeraltı ocağında vardiya başlamadan önce bir galeride metan ölçümü sınır değerin üstünde çıktı. Üretim planı yetişmek zorunda ve ekip girişe hazır.",
           [("Galeriye girişi durdururum, havalandırmayı artırıp ölçümü tekrarlatırım; değer düşmeden kimse girmez.",
             "Doğru karar. Madencilikte gaz sınırı aşıldığında çalışma durdurulur; üretim gecikmesi telafi edilebilir, iş kazası edilemez. Maden mühendisinin ilk sorumluluğu ekibin güvenliğidir.", "guvenlik", True),
            ("Ekibi başka bir galeriye yönlendiririm, bu arada havalandırma ekibi sorunu çözer.",
             "Akıllıca bir esneklik: üretim tamamen durmaz, riskli bölge kapalı kalır. Yine de diğer galerilerin de ölçüldüğünden emin olmalısın.", "planli", False),
            ("Ölçüm cihazının hatalı olabileceğini düşünüp kısa bir süre çalışmaya izin veririm.",
             "Bu, madencilikte en tehlikeli varsayımdır. Cihazdan şüphe ediliyorsa ikinci bir cihazla ölçülür ama o sırada kimse içeri girmez. Mevzuat da bunu zorunlu tutar.", "hizli", False)]),
        _k("14:00", "Üretim hedefi geride",
           "Ay sonuna 5 gün kala üretim hedefinin %12 gerisindesiniz. Genel müdür ek vardiya istiyor; ekip yorgun ve bir iş makinesi bakımda.",
           [("Verileri çıkarıp gerçekçi bir plan sunarım: bakımdaki makine dönünce hangi tarihte yakalanacağını gösteririm.",
             "Analitik ve dürüst bir yaklaşım. Yöneticiler sayıya dayalı bir planı, aceleyle verilmiş bir sözden daha çok sever.", "analitik", False),
            ("Ekiple konuşup gönüllülerle kısa süreli ek vardiya düzenlerim, dinlenme sürelerini korurum.",
             "Ekibi sürece katmak motivasyonu artırır. Yorgunluğun iş kazası riskini artırdığını unutmadan sınırlı tutman önemli.", "ekip", False),
            ("Bakımı erteleyip makineyi hemen çalıştırırım.",
             "Kısa vadede üretim artar ama ertelenen bakım daha büyük arızaya ve güvenlik riskine dönüşebilir. Madende bakım takvimi pazarlık konusu olmamalı.", "hizli", False)]),
    ],
    "yazılım geliştirici": [
        _k("10:30", "Canlı sistemde hata",
           "Uygulamanızda kullanıcıların bir kısmı ödeme yapamıyor. Hata bir saat önceki güncellemeden sonra başladı.",
           [("Önce güncellemeyi geri alırım (rollback), sistem düzelince hatayı sakin kafayla incelerim.",
             "Yazılım ekiplerinin en çok önerdiği yol: önce kullanıcıyı kurtar, sonra nedeni bul. Buna olay yönetimi denir.", "planli", False),
            ("Logları inceleyip hatanın nedenini bulur, hızlıca düzeltme yazarım.",
             "Hata kısa sürede bulunursa işe yarar, ama kullanıcılar beklerken baskı altında yazılan düzeltme yeni hata doğurabilir.", "analitik", False),
            ("Ekip kanalına durumu yazıp kimin ne yapacağını paylaştırırım.",
             "İletişim olay anında çok değerlidir: biri geri alır, biri inceler, biri kullanıcılara bilgi verir. Tek başına kahraman olmaya gerek yok.", "iletisim", False)]),
        _k("15:00", "Kod incelemesi",
           "Takım arkadaşının yazdığı kodu incelerken, çalışan ama okunması çok zor ve test yazılmamış bir bölüm görüyorsun. Teslim tarihi yarın.",
           [("Nazik bir yorumla neyi neden önerdiğimi yazar, testleri birlikte eklemeyi teklif ederim.",
             "İyi kod incelemesi eleştiri değil iş birliğidir. Bu yaklaşım hem kodu hem ekip ilişkisini güçlendirir.", "ekip", False),
            ("Teslimden sonra düzeltilmek üzere bir iş kaydı açar, bugün onaylarım.",
             "Gerçek hayatta sık yapılan bir denge: buna 'teknik borç' denir. Kaydı açmak borcu unutmamanı sağlar.", "planli", False),
            ("Test yazılmadan onaylamam; kalite her şeyden önce gelir.",
             "Kaliteye önem vermen değerli. Bunu ekibe teslim baskısını da anladığını gösterecek şekilde iletmek önemli.", "etik", False)]),
    ],
    "pratisyen hekim": [
        _k("09:20", "Kalabalık poliklinik",
           "Sabah 40 hasta randevusu var. Bir hasta 'sadece reçete yazdırmaya geldim' diyor ama konuşurken son günlerde nefes darlığı yaşadığını söylüyor.",
           [("Reçeteyi yazmadan önce muayene eder, nefes darlığını sorgularım.",
             "Hekimlikte asıl iş, hastanın 'önemsiz' gördüğü belirtiyi yakalamaktır. Nefes darlığı ciddi bir hastalığın işareti olabilir.", "guvenlik", True),
            ("Reçeteyi yazar, nefes darlığı için ayrı randevu almasını söylerim.",
             "Yoğunluk anlaşılır ama hasta yeniden gelmeyebilir. Hekim ciddi olabilecek bir belirtiyi o anda değerlendirmelidir.", "hizli", False),
            ("Hastaya belirtilerini sakin bir dille sorar, korkutmadan neden önemli olduğunu anlatırım.",
             "İletişim hekimliğin yarısıdır: hasta anlaşıldığını hissederse bilgiyi daha doğru verir.", "empati", False)]),
        _k("13:00", "Antibiyotik isteği",
           "Bir veli, 2 gündür ateşi ve boğaz ağrısı olan çocuğu için ısrarla antibiyotik istiyor. Muayenede viral enfeksiyon düşünüyorsun.",
           [("Neden gerekmediğini sakin bir dille anlatır, hangi durumda tekrar gelmesi gerektiğini söylerim.",
             "Gereksiz antibiyotik direnç gelişimine yol açar. Velinin endişesini ciddiye alıp bilgilendirmek doğru yaklaşımdır.", "etik", True),
            ("Hızlı strep testi yapıp sonuca göre karar veririm.",
             "Veriye dayalı ve ikna edici bir yol: test, veliyi de seni de rahatlatır.", "analitik", False),
            ("Veli memnun kalsın diye reçeteyi yazarım.",
             "Kısa vadede çatışma biter ama hasta ve toplum sağlığı için zararlıdır. Hekim, istek değil endikasyonla reçete yazar.", "hizli", False)]),
    ],
    "avukat": [
        _k("09:00", "Duruşma öncesi yeni belge",
           "Duruşmaya bir saat var. Müvekkilin, davayı zayıflatabilecek ama karşı tarafın da bildiği bir belgeyi sana yeni gösteriyor.",
           [("Belgeyi dikkatle okuyup savunma stratejimi buna göre güncellerim.",
             "Avukatlık, sürprizlere hızla uyum sağlamaktır. Karşı tarafın bildiği bir belgeyi yok saymak işe yaramaz.", "analitik", False),
            ("Müvekkille kısa bir görüşme yapıp belgenin hikâyesini öğrenirim.",
             "Belgenin bağlamı çoğu zaman belgenin kendisinden önemlidir. İyi soru sormak avukatın en güçlü aracıdır.", "iletisim", False),
            ("Mahkemeden süre isterim; hazırlıksız savunma yapmam.",
             "Gerekirse süre istemek meşru bir haktır. Ancak gerekçesini iyi açıklaman gerekir.", "planli", False)]),
        _k("16:00", "Müvekkilin isteği",
           "Bir müvekkil, tanık olarak dinlenecek arkadaşına 'ne söyleyeceğini' önceden yazmanı istiyor.",
           [("Bunun yapılamayacağını, tanığın yalnızca bildiğini anlatması gerektiğini açıklarım.",
             "Doğru. Tanığa ifade yazdırmak meslek kurallarına ve hukuka aykırıdır. Avukatlıkta güven, ilkelerden ödün vermemekle kazanılır.", "etik", True),
            ("Tanığa duruşmanın nasıl işlediğini, neler sorulabileceğini anlatırım ama ne söyleyeceğini yönlendirmem.",
             "Tanığı süreç hakkında bilgilendirmek meşrudur; içeriği yönlendirmemek şartıyla.", "iletisim", False),
            ("Müvekkili kırmamak için genel hatlarıyla bir metin hazırlarım.",
             "Bu, disiplin cezasına ve davanın kaybına yol açabilir. Müvekkile 'hayır' diyebilmek mesleğin parçasıdır.", "hizli", False)]),
    ],
    "psikolog": [
        _k("11:00", "İlk görüşme",
           "Danışan ilk seansta çok az konuşuyor, sorulara kısa cevaplar veriyor ve sık sık saate bakıyor.",
           [("Acele etmeden güven ilişkisi kurmaya odaklanır, onu buraya neyin getirdiğini merak ettiğimi söylerim.",
             "Terapötik ilişki her şeyin temelidir. İlk seanslarda güven, bilgi toplamaktan önce gelir.", "empati", False),
            ("Görüşmeyi daha yapılandırılmış hale getirip kısa bir ölçek uygularım.",
             "Yapılandırılmış araçlar bazı danışanları rahatlatır. Yine de ilişkiyi ihmal etmemek gerekir.", "analitik", False),
            ("Saate baktığını fark ettiğimi nazikçe söyler, nasıl hissettiğini sorarım.",
             "O anda olanı fark edip konuşmak (buna 'şimdi ve burada' denir) güçlü bir tekniktir.", "iletisim", False)]),
        _k("15:30", "Gizlilik ve risk",
           "16 yaşındaki bir danışan, kendine zarar verme düşüncelerinden söz ediyor ve bunu kimsenin bilmemesini istiyor.",
           [("Gizliliğin sınırını açıklar, güvenliği için ailesiyle ve gerekli birimlerle iş birliği yapacağımı birlikte konuşurum.",
             "Doğru. Gizlilik değerlidir ama yaşam riski olduğunda sınırı vardır; bunu danışana açıkça ve şefkatle anlatmak gerekir.", "etik", True),
            ("Risk düzeyini değerlendirmek için ayrıntılı sorular sorarım.",
             "Risk değerlendirmesi önemli bir adımdır; ardından güvenlik planı ve iş birliği gelir.", "analitik", False),
            ("Söz verdiğim için kimseye söylemem.",
             "Bu, danışanı tehlikede bırakabilir. Psikologlar risk durumunda gizliliği sınırlamakla yükümlüdür.", "hizli", False)]),
    ],
    "mimar": [
        _k("10:00", "Bütçe kısıtı",
           "Müşteri, tasarladığın evin bütçeyi %20 aştığını söylüyor ama büyük cam cepheden vazgeçmek istemiyor.",
           [("Cam cepheyi koruyup diğer kalemlerde (malzeme, metrekare) alternatifler hazırlarım.",
             "Müşterinin önceliğini koruyarak çözüm üretmek iyi mimarlığın parçasıdır.", "yaratici", False),
            ("Maliyet tablosu çıkarıp her seçeneğin bütçeye etkisini gösteririm.",
             "Rakamlar karar vermeyi kolaylaştırır; müşteri neyden vazgeçtiğini görerek seçer.", "analitik", False),
            ("Cam cephenin enerji kaybı ve maliyetini anlatıp daha küçük pencereler öneririm.",
             "Teknik bilgiye dayalı dürüst bir öneri. İletişim tonu, müşterinin hayalini küçümsemeyecek şekilde olmalı.", "iletisim", False)]),
        _k("15:00", "Şantiyede farklılık",
           "Şantiye ziyaretinde bir kolonun projedekinden farklı yere konduğunu fark ediyorsun; beton dökümü yarın.",
           [("Dökümü durdurup statik mühendis ve şantiye şefiyle hemen toplantı yaparım.",
             "Doğru. Taşıyıcı sistemdeki bir sapma güvenlik konusudur; beton döküldükten sonra düzeltmek çok zordur.", "guvenlik", True),
            ("Fotoğraflayıp tutanak tutar, yazılı olarak ilgililere bildiririm.",
             "Kayıt tutmak önemlidir, ama döküm öncesi acil bir görüşme de gerekir.", "planli", False),
            ("Küçük bir fark olduğunu düşünüp devam edilmesine izin veririm.",
             "Taşıyıcı elemanlarda 'küçük fark' yoktur; statik hesap değişebilir. Bu risk alınmamalı.", "hizli", False)]),
    ],
    "klinik hemşire": [
        _k("08:15", "Vardiya devri",
           "Gece vardiyasından devraldığın bir hastanın ilaç saatinin geçtiği ve kaydının eksik olduğu görünüyor.",
           [("İlacın verilip verilmediğini gece hemşiresiyle hemen netleştirir, sonra karar veririm.",
             "Doğru. Çift doz vermek de hiç vermemek de tehlikeli olabilir; önce bilgi doğrulanır.", "guvenlik", True),
            ("Hekimi bilgilendirip talimat isterim.",
             "Belirsizlikte hekimle iletişim doğru adımdır. Devir teslimdeki eksik de kayda geçirilmeli.", "iletisim", False),
            ("Saat geçtiği için ilacı hemen veririm.",
             "Bilgi doğrulanmadan verilen ilaç çift doza yol açabilir. Hemşirelikte 'emin değilsen sor' temel kuraldır.", "hizli", False)]),
        _k("14:30", "Kaygılı hasta yakını",
           "Ameliyattan çıkan hastanın kızı, annesinin durumu hakkında sürekli soru soruyor ve servis çok yoğun.",
           [("Birkaç dakika ayırıp anlayabileceği şekilde bilgi verir, ne zaman tekrar konuşacağımızı söylerim.",
             "Kısa ama düzenli bilgi, kaygıyı azaltır ve tekrar tekrar gelen soruları önler.", "empati", False),
            ("Hekimin bilgi vereceği saati öğrenip hasta yakınına iletirim.",
             "Rol sınırlarını bilmek önemli: tanı ve seyir bilgisini hekim verir, hemşire süreci açıklar.", "planli", False),
            ("Yoğun olduğumu söyleyip başka bir zaman sormasını isterim.",
             "Anlaşılır bir durum ama hasta yakını yalnız kalmış hisseder. Kısa bir açıklama bile fark yaratır.", "hizli", False)]),
    ],
    "şantiye mühendisi": [
        _k("07:30", "Kaskı olmayan işçi",
           "Sabah turunda iskelede baret takmadan çalışan bir işçi görüyorsun; 'bir dakikalık iş' diyor.",
           [("İşi durdurup baretini takmasını sağlar, ekip başıyla iş güvenliği hatırlatması yaparım.",
             "Doğru. Şantiyede kazaların büyük kısmı 'bir dakikalık' işlerde olur; mühendis güvenlik kültürünü örnek olarak yaşatır.", "guvenlik", True),
            ("Kısa bir güvenlik toplantısı yapıp nedenlerini anlatırım.",
             "Kuralın nedenini anlatmak uyumu artırır. Önce o anki tehlikeyi gidermek gerekir.", "iletisim", False),
            ("İşi bitirmesini bekler, sonra uyarırım.",
             "Tehlike tam o anda var. Uyarı sonraya bırakılmamalı.", "hizli", False)]),
        _k("11:00", "Malzeme gecikmesi",
           "Demir teslimatı iki gün gecikecek; kalıp ekibi yarın boşta kalacak.",
           [("İş programını değiştirip ekibi başka bir bölümün işine kaydırırım.",
             "Planlamada esneklik şantiye mühendisinin en önemli becerilerinden biridir.", "planli", False),
            ("Tedarikçiyle görüşüp kısmi teslimat ayarlamaya çalışırım.",
             "Çözüm odaklı iletişim. Kısmi teslimat çoğu zaman mümkündür.", "iletisim", False),
            ("Gecikmenin maliyetini hesaplayıp işverene rapor ederim.",
             "Kayıt ve raporlama sözleşme açısından önemlidir; çözümle birlikte sunulursa daha değerlidir.", "analitik", False)]),
    ],
    "klinisyen veteriner hekim": [
        _k("10:00", "Acil getirilen köpek",
           "Bir aile, çikolata yemiş küçük bir köpekle geliyor. Bekleme salonunda aşı için gelen üç hasta var.",
           [("Acil hastayı öne alır, bekleyenlere kısaca durumu açıklarım.",
             "Doğru. Çikolata (teobromin) köpekler için zehirlidir; erken müdahale hayat kurtarır. Önceliklendirme (triyaj) veteriner hekimlikte de temeldir.", "guvenlik", True),
            ("Ne kadar ve hangi çikolatayı yediğini sorup riski hesaplarım.",
             "Miktar ve tür (bitter/sütlü) tedaviyi belirler; doğru bilgi doğru müdahaleyi sağlar.", "analitik", False),
            ("Aileyi sakinleştirip sürecin nasıl ilerleyeceğini anlatırım.",
             "Hayvan sahipleriyle iletişim, tedaviye uyum için çok önemlidir.", "empati", False)]),
        _k("16:30", "Tedavi ücreti",
           "Kedinin ameliyata ihtiyacı var ama sahibi ücreti karşılayamayacağını söylüyor.",
           [("Seçenekleri (taksit, daha basit tedavi, belediye ya da dernek desteği) birlikte konuşurum.",
             "Gerçekçi seçenekler sunmak hem hayvan refahını hem sahibinin durumunu gözetir.", "empati", False),
            ("Tedavinin zorunlu kısmını ve ertelenebilecek kısmını ayırıp maliyeti düşürürüm.",
             "Analitik ve çözüm odaklı bir yaklaşım.", "analitik", False),
            ("Ücretin klinik politikası olduğunu söyler, başka kliniğe yönlendiririm.",
             "İşletme gerçekliği anlaşılır, ancak hayvanın durumu aciliyet taşıyorsa yalnızca yönlendirme yeterli olmayabilir.", "hizli", False)]),
    ],
    "serbest eczacı": [
        _k("11:30", "İlaç etkileşimi",
           "Yaşlı bir hasta yeni bir reçeteyle geliyor. Kullandığı diğer ilaçlarla ciddi bir etkileşim riski görüyorsun.",
           [("Reçeteyi yazan hekimi arayıp durumu bildirir, alternatif isterim.",
             "Doğru. Eczacı reçetenin son güvenlik kontrolüdür; hekimle iletişim hastayı korur.", "guvenlik", True),
            ("Hastaya hangi ilaçları kullandığını ayrıntılı sorarım.",
             "Tam ilaç listesi olmadan etkileşim değerlendirmesi eksik kalır. İyi bir ilk adım.", "analitik", False),
            ("İlacı veririm, hekim bilir.",
             "Eczacının mesleki sorumluluğu buna izin vermez; etkileşimi fark eden kişi olarak harekete geçmelisin.", "hizli", False)]),
        _k("17:00", "Reçetesiz antibiyotik",
           "Tanıdık bir müşteri, 'boğazım ağrıyor, hep bunu kullanıyorum' diyerek reçetesiz antibiyotik istiyor.",
           [("Reçetesiz veremeyeceğimi nazikçe söyler, semptomları için uygun öneri verip hekime yönlendiririm.",
             "Doğru. Antibiyotikler reçeteyle verilir; eczacı aynı zamanda halk sağlığı danışmanıdır.", "etik", True),
            ("Neden reçete gerektiğini, antibiyotik direncini kısaca anlatırım.",
             "Bilgilendirme müşterinin tekrar istemesini önler.", "iletisim", False),
            ("Tanıdık olduğu için bir kutu veririm.",
             "Hem yasal hem sağlık açısından risklidir.", "hizli", False)]),
    ],
    "grafik tasarımcı": [
        _k("10:00", "Belirsiz brif",
           "Müşteri 'modern, dikkat çekici ama sade bir logo' istiyor; başka bilgi yok, teslim 3 gün sonra.",
           [("Müşteriyle kısa bir toplantı yapıp hedef kitle, renk ve örnek beğenilerini sorarım.",
             "İyi tasarım iyi sorularla başlar. Netleşmemiş brif çok sayıda revizyon demektir.", "iletisim", False),
            ("Farklı yönlerde 3 hızlı eskiz hazırlayıp müşteriye seçtiririm.",
             "Görsel seçenekler müşterinin ne istediğini anlamasına yardım eder.", "yaratici", False),
            ("Rakip markaları inceleyip bir ruh hali panosu (moodboard) hazırlarım.",
             "Araştırmaya dayalı başlangıç, tasarımı gerekçelendirmeyi kolaylaştırır.", "analitik", False)]),
        _k("15:30", "Yedinci revizyon",
           "Müşteri yedinci kez değişiklik istiyor; sözleşmede 3 revizyon hakkı var.",
           [("Sözleşmeyi hatırlatıp ek revizyonlar için ücret teklifi sunarım.",
             "Profesyonel sınırlar koymak serbest çalışmanın önemli parçasıdır.", "etik", False),
            ("Neden memnun olmadığını derinlemesine sorup asıl sorunu bulmaya çalışırım.",
             "Çok revizyon çoğu zaman yanlış anlaşılmış bir ihtiyacın işaretidir.", "empati", False),
            ("İlişki bozulmasın diye değişiklikleri yaparım.",
             "Kısa vadede müşteri memnun olur ama emeğinin karşılığını alamazsın.", "hizli", False)]),
    ],
    "sınıf öğretmeni": [
        _k("09:40", "Derse katılmayan öğrenci",
           "Bir öğrenci son bir haftadır derste hiç konuşmuyor ve teneffüslerde yalnız kalıyor.",
           [("Teneffüste kısa bir sohbetle nasıl olduğunu sorarım.",
             "Öğretmenle kurulan güven bağı, çocuğun derdini paylaşmasının ilk adımıdır.", "empati", False),
            ("Rehberlik servisi ve veliyle iletişime geçerim.",
             "Okul içi iş birliği doğru adımdır; değişikliğin nedeni okul dışında olabilir.", "ekip", False),
            ("Gözlemlerimi birkaç gün not edip bir örüntü olup olmadığına bakarım.",
             "Sistemli gözlem, sonraki adımları doğru seçmeyi sağlar.", "analitik", False)]),
        _k("13:30", "Konu anlaşılmadı",
           "Kesirler konusunu anlattın ama sınıfın yarısı alıştırmaları yapamıyor; müfredat programı ilerlemen gerektiğini söylüyor.",
           [("Konuyu somut materyallerle (pizza dilimleri, kâğıt katlama) farklı bir yoldan yeniden anlatırım.",
             "Farklı öğrenme yollarına hitap etmek kalıcı öğrenmeyi sağlar.", "yaratici", False),
            ("Anlayan öğrencileri anlamayanlarla eşleştirip akran öğretimi yaptırırım.",
             "Akran öğretimi hem anlatan hem dinleyen için etkili bir yöntemdir.", "ekip", False),
            ("Hafta planını yeniden düzenleyip konuya bir ders daha ayırırım.",
             "Temel konuyu oturtmadan ilerlemek sonraki konuları da zorlaştırır; plan esnekliği önemlidir.", "planli", False)]),
    ],
    "lise matematik öğretmeni": [
        _k("10:30", "'Bu ne işime yarayacak?'",
           "Bir öğrenci logaritma dersinde 'Bu hayatta ne işime yarayacak?' diye soruyor; sınıf da merakla bakıyor.",
           [("Deprem büyüklüğü, ses şiddeti ve faiz hesabı gibi gerçek örneklerle cevaplarım.",
             "Konuyu hayata bağlamak motivasyonu artırır.", "yaratici", False),
            ("Soruyu sınıfa yöneltip birlikte örnek bulmalarını isterim.",
             "Öğrencileri düşünmeye katmak, cevabı vermekten daha kalıcıdır.", "iletisim", False),
            ("YKS'de kaç soru çıktığını hatırlatırım.",
             "Kısa vadede işe yarar ama öğrenmeyi yalnızca sınava bağlar.", "hizli", False)]),
        _k("16:00", "Deneme sonuçları",
           "12. sınıfların deneme sonuçlarında türev sorularında sınıf ortalaması çok düşük.",
           [("Soru bazında analiz yapıp hangi alt konunun eksik olduğunu belirlerim.",
             "Veriye dayalı öğretim, zamanı doğru yere harcamanı sağlar.", "analitik", False),
            ("Gönüllüler için hafta sonu ek çalışma saati planlarım.",
             "Ek destek değerlidir; katılımı artırmak için kısa ve hedefli tutmak işe yarar.", "planli", False),
            ("Öğrencilerle konuşup zorlandıkları yeri onlardan dinlerim.",
             "Öğrencinin gözünden sorunu görmek, yöntemi doğru seçmeyi sağlar.", "empati", False)]),
    ],
    "diş hekimi": [
        _k("09:00", "Korkan hasta",
           "Çocukluğundan beri diş hekiminden korkan yetişkin bir hasta koltukta titriyor; dolgusu yapılmalı.",
           [("İşlemi adım adım anlatır, durmak istediğinde el kaldırabileceğini söylerim.",
             "Kontrolü hastaya vermek kaygıyı belirgin azaltır; bu yöntem yaygın olarak kullanılır.", "empati", False),
            ("Bugün yalnızca muayene ve temizlik yapıp güven kazanınca dolguya geçeriz.",
             "Kademeli yaklaşım uzun vadeli tedavi uyumunu artırır.", "planli", False),
            ("Hızlıca bitirmek için işleme hemen başlarım.",
             "İşlem bitse de hasta bir daha gelmeyebilir. Diş hekimliğinde güven, tedavinin parçasıdır.", "hizli", False)]),
        _k("14:00", "Sterilizasyon",
           "Asistanın, yoğunluk nedeniyle bazı aletlerin sterilizasyon döngüsünün kısa kesildiğini söylüyor.",
           [("O aletleri kullanmaz, döngünün tamamlanmasını beklerim; gerekirse randevuları kaydırırım.",
             "Doğru. Sterilizasyon pazarlık konusu olamaz; enfeksiyon kontrolü diş hekimliğinin temel kuralıdır.", "guvenlik", True),
            ("Alet sayısını ve iş akışını gözden geçirip bunun tekrar olmaması için plan yaparım.",
             "Kök nedeni çözmek gelecekteki riskleri önler.", "planli", False),
            ("Bu seferlik kullanırım.",
             "Hasta güvenliğini riske atar ve yasal sorumluluk doğurur.", "hizli", False)]),
    ],
    "pazarlama uzmanı": [
        _k("10:00", "Düşük performanslı kampanya",
           "Bir hafta önce başlayan sosyal medya kampanyası beklenen tıklamanın yarısını getiriyor.",
           [("Verileri inceleyip hangi görsel ve kitlenin işe yaradığını bulur, bütçeyi oraya kaydırırım.",
             "Veriye dayalı optimizasyon dijital pazarlamanın temelidir.", "analitik", False),
            ("İki farklı mesajla küçük bir A/B testi başlatırım.",
             "Deneme yapmak tahmin etmekten daha güvenilirdir.", "yaratici", False),
            ("Ekibi toplayıp beyin fırtınası yaparım.",
             "Farklı bakış açıları yeni fikirler getirir.", "ekip", False)]),
        _k("15:00", "Abartılı iddia",
           "Yönetici, ürün için 'piyasadaki en iyi' ifadesinin kullanılmasını istiyor; bunu destekleyen bir veri yok.",
           [("Kanıtlanamayan iddiaların reklam mevzuatına aykırı olabileceğini söyleyip ölçülebilir bir mesaj öneririm.",
             "Doğru. Kanıtsız üstünlük iddiaları tüketiciyi yanıltıcı reklam sayılabilir.", "etik", True),
            ("Müşteri yorumlarından gerçek ve güçlü bir mesaj çıkarırım.",
             "Gerçek kanıta dayalı mesaj hem güvenilir hem etkilidir.", "yaratici", False),
            ("Yönetici istediği için kullanırım.",
             "Şirketi hukuki ve itibari riske sokabilir.", "hizli", False)]),
    ],
    "üretim mühendisi": [
        _k("08:30", "Hatalı ürün oranı",
           "Gece vardiyasında bir hattaki hatalı ürün oranı %1'den %6'ya çıkmış.",
           [("Hattı inceleyip makine, malzeme, yöntem ve insan açısından kök neden analizi yaparım.",
             "Kök neden analizi (balık kılçığı, 5 neden) üretim mühendisinin temel aracıdır.", "analitik", False),
            ("Hatayı yayılmadan durdurmak için hattı kısa süre durdurup ürünleri ayırırım.",
             "Hatalı ürünün müşteriye gitmesini önlemek önceliklidir.", "guvenlik", False),
            ("Gece vardiyası operatörleriyle konuşup ne değiştiğini sorarım.",
             "Sahadaki insanlar sorunun ilk tanığıdır.", "iletisim", False)]),
        _k("14:00", "Verimlilik önerisi",
           "Bir operatör, iş istasyonundaki yerleşimi değiştirerek zaman kazanılabileceğini söylüyor.",
           [("Önerisini dinler, küçük bir denemeyle sonucu ölçeriz.",
             "Sürekli iyileştirme (kaizen) çalışanların fikirleriyle büyür.", "ekip", False),
            ("Zaman etüdü yapıp öneriyi verilerle değerlendiririm.",
             "Ölçmeden yapılan değişiklik doğru değerlendirilemez.", "analitik", False),
            ("Mevcut düzen standart olduğu için değiştirmem.",
             "Standartlar önemlidir, ama iyileştirmeye kapalı olmak verimlilik fırsatlarını kaçırır.", "planli", False)]),
    ],
}

# Aynı içeriği kullanan meslek adları
SENARYOLAR["yazılım mühendisi"] = SENARYOLAR["yazılım geliştirici"]
SENARYOLAR["aile hekimi"] = SENARYOLAR["pratisyen hekim"]
SENARYOLAR["şirket avukatı / hukuk müşaviri"] = SENARYOLAR["avukat"]
SENARYOLAR["klinik psikolog"] = SENARYOLAR["psikolog"]
SENARYOLAR["şantiye mimarı"] = SENARYOLAR["mimar"]
SENARYOLAR["yoğun bakım hemşiresi"] = SENARYOLAR["klinik hemşire"]
SENARYOLAR["muayenehane sahibi diş hekimi"] = SENARYOLAR["diş hekimi"]
SENARYOLAR["kurs/etüt öğretmeni"] = SENARYOLAR["lise matematik öğretmeni"]
SENARYOLAR["kurumsal kimlik tasarımcısı"] = SENARYOLAR["grafik tasarımcı"]


# Diğer meslekler (yaklaşık 1000): app/data/meslek_senaryolari.json — aynı biçim, aynı kurallar.
# Elle yazılan SENARYOLAR öncelikli; JSON yalnızca eksik meslekleri tamamlar.
def _json_yukle() -> dict:
    import json
    from pathlib import Path
    yol = Path(__file__).resolve().parent.parent / "data" / "meslek_senaryolari.json"
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


for _ad, _kararlar in _json_yukle().items():
    SENARYOLAR.setdefault(_ad, _kararlar)

KAYNAK_NOTU = ("Karar anları; mesleklerin günlük iş tanımları, MYK ulusal meslek standartları ve iş sağlığı ve güvenliği "
               "ilkeleri gibi genel mesleki bilgi esas alınarak hazırlanmış kurgusal durumlardır. Gerçek kişi, kurum veya "
               "istatistik içermez; rehber öğretmen ve meslek sahipleriyle gözden geçirilmesi önerilir.")


def senaryo_bul(meslek_adi: str) -> list[dict]:
    return SENARYOLAR.get((meslek_adi or "").strip().lower(), [])
