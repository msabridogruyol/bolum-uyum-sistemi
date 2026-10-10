# -*- coding: utf-8 -*-
"""
[2026-10-10] Test hesapları — süper adminin deneme / tanıtım için açtığı öğrenci ve okul yetkilisi hesapları.

* 2 adımlı doğrulama istenmez; giriş bağlantısı (süreli, iptal edilebilir) ile tek tıkla açılır.
* Öğrenci ilerlemesi "senaryo" ile kurulur: sistem, öğrencinin yerine soruları GERÇEK akışla cevaplar
  (katman_oturumu_baslat → cevabi_kaydet → katmani_tamamla → toplam_uyum_hesapla → k5_tetikle → dallar).
  Böylece sonuçlar, koçluk planı, cevap analizi vb. gerçek hesaplamalarla oluşur; hiçbir skor elle yazılmaz.
* Cevaplar bir "eğilim" vektörüne göre seçilir: her şık, puanlama kuralıyla değerlendirilir ve hedef profile en
  yakın olan (biraz rastgelelikle) seçilir. "Bölüme göre" eğilimde hedef profil, o bölümün özellik beklentileridir.
"""
import hashlib
import random
import secrets
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.katman_servisi import (
    IsKuraliHatasi, aktif_veya_yeni_tur_getir, cevabi_kaydet, cevaplari_puanla, katman_oturumu_baslat,
    katmani_tamamla, parametre_oku, puanlama_onbellegi, tum_ana_katmanlar_tamamlandi_mi,
)
from app.models import (
    Dal, Degisken, Katman, Ogrenci, OgrenciCevap, OgrenciDalOturumu, OgrenciDegerlendirmeTuru,
    OgrenciFavoriBolum, OgrenciGelisimAdimDurumu, OgrenciKatmanOturumu, Soru,
)

ASAMALAR = {
    "baslamadi": 0, "k1": 1, "k2": 2, "k3": 3, "k5_bekliyor": 4, "tamamlandi": 4,
}
ASAMA_ADI = {
    "baslamadi": "Hiç başlamadı", "k1": "K1 bitti", "k2": "K1–K2 bitti", "k3": "K1–K3 bitti",
    "k5_bekliyor": "K1–K4 bitti, alan soruları (K5) bekliyor", "tamamlandi": "Değerlendirme tamamlandı",
}


def _simdi() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------------------- giriş bağlantısı
def anahtar_ozeti(anahtar: str) -> str:
    return hashlib.sha256(anahtar.encode()).hexdigest()


def giris_anahtari_uret(hesap, saat: int) -> str:
    """Yeni bağlantı anahtarı üretir (eskisi geçersiz olur). Veritabanında yalnızca özeti saklanır."""
    anahtar = secrets.token_urlsafe(24)
    hesap.test_giris_anahtari = anahtar_ozeti(anahtar)
    hesap.test_giris_bitis = _simdi() + timedelta(hours=max(1, min(saat, 24 * 30)))
    return anahtar


# ----------------------------------------------------------------------------- ilerlemeyi sıfırla
def _ogrenci_tablolari(db: Session) -> list[str]:
    satirlar = db.execute(text(
        "SELECT table_name FROM information_schema.columns "
        "WHERE column_name = 'ogrenci_id' AND table_schema = current_schema() AND table_name <> 'ogrenciler'"
    )).all()
    return [r[0] for r in satirlar]


def ilerlemeyi_sifirla(db: Session, o: Ogrenci) -> None:
    """Öğrenciye bağlı tüm değerlendirme / koçluk / görev kayıtlarını siler (hesap ve KVKK onayları kalır).
    Tablolar arası bağımlılık sırası bilinmediği için silinemeyenler bir sonraki turda yeniden denenir."""
    bekleyen = [t for t in _ogrenci_tablolari(db) if t != "ogrenci_hesap_olaylari"]
    for _ in range(6):
        kalan = []
        for t in bekleyen:
            try:
                with db.begin_nested():
                    db.execute(text(f'DELETE FROM "{t}" WHERE ogrenci_id = :id'), {"id": o.id})
            except Exception:
                kalan.append(t)
        if not kalan:
            break
        bekleyen = kalan
    o.hedef_degisim_sayisi = 0
    db.flush()


