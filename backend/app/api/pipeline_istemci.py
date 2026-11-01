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
POST /pipeline-istemci/gonderim/tamamla     — yeni veri sürümünü kaydet (başka bilgisayar daha yeni gönderdiyse 409)
POST /pipeline-istemci/parca-bozuk          — doğrulanamayan parçayı sunucu denetler, bozuksa siler
Bu uçlar canlı sisteme hiçbir şey YAYIMLAMAZ; çıktılar yine süper admin Pipeline Sonuçları ekranından canlıya alınır.
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi.responses import Response
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints
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


Hex64 = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class ParcaListesi(BaseModel):
    parcalar: list[Hex64] = Field(..., max_length=pp.EN_FAZLA_DOSYA)


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
    sha256: Hex64
    boyut: int = Field(..., ge=0, le=pp.depo.PARCA_BOYUTU)


class BaslatIstek(BaseModel):
    parcalar: list[Parca] = Field(..., max_length=500)   # bilgisayar 100'lük gruplar hâlinde gönderir


@router.post("/gonderim/baslat")
def gonderim_baslat(istek: BaslatIstek, cihaz: dict = Depends(_cihaz)):
    try:
        return pp.gonderim_baslat([p.model_dump() for p in istek.parcalar])
    except pp.PaketHatasi as e:
        raise HTTPException(422, str(e))
    except depo.DepoHatasi as e:
        _depo_hatasi(e)


class TamamlaIstek(BaseModel):
    dosyalar: dict = Field(..., max_length=pp.EN_FAZLA_DOSYA)
    girdi_ozeti: dict[str, Annotated[str, StringConstraints(max_length=64)]] | None = Field(None, max_length=10)
    aciklama: str | None = Field(None, max_length=500)
    taban_surum_id: int | None = None     # bu çalıştırmanın başladığı veri sürümü (yoksa ilk gönderim)
    zorla: bool = False                    # başka bilgisayarın daha yeni sürümü olsa da bunu en yeni yap


@router.post("/gonderim/tamamla")
def gonderim_tamamla(istek: TamamlaIstek, db: Session = Depends(get_db), cihaz: dict = Depends(_cihaz)):
    try:
        return pp.gonderim_tamamla(db, cihaz, istek.dosyalar, istek.girdi_ozeti, istek.aciklama, istek.taban_surum_id, istek.zorla)
    except pp.SurumCakismasi as e:
        db.rollback()
        raise HTTPException(409, str(e))
    except pp.PaketHatasi as e:
        db.rollback()
        raise HTTPException(422, str(e))
    except depo.DepoHatasi as e:
        db.rollback()
        _depo_hatasi(e)


class BozukIstek(BaseModel):
    sha256: Hex64


@router.post("/parca-bozuk")
def parca_bozuk(istek: BozukIstek, cihaz: dict = Depends(_cihaz)):
    """İndirilen parça adıyla uyuşmadı: sunucu parçayı depodan okuyup denetler, gerçekten bozuksa siler."""
    try:
        return {"bozuktu": pp.parca_bozuk_bildir(istek.sha256)}
    except depo.DepoHatasi as e:
        _depo_hatasi(e)


# [2026-11-01] "disk" türü depo (kendi sunucu): parçalar backend üzerinden, kısa süreli imzalı adresle.
# Supabase türünde bu uçlar kullanılmaz (404). Ayrıntı: app/core/pipeline_depo_disk.py
def _disk_imza(sha256: str, islem: str, son: int, imza: str):
    from app.core import pipeline_depo_disk as disk
    if depo.tur() != "disk":
        raise HTTPException(404, "Bu sistemde disk deposu kullanılmıyor.")
    if not pp._HEX64.match(sha256) or islem not in ("indir", "yukle") or not disk.imza_gecerli_mi(islem, sha256, son, imza):
        raise HTTPException(403, "Adres geçersiz ya da süresi dolmuş.")
    return disk


@router.get("/depo/{sha256}")
def depo_indir(sha256: str, islem: str = Query(...), son: int = Query(...), imza: str = Query(..., max_length=64)):
    disk = _disk_imza(sha256, islem, son, imza)
    if islem != "indir":
        raise HTTPException(403, "Adres bu işlem için değil.")
    try:
        return Response(disk.parca_oku(sha256), media_type="application/octet-stream")
    except depo.DepoHatasi as e:
        raise HTTPException(404, str(e))


@router.put("/depo/{sha256}")
async def depo_yukle(sha256: str, request: Request, islem: str = Query(...), son: int = Query(...),
                     imza: str = Query(..., max_length=64)):
    disk = _disk_imza(sha256, islem, son, imza)
    if islem != "yukle":
        raise HTTPException(403, "Adres bu işlem için değil.")
    veri = await request.body()
    if len(veri) > depo.PARCA_BOYUTU:
        raise HTTPException(413, "Parça en fazla 20 MB olabilir.")
    try:
        disk.parca_yaz(sha256, veri)
    except depo.DepoHatasi as e:
        raise HTTPException(400, str(e))
    return {"Key": sha256}
