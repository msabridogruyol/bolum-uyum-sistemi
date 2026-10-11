# -*- coding: utf-8 -*-
"""
[2026-10-11] İş Hayatı → CV Atölyesi → "ATS kontrolü" algoritması (uç: POST /ogrenci/is-hayati/cv/ats, app/api/is_hayati_cv.py).

İki parça:
 1) Biçim kontrolü — sistemin ürettiği PDF pypdf ile GERÇEKTEN ayrıştırılır; çıkan düz metin ("ATS'nin gördüğü") üzerinde:
    metin seçilebilir mi + Türkçe karakterler bozulmadan geliyor mu, standart bölüm başlıkları, e-posta deseni, tarih biçimi
    tutarlılığı, sayfa sayısı, garip karakter / harf aralıklı metin. Puan /100 (ağırlıklar aşağıda, ürün kararı).
 2) İlana uyum — ilan metninden anahtar kelime / öbek çıkarımı ve CV metniyle eşleştirme:
    - Türkçe küçük harf (İ→i, I→ı), noktalama atılır, durak sözcükleri ve ilan dolgu sözcükleri ("deneyim", "bilgi", "aday" …) atılır.
    - Hafif kök bulma: yaygın çekim/yapım ekleri sondan en çok 3 tur budanır (kök ≥ 3 harf kalır), sonra son ünsüz
      yumuşaması geri alınır (ekib → ekip, kitab → kitap). Mükemmel değildir: "yazılım" ile "yazı" ayrılır ama bazı farklı
      sözcükler aynı köke düşebilir. Bilinçli olarak basit tutuldu; öğrenciye "tahmin" olarak gösterilir.
    - Öbekler: sık beceri öbekleri listesi (ÖBEKLER) + ilanda en az iki kez geçen ardışık ikililer.
    - Ağırlık: zorunlu satır 3, tercih satırı 2, diğer 1 (aynı kök birden çok satırda geçerse en yüksek ağırlık + 0,5/tekrar, en çok 4).
      Satır türü örnek ilanlarda veri dosyasındaki etiketten, yapıştırılan ilanda ipucu sözcüklerinden ("şart", "zorunlu",
      "en az", "aranır" / "tercih", "tercihen", "avantaj", "artı") ya da "Aranan nitelikler / Tercih sebebi" alt başlığından gelir.
    - Uyum % = bulunan ağırlık / toplam ağırlık (öbekte kökler CV'de var ama yan yana değilse yarım puan).
    - Yerleştirme önerisi: dil adları → Diller, araç/yazılım → Beceriler, sertifika/kurs → Sertifikalar, kişisel beceriler →
      deneyim açıklamasında örnekle, diğerleri → deneyim/proje açıklaması.
Hiçbir şey kaydedilmez; fonksiyonlar saf (DB'siz) — birim testi: backend/test_ats.py.
"""
import io
import re
import unicodedata

# ============================================================================= normalize + kök
DURAK = set("""
acaba ama ancak artık aslında az bazı belki ben bana beni benim bile bir biraz birçok biri birkaç birşey biz bize bizi bizim
bu buna bunda bundan bunu bunun burada böyle bütün da daha de değil diye dolayı en fakat gibi göre hem hep hepsi her hiç
için ile ise ister kadar ki kim kimse mı mi mu mü nasıl ne neden nerede nereye niye o olan olarak olduğu olduğunu olmak
olması olup ona ondan onlar onları onu onun orada öyle şey şu şuna şunu tüm üzere var ve veya ya yani yine yoksa çok çünkü
sen seni senin siz sizi sizin size sana bunlar şöyle ayrıca diğer kendi kendini sadece yalnızca yalnız hangi böylece
ve/veya vb vs gibi olmalı olmalıdır olmasi olabilen olabilecek edebilen edebilecek eden etmek etme yapmak yapabilen
the and or of to in for with a an on at is are be as by we you our your
""".split())

