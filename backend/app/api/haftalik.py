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


@router.get("/gecmis")
def haftalik_gecmis(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    """[2026-10-10] Görevlerim sayfası: önceki haftaların görevleri ve yansıtma cevapları (son 16 hafta)."""
    import json
    from collections import OrderedDict
    from app.core.haftalik_servisi import YANSITMA_SORULARI, bugun_tr, hafta_baslangici
    from app.models import OgrenciHaftalikGorev
    bu_hafta = hafta_baslangici(bugun_tr())
    gorevler = (db.query(OgrenciHaftalikGorev)
                .filter(OgrenciHaftalikGorev.ogrenci_id == ogrenci.id, OgrenciHaftalikGorev.hafta_baslangic < bu_hafta)
                .order_by(OgrenciHaftalikGorev.hafta_baslangic.desc(), OgrenciHaftalikGorev.sira).limit(16 * 3).all())
    haftalar: "OrderedDict" = OrderedDict()
    for g in gorevler:
        h = haftalar.setdefault(g.hafta_baslangic, {"hafta": g.hafta_baslangic, "gorevler": [], "tamamlanan": 0})
        h["gorevler"].append({"baslik": g.baslik, "aciklama": g.aciklama, "tur": g.tur, "durum": g.durum,
                              "tamamlanma": g.tamamlanma_zamani, "yanit": json.loads(g.yanit) if g.yanit else None})
        h["tamamlanan"] += g.durum == "tamamlandi"
    return {"haftalar": list(haftalar.values()), "yansitma_sorulari": [{"anahtar": a, "soru": s} for a, s in YANSITMA_SORULARI]}
