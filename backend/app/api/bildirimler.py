# -*- coding: utf-8 -*-
"""
[2026-10-10] Bildirim kutusu (öğrenci ve yönetim) ve e-posta tercihi.

  GET  /ogrenci/bildirimler            — son 40 bildirim + okunmamış sayısı
  POST /ogrenci/bildirimler/okundu     — {idler: [..]} ya da {} (hepsi)
  GET  /ogrenci/bildirim-tercihi       — {eposta}
  PUT  /ogrenci/bildirim-tercihi       — {eposta}
  GET  /yonetim/bildirimler, POST /yonetim/bildirimler/okundu, GET/PUT /yonetim/bildirim-tercihi — aynıları okul yetkilisi / süper admin için
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.database import get_db

ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Bildirimler"])
yonetim_router = APIRouter(prefix="/yonetim", tags=["Bildirimler"])


def _liste(db: Session, tip: str, kid) -> dict:
    rows = db.execute(text("""
        SELECT id, tur, baslik, metin, link, okundu, olusturulma_zamani FROM bildirimler
         WHERE alici_tipi = :t AND alici_id = :k ORDER BY olusturulma_zamani DESC LIMIT 40
    """), {"t": tip, "k": kid}).mappings().all()
    okunmamis = db.execute(text("SELECT count(*) FROM bildirimler WHERE alici_tipi = :t AND alici_id = :k AND NOT okundu"),
                           {"t": tip, "k": kid}).scalar() or 0
    return {"bildirimler": [dict(r) for r in rows], "okunmamis": okunmamis}


class OkunduIstek(BaseModel):
    idler: list[int] | None = None


def _okundu(db: Session, tip: str, kid, idler) -> dict:
    if idler:
        db.execute(text("UPDATE bildirimler SET okundu = TRUE WHERE alici_tipi = :t AND alici_id = :k AND id = ANY(:i)"),
                   {"t": tip, "k": kid, "i": idler})
    else:
        db.execute(text("UPDATE bildirimler SET okundu = TRUE WHERE alici_tipi = :t AND alici_id = :k AND NOT okundu"), {"t": tip, "k": kid})
    db.commit()
    return _liste(db, tip, kid)


class TercihIstek(BaseModel):
    eposta: bool


def _tercih(db: Session, kid) -> dict:
    r = db.execute(text("SELECT eposta FROM bildirim_tercihleri WHERE kullanici_id = :k"), {"k": kid}).first()
    return {"eposta": True if r is None else bool(r.eposta)}


def _tercih_yaz(db: Session, kid, eposta: bool) -> dict:
    db.execute(text("INSERT INTO bildirim_tercihleri (kullanici_id, eposta) VALUES (:k, :e) "
                    "ON CONFLICT (kullanici_id) DO UPDATE SET eposta = EXCLUDED.eposta"), {"k": kid, "e": eposta})
    db.commit()
    return _tercih(db, kid)


@ogrenci_router.get("/bildirimler")
def ogrenci_bildirimleri(db: Session = Depends(get_db), o=Depends(get_mevcut_ogrenci)):
    return _liste(db, "ogrenci", o.id)


@ogrenci_router.post("/bildirimler/okundu")
def ogrenci_okundu(istek: OkunduIstek, db: Session = Depends(get_db), o=Depends(get_mevcut_ogrenci)):
    return _okundu(db, "ogrenci", o.id, istek.idler)


@ogrenci_router.get("/bildirim-tercihi")
def ogrenci_tercih(db: Session = Depends(get_db), o=Depends(get_mevcut_ogrenci)):
    return _tercih(db, o.id)


@ogrenci_router.put("/bildirim-tercihi")
def ogrenci_tercih_yaz(istek: TercihIstek, db: Session = Depends(get_db), o=Depends(get_mevcut_ogrenci)):
    return _tercih_yaz(db, o.id, istek.eposta)


@yonetim_router.get("/bildirimler")
def yonetim_bildirimleri(db: Session = Depends(get_db), yon=Depends(get_mevcut_yonetim)):
    return _liste(db, "yonetim", yon.id)


@yonetim_router.post("/bildirimler/okundu")
def yonetim_okundu(istek: OkunduIstek, db: Session = Depends(get_db), yon=Depends(get_mevcut_yonetim)):
    return _okundu(db, "yonetim", yon.id, istek.idler)


@yonetim_router.get("/bildirim-tercihi")
def yonetim_tercih(db: Session = Depends(get_db), yon=Depends(get_mevcut_yonetim)):
    return _tercih(db, yon.id)


@yonetim_router.put("/bildirim-tercihi")
def yonetim_tercih_yaz(istek: TercihIstek, db: Session = Depends(get_db), yon=Depends(get_mevcut_yonetim)):
    return _tercih_yaz(db, yon.id, istek.eposta)
