# -*- coding: utf-8 -*-
"""
[2026-10-11] Filiz — yönetim paneli asistanının yapay zekâ modu ve yönlendirme katmanı.

Etkinlik (ai_modu):
  okul yetkilisi → OPENAI_API_KEY tanımlı VE okulun paketinde 'filiz_ai'; süper admin → anahtar tanımlı.
  Değilse kural tabanlı rehber (app/core/filiz_yonetim_rehber.yanitla) aynen çalışır. Yapay zekâ çağrısı hata / zaman aşımı
  verirse ya da günlük sınır dolarsa da rehber cevabı döner. Yanıtta mod: 'ai' | 'rehber'.

Her soruda yönlendirme sırası (yanitla_yonetim):
  (i)   kriz ifadesi (öğrencideki KRIZ_IFADELERI) → sabit yönlendirme: okulun kriz protokolü, 112, ALO 183. Model çağrılmaz.
  (ii)  KİŞİYE ÖZEL VERİ NİYETİ → yapay zekâya GİTMEZ; yetki kapsamında YEREL cevap:
          - belirli bir öğrenci: ad-soyad (kapsamdaki öğrencilerin ad dizini), e-posta, "no 123", ya da kapsam dışı bir ad
            olabilecek büyük harfli ad çifti + kişi kelimesi. Okul yetkilisi yalnızca kendi okulunda aranır; bulunamayan /
            başka okuldaki kişi için AYNI cümle: "Bu isimde okulunuzda bir öğrenci bulunamadı" (başka okulda olup olmadığı
            belli edilmez). Süper admin tüm sistemde arar. Cevap: kısa özet + öğrenci detayına derin bağlantı
            (/admin/okul/{okul}?sekme=ogrenciler&ogrenci={id}).
          - kişi listesi ("kritik öğrencilerim kimler", "en düşük netler kimin") → isim verilmez; ilgili ekrana bağlantı.
  (iii) diğer sorular → yapay zekâ. Bağlam: SSS (filiz_yonetim_rehber.YONETIM_SSS, tek kaynak), rol bazlı sayfa listesi,
        kapsamın toplu bulguları (filiz_ozeti metinleri; isimsiz). Gönderilmeden önce soru ve sohbet geçmişi maskelenir:
        e-posta, telefon, TC, öğrenci no ve kapsamdaki öğrenci adları → "[öğrenci]", ad benzeri çiftler → "[kişi]".
        Cevap son filtreden geçer (kapsamdaki bir öğrenci adı geçerse maskelenir).
Sorular kaydedilmez; yalnızca yönetici başına günlük sayaç (filiz_yonetim_sayac, sınır: filiz_yonetim_gunluk_limit, 50).
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import filiz_gizlilik as G
from app.core import filiz_yonetim_rehber as R

_log = logging.getLogger("filiz_yonetim_ai")

GUNLUK_LIMIT_VARSAYILAN = 50
GECMIS_EN_FAZLA = 6          # son 3 tur (soru + cevap)
EN_FAZLA_LISTE = 8

KRIZ_YONETIM_YANITI = (
    "Bir öğrencinin güvenliğiyle ilgili acil bir durum varsa lütfen okulunuzun kriz / acil durum protokolünü hemen uygulayın: "
    "öğrenciyi yalnız bırakmayın, okulun psikolojik danışmanını ve okul yönetimini bilgilendirin, veliyle iletişime geçin. "
    "Hayati tehlike varsa 112 Acil Çağrı'yı arayın; ALO 183 Sosyal Destek Hattı 7/24 açıktır. "
    "Görüşmeyi daha sonra Rehberlik sekmesinde kayıt altına alabilirsiniz."
)


# ============================================================================= etkinlik, sayaç
def ai_modu(db: Session, yon) -> bool:
    from app.core.ai_koc_servisi import asistan_aktif_mi
    if not asistan_aktif_mi():
        return False
    if yon.rol == R.SUPER:
        return True
    if not yon.okul_id:
        return False
    from app.core.paketler import okul_modulleri
    return "filiz_ai" in okul_modulleri(db, yon.okul_id)


def gunluk_limit(db: Session) -> int:
    from app.core.katman_servisi import parametre_oku
    try:
        return max(1, int(parametre_oku(db, "filiz_yonetim_gunluk_limit", str(GUNLUK_LIMIT_VARSAYILAN))))
    except Exception:
        return GUNLUK_LIMIT_VARSAYILAN


def _bugun_tr():
    from app.core.haftalik_servisi import TR_SAAT
    return datetime.now(timezone.utc).astimezone(TR_SAAT).date()


def bugun_sayi(db: Session, yon) -> int:
    try:
        with db.begin_nested():
            return int(db.execute(text("SELECT sayi FROM filiz_yonetim_sayac WHERE admin_id = :a AND gun = :g"),
                                  {"a": yon.id, "g": _bugun_tr()}).scalar() or 0)
    except Exception:
        return 0


def sayac_artir(db: Session, yon) -> None:
    try:
        with db.begin_nested():
            db.execute(text("""INSERT INTO filiz_yonetim_sayac (admin_id, gun, sayi) VALUES (:a, :g, 1)
                               ON CONFLICT (admin_id, gun) DO UPDATE SET sayi = filiz_yonetim_sayac.sayi + 1"""),
                       {"a": yon.id, "g": _bugun_tr()})
        db.commit()
    except Exception:
        db.rollback()


# ============================================================================= kişiye özel veri niyeti
_LISTE_SORU = re.compile(r"(?:^|\s)(kim|kimler|kimin|kimlerin|kimde|kimlerde|kimdir|isim\w*|adlari\w*|listele\w*|hangi ogrenci\w*|hangileri)(?:\s|$)")
_LISTE_EN = re.compile(r"(?:^|\s)en (yuksek|dusuk|basarili|basarisiz|iyi|kotu|cok|az|riskli|kritik|gec)\w* .*(ogrenci|net|puan)")
_LISTE_KONU = ("ogrenci", "net", "puan", "kritik", "risk", "uyari", "sonuc", "test", "basari", "deneme", "giris", "sinif", "sube",
               "gorusme", "tercih", "kulup", "devam", "yarim", "dusuk", "yuksek")
# Ad benzeri çiftten sonra "belirli bir kişi" sorusu olduğunu gösteren kelimeler ("öğrencilere" gibi genel kullanım sayılmaz;
# o durumda çift yalnızca "[kişi]" olarak maskelenip soru yapay zekâya gider — ör. "Elif Şafak kitabı önerilir mi").
_KISI_KELIME = ("sonuc", "puan", "net", "hedef", "durum", "ilerle", "profil", "uyari", "gorusme", "detay", "sifre", "sinifi",
                "subesi", "numara", "ogrencisi", "ogrencim", "ogrencimiz", "velisi", "nasil gidiyor", "hakkinda bilgi", "dosyasi",
                "kayitlari", "testi", "raporu", "tercih", "deneme")


def _n(metin: str) -> str:
    return R.normalize(metin)


def _icerir(n: str, kokler) -> bool:
    return any(re.search(r"(?:^|\s)" + re.escape(k), n) for k in kokler)


def kisi_niyeti(metin: str, dizin: G.AdDizini) -> dict | None:
    """{'tur': 'ogrenci', 'kayitlar': [...]} | {'tur': 'liste', 'n': normalize} | None"""
    n = _n(metin)
    epostalar, numaralar = G.eposta_bul(metin), G.ogrenci_no_bul(metin)
    adlar = dizin.bul(metin)
    if epostalar or numaralar or adlar:
        kayitlar = list(adlar)
        if epostalar:
            kayitlar += [k for k in dizin.kayitlar if k.email and k.email in epostalar]
        if numaralar:
            kayitlar += [k for k in dizin.kayitlar if k.ogrenci_no and str(k.ogrenci_no).strip() in numaralar]
        gorulen, tek = set(), []
        for k in kayitlar:
            if k.id not in gorulen:
                gorulen.add(k.id)
                tek.append(k)
        return {"tur": "ogrenci", "kayitlar": tek}
    ciftler = G.ad_benzeri_ciftler(metin)
    if ciftler:
        kalan = metin
        for b, s in reversed(ciftler):
            kalan = kalan[:b] + " " + kalan[s:]
        sonrasi = metin[ciftler[0][1]:ciftler[0][1] + 2]
        if sonrasi[:1] in ("'", "’") or _icerir(_n(kalan), _KISI_KELIME) or len(R._kokler(kalan)) <= 1:
            return {"tur": "ogrenci", "kayitlar": []}   # kapsamda böyle biri yok: bulunamadı (başka yerde olup olmadığı söylenmez)
    if (_LISTE_SORU.search(n) and _icerir(n, _LISTE_KONU)) or _LISTE_EN.search(n):
        return {"tur": "liste", "n": n}
    return None


def _ogrenci_ozetleri(db: Session, kayitlar: list[G.OgrenciKaydi]) -> dict:
    ids = [G.kimlik_uuid(k.id) for k in kayitlar if G.kimlik_uuid(k.id)]
    if not ids:
        return {}
    try:
        with db.begin_nested():
            satirlar = db.execute(text("""
                SELECT o.id, o.son_giris_zamani,
                       (SELECT t.durum FROM ogrenci_degerlendirme_turu t WHERE t.ogrenci_id = o.id ORDER BY t.tur_no DESC LIMIT 1) AS tur_durum,
                       (SELECT count(*) FROM ogrenci_katman_oturumlari k JOIN katmanlar km ON km.id = k.katman_id
                         WHERE k.ogrenci_id = o.id AND k.durum = 'tamamlandi' AND NOT km.kosullu_mu
                           AND k.tur_id = (SELECT t.id FROM ogrenci_degerlendirme_turu t WHERE t.ogrenci_id = o.id ORDER BY t.tur_no DESC LIMIT 1)) AS biten
                  FROM ogrenciler o WHERE o.id = ANY(:i)"""), {"i": ids}).all()
    except Exception:
        return {}
    return {str(r.id): r for r in satirlar}


def _ogrenci_yolu(k: G.OgrenciKaydi) -> str:
    return f"/admin/okul/{k.okul_id or 0}?sekme=ogrenciler&ogrenci={k.id}"


def _bulunamadi(yon) -> dict:
    bos = {"cevaplar": [], "bulgular": [], "oneriler": [], "ogrenciler": []}
    if yon.rol == R.SUPER:
        return {**bos, "tur": "ogrenci", "metin": "Bu bilgilerle sistemde bir öğrenci bulunamadı. Okullar → okul → Öğrenciler'de ad, e-posta ya da numarayla arayabilirsiniz.",
                "baglantilar": [{"etiket": "Okullar", "yol": "/admin/okullar"}, {"etiket": "Okul Harici Öğrenciler", "yol": "/admin/okul/0?sekme=ogrenciler"}]}
    return {**bos, "tur": "ogrenci", "metin": "Bu isimde okulunuzda bir öğrenci bulunamadı. Öğrenciler sekmesinde ad, e-posta ya da numarayla arayabilirsiniz.",
            "baglantilar": [R._bag("Öğrenciler", "ogrenciler", R.OKUL, yon.okul_id)]}


def ogrenci_yaniti(db: Session, yon, kayitlar: list[G.OgrenciKaydi]) -> dict:
    if not kayitlar:
        return _bulunamadi(yon)
    ozet = _ogrenci_ozetleri(db, kayitlar[:EN_FAZLA_LISTE])
    liste = []
    for k in kayitlar[:EN_FAZLA_LISTE]:
        r = ozet.get(k.id)
        if r is None or r.tur_durum is None:
            deg = "değerlendirmeye başlamadı"
        elif r.tur_durum == "tamamlandi":
            deg = "değerlendirmeyi tamamladı"
        else:
            deg = f"değerlendirmede {r.biten or 0} katman tamamlandı"
        giris = (f"son giriş {r.son_giris_zamani.strftime('%d.%m.%Y')}" if r is not None and r.son_giris_zamani else "henüz giriş yapmadı")
        sinif = " ".join(x for x in (k.sinif, f"({k.sube})" if k.sube else None) if x)
        bilgi = " · ".join(x for x in (sinif or None, (k.okul_ad or "okul harici") if yon.rol == R.SUPER else None,
                                        f"no {k.ogrenci_no}" if k.ogrenci_no else None, deg, giris) if x)
        liste.append({"id": k.id, "ad_soyad": k.ad_soyad, "bilgi": bilgi, "baglanti": {"etiket": "Öğrenci detayı", "yol": _ogrenci_yolu(k)}})
    yer = "sistemde" if yon.rol == R.SUPER else "okulunuzda"
    metin = (f"{yer.capitalize()} eşleşen öğrenci:" if len(kayitlar) == 1
             else f"{yer.capitalize()} eşleşen {len(kayitlar)} öğrenci var" + (f"; ilk {EN_FAZLA_LISTE} tanesi:" if len(kayitlar) > EN_FAZLA_LISTE else ":"))
    return {"tur": "ogrenci", "metin": metin, "ogrenciler": liste, "baglantilar": [], "cevaplar": [], "bulgular": [], "oneriler": []}


def liste_yaniti(yon, n: str) -> dict:
    """Kişi listeleri sohbette verilmez (ekranı başkaları görebilir, dış servise gitmez): ilgili ekran."""
    okul = yon.rol == R.OKUL

    def b(etiket, sayfa):
        return R._bag(etiket, sayfa, yon.rol, yon.okul_id)
    if okul:
        if _icerir(n, ("kritik", "risk", "uyari", "gorusme", "dikkat", "devam", "yarim")):
            bag, ne = [b("Rehberlik", "rehberlik"), b("Tek Bakışta", "raporlar")], "Dikkat gerektiren öğrencilerin listesi (seviye, neden, son görüşme) Rehberlik → erken uyarı listesinde; kritik öğrenciler Rapor Merkezi → Tek Bakışta'da."
        elif _icerir(n, ("net", "deneme", "puan", "basari", "sirala", "dusuk", "yuksek")):
            bag, ne = [b("Tek Bakışta", "raporlar"), b("Okul Denemeleri", "denemeler")], "Deneme sıralamaları ve en düşük / en yüksek netler Rapor Merkezi → Tek Bakışta'da; deneme bazında sonuçlar Okul Denemeleri'nde."
        elif _icerir(n, ("tercih", "mezun", "yerles")):
            bag, ne = [b("Tercih Dönemi", "tercih"), b("Mezunlar", "mezunlar")], "Tercih listeleri Tercih Dönemi'nde, yerleşmeler Mezunlar'da."
        elif _icerir(n, ("kulup",)):
            bag, ne = [b("Kulüpler", "kulupler")], "Kulüp üyeleri ve bekleyen talepler Kulüpler sekmesinde."
        else:
            bag, ne = [b("Öğrenciler", "ogrenciler"), b("Tek Bakışta", "raporlar")], "Öğrenci listesi (durum, sınıf ve şube süzgeçleriyle) Öğrenciler sekmesinde; öne çıkan öğrenciler Rapor Merkezi → Tek Bakışta'da."
    else:
        bag = [{"etiket": "Okullar", "yol": "/admin/okullar"}, {"etiket": "Okul Karşılaştırması", "yol": "/admin/karsilastirma"},
               {"etiket": "Kontrol Paneli", "yol": "/admin"}]
        ne = "Öğrenci listeleri okul panellerinde (Okullar → okul → Öğrenciler / Rehberlik / Rapor Merkezi → Tek Bakışta); okul bazında sayılar Okul Karşılaştırması'nda."
    return {"tur": "yanit", "metin": "Öğrenci listelerini sohbette paylaşmıyorum; ilgili ekranda süzgeçlerle görebilirsiniz. " + ne,
            "baglantilar": [x for x in bag if x], "cevaplar": [], "bulgular": [], "oneriler": [], "ogrenciler": []}


# ============================================================================= yapay zekâ bağlamı
def sayfa_listesi(yon) -> list[dict]:
    """Rol bazlı bağlantı listesi (etiket → yol). Model yalnızca bunlardan seçebilir."""
    gorulen, l = set(), []

    def ekle(etiket, sayfa):
        x = R._bag(etiket, sayfa, yon.rol, yon.okul_id)
        if x and x["etiket"] not in gorulen:
            gorulen.add(x["etiket"])
            l.append(x)
    if yon.rol == R.OKUL:
        for k, ad in R._SAYFA_ADI.items():
            ekle(ad, k)
        ekle("Kayıtlar", "kayitlar")
        ekle("Mezunlar", "mezunlar")
        ekle("Tek Bakışta", "raporlar")
    for niy in R.NIYETLER:
        if yon.rol in niy["rol"]:
            for etiket, sayfa in niy["bag"]:
                ekle(etiket, sayfa)
    if yon.rol == R.SUPER:
        for no, bas, _ in R.SISTEM_HAKKINDA:
            ekle(f"Sistem Hakkında — {bas}", f"/admin/sistem-hakkinda#sh-{no}")
    return l


def sistem_istemi(db: Session, yon, dizin: G.AdDizini) -> str:
    rol_adi = "bir okulun yetkilisine (müdür, müdür yardımcısı, rehber öğretmen)" if yon.rol == R.OKUL else "Filizyol'un sistem yöneticisine (süper admin)"
    sss = "\n".join(f"- S: {s}\n  C: {c}" for _, s, c, _ in R.YONETIM_SSS)
    kisa = "\n".join(f"- {niy['metin']}" for niy in R.NIYETLER if yon.rol in niy["rol"])
    sayfalar = "\n".join(f"- {x['etiket']}" for x in sayfa_listesi(yon))
    try:
        bulgular = [b["metin"] for b in R.filiz_ozeti(db, yon)["bulgular"]]
    except Exception:
        db.rollback()
        bulgular = []
    bulgu_metni = "\n".join(f"- {G.ad_benzerlerini_maskele(dizin.maskele(G.temel_maskele(b)))}" for b in bulgular) or "- (şu an öne çıkan bir konu yok)"
    kapsam = "okulun" if yon.rol == R.OKUL else "sistemin"
    return f"""Sen "Filiz"sin: Filizyol adlı lise bölüm / meslek rehberlik sisteminin yönetim paneli kullanım asistanısın. {rol_adi} panelin nasıl kullanılacağı, ekranlardaki göstergelerin ne anlama geldiği ve rehberlik çalışmalarının nasıl yürütüleceği konusunda yardım ediyorsun.

