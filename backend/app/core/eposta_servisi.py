"""
[2026-10-04] E-posta gönderimi.

Öncelik sırası:
  1. EPOSTA_SERVIS_URL + EPOSTA_GIZLI_ANAHTAR tanımlıysa → Vercel'deki /api/eposta-gonder fonksiyonuna
     HTTPS ile iletilir; o fonksiyon Gmail (uygulama şifresi) ile gönderir. Render ücretsiz plan
     SMTP portlarını engellediği için varsayılan yol budur.
  2. SMTP_SUNUCU tanımlıysa → doğrudan SMTP (Render ücretli plan veya yerel geliştirme).
  3. Hiçbiri yoksa → gönderilmez, False döner (2 adımlı doğrulama bu durumda kendiliğinden kapalı sayılır).

Testlerde `GONDERILENLER` listesine de yazılır (TEST_EPOSTA_KAYDI ortam değişkeni ile).

[2026-10-12] Ek dosya desteği: `ekler=[(dosya_adi, icerik_bytes, mime)]` (ör. sonuç raporu PDF'i).
Vercel fonksiyonuna base64 olarak gider; toplam ek boyutu EK_SINIRI ile sınırlıdır.
"""
import base64
import html as _html
import json
import logging
import os
import smtplib
import ssl
import urllib.request
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.core.config import settings

log = logging.getLogger("eposta")
GONDERILENLER: list[dict] = []          # yalnızca testler için
GONDEREN_ADI = "Filizyol"
EK_SINIRI = 3 * 1024 * 1024             # toplam ek boyutu (Vercel istek gövdesi sınırı 4,5 MB; base64 ~%33 büyütür)


def eposta_yapilandirildi_mi() -> bool:
    if os.environ.get("TEST_EPOSTA_KAYDI") == "1":
        return True
    return bool((settings.EPOSTA_SERVIS_URL and settings.EPOSTA_GIZLI_ANAHTAR) or settings.SMTP_SUNUCU)


def eposta_gonder(alici: str, konu: str, html: str, metin: str, ekler: list[tuple[str, bytes, str]] | None = None) -> bool:
    ekler = ekler or []
    if sum(len(e[1]) for e in ekler) > EK_SINIRI:
        log.error("E-posta ekleri çok büyük (%s): %d bayt", alici, sum(len(e[1]) for e in ekler))
        return False
    if os.environ.get("TEST_EPOSTA_KAYDI") == "1":
        GONDERILENLER.append({"alici": alici, "konu": konu, "html": html, "metin": metin,
                              "ekler": [(ad, len(icerik), mime) for ad, icerik, mime in ekler]})
        return True
    try:
        if settings.EPOSTA_SERVIS_URL and settings.EPOSTA_GIZLI_ANAHTAR:
            veri = {"alici": alici, "konu": konu, "html": html, "metin": metin}
            if ekler:
                veri["ekler"] = [{"ad": ad, "icerik": base64.b64encode(icerik).decode("ascii"), "tur": mime}
                                 for ad, icerik, mime in ekler]
            govde = json.dumps(veri).encode("utf-8")
            istek = urllib.request.Request(
                settings.EPOSTA_SERVIS_URL, data=govde, method="POST",
                headers={"Content-Type": "application/json", "X-Eposta-Anahtar": settings.EPOSTA_GIZLI_ANAHTAR},
            )
            with urllib.request.urlopen(istek, timeout=40 if ekler else 20) as yanit:
                return 200 <= yanit.status < 300
        if settings.SMTP_SUNUCU:
            govde = MIMEMultipart("alternative")
            govde.attach(MIMEText(metin, "plain", "utf-8"))
            govde.attach(MIMEText(html, "html", "utf-8"))
            if ekler:
                mesaj = MIMEMultipart("mixed")
                mesaj.attach(govde)
                for ad, icerik, mime in ekler:
                    parca = MIMEApplication(icerik, _subtype=mime.split("/")[-1])
                    parca.add_header("Content-Disposition", "attachment", filename=ad)
                    mesaj.attach(parca)
            else:
                mesaj = govde
            mesaj["Subject"] = konu
            mesaj["From"] = formataddr((GONDEREN_ADI, settings.SMTP_KULLANICI))
            mesaj["To"] = alici
            if settings.SMTP_PORT == 465:
                with smtplib.SMTP_SSL(settings.SMTP_SUNUCU, 465, context=ssl.create_default_context(), timeout=20) as s:
                    s.login(settings.SMTP_KULLANICI, settings.SMTP_SIFRE)
                    s.send_message(mesaj)
            else:
                with smtplib.SMTP(settings.SMTP_SUNUCU, settings.SMTP_PORT, timeout=20) as s:
                    s.starttls(context=ssl.create_default_context())
                    s.login(settings.SMTP_KULLANICI, settings.SMTP_SIFRE)
                    s.send_message(mesaj)
            return True
        log.warning("E-posta yapılandırılmadı; '%s' konulu e-posta gönderilmedi.", konu)
        return False
    except Exception as hata:
        log.error("E-posta gönderilemedi (%s): %s: %s", alici, type(hata).__name__, hata)
        return False


