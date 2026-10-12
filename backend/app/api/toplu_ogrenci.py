# -*- coding: utf-8 -*-
"""
[2026-10-12] Toplu öğrenci işlemleri (okul yetkilisi + süper admin; okul yetkilisi yalnızca kendi okulu).

Yeni eğitim yılı — sınıf atlatma
  GET  /yonetim/okul/{okul_id}/sinif-atlat?haric=<id,id>     önizleme: hangi sınıftan kaç öğrenci nereye geçecek
  POST /yonetim/okul/{okul_id}/sinif-atlat                    {siniflar: ["9. Sınıf", …], haric: [id…], onay: true}
        9 → 10, 10 → 11, 11 → 12, 12 → Mezun. Şube harfi korunur (11-A → 12-A). "Aday", "Mezun" ve sınıfı
        tanımsız öğrenciler değişmez. Test hesapları dahil edilmez. haric: sınıf tekrarı yapacak öğrenciler.
        Her öğrencinin eski sınıfı toplu_islemler.veri'ye yazılır.
  POST /yonetim/toplu-islem/{islem_id}/geri-al                30 gün içinde; yalnızca o işlemden sonra sınıfı
        elle değiştirilmemiş öğrenciler eski sınıfına döner.

Değerlendirmeyi sıfırlama
  POST /yonetim/ogrenciler/degerlendirme-sifirla              {idler: [...]}
        Öğrencinin SON değerlendirme turu (devam eden ya da tamamlanmış) silinir: cevaplar, özellik puanları, bölüm
        uyumları, K5 dal sonuçları, güvenlik kayıtları ve o tura bağlı koçluk adımları. Önceki turlar, hesap, şifre,
        hedef bölüm, denemeler, çalışma kayıtları, portfolyo, rehberlik notları kalır. Öğrenci değerlendirmeye
        bekleme süresi olmadan baştan başlar (ogrenciler.yeni_tur_izni).
"""
from __future__ import annotations

import re
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_yonetimi import _ogrenci_kapsami, _okul_kapsami, sinif_ayir
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz, olay_yaz, simdi, yapan_etiketi
from app.models import AdminKullanici, Ogrenci

router = APIRouter(prefix="/yonetim", tags=["Yönetim — Toplu öğrenci işlemleri"])

SIRA = ["9. Sınıf", "10. Sınıf", "11. Sınıf", "12. Sınıf"]
SONRAKI = {"9. Sınıf": "10. Sınıf", "10. Sınıf": "11. Sınıf", "11. Sınıf": "12. Sınıf", "12. Sınıf": "Mezun"}
GERI_ALMA_GUN = 30
TEKRAR_UYARI_GUN = 180


def _okul_ogrencileri(db: Session, okul_id: int) -> list[Ogrenci]:
    q = db.query(Ogrenci).filter(Ogrenci.okul_id == okul_id)
    if hasattr(Ogrenci, "test_hesabi"):
        q = q.filter(Ogrenci.test_hesabi.is_(False))
    return q.all()


def _son_islem(db: Session, okul_id: int) -> dict | None:
    r = db.execute(text("""SELECT id, zaman, sayi, yapan_ad, geri_alindi_zamani FROM toplu_islemler
                           WHERE okul_id = :o AND tur = 'sinif_atlat' ORDER BY zaman DESC LIMIT 1"""), {"o": okul_id}).first()
    if not r:
        return None
    zaman = r.zaman
    return {"id": r.id, "zaman": zaman, "sayi": r.sayi, "yapan": r.yapan_ad,
            "geri_alindi": r.geri_alindi_zamani is not None,
            "geri_alinabilir": r.geri_alindi_zamani is None and simdi() - zaman <= timedelta(days=GERI_ALMA_GUN)}


def _haric_coz(haric: str | list | None) -> set[str]:
    if not haric:
        return set()
    if isinstance(haric, str):
        haric = [x for x in re.split(r"[,\s]+", haric) if x]
    return {str(x) for x in haric}


def _sinif(o: Ogrenci) -> str | None:
    """Kayıtlı sınıf "11", "11-A", "11. sınıf" gibi yazılmış olabilir: "11. Sınıf" biçimine getirilir."""
    try:
        return sinif_ayir(o.sinif, None)[0] if o.sinif else None
    except Exception:
        return o.sinif


