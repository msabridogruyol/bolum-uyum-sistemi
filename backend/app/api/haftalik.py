"""
[2026-10-04] Haftalık görevler.
GET  /haftalik                       — bu haftanın 3 görevi + seri + son 8 hafta + Filiz seviyesi
POST /haftalik/gorev/{id}/tamamla    — görevi tamamla (yansıtma için 3 cevap gönderilir)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core.database import get_db
from app.core.katman_servisi import IsKuraliHatasi
from app.core.haftalik_servisi import haftalik_ozet, gorevi_tamamla
from app.models import Ogrenci
from app.schemas.haftalik import HaftalikOzetOut, GorevTamamlaIstek

router = APIRouter()


@router.get("", response_model=HaftalikOzetOut)
def haftalik_ozeti_getir(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    ozet = haftalik_ozet(db, ogrenci)
    db.commit()  # ilk açılışta oluşturulan görevler ve otomatik tamamlamalar kaydedilir
    return HaftalikOzetOut(**ozet)


@router.post("/gorev/{gorev_id}/tamamla", response_model=HaftalikOzetOut)
def haftalik_gorevi_tamamla(
    gorev_id: int,
    istek: GorevTamamlaIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    try:
        gorevi_tamamla(db, ogrenci, gorev_id, istek.yanit)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    ozet = haftalik_ozet(db, ogrenci)
    db.commit()
    return HaftalikOzetOut(**ozet)
