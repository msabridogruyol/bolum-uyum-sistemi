# -*- coding: utf-8 -*-
"""
[2026-10-10] Bildirim servisi.

bildir(db, alici_tipi, alici_idler, tur, baslik, metin, link, okul_id, eposta=False)
  - Satırları ekler (commit çağıran tarafındadır). Okulun paketinde 'bildirimler' yoksa hiçbir şey yapmaz.
  - eposta=True ise ve kişi e-postayı kapatmadıysa satır 'bekliyor' olarak kuyruğa girer;
    commit'ten sonra kuyruk_tetikle() arka planda (ayrı oturum, iş parçacığı) gönderir.
E-posta sınırı: Gmail tabanlı gönderim günde ~500 e-postayla sınırlı olduğundan GUNLUK_SINIR uygulanır;
sınır aşılırsa e-posta atlanır ('sinir'), uygulama içi bildirim yine görünür.
"""
import html as _html
import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

log = logging.getLogger("bildirim")
GUNLUK_SINIR = 300
_kilit = threading.Lock()
_calisiyor = False


def _acik_mi(db: Session, okul_id) -> bool:
    from app.core.paketler import okul_modulleri
    return "bildirimler" in okul_modulleri(db, okul_id)


def bildir(db: Session, alici_tipi: str, alici_idler, tur: str, baslik: str, metin: str | None = None, link: str | None = None,
           okul_id: int | None = None, eposta: bool = False) -> int:
    idler = [i for i in dict.fromkeys(alici_idler or []) if i]
    if not idler or not _acik_mi(db, okul_id):
        return 0
    kapali = set()
    if eposta:
        kapali = {r[0] for r in db.execute(text("SELECT kullanici_id FROM bildirim_tercihleri WHERE kullanici_id = ANY(:i) AND NOT eposta"),
                                           {"i": idler}).all()}
    for i in idler:
        db.execute(text("""
            INSERT INTO bildirimler (alici_tipi, alici_id, okul_id, tur, baslik, metin, link, eposta_durum)
            VALUES (:t, :a, :ok, :tu, :b, :m, :l, :e)
        """), {"t": alici_tipi, "a": i, "ok": okul_id, "tu": tur, "b": baslik[:200], "m": (metin or None) and metin[:600], "l": link,
               "e": "bekliyor" if eposta and i not in kapali else "yok"})
    if eposta:
        kuyruk_tetikle()
    return len(idler)


def okul_yetkililerine(db: Session, okul_id: int, *args, **kw) -> int:
    ids = [r[0] for r in db.execute(text("SELECT id FROM admin_kullanicilar WHERE okul_id = :o AND rol = 'okul_yetkilisi'"), {"o": okul_id}).all()]
    return bildir(db, "yonetim", ids, *args, okul_id=okul_id, **kw)


# ----------------------------------------------------------------------------- e-posta kuyruğu
def kuyruk_tetikle(gecikme: float = 2.0) -> None:
    """Arka planda bekleyen e-postaları gönderir. Zaten çalışıyorsa yeni iş parçacığı açmaz."""
    global _calisiyor
    with _kilit:
        if _calisiyor:
            return
        _calisiyor = True
    threading.Thread(target=_isle, args=(gecikme,), daemon=True, name="bildirim-eposta").start()


def _eposta_icerigi(ad: str, baslik: str, metin: str | None, link: str | None, site: str) -> tuple[str, str]:
    from app.core.eposta_servisi import _buton, _sablon
    govde = f'<p style="font-size:14px;line-height:1.6">Merhaba {_html.escape(ad or "")},</p>'
    if metin:
        govde += f'<p style="font-size:14px;line-height:1.6">{_html.escape(metin)}</p>'
    if link:
        govde += _buton(site + link, "Filizyol'da aç")
    govde += ('<p style="font-size:11.5px;color:#A79C7C;margin-top:14px">Bu e-postaları almak istemiyorsan '
              'Filizyol → Ayarlar → Bildirimler bölümünden kapatabilirsin.</p>')
    duz = f"Merhaba {ad},\n\n{baslik}\n{metin or ''}\n" + (f"\n{site + link}\n" if link else "") + "\nFilizyol"
    return _sablon(_html.escape(baslik), govde), duz


def _isle(gecikme: float) -> None:
    global _calisiyor
    time.sleep(gecikme)   # çağıranın commit'i tamamlansın
    try:
        from app.core.config import settings
        from app.core.database import SessionLocal
        from app.core.eposta_servisi import eposta_gonder, eposta_yapilandirildi_mi
        site = (settings.FRONTEND_URL or "").rstrip("/") or "http://localhost:5173"
        db = SessionLocal()
        try:
            if not eposta_yapilandirildi_mi():
                db.execute(text("UPDATE bildirimler SET eposta_durum = 'yapilandirilmadi' WHERE eposta_durum = 'bekliyor'"))
                db.commit()
                return
            while True:
                gun = datetime.now(timezone.utc) - timedelta(days=1)
                gonderilen = db.execute(text("SELECT count(*) FROM bildirimler WHERE eposta_durum = 'gonderildi' AND olusturulma_zamani >= :g"),
                                        {"g": gun}).scalar() or 0
                rows = db.execute(text("""
                    SELECT b.id, b.alici_tipi, b.alici_id, b.baslik, b.metin, b.link,
                           coalesce(o.email, a.email) AS email, coalesce(o.ad_soyad, a.ad_soyad) AS ad
                      FROM bildirimler b
                      LEFT JOIN ogrenciler o ON b.alici_tipi = 'ogrenci' AND o.id = b.alici_id
                      LEFT JOIN admin_kullanicilar a ON b.alici_tipi = 'yonetim' AND a.id = b.alici_id
                     WHERE b.eposta_durum = 'bekliyor' ORDER BY b.id LIMIT 20
                """)).all()
                if not rows:
                    return
                for r in rows:
                    if gonderilen >= GUNLUK_SINIR:
                        durum = "sinir"
                    elif not r.email:
                        durum = "adres_yok"
                    else:
                        h, d = _eposta_icerigi(r.ad, r.baslik, r.metin, r.link, site)
                        durum = "gonderildi" if eposta_gonder(r.email, f"Filizyol: {r.baslik}", h, d) else "hata"
                        gonderilen += durum == "gonderildi"
                        time.sleep(1.0)
                    db.execute(text("UPDATE bildirimler SET eposta_durum = :d WHERE id = :i"), {"d": durum, "i": r.id})
                    db.commit()
        finally:
            db.close()
    except Exception as e:   # kuyruk çökmesin; bir sonraki tetiklemede devam eder
        log.error("Bildirim e-posta kuyruğu: %s: %s", type(e).__name__, e)
    finally:
        with _kilit:
            _calisiyor = False
