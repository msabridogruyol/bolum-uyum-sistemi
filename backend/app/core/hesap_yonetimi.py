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


def ogrenciyi_sil(db: Session, ogrenci: Ogrenci) -> None:
    """Öğrenciyi ve ona bağlı tüm verileri siler. Tablolar arası bağlar ON DELETE CASCADE (0017);
    kullanıcı tipine göre tutulan (yabancı anahtarsız) güvenlik kayıtları burada ayrıca silinir."""
    for tablo in ("kvkk_onaylari", "dogrulama_kodlari", "sifre_sifirlama_tokenleri", "guvenilir_cihazlar"):
        try:
            with db.begin_nested():
                db.execute(text(f"DELETE FROM {tablo} WHERE kullanici_tipi = 'ogrenci' AND kullanici_id = :id"),
                           {"id": ogrenci.id})
        except Exception:
            pass  # tablo bu ortamda yoksa geç
    db.delete(ogrenci)
