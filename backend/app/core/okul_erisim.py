# -*- coding: utf-8 -*-
"""
[2026-10-11] Okul bazında sistem erişimi (süper admin açar / kapatır).

Kapalı okulun öğrencileri ve okul yetkilileri:
  * giriş yapamaz (POST /auth/giris, 2 adımlı doğrulama, test girişi),
  * açık oturumları bir sonraki istekte 423 ile sonlanır (deps.get_mevcut_ogrenci / get_mevcut_yonetim).
Süper admin etkilenmez. 423 (Locked) yalnızca bu durumda kullanılır; arayüz bu kodu görünce oturumu kapatıp
giriş ekranında mesajı gösterir.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

KAPALI_DURUM_KODU = 423
VARSAYILAN_MESAJ = "Sisteminiz şu anda kapalıdır. Ayrıntılı bilgi için okulunuzla iletişime geçebilirsiniz."
MESAJ_EN_FAZLA = 300


def kapali_mesaji(db: Session, okul_id: int | None) -> str | None:
    """Okul kapalıysa gösterilecek mesaj; açıksa (ya da okul yoksa) None."""
    if not okul_id:
        return None
    from app.models import Okul
    okul = db.get(Okul, okul_id)
    if okul is None or okul.erisim_acik is not False:
        return None
    return (okul.kapali_mesaji or "").strip() or VARSAYILAN_MESAJ


def okul_acik_olmali(db: Session, okul_id: int | None) -> None:
    mesaj = kapali_mesaji(db, okul_id)
    if mesaj:
        raise HTTPException(status_code=KAPALI_DURUM_KODU, detail=mesaj)


def hesap_okulu_acik_olmali(db: Session, hesap, rol: str) -> None:
    """Öğrenci ve okul yetkilisi için okul kapalıysa 423; süper admin her zaman geçer."""
    if rol == "super_admin":
        return
    okul_acik_olmali(db, getattr(hesap, "okul_id", None))
