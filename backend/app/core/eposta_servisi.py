"""
[2026-10-04] E-posta gönderimi.

Öncelik sırası:
  1. EPOSTA_SERVIS_URL + EPOSTA_GIZLI_ANAHTAR tanımlıysa → Vercel'deki /api/eposta-gonder fonksiyonuna
     HTTPS ile iletilir; o fonksiyon Gmail (uygulama şifresi) ile gönderir. Render ücretsiz plan
     SMTP portlarını engellediği için varsayılan yol budur.
  2. SMTP_SUNUCU tanımlıysa → doğrudan SMTP (Render ücretli plan veya yerel geliştirme).
  3. Hiçbiri yoksa → gönderilmez, False döner (2 adımlı doğrulama bu durumda kendiliğinden kapalı sayılır).

Testlerde `GONDERILENLER` listesine de yazılır (TEST_EPOSTA_KAYDI ortam değişkeni ile).
"""
import html as _html
import json
import logging
import os
import smtplib
import ssl
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.core.config import settings

log = logging.getLogger("eposta")
GONDERILENLER: list[dict] = []          # yalnızca testler için
GONDEREN_ADI = "Filizyol"


def eposta_yapilandirildi_mi() -> bool:
    if os.environ.get("TEST_EPOSTA_KAYDI") == "1":
        return True
    return bool((settings.EPOSTA_SERVIS_URL and settings.EPOSTA_GIZLI_ANAHTAR) or settings.SMTP_SUNUCU)


def eposta_gonder(alici: str, konu: str, html: str, metin: str) -> bool:
    if os.environ.get("TEST_EPOSTA_KAYDI") == "1":
        GONDERILENLER.append({"alici": alici, "konu": konu, "html": html, "metin": metin})
        return True
    try:
        if settings.EPOSTA_SERVIS_URL and settings.EPOSTA_GIZLI_ANAHTAR:
            govde = json.dumps({"alici": alici, "konu": konu, "html": html, "metin": metin}).encode("utf-8")
            istek = urllib.request.Request(
                settings.EPOSTA_SERVIS_URL, data=govde, method="POST",
                headers={"Content-Type": "application/json", "X-Eposta-Anahtar": settings.EPOSTA_GIZLI_ANAHTAR},
            )
            with urllib.request.urlopen(istek, timeout=20) as yanit:
                return 200 <= yanit.status < 300
        if settings.SMTP_SUNUCU:
            mesaj = MIMEMultipart("alternative")
            mesaj["Subject"] = konu
            mesaj["From"] = formataddr((GONDEREN_ADI, settings.SMTP_KULLANICI))
            mesaj["To"] = alici
            mesaj.attach(MIMEText(metin, "plain", "utf-8"))
            mesaj.attach(MIMEText(html, "html", "utf-8"))
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
def _sablon(baslik: str, govde_html: str) -> str:
    return f"""<!doctype html><html><body style="margin:0;background:#FAF7EF;font-family:Arial,Helvetica,sans-serif;color:#2C2717">
<div style="max-width:520px;margin:0 auto;padding:28px 18px">
  <div style="font-size:20px;font-weight:bold;margin-bottom:4px">🌱 Filizyol</div>
  <div style="font-size:12px;color:#A79C7C;margin-bottom:18px">Kendi yolunu filizlendir</div>
  <div style="background:#fff;border-radius:16px;padding:24px;border:1px solid #ece5d3">
    <div style="font-size:17px;font-weight:bold;margin-bottom:12px">{baslik}</div>
    {govde_html}
  </div>
  <div style="font-size:11px;color:#A79C7C;margin-top:16px;line-height:1.5">
    Bu e-postayı sen istemediysen dikkate alma; hesabında bir değişiklik yapılmaz.
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
    konu = "Filizyol — rehber öğretmen hesabın hazır"
    html = _sablon("Rehber öğretmen hesabın oluşturuldu", f"""
      <p style="font-size:14px;line-height:1.6">Merhaba {ad_h}, <b>{okul_h}</b> için rehber öğretmen hesabın oluşturuldu.
      Aşağıdaki düğmeyle şifreni belirleyip öğrenci giriş sayfasından giriş yapabilirsin. Bağlantı 3 gün geçerlidir.</p>
      {_buton(baglanti, "Şifremi belirle")}""")
    metin = f"Merhaba {ad},\n\n{okul} için rehber öğretmen hesabın oluşturuldu. Şifreni belirlemek için (3 gün geçerli):\n{baglanti}\n\nFilizyol"
    return konu, html, metin
