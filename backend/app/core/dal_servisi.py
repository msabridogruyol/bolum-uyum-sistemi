"""
D3 — K5 Dal Derinleşme Modülü iş mantığı.
Kaynak: sistem_genel_anlatim.md D3, A6

Tetikleme kuralı (D3):
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

from app.models import (
    Ogrenci, Katman, Degisken, Dal, Soru, SoruSecenegi,
    OgrenciDegerlendirmeTuru, OgrenciDegiskenSkoru, OgrenciDalOturumu, OgrenciCevap,
)
from app.core.katman_servisi import IsKuraliHatasi, parametre_oku, likert_puan


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
    degisken_id_to_dal = {
        d.bagli_degisken_id: d
        for d in db.query(Dal).filter(Dal.bagli_degisken_id.in_([v.id for v in k4_degiskenler])).all()
    }

    adaylar: list[DalAday] = []
    for degisken in k4_degiskenler:
        dal = degisken_id_to_dal.get(degisken.id)
        if dal is None:
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
            adaylar.append(DalAday(dal=dal, degisken_id=degisken.id, puan=float(skor.puan)))

    return sorted(adaylar, key=lambda a: a.puan, reverse=True)


def k5_tetikle(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict:
    """
    D3 — K4 tamamlandığında çağrılır. Açılan dallar için ogrenci_dal_oturumlari
    satırı oluşturur (durum='baslamadi'). Dönen sözlük, sonuç ekranının
    ihtiyaç duyduğu üç listeyi içerir: acilan, ilgi_gosterilen (derinleştirilmeyen), esik.
    """
    esik = float(parametre_oku(db, "k5_esik_puani", "80"))
    max_dal = int(parametre_oku(db, "k5_max_dal_sayisi", "3"))

    tum_adaylar = k5_adaylarini_hesapla(db, ogrenci, tur)
    esigi_gecenler = [a for a in tum_adaylar if a.puan >= esik]

    if len(esigi_gecenler) == 0:
        # Kural 2: 0 aday varsa en yüksek skorlu 1 dal otomatik seçilir
        acilacaklar = tum_adaylar[:1]
        ilgi_gosterilenler = []
    elif len(esigi_gecenler) <= max_dal:
        # Kural 3: 1-3 aday varsa hepsi açılır
        acilacaklar = esigi_gecenler
        ilgi_gosterilenler = []
    else:
        # Kural 4: en yüksek max_dal kadarı açılır, kalanı bilgi notu olarak kalır
        acilacaklar = esigi_gecenler[:max_dal]
        ilgi_gosterilenler = esigi_gecenler[max_dal:]

    for aday in acilacaklar:
        mevcut = (
            db.query(OgrenciDalOturumu)
            .filter(
                OgrenciDalOturumu.ogrenci_id == ogrenci.id,
                OgrenciDalOturumu.tur_id == tur.id,
                OgrenciDalOturumu.dal_id == aday.dal.id,
            )
            .first()
        )
        if mevcut is None:
            db.add(OgrenciDalOturumu(
                ogrenci_id=ogrenci.id, tur_id=tur.id, dal_id=aday.dal.id, durum="baslamadi",
            ))
    db.flush()

    return {
        "esik": esik,
        "acilan": [{"dal_kodu": a.dal.kod, "dal_adi": a.dal.ad, "puan": a.puan} for a in acilacaklar],
        "ilgi_gosterilen": [{"dal_kodu": a.dal.kod, "dal_adi": a.dal.ad, "puan": a.puan} for a in ilgi_gosterilenler],
    }


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
    sorular = {
        s.id: s for s in db.query(Soru).filter(Soru.degisken_id.in_(degisken_idler)).all()
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
    return sonuc
