"""
AI Koçluk Asistanı — Servis Katmanı

Tasarım prensipleri:
- Asistan, sistemin KENDİ hesapladığı verileri (gap_analizi_hesapla,
  aktif_hedef_getir — koclugu_servisi.py'den) YORUMLAR/ANLATIR; kendi
  başına farklı bir tavsiye üretmez, sistemle çelişmez.
- Ton: sohbet tarzı, koç gibi, madde madde/liste halinde DEĞİL. Kendi
  kişisel anısı/deneyimi uydurmaz.
- Maliyet ve kalite kontrolü için "oturum" mantığı: bir oturum belirli
  sayıda turdan sonra kapanır, kapanırken kısa bir özet çıkarılır. Yeni
  oturumda ham geçmiş değil, bu özet + öğrencinin GÜNCEL profili kullanılır.
- API anahtarı henüz girilmemişse (OPENAI_API_KEY yok), sistem çökmez —
  kullanıcıya "asistan henüz aktif değil" mesajı döner. Anahtar eklenince
  hiçbir kod değişikliği gerekmeden çalışmaya başlar.
"""
import os
import re
from sqlalchemy.orm import Session

from app.models import Ogrenci, Bolum, GelisimKaynakOnerisi
from app.core.katman_servisi import son_tur_getir, IsKuraliHatasi
from app.core.koclugu_servisi import aktif_hedef_getir, gap_analizi_hesapla, gap_kategorisi

MAKSIMUM_TUR = 20  # bir oturumda bu kadar (öğrenci+asistan) mesajdan sonra oturum otomatik kapanır
MODEL_ADI = os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini"  # Render ortam değişkeniyle değiştirilebilir
GUNLUK_MESAJ_LIMITI_VARSAYILAN = 40  # [2026-10-31] Tam paket / okulsuz öğrenci günlük yapay zekâ mesajı (parametre: filiz_gunluk_mesaj_limiti)

# [2026-10-04] Öğrenci güvenliği: kullanıcılar reşit olmayan öğrenciler. Kendine zarar / intihar / istismar
# ifadesi geçen mesajlarda model ÇAĞRILMAZ; her zaman aynı, güvenli ve yönlendirici cevap verilir
# (anahtar olmasa da çalışır). Daha örtük durumlar için sistem promptunda ayrıca kural var (madde 8).
KRIZ_IFADELERI = (
    "intihar", "ölmek istiyorum",   # "kendimi öldür" → desen ("kendimi öldüresiye çalıştım" kriz değil) "olmek istiyorum",
    "yaşamak istemiyorum", "yasamak istemiyorum", "hayatıma son", "hayatima son", "canıma kıy", "canima kiy",
    "kendime zarar", "kendimi kesiyorum",   # "kendimi kes" → desen: "kendimi kesin olarak" kriz değil "bileklerimi", "yok olmak istiyorum", "her şeye son",
    "bana şiddet", "bana siddet", "taciz", "istismar", "beni dövüyor", "beni dovuyor",
    # [2026-10-19] denetim: zorbalık, tehdit ve örtük çaresizlik ifadeleri
    "zorbalık", "zorbalik", "zorbalığa", "zorbaliga", "beni tehdit", "kendime bir şey yap", "kendime bir sey yap",
    "dayanamıyorum artık", "dayanamiyorum artik", "depresyondayım", "depresyondayim",
)
KRIZ_YANITI = (
    "Bunu benimle paylaştığın için teşekkür ederim, yazdıklarını çok önemsiyorum. Şu an yaşadığın şey "
    "bir kariyer sohbetinden çok daha önemli ve bu konuda sana gerçek bir insanın destek olması gerekiyor. "
    "Lütfen hemen güvendiğin bir yetişkinle konuş: ailenden biri, rehber öğretmenin ya da okulundaki psikolojik "
    "danışman. Kendini tehlikede hissediyorsan ya da biri sana zarar veriyorsa 112 Acil Çağrı'yı arayabilirsin; "
    "ALO 183 Sosyal Destek Hattı da 7/24 açık. Yalnız değilsin ve yardım istemek çok cesurca bir adım. 💚"
)


def _sade(metin: str) -> str:
    return " ".join(str(metin).replace("İ", "i").replace("I", "ı").lower().split())


def _ascii(metin: str) -> str:
    t = str(metin or "").replace("İ", "i").replace("I", "ı").lower().replace("i̇", "i")
    t = t.translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


