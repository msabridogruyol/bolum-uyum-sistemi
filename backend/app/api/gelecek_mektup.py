"""
[2026-10-13] Öğrenci: "Gelecekteki sana mektup" (prefix /ogrenci; ayrıntı ve gizlilik: app/core/gelecek_mektup.py).

  GET    /gelecek-mektup             — mektuplar (mühürlü olanların metni dönmez), tarih seçenekleri
  POST   /gelecek-mektup             — yaz ve mühürle (en çok 3 bekleyen)
  PUT    /gelecek-mektup/{id}        — bekleyen mektubun teslim tarihini değiştir
  DELETE /gelecek-mektup/{id}        — sil (kalıcı)
Okul / yönetim ucu yoktur.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core import gelecek_mektup as gm
from app.core.database import get_db
from app.models import Ogrenci

router = APIRouter()


def _mektuplar(db: Session, o: Ogrenci) -> list[dict]:
    bugun = gm.turkiye_bugun()
    sonuc = []
    for r in db.execute(text("""SELECT id, metin_sifreli, kisisel_eposta_sifreli, teslim_tarihi, durum, olusturulma_zamani
                                  FROM gelecek_mektuplari WHERE ogrenci_id = :o ORDER BY teslim_tarihi"""), {"o": o.id}).all():
        acik = r.teslim_tarihi <= bugun
        sonuc.append({"id": r.id, "teslim_tarihi": r.teslim_tarihi.isoformat(), "durum": r.durum, "acik": acik,
                      "yazildigi": r.olusturulma_zamani.date().isoformat(),
                      "metin": gm.coz(r.metin_sifreli) if acik else None,
                      "kisisel_eposta": gm.maskele(gm.coz(r.kisisel_eposta_sifreli))})
    return sonuc


@router.get("/gelecek-mektup")
def mektuplarim(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.core import eposta_servisi as ep
    return {"mektuplar": _mektuplar(db, o), "secenekler": gm.tarih_secenekleri(o.sinif),
            "okul_eposta": gm.maskele(o.email), "eposta_acik": ep.eposta_yapilandirildi_mi(),
            "sinirlar": {"en_kisa": gm.EN_KISA, "en_uzun": gm.EN_UZUN, "en_az_gun": gm.EN_AZ_GUN, "en_cok_yil": gm.EN_COK_YIL}}


class MektupIstek(BaseModel):
    metin: str = Field(..., max_length=gm.EN_UZUN)
    teslim_tarihi: date
    kisisel_eposta: str | None = Field(None, max_length=200)


def _tarih_kontrol(t: date):
    if not gm.tarih_gecerli_mi(t):
        raise HTTPException(400, f"Teslim tarihi en az {gm.EN_AZ_GUN} gün, en çok {gm.EN_COK_YIL} yıl sonrası olmalı.")


@router.post("/gelecek-mektup")
def mektup_yaz(istek: MektupIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    metin = (istek.metin or "").strip()
    if len(metin) < gm.EN_KISA:
        raise HTTPException(400, f"Mektubun en az {gm.EN_KISA} karakter olmalı.")
    _tarih_kontrol(istek.teslim_tarihi)
    eposta = (istek.kisisel_eposta or "").strip() or None
    if eposta and not gm.EPOSTA_RX.match(eposta):
        raise HTTPException(400, "Kişisel e-posta adresi geçersiz görünüyor.")
    bekleyen = db.execute(text("SELECT count(*) FROM gelecek_mektuplari WHERE ogrenci_id = :o AND durum = 'bekliyor'"), {"o": o.id}).scalar()
    if bekleyen >= gm.EN_COK_BEKLEYEN:
        raise HTTPException(400, f"Aynı anda en çok {gm.EN_COK_BEKLEYEN} mühürlü mektubun olabilir.")
    db.execute(text("""INSERT INTO gelecek_mektuplari (ogrenci_id, metin_sifreli, kisisel_eposta_sifreli, teslim_tarihi)
                       VALUES (:o, :m, :e, :t)"""),
               {"o": o.id, "m": gm.sifrele(metin), "e": gm.sifrele(eposta), "t": istek.teslim_tarihi})
    db.commit()
    return {"mektuplar": _mektuplar(db, o)}


class TarihIstek(BaseModel):
    teslim_tarihi: date


@router.put("/gelecek-mektup/{mid}")
def mektup_tarih(mid: int, istek: TarihIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    _tarih_kontrol(istek.teslim_tarihi)
    r = db.execute(text("""UPDATE gelecek_mektuplari SET teslim_tarihi = :t
                            WHERE id = :i AND ogrenci_id = :o AND durum = 'bekliyor' RETURNING id"""),
                   {"t": istek.teslim_tarihi, "i": mid, "o": o.id}).first()
    if r is None:
        raise HTTPException(404, "Mühürlü mektup bulunamadı.")
    db.commit()
    return {"mektuplar": _mektuplar(db, o)}


@router.delete("/gelecek-mektup/{mid}")
def mektup_sil(mid: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    r = db.execute(text("DELETE FROM gelecek_mektuplari WHERE id = :i AND ogrenci_id = :o RETURNING id"), {"i": mid, "o": o.id}).first()
    if r is None:
        raise HTTPException(404, "Mektup bulunamadı.")
    db.commit()
    return {"mektuplar": _mektuplar(db, o)}
