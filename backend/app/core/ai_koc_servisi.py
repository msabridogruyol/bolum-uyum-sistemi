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
from sqlalchemy.orm import Session

from app.models import Ogrenci, Bolum, GelisimKaynakOnerisi
from app.core.katman_servisi import son_tur_getir, IsKuraliHatasi
from app.core.koclugu_servisi import aktif_hedef_getir, gap_analizi_hesapla, gap_kategorisi

MAKSIMUM_TUR = 20  # bir oturumda bu kadar (öğrenci+asistan) mesajdan sonra oturum otomatik kapanır
MODEL_ADI = os.environ.get("OPENAI_MODEL", "").strip() or "gpt-4o-mini"  # Render ortam değişkeniyle değiştirilebilir
GUNLUK_MESAJ_LIMITI_VARSAYILAN = 30  # öğrenci başına günlük mesaj (sistem parametresi: filiz_gunluk_mesaj_limiti)

# [2026-10-04] Öğrenci güvenliği: kullanıcılar reşit olmayan öğrenciler. Kendine zarar / intihar / istismar
# ifadesi geçen mesajlarda model ÇAĞRILMAZ; her zaman aynı, güvenli ve yönlendirici cevap verilir
# (anahtar olmasa da çalışır). Daha örtük durumlar için sistem promptunda ayrıca kural var (madde 8).
KRIZ_IFADELERI = (
    "intihar", "kendimi öldür", "kendimi oldur", "ölmek istiyorum", "olmek istiyorum",
    "yaşamak istemiyorum", "yasamak istemiyorum", "hayatıma son", "hayatima son", "canıma kıy", "canima kiy",
    "kendime zarar", "kendimi kes", "kendimi kesiyorum", "bileklerimi", "yok olmak istiyorum", "her şeye son",
    "bana şiddet", "bana siddet", "taciz", "istismar", "beni dövüyor", "beni dovuyor",
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


def kriz_mesaji_mi(metin: str) -> bool:
    t = _sade(metin)
    return any(ifade in t for ifade in KRIZ_IFADELERI)


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

    guclu_metni = ", ".join(f"{s.degisken.ad} (bölüm beklentisinin üzerinde)" for s in en_guclu if duzeltilmis_fark(s) > 0)
    gelisim_metni = ", ".join(f"{s.degisken.ad} (bölüm beklentisinin altında)" for s in en_gelisim if duzeltilmis_fark(s) < 0)

    parcalar = [f"Hedef bölümü: {bolum_adi}."]
    if guclu_metni:
        parcalar.append(f"Bu bölüme göre en güçlü olduğu yönler: {guclu_metni}.")
    if gelisim_metni:
        parcalar.append(f"Gelişime en açık yönler: {gelisim_metni}.")

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
    "/kesfet": "bölüm keşfetme", "/koclugu": "hedef bölüm koçluğu ve yol haritası", "/profil": "profil ayarları",
}


def sistem_promptu_olustur(db: Session, ogrenci: Ogrenci, onceki_ozet: str | None, sayfa: str | None = None) -> str:
    profil = _ogrenci_profil_ozeti(db, ogrenci)
    ozet_blogu = f"\n\nÖnceki konuşmalardan kısa özet: {onceki_ozet}" if onceki_ozet else ""
    haftalik = _haftalik_ozet_metni(db, ogrenci)
    if haftalik:
        ozet_blogu += f"\n\n{haftalik}"
    sayfa_adi = SAYFA_ADLARI.get(sayfa or "") or (SAYFA_ADLARI["/sonuc"] if (sayfa or "").startswith("/sonuc") else None)
    if sayfa_adi:
        ozet_blogu += f"\n\nÖğrenci şu an sistemin '{sayfa_adi}' sayfasında."

    return f"""Sen "Filiz" adında, Filizyol adlı üniversite bölüm/kariyer koçluğu sisteminde çalışan, öğrenciyle sohbet tarzında konuşan bir kariyer koçusun. İsmin, Filizyol'un "kendi yolunu filizlendir" temasından geliyor — büyümeyi, gelişimi çağrıştıran bir isim.

ÖĞRENCİ: {ogrenci.ad_soyad}
{profil}{ozet_blogu}

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
"""


def openai_ile_konus(sistem_promptu: str, mesaj_gecmisi: list[dict]) -> str:
    """
    mesaj_gecmisi: [{"role": "user"|"assistant", "content": "..."}]
    """
    if not _api_anahtari_var_mi():
        raise AsistanKullanilamiyorHatasi(
            "AI koçluk asistanı henüz aktif değil — OPENAI_API_KEY tanımlanmadı."
        )

    try:
        from openai import OpenAI  # yalnızca anahtar varsa import edilir, gereksiz bağımlılık hatası önlenir
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"].strip(), timeout=40)
        yanit = client.chat.completions.create(
            model=MODEL_ADI,
            messages=[{"role": "system", "content": sistem_promptu}] + mesaj_gecmisi,
            temperature=0.7,
            max_tokens=500,
        )
        return yanit.choices[0].message.content
    except AsistanKullanilamiyorHatasi:
        raise
    except Exception as hata:  # yanlış anahtar, kota, ağ hatası: öğrenciye 500 yerine anlaşılır mesaj
        import logging
        logging.getLogger("ai_koc").warning("OpenAI hatası: %s: %s", type(hata).__name__, hata)
        raise AsistanKullanilamiyorHatasi("Filiz'e şu an ulaşılamıyor, biraz sonra tekrar dene.") from hata


def oturumu_ozetle(sistem_promptu: str, mesaj_gecmisi: list[dict]) -> str:
    """Oturum kapanırken, ham geçmiş yerine bir sonraki oturuma taşınacak kısa özeti üretir."""
    if not _api_anahtari_var_mi():
        return "Özet çıkarılamadı (asistan aktif değil)."

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"].strip(), timeout=40)
    except Exception:
        return None

    ozetleme_istegi = mesaj_gecmisi + [{
        "role": "user",
        "content": "Bu konuşmayı, bir sonraki oturumda hatırlaman için 2-3 cümlelik kısa bir özete çevir. Yalnızca özeti yaz, başka bir şey ekleme.",
    }]
    try:
        yanit = client.chat.completions.create(
            model=MODEL_ADI,
            messages=[{"role": "system", "content": sistem_promptu}] + ozetleme_istegi,
            temperature=0.3,
            max_tokens=150,
        )
        return yanit.choices[0].message.content
    except Exception:  # özet çıkmazsa oturum yine kapanır
        return None
