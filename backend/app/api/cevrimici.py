# -*- coding: utf-8 -*-
"""
[2026-10-11] Çevrim içi öğrenciler — sağ altta "şu an kimler burada" listesi (etkileşim yok: mesaj, profil, puan yok).

POST /ogrenci/cevrimici              — öğrenci: "buradayım" sinyali (sayfa açıkken dakikada bir) + okulundaki çevrim içi liste
PUT  /ogrenci/cevrimici/gizlilik     — öğrenci: listede görünmeyi kapat / aç
GET  /yonetim/cevrimici?okul_id=     — okul yetkilisi: kendi okulu; süper admin: seçilen okul ya da tüm okullar

Gizlilik:
  * Öğrenci yalnızca KENDİ OKULUNDAKİ çevrim içi öğrencileri görür; yalnızca ad + soyadın baş harfi ve sınıf-şube.
    Puan, sonuç, okul dışı bilgi yok. Okul harici (okulsuz) öğrenci liste görmez.
  * "Gizli" seçen öğrenci kimsenin listesinde görünmez (yönetim yine sayıyı görür, adını görmez).
  * Yönetim tam adı görür (zaten öğrenci listesine erişimi var).
Çevrim içi = son CEVRIMICI_SN saniyede sinyal göndermiş. Sinyal en fazla YAZMA_SN'de bir veritabanına yazılır.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.aktiflik import gune_isle
from app.core.database import get_db
from app.models import AdminKullanici, Ogrenci

CEVRIMICI_SN = 120
YAZMA_SN = 45
LISTE_EN_FAZLA = 60

ogrenci_router = APIRouter(prefix="/ogrenci/cevrimici", tags=["Çevrim içi"])
yonetim_router = APIRouter(prefix="/yonetim/cevrimici", tags=["Çevrim içi"])


def _simdi() -> datetime:
    return datetime.now(timezone.utc)


def _sinif_metni(sinif: str | None, sube: str | None) -> str:
    if not sinif:
        return ""
    return f"{sinif.replace('. Sınıf', '')}-{sube}" if sube and sinif != "Mezun" else sinif


def _kisa_ad(ad_soyad: str) -> str:
    """'Ayşe Nur Yılmaz' → 'Ayşe Nur Y.' — öğrenciler birbirinin tam soyadını görmez."""
    p = (ad_soyad or "").split()
    if len(p) < 2:
        return ad_soyad or ""
    return " ".join(p[:-1]) + f" {p[-1][0]}."


def _cevrimici(db: Session, okul_id: int, haric_id=None, gizlileri_de: bool = False):
    esik = _simdi() - timedelta(seconds=CEVRIMICI_SN)
    return db.execute(text(
        "SELECT id, ad_soyad, sinif, sube, cevrimici_gizli FROM ogrenciler "
        "WHERE okul_id = :o AND son_gorulme >= :e AND (CAST(:h AS uuid) IS NULL OR id <> CAST(:h AS uuid)) "
        + ("" if gizlileri_de else "AND NOT cevrimici_gizli ")
        + "ORDER BY NULLIF(regexp_replace(coalesce(sinif, ''), '\\D', '', 'g'), '')::int NULLS LAST, sinif, sube NULLS LAST, ad_soyad"),
        {"o": okul_id, "e": esik, "h": str(haric_id) if haric_id else None}).all()


@ogrenci_router.post("")
def buradayim(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    simdi = _simdi()
    if o.son_gorulme is None or (simdi - o.son_gorulme).total_seconds() >= YAZMA_SN:
        db.execute(text("UPDATE ogrenciler SET son_gorulme = :s WHERE id = :i"), {"s": simdi, "i": o.id})
        gune_isle(db, o.id)   # [2026-10-11] günün ilk açılışı işaretlenir (beni hatırla ile açık kalan oturumlar da sayılır)
        db.commit()
    if not o.okul_id:
        return {"gizli": bool(o.cevrimici_gizli), "toplam": 0, "sinifim": [], "digerleri": [], "kesildi": False}
    satir = _cevrimici(db, o.okul_id, haric_id=o.id)
    sinifim = [s for s in satir if o.sinif and s.sinif == o.sinif and (s.sube or "") == (o.sube or "")]
    digerleri = [s for s in satir if s not in sinifim]
    kalan = max(0, LISTE_EN_FAZLA - len(sinifim))
    f = lambda s: {"ad": _kisa_ad(s.ad_soyad), "sinif": _sinif_metni(s.sinif, s.sube)}
    return {"gizli": bool(o.cevrimici_gizli), "toplam": len(satir),
            "sinifim": [f(s) for s in sinifim[:LISTE_EN_FAZLA]], "digerleri": [f(s) for s in digerleri[:kalan]],
            "kesildi": len(sinifim) + len(digerleri) > LISTE_EN_FAZLA}


class GizlilikIstek(BaseModel):
    gizli: bool


@ogrenci_router.put("/gizlilik")
def gizlilik(istek: GizlilikIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    o.cevrimici_gizli = bool(istek.gizli)
    db.commit()
    return {"gizli": o.cevrimici_gizli}


@yonetim_router.get("")
def yonetim_cevrimici(okul_id: int | None = Query(None), db: Session = Depends(get_db),
                      yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    if yon.rol == "okul_yetkilisi":
        if okul_id is not None and okul_id != yon.okul_id:
            raise HTTPException(status_code=403, detail="Yalnızca kendi okulunuzun bilgilerine erişebilirsiniz.")
        okul_id = yon.okul_id
    if okul_id is None:   # süper admin, tüm okullar: okul başına sayı
        esik = _simdi() - timedelta(seconds=CEVRIMICI_SN)
        okullar = db.execute(text(
            "SELECT k.id, k.ad, count(o.id) AS sayi FROM okullar k JOIN ogrenciler o ON o.okul_id = k.id AND o.son_gorulme >= :e "
            "GROUP BY k.id, k.ad ORDER BY sayi DESC, k.ad"), {"e": esik}).mappings().all()
        return {"toplam": sum(x["sayi"] for x in okullar), "okullar": [dict(x) for x in okullar], "ogrenciler": [], "gizli_sayisi": 0}
    satir = _cevrimici(db, okul_id, gizlileri_de=True)
    acik = [s for s in satir if not s.cevrimici_gizli]
    return {"toplam": len(satir), "gizli_sayisi": len(satir) - len(acik), "okullar": [],
            "ogrenciler": [{"id": str(s.id), "ad": s.ad_soyad, "sinif": _sinif_metni(s.sinif, s.sube)} for s in acik[:200]],
            "kesildi": len(acik) > 200}
