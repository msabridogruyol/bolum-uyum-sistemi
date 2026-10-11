# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı → "Zor Günler" sekmesi (prefix: /ogrenci/is-hayati, modül kapısı is_hayati otomatik).

Her mesleğin zor günleri olur: fazla mesai, nöbet, öfkeli bir müşteri, yapılan bir hata, beklenenden düşük zam, monotonluk…
Öğrenci her durumda bir seçim yapar, sonucunu görür, "nasıl başa çıkılır" notunu ve "yine de sevenler neden seviyor"
cümlesini okur. Sonunda hangi yaklaşımla davrandığı (simülasyondaki YAKLASIMLAR) özetlenir.

  GET  /zor-gun/{bolum_id}                 — üst alan, bölümün meslekleri (mesleğe özgü senaryo var mı), son turlar
  GET  /zor-gun/{bolum_id}/tur?meslek=ad   — tur: mesleğe özgü 2 + alan 3 senaryo; meslek yoksa alanın 5 senaryosu
  POST /zor-gun                            — seçimleri kaydet, özet döner

İçerik: app/data/zor_gunler.json (kurgusal durumlar; gerçek kişi/kurum/istatistik yok).
"""
import json
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core import is_hayati_pratik as ihp
from app.core.database import get_db
from app.core.meslek_senaryolari import YAKLASIMLAR
from app.models import Ogrenci

ogrenci_router = APIRouter()

DOSYA = "zor_gunler.json"
KAYNAK_NOTU = ("Durumlar kurgusaldır; mesleklerin iş tanımları, iş sağlığı ve güvenliği ve çalışma hayatına ilişkin genel bilgiler "
               "esas alınarak hazırlanmıştır. Gerçek kişi, kurum ya da istatistik içermez. Zor anlarda iş yerinin kuralları, "
               "yöneticin ve gerekiyorsa bir uzman en doğru rehberdir.")


def _alan_senaryolari(kod: str | None) -> list[dict]:
    return ((ihp.veri(DOSYA).get("alanlar") or {}).get(kod or "") or {}).get("senaryolar") or []


def _meslek_senaryolari(ad: str | None) -> list[dict]:
    return (ihp.veri(DOSYA).get("meslekler") or {}).get(ihp.meslek_anahtari(ad)) or []


def _tur(alan_kod: str | None, meslek: str | None) -> list[tuple[str, dict]]:
    """[(id, senaryo)] — mesleğe özgü 2 + alanın (meslektekilerle aynı türde olmayan) 3 senaryosu; meslek yoksa alanın 5'i."""
    alan = [(f"a{i}", s) for i, s in enumerate(_alan_senaryolari(alan_kod))]
    ozel = [(f"m{i}", s) for i, s in enumerate(_meslek_senaryolari(meslek))] if meslek else []
    if not ozel:
        return alan
    turler = {s.get("tur") for _i, s in ozel}
    farkli = [x for x in alan if x[1].get("tur") not in turler]
    secilen = (farkli + [x for x in alan if x not in farkli])[:3]
    return ozel + secilen


def _istemci(sid: str, s: dict) -> dict:
    return {"id": sid, "saat": s.get("saat"), "baslik": s.get("baslik"), "tur": s.get("tur"),
            "tur_ad": (ihp.veri(DOSYA).get("turler") or {}).get(s.get("tur")), "durum": s.get("durum"),
            "ozel": sid.startswith("m"),
            "secenekler": [{"no": j, "metin": x["metin"], "sonuc": x["sonuc"], "yaklasim": YAKLASIMLAR.get(x["yaklasim"]),
                            "onerilen": bool(x.get("onerilen"))} for j, x in enumerate(s.get("secenekler") or [])],
            "onerilen_var": any(x.get("onerilen") for x in s.get("secenekler") or []),
            "basa_cikma": s.get("basa_cikma"), "neden_seviyorlar": s.get("neden_seviyorlar")}


def _bolum_bilgisi(db: Session, bolum_id: int):
    ad, meslekler = ihp.bolum_meslekleri(db, bolum_id)
    if ad is None:
        raise HTTPException(404, "Bölüm bulunamadı.")
    return ad, meslekler, ihp.bolum_alani(db, bolum_id)


