"""
[2026-10-08] Bölüm bilgi kartı (her sayfadaki açılır pencere) için herkese açık, salt-okunur uç noktalar.
GET /bolumler/{bolum_id}/bilgi           — tanıtım (özet, dersler, meslekler...) + üst/alt alan
GET /bolumler/{bolum_id}/universiteler   — YÖK Atlas: üniversiteler, kontenjan, taban puan, başarı sırası
GET /bolumler/ada-gore?ad=...            — sadece bölüm adı bilinen ekranlar için id bulma
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Bolum, BolumDalEslesme, Dal, BolumAgirligi, Degisken, Katman
from app.core.katman_servisi import parametre_oku
from app.core.yokatlas_servisi import bolum_universiteleri, baglanti_tani
from app.api.deps import get_opsiyonel_ogrenci
from app.core.meslek_dili_servisi import etkin_surum

router = APIRouter()



def _bolum(db: Session, bolum_id: int) -> Bolum:
    b = db.get(Bolum, bolum_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")
    return b


@router.get("/ada-gore")
def bolum_ada_gore(ad: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    b = db.query(Bolum).filter(Bolum.ad == ad.strip()).first()
    if b is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")
    return {"bolum_id": b.id, "ad": b.ad}


@router.get("/yokatlas-tani")
def yokatlas_tani():
    """Teknik tanı: YÖK Atlas bağlantısının hangi adımda takıldığını gösterir."""
    return baglanti_tani()


@router.get("/{bolum_id}/bilgi")
def bolum_bilgi(bolum_id: int, db: Session = Depends(get_db), ogrenci=Depends(get_opsiyonel_ogrenci)):
    b = _bolum(db, bolum_id)
    e = db.query(BolumDalEslesme).filter(BolumDalEslesme.bolum_id == b.id).first()
    dal = db.get(Dal, e.dal_id) if e else None
    # [2026-10-10] Haftalık keşif görevi: öğrenci bu bölümün bilgi kartını açınca tamamlanır
    # (eskiden örnek meslekler ucuna bağlıydı; o uç artık ekrandan çağrılmıyordu → görev hiç tamamlanmıyordu)
    if ogrenci is not None and getattr(ogrenci, "__tablename__", "") == "ogrenciler":
        try:
            from app.core.haftalik_servisi import kesif_isaretle
            if kesif_isaretle(db, ogrenci, b.id):
                db.commit()
        except Exception:
            db.rollback()
    return {
        "bolum_id": b.id, "ad": b.ad, "kisa_aciklama": b.kisa_aciklama, "detay": b.detay,
        # Meslek dili: öğrencinin okuluna özel sürüm varsa o, yoksa genel/varsayılan
        "jargon": etkin_surum(db, b, getattr(ogrenci, "okul_id", None))["terimler"],
        "ust_alan": dal.ad if dal and dal.kod.startswith("U") else None,
        "alt_alan": getattr(e, "alt_alan", None) if e else None,
    }


# [2026-10-09] Bölümde ÖNE ÇIKAN özellikler. Her değişkenin iki ucu vardır; puan yüksekse "yüksek" ucu,
# iki uçlu (anlamlı karşıtı olan) değişkenlerde puan düşükse "düşük" ucu öne çıkar. Diğer özellikler
# "düşük" diye etiketlenmez — öğrenciye yanlış mesaj vermesin diye listede gösterilmez.
# (yüksek uç etiketi, düşük uç etiketi | None)
KUTUP_ETIKET = {
    "D1": ("İş güvencesi ve istikrar", None), "D2": ("Yüksek kazanç imkânı", None), "D3": ("Statü ve prestij", None),
    "D4": ("Anlamlı bir iş yapma", None), "D5": ("Topluma katkı", None), "D6": ("Özerklik ve özgürlük", None),
    "D7": ("Estetik ve yaratıcılık", None),
    "P1": ("İnsanlarla iç içe çalışma", "Bağımsız, bireysel çalışma"),
    "P2": ("Uyum ve işbirliği", "Rekabetçi ortam, görüşünü savunma"),
    "P3": ("Sorumluluk ve disiplin", None),
    "P4": ("Duygusal yükle başa çıkabilme", "Sakin, duygusal yükü düşük ortam"),
    "P5": ("Yeniliğe açıklık", None),
    "P6": ("Dinamik, değişken iş ortamı", "Rutin, düzenli iş ortamı"),
    "P7": ("Belirsizlik ve risk alma", None), "P8": ("Liderlik ve yönetme", None),
    "I1": ("Zaman yönetimi ve önceliklendirme", None), "I2": ("Ekip ve çatışma yönetimi", None),
    "I3": ("Baskı altında karar verme", None), "I4": ("Etik ve dürüstlük", None), "I5": ("İnisiyatif alma", None),
    "I6": ("Eleştiriye açıklık", None), "I7": ("Strateji ve iş dünyası bilgisi", None),
    "A1": ("Sayısal düşünme ve veri", None), "A2": ("Sözel ifade ve dil", None), "A3": ("İnsan odaklı alanlar", None),
    "A4": ("Tasarım ve uzamsal düşünme", None), "A5": ("Doğa ve laboratuvar", None), "A6": ("Fiziksel aktivite ve hareket", None),
    # A7/A8 iki ayrı stil değişkeni; düşük uçları birbirinin yüksek ucuyla çakıştığı için yalnızca yüksek uç gösterilir
    "A7": ("Adım adım, yapılandırılmış çalışma", None),
    "A8": ("Büyük resmi görme, sezgisel düşünme", None),
    "A9": ("Girişimcilik ve ikna", None),
}
ONEM_COK, ONEM = 80.0, 65.0      # yüzdelik eşikleri (düşük uç için 100 - eşik)


def _one_cikan(kod: str, yuzdelik: float) -> dict | None:
    yuksek, dusuk = KUTUP_ETIKET.get(kod, (None, None))
    if yuzdelik >= ONEM:
        return {"etiket": yuksek, "uc": "yuksek", "guc": yuzdelik, "onem": "Çok önemli" if yuzdelik >= ONEM_COK else "Önemli"}
    if dusuk and yuzdelik <= 100 - ONEM:
        g = 100 - yuzdelik
        return {"etiket": dusuk, "uc": "dusuk", "guc": g, "onem": "Çok önemli" if g >= ONEM_COK else "Önemli"}
    return None


def _seviye(yuzdelik: float) -> str:
    if yuzdelik >= 80: return "Çok yüksek"
    if yuzdelik >= 60: return "Yüksek"
    if yuzdelik >= 40: return "Orta"
    if yuzdelik >= 20: return "Düşük"
    return "Çok düşük"


_YETKINLIK_ONBELLEK: dict = {"zaman": 0.0, "veri": None}
_YETKINLIK_SURE = 600  # saniye — ağırlıklar yalnızca pipeline yüklemesinde değişir


def _yetkinlik_tablosu(db: Session) -> dict:
    """Tüm yayındaki bölümler için {bolum_id: {katman_id: [değişken satırları]}} — tek geçişte, 10 dk önbellekli."""
    import time
    if _YETKINLIK_ONBELLEK["veri"] is not None and time.time() - _YETKINLIK_ONBELLEK["zaman"] < _YETKINLIK_SURE:
        return _YETKINLIK_ONBELLEK["veri"]
    katmanlar = {k.id: k for k in db.query(Katman).filter(Katman.kosullu_mu.is_(False)).all()}
    haric = {x.strip() for x in (parametre_oku(db, "eslesme_disi_degiskenler", "P4") or "").split(",") if x.strip()}
    degiskenler = [d for d in db.query(Degisken).filter(Degisken.katman_id.in_(list(katmanlar))).order_by(Degisken.id).all()
                   if d.kod not in haric]
    yayinda = {x.id for x in db.query(Bolum.id).filter(Bolum.durum == "yayinda").all()}
    en_guncel: dict[tuple[int, int], tuple[int, float]] = {}
    for a in db.query(BolumAgirligi).filter(BolumAgirligi.degisken_id.in_([d.id for d in degiskenler])).all():
        if a.bolum_id not in yayinda:
            continue
        k = (a.bolum_id, a.degisken_id)
        if k not in en_guncel or a.versiyon > en_guncel[k][0]:
            en_guncel[k] = (a.versiyon, float(a.agirlik_degeri))
    tablo: dict[int, dict[int, list]] = {}
    for d in degiskenler:
        degerler = sorted((v[1], bid) for (bid, did), v in en_guncel.items() if did == d.id)
        n = len(degerler)
        if n == 0:
            continue
        # [2026-10-08] Seviye, sıra yüzdeliği yerine standart puandan (z) normal dağılım karşılığıyla hesaplanır.
        # Dengeli özelliklerde sonuç sıra yüzdeliğiyle aynıdır; çarpık özelliklerde (ör. A6 spor: bölümlerin
        # çoğu "gerekmez" düzeyinde eşit) eşit değerli bölümler arasında yapay sıralama/şişme oluşmaz.
        import math
        sadece = [x for x, _ in degerler]
        ort = sum(sadece) / n
        std = (sum((x - ort) ** 2 for x in sadece) / n) ** 0.5 or 1.0
        for deger, bid in degerler:
            z = (deger - ort) / std
            yuzdelik = round(50.0 * (1.0 + math.erf(z / math.sqrt(2.0))), 1)
            oc = _one_cikan(d.kod, yuzdelik)
            tablo.setdefault(bid, {}).setdefault(d.katman_id, []).append(
                {"kod": d.kod, "ad": d.ad, "aciklama": d.aciklama, "yuzdelik": yuzdelik, "seviye": _seviye(yuzdelik),
                 "one_cikan": oc is not None, "etiket": (oc or {}).get("etiket") or d.ad,
                 "uc": (oc or {}).get("uc"), "guc": round((oc or {}).get("guc", 0.0), 1), "onem": (oc or {}).get("onem")})
    veri = {"tablo": tablo, "katmanlar": {k.id: (k.kod, k.ad, k.sira) for k in katmanlar.values()}, "bolum_sayisi": len(yayinda)}
    _YETKINLIK_ONBELLEK.update(zaman=time.time(), veri=veri)
    return veri


@router.get("/{bolum_id}/yetkinlik")
def bolum_yetkinlik_profili(bolum_id: int, db: Session = Depends(get_db)):
    """
    [2026-10-08] Bölümün K1-K4'teki TÜM değişkenlerde beklenti düzeyi. Ham ağırlık (50 civarı sayılar)
    yerine, bu bölümün o değişkendeki ağırlığının yayındaki tüm bölümler arasındaki yüzdelik sırası
    verilir: 'bu özelliği bölümlerin %X'inden daha çok gerektirir'. Eşleşme dışı değişkenler (P4) gösterilmez.
    """
    b = _bolum(db, bolum_id)
    v = _yetkinlik_tablosu(db)
    gruplar = v["tablo"].get(b.id, {})
    return {
        "bolum_id": b.id,
        "bolum_sayisi": v["bolum_sayisi"],
        "katmanlar": [
            {"kod": v["katmanlar"][kid][0], "ad": v["katmanlar"][kid][1],
             "degiskenler": sorted(satirlar, key=lambda x: -x["yuzdelik"]),
             # [2026-10-09] öğrenciye gösterilen: yalnızca bu bölümde öne çıkanlar, en belirgin olan önce
             "one_cikanlar": sorted([x for x in satirlar if x["one_cikan"]], key=lambda x: -x["guc"])}
            for kid, satirlar in sorted(gruplar.items(), key=lambda kv: v["katmanlar"][kv[0]][2])
        ],
    }


@router.get("/{bolum_id}/universiteler")
def bolum_universite_listesi(bolum_id: int, db: Session = Depends(get_db)):
    return bolum_universiteleri(db, _bolum(db, bolum_id))