# ----------------------------------------------------------------------------- şablonlar
def _sablon(baslik: str, govde_html: str, alt_not: str | None = None) -> str:
    return f"""<!doctype html><html><body style="margin:0;background:#FAF7EF;font-family:Arial,Helvetica,sans-serif;color:#2C2717">
<div style="max-width:520px;margin:0 auto;padding:28px 18px">
  <div style="font-size:20px;font-weight:bold;margin-bottom:4px">🌱 Filizyol</div>
  <div style="font-size:12px;color:#A79C7C;margin-bottom:18px">Kendi yolunu filizlendir</div>
  <div style="background:#fff;border-radius:16px;padding:24px;border:1px solid #ece5d3">
    <div style="font-size:17px;font-weight:bold;margin-bottom:12px">{baslik}</div>
    {govde_html}
  </div>
  <div style="font-size:11px;color:#A79C7C;margin-top:16px;line-height:1.5">
    {alt_not or "Bu e-postayı sen istemediysen dikkate alma; hesabında bir değişiklik yapılmaz."}
  </div>
</div></body></html>"""


def dogrulama_kodu_epostasi(ad: str, kod: str) -> tuple[str, str, str]:
    ad_h = _html.escape(ad or "")
    konu = f"Giriş doğrulama kodun: {kod}"
    html = _sablon("Giriş doğrulama kodu", f"""
      <p style="font-size:14px;line-height:1.6">Merhaba {ad_h}, giriş yapmak için aşağıdaki kodu kullan:</p>
      <div style="font-size:32px;font-weight:bold;letter-spacing:8px;text-align:center;background:#FBE4D2;color:#C86530;border-radius:12px;padding:14px;margin:16px 0">{kod}</div>
      <p style="font-size:13px;color:#7A7157;line-height:1.6">Kod 10 dakika geçerlidir. Kodu kimseyle paylaşma.</p>""")
    metin = f"Merhaba {ad},\n\nGiriş doğrulama kodun: {kod}\nKod 10 dakika geçerlidir. Kodu kimseyle paylaşma.\n\nFilizyol"
    return konu, html, metin


def sifre_degisikligi_kodu_epostasi(ad: str, kod: str) -> tuple[str, str, str]:
    """[2026-11-04] Şifre değişikliği onay kodu."""
    ad_h = _html.escape(ad or "")
    konu = f"Şifre değişikliği onay kodun: {kod}"
    html = _sablon("Şifre değişikliği onayı", f"""
      <p style="font-size:14px;line-height:1.6">Merhaba {ad_h}, hesabının şifresini değiştirmek istedin. Değişikliği onaylamak için bu kodu gir:</p>
      <div style="font-size:32px;font-weight:bold;letter-spacing:8px;text-align:center;background:#FBE4D2;color:#C86530;border-radius:12px;padding:14px;margin:16px 0">{kod}</div>
      <p style="font-size:13px;color:#7A7157;line-height:1.6">Kod 10 dakika geçerlidir. Bu isteği sen yapmadıysan kodu kimseyle paylaşma; şifren değişmez. Yine de şifreni yenilemeni öneririz.</p>""")
    metin = (f"Merhaba {ad},\n\nŞifre değişikliği onay kodun: {kod}\nKod 10 dakika geçerlidir. Bu isteği sen yapmadıysan kodu "
             "kimseyle paylaşma; şifren değişmez.\n\nFilizyol")
    return konu, html, metin


