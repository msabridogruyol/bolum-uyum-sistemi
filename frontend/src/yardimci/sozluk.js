// [2026-10-11] Filizyol sözlüğü — öğrencinin karşılaştığı terimler, lise öğrencisinin anlayacağı dilde.
// Kullanım: Sözlük penceresi (Filiz'in yanından açılır, aramalı), Filiz sohbetindeki "… ne demek?" soruları ve Sözlük sayfası (/sozluk).
// [2026-10-11] Metin içinde işaretleme kaldırıldı (görüntüyü bozuyordu); sözlük yalnızca aramayla çalışır.
//
// Alanlar:
//   k   : benzersiz anahtar
//   ad  : sözlükte görünen ad
//   g   : grup (GRUPLAR'dan biri)
//   t   : tanım (1–3 kısa cümle)
//   o   : (isteğe bağlı) örnek
//   es  : aramada bu terimi bulduran başka yazılışlar (ör. "özgeçmiş" → CV, "ortanca" → medyan)
//   tam / bh: eski metin içi işaretleme için kalan alanlar; aramada kullanılmaz.
//
// Kural: tanımlar sistemin gerçekte yaptığıyla uyumlu olmalı; rakam veriliyorsa doğru ve kaynaklı olmalı.

export const GRUPLAR = [
  'Değerlendirme',
  'Özelliklerin',
  'Sınav ve tercih',
  'Hedef ve takip',
  'İş hayatı',
  'Para ve çalışma hakları',
  'Hesap ve gizlilik',
  'Sayılar ve grafikler',
]

