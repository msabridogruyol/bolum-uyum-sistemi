# -*- coding: utf-8 -*-
"""
[2026-10-10] Paket yönetimi.

Süper admin:
  GET    /yonetim/paketler                    — paketler + modül tanımları + her paketi kullanan okul sayısı
  POST   /yonetim/paketler                    — {ad, aciklama, moduller} yeni paket
  PUT    /yonetim/paketler/{kod}              — paketi düzenle
  DELETE /yonetim/paketler/{kod}              — kullanılmayan paketi sil
  PUT    /yonetim/okul/{okul_id}/paket        — {paket, ekle, cikar} okulun paketi ve okula özel modül farkları
Okul yetkilisi + süper admin:
  GET    /yonetim/okul/{okul_id}/paket        — okulun paketi ve etkin modülleri
Öğrenci:
  GET    /ogrenci/moduller                    — öğrencinin okulunda açık modüller
"""
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_super_admin, get_mevcut_yonetim
from app.api.okul_yonetimi import _okul_kapsami
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.paketler import MODULLER, okul_modulleri, okul_paket_bilgisi, paket_listesi
from app.models import AdminKullanici, Ogrenci
import json

router = APIRouter(prefix="/yonetim", tags=["Paketler"])
ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — Modüller"])


@ogrenci_router.get("/moduller")
def ogrenci_modulleri(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return {"moduller": okul_modulleri(db, o.okul_id)}


def _modul_listesi(liste: list[str]) -> list[str]:
    return [m for m in MODULLER if m in set(liste or [])]


@router.get("/paketler")
def paketler(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    sayi = dict(db.execute(text("SELECT paket, count(*) FROM okullar GROUP BY paket")).all())
    return {"paketler": [{**p, "okul_sayisi": sayi.get(p["kod"], 0)} for p in paket_listesi(db)],
            "moduller": [{"kod": k, **v} for k, v in MODULLER.items()]}


class PaketIstek(BaseModel):
    ad: str = Field(min_length=2, max_length=40)
    aciklama: str | None = Field(default=None, max_length=300)
    moduller: list[str] = Field(default_factory=list)


def _kod_uret(ad: str) -> str:
    t = ad.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU"))
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")[:30] or "paket"


@router.post("/paketler", status_code=201)
def paket_ekle(istek: PaketIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    kod = _kod_uret(istek.ad)
    if db.execute(text("SELECT 1 FROM paketler WHERE kod = :k"), {"k": kod}).first():
        raise HTTPException(400, "Bu adla bir paket zaten var.")
    sira = db.execute(text("SELECT coalesce(max(sira), 0) + 1 FROM paketler")).scalar()
    db.execute(text("INSERT INTO paketler (kod, ad, aciklama, moduller, sira) VALUES (:k, :a, :c, CAST(:m AS JSONB), :s)"),
               {"k": kod, "a": istek.ad.strip(), "c": (istek.aciklama or "").strip() or None,
                "m": json.dumps(_modul_listesi(istek.moduller)), "s": sira})
    denetim_yaz(db, yon, "paket_ekle", "paketler", kod, istek.ad)
    db.commit()
    return {"kod": kod}


@router.put("/paketler/{kod}", status_code=204)
def paket_duzenle(kod: str, istek: PaketIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    n = db.execute(text("UPDATE paketler SET ad = :a, aciklama = :c, moduller = CAST(:m AS JSONB) WHERE kod = :k"),
                   {"k": kod, "a": istek.ad.strip(), "c": (istek.aciklama or "").strip() or None,
                    "m": json.dumps(_modul_listesi(istek.moduller))}).rowcount
    if not n:
        raise HTTPException(404, "Paket bulunamadı.")
    denetim_yaz(db, yon, "paket_duzenle", "paketler", kod, f"{istek.ad}: {', '.join(_modul_listesi(istek.moduller))}")
    db.commit()


@router.delete("/paketler/{kod}", status_code=204)
def paket_sil(kod: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    kullanan = db.execute(text("SELECT count(*) FROM okullar WHERE paket = :k"), {"k": kod}).scalar() or 0
    if kullanan:
        raise HTTPException(400, f"Bu paketi {kullanan} okul kullanıyor; önce okulları başka pakete alın.")
    if not db.execute(text("DELETE FROM paketler WHERE kod = :k"), {"k": kod}).rowcount:
        raise HTTPException(404, "Paket bulunamadı.")
    denetim_yaz(db, yon, "paket_sil", "paketler", kod, kod)
    db.commit()


@router.get("/okul/{okul_id}/paket")
def okul_paketi(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    b = okul_paket_bilgisi(db, okul_id)
    return {**b, "modul_tanimlari": [{"kod": k, **v} for k, v in MODULLER.items()]}


class OkulPaketIstek(BaseModel):
    paket: str
    ekle: list[str] = Field(default_factory=list)
    cikar: list[str] = Field(default_factory=list)


@router.put("/okul/{okul_id}/paket")
def okul_paketi_kaydet(okul_id: int, istek: OkulPaketIstek, db: Session = Depends(get_db),
                       yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    if not okul_id or not db.execute(text("SELECT 1 FROM okullar WHERE id = :o"), {"o": okul_id}).first():
        raise HTTPException(404, "Okul bulunamadı.")
    p = db.execute(text("SELECT ad, moduller FROM paketler WHERE kod = :k"), {"k": istek.paket}).first()
    if p is None:
        raise HTTPException(400, "Paket bulunamadı.")
    paket_mod = set(p.moduller if isinstance(p.moduller, list) else json.loads(p.moduller or "[]"))
    ekle = [m for m in _modul_listesi(istek.ekle) if m not in paket_mod]          # pakette zaten olanı eklemeye gerek yok
    cikar = [m for m in _modul_listesi(istek.cikar) if m in paket_mod]           # pakette olmayanı çıkarmaya gerek yok
    db.execute(text("UPDATE okullar SET paket = :p, modul_ekle = CAST(:e AS JSONB), modul_cikar = CAST(:c AS JSONB) WHERE id = :o"),
               {"p": istek.paket, "e": json.dumps(ekle), "c": json.dumps(cikar), "o": okul_id})
    denetim_yaz(db, yon, "okul_paket", "okullar", okul_id,
                f"{p.ad}" + (f" + {', '.join(ekle)}" if ekle else "") + (f" − {', '.join(cikar)}" if cikar else ""), okul_id)
    db.commit()
    return okul_paket_bilgisi(db, okul_id)
