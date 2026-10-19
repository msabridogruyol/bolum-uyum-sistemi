"""
K5 — İş türü tercihleriyle sıralamayı netleştirme.

[2026-10-18] YENİ K5 (alan bazlı K5'in yerine):
  1. Küme: K1-K4 bitince öğrencinin uyum puanı ≥ KUME_ESIK (70) olan bölümler alınır; en fazla KUME_EN_FAZLA (20),
     en az KUME_EN_AZ (5) bölüm. Puanlar göreli olduğundan (en iyi bölüm ≈100) "≥70" = en iyi bölüme 30 puandan yakın.
  2. İş türleri: kümedeki bölümlerin bağlı olduğu iş türleri (bolum_k5_baglari) toplanır; alan sınırı yoktur.
  3. Sorular öğrenciye özel üretilir (sorular.ogrenci_id / tur_id dolu) ve tur başına sabittir (tohum = tur_id):
     soru sayısı = iş türü sayısı × 3/4 (en az 6, en fazla 15); yaklaşık %50 en çok / en az, %20 tek seçim
     (tarama: her iş türü dengeli sayıda görünür), %30 uçlar (kapıştırma: K1-K4'te birbirine en yakın bölüm
     çiftlerinin ana iş türleri karşı karşıya). Cümleler k5_cumleleri, kökler k5_soru_kokleri tablosundadır.
  4. Puan: her iş türü 0-100 (K1-K4 ile aynı puanlama kuralları). Bölümün K5 puanı = bağlı iş türlerinin bağ ağırlıklı
     ortalaması; öğrencinin iş türü puanları düzse (std < K5_GUVEN_STD) etki orantılı olarak 50'ye (nötr) çekilir.
  5. Sıralama: kümedeki bölümler kendi aralarında yeniden sıralanır (skor_motoru.k5_nihai, katsayı 0,15).

Eski alan bazlı K5 (17 üst alan, alan açma, alan içi göreli puan) kaldırıldı: simülasyonda doğru bölümü ezip
tekrar tutarlılığını bozuyordu. Dış arayüz (k5_tetikle, dal_oturumu_baslat, dali_tamamla, dal_sorulari,
bekleyen_dal_var_mi, dal_bul) aynı kaldı; öğrenci tek bir "dal" (K5_DAL_KODU) oturumu görür.
"""
import itertools
import math
import random
from datetime import datetime, timezone

import numpy as np
from sqlalchemy.orm import Session

from app.core.katman_servisi import IsKuraliHatasi, cevaplari_puanla
from app.core.skor_motoru import K5_DAL_KODU
from app.models import (
    BolumK5Bag, Dal, Degisken, K5Cumle, K5SoruKoku, Katman, Ogrenci, OgrenciBolumUyumSkoru, OgrenciCevap,
    OgrenciDalOturumu, OgrenciDalUyumSkoru, OgrenciDegerlendirmeTuru, OgrenciDegiskenSkoru, SjtSecenekDegiskenAgirlik,
    Soru, SoruSecenegi,
)

KUME_ESIK = 70.0
KUME_EN_AZ = 5
KUME_EN_FAZLA = 20
SORU_EN_AZ = 6
SORU_EN_FAZLA = 15
PAY_UCLAR = 0.30
PAY_TEK = 0.20
K5_GUVEN_STD = 15.0         # öğrencinin iş türü puanlarında bu std'ye ulaşınca K5 tam etkili; düz profilde etki 0
UCLAR_ADAY_BOLUM = 8        # kapıştırma çiftleri K1-K4'teki ilk 8 küme bölümünden kurulur
KUTUP_SECENEKLERI = ("Kesinlikle A", "Daha çok A", "Daha çok B", "Kesinlikle B")


# ----------------------------------------------------------------------------------------------------------------
# Küme ve iş türleri
# ----------------------------------------------------------------------------------------------------------------
def k5_dali(db: Session) -> Dal | None:
    return db.query(Dal).filter(Dal.kod == K5_DAL_KODU).first()


