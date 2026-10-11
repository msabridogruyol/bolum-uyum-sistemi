# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı → Mezunlardan (sekme 'mezun'): okulun GERÇEK mezunlarının, açık rızayla paylaşılan anlatıları.
Göç: 0057 (tablo mezun_hikayeleri).

Sahte tanıklık yasağı: hikâyeyi yalnızca o okulun yetkilisi (rol = okul_yetkilisi, kendi okulu) ekler ve düzenler.
Süper admin genel / örnek hikâye EKLEYEMEZ; yalnızca görüntüleyebilir ve (uygunsuz içerik için) kaldırabilir.
Her kayıtta "mezunun açık rızası alındı" onayı ve rıza tarihi zorunludur (DB CHECK + uç doğrulaması).

Okul (modül kapısı okul_modulu("mezun_takibi")):
  GET    /yonetim/okul/{okul_id}/mezun-hikayeleri
  POST   /yonetim/okul/{okul_id}/mezun-hikayeleri
  PUT    /yonetim/okul/{okul_id}/mezun-hikayeleri/{hikaye_id}
  DELETE /yonetim/okul/{okul_id}/mezun-hikayeleri/{hikaye_id}
Öğrenci (/ogrenci/is-hayati/..., modül kapısı is_hayati):
  GET    /mezun/hikayeler?bolum_id=   — kendi okulunun yayındaki hikâyeleri; seçili bölüm → aynı alan → diğerleri