# [2026-11-02 kör test] Kriz ifadeleri yalnızca birkaç kalıpla aranıyordu; örtük, çekimli ve dolaylı ifadeler kaçıyordu.
# İki kör ölçüm: Filiz'e sorulan 10 kriz cümlesinin 5'i, ayrı bir 90 cümlelik kriz setinin ise yalnızca 35'i yakalanıyordu
# ("Ölsem kimse fark etmez", "Tükendim, devam edemem artık", "Herkese teşekkürler, bu benim son mesajım",
# "babam beni kemerle dövdü yine", "internetten tanıştığım biri çıplak foto istiyor").
# Desenler Türkçe karaktersiz sadeleştirilmiş metinde, sözcük başında aranır; çekim ekleri desenin içindedir.
# Kural: yanlış alarm, kaçırılan krizden her zaman iyidir (yanlış alarmda öğrenci yalnızca nazik bir destek mesajı görür).
# Tek istisna akademik/meslek bağlamı: "intihar oranları üzerine araştırma", "istismara uğramış çocuklarla çalışmak".
_KISI = r"(babam|annem|abim|ablam|uvey \w+|enistem|amcam|dayim|kocam|sevgilim|ogretmen\w*|komsu\w*|sofor\w*|biri|bir grup|grup|cocuk\w*|onlar)"
_KRIZ_DESENLERI = [re.compile(r"(?<![a-z0-9])" + d) for d in (
    # açık intihar düşüncesi ya da hazırlık
    r"intihar", r"kendimi( \w+){0,2} (oldur(?!esiye)|as(ar|mak|may|acag|sam|tim)|at(ar|mak|acag|sam)|bitir|yok ed)",
    r"(olmek|olmeyi) (ist|dusun)", r"(keske )?olsem (mi|keske|iyi|rahat|kurtul)", r"keske olsem", r"olup gitse", r"oleyim\b", r"olmem lazim", r"olum\w* (cok )?dusun",
    r"(keske|hic) dogmasa", r"dogmamis olmay", r"yasamak (istemi|zorunda degil)", r"yasamaya (devam etmek )?istemi",
    r"(yasama|yasamak|hayat)\w* (bir |bi |hicbir )?(anlami|sebeb\w*) (yok|kalma|kalmi|kalmay)", r"yasamak icin (bir |bi |hicbir )?sebeb",
    r"(hayat|yasam)\w* son (ver|veri)", r"hayatima son", r"canima kiy", r"her seye son", r"her sey bitsin",
    r"her seyi bitir(mek isti|ecegim|sem|eyim)", r"bu hayati bitir",
    r"(bir daha |bi daha )?(hic )?uyanma(mak|sam|yayim|mayi)", r"sonsuza (kadar|dek) uyu", r"yok ol(mak|sam|ayim|up gitsem)",
    r"ortadan kaybol(mak|sam|ayim)", r"bu dunyadan git", r"(beni )?(bu )?dunyaya baglayan", r"bensiz (herkes |daha |dunya |her sey |hayat )*(mutlu|iyi|rahat|kolay)",
    r"kimse (beni )?(ozlemez|aramaz)", r"(olsem|gitsem|olmasam) (kimse|herkes|daha)", r"kimse fark etmez", r"kimsenin umrunda (degil|olmaz)",
    r"(kopru|cati|cam|bina|balkon|yuksek)\w* (den |dan )?atla(mak isti|mayi|yacag|sam|yip|yim)", r"(cok|kutu kutu|bir avuc|butun) ilac",
    r"ilac\w* (biriktir|hepsini|icip|icsem|icerek|icecem|icecegim)", r"\bip (sakl|ald|hazir)", r"kaza olsa (da|ta) gitsem",
    r"gelecek (yili|seneyi|yazi|ayi) gor(meyecegim|ecegimi sanmiyorum|emeyecegim)", r"(benden|bensiz) kurtul",
    r"(bir |bi )?yuk (gibi|oldugumu|oluyorum)", r"yukten baska", r"(yasamak|yasamaktan|hayattan|nefes almaktan) yoruldum",
    r"tukendim", r"devam edemem", r"cabalamayi birak", r"savasacak guc", r"(bir|bi|hic)\s?seyin duzelmeyecegi",
    r"her seyi birak(mak isti|iyorum)", r"kendimi de birak",
    # yaşamın sonunu ima eden ifadeler (kariyer sorusunun içinde de olabilir)
    r"yasamayacag", r"(uzun|fazla) (kalmayacag|yasamayacag)", r"dayanabilecegimi sanmiyorum", r"(bi|bir) daha sabah olmasin",
    r"sabah olmasin", r"(artik )?bitti her sey", r"her sey bitti artik", r"ben yokken", r"beni affed", r"ben gidiyorum.*hosca",
    r"hosca ?kal(in)? herkes", r"herkes(e)? hosca ?kal", r"yoruldum (yasamaktan|hayattan)", r"ilac kutusu",
    r"(anneme|babama|aileme|herkese) (bir |bi )?mektup yazdim", r"(iyi bak(in|sin)|bakin)\w*.*benden sonra|benden sonra.*(iyi bak|bakin)",
    r"var olmasa(ydim|m)", r"(seneye|yarin|haftaya|gelecek yil)\w* (burada|hayatta) ol(mayacag|acagimi sanmiyorum)",
    r"burada olacagimi sanmiyorum", r"fisi (tamamen )?cek", r"(yarin|bu aksam|bu gece)( \w+){0,5} (her sey )?bitmis olacak",
    r"yarin yazmazsam", r"gitmem gereken yere", r"artik( \w+)? gidecegim\b",
    # veda
    r"son mesajim", r"son kez yaziyorum", r"son konusmamiz", r"veda ettim", r"burada olmayacagim", r"bundan sonra gerek kalmayacak",
    r"(bir |bi )?daha yaz(mayacag|micam|mayacam)", r"(esyalarimi|seylerimi|kedimi|kopegimi|sifrelerimi|kiyafetlerimi)( \w+){0,4} (verdim|biraktim)",
    r"ihtiyacim (olmayacak|olmicak)", r"bakam(icam|ayacagim)", r"mektup yazdim.*(bulunca|anlar)", r"artik her sey hazir",
    # kendine zarar verme
    r"kendime( \w+){0,2} (zarar|bir sey yap|bisey yap|kiy)",
    r"kendimi( \w+){0,2} (kes(tim|iyor|ecek|mek|meyi|sem|erim|ip)|yarala|jilet|cizi|yak(tim|iyor|mak|acak)|cezalandir)",
    r"(kolumu|kollarimi|bacagimi|bacaklarimi|bilegimi|bileklerimi)( \w+){0,1} (kes|ciz)", r"izler\w* (artik )?gecm", r"bilek(ler)?imi", r"jilet",
    r"kesiklerim", r"kesik izler", r"(kolumda|kollarimda|bacagimda|bacaklarimda|bileklerimde) (\w+ )?iz", r"kendime (vur|eziyet)",
    r"(duvara )?kafami (duvara )?vur(uyorum|dum|uyom|du|dular|uyor)", r"bilerek (yemek )?yemiyorum",
    r"kendimi (acit|incit)", r"(kollarim|bileklerim|bacaklarim)\w* (kimse )?gorme", r"uzun kollu giy",
    r"(izleri|yaralari|kesikleri)\w* (nasil )?sakla", r"(kollarimdaki|bileklerimdeki|bacaklarimdaki) (iz|yara|kesik)",
    # şiddet, istismar, zorbalık, tehdit
    r"taciz", r"istismar", r"tecavuz", r"cinsel", r"beni( \w+){0,3} dov", r"(bizi|hepimizi|annemi|kardesimi)( \w+){0,2} dov",
    r"dov(uyor|uyo|du|duler|dular|ecek|eceklermis|erler)\b", r"dayak (yi|ye|at)", r"(cok|hep|surekli|yine) vur(uyo|uyor|du)",
    r"bana (siddet|vuruyor|vurdu|el kaldir|zarar veriyor)", r"beni (kemerle|sopayla|terlikle)", r"kemerle",
    r"tekmel(iyo|iyor|edi)", r"sikistirip", r"(odaya|odama|eve) kilitle", r"(bicak|silah|tabanca)\w*( \w+){0,4} tehdit",
    r"tehdit (etti|ediyor|ediyo|ediyorlar)", r"oldurmekle", r"(seni|beni|hepimizi|onu) oldurecegim", r"oldurecegim diye", r"oldurecekmis",
    r"(herkesi|hepimizi) vur(acag|acak)", r"silah getir", r"adresimi (de )?biliyo", r"zorbalik", r"zorbaliga", r"beni tehdit",
    r"uygunsuz (sey|mesaj|foto|istek|soz)", r"ciplak", r"ifsa", r"(fotograf|foto)\w*( \w+){0,2} (yaymak|yayacag|ifsa)",
    r"(garip|kotu|tuhaf) (sekilde )?dokun", r"dokun(maya|uyo|uyor|du|acak)", r"odama (gece )?gir(iyo|iyor|di)",
    r"rahatsiz edici", r"zorla (nisan|evlen|ople|dokun|elle|bir sey|bisey|seyler)", r"(nisanla|evlendir)\w* (istiyo|istiyor)",
    r"kilitli(yor|yo)", r"yemek vermi(yor|yo)", r"tokat at", r"yumruk at", r"(kafama|yuzume) (vur|tokat|yumruk)", r"elles",
    r"yayacak", r"yaymakla", r"(foto|fotograf|video)\w*( \w+){0,3} (yay|ifsa)", r"sir aramizda", r"\d{2} yasinda oldugumu",
    r"gebert", r"canini yak", r"(oldurecegim|oldururum|oldurcem|olduruce)", r"silah\w*( \w+){0,3} okul", r"okula (goturup|getirip)",
    r"kendimi tutamiyorum", r"mor(luk|armis|ardi|ariyor)",
    # [kör set 4] şantaj, gizli ilişki, veda, kendine zarar, şiddet: kavram düzeyinde genelleştirilmiş kalıplar
    r"yoksa( \w+){0,4} (herkes gor|paylas(acak|acag|ir|ilacak|maya)|yay(acak|acag|ar\b|arim|arlar|ilacak|mak|maya)|at(acak|cak)|yolla(yacak|r\b|ycak)|gonder(ecek|ir\b|icek))",
    r"(gondermezsem|atmazsam|vermezsem)( \w+){0,4} (yay(acak|acag|ar\b|arlar|ilacak|mak)|at(acak|cak)|yolla|gonder|paylas)",
    r"(ozel|mahrem|ciplak)\w* (foto|fotograf|video|goruntu)", r"(ikimizin|aramizin|bizim) sirr", r"sirrimiz", r"yalniz kalalim",
    r"\d{2} yasindayim", r"hakkini(zi)? helal", r"beni unutma", r"artik hazirim", r"(bir|bi) daha gormeyeceksin",
    r"esyalarimi (dagit|ver)", r"(kalmicam|kalmayacagim) zaten", r"ortadan kaybolmam", r"fisimi cek", r"sonunu kendim yaz",
    r"kolumdaki iz", r"canim yanmazsa", r"kendime bi\w* (seyler|sey) yap", r"kolunu kir", r"(kardesime|anneme|bana) vurdu",
    r"esya\w* firlat", r"tekme tokat", r"dovul(uyorum|dum)", r"kafami (dolaba|duvara|kapiya|yere) carp", r"burnum kana",
    r"(bir sey|bisey) yapacagimdan korkuyorum", r"zarar vermeyi planl", r"okula (bisiyle|biseyle|bir seyle) gel", r"(bize|bana|anneme|kardesime) el kaldir", r"eve gitmekten kork",
    r"kapi sesi\w*.*titre", r"kimseye (soylememi|anlatmamami|soylemememi|anlatma)", r"(sir|gizli)\w* (tut|kalsin|kalmasini)",
    r"gizlice bulus", r"kamera\w* acmami", r"bedenim\w* (ilgili|hakkinda)", r"(bana|beni) sey yap", r"\d{2} yasinda\w*.*(foto|bulus|gizli|kamera)",
    r"(foto|fotograf|video)\w*.*\d{2} yasinda", r"(para|harclik)\w* (vermezsem|istiyor)", r"herkese yay", r"herkes gorecek",
    r"ekran goruntu\w*( \w+){0,3} (atacag|yayacag|gonderecek)", r"yere yatirip", r"merdivenden it", r"itip kak",
    r"(kaydedip|cekip) dov", r"beni bekliyorlar",
    r"(onu|ona|birini|birine|hepsini|cocugu|cocuga|kizi|babami|annemi)( \w+){0,3} (yaralayacag|zarar verecegim|oldur|bitirecegim)",
    r"zarar (verecegim|vermek isti|vermenin yolu)", r"oldurmek isti", r"okula (bisey|bir sey|silah)\w* getir", r"hepsi pisman olacak",
    # yoğun çaresizlik
    r"dayanamiyorum artik", r"artik dayanamiyorum", r"depresyon(dayim|a girdim|da hissed)", r"artik (yasa|dayana)mam",
)]
# Akademik / meslek bağlamı: suç ya da sorun bir araştırma, ders ya da meslek konusu olarak geçiyorsa (birinci tekil kişide
# bir niyet ya da yaşantı yoksa) kriz sayılmaz.
_AKADEMIK = re.compile(r"(?<![a-z0-9])(arastirma|oran\w*|bolum\w*|ders\w*|kitab\w*|program\w*|onleme|hasta\w*|meslek\w*|okuyup|"
                       r"calismak isti|calisan|uzerine|konusu|teori\w*|sosyoloji|psikoloji|psikiyatri|sosyal hizmet|hemsire\w*|"
                       r"avukat\w*|polis\w*|hakim\w*|savci\w*|kriminoloji|adli)")
