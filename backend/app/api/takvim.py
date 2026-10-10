# -*- coding: utf-8 -*-
"""
[2026-10-10] Takvim.
Kaynaklar: genel (süper admin; ör. YKS başvuru/sınav, tercih dönemi) · okul (okul yetkilisi; veli toplantısı, kulüp günü)
· kişisel (öğrencinin kendi hatırlatmaları) · eğitim koçu randevuları (otomatik).

Öğrenci:  GET /ogrenci/takvim · POST /ogrenci/takvim · DELETE /ogrenci/takvim/{id}
Yönetim:  GET /yonetim/takvim?okul_id= · POST /yonetim/takvim · PUT/DELETE /yonetim/takvim/{id}
"""
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.api.okul_yonetimi import SINIFLAR, _okul_kapsami
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici, Ogrenci
from app.api.koclar import gorunen_ad

ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — Takvim"])
router = APIRouter(prefix="/yonetim", tags=["Takvim"])

TURLER = {
    "sinav": {"ad": "Sınav", "ikon": "📝"}, "basvuru": {"ad": "Başvuru", "ikon": "🗂️"},
    "tercih": {"ad": "Tercih dönemi", "ikon": "🎯"}, "ozel_yetenek": {"ad": "Özel yetenek sınavı", "ikon": "🎨"},
    "okul": {"ad": "Okul etkinliği", "ikon": "🏫"}, "toplanti": {"ad": "Toplantı / görüşme", "ikon": "👥"},
    "tanitim": {"ad": "Üniversite tanıtımı / fuar", "ikon": "🎓"}, "kisisel": {"ad": "Kişisel", "ikon": "📌"},
    "diger": {"ad": "Diğer", "ikon": "🗓️"},
}


def _satir(r: dict, kaynak: str, duzenlenebilir: bool = False) -> dict:
    t = TURLER.get(r["tur"], TURLER["diger"])
    return {"id": r["id"], "baslik": r["baslik"], "aciklama": r["aciklama"], "tur": r["tur"], "tur_adi": t["ad"],
            "ikon": t["ikon"], "baslangic": r["baslangic"], "bitis": r["bitis"], "saat": r["saat"], "link": r["link"],
            "hedef_sinif": r["hedef_sinif"], "kaynak": kaynak, "duzenlenebilir": duzenlenebilir}


class EtkinlikIstek(BaseModel):
    baslik: str = Field(min_length=2, max_length=120)
    aciklama: str | None = Field(default=None, max_length=600)
    tur: str = "diger"
    baslangic: date
    bitis: date | None = None
    saat: str | None = Field(default=None, max_length=20)
    hedef_sinif: str | None = None
    link: str | None = Field(default=None, max_length=300)
    okul_id: int | None = None          # yönetim: None = genel (yalnızca süper admin)


def _degerler(istek: EtkinlikIstek, kisisel: bool = False) -> dict:
    if istek.bitis and istek.bitis < istek.baslangic:
        raise HTTPException(status_code=400, detail="Bitiş tarihi başlangıçtan önce olamaz.")
    tur = "kisisel" if kisisel else (istek.tur if istek.tur in TURLER else "diger")
    hedef = istek.hedef_sinif if istek.hedef_sinif in SINIFLAR else None
    link = (istek.link or "").strip() or None
    if link and not link.startswith(("http://", "https://")):
        link = "https://" + link
    t = lambda v: (v or "").strip() or None  # noqa: E731
    return {"ba": istek.baslik.strip(), "ac": t(istek.aciklama), "tu": tur, "bs": istek.baslangic, "bt": istek.bitis,
            "sa": t(istek.saat), "hs": None if kisisel else hedef, "li": None if kisisel else link}


