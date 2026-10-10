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
    OgrenciBolumUyumSkoru, BolumDalEslesme, BolumAgirligi, OgrenciDalUyumSkoru, BolumK5Bag,
)
from app.core.katman_servisi import IsKuraliHatasi, parametre_oku, likert_puan, cevaplari_puanla
from app.core.skor_motoru import _katman_ici_olcekle

DAL_SECIM_UST_N = 15        # dal seçiminde bakılan ilk N bölüm
IKINCI_DAL_MIN_BOLUM = 4    # ikinci dalın açılması için ilk N'de en az bu kadar bölüm
K5_GUVEN_STD = 15.0         # öğrencinin K5 puanlarında bu std'ye ulaşınca K5 tam etkili; düz profilde etki 0
# [2026-10-08] Yeni K5 (17 üst alan): ana alan = 1. sıradaki bölümün alanı (her zaman açılır).
# İkinci alan: en iyi 3 bölümünün ortalaması ana alanınkine IKINCI_ALAN_FARK puandan yakınsa açılır
# ve ondan yalnızca ilk IKINCI_ALAN_SORU soru sorulur (toplam K5 en fazla 14 + 6 = 20 soru).
IKINCI_ALAN_FARK = 10.0
IKINCI_ALAN_SORU = 6


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
    # [DÜZELTME 2026-10-03] Seçim ve gösterilen puan TEK ölçüye bağlandı: dalın ilk N bölümdeki
    # toplam uyum payı (%). Önceden seçim "bölüm sayısı", puan "ortalama" idi → ekranda daha
    # düşük puanlı dal "en güçlü" görünebiliyordu.
    toplam_pay = sum(sum(v) for v in sayim.values()) or 1.0
    sirali = sorted(sayim.items(), key=lambda kv: (-sum(kv[1]), -len(kv[1])))
    dallar = {d.id: d for d in db.query(Dal).filter(Dal.id.in_(list(sayim.keys()))).all()} if sayim else {}

    def _ozet(dal_id: int) -> dict:
        d = dallar.get(dal_id) or db.get(Dal, dal_id)
        puanlar = sayim.get(dal_id, [])
        pay = round(100.0 * sum(puanlar) / toplam_pay, 1) if puanlar else 0.0
        return {"dal_kodu": d.kod, "dal_adi": d.ad, "puan": pay}  # ilk N bölümdeki uyum payı (%)

    mevcut = (
        db.query(OgrenciDalOturumu)
        .filter(OgrenciDalOturumu.ogrenci_id == ogrenci.id, OgrenciDalOturumu.tur_id == tur.id)
        .order_by(OgrenciDalOturumu.id)
        .all()
    )
    if mevcut:
        acilan_idler = [o.dal_id for o in mevcut]
    elif sirali:
        # [2026-10-08] 'ilk1' kuralı: 1. sıradaki bölümün alanı her zaman açılır (öğrencinin en
        # uygun bölümü hiçbir zaman K5 dışında kalmaz). Diğer alanlar, en iyi 3 bölümünün
        # ortalaması ana alanınkine IKINCI_ALAN_FARK puandan yakınsa açılır (en fazla max_dal).
        def _ust3(liste: list[float]) -> float:
            en_iyi = sorted(liste, reverse=True)[:3]
            return sum(en_iyi) / len(en_iyi)
        ana_id = bolum_dal.get(ust_skorlar[0].bolum_id) if ust_skorlar else None
        if ana_id is None:
            ana_id = sirali[0][0]
        ana_ust3 = _ust3(sayim[ana_id])
        digerleri = sorted(
            [(dal_id, _ust3(liste)) for dal_id, liste in sayim.items() if dal_id != ana_id],
            key=lambda kv: -kv[1],
        )
        acilan_idler = [ana_id] + [
            dal_id for dal_id, ort in digerleri[: max(0, max_dal - 1)] if ana_ust3 - ort <= IKINCI_ALAN_FARK
        ]
        for dal_id in acilan_idler:
            db.add(OgrenciDalOturumu(ogrenci_id=ogrenci.id, tur_id=tur.id, dal_id=dal_id, durum="baslamadi"))
        db.flush()
    else:
        acilan_idler = []

    ilgi_idler = [dal_id for dal_id, liste in sirali if dal_id not in acilan_idler and len(liste) >= 2]
    # açık alanlar açılış sırasıyla döner: önce ana alan (1. sıradaki bölümün alanı)
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

    # [2026-10-08] Yeni K5: bölüm–eksen bağları tanımlıysa, bölümün K5 uyumu = öğrencinin eksen
    # puanlarının bölümün bağlarıyla ağırlıklı ortalaması. (Bağ yoksa eski yöntem çalışır.)
    baglar: dict[int, dict[int, float]] = {}
    for b in db.query(BolumK5Bag).filter(
        BolumK5Bag.bolum_id.in_(bolum_idler), BolumK5Bag.degisken_id.in_(degisken_idler)
    ).all():
        baglar.setdefault(b.bolum_id, {})[b.degisken_id] = float(b.bag)
    if baglar:
        bolum_idler = [b for b in bolum_idler if b in baglar]
        ham = np.array([
            sum(w * puanlar[d] for d, w in baglar[b].items()) / sum(baglar[b].values())
            for b in bolum_idler
        ])
        ogr = np.array([puanlar[d] for d in degisken_idler])
        z = (ham - ham.mean()) / (ham.std() + 1e-9) if len(ham) > 1 else np.zeros(len(ham))
        guven = float(min(1.0, ogr.std() / K5_GUVEN_STD))
        skor = np.clip(50.0 + guven * 15.0 * z, 0.0, 100.0)
        return _dal_ici_kaydet(db, ogrenci, tur, dal, bolum_idler, skor)

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
    # [DÜZELTME 2026-10-03] Önceki sürüm min-max ile her zaman 0-100'e yayıyordu: öğrenci
    # K5'te hep aynı cevabı verse bile (bilgi yok) bölümleri rastgele ödüllendirip cezalandırıyordu.
    # Artık: dal içi z-skoru (50 ± 15) ve öğrencinin K5 cevaplarındaki ayrışma kadar güven katsayısı.
    # Düz profil (std≈0) → herkes 50 = nötr → sıralama değişmez.
    z = (ham - ham.mean()) / (ham.std() + 1e-9)
    guven = float(min(1.0, ogr.std() / K5_GUVEN_STD))
    skor = np.clip(50.0 + guven * 15.0 * z, 0.0, 100.0)
    return _dal_ici_kaydet(db, ogrenci, tur, dal, bolum_idler, skor)


