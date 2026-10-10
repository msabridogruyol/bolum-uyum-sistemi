# -*- coding: utf-8 -*-
"""
[2026-10-10] Öğrenci "Listem" (★ favori bölümler) ve bölüm karşılaştırma.

GET    /ogrenci/listem                 — listem (uyum puanıyla, eklenme sırasına göre)
POST   /ogrenci/listem/{bolum_id}      — listeye ekle (en fazla 20)
DELETE /ogrenci/listem/{bolum_id}      — listeden çıkar
GET    /ogrenci/karsilastir?ids=1,2,3  — 2-3 bölümü yan yana: uyum, alan, öne çıkan özellikler
                                         (öğrencide de güçlü olanlar işaretli), örnek meslekler, meslek dili örneği.
                                         Üniversite / taban puan bilgisi frontend'de /bolumler/{id}/universiteler'den
                                         ayrı çekilir (YÖK Atlas önbelleği yavaş olabilir, sayfayı bekletmesin).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core.database import get_db
from app.models import (
    Bolum, BolumDalEslesme, Dal, Degisken, Ogrenci, OgrenciDegerlendirmeTuru, OgrenciDegiskenSkoru,
    OgrenciFavoriBolum,
)

router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — Listem ve Karşılaştırma"])

LISTE_SINIRI = 20


def _son_tamamlanan_tur(db: Session, o: Ogrenci):
    return (db.query(OgrenciDegerlendirmeTuru)
            .filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id, OgrenciDegerlendirmeTuru.durum == "tamamlandi")
            .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).first())


def uyum_haritasi(db: Session, o: Ogrenci) -> dict[int, float]:
    """Sonuç listesi ve Keşfet ile AYNI nihai uyum; K5 dalları bitmeden boş döner."""
    tur = _son_tamamlanan_tur(db, o)
    if tur is None:
        return {}
    try:
        from app.core.dal_servisi import bekleyen_dal_var_mi
        from app.core.skor_motoru import nihai_uyum_haritasi
        if bekleyen_dal_var_mi(db, o, tur):
            return {}
        return nihai_uyum_haritasi(db, o, tur)
    except Exception:
        db.rollback()
        return {}


def _alanlar(db: Session, bolum_idler: list[int]) -> dict[int, dict]:
    dallar = {d.id: d for d in db.query(Dal).all()}
    sonuc = {}
    for e in db.query(BolumDalEslesme).filter(BolumDalEslesme.bolum_id.in_(bolum_idler or [-1])).all():
        if e.bolum_id in sonuc:
            continue
        d = dallar.get(e.dal_id)
        sonuc[e.bolum_id] = {"ust_alan": d.ad if d and d.kod.startswith("U") else None,
                             "alt_alan": getattr(e, "alt_alan", None)}
    return sonuc


def favori_listesi(db: Session, o: Ogrenci, uyumlu: bool = True) -> list[dict]:
    satirlar = (db.query(OgrenciFavoriBolum, Bolum).join(Bolum, Bolum.id == OgrenciFavoriBolum.bolum_id)
                .filter(OgrenciFavoriBolum.ogrenci_id == o.id).order_by(OgrenciFavoriBolum.eklenme_zamani.desc()).all())
    uyum = uyum_haritasi(db, o) if uyumlu else {}
    alan = _alanlar(db, [b.id for _, b in satirlar])
    return [{"bolum_id": b.id, "bolum_adi": b.ad, "kisa_aciklama": b.kisa_aciklama,
             "toplam_uyum": round(float(uyum[b.id]), 1) if b.id in uyum else None,
             **alan.get(b.id, {"ust_alan": None, "alt_alan": None}),
             "eklenme_zamani": f.eklenme_zamani} for f, b in satirlar]


@router.get("/listem")
def listem(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return favori_listesi(db, o)


@router.post("/listem/{bolum_id}", status_code=201)
def listeye_ekle(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if db.get(Bolum, bolum_id) is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")
    var = db.query(OgrenciFavoriBolum).filter(OgrenciFavoriBolum.ogrenci_id == o.id, OgrenciFavoriBolum.bolum_id == bolum_id).first()
    if var is None:
        sayi = db.query(OgrenciFavoriBolum).filter(OgrenciFavoriBolum.ogrenci_id == o.id).count()
        if sayi >= LISTE_SINIRI:
            raise HTTPException(status_code=400, detail=f"Listende en fazla {LISTE_SINIRI} bölüm olabilir. Yer açmak için birini çıkar.")
        db.add(OgrenciFavoriBolum(ogrenci_id=o.id, bolum_id=bolum_id))
        db.commit()
    return {"bolum_id": bolum_id, "listede": True}


@router.delete("/listem/{bolum_id}")
def listeden_cikar(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    db.query(OgrenciFavoriBolum).filter(OgrenciFavoriBolum.ogrenci_id == o.id, OgrenciFavoriBolum.bolum_id == bolum_id).delete()
    db.commit()
    return {"bolum_id": bolum_id, "listede": False}


@router.get("/karsilastir")
def karsilastir(ids: str = Query(..., description="virgülle ayrılmış 2-3 bölüm id"), db: Session = Depends(get_db),
                o: Ogrenci = Depends(get_mevcut_ogrenci)):
    try:
        idler = list(dict.fromkeys(int(x) for x in ids.split(",") if x.strip()))[:3]
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz bölüm listesi.")
    if len(idler) < 2:
        raise HTTPException(status_code=400, detail="Karşılaştırmak için en az 2 bölüm seç.")
    bolumler = {b.id: b for b in db.query(Bolum).filter(Bolum.id.in_(idler)).all()}
    if len(bolumler) != len(idler):
        raise HTTPException(status_code=404, detail="Bölümlerden biri bulunamadı.")

    from app.api.bolum_bilgi import _yetkinlik_tablosu
    from app.core.meslek_dili_servisi import etkin_surum

    uyum = uyum_haritasi(db, o)
    alan = _alanlar(db, idler)
    tablo = _yetkinlik_tablosu(db)

    # Öğrencinin son tamamlanan turdaki özellik puanları (kod → puan): "sende de var" işareti için
    ogr_puan: dict[str, float] = {}
    tur = _son_tamamlanan_tur(db, o)
    if tur is not None:
        kodlar = {d.id: d.kod for d in db.query(Degisken).all()}
        for s in db.query(OgrenciDegiskenSkoru).filter(OgrenciDegiskenSkoru.ogrenci_id == o.id,
                                                       OgrenciDegiskenSkoru.tur_id == tur.id).all():
            if s.degisken_id in kodlar:
                ogr_puan[kodlar[s.degisken_id]] = float(s.puan)

    def sende_mi(x: dict) -> bool | None:
        p = ogr_puan.get(x["kod"])
        if p is None:
            return None
        return p >= 60 if x.get("uc") != "dusuk" else p <= 40

    sonuc = []
    for bid in idler:
        b = bolumler[bid]
        satirlar = [x for grup in tablo["tablo"].get(bid, {}).values() for x in grup if x["one_cikan"]]
        satirlar.sort(key=lambda x: -x["guc"])
        try:
            meslekler = [r[0] for r in db.execute(text(
                "SELECT meslek_adi FROM bolum_ornek_meslekler WHERE bolum_id = :b ORDER BY sira LIMIT 5"), {"b": bid}).all()]
        except Exception:   # tablo yoksa (yerel test vb.) karşılaştırma yine gösterilsin
            db.rollback()
            meslekler = []
        try:
            jargon = (etkin_surum(db, b, o.okul_id) or {}).get("terimler") or []
        except Exception:
            db.rollback()
            jargon = []
        sonuc.append({
            "bolum_id": bid, "bolum_adi": b.ad, "kisa_aciklama": b.kisa_aciklama,
            **alan.get(bid, {"ust_alan": None, "alt_alan": None}),
            "toplam_uyum": round(float(uyum[bid]), 1) if bid in uyum else None,
            "one_cikanlar": [{"kod": x["kod"], "etiket": x["etiket"], "onem": x["onem"], "sende": sende_mi(x)} for x in satirlar[:6]],
            "meslekler": meslekler,
            "jargon": [{"terim": t.get("terim"), "anlam": t.get("anlam")} for t in jargon[:3] if isinstance(t, dict)],
        })
    return {"bolumler": sonuc, "profil_var": bool(ogr_puan)}