# ----------------------------------------------------------------------------- cevap seçimi
def hedef_profil(db: Session, egilim: str, bolum_id: int | None, rnd: random.Random) -> dict[int, float]:
    """degisken_id → öğrencinin bu özellikte "olmasını istediğimiz" puan (0-100)."""
    degiskenler = db.query(Degisken).all()
    yuzdelik: dict[str, float] = {}
    if egilim == "bolum" and bolum_id:
        from app.api.bolum_bilgi import _yetkinlik_tablosu
        for grup in _yetkinlik_tablosu(db)["tablo"].get(bolum_id, {}).values():
            for x in grup:
                yuzdelik[x["kod"]] = x["yuzdelik"]
    profil = {}
    for d in degiskenler:
        if d.dal_id is not None:                       # K5 alan soruları: açılan alana ilgili bir öğrenci
            profil[d.id] = rnd.uniform(50, 80)
        elif d.kod in yuzdelik:                        # bölüm beklentisine yakın ama birebir değil
            profil[d.id] = 15 + 0.7 * yuzdelik[d.kod] + rnd.gauss(0, 10)
        elif egilim == "dengeli":
            profil[d.id] = rnd.uniform(40, 62)
        else:
            profil[d.id] = rnd.uniform(15, 90)
    return {k: max(0.0, min(100.0, v)) for k, v in profil.items()}


def _sec(db: Session, soru: Soru, onb: dict, profil: dict, rnd: random.Random, gurultu: float):
    secenekler = sorted(onb["soru_secenekleri"].get(soru.id, []), key=lambda s: s.secenek_sirasi)
    if not secenekler:
        raise IsKuraliHatasi(f"Soru {soru.id} için şık yok.")
    if soru.soru_tipi == "kontrol":                     # dikkat sorusu: dikkatli öğrenci doğru şıkkı seçer
        dogru = next((s for s in secenekler if s.secenek_sirasi == soru.beklenen_secenek_sira), secenekler[0])
        return dogru.id, None
    encok = (soru.cevap_bicimi or "tek") == "encok_enaz"
    adaylar = [(a.id, b.id) for a in secenekler for b in secenekler if a.id != b.id] if encok \
        else [(s.id, None) for s in secenekler]

    def maliyet(aday):
        p = cevaplari_puanla(db, {soru.id: soru}, [SimpleNamespace(soru_id=soru.id, secenek_id=aday[0], en_az_secenek_id=aday[1])], onb)
        degerler = [(did, v) for did, liste in p.items() for v in liste]
        if not degerler:
            return rnd.random()
        return sum(abs(v - profil.get(did, 50.0)) for did, v in degerler) / len(degerler) + rnd.gauss(0, gurultu)

    return min(adaylar, key=maliyet)


def _sorulari_cevapla(db: Session, o: Ogrenci, tur, sorular: list[Soru], profil, rnd, gurultu, kac: int | None = None):
    onb = puanlama_onbellegi(db, [s.id for s in sorular])
    for s in sorular[: kac if kac is not None else len(sorular)]:
        secenek_id, en_az = _sec(db, s, onb, profil, rnd, gurultu)
        cevabi_kaydet(db, o, tur, s.id, secenek_id, en_az)