def _plan(ogrenciler: list[Ogrenci], siniflar: set[str], haric: set[str]) -> tuple[list[dict], list[Ogrenci]]:
    sayac = {s: {"eski": s, "yeni": SONRAKI[s], "sayi": 0, "kalan": 0, "secili": s in siniflar} for s in SIRA}
    gecenler = []
    for o in ogrenciler:
        s = _sinif(o)
        if s not in SONRAKI:
            continue
        if str(o.id) in haric:
            sayac[s]["kalan"] += 1
            continue
        sayac[s]["sayi"] += 1
        if s in siniflar:
            gecenler.append(o)
    return [sayac[s] for s in SIRA], gecenler


@router.get("/okul/{okul_id}/sinif-atlat")
def sinif_atlat_onizle(okul_id: int, haric: str | None = Query(None), db: Session = Depends(get_db),
                       yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    ogr = _okul_ogrencileri(db, okul_id)
    gecisler, _ = _plan(ogr, set(SIRA), _haric_coz(haric))
    degismeyen = {}
    for o in ogr:
        if _sinif(o) not in SONRAKI:
            k = _sinif(o) or "Sınıfı belirtilmemiş"
            degismeyen[k] = degismeyen.get(k, 0) + 1
    son = _son_islem(db, okul_id)
    uyari = None
    if son and not son["geri_alindi"] and simdi() - son["zaman"] < timedelta(days=TEKRAR_UYARI_GUN):
        uyari = (f"Bu okulda {son['zaman']:%d.%m.%Y} tarihinde zaten sınıf atlatma yapıldı ({son['sayi']} öğrenci). "
                 "Aynı yıl içinde ikinci kez yapılırsa öğrenciler iki sınıf ilerler.")
    return {"gecisler": gecisler, "degismeyen": [{"sinif": k, "sayi": v} for k, v in sorted(degismeyen.items())],
            "son_islem": son, "uyari": uyari, "geri_alma_gun": GERI_ALMA_GUN}


class SinifAtlatIstek(BaseModel):
    siniflar: list[str] = Field(default_factory=lambda: SIRA[:])
    haric: list[str] = Field(default_factory=list)
    onay: bool = False


@router.post("/okul/{okul_id}/sinif-atlat")
def sinif_atlat(okul_id: int, istek: SinifAtlatIstek, db: Session = Depends(get_db),
                yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    okul = _okul_kapsami(db, yon, okul_id)
    if not okul:
        raise HTTPException(status_code=400, detail="Sınıf atlatma bir okul için yapılır.")
    if not istek.onay:
        raise HTTPException(status_code=400, detail="İşlemi onaylamanız gerekiyor.")
    siniflar = {s for s in istek.siniflar if s in SONRAKI}
    if not siniflar:
        raise HTTPException(status_code=400, detail="Sınıf atlatılacak en az bir sınıf seçin.")
    _, gecenler = _plan(_okul_ogrencileri(db, okul_id), siniflar, _haric_coz(istek.haric))
    if not gecenler:
        raise HTTPException(status_code=400, detail="Seçilen sınıflarda sınıf atlatılacak öğrenci yok.")
    veri, yapan = [], yapan_etiketi(yon)
    for o in gecenler:
        eski, yeni = o.sinif, SONRAKI[_sinif(o)]
        veri.append({"id": str(o.id), "eski": eski, "yeni": yeni, "sube": o.sube})
        o.sinif = yeni
        if not o.sube:   # "9-A" gibi tek alanda yazılmış şube korunur
            o.sube = sinif_ayir(eski, None)[1]
        olay_yaz(db, o.id, "sinif_atladi", f"{eski} → {yeni}", yapan)
    islem_id = db.execute(text("""INSERT INTO toplu_islemler (okul_id, tur, yapan_id, yapan_ad, sayi, veri)
                                  VALUES (:o, 'sinif_atlat', :y, :ya, :n, CAST(:v AS JSONB)) RETURNING id"""),
                          {"o": okul_id, "y": yon.id, "ya": yon.ad_soyad, "n": len(veri),
                           "v": __import__("json").dumps(veri, ensure_ascii=False)}).scalar()
    ozet = ", ".join(f"{s} → {SONRAKI[s]}: {sum(1 for x in veri if x['yeni'] == SONRAKI[s])}" for s in SIRA if s in siniflar)
    denetim_yaz(db, yon, "sinif_atlat", "toplu_islemler", islem_id,
                f"{len(veri)} öğrenci ({ozet}); {len(_haric_coz(istek.haric))} öğrenci sınıfında bırakıldı", okul_id)
    db.commit()
    return {"islem_id": islem_id, "sayi": len(veri), "geri_alma_gun": GERI_ALMA_GUN}


@router.post("/toplu-islem/{islem_id}/geri-al")
def toplu_islem_geri_al(islem_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = db.execute(text("SELECT id, okul_id, tur, zaman, veri, geri_alindi_zamani FROM toplu_islemler WHERE id = :i FOR UPDATE"),
                   {"i": islem_id}).first()
    if not r or r.tur != "sinif_atlat":
        raise HTTPException(status_code=404, detail="İşlem bulunamadı.")
    _okul_kapsami(db, yon, r.okul_id)
    if r.geri_alindi_zamani is not None:
        raise HTTPException(status_code=400, detail="Bu işlem zaten geri alındı.")
    if simdi() - r.zaman > timedelta(days=GERI_ALMA_GUN):
        raise HTTPException(status_code=400, detail=f"Sınıf atlatma yalnızca {GERI_ALMA_GUN} gün içinde geri alınabilir.")
    sonraki = db.execute(text("""SELECT 1 FROM toplu_islemler WHERE okul_id = :o AND tur = 'sinif_atlat' AND zaman > :z
                                 AND geri_alindi_zamani IS NULL LIMIT 1"""), {"o": r.okul_id, "z": r.zaman}).first()
    if sonraki:
        raise HTTPException(status_code=400, detail="Bundan sonra yapılmış bir sınıf atlatma var; önce onu geri alın.")
    yapan, donen, atlanan = yapan_etiketi(yon), 0, 0
    for k in r.veri or []:
        o = db.get(Ogrenci, k["id"])
        if o is None or o.okul_id != r.okul_id or o.sinif != k["yeni"]:
            atlanan += 1   # silinmiş, okul değiştirmiş ya da sınıfı sonradan elle değiştirilmiş
            continue
        o.sinif, o.sube = k["eski"], k.get("sube")
        olay_yaz(db, o.id, "sinif_atlatma_geri_alindi", f"{k['yeni']} → {k['eski']}", yapan)
        donen += 1
    db.execute(text("UPDATE toplu_islemler SET geri_alindi_zamani = now() WHERE id = :i"), {"i": islem_id})
    denetim_yaz(db, yon, "sinif_atlat_geri_al", "toplu_islemler", islem_id,
                f"{donen} öğrenci eski sınıfına döndü" + (f", {atlanan} öğrenci atlandı" if atlanan else ""), r.okul_id)
    db.commit()
    return {"donen": donen, "atlanan": atlanan}


class IdlerIstek(BaseModel):
    idler: list[str] = Field(default_factory=list, max_length=5000)


@router.post("/ogrenciler/degerlendirme-sifirla")
def degerlendirme_sifirla(istek: IdlerIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    if not istek.idler:
        raise HTTPException(status_code=400, detail="Öğrenci seçilmedi.")
    ogrenciler = [_ogrenci_kapsami(db, yon, i) for i in istek.idler]
    yapan, sifirlanan, turu_yok, okullar = yapan_etiketi(yon), [], 0, set()
    for o in ogrenciler:
        tur = db.execute(text("""SELECT id, tur_no, durum FROM ogrenci_degerlendirme_turu WHERE ogrenci_id = :o
                                 ORDER BY tur_no DESC LIMIT 1"""), {"o": o.id}).first()
        if not tur:
            turu_yok += 1
            continue
        # Bağlı tablolar ON DELETE CASCADE (cevaplar, puanlar, uyumlar, K5, güvenlik, koçluk oturumları)
        db.execute(text("DELETE FROM ogrenci_degerlendirme_turu WHERE id = :t"), {"t": tur.id})
        o.yeni_tur_izni = simdi()
        olay_yaz(db, o.id, "degerlendirme_sifirlandi",
                 f"{tur.tur_no}. tur ({'tamamlanmış' if tur.durum == 'tamamlandi' else 'devam eden'}) silindi; öğrenci baştan başlayacak", yapan)
        sifirlanan.append(o)
        okullar.add(o.okul_id)
    if sifirlanan:
        denetim_yaz(db, yon, "degerlendirme_sifirla", "ogrenciler", ",".join(str(o.id) for o in sifirlanan[:5]),
                    f"{len(sifirlanan)} öğrenci: " + ", ".join(o.ad_soyad for o in sifirlanan[:10]) + ("…" if len(sifirlanan) > 10 else ""),
                    okullar.pop() if len(okullar) == 1 else None)
    db.commit()
    return {"sifirlanan": len(sifirlanan), "degerlendirmesi_olmayan": turu_yok}


# ----------------------------------------------------------------------------- [2026-10-12] Yeniden değerlendirme
@router.get("/ogrenci/{ogrenci_id}/degerlendirme-durumu")
def ogrenci_degerlendirme_durumu(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.core.guvenlik_servisi import katman_guven_durumlari
    from app.core.katman_servisi import degerlendirme_durumu
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    d = degerlendirme_durumu(db, o)
    tur = db.execute(text("SELECT id FROM ogrenci_degerlendirme_turu WHERE ogrenci_id = :o ORDER BY tur_no DESC LIMIT 1"),
                     {"o": o.id}).first()
    katmanlar = []
    if tur:
        from app.models import OgrenciDegerlendirmeTuru
        t = db.get(OgrenciDegerlendirmeTuru, tur.id)
        biten = {k for (k,) in db.execute(text("""SELECT k.kod FROM ogrenci_katman_oturumlari o JOIN katmanlar k ON k.id = o.katman_id
                                                   WHERE o.tur_id = :t AND o.durum = 'tamamlandi'"""), {"t": tur.id})}
        sorunlu = {k["kod"] for k in d.get("sorunlu_katmanlar") or []}
        katmanlar = [{**{k: v for k, v in x.items() if k != "katman_id"}, "tamamlandi": x["kod"] in biten,
                      "sorunlu": x["kod"] in sorunlu}   # öğrenciye gösterilen sorunlu bölümle aynı olsun
                     for x in katman_guven_durumlari(db, o, t).values()]
    return {**d, "katmanlar": katmanlar}


class KatmanTekrarIstek(BaseModel):
    kod: str


@router.post("/ogrenci/{ogrenci_id}/katman-tekrar")
def katman_tekrarlat(ogrenci_id: str, istek: KatmanTekrarIstek, db: Session = Depends(get_db),
                     yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    """Okul yetkilisi bir öğrencinin son turundaki tek bir katmanı tekrarlatır (diğer katmanlar ve sonuçlar kalır)."""
    from app.core.katman_servisi import katmani_tekrara_ac
    from app.models import Katman, OgrenciDegerlendirmeTuru
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    katman = db.query(Katman).filter(Katman.kod == istek.kod.upper(), Katman.kosullu_mu.is_(False)).first()
    if not katman:
        raise HTTPException(status_code=400, detail="Bu bölüm tekrarlatılamaz.")
    tur = (db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id)
           .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).first())
    if tur is None:
        raise HTTPException(status_code=400, detail="Öğrencinin henüz değerlendirmesi yok.")
    katmani_tekrara_ac(db, o, tur, katman)
    olay_yaz(db, o.id, "katman_tekrar", f"{katman.kod} okul yetkilisi tarafından tekrar açıldı ({tur.tur_no}. tur)", yapan_etiketi(yon))
    denetim_yaz(db, yon, "katman_tekrarlat", "ogrenciler", o.id, f"{o.ad_soyad}: {katman.kod} ({tur.tur_no}. tur)", o.okul_id)
    db.commit()
    return {"tamam": True}


@router.post("/ogrenciler/yeniden-degerlendirme")
def yeniden_degerlendirme_ac(istek: IdlerIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    """Seçili öğrenciler bekleme süresini beklemeden yeni bir değerlendirme turuna başlayabilir. Önceki sonuçlar silinmez,
    geçmişte kalır (gelişim karşılaştırması için)."""
    if not istek.idler:
        raise HTTPException(status_code=400, detail="Öğrenci seçilmedi.")
    ogrenciler = [_ogrenci_kapsami(db, yon, i) for i in istek.idler]
    yapan, acilan, devam, yok, okullar = yapan_etiketi(yon), [], 0, 0, set()
    for o in ogrenciler:
        son = db.execute(text("SELECT durum FROM ogrenci_degerlendirme_turu WHERE ogrenci_id = :o ORDER BY tur_no DESC LIMIT 1"),
                         {"o": o.id}).first()
        if son is None:
            yok += 1
            continue
        if son.durum != "tamamlandi":
            devam += 1   # zaten devam eden bir değerlendirmesi var
            continue
        o.yeni_tur_izni = simdi()
        olay_yaz(db, o.id, "yeniden_degerlendirme_izni", "Bekleme süresi olmadan yeni değerlendirme açıldı", yapan)
        acilan.append(o)
        okullar.add(o.okul_id)
    if acilan:
        denetim_yaz(db, yon, "yeniden_degerlendirme_ac", "ogrenciler", ",".join(str(o.id) for o in acilan[:5]),
                    f"{len(acilan)} öğrenci: " + ", ".join(o.ad_soyad for o in acilan[:10]) + ("…" if len(acilan) > 10 else ""),
                    okullar.pop() if len(okullar) == 1 else None)
    db.commit()
    return {"acilan": len(acilan), "devam_eden": devam, "degerlendirmesi_olmayan": yok}