# İlanlarda nitelik olmadan geçen dolgu sözcükleri (kök hâlinde karşılaştırılır).
DOLGU = set("""
aday adaylar arıyoruz aranıyor aranmaktadır aranan arkadaş arkadaşı arkadaşlar alım başvuru başvurular başvurabilir
bilgi bilgisi bilgili bilgisine deneyim deneyimi deneyimli tecrübe tecrübeli tecrübesi yetkinlik yetkinliği beceri becerisi
becerileri yetenek yeteneği yetenekli sahip sahibi pozisyon pozisyonu pozisyonumuz ilan şirket şirketimiz firmamız kurum
kurumumuz ekibimize ekibimiz bünyemizde bünyesinde iş işler işi konu konusunda konularında alan alanında alanda düzey
düzeyde düzeyinde seviye seviyede seviyesinde iyi derece derecede temel ileri orta en az fazla yıl yıllık ay ayda gün
tercih tercihen sebebi sebebidir nedeni zorunlu şart şarttır gerekli gerekir gerekmektedir mutlaka aranır beklenir
olmak olan olması olmaları olabilen olarak yapabilen edebilen kullanabilen sağlayabilen kişi kişiler kişiye herhangi
nitelik nitelikler nitelikli genel tam yarı zaman saat saatleri hafta haftada sonu sonları dönem dönemi süre süreli
lazım istekli isteyen açık önemli uygun yeni gelecek çalışacak çalışabilecek çalışmak çalışma çalışan çalışanlar
öğrenci öğrencisi öğrencileri lise üniversite mezun mezunu sağlanır sağlıyoruz sunuyoruz imkanı imkânı fırsatı
artı artıdır hakkında oluşur güçlü kuvvetli hızlı dinamik benzer yatkın güler yüzlü akıcı söz sözü ilgi ilgisi soru
baş başına araç aracı değer değerleri gündem gündemi bağlantı bağlantısı doküman dokümanları kural kuralları tempo
tutan veren eden yapan olan uyan işe işi yaş yaşını yaşından yaşında boyunca cumartesi pazar pazartesi form formu izin izni veli velisi keyif küçük büyük kesinlikle
içinde içi dışında kıyafet ayakkabı sabah akşam öğle ortam ortamda hazır geri destek ikinci program programı programları
eğitim eğitimi dil dili durum durumlarla gerektiğinde gerekirse herkes birlikte beraber kez sık sıklıkla örnek örnekleri
""".split())

# Ekler: uzun olan önce denenir. Kök en az 3 harf kalır.
EKLER = sorted(set("""
larının lerinin larını lerini larına lerine larında lerinde larından lerinden ların lerin ları leri lara lere larda lerde
lardan lerden lar ler
sının sinin sunun sünün ının inin unun ünün nın nin nun nün ın in un ün
ında inde unda ünde ndan nden nda nde ından inden
yla yle ıyla iyle uyla üyle la le
dan den tan ten da de ta te
yı yi yu yü ya ye sı si su sü ı i u ü a e
lık lik luk lük lı li lu lü sız siz suz süz
mak mek ması mesi ma me
dır dir dur dür tır tir tur tür
masına mesine sına sine suna süne ına ine una üne nı ni nu nü na ne
ımız imiz umuz ümüz ınız iniz unuz ünüz mız miz muz müz nız niz nuz nüz
sıyla siyle suyla süyle sında sinde sunda sünde sından sinden sundan sünden
masıyla mesiyle masında mesinde masından mesinden larıyla leriyle
""".split()), key=len, reverse=True)
# Sıfat-fiil / zarf-fiil / çekimli fiil görünümlü kelimeler (bilen, alabilen, doldurmuş, yapacak, yaptığı, araştırıp) nitelik
# adı değildir; anahtar kelime olarak alınmaz. Kısa isimleri (plan, alan) korumak için en az 5 harf.
_FIILIMSI = re.compile(r"(?:[ae]bil(?:en|ir|ecek|mek)|m[ae]y[ae]n|y[ae]n|[^aeıioöuüdt][ae]n|m[ıiuü]ş(?:t[ıiuü]r)?|[ae]c[ae]k|"
                       r"[dt][ıiuü]ğ[ıiuü](?:n[ıiuü])?|[^aeıioöuü][ıiuü]p|[ıiuü]yor(?:um|uz|lar)?|m[ae]z|m[ae]kt[ae]n|m[ae]k|"
                       r"m[ae]l[ıi](?:d[ıi]r)?|[ae]c[ae]kt[ıi]r|m[ae]y[ıiae])$")