def sifre_degisti_bildirimi_epostasi(ad: str) -> tuple[str, str, str]:
    """[2026-11-04] Şifre değiştikten sonra bilgi e-postası (diğer cihazlardaki oturumlar kapatıldı)."""
    ad_h = _html.escape(ad or "")
    konu = "Şifren değiştirildi"
    html = _sablon("Şifren değiştirildi", f"""
      <p style="font-size:14px;line-height:1.6">Merhaba {ad_h}, hesabının şifresi az önce değiştirildi ve diğer cihazlardaki oturumlar kapatıldı.</p>
      <p style="font-size:13px;color:#7A7157;line-height:1.6">Bu değişikliği sen yapmadıysan hemen "Şifremi unuttum" ile yeni şifre al ve rehber öğretmenine ya da okul yönetimine haber ver.</p>""")
    metin = (f"Merhaba {ad},\n\nHesabının şifresi az önce değiştirildi ve diğer cihazlardaki oturumlar kapatıldı. Bu değişikliği sen "
             "yapmadıysan hemen \"Şifremi unuttum\" ile yeni şifre al.\n\nFilizyol")
    return konu, html, metin


def _buton(baglanti: str, yazi: str) -> str:
    return (f'<div style="text-align:center;margin:20px 0"><a href="{baglanti}" '
            f'style="background:#E8804A;color:#fff;text-decoration:none;font-weight:bold;padding:12px 22px;border-radius:12px;display:inline-block">{yazi}</a></div>'
            f'<p style="font-size:11.5px;color:#A79C7C;word-break:break-all">Düğme çalışmazsa bu bağlantıyı tarayıcına yapıştır:<br>{baglanti}</p>')


def sifre_sifirlama_epostasi(ad: str, baglanti: str) -> tuple[str, str, str]:
    ad_h = _html.escape(ad or "")
    konu = "Şifre sıfırlama bağlantın"
    html = _sablon("Şifreni sıfırla", f"""
      <p style="font-size:14px;line-height:1.6">Merhaba {ad_h}, şifreni sıfırlamak için aşağıdaki düğmeye tıkla. Bağlantı 1 saat geçerlidir ve yalnızca bir kez kullanılabilir.</p>
      {_buton(baglanti, "Yeni şifre belirle")}""")
    metin = f"Merhaba {ad},\n\nŞifreni sıfırlamak için bu bağlantıyı aç (1 saat geçerli):\n{baglanti}\n\nFilizyol"
    return konu, html, metin


def rehber_davet_epostasi(ad: str, okul: str, baglanti: str) -> tuple[str, str, str]:
    ad_h, okul_h = _html.escape(ad or ""), _html.escape(okul or "")
    konu = "Filizyol — okul yetkilisi hesabın hazır"
    html = _sablon("Okul yetkilisi hesabın oluşturuldu", f"""
      <p style="font-size:14px;line-height:1.6">Merhaba {ad_h}, <b>{okul_h}</b> için okul yetkilisi hesabın oluşturuldu.
      Aşağıdaki düğmeyle şifreni belirleyip Filizyol giriş ekranından (öğrencilerle aynı ekran) giriş yapabilirsin. Bağlantı 3 gün geçerlidir.</p>
      {_buton(baglanti, "Şifremi belirle")}""")
    metin = f"Merhaba {ad},\n\n{okul} için okul yetkilisi hesabın oluşturuldu. Şifreni belirlemek için (3 gün geçerli):\n{baglanti}\n\nFilizyol"
    return konu, html, metin