_AKADEMIK_KRIZ = re.compile(r"(?<![a-z0-9])(intihar|istismar\w*|taciz|siddet|depresyon|cinsel|tecavuz|zorbalik|zorbaliga)")
_KISISEL_KRIZ = re.compile(r"(?<![a-z0-9])(intihar (et|eder|edec|etme)|kendimi|kendime|ugradim|ugruyorum|maruz kal|"
                           r"(beni|bana|bize) (taciz|istismar|tecavuz|siddet)|(taciz|istismar|tecavuz|siddet)\w* (ediyor|etti|ediyo|"
                           r"uyguluyor|goruyorum|gordum|edildim|ediliyorum))")


# Oyun bağlamı: "lol oynarken takım arkadaşlarımı öldürcem" bir tehdit değil (yalnızca başkasına zarar desenleri için)
_OYUN = re.compile(r"(?<![a-z0-9])(oyun\w*|oynar\w*|oynuyor\w*|lol|valorant|pubg|minecraft|fortnite|cs ?go|takim arkadas\w*|mac\w*|rank\w*)")
_BASKASINA = ("oldur", "gebert", "bitirecegim", "yaralayacag", "zarar verecegim", "vurac")


def kriz_mesaji_mi(metin: str) -> bool:
    t = _sade(metin)
    a = _ascii(metin)
    eslesen = [d for d in _KRIZ_DESENLERI if d.search(a)]
    if not eslesen and not any(ifade in t for ifade in KRIZ_IFADELERI):
        return False
    if _OYUN.search(a) and eslesen and all(any(k in d.pattern for k in _BASKASINA) for d in eslesen) \
            and not any(ifade in t for ifade in KRIZ_IFADELERI):
        return False
    # Yalnızca akademik/meslek konusu olarak geçen suç ya da sorun sözcükleri ("intihar oranları üzerine araştırma")
    if _AKADEMIK.search(a) and all(_AKADEMIK_KRIZ.search(d.pattern) or d.pattern.endswith("dov") for d in eslesen) \
            and not _KISISEL_KRIZ.search(a):
        return False
    return True