@ogrenci_router.get("/zor-gun/{bolum_id}")
def zor_gun_ozet(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    _ad, meslekler, alan = _bolum_bilgisi(db, bolum_id)
    son = [{"meslek_ad": r.meslek_ad, "yaklasimlar": r.yaklasimlar, "zaman": r.olusturulma_zamani.isoformat()} for r in db.execute(text("""
        SELECT meslek_ad, yaklasimlar, olusturulma_zamani FROM is_hayati_zor_gun
         WHERE ogrenci_id = :o AND bolum_id = :b ORDER BY olusturulma_zamani DESC LIMIT 5"""), {"o": o.id, "b": bolum_id}).all()]
    return {
        "alan": alan, "alan_senaryo_sayisi": len(_alan_senaryolari(alan["kod"] if alan else None)),
        "meslekler": [{"ad": m, "ozel": bool(_meslek_senaryolari(m))} for m in meslekler],
        "son": son, "kaynak_notu": KAYNAK_NOTU,
    }


@ogrenci_router.get("/zor-gun/{bolum_id}/tur")
def zor_gun_turu(bolum_id: int, meslek: str | None = Query(None, max_length=200), db: Session = Depends(get_db),
                 o: Ogrenci = Depends(get_mevcut_ogrenci)):
    _ad, meslekler, alan = _bolum_bilgisi(db, bolum_id)
    if meslek and ihp.meslek_anahtari(meslek) not in {ihp.meslek_anahtari(m) for m in meslekler}:
        raise HTTPException(404, "Bu meslek seçili bölümde yok.")
    tur = _tur(alan["kod"] if alan else None, meslek)
    if not tur:
        raise HTTPException(404, "Bu bölüm için zor gün senaryosu henüz hazırlanmadı.")
    return {"alan": alan, "meslek": meslek, "senaryolar": [_istemci(sid, s) for sid, s in tur], "kaynak_notu": KAYNAK_NOTU}


class ZorGunIstek(BaseModel):
    bolum_id: int
    meslek: str | None = Field(None, max_length=200)
    secimler: dict[str, int] = Field(default_factory=dict)   # {"m0": 1, "a3": 0, ...}


@ogrenci_router.post("/zor-gun")
def zor_gun_kaydet(istek: ZorGunIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    _ad, meslekler, alan = _bolum_bilgisi(db, istek.bolum_id)
    meslek = istek.meslek if istek.meslek and ihp.meslek_anahtari(istek.meslek) in {ihp.meslek_anahtari(m) for m in meslekler} else None
    tur = _tur(alan["kod"] if alan else None, meslek)
    yaklasim, ozet = Counter(), []
    for sid, s in tur:
        sec = istek.secimler.get(sid)
        secenekler = s.get("secenekler") or []
        if sec is None or not (0 <= sec < len(secenekler)):
            continue
        x = secenekler[sec]
        yaklasim[x["yaklasim"]] += 1
        onerilen = next((y["metin"] for y in secenekler if y.get("onerilen")), None)
        ozet.append({"baslik": s.get("baslik"), "secim": x["metin"], "yaklasim": YAKLASIMLAR.get(x["yaklasim"]),
                     "onerilen_mi": bool(x.get("onerilen")), "onerilen": onerilen if onerilen and not x.get("onerilen") else None,
                     "basa_cikma": s.get("basa_cikma")})
    if not ozet:
        raise HTTPException(400, "En az bir durumda seçim yapmalısın.")
    dagilim = [{"kod": k, "ad": YAKLASIMLAR[k], "sayi": n} for k, n in yaklasim.most_common()]
    db.execute(text("""INSERT INTO is_hayati_zor_gun (ogrenci_id, bolum_id, alan_kod, meslek_ad, secimler, yaklasimlar)
                       VALUES (:o, :b, :a, :m, CAST(:s AS JSONB), CAST(:y AS JSONB))"""),
               {"o": o.id, "b": istek.bolum_id, "a": alan["kod"] if alan else None, "m": meslek,
                "s": json.dumps(istek.secimler), "y": json.dumps([d["ad"] for d in dagilim], ensure_ascii=False)})
    db.commit()
    en = dagilim[0]
    esit = [d["ad"] for d in dagilim if d["sayi"] == en["sayi"]]
    return {"kararlar": ozet, "dagilim": dagilim, "en_cok": esit, "toplam": len(ozet),
            "yorum": YORUMLAR.get(en["kod"], "") if len(esit) == 1 else
            "Durumlara göre farklı yollar seçtin. Esneklik iş hayatında çok değerli: her zor gün aynı çözümü istemez.",
            "meslek": meslek, "alan": alan}


YORUMLAR = {
    "guvenlik": "Zor anlarda önce riski azaltmayı seçiyorsun. Bu, sağlık ve teknik mesleklerde çok değerli; yalnızca her şeyi tek başına üstlenmemeye dikkat et.",
    "analitik": "Zorlanınca önce durumu anlamaya çalışıyorsun. Veri ve neden-sonuç düşünmek seni sakin tutar; bazen hızlı bir ilk adımın da gerektiğini unutma.",
    "iletisim": "Zor anlarda konuşarak çözmeyi seçiyorsun. Açık iletişim çoğu sorunu büyümeden çözer; sınırlarını da aynı açıklıkla söyleyebilmek önemli.",
    "ekip": "Zorlandığında ekibine yaslanmayı biliyorsun. Yardım istemek bir zayıflık değil, profesyonelliğin parçası.",
    "yaratici": "Zor anlarda yeni bir yol arıyorsun. Bu bakış monotonluğu ve tıkanmayı aşmana yardım eder; kurallarla dengelemeyi unutma.",
    "planli": "Zorlukları plan yaparak yönetiyorsun. Öncelik belirlemek tükenmişliğe karşı en güçlü kalkanlardan biri.",
    "empati": "Zor anlarda karşındakini anlamaya çalışıyorsun. Bu insanlarla çalışan her meslekte güç; kendi duygularına da aynı özeni göstermeyi unutma.",
    "etik": "Zor anlarda doğru olandan şaşmıyorsun. Bu güven kazandırır; ilkeli olmak bazen kısa vadede zor ama uzun vadede seni korur.",
    "hizli": "Zor anlarda hızlı karar veriyorsun. Acil durumlarda bu çok işe yarar; ama acele bazen ayrıntıyı kaçırtır, kritik işlerde bir nefes almayı dene.",
}