def sonuc_raporu_epostasi(ad: str, tarih: str, ekli: bool, giris_adresi: str | None = None) -> tuple[str, str, str]:
    """[2026-10-12] Değerlendirme tamamlanınca öğrenciye giden sonuç e-postası. Gövdede sonuç ayrıntısı yoktur
    (e-posta önizlemelerinde kişisel değerlendirme bilgisi görünmesin); ayrıntılar ekteki PDF'te ve sistemdedir."""
    ad_h = _html.escape(ad or "")
    konu = "Filizyol — değerlendirme sonuç raporun"
    ek_cumle = ("Sonuç raporun bu e-postanın ekinde (PDF). Raporda güçlü yönlerin ve sana uygun bölümler yer alıyor; hedef bölüm seçtiysen yol haritan da."
                if ekli else "Sonuçlarını ve sana uygun bölümleri Filizyol hesabından inceleyebilirsin; hedef bölüm seçince yol haritan da orada hazırlanır.")
    dugme = _buton(giris_adresi, "Sonuçlarımı aç") if giris_adresi else ""
    html = _sablon("Değerlendirmeni tamamladın 🎉", f"""
      <p style="font-size:14px;line-height:1.6">Merhaba {ad_h}, {_html.escape(tarih)} tarihinde değerlendirmeni tamamladın.</p>
      <p style="font-size:14px;line-height:1.6">{ek_cumle}</p>
      {dugme}
      <p style="font-size:12.5px;color:#7A7157;line-height:1.6">Sonuçlarını rehber öğretmeninle ve ailenle konuşman, karar verirken sana yardımcı olur.
      Bu rapor kişiseldir; yalnızca güvendiğin kişilerle paylaş.</p>""",
        alt_not="Bu e-posta, okulunun Filizyol hesabında değerlendirmeni tamamladığın için otomatik gönderildi.")
    metin = (f"Merhaba {ad},\n\n{tarih} tarihinde değerlendirmeni tamamladın.\n{ek_cumle}\n"
             + (f"\nSonuçların: {giris_adresi}\n" if giris_adresi else "") + "\nFilizyol")
    return konu, html, metin


# ----------------------------------------------------------------------------- hoş geldin e-postaları
# [2026-11-11] Toplu hesap açılışında ve "okulun tamamına hoş geldin e-postası" düğmesiyle gönderilir.
# Öğrenciye "sen", okul yetkilisine "siz" diliyle; ikisinde de giriş adresi, e-posta ve (varsa) geçici şifre yer alır.
def _giris_kutusu(giris_adresi: str, eposta: str, gecici_sifre: str | None, siz: bool) -> str:
    satir = lambda k, v: (f'<tr><td style="padding:5px 10px 5px 0;color:#7A7157;font-size:13px;white-space:nowrap">{k}</td>'
                          f'<td style="padding:5px 0;font-size:13.5px;font-weight:bold;word-break:break-all">{v}</td></tr>')
    if gecici_sifre:
        sifre = (f'<span style="font-family:Consolas,monospace;background:#FBE4D2;color:#C86530;padding:2px 8px;border-radius:6px">'
                 f'{_html.escape(gecici_sifre)}</span>')
    else:
        sifre = ('<span style="font-weight:normal">Belirlediğiniz şifre (hatırlamıyorsanız giriş ekranında “Şifremi unuttum”)</span>' if siz
                 else '<span style="font-weight:normal">Belirlediğin şifre (hatırlamıyorsan giriş ekranında “Şifremi unuttum”)</span>')
    return (f'<div style="background:#FAF7EF;border:1px solid #ece5d3;border-radius:12px;padding:12px 14px;margin:14px 0">'
            f'<div style="font-size:12px;font-weight:bold;color:#A79C7C;letter-spacing:.5px;margin-bottom:4px">GİRİŞ BİLGİLERİ</div>'
            f'<table style="border-collapse:collapse">{satir("Adres", _html.escape(giris_adresi))}{satir("E-posta", _html.escape(eposta))}'
            f'{satir("Geçici şifre" if gecici_sifre else "Şifre", sifre)}</table></div>')


def _p(metin_html: str, kucuk: bool = False) -> str:
    stil = "font-size:12.5px;color:#7A7157;line-height:1.65" if kucuk else "font-size:14px;line-height:1.65"
    return f'<p style="{stil}">{metin_html}</p>'


def _sirala(parcalar: list[str]) -> str:
    """['a', 'b', 'c'] → 'a, b ve c'"""
    return parcalar[0] if len(parcalar) == 1 else ", ".join(parcalar[:-1]) + " ve " + parcalar[-1]


