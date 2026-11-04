"""[2026-11-04] Süper admin › Gece Bakımı: bekleyen gece işleri (iptal edilebilir) ve son bakımların sonucu."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_super_admin
from app.core.database import get_db
from app.core.gece_bakimi import KUYRUK_TURLERI, bakim_saati, bekleyenler, zamanlama_metni
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici

router = APIRouter(prefix="/admin/gece-bakimi", tags=["Yönetim — Gece bakımı"])


@router.get("")
def gece_bakimi_durumu(db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_super_admin)):
    s, d = bakim_saati(db)
    son = [dict(r) for r in db.execute(text("""SELECT gun, baslama, bitis, durum, ayrinti FROM gece_bakim_kaydi
                                              ORDER BY gun DESC LIMIT 14""")).mappings().all()]
    return {"saat": f"{s:02d}:{d:02d}", "sonraki": zamanlama_metni(db), "turler": KUYRUK_TURLERI,
            "kuyruk": bekleyenler(db), "son_bakimlar": son}


@router.post("/kuyruk/{kid}/iptal", status_code=204)
def gece_isini_iptal_et(kid: int, db: Session = Depends(get_db), admin: AdminKullanici = Depends(get_mevcut_super_admin)):
    n = db.execute(text("UPDATE gece_kuyrugu SET durum = 'iptal', sonuc = :s WHERE id = :i AND durum = 'bekliyor'"),
                   {"i": kid, "s": f"{admin.ad_soyad} iptal etti"}).rowcount
    if not n:
        raise HTTPException(status_code=404, detail="Bekleyen iş bulunamadı (çalışmış ya da iptal edilmiş olabilir).")
    denetim_yaz(db, admin, "gece_isi_iptal", "gece_kuyrugu", kid, None)
    db.commit()