_YUMUSAMA = {"ğ": "k", "b": "p", "c": "ç", "d": "t"}
# Eşanlamlı kökler (ilan "takım", CV "ekip" diyebilir).
ESANLAM = {"takım": "ekip", "tecrüp": "deneyim", "yetkinlik": "beceri", "ms": "microsoft", "ingiliz": "ingilizce"}

ÖBEKLER = [
    "ekip çalışması", "takım çalışması", "müşteri iletişimi", "müşteri ilişkileri", "sosyal medya", "zaman yönetimi",
    "problem çözme", "sorun çözme", "microsoft office", "ms office", "google workspace", "ilk yardım", "veri analizi",
    "sunum hazırlama", "sunum yapma", "yazılı iletişim", "sözlü iletişim", "proje yönetimi", "grafik tasarım", "web tasarım",
    "içerik üretimi", "içerik hazırlama", "etkinlik düzenleme", "etkinlik organizasyonu", "çocuklarla çalışma",
    "el becerisi", "teknik çizim", "iş güvenliği", "hijyen eğitimi", "kod yazma", "versiyon kontrol", "yapay zeka",
    "dijital okuryazarlık", "eleştirel düşünme", "analitik düşünme", "stres yönetimi", "kriz yönetimi", "hasta iletişimi",
    "fotoğraf çekme", "video düzenleme", "görsel tasarım", "programlama dili", "müşteri hizmetleri", "kamera önü",
]

DILLER = {"ingilizce", "almanca", "fransızca", "ispanyolca", "italyanca", "rusça", "arapça", "japonca", "çince", "korece",
          "farsça", "yunanca", "felemenkçe", "portekizce", "türkçe", "işaret dili"}
ARACLAR = {"excel", "word", "powerpoint", "office", "microsoft", "google", "canva", "photoshop", "illustrator", "figma",
           "python", "java", "javascript", "html", "css", "sql", "scratch", "arduino", "autocad", "sketchup", "revit",
           "git", "github", "linux", "c++", "c#", "matlab", "tinkercad", "blender", "premiere", "capcut", "wordpress",
           "trello", "notion", "kotlin", "swift", "react", "solidworks", "fusion", "spss", "r"}
SERTIFIKA = {"sertifika", "sertifikası", "belge", "belgesi", "kurs", "kursu", "eğitimi", "ehliyet", "lisans", "toefl",
             "ielts", "yds", "yökdil", "ecdl", "hijyen", "ilk yardım"}
KISISEL = {"iletişim", "ekip", "takım", "sorumluluk", "liderlik", "dikkat", "düzen", "zaman", "uyum", "güler", "sabır",
           "empati", "planlama", "organizasyon", "problem", "sorun", "yaratıcı", "yaratıcılık", "inisiyatif", "motivasyon",
           "dakik", "dakiklik", "esnek", "öğrenme", "merak", "analitik", "eleştirel", "stres", "titiz", "özen"}

ZORUNLU_IPUCU = re.compile(r"\b(zorunlu|şart|gerekli|gerekmekte|mutlaka|aranır|aranmaktadır|en az|olmalı|beklenmekte|"
                           r"aranan nitelik|olmazsa olmaz|required|must)\w*", re.I)
TERCIH_IPUCU = re.compile(r"\b(tercih|tercihen|avantaj|artı|olması halinde|olursa|plus|preferred|nice to have)\w*", re.I)
_ALT_BASLIK_Z = re.compile(r"^(aranan|genel)?\s*(nitelik|şart|gereksinim|beklenti)\w*\s*:?$", re.I)
_ALT_BASLIK_T = re.compile(r"^(tercih\w*|artı\w*|avantaj\w*)(\s+\w+){0,2}\s*:?$", re.I)
# "Şirket hakkında:", "İş tanımı", "Yan haklar" gibi alt başlıklar nitelik bölümünü kapatır (satır içi metin varsa o da 'genel').
_ALT_BASLIK_G = re.compile(r"^(şirket|firma|kurum|biz kimiz|hakkımızda|iş tanımı|görev|sorumluluk|sunduklar|yan hak|çalışma koşul|"
                           r"neler sunuyoruz|başvuru)\w*(\s+\w+){0,2}\s*:", re.I)


def tr_kucuk(m: str) -> str:
    m = unicodedata.normalize("NFC", m or "").replace("I", "ı").replace("İ", "i").lower()
    return m.replace("i̇", "i").replace("â", "a").replace("î", "i").replace("û", "u")