class AsistanKullanilamiyorHatasi(Exception):
    """API anahtarı tanımlı değilse ya da OpenAI'ye ulaşılamazsa fırlatılır — router bunu 503'e çevirir."""
    pass


def _api_anahtari_var_mi() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def asistan_aktif_mi() -> bool:
    return _api_anahtari_var_mi()


def _durum_ve_oneriler(db: Session, ogrenci: Ogrenci) -> str:
    """[2026-10-04] Hedef seçilmemişse: kaç katman bitti, sonuçlar hazırsa en uyumlu 3 bölüm."""
    from app.models import Katman, OgrenciKatmanOturumu
    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi:
        return "Henüz hiçbir değerlendirme katmanına başlamamış; ilk adımı K1 (Değerler) katmanı."
    toplam = db.query(Katman).filter(Katman.kosullu_mu.is_(False)).count()
    biten = (db.query(OgrenciKatmanOturumu).join(Katman, Katman.id == OgrenciKatmanOturumu.katman_id)
             .filter(OgrenciKatmanOturumu.ogrenci_id == ogrenci.id, OgrenciKatmanOturumu.tur_id == tur.id,
                     OgrenciKatmanOturumu.durum == "tamamlandi", Katman.kosullu_mu.is_(False)).count())
    if tur.durum != "tamamlandi":
        return f"Değerlendirmenin {biten}/{toplam} katmanını tamamladı; bölüm önerileri tüm katmanlar bitince çıkacak."
    try:
        from app.core.skor_motoru import siralama_getir
        ilk3 = siralama_getir(db, ogrenci, tur, ilk_n=3)
        adlar = ", ".join(f"{db.get(Bolum, s.bolum_id).ad} (%{round(s.toplam_uyum)})" for s in ilk3)
        return f"Tüm katmanları tamamladı. Sistemin önerdiği en uyumlu bölümler: {adlar}. Hedef seçmesi için koçluk sayfasına yönlendirebilirsin."
    except Exception:
        return "Tüm katmanları tamamladı; koçluk sayfasından bir hedef bölüm seçebilir."


