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

from app.models import Ogrenci, Bolum
from app.core.katman_servisi import son_tur_getir, IsKuraliHatasi
from app.core.koclugu_servisi import aktif_hedef_getir, gap_analizi_hesapla

MAKSIMUM_TUR = 20  # bir oturumda bu kadar (öğrenci+asistan) mesajdan sonra oturum otomatik kapanır
MODEL_ADI = "gpt-4o-mini"


class AsistanKullanilamiyorHatasi(Exception):
    """API anahtarı tanımlı değilse fırlatılır — router bunu 503'e çevirir."""
    pass


def _api_anahtari_var_mi() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _ogrenci_profil_ozeti(db: Session, ogrenci: Ogrenci) -> str:
    """
    Sistem promptuna eklenecek özet — koclugu_servisi.py'nin GERÇEK, zaten
    var olan fonksiyonlarını kullanır (gap_analizi_hesapla, aktif_hedef_getir)
    — burada ayrıca bir hesaplama/varsayım YAPILMAZ, yalnızca sonuçlar
    doğal dile çevrilir.
    """
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        return "Öğrenci henüz bir hedef bölüm seçmemiş."

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
    return " ".join(parcalar)


def sistem_promptu_olustur(db: Session, ogrenci: Ogrenci, onceki_ozet: str | None) -> str:
    profil = _ogrenci_profil_ozeti(db, ogrenci)
    ozet_blogu = f"\n\nÖnceki konuşmalardan kısa özet: {onceki_ozet}" if onceki_ozet else ""

    return f"""Sen, bir üniversite bölüm/kariyer koçluğu sisteminde çalışan, öğrenciyle sohbet tarzında konuşan bir kariyer koçusun.

ÖĞRENCİ: {ogrenci.ad_soyad}
{profil}{ozet_blogu}

KURALLAR (bunlara kesinlikle uy):
1. Sohbet tarzında, doğal cümlelerle konuş — madde madde liste, numaralı adım ya da "1. ... 2. ..." formatı KULLANMA. Gerçek bir insan koç gibi, akıcı paragraflar halinde yaz.
2. Kendi kişisel bir anını, deneyimini ya da hikayeni ASLA uydurma ("ben de senin yaşındayken..." gibi cümleler kurma). Sen bir insan değilsin, bunu gizlemeye çalışma ama gereksiz yere de vurgulama.
3. Öğrencinin yukarıdaki gerçek profil verisine dayan — uydurma bilgi verme. Profilde olmayan bir şeyi biliyormuş gibi davranma.
4. Sistemin kendi hesapladığı sonuçlarla ÇELİŞME — örneğin hedef bölümü olarak gösterilenden başka bir bölümü "asıl sana bu uyar" diye önerme; onun yerine mevcut hedefi/güçlü yönlerini nasıl değerlendirebileceğini konuş.
5. Ne çok dar (yalnızca tek cümlelik cevaplar) ne çok geniş (alakasız konulara sürüklenen) ol — kariyer, bölüm, gelişim, motivasyon eksenli sohbet et, öğrenci başka bir şey sorarsa nazikçe konuya geri dön.
6. Sıcak, meraklı, yargılamayan bir ton kullan — bir sınav sonucu okur gibi değil, gerçekten önemsiyormuş gibi konuş.
"""


def openai_ile_konus(sistem_promptu: str, mesaj_gecmisi: list[dict]) -> str:
    """
    mesaj_gecmisi: [{"role": "user"|"assistant", "content": "..."}]
    """
    if not _api_anahtari_var_mi():
        raise AsistanKullanilamiyorHatasi(
            "AI koçluk asistanı henüz aktif değil — OPENAI_API_KEY tanımlanmadı."
        )

    from openai import OpenAI  # yalnızca anahtar varsa import edilir, gereksiz bağımlılık hatası önlenir
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    yanit = client.chat.completions.create(
        model=MODEL_ADI,
        messages=[{"role": "system", "content": sistem_promptu}] + mesaj_gecmisi,
        temperature=0.7,
        max_tokens=500,
    )
    return yanit.choices[0].message.content


def oturumu_ozetle(sistem_promptu: str, mesaj_gecmisi: list[dict]) -> str:
    """Oturum kapanırken, ham geçmiş yerine bir sonraki oturuma taşınacak kısa özeti üretir."""
    if not _api_anahtari_var_mi():
        return "Özet çıkarılamadı (asistan aktif değil)."

    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    ozetleme_istegi = mesaj_gecmisi + [{
        "role": "user",
        "content": "Bu konuşmayı, bir sonraki oturumda hatırlaman için 2-3 cümlelik kısa bir özete çevir. Yalnızca özeti yaz, başka bir şey ekleme.",
    }]
    yanit = client.chat.completions.create(
        model=MODEL_ADI,
        messages=[{"role": "system", "content": sistem_promptu}] + ozetleme_istegi,
        temperature=0.3,
        max_tokens=150,
    )
    return yanit.choices[0].message.content