_KELIME = re.compile(r"[a-zçğıöşü0-9][a-zçğıöşü0-9+#]*(?:\.[a-z]{2,4})?")


def kelimeler(metin: str) -> list[str]:
    """Türkçe küçük harfe çevrilmiş kelime dizisi (C++, C#, Node.js gibi biçimler korunur)."""
    return _KELIME.findall(tr_kucuk(metin))


def kok(k: str) -> str:
    """Hafif kök: ekleri sondan en çok 3 tur budar, son ünsüz yumuşamasını geri alır. Sayı / kısa kelime / araç adı olduğu gibi."""
    if len(k) <= 3 or not k.isalpha() or k in ARACLAR or k in DILLER:
        return ESANLAM.get(k, k)
    for _ in range(4):
        for e in EKLER:
            if k.endswith(e) and len(k) - len(e) >= 3:
                k = k[: -len(e)]
                break
        else:
            break
    if len(k) >= 4 and k[-1] in _YUMUSAMA:
        k = k[:-1] + _YUMUSAMA[k[-1]]
    return ESANLAM.get(k, k)


def _icerik_kelimesi(k: str) -> bool:
    if len(k) < 2 or k in DURAK or k in DOLGU or k.isdigit():
        return False
    if k in ARACLAR or k in DILLER:
        return True
    if len(k) >= 5 and _FIILIMSI.search(k):
        return False
    return kok(k) not in _DOLGU_KOK and len(kok(k)) >= 3


_DOLGU_KOK = {kok(x) for x in DOLGU if len(x) > 3} - {kok(x) for x in KISISEL}


# ============================================================================= ilan → anahtar kelimeler
def ilan_satirlari(metin: str) -> list[dict]:
    """Yapıştırılan ilanı satırlara/cümlelere böler ve her birine tür (zorunlu | tercih | genel) atar."""
    sonuc, bolum = [], None
    for ham in re.split(r"\n+", metin or ""):
        ham = ham.strip(" \t•-–*·▪●")
        if not ham:
            continue
        if len(ham) <= 40 and _ALT_BASLIK_T.match(ham):
            bolum = "tercih"
            continue
        if len(ham) <= 40 and _ALT_BASLIK_Z.match(ham):
            bolum = "zorunlu"
            continue
        m = _ALT_BASLIK_G.match(ham)
        if m:
            bolum = None
            ham = ham[m.end():].strip()
            if not ham:
                continue
        for c in re.split(r"(?<=[.!?;])\s+", ham):
            if not c.strip():
                continue
            tur = "tercih" if TERCIH_IPUCU.search(c) else ("zorunlu" if ZORUNLU_IPUCU.search(c) else (bolum or "genel"))
            sonuc.append({"metin": c.strip(), "tur": tur})
    return sonuc


AGIRLIK = {"zorunlu": 3.0, "tercih": 2.0, "gizli": 0.5, "genel": 1.0, "bilgi": 0.0}