def _haftalik_ozet_metni(db: Session, ogrenci: Ogrenci) -> str:
    """[2026-10-04] Bu haftanın görevleri ve seri — Filiz 'bu hafta neye odaklanayım?' sorusunu bunlara göre cevaplar."""
    try:
        from app.core.haftalik_servisi import haftanin_gorevleri, _haftalik_sayimlar, seri_hesapla, hafta_baslangici, bugun_tr
        gorevler = haftanin_gorevleri(db, ogrenci)
        satirlar = [f"- {g.baslik} ({'tamamlandı' if g.durum == 'tamamlandi' else 'bekliyor'})" for g in gorevler]
        guncel, _ = seri_hesapla(_haftalik_sayimlar(db, ogrenci), hafta_baslangici(bugun_tr()))
        return "Bu haftanın görevleri:\n" + "\n".join(satirlar) + f"\nHaftalık seri: {guncel} hafta."
    except Exception:
        return ""


def _ogrenci_profil_ozeti(db: Session, ogrenci: Ogrenci) -> str:
    """
    Sistem promptuna eklenecek özet — koclugu_servisi.py'nin GERÇEK, zaten
    var olan fonksiyonlarını kullanır (gap_analizi_hesapla, aktif_hedef_getir)
    — burada ayrıca bir hesaplama/varsayım YAPILMAZ, yalnızca sonuçlar
    doğal dile çevrilir.
    """
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        return "Öğrenci henüz bir hedef bölüm seçmemiş. " + _durum_ve_oneriler(db, ogrenci)

    bolum = db.get(Bolum, hedef.bolum_id)
    bolum_adi = bolum.ad if bolum else f"(id={hedef.bolum_id})"

    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi:
        return f"Hedef bölümü: {bolum_adi}. Henüz K1-K4 değerlendirmesi tamamlanmamış."

    gap_satirlari = gap_analizi_hesapla(db, ogrenci, tur, hedef.bolum_id)
    if not gap_satirlari:
        return f"Hedef bölümü: {bolum_adi}. Henüz gap analizi için yeterli veri yok."

    # [DÜZELTME] ters_yonlu değişkenlerde ham `gap`in yönü tersine döner
    # (bkz. koclugu_servisi.py'deki aynı mantık) — "en güçlü/en gelişime
    # açık" sıralaması ham gap değil, yön-düzeltilmiş farka göre yapılmalı.
    def duzeltilmis_fark(s):
        return -s.gap if s.degisken.ters_yonlu else s.gap

    en_guclu = sorted(gap_satirlari, key=duzeltilmis_fark, reverse=True)[:3]
    en_gelisim = sorted(gap_satirlari, key=duzeltilmis_fark)[:3]

    guclu_metni = ", ".join(f"{s.degisken.ad} (bölümün beklediğinden fazla)" for s in en_guclu if s.gap > 0 and not s.degisken.ters_yonlu)
    gelisim_metni = ", ".join(f"{s.degisken.ad} (bölüm beklentisinin altında)" for s in en_gelisim if duzeltilmis_fark(s) < 0)

    parcalar = [f"Hedef bölümü: {bolum_adi}."]
    if guclu_metni:
        parcalar.append(f"Bölümün beklediğinden FAZLA olduğu yönler (bunlar güçlü yön ya da avantaj DEĞİL, bir uyumsuzluktur; 'bu bölümde bu yönünü daha az kullanabilirsin, sana uyup uymadığını sına' diye anlat): {guclu_metni}.")
    if gelisim_metni:
        parcalar.append(f"Bölümün beklediğinden EKSİK kaldığı yönler (değerler geliştirilmez: 'senin için daha az önemli; bölümün bu yönü sana uyar mı, sına' diye anlat; beceriler çalışarak gelişir, kişilik küçük alışkanlıklarla esner, ilgiler denenerek keşfedilir): {gelisim_metni}.")

    # [EKLENDİ] En belirgin 3 güçlü + 3 gelişim alanı için, o değişkenin
    # gerçek gap kategorisine uygun kaynak önerilerini (kitap/film/rol
    # model/psikolojik yaklaşım/aktivite) çek — bölümden BAĞIMSIZ, genel
    # öneriler. Filiz bunları öğrencinin hedef bölümüne göre YORUMLAYARAK
    # sunacak (bkz. aşağıdaki sistem promptu talimatı).
    onemli_satirlar = en_guclu + en_gelisim
    if onemli_satirlar:
        degisken_idler = [s.degisken.id for s in onemli_satirlar]
        tum_kaynaklar = (
            db.query(GelisimKaynakOnerisi)
            .filter(GelisimKaynakOnerisi.degisken_id.in_(degisken_idler))
            .all()
        )
        kaynak_metinleri = []
        for s in onemli_satirlar:
            aralik = gap_kategorisi(duzeltilmis_fark(s))
            eslesenler = [k for k in tum_kaynaklar if k.degisken_id == s.degisken.id and k.aralik == aralik]
            for k in eslesenler[:2]:  # değişken başına en fazla 2 kaynak, prompt şişmesin
                kaynak_metinleri.append(f"[{s.degisken.ad} / {k.kaynak_tipi}] {k.baslik} — {k.aciklama}")
        if kaynak_metinleri:
            parcalar.append("Önerilebilecek somut kaynaklar (bunları öğrencinin HEDEF BÖLÜMÜNE göre yorumlayarak sun, olduğu gibi kopyalama):\n" + "\n".join(kaynak_metinleri))

    return " ".join(parcalar)


