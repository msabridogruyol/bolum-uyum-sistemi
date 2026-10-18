# -*- coding: utf-8 -*-
"""
[2026-10-11] Sistem Sözlüğü — veritabanından gelen terimler (sözlükte aranabilsin diye).

POST /ogrenci/sozluk/bildir                 — [2026-10-11] "Bu tanımda hata var" (öğrenci) → sozluk_bildirimleri
GET  /admin/sozluk-bildirimleri             — süper admin: açık bildirimler
PUT  /admin/sozluk-bildirimleri/{id}        — süper admin: {durum: 'cozuldu' | 'yeni'}
GET /ogrenci/sozluk/ek
  bolumler   : [{id, ad, t}]                 — 278 bölüm, açıklama = detay.ozet
  meslekler  : [{ad, t, bolumler:[{id, ad}]}] — bölüm detaylarındaki meslekler (tekil ada göre birleştirilir)
  ozellikler : [{ad, t, katman}]             — değerlendirmede ölçülen özellikler (açıklaması olanlar)

Kişisel veri yok; içerik herkese aynı. Yanıt süreç içinde önbelleğe alınır (içerik yönetim ekranından güncellenince
ONBELLEK_SN içinde tazelenir). Durumu 'aktif' olmayan bölümler dahil edilmez.
"""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_admin, get_mevcut_ogrenci
from app.core.database import get_db
from app.models import AdminKullanici, Ogrenci

router = APIRouter(prefix="/ogrenci/sozluk", tags=["Sözlük"])

ONBELLEK_SN = 600
_onbellek: dict = {"zaman": 0.0, "veri": None}


def _veri(db: Session) -> dict:
    bolumler, meslekler = [], {}
    rows = db.execute(text("SELECT id, ad, detay, durum FROM bolumler ORDER BY ad")).all()
    for r in rows:
        if r.durum and r.durum not in ("aktif", "yayinda"):
            continue
        d = r.detay or {}
        ozet = (d.get("ozet") or "").strip()
        if ozet:
            bolumler.append({"id": r.id, "ad": r.ad, "t": ozet})
        for m in d.get("meslekler") or []:
            if not isinstance(m, dict) or not (m.get("ad") or "").strip():
                continue
            ad = m["ad"].strip()
            k = meslekler.setdefault(ad, {"ad": ad, "t": (m.get("aciklama") or "").strip(), "bolumler": []})
            if not k["t"] and m.get("aciklama"):
                k["t"] = m["aciklama"].strip()
            if all(b["id"] != r.id for b in k["bolumler"]):
                k["bolumler"].append({"id": r.id, "ad": r.ad})
    ozellikler = [{"ad": r.ad, "t": r.aciklama.strip(), "katman": r.katman} for r in db.execute(text(
        "SELECT d.ad, d.aciklama, k.kod AS katman FROM degiskenler d LEFT JOIN katmanlar k ON k.id = d.katman_id "
        "WHERE coalesce(d.aciklama, '') <> '' ORDER BY d.ad")).all()]
    return {"bolumler": bolumler, "meslekler": [m for m in meslekler.values() if m["t"]], "ozellikler": ozellikler}


@router.get("/ek")
def sozluk_ek(response: Response, db: Session = Depends(get_db), _o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if _onbellek["veri"] is None or time.time() - _onbellek["zaman"] > ONBELLEK_SN:
        _onbellek["veri"] = _veri(db)
        _onbellek["zaman"] = time.time()
    response.headers["Cache-Control"] = "private, max-age=600"
    return _onbellek["veri"]


# ----------------------------------------------------------------------------- [2026-10-11] hata bildirimi
admin_router = APIRouter(prefix="/admin/sozluk-bildirimleri", tags=["Sözlük"])


class BildirimIstek(BaseModel):
    terim: str = Field(min_length=1, max_length=200)
    k: str | None = Field(default=None, max_length=40)
    aciklama: str | None = Field(default=None, max_length=500)


@router.post("/bildir", status_code=201)
def sozluk_bildir(istek: BildirimIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    # aynı öğrenci aynı terimi 24 saatte bir kez bildirebilir (spam olmasın)
    var = db.execute(text("SELECT 1 FROM sozluk_bildirimleri WHERE ogrenci_id = :o AND terim = :t AND olusturulma_zamani > now() - interval '1 day'"),
                     {"o": o.id, "t": istek.terim.strip()}).first()
    if var:
        return {"kaydedildi": False, "mesaj": "Bu kelimeyi zaten bildirdin, teşekkürler."}
    db.execute(text("INSERT INTO sozluk_bildirimleri (terim, terim_k, aciklama, ogrenci_id, okul_id) VALUES (:t, :k, :a, :o, :ok)"),
               {"t": istek.terim.strip(), "k": istek.k, "a": (istek.aciklama or "").strip() or None, "o": o.id, "ok": o.okul_id})
    db.commit()
    return {"kaydedildi": True, "mesaj": "Teşekkürler! Bildirimin incelenecek."}


@admin_router.get("")
def bildirimler(durum: str = "yeni", db: Session = Depends(get_db), _a: AdminKullanici = Depends(get_mevcut_admin)):
    rows = db.execute(text("""SELECT b.id, b.terim, b.terim_k, b.aciklama, b.durum, b.olusturulma_zamani, k.ad AS okul
                                FROM sozluk_bildirimleri b LEFT JOIN okullar k ON k.id = b.okul_id
                               WHERE (:d = 'hepsi' OR b.durum = :d) ORDER BY b.olusturulma_zamani DESC LIMIT 200"""), {"d": durum}).mappings().all()
    return {"bildirimler": [dict(r) for r in rows],
            "yeni_sayisi": db.execute(text("SELECT count(*) FROM sozluk_bildirimleri WHERE durum = 'yeni'")).scalar() or 0}


class DurumIstek(BaseModel):
    durum: str


@admin_router.put("/{bildirim_id}", status_code=204)
def bildirim_durumu(bildirim_id: int, istek: DurumIstek, db: Session = Depends(get_db), _a: AdminKullanici = Depends(get_mevcut_admin)):
    if istek.durum not in ("yeni", "cozuldu"):
        raise HTTPException(400, "Geçersiz durum.")
    db.execute(text("UPDATE sozluk_bildirimleri SET durum = :d WHERE id = :i"), {"d": istek.durum, "i": bildirim_id})
    db.commit()