def _dal_ici_kaydet(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru, dal: Dal, bolum_idler: list[int], skor) -> int:
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


def dal_sorulari(db: Session, ogrenci: Ogrenci, dal: Dal, tur: OgrenciDegerlendirmeTuru) -> list[Soru]:
    """
    [2026-10-08] Bu öğrenciye bu alanda sorulacak sorular (oturum başlatma ve tamamlama aynı listeyi kullanır).
    Ana alan (öğrencinin ilk açılan alanı): alanın tüm aktif soruları. Diğer açılan alanlar: yalnızca ilk
    IKINCI_ALAN_SORU soru (soru setleri, ilk sorular kendi içinde dengeli olacak şekilde sıralanmıştır).
    """
    dal_degisken_idler = [d.id for d in db.query(Degisken).filter(Degisken.dal_id == dal.id).all()]
    if not dal_degisken_idler:
        return []
    sorular = (
        db.query(Soru)
        .filter(Soru.degisken_id.in_(dal_degisken_idler), Soru.aktif_mi.is_(True))
        .order_by(Soru.id)
        .all()
    )
    ilk_oturum = (
        db.query(OgrenciDalOturumu)
        .filter(OgrenciDalOturumu.ogrenci_id == ogrenci.id, OgrenciDalOturumu.tur_id == tur.id)
        .order_by(OgrenciDalOturumu.id)
        .first()
    )
    if ilk_oturum is not None and ilk_oturum.dal_id != dal.id:
        sorular = sorular[:IKINCI_ALAN_SORU]
    return sorular


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
        raise IsKuraliHatasi(f"{dal.kod} alan soruları şu an açılamıyor. Biraz sonra tekrar dene ya da rehber öğretmenine bildir.")

    sorular = dal_sorulari(db, ogrenci, dal, tur)
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
    sorular = {s.id: s for s in dal_sorulari(db, ogrenci, dal, tur)}

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

    # [2026-10-08] K1-K4 ile aynı puanlama (likert / en çok-en az senaryo soruları)
    degisken_puanlari = cevaplari_puanla(db, sorular, cevaplar)

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
