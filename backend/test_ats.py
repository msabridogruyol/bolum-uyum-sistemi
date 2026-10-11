"""ATS kontrolü (app/core/ats.py) izole testi — DB'siz; CV PDF'i gerçekten üretilip pypdf ile ayrıştırılır. Çalıştır: python3 test_ats.py"""
import json
import os
import sys

os.environ.setdefault("DATABASE_URL", "sqlite:///./_test_ats.db")
sys.path.insert(0, ".")

from app.core import ats  # noqa: E402
from app.api.is_hayati_cv import cv_pdf, _temizle  # noqa: E402


def basarili(kosul, mesaj):
    print(("✓ " if kosul else "✗ ") + mesaj)
    assert kosul, mesaj


# --- normalize + kök ---
basarili(ats.tr_kucuk("İSTANBUL IŞIK") == "istanbul ışık", "Türkçe küçük harf: İ→i, I→ı")
basarili(ats.kok("projelerinde") == ats.kok("projeyi") == ats.kok("proje"), "kök: proje / projeyi / projelerinde aynı köke iner")
basarili(ats.kok("ekibimize") == ats.kok("ekip") == ats.kok("takım"), "kök: ünsüz yumuşaması (ekib→ekip) + eşanlam (takım→ekip)")
basarili(ats.kok("iletişimi") == ats.kok("iletişim"), "kök: iletişimi → iletişim")
basarili(ats.kok("excel") == "excel" and ats.kok("python") == "python", "araç adları budanmaz")
basarili(not ats._icerik_kelimesi("ve") and not ats._icerik_kelimesi("deneyimi"), "durak sözcüğü ve ilan dolgusu atılır")
basarili(not ats._icerik_kelimesi("doldurmuş") and not ats._icerik_kelimesi("alabilen"), "sıfat-fiil görünümlü kelimeler atılır")

# --- ilan satırları: alt başlık + ipucu sözcükleri ---
ILAN = """Aranan Nitelikler:
- Excel ve Word bilgisi zorunludur.
- Takım çalışmasına yatkın, iletişimi güçlü.
- İngilizce okuyup anlayabilen.
Tercih Sebebi:
- Python ya da Scratch ile proje deneyimi olan.
- Sosyal medya hesaplarını yönetmiş olmak artıdır.
Şirket hakkında: Ekibimiz 20 kişiden oluşur."""
satir = ats.ilan_satirlari(ILAN)
tur = {s["metin"][:10]: s["tur"] for s in satir}
basarili(tur["Excel ve W"] == "zorunlu", "zorunlu satır tanındı")
basarili(tur["Python ya "] == "tercih", "'Tercih Sebebi' alt başlığı altındaki satır tercih")
basarili(tur["Ekibimiz 2"] == "genel", "'Şirket hakkında:' nitelik bölümünü kapatır")

anahtar = ats.anahtar_kelimeler(satir)
ifadeler = {a["ifade"]: a for a in anahtar}
basarili("excel" in ifadeler and ifadeler["excel"]["agirlik"] == 3.0, "excel zorunlu ağırlığıyla (3) çıkarıldı")
basarili("takım çalışması" in ifadeler, "öbek: 'takım çalışması' tek anahtar olarak çıkarıldı")
basarili(ifadeler["python"]["agirlik"] == 2.0, "tercih edilen nitelik ağırlığı 2")
basarili("ve" not in ifadeler and "deneyimi" not in ifadeler and "bilgisi" not in ifadeler, "dolgu sözcükleri anahtar değil")
basarili(all(ifadeler.get(k, {"agirlik": 0})["agirlik"] <= 1 for k in ("ekibimiz", "kişiden")), "şirket tanıtım satırı düşük ağırlıkta")

# --- gerçek PDF: üret → ayrıştır → biçim kontrolü ---
icerik = _temizle({
    "kisisel": {"ad": "Deniz Yılmaz", "eposta": "deniz.yilmaz@ornek.com", "sehir": "İzmir"},
    "profil": "11. sınıf öğrencisiyim; okul robotik takımında iki yıldır yazılım sorumlusuyum. Yaz döneminde gözlem stajı arıyorum.",
    "bolumler": [
        {"kod": "egitim", "ogeler": [{"baslik": "Örnek Anadolu Lisesi", "kurum": "Lise, 11. sınıf", "donem": "Eylül 2023 – devam ediyor"}]},
        {"kod": "deneyim", "ogeler": [{"baslik": "Robotik kulübü yazılım sorumlusu", "kurum": "Örnek Anadolu Lisesi",
                                       "donem": "Ekim 2024 – Mayıs 2025",
                                       "aciklama": "Ekip çalışmasıyla 4 kişilik takımda engelden kaçan araç tasarladık.\nSensör kodunu Python ile yazdım."}]},
        {"kod": "projeler", "ogeler": [{"baslik": "Hava durumu sayfası", "kurum": "Kişisel proje", "donem": "Mart 2025",
                                        "aciklama": "JavaScript ile web sayfası geliştirdim."}]},
        {"kod": "beceriler", "ogeler": ["Python", "JavaScript", "Excel", "Canva"]},
        {"kod": "diller", "ogeler": [{"dil": "İngilizce", "seviye": "B1"}]},
    ]})
