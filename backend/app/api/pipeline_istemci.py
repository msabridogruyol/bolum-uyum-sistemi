# -*- coding: utf-8 -*-
"""
[2026-11-01] Bilgisayardaki pipeline'ın sistemle konuştuğu uç noktalar. Ayrıntı: app/core/pipeline_paketi.py

Kimlik: "X-Pipeline-Anahtari" başlığında bilgisayar anahtarı (kurulumda alınır, C:\\pipeline\\ayar.json).
POST /pipeline-istemci/etkinlestir          — tek kullanımlık kurulum anahtarı → bilgisayar anahtarı (anahtarsız uç)
GET  /pipeline-istemci/manifest             — kod dosyaları + son veri sürümünün dosya/parça listesi
GET  /pipeline-istemci/kod?yol=src/x.py      — kod dosyası
POST /pipeline-istemci/parca-adresleri      — parçalar için kısa süreli indirme adresleri (Storage)
GET  /pipeline-istemci/canli                — canlı bölüm / özellik / K5 listeleri (+ özetleri)
POST /pipeline-istemci/gonderim/baslat      — depoda olmayan parçalar için yükleme adresleri
POST /pipeline-istemci/gonderim/tamamla     — yeni veri sürümünü kaydet (eski sürümlerin artık parçaları budanır)
Bu uçlar canlı sisteme hiçbir şey YAYIMLAMAZ; çıktılar yine süper admin Pipeline Sonuçları ekranından canlıya alınır.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import pipeline_depo as depo
from app.core import pipeline_paketi as pp
from app.core.database import get_db

router = APIRouter(prefix="/pipeline-istemci", tags=["Pipeline istemcisi (bilgisayar)"])


def _cihaz(x_pipeline_anahtari: str | None = Header(None), db: Session = Depends(get_db)) -> dict:
    cihaz = pp.cihazi_dogrula(db, x_pipeline_anahtari)
    if cihaz is None:
        raise HTTPException(401, "Bilgisayar anahtarı geçersiz ya da erişimi kaldırılmış. Admin panelinden yeni kurulum "
                                 "dosyası indirip bu bilgisayara yeniden kurun.")
    return cihaz


def _depo_hatasi(e: Exception):
    raise HTTPException(503, str(e))


class EtkinlestirIstek(BaseModel):
    kurulum_anahtari: str = Field(..., min_length=20, max_length=200)


@router.post("/etkinlestir")
def etkinlestir(istek: EtkinlestirIstek, db: Session = Depends(get_db)):
    try:
        anahtar, ad = pp.kurulumu_etkinlestir(db, istek.kurulum_anahtari)
    except pp.PaketHatasi as e:
        db.rollback()
        raise HTTPException(400, str(e))
    db.commit()
    return {"cihaz_anahtari": anahtar, "cihaz_adi": ad}


@router.get("/manifest")
def manifest(db: Session = Depends(get_db), cihaz: dict = Depends(_cihaz)):
    kod = pp.kod_manifesti()
    son = pp.son_surum(db)
    return {"kod_surumu": pp.kod_surumu(kod), "kod": kod, "parca_boyutu": depo.PARCA_BOYUTU, "depo_hazir": depo.hazir_mi(),
            "veri": None if son is None else {"surum_id": son["id"], "zaman": son["zaman"], "cihaz_adi": son["cihaz_adi"],
                                              "dosyalar": son["dosyalar"]}}


@router.get("/kod")
def kod(yol: str = Query(..., max_length=300), cihaz: dict = Depends(_cihaz)):
    try:
        return Response(pp.kod_dosyasi(yol), media_type="application/octet-stream")
    except pp.PaketHatasi as e:
        raise HTTPException(404, str(e))


class ParcaListesi(BaseModel):
    parcalar: list[str] = Field(..., max_length=pp.EN_FAZLA_DOSYA)


@router.post("/parca-adresleri")
def parca_adresleri(istek: ParcaListesi, cihaz: dict = Depends(_cihaz)):
    try:
        return {"adresler": depo.indirme_adresleri(sorted(set(istek.parcalar)))}
    except depo.DepoHatasi as e:
        _depo_hatasi(e)


@router.get("/canli")
def canli(db: Session = Depends(get_db), cihaz: dict = Depends(_cihaz)):
    return pp.canli_listeler(db)


class Parca(BaseModel):
    sha256: str = Field(..., min_length=64, max_length=64)
    boyut: int = Field(..., ge=0)


class BaslatIstek(BaseModel):
    parcalar: list[Parca] = Field(..., max_length=pp.EN_FAZLA_DOSYA * 4)


@router.post("/gonderim/baslat")
def gonderim_baslat(istek: BaslatIstek, cihaz: dict = Depends(_cihaz)):
    try:
        return pp.gonderim_baslat([p.model_dump() for p in istek.parcalar])
    except pp.PaketHatasi as e:
        raise HTTPException(422, str(e))
    except depo.DepoHatasi as e:
        _depo_hatasi(e)


class TamamlaIstek(BaseModel):
    dosyalar: dict
    girdi_ozeti: dict | None = None
    aciklama: str | None = Field(None, max_length=500)


@router.post("/gonderim/tamamla")
def gonderim_tamamla(istek: TamamlaIstek, db: Session = Depends(get_db), cihaz: dict = Depends(_cihaz)):
    try:
        return pp.gonderim_tamamla(db, cihaz, istek.dosyalar, istek.girdi_ozeti, istek.aciklama)
    except pp.PaketHatasi as e:
        db.rollback()
        raise HTTPException(422, str(e))
    except depo.DepoHatasi as e:
        db.rollback()
        _depo_hatasi(e)