export const SOZLUK = [
  // ------------------------------------------------------------------ Değerlendirme
  { k: 'degerlendirme', ad: 'Değerlendirme', g: 'Değerlendirme', es: ['değerlendirme'],
    t: 'Filizyol\'daki sorulara verdiğin cevaplarla seni tanımaya çalışan bölüm. Bir sınav değildir; doğru ya da yanlış cevap yoktur.' },
  { k: 'katman', ad: 'Katman', g: 'Değerlendirme', es: ['katman'],
    t: 'Değerlendirmenin her bir parçası. K1\'den K4\'e kadar dört ana katman, sonunda da K5 (İş türü tercihleri) vardır. Her katman seni başka bir yönden tanır.',
    o: 'K1 seni değerlerinle, K2 kişiliğinle tanır. Dördünü bitirince bölüm önerilerin hazırlanır.' },
  { k: 'k1', ad: 'K1 – Değerler / Motivasyon', g: 'Değerlendirme', es: ['k1'], tam: true, bh: true,
    t: 'Bir işte senin için neyin önemli olduğuna bakar: güvence mi, gelir mi, anlam mı, özgürlük mü?' },
  { k: 'k2', ad: 'K2 – Kişilik ve Çalışma Tarzı', g: 'Değerlendirme', es: ['k2'], tam: true, bh: true,
    t: 'Nasıl bir ortamda rahat ettiğine ve insanlarla nasıl çalıştığına bakar.' },
  { k: 'k3', ad: 'K3 – İş Ortamı ve Yetkinlik', g: 'Değerlendirme', es: ['k3'], tam: true, bh: true,
    t: 'Zor bir durumda nasıl davrandığına bakar: zamanı yönetmek, karar vermek, ekipte çalışmak gibi.' },
  { k: 'k4', ad: 'K4 – Alan Eğilimi ve Düşünme Stili', g: 'Değerlendirme', es: ['k4'], tam: true, bh: true,
    t: 'Hangi konuların seni çektiğine (sayılar, dil, insanlar, tasarım, doğa…) ve nasıl düşündüğüne bakar.' },
  { k: 'k5', ad: 'K5 – İş türü tercihleri', g: 'Değerlendirme', es: ['k5', 'iş türü tercihleri', 'iş türü soruları'], bh: true,
    t: 'İlk dört katman bitince uyumu 70 ve üzerinde çıkan bölümlerinin (en fazla 20) işleriyle ilgili ek sorular. Yalnızca bu bölümleri kendi aralarında yeniden sıralar; listeye yeni bölüm girmez, listeden bölüm çıkmaz.' },
  { k: 'maarif', ad: 'Maarif Modeli karşılığı', g: 'Değerlendirme', es: ['maarif modeli', 'maarif', 'türkiye yüzyılı maarif modeli'],
    t: 'Okulda uygulanan Türkiye Yüzyılı Maarif Modeli\'nde değerler, eğilimler (merak, sorumluluk, empati…) ve beceriler (iş birliği, karar verme…) tanımlanır. Filizyol, özelliklerinin bu kavramlardan hangilerine yakın olduğunu gösterir. Bu yorumsal bir ilişkilendirmedir; puanlarını etkilemez.',
    o: '"Yeniliğe açıklık" özelliğin Maarif Modeli\'nde "Merak" ve "Açık fikirlilik" eğilimleriyle ilişkilidir.' },
  { k: 'tur', ad: 'Tur', g: 'Değerlendirme', es: ['tur', 'turu', 'turun', 'turda', 'turlar', 'turları', 'turdan', 'yeni tur', 'sonraki tur', 'önceki tur'], tam: true,
    t: 'Değerlendirmeyi baştan sona bir kez yapmak. Bir süre sonra yeni bir tur açılır; böylece zamanla nasıl değiştiğini görebilirsin.',
    o: 'Ekim\'de değerlendirmeyi bitirdin; birkaç ay sonra yeni tur açılınca tekrar yapıp neyin değiştiğini görürsün.' },
  { k: 'durum_sorusu', ad: 'Durum sorusu (en çok / en az)', g: 'Değerlendirme', es: ['durum sorusu', 'durum soruları', 'en çok / en az', 'en çok/en az'],
    t: 'Sana bir durum anlatılır ve seçenekler verilir. Sana en çok uyanı ve en az uyanı seçersin. Tek doğru cevap yoktur.',
    o: '"Arkadaşın grup ödevini yapmadı. Ne yaparsın?" — 4 seçenekten sana en çok ve en az uyanı seçersin.' },
  { k: 'guven_puani', ad: 'Güven puanı', g: 'Değerlendirme', es: ['güven puanı', 'güven puanın'],
    t: 'Değerlendirmeyi kurallara uygun, kendi başına yaptığını gösteren puan. Sekme değiştirmek, tam ekrandan çıkmak ya da kopyalamaya çalışmak gibi durumlar bu puanı düşürür. Kamerayı açmamak puanı düşürmez.',
    o: 'Test sırasında 2 kez başka sekmeye geçtiysen güven puanın biraz düşer.' },
  { k: 'uyum', ad: 'Uyum (uyum puanı)', g: 'Değerlendirme', es: ['uyum puanı', 'uyum yüzdesi', 'uyum oranı', 'bölüm uyumu', '% uyum'],
    t: 'Bir bölümün, senin özelliklerine tüm bölümler içinde ne kadar yakın olduğu: 100 sana en yakın bölüm, 0 en uzak bölüm. Başarı ya da kazanma tahmini değildir; "bu yol sana ne kadar benziyor" sorusunun cevabıdır.',
    o: 'Psikoloji için %82 uyum: Psikoloji, tüm bölümler içinde senin özelliklerine en yakın bölümler arasında.' },
  { k: 'profil', ad: 'Profil', g: 'Değerlendirme', es: ['profilin', 'profili', 'profil'], tam: true,
    t: 'Değerlendirmeden çıkan, seni anlatan özelliklerin tamamı. Zamanla değişebilir.' },
  { k: 'ozellik', ad: 'Özellik', g: 'Değerlendirme', es: ['özelliklerin', 'özelliğin', 'özellik'],
    t: 'Değerlendirmenin ölçtüğü her bir yönün. Örneğin "Sorumluluk ve disiplin" ya da "Sayısal ve veri eğilimi". Her birine 0–100 arasında bir puan verilir.',
    o: '"Sorumluluk ve disiplin" puanın 70 ise, bu yön kendi profilinde öne çıkıyor demektir.' },
  { k: 'egilim', ad: 'Eğilim', g: 'Değerlendirme', es: ['eğilim'],
    t: 'Bir şeye kendiliğinden yönelme, ona yatkın olma. "Sayısal eğilim", sayılarla uğraşmayı sevme ve buna yatkın olma demektir.',
    o: 'Boş zamanında hep bir şeyler çiziyorsan tasarım eğilimin olabilir.' },
  { k: 'guclu_yon', ad: 'Güçlü yön', g: 'Değerlendirme', es: ['güçlü yön', 'çok güçlü'],
    t: 'Kendi profilinde öne çıkan özelliklerin (62 ve üstü "Güçlü", 75 ve üstü "Çok güçlü"). Puanlar görelidir: başkalarıyla değil, kendi diğer özelliklerinle karşılaştırılır. Değerlerin (önem verdiklerin) ve duygusal hassasiyet güçlü yön sayılmaz.',
    o: '"Sorumluluk ve disiplin" puanın 80 → kendi profilinde çok öne çıkan bir yönün; planlı ve özenli çalışmak sende belirgin.' },
  { k: 'gelisime_acik', ad: 'Gelişime açık', g: 'Değerlendirme', es: ['gelişime açık'],
    t: 'Puanı 40\'ın altında kalan, kendi profilinde geride kalan özelliklerin. Kötü olduğun anlamına gelmez. Becerilerse çalıştıkça gelişir, kişilik yönlerin küçük alışkanlıklarla esneyebilir, ilgileri deneyerek keşfedersin. Değerlerde ise bu yalnızca o şeyin senin için daha az önemli olduğunu gösterir; geliştirilecek bir eksik değildir.',
    o: '"Zaman yönetimi" puanın 35 → gelişime açık; plan yapmayı deneyerek güçlendirebilirsin.' },
  { k: 'ortanin_ustu', ad: 'Ortanın üstü / Orta', g: 'Değerlendirme', es: ['ortanın üstü'],
    t: '"Ortanın üstü" 50–61, "Orta" 40–49 puan demek. Bu yönlerde davranışın duruma göre değişiyor.' },
  { k: 'boyut', ad: 'Boyut', g: 'Değerlendirme', es: ['boyut'],
    t: 'Bir şeyi anlatırken baktığımız yönlerden biri. Bu sistemde "özellik" ile aynı anlamda kullanılır.' },
  { k: 'yetkinlik', ad: 'Yetkinlik', g: 'Değerlendirme', es: ['yetkinlik'],
    t: 'Bir işi iyi yapabilmek için gereken bilgi, beceri ve tutumun hepsi. Örneğin "ekip çalışması yetkinliği".',
    o: 'Bir mühendisin hesap yapabilmesi bir yetkinliktir; ekiple çalışabilmesi de.' },
  { k: 'motivasyon', ad: 'Motivasyon', g: 'Değerlendirme', es: ['motivasyon'],
    t: 'Seni harekete geçiren, bir işi yapmak için isteklendiren şey.',
    o: 'Yüksek puanlı bir bölüme girme isteği seni ders çalışmaya motive edebilir.' },
  { k: 'bilissel', ad: 'Bilişsel stil', g: 'Değerlendirme', es: ['bilişsel'],
    t: '"Bilişsel", düşünmeyle ilgili demek. Bilişsel stil, bilgiyi nasıl işlediğin ve problemleri nasıl çözdüğündür: adım adım mı, yoksa büyük resme bakarak mı?' },
  { k: 'kisilik', ad: 'Kişilik', g: 'Değerlendirme', es: ['kişilik'],
    t: 'Duygu, düşünce ve davranışlarında zaman içinde görece kararlı kalan özelliklerin bütünü.' },
  { k: 'ihlal', ad: 'Kural dışı durum (ihlal)', g: 'Değerlendirme', es: ['ihlal'],
    t: 'Değerlendirme sırasında kurallara uymayan bir durum. Örneğin başka bir sekmeye geçmek. Güven puanını düşürür.' },

  // ------------------------------------------------------------------ Özelliklerin (K1–K4)
  { k: 'd_guvence', ad: 'Güvence ve istikrar', g: 'Özelliklerin', es: ['güvence ve istikrar'],
    t: 'İşinin sağlam, düzenli ve uzun süreli olmasını önemsemek. Belirsizlik yerine öngörülebilir bir hayatı tercih etmek.' },
  { k: 'd_gelir', ad: 'Yüksek gelir', g: 'Özelliklerin', es: ['yüksek gelir'],
    t: 'Bir işte iyi para kazanmayı önemli bir hedef olarak görmek.' },
  { k: 'd_statu', ad: 'Statü ve prestij', g: 'Özelliklerin', es: ['statü ve prestij', 'statü', 'prestij'],
    t: 'Statü, toplumdaki konum demek; prestij ise saygınlık. Bu özellik, işinin insanlar tarafından saygın görülmesini önemsemeni anlatır.',
    o: 'Toplumda saygın görülen bir mesleği (hâkimlik, doktorluk gibi) seçmek senin için önemliyse bu puanın yüksek çıkar.' },
  { k: 'd_anlam', ad: 'Anlam ve amaç', g: 'Özelliklerin', es: ['anlam ve amaç'],
    t: 'Yaptığın işin sana anlamlı gelmesini, bir amaca hizmet etmesini önemsemek.' },
  { k: 'd_katki', ad: 'Topluma katkı', g: 'Özelliklerin', es: ['topluma katkı'],
    t: 'İşinle başkalarına ve topluma yararlı olmayı önemsemek.' },
  { k: 'd_ozerklik', ad: 'Özerklik ve özgürlük', g: 'Özelliklerin', es: ['özerklik ve özgürlük', 'özerklik'],
    t: 'Özerklik, kendi kararlarını kendin verebilmek demek. Bu özellik, nasıl ve ne zaman çalışacağına kendin karar vermeyi istemeni anlatır.',
    o: 'Saatlerini kendin belirleyebileceğin bir işi, her şeyin söylendiği bir işe tercih etmek.' },
  { k: 'd_estetik', ad: 'Estetik ve yaratıcılık', g: 'Özelliklerin', es: ['estetik ve yaratıcılık', 'estetik'],
    t: 'Estetik, güzellik ve görünüşle ilgili duyarlılık demek. Bu özellik, güzel ve özgün şeyler ortaya koymayı önemsemeni anlatır.' },
  { k: 'p_disadonuk', ad: 'İnsanlarla çalışma (dışadönüklük)', g: 'Özelliklerin', es: ['insanlarla çalışma', 'dışadönüklük', 'dışa dönüklük'],
    t: 'Dışadönüklük, insanlarla birlikte olmaktan enerji almak demek. Kalabalık ve konuşmalı ortamlarda rahat etmeyi anlatır.' },
  { k: 'p_uyum', ad: 'Uyum ve işbirliği', g: 'Özelliklerin', es: ['uyum ve işbirliği'],
    t: 'Başkalarıyla anlaşarak, birlikte iş yapmaya yatkın olmak.' },
  { k: 'p_sorumluluk', ad: 'Sorumluluk ve disiplin', g: 'Özelliklerin', es: ['sorumluluk ve disiplin'],
    t: 'İşini zamanında, planlı ve özenle yapmaya yatkın olmak.' },
  { k: 'p_hassasiyet', ad: 'Duygusal hassasiyet', g: 'Özelliklerin', es: ['duygusal hassasiyet'],
    t: 'Duyguları güçlü yaşamak; stres ve gerginlikten daha çabuk etkilenmek. Başkalarının duygularını fark etmekte de yardımcı olabilir.' },
  { k: 'p_yenilik', ad: 'Yeniliğe açıklık', g: 'Özelliklerin', es: ['yeniliğe açıklık'],
    t: 'Yeni fikirleri, deneyimleri ve farklı yolları denemeye istekli olmak.' },
  { k: 'p_dinamik', ad: 'Dinamik ortam tercihi', g: 'Özelliklerin', es: ['dinamik ortam'],
    t: 'Dinamik, hareketli ve sürekli değişen demek. Bu özellik, her günü aynı geçmeyen, tempolu ortamlarda çalışmayı sevmeni anlatır.' },
  { k: 'p_belirsizlik', ad: 'Belirsizlik ve risk toleransı', g: 'Özelliklerin', es: ['belirsizlik ve risk toleransı', 'risk toleransı', 'tolerans'],
    t: 'Tolerans, bir şeye katlanabilme ve onu kaldırabilme demek. Bu özellik, sonucu belli olmayan durumlarda ve risk alırken ne kadar rahat olduğunu anlatır.',
    o: 'Sonucu belli olmayan yeni bir projeye girmekten çekinmiyorsan bu puanın yüksek çıkar.' },
  { k: 'p_liderlik', ad: 'Liderlik isteği', g: 'Özelliklerin', es: ['liderlik isteği'],
    t: 'Bir grubu yönlendirmek, sorumluluk alıp karar vermek istemek.' },
  { k: 'i_zaman', ad: 'Zaman yönetimi ve önceliklendirme', g: 'Özelliklerin', es: ['zaman yönetimi ve önceliklendirme', 'önceliklendirme'],
    t: 'Önceliklendirme, işleri önem sırasına koymak demek. Bu özellik, zamanını planlamayı ve önce önemli olanı yapmayı anlatır.' },
  { k: 'i_catisma', ad: 'Ekip ve çatışma yönetimi', g: 'Özelliklerin', es: ['ekip ve çatışma yönetimi', 'çatışma yönetimi'],
    t: 'Ekipte anlaşmazlık çıkınca bunu sakin ve adil bir şekilde çözebilmek.' },
  { k: 'i_baski', ad: 'Baskı altında karar verme', g: 'Özelliklerin', es: ['baskı altında karar verme'],
    t: 'Zaman az ya da durum zorken soğukkanlı kalıp doğru kararı verebilmek.' },
  { k: 'i_etik', ad: 'Etik ve dürüstlük', g: 'Özelliklerin', es: ['etik ve dürüstlük', 'etik', 'etiği', 'etiğe'], tam: true,
    t: 'Etik, neyin doğru neyin yanlış olduğuna dair ahlak kuralları demek. Bu özellik, zor durumda bile dürüst ve kurallara uygun davranmayı anlatır.',
    o: 'Sınavda kopya imkânı olsa da kopya çekmemek.' },
  { k: 'i_inisiyatif', ad: 'İnisiyatif alma', g: 'Özelliklerin', es: ['inisiyatif'],
    t: 'Kimse söylemeden, gerektiğinde kendiliğinden harekete geçmek ve sorumluluk almak.',
    o: 'Sınıfta bir sorun gördüğünde kimse söylemeden çözmek için harekete geçmek.' },
  { k: 'i_elestiri', ad: 'Eleştiriye açıklık', g: 'Özelliklerin', es: ['eleştiriye açıklık'],
    t: 'Sana yapılan eleştiriyi kişisel algılamadan dinleyip ondan ders çıkarabilmek.' },
  { k: 'i_strateji', ad: 'Strateji ve iş dünyası yetkinliği', g: 'Özelliklerin', es: ['strateji ve iş dünyası', 'strateji'],
    t: 'Strateji, bir hedefe ulaşmak için yapılan uzun vadeli plan demek. Bu özellik, büyük resmi düşünüp plan yapmayı ve iş dünyasının nasıl işlediğini anlamayı anlatır.',
    o: 'Bir oyunda tek hamleyi değil, 5 hamle sonrasını düşünmek.' },
  { k: 'a_sayisal', ad: 'Sayısal ve veri eğilimi', g: 'Özelliklerin', es: ['sayısal ve veri eğilimi'],
    t: 'Sayılarla, hesapla ve verilerle uğraşmayı sevmek.' },
  { k: 'a_sozel', ad: 'Sözel ve dil eğilimi', g: 'Özelliklerin', es: ['sözel ve dil eğilimi'],
    t: 'Okumayı, yazmayı, dilleri ve kelimelerle düşünmeyi sevmek.' },
  { k: 'a_insan', ad: 'İnsan odaklı eğilim', g: 'Özelliklerin', es: ['insan odaklı eğilim', 'insan odaklı'],
    t: 'İnsanlara yardım etmek, onları anlamak ve onlarla çalışmak isteği.' },
  { k: 'a_tasarim', ad: 'Tasarım ve uzamsal eğilim', g: 'Özelliklerin', es: ['tasarım ve uzamsal eğilim', 'uzamsal'],
    t: 'Uzamsal, boşluk ve şekillerle ilgili demek. Bu özellik, şekilleri zihninde döndürmeyi, çizmeyi, tasarlamayı ve mekânı düşünmeyi sevmeni anlatır.',
    o: 'Bir odayı kafanda farklı şekilde düzenleyebilmek ya da harita okumakta iyi olmak.' },
  { k: 'a_doga', ad: 'Doğa ve laboratuvar eğilimi', g: 'Özelliklerin', es: ['doğa ve laboratuvar eğilimi'],
    t: 'Canlıları, doğayı ve deneyleri merak etmek; laboratuvarda çalışmayı sevmek.' },
  { k: 'a_fiziksel', ad: 'Fiziksel ve hareket eğilimi', g: 'Özelliklerin', es: ['fiziksel ve hareket eğilimi'],
    t: 'Elle, bedenle ve hareket ederek çalışmayı masa başına tercih etmek.' },
  { k: 'a_yapili', ad: 'Yapılandırılmış çalışma stili', g: 'Özelliklerin', es: ['yapılandırılmış çalışma stili', 'yapılandırılmış'],
    t: 'Yapılandırılmış, kuralları ve adımları belli demek. Bu özellik, ne yapacağının açıkça tanımlandığı, düzenli işlerde rahat etmeni anlatır.' },
  { k: 'a_sezgisel', ad: 'Büyük resmi görme (sezgisel stil)', g: 'Özelliklerin', es: ['büyük resmi görme', 'sezgisel'],
    t: 'Sezgisel, ayrıntıdan çok bütüne ve olasılıklara bakan düşünme demek. Bu özellik, parçalar arasındaki bağlantıyı hızlıca görmeni anlatır.',
    o: 'Bir romanın sonunu erkenden tahmin etmek ya da bir konunun ana fikrini hemen yakalamak.' },
  { k: 'a_girisim', ad: 'Girişimcilik ve ikna eğilimi', g: 'Özelliklerin', es: ['girişimcilik ve ikna eğilimi', 'girişimcilik'],
    t: 'Girişimcilik, risk alıp yeni bir iş ya da fikir başlatmak demek. Bu özellik, insanları bir fikre ikna etmeyi ve yeni bir şey kurmayı sevmeni anlatır.' },

  // ------------------------------------------------------------------ Sınav ve tercih
  { k: 'yks', ad: 'YKS', g: 'Sınav ve tercih', es: ['yks'], tam: true,
    t: 'Yükseköğretim Kurumları Sınavı. Üniversiteye girmek için ÖSYM\'nin yaptığı sınav. TYT, AYT ve YDT oturumlarından oluşur.',
    o: 'Haziranda YKS\'ye girersin; puanınla temmuzda tercih yaparsın.' },
  { k: 'tyt', ad: 'TYT', g: 'Sınav ve tercih', es: ['tyt'], tam: true,
    t: 'Temel Yeterlilik Testi. YKS\'nin herkesin girdiği ilk oturumu: Türkçe, matematik, fen ve sosyal bilimler soruları.',
    o: 'TYT\'de 120 soru var; önlisans bölümlerine yalnızca TYT puanıyla girilir.' },
  { k: 'ayt', ad: 'AYT', g: 'Sınav ve tercih', es: ['ayt'], tam: true,
    t: 'Alan Yeterlilik Testleri. Gitmek istediğin bölümün puan türüne göre (sayısal, eşit ağırlık, sözel) çözdüğün YKS oturumu.',
    o: 'Tıp okumak istiyorsan sayısal (SAY) AYT testlerini çözersin.' },
  { k: 'ydt', ad: 'YDT', g: 'Sınav ve tercih', es: ['ydt'], tam: true,
    t: 'Yabancı Dil Testi. Dil bölümlerine (ör. İngilizce öğretmenliği, mütercim-tercümanlık) girmek isteyenlerin girdiği YKS oturumu.' },
  { k: 'osym', ad: 'ÖSYM', g: 'Sınav ve tercih', es: ['ösym'], tam: true,
    t: 'Ölçme, Seçme ve Yerleştirme Merkezi. YKS\'yi yapan ve öğrencileri üniversitelere yerleştiren devlet kurumu.' },
  { k: 'yok_atlas', ad: 'YÖK Atlas', g: 'Sınav ve tercih', es: ['yök atlas'],
    t: 'Yükseköğretim Kurulu\'nun resmî bilgi sitesi. Her bölümün taban puanını, başarı sırasını ve yerleşen öğrencilerin netlerini gösterir.' },
  { k: 'net', ad: 'Net', g: 'Sınav ve tercih', es: ['net', 'neti', 'netin', 'netini', 'netim', 'netler', 'netlerin', 'netlerini', 'netlerim', 'netlerimi', 'netleri', 'netinle', 'netlerinle'], tam: true,
    t: 'Doğru sayından yanlışlarının dörtte birinin çıkarılmasıyla bulunan sayı. Yani 4 yanlış 1 doğruyu götürür.',
    o: '30 doğru, 8 yanlış → 30 − 8 ÷ 4 = 28 net' },
  { k: 'puan_turu', ad: 'Puan türü', g: 'Sınav ve tercih', es: ['puan türü', 'puan türün', 'puan türüne'],
    t: 'Bir bölüme yerleştirmede hangi derslerin daha çok sayıldığını gösterir: SAY (sayısal), EA (eşit ağırlık), SÖZ (sözel) ve DİL (yabancı dil).',
    o: 'Hukuk EA ile, bilgisayar mühendisliği SAY ile öğrenci alır.' },
  { k: 'say', ad: 'SAY (Sayısal)', g: 'Sınav ve tercih', es: ['say'], tam: true, bh: true,
    t: 'Matematik ve fen derslerinin ağırlıklı olduğu puan türü. Mühendislik, tıp gibi bölümler bu puanla öğrenci alır.' },
  { k: 'ea', ad: 'EA (Eşit Ağırlık)', g: 'Sınav ve tercih', es: ['ea', 'eşit ağırlık'], tam: true, bh: true,
    t: 'Matematik ile edebiyat ve sosyal bilimler derslerinin birlikte sayıldığı puan türü. Hukuk, işletme, psikoloji gibi bölümler bu puanla öğrenci alır.' },
  { k: 'soz', ad: 'SÖZ (Sözel)', g: 'Sınav ve tercih', es: ['söz'], tam: true, bh: true,
    t: 'Türk dili ve edebiyatı ile sosyal bilimler derslerinin ağırlıklı olduğu puan türü. Tarih, edebiyat gibi bölümler bu puanla öğrenci alır.' },
  { k: 'dil', ad: 'DİL (Yabancı Dil)', g: 'Sınav ve tercih', es: ['dil puanı'], tam: true,
    t: 'Yabancı Dil Testi\'ne (YDT) göre hesaplanan puan türü. Dil bölümleri bu puanla öğrenci alır.' },
  { k: 'taban_puan', ad: 'Taban puan', g: 'Sınav ve tercih', es: ['taban puan'],
    t: 'Bir bölüme o yıl yerleşen en düşük puanlı öğrencinin puanı. Her yıl değişir.',
    o: 'Bir bölümün taban puanı 450 ise, o yıl 450\'nin altında puanı olan kimse oraya yerleşemedi.' },
  { k: 'basari_sirasi', ad: 'Başarı sırası', g: 'Sınav ve tercih', es: ['başarı sırası', 'başarı sıran', 'taban sıra', 'taban sırası'],
    t: 'Sınavda o puan türünde Türkiye genelinde kaçıncı olduğun. Sayı ne kadar küçükse o kadar iyidir. "Taban sırası", bölüme yerleşen son öğrencinin başarı sırasıdır.',
    o: 'Başarı sıran 25.000 ise, o puan türünde senden önce 24.999 kişi var.' },
  { k: 'kontenjan', ad: 'Kontenjan', g: 'Sınav ve tercih', es: ['kontenjan'],
    t: 'Bir bölümün o yıl alacağı öğrenci sayısı.',
    o: 'Kontenjanı 60 olan bir bölüme o yıl 60 öğrenci yerleşir.' },
  { k: 'tercih', ad: 'Tercih', g: 'Sınav ve tercih', es: ['tercih listesi', 'tercih dönemi', 'tercih sayfası'],
    t: 'Sınavdan sonra girmek istediğin bölümleri öncelik sırasıyla ÖSYM\'ye bildirmen. Yerleştirme bu sıraya ve puanına göre yapılır.',
    o: 'Tercih listenin en üstüne en çok istediğin bölümü, altına diğerlerini sırayla yazarsın.' },
  { k: 'yerlesme', ad: 'Yerleşme', g: 'Sınav ve tercih', es: ['yerleşme', 'yerleşen', 'yerleştin'],
    t: 'Puanına ve tercih sıralamana göre bir bölüme kaydının yapılmaya hak kazanması.',
    o: 'Puanın ilk 3 tercihine yetmedi ama 4.\'ye yetti → 4. tercihine yerleştin.' },
  { k: 'bolum', ad: 'Bölüm', g: 'Sınav ve tercih', es: ['bölüm', 'üniversite bölümü'],
    t: 'Üniversitede okuyacağın alan. Örneğin Psikoloji, Bilgisayar Mühendisliği ya da Hukuk. Filizyol sana uygun bölümleri önerir.',
    o: 'Aynı bölüm (ör. Hukuk) birçok üniversitede vardır; her biri ayrı bir programdır.' },
  { k: 'lisans', ad: 'Lisans', g: 'Sınav ve tercih', es: ['lisans'], tam: true,
    t: 'Üniversitede genellikle 4 yıl süren eğitim (tıp gibi bazı bölümlerde daha uzun). Bitirince lisans diploması alırsın.' },
  { k: 'onlisans', ad: 'Önlisans', g: 'Sınav ve tercih', es: ['önlisans', 'ön lisans'],
    t: 'Genellikle 2 yıl süren yükseköğretim programı (meslek yüksekokulları). TYT puanıyla öğrenci alır.' },
  { k: 'program', ad: 'Program', g: 'Sınav ve tercih', es: ['program kodu'],
    t: 'Bir üniversitedeki belirli bir bölüm seçeneği. Aynı bölümün farklı üniversitelerde, burslu ya da ücretli seçenekleri ayrı programlardır.' },
  { k: 'burs', ad: 'Burs', g: 'Sınav ve tercih', es: ['burslu', 'burs'], tam: true,
    t: 'Öğrenciye karşılıksız verilen destek. Vakıf üniversitelerinde "burslu" program, ücretin tamamını ya da bir kısmını ödemeden okuyabileceğin anlamına gelir.' },
  { k: 'vakif', ad: 'Vakıf üniversitesi', g: 'Sınav ve tercih', es: ['vakıf üniversite', 'vakıf'], tam: true,
    t: 'Bir vakfın kurduğu, kâr amacı gütmeyen, genelde ücretli üniversite. Burslu ve indirimli kontenjanları da olur.' },
  { k: 'obp', ad: 'OBP', g: 'Sınav ve tercih', es: ['obp'], tam: true,
    t: 'Ortaöğretim Başarı Puanı. Lise diploma notundan hesaplanır ve YKS yerleştirme puanına eklenir.',
    o: 'Diploma notun 85 ise OBP\'n 425 olur; bunun belli bir kısmı YKS puanına eklenir.' },
  { k: 'ozel_yetenek', ad: 'Özel yetenek sınavı', g: 'Sınav ve tercih', es: ['özel yetenek'],
    t: 'Beden eğitimi, resim, müzik gibi bölümlerin YKS\'ye ek olarak kendi yaptığı uygulamalı sınav.' },
  { k: 'kktc', ad: 'KKTC', g: 'Sınav ve tercih', es: ['kktc'], tam: true,
    t: 'Kuzey Kıbrıs Türk Cumhuriyeti. Oradaki bazı üniversiteler de YKS ile öğrenci alır.' },
  { k: 'deneme', ad: 'Deneme sınavı', g: 'Sınav ve tercih', es: ['deneme sınavı', 'deneme sonuçları'],
    t: 'YKS\'ye hazırlanmak için gerçek sınav gibi çözülen alıştırma sınavı.' },

  // ------------------------------------------------------------------ Hedef ve takip
  { k: 'hedef_bolum', ad: 'Hedef bölüm', g: 'Hedef ve takip', es: ['hedef bölüm'],
    t: 'Girmek istediğin ve sana özel planı hazırlanan bölüm. Değiştirme hakkın sınırlıdır; hakkın bitince okulun ek hak verebilir.',
    o: 'Hedefini "Bilgisayar Mühendisliği" seçince Koçluğum sayfasında sana özel adımlar çıkar.' },
  { k: 'gelisim_plani', ad: 'Gelişim planı (yol haritası)', g: 'Hedef ve takip', es: ['gelişim planı', 'yol haritası', 'yol haritan'],
    t: 'Hedef bölümüne göre hangi özelliklerini geliştirebileceğini gösteren, adım adım hazırlanmış öneri listesi.',
    o: '"Ekip çalışmanı güçlendir" adımı: bu hafta bir grup projesinde görev al.' },
  { k: 'kocluk', ad: 'Koçluk', g: 'Hedef ve takip', es: ['koçluk'],
    t: 'Hedefine ulaşman için seni yönlendiren, plan yapmana yardım eden destek.' },
  { k: 'egitim_kocu', ad: 'Eğitim koçu', g: 'Hedef ve takip', es: ['eğitim koçu', 'eğitim koçları'],
    t: 'Ders çalışma ve hedef belirleme konusunda seninle görüşen uzman. Görüşme talebin incelenir, uygunsa görüşme günü planlanır.' },
  { k: 'filiz', ad: 'Filiz', g: 'Hedef ve takip', es: ['filiz'], tam: true,
    t: 'Filizyol\'un maskotu ve sana yol gösteren asistanı. Sorularını cevaplar. Önemli kararlarını yine de rehber öğretmeninle ver.' },
  { k: 'seri', ad: 'Seri', g: 'Hedef ve takip', es: ['hafta seri', 'serin'], tam: true,
    t: 'Haftalık görevlerini art arda kaç hafta yaptığını gösterir. Bir haftada en az 2 görevi bitirirsen o hafta seriye sayılır; bir hafta eksik kalırsa seri yeniden başlar.' },
  { k: 'rozet', ad: 'Rozet', g: 'Hedef ve takip', es: ['rozet'],
    t: 'Belirli bir şeyi başardığında kazandığın küçük ödül işareti. Örneğin değerlendirmeni bitirince ya da bir hedef bölüm seçince.' },
  { k: 'haftalik_gorev', ad: 'Haftalık görev', g: 'Hedef ve takip', es: ['haftalık görev'],
    t: 'Her hafta sana verilen küçük ve kısa görevler. Kendini tanımana ve hedefine yaklaşmana yardım eder.' },
  { k: 'yansitma', ad: 'Yansıtma', g: 'Hedef ve takip', es: ['yansıtma'],
    t: 'Yaptığın bir şeyi durup düşünmek: Ne öğrendim, nasıl hissettim, bir dahaki sefere ne yaparım?' },
  { k: 'portfolyo', ad: 'Portfolyo', g: 'Hedef ve takip', es: ['portfolyo', 'e-portfolyo'],
    t: 'Yaptığın etkinlikleri, projeleri, aldığın belgeleri ve başarılarını bir arada topladığın dosya. CV hazırlarken işine yarar.',
    o: 'Katıldığın bilim fuarını, aldığın sertifikayı ve gönüllü çalışmanı portfolyona eklersin.' },
  { k: 'kulup', ad: 'Kulüp', g: 'Hedef ve takip', es: ['kulüp'],
    t: 'Okulundaki ortak ilgi grupları (ör. robotik, tiyatro). Talep gönderirsin; rehber öğretmenin onaylayınca üye olursun.' },
  { k: 'akran', ad: 'Akran', g: 'Hedef ve takip', es: ['akran'],
    t: 'Senin yaşında ve sınıf düzeyindeki diğer öğrenciler.' },
  { k: 'simulasyon', ad: 'Simülasyon (Bir Günümü Yaşa)', g: 'Hedef ve takip', es: ['simülasyon'],
    t: 'Bir mesleği gerçekte yapmadan, örnek durumlar üzerinden denemek. "Bir Günümü Yaşa" o meslekten bir günü karar anlarıyla yaşatır.' },
  { k: 'anket', ad: 'Anket', g: 'Hedef ve takip', es: ['anket'],
    t: 'Okulunun sana sorduğu kısa soru formu. Bazı anketlerde adın görünmez (anonim).' },
  { k: 'anonim', ad: 'Anonim', g: 'Hedef ve takip', es: ['anonim'],
    t: 'Kim olduğunun belli olmaması. Anonim bir ankette cevapların adınla eşleştirilmez.' },

  // ------------------------------------------------------------------ İş hayatı
  { k: 'cv', ad: 'CV (özgeçmiş)', g: 'İş hayatı', es: ['cv', 'özgeçmiş'], tam: true,
    t: 'Eğitimini, deneyimlerini ve becerilerini kısaca anlatan, iş ya da staj başvurusunda verdiğin belge.',
    o: 'Bir yaz stajına başvururken adını, okulunu, becerilerini ve projelerini yazdığın 1 sayfalık belge.' },
  { k: 'ats', ad: 'ATS', g: 'İş hayatı', es: ['ats'], tam: true, bh: true,
    t: 'Aday Takip Sistemi (İngilizce "Applicant Tracking System"). Şirketlerin başvuruları toplayıp CV\'leri otomatik taradığı yazılım. CV\'n bu sistemin okuyabileceği biçimde olmalı.',
    o: 'Şirket "Excel" kelimesini arıyorsa ve CV\'nde yoksa, ATS seni listenin altına atabilir.' },
  { k: 'on_yazi', ad: 'Ön yazı', g: 'İş hayatı', es: ['ön yazı'],
    t: 'CV\'nin yanında gönderilen kısa mektup. Neden bu işe başvurduğunu ve neden uygun olduğunu anlatır.',
    o: '"Robotik kulübünde 2 yıl çalıştım, bu yüzden bu staja uygun olduğumu düşünüyorum" gibi cümleler yazarsın.' },
  { k: 'mulakat', ad: 'Mülakat', g: 'İş hayatı', es: ['mülakat'],
    t: 'İş ya da okul başvurusunda yapılan yüz yüze veya çevrim içi görüşme.',
    o: '"Kendinden bahseder misin?" mülakatta en sık sorulan sorulardan biridir.' },
  { k: 'star', ad: 'STAR yöntemi', g: 'İş hayatı', es: ['star'], tam: true, bh: true,
    t: 'Mülakatta bir deneyimini anlatmak için dört adım: Durum (Situation), Görev (Task), Yaptığın (Action), Sonuç (Result).' },
  { k: 'davranissal', ad: 'Davranışsal soru', g: 'İş hayatı', es: ['davranışsal'],
    t: '"Daha önce şöyle bir durumda ne yaptın?" diye geçmiş deneyimini soran mülakat sorusu.' },
  // [2026-10-13] Mülakat Simülasyonu ve Düşünme Atölyesi terimleri
  { k: 'mulakat_sim', ad: 'Mülakat Simülasyonu', g: 'İş hayatı', es: ['mülakat simülasyonu'],
    t: 'İş Hayatı\'nda, seçtiğin bölüm için canlandırılan kısa iş görüşmesi: iki adaydan daha iyi cevabı seçer, gerekçelerini ve o meslekte işin nasıl yapıldığını görürsün.' },
  { k: 'dusunme_atolyesi', ad: 'Düşünme Atölyesi', g: 'İş hayatı', es: ['düşünme atölyesi'],
    t: 'Her derste ve meslekte işe yarayan düşünme araçlarını (kök neden, korelasyon, algoritma, ikiye bölerek arama…) 5–7 dakikalık alıştırmalarla yaparak öğrendiğin bölüm.' },
  { k: 'kok_neden', ad: 'Kök neden', g: 'İş hayatı', es: ['kök neden'],
    t: 'Bir sorunu gerçekten doğuran, düzeltilince sorunun geri gelmediği neden. Görünen belirtiye değil, ona yol açan şeye odaklanır.',
    o: 'Telefonun şarjı her gün bitiyorsa powerbank yalnızca belirtiyi giderir; şarjı neyin tükettiğini bulup onu değiştirmek kökü çözer.' },
  { k: 'korelasyon', ad: 'Korelasyon', g: 'İş hayatı', es: ['korelasyon'],
    t: 'İki şeyin birlikte artıp azalması. Birinin ötekine yol açtığını tek başına göstermez; ikisini birden etkileyen üçüncü bir etken olabilir.',
    o: 'Dondurma satışı ile güneş yanığı birlikte artar; ikisinin de nedeni sıcak ve güneşli havadır.' },
  { k: 'algoritma', ad: 'Algoritma', g: 'İş hayatı', es: ['algoritma'],
    t: 'Bir işi kimseye bir şey sormadan yapılabilecek kadar açık, sıralı adımlarla tarif etmek. Koşullar ("eğer… ise") ve tekrarlar içerebilir.' },
  { k: 'kendini_sinama', ad: 'Kendini sınama', g: 'İş hayatı', es: ['kendini sınama', 'kendini sınayarak'],
    t: 'Okuduğunu yeniden okumak yerine kitabı kapatıp hatırlamaya çalışmak. Bilgiyi hafızadan çekip çıkarmak, onu genellikle daha kalıcı hâle getirir.' },
  { k: 'staj', ad: 'Staj', g: 'İş hayatı', es: ['staj'],
    t: 'Okurken ya da mezun olurken bir iş yerinde belirli bir süre çalışarak işi öğrenmek.',
    o: 'Mühendislik öğrencileri yazın birkaç hafta bir fabrikada staj yapabilir.' },
  { k: 'referans', ad: 'Referans', g: 'İş hayatı', es: ['referans'],
    t: 'Seni tanıyan ve gerektiğinde senin hakkında bilgi verebilecek kişi (ör. öğretmenin, eski yöneticin).' },
  { k: 'istihdam', ad: 'İstihdam', g: 'İş hayatı', es: ['istihdam'],
    t: 'İnsanların bir işte çalışıyor olması. "İstihdam oranı", mezunların ne kadarının iş bulduğunu gösterir.',
    o: 'Mezunların %80\'i 1 yıl içinde iş bulduysa istihdam oranı %80\'dir.' },
  { k: 'issizlik', ad: 'İşsizlik', g: 'İş hayatı', es: ['işsizlik'],
    t: 'Çalışmak isteyip iş arayan ama iş bulamayan kişilerin durumu.' },
  { k: 'sektor', ad: 'Sektör', g: 'İş hayatı', es: ['sektör'],
    t: 'Aynı alanda çalışan işlerin ve şirketlerin bütünü (ör. sağlık sektörü, yazılım sektörü).' },
  { k: 'kamu', ad: 'Kamu / Özel sektör', g: 'İş hayatı', es: ['kamu', 'özel sektör'], tam: false,
    t: 'Kamu, devlete ait kurumlar (okul, hastane, bakanlık). Özel sektör, kişilere ya da şirketlere ait iş yerleri.' },
  { k: 'serbest', ad: 'Serbest çalışma', g: 'İş hayatı', es: ['serbest çalış', 'serbest meslek'],
    t: 'Bir şirkete bağlı olmadan, kendi müşterilerine iş yaparak çalışmak.' },
  { k: 'tuik', ad: 'TÜİK', g: 'İş hayatı', es: ['tüik'], tam: true,
    t: 'Türkiye İstatistik Kurumu. Kazanç, istihdam gibi resmî istatistikleri yayınlayan devlet kurumu.' },
  { k: 'otomasyon', ad: 'Otomasyon', g: 'İş hayatı', es: ['otomasyon'],
    t: 'Bir işin insan yerine makine ya da yazılım tarafından yapılması.' },
  { k: 'yapay_zeka', ad: 'Yapay zekâ', g: 'İş hayatı', es: ['yapay zekâ', 'yapay zeka'],
    t: 'Öğrenme, dil anlama, karar verme gibi işleri yapabilen bilgisayar sistemleri.' },
  { k: 'meslek_odasi', ad: 'Meslek odası', g: 'İş hayatı', es: ['meslek odası', 'oda kaydı'],
    t: 'Aynı mesleği yapanların üye olduğu kurum (ör. Mühendis Odası, Baro). Bazı meslekleri yapabilmek için odaya kayıt zorunludur.' },
  { k: 'yasal_meslek', ad: 'Yasayla düzenlenen meslek', g: 'İş hayatı', es: ['yasayla düzenlenen'],
    t: 'Yapılabilmesi için yasada belirli bir diploma, izin ya da belge istenen meslek (ör. doktorluk, avukatlık).' },
  { k: 'surdurulebilirlik', ad: 'Sürdürülebilirlik', g: 'İş hayatı', es: ['sürdürülebilir'],
    t: 'Bugünün ihtiyaçlarını, gelecek nesillerin kaynaklarını tüketmeden karşılamak.' },

  // ------------------------------------------------------------------ Para ve çalışma hakları
  { k: 'brut', ad: 'Brüt maaş', g: 'Para ve çalışma hakları', es: ['brüt'],
    t: 'Vergi ve sigorta kesintilerinden ÖNCEKİ maaş. İş ilanlarında ve sözleşmede genelde bu yazar.',
    o: 'İlanda brüt 40.000 TL yazıyorsa, kesintilerden sonra eline daha az geçer.' },
  { k: 'net_maas', ad: 'Net maaş', g: 'Para ve çalışma hakları', es: ['net maaş', 'net ücret', 'eline geçen'],
    t: 'Kesintilerden SONRA hesabına yatan para. Brüt maaştan her zaman daha azdır.',
    o: 'Brüt maaşın 40.000 TL ise, net maaşın kesintilerden sonra daha düşük olur.' },
  { k: 'asgari', ad: 'Asgari ücret', g: 'Para ve çalışma hakları', es: ['asgari ücret'],
    t: 'Yasaya göre bir çalışana ödenebilecek en düşük ücret. Her yıl devlet belirler.',
    o: 'İş yeri sana asgari ücretten daha az ödeyemez.' },
  { k: 'sgk', ad: 'SGK (sigorta)', g: 'Para ve çalışma hakları', es: ['sgk', 'sigorta primi', 'prim'], tam: true,
    t: 'Sosyal Güvenlik Kurumu. Çalışırken maaşından kesilen sigorta primleri sağlık hizmeti ve ileride emeklilik hakkı sağlar.',
    o: 'İlk işine başladığında işveren seni SGK\'ya kaydeder; sigortalı olursun.' },
  { k: 'vergi', ad: 'Vergi dilimi', g: 'Para ve çalışma hakları', es: ['vergi dilimi', 'matrah', 'kümülatif'],
    t: 'Gelir arttıkça daha yüksek oranda vergi ödenir; her oran bir "dilim"dir. Matrah, verginin hesaplandığı tutardır. Kümülatif, yıl başından beri toplanan demektir.' },
  { k: 'bordro', ad: 'Bordro', g: 'Para ve çalışma hakları', es: ['bordro'],
    t: 'Maaşının brüt tutarını, kesintileri ve eline geçen net tutarı gösteren belge.' },
  { k: 'kidem', ad: 'Kıdem tazminatı', g: 'Para ve çalışma hakları', es: ['kıdem'],
    t: 'Belirli bir süre çalıştıktan sonra, yasada sayılan durumlarda işten ayrılınca işverenin ödediği para.',
    o: 'Bir iş yerinde 5 yıl çalıştıktan sonra emekli olursan kıdem tazminatı alırsın.' },
  { k: 'ihbar', ad: 'İhbar süresi ve tazminatı', g: 'Para ve çalışma hakları', es: ['ihbar', 'bildirim süresi'],
    t: 'İşi bırakmadan ya da işten çıkarmadan önce karşı tarafa önceden haber verme süresi. Bu süreye uyulmazsa ödenen paraya ihbar tazminatı denir.' },
  { k: 'fesih', ad: 'Fesih', g: 'Para ve çalışma hakları', es: ['fesih'],
    t: 'Bir sözleşmeyi sona erdirmek.' },
  { k: 'deneme_suresi', ad: 'Deneme süresi', g: 'Para ve çalışma hakları', es: ['deneme süresi'],
    t: 'İşe başladıktan sonraki ilk dönem. Bu sürede iki taraf da sözleşmeyi beklemeden bitirebilir; çalıştığın günlerin ücreti yine ödenir.' },
  { k: 'toplu_sozlesme', ad: 'Toplu iş sözleşmesi', g: 'Para ve çalışma hakları', es: ['toplu iş sözleşmesi'],
    t: 'Sendika ile işveren arasında, çalışanların ücret ve haklarını belirlemek için yapılan anlaşma.' },
  { k: 'ekstre', ad: 'Ekstre', g: 'Para ve çalışma hakları', es: ['ekstre'],
    t: 'Kredi kartıyla ya da hesabınla yaptığın harcamaları ve ödemen gereken tutarı gösteren dönem özeti.' },
  { k: 'kredi_notu', ad: 'Kredi notu', g: 'Para ve çalışma hakları', es: ['kredi notu'],
    t: 'Borçlarını zamanında ödeyip ödemediğine göre bankaların sana verdiği puan.' },
  { k: 'vade', ad: 'Vade farkı', g: 'Para ve çalışma hakları', es: ['vade farkı', 'vade'], tam: true,
    t: 'Vade, ödemenin yapılacağı zaman. Vade farkı, ödemeyi ileriye ya da taksitlere bölünce fiyata eklenen ek tutar.' },

  // ------------------------------------------------------------------ Hesap ve gizlilik
  { k: 'kvkk', ad: 'KVKK', g: 'Hesap ve gizlilik', es: ['kvkk'], tam: true,
    t: 'Kişisel Verilerin Korunması Kanunu. Bilgilerinin nasıl toplanacağını, saklanacağını ve kimlerle paylaşılabileceğini belirleyen yasa.',
    o: 'Okulun senin bilgilerini başka bir şirketle izinsiz paylaşamaz.' },
  { k: 'kisisel_veri', ad: 'Kişisel veri', g: 'Hesap ve gizlilik', es: ['kişisel veri', 'kişisel bilgi'],
    t: 'Seni tanımlayan her bilgi: adın, e-postan, cevapların, sonuçların gibi.' },
  { k: 'acik_riza', ad: 'Açık rıza', g: 'Hesap ve gizlilik', es: ['açık rıza'],
    t: 'Bir konuda bilgilendirildikten sonra kendi isteğinle verdiğin açık izin. İstediğin zaman geri alabilirsin.',
    o: '"Sonuçlarım rehber öğretmenimle paylaşılsın" kutusunu işaretlemen bir açık rızadır.' },
  { k: 'aydinlatma', ad: 'Aydınlatma metni', g: 'Hesap ve gizlilik', es: ['aydınlatma metni'],
    t: 'Bilgilerinin hangi amaçla, nasıl kullanıldığını ve haklarını anlatan metin.' },
  { k: 'iki_adim', ad: 'İki adımlı doğrulama', g: 'Hesap ve gizlilik', es: ['iki adımlı', '2 adımlı'],
    t: 'Girişte şifrenden sonra e-postana gelen kodu da yazman. Şifren başkasının eline geçse bile hesabını korur.' },
  { k: 'gecici_sifre', ad: 'Geçici şifre', g: 'Hesap ve gizlilik', es: ['geçici şifre'],
    t: 'Okulunun ilk girişin için verdiği şifre. İlk girişte kendi şifreni belirlemen istenir.' },
  { k: 'koordinator', ad: 'Koordinatör', g: 'Hesap ve gizlilik', es: ['koordinatör'],
    t: 'Bir işin düzenli yürümesini sağlayan ve kişiler arasında bağlantıyı kuran sorumlu kişi.' },

  // ------------------------------------------------------------------ Sayılar ve grafikler
  { k: 'ortalama', ad: 'Ortalama', g: 'Sayılar ve grafikler', es: ['ortalama'],
    t: 'Sayıların toplamının sayı adedine bölünmesi. Grubun genel düzeyini gösterir.',
    o: '70, 80 ve 90 → ortalama (70+80+90) ÷ 3 = 80.' },
  { k: 'medyan', ad: 'Medyan (ortanca)', g: 'Sayılar ve grafikler', es: ['medyan', 'ortanca'],
    t: 'Sayılar küçükten büyüğe dizilince tam ortada kalan değer. Çok uç değerlerden ortalama kadar etkilenmez.',
    o: '5 kişinin maaşı: 20, 22, 25, 30, 90 bin TL → medyan 25 bin TL (ortalama ise 37,4 bin TL).' },
  { k: 'yuzdelik', ad: 'Yüzdelik dilim', g: 'Sayılar ve grafikler', es: ['yüzdelik'],
    t: '"İlk %10" gibi, bir grubun içinde nerede olduğunu gösterir. Örneğin ilk %10\'luk dilim, en yüksek puanlı onda bir kişidir.',
    o: 'İlk %10\'luk dilimdeysen, 100 kişiden yalnızca 10\'u senden iyi ya da senin kadar.' },
  { k: 'isabet', ad: 'İsabet', g: 'Sayılar ve grafikler', es: ['isabet'],
    t: 'Çözdüğün sorular içinde doğru cevapladıklarının oranı.' },
  { k: 'tahmin', ad: 'Tahmin', g: 'Sayılar ve grafikler', es: ['tahmini', 'tahmin'], tam: true,
    t: 'Kesin bilgi değil, eldeki verilere göre yapılan yaklaşık hesap. Filizyol tahmin olan sayıları bu kelimeyle işaretler.' },
]