KURALLAR (kesinlikle uy):
1. Yalnızca aşağıdaki SSS, kısa yönlendirmeler, sayfa listesi ve toplu bulgulara dayan. Bilmediğin bir özelliği, ekranı ya da sayıyı UYDURMA; emin değilsen "Bunu panelde göremiyorum; Sistem Hakkında & SSS sayfasına ya da sistem yöneticisine danışabilirsiniz" de.
2. Hiçbir öğrenci hakkında bilgi verme, uydurma ya da tahmin yürütme; öğrenci adı yazma. Soruda "[öğrenci]", "[kişi]", "[e-posta]", "[numara]" gibi yer tutucular gizlenmiş kişisel verilerdir: onları çözmeye çalışma, kişiye özel bilginin panelde öğrencinin detay penceresinde olduğunu söyle.
3. Kullanıcıdan kişisel veri (öğrenci adı, numarası, e-postası, TC kimlik no) isteme.
4. Kısa ve maddeli Türkçe yaz (en fazla 6 kısa madde ya da 2-3 cümle). Resmî ama sıcak bir dil kullan, "siz" diye hitap et.
5. İlgili sayfa önermek istersen cevabın EN SONUNA her biri ayrı satırda en fazla 3 satır "SAYFA: <sayfa adı>" yaz; sayfa adını YALNIZCA aşağıdaki SAYFA LİSTESİ'nden, harfi harfine seç. Listede olmayan sayfa yazma.
6. Rehberlik / psikolojik danışmanlık sorularında genel, mesleki ilkelere uygun öneriler verebilirsin; teşhis koyma. Bir öğrencinin güvenliği söz konusuysa okulun kriz protokolünü, 112'yi ve ALO 183'ü hatırlat.
7. Konu Filizyol paneli ya da okul rehberliği dışındaysa kısaca nazikçe panelle ilgili konulara dön.

