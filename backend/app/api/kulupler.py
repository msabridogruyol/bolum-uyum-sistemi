# -*- coding: utf-8 -*-
"""
[2026-10-10] Kulüpler (öğrenci toplulukları) ve kısa ilgi testi.

Öğrenci:
  GET  /ogrenci/ilgi-testi        — sorular + (varsa) sonuç ve kulüp önerileri
  POST /ogrenci/ilgi-testi        — cevapları kaydet (tekrar çözülebilir; son cevap geçerli)
Yönetim (okul yetkilisi kendi okulu, süper admin hepsi):
  GET    /yonetim/okul/{id}/kulupler              — kulüpler + öneri sayıları + ilgi testi istatistiği
  POST   /yonetim/okul/{id}/kulupler              — kulüp ekle
  POST   /yonetim/okul/{id}/kulupler/hazir        — hazır listeden ekle (aynı adlı olanlar atlanır)
  PUT    /yonetim/kulup/{kulup_id}                — düzenle
  DELETE /yonetim/kulup/{kulup_id}                — sil
  GET    /yonetim/kulup/{kulup_id}/ogrenciler     — bu kulübü ilk 3 önerisinde gören öğrenciler
  GET    /yonetim/ogrenci/{id}/ilgi               — öğrencinin ilgi testi sonucu + kulüp önerileri
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.api.okul_yonetimi import _okul_kapsami, _ogrenci_kapsami, _sinif_metni
from app.core import kulup_servisi as ks
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — İlgi testi ve kulüpler"])
router = APIRouter(prefix="/yonetim", tags=["Kulüpler"])


def _oneri_paketi(db: Session, o: Ogrenci, sonuc: dict | None) -> dict:
    kulupler = ks.okul_kulupleri(db, o.okul_id)
    okulda = bool(kulupler)
    havuz = kulupler or ks.hazir_liste()
    return {"okul_kulubu_var": okulda,
            "oneriler": ks.oneriler(sonuc["puanlar"], havuz, n=6) if sonuc else [],
            "kulup_sayisi": len(kulupler)}


# ============================================================================= öğrenci
@ogrenci_router.get("/ilgi-testi")
def ilgi_testi(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    sonuc = ks.ilgi_sonucu(db, o.id)
    return {"sorular": [{"kod": k, "metin": m} for k, _, m in ks.SORULAR], "boyutlar": ks.boyut_listesi(),
            "sonuc": sonuc, **_oneri_paketi(db, o, sonuc)}


class IlgiCevapIstek(BaseModel):
    cevaplar: dict[str, int]


@ogrenci_router.post("/ilgi-testi")
def ilgi_testi_kaydet(istek: IlgiCevapIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    gecerli = {k: v for k, v in istek.cevaplar.items() if k in ks.SORU_BOYUT and isinstance(v, int) and 1 <= v <= 5}
    if len(gecerli) < len(ks.SORULAR):
        raise HTTPException(status_code=400, detail=f"Lütfen tüm soruları cevapla ({len(gecerli)}/{len(ks.SORULAR)}).")
    puanlar = ks.puanla(gecerli)
    db.execute(text("""
        INSERT INTO ogrenci_ilgi_testleri (ogrenci_id, cevaplar, puanlar, tamamlanma_zamani)
        VALUES (:i, CAST(:c AS JSONB), CAST(:p AS JSONB), :z)
        ON CONFLICT (ogrenci_id) DO UPDATE SET cevaplar = EXCLUDED.cevaplar, puanlar = EXCLUDED.puanlar,
            tamamlanma_zamani = EXCLUDED.tamamlanma_zamani
    """), {"i": str(o.id), "c": json.dumps(gecerli), "p": json.dumps(puanlar), "z": datetime.now(timezone.utc)})
    db.commit()
    return ilgi_testi(db, o)


# ============================================================================= yönetim
class KulupIstek(BaseModel):
    ad: str = Field(min_length=2, max_length=80)
    aciklama: str | None = Field(default=None, max_length=300)
    ilgiler: list[str] = Field(default_factory=list)
    sorumlu: str | None = Field(default=None, max_length=80)
    bulusma: str | None = Field(default=None, max_length=80)
    aktif: bool = True


def _ilgi_metni(liste: list[str]) -> str:
    e = [x for x in dict.fromkeys(liste) if x in ks.BOYUTLAR][:3]
    if not e:
        raise HTTPException(status_code=400, detail="En az bir ilgi alanı seçin.")
    return ",".join(e)


def _kulup(db: Session, yon: AdminKullanici, kulup_id: int) -> dict:
    k = db.execute(text("SELECT * FROM okul_kulupleri WHERE id = :k"), {"k": kulup_id}).mappings().first()
    if not k:
        raise HTTPException(status_code=404, detail="Kulüp bulunamadı.")
    _okul_kapsami(db, yon, k["okul_id"])
    return dict(k)


def _okul_ilgi_sonuclari(db: Session, okul_id: int) -> list[tuple[Ogrenci, dict]]:
    satirlar = db.execute(text("""
        SELECT t.ogrenci_id, t.puanlar FROM ogrenci_ilgi_testleri t JOIN ogrenciler o ON o.id = t.ogrenci_id
        WHERE o.okul_id = :o
    """), {"o": okul_id}).all()
    ogr = {x.id: x for x in db.query(Ogrenci).filter(Ogrenci.id.in_([r[0] for r in satirlar] or [None])).all()}
    return [(ogr[r[0]], r[1] if isinstance(r[1], dict) else json.loads(r[1])) for r in satirlar if r[0] in ogr]


@router.get("/okul/{okul_id}/kulupler")
def kulupleri_listele(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    if not okul_id:
        raise HTTPException(status_code=400, detail="Kulüpler okul bazlıdır.")
    kulupler = ks.okul_kulupleri(db, okul_id, sadece_aktif=False)
    sonuclar = _okul_ilgi_sonuclari(db, okul_id)
    aktif = [k for k in kulupler if k["aktif"]]
    say = {k["id"]: 0 for k in kulupler}
    boyut_top = {b: [] for b in ks.BOYUTLAR}
    for _, p in sonuclar:
        for x in ks.oneriler(p, aktif, n=3):
            say[x["id"]] += 1
        for b, v in p.items():
            if b in boyut_top:
                boyut_top[b].append(v)
    toplam_ogr = db.query(Ogrenci).filter(Ogrenci.okul_id == okul_id).count()
    # [2026-10-10] üyelik ve bekleyen talep sayıları
    uyelik = {}
    try:
        for kid, durum, n in db.execute(text("SELECT kulup_id, durum, count(*) FROM kulup_uyelikleri WHERE kulup_id = ANY(:k) "
                                             "GROUP BY kulup_id, durum"), {"k": [k["id"] for k in kulupler] or [-1]}).all():
            uyelik.setdefault(kid, {})[durum] = n
    except Exception:
        db.rollback()
    return {
        "kulupler": [{**k, "ilgi_listesi": ks.etiketler(k["ilgiler"]), "oneri_sayisi": say.get(k["id"], 0),
                      "uye_sayisi": uyelik.get(k["id"], {}).get("onaylandi", 0),
                      "bekleyen_talep": uyelik.get(k["id"], {}).get("bekliyor", 0)} for k in kulupler],
        "boyutlar": ks.boyut_listesi(),
        "test_yapan": len(sonuclar), "ogrenci_sayisi": toplam_ogr,
        "okul_ilgi": sorted([{"kod": b, "ad": ks.BOYUTLAR[b]["ad"], "ikon": ks.BOYUTLAR[b]["ikon"], "ort": round(sum(v) / len(v))}
                             for b, v in boyut_top.items() if v], key=lambda x: -x["ort"]),
        "hazir_sayisi": len(ks.HAZIR_KULUPLER),
    }


@router.post("/okul/{okul_id}/kulupler", status_code=201)
def kulup_ekle(okul_id: int, istek: KulupIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    if not okul_id:
        raise HTTPException(status_code=400, detail="Kulüpler okul bazlıdır.")
    sira = db.execute(text("SELECT COALESCE(MAX(sira), 0) + 1 FROM okul_kulupleri WHERE okul_id = :o"), {"o": okul_id}).scalar()
    kid = db.execute(text("""
        INSERT INTO okul_kulupleri (okul_id, ad, aciklama, ilgiler, sorumlu, bulusma, aktif, sira)
        VALUES (:o, :ad, :ac, :il, :so, :bu, :ak, :si) RETURNING id
    """), {"o": okul_id, "ad": istek.ad.strip(), "ac": (istek.aciklama or "").strip() or None, "il": _ilgi_metni(istek.ilgiler),
           "so": (istek.sorumlu or "").strip() or None, "bu": (istek.bulusma or "").strip() or None, "ak": istek.aktif, "si": sira}).scalar()
    denetim_yaz(db, yon, "kulup_ekle", "okul_kulupleri", kid, istek.ad.strip(), okul_id)
    db.commit()
    return {"id": kid}


@router.post("/okul/{okul_id}/kulupler/hazir")
def hazir_ekle(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    if not okul_id:
        raise HTTPException(status_code=400, detail="Kulüpler okul bazlıdır.")
    var = {k["ad"].lower() for k in ks.okul_kulupleri(db, okul_id, sadece_aktif=False)}
    sira = db.execute(text("SELECT COALESCE(MAX(sira), 0) FROM okul_kulupleri WHERE okul_id = :o"), {"o": okul_id}).scalar()
    eklenen = 0
    for ad, ac, il in ks.HAZIR_KULUPLER:
        if ad.lower() in var:
            continue
        sira += 1
        db.execute(text("INSERT INTO okul_kulupleri (okul_id, ad, aciklama, ilgiler, sira) VALUES (:o, :ad, :ac, :il, :si)"),
                   {"o": okul_id, "ad": ad, "ac": ac, "il": il, "si": sira})
        eklenen += 1
    if eklenen:
        denetim_yaz(db, yon, "kulup_hazir_liste", "okul_kulupleri", okul_id, f"{eklenen} hazır kulüp eklendi", okul_id)
    db.commit()
    return {"eklenen": eklenen}


@router.put("/kulup/{kulup_id}")
def kulup_duzenle(kulup_id: int, istek: KulupIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    k = _kulup(db, yon, kulup_id)
    db.execute(text("""
        UPDATE okul_kulupleri SET ad = :ad, aciklama = :ac, ilgiler = :il, sorumlu = :so, bulusma = :bu, aktif = :ak WHERE id = :k
    """), {"k": kulup_id, "ad": istek.ad.strip(), "ac": (istek.aciklama or "").strip() or None, "il": _ilgi_metni(istek.ilgiler),
           "so": (istek.sorumlu or "").strip() or None, "bu": (istek.bulusma or "").strip() or None, "ak": istek.aktif})
    denetim_yaz(db, yon, "kulup_duzenle", "okul_kulupleri", kulup_id, istek.ad.strip(), k["okul_id"])
    db.commit()
    return {"tamam": True}


@router.delete("/kulup/{kulup_id}", status_code=204)
def kulup_sil(kulup_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    k = _kulup(db, yon, kulup_id)
    db.execute(text("DELETE FROM okul_kulupleri WHERE id = :k"), {"k": kulup_id})
    denetim_yaz(db, yon, "kulup_sil", "okul_kulupleri", kulup_id, k["ad"], k["okul_id"])
    db.commit()


@router.get("/kulup/{kulup_id}/ogrenciler")
def kulup_ogrencileri(kulup_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    k = _kulup(db, yon, kulup_id)
    aktif = ks.okul_kulupleri(db, k["okul_id"])
    sonuc = []
    for o, p in _okul_ilgi_sonuclari(db, k["okul_id"]):
        ilk = ks.oneriler(p, aktif, n=3)
        for sira, x in enumerate(ilk, 1):
            if x["id"] == kulup_id:
                sonuc.append({"id": str(o.id), "ad_soyad": o.ad_soyad, "sinif": _sinif_metni(o), "uyum": x["uyum"], "sira": sira})
    sonuc.sort(key=lambda x: (-x["uyum"], x["ad_soyad"]))
    return {"kulup": k["ad"], "ogrenciler": sonuc}


@router.get("/ogrenci/{ogrenci_id}/ilgi")
def ogrenci_ilgi(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    sonuc = ks.ilgi_sonucu(db, o.id)
    if sonuc:
        sonuc.pop("cevaplar", None)
    return {"boyutlar": ks.boyut_listesi(), "sonuc": sonuc, **_oneri_paketi(db, o, sonuc)}
