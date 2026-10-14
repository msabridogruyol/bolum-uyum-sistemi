"""
[2026-10-13] İş Hayatı → "Mülakat Simülasyonu" sekmesi (prefix: /ogrenci/is-hayati, modül kapısı is_hayati otomatik).

Her bölüm için kısa bir iş görüşmesi: mülakatçı alana özgü bir durum sorar, iki aday farklı yaklaşımla cevap verir, öğrenci
hangisinin daha iyi cevap verdiğini seçer. Ardından iki cevabın neden güçlü / zayıf olduğu, mülakatçının tercihi ve "alandan bir
bilgi" gösterilir. Amaç bilgi sınavı değil, mesleğe ön bakıştır: doğru cevap adayların gerekçesinden mantıkla bulunabilir.
Soru türleri: 'dogru' (bir aday daha iyi) · 'ikisi_de' (iki yaklaşım da savunulabilir, sonuçları farklı).

  GET  /mulakat-sim/{bolum_id}  — mülakatçı, pozisyon, 4 soru (adaylar, açıklamalar), son denemeler
  POST /mulakat-sim             — seçimleri kaydet, özet döner (sonuçlar yalnızca öğrencinin kendisine görünür)

İçerik: app/data/mulakat_simulasyonu.json — {"bolumler": {"<BÖLÜM ADI>": {mulakatci, pozisyon, sorular: [4]}}}.
Durumlar kurgusaldır; gerçek kişi, kurum ya da istatistik içermez.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.api.is_hayati_dusunme import arac_ozeti
from app.core import is_hayati_pratik as ihp
from app.core.database import get_db
from app.models import Ogrenci

ogrenci_router = APIRouter()
DOSYA = "mulakat_simulasyonu.json"
KAYNAK_NOTU = ("Mülakat durumları kurgusaldır; mesleğin günlük işleri ve bölümde okutulan dersler esas alınarak hazırlanmıştır. "
               "Gerçek kişi, kurum ya da istatistik içermez. Bu bir sınav değil, mesleğe kısa bir ön bakıştır.")


def _anahtar(ad: str | None) -> str:
    return " ".join((ad or "").split())


def _icerik(bolum_ad: str | None) -> dict | None:
    return (ihp.veri(DOSYA).get("bolumler") or {}).get(_anahtar(bolum_ad))


def _bolum(db: Session, bolum_id: int) -> tuple[str, dict]:
    ad, _m = ihp.bolum_meslekleri(db, bolum_id)
    if ad is None:
        raise HTTPException(404, "Bölüm bulunamadı.")
    ic = _icerik(ad)
    if not ic or not ic.get("sorular"):
        raise HTTPException(404, "Bu bölüm için mülakat simülasyonu henüz hazırlanmadı.")
    return ad, ic


def _iyi_adaylar(q: dict) -> list[int]:
    return [i for i, a in enumerate(q.get("adaylar") or []) if a.get("iyi")]


@ogrenci_router.get("/mulakat-sim/{bolum_id}")
def mulakat_sim(bolum_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    ad, ic = _bolum(db, bolum_id)
    son = [{"dogru": r.dogru, "toplam": r.toplam, "zaman": r.olusturulma_zamani.isoformat()} for r in db.execute(text("""
        SELECT dogru, toplam, olusturulma_zamani FROM is_hayati_mulakat_sim
         WHERE ogrenci_id = :o AND bolum_id = :b ORDER BY olusturulma_zamani DESC LIMIT 3"""), {"o": o.id, "b": bolum_id}).all()]
    sorular = []
    for i, q in enumerate(ic["sorular"]):
        sorular.append({
            "no": i, "konu": q.get("konu"), "beceri": q.get("beceri"), "soru": q.get("soru"), "tur": q.get("tur"),
            "terimler": q.get("terimler") or [], "ders": q.get("ders"), "arac": arac_ozeti(q.get("arac")),
            "adaylar": [{"cevap": a.get("cevap"), "iyi": bool(a.get("iyi")), "neden": a.get("neden"), "sonuc": a.get("sonuc")}
                        for a in q.get("adaylar") or []],
        })
    return {"bolum": {"id": bolum_id, "ad": ad}, "mulakatci": ic.get("mulakatci"), "pozisyon": ic.get("pozisyon"),
            "sorular": sorular, "son": son, "kaynak_notu": KAYNAK_NOTU}


class MulakatSimIstek(BaseModel):
    bolum_id: int
    secimler: dict[str, int] = Field(default_factory=dict)   # {"0": 1, "1": 0, ...} soru no → seçilen aday (0 / 1)


def _yorum(dogru: int, toplam: int, yanitsiz: int = 0) -> str:
    """[2026-10-14] Oran yalnızca YANITLANAN sorulara göre; yarı yarıya "çoğunda" sayılmaz. Her cümle tek parça yazılır
    (çeviride parça birleştirme bozulmasın); boş bırakılan sorular için ayrı cümle: _yanitsiz_notu."""
    if not toplam:
        return "Bu mülakatta iki yaklaşımın da savunulabildiği durumları inceledin; iş hayatında her sorunun tek bir doğrusu olmaz."
    if dogru == toplam:
        return ("Yanıtladığın her soruda mülakatçıyla aynı adayı seçtin. Bu alandaki düşünme biçimi sana yabancı gelmiyor gibi; "
                "alandan bilgileri okuyarak bu meslekte işlerin nasıl yürüdüğünü daha yakından tanıyabilirsin." if yanitsiz else
                "Her soruda mülakatçıyla aynı adayı seçtin. Bu alandaki düşünme biçimi sana yabancı gelmiyor gibi; "
                "alandan bilgileri okuyarak bu meslekte işlerin nasıl yürüdüğünü daha yakından tanıyabilirsin.")
    if 2 * dogru > toplam:
        return ("Yanıtladığın soruların çoğunda mülakatçıyla aynı düşündün. Farklı seçtiğin sorulardaki açıklamalara bir daha göz at; "
                "bu alanda neye dikkat edildiğini en iyi orada görürsün." if yanitsiz else
                "Soruların çoğunda mülakatçıyla aynı düşündün. Farklı seçtiğin sorulardaki açıklamalara bir daha göz at; "
                "bu alanda neye dikkat edildiğini en iyi orada görürsün.")
    if 2 * dogru == toplam:
        return ("Yanıtladığın soruların yarısında mülakatçıyla aynı düşündün. Farklı seçtiğin sorulardaki açıklamalar, "
                "bu alanda neye dikkat edildiğini gösteriyor; onlara bir daha göz at." if yanitsiz else
                "Soruların yarısında mülakatçıyla aynı düşündün. Farklı seçtiğin sorulardaki açıklamalar, "
                "bu alanda neye dikkat edildiğini gösteriyor; onlara bir daha göz at.")
    return ("Bu alanın düşünme biçimi sana henüz yeni; bu çok doğal, çünkü bu bilgiler bölümde öğrenilir. "
            "Açıklamalar, bu meslekte bir sorunun nasıl ele alındığını gösteriyor; merak ettiysen bu bölümü daha yakından incele.")


def _yanitsiz_notu(yanitsiz: int) -> str | None:
    return f"{yanitsiz} soruyu boş bıraktın; onlara da dönüp bakarsan bu alanı daha bütünlüklü tanırsın." if yanitsiz else None


@ogrenci_router.post("/mulakat-sim")
def mulakat_sim_kaydet(istek: MulakatSimIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    ad, ic = _bolum(db, istek.bolum_id)
    sorular = ic["sorular"]
    dogru = toplam = ikisi_de = 0
    secimler, ozet = {}, []
    for i, q in enumerate(sorular):
        sec = istek.secimler.get(str(i))
        if sec is None or not (0 <= sec < len(q.get("adaylar") or [])):
            continue
        secimler[str(i)] = sec
        iyi = _iyi_adaylar(q)
        if q.get("tur") == "ikisi_de":
            ikisi_de += 1
            ayni = None
        else:
            toplam += 1
            ayni = sec in iyi
            dogru += int(ayni)
        ozet.append({"no": i, "konu": q.get("konu"), "beceri": q.get("beceri"), "ayni": ayni, "ders": q.get("ders")})
    if not ozet:
        raise HTTPException(400, "En az bir soruda aday seçmelisin.")
    db.execute(text("""INSERT INTO is_hayati_mulakat_sim (ogrenci_id, bolum_id, secimler, dogru, toplam)
                       VALUES (:o, :b, CAST(:s AS JSONB), :d, :t)"""),
               {"o": o.id, "b": istek.bolum_id, "s": json.dumps(secimler), "d": dogru, "t": toplam})
    db.commit()
    return {"bolum": {"id": istek.bolum_id, "ad": ad}, "dogru": dogru, "toplam": toplam, "ikisi_de": ikisi_de,
            "sorular": ozet, "beceriler": list(dict.fromkeys(x["beceri"] for x in ozet if x.get("beceri"))),
            "yorum": _yorum(dogru, toplam, len(sorular) - len(ozet)), "yorum_ek": _yanitsiz_notu(len(sorular) - len(ozet))}