# [2026-11-11] Okulların paketleri farklı: e-postada yalnızca okulun paketinde olan modüller anılır (app/core/paketler.py).
# Sıra: kitleye en çok değer katan önce. moduller=None → paket bilinmiyor, ek cümle yazılmaz.
_OGRENCI_MODUL = [
    ("is_hayati", "mesleklerin iş hayatındaki karşılığını gösteren İş Hayatı"),
    ("net_takibi", "deneme netlerini izleyebileceğin Net Takibi"),
    ("calisma", "haftalık çalışma programın"),
    ("portfolyo", "başarılarını biriktirebileceğin e-Portfolyo"),
    ("kulupler", "sana uygun kulüp önerileri"),
    ("tercih", "tercih listeni hazırlayabileceğin Tercih bölümü"),
    ("egitim_koclari", "eğitim koçlarıyla görüşme imkânı"),
]
_YETKILI_MODUL = [
    ("rehberlik", "rehberlik görüşmeleri ile erken uyarı"),
    ("net_takibi", "deneme netleri ile konu takibi"),
    ("okul_denemeleri", "okul denemelerinin şube bazında analizi"),
    ("tercih", "tercih dönemi desteği"),
    ("anketler", "hazır tarama formları ile okul anketleri"),
    ("akran", "akran analizi"),
    ("mezun_takibi", "mezun takibi"),
    ("is_hayati", "öğrenciler için İş Hayatı bölümü"),
]


def _da(kelime: str) -> str:
    """Bağlaç "da/de": son ünlüye göre (kalın → da, ince → de)."""
    for h in reversed(kelime.lower()):
        if h in "aıou":
            return "da"
        if h in "eiöü":
            return "de"
    return "de"


def _paket_cumlesi(moduller: list[str] | None, liste: list[tuple[str, str]], en_fazla: int = 4) -> list[str]:
    if moduller is None:
        return []
    return [m for k, m in liste if k in set(moduller)][:en_fazla]


def ogrenci_hosgeldin_epostasi(ad: str, okul: str | None, eposta: str, gecici_sifre: str | None,
                               giris_adresi: str, moduller: list[str] | None = None) -> tuple[str, str, str]:
    """[2026-11-11] Öğrenciye "sen" diliyle, düz anlatımlı (madde listesi yok) tanıtım + giriş bilgileri + başlarken."""
    okul_m = okul or "Okulun"
    konu = "Filizyol'a hoş geldin — hesabın hazır"
    p1 = f"{okul_m} senin için Filizyol hesabı açtı; hesabın artık kullanıma hazır."
    p2 = ("Filizyol, kendini daha iyi tanıman ve sana gerçekten uyan yolu bulman için hazırlandı. Değerlerin, kişiliğin, "
          "yetkinliklerin ve ilgi alanlarınla ilgili soruları cevapladığında sana en yakın bölümleri ve meslekleri görürsün. "
          "Bölümleri birbiriyle karşılaştırabilir, birini hedef olarak seçtiğinde de ona giden kişisel yol haritanı "
          "oluşturabilirsin. Takıldığın her yerde asistanımız Filiz sana eşlik eder.")
    ek = _paket_cumlesi(moduller, _OGRENCI_MODUL)
    p3 = f"Okulunun paketinde bunların yanında {_sirala(ek)} {_da(ek[-1])} seni bekliyor." if ek else ""
    p4 = (("İlk girişte geçici şifreni kendi belirleyeceğin bir şifreyle değiştirmen istenecek. " if gecici_sifre else "")
          + "18 yaşından küçüksen değerlendirmeye başlamadan önce veli onay formunun okuluna ulaşması gerekiyor: formu giriş "
          "yaptıktan sonra Ana Sayfa'daki “Formu indir” düğmesinden alabilir, velin imzaladıktan sonra okuluna teslim "
          "edebilirsin. Soruları acele etmeden, kendin gibi cevaplaman sonuçlarının sana gerçekten uyması için en önemli şey.")
    h = _html.escape
    html = _sablon(f"Hoş geldin, {h(ad or '')}! 🌱", f"""
      {_p(f"{h(p1)}")}
      {_p(h(p2))}
      {_p(h(p3)) if p3 else ""}
      {_giris_kutusu(giris_adresi, eposta, gecici_sifre, siz=False)}
      {_buton(giris_adresi, "Filizyol'a giriş yap")}
      {_p(h(p4), kucuk=True)}
      {_p("Yolun açık olsun,<br><b>Filizyol</b>")}""",
        alt_not="Bu e-posta, okulun senin için Filizyol hesabı açtığı için gönderildi. Şifreni kimseyle paylaşma. "
                "Bir yanlışlık olduğunu düşünüyorsan rehber öğretmenine haber ver.")
    metin = (f"Merhaba {ad},\n\n{p1}\n\n{p2}\n\n" + (f"{p3}\n\n" if p3 else "")
             + f"Giriş adresi: {giris_adresi}\nE-posta: {eposta}\n"
             + (f"Geçici şifre: {gecici_sifre}\n" if gecici_sifre else "Şifre: belirlediğin şifre (hatırlamıyorsan \"Şifremi unuttum\")\n")
             + f"\n{p4}\n\nŞifreni kimseyle paylaşma.\n\nYolun açık olsun,\nFilizyol")
    return konu, html, metin