def anahtar_kelimeler(satirlar: list[dict], en_cok: int = 20) -> list[dict]:
    """[{metin, tur}] → [{ifade, kokler, agirlik, tur, adet}] (ağırlığa göre azalan). 'bilgi' satırları atlanır."""
    aday: dict[tuple, dict] = {}
    nitelik_var = any(s.get("tur") in ("zorunlu", "tercih") for s in satirlar)

    def ekle(kokler: tuple, ifade: str, tur: str):
        a = 0.5 if tur == "genel" and nitelik_var else AGIRLIK.get(tur, 1.0)
        if a <= 0:
            return
        x = aday.get(kokler)
        if x is None:
            aday[kokler] = {"ifade": ifade, "kokler": list(kokler), "agirlik": a, "taban": a, "tur": tur, "adet": 1}
        else:
            x["adet"] += 1
            if len(ifade) < len(x["ifade"]) and len(kokler) == 1:   # en kısa yüzey biçimi gösterilir ("projeyi" yerine "proje")
                x["ifade"] = ifade
            if a > x["taban"]:
                x["agirlik"] = x["taban"] = a
                x["tur"] = tur

    ikililer: dict[tuple, list] = {}
    for s in satirlar:
        tur = s.get("tur") or "genel"
        if AGIRLIK.get(tur, 1.0) <= 0:
            continue
        kucuk = tr_kucuk(s["metin"])
        tuketilen = set()
        for ob in ÖBEKLER:
            if re.search(rf"(?<![a-zçğıöşü]){re.escape(ob)}", kucuk):
                kk = tuple(kok(w) for w in ob.split())
                ekle(kk, ob, tur)
                tuketilen.update(kk)
        kel = kelimeler(s["metin"])
        for i, w in enumerate(kel):
            if not _icerik_kelimesi(w):
                continue
            kw = kok(w)
            if kw in tuketilen:
                continue
            ekle((kw,), w, tur)
            if i + 1 < len(kel) and _icerik_kelimesi(kel[i + 1]):
                ikililer.setdefault((kw, kok(kel[i + 1])), []).append((f"{w} {kel[i + 1]}", tur))
    for kk, gecis in ikililer.items():   # ilanda en az iki kez geçen ikili → öbek
        if len(gecis) >= 2 and kk not in aday:
            for ifade, tur in gecis:
                ekle(kk, gecis[0][0], tur)
            aday[kk]["adet"] = len(gecis)
    liste = []
    for x in aday.values():
        x["agirlik"] = min(4.0, x.pop("taban") + 0.5 * (x["adet"] - 1))
        liste.append(x)
    # öbeğin parçası olan tek kelimeleri (öbek seçildiyse) ele
    obek_kok = {k for x in liste if len(x["kokler"]) > 1 for k in x["kokler"]}
    liste = [x for x in liste if len(x["kokler"]) > 1 or x["kokler"][0] not in obek_kok or x["tur"] == "zorunlu"]
    liste.sort(key=lambda x: (-x["agirlik"], -x["adet"], -len(x["kokler"]), x["ifade"]))
    return liste[:en_cok]


# ============================================================================= CV metni → bölümler
STANDART_BASLIK = {
    "profil": ["profil", "özet", "hakkımda", "kariyer hedefi", "summary", "profile", "about"],
    "egitim": ["eğitim", "eğitim bilgileri", "education"],
    "deneyim": ["deneyim", "deneyimler", "iş deneyimi", "deneyim ve görevler", "staj", "stajlar", "görevler",
                "experience", "work experience"],
    "projeler": ["projeler", "proje", "projects"],
    "gonulluluk": ["gönüllülük", "gönüllü çalışmalar", "sosyal sorumluluk", "volunteering", "volunteer"],
    "oduller": ["ödüller", "ödüller ve yarışmalar", "başarılar", "yarışmalar", "awards"],
    "sertifikalar": ["sertifikalar", "sertifikalar ve kurslar", "kurslar", "certificates", "certifications"],
    "beceriler": ["beceriler", "yetenekler", "yetkinlikler", "skills"],
    "diller": ["diller", "yabancı dil", "yabancı diller", "languages"],
    "ilgi": ["ilgi alanları", "hobiler", "interests"],
    "referanslar": ["referanslar", "references"],
}
_STANDART = {tr_kucuk(a): kod for kod, adlar in STANDART_BASLIK.items() for a in adlar}
BOLUM_AD = {"profil": "Profil", "egitim": "Eğitim", "deneyim": "Deneyim", "projeler": "Projeler", "gonulluluk": "Gönüllülük",
            "oduller": "Ödüller", "sertifikalar": "Sertifikalar", "beceriler": "Beceriler", "diller": "Diller",
            "ilgi": "İlgi alanları", "referanslar": "Referanslar"}


def baslik_satiri_mi(satir: str) -> bool:
    s = satir.strip()
    harf = [c for c in s if c.isalpha()]
    return 2 <= len(s) <= 45 and len(harf) >= 3 and all(c.isupper() for c in harf) and not re.search(r"[@|]", s)


def bolumlere_ayir(metin: str) -> list[dict]:
    """Ayrıştırılmış düz metni başlık satırlarına göre böler: [{baslik, kod|None, satirlar[]}]. İlk parça başlıksızdır (ad + iletişim)."""
    parca = [{"baslik": None, "kod": None, "satirlar": []}]
    for satir in (metin or "").splitlines():
        if baslik_satiri_mi(satir):
            parca.append({"baslik": satir.strip(), "kod": _STANDART.get(tr_kucuk(satir.strip())), "satirlar": []})
        elif satir.strip():
            parca[-1]["satirlar"].append(satir.strip())
    return parca


