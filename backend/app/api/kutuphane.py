# -*- coding: utf-8 -*-
"""
[2026-10-10] Öğrenci kütüphanesi / kişisel gelişim günlüğü: okuduğu kitaplar, izlediği film-dizi-belgeseller,
aldığı kurs-sertifikalar, katıldığı etkinlik-proje-yarışmalar. Öğrenci girer; okul yetkilisi okur.

Öğrenci:  GET/POST /ogrenci/kutuphane · PUT/DELETE /ogrenci/kutuphane/{id}
Yönetim:  GET /yonetim/ogrenci/{id}/kutuphane
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.api.okul_yonetimi import _ogrenci_kapsami
from app.core.database import get_db
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — Kütüphanem"])
router = APIRouter(prefix="/yonetim", tags=["Öğrenci kütüphanesi"])

KATEGORILER = {
    "kitap": {"ad": "Kitaplar", "tekil": "Kitap", "ikon": "📖", "kisi": "Yazar",
              "alt": ["Roman", "Bilim / popüler bilim", "Biyografi", "Kişisel gelişim", "Tarih", "Felsefe", "Şiir", "Çizgi roman", "Diğer"],
              "durum": {"istek": "Okumak istiyorum", "devam": "Okuyorum", "bitti": "Okudum"}},
    "izleme": {"ad": "Film, dizi ve belgeseller", "tekil": "Film / dizi", "ikon": "🎬", "kisi": "Yönetmen / kanal",
               "alt": ["Film", "Dizi", "Belgesel", "Video / YouTube", "Podcast"],
               "durum": {"istek": "İzlemek istiyorum", "devam": "İzliyorum", "bitti": "İzledim"}},
    "kurs": {"ad": "Kurs ve sertifikalar", "tekil": "Kurs", "ikon": "🎓", "kisi": "Kurum / platform",
             "alt": ["Online kurs", "Yüz yüze kurs", "Sertifika", "Dil kursu", "Yaz okulu"],
             "durum": {"istek": "Planlıyorum", "devam": "Devam ediyorum", "bitti": "Tamamladım"}},
    "etkinlik": {"ad": "Etkinlik, proje ve yarışmalar", "tekil": "Etkinlik", "ikon": "🏅", "kisi": "Kurum / takım",
                 "alt": ["Yarışma / olimpiyat", "Proje", "Gönüllülük", "Gezi / ziyaret", "Konferans / seminer", "Spor / sanat etkinliği", "Staj / iş gölgeleme"],
                 "durum": {"istek": "Planlıyorum", "devam": "Devam ediyor", "bitti": "Tamamlandı"}},
}
SINIR = 500


def _out(r: dict) -> dict:
    k = KATEGORILER.get(r["kategori"], KATEGORILER["kitap"])
    return {**dict(r), "durum_adi": k["durum"].get(r["durum"], r["durum"]), "ikon": k["ikon"]}


def _liste(db: Session, ogrenci_id) -> dict:
    satirlar = db.execute(text("""
        SELECT id, kategori, alt_tur, baslik, kisi, durum, puan, notlar, tarih, sayfa, olusturulma_zamani
          FROM ogrenci_kutuphane WHERE ogrenci_id = :o
         ORDER BY CASE durum WHEN 'devam' THEN 0 WHEN 'bitti' THEN 1 ELSE 2 END, COALESCE(tarih, olusturulma_zamani::date) DESC, id DESC
    """), {"o": ogrenci_id}).mappings().all()
    kayitlar = [_out(dict(r)) for r in satirlar]
    istatistik = {k: {"toplam": 0, "bitti": 0} for k in KATEGORILER}
    for x in kayitlar:
        if x["kategori"] in istatistik:
            istatistik[x["kategori"]]["toplam"] += 1
            istatistik[x["kategori"]]["bitti"] += x["durum"] == "bitti"
    return {"kayitlar": kayitlar, "istatistik": istatistik,
            "kategoriler": [{"kod": k, **{a: b for a, b in v.items()}} for k, v in KATEGORILER.items()]}


class KayitIstek(BaseModel):
    kategori: str
    alt_tur: str | None = Field(default=None, max_length=40)
    baslik: str = Field(min_length=1, max_length=160)
    kisi: str | None = Field(default=None, max_length=120)
    durum: str = "bitti"
    puan: int | None = Field(default=None, ge=1, le=5)
    notlar: str | None = Field(default=None, max_length=1500)
    tarih: date | None = None
    sayfa: int | None = Field(default=None, ge=1, le=5000)   # [2026-10-10] kitaplar için


def _degerler(istek: KayitIstek) -> dict:
    if istek.kategori not in KATEGORILER:
        raise HTTPException(status_code=400, detail="Geçersiz tür.")
    if istek.durum not in ("istek", "devam", "bitti"):
        raise HTTPException(status_code=400, detail="Geçersiz durum.")
    if istek.tarih and istek.tarih > date.today():
        raise HTTPException(status_code=400, detail="Tarih ileri bir gün olamaz.")
    t = lambda v: (v or "").strip() or None  # noqa: E731
    return {"ka": istek.kategori, "al": t(istek.alt_tur), "ba": istek.baslik.strip(), "ki": t(istek.kisi), "du": istek.durum,
            "pu": istek.puan if istek.durum != "istek" else None, "no": t(istek.notlar), "ta": istek.tarih,
            "sa": istek.sayfa if istek.kategori == "kitap" else None}


@ogrenci_router.get("/kutuphane")
def kutuphanem(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return _liste(db, o.id)


@ogrenci_router.post("/kutuphane", status_code=201)
def kayit_ekle(istek: KayitIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if db.execute(text("SELECT COUNT(*) FROM ogrenci_kutuphane WHERE ogrenci_id = :o"), {"o": o.id}).scalar() >= SINIR:
        raise HTTPException(status_code=400, detail=f"En fazla {SINIR} kayıt eklenebilir.")
    kid = db.execute(text("""
        INSERT INTO ogrenci_kutuphane (ogrenci_id, kategori, alt_tur, baslik, kisi, durum, puan, notlar, tarih, sayfa)
        VALUES (:o, :ka, :al, :ba, :ki, :du, :pu, :no, :ta, :sa) RETURNING id
    """), {**_degerler(istek), "o": o.id}).scalar()
    db.commit()
    return {"id": kid}


@ogrenci_router.put("/kutuphane/{kayit_id}")
def kayit_duzenle(kayit_id: int, istek: KayitIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    n = db.execute(text("""
        UPDATE ogrenci_kutuphane SET kategori = :ka, alt_tur = :al, baslik = :ba, kisi = :ki, durum = :du, puan = :pu,
               notlar = :no, tarih = :ta, sayfa = :sa, guncelleme_zamani = :z WHERE id = :i AND ogrenci_id = :o
    """), {**_degerler(istek), "i": kayit_id, "o": o.id, "z": datetime.now(timezone.utc)}).rowcount
    db.commit()
    if not n:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")
    return {"tamam": True}


@ogrenci_router.delete("/kutuphane/{kayit_id}", status_code=204)
def kayit_sil(kayit_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    n = db.execute(text("DELETE FROM ogrenci_kutuphane WHERE id = :i AND ogrenci_id = :o"), {"i": kayit_id, "o": o.id}).rowcount
    db.commit()
    if not n:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı.")


@router.get("/ogrenci/{ogrenci_id}/kutuphane")
def ogrenci_kutuphanesi(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    return _liste(db, o.id)
