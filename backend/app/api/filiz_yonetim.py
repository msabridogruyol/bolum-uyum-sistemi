# -*- coding: utf-8 -*-
"""
[2026-10-11] Filiz — yönetim paneli asistanı uç noktaları (okul yetkilisi + süper admin).

  GET  /yonetim/filiz/ozet  — balon için günün bulguları (yalnızca sayılar, öğrenci adı yok) + hazır soru çipleri + mod
  POST /yonetim/filiz/sor   — {metin, gecmis?} → cevap + mod ('ai' | 'rehber'). Yönlendirme (app/core/filiz_yonetim_ai.py):
                              kriz → sabit yönlendirme; kişiye özel veri (öğrenci adı / e-posta / no, kişi listesi) → yetki
                              kapsamında YEREL cevap (yapay zekâya gitmez); diğerleri → yapay zekâ (maskelenmiş) ya da
                              kural tabanlı rehber (app/core/filiz_yonetim_rehber.py).
  GET  /yonetim/filiz/sss   — okul yetkilisi SSS'i (Sistem Hakkında & SSS sayfası bunu gösterir; tek kaynak)

Kapsam: okul yetkilisi YALNIZCA kendi okulunu görür (okul_id istemciden alınmaz, hesaptan gelir) ve /ozet, /sor
okulun paketinde 'filiz' modülü açıksa çalışır; süper admin her zaman. Yapay zekâ modu: okulda 'filiz_ai' + OPENAI_API_KEY
(süper adminde yalnızca anahtar). Sorular kaydedilmez; yalnızca günlük sayaç.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.core.database import get_db
from app.core.filiz_yonetim_ai import ai_modu, yanitla_yonetim
from app.core.filiz_yonetim_rehber import filiz_ozeti, sss_listesi
from app.models import AdminKullanici

router = APIRouter(prefix="/yonetim/filiz", tags=["Filiz — yönetim asistanı"])


def _filiz_acik(db: Session, yon: AdminKullanici) -> None:
    if yon.rol == "super_admin":
        return
    from app.core.paketler import okul_modulleri
    if not yon.okul_id or "filiz" not in okul_modulleri(db, yon.okul_id):
        raise HTTPException(403, "Filiz okulunuzun paketinde açık değil.")


@router.get("/ozet")
def ozet(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _filiz_acik(db, yon)
    from app.core.kvkk_metinleri import YONETIM_FILIZ_AI_AYDINLATMA, YONETIM_FILIZ_REHBER_AYDINLATMA
    ai = ai_modu(db, yon)
    return {**filiz_ozeti(db, yon), "mod": "ai" if ai else "rehber",
            "aydinlatma": YONETIM_FILIZ_AI_AYDINLATMA if ai else YONETIM_FILIZ_REHBER_AYDINLATMA}


class GecmisMesaj(BaseModel):
    rol: str = Field(..., pattern="^(kullanici|filiz)$")
    metin: str = Field(..., max_length=2000)


class SoruIstek(BaseModel):
    metin: str = Field(..., max_length=500)
    gecmis: list[GecmisMesaj] = Field(default_factory=list, max_length=20)   # yalnızca bu sekmedeki sohbet; sunucuda saklanmaz


@router.post("/sor")
def sor(istek: SoruIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _filiz_acik(db, yon)
    return yanitla_yonetim(db, yon, istek.metin, istek.gecmis)


@router.get("/sss")
def sss(yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    return {"sss": sss_listesi(yon.rol, yon.okul_id)}
