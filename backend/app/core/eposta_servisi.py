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


def _madde_listesi(maddeler: list[tuple[str, str]]) -> str:
    return "".join(f'<div style="margin:0 0 9px 0;font-size:13.5px;line-height:1.55"><b>{_html.escape(b)}</b> — {_html.escape(a)}</div>'
                   for b, a in maddeler)


def ogrenci_hosgeldin_epostasi(ad: str, okul: str | None, eposta: str, gecici_sifre: str | None,
                               giris_adresi: str) -> tuple[str, str, str]:
    ad_h, okul_h = _html.escape(ad or ""), _html.escape(okul or "Okulun")
    konu = "Filizyol'a hoş geldin — hesabın hazır"
    maddeler = [("Değerlendirme", "İlgilerini, güçlü yönlerini ve çalışma biçimini beş boyutta tanırsın."),
                ("Sana uygun bölümler", "Sonuçlarına göre bölüm ve meslek önerilerini görür, bölümleri karşılaştırırsın."),
                ("Hedef ve yol haritası", "Bir hedef bölüm seçtiğinde ona giden gelişim planın hazırlanır."),
                ("İş hayatı", "Mesleklerin gerçek dünyadaki karşılığını ve okulda öğretilmeyen becerileri keşfedersin.")]
    ilk = ("İlk girişte geçici şifreni kendi belirleyeceğin bir şifreyle değiştirmen istenir." if gecici_sifre
           else "Giriş yaptıktan sonra değerlendirmeye kaldığın yerden devam edebilirsin.")
    html = _sablon(f"Hoş geldin, {ad_h}! 🌱", f"""
      <p style="font-size:14px;line-height:1.6"><b>{okul_h}</b> seni Filizyol'a dahil etti; hesabın aktif hale getirildi.</p>
      <p style="font-size:14px;line-height:1.6">Filizyol, kendini tanıman ve sana uygun yolu bulman için hazırlanmış bir yönlendirme sistemidir.
      Neler yapabileceğin:</p>
      {_madde_listesi(maddeler)}
      {_giris_kutusu(giris_adresi, eposta, gecici_sifre, siz=False)}
      {_buton(giris_adresi, "Filizyol'a giriş yap")}
      <p style="font-size:12.5px;color:#7A7157;line-height:1.6">{ilk} Soruları acele etmeden, kendin gibi cevaplaman sonuçların
      doğruluğu için önemlidir. 18 yaşından küçüksen okulun senden veli onay formu isteyebilir.</p>""",
        alt_not="Bu e-posta, okulun senin için Filizyol hesabı açtığı için gönderildi. Şifreni kimseyle paylaşma. "
                "Bir yanlışlık olduğunu düşünüyorsan rehber öğretmenine haber ver.")
    metin = (f"Merhaba {ad},\n\n{okul or 'Okulun'} seni Filizyol'a dahil etti; hesabın aktif hale getirildi.\n\n"
             "Filizyol, kendini tanıman ve sana uygun yolu bulman için hazırlanmış bir yönlendirme sistemidir.\n"
             + "".join(f"- {b}: {a}\n" for b, a in maddeler)
             + f"\nGiriş adresi: {giris_adresi}\nE-posta: {eposta}\n"
             + (f"Geçici şifre: {gecici_sifre}\n" if gecici_sifre else "Şifre: belirlediğin şifre (hatırlamıyorsan \"Şifremi unuttum\")\n")
             + f"\n{ilk}\nŞifreni kimseyle paylaşma.\n\nFilizyol")
    return konu, html, metin


def yetkili_hosgeldin_epostasi(ad: str, okul: str | None, unvan: str | None, eposta: str, gecici_sifre: str | None,
                               giris_adresi: str) -> tuple[str, str, str]:
    ad_h, okul_h = _html.escape(ad or ""), _html.escape(okul or "okulunuz")
    gorev = f" ({_html.escape(unvan)})" if unvan else ""
    konu = "Filizyol — hoş geldiniz, sisteminiz aktif hale getirilmiştir"
    maddeler = [("Öğrenci hesapları", "Excel ile toplu hesap açma, geçici şifre listesi, hoş geldin e-postası."),
                ("İlerleme ve sonuçlar", "Öğrencilerin değerlendirme durumu, sınıf ve şube bazında sonuçlar."),
                ("Rehberlik", "Öğrenci bazında görüşme notları, hedef bölüm ve gelişim planı takibi."),
                ("Raporlar", "Okul raporları ve Excel çıktıları; veli onay formu takibi.")]
    adimlar = ["Giriş yapın ve geçici şifrenizi kendi şifrenizle değiştirin." if gecici_sifre else "Giriş yapın.",
               "Okul bilgilerinizi ve amblemi kontrol edin.",
               "Öğrenci hesaplarını açın (Excel ile toplu yükleme).",
               "Öğrencilerinize tek tuşla hoş geldin e-postası gönderin."]
    html = _sablon("Hoş geldiniz, sisteminiz aktif hale getirilmiştir", f"""
      <p style="font-size:14px;line-height:1.6">Sayın {ad_h}{gorev},</p>
      <p style="font-size:14px;line-height:1.6"><b>{okul_h}</b> için Filizyol okul yetkilisi hesabınız oluşturuldu ve kullanıma açıldı.</p>
      <p style="font-size:14px;line-height:1.6">Filizyol, öğrencilerin ilgi, yetenek ve çalışma biçimlerini beş boyutta değerlendirip
      onlara uygun bölüm ve meslekleri gösteren bir rehberlik sistemidir. Okul paneli şunları sunar:</p>
      {_madde_listesi(maddeler)}
      {_giris_kutusu(giris_adresi, eposta, gecici_sifre, siz=True)}
      {_buton(giris_adresi, "Okul paneline giriş yap")}
      <div style="font-size:13px;line-height:1.6;color:#4A4430"><b>İlk adımlar</b><ol style="margin:6px 0 0 18px;padding:0">
      {"".join(f"<li>{_html.escape(a)}</li>" for a in adimlar)}</ol></div>
      <p style="font-size:12.5px;color:#7A7157;line-height:1.6;margin-top:12px">Giriş ekranı öğrencilerle aynıdır; e-posta adresinize göre
      okul paneline yönlendirilirsiniz.</p>""",
        alt_not="Bu e-posta, Filizyol okul yetkilisi hesabınız açıldığı için gönderildi. Şifrenizi kimseyle paylaşmayın.")
    metin = (f"Sayın {ad}{f' ({unvan})' if unvan else ''},\n\n{okul or 'Okulunuz'} için Filizyol okul yetkilisi hesabınız oluşturuldu "
             "ve kullanıma açıldı.\n\n"
             + "".join(f"- {b}: {a}\n" for b, a in maddeler)
             + f"\nGiriş adresi: {giris_adresi}\nE-posta: {eposta}\n"
             + (f"Geçici şifre: {gecici_sifre}\n" if gecici_sifre else "Şifre: belirlediğiniz şifre (hatırlamıyorsanız \"Şifremi unuttum\")\n")
             + "\nİlk adımlar:\n" + "".join(f"{i}. {a}\n" for i, a in enumerate(adimlar, 1)) + "\nFilizyol")
    return konu, html, metin