pdf, _ = cv_pdf(icerik)
metin, sayfa = ats.pdf_metni(pdf)
basarili(sayfa == 1 and "deniz.yilmaz@ornek.com" in metin, "PDF ayrıştırıldı: tek sayfa, e-posta metinde")
basarili("ĞİTİM" in metin and "İzmir" in metin, "Türkçe harfler ayrıştırmada bozulmuyor")
basarili("\x7f" not in metin and "•" in metin, "madde işareti düz metinde '•' (denetim karakteri değil)")
b = ats.bicim_kontrolu(metin, sayfa, "ğış")
d = {m["kod"]: m["durum"] for m in b["maddeler"]}
basarili(sum(m["agirlik"] for m in b["maddeler"]) == 100, "biçim ağırlıkları toplamı 100")
basarili(d == {"secilebilir": "tamam", "basliklar": "tamam", "iletisim": "tamam", "tarih": "tamam", "tek_sayfa": "tamam", "karakter": "tamam"},
         f"sistemin ürettiği düzgün CV tüm biçim maddelerini geçer ({b['puan']}/100)")

# yaratıcı başlık + karışık tarih + emoji → yakalanır
bozuk = json.loads(json.dumps(icerik))
bozuk["bolumler"][1]["baslik"] = "Maceralarım"
bozuk["bolumler"][2]["ogeler"][0]["donem"] = "03/2025"
bozuk["bolumler"][2]["ogeler"][0]["aciklama"] = "JavaScript ile web sayfası geliştirdim 🚀"
pdf2, _ = cv_pdf(bozuk)
m2, s2 = ats.pdf_metni(pdf2)
d2 = {m["kod"]: m for m in ats.bicim_kontrolu(m2, s2)["maddeler"]}
basarili(d2["basliklar"]["durum"] == "kismen" and "MACERALARIM" in d2["basliklar"]["oneri"], "standart olmayan başlık bulundu")
basarili(d2["tarih"]["durum"] == "eksik", "karışık tarih biçimi (Ay Yıl + 03/2025) bulundu")
basarili(d2["karakter"]["durum"] != "tamam", "emoji / bozuk karakter bulundu")
basarili(ats.bicim_kontrolu("", 1)["maddeler"][0]["durum"] == "eksik", "metin çıkmayan (görüntü) CV: 'seçilebilir' eksik")
basarili(ats.bicim_kontrolu(metin, 2)["maddeler"][4]["durum"] == "eksik", "iki sayfa: tek sayfa maddesi eksik")

# --- eşleştirme ---
u = ats.ilan_uyumu(satir, metin)
bul = {x["ifade"]: x for x in u["bulunan"]}
eks = {x["ifade"]: x for x in u["eksik"]}
basarili("excel" in bul and bul["excel"]["bolum"] == "beceriler", "excel bulundu, Beceriler bölümünde")
basarili("takım çalışması" in bul, "öbek eşanlamla bulundu (ilan 'takım çalışması', CV 'Ekip çalışmasıyla')")
basarili("word" in eks and eks["word"]["bolum"] == "beceriler", "word eksik → Beceriler'e yerleştirme önerisi")
basarili("sosyal medya" in eks, "eksik öbek listelendi")
basarili(eks.get("ingilizce") is None and "ingilizce" in bul and bul["ingilizce"]["bolum"] == "diller", "dil Diller bölümünde bulundu")
basarili(0 < u["uyum"] < 100, f"uyum yüzdesi aralıkta ({u['uyum']}%)")
bos = ats.eslestir(ats.anahtar_kelimeler(satir), "")
basarili(bos["uyum"] == 0 and not bos["bulunan"], "boş CV: uyum %0")
tam = ats.eslestir(ats.anahtar_kelimeler([{"metin": "Excel bilgisi zorunludur.", "tur": "zorunlu"}]), "BECERİLER\nExcel")
basarili(tam["uyum"] == 100, "tek anahtar bulunan: uyum %100")
yarim = ats.eslestir([{"ifade": "sosyal medya", "kokler": [ats.kok("sosyal"), ats.kok("medya")], "agirlik": 2.0, "tur": "tercih"}], "Medya ve sosyal etkinlikler")
basarili(yarim["uyum"] == 50 and yarim["kismen"], "öbeğin kelimeleri var ama yan yana değil: yarım puan")

# --- örnek ilanların hepsi çalışır ve 'bilgi' satırları anahtar üretmez ---
ilanlar = json.loads(open("app/data/ornek_ilanlar.json", encoding="utf-8").read())["ilanlar"]
for il in ilanlar:
    st = [{"metin": s["metin"], "tur": s["dogru"]} for s in il["satirlar"]]
    a = ats.anahtar_kelimeler(st)
    basarili(3 <= len(a) <= 20, f"örnek ilan '{il['id']}': {len(a)} anahtar")
basarili(not ats.anahtar_kelimeler([{"metin": "Yemek ve ulaşım desteği sağlanır.", "tur": "bilgi"}]), "'bilgi' satırı anahtar üretmez")

# --- rehber verisi tutarlı ---
r = json.loads(open("app/data/cv_rehberi.json", encoding="utf-8").read())
for k in r["konular"]:
    basarili(all(x in r["kaynaklar"] for x in k["kaynaklar"]) and 2 <= len(k["sinav"]) <= 3
             and all(0 <= s["dogru"] < len(s["secenekler"]) for s in k["sinav"]), f"rehber konusu '{k['kod']}': kaynaklar + mini sınav geçerli")

if os.path.exists("_test_ats.db"):
    os.remove("_test_ats.db")
print("\nTüm ATS testleri geçti.")
