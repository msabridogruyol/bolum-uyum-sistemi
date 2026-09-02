# -*- coding: utf-8 -*-
"""
Admin — Kutup Soru Toplu Yükleme (sonradan eklendi)

Bağımsız router — mevcut Likert/SJT toplu yükleme mantığına dokunmaz.

Format: her satır TEK bir kutup sorusu tanımlar (Likert/SJT'nin aksine
çok satırlı değil, çünkü 4 seçenek metni A/B uç etiketlerinden otomatik
üretilir).

Beklenen sütunlar: katman_kod, a_degisken_kod, b_degisken_kod, soru_metni,
                    a_ucu_etiketi, b_ucu_etiketi

GET  /admin/kutup-sorulari/sablon-bilgisi — sütun açıklaması (opsiyonel yardımcı)
POST /admin/kutup-sorulari/toplu          — toplu yükleme
"""

from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.api.deps import get_mevcut_admin
from app.models import AdminKullanici, Soru, SoruSecenegi, Katman, Degisken

router = APIRouter(prefix="/kutup-sorulari", tags=["admin-kutup"])


class KutupSoruGirisi(BaseModel):
    katman_kod: str
    a_degisken_kod: str
    b_degisken_kod: str
    soru_metni: str
    a_ucu_etiketi: str  # kısa etiket, örn. "Yalnız çalışmak"
    b_ucu_etiketi: str  # kısa etiket, örn. "Ekiple çalışmak"


class TopluKutupIstek(BaseModel):
    satirlar: list[KutupSoruGirisi]


class TopluKutupSonuc(BaseModel):
    eklenen_soru_sayisi: int
    hatalar: list[str]


@router.post("/toplu", response_model=TopluKutupSonuc)
def kutup_sorularini_toplu_yukle(
    istek: TopluKutupIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    hatalar: list[str] = []
    eklenen = 0

    for i, satir in enumerate(istek.satirlar, start=1):
        katman = db.query(Katman).filter(Katman.kod == satir.katman_kod).first()
        if katman is None:
            hatalar.append(f"Satır {i}: katman bulunamadı ({satir.katman_kod})")
            continue

        a_degisken = db.query(Degisken).filter(Degisken.kod == satir.a_degisken_kod).first()
        b_degisken = db.query(Degisken).filter(Degisken.kod == satir.b_degisken_kod).first()
        if a_degisken is None:
            hatalar.append(f"Satır {i}: A ucu değişkeni bulunamadı ({satir.a_degisken_kod})")
            continue
        if b_degisken is None:
            hatalar.append(f"Satır {i}: B ucu değişkeni bulunamadı ({satir.b_degisken_kod})")
            continue
        if not satir.soru_metni.strip():
            hatalar.append(f"Satır {i}: soru metni boş")
            continue

        soru = Soru(
            katman_id=katman.id, degisken_id=a_degisken.id, b_ucu_degisken_id=b_degisken.id,
            soru_tipi="kutup", soru_metni=satir.soru_metni.strip(), aktif_mi=True,
        )
        db.add(soru)
        db.flush()  # soru.id'yi almak için

        secenek_metinleri = [
            f"Kesinlikle {satir.a_ucu_etiketi}",
            f"Daha Çok {satir.a_ucu_etiketi}",
            f"Daha Çok {satir.b_ucu_etiketi}",
            f"Kesinlikle {satir.b_ucu_etiketi}",
        ]
        for sira, metin in enumerate(secenek_metinleri, start=1):
            db.add(SoruSecenegi(soru_id=soru.id, secenek_sirasi=sira, secenek_metni=metin))

        eklenen += 1

    db.commit()
    return TopluKutupSonuc(eklenen_soru_sayisi=eklenen, hatalar=hatalar)


# ============================================================================
# NOT — main.py'de, admin_guvenlik ile AYNI yere şunu ekleyin:
#   from app.api.admin_kutup_yukleme import router as admin_kutup_router
#   app.include_router(admin_kutup_router, prefix="/admin", tags=["admin"])
# Dosyayı backend/app/api/admin_kutup_yukleme.py olarak kaydedin.
# ============================================================================