SAYFA_ADLARI = {
    "/": "ana sayfa", "/katmanlar": "değerlendirme katmanları", "/sonuc": "bölüm uyum sonuçları",
    "/kesfet": "bölüm keşfetme", "/bolumler": "sana uygun bölümler", "/bolumler/tum": "tüm bölümleri keşfetme",
    "/bolumler/karsilastir": "bölüm karşılaştırma", "/bolumler/listem": "favori bölüm listesi", "/profilim": "kişisel profil sonuçları", "/koclugu": "hedef bölüm koçluğu ve yol haritası", "/profil": "profil ayarları",
}


def sistem_promptu_olustur(db: Session, ogrenci: Ogrenci, onceki_ozet: str | None, sayfa: str | None = None) -> str:
    profil = _ogrenci_profil_ozeti(db, ogrenci)
    ozet_blogu = f"\n\nÖnceki konuşmalardan kısa özet: {onceki_ozet}" if onceki_ozet else ""
    haftalik = _haftalik_ozet_metni(db, ogrenci)
    if haftalik:
        ozet_blogu += f"\n\n{haftalik}"
    sayfa_adi = SAYFA_ADLARI.get(sayfa or "") or (SAYFA_ADLARI["/sonuc"] if (sayfa or "").startswith("/sonuc") else
                                                   SAYFA_ADLARI["/profilim"] if (sayfa or "").startswith("/profilim") else None)
    if sayfa_adi:
        ozet_blogu += f"\n\nÖğrenci şu an sistemin '{sayfa_adi}' sayfasında."

    return f"""Sen "Filiz Gelişim Koçu"sun (kısaca Filiz); Filizyol adlı üniversite bölüm/kariyer koçluğu sisteminde çalışan, öğrenciyle sohbet tarzında konuşan bir gelişim ve kariyer koçusun. Kendini tanıtman gerekirse "Filiz, gelişim koçun" de. İsmin, Filizyol'un "kendi yolunu filizlendir" temasından geliyor — büyümeyi, gelişimi çağrıştıran bir isim.

ÖĞRENCİ: (gizlilik gereği adı sana verilmez; ona adıyla değil "sen" diye hitap et)
{profil}{ozet_blogu}

SİSTEMİN BÖLÜMLERİ (öğrenci "nerede, nasıl" diye sorarsa bunlara dayan; burada olmayan bir özelliği varmış gibi anlatma):
Profilim: sonuçlar ve kısa yorum ("Kısaca", bunu yap / bundan kaçın). Bölümler: uyumlu bölümler. Koçluğum: hedef bölüm ve yol haritası.
Raporlarım: kendi ve veli raporu (okulunda açıksa); değerlendirmenin son bölümü bitince sonuç e-postası gider, gelmediyse rehber öğretmen yeniden gönderebilir.
Yeniden değerlendirme: yaklaşık 3 ay sonra yeni tur açılır; cevaplar tutarsız bulunduysa yalnızca o bölüm beklemeden yeniden yanıtlanır.
İş Hayatı (okulunda açıksa): maaşlar, zor günler, CV, Mülakat Pratiği, Mülakat Simülasyonu (iki adaydan daha iyi cevabı seçme),
Düşünme Atölyesi (kök neden, korelasyon/nedensellik, algoritma, ikiye bölerek arama, tercih verisini okuma, öğrenmeyi öğren deneyi; ikinci ölçüm en erken 12 saat sonra).
Ayarlar: dil seçimi (Türkçe dışında 12 dil), gizlilik. Sistem Hakkında: SSS.

KURALLAR (bunlara kesinlikle uy):
1. Sohbet tarzında, doğal cümlelerle konuş — madde madde liste, numaralı adım ya da "1. ... 2. ..." formatı KULLANMA. Gerçek bir insan koç gibi, akıcı paragraflar halinde yaz.
2. Kendi kişisel bir anını, deneyimini ya da hikayeni ASLA uydurma ("ben de senin yaşındayken..." gibi cümleler kurma). Sen bir insan değilsin, bunu gizlemeye çalışma ama gereksiz yere de vurgulama.
3. Öğrencinin yukarıdaki gerçek profil verisine dayan — uydurma bilgi verme. Profilde olmayan bir şeyi biliyormuş gibi davranma.
4. Sistemin kendi hesapladığı sonuçlarla ÇELİŞME — örneğin hedef bölümü olarak gösterilenden başka bir bölümü "asıl sana bu uyar" diye önerme; onun yerine mevcut hedefi/güçlü yönlerini nasıl değerlendirebileceğini konuş.
5. Ne çok dar (yalnızca tek cümlelik cevaplar) ne çok geniş (alakasız konulara sürüklenen) ol — kariyer, bölüm, gelişim, motivasyon eksenli sohbet et, öğrenci başka bir şey sorarsa nazikçe konuya geri dön.
6. Sıcak, meraklı, yargılamayan bir ton kullan — bir sınav sonucu okur gibi değil, gerçekten önemsiyormuş gibi konuş.
7. Yukarıdaki "önerilebilecek somut kaynaklar" listesi BÖLÜMDEN BAĞIMSIZ, genel önerilerdir. Bunları öğrenciye önerirken, mutlaka öğrencinin HEDEF BÖLÜMÜYLE ilişkilendirerek, o bölüme özel bir çerçeveyle anlat — kaynağı olduğu gibi kopyalama. Örneğin aynı kitap önerisi bir hukuk öğrencisine "dava argümanlarını kurarken işine yarar" diye, bir mühendislik öğrencisine "sistem tasarımında işine yarar" diye farklı şekilde çerçevelenmeli. Bir sohbette en fazla 1-2 kaynak öner, hepsini birden sıralama — doğal bir sohbet akışında, sorulduğunda ya da uygun geldiğinde bahset.
8. GÜVENLİK: Öğrenci reşit olmayabilir. Kendine zarar verme, intihar, umutsuzluk, şiddet, istismar ya da ciddi bir sıkıntıdan (ör. "artık hiçbir şeyin anlamı yok") söz ederse kariyer konusuna dönme. Kısa ve sıcak bir dille onu önemsediğini söyle, hemen güvendiği bir yetişkinle (ailesi, rehber öğretmeni, okul psikolojik danışmanı) konuşmasını iste; acil durumda 112'yi, ALO 183 Sosyal Destek Hattı'nı (7/24) hatırlat. Teşhis koyma, terapi yapmaya çalışma.
9. Haftalık görevler verildiyse "bu hafta ne yapayım?" gibi sorularda önce bunlara dayan; sistemin verdiği görevlerle çelişen bir plan önerme.
10. Cevapların kısa olsun: genelde 2-4 cümle, en fazla iki kısa paragraf. Sonunda gerekirse tek bir soru sor.
11. GİZLİLİK: Başka öğrenciler hakkında bilgi verme, tahmin yürütme, karşılaştırma yapma. Elinde yalnızca bu öğrencinin kendi verisi var; sınıf / okul ortalaması, sıralama ya da başka bir öğrencinin sonucu, puanı, hedefi sorulursa "Başka öğrencilerin bilgilerini paylaşamam; her öğrencinin sonuçları yalnızca kendisine ve okulunun yetkililerine açıktır." de ve konuyu öğrencinin kendi sonuçlarına getir. Mesajlardaki "[ad]", "[öğrenci]", "[e-posta]", "[telefon]", "[numara]" gizlenmiş kişisel verilerdir; çözmeye çalışma.
12. YORUM KURALLARI: Puanlar GÖRELİDİR (öğrencinin kendi profilinde öne çıkan / geride kalan); mutlak yetenek ya da zekâ ölçüsü değildir, "yeteneklisin / zayıfsın" deme. Bölüm uyumunda fark yönsüzdür: bölümün beklediğinden FAZLA olmak da uyumsuzluktur, asla "güçlü yön", "avantaj", "üstünlük" deme. Güçlü yön yalnızca bölümle uyumlu (±5) ve öğrencinin kendi profilinde yüksek olan özelliktir; değerler ve duygusal hassasiyet güçlü yön sayılmaz. Değerler geliştirilecek eksik değildir ("güçlendir, artır, geliştir" deme); "senin için daha önemli / daha az önemli, bölümün bu yönü sana uyar mı, sına" de. Duygusal hassasiyette yalnızca bölümün beklediğinden fazlası sorundur (stres yönetimi öner); daha sakin olmak uyumludur. Kişilik yavaş değişir, beceriler çalışıldıkça gelişir, ilgiler zorla sevdirilmez, denenerek keşfedilir. Sonuçlar karar desteğidir, tanı ya da kesin hüküm değildir; sayı, istatistik ya da kurum uydurma.
"""


