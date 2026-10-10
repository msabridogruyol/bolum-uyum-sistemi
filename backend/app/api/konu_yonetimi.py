# -*- coding: utf-8 -*-
"""
[2026-10-10] Konu takibi listesinin yönetimi.

GET    /yonetim/konular?okul_id=           — okul_id yoksa genel liste (süper admin); varsa o okulun görünümü
POST   /yonetim/konular                    — {ders, ad, okul_id|null} konu ekle (okul_id null → genel, yalnızca süper admin)
PUT    /yonetim/konular/{id}               — {ad} yeniden adlandır (öğrencilerin bu konudaki durumu korunur)
DELETE /yonetim/konular/{id}               — sil (genel konu yalnızca süper admin; öğrenci durumları da silinir)
POST   /yonetim/konular/{id}/gizle         — {okul_id, gizli} genel konuyu okulda gizle / göster
POST   /yonetim/konular/{id}/tasi          — {yon: yukari|asagi} aynı kaynaktaki komşusuyla yer değiştir
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_yonetimi import _okul_kapsami
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.konu_servisi import yonetim_listesi
from app.core.sinav_yapisi import KONU_DERSLERI
from app.models import AdminKullanici

router = APIRouter(prefix="/yonetim/konular", tags=["Konu listesi"])


def _super(yon: AdminKullanici):
    if yon.rol != "super_admin":
        raise HTTPException(403, "Genel konu listesini yalnızca süper admin değiştirebilir.")


def _konu(db: Session, konu_id: int):
    r = db.execute(text("SELECT id, ders, ad, sira, okul_id FROM sinav_konulari WHERE id = :i"), {"i": konu_id}).first()
    if r is None:
        raise HTTPException(404, "Konu bulunamadı.")
    return r


def _yetki(db: Session, yon: AdminKullanici, r):
    """Genel konu → süper admin; okul konusu → o okulun yetkilisi ya da süper admin."""
    if r.okul_id is None:
        _super(yon)
    else:
        _okul_kapsami(db, yon, r.okul_id)


def _ad_temizle(ad: str) -> str:
    ad = " ".join((ad or "").split())
    if not ad:
        raise HTTPException(400, "Konu adı boş olamaz.")
    return ad[:120]


@router.get("")
def listele(okul_id: int | None = None, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    if okul_id:
        _okul_kapsami(db, yon, okul_id)
    elif yon.rol != "super_admin":
        okul_id = yon.okul_id
    return {"okul_id": okul_id, "duzenleyebilir_genel": yon.rol == "super_admin", "dersler": yonetim_listesi(db, okul_id)}


class EkleIstek(BaseModel):
    ders: str
    ad: str = Field(max_length=120)
    okul_id: int | None = None


@router.post("")
def ekle(istek: EkleIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    if istek.ders not in KONU_DERSLERI:
        raise HTTPException(400, "Geçersiz ders.")
    if istek.okul_id:
        _okul_kapsami(db, yon, istek.okul_id)
    else:
        _super(yon)
    ad = _ad_temizle(istek.ad)
    var = db.execute(text("SELECT 1 FROM sinav_konulari WHERE ders = :d AND lower(ad) = lower(:a) AND (okul_id IS NULL OR okul_id = :o)"),
                     {"d": istek.ders, "a": ad, "o": istek.okul_id or -1}).first()
    if var:
        raise HTTPException(400, "Bu derste aynı adlı bir konu zaten var.")
    sira = db.execute(text("SELECT coalesce(max(sira), 0) + 10 FROM sinav_konulari WHERE ders = :d AND (okul_id IS NULL OR okul_id = :o)"),
                      {"d": istek.ders, "o": istek.okul_id or -1}).scalar()
    r = db.execute(text("INSERT INTO sinav_konulari (ders, ad, sira, okul_id, olusturan) VALUES (:d, :a, :s, :o, :u) RETURNING id"),
                   {"d": istek.ders, "a": ad, "s": sira, "o": istek.okul_id, "u": yon.ad_soyad}).first()
    denetim_yaz(db, yon, "konu_ekle", "sinav_konulari", r.id, f"{KONU_DERSLERI[istek.ders][1]}: {ad}", istek.okul_id)
    db.commit()
    return {"id": r.id}


class DuzenleIstek(BaseModel):
    ad: str = Field(max_length=120)


@router.put("/{konu_id}", status_code=204)
def duzenle(konu_id: int, istek: DuzenleIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = _konu(db, konu_id)
    _yetki(db, yon, r)
    ad = _ad_temizle(istek.ad)
    if ad == r.ad:
        return
    if db.execute(text("SELECT 1 FROM sinav_konulari WHERE ders = :d AND lower(ad) = lower(:a) AND id <> :i "
                       "AND (okul_id IS NULL OR okul_id = :o)"), {"d": r.ders, "a": ad, "i": r.id, "o": r.okul_id or -1}).first():
        raise HTTPException(400, "Bu derste aynı adlı bir konu zaten var.")
    db.execute(text("UPDATE sinav_konulari SET ad = :a WHERE id = :i"), {"a": ad, "i": r.id})
    # Öğrencilerin bu konudaki durumu yeni ada taşınır (genel konu: herkes; okul konusu: o okulun öğrencileri)
    db.execute(text("""
        UPDATE ogrenci_konu_takibi t SET konu = :yeni
         WHERE t.ders = :d AND t.konu = :eski
           AND (CAST(:o AS INTEGER) IS NULL OR t.ogrenci_id IN (SELECT id FROM ogrenciler WHERE okul_id = :o))
           AND NOT EXISTS (SELECT 1 FROM ogrenci_konu_takibi x WHERE x.ogrenci_id = t.ogrenci_id AND x.ders = t.ders AND x.konu = :yeni)"""),
               {"yeni": ad, "eski": r.ad, "d": r.ders, "o": r.okul_id})
    denetim_yaz(db, yon, "konu_duzenle", "sinav_konulari", r.id, f"{KONU_DERSLERI.get(r.ders, ('', r.ders))[1]}: {r.ad} → {ad}", r.okul_id)
    db.commit()


@router.delete("/{konu_id}", status_code=204)
def sil(konu_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = _konu(db, konu_id)
    _yetki(db, yon, r)
    db.execute(text("""
        DELETE FROM ogrenci_konu_takibi t WHERE t.ders = :d AND t.konu = :a
           AND (CAST(:o AS INTEGER) IS NULL OR t.ogrenci_id IN (SELECT id FROM ogrenciler WHERE okul_id = :o))"""),
               {"d": r.ders, "a": r.ad, "o": r.okul_id})
    db.execute(text("DELETE FROM sinav_konulari WHERE id = :i"), {"i": r.id})
    denetim_yaz(db, yon, "konu_sil", "sinav_konulari", r.id, f"{KONU_DERSLERI.get(r.ders, ('', r.ders))[1]}: {r.ad}", r.okul_id)
    db.commit()


class GizleIstek(BaseModel):
    okul_id: int
    gizli: bool


@router.post("/{konu_id}/gizle", status_code=204)
def gizle(konu_id: int, istek: GizleIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = _konu(db, konu_id)
    if r.okul_id is not None:
        raise HTTPException(400, "Okula özel konu gizlenmez; silinebilir.")
    _okul_kapsami(db, yon, istek.okul_id)
    if istek.gizli:
        db.execute(text("INSERT INTO okul_konu_gizleme (okul_id, konu_id) VALUES (:o, :k) ON CONFLICT DO NOTHING"),
                   {"o": istek.okul_id, "k": r.id})
    else:
        db.execute(text("DELETE FROM okul_konu_gizleme WHERE okul_id = :o AND konu_id = :k"), {"o": istek.okul_id, "k": r.id})
    denetim_yaz(db, yon, "konu_gizle" if istek.gizli else "konu_goster", "sinav_konulari", r.id,
                f"{KONU_DERSLERI.get(r.ders, ('', r.ders))[1]}: {r.ad}", istek.okul_id)
    db.commit()


class TasiIstek(BaseModel):
    yon: str = Field(pattern="^(yukari|asagi)$")


@router.post("/{konu_id}/tasi", status_code=204)
def tasi(konu_id: int, istek: TasiIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = _konu(db, konu_id)
    _yetki(db, yon, r)
    kosul = "okul_id IS NULL" if r.okul_id is None else "okul_id = :o"
    liste = db.execute(text(f"SELECT id, sira FROM sinav_konulari WHERE ders = :d AND {kosul} ORDER BY sira, id"),
                       {"d": r.ders, "o": r.okul_id}).all()
    idx = [x.id for x in liste].index(r.id)
    hedef = idx - 1 if istek.yon == "yukari" else idx + 1
    if hedef < 0 or hedef >= len(liste):
        return
    # sıraları 10'ar aralıkla yeniden yaz (eşit sıra değerleri sorun olmasın), sonra yer değiştir
    sirali = [x.id for x in liste]
    sirali[idx], sirali[hedef] = sirali[hedef], sirali[idx]
    for i, kid in enumerate(sirali, 1):
        db.execute(text("UPDATE sinav_konulari SET sira = :s WHERE id = :i"), {"s": i * 10, "i": kid})
    db.commit()