const _harita = new Map(SOZLUK.map((x) => [x.k, x]))
export const terimBul = (k) => _harita.get(k)

// ------------------------------------------------------------------ [2026-10-11] Genişletilmiş sözlük
// Öğrenci sistemde okuduğu hiçbir kelimede takılmasın diye sözlük üç kaynaktan oluşur:
//  1. SOZLUK (yukarıda) — sistemin kendi terimleri (değerlendirme, net, taban puan…)
//  2. sozlukGenis.json — bölüm açıklamaları, öğrenci ekranları, sorular ve özellik açıklamalarında geçen ~3.300 terim
//     (alan terimleri, ders adları, kısaltmalar, resmî/akademik kelimeler). Lise düzeyinde yazıldı ve bağımsız olarak
//     gözden geçirildi; sayı / maaş / istatistik içermez. Sıkı biçim: [ad, grupNo, tanım, örnek, [yazılışlar]].
//  3. GET /ogrenci/sozluk/ek — veritabanından 301 bölüm (özet), bölümlerdeki meslekler ve ölçülen özellikler.
// 2 ve 3 yalnızca sözlük ilk kez kullanıldığında yüklenir (ana paket büyümesin).
const baslik = (ad) => String(ad || '').toLocaleLowerCase('tr').split(' ')
  .map((w) => (['ve', 'ile', 'veya'].includes(w) ? w : w.charAt(0).toLocaleUpperCase('tr') + w.slice(1))).join(' ')

