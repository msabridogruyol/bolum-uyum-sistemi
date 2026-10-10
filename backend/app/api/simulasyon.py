# -*- coding: utf-8 -*-
"""
[2026-10-10] "Bir günümü yaşa" — meslek simülasyonu ve bölümü tanıma (modül: kocluk).

Her bölümün detayındaki meslekler (günlük işler, çalışma ortamı, beceriler, nasıl olunur) bir güne dönüştürülür:
sabah → gün içindeki işler → (popüler mesleklerde) karar anları → akşam. Öğrenci her işe tepki verir
(😍 2 · 🙂 1 · 😕 0); karar anlarında seçim yapar ve geri bildirim alır. Sonunda keyif yüzdesi, sevdiği / sevmediği
işler, karar yaklaşımları ve kendi güçlü yönleriyle mesleğin istediği beceriler yan yana gösterilir.

Öğrenci:  GET  /ogrenci/bolum/{bolum_id}/tanit             — bölüm detayı (özet, dersler, iş alanları, meslekler) + uyum
          GET  /ogrenci/bolum/{bolum_id}/simulasyon?meslek=0
          POST /ogrenci/simulasyon                         — sonuç kaydet, özet döner
          GET  /ogrenci/simulasyonlarim
Yönetim:  GET  /yonetim/ogrenci/{ogrenci_id}/simulasyonlar
"""
import json
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.database import get_db
from app.core.meslek_senaryolari import YAKLASIMLAR, senaryo_bul
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter(prefix="/ogrenci", tags=["Meslek simülasyonu"])
yonetim_router = APIRouter(prefix="/yonetim", tags=["Meslek simülasyonu"])

IS_SAATLERI = ["09:00", "10:30", "13:30", "15:00", "16:30", "17:30"]


def _bolum(db: Session, bolum_id: int):
    r = db.execute(text("SELECT id, ad, osym_puan_turu, detay FROM bolumler WHERE id = :i AND durum = 'yayinda'"), {"i": bolum_id}).first()
    if r is None:
        raise HTTPException(404, "Bölüm bulunamadı.")
    d = r.detay if isinstance(r.detay, dict) else json.loads(r.detay or "{}")
    return r, d


def _kucuk(m: str) -> str:
    return m.replace("I", "ı").replace("İ", "i").lower()


def _baslik(ad: str) -> str:
    """'MADEN MÜHENDİSLİĞİ' → 'Maden Mühendisliği' (Türkçe büyük / küçük harf kurallarıyla)."""
    if not ad or not ad.isupper():
        return ad
    return " ".join(_kucuk(w) if _kucuk(w) in ("ve", "ile") else w[:1] + _kucuk(w[1:]) for w in ad.split())


def _uyum(db: Session, ogrenci_id, bolum_id):
    from app.api.tercih import uyumlar
    return uyumlar(db, ogrenci_id).get(bolum_id)