# ----------------------------------------------------------------------------- bir değerlendirme turu
def _tur_yap(db: Session, o: Ogrenci, asama: str, yarim: bool, profil: dict, rnd: random.Random, gurultu: float):
    from app.core.dal_servisi import dal_oturumu_baslat, dali_tamamla, k5_tetikle
    from app.core.skor_motoru import toplam_uyum_hesapla

    n = ASAMALAR[asama]
    katmanlar = db.query(Katman).filter(Katman.kosullu_mu.is_(False)).order_by(Katman.sira).all()
    if n == 0 and not yarim:
        return None
    tur = aktif_veya_yeni_tur_getir(db, o)
    for k in katmanlar[:n]:
        oturum, sorular = katman_oturumu_baslat(db, o, k, tur)
        _sorulari_cevapla(db, o, tur, sorular, profil, rnd, gurultu)
        katmani_tamamla(db, o, k, tur, oturum)
    if n < len(katmanlar) and yarim:                    # sıradaki katman yarıda bırakılmış
        k = katmanlar[n]
        _, sorular = katman_oturumu_baslat(db, o, k, tur)
        _sorulari_cevapla(db, o, tur, sorular, profil, rnd, gurultu, kac=max(1, len(sorular) // 2))
    if n == len(katmanlar) and tum_ana_katmanlar_tamamlandi_mi(db, o, tur):
        toplam_uyum_hesapla(db, o, tur)
        k5_tetikle(db, o, tur)
        if asama == "tamamlandi":
            for do in db.query(OgrenciDalOturumu).filter(OgrenciDalOturumu.ogrenci_id == o.id,
                                                         OgrenciDalOturumu.tur_id == tur.id).order_by(OgrenciDalOturumu.id).all():
                dal = db.get(Dal, do.dal_id)
                try:
                    oturum, sorular = dal_oturumu_baslat(db, o, dal, tur)
                except IsKuraliHatasi:
                    continue                             # sorusu olmayan alan öğrenciyi kilitlemez
                _sorulari_cevapla(db, o, tur, sorular, profil, rnd, gurultu)
                dali_tamamla(db, o, dal, tur, oturum)
    db.flush()
    return tur


def _zamanlari_kaydir(db: Session, o: Ogrenci, tur, bitis: datetime, rnd: random.Random) -> None:
    """Her şey "şimdi" olmuş görünmesin: katmanlar ardışık günlerde, her biri 5-12 dakikada çözülmüş gibi.
    Son katman `bitis` anında biter; K5 alanları aynı gün biraz sonra."""
    oturumlar = (db.query(OgrenciKatmanOturumu, Katman).join(Katman, Katman.id == OgrenciKatmanOturumu.katman_id)
                 .filter(OgrenciKatmanOturumu.ogrenci_id == o.id, OgrenciKatmanOturumu.tur_id == tur.id)
                 .order_by(Katman.sira).all())
    cevaplar = db.query(OgrenciCevap).filter(OgrenciCevap.ogrenci_id == o.id, OgrenciCevap.tur_id == tur.id).all()
    cevap_of = {c.soru_id: c for c in cevaplar}
    adet = len(oturumlar)
    ilk = None

    def yay(soru_idler, bas, son):
        idler = [i for i in (soru_idler or []) if i in cevap_of]
        for i, sid in enumerate(idler):
            cevap_of[sid].cevap_zamani = bas + (son - bas) * ((i + 1) / (len(idler) + 1))

    for i, (ot, _k) in enumerate(oturumlar):
        son = bitis - timedelta(days=(adet - 1 - i), minutes=rnd.randint(0, 90))
        bas = son - timedelta(minutes=rnd.randint(5, 12))
        ot.baslama_zamani = bas
        if ot.durum == "tamamlandi":
            ot.tamamlanma_zamani = son
        yay(ot.kilitlenen_soru_id_listesi, bas, son)
        ilk = ilk or bas
    for j, do in enumerate(db.query(OgrenciDalOturumu).filter(OgrenciDalOturumu.ogrenci_id == o.id,
                                                              OgrenciDalOturumu.tur_id == tur.id).order_by(OgrenciDalOturumu.id).all()):
        if do.durum == "baslamadi":
            continue
        bas = bitis + timedelta(minutes=15 + 12 * j)
        do.baslama_zamani = bas
        if do.durum == "tamamlandi":
            do.tamamlanma_zamani = bas + timedelta(minutes=rnd.randint(4, 9))
    tur.baslama_zamani = ilk or bitis
    if tur.durum == "tamamlandi":
        tur.tamamlanma_zamani = bitis
    db.flush()


# ----------------------------------------------------------------------------- senaryo
def senaryo_uygula(db: Session, o: Ogrenci, ayar: dict) -> dict:
    """
    ayar: asama, yarim, egilim ('rastgele' | 'dengeli' | 'bolum'), egilim_bolum_id, gun_once, yeni_tur_hazir,
          onceki_tur, hedef ('yok' | 'otomatik' | bolum_id), tamamlanan_adim, listem_otomatik, tohum
    """
    asama = ayar.get("asama", "tamamlandi")
    if asama not in ASAMALAR:
        raise IsKuraliHatasi("Geçersiz aşama.")
    tohum = ayar.get("tohum") or secrets.randbelow(10**6)
    rnd = random.Random(tohum)
    gurultu = 8.0
    min_gun = int(parametre_oku(db, "yeniden_degerlendirme_min_gun", "120"))
    gun_once = max(0, int(ayar.get("gun_once") or 0))
    if ayar.get("yeni_tur_hazir") and asama in ("tamamlandi", "k5_bekliyor"):
        gun_once = max(gun_once, min_gun + 1)

    ilerlemeyi_sifirla(db, o)
    profil = hedef_profil(db, ayar.get("egilim", "rastgele"), ayar.get("egilim_bolum_id"), rnd)

    # İsteğe bağlı önceki tur: aynı öğrencinin ~4-5 ay önceki, biraz farklı profili (gelişim karşılaştırması için)
    if ayar.get("onceki_tur") and asama in ("tamamlandi", "k5_bekliyor"):
        eski_profil = {k: max(0.0, min(100.0, v + rnd.gauss(0, 12))) for k, v in profil.items()}
        eski = _tur_yap(db, o, "tamamlandi", False, eski_profil, rnd, gurultu)
        if eski is not None:
            _zamanlari_kaydir(db, o, eski, _simdi() - timedelta(days=gun_once + min_gun + 20), rnd)

    tur = _tur_yap(db, o, asama, bool(ayar.get("yarim")), profil, rnd, gurultu)
    if tur is not None:
        _zamanlari_kaydir(db, o, tur, _simdi() - timedelta(days=gun_once, hours=rnd.randint(1, 5)), rnd)

    ozet = {"tohum": tohum, "asama": ASAMA_ADI[asama], "ilk_bolumler": [], "hedef": None, "tamamlanan_adim": 0}
    if asama != "tamamlandi" or tur is None:
        db.flush()
        return ozet

    from app.core.skor_motoru import siralama_getir
    from app.models import Bolum
    sira = siralama_getir(db, o, tur, ilk_n=10)
    adlar = {b.id: b.ad for b in db.query(Bolum).filter(Bolum.id.in_([s.bolum_id for s in sira] or [-1])).all()}
    ozet["ilk_bolumler"] = [{"bolum_id": s.bolum_id, "bolum_adi": adlar.get(s.bolum_id), "uyum": round(float(s.toplam_uyum), 1)}
                            for s in sira[:5]]

    # Hedef bölüm + koçluk ilerlemesi
    hedef = ayar.get("hedef") or "yok"
    hedef_id = None
    if hedef == "otomatik" and sira:
        hedef_id = sira[0].bolum_id
    elif str(hedef).isdigit():
        hedef_id = int(hedef)
    if hedef_id:
        from app.core.koclugu_servisi import adim_durumu_guncelle, gelisim_plani_olustur, hedef_sec
        hedef_sec(db, o, hedef_id, onay=True, yonetici=True)
        db.flush()
        ozet["hedef"] = db.get(Bolum, hedef_id).ad
        n = max(0, int(ayar.get("tamamlanan_adim") or 0))
        if n:
            from app.api.koclugu import _gap_satirlarini_hazirla
            plan = gelisim_plani_olustur(db, o, hedef_id, _gap_satirlarini_hazirla(db, o))
            adimlar = [x["kod"] for a in plan["asamalar"] for x in a["adimlar"]][:n]
            for i, kod in enumerate(adimlar):
                adim_durumu_guncelle(db, o, hedef_id, kod, "tamamlandi")
            db.flush()
            # adımlar son haftalara yayılır (Gelişimin grafiği boş görünmesin)
            kayitlar = (db.query(OgrenciGelisimAdimDurumu)
                        .filter(OgrenciGelisimAdimDurumu.ogrenci_id == o.id, OgrenciGelisimAdimDurumu.hedef_bolum_id == hedef_id,
                                OgrenciGelisimAdimDurumu.adim_kodu.in_(adimlar)).all())
            sira_of = {k: i for i, k in enumerate(adimlar)}
            gun = max(1, min(gun_once, 56)) if gun_once else 1
            for k in kayitlar:
                oran = (sira_of.get(k.adim_kodu, 0) + 1) / (len(adimlar) + 1)
                k.guncelleme_zamani = _simdi() - timedelta(days=gun * (1 - oran), hours=rnd.randint(1, 8))
            ozet["tamamlanan_adim"] = len(adimlar)

    if ayar.get("listem_otomatik"):
        idler = [s.bolum_id for s in sira[:3]]
        if hedef_id and hedef_id not in idler:
            idler.append(hedef_id)
        for bid in idler:
            db.add(OgrenciFavoriBolum(ogrenci_id=o.id, bolum_id=bid))
    db.flush()
    return ozet


def ilerleme_ozeti(db: Session, o: Ogrenci) -> str:
    tur = (db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id)
           .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).first())
    if tur is None:
        return "Başlamadı"
    biten = db.query(OgrenciKatmanOturumu).join(Katman, Katman.id == OgrenciKatmanOturumu.katman_id).filter(
        OgrenciKatmanOturumu.ogrenci_id == o.id, OgrenciKatmanOturumu.tur_id == tur.id,
        OgrenciKatmanOturumu.durum == "tamamlandi", Katman.kosullu_mu.is_(False)).count()
    if tur.durum != "tamamlandi":
        return f"{tur.tur_no}. tur · {biten}/4 katman"
    dallar = db.query(OgrenciDalOturumu).filter(OgrenciDalOturumu.ogrenci_id == o.id, OgrenciDalOturumu.tur_id == tur.id).all()
    if any(d.durum != "tamamlandi" for d in dallar):
        return f"{tur.tur_no}. tur · K5 bekliyor"
    return f"{tur.tur_no}. tur · tamamlandı"
