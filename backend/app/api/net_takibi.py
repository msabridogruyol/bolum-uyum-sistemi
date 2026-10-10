# -*- coding: utf-8 -*-
"""
[2026-10-10] Net takibi: deneme sonuçları, konu takibi ve hedef programa göre net kıyası.

- Öğrenci TYT / AYT / YDT denemelerinin doğru-yanlış sayılarını girer; net = D − Y/4.
- Konu takibi: her dersin konuları için durum (başlamadı / çalışıyorum / bitti / tekrar).
- Hedef kıyası: YÖK Atlas Net Sihirbazı'ndan hedef bölümün programlarına GEÇEN YIL yerleşen SON öğrencinin
  netleri alınır (7 gün önbellek); öğrenci bir programı (üniversite) seçer, son denemelerinin ortalaması ders ders
  bu netlerle karşılaştırılır. Bu netler taban puanla yerleşen kişinindir ve OBP etkisini içerir; kesin hedef değil, yön göstericidir.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core.database import get_db
from app.core.sinav_yapisi import (
    KONU_DERSLERI, KONU_DURUMLARI, PUAN_TURU_AD, PUAN_TURU_KONU_DERSLERI, PUAN_TURU_TESTLERI, TESTLER, net_hesapla,
    puan_turu_normalize,
)
from app.models import Bolum, Ogrenci

router = APIRouter(prefix="/ogrenci/net", tags=["Öğrenci — Net takibi"])
_log = logging.getLogger(__name__)
NET_ONBELLEK_GUN = 7
MAKS_NET_SATIRI = 1500
KIYAS_DENEME_SAYISI = 3   # son 3 denemenin ortalaması


# ----------------------------------------------------------------------------- yardımcılar
def _hedef_bolum(db: Session, o: Ogrenci) -> Bolum | None:
    from app.core.koclugu_servisi import aktif_hedef_getir
    h = aktif_hedef_getir(db, o)
    return db.get(Bolum, h.bolum_id) if h else None


def _net_hedefi(db: Session, o: Ogrenci) -> dict | None:
    r = db.execute(text("SELECT veri FROM ogrenci_net_hedefi WHERE ogrenci_id = :o"), {"o": o.id}).first()
    return r[0] if r else None


def _puan_turu(db: Session, o: Ogrenci) -> str:
    h = _net_hedefi(db, o)
    if h and puan_turu_normalize(h.get("puan_turu")):
        return puan_turu_normalize(h.get("puan_turu"))
    b = _hedef_bolum(db, o)
    return puan_turu_normalize(b.osym_puan_turu if b else None) or "SAY"


def _test_listesi(kodlar: list[str]) -> list[dict]:
    return [{"kod": k, "oturum": TESTLER[k][0], "ad": TESTLER[k][1], "soru": TESTLER[k][2]} for k in kodlar]


# ----------------------------------------------------------------------------- yapı
@router.get("/yapi")
def yapi(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    pt = _puan_turu(db, o)
    b = _hedef_bolum(db, o)
    konu_dersleri = [k for k, v in KONU_DERSLERI.items() if v[0] == "TYT"] + PUAN_TURU_KONU_DERSLERI.get(pt, [])
    from app.core.konu_servisi import etkin_konular   # [2026-10-10] liste veritabanında (genel + okula özel)
    liste = etkin_konular(db, o.okul_id)
    return {
        "puan_turu": pt, "puan_turu_ad": PUAN_TURU_AD.get(pt, pt),
        "hedef_bolum": {"id": b.id, "ad": b.ad} if b else None,
        "testler": _test_listesi(PUAN_TURU_TESTLERI[pt]),
        "tum_testler": _test_listesi(list(TESTLER)),
        "konu_dersleri": [{"kod": k, "oturum": KONU_DERSLERI[k][0], "ad": KONU_DERSLERI[k][1], "konular": liste.get(k, [])}
                          for k in konu_dersleri if liste.get(k)],
    }


# ----------------------------------------------------------------------------- denemeler
class DenemeIstek(BaseModel):
    tarih: date
    oturum: str = Field(pattern="^(TYT|AYT|YDT)$")
    ad: str | None = Field(default=None, max_length=80)
    dersler: dict[str, dict[str, int]]   # {"tyt_mat": {"d": 30, "y": 6}}


def _deneme_satiri(r) -> dict:
    return {"id": r.id, "tarih": r.tarih.isoformat(), "oturum": r.oturum, "ad": r.ad, "dersler": r.dersler,
            "toplam_net": float(r.toplam_net)}


@router.get("/denemeler")
def denemeler(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    rows = db.execute(text("SELECT id, tarih, oturum, ad, dersler, toplam_net FROM ogrenci_denemeleri "
                           "WHERE ogrenci_id = :o ORDER BY tarih, id"), {"o": o.id}).all()
    return {"denemeler": [_deneme_satiri(r) for r in rows]}


@router.post("/denemeler")
def deneme_ekle(istek: DenemeIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if istek.tarih > date.today() + timedelta(days=1) or istek.tarih < date.today() - timedelta(days=730):
        raise HTTPException(400, "Tarih geçersiz.")
    temiz, toplam = {}, 0.0
    for kod, v in istek.dersler.items():
        if kod not in TESTLER or TESTLER[kod][0] != istek.oturum:
            raise HTTPException(400, f"Bu oturumda olmayan ders: {kod}")
        d, y = int(v.get("d", 0) or 0), int(v.get("y", 0) or 0)
        soru = TESTLER[kod][2]
        if d < 0 or y < 0 or d + y > soru:
            raise HTTPException(400, f"{TESTLER[kod][1]}: doğru + yanlış en fazla {soru} olabilir.")
        net = net_hesapla(d, y)
        temiz[kod] = {"d": d, "y": y, "net": net}
        toplam += net
    if not temiz:
        raise HTTPException(400, "En az bir dersin sonucunu gir.")
    r = db.execute(text("INSERT INTO ogrenci_denemeleri (ogrenci_id, tarih, oturum, ad, dersler, toplam_net) "
                        "VALUES (:o, :t, :ot, :ad, CAST(:d AS JSONB), :tn) RETURNING id, tarih, oturum, ad, dersler, toplam_net"),
                   {"o": o.id, "t": istek.tarih, "ot": istek.oturum, "ad": (istek.ad or "").strip() or None,
                    "d": json.dumps(temiz), "tn": round(toplam, 2)}).first()
    db.commit()
    return _deneme_satiri(r)


@router.delete("/denemeler/{deneme_id}", status_code=204)
def deneme_sil(deneme_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    n = db.execute(text("DELETE FROM ogrenci_denemeleri WHERE id = :i AND ogrenci_id = :o"), {"i": deneme_id, "o": o.id}).rowcount
    db.commit()
    if not n:
        raise HTTPException(404, "Deneme bulunamadı.")


# ----------------------------------------------------------------------------- konu takibi
class KonuIstek(BaseModel):
    ders: str
    konu: str
    durum: str


@router.get("/konular")
def konular(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    rows = db.execute(text("SELECT ders, konu, durum FROM ogrenci_konu_takibi WHERE ogrenci_id = :o"), {"o": o.id}).all()
    d: dict[str, dict[str, str]] = {}
    for r in rows:
        d.setdefault(r.ders, {})[r.konu] = r.durum
    return {"durumlar": d}


@router.put("/konular", status_code=204)
def konu_guncelle(istek: KonuIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.core.konu_servisi import etkin_konular
    if istek.ders not in KONU_DERSLERI or istek.konu not in etkin_konular(db, o.okul_id).get(istek.ders, []) or istek.durum not in KONU_DURUMLARI:
        raise HTTPException(400, "Geçersiz konu ya da durum.")
    if istek.durum == "baslamadi":
        db.execute(text("DELETE FROM ogrenci_konu_takibi WHERE ogrenci_id = :o AND ders = :d AND konu = :k"),
                   {"o": o.id, "d": istek.ders, "k": istek.konu})
    else:
        db.execute(text("INSERT INTO ogrenci_konu_takibi (ogrenci_id, ders, konu, durum) VALUES (:o, :d, :k, :s) "
                        "ON CONFLICT (ogrenci_id, ders, konu) DO UPDATE SET durum = EXCLUDED.durum, guncelleme_zamani = now()"),
                   {"o": o.id, "d": istek.ders, "k": istek.konu, "s": istek.durum})
    db.commit()


# ----------------------------------------------------------------------------- YÖK Atlas Net Sihirbazı
def _net_satiri(d: dict) -> dict | None:
    if not isinstance(d, dict) or d.get("kilavuzKodu") is None:
        return None
    netler = {k: d.get(v[3]) for k, v in TESTLER.items() if d.get(v[3]) is not None}
    return {"kilavuz_kodu": int(d["kilavuzKodu"]), "yil": d.get("yil"), "universite": (d.get("universiteAdi") or "").strip(),
            "universite_turu": d.get("universiteTuru"), "program": (d.get("birimAdi") or "").strip(), "puan_turu": d.get("puanTuru"),
            "taban_puan": d.get("tabanPuan"), "obp": d.get("obp"), "netler": netler}


def programlara_grupla(satirlar: list[dict]) -> list[dict]:
    """Net Sihirbazı her program için birkaç yılın satırını döndürür; programa göre toplanır.
    son = en yeni yıl (geçen yıl), gecmis = önceki yıllar, ortalama = yılların ders ders ortalaması (tek kişiye bağlı dalgalanmayı yumuşatır)."""
    gruplar: dict[int, list[dict]] = {}
    for s in satirlar:
        gruplar.setdefault(s["kilavuz_kodu"], []).append(s)
    sonuc = []
    for kod, l in gruplar.items():
        l.sort(key=lambda x: -(x.get("yil") or 0))
        son = l[0]
        ort = {}
        for t in {k for x in l for k in x["netler"]}:
            v = [x["netler"][t] for x in l if x["netler"].get(t) is not None]
            ort[t] = round(sum(v) / len(v), 2) if v else None
        sonuc.append({"kilavuz_kodu": kod, "universite": son["universite"], "universite_turu": son.get("universite_turu"),
                      "program": son["program"], "puan_turu": son.get("puan_turu"),
                      "son": {k: son.get(k) for k in ("yil", "taban_puan", "obp", "netler")},
                      "gecmis": [{k: x.get(k) for k in ("yil", "taban_puan", "obp", "netler")} for x in l[1:]],
                      "ortalama": ort, "yil_sayisi": len(l)})
    sonuc.sort(key=lambda p: -((p["son"] or {}).get("taban_puan") or 0))
    return sonuc


def _yokatlas_netleri_cek(bolum: Bolum, puan_turu: str | None) -> dict:
    from app.core.yokatlas_servisi import _istemci_al, _program_grubu_idleri, elle_gruplar
    gruplar = _program_grubu_idleri(bolum.ad, elle_gruplar(bolum))
    if not gruplar:
        return {"eslesme": False, "programlar": [], "yil": None}
    istemci = _istemci_al()
    satirlar = []
    for g in gruplar:
        for sayfa in range(20):
            govde = {"filters": {"puanTuru": puan_turu, "universiteId": None, "birimGrupId": g, "birimTuruId": None,
                                 "universiteTuru": None, "yil": None, "katsayi": None}, "page": sayfa, "size": 100}
            ham = istemci._http.post_json("/api/netler/search", json_body=govde) or {}
            icerik = ham.get("content") or []
            satirlar += [x for x in (_net_satiri(d) for d in icerik) if x]
            if ham.get("last", True) or not icerik or len(satirlar) >= MAKS_NET_SATIRI:
                break
        if len(satirlar) >= MAKS_NET_SATIRI:
            break
    programlar = programlara_grupla(satirlar)
    yil = max((p["son"]["yil"] for p in programlar if p["son"].get("yil")), default=None)
    return {"eslesme": True, "programlar": programlar, "yil": yil}


def hedef_programlar(db: Session, bolum: Bolum) -> dict:
    r = db.execute(text("SELECT veri, guncellenme FROM yokatlas_net_onbellek WHERE bolum_id = :b"), {"b": bolum.id}).first()
    simdi = datetime.now(timezone.utc)
    taze = bool(r and r.veri is not None and r.guncellenme and simdi - r.guncellenme < timedelta(days=NET_ONBELLEK_GUN))
    if not taze:
        try:
            veri = _yokatlas_netleri_cek(bolum, puan_turu_normalize(bolum.osym_puan_turu))
            db.execute(text("INSERT INTO yokatlas_net_onbellek (bolum_id, veri, guncellenme, hata) VALUES (:b, CAST(:v AS JSONB), now(), NULL) "
                            "ON CONFLICT (bolum_id) DO UPDATE SET veri = EXCLUDED.veri, guncellenme = now(), hata = NULL"),
                       {"b": bolum.id, "v": json.dumps(veri)})
            db.commit()
            return {"durum": "tamam", **veri}
        except Exception as e:
            db.rollback()
            _log.warning("YÖK Atlas net hatası (%s): %s", bolum.ad, e)
            if r and r.veri:
                return {"durum": "tamam", "eski": True, **r.veri}
            return {"durum": "hata", "programlar": [], "yil": None,
                    "mesaj": "Geçen yılın netleri şu anda YÖK Atlas'tan alınamıyor. Biraz sonra tekrar dene."}
    return {"durum": "tamam", **r.veri}


@router.get("/hedef-programlar")
def hedef_programlari(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    b = _hedef_bolum(db, o)
    if b is None:
        return {"durum": "hedef_yok", "programlar": [], "mesaj": "Önce bir hedef bölüm seç; sonra o bölümün üniversitelerini burada görürsün."}
    v = hedef_programlar(db, b)
    if v.get("durum") == "tamam" and not v.get("programlar"):
        v = {**v, "durum": "eslesme_yok",
             "mesaj": "Bu bölüm için YÖK Atlas'ta net bilgisi bulunamadı (özel yetenekle öğrenci alan bölümlerde net yoktur)."}
    return {**v, "bolum": b.ad, "secili": (_net_hedefi(db, o) or {}).get("kilavuz_kodu")}


class HedefIstek(BaseModel):
    kilavuz_kodu: int


@router.put("/hedef")
def net_hedefi_kaydet(istek: HedefIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    b = _hedef_bolum(db, o)
    if b is None:
        raise HTTPException(400, "Önce bir hedef bölüm seç.")
    v = hedef_programlar(db, b)
    p = next((x for x in v.get("programlar", []) if x["kilavuz_kodu"] == istek.kilavuz_kodu), None)
    if p is None:
        raise HTTPException(400, "Bu program hedef bölümünün listesinde yok.")
    db.execute(text("INSERT INTO ogrenci_net_hedefi (ogrenci_id, kilavuz_kodu, veri) VALUES (:o, :k, CAST(:v AS JSONB)) "
                    "ON CONFLICT (ogrenci_id) DO UPDATE SET kilavuz_kodu = EXCLUDED.kilavuz_kodu, veri = EXCLUDED.veri, guncelleme_zamani = now()"),
               {"o": o.id, "k": p["kilavuz_kodu"], "v": json.dumps({**p, "bolum_id": b.id})})
    db.commit()
    return p


@router.delete("/hedef", status_code=204)
def net_hedefi_sil(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    db.execute(text("DELETE FROM ogrenci_net_hedefi WHERE ogrenci_id = :o"), {"o": o.id})
    db.commit()


# ----------------------------------------------------------------------------- kıyas
def kiyas_hesapla(db: Session, o: Ogrenci) -> dict:
    hedef = _net_hedefi(db, o)
    pt = _puan_turu(db, o)
    rows = db.execute(text("SELECT tarih, oturum, dersler FROM ogrenci_denemeleri WHERE ogrenci_id = :o ORDER BY tarih DESC, id DESC"),
                      {"o": o.id}).all()
    son: dict[str, list[float]] = {}
    for oturum in ("TYT", "AYT", "YDT"):
        for r in [x for x in rows if x.oturum == oturum][:KIYAS_DENEME_SAYISI]:
            for kod, v in (r.dersler or {}).items():
                son.setdefault(kod, []).append(float(v.get("net", 0)))
    satirlar = []
    for kod in PUAN_TURU_TESTLERI[pt]:
        ben = round(sum(son[kod]) / len(son[kod]), 2) if son.get(kod) else None
        h = ((hedef or {}).get("son") or {}).get("netler", {}).get(kod)
        onceki = next(((g.get("netler") or {}).get(kod) for g in (hedef or {}).get("gecmis", []) if (g.get("netler") or {}).get(kod) is not None), None)
        ort = ((hedef or {}).get("ortalama") or {}).get(kod)
        satirlar.append({"kod": kod, "ad": TESTLER[kod][1], "oturum": TESTLER[kod][0], "soru": TESTLER[kod][2],
                         "ben": ben, "deneme_sayisi": len(son.get(kod, [])), "hedef": h, "hedef_onceki_yil": onceki,
                         "hedef_ortalama": ort, "fark": round(ben - h, 2) if ben is not None and h is not None else None})
    karsilastirilan = [s for s in satirlar if s["fark"] is not None]
    acik = sorted([s for s in karsilastirilan if s["fark"] < 0], key=lambda s: s["fark"])
    return {"hedef": hedef, "puan_turu": pt, "satirlar": satirlar,
            "toplam_ben": round(sum(s["ben"] for s in karsilastirilan), 2) if karsilastirilan else None,
            "toplam_hedef": round(sum(s["hedef"] for s in karsilastirilan), 2) if karsilastirilan else None,
            "en_buyuk_acik": [{"ad": s["ad"], "fark": s["fark"]} for s in acik[:3]],
            "yil": ((hedef or {}).get("son") or {}).get("yil"),
            "onceki_yil": next((g.get("yil") for g in (hedef or {}).get("gecmis", [])), None),
            "aciklama": "Hedef netler, geçen yıl bu programa yerleşen SON öğrencinin netleridir (YÖK Atlas). Yerleşmede "
                        "diploma notu (OBP) da etkili olduğu ve netler tek bir kişiye ait olduğu için kesin hedef değil, yön göstericidir; "
                        "yıllar arası ortalama daha dengeli bir hedeftir. Senin netlerin son "
                        f"{KIYAS_DENEME_SAYISI} denemenin ortalamasıdır."}


@router.get("/kiyas")
def kiyas(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return kiyas_hesapla(db, o)