"""
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.paketler import okul_modulu
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter()
yonetim_router = APIRouter(prefix="/yonetim", tags=["İş Hayatı · Mezun hikâyeleri"],
                           dependencies=[Depends(okul_modulu("mezun_takibi"))])

SORULAR = [
    ("ne_yapiyorum", "İşimde gerçekte ne yapıyorum?", "Unvanın değil, bir haftanın gerçek işleri: neye en çok zaman harcıyorsun?"),
    ("bir_gunum", "Bir günüm", "Sabah kaçta başlıyor, gün nasıl akıyor, ne zaman bitiyor?"),
    ("keske", "Keşke lisede bilseydim", "Lisedeki hâline ne söylerdin?"),
    ("zorluklar", "Zorlukları", "Bu işin seni yoran, kimsenin baştan söylemediği tarafları."),
    ("neden", "Bu mesleği neden seviyorum / sevmiyorum", "Dürüst cevap: iki yönü de olabilir."),
    ("tavsiye", "Öğrencilere tavsiyem", "Bu alanı düşünen bir lise öğrencisi şimdi ne yapmalı?"),
]
SORU_KODLARI = [k for k, *_ in SORULAR]
ALANLAR = """id, okul_id, mezun_ad, ad_bicimi, mezuniyet_yili, bolum_id, bolum_ad, universite, su_anki_is, cevaplar, riza_alindi,
             riza_tarihi, riza_kaydeden, riza_kayit_zamani, durum, olusturan, olusturulma, guncelleme"""


def bas_harfler(ad: str) -> str:
    parca = [p for p in (ad or "").replace(".", " ").split() if p]
    return " ".join(p[0].upper() + "." for p in parca) or "Mezun"


def _satir(r, tam: bool = True) -> dict:
    d = dict(r._mapping)
    d["cevaplar"] = d["cevaplar"] if isinstance(d["cevaplar"], dict) else json.loads(d["cevaplar"] or "{}")
    d["gorunen_ad"] = d["mezun_ad"] if d["ad_bicimi"] == "tam" else bas_harfler(d["mezun_ad"])
    for k in ("riza_tarihi", "riza_kayit_zamani", "olusturulma", "guncelleme"):
        d[k] = d[k].isoformat() if d.get(k) else None
    if d.get("bolum_ad") and d["bolum_ad"] == d["bolum_ad"].upper():   # bölüm tablosundaki BÜYÜK HARF adlar okunur hâle
        from app.core.is_hayati_servisi import tr_baslik
        d["bolum_ad"] = tr_baslik(d["bolum_ad"])
    if not tam:   # öğrenciye: yalnızca gösterilecek alanlar (tam ad yalnızca mezun tercih ettiyse)
        return {k: d[k] for k in ("id", "gorunen_ad", "mezuniyet_yili", "bolum_id", "bolum_ad", "universite", "su_anki_is", "cevaplar")}
    return d


def _yetkili_mi(yon: AdminKullanici, okul_id: int):
    """Yalnızca kendi okulunun yetkilisi yazabilir. Süper admin dahil başka hiç kimse hikâye ekleyemez/düzenleyemez."""
    if yon.rol != "okul_yetkilisi" or yon.okul_id != okul_id:
        raise HTTPException(403, "Mezun hikâyelerini yalnızca okulun kendi yetkilileri ekleyebilir ve düzenleyebilir. "
                                 "Bu özellik okulun gerçek mezunları içindir; örnek ya da genel hikâye eklenemez.")


def _hikaye(db: Session, okul_id: int, hikaye_id: int):
    r = db.execute(text(f"SELECT {ALANLAR} FROM mezun_hikayeleri WHERE id = :i AND okul_id = :o"), {"i": hikaye_id, "o": okul_id}).first()
    if r is None:
        raise HTTPException(404, "Hikâye bulunamadı.")
    return r


# ============================================================================= okul
@yonetim_router.get("/okul/{okul_id}/mezun-hikayeleri")
def liste(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.okul_yonetimi import _okul_kapsami
    _okul_kapsami(db, yon, okul_id)
    rows = db.execute(text(f"SELECT {ALANLAR} FROM mezun_hikayeleri WHERE okul_id = :o ORDER BY durum DESC, mezuniyet_yili DESC, id DESC"),
                      {"o": okul_id}).all()
    return {"hikayeler": [_satir(r) for r in rows],
            "sorular": [{"kod": k, "soru": s, "ipucu": i} for k, s, i in SORULAR],
            "yazabilir": yon.rol == "okul_yetkilisi" and yon.okul_id == okul_id,
            "bolumler": [{"id": b.id, "ad": b.ad} for b in db.execute(text("SELECT id, ad FROM bolumler WHERE durum = 'yayinda' ORDER BY ad")).all()]}


class HikayeIstek(BaseModel):
    mezun_ad: str = Field(min_length=2, max_length=120)
    ad_bicimi: str = "bas_harf"
    mezuniyet_yili: int = Field(ge=1950, le=2100)
    bolum_id: int | None = None
    bolum_ad: str | None = Field(default=None, max_length=160)
    universite: str | None = Field(default=None, max_length=160)
    su_anki_is: str | None = Field(default=None, max_length=160)
    cevaplar: dict[str, str] = Field(default_factory=dict)
    riza_alindi: bool
    riza_tarihi: date
    durum: str = "taslak"


def _dogrula(db: Session, istek: HikayeIstek) -> dict:
    if not istek.riza_alindi:
        raise HTTPException(400, "Mezunun bu metnin okul öğrencilerine gösterilmesine açık rıza verdiğini onaylamadan kaydedilemez.")
    if istek.riza_tarihi > date.today():
        raise HTTPException(400, "Rıza tarihi gelecekte olamaz.")
    if istek.ad_bicimi not in ("tam", "bas_harf"):
        raise HTTPException(400, "Geçersiz ad gösterimi.")
    if istek.durum not in ("taslak", "yayinda"):
        raise HTTPException(400, "Geçersiz durum.")
    if istek.mezuniyet_yili > date.today().year:
        raise HTTPException(400, "Mezuniyet yılı gelecekte olamaz.")
    cevaplar = {k: (istek.cevaplar.get(k) or "").strip()[:2500] for k in SORU_KODLARI if (istek.cevaplar.get(k) or "").strip()}
    if istek.durum == "yayinda" and len(cevaplar) < 2:
        raise HTTPException(400, "Yayınlamak için en az iki soruyu cevaplayın.")
    bolum_ad = (istek.bolum_ad or "").strip() or None
    if istek.bolum_id:
        ad = db.execute(text("SELECT ad FROM bolumler WHERE id = :i"), {"i": istek.bolum_id}).scalar()
        if ad is None:
            raise HTTPException(400, "Bölüm bulunamadı.")
        bolum_ad = bolum_ad or ad
    t = lambda v: (v or "").strip() or None  # noqa: E731
    return {"ma": istek.mezun_ad.strip(), "ab": istek.ad_bicimi, "my": istek.mezuniyet_yili, "bi": istek.bolum_id, "ba": bolum_ad,
            "un": t(istek.universite), "is": t(istek.su_anki_is), "ce": json.dumps(cevaplar, ensure_ascii=False),
            "rt": istek.riza_tarihi, "du": istek.durum}


@yonetim_router.post("/okul/{okul_id}/mezun-hikayeleri", status_code=201)
def ekle(okul_id: int, istek: HikayeIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _yetkili_mi(yon, okul_id)
    if db.execute(text("SELECT count(*) FROM mezun_hikayeleri WHERE okul_id = :o"), {"o": okul_id}).scalar() >= 300:
        raise HTTPException(400, "Bir okul için en fazla 300 hikâye eklenebilir.")
    v = _dogrula(db, istek)
    yeni = db.execute(text("""
        INSERT INTO mezun_hikayeleri (okul_id, mezun_ad, ad_bicimi, mezuniyet_yili, bolum_id, bolum_ad, universite, su_anki_is, cevaplar,
                                      riza_alindi, riza_tarihi, riza_kaydeden, durum, olusturan)
        VALUES (:ok, :ma, :ab, :my, :bi, :ba, :un, :is, CAST(:ce AS JSONB), TRUE, :rt, :yk, :du, :yk) RETURNING id
    """), {**v, "ok": okul_id, "yk": yon.ad_soyad}).scalar()
    denetim_yaz(db, yon, "mezun_hikayesi_ekle", "mezun_hikayeleri", yeni,
                f"{bas_harfler(v['ma'])} · {v['du']} · rıza {v['rt'].isoformat()}", okul_id)
    db.commit()
    return _satir(_hikaye(db, okul_id, yeni))


@yonetim_router.put("/okul/{okul_id}/mezun-hikayeleri/{hikaye_id}")
def duzenle(okul_id: int, hikaye_id: int, istek: HikayeIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _yetkili_mi(yon, okul_id)
    eski = _hikaye(db, okul_id, hikaye_id)
    v = _dogrula(db, istek)
    riza_degisti = eski.riza_tarihi != v["rt"]
    db.execute(text(f"""
        UPDATE mezun_hikayeleri SET mezun_ad = :ma, ad_bicimi = :ab, mezuniyet_yili = :my, bolum_id = :bi, bolum_ad = :ba, universite = :un,
               su_anki_is = :is, cevaplar = CAST(:ce AS JSONB), riza_tarihi = :rt, durum = :du, guncelleme = now()
               {", riza_kaydeden = :yk, riza_kayit_zamani = now()" if riza_degisti else ""}
         WHERE id = :i AND okul_id = :ok
    """), {**v, "i": hikaye_id, "ok": okul_id, "yk": yon.ad_soyad})
    islem = "mezun_hikayesi_yayinla" if v["du"] == "yayinda" and eski.durum != "yayinda" else (
        "mezun_hikayesi_yayindan_kaldir" if v["du"] != "yayinda" and eski.durum == "yayinda" else "mezun_hikayesi_duzenle")
    denetim_yaz(db, yon, islem, "mezun_hikayeleri", hikaye_id, f"{bas_harfler(v['ma'])} · {v['du']}", okul_id)
    db.commit()
    return _satir(_hikaye(db, okul_id, hikaye_id))


@yonetim_router.delete("/okul/{okul_id}/mezun-hikayeleri/{hikaye_id}", status_code=204)
def kaldir(okul_id: int, hikaye_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    """Okul yetkilisi kendi okulunun hikâyesini; süper admin yalnızca moderasyon için kaldırabilir."""
    if yon.rol != "super_admin":
        _yetkili_mi(yon, okul_id)
    r = _hikaye(db, okul_id, hikaye_id)
    db.execute(text("DELETE FROM mezun_hikayeleri WHERE id = :i AND okul_id = :o"), {"i": hikaye_id, "o": okul_id})
    denetim_yaz(db, yon, "mezun_hikayesi_kaldir", "mezun_hikayeleri", hikaye_id, bas_harfler(r.mezun_ad), okul_id)
    db.commit()


# ============================================================================= öğrenci
@ogrenci_router.get("/mezun/hikayeler")
def ogrenci_hikayeleri(bolum_id: int | None = Query(None), db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    sorular = [{"kod": k, "soru": s} for k, s, _i in SORULAR]
    if not o.okul_id:
        return {"hikayeler": [], "sorular": sorular, "okul_var": False}
    rows = db.execute(text(f"SELECT {ALANLAR} FROM mezun_hikayeleri WHERE okul_id = :o AND durum = 'yayinda' ORDER BY mezuniyet_yili DESC, id DESC"),
                      {"o": o.okul_id}).all()
    hikayeler = [_satir(r, tam=False) for r in rows]
    dal = {}
    if bolum_id and hikayeler:
        ids = list({bolum_id, *[h["bolum_id"] for h in hikayeler if h["bolum_id"]]})
        try:
            dal = {r.bolum_id: r.dal_id for r in db.execute(text("SELECT bolum_id, dal_id FROM bolum_dal_eslesme WHERE bolum_id = ANY(:i)"), {"i": ids}).all()}
        except Exception:
            db.rollback()
    for h in hikayeler:
        if bolum_id and h["bolum_id"] == bolum_id:
            h["eslesme"] = "bolum"
        elif bolum_id and h["bolum_id"] and dal.get(bolum_id) and dal.get(h["bolum_id"]) == dal.get(bolum_id):
            h["eslesme"] = "alan"
        else:
            h["eslesme"] = None
    sira = {"bolum": 0, "alan": 1, None: 2}
    hikayeler.sort(key=lambda h: sira[h["eslesme"]])   # kararlı sıralama: grup içinde yeni mezun önce
    return {"hikayeler": hikayeler, "sorular": sorular, "okul_var": True}
