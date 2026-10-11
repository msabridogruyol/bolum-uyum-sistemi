# -*- coding: utf-8 -*-
"""
[2026-10-10] Çalışma programı ve soru takibi (modül: calisma).

Öğrenci:
  GET    /ogrenci/calisma                 — dersler, haftalık program, son 60 günün kayıtları, özet (bu hafta, 6 hafta, ders bazında)
  PUT    /ogrenci/calisma/program         — haftalık programı baştan yazar (en çok 80 blok)
  POST   /ogrenci/calisma/kayit           — {tarih, ders, sure_dk, soru, dogru?, yanlis?, konu?}
  DELETE /ogrenci/calisma/kayit/{kayit_id}
Yönetim (okul yetkilisi / süper admin):
  GET    /yonetim/ogrenci/{ogrenci_id}/calisma — özet (öğrenci detayı)
"""
import re
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.database import get_db
from app.core.sinav_yapisi import KONU_DERSLERI
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter(prefix="/ogrenci/calisma", tags=["Çalışma"])
yonetim_router = APIRouter(prefix="/yonetim", tags=["Çalışma"])

DERSLER = {k: f"{v[0]} {v[1]}" for k, v in KONU_DERSLERI.items()}
DERSLER.update({"ydt_dil": "YDT Yabancı Dil", "okul": "Okul dersleri", "kitap": "Kitap okuma", "diger": "Diğer"})
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def _pazartesi(g: date) -> date:
    return g - timedelta(days=g.weekday())


def ozet_hesapla(db: Session, ogrenci_id) -> dict:
    bugun = date.today()
    pzt = _pazartesi(bugun)
    plan_dk = db.execute(text("SELECT coalesce(sum(sure_dk), 0) FROM calisma_programi WHERE ogrenci_id = :o"), {"o": ogrenci_id}).scalar() or 0
    kayit = db.execute(text("""
        SELECT tarih, ders, sure_dk, soru, dogru, yanlis FROM calisma_kayitlari
         WHERE ogrenci_id = :o AND tarih >= :bas ORDER BY tarih
    """), {"o": ogrenci_id, "bas": pzt - timedelta(weeks=5)}).all()
    hafta = defaultdict(lambda: {"dk": 0, "soru": 0})
    for r in kayit:
        h = _pazartesi(r.tarih)
        hafta[h]["dk"] += r.sure_dk
        hafta[h]["soru"] += r.soru
    haftalar = [{"hafta": (pzt - timedelta(weeks=i)).isoformat(), **hafta[pzt - timedelta(weeks=i)]} for i in range(5, -1, -1)]
    bu = [r for r in kayit if r.tarih >= pzt]
    ders = defaultdict(lambda: {"dk": 0, "soru": 0, "dogru": 0, "yanlis": 0, "isaretli": 0})
    for r in kayit:
        if r.tarih < bugun - timedelta(days=27):
            continue
        x = ders[r.ders]
        x["dk"] += r.sure_dk
        x["soru"] += r.soru
        if r.dogru is not None or r.yanlis is not None:
            x["dogru"] += r.dogru or 0
            x["yanlis"] += r.yanlis or 0
            x["isaretli"] += (r.dogru or 0) + (r.yanlis or 0)
    dersler = sorted([{"ders": k, "ad": DERSLER.get(k, k), **v,
                       "isabet": round(100 * v["dogru"] / v["isaretli"]) if v["isaretli"] >= 10 else None} for k, v in ders.items()],
                     key=lambda d: (-d["soru"], -d["dk"]))
    # seri: bugün ya da dün biten, art arda kayıt girilen günler
    gunler = {r[0] for r in db.execute(text("SELECT DISTINCT tarih FROM calisma_kayitlari WHERE ogrenci_id = :o AND tarih >= :b"),
                                       {"o": ogrenci_id, "b": bugun - timedelta(days=120)}).all()}
    seri, g = 0, bugun if bugun in gunler else bugun - timedelta(days=1)
    while g in gunler:
        seri += 1
        g -= timedelta(days=1)
    return {
        "bu_hafta": {"plan_dk": plan_dk, "dk": sum(r.sure_dk for r in bu), "soru": sum(r.soru for r in bu),
                     "gun": len({r.tarih for r in bu}), "uyum": round(100 * sum(r.sure_dk for r in bu) / plan_dk) if plan_dk else None},
        "haftalar": haftalar, "dersler": dersler, "seri": seri,
        "son_28_gun": {"dk": sum(d["dk"] for d in dersler), "soru": sum(d["soru"] for d in dersler)},
    }


def _program(db: Session, ogrenci_id) -> list[dict]:
    return [dict(r._mapping) for r in db.execute(text(
        "SELECT id, gun, baslangic, sure_dk, ders, notlar FROM calisma_programi WHERE ogrenci_id = :o ORDER BY gun, baslangic"),
        {"o": ogrenci_id}).all()]