export const EK_GRUPLAR = ['Bölümler', 'Meslekler']
let EK = []
let _yukleme = null
let _genisGruplar = []
const _dinleyiciler = new Set()

export function sozlukYukle() {
  if (_yukleme) return _yukleme
  _yukleme = Promise.all([
    import('./sozlukGenis.json').then((m) => m.default || m).catch(() => null),
    import('../api/client').then(({ api }) => api.sozlukEk()).catch(() => null),
  ]).then(([genis, ek]) => {
    const liste = []
    if (genis) {
      _genisGruplar = genis.gruplar
      genis.terimler.forEach(([ad, g, t, o, es], i) => liste.push({ k: `g${i}`, ad, g: genis.gruplar[g], t, o: o || undefined, es }))
    }
    if (ek) {
      ek.bolumler.forEach((b) => liste.push({ k: `b${b.id}`, ad: baslik(b.ad), g: 'Bölümler', t: b.t, tur: 'bolum', bolumId: b.id, bolumAd: b.ad }))
      ek.meslekler.forEach((m, i) => liste.push({ k: `m${i}`, ad: m.ad, g: 'Meslekler', t: m.t, tur: 'meslek',
        bolumler: m.bolumler.map((b) => ({ id: b.id, ad: baslik(b.ad), hamAd: b.ad })) }))
      ek.ozellikler.forEach((x, i) => liste.push({ k: `o${i}`, ad: x.ad, g: 'Özelliklerin', t: `${x.t.charAt(0).toLocaleUpperCase('tr')}${x.t.slice(1)}.`.replace(/\.\.$/, '.'),
        tur: 'ozellik', katman: x.katman }))
    }
    // Ana sözlükteki bir terimle aynı adı taşıyan ek terim gösterilmez (sistemin kendi tanımı önceliklidir)
    const ana = new Set(SOZLUK.flatMap((t) => [t.ad, ...(t.es || [])].map(sade)))
    EK = liste.filter((t) => t.tur === 'bolum' || t.tur === 'meslek' || !ana.has(sade(t.ad)))
    EK.forEach(hazirla)
    _dinleyiciler.forEach((f) => f())
    return EK.length
  })
  return _yukleme
}
export const sozlukYuklendiMi = () => EK.length > 0
export function sozlukDinle(f) { _dinleyiciler.add(f); return () => _dinleyiciler.delete(f) }
export const tumGruplar = () => [...GRUPLAR, ..._genisGruplar.filter((g) => !GRUPLAR.includes(g)), ...EK_GRUPLAR]
export const tumTerimler = () => [...SOZLUK, ...EK]
export const toplamTerim = () => SOZLUK.length + EK.length

