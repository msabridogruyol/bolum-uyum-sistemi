"""
D3 — K5 Dal Derinleşme Modülü iş mantığı.
Kaynak: sistem_genel_anlatim.md D3, A6

[YENİ KURAL 2026-10-03] Dal artık K4'teki tek bir değişkene göre değil,
öğrencinin K1-K4 sonrası BÖLÜM LİSTESİNE göre açılır: ilk 15 bölümde en çok
temsil edilen dal her zaman açılır; ikinci dal, ilk 15'te en az 4 bölümü
varsa açılır (en fazla k5_max_dal_sayisi). Böylece açılan dal ile sonuç
listesi her zaman tutarlıdır. Dal tamamlanınca o dalın bölümleri için
dal_ici_uyum hesaplanır ve sonuç sıralamasına %30 ağırlıkla katılır
(bkz. skor_motoru.siralama_getir).

ESKİ tetikleme kuralı (artık kullanılmıyor, k5_adaylarini_hesapla korunuyor):
  1. K4'ün (Alan Eğilimi) 9 boyutundan skoru >= k5_esik_puani olanlar aday dal.
  2. 0 aday varsa -> en yüksek skorlu 1 dal otomatik seçilir.
  3. 1-3 aday varsa -> hepsi açılır.
  4. 3'ten fazla aday varsa -> en yüksek 3'ü açılır (k5_max_dal_sayisi),
     kalanlar "ayrıca ilgi gösterdiğin alanlar" olarak yalnızca bilgi
     amaçlı listelenir, oturum açılmaz.

K5'in yeni sorularının şema bağlantısı [ÇIKARIM/EKLENDİ, bkz. models/icerik_yapisi.py
Degisken.dal_id] burada devreye girer: bir dal oturumu başlatıldığında,
o dala ait (degiskenler.dal_id = dal.id) değişkenlere bağlı sorular sorulur.
"""
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

import numpy as np

from app.models import (
    Ogrenci, Katman, Degisken, Dal, Soru, SoruSecenegi,
    OgrenciDegerlendirmeTuru, OgrenciDegiskenSkoru, OgrenciDalOturumu, OgrenciCevap,
    OgrenciBolumUyumSkoru, BolumDalEslesme, BolumAgirligi, OgrenciDalUyumSkoru,
)
from app.core.katman_servisi import IsKuraliHatasi, parametre_oku, likert_puan
from app.core.skor_motoru import _katman_ici_olcekle

DAL_SECIM_UST_N = 15        # dal seçiminde bakılan ilk N bölüm
IKINCI_DAL_MIN_BOLUM = 4    # ikinci dalın açılması için ilk N'de en az bu kadar bölüm


class DalAday:
    def __init__(self, dal: Dal, degisken_id: int, puan: float):
        self.dal = dal
        self.degisken_id = degisken_id
        self.puan = puan


def k5_adaylarini_hesapla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> list[DalAday]:
    """
    K4 katmanındaki her değişken için öğrencinin puanını, o değişkene bağlı
    dalın bilgisiyle birlikte döner (aday olsun olmasın hepsi) — eşik
    filtrelemesi ayrı bir adımda yapılır ki UI'da "eşiğe yakın ama
    derinleştirilmedi" notunu göstermek mümkün olsun.
    """
    k4 = db.query(Katman).filter(Katman.kod == "K4").first()
    if k4 is None:
        return []

    k4_degiskenler = db.query(Degisken).filter(Degisken.katman_id == k4.id).all()
    # [DÜZELTME 2026-10-03] Önceden {degisken_id: dal} sözlüğüydü — aynı K4
    # değişkenine bağlı İKİ dal varsa (örn. A5 → Sağlık ve Doğa Bilimleri)
    # biri sessizce eziliyordu. Artık her değişken bir dal LİSTESİNE eşleniyor.
    degisken_id_to_dallar: dict[int, list[Dal]] = {}
    for d in db.query(Dal).filter(Dal.bagli_degisken_id.in_([v.id for v in k4_degiskenler])).order_by(Dal.id).all():
        degisken_id_to_dallar.setdefault(d.bagli_degisken_id, []).append(d)

    adaylar: list[DalAday] = []
    for degisken in k4_degiskenler:
        dallar = degisken_id_to_dallar.get(degisken.id)
        if not dallar:
            continue  # bu K4 değişkenine bağlı bir dal tanımlanmamış
        skor = (
            db.query(OgrenciDegiskenSkoru)
            .filter(
                OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id,
                OgrenciDegiskenSkoru.tur_id == tur.id,
                OgrenciDegiskenSkoru.degisken_id == degisken.id,
            )
            .first()
        )
        if skor is not None:
            for dal in dallar:
                adaylar.append(DalAday(dal=dal, degisken_id=degisken.id, puan=float(skor.puan)))

    return sorted(adaylar, key=lambda a: a.puan, reverse=True)


