# -*- coding: utf-8 -*-
"""
Admin — Meslek Verisi Toplu Yükleme (sonradan eklendi)

Bağımsız bir router — mevcut admin.py'ye dokunmaz. main.py'de admin_guvenlik
ile AYNI şekilde kaydedilir.

POST /admin/meslekler/toplu-yukle — meslekler_esco.csv/xlsx içeriğini
                                     meslekler tablosuna yükler (eskisini
                                     temizleyip yeniden doldurur).
GET  /admin/meslekler/sayi         — mevcut meslek sayısını döner (kontrol için)
"""

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.api.deps import get_mevcut_admin
from app.models import AdminKullanici, Meslek

router = APIRouter(prefix="/meslekler", tags=["admin-meslekler"])


class MeslekGirisi(BaseModel):
    esco_kodu: str
    ad: str
    aciklama: str | None = None
    isco_grubu: str | None = None


class TopluMeslekYuklemeIstek(BaseModel):
    meslekler: list[MeslekGirisi]


class TopluMeslekSonuc(BaseModel):
    yuklenen_sayisi: int
    onceki_sayisi: int


@router.get("/sayi")
def meslek_sayisini_getir(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    sayi = db.query(Meslek).count()
    return {"meslek_sayisi": sayi}


@router.post("/toplu-yukle", response_model=TopluMeslekSonuc)
def meslekleri_toplu_yukle(
    istek: TopluMeslekYuklemeIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """
    [DİKKAT] Bu uç nokta meslekler tablosunu TAMAMEN TEMİZLEYİP yeniden
    doldurur (eski/kısmi veri kalmasın diye). Öğrencilerin hedef_meslek_id
    alanı bu tabloya referans veriyor — tablo boşken (ilk yükleme) risksiz,
    ama İKİNCİ bir yeniden yükleme öncesi öğrencilerin hedef meslek seçimleri
    sıfırlanabileceğini unutmayın (aşağıdaki NOT'a bakın).
    """
    if not istek.meslekler:
        raise HTTPException(status_code=400, detail="Yüklenecek meslek yok.")

    onceki_sayisi = db.query(Meslek).count()

    # [NOT] hedef_meslek_id bu tabloya referans veriyor — silmeden önce
    # var olan referansları temizle (öğrencinin hedef mesleği "boşa düşer",
    # silinmez, yalnızca hedef_meslek_id NULL olur).
    db.execute(text("UPDATE ogrenciler SET hedef_meslek_id = NULL WHERE hedef_meslek_id IS NOT NULL"))
    db.query(Meslek).delete()
    db.flush()

    for m in istek.meslekler:
        db.add(Meslek(
            isco_kodu=m.esco_kodu,
            ad=m.ad,
            aciklama=m.aciklama,
            alt_grup_kodu=m.isco_grubu or "",
            alt_grup_adi=None,
            ana_grup_kodu=None,
            kaynak="esco",
        ))

    db.commit()
    yeni_sayisi = db.query(Meslek).count()

    return TopluMeslekSonuc(yuklenen_sayisi=yeni_sayisi, onceki_sayisi=onceki_sayisi)


# ============================================================================
# NOT — main.py'de, admin_guvenlik ile AYNI yere şunu ekleyin:
#
#   from app.api.admin_meslek_yukleme import router as admin_meslek_router
#   app.include_router(admin_meslek_router, prefix="/admin", tags=["admin"])
#
# Dosyayı backend/app/api/admin_meslek_yukleme.py olarak kaydedin.
# ============================================================================