# ============================================================================= eşleştirme
def yerlestirme(x: dict) -> dict:
    ifade = x["ifade"]
    kel = set(ifade.split())
    if kel & DILLER or ifade in DILLER:
        return {"bolum": "diller", "oneri": "Diller bölümüne seviyesiyle (A1–C2) ekle."}
    if kel & ARACLAR:
        return {"bolum": "beceriler", "oneri": "Beceriler bölümüne ekle; bir projede kullandıysan o projenin açıklamasında da an."}
    if kel & SERTIFIKA or ifade in SERTIFIKA:
        return {"bolum": "sertifikalar", "oneri": "Belgen varsa Sertifikalar ve kurslar bölümüne ekle."}
    if {kok(w) for w in kel} & {kok(w) for w in KISISEL}:
        return {"bolum": "deneyim", "oneri": "Sıfat olarak yazmak yerine bir deneyiminin açıklamasında örnekle göster "
                                              "(ör. \"4 kişilik ekipte görev dağılımını ben yaptım\")."}
    return {"bolum": "deneyim", "oneri": "Gerçekten yaptıysan ilgili deneyim ya da proje açıklamasında bu ifadeyi kullan."}


def eslestir(anahtarlar: list[dict], cv_metni: str) -> dict:
    """CV düz metninde anahtar kelimeleri arar. Dönen: {uyum, bulunan[], kismen[], eksik[]}."""
    bolumler = bolumlere_ayir(cv_metni)
    dizi = []   # (kök, bölüm kodu, bölüm adı)
    for b in bolumler:
        kod = b["kod"] or ("iletisim" if b["baslik"] is None else "diger")
        ad = BOLUM_AD.get(kod) or ("Üst bilgi" if kod == "iletisim" else (b["baslik"] or "").capitalize())
        for satir in b["satirlar"]:
            for w in kelimeler(satir):
                dizi.append((kok(w), kod, ad))
    kokler = [d[0] for d in dizi]
    kume = set(kokler)
    toplam = sum(x["agirlik"] for x in anahtarlar) or 1.0
    puan, bulunan, kismen, eksik = 0.0, [], [], []
    for x in anahtarlar:
        kk = x["kokler"]
        nerede = None
        if len(kk) == 1:
            if kk[0] in kume:
                nerede = next(d for d in dizi if d[0] == kk[0])
        else:
            for i in range(len(kokler) - len(kk) + 1):
                if kokler[i:i + len(kk)] == kk:
                    nerede = dizi[i]
                    break
        oge = {"ifade": x["ifade"], "tur": x["tur"], "agirlik": x["agirlik"]}
        if nerede:
            puan += x["agirlik"]
            bulunan.append({**oge, "bolum": nerede[1], "bolum_ad": nerede[2]})
        elif len(kk) > 1 and all(k in kume for k in kk):
            puan += x["agirlik"] / 2
            kismen.append({**oge, **yerlestirme(x), "not": "Kelimeler CV'nde var ama yan yana değil."})
        else:
            eksik.append({**oge, **yerlestirme(x)})
    return {"uyum": round(100 * puan / toplam), "bulunan": bulunan, "kismen": kismen, "eksik": eksik,
            "toplam_agirlik": round(toplam, 1)}


def ilan_uyumu(ilan_satirlari_: list[dict], cv_metni: str) -> dict:
    anahtarlar = anahtar_kelimeler(ilan_satirlari_)
    sonuc = eslestir(anahtarlar, cv_metni)
    sonuc["anahtar_sayisi"] = len(anahtarlar)
    sonuc["satir_turleri"] = {t: sum(1 for s in ilan_satirlari_ if s.get("tur") == t) for t in ("zorunlu", "tercih", "genel", "gizli", "bilgi")}
    return sonuc


# ============================================================================= PDF → metin + biçim kontrolü
def pdf_metni(pdf: bytes) -> tuple[str, int]:
    from pypdf import PdfReader
    r = PdfReader(io.BytesIO(pdf))
    sayfalar = [(p.extract_text() or "") for p in r.pages]
    return "\n".join(sayfalar).replace("\r", ""), len(r.pages)


