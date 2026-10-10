# -*- coding: utf-8 -*-
"""
[2026-10-10] YÖK Atlas eşleştirme yönetimi (süper admin).

GET  /admin/yokatlas/eslesme            — tüm bölümler: otomatik / elle / eşleşmeyen + benzer YÖK Atlas program adayları
PUT  /admin/yokatlas/bolum/{bolum_id}   — bölüme elle YÖK Atlas program grubu ata (boş liste = otomatiğe dön)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.api.deps import get_mevcut_super_admin
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core import yokatlas_servisi as ys
from app.models import AdminKullanici, Bolum, YokatlasOnbellek

router = APIRouter(prefix="/admin/yokatlas", tags=["Admin — YÖK Atlas"])


@router.get("/eslesme")
def eslesme_raporu(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    try:
        gruplar = ys.grup_listesi()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"YÖK Atlas'a bağlanılamadı: {type(e).__name__}")
    alan = {r[0]: (r[1], r[2]) for r in db.execute(text(
        "SELECT e.bolum_id, d.kod, d.ad FROM bolum_dal_eslesme e JOIN dallar d ON d.id = e.dal_id")).all()}
    onbellek = {k.bolum_id: k for k in db.query(YokatlasOnbellek).all()}
    satirlar = []
    for b in db.query(Bolum).order_by(Bolum.ad).all():
        elle = ys.elle_gruplar(b)
        otomatik = [g.birim_grup_adi for g in ys.otomatik_eslesme(b.ad, gruplar)]
        durum = "elle" if elle else ("otomatik" if otomatik else "yok")
        kod, alan_ad = alan.get(b.id, (None, None))
        k = onbellek.get(b.id)
        program = len((k.veri or {}).get("programlar") or []) if k and k.veri else None
        satirlar.append({
            "id": b.id, "ad": b.ad, "alan": alan_ad, "ozel_yetenek_alani": kod in ys.OZEL_YETENEK_ALANLARI,
            "durum": durum, "gruplar": elle or otomatik,
            "adaylar": [] if (elle or otomatik) else [{"ad": a, "puan": p} for a, p in ys.benzer_adaylar(b.ad, gruplar)],
            "program_sayisi": program,
        })
    return {
        "bolumler": satirlar,
        "grup_adlari": sorted(g.birim_grup_adi for g in gruplar),
        "ozet": {"toplam": len(satirlar), "otomatik": sum(s["durum"] == "otomatik" for s in satirlar),
                 "elle": sum(s["durum"] == "elle" for s in satirlar), "yok": sum(s["durum"] == "yok" for s in satirlar)},
    }


class GrupIstek(BaseModel):
    gruplar: list[str]


@router.put("/bolum/{bolum_id}")
def elle_eslestir(bolum_id: int, istek: GrupIstek, db: Session = Depends(get_db),
                  yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    b = db.get(Bolum, bolum_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")
    gecerli = {ys._normalize(g.birim_grup_adi): g.birim_grup_adi for g in ys.grup_listesi()}
    secilen = []
    for ad in istek.gruplar:
        g = gecerli.get(ys._normalize(ad))
        if g is None:
            raise HTTPException(status_code=400, detail=f"YÖK Atlas'ta böyle bir program yok: {ad}")
        if g not in secilen:
            secilen.append(g)
    detay = dict(b.detay) if isinstance(b.detay, dict) else {}
    if secilen:
        detay["yokatlas_gruplari"] = secilen[:10]
    else:
        detay.pop("yokatlas_gruplari", None)
    b.detay = detay
    flag_modified(b, "detay")
    k = db.get(YokatlasOnbellek, b.id)
    if k is not None:
        db.delete(k)          # bir sonraki açılışta yeni eşleşmeyle çekilsin
    denetim_yaz(db, yon, "yokatlas_eslestir", "bolumler", b.id, f"{b.ad} → {', '.join(secilen) or 'otomatik'}")
    db.commit()
    return {"gruplar": secilen}