// ------------------------------------------------------------------ Arama
const kucuk = (x) => (x || '').toLocaleLowerCase('tr-TR').trim()
const sade = (x) => kucuk(x).replace(/[^\p{L}\p{N} ]/gu, ' ').replace(/\s+/g, ' ').trim()
// parantez içi açıklama aramada ayrı ad sayılır: "KPSS (Kamu Personeli Seçme Sınavı)" → "kpss", "kamu personeli…"
function hazirla(t) {
  if (t._adlar) return t
  const ad = sade(t.ad)
  const parca = /^(.*?)\s*\((.*?)\)\s*$/.exec(t.ad)
  t._ad = ad
  t._adlar = [...new Set([ad, ...(parca ? [sade(parca[1]), sade(parca[2])] : []), ...(t.es || []).map(sade)].filter(Boolean))]
  t._t = sade(t.t)
  return t
}
SOZLUK.forEach((t) => { hazirla(t); t._ana = true })

// Sorguya en uygun terimleri sırayla döndürür: ad/yazılış başta eşleşmesi > içinde geçmesi > tanımda geçmesi
function puanla(q, t) {
  const adlar = t._adlar
  let p = 0
  if (adlar.some((a) => a === q)) p = 100
  else if (adlar.some((a) => a.startsWith(q))) p = 80
  else if (adlar.some((a) => a.split(' ').some((w) => w.startsWith(q)))) p = 65
  else if (adlar.some((a) => a.includes(q))) p = 50
  else if (q.length >= 3 && adlar.some((a) => q.startsWith(a) && a.length >= 3)) p = 45   // "taban puanı" → taban puan
  else if (q.length >= 4 && t._t.includes(q)) p = 20
  if (!p) return 0
  if (t._ad.startsWith(q)) p += 5               // aynı puanda adı eşleşen öne
  if (t._ana) p += 2                            // sistemin kendi terimi önce
  if (t.tur === 'bolum' && p >= 80) p += 1       // bölüm adı tam yazıldıysa bölüm kartı üstte
  return p
}