_EPOSTA = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_AY = "(?:ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık|oca|şub|mar|nis|may|haz|tem|ağu|eyl|eki|kas|ara)"
_TARIHLER = [("ay_yil", re.compile(rf"(?<![a-zçğıöşü]){_AY}\.?\s+(?:19|20)\d\d\b")),
             ("tam", re.compile(r"\b\d{1,2}[./]\d{1,2}[./](?:19|20)\d\d\b")),
             ("sayisal", re.compile(r"(?<![\d./])\d{1,2}[./](?:19|20)\d\d\b"))]
# U+FFFD (bozuk karakter), özel kullanım alanı (ikon yazı tipleri), denetim karakterleri, emoji ve simgeler
_GARIP_ARALIK = [(0xFFFD, 0xFFFD), (0xE000, 0xF8FF), (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F), (0x7F, 0x9F),
                 (0x1F300, 0x1FAFF), (0x2600, 0x27BF)]
_GARIP = re.compile("[" + "".join(re.escape(chr(a)) + "-" + re.escape(chr(b)) for a, b in _GARIP_ARALIK) + "]")
_ARALIKLI = re.compile(r"(?:\b\w ){4,}\w\b")
TR_HARF = set("çğıöşüÇĞİÖŞÜ")
BICIM_AGIRLIK = {"secilebilir": 25, "basliklar": 20, "iletisim": 15, "tek_sayfa": 15, "karakter": 15, "tarih": 10}