# ============================================================================= öğrenci
@ogrenci_router.get("/takvim")
def ogrenci_takvim(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    bas = date.today() - timedelta(days=45)
    satirlar = db.execute(text("""
        SELECT * FROM takvim_etkinlikleri
         WHERE COALESCE(bitis, baslangic) >= :bas
           AND ((okul_id IS NULL AND ogrenci_id IS NULL) OR (okul_id = :ok AND ogrenci_id IS NULL) OR ogrenci_id = :o)
           AND (hedef_sinif IS NULL OR hedef_sinif = :sf)
         ORDER BY baslangic, id
    """), {"bas": bas, "ok": o.okul_id or -1, "o": o.id, "sf": o.sinif or ""}).mappings().all()
    sonuc = [_satir(dict(r), "kisisel" if r["ogrenci_id"] else ("okul" if r["okul_id"] else "genel"),
                    duzenlenebilir=bool(r["ogrenci_id"])) for r in satirlar]
    try:   # eğitim koçu randevuları (planlandı)
        for r in db.execute(text("""
            SELECT t.id, t.randevu_zamani, k.ad_soyad, k.gorunen_ad FROM koc_gorusme_talepleri t JOIN egitim_koclari k ON k.id = t.koc_id
             WHERE t.ogrenci_id = :o AND t.durum = 'onaylandi' AND t.randevu_zamani IS NOT NULL AND t.randevu_zamani >= :bas
        """), {"o": o.id, "bas": bas}).mappings().all():
            z = r["randevu_zamani"]
            z = z.astimezone(ZoneInfo("Europe/Istanbul")) if z.tzinfo else z
            sonuc.append({"id": f"koc-{r['id']}", "baslik": f"Eğitim koçu görüşmesi: {gorunen_ad(dict(r))}", "aciklama": None,
                          "tur": "toplanti", "tur_adi": "Koç görüşmesi", "ikon": "👩‍🏫", "baslangic": z.date(), "bitis": None,
                          "saat": z.strftime("%H:%M"), "link": "/koclar",
                          "hedef_sinif": None, "kaynak": "koc", "duzenlenebilir": False})
    except Exception:
        db.rollback()
    sonuc.sort(key=lambda x: (x["baslangic"], x["saat"] or ""))
    return {"etkinlikler": sonuc, "turler": [{"kod": k, **v} for k, v in TURLER.items()], "bugun": date.today()}


@ogrenci_router.post("/takvim", status_code=201)
def kisisel_ekle(istek: EtkinlikIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    say = db.execute(text("SELECT COUNT(*) FROM takvim_etkinlikleri WHERE ogrenci_id = :o"), {"o": o.id}).scalar()
    if say >= 200:
        raise HTTPException(status_code=400, detail="Takvimine en fazla 200 kişisel not ekleyebilirsin.")
    d = _degerler(istek, kisisel=True)
    eid = db.execute(text("""
        INSERT INTO takvim_etkinlikleri (ogrenci_id, baslik, aciklama, tur, baslangic, bitis, saat, olusturan)
        VALUES (:o, :ba, :ac, :tu, :bs, :bt, :sa, 'Öğrenci') RETURNING id
    """), {**d, "o": o.id}).scalar()
    db.commit()
    return {"id": eid}


@ogrenci_router.delete("/takvim/{etkinlik_id}", status_code=204)
def kisisel_sil(etkinlik_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    n = db.execute(text("DELETE FROM takvim_etkinlikleri WHERE id = :i AND ogrenci_id = :o"), {"i": etkinlik_id, "o": o.id}).rowcount
    db.commit()
    if not n:
        raise HTTPException(status_code=404, detail="Bulunamadı.")


# ============================================================================= yönetim
@router.get("/takvim")
def yonetim_takvim(okul_id: int | None = None, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    if yon.rol == "okul_yetkilisi":
        okul_id = yon.okul_id
    elif okul_id:
        _okul_kapsami(db, yon, okul_id)
    bas = date.today() - timedelta(days=120)
    satirlar = db.execute(text("""
        SELECT * FROM takvim_etkinlikleri WHERE ogrenci_id IS NULL AND COALESCE(bitis, baslangic) >= :bas
           AND (okul_id IS NULL""" + (" OR okul_id = :ok" if okul_id else "") + ") ORDER BY baslangic, id"),
        {"bas": bas, "ok": okul_id}).mappings().all()
    sonuc = []
    for r in satirlar:
        genel = r["okul_id"] is None
        sonuc.append(_satir(dict(r), "genel" if genel else "okul", duzenlenebilir=yon.rol == "super_admin" or not genel))
    return {"etkinlikler": sonuc, "turler": [{"kod": k, **v} for k, v in TURLER.items() if k != "kisisel"],
            "siniflar": [s for s in SINIFLAR if s != "Mezun"], "super": yon.rol == "super_admin"}


def _yonetim_okul(db: Session, yon: AdminKullanici, istenen: int | None) -> int | None:
    if yon.rol == "okul_yetkilisi":
        return yon.okul_id
    if istenen:
        _okul_kapsami(db, yon, istenen)
    return istenen or None


def _etkinlik(db: Session, yon: AdminKullanici, eid: int) -> dict:
    r = db.execute(text("SELECT * FROM takvim_etkinlikleri WHERE id = :i AND ogrenci_id IS NULL"), {"i": eid}).mappings().first()
    if not r:
        raise HTTPException(status_code=404, detail="Etkinlik bulunamadı.")
    if yon.rol == "okul_yetkilisi" and r["okul_id"] != yon.okul_id:
        raise HTTPException(status_code=403, detail="Genel takvimi yalnızca süper admin düzenler.")
    return dict(r)


@router.post("/takvim", status_code=201)
def yonetim_ekle(istek: EtkinlikIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    d = _degerler(istek)
    ok = _yonetim_okul(db, yon, istek.okul_id)
    eid = db.execute(text("""
        INSERT INTO takvim_etkinlikleri (okul_id, baslik, aciklama, tur, baslangic, bitis, saat, hedef_sinif, link, olusturan)
        VALUES (:ok, :ba, :ac, :tu, :bs, :bt, :sa, :hs, :li, :ol) RETURNING id
    """), {**d, "ok": ok, "ol": yon.ad_soyad}).scalar()
    denetim_yaz(db, yon, "takvim_ekle", "takvim_etkinlikleri", eid, f"{d['ba']} ({d['bs']})", ok)
    db.commit()
    return {"id": eid}


@router.put("/takvim/{etkinlik_id}")
def yonetim_duzenle(etkinlik_id: int, istek: EtkinlikIstek, db: Session = Depends(get_db),
                    yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = _etkinlik(db, yon, etkinlik_id)
    d = _degerler(istek)
    db.execute(text("""
        UPDATE takvim_etkinlikleri SET baslik = :ba, aciklama = :ac, tur = :tu, baslangic = :bs, bitis = :bt, saat = :sa,
               hedef_sinif = :hs, link = :li WHERE id = :i
    """), {**d, "i": etkinlik_id})
    denetim_yaz(db, yon, "takvim_duzenle", "takvim_etkinlikleri", etkinlik_id, d["ba"], r["okul_id"])
    db.commit()
    return {"tamam": True}


@router.delete("/takvim/{etkinlik_id}", status_code=204)
def yonetim_sil(etkinlik_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = _etkinlik(db, yon, etkinlik_id)
    db.execute(text("DELETE FROM takvim_etkinlikleri WHERE id = :i"), {"i": etkinlik_id})
    denetim_yaz(db, yon, "takvim_sil", "takvim_etkinlikleri", etkinlik_id, r["baslik"], r["okul_id"])
    db.commit()
