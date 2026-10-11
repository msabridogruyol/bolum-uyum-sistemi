# -*- coding: utf-8 -*-
"""
[2026-10-10] Kulüp üyeliği ve kulüp duyuruları.

Öğrenci:
  GET    /ogrenci/kulup-durumu                 — okulun aktif kulüpleri + benim üyelik durumum + bana görünen duyurular
  POST   /ogrenci/kulupler/{id}/talep          — {mesaj?} katılma talebi (reddedilen / ayrılan tekrar talep edebilir)
  DELETE /ogrenci/kulupler/{id}/talep          — bekleyen talebi geri çek ya da kulüpten ayrıl
Yönetim (okul yetkilisi kendi okulu, süper admin hepsi):
  GET    /yonetim/okul/{okul_id}/kulup-talepleri?durum=bekliyor
  POST   /yonetim/kulup-talep/{id}             — {karar: onayla|reddet|cikar, yanit?}
  GET    /yonetim/kulup/{id}/uyeler            — onaylı üyeler
  GET    /yonetim/kulup/{id}/duyurular · POST /yonetim/kulup/{id}/duyurular · PUT/DELETE /yonetim/kulup-duyuru/{id}

Duyuru görünürlüğü: kulübün onaylı üyeleri görür; "herkese" işaretliyse okuldaki tüm öğrenciler görür.
Etkinlik (tarihli duyuru) görenlerin Takvim'ine de düşer.
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.api.okul_yonetimi import _okul_kapsami, _sinif_metni
from app.core import kulup_servisi as ks
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — Kulüp üyeliği"])
router = APIRouter(prefix="/yonetim", tags=["Kulüp üyeliği ve duyurular"])
MAKS_AKTIF_TALEP = 6   # bekleyen + onaylı toplamı


def ogrenci_duyurulari(db: Session, o: Ogrenci, limit: int = 30) -> list[dict]:
    """Öğrencinin görebildiği duyurular: üyesi olduğu kulüpler + okulda herkese açık olanlar."""
    if not o.okul_id:
        return []
    rows = db.execute(text("""
        SELECT d.id, d.kulup_id, k.ad AS kulup, d.tur, d.baslik, d.metin, d.tarih, d.saat, d.yer, d.herkese, d.olusturulma_zamani,
               EXISTS (SELECT 1 FROM kulup_uyelikleri u WHERE u.kulup_id = d.kulup_id AND u.ogrenci_id = :o AND u.durum = 'onaylandi') AS uye
          FROM kulup_duyurulari d JOIN okul_kulupleri k ON k.id = d.kulup_id
         WHERE k.okul_id = :ok AND k.aktif
           AND (d.herkese OR EXISTS (SELECT 1 FROM kulup_uyelikleri u WHERE u.kulup_id = d.kulup_id AND u.ogrenci_id = :o AND u.durum = 'onaylandi'))
           AND (d.tarih IS NULL OR d.tarih >= CURRENT_DATE - 1 OR d.olusturulma_zamani >= now() - interval '30 days')
         ORDER BY d.olusturulma_zamani DESC LIMIT :n"""), {"o": o.id, "ok": o.okul_id, "n": limit}).mappings().all()
    return [dict(r) for r in rows]


# ============================================================================= öğrenci
@ogrenci_router.get("/kulup-durumu")
def kulup_durumu(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    kulupler = ks.okul_kulupleri(db, o.okul_id)
    uyelik = {r.kulup_id: dict(r._mapping) for r in db.execute(text(
        "SELECT kulup_id, durum, mesaj, yanit, talep_zamani, karar_zamani FROM kulup_uyelikleri WHERE ogrenci_id = :o"), {"o": o.id}).all()}
    uye_say = dict(db.execute(text("SELECT kulup_id, count(*) FROM kulup_uyelikleri WHERE durum = 'onaylandi' AND kulup_id = ANY(:k) "
                                   "GROUP BY kulup_id"), {"k": [k["id"] for k in kulupler] or [-1]}).all())
    sonuc = ks.ilgi_sonucu(db, o.id)
    uyum = {x["id"]: x["uyum"] for x in ks.oneriler(sonuc["puanlar"], kulupler, n=len(kulupler))} if sonuc and kulupler else {}
    return {
        "kulupler": [{**{k2: k[k2] for k2 in ("id", "ad", "aciklama", "sorumlu", "bulusma")}, "ilgi_listesi": ks.etiketler(k["ilgiler"]),
                      "uyum": uyum.get(k["id"]), "uye_sayisi": uye_say.get(k["id"], 0), "uyelik": uyelik.get(k["id"])} for k in kulupler],
        "duyurular": ogrenci_duyurulari(db, o),
        "maks_aktif": MAKS_AKTIF_TALEP,
    }


class TalepIstek(BaseModel):
    mesaj: str | None = Field(default=None, max_length=300)


@ogrenci_router.post("/kulupler/{kulup_id}/talep")
def talep_et(kulup_id: int, istek: TalepIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    k = db.execute(text("SELECT id, ad FROM okul_kulupleri WHERE id = :k AND okul_id = :o AND aktif"), {"k": kulup_id, "o": o.okul_id or -1}).first()
    if k is None:
        raise HTTPException(404, "Kulüp bulunamadı.")
    mevcut = db.execute(text("SELECT durum FROM kulup_uyelikleri WHERE kulup_id = :k AND ogrenci_id = :o"), {"k": kulup_id, "o": o.id}).first()
    if mevcut and mevcut.durum in ("bekliyor", "onaylandi"):
        raise HTTPException(400, "Bu kulüp için zaten bir talebin ya da üyeliğin var.")
    aktif = db.execute(text("SELECT count(*) FROM kulup_uyelikleri WHERE ogrenci_id = :o AND durum IN ('bekliyor','onaylandi')"),
                       {"o": o.id}).scalar() or 0
    if aktif >= MAKS_AKTIF_TALEP:
        raise HTTPException(400, f"Aynı anda en fazla {MAKS_AKTIF_TALEP} kulüpte üyelik ya da bekleyen talebin olabilir.")
    mesaj = (istek.mesaj or "").strip() or None
    db.execute(text("""
        INSERT INTO kulup_uyelikleri (kulup_id, ogrenci_id, durum, mesaj) VALUES (:k, :o, 'bekliyor', :m)
        ON CONFLICT (kulup_id, ogrenci_id) DO UPDATE SET durum = 'bekliyor', mesaj = EXCLUDED.mesaj, yanit = NULL,
            talep_zamani = now(), karar_zamani = NULL, karar_veren = NULL"""), {"k": kulup_id, "o": o.id, "m": mesaj})
    from app.core.bildirim import okul_yetkililerine   # [2026-10-10] bildirim
    okul_yetkililerine(db, o.okul_id, "kulup_talep", f"Yeni kulüp talebi: {k.ad}", f"{o.ad_soyad} kulübe katılmak istiyor.",
                       f"/admin/okul/{o.okul_id}?sekme=kulupler")
    db.commit()
    return kulup_durumu(db, o)


@ogrenci_router.delete("/kulupler/{kulup_id}/talep")
def talep_geri_cek(kulup_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    r = db.execute(text("SELECT durum FROM kulup_uyelikleri WHERE kulup_id = :k AND ogrenci_id = :o"), {"k": kulup_id, "o": o.id}).first()
    if r is None or r.durum not in ("bekliyor", "onaylandi"):
        raise HTTPException(400, "Geri çekilecek bir talep ya da üyelik yok.")
    if r.durum == "bekliyor":
        db.execute(text("DELETE FROM kulup_uyelikleri WHERE kulup_id = :k AND ogrenci_id = :o"), {"k": kulup_id, "o": o.id})
    else:
        db.execute(text("UPDATE kulup_uyelikleri SET durum = 'ayrildi', karar_zamani = now() WHERE kulup_id = :k AND ogrenci_id = :o"),
                   {"k": kulup_id, "o": o.id})
    db.commit()
    return kulup_durumu(db, o)


# ============================================================================= yönetim
def _kulup(db: Session, yon: AdminKullanici, kulup_id: int):
    k = db.execute(text("SELECT id, okul_id, ad FROM okul_kulupleri WHERE id = :k"), {"k": kulup_id}).first()
    if k is None:
        raise HTTPException(404, "Kulüp bulunamadı.")
    _okul_kapsami(db, yon, k.okul_id)
    return k


def _uyelik_satiri(r, o: Ogrenci | None) -> dict:
    return {"id": r.id, "kulup_id": r.kulup_id, "kulup": r.kulup, "durum": r.durum, "mesaj": r.mesaj, "yanit": r.yanit,
            "talep_zamani": r.talep_zamani, "karar_zamani": r.karar_zamani, "karar_veren": r.karar_veren,
            "ogrenci": {"id": str(o.id), "ad_soyad": o.ad_soyad, "sinif": _sinif_metni(o)} if o else None}


@router.get("/okul/{okul_id}/kulup-talepleri")
def talepler(okul_id: int, durum: str = "bekliyor", db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    rows = db.execute(text("""
        SELECT u.*, k.ad AS kulup FROM kulup_uyelikleri u JOIN okul_kulupleri k ON k.id = u.kulup_id
         WHERE k.okul_id = :ok AND (:d = 'hepsi' OR u.durum = :d) ORDER BY u.talep_zamani DESC LIMIT 300"""),
                      {"ok": okul_id, "d": durum}).all()
    ogr = {x.id: x for x in db.query(Ogrenci).filter(Ogrenci.id.in_([r.ogrenci_id for r in rows] or [None])).all()}
    bekleyen = db.execute(text("SELECT count(*) FROM kulup_uyelikleri u JOIN okul_kulupleri k ON k.id = u.kulup_id "
                               "WHERE k.okul_id = :ok AND u.durum = 'bekliyor'"), {"ok": okul_id}).scalar() or 0
    return {"talepler": [_uyelik_satiri(r, ogr.get(r.ogrenci_id)) for r in rows], "bekleyen": bekleyen}


class KararIstek(BaseModel):
    karar: str = Field(pattern="^(onayla|reddet|cikar)$")
    yanit: str | None = Field(default=None, max_length=300)


@router.post("/kulup-talep/{uyelik_id}", status_code=204)
def karar_ver(uyelik_id: int, istek: KararIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = db.execute(text("SELECT u.id, u.kulup_id, u.durum, u.ogrenci_id FROM kulup_uyelikleri u WHERE u.id = :i"), {"i": uyelik_id}).first()
    if r is None:
        raise HTTPException(404, "Talep bulunamadı.")
    k = _kulup(db, yon, r.kulup_id)
    yeni = {"onayla": "onaylandi", "reddet": "reddedildi", "cikar": "ayrildi"}[istek.karar]
    if istek.karar in ("onayla", "reddet") and r.durum != "bekliyor":
        raise HTTPException(400, "Bu talep zaten sonuçlanmış.")
    if istek.karar == "cikar" and r.durum != "onaylandi":
        raise HTTPException(400, "Öğrenci bu kulübün üyesi değil.")
    db.execute(text("UPDATE kulup_uyelikleri SET durum = :d, yanit = :y, karar_zamani = now(), karar_veren = :v WHERE id = :i"),
               {"d": yeni, "y": (istek.yanit or "").strip() or None, "v": yon.ad_soyad, "i": r.id})
    o = db.get(Ogrenci, r.ogrenci_id)
    denetim_yaz(db, yon, f"kulup_{istek.karar}", "kulup_uyelikleri", r.id, f"{k.ad}: {o.ad_soyad if o else ''}", k.okul_id)
    if o is not None:   # [2026-10-10] bildirim (+ e-posta)
        from app.core.bildirim import bildir
        baslik = {"onayla": f"Kulüp talebin kabul edildi 🎉 — {k.ad}", "reddet": f"Kulüp talebin kabul edilmedi — {k.ad}",
                  "cikar": f"Kulüp üyeliğin sona erdi — {k.ad}"}[istek.karar]
        bildir(db, "ogrenci", [o.id], "kulup_karar", baslik, (istek.yanit or "").strip() or None, "/kulupler", k.okul_id, eposta=True)
    db.commit()


@router.get("/kulup/{kulup_id}/uyeler")
def uyeler(kulup_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    k = _kulup(db, yon, kulup_id)
    rows = db.execute(text("SELECT u.*, :ad AS kulup FROM kulup_uyelikleri u WHERE u.kulup_id = :k AND u.durum = 'onaylandi' "
                           "ORDER BY u.karar_zamani"), {"k": kulup_id, "ad": k.ad}).all()
    ogr = {x.id: x for x in db.query(Ogrenci).filter(Ogrenci.id.in_([r.ogrenci_id for r in rows] or [None])).all()}
    liste = [_uyelik_satiri(r, ogr.get(r.ogrenci_id)) for r in rows]
    liste.sort(key=lambda x: ((x["ogrenci"] or {}).get("sinif") or "", (x["ogrenci"] or {}).get("ad_soyad") or ""))
    return {"kulup": k.ad, "uyeler": liste}


class DuyuruIstek(BaseModel):
    tur: str = Field(default="duyuru", pattern="^(duyuru|etkinlik)$")
    baslik: str = Field(min_length=2, max_length=120)
    metin: str | None = Field(default=None, max_length=1000)
    tarih: date | None = None
    saat: str | None = Field(default=None, max_length=20)
    yer: str | None = Field(default=None, max_length=80)
    herkese: bool = False


def _duyuru_kontrol(istek: DuyuruIstek):
    if istek.tur == "etkinlik" and not istek.tarih:
        raise HTTPException(400, "Etkinlik için tarih seçin.")


@router.get("/kulup/{kulup_id}/duyurular")
def duyurular(kulup_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    k = _kulup(db, yon, kulup_id)
    rows = db.execute(text("SELECT * FROM kulup_duyurulari WHERE kulup_id = :k ORDER BY olusturulma_zamani DESC"), {"k": kulup_id}).mappings().all()
    return {"kulup": k.ad, "duyurular": [dict(r) for r in rows]}


@router.post("/kulup/{kulup_id}/duyurular", status_code=201)
def duyuru_ekle(kulup_id: int, istek: DuyuruIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    k = _kulup(db, yon, kulup_id)
    _duyuru_kontrol(istek)
    r = db.execute(text("""
        INSERT INTO kulup_duyurulari (kulup_id, tur, baslik, metin, tarih, saat, yer, herkese, olusturan)
        VALUES (:k, :t, :b, :m, :ta, :s, :y, :h, :o) RETURNING id"""),
                   {"k": kulup_id, "t": istek.tur, "b": istek.baslik.strip(), "m": (istek.metin or "").strip() or None,
                    "ta": istek.tarih if istek.tur == "etkinlik" else None, "s": istek.saat if istek.tur == "etkinlik" else None,
                    "y": istek.yer if istek.tur == "etkinlik" else None, "h": istek.herkese, "o": yon.ad_soyad}).first()
    denetim_yaz(db, yon, "kulup_duyuru_ekle", "kulup_duyurulari", r.id, f"{k.ad}: {istek.baslik}", k.okul_id)
    # [2026-10-10] bildirim: üyelere (herkese açıksa okulun tüm öğrencilerine); etkinlikse üyelere e-posta da
    from app.core.bildirim import bildir
    uyeler = [x[0] for x in db.execute(text("SELECT ogrenci_id FROM kulup_uyelikleri WHERE kulup_id = :k AND durum = 'onaylandi'"), {"k": kulup_id}).all()]
    hepsi = [x[0] for x in db.execute(text("SELECT id FROM ogrenciler WHERE okul_id = :o"), {"o": k.okul_id}).all()] if istek.herkese else []
    zaman = (f"📅 {istek.tarih.strftime('%d.%m.%Y')}{' ' + istek.saat if istek.saat else ''}{' · ' + istek.yer if istek.yer else ''}"
             if istek.tur == "etkinlik" and istek.tarih else "")
    metin = " — ".join(x for x in (zaman, (istek.metin or "").strip()[:300]) if x) or None
    baslik = f"{k.ad}: {istek.baslik.strip()}"
    bildir(db, "ogrenci", uyeler, f"kulup_{istek.tur}", baslik, metin, "/kulupler", k.okul_id, eposta=istek.tur == "etkinlik")
    uye_kume = set(uyeler)
    bildir(db, "ogrenci", [x for x in hepsi if x not in uye_kume], f"kulup_{istek.tur}", baslik, metin, "/kulupler", k.okul_id)
    db.commit()
    return {"id": r.id}


def _duyuru(db: Session, yon: AdminKullanici, duyuru_id: int):
    d = db.execute(text("SELECT id, kulup_id, baslik FROM kulup_duyurulari WHERE id = :i"), {"i": duyuru_id}).first()
    if d is None:
        raise HTTPException(404, "Duyuru bulunamadı.")
    return d, _kulup(db, yon, d.kulup_id)


@router.put("/kulup-duyuru/{duyuru_id}", status_code=204)
def duyuru_duzenle(duyuru_id: int, istek: DuyuruIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    d, k = _duyuru(db, yon, duyuru_id)
    _duyuru_kontrol(istek)
    db.execute(text("""UPDATE kulup_duyurulari SET tur = :t, baslik = :b, metin = :m, tarih = :ta, saat = :s, yer = :y, herkese = :h
                        WHERE id = :i"""),
               {"t": istek.tur, "b": istek.baslik.strip(), "m": (istek.metin or "").strip() or None,
                "ta": istek.tarih if istek.tur == "etkinlik" else None, "s": istek.saat if istek.tur == "etkinlik" else None,
                "y": istek.yer if istek.tur == "etkinlik" else None, "h": istek.herkese, "i": d.id})
    denetim_yaz(db, yon, "kulup_duyuru_duzenle", "kulup_duyurulari", d.id, f"{k.ad}: {istek.baslik}", k.okul_id)
    db.commit()


@router.delete("/kulup-duyuru/{duyuru_id}", status_code=204)
def duyuru_sil(duyuru_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    d, k = _duyuru(db, yon, duyuru_id)
    db.execute(text("DELETE FROM kulup_duyurulari WHERE id = :i"), {"i": d.id})
    denetim_yaz(db, yon, "kulup_duyuru_sil", "kulup_duyurulari", d.id, f"{k.ad}: {d.baslik}", k.okul_id)
    db.commit()