def yetkili_hosgeldin_epostasi(ad: str, okul: str | None, unvan: str | None, eposta: str, gecici_sifre: str | None,
                               giris_adresi: str, moduller: list[str] | None = None) -> tuple[str, str, str]:
    """[2026-11-11] Okul yetkilisine "siz" diliyle, düz anlatımlı: sistem tanıtımı, panelin sunduğu, paketteki ek
    modüller, giriş bilgileri ve başlarken. İç işlemler (hesap açma, şifre listesi, e-posta gönderimi) anlatılmaz."""
    okul_m = okul or "Okulunuz"
    konu = "Filizyol — hoş geldiniz, sisteminiz aktif hale getirilmiştir"
    hitap = f"Sayın {ad}" + (f" ({unvan})" if unvan else "") + ","
    p1 = f"{okul_m} için Filizyol okul yetkilisi hesabınız oluşturuldu ve sisteminiz aktif hale getirildi. Filizyol'a hoş geldiniz."
    p2 = ("Filizyol, öğrencilerin değerlerini, kişilik özelliklerini, yetkinliklerini ve ilgi alanlarını çok boyutlu bir "
          "değerlendirmeyle ölçerek her öğrenciye kendisine uygun bölüm ve meslekleri gösteren bir rehberlik sistemidir. "
          "Öğrenci sonuçlarını inceleyip bir hedef bölüm seçtiğinde sistem onun için kişisel bir gelişim yol haritası hazırlar.")
    p3 = ("Okul paneli bu sürecin tamamını önünüze getirir. Hangi öğrencinin değerlendirmeye başladığını ve tamamladığını, "
          "sonuçların sınıf ve şube düzeyinde nasıl dağıldığını görebilir; her öğrencinin profiline, önerilen bölümlerine ve "
          "hedefine tek tıkla ulaşabilirsiniz. Hazır raporlar ve yönetici özeti, okulunuzun genel tablosunu toplantılara hazır hale getirir.")
    ek = _paket_cumlesi(moduller, _YETKILI_MODUL)
    p4 = f"Okulunuzun paketinde bunlara ek olarak {_sirala(ek)} {_da(ek[-1])} yer alıyor." if ek else ""
    p5 = (("Başlamak için giriş yapıp geçici şifrenizi kendi şifrenizle değiştirmeniz yeterli. " if gecici_sifre
           else "Başlamak için giriş yapmanız yeterli. ")
          + "Ardından okul bilgilerinizi kontrol edebilir, öğrencilerinizin ilerlemesini Öğrenciler bölümünden izlemeye "
          "başlayabilirsiniz. Giriş ekranı öğrencilerle aynıdır; e-posta adresinize göre okul paneline yönlendirilirsiniz.")
    h = _html.escape
    html = _sablon("Hoş geldiniz, sisteminiz aktif hale getirilmiştir", f"""
      {_p(h(hitap))}
      {_p(h(p1))}
      {_p(h(p2))}
      {_p(h(p3))}
      {_p(h(p4)) if p4 else ""}
      {_giris_kutusu(giris_adresi, eposta, gecici_sifre, siz=True)}
      {_buton(giris_adresi, "Okul paneline giriş yap")}
      {_p(h(p5), kucuk=True)}
      {_p("Saygılarımızla,<br><b>Filizyol</b>")}""",
        alt_not="Bu e-posta, Filizyol okul yetkilisi hesabınız açıldığı için gönderildi. Şifrenizi kimseyle paylaşmayın.")
    metin = (f"{hitap}\n\n{p1}\n\n{p2}\n\n{p3}\n\n" + (f"{p4}\n\n" if p4 else "")
             + f"Giriş adresi: {giris_adresi}\nE-posta: {eposta}\n"
             + (f"Geçici şifre: {gecici_sifre}\n" if gecici_sifre else "Şifre: belirlediğiniz şifre (hatırlamıyorsanız \"Şifremi unuttum\")\n")
             + f"\n{p5}\n\nSaygılarımızla,\nFilizyol")
    return konu, html, metin