def k5_tetikle(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict:
    """
    [YENİ KURAL 2026-10-03] K1-K4 bitip TOPLAM_UYUM hesaplandıktan sonra çağrılır.
    Bu tur için zaten açılmış dal varsa onları döner (idempotent, sonradan değişmez).
    Yoksa: ilk DAL_SECIM_UST_N bölümün dallarını sayar; en çok temsil edilen dal
    her zaman açılır, sonrakiler IKINCI_DAL_MIN_BOLUM şartıyla (en fazla k5_max_dal_sayisi).
    TOPLAM_UYUM henüz yoksa (K1-K4 bitmemiş) hiçbir dal açılmaz.
    """
    esik = float(parametre_oku(db, "k5_esik_puani", "70"))
    max_dal = int(parametre_oku(db, "k5_max_dal_sayisi", "2"))

    ust_skorlar = (
        db.query(OgrenciBolumUyumSkoru)
        .filter(OgrenciBolumUyumSkoru.ogrenci_id == ogrenci.id, OgrenciBolumUyumSkoru.tur_id == tur.id)
        .order_by(OgrenciBolumUyumSkoru.toplam_uyum.desc())
        .limit(DAL_SECIM_UST_N)
        .all()
    )
    bolum_dal = {
        e.bolum_id: e.dal_id
        for e in db.query(BolumDalEslesme).filter(
            BolumDalEslesme.bolum_id.in_([u.bolum_id for u in ust_skorlar])
        ).all()
    } if ust_skorlar else {}

    sayim: dict[int, list[float]] = {}
    for u in ust_skorlar:
        dal_id = bolum_dal.get(u.bolum_id)
        if dal_id is not None:
            sayim.setdefault(dal_id, []).append(float(u.toplam_uyum))
    sirali = sorted(sayim.items(), key=lambda kv: (-len(kv[1]), -sum(kv[1]) / len(kv[1])))
    dallar = {d.id: d for d in db.query(Dal).filter(Dal.id.in_(list(sayim.keys()))).all()} if sayim else {}

    def _ozet(dal_id: int) -> dict:
        d = dallar.get(dal_id) or db.get(Dal, dal_id)
        puanlar = sayim.get(dal_id, [])
        ort = round(sum(puanlar) / len(puanlar), 1) if puanlar else 0.0
        return {"dal_kodu": d.kod, "dal_adi": d.ad, "puan": ort}

    mevcut = (
        db.query(OgrenciDalOturumu)
        .filter(OgrenciDalOturumu.ogrenci_id == ogrenci.id, OgrenciDalOturumu.tur_id == tur.id)
        .order_by(OgrenciDalOturumu.id)
        .all()
    )
    if mevcut:
        acilan_idler = [o.dal_id for o in mevcut]
    elif sirali:
        acilan_idler = [sirali[0][0]] + [
            dal_id for dal_id, liste in sirali[1:max_dal] if len(liste) >= IKINCI_DAL_MIN_BOLUM
        ]
        for dal_id in acilan_idler:
            db.add(OgrenciDalOturumu(ogrenci_id=ogrenci.id, tur_id=tur.id, dal_id=dal_id, durum="baslamadi"))
        db.flush()
    else:
        acilan_idler = []

    ilgi_idler = [dal_id for dal_id, liste in sirali if dal_id not in acilan_idler and len(liste) >= 2]
    return {
        "esik": esik,
        "acilan": [_ozet(i) for i in acilan_idler],
        "ilgi_gosterilen": [_ozet(i) for i in ilgi_idler],
    }


def dal_ici_uyum_hesapla(db: Session, ogrenci: Ogrenci, dal: Dal, tur: OgrenciDegerlendirmeTuru) -> int:
    """
    [YENİ 2026-10-03] Dal tamamlanınca: o dalın bölümleri için öğrencinin K5
    değişken profili ile bölümün aynı değişkenlerdeki ağırlıkları, TOPLAM_UYUM ile
    aynı göreli yöntemle (katman içi ölçekleme) karşılaştırılır; dal içinde 0-100'e
    yayılır ve ogrenci_dal_uyum_skorlari'na yazılır. Dönen: kaç bölüm için hesaplandı.
    """
    degiskenler = db.query(Degisken).filter(Degisken.dal_id == dal.id).order_by(Degisken.id).all()
    degisken_idler = [d.id for d in degiskenler]
    puanlar = {
        s.degisken_id: float(s.puan)
        for s in db.query(OgrenciDegiskenSkoru).filter(
            OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id,
            OgrenciDegiskenSkoru.tur_id == tur.id,
            OgrenciDegiskenSkoru.degisken_id.in_(degisken_idler),
        ).all()
    }
    degisken_idler = [d for d in degisken_idler if d in puanlar]
    bolum_idler = [e.bolum_id for e in db.query(BolumDalEslesme).filter(BolumDalEslesme.dal_id == dal.id).all()]
    if len(degisken_idler) < 2 or not bolum_idler:
        return 0

    en_guncel: dict[tuple[int, int], tuple[int, float]] = {}
    for a in db.query(BolumAgirligi).filter(
        BolumAgirligi.bolum_id.in_(bolum_idler), BolumAgirligi.degisken_id.in_(degisken_idler)
    ).all():
        anahtar = (a.bolum_id, a.degisken_id)
        if anahtar not in en_guncel or a.versiyon > en_guncel[anahtar][0]:
            en_guncel[anahtar] = (a.versiyon, float(a.agirlik_degeri))

    ogr = np.array([[puanlar[d] for d in degisken_idler]])
    blm = np.array([[en_guncel.get((b, d), (0, 50.0))[1] for d in degisken_idler] for b in bolum_idler])
    grup = [list(range(len(degisken_idler)))]
    perf = np.maximum(0.0, 100.0 - np.abs(_katman_ici_olcekle(ogr, grup) - _katman_ici_olcekle(blm, grup)))
    ham = perf.mean(axis=1)
    lo, hi = ham.min(), ham.max()
    skor = np.full_like(ham, 50.0) if hi - lo < 1e-9 else (ham - lo) / (hi - lo) * 100

    db.query(OgrenciDalUyumSkoru).filter(
        OgrenciDalUyumSkoru.ogrenci_id == ogrenci.id,
        OgrenciDalUyumSkoru.tur_id == tur.id,
        OgrenciDalUyumSkoru.dal_id == dal.id,
    ).delete()
    for bolum_id, deger in zip(bolum_idler, skor):
        db.add(OgrenciDalUyumSkoru(
            ogrenci_id=ogrenci.id, tur_id=tur.id, dal_id=dal.id, bolum_id=bolum_id,
            dal_ici_uyum=round(float(deger), 2),
        ))
    db.flush()
    return len(bolum_idler)


def bekleyen_dal_var_mi(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> bool:
    """
    [YENİ 2026-10-03] K5 zorunlu kuralı — açılmış ama tamamlanmamış bir dal
    oturumu varsa True döner; sonuç ekranı bu durumda gösterilmez.
    Sorusu olmayan bir dal (içerik eksikliği) öğrenciyi kilitlemesin diye sayılmaz.
    """
    oturumlar = (
        db.query(OgrenciDalOturumu)
        .filter(
            OgrenciDalOturumu.ogrenci_id == ogrenci.id,
            OgrenciDalOturumu.tur_id == tur.id,
            OgrenciDalOturumu.durum != "tamamlandi",
        )
        .all()
    )
    for o in oturumlar:
        dal_degisken_idler = [d.id for d in db.query(Degisken).filter(Degisken.dal_id == o.dal_id).all()]
        if not dal_degisken_idler:
            continue
        soru_var = (
            db.query(Soru.id)
            .filter(Soru.degisken_id.in_(dal_degisken_idler), Soru.aktif_mi.is_(True))
            .first()
        )
        if soru_var is not None:
            return True
    return False


def dal_bul(db: Session, kod: str) -> Dal:
    dal = db.query(Dal).filter(Dal.kod == kod.upper()).first()
    if dal is None:
        raise IsKuraliHatasi(f"Dal bulunamadı: {kod}")
    return dal


def dal_oturumu_baslat(db: Session, ogrenci: Ogrenci, dal: Dal, tur: OgrenciDegerlendirmeTuru) -> tuple[OgrenciDalOturumu, list[Soru]]:
    oturum = (
        db.query(OgrenciDalOturumu)
        .filter(
            OgrenciDalOturumu.ogrenci_id == ogrenci.id,
            OgrenciDalOturumu.tur_id == tur.id,
            OgrenciDalOturumu.dal_id == dal.id,
        )
        .first()
    )
    if oturum is None:
        raise IsKuraliHatasi(f"{dal.kod} senin için açılmamış — K5 eşiğini geçmemiş olabilirsin.")
    if oturum.durum == "tamamlandi":
        raise IsKuraliHatasi(f"{dal.kod} bu tur için zaten tamamlandı.")

    dal_degiskenleri = db.query(Degisken).filter(Degisken.dal_id == dal.id).all()
    if not dal_degiskenleri:
        raise IsKuraliHatasi(f"{dal.kod} için henüz soru tanımlanmamış (admin P6 aşaması tamamlanmamış olabilir).")

    sorular = (
        db.query(Soru)
        .filter(Soru.degisken_id.in_([d.id for d in dal_degiskenleri]), Soru.aktif_mi.is_(True))
        .order_by(Soru.id)
        .all()
    )
    if not sorular:
        raise IsKuraliHatasi(f"{dal.kod} için aktif soru bulunamadı.")

    oturum.durum = "devam_ediyor"
    if oturum.baslama_zamani is None:
        oturum.baslama_zamani = datetime.now(timezone.utc)
    db.flush()
    return oturum, sorular


def dali_tamamla(db: Session, ogrenci: Ogrenci, dal: Dal, tur: OgrenciDegerlendirmeTuru, oturum: OgrenciDalOturumu) -> list[tuple[int, float]]:
    """
    K1-K4 ile BİREBİR AYNI mekanizma (D3'ün kendi ilkesi) — katman_servisi'ndeki
    likert_puan formülü tekrar kullanılır, sonuç ogrenci_degisken_skorlari'na
    (aynı tabloya, K5'in değişkenleriyle) yazılır.
    """
    dal_degiskenleri = db.query(Degisken).filter(Degisken.dal_id == dal.id).all()
    degisken_idler = [d.id for d in dal_degiskenleri]
    # [DÜZELTME] aktif_mi filtresi eklendi — dal_oturumu_baslat yalnızca aktif
    # soruları soruyor; burada pasif sorular da sayılırsa "cevaplanmadı" hatası çıkar.
    sorular = {
        s.id: s for s in db.query(Soru).filter(Soru.degisken_id.in_(degisken_idler), Soru.aktif_mi.is_(True)).all()
    }

    cevaplar = (
        db.query(OgrenciCevap)
        .filter(
            OgrenciCevap.ogrenci_id == ogrenci.id,
            OgrenciCevap.tur_id == tur.id,
            OgrenciCevap.soru_id.in_(sorular.keys()),
        )
        .all()
    )
    cevaplanan = {c.soru_id for c in cevaplar}
    eksik = set(sorular.keys()) - cevaplanan
    if eksik:
        raise IsKuraliHatasi(f"{len(eksik)} soru henüz cevaplanmadı — dal tamamlanamaz.")

    degisken_puanlari: dict[int, list[float]] = {}
    for cevap in cevaplar:
        soru = sorular[cevap.soru_id]
        if soru.degisken_id is None:
            continue
        secenek = db.get(SoruSecenegi, cevap.secenek_id)
        toplam_secenek = db.query(func.count(SoruSecenegi.id)).filter(SoruSecenegi.soru_id == soru.id).scalar()
        puan = likert_puan(secenek.secenek_sirasi, toplam_secenek, soru.ters_kodlanmis_mi)
        degisken_puanlari.setdefault(soru.degisken_id, []).append(puan)

    sonuc: list[tuple[int, float]] = []
    for degisken_id, puanlar in degisken_puanlari.items():
        nihai = round(sum(puanlar) / len(puanlar), 2)
        mevcut_skor = (
            db.query(OgrenciDegiskenSkoru)
            .filter(
                OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id,
                OgrenciDegiskenSkoru.tur_id == tur.id,
                OgrenciDegiskenSkoru.degisken_id == degisken_id,
            )
            .first()
        )
        if mevcut_skor is not None:
            mevcut_skor.puan = nihai
        else:
            db.add(OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur.id, degisken_id=degisken_id, puan=nihai))
        sonuc.append((degisken_id, nihai))

    oturum.durum = "tamamlandi"
    oturum.tamamlanma_zamani = datetime.now(timezone.utc)
    db.flush()
    dal_ici_uyum_hesapla(db, ogrenci, dal, tur)  # [YENİ] K5 sonucu sıralamaya yansısın
    return sonuc
