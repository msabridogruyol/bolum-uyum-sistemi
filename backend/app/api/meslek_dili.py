# -*- coding: utf-8 -*-
"""
[2026-10-09] Meslek dili (jargon) sözlüğünü düzenleme — süper admin ve okul yetkilisi.

Kapsam (okul_id sorgu parametresi):
  okul_id = 0  → GENEL sürüm: tüm okulların öğrencileri görür. Yalnızca süper admin.
  okul_id = N  → N okuluna ÖZEL sürüm: yalnızca o okulun öğrencileri görür. Okul yetkilisi yalnızca kendi okulu;
                 süper admin her okul için düzenleyebilir.
Okula özel sürüm yoksa öğrenci genel sürümü, genel sürüm de yoksa varsayılan içeriği (meslek_jargonu.json) görür.

GET    /yonetim/meslek-dili?okul_id=            — bölüm listesi + her bölümde hangi sürümün kullanıldığı
GET    /yonetim/meslek-dili/{bolum_id}?okul_id= — düzenlenecek terimler (+ bir üst sürüm, karşılaştırma için)
PUT    /yonetim/meslek-dili/{bolum_id}?okul_id= — kaydet (yoksa oluşturur)
DELETE /yonetim/meslek-dili/{bolum_id}?okul_id= — düzenlemeyi kaldır (okul → genele, genel → varsayılana döner)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz, simdi
from app.core.meslek_dili_servisi import etkin_surum, kayit_getir, varsayilan_terimler
from app.models import AdminKullanici, Bolum, MeslekDili, Okul

router = APIRouter(prefix="/yonetim/meslek-dili", tags=["Meslek dili"])

EN_FAZLA_TERIM = 40


def _kapsam(db: Session, yon: AdminKullanici, okul_id: int) -> int | None:
    """Dönen: None = genel sürüm, int = okul id."""
    if yon.rol == "okul_yetkilisi":
        if okul_id != yon.okul_id:
            raise HTTPException(status_code=403, detail="Yalnızca kendi okulunuzun meslek dili sözlüğünü düzenleyebilirsiniz.")
        return okul_id
    if okul_id == 0:
        return None
    if db.get(Okul, okul_id) is None:
        raise HTTPException(status_code=404, detail="Okul bulunamadı.")
    return okul_id


def _bolum(db: Session, bolum_id: int) -> Bolum:
    b = db.get(Bolum, bolum_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")
    return b


def _ust_surum(db: Session, b: Bolum, okul: int | None) -> dict:
    """Bu kapsamdaki düzenleme kaldırılırsa gösterilecek sürüm."""
    return etkin_surum(db, b, None) if okul else {"terimler": varsayilan_terimler(b.ad), "kaynak": "varsayilan"}


@router.get("")
def liste(okul_id: int = Query(...), db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    okul = _kapsam(db, yon, okul_id)
    kayitlar = {k.bolum_id: k for k in db.query(MeslekDili).filter(
        MeslekDili.okul_id.is_(None) if okul is None else MeslekDili.okul_id == okul).all()}
    genel = {} if okul is None else {k.bolum_id: k for k in db.query(MeslekDili).filter(MeslekDili.okul_id.is_(None)).all()}
    sonuc = []
    for b in db.query(Bolum).order_by(Bolum.ad).all():
        k = kayitlar.get(b.id)
        if k is not None:
            kaynak, sayi = ("okul" if okul else "genel"), len(k.terimler or [])
        elif b.id in genel:
            kaynak, sayi = "genel", len(genel[b.id].terimler or [])
        else:
            kaynak, sayi = "varsayilan", len(varsayilan_terimler(b.ad))
        sonuc.append({
            "bolum_id": b.id, "ad": b.ad, "terim_sayisi": sayi, "kaynak": kaynak,
            "duzenlendi": k is not None,
            "guncelleyen_ad": k.guncelleyen_ad if k else None,
            "guncelleme_zamani": k.guncelleme_zamani if k else None,
        })
    return {"kapsam": "genel" if okul is None else "okul", "okul_id": okul or 0, "bolumler": sonuc}


@router.get("/{bolum_id}")
def getir(bolum_id: int, okul_id: int = Query(...), db: Session = Depends(get_db),
          yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    okul = _kapsam(db, yon, okul_id)
    b = _bolum(db, bolum_id)
    k = kayit_getir(db, b.id, okul)
    ust = _ust_surum(db, b, okul)
    return {
        "bolum_id": b.id, "ad": b.ad, "kapsam": "genel" if okul is None else "okul",
        "duzenlendi": k is not None,
        "terimler": (k.terimler if k is not None else ust["terimler"]) or [],
        "guncelleyen_ad": k.guncelleyen_ad if k else None,
        "guncelleme_zamani": k.guncelleme_zamani if k else None,
        "ust_kaynak": ust["kaynak"],
    }


class TerimGirdi(BaseModel):
    terim: str = Field(..., max_length=80)
    anlam: str = Field(..., max_length=600)
    ornek: str | None = Field(None, max_length=400)


class KaydetGirdi(BaseModel):
    terimler: list[TerimGirdi]


@router.put("/{bolum_id}")
def kaydet(bolum_id: int, girdi: KaydetGirdi, okul_id: int = Query(...), db: Session = Depends(get_db),
           yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    okul = _kapsam(db, yon, okul_id)
    b = _bolum(db, bolum_id)
    temiz, gorulen = [], set()
    for i, t in enumerate(girdi.terimler, 1):
        terim, anlam, ornek = t.terim.strip(), t.anlam.strip(), (t.ornek or "").strip()
        if not terim and not anlam and not ornek:
            continue                                     # tamamen boş satır: atla
        if not terim or not anlam:
            raise HTTPException(status_code=422, detail=f"{i}. satır: terim ve anlamı boş bırakılamaz.")
        anahtar = terim.casefold()
        if anahtar in gorulen:
            raise HTTPException(status_code=422, detail=f"\"{terim}\" terimi listede birden fazla kez var.")
        gorulen.add(anahtar)
        temiz.append({"terim": terim, "anlam": anlam, "ornek": ornek})
    if not temiz:
        raise HTTPException(status_code=422, detail="En az bir terim girin. Tüm terimleri kaldırmak yerine 'Varsayılana dön' kullanın.")
    if len(temiz) > EN_FAZLA_TERIM:
        raise HTTPException(status_code=422, detail=f"Bir bölüm için en fazla {EN_FAZLA_TERIM} terim eklenebilir.")

    k = kayit_getir(db, b.id, okul)
    yeni = k is None
    if yeni:
        k = MeslekDili(bolum_id=b.id, okul_id=okul)
        db.add(k)
    k.terimler = temiz
    k.guncelleyen_ad = yon.ad_soyad
    k.guncelleme_zamani = simdi()
    kapsam_metni = "genel" if okul is None else "okula özel"
    denetim_yaz(db, yon, "meslek_dili_kaydet", "meslek_dili", b.id,
                f"{b.ad} — {kapsam_metni} sürüm {'oluşturuldu' if yeni else 'güncellendi'} ({len(temiz)} terim)", okul)
    db.commit()
    return getir(b.id, okul_id, db, yon)


@router.delete("/{bolum_id}")
def sifirla(bolum_id: int, okul_id: int = Query(...), db: Session = Depends(get_db),
            yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    okul = _kapsam(db, yon, okul_id)
    b = _bolum(db, bolum_id)
    k = kayit_getir(db, b.id, okul)
    if k is not None:
        db.delete(k)
        denetim_yaz(db, yon, "meslek_dili_sifirla", "meslek_dili", b.id,
                    f"{b.ad} — {'genel' if okul is None else 'okula özel'} düzenleme kaldırıldı", okul)
        db.commit()
    return getir(b.id, okul_id, db, yon)
