# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı — öğrenci uçları (modül: is_hayati).

  GET /ogrenci/is-hayati/ozet                 — sayfa açılışı: hedef bölüm, ilk 5 öneri, tüm bölümler (seçici), kısa veri
  GET /ogrenci/is-hayati/bolum/{bolum_id}     — istihdam, kazanç (tahmin işaretli), kamu maaşları, asgari ücret, eksikler
  GET /ogrenci/is-hayati/giderler?il=         — yaşam gideri kalemleri (il varsa il, yoksa Türkiye geneli) + il listesi

Genişletme sözleşmesi (diğer içerik bileşenleri için — ayrıntı docs/IS_HAYATI.md):
  Her içerik bileşeni kendi dosyasını açar: app/api/is_hayati_<konu>.py (ör. is_hayati_cv.py).
  - `ogrenci_router = APIRouter()` tanımlarsa, yolları bu dosyadaki router'a eklenir → /ogrenci/is-hayati/<yol>
    ve modül kapısı (ogrenci_modulu("is_hayati")) otomatik uygulanır. Kendi prefix'ini VERMEZ.
  - `yonetim_router` tanımlarsa olduğu gibi uygulamaya eklenir (kendi prefix'i ve yetki bağımlılığı kendisinde).
  main.py'ye dokunmak gerekmez; bu dosya açılışta is_hayati_* modüllerini bulup bağlar.
"""
import importlib
import logging
import pkgutil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core import is_hayati_servisi as ihs
from app.core.database import get_db
from app.models import Ogrenci

_log = logging.getLogger("is_hayati")

router = APIRouter(prefix="/ogrenci/is-hayati", tags=["İş Hayatı"])
# Alt modüllerin yönetim router'ları (main.py bunları da ekler)
ek_yonetim_routerlari: list[APIRouter] = []


def _hedef_ve_oneriler(db: Session, ogrenci_id) -> tuple[dict | None, list[dict]]:
    from app.api.tercih import uyumlar
    h = db.execute(text("SELECT b.id, b.ad FROM ogrenci_hedef_bolum h JOIN bolumler b ON b.id = h.bolum_id "
                        "WHERE h.ogrenci_id = :o AND h.aktif_mi ORDER BY h.secim_zamani DESC LIMIT 1"), {"o": ogrenci_id}).first()
    hedef = {"id": h.id, "ad": ihs.tr_baslik(h.ad)} if h else None
    uy = uyumlar(db, ogrenci_id)
    ilk = sorted(uy.items(), key=lambda x: x[1][1])[:5]
    adlar = {}
    if ilk:
        adlar = {r.id: r.ad for r in db.execute(text("SELECT id, ad FROM bolumler WHERE id = ANY(:i)"), {"i": [b for b, _ in ilk]}).all()}
    oneriler = [{"id": b, "ad": ihs.tr_baslik(adlar.get(b, "?")), "uyum": u, "sira": s} for b, (u, s) in ilk]
    return hedef, oneriler


@router.get("/ozet")
def ozet(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    hedef, oneriler = _hedef_ve_oneriler(db, o.id)
    ilgili = ([hedef["id"]] if hedef else []) + [x["id"] for x in oneriler if not hedef or x["id"] != hedef["id"]]
    kisa = {}
    if ilgili:
        for r in db.execute(text("""SELECT DISTINCT ON (bolum_id) bolum_id, istihdam_orani, is_bulma_suresi_ay, alan_uyum_orani,
                                           kazanc_grubu, veri_yili
                                      FROM istihdam_gostergeleri WHERE bolum_id = ANY(:i)
                                     ORDER BY bolum_id, veri_yili DESC, (duzey = 'lisans') DESC NULLS LAST, id"""), {"i": ilgili}).mappings().all():
            kisa[r["bolum_id"]] = {"istihdam_orani": ihs._f(r["istihdam_orani"]), "is_bulma_suresi_ay": ihs._f(r["is_bulma_suresi_ay"]),
                                   "alan_uyum_orani": ihs._f(r["alan_uyum_orani"]), "kazanc_grubu": r["kazanc_grubu"],
                                   "kazanc_grubu_ad": ihs.KAZANC_GRUPLARI.get(r["kazanc_grubu"]), "veri_yili": r["veri_yili"]}
    bolumler = [{"id": r.id, "ad": ihs.tr_baslik(r.ad)} for r in db.execute(text("SELECT id, ad FROM bolumler WHERE durum = 'yayinda' ORDER BY ad")).all()]
    varsayilan = hedef["id"] if hedef else (oneriler[0]["id"] if oneriler else None)
    return {
        "hedef": hedef, "oneriler": oneriler, "varsayilan_bolum_id": varsayilan, "bolumler": bolumler,
        "kisa": {str(k): v for k, v in kisa.items()}, "asgari": ihs.guncel_asgari(db),
        "veri_kaynaklari": ihs.veri_kaynaklari(db),
    }


@router.get("/bolum/{bolum_id}")
def bolum(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    v = ihs.bolum_verisi(db, bolum_id)
    if v is None:
        raise HTTPException(404, "Bölüm bulunamadı.")
    return v


@router.get("/giderler")
def giderler(il: str | None = Query(None, max_length=60), db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    il = (il or "").strip() or None
    rows = db.execute(text("SELECT il, kalem_kodu, ad, aylik_tutar, kaynak, tarih FROM yasam_giderleri "
                           "WHERE il IS NULL OR il = :il ORDER BY kalem_kodu, (il IS NULL)"), {"il": il or ""}).mappings().all()
    secilen = {}
    for r in rows:   # il satırı varsa Türkiye geneli yerine o kullanılır (sıralama: il önce)
        if r["kalem_kodu"] not in secilen:
            secilen[r["kalem_kodu"]] = r
    kalemler = [{"kalem_kodu": r["kalem_kodu"], "ad": r["ad"], "aylik_tutar": ihs._f(r["aylik_tutar"]), "il": r["il"],
                 "turkiye_geneli": r["il"] is None, "kaynak": r["kaynak"], "tarih": r["tarih"].isoformat() if r["tarih"] else None,
                 "tahmin": False} for r in secilen.values()]
    iller = [x[0] for x in db.execute(text("SELECT DISTINCT il FROM yasam_giderleri WHERE il IS NOT NULL ORDER BY il")).all()]
    return {"il": il, "iller": iller, "kalemler": kalemler, "toplam": round(sum(k["aylik_tutar"] or 0 for k in kalemler), 2) if kalemler else None,
            "asgari": ihs.guncel_asgari(db)}


def _alt_modulleri_bagla():
    """app/api/is_hayati_*.py dosyalarını bulur; ogrenci_router yollarını bu router'a, yonetim_router'ı listeye ekler."""
    import app.api as paket
    for m in sorted(pkgutil.iter_modules(paket.__path__), key=lambda x: x.name):
        if not m.name.startswith("is_hayati_"):
            continue
        try:
            mod = importlib.import_module(f"app.api.{m.name}")
        except Exception:
            _log.exception("İş Hayatı alt modülü yüklenemedi: %s", m.name)
            continue
        alt = getattr(mod, "ogrenci_router", None)
        if isinstance(alt, APIRouter):
            router.include_router(alt)
        yon = getattr(mod, "yonetim_router", None)
        if isinstance(yon, APIRouter):
            ek_yonetim_routerlari.append(yon)


_alt_modulleri_bagla()