# [2026-10-31] Yapay zekâ çağrıları sunucuyu kilitlemesin: tüm sohbet çağrıları (öğrenci Filiz'i, mülakat geri
# bildirimi, yönetim Filiz'i, oturum özeti) bu tek kapıdan geçer.
#  * Aynı anda en fazla YZ_ESZAMANLI çağrı. Kapı doluysa BEKLENMEZ: AsistanMesgulHatasi → çağıran rehber moduna düşer.
#    Böylece yapay zekâ beklerken sunucunun iş parçacıklarının en fazla bu kadarı dolu kalır; değerlendirme ekranı vb. etkilenmez.
#  * Kısa zaman aşımı ve kütüphanenin kendi yeniden denemeleri kapalı (önceden 40 sn × 3 deneme = 2 dakikaya kadar bekleyebiliyordu).
#  * Ana model hata verirse aynı sağlayıcıdaki yedek model bir kez denenir (KVKK metninde sağlayıcı OpenAI; değişmez).
#  * İçerik çevirisi (ceviri_servisi) de bu kapıdan geçer.
#  * Kapı SÜREÇ başınadır: birden fazla sunucu süreci / kopya varsa gerçek üst sınır = süreç sayısı × YZ_ESZAMANLI.
import threading
import logging

YZ_ESZAMANLI = max(1, int(os.environ.get("FILIZ_YZ_ESZAMANLI", "10") or 10))
YZ_ZAMAN_ASIMI_SN = 15.0        # ana model
YZ_YEDEK_ZAMAN_ASIMI_SN = 10.0  # yedek model
YEDEK_MODEL_ADI = os.environ.get("OPENAI_YEDEK_MODEL", "").strip() or "gpt-4.1-mini"
_YZ_KAPI = threading.BoundedSemaphore(YZ_ESZAMANLI)
_istemciler: dict = {}
_istemci_kilit = threading.Lock()
_log = logging.getLogger("ai_koc")