@ogrenci_router.get("")
def calisma(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.core.konu_servisi import etkin_konular
    kayitlar = db.execute(text("""
        SELECT id, tarih, ders, sure_dk, soru, dogru, yanlis, konu FROM calisma_kayitlari
         WHERE ogrenci_id = :o AND tarih >= :b ORDER BY tarih DESC, id DESC
    """), {"o": o.id, "b": date.today() - timedelta(days=60)}).all()
    try:
        konular = etkin_konular(db, o.okul_id)
    except Exception:
        db.rollback()
        konular = {k: v[2] for k, v in KONU_DERSLERI.items()}
    return {
        "dersler": [{"kod": k, "ad": a} for k, a in DERSLER.items()], "gunler": GUNLER, "konular": konular,
        "program": _program(db, o.id),
        "kayitlar": [{**dict(r._mapping), "tarih": r.tarih.isoformat(), "ders_ad": DERSLER.get(r.ders, r.ders)} for r in kayitlar],
        "ozet": ozet_hesapla(db, o.id), "bugun": date.today().isoformat(),
    }


class ProgramBlok(BaseModel):
    gun: int = Field(ge=0, le=6)
    baslangic: str
    sure_dk: int = Field(ge=10, le=300)
    ders: str
    notlar: str | None = Field(default=None, max_length=80)


@ogrenci_router.put("/program")
def program_kaydet(bloklar: list[ProgramBlok], db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if len(bloklar) > 80:
        raise HTTPException(400, "Haftalık programda en fazla 80 blok olabilir.")
    for b in bloklar:
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", b.baslangic):
            raise HTTPException(400, "Saat SS:DD biçiminde olmalı.")
        if b.ders not in DERSLER:
            raise HTTPException(400, "Geçersiz ders.")
    db.execute(text("DELETE FROM calisma_programi WHERE ogrenci_id = :o"), {"o": o.id})
    for b in bloklar:
        db.execute(text("INSERT INTO calisma_programi (ogrenci_id, gun, baslangic, sure_dk, ders, notlar) VALUES (:o, :g, :b, :s, :d, :n)"),
                   {"o": o.id, "g": b.gun, "b": b.baslangic, "s": b.sure_dk, "d": b.ders, "n": (b.notlar or "").strip() or None})
    db.commit()
    return {"program": _program(db, o.id), "ozet": ozet_hesapla(db, o.id)}


class KayitIstek(BaseModel):
    tarih: date
    ders: str
    sure_dk: int = Field(default=0, ge=0, le=720)
    soru: int = Field(default=0, ge=0, le=1000)
    dogru: int | None = Field(default=None, ge=0, le=1000)
    yanlis: int | None = Field(default=None, ge=0, le=1000)
    konu: str | None = Field(default=None, max_length=120)


@ogrenci_router.post("/kayit", status_code=201)
def kayit_ekle(istek: KayitIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if istek.ders not in DERSLER:
        raise HTTPException(400, "Geçersiz ders.")
    if istek.tarih > date.today() or istek.tarih < date.today() - timedelta(days=14):
        raise HTTPException(400, "Kayıt en çok 14 gün geriye girilebilir.")
    if not istek.sure_dk and not istek.soru:
        raise HTTPException(400, "Süre ya da soru sayısından en az birini gir.")
    if (istek.dogru or 0) + (istek.yanlis or 0) > istek.soru:
        raise HTTPException(400, "Doğru + yanlış, çözülen soru sayısını geçemez.")
    if db.execute(text("SELECT count(*) FROM calisma_kayitlari WHERE ogrenci_id = :o AND tarih = :t"), {"o": o.id, "t": istek.tarih}).scalar() >= 30:
        raise HTTPException(400, "Bir gün için en fazla 30 kayıt girilebilir.")
    db.execute(text("""
        INSERT INTO calisma_kayitlari (ogrenci_id, tarih, ders, sure_dk, soru, dogru, yanlis, konu)
        VALUES (:o, :t, :d, :s, :q, :dg, :y, :k)
    """), {"o": o.id, "t": istek.tarih, "d": istek.ders, "s": istek.sure_dk, "q": istek.soru, "dg": istek.dogru, "y": istek.yanlis,
           "k": (istek.konu or "").strip() or None})
    db.commit()
    return calisma(db, o)


@ogrenci_router.delete("/kayit/{kayit_id}")
def kayit_sil(kayit_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if not db.execute(text("DELETE FROM calisma_kayitlari WHERE id = :i AND ogrenci_id = :o"), {"i": kayit_id, "o": o.id}).rowcount:
        raise HTTPException(404, "Kayıt bulunamadı.")
    db.commit()
    return calisma(db, o)


@yonetim_router.get("/ogrenci/{ogrenci_id}/calisma")
def ogrenci_calisma_ozeti(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.okul_yonetimi import _ogrenci_kapsami
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    son = db.execute(text("SELECT max(tarih) FROM calisma_kayitlari WHERE ogrenci_id = :o"), {"o": o.id}).scalar()
    return {"ozet": ozet_hesapla(db, o.id), "program_blok": len(_program(db, o.id)), "son_kayit": son.isoformat() if son else None}