SSS:
{sss}

KISA YÖNLENDİRMELER:
{kisa}

SAYFA LİSTESİ:
{sayfalar}

{kapsam.upper()} BUGÜNKÜ TOPLU BULGULARI (yalnızca sayılar):
{bulgu_metni}
"""


def soru_maskele(metin: str, dizin: G.AdDizini) -> str:
    return G.ad_benzerlerini_maskele(dizin.maskele(G.temel_maskele(metin or "")))


def _gecmis_mesajlari(gecmis, dizin: G.AdDizini) -> list[dict]:
    l = []
    for x in (gecmis or [])[-GECMIS_EN_FAZLA:]:
        rol = getattr(x, "rol", None) or (x.get("rol") if isinstance(x, dict) else None)
        metin = getattr(x, "metin", None) or (x.get("metin") if isinstance(x, dict) else None)
        if rol not in ("kullanici", "filiz") or not metin:
            continue
        l.append({"role": "user" if rol == "kullanici" else "assistant", "content": soru_maskele(str(metin)[:800], dizin)})
    return l


_SAYFA_SATIRI = re.compile(r"^\s*[-*•]?\s*\**SAYFA\**\s*:\s*(.+?)\s*$", re.I | re.M)


def ai_cevabini_coz(yanit: str, yon, dizin: G.AdDizini) -> tuple[str, list[dict]]:
    etiketler = {x["etiket"].casefold(): x for x in sayfa_listesi(yon)}
    bag, gorulen = [], set()
    for m in _SAYFA_SATIRI.finditer(yanit or ""):
        x = etiketler.get(m.group(1).strip(" .\"'“”").casefold())
        if x and x["yol"] not in gorulen and len(bag) < 3:
            gorulen.add(x["yol"])
            bag.append(x)
    metin = _SAYFA_SATIRI.sub("", yanit or "").strip()
    metin = G.temel_maskele(dizin.maskele(metin))   # son kontrol: kapsamdaki bir öğrenci adı geçerse maskele
    return metin, bag


# ============================================================================= orkestrasyon
def yanitla_yonetim(db: Session, yon, metin: str, gecmis=None) -> dict:
    from app.core.ai_koc_servisi import kriz_mesaji_mi
    ai = ai_modu(db, yon)
    mod = "ai" if ai else "rehber"

    if not (metin or "").strip():
        return {**R.yanitla(db, yon, metin), "mod": mod}
    # (i) kriz
    if kriz_mesaji_mi(metin):
        return {"tur": "kriz", "metin": KRIZ_YONETIM_YANITI, "baglantilar": [x for x in [R._bag("Rehberlik", "rehberlik", yon.rol, yon.okul_id)] if x and yon.rol == R.OKUL],
                "cevaplar": [], "bulgular": [], "oneriler": [], "mod": mod}
    # (ii) kişiye özel veri — yerel, yetki kapsamında
    dizin = G.dizin_yukle(db, tum_sistem=True) if yon.rol == R.SUPER else G.dizin_yukle(db, okul_id=yon.okul_id)
    kisi = kisi_niyeti(metin, dizin)
    if kisi and kisi["tur"] == "ogrenci":
        return {**ogrenci_yaniti(db, yon, kisi["kayitlar"]), "mod": mod}
    if kisi and kisi["tur"] == "liste":
        return {**liste_yaniti(yon, kisi["n"]), "mod": mod}
    # (iii) yapay zekâ ya da rehber
    if not ai:
        return {**R.yanitla(db, yon, metin), "mod": "rehber"}
    if bugun_sayi(db, yon) >= gunluk_limit(db):
        return {**R.yanitla(db, yon, metin), "mod": "rehber",
                "not": "Bugünkü yapay zekâ soru hakkınız doldu; yarına kadar cevaplar rehber modundan geliyor."}
    maskeli = soru_maskele(metin, dizin)
    if G.OGRENCI_ETIKETI in maskeli:   # güvenlik ağı: maskeleme sonrası hâlâ öğrenci verisi isteniyorsa yerel yol
        return {**ogrenci_yaniti(db, yon, dizin.bul(metin)), "mod": mod}
    from app.core import ai_koc_servisi as aks
    try:
        mesajlar = _gecmis_mesajlari(gecmis, dizin) + [{"role": "user", "content": maskeli}]
        yanit = aks.openai_ile_konus(sistem_istemi(db, yon, dizin), mesajlar)
        if not (yanit or "").strip():
            raise aks.AsistanKullanilamiyorHatasi("boş cevap")
    except Exception as e:   # anahtar hatası, kota, ağ, zaman aşımı → kural tabanlı cevap
        _log.warning("Filiz yönetim yapay zekâ çağrısı başarısız, rehber cevabı veriliyor: %s", type(e).__name__)
        db.rollback()
        return {**R.yanitla(db, yon, metin), "mod": "rehber"}
    sayac_artir(db, yon)
    govde, bag = ai_cevabini_coz(yanit, yon, dizin)
    return {"tur": "ai", "metin": govde, "baglantilar": bag, "cevaplar": [], "bulgular": [], "oneriler": [], "mod": "ai"}