@ogrenci_router.get("/bolum/{bolum_id}/tanit")
def bolum_tanit(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    r, d = _bolum(db, bolum_id)
    u = _uyum(db, o.id, bolum_id)
    yapilan = {x.meslek_ad: x.keyif for x in db.execute(text("""
        SELECT DISTINCT ON (meslek_ad) meslek_ad, keyif FROM simulasyon_sonuclari WHERE ogrenci_id = :o AND bolum_id = :b
         ORDER BY meslek_ad, olusturulma_zamani DESC"""), {"o": o.id, "b": bolum_id}).all()}
    return {
        "bolum": {"id": r.id, "ad": _baslik(r.ad), "puan_turu": d.get("puan_turu") or r.osym_puan_turu, "ogrenim_suresi": d.get("ogrenim_suresi"),
                  "ozet": d.get("ozet"), "neler_ogrenilir": d.get("neler_ogrenilir") or [], "ornek_dersler": d.get("ornek_dersler") or [],
                  "calisma_alanlari": d.get("calisma_alanlari") or [], "kimler_icin_uygun": d.get("kimler_icin_uygun"),
                  "bilmen_gerekenler": d.get("bilmen_gerekenler")},
        "meslekler": [{"no": i, "ad": m.get("ad"), "aciklama": m.get("aciklama"), "calisma_ortami": m.get("calisma_ortami"),
                       "nasil_olunur": m.get("nasil_olunur"), "gerekli_beceriler": m.get("gerekli_beceriler") or [],
                       "simulasyon": len(m.get("gunluk_isler") or []) >= 3, "kararli": bool(senaryo_bul(m.get("ad"))),
                       "keyif": yapilan.get(m.get("ad"))} for i, m in enumerate(d.get("meslekler") or [])],
        "uyum": {"yuzde": u[0], "sira": u[1]} if u else None,
    }


@ogrenci_router.get("/bolum/{bolum_id}/simulasyon")
def simulasyon(bolum_id: int, meslek: int = Query(0, ge=0), db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    r, d = _bolum(db, bolum_id)
    ml = d.get("meslekler") or []
    if meslek >= len(ml):
        raise HTTPException(404, "Meslek bulunamadı.")
    m = ml[meslek]
    isler = (m.get("gunluk_isler") or [])[:6]
    if len(isler) < 3:
        raise HTTPException(400, "Bu meslek için simülasyon hazırlanacak kadar bilgi yok.")
    kararlar = senaryo_bul(m.get("ad"))
    sahneler = [{"id": "sabah", "tur": "giris", "saat": "07:30", "baslik": "Güne başlıyorsun",
                 "metin": f"Bugün bir {m.get('ad', '').lower()} olarak çalışıyorsun. {m.get('calisma_ortami') or ''}".strip()}]
    for i, is_ in enumerate(isler):
        sahneler.append({"id": f"is{i}", "tur": "is", "saat": IS_SAATLERI[min(i, len(IS_SAATLERI) - 1)], "baslik": "Görev", "metin": is_})
    for kno, k in enumerate(kararlar):   # karar anları kendi saatlerine yerleşir
        sahneler.append({"id": f"karar{kno}", "tur": "karar", "saat": k["saat"], "baslik": k["baslik"], "metin": k["durum"],
                         "secenekler": [{"no": j, "metin": x["metin"], "sonuc": x["sonuc"], "yaklasim": YAKLASIMLAR.get(x["yaklasim"]),
                                         "onerilen": bool(x.get("onerilen"))} for j, x in enumerate(k["secenekler"])],
                         "onerilen_var": any(x.get("onerilen") for x in k["secenekler"])})
    sahneler.sort(key=lambda x: (x["saat"], x["tur"] != "karar"))
    sahneler.append({"id": "aksam", "tur": "cikis", "saat": "18:00", "baslik": "Gün bitti",
                     "metin": "Bir günü geride bıraktın. Şimdi bu mesleğin sana ne kadar uyduğuna bakalım."})
    return {"bolum": {"id": r.id, "ad": _baslik(r.ad)}, "meslek": {"no": meslek, "ad": m.get("ad"), "aciklama": m.get("aciklama"),
            "calisma_ortami": m.get("calisma_ortami"), "nasil_olunur": m.get("nasil_olunur"), "gerekli_beceriler": m.get("gerekli_beceriler") or []},
            "sahneler": sahneler, "kararli": bool(kararlar)}


class SonucIstek(BaseModel):
    bolum_id: int
    meslek: int = Field(ge=0)
    tepkiler: dict[str, int] = Field(default_factory=dict)    # {"is0": 2, ...}
    kararlar: dict[str, int] = Field(default_factory=dict)    # {"karar0": 1, ...}


@ogrenci_router.post("/simulasyon")
def simulasyon_kaydet(istek: SonucIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    r, d = _bolum(db, istek.bolum_id)
    ml = d.get("meslekler") or []
    if istek.meslek >= len(ml):
        raise HTTPException(404, "Meslek bulunamadı.")
    m = ml[istek.meslek]
    isler = (m.get("gunluk_isler") or [])[:6]
    tepki = {f"is{i}": max(0, min(2, int(istek.tepkiler.get(f"is{i}", 1)))) for i in range(len(isler))}
    keyif = round(100 * sum(tepki.values()) / (2 * len(tepki))) if tepki else 0
    senaryo = senaryo_bul(m.get("ad"))
    karar_ozet, yaklasim = [], Counter()
    for kno, k in enumerate(senaryo):
        sec = istek.kararlar.get(f"karar{kno}")
        if sec is None or not (0 <= sec < len(k["secenekler"])):
            continue
        s = k["secenekler"][sec]
        yaklasim[s["yaklasim"]] += 1
        onerilen = next((x["metin"] for x in k["secenekler"] if x.get("onerilen")), None)
        karar_ozet.append({"baslik": k["baslik"], "secim": s["metin"], "sonuc": s["sonuc"], "yaklasim": YAKLASIMLAR.get(s["yaklasim"]),
                           "onerilen_mi": bool(s.get("onerilen")), "onerilen": onerilen if onerilen and not s.get("onerilen") else None})
    yaklasimlar = [YAKLASIMLAR[k] for k, _n in yaklasim.most_common()]
    db.execute(text("""
        INSERT INTO simulasyon_sonuclari (ogrenci_id, bolum_id, meslek_ad, keyif, tepkiler, kararlar, yaklasimlar)
        VALUES (:o, :b, :m, :k, CAST(:t AS JSONB), CAST(:kr AS JSONB), CAST(:y AS JSONB))
    """), {"o": o.id, "b": r.id, "m": m.get("ad"), "k": keyif, "t": json.dumps(tepki), "kr": json.dumps(istek.kararlar),
           "y": json.dumps(yaklasimlar, ensure_ascii=False)})
    db.commit()
    gucluler = []
    try:
        from app.core.rapor.veri import ogrenci_raporu_verisi
        gucluler = [x["ad"] for x in ogrenci_raporu_verisi(db, o).get("gucluler", [])[:5]]
    except Exception:
        db.rollback()
    u = _uyum(db, o.id, r.id)
    if keyif >= 70:
        yorum = "Bu günün çoğu sana keyifli geldi. Bu mesleği daha yakından tanımak için bir meslek sahibiyle konuşmayı ya da kampüs gezisini düşünebilirsin."
    elif keyif >= 40:
        yorum = "Bazı işler sana uygun, bazıları değil. Her meslekte sevilmeyen işler olur; önemli olan çoğunluğun sana iyi gelmesi. Aynı bölümün başka mesleklerine de bakabilirsin."
    else:
        yorum = "Bu günün işleri sana pek keyifli gelmedi. Bu da değerli bir bilgi! Bölümün diğer mesleklerini ya da sana önerilen başka bölümleri deneyebilirsin."
    return {
        "keyif": keyif, "yorum": yorum,
        "sevdiklerin": [isler[int(k[2:])] for k, v in tepki.items() if v == 2],
        "sevmediklerin": [isler[int(k[2:])] for k, v in tepki.items() if v == 0],
        "kararlar": karar_ozet, "yaklasimlar": yaklasimlar,
        "gerekli_beceriler": m.get("gerekli_beceriler") or [], "gucluler": gucluler,
        "nasil_olunur": m.get("nasil_olunur"), "uyum": {"yuzde": u[0], "sira": u[1]} if u else None,
        "meslek": m.get("ad"), "bolum": _baslik(r.ad),
    }


def _gecmis(db: Session, ogrenci_id) -> list[dict]:
    return [{**dict(x._mapping), "olusturulma_zamani": x.olusturulma_zamani.isoformat()} for x in db.execute(text("""
        SELECT DISTINCT ON (s.bolum_id, s.meslek_ad) s.bolum_id, b.ad AS bolum_ad, s.meslek_ad, s.keyif, s.yaklasimlar, s.olusturulma_zamani
          FROM simulasyon_sonuclari s LEFT JOIN bolumler b ON b.id = s.bolum_id
         WHERE s.ogrenci_id = :o ORDER BY s.bolum_id, s.meslek_ad, s.olusturulma_zamani DESC
    """), {"o": ogrenci_id}).all()]


@ogrenci_router.get("/simulasyonlarim")
def simulasyonlarim(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    liste = sorted(_gecmis(db, o.id), key=lambda x: x["olusturulma_zamani"], reverse=True)
    for x in liste:
        x["bolum_ad"] = _baslik(x["bolum_ad"])
    return {"simulasyonlar": liste}


@yonetim_router.get("/ogrenci/{ogrenci_id}/simulasyonlar")
def ogrenci_simulasyonlari(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.okul_yonetimi import _ogrenci_kapsami
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    liste = sorted(_gecmis(db, o.id), key=lambda x: -x["keyif"])
    for x in liste:
        x["bolum_ad"] = _baslik(x["bolum_ad"])
    return {"simulasyonlar": liste}
