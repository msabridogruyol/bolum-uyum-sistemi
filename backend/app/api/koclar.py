# -*- coding: utf-8 -*-
"""
[2026-10-10] Dışarıdan anlaşmalı eğitim koçları ve görüşme talepleri — YALNIZCA SÜPER ADMİN yönetir.

Akış:
  1) Süper admin koçla anlaşır, koçu ekler ve hangi okullarda çalışacağını okul okul atar.
     Okul bazında durum: aktif (öğrenciler görür) · onay_bekliyor (okulun onayı bekleniyor, görünmez)
     · reddedildi (okul istemedi, görünmez; not tutulur).
  2) Öğrenci yalnızca kendi okulunda "aktif" olan koçları görür, görüşme talebi bırakır. Koçun iletişim bilgisini GÖRMEZ.
  3) Talepler süper adminin ekranına düşer; durum, randevu zamanı ve öğrenciye not girilir. Okul yetkilileri koç ekranı görmez.

Öğrenci:  GET /ogrenci/koclar · POST /ogrenci/koclar/{id}/talep · POST /ogrenci/koc-talep/{id}/iptal
Süper admin: GET/POST /yonetim/koclar · PUT/DELETE /yonetim/koc/{id} · PUT /yonetim/koc/{id}/okullar
             GET /yonetim/koc-talepleri?okul_id= · PUT /yonetim/koc-talep/{id}
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_super_admin
from app.api.okul_yonetimi import _sinif_metni
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — Eğitim koçları"])
router = APIRouter(prefix="/yonetim", tags=["Eğitim koçları"])

KONULAR = [
    "Bölüm ve meslek seçimi", "Ders çalışma ve sınav planı", "Motivasyon ve sınav kaygısı",
    "Üniversite tercih danışmanlığı", "Yurt dışında eğitim", "Hedef belirleme ve kişisel gelişim",
]
GORUSME = {"online": "Online", "yuz_yuze": "Yüz yüze", "ikisi": "Online veya yüz yüze"}
DURUMLAR = {"beklemede": "Talebin inceleniyor", "onaylandi": "Görüşme planlandı", "tamamlandi": "Görüşme yapıldı",
            "reddedildi": "Şu an planlanamadı", "iptal": "İptal edildi"}
ACIK = ("beklemede", "onaylandi")
OKUL_DURUM = {"aktif": "Aktif", "onay_bekliyor": "Okul onayı bekleniyor", "reddedildi": "Okul reddetti"}
EN_FAZLA_ACIK = 3


def _simdi():
    return datetime.now(timezone.utc)


def _alan_adlari(db: Session) -> dict[str, str]:
    return {r[0]: r[1] for r in db.execute(text("SELECT kod, ad FROM dallar WHERE kod LIKE 'U%' ORDER BY kod")).all()}


def _liste(metin: str | None) -> list[str]:
    return [x for x in (metin or "").split(",") if x]


def _ogrenci_alanlari(db: Session, o: Ogrenci) -> list[str]:
    """Hedef bölüm + Listem bölümlerinin üst alan kodları (önce hedef)."""
    satirlar = db.execute(text("""
        SELECT d.kod, 0 AS oncelik FROM ogrenci_hedef_bolum h
          JOIN bolum_dal_eslesme e ON e.bolum_id = h.bolum_id JOIN dallar d ON d.id = e.dal_id
         WHERE h.ogrenci_id = :o AND h.aktif_mi AND d.kod LIKE 'U%'
        UNION ALL
        SELECT d.kod, 1 FROM ogrenci_favori_bolumler f
          JOIN bolum_dal_eslesme e ON e.bolum_id = f.bolum_id JOIN dallar d ON d.id = e.dal_id
         WHERE f.ogrenci_id = :o AND d.kod LIKE 'U%'
    """), {"o": o.id}).all()
    sira: list[str] = []
    for kod, _ in sorted(satirlar, key=lambda r: r[1]):
        if kod not in sira:
            sira.append(kod)
    return sira


def _koc_out(k: dict, alanlar: dict, ozel: bool = False) -> dict:
    d = {"id": k["id"], "ad_soyad": k["ad_soyad"], "unvan": k["unvan"], "hakkinda": k["hakkinda"],
         "alanlar": _liste(k["alanlar"]), "alan_adlari": [alanlar.get(a, a) for a in _liste(k["alanlar"])],
         "konular": _liste(k["konular"]), "deneyim_yil": k["deneyim_yil"], "gorusme_sekli": k["gorusme_sekli"],
         "gorusme_metni": GORUSME.get(k["gorusme_sekli"], k["gorusme_sekli"]), "ucret_bilgisi": k["ucret_bilgisi"],
         "aktif": k["aktif"]}
    if ozel:
        d.update({"eposta": k["eposta"], "telefon": k["telefon"]})
    return d


# ============================================================================= öğrenci
@ogrenci_router.get("/koclar")
def ogrenci_koclar(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    alanlar = _alan_adlari(db)
    ilgili = _ogrenci_alanlari(db, o)
    koclar = db.execute(text("""
        SELECT k.* FROM egitim_koclari k JOIN koc_okullari ko ON ko.koc_id = k.id
         WHERE k.aktif AND ko.okul_id = :ok AND ko.durum = 'aktif' ORDER BY k.ad_soyad
    """), {"ok": o.okul_id or -1}).mappings().all()
    sonuc = []
    for k in koclar:
        x = _koc_out(dict(k), alanlar)
        ortak = [a for a in ilgili if a in x["alanlar"]]
        x["uygun"] = bool(ortak)
        x["uygun_alanlar"] = [alanlar.get(a, a) for a in ortak]
        x["_sira"] = (0 if ortak else 1, ilgili.index(ortak[0]) if ortak else 99)
        sonuc.append(x)
    sonuc.sort(key=lambda x: (x["_sira"], x["ad_soyad"]))
    for x in sonuc:
        x.pop("_sira")
    talepler = db.execute(text("""
        SELECT t.id, t.koc_id, k.ad_soyad AS koc_ad, t.konu, t.durum, t.randevu_zamani, t.ogrenciye_not, t.tercih_zamani,
               t.talep_eden, t.olusturulma_zamani, t.guncelleme_zamani
          FROM koc_gorusme_talepleri t JOIN egitim_koclari k ON k.id = t.koc_id
         WHERE t.ogrenci_id = :o ORDER BY t.olusturulma_zamani DESC LIMIT 20
    """), {"o": o.id}).mappings().all()
    return {"koclar": sonuc, "ilgili_alanlar": [alanlar.get(a, a) for a in ilgili], "konular": KONULAR,
            "talepler": [{**dict(t), "durum_metni": DURUMLAR.get(t["durum"], t["durum"])} for t in talepler],
            "okul_var": bool(o.okul_id)}


class TalepIstek(BaseModel):
    konu: str
    tercih_zamani: str | None = Field(default=None, max_length=120)
    mesaj: str | None = Field(default=None, max_length=800)
    talep_eden: str = "ogrenci"           # ogrenci | veli
    veli_ad: str | None = Field(default=None, max_length=80)
    iletisim: str | None = Field(default=None, max_length=120)


@ogrenci_router.post("/koclar/{koc_id}/talep", status_code=201)
def talep_olustur(koc_id: int, istek: TalepIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if not o.okul_id:
        raise HTTPException(status_code=400, detail="Eğitim koçları okul bazında atanır; hesabın bir okula bağlı olmadığı için görüşme talebi gönderemezsin.")
    k = db.execute(text("""SELECT k.id, k.ad_soyad FROM egitim_koclari k JOIN koc_okullari ko ON ko.koc_id = k.id
                            WHERE k.id = :k AND k.aktif AND ko.okul_id = :ok AND ko.durum = 'aktif'"""),
                   {"k": koc_id, "ok": o.okul_id}).mappings().first()
    if not k:
        raise HTTPException(status_code=404, detail="Koç bulunamadı.")
    if istek.konu not in KONULAR:
        raise HTTPException(status_code=400, detail="Lütfen bir görüşme konusu seç.")
    if istek.talep_eden not in ("ogrenci", "veli"):
        raise HTTPException(status_code=400, detail="Geçersiz talep.")
    if istek.talep_eden == "veli" and (not (istek.veli_ad or "").strip() or not (istek.iletisim or "").strip()):
        raise HTTPException(status_code=400, detail="Veli adına taleplerde veli adı ve iletişim bilgisi gerekli.")
    acik = db.execute(text("SELECT koc_id FROM koc_gorusme_talepleri WHERE ogrenci_id = :o AND durum IN ('beklemede','onaylandi')"),
                      {"o": o.id}).scalars().all()
    if koc_id in acik:
        raise HTTPException(status_code=400, detail="Bu koçla zaten açık bir talebin var.")
    if len(acik) >= EN_FAZLA_ACIK:
        raise HTTPException(status_code=400, detail=f"Aynı anda en fazla {EN_FAZLA_ACIK} açık talebin olabilir.")
    tid = db.execute(text("""
        INSERT INTO koc_gorusme_talepleri (koc_id, ogrenci_id, okul_id, talep_eden, veli_ad, iletisim, konu, tercih_zamani, mesaj)
        VALUES (:k, :o, :ok, :te, :va, :il, :ko, :tz, :me) RETURNING id
    """), {"k": koc_id, "o": o.id, "ok": o.okul_id, "te": istek.talep_eden,
           "va": (istek.veli_ad or "").strip() or None, "il": (istek.iletisim or "").strip() or None, "ko": istek.konu,
           "tz": (istek.tercih_zamani or "").strip() or None, "me": (istek.mesaj or "").strip() or None}).scalar()
    db.commit()
    return {"id": tid}


@ogrenci_router.post("/koc-talep/{talep_id}/iptal")
def talep_iptal(talep_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    n = db.execute(text("""
        UPDATE koc_gorusme_talepleri SET durum = 'iptal', guncelleme_zamani = :z
         WHERE id = :t AND ogrenci_id = :o AND durum IN ('beklemede','onaylandi')
    """), {"t": talep_id, "o": o.id, "z": _simdi()}).rowcount
    db.commit()
    if not n:
        raise HTTPException(status_code=400, detail="Bu talep iptal edilemez.")
    return {"tamam": True}


# ============================================================================= yönetim
class KocIstek(BaseModel):
    ad_soyad: str = Field(min_length=3, max_length=80)
    unvan: str | None = Field(default=None, max_length=80)
    hakkinda: str | None = Field(default=None, max_length=1000)
    alanlar: list[str] = Field(default_factory=list)
    konular: list[str] = Field(default_factory=list)
    deneyim_yil: int | None = Field(default=None, ge=0, le=60)
    gorusme_sekli: str = "online"
    ucret_bilgisi: str | None = Field(default=None, max_length=120)
    eposta: str | None = Field(default=None, max_length=120)
    telefon: str | None = Field(default=None, max_length=40)
    aktif: bool = True


def _degerler(db: Session, istek: KocIstek) -> dict:
    alan_kodlari = set(_alan_adlari(db))
    if istek.gorusme_sekli not in GORUSME:
        raise HTTPException(status_code=400, detail="Geçersiz görüşme şekli.")
    t = lambda v: (v or "").strip() or None  # noqa: E731
    return {"ad": istek.ad_soyad.strip(), "un": t(istek.unvan), "ha": t(istek.hakkinda),
            "al": ",".join(a for a in dict.fromkeys(istek.alanlar) if a in alan_kodlari),
            "ko": ",".join(k for k in dict.fromkeys(istek.konular) if k in KONULAR),
            "de": istek.deneyim_yil, "gs": istek.gorusme_sekli, "uc": t(istek.ucret_bilgisi),
            "ep": t(istek.eposta), "te": t(istek.telefon), "ak": istek.aktif}


def _okul_atamalari(db: Session) -> dict[int, list[dict]]:
    sonuc: dict[int, list[dict]] = {}
    for r in db.execute(text("""
        SELECT ko.koc_id, ko.okul_id, ko.durum, ko.notlar, o.ad FROM koc_okullari ko JOIN okullar o ON o.id = ko.okul_id ORDER BY o.ad
    """)).mappings().all():
        sonuc.setdefault(r["koc_id"], []).append({"okul_id": r["okul_id"], "okul_ad": r["ad"], "durum": r["durum"],
                                                  "durum_adi": OKUL_DURUM.get(r["durum"], r["durum"]), "notlar": r["notlar"]})
    return sonuc


@router.get("/koclar")
def koclari_listele(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    alanlar = _alan_adlari(db)
    satirlar = db.execute(text("SELECT * FROM egitim_koclari ORDER BY ad_soyad")).mappings().all()
    talep = {r[0]: (r[1], r[2]) for r in db.execute(text(
        "SELECT koc_id, COUNT(*) FILTER (WHERE durum = 'beklemede'), COUNT(*) FROM koc_gorusme_talepleri GROUP BY koc_id")).all()}
    atama = _okul_atamalari(db)
    return {
        "koclar": [{**_koc_out(dict(k), alanlar, ozel=True), "okullar": atama.get(k["id"], []),
                    "bekleyen": talep.get(k["id"], (0, 0))[0], "toplam_talep": talep.get(k["id"], (0, 0))[1]} for k in satirlar],
        "alanlar": [{"kod": k, "ad": v} for k, v in alanlar.items()], "konular": KONULAR,
        "gorusme": [{"kod": k, "ad": v} for k, v in GORUSME.items()],
        "okul_durumlari": [{"kod": k, "ad": v} for k, v in OKUL_DURUM.items()],
        "okullar": [{"id": r[0], "ad": r[1]} for r in db.execute(text("SELECT id, ad FROM okullar ORDER BY ad")).all()],
    }


@router.post("/koclar", status_code=201)
def koc_ekle(istek: KocIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    d = _degerler(db, istek)
    kid = db.execute(text("""
        INSERT INTO egitim_koclari (ad_soyad, unvan, hakkinda, alanlar, konular, deneyim_yil, gorusme_sekli,
                                    ucret_bilgisi, eposta, telefon, aktif, okullar_tasindi)
        VALUES (:ad, :un, :ha, :al, :ko, :de, :gs, :uc, :ep, :te, :ak, TRUE) RETURNING id
    """), d).scalar()
    denetim_yaz(db, yon, "koc_ekle", "egitim_koclari", kid, d["ad"])
    db.commit()
    return {"id": kid}


def _koc(db: Session, koc_id: int) -> dict:
    k = db.execute(text("SELECT * FROM egitim_koclari WHERE id = :k"), {"k": koc_id}).mappings().first()
    if not k:
        raise HTTPException(status_code=404, detail="Koç bulunamadı.")
    return dict(k)


@router.put("/koc/{koc_id}")
def koc_duzenle(koc_id: int, istek: KocIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    _koc(db, koc_id)
    d = _degerler(db, istek)
    db.execute(text("""
        UPDATE egitim_koclari SET ad_soyad = :ad, unvan = :un, hakkinda = :ha, alanlar = :al, konular = :ko,
               deneyim_yil = :de, gorusme_sekli = :gs, ucret_bilgisi = :uc, eposta = :ep, telefon = :te, aktif = :ak
         WHERE id = :id
    """), {**d, "id": koc_id})
    denetim_yaz(db, yon, "koc_duzenle", "egitim_koclari", koc_id, d["ad"])
    db.commit()
    return {"tamam": True}


class OkulAtama(BaseModel):
    okul_id: int
    durum: str = "aktif"
    notlar: str | None = Field(default=None, max_length=300)


class OkulAtamaIstek(BaseModel):
    okullar: list[OkulAtama] = Field(default_factory=list, max_length=500)


@router.put("/koc/{koc_id}/okullar")
def koc_okullari(koc_id: int, istek: OkulAtamaIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    """Koçun çalıştığı okullar (listede olmayan okullardan kaldırılır)."""
    k = _koc(db, koc_id)
    gecerli = {r[0] for r in db.execute(text("SELECT id FROM okullar")).all()}
    yeni = {}
    for a in istek.okullar:
        if a.okul_id not in gecerli:
            raise HTTPException(status_code=400, detail="Geçersiz okul.")
        if a.durum not in OKUL_DURUM:
            raise HTTPException(status_code=400, detail="Geçersiz durum.")
        yeni[a.okul_id] = a
    db.execute(text("DELETE FROM koc_okullari WHERE koc_id = :k"), {"k": koc_id})
    for a in yeni.values():
        db.execute(text("""INSERT INTO koc_okullari (koc_id, okul_id, durum, notlar, guncelleme_zamani)
                           VALUES (:k, :o, :d, :n, now())"""),
                   {"k": koc_id, "o": a.okul_id, "d": a.durum, "n": (a.notlar or "").strip() or None})
    ozet = ", ".join(f"{OKUL_DURUM[a.durum].lower()}: {sum(1 for x in yeni.values() if x.durum == a.durum)}" for a in
                     {x.durum: x for x in yeni.values()}.values())
    denetim_yaz(db, yon, "koc_okullari", "egitim_koclari", koc_id, f"{k['ad_soyad']} — {len(yeni)} okul ({ozet or 'yok'})")
    db.commit()
    return {"okullar": _okul_atamalari(db).get(koc_id, [])}


@router.delete("/koc/{koc_id}", status_code=204)
def koc_sil(koc_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    k = _koc(db, koc_id)
    acik = db.execute(text("SELECT COUNT(*) FROM koc_gorusme_talepleri WHERE koc_id = :k AND durum IN ('beklemede','onaylandi')"),
                      {"k": koc_id}).scalar()
    if acik:
        raise HTTPException(status_code=400, detail=f"Bu koçun {acik} açık talebi var. Önce talepleri sonuçlandırın ya da koçu pasif yapın.")
    db.execute(text("DELETE FROM egitim_koclari WHERE id = :k"), {"k": koc_id})
    denetim_yaz(db, yon, "koc_sil", "egitim_koclari", koc_id, k["ad_soyad"])
    db.commit()


@router.get("/koc-talepleri")
def talepleri_listele(okul_id: int | None = None, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    satirlar = db.execute(text("""
        SELECT t.*, k.ad_soyad AS koc_ad, k.eposta AS koc_eposta, k.telefon AS koc_telefon, s.ad AS okul_ad
          FROM koc_gorusme_talepleri t JOIN egitim_koclari k ON k.id = t.koc_id LEFT JOIN okullar s ON s.id = t.okul_id
    """ + (" WHERE t.okul_id = :ok" if okul_id else "") + " ORDER BY (t.durum = 'beklemede') DESC, t.olusturulma_zamani DESC LIMIT 500"),
        {"ok": okul_id} if okul_id else {}).mappings().all()
    ogr = {x.id: x for x in db.query(Ogrenci).filter(Ogrenci.id.in_([r["ogrenci_id"] for r in satirlar] or [None])).all()}
    sonuc = []
    for r in satirlar:
        o = ogr.get(r["ogrenci_id"])
        sonuc.append({**{k: v for k, v in dict(r).items() if k != "ogrenci_id"}, "ogrenci_id": str(r["ogrenci_id"]),
                      "ogrenci_ad": o.ad_soyad if o else "?", "ogrenci_sinif": _sinif_metni(o) if o else "",
                      "ogrenci_eposta": o.email if o else None, "durum_metni": DURUMLAR.get(r["durum"], r["durum"])})
    return {"talepler": sonuc, "durumlar": [{"kod": k, "ad": v} for k, v in DURUMLAR.items() if k != "iptal"],
            "bekleyen": sum(1 for x in sonuc if x["durum"] == "beklemede")}


class TalepGuncelleIstek(BaseModel):
    durum: str
    randevu_zamani: datetime | None = None
    ogrenciye_not: str | None = Field(default=None, max_length=500)
    ic_not: str | None = Field(default=None, max_length=1000)


@router.put("/koc-talep/{talep_id}")
def talep_guncelle(talep_id: int, istek: TalepGuncelleIstek, db: Session = Depends(get_db),
                   yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    t = db.execute(text("SELECT okul_id, durum FROM koc_gorusme_talepleri WHERE id = :t"), {"t": talep_id}).mappings().first()
    if not t:
        raise HTTPException(status_code=404, detail="Talep bulunamadı.")
    if istek.durum not in DURUMLAR or istek.durum == "iptal":
        raise HTTPException(status_code=400, detail="Geçersiz durum.")
    if t["durum"] == "iptal":
        raise HTTPException(status_code=400, detail="Öğrenci bu talebi iptal etti.")
    db.execute(text("""
        UPDATE koc_gorusme_talepleri SET durum = :d, randevu_zamani = :r, ogrenciye_not = :n, ic_not = :i, guncelleme_zamani = :z
         WHERE id = :t
    """), {"t": talep_id, "d": istek.durum, "r": istek.randevu_zamani, "n": (istek.ogrenciye_not or "").strip() or None,
           "i": (istek.ic_not or "").strip() or None, "z": _simdi()})
    denetim_yaz(db, yon, "koc_talep_guncelle", "koc_gorusme_talepleri", talep_id, DURUMLAR[istek.durum], t["okul_id"])
    db.commit()
    return {"tamam": True}