export function sozlukAra(sorgu, enFazla = 30) {
  const q = sade(sorgu)
  if (!q) return []
  return tumTerimler().map((t) => [puanla(q, t), t]).filter((x) => x[0])
    .sort((a, b) => b[0] - a[0] || a[1].ad.length - b[1].ad.length || a[1].ad.localeCompare(b[1].ad, 'tr')).slice(0, enFazla).map((x) => x[1])
}

// Filiz sohbeti: "taban puan ne demek?", "ATS nedir", "net ne anlama geliyor" → sözlükteki terim (yoksa null)
// [2026-10-11] Bölüm ve meslek adları Filiz'e bırakılır (bölüm sorusu genelde "ne iş yapar, nasıl bir bölüm" demektir).
export function sozlukSorusu(metin) {
  const m = /^\s*(.{2,60}?)\s*(?:ne demek(?:tir)?|nedir|ne anlama gel\w*|anlamı ne|ne anlama gelir)\s*\??\s*$/iu.exec(metin || '')
  if (!m) return null
  const q = sade(m[1].replace(/['’]?(?:nın|nin|nun|nün|ın|in|un|ün)$/iu, ''))
  let en = null, enPuan = 0
  for (const t of tumTerimler()) {
    if (t.tur === 'bolum' || t.tur === 'meslek') continue
    const p = puanla(q, t); if (p > enPuan) { en = t; enPuan = p }
  }
  return enPuan >= 80 ? en : null   // yalnızca güçlü eşleşmede sözlük cevaplar; yoksa soru Filiz'e gider
}
