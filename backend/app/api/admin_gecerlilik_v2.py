# -*- coding: utf-8 -*-
"""
Admin — Soru Geçerlilik Testi Girdisi V2 (sonradan eklendi)

Mevcut gecerlilik girdisi uç noktasından TEK FARKI: her satıra katman_kod
ekliyor. Bu sayede yerel test script'i (soru_gecerlilik_testi.py), her
soruyu yalnızca KENDİ KATMANINDAKİ değişkenler arasından test edebiliyor
— önceki sürüm 87+ değişkenin TAMAMI arasından seçtirdiği için katmanlar
arası anlamsız eşleşmeler (K1 sorusu K3 değişkeniyle karışması gibi) çıkıyordu.

Bağımsız router — mevcut admin.py'ye dokunmaz.

GET /admin/gecerlilik-girdisi-v2 — Likert soruları + SJT seçeneklerini,
                                     katman_kod dahil, dışa aktarır.
"""

from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.core.database import get_db
from app.api.deps import get_mevcut_admin
from app.models import (
    AdminKullanici, Soru, SoruSecenegi, SjtSecenekDegiskenAgirlik, Katman, Degisken,
)

router = APIRouter(prefix="/gecerlilik-girdisi-v2", tags=["admin-gecerlilik-v2"])


@router.delete("/sonuclar", status_code=204)
def gecerlilik_sonuclarini_temizle(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """[EKLENDİ] Ekrandaki eski soru geçerlilik test sonuçlarının tamamını
    siler — soruların/sistemin kendisine dokunmaz, yalnızca bu test
    kayıtlarını temizler. Yeni bir test çalıştırıp tekrar yükleyebilirsiniz."""
    from sqlalchemy import text
    db.execute(text("DELETE FROM soru_gecerlilik_sonuclari"))
    db.commit()


class GecerlilikBirimiOut(BaseModel):
    birim_anahtari: str
    kaynak_soru_id: int
    secenek_id: int | None
    kaynak_tipi: str  # 'likert' | 'sjt'
    katman_kod: str
    metin: str
    baglam: str | None
    beklenen_degisken_kod: str


@router.get("", response_model=list[GecerlilikBirimiOut])
def gecerlilik_girdisi_getir_v2(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    sonuc: list[GecerlilikBirimiOut] = []
    degisken_kodlari = dict(db.query(Degisken.id, Degisken.kod).all())

    # --- Likert sorular: soru metninin kendisi test edilir ---
    likert_sorular = (
        db.query(Soru, Katman.kod)
        .join(Katman, Katman.id == Soru.katman_id)
        .filter(Soru.soru_tipi == "likert", Soru.aktif_mi.is_(True), Soru.degisken_id.isnot(None))
        .all()
    )
    for soru, katman_kodu in likert_sorular:
        sonuc.append(GecerlilikBirimiOut(
            birim_anahtari=f"soru_{soru.id}", kaynak_soru_id=soru.id, secenek_id=None,
            kaynak_tipi="likert", katman_kod=katman_kodu, metin=soru.soru_metni, baglam=None,
            beklenen_degisken_kod=degisken_kodlari.get(soru.degisken_id, ""),
        ))

    # --- SJT seçenekleri: her seçeneğin EN YÜKSEK ağırlıklı değişkeni "beklenen" sayılır ---
    sjt_sorular = (
        db.query(Soru, Katman.kod)
        .join(Katman, Katman.id == Soru.katman_id)
        .filter(Soru.soru_tipi == "sjt", Soru.aktif_mi.is_(True))
        .all()
    )
    for soru, katman_kodu in sjt_sorular:
        secenekler = db.query(SoruSecenegi).filter(SoruSecenegi.soru_id == soru.id).all()
        for sec in secenekler:
            agirliklar = (
                db.query(SjtSecenekDegiskenAgirlik)
                .filter(SjtSecenekDegiskenAgirlik.secenek_id == sec.id)
                .order_by(SjtSecenekDegiskenAgirlik.agirlik.desc())
                .all()
            )
            if not agirliklar:
                continue
            en_yuksek = agirliklar[0]
            sonuc.append(GecerlilikBirimiOut(
                birim_anahtari=f"sjt_{soru.id}_{sec.id}", kaynak_soru_id=soru.id, secenek_id=sec.id,
                kaynak_tipi="sjt", katman_kod=katman_kodu, metin=sec.secenek_metni, baglam=soru.soru_metni,
                beklenen_degisken_kod=degisken_kodlari.get(en_yuksek.degisken_id, ""),
            ))

    # --- [EKLENDİ] Kutup seçenekleri: 1-2 numaralı şıklar A ucu değişkenine,
    # 3-4 numaralı şıklar B ucu değişkenine "beklenen" olarak atanır. ---
    kutup_sorular = (
        db.query(Soru, Katman.kod)
        .join(Katman, Katman.id == Soru.katman_id)
        .filter(Soru.soru_tipi == "kutup", Soru.aktif_mi.is_(True))
        .all()
    )
    for soru, katman_kodu in kutup_sorular:
        if soru.degisken_id is None or soru.b_ucu_degisken_id is None:
            continue
        secenekler = db.query(SoruSecenegi).filter(SoruSecenegi.soru_id == soru.id).order_by(SoruSecenegi.secenek_sirasi).all()
        for sec in secenekler:
            beklenen_id = soru.degisken_id if sec.secenek_sirasi <= 2 else soru.b_ucu_degisken_id
            sonuc.append(GecerlilikBirimiOut(
                birim_anahtari=f"kutup_{soru.id}_{sec.id}", kaynak_soru_id=soru.id, secenek_id=sec.id,
                kaynak_tipi="kutup", katman_kod=katman_kodu, metin=sec.secenek_metni, baglam=soru.soru_metni,
                beklenen_degisken_kod=degisken_kodlari.get(beklenen_id, ""),
            ))

    return sonuc


# ============================================================================
# NOT — main.py'de, admin_guvenlik ile AYNI yere şunu ekleyin:
#   from app.api.admin_gecerlilik_v2 import router as admin_gecerlilik_v2_router
#   app.include_router(admin_gecerlilik_v2_router, prefix="/admin", tags=["admin"])
# Dosyayı backend/app/api/admin_gecerlilik_v2.py olarak kaydedin.
# ============================================================================