def kume_sec(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> list[tuple[int, float]]:
    """[(bolum_id, K1-K4 uyumu)] — büyükten küçüğe; ≥ KUME_ESIK olanlar, en az KUME_EN_AZ, en fazla KUME_EN_FAZLA."""
    satirlar = sorted(
        ((s.bolum_id, float(s.toplam_uyum)) for s in db.query(OgrenciBolumUyumSkoru).filter(
            OgrenciBolumUyumSkoru.ogrenci_id == ogrenci.id, OgrenciBolumUyumSkoru.tur_id == tur.id).all()),
        key=lambda x: (-x[1], x[0]))
    ust = [x for x in satirlar if x[1] >= KUME_ESIK][:KUME_EN_FAZLA]
    return satirlar[:KUME_EN_AZ] if len(ust) < KUME_EN_AZ else ust


def _baglar(db: Session, bolum_idler) -> dict[int, dict[int, float]]:
    sonuc: dict[int, dict[int, float]] = {}
    for b in db.query(BolumK5Bag).filter(BolumK5Bag.bolum_id.in_(list(bolum_idler) or [-1])).all():
        sonuc.setdefault(b.bolum_id, {})[b.degisken_id] = float(b.bag)
    return sonuc


def _cumleler(db: Session, degisken_idler) -> dict[int, list[str]]:
    sonuc: dict[int, list[str]] = {}
    for c in (db.query(K5Cumle).filter(K5Cumle.degisken_id.in_(list(degisken_idler) or [-1]), K5Cumle.aktif_mi.is_(True))
              .order_by(K5Cumle.degisken_id, K5Cumle.sira).all()):
        sonuc.setdefault(c.degisken_id, []).append(c.metin)
    return sonuc


def _kokler(db: Session) -> dict[str, list[str]]:
    sonuc: dict[str, list[str]] = {"encok": [], "tek": [], "kutup": []}
    for k in db.query(K5SoruKoku).filter(K5SoruKoku.aktif_mi.is_(True)).order_by(K5SoruKoku.id).all():
        sonuc.setdefault(k.tip, []).append(k.metin)
    return sonuc


# ----------------------------------------------------------------------------------------------------------------
# Soru planı (saf fonksiyon: test edilebilir, veritabanına dokunmaz)
# ----------------------------------------------------------------------------------------------------------------
def soru_plani(kume: list[tuple[int, float]], baglar: dict[int, dict[int, float]], cumleler: dict[int, list[str]],
               kokler: dict[str, list[str]], tohum: int) -> list[dict]:
    """Öğrenciye sorulacak K5 sorularının planı.
    Dönen her soru: {"tip": "encok"|"tek"|"kutup", "kok": str, "secenekler": [(degisken_id, cümle), ...]} — kutupta
    secenekler tam 2 öğedir (A, B)."""
    r = random.Random(tohum)
    eksenler = sorted({e for b, _ in kume for e in baglar.get(b, {}) if cumleler.get(e)})
    if len(eksenler) < 2:
        return []
    nq = min(SORU_EN_FAZLA, max(SORU_EN_AZ, math.ceil(len(eksenler) * 3 / 4)))
    n_uc = round(nq * PAY_UCLAR)
    n_tek = round(nq * PAY_TEK)
    n_encok = nq - n_uc - n_tek

    # kapıştırma çiftleri: K1-K4'te birbirine en yakın bölümlerin ana iş türleri (farklı olmalı)
    def ana(b):
        d = {e: w for e, w in baglar.get(b, {}).items() if cumleler.get(e)}
        return max(sorted(d), key=lambda e: d[e]) if d else None
    adaylar = [(b, u) for b, u in kume[:UCLAR_ADAY_BOLUM] if ana(b) is not None]
    ciftler, gorulen = [], set()
    for (a, ua), (b, ub) in sorted(itertools.combinations(adaylar, 2), key=lambda p: (abs(p[0][1] - p[1][1]), p[0][0], p[1][0])):
        ea, eb = ana(a), ana(b)
        if ea == eb or frozenset((ea, eb)) in gorulen:
            continue
        gorulen.add(frozenset((ea, eb)))
        ciftler.append((ea, eb) if r.random() < 0.5 else (eb, ea))
    n_uc = min(n_uc, len(ciftler))
    n_encok = nq - n_uc - n_tek

    say = {e: 0 for e in eksenler}
    cumle_sirasi = {e: r.sample(range(len(cumleler[e])), len(cumleler[e])) for e in eksenler}
    kullanilan = {e: 0 for e in eksenler}

    def cumle(e):
        i = cumle_sirasi[e][kullanilan[e] % len(cumle_sirasi[e])]
        kullanilan[e] += 1
        return cumleler[e][i]

    def sec(n):
        n = min(n, len(eksenler))
        secilen = sorted(eksenler, key=lambda e: (say[e], r.random()))[:n]
        r.shuffle(secilen)
        for e in secilen:
            say[e] += 1
        return secilen

    kok_sira = {t: r.sample(kokler.get(t) or [""], len(kokler.get(t) or [""])) for t in ("encok", "tek", "kutup")}
    kok_i = {t: 0 for t in kok_sira}

    def kok(t):
        k = kok_sira[t][kok_i[t] % len(kok_sira[t])]
        kok_i[t] += 1
        return k

    tarama = ["encok"] * n_encok + ["tek"] * n_tek
    r.shuffle(tarama)
    plan = []
    for tip in tarama:
        plan.append({"tip": tip, "kok": kok(tip), "secenekler": [(e, cumle(e)) for e in sec(4)]})
    uclar = []
    for ea, eb in ciftler[:n_uc]:
        say[ea] += 1
        say[eb] += 1
        uclar.append({"tip": "kutup", "kok": kok("kutup"), "secenekler": [(ea, cumle(ea)), (eb, cumle(eb))]})
    # uçlar soruları sona yığılmasın: tarama soruları arasına eşit aralıklarla yerleştirilir (2., …)
    for j, u in enumerate(uclar):
        plan.insert(min(len(plan), round((j + 0.5) * (len(plan) + len(uclar)) / len(uclar))), u)
    return plan


def bolum_k5_puanlari(kume_bolumleri, baglar: dict[int, dict[int, float]], puan: dict[int, float]) -> dict[int, float]:
    """Kümedeki her bölüm için K5 puanı (0-100, 50 nötr): ölçülen bağlı iş türlerinin bağ ağırlıklı ortalaması;
    öğrencinin iş türü puanlarının yayılımı K5_GUVEN_STD'nin altındaysa orantılı olarak 50'ye çekilir.
    Ölçülen iş türü olmayan bölüm 50 alır (sırası değişmez ama kümede kalır)."""
    olculen = [v for v in puan.values()]
    guven = float(min(1.0, (np.std(olculen) / K5_GUVEN_STD) if len(olculen) > 1 else 0.0))
    sonuc = {}
    for b in kume_bolumleri:
        ws = [(w, puan[e]) for e, w in baglar.get(b, {}).items() if e in puan]
        ham = sum(w * p for w, p in ws) / sum(w for w, _ in ws) if ws else 50.0
        sonuc[b] = round(50.0 + guven * (ham - 50.0), 2)
    return sonuc


# ----------------------------------------------------------------------------------------------------------------
# Akış (öğrenci API'sinin kullandığı dış arayüz)
# ----------------------------------------------------------------------------------------------------------------
def dal_bul(db: Session, kod: str) -> Dal:
    dal = db.query(Dal).filter(Dal.kod == kod.upper()).first()
    if dal is None:
        raise IsKuraliHatasi(f"Dal bulunamadı: {kod}")
    return dal


def k5_tetikle(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict:
    """K1-K4 bitip uyum puanları hesaplandıktan sonra çağrılır; idempotent. Kümede en az 2 iş türü (cümlesi olan)
    varsa tek bir K5 oturumu açılır. Dönen: {"esik", "acilan": [{dal_kodu, dal_adi, puan}], "ilgi_gosterilen": []}
    — puan = kümedeki bölüm sayısı."""
    dal = k5_dali(db)
    sonuc = {"esik": KUME_ESIK, "acilan": [], "ilgi_gosterilen": []}
    if dal is None:
        return sonuc
    kume = kume_sec(db, ogrenci, tur)
    oturum = (db.query(OgrenciDalOturumu)
              .filter(OgrenciDalOturumu.ogrenci_id == ogrenci.id, OgrenciDalOturumu.tur_id == tur.id,
                      OgrenciDalOturumu.dal_id == dal.id).first())
    if oturum is None:
        if not kume:
            return sonuc
        baglar = _baglar(db, [b for b, _ in kume])
        eksenler = {e for d in baglar.values() for e in d}
        if len(_cumleler(db, eksenler)) < 2:
            return sonuc
        oturum = OgrenciDalOturumu(ogrenci_id=ogrenci.id, tur_id=tur.id, dal_id=dal.id, durum="baslamadi")
        db.add(oturum)
        db.flush()
    sonuc["acilan"] = [{"dal_kodu": dal.kod, "dal_adi": dal.ad, "puan": float(len(kume)), "durum": oturum.durum}]
    return sonuc


def dal_sorulari(db: Session, ogrenci: Ogrenci, dal: Dal, tur: OgrenciDegerlendirmeTuru) -> list[Soru]:
    """Bu öğrenciye bu turda üretilmiş K5 soruları (oturum başlatılmadıysa boş)."""
    if dal.kod != K5_DAL_KODU:
        return []
    return (db.query(Soru).filter(Soru.ogrenci_id == ogrenci.id, Soru.tur_id == tur.id, Soru.aktif_mi.is_(True))
            .order_by(Soru.id).all())


def _sorulari_uret(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> list[Soru]:
    k5_katman = db.query(Katman).filter(Katman.kod == "K5").first()
    if k5_katman is None:
        raise IsKuraliHatasi("K5 katmanı tanımlı değil. Rehber öğretmenine bildir.")
    kume = kume_sec(db, ogrenci, tur)
    baglar = _baglar(db, [b for b, _ in kume])
    cumleler = _cumleler(db, {e for d in baglar.values() for e in d})
    plan = soru_plani(kume, baglar, cumleler, _kokler(db), tohum=int(tur.id))
    for p in plan:
        if p["tip"] == "kutup":
            (ea, ma), (eb, mb) = p["secenekler"]
            soru = Soru(katman_id=k5_katman.id, degisken_id=ea, b_ucu_degisken_id=eb, soru_tipi="kutup",
                        soru_metni=p["kok"], cevap_bicimi="tek", aktif_mi=True, ogrenci_id=ogrenci.id, tur_id=tur.id,
                        uc_a_metni=ma, uc_b_metni=mb)
            db.add(soru)
            db.flush()
            for i, metin in enumerate(KUTUP_SECENEKLERI, start=1):
                db.add(SoruSecenegi(soru_id=soru.id, secenek_sirasi=i, secenek_metni=metin))
        else:
            soru = Soru(katman_id=k5_katman.id, soru_tipi="sjt", soru_metni=p["kok"], aktif_mi=True,
                        cevap_bicimi="encok_enaz" if p["tip"] == "encok" else "tek",
                        ogrenci_id=ogrenci.id, tur_id=tur.id)
            db.add(soru)
            db.flush()
            for i, (e, metin) in enumerate(p["secenekler"], start=1):
                sec = SoruSecenegi(soru_id=soru.id, secenek_sirasi=i, secenek_metni=metin)
                db.add(sec)
                db.flush()
                db.add(SjtSecenekDegiskenAgirlik(secenek_id=sec.id, degisken_id=e, agirlik=1))
    db.flush()
    return dal_sorulari(db, ogrenci, k5_dali(db), tur)


def dal_oturumu_baslat(db: Session, ogrenci: Ogrenci, dal: Dal, tur: OgrenciDegerlendirmeTuru) -> tuple[OgrenciDalOturumu, list[Soru]]:
    # Satır kilidi: aynı anda gelen iki "başla" isteği (çift tıklama, iki sekme, React geliştirme kipinde çift çağrı)
    # soruları iki kez üretmesin — ikinci istek ilki bitene kadar bekler, sonra üretilmiş soruları görür.
    oturum = (db.query(OgrenciDalOturumu)
              .filter(OgrenciDalOturumu.ogrenci_id == ogrenci.id, OgrenciDalOturumu.tur_id == tur.id,
                      OgrenciDalOturumu.dal_id == dal.id).with_for_update().first())
    if oturum is None or dal.kod != K5_DAL_KODU:
        raise IsKuraliHatasi("Bu bölüm senin için açılmadı.")
    if oturum.durum == "tamamlandi":
        raise IsKuraliHatasi("Bu soruları bu turda zaten tamamladın.")
    sorular = dal_sorulari(db, ogrenci, dal, tur) or _sorulari_uret(db, ogrenci, tur)
    if not sorular:
        raise IsKuraliHatasi("Şu an soru yok. Biraz sonra tekrar dene ya da rehber öğretmenine bildir.")
    oturum.durum = "devam_ediyor"
    if oturum.baslama_zamani is None:
        oturum.baslama_zamani = datetime.now(timezone.utc)
    db.flush()
    return oturum, sorular


def dali_tamamla(db: Session, ogrenci: Ogrenci, dal: Dal, tur: OgrenciDegerlendirmeTuru, oturum: OgrenciDalOturumu) -> list[tuple[int, float]]:
    """Cevapları K1-K4 ile aynı kurallarla iş türü puanlarına çevirir (ogrenci_degisken_skorlari), ardından kümedeki
    bölümlerin K5 puanlarını yazar (ogrenci_dal_uyum_skorlari). Dönen: [(degisken_id, puan)]."""
    sorular = {s.id: s for s in dal_sorulari(db, ogrenci, dal, tur)}
    cevaplar = (db.query(OgrenciCevap).filter(OgrenciCevap.ogrenci_id == ogrenci.id, OgrenciCevap.tur_id == tur.id,
                                              OgrenciCevap.soru_id.in_(list(sorular) or [-1])).all())
    eksik = set(sorular) - {c.soru_id for c in cevaplar}
    if eksik:
        raise IsKuraliHatasi(f"{len(eksik)} soruyu henüz cevaplamadın. Bitirmek için hepsini cevapla.")

    degisken_puanlari = cevaplari_puanla(db, sorular, cevaplar)
    puan: dict[int, float] = {}
    sonuc: list[tuple[int, float]] = []
    for degisken_id, puanlar in degisken_puanlari.items():
        nihai = round(sum(puanlar) / len(puanlar), 2)
        puan[degisken_id] = nihai
        mevcut = (db.query(OgrenciDegiskenSkoru).filter(
            OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id, OgrenciDegiskenSkoru.tur_id == tur.id,
            OgrenciDegiskenSkoru.degisken_id == degisken_id).first())
        if mevcut is not None:
            mevcut.puan = nihai
        else:
            db.add(OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur.id, degisken_id=degisken_id, puan=nihai))
        sonuc.append((degisken_id, nihai))

    kume = [b for b, _ in kume_sec(db, ogrenci, tur)]
    k5 = bolum_k5_puanlari(kume, _baglar(db, kume), puan)
    db.query(OgrenciDalUyumSkoru).filter(OgrenciDalUyumSkoru.ogrenci_id == ogrenci.id, OgrenciDalUyumSkoru.tur_id == tur.id,
                                        OgrenciDalUyumSkoru.dal_id == dal.id).delete()
    for b, v in k5.items():
        db.add(OgrenciDalUyumSkoru(ogrenci_id=ogrenci.id, tur_id=tur.id, dal_id=dal.id, bolum_id=b, dal_ici_uyum=v))

    oturum.durum = "tamamlandi"
    oturum.tamamlanma_zamani = datetime.now(timezone.utc)
    db.flush()
    return sonuc


def k5_sifirla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> None:
    """Bu turun K5'ini baştan alır: üretilmiş sorular (cevaplarıyla), K5 oturumu, iş türü puanları ve bölüm K5 puanları
    silinir. K1-K4'ten bir katman tekrar açıldığında çağrılır — K1-K4 sonucu değişince küme ve sorular da değişebilir;
    eski kümeye göre sorulmuş sorular yeni kümeyi puanlamamalı. Katman yeniden bitince k5_tetikle yeni oturum açar."""
    soru_idler = [i for (i,) in db.query(Soru.id).filter(Soru.ogrenci_id == ogrenci.id, Soru.tur_id == tur.id).all()]
    if soru_idler:
        db.query(OgrenciCevap).filter(OgrenciCevap.soru_id.in_(soru_idler)).delete(synchronize_session=False)
        db.query(Soru).filter(Soru.id.in_(soru_idler)).delete(synchronize_session=False)   # seçenekler CASCADE
    k5_degiskenler = [i for (i,) in db.query(Degisken.id).join(Katman, Katman.id == Degisken.katman_id)
                      .filter(Katman.kod == "K5").all()]
    if k5_degiskenler:
        db.query(OgrenciDegiskenSkoru).filter(OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id, OgrenciDegiskenSkoru.tur_id == tur.id,
                                              OgrenciDegiskenSkoru.degisken_id.in_(k5_degiskenler)).delete(synchronize_session=False)
    dal = k5_dali(db)
    if dal is not None:
        for model in (OgrenciDalUyumSkoru, OgrenciDalOturumu):
            db.query(model).filter(model.ogrenci_id == ogrenci.id, model.tur_id == tur.id,
                                   model.dal_id == dal.id).delete(synchronize_session=False)
    db.flush()


def bekleyen_dal_var_mi(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> bool:
    """K5 zorunlu kuralı: açılmış ama tamamlanmamış K5 oturumu varsa True (sonuç ekranı bu durumda gösterilmez).
    Eski alan oturumları (kaldırılan alan K5'i) öğrenciyi kilitlemez."""
    return (db.query(OgrenciDalOturumu.id).join(Dal, Dal.id == OgrenciDalOturumu.dal_id)
            .filter(OgrenciDalOturumu.ogrenci_id == ogrenci.id, OgrenciDalOturumu.tur_id == tur.id,
                    OgrenciDalOturumu.durum != "tamamlandi", Dal.kod == K5_DAL_KODU).first()) is not None