def bicim_kontrolu(metin: str, sayfa: int, kaynak_metin: str = "") -> dict:
    """Ayrıştırılmış PDF metni üzerinde ATS biçim kontrolleri. kaynak_metin: CV'nin özgün metni (Türkçe harf karşılaştırması için)."""
    M = []

    def madde(kod, ad, durum, aciklama, oneri, ayrinti=None):
        a = BICIM_AGIRLIK[kod]
        M.append({"kod": kod, "ad": ad, "agirlik": a, "durum": durum, "aciklama": aciklama, "oneri": oneri, "ayrinti": ayrinti or [],
                  "puan": a if durum == "tamam" else (a / 2 if durum == "kismen" else 0)})

    duz = metin.strip()
    harf = sum(c.isalpha() for c in duz)
    tr_kayip = bool(set(kaynak_metin) & TR_HARF) and not (set(duz) & TR_HARF)
    madde("secilebilir", "Metin seçilebilir ve okunuyor", "tamam" if harf >= 80 and not tr_kayip else ("kismen" if harf >= 80 else "eksik"),
          "ATS, CV'ndeki metni dosyadan çıkararak okur. Fotoğrafı çekilmiş ya da görüntü olarak kaydedilmiş bir CV'de çıkarılacak metin yoktur.",
          "İyi: PDF'teki metin seçilebilir; Türkçe harfler de doğru çıkıyor." if harf >= 80 and not tr_kayip
          else ("Türkçe harfler (ç, ğ, ı, ö, ş, ü) metne doğru geçmiyor; başka bir yazı tipiyle yeniden kaydet." if harf >= 80
                else "PDF'ten neredeyse hiç metin çıkmadı. CV'ni taranmış görüntü olarak değil, metin olarak kaydet."))

    bolumler = bolumlere_ayir(duz)
    basliklar = [b for b in bolumler if b["baslik"]]
    standart = [b["baslik"] for b in basliklar if b["kod"]]
    ozel = [b["baslik"] for b in basliklar if not b["kod"]]
    kodlar = {b["kod"] for b in basliklar}
    temel = {"egitim", "beceriler"} <= kodlar and bool(kodlar & {"deneyim", "projeler", "gonulluluk"})
    madde("basliklar", "Standart bölüm başlıkları", "tamam" if temel and not ozel else ("kismen" if len(standart) >= 2 else "eksik"),
          "ATS'ler CV'yi \"Eğitim\", \"Deneyim\", \"Beceriler\" gibi tanıdık başlıklarla bölümlere ayırır. \"Maceralarım\" gibi yaratıcı başlıkları tanımayabilir.",
          ("Şu başlıkları standart bir adla değiştir: " + ", ".join(ozel)) if ozel
          else ("İyi: başlıklar tanınıyor." if temel else "Eğitim, Beceriler ve en az bir Deneyim/Proje/Gönüllülük bölümü olsun."),
          [f"Tanınan: {', '.join(standart) or '—'}"] + ([f"Tanınmayan: {', '.join(ozel)}"] if ozel else []))

    ust = "\n".join(bolumler[0]["satirlar"][:6])
    eposta = _EPOSTA.findall(ust) or _EPOSTA.findall(duz[:600])
    ad_var = bool(bolumler[0]["satirlar"]) and len(re.findall(r"[^\W\d_]+", bolumler[0]["satirlar"][0])) >= 2
    madde("iletisim", "İletişim bilgisi ayrıştırılabiliyor", "tamam" if eposta and ad_var else ("kismen" if eposta or ad_var else "eksik"),
          "ATS, adını ve e-postanı genellikle metnin en üstünde arar. Bu bilgiler üst bilgi/alt bilgi alanında ya da görselde olursa bulunamayabilir.",
          ("İyi: ad ve e-posta (" + eposta[0] + ") en üstte bulundu.") if eposta and ad_var
          else ("E-posta adresi bulunamadı; geçerli bir e-posta ekle." if not eposta else "En üst satırda ad soyad bulunamadı."),
          eposta[:1])

    bicimler = {ad for ad, r in _TARIHLER if r.search(tr_kucuk(duz))}
    # 'tam' (gün.ay.yıl) varsa 'sayisal' deseni onun parçası olarak da eşleşebilir — ayrı sayılmaz
    if "tam" in bicimler and not re.search(r"(?<![\d./])\d{1,2}[./](?:19|20)\d\d\b(?![./]\d)", re.sub(r"\b\d{1,2}[./]\d{1,2}[./](?:19|20)\d\d\b", "", duz)):
        bicimler.discard("sayisal")
    AD = {"ay_yil": "Ay Yıl (Eylül 2024)", "sayisal": "09/2024", "tam": "01.09.2024"}
    madde("tarih", "Tarih biçimi tutarlı", "tamam" if len(bicimler) == 1 else ("kismen" if not bicimler else "eksik"),
          "ATS'ler tarihleri deneyim sürelerini anlamak için okur. Tek biçim hem makinenin hem de okuyan kişinin işini kolaylaştırır.",
          ("İyi: tüm tarihler aynı biçimde (" + AD[next(iter(bicimler))] + ").") if len(bicimler) == 1
          else ("Tarih bulunamadı; deneyimlerine dönem ekle (ör. Eylül 2024 – Haziran 2025)." if not bicimler
                else "Birden fazla biçim var (" + ", ".join(AD[b] for b in sorted(bicimler)) + "); hepsini aynı biçime çevir."),
          sorted(AD[b] for b in bicimler))

    madde("tek_sayfa", "Tek sayfa", "tamam" if sayfa == 1 else "eksik",
          "Lise öğrencisi için bir sayfa yeter. İkinci sayfa çoğu zaman okunmaz; ATS de uzun metinde anahtar kelimeleri sulandırır.",
          "İyi: tek sayfa." if sayfa == 1 else f"Şu an {sayfa} sayfa: ilgisiz öğeleri gizle, açıklamaları kısalt.")

    garip = sorted({f"U+{ord(c):04X}" for c in _GARIP.findall(duz)})
    aralikli = _ARALIKLI.findall(duz)
    madde("karakter", "Garip karakter / ikon yok", "tamam" if not garip and not aralikli else ("kismen" if len(garip) + len(aralikli) <= 2 else "eksik"),
          "İkonlar, emojiler ve özel yazı tipleri ATS'nin gördüğü metinde anlamsız karakterlere ya da boşluklara dönüşebilir. "
          "\"Ö Z G E Ç M İ Ş\" gibi harf aralıklı yazılar da tek kelime olarak okunamaz.",
          "İyi: anlamsız karakter yok." if not garip and not aralikli
          else "Emoji/ikon ve harf aralıklı yazıları kaldır; yerine düz metin yaz.",
          ([f"{len(_GARIP.findall(duz))} anlamsız karakter (kod: {', '.join(garip[:4])})"] if garip else [])
          + [f"Harf aralıklı: {a.strip()}" for a in aralikli[:3]])

    puan = round(sum(m["puan"] for m in M))
    return {"puan": puan, "tamam": sum(1 for m in M if m["durum"] == "tamam"), "toplam": len(M), "maddeler": M,
            "bolumler": [{"baslik": b["baslik"], "kod": b["kod"], "standart": bool(b["kod"])} for b in basliklar]}
