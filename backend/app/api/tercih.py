# -*- coding: utf-8 -*-
"""
[2026-10-10] Tercih dönemi (modül: tercih) ve mezun takibi (modül: mezun_takibi).

Tercih — öğrenci (12. sınıf / mezun):
  GET  /ogrenci/tercih                    — liste, sıralama bilgisi, uyarılar, bölümler (uyum %)
  PUT  /ogrenci/tercih                    — {puan_turu, siralama, puan, tercihler: [...]} (en çok 24)
  POST /ogrenci/tercih/gonder             — rehbere incelemeye gönder
  POST /ogrenci/yerlesme                  — "Sonucumu bildir": yerleşme / durum (mezun kaydına düşer)
Tercih — yönetim:
  GET  /yonetim/okul/{okul_id}/tercihler          — 12. sınıf + mezun öğrencilerin tercih durumu
  GET  /yonetim/ogrenci/{ogrenci_id}/tercih        — öğrencinin listesi
  POST /yonetim/ogrenci/{ogrenci_id}/tercih-karar  — {karar: onayla|duzeltme, notu}
Mezun takibi — yönetim:
  GET  /yonetim/okul/{okul_id}/mezunlar            — kayıtlar + yıl bazında oranlar
  POST /yonetim/okul/{okul_id}/mezunlar            — elle kayıt
  PUT/DELETE /yonetim/mezun/{mezun_id}

Risk sınıflaması (yalnızca yön gösterir): öğrencinin başarı sırası ÷ programın geçen yıl taban sırası
  ≤ 0,85 güvenli · ≤ 1,10 dengeli · > 1,10 riskli. Taban sıralaması yıldan yıla değişir; kesin tahmin değildir.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.api.okul_yonetimi import _ogrenci_kapsami, _okul_kapsami, _sinif_metni
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Tercih"])
yonetim_router = APIRouter(prefix="/yonetim", tags=["Tercih"])
mezun_router = APIRouter(prefix="/yonetim", tags=["Mezun takibi"])

EN_FAZLA = 24
TURLER = {"devlet": "Devlet", "vakif": "Vakıf", "kktc": "KKTC", "yurtdisi": "Yurt dışı"}
BURSLAR = ["Ücretsiz", "Tam burslu", "%75 indirimli", "%50 indirimli", "%25 indirimli", "Ücretli", "İkinci öğretim"]
DURUMLAR = {"taslak": "Hazırlanıyor", "incelemede": "Rehber incelemesinde", "onaylandi": "Rehber onayladı", "duzeltme": "Düzeltme istendi"}
MEZUN_DURUM = {"yerlesti": "Yerleşti", "yerlesemedi": "Yerleşemedi", "tekrar": "Sınava tekrar hazırlanıyor",
               "yurtdisi": "Yurt dışında okuyor", "calisiyor": "Çalışıyor", "diger": "Diğer"}
PUAN_TURLERI = ["SAY", "EA", "SÖZ", "DİL", "TYT"]


def risk(ogrenci_sira: int | None, taban: int | None) -> str | None:
    if not ogrenci_sira or not taban:
        return None
    oran = ogrenci_sira / taban
    return "guvenli" if oran <= 0.85 else ("dengeli" if oran <= 1.10 else "riskli")


def uyumlar(db: Session, ogrenci_id) -> dict:
    """{bolum_id: (uyum, öneri sırası)} — son tamamlanan değerlendirme turundan."""
    tur = db.execute(text("SELECT id FROM ogrenci_degerlendirme_turu WHERE ogrenci_id = :o AND durum = 'tamamlandi' ORDER BY tur_no DESC LIMIT 1"),
                     {"o": ogrenci_id}).scalar()
    if not tur:
        return {}
    rows = db.execute(text("SELECT bolum_id, toplam_uyum FROM ogrenci_bolum_uyum_skorlari WHERE tur_id = :t ORDER BY toplam_uyum DESC"), {"t": tur}).all()
    return {r.bolum_id: (round(float(r.toplam_uyum)), i) for i, r in enumerate(rows, 1)}


def _hedef(db: Session, ogrenci_id):
    return db.execute(text("SELECT b.id, b.ad FROM ogrenci_hedef_bolum h JOIN bolumler b ON b.id = h.bolum_id WHERE h.ogrenci_id = :o AND h.aktif_mi"),
                      {"o": ogrenci_id}).first()


def tercih_verisi(db: Session, o: Ogrenci, bolumler: bool = True) -> dict:
    l = db.execute(text("SELECT * FROM tercih_listesi WHERE ogrenci_id = :o"), {"o": o.id}).mappings().first()
    l = dict(l) if l else {"puan_turu": None, "siralama": None, "puan": None, "durum": "taslak", "rehber_notu": None, "rehber": None}
    uy = uyumlar(db, o.id)
    hedef = _hedef(db, o.id)
    satir = []
    for r in db.execute(text("SELECT * FROM tercihler WHERE ogrenci_id = :o ORDER BY sira"), {"o": o.id}).mappings().all():
        u = uy.get(r["bolum_id"]) if r["bolum_id"] else None
        satir.append({**dict(r), "risk": risk(l["siralama"], r["taban_siralama"]), "uyum": u[0] if u else None, "oneri_sirasi": u[1] if u else None,
                      "hedef": bool(hedef and r["bolum_id"] == hedef.id), "tur_ad": TURLER.get(r["tur"], r["tur"])})
    say = {k: sum(1 for t in satir if t["risk"] == k) for k in ("guvenli", "dengeli", "riskli")}
    uyari = []
    if satir and l["siralama"]:
        if say["guvenli"] == 0:
            uyari.append("Listende hiç güvenli tercih yok; yerleşememe riskine karşı sonlara birkaç güvenli program ekle.")
        ilk = [t for t in satir[:3] if t["risk"] == "guvenli"]
        if len(ilk) == min(3, len(satir)) and say["riskli"] == 0 and len(satir) >= 3:
            uyari.append("İlk sıralarda yalnızca güvenli tercihler var; hayalindeki programları daha üst sıralara koymayı düşün.")
        sira_bozuk = any(satir[i]["risk"] == "riskli" and any(t["risk"] == "guvenli" for t in satir[:i]) for i in range(len(satir)))
        if sira_bozuk:
            uyari.append("Güvenli bir tercihin, riskli bir tercihin üstünde. Yerleştirme sırana göre yapılır: önce en çok istediklerin, en sona güvenliler.")
    if satir and not l["siralama"]:
        uyari.append("Başarı sıranı girersen her tercihin güvenli / dengeli / riskli durumunu görürsün.")
    eksik = sum(1 for t in satir if not t["taban_siralama"])
    if eksik:
        uyari.append(f"{eksik} tercihte geçen yılın taban sıralaması yok; YÖK Atlas'tan bakıp yazarsan risk hesaplanır.")
    if satir and uy and not any(t["oneri_sirasi"] for t in satir):
        uyari.append(f"Listendeki bölümlerin hiçbiri Filizyol'un sana önerdiği {len(uy)} bölüm arasında değil; Bölümler sayfasındaki önerilere bir kez daha göz at.")
    v = {"liste": {**l, "puan": float(l["puan"]) if l.get("puan") is not None else None, "durum_adi": DURUMLAR.get(l["durum"], l["durum"])},
         "tercihler": satir, "sayilar": {**say, "toplam": len(satir), "en_fazla": EN_FAZLA}, "uyarilar": uyari,
         "hedef": {"id": hedef.id, "ad": hedef.ad} if hedef else None,
         "secenekler": {"turler": TURLER, "burslar": BURSLAR, "puan_turleri": PUAN_TURLERI, "mezun_durumlari": MEZUN_DURUM}}
    if bolumler:
        tum = db.execute(text("SELECT id, ad FROM bolumler WHERE durum = 'yayinda' ORDER BY ad")).all()
        v["bolumler"] = sorted([{"id": b.id, "ad": b.ad, "uyum": uy.get(b.id, (None, None))[0], "sira": uy.get(b.id, (None, None))[1]} for b in tum],
                               key=lambda b: (b["sira"] or 9999, b["ad"]))
    yer = db.execute(text("SELECT * FROM mezun_yerlesmeleri WHERE ogrenci_id = :o ORDER BY yil DESC LIMIT 1"), {"o": o.id}).mappings().first()
    v["yerlesme"] = dict(yer) if yer else None
    return v


def _uygun(o: Ogrenci):
    if o.sinif not in ("12. Sınıf", "Mezun"):
        raise HTTPException(400, "Tercih listesi 12. sınıf ve mezun öğrenciler içindir.")


# ============================================================================= öğrenci
@ogrenci_router.get("/tercih")
def tercihim(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return {**tercih_verisi(db, o), "uygun": o.sinif in ("12. Sınıf", "Mezun")}


class TercihSatir(BaseModel):
    universite: str = Field(min_length=2, max_length=140)
    bolum_ad: str = Field(min_length=2, max_length=160)
    bolum_id: int | None = None
    tur: str = "devlet"
    burs: str | None = None
    sehir: str | None = Field(default=None, max_length=40)
    taban_siralama: int | None = Field(default=None, ge=1, le=3_000_000)
    notlar: str | None = Field(default=None, max_length=200)


class TercihIstek(BaseModel):
    puan_turu: str | None = None
    siralama: int | None = Field(default=None, ge=1, le=3_000_000)
    puan: float | None = Field(default=None, ge=0, le=600)
    tercihler: list[TercihSatir] = Field(default_factory=list)


@ogrenci_router.put("/tercih")
def tercih_kaydet(istek: TercihIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    _uygun(o)
    if len(istek.tercihler) > EN_FAZLA:
        raise HTTPException(400, f"En fazla {EN_FAZLA} tercih yapılabilir.")
    if istek.puan_turu and istek.puan_turu not in PUAN_TURLERI:
        raise HTTPException(400, "Geçersiz puan türü.")
    mevcut = db.execute(text("SELECT durum FROM tercih_listesi WHERE ogrenci_id = :o"), {"o": o.id}).scalar()
    db.execute(text("""
        INSERT INTO tercih_listesi (ogrenci_id, puan_turu, siralama, puan, durum, guncelleme_zamani) VALUES (:o, :pt, :s, :p, 'taslak', now())
        ON CONFLICT (ogrenci_id) DO UPDATE SET puan_turu = EXCLUDED.puan_turu, siralama = EXCLUDED.siralama, puan = EXCLUDED.puan,
            durum = CASE WHEN tercih_listesi.durum = 'onaylandi' THEN 'taslak' ELSE tercih_listesi.durum END, guncelleme_zamani = now()
    """), {"o": o.id, "pt": istek.puan_turu, "s": istek.siralama, "p": istek.puan})
    db.execute(text("DELETE FROM tercihler WHERE ogrenci_id = :o"), {"o": o.id})
    gecerli = {r[0] for r in db.execute(text("SELECT id FROM bolumler")).all()}
    for i, t in enumerate(istek.tercihler, 1):
        db.execute(text("""
            INSERT INTO tercihler (ogrenci_id, sira, universite, bolum_ad, bolum_id, tur, burs, sehir, taban_siralama, notlar)
            VALUES (:o, :s, :u, :b, :bi, :t, :bu, :se, :ts, :n)
        """), {"o": o.id, "s": i, "u": t.universite.strip(), "b": t.bolum_ad.strip(), "bi": t.bolum_id if t.bolum_id in gecerli else None,
               "t": t.tur if t.tur in TURLER else "devlet", "bu": t.burs if t.burs in BURSLAR else None, "se": (t.sehir or "").strip() or None,
               "ts": t.taban_siralama, "n": (t.notlar or "").strip() or None})
    db.commit()
    v = tercih_verisi(db, o)
    v["onay_dustu"] = mevcut == "onaylandi"
    return v


@ogrenci_router.post("/tercih/gonder")
def tercih_gonder(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    _uygun(o)
    n = db.execute(text("SELECT count(*) FROM tercihler WHERE ogrenci_id = :o"), {"o": o.id}).scalar() or 0
    if not n:
        raise HTTPException(400, "Önce listene tercih ekle.")
    db.execute(text("UPDATE tercih_listesi SET durum = 'incelemede', guncelleme_zamani = now() WHERE ogrenci_id = :o"), {"o": o.id})
    from app.core.bildirim import okul_yetkililerine
    if o.okul_id:
        okul_yetkililerine(db, o.okul_id, "tercih_inceleme", f"Tercih listesi incelemede: {o.ad_soyad}", f"{n} tercih · {_sinif_metni(o)}",
                           f"/admin/okul/{o.okul_id}?sekme=tercih")
    db.commit()
    return tercih_verisi(db, o)


class YerlesmeIstek(BaseModel):
    durum: str
    universite: str | None = Field(default=None, max_length=140)
    bolum_ad: str | None = Field(default=None, max_length=160)
    bolum_id: int | None = None
    burs: str | None = None
    siralama: int | None = Field(default=None, ge=1, le=3_000_000)
    yil: int | None = None


def _mezun_kaydi_yaz(db: Session, okul_id: int, ogrenci: Ogrenci | None, ad: str, istek: YerlesmeIstek, kaynak: str, mezun_id: int | None = None):
    if istek.durum not in MEZUN_DURUM:
        raise HTTPException(400, "Geçersiz durum.")
    yil = istek.yil or date.today().year
    if yil < 2000 or yil > date.today().year + 1:
        raise HTTPException(400, "Yıl geçersiz.")
    bolum_id = istek.bolum_id if istek.bolum_id and db.execute(text("SELECT 1 FROM bolumler WHERE id = :i"), {"i": istek.bolum_id}).first() else None
    hedef_ad, ayni, oneri = None, None, None
    if ogrenci is not None:
        h = _hedef(db, ogrenci.id)
        hedef_ad = h.ad if h else None
        ayni = (bolum_id == h.id) if (h and bolum_id) else None
        oneri = uyumlar(db, ogrenci.id).get(bolum_id, (None, None))[1] if bolum_id else None
    p = {"ok": okul_id, "o": ogrenci.id if ogrenci else None, "ad": ad, "y": yil, "d": istek.durum, "u": (istek.universite or "").strip() or None,
         "b": (istek.bolum_ad or "").strip() or None, "bi": bolum_id, "bu": istek.burs if istek.burs in BURSLAR else None, "s": istek.siralama,
         "h": hedef_ad, "a": ayni, "on": oneri, "k": kaynak}
    if mezun_id:
        db.execute(text("""UPDATE mezun_yerlesmeleri SET ad_soyad = :ad, yil = :y, durum = :d, universite = :u, bolum_ad = :b, bolum_id = :bi, burs = :bu,
                           siralama = :s, hedefle_ayni = coalesce(:a, hedefle_ayni), oneri_sirasi = coalesce(:on, oneri_sirasi) WHERE id = :i"""), {**p, "i": mezun_id})
        return mezun_id
    if ogrenci is not None:
        db.execute(text("DELETE FROM mezun_yerlesmeleri WHERE ogrenci_id = :o AND yil = :y"), p)
    return db.execute(text("""
        INSERT INTO mezun_yerlesmeleri (okul_id, ogrenci_id, ad_soyad, yil, durum, universite, bolum_ad, bolum_id, burs, siralama,
                                        hedef_bolum_ad, hedefle_ayni, oneri_sirasi, kaynak)
        VALUES (:ok, :o, :ad, :y, :d, :u, :b, :bi, :bu, :s, :h, :a, :on, :k) RETURNING id
    """), p).scalar()


@ogrenci_router.post("/yerlesme")
def yerlesme_bildir(istek: YerlesmeIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    _uygun(o)
    if not o.okul_id:
        raise HTTPException(400, "Okulu olmayan hesaplar için kaydedilmez.")
    _mezun_kaydi_yaz(db, o.okul_id, o, o.ad_soyad, istek, "ogrenci")
    db.commit()
    return tercih_verisi(db, o, bolumler=False)


# ============================================================================= yönetim — tercih
@yonetim_router.get("/okul/{okul_id}/tercihler")
def okul_tercihleri(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    ogr = [o for o in db.query(Ogrenci).filter(Ogrenci.okul_id == okul_id, Ogrenci.sinif.in_(["12. Sınıf", "Mezun"])).all()
           if not getattr(o, "test_hesabi", False)]
    sonuc = []
    for o in sorted(ogr, key=lambda x: (x.sinif or "", x.sube or "", x.ad_soyad.lower())):
        v = tercih_verisi(db, o, bolumler=False)
        sonuc.append({"ogrenci_id": str(o.id), "ad_soyad": o.ad_soyad, "sinif_metni": _sinif_metni(o), "durum": v["liste"]["durum"] if v["tercihler"] else None,
                      "durum_adi": v["liste"]["durum_adi"] if v["tercihler"] else "Liste yok", "sayilar": v["sayilar"], "uyari": len(v["uyarilar"]),
                      "siralama": v["liste"]["siralama"], "yerlesme": v["yerlesme"]["durum"] if v["yerlesme"] else None})
    return {"ogrenciler": sonuc, "ozet": {"toplam": len(sonuc), "liste_var": sum(1 for s in sonuc if s["durum"]),
                                          "incelemede": sum(1 for s in sonuc if s["durum"] == "incelemede"),
                                          "onaylandi": sum(1 for s in sonuc if s["durum"] == "onaylandi")}}


@yonetim_router.get("/ogrenci/{ogrenci_id}/tercih")
def ogrenci_tercihi(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    return {**tercih_verisi(db, o, bolumler=False), "ogrenci": {"ad_soyad": o.ad_soyad, "sinif_metni": _sinif_metni(o)}}


class KararIstek(BaseModel):
    karar: str = Field(pattern="^(onayla|duzeltme)$")
    notu: str | None = Field(default=None, max_length=1500)


@yonetim_router.post("/ogrenci/{ogrenci_id}/tercih-karar", status_code=204)
def tercih_karar(ogrenci_id: str, istek: KararIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    n = db.execute(text("UPDATE tercih_listesi SET durum = :d, rehber_notu = :n, rehber = :r, guncelleme_zamani = now() WHERE ogrenci_id = :o"),
                   {"d": "onaylandi" if istek.karar == "onayla" else "duzeltme", "n": (istek.notu or "").strip() or None, "r": yon.ad_soyad, "o": o.id}).rowcount
    if not n:
        raise HTTPException(400, "Öğrencinin tercih listesi yok.")
    from app.core.bildirim import bildir
    bildir(db, "ogrenci", [o.id], "tercih_karar", "Rehber öğretmenin tercih listeni onayladı ✓" if istek.karar == "onayla" else "Rehber öğretmenin tercih listende düzeltme önerdi",
           (istek.notu or "").strip()[:300] or None, "/tercih", o.okul_id, eposta=True)
    denetim_yaz(db, yon, f"tercih_{istek.karar}", "tercih_listesi", o.id, o.ad_soyad, o.okul_id)
    db.commit()


# ============================================================================= yönetim — mezun takibi
@mezun_router.get("/okul/{okul_id}/mezunlar")
def mezunlar(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    rows = [dict(r) for r in db.execute(text("SELECT * FROM mezun_yerlesmeleri WHERE okul_id = :o ORDER BY yil DESC, ad_soyad"), {"o": okul_id}).mappings().all()]
    yillar = {}
    for r in rows:
        y = yillar.setdefault(r["yil"], {"yil": r["yil"], "kayit": 0, "yerlesti": 0, "hedef_bilinen": 0, "hedefle_ayni": 0, "oneri_bilinen": 0, "ilk10": 0})
        y["kayit"] += 1
        if r["durum"] == "yerlesti":
            y["yerlesti"] += 1
            if r["hedefle_ayni"] is not None:
                y["hedef_bilinen"] += 1
                y["hedefle_ayni"] += bool(r["hedefle_ayni"])
            if r["ogrenci_id"] and r["bolum_id"]:
                y["oneri_bilinen"] += 1
                y["ilk10"] += bool(r["oneri_sirasi"] and r["oneri_sirasi"] <= 10)
    for r in rows:
        r["durum_adi"] = MEZUN_DURUM.get(r["durum"], r["durum"])
    return {"kayitlar": rows, "yillar": sorted(yillar.values(), key=lambda y: -y["yil"]),
            "secenekler": {"durumlar": MEZUN_DURUM, "burslar": BURSLAR},
            "bolumler": [{"id": b.id, "ad": b.ad} for b in db.execute(text("SELECT id, ad FROM bolumler WHERE durum = 'yayinda' ORDER BY ad")).all()]}


class MezunIstek(YerlesmeIstek):
    ad_soyad: str = Field(min_length=3, max_length=120)
    ogrenci_id: str | None = None


@mezun_router.post("/okul/{okul_id}/mezunlar", status_code=201)
def mezun_ekle(okul_id: int, istek: MezunIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    if _okul_kapsami(db, yon, okul_id) is None:
        raise HTTPException(400, "Okul seçin.")
    o = _ogrenci_kapsami(db, yon, istek.ogrenci_id) if istek.ogrenci_id else None
    yeni = _mezun_kaydi_yaz(db, okul_id, o, o.ad_soyad if o else istek.ad_soyad.strip(), istek, "okul")
    denetim_yaz(db, yon, "mezun_ekle", "mezun_yerlesmeleri", yeni, istek.ad_soyad, okul_id)
    db.commit()
    return {"id": yeni}


@mezun_router.put("/mezun/{mezun_id}", status_code=204)
def mezun_duzenle(mezun_id: int, istek: MezunIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = db.execute(text("SELECT okul_id, ogrenci_id FROM mezun_yerlesmeleri WHERE id = :i"), {"i": mezun_id}).first()
    if r is None:
        raise HTTPException(404, "Kayıt bulunamadı.")
    _okul_kapsami(db, yon, r.okul_id)
    o = db.get(Ogrenci, r.ogrenci_id) if r.ogrenci_id else None
    _mezun_kaydi_yaz(db, r.okul_id, o, o.ad_soyad if o else istek.ad_soyad.strip(), istek, "okul", mezun_id)
    denetim_yaz(db, yon, "mezun_duzenle", "mezun_yerlesmeleri", mezun_id, istek.ad_soyad, r.okul_id)
    db.commit()


@mezun_router.delete("/mezun/{mezun_id}", status_code=204)
def mezun_sil(mezun_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = db.execute(text("SELECT okul_id, ad_soyad FROM mezun_yerlesmeleri WHERE id = :i"), {"i": mezun_id}).first()
    if r is None:
        raise HTTPException(404, "Kayıt bulunamadı.")
    _okul_kapsami(db, yon, r.okul_id)
    db.execute(text("DELETE FROM mezun_yerlesmeleri WHERE id = :i"), {"i": mezun_id})
    denetim_yaz(db, yon, "mezun_sil", "mezun_yerlesmeleri", mezun_id, r.ad_soyad, r.okul_id)
    db.commit()