class AsistanMesgulHatasi(AsistanKullanilamiyorHatasi):
    """Aynı anda izin verilen yapay zekâ çağrısı sayısı dolu; beklenmeden rehber moduna geçilir."""


def _yz_istemcisi(zaman_asimi: float):
    """Bağlantı havuzu yeniden kullanılsın diye istemci (anahtar, zaman aşımı) başına bir kez kurulur."""
    from openai import OpenAI  # yalnızca anahtar varsa import edilir
    anahtar = os.environ["OPENAI_API_KEY"].strip()
    k = (id(OpenAI), anahtar, zaman_asimi)
    with _istemci_kilit:
        if k not in _istemciler:
            _istemciler.clear() if len(_istemciler) > 8 else None
            _istemciler[k] = OpenAI(api_key=anahtar, timeout=zaman_asimi, max_retries=0)
        return _istemciler[k]


def yz_sohbet(mesajlar: list[dict], *, temperature: float, max_tokens: int | None, yedek: bool = True,
              zaman_asimi: float | None = None, **ek) -> str:
    """Tek kapı: eşzamanlılık sınırı + kısa zaman aşımı + (isteğe bağlı) yedek model. Hata → AsistanKullanilamiyorHatasi."""
    if not _api_anahtari_var_mi():
        raise AsistanKullanilamiyorHatasi("Filiz'e şu an ulaşılamıyor, biraz sonra tekrar dene.")
    if not _YZ_KAPI.acquire(blocking=False):
        raise AsistanMesgulHatasi("Filiz'in yapay zekâsı şu an çok yoğun; birkaç dakika sonra tekrar dene.")
    try:
        denemeler = [(MODEL_ADI, zaman_asimi or YZ_ZAMAN_ASIMI_SN)]
        if yedek and YEDEK_MODEL_ADI and YEDEK_MODEL_ADI != MODEL_ADI:
            denemeler.append((YEDEK_MODEL_ADI, YZ_YEDEK_ZAMAN_ASIMI_SN))
        son_hata = None
        for model, sure in denemeler:
            try:
                parametre = {"max_tokens": max_tokens} if max_tokens else {}
                yanit = _yz_istemcisi(sure).chat.completions.create(
                    model=model, messages=mesajlar, temperature=temperature, **parametre, **ek)
                icerik = (yanit.choices[0].message.content or "").strip()
                if icerik:
                    return icerik
                son_hata = ValueError("boş cevap")
            except Exception as hata:  # yanlış anahtar, kota, ağ, zaman aşımı
                son_hata = hata
                _log.warning("Yapay zekâ çağrısı başarısız (%s): %s: %s", model, type(hata).__name__, hata)
        raise AsistanKullanilamiyorHatasi("Filiz'e şu an ulaşılamıyor, biraz sonra tekrar dene.") from son_hata
    finally:
        _YZ_KAPI.release()


def openai_ile_konus(sistem_promptu: str, mesaj_gecmisi: list[dict]) -> str:
    """
    mesaj_gecmisi: [{"role": "user"|"assistant", "content": "..."}]
    """
    from app.core.ceviri_servisi import yapay_zeka_dil_talimati
    return yz_sohbet([{"role": "system", "content": sistem_promptu + yapay_zeka_dil_talimati()}] + mesaj_gecmisi,   # [2026-10-12] seçili dilde cevap
                     temperature=0.7, max_tokens=500)


def oturumu_ozetle(sistem_promptu: str, mesaj_gecmisi: list[dict]) -> str | None:
    """Oturum kapanırken, ham geçmiş yerine bir sonraki oturuma taşınacak kısa özeti üretir.
    Özet çıkmazsa (anahtar yok, yoğunluk, hata) oturum yine kapanır; None döner."""
    ozetleme_istegi = mesaj_gecmisi + [{
        "role": "user",
        "content": "Bu konuşmayı, bir sonraki oturumda hatırlaman için 2-3 cümlelik kısa bir özete çevir. Yalnızca özeti yaz, başka bir şey ekleme.",
    }]
    try:
        return yz_sohbet([{"role": "system", "content": sistem_promptu}] + ozetleme_istegi,
                         temperature=0.3, max_tokens=150, yedek=False)
    except AsistanKullanilamiyorHatasi:
        return None
