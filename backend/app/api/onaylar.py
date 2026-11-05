"""
[2026-11-05] Onay formları — KVKK onayı ve veli onay formu tamamlanma durumu (okul yetkilisi + süper admin).

GET  /yonetim/okul/{okul_id}/onaylar                 özet, sınıf kırılımı, öğrenci listesi (okul_id = 0: okul harici, süper admin)
POST /yonetim/okul/{okul_id}/onaylar/veli            {ogrenci_idler, islem: alindi | resit, form_tarihi?, veli_ad_soyad?, kamera}
POST /yonetim/ogrenci/{ogrenci_id}/veli-onayi/geri-al  {aciklama}
GET  /yonetim/ogrenci/{ogrenci_id}/veli-onayi        kayıt geçmişi
GET  /yonetim/okul/{okul_id}/onaylar/form?idler=…|sinif=…   öğrenci adlarıyla doldurulmuş veli onay formları (PDF)
GET  /yonetim/onaylar/okullar                        (süper admin) okul okul tamamlanma özeti + okul harici satırı
Öğrenci:
GET  /ogrenci/veli-onayi                             kendi durumu
GET  /ogrenci/veli-onayi/form                        kendi adıyla doldurulmuş form (PDF) — veliye götürmek için
Ayrıntı ve kurallar: app/core/veli_onayi.py
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.api.okul_yonetimi import _ogrenci_kapsami, _okul_kapsami, _super
from app.core import veli_onayi as vo
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.katman_servisi import IsKuraliHatasi
from app.models import AdminKullanici, Ogrenci
from app.schemas.girdi import GirdiModeli

router = APIRouter(tags=["Onay formları"])


class VeliIsaretIstek(GirdiModeli):
    ogrenci_idler: list[uuid.UUID] = Field(min_length=1, max_length=2000)
    islem: str = Field(pattern="^(alindi|resit)$")
    form_tarihi: date | None = None
    veli_ad_soyad: str | None = Field(default=None, max_length=120)
    kamera: bool = False


class GeriAlIstek(GirdiModeli):
    aciklama: str | None = Field(default=None, max_length=300)


def _ogrenciler(db: Session, okul_id: int) -> list:
    kosul = "o.okul_id IS NULL" if okul_id == 0 else "o.okul_id = :okul"
    return db.execute(text(f"""SELECT o.id, o.ad_soyad, o.sinif, o.sube, o.ogrenci_no, o.test_hesabi
                                 FROM ogrenciler o WHERE {kosul} ORDER BY o.sinif NULLS LAST, o.sube NULLS LAST, o.ad_soyad"""),
                      {"okul": okul_id}).all()


def _ozet(satirlar: list[dict]) -> dict:
    gercek = [s for s in satirlar if not s["test_hesabi"]]
    n = len(gercek)
    kvkk = sum(1 for s in gercek if s["kvkk"])
    veli = sum(1 for s in gercek if s["veli"]["islem"] == "alindi")
    resit = sum(1 for s in gercek if s["veli"]["islem"] == "resit")
    tamam = sum(1 for s in gercek if s["kvkk"] and s["veli"]["tamam"])
    return {"ogrenci": n, "kvkk": kvkk, "veli_alindi": veli, "resit": resit, "veli_bekleyen": n - veli - resit,
            "tamam": tamam, "yuzde": round(100 * tamam / n) if n else 0}


def okul_onaylari(db: Session, okul_id: int) -> dict:
    rows = _ogrenciler(db, okul_id)
    ids = [r.id for r in rows]
    veli = vo.toplu_durum(db, ids)
    kvkk = vo.kvkk_guncel_idler(db, ids)
    satirlar = [{"id": str(r.id), "ad_soyad": r.ad_soyad, "sinif": r.sinif, "sube": r.sube, "test_hesabi": bool(r.test_hesabi),
                 "kvkk": kvkk.get(r.id) is not None, "kvkk_zaman": kvkk[r.id].isoformat() if kvkk.get(r.id) else None,
                 "veli": veli.get(r.id) or {"tamam": False, "islem": None}} for r in rows]
    siniflar: dict = {}
    for s in satirlar:
        siniflar.setdefault(s["sinif"] or "Sınıfı yok", []).append(s)
    return {"ozet": _ozet(satirlar),
            "siniflar": [{"sinif": k, **_ozet(v)} for k, v in siniflar.items()],
            "ogrenciler": satirlar}


@router.get("/yonetim/okul/{okul_id}/onaylar")
def onaylar(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    return okul_onaylari(db, okul_id)


@router.post("/yonetim/okul/{okul_id}/onaylar/veli")
def veli_isaretle(okul_id: int, istek: VeliIsaretIstek, db: Session = Depends(get_db),
                  yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    idler = list(dict.fromkeys(istek.ogrenci_idler))
    for oid in idler:   # her öğrenci bu okulda (ya da okul harici) olmalı
        o = _ogrenci_kapsami(db, yon, oid)
        if (o.okul_id or 0) != okul_id:
            raise HTTPException(status_code=400, detail="Seçilen öğrencilerden biri bu okulda değil.")
    try:
        n = vo.isaretle(db, yon, idler, istek.islem, istek.form_tarihi, istek.veli_ad_soyad, istek.kamera)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    denetim_yaz(db, yon, "veli_onayi_alindi" if istek.islem == "alindi" else "veli_onayi_resit", "veli_onaylari", f"{n} öğrenci",
                gerekce=(f"form tarihi {istek.form_tarihi.isoformat()}" if istek.form_tarihi else None), okul_id=okul_id or None)
    db.commit()
    return okul_onaylari(db, okul_id)


@router.post("/yonetim/ogrenci/{ogrenci_id}/veli-onayi/geri-al")
def veli_geri_al(ogrenci_id: str, istek: GeriAlIstek, db: Session = Depends(get_db),
                 yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    if o.okul_id is None:
        _super(yon)
    try:
        vo.geri_al(db, yon, o.id, istek.aciklama)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    denetim_yaz(db, yon, "veli_onayi_geri_al", "ogrenciler", o.id, gerekce=istek.aciklama, okul_id=o.okul_id)
    db.commit()
    return {"durum": vo.durum(db, o.id), "gecmis": vo.gecmis(db, o.id)}


@router.get("/yonetim/ogrenci/{ogrenci_id}/veli-onayi")
def veli_gecmis(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    if o.okul_id is None:
        _super(yon)
    return {"durum": vo.durum(db, o.id), "gecmis": vo.gecmis(db, o.id)}


def _pdf(icerik: bytes, ad: str) -> Response:
    return Response(content=icerik, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{ad}.pdf"', "Cache-Control": "no-store"})


@router.get("/yonetim/okul/{okul_id}/onaylar/form")
def veli_formlari(okul_id: int, idler: str | None = Query(None), sinif: str | None = Query(None),
                  bekleyenler: bool = Query(False), db: Session = Depends(get_db),
                  yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    """idler (virgülle) ya da sinif ile süzülür; bekleyenler=true yalnızca veli onayı tamamlanmamışları alır."""
    from app.core.rapor.veli_formu import veli_formu_pdf
    from app.core.rapor.veri import okul_bilgisi
    _okul_kapsami(db, yon, okul_id)
    rows = [r for r in _ogrenciler(db, okul_id) if not r.test_hesabi]
    if idler:
        secili = {x.strip() for x in idler.split(",") if x.strip()}
        rows = [r for r in rows if str(r.id) in secili]
    if sinif:
        rows = [r for r in rows if (r.sinif or "Sınıfı yok") == sinif]
    if bekleyenler:
        d = vo.toplu_durum(db, [r.id for r in rows])
        rows = [r for r in rows if not d.get(r.id, {}).get("tamam")]
    if not rows:
        raise HTTPException(status_code=404, detail="Form üretilecek öğrenci yok.")
    if len(rows) > 400:
        raise HTTPException(status_code=400, detail="Tek seferde en fazla 400 öğrencinin formu üretilir; sınıf seçerek indirin.")
    okul = okul_bilgisi(db, okul_id or None)
    pdf = veli_formu_pdf([{"ad_soyad": r.ad_soyad, "sinif": r.sinif, "sube": r.sube, "ogrenci_no": r.ogrenci_no} for r in rows], okul)
    return _pdf(pdf, "veli_onay_formlari")


@router.get("/yonetim/onaylar/okullar")
def okullar_ozeti(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _super(yon)
    okullar = db.execute(text("SELECT id, ad, aktif_mi FROM okullar ORDER BY ad")).all()
    out = []
    for ok in okullar:
        out.append({"okul_id": ok.id, "ad": ok.ad, "aktif": bool(ok.aktif_mi), **okul_onaylari(db, ok.id)["ozet"]})
    out.append({"okul_id": 0, "ad": "Okul harici (bireysel)", "aktif": True, **okul_onaylari(db, 0)["ozet"]})
    toplam = {k: sum(r[k] for r in out) for k in ("ogrenci", "kvkk", "veli_alindi", "resit", "veli_bekleyen", "tamam")}
    toplam["yuzde"] = round(100 * toplam["tamam"] / toplam["ogrenci"]) if toplam["ogrenci"] else 0
    return {"okullar": out, "toplam": toplam}


# ----------------------------------------------------------------------------- öğrenci
@router.get("/ogrenci/veli-onayi")
def ogrenci_veli_onayi(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    return vo.durum(db, ogrenci.id)


@router.get("/ogrenci/veli-onayi/form")
def ogrenci_veli_formu(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.core.rapor.veli_formu import veli_formu_pdf
    from app.core.rapor.veri import okul_bilgisi
    pdf = veli_formu_pdf([{"ad_soyad": ogrenci.ad_soyad, "sinif": ogrenci.sinif, "sube": ogrenci.sube,
                           "ogrenci_no": getattr(ogrenci, "ogrenci_no", None)}], okul_bilgisi(db, ogrenci.okul_id))
    return _pdf(pdf, "veli_onay_formu")
