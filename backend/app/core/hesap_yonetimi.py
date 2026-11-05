# -*- coding: utf-8 -*-
"""
[2026-10-09] Okul bazlı hesap yönetimi için ortak yardımcılar:
geçici şifre üretimi, öğrenci hesap olay kaydı, denetim kaydı, öğrenciyi tüm verisiyle silme.
"""
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import AdminKullanici, AuditLog, Ogrenci, OgrenciHesapOlayi

# Karışan karakterler (0/O, 1/l/I) yok; okunup yazdırılması kolay.
_HARFLER = "abcdefghjkmnpqrstuvwxyz"
_RAKAMLAR = "23456789"


def gecici_sifre() -> str:
    """Örn. 'kemr-4827' — 9 karakter, okunaklı; ilk girişte değiştirilmesi zorunlu."""
    return "".join(secrets.choice(_HARFLER) for _ in range(4)) + "-" + "".join(secrets.choice(_RAKAMLAR) for _ in range(4))


def simdi() -> datetime:
    return datetime.now(timezone.utc)


def olay_yaz(db: Session, ogrenci_id: uuid.UUID, olay: str, aciklama: str | None = None,
             yapan: str | None = None, ip: str | None = None) -> None:
    db.add(OgrenciHesapOlayi(ogrenci_id=ogrenci_id, olay=olay, aciklama=aciklama, yapan=yapan, ip=ip, zaman=simdi()))


def denetim_yaz(db: Session, yapan: AdminKullanici, islem: str, hedef_tablo: str, hedef_id, gerekce: str | None = None,
                okul_id: int | None = None) -> None:
    db.add(AuditLog(admin_id=yapan.id, islem=islem, hedef_tablo=hedef_tablo, hedef_id=str(hedef_id), gerekce=gerekce,
                    okul_id=okul_id, yapan_ad=yapan.ad_soyad, zaman=simdi()))


def yapan_etiketi(yapan: AdminKullanici) -> str:
    return f"{yapan.ad_soyad} ({'Süper admin' if yapan.rol == 'super_admin' else 'Okul yetkilisi'})"


# [2026-11-06] Kullanıcı tipine göre tutulan (yabancı anahtarsız) güvenlik kayıtları: hesap silinince bunlar da silinir
GUVENLIK_TABLOLARI = ("kvkk_onaylari", "dogrulama_kodlari", "sifre_sifirlama_tokenleri", "guvenilir_cihazlar",
                      "sifre_degisiklik_talepleri")


def _guvenlik_kayitlarini_sil(db: Session, kullanici_tipi: str, kullanici_id) -> None:
    for tablo in GUVENLIK_TABLOLARI:
        try:
            with db.begin_nested():
                db.execute(text(f"DELETE FROM {tablo} WHERE kullanici_tipi = :t AND kullanici_id = :id"),
                           {"t": kullanici_tipi, "id": kullanici_id})
        except Exception:
            pass  # tablo bu ortamda yoksa geç


def yoneticiyi_sil(db: Session, yonetici: AdminKullanici, yapan_id) -> None:
    """[2026-11-06] Yönetim hesabını (okul yetkilisi / süper admin) siler. Önceden yalnızca db.delete yapılıyordu:
    KVKK onayı, doğrulama kodu, güvenilir cihaz gibi kayıtlar sahipsiz kalıyordu. admin_kullanicilar'a bağlı kayıtlarda
    (denetim kaydı, parametreler …) bağ NULL yapılır; sütun NULL olamıyorsa kayıt silmeyi yapana devredilir (kayıt kaybolmaz)."""
    # Yalnızca veritabanının kendisinin çözmediği bağlar (NO ACTION / RESTRICT); CASCADE ve SET NULL'u veritabanı yapar
    # (ör. filiz_yonetim_sayac CASCADE: sayaç silinir, başkasına devredilmez).
    baglar = db.execute(text("""
        SELECT c.conrelid::regclass::text AS tablo, a.attname AS sutun, a.attnotnull AS zorunlu
        FROM pg_constraint c JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
        WHERE c.contype = 'f' AND c.confrelid = 'admin_kullanicilar'::regclass AND c.confdeltype IN ('a', 'r')""")).all()
    for tablo, sutun, zorunlu in baglar:
        with db.begin_nested():
            db.execute(text(f'UPDATE {tablo} SET "{sutun}" = :d WHERE "{sutun}" = :id'),
                       {"d": yapan_id if zorunlu else None, "id": yonetici.id})
    _guvenlik_kayitlarini_sil(db, "yonetim", yonetici.id)
    db.delete(yonetici)


def ogrenciyi_sil(db: Session, ogrenci: Ogrenci) -> None:
    """Öğrenciyi ve ona bağlı tüm verileri siler. Tablolar arası bağlar ON DELETE CASCADE (0017);
    kullanıcı tipine göre tutulan (yabancı anahtarsız) güvenlik kayıtları burada ayrıca silinir."""
    for tablo in GUVENLIK_TABLOLARI:
        try:
            with db.begin_nested():
                db.execute(text(f"DELETE FROM {tablo} WHERE kullanici_tipi = 'ogrenci' AND kullanici_id = :id"),
                           {"id": ogrenci.id})
        except Exception:
            pass  # tablo bu ortamda yoksa geç
    db.delete(ogrenci)
