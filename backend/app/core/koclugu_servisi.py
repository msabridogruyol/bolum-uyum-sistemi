"""
Bölüm F — Hedef Bölüm Karşılaştırma ve Koçluk Modülü.
Kaynak: koclugu_karsilastirma_modulu.md F1-F5, F8

Bu modül D4'ün (skor_motoru.py) ürettiği bolum_agirliklari verisini okur,
öğrenci profiliyle karşılaştırıp gap/öncelik/yol haritası üretir.
"""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import (
    Ogrenci, Bolum, Degisken, BolumAgirligi,
    OgrenciDegiskenSkoru, OgrenciDegerlendirmeTuru,
    OgrenciHedefBolum, GelisimYorumHavuzu, GelisimKarsilastirmaYorumu,
    OgrenciGelisimAksiyonDurumu,
)
from app.core.katman_servisi import IsKuraliHatasi


# ============================= F1 — Hedef Seçme ============================= #

def aktif_hedef_getir(db: Session, ogrenci: Ogrenci) -> OgrenciHedefBolum | None:
    return (
        db.query(OgrenciHedefBolum)
        .filter(OgrenciHedefBolum.ogrenci_id == ogrenci.id, OgrenciHedefBolum.aktif_mi.is_(True))
        .first()
    )


def hedef_sec(db: Session, ogrenci: Ogrenci, bolum_id: int, onay: bool = False) -> OgrenciHedefBolum:
    """
    F8 — Aynı anda yalnızca 1 aktif hedef olabilir (odaklanma ilkesi).
    Zaten aktif bir hedef varsa ve `onay=True` verilmediyse IsKuraliHatasi
    fırlatılır — çağıran taraf (API) bunu "emin misin?" onayı istemek için
    kullanır. Aynı bölüm zaten aktifse hiçbir şey yapılmaz (no-op).
    """
    bolum = db.get(Bolum, bolum_id)
    if bolum is None or bolum.durum != "yayinda":
        raise IsKuraliHatasi("Bu bölüm hedef olarak seçilemez — yayında değil veya mevcut değil.")

    mevcut_aktif = aktif_hedef_getir(db, ogrenci)

    if mevcut_aktif is not None and mevcut_aktif.bolum_id == bolum_id:
        return mevcut_aktif  # zaten bu hedefteyiz, no-op

    if mevcut_aktif is not None and not onay:
        raise IsKuraliHatasi(
            f"Zaten aktif bir hedefin var (bolum_id={mevcut_aktif.bolum_id}). "
            f"Değiştirmek için onay=true göndermelisin."
        )

    if mevcut_aktif is not None:
        mevcut_aktif.aktif_mi = False
        mevcut_aktif.pasif_zamani = datetime.now(timezone.utc)

    # F8.2 — daha önce bu bölüm hedeflenmişse (pasif durumda) geri aktive et,
    # ilerleme geçmişi (ogrenci_gelisim_aksiyon_durumu) sıfırlanmaz
    eski_kayit = (
        db.query(OgrenciHedefBolum)
        .filter(OgrenciHedefBolum.ogrenci_id == ogrenci.id, OgrenciHedefBolum.bolum_id == bolum_id)
        .first()
    )
    if eski_kayit is not None:
        eski_kayit.aktif_mi = True
        eski_kayit.pasif_zamani = None
        yeni = eski_kayit
    else:
        yeni = OgrenciHedefBolum(ogrenci_id=ogrenci.id, bolum_id=bolum_id, aktif_mi=True)
        db.add(yeni)

    db.flush()
    return yeni


# ============================= F2 — Gap + Öncelik ============================= #

def gap_kategorisi(gap: float) -> str:
    if gap >= 15:
        return "belirgin_ustun"
    if gap >= 5:
        return "ustun"
    if gap > -5:
        return "beklenti"
    if gap > -15:
        return "altinda"
    return "belirgin_altinda"


class GapSatiri:
    def __init__(self, degisken: Degisken, ogrenci_puan: float, bolum_beklenen: float,
                 bolum_agirlik: float, gelisim_karti: GelisimYorumHavuzu | None):
        self.degisken = degisken
        self.ogrenci_puan = ogrenci_puan
        self.bolum_beklenen = bolum_beklenen
        self.gap = ogrenci_puan - bolum_beklenen  # HAM fark — her zaman "öğrenci - bölüm", şeffaflık için değişmez
        # [DÜZELTME] Bazı değişkenlerde (ters_yonlu=True) yüksek ham fark
        # aslında olumsuzdur (örn. P4 Nevrotiklik'te öğrencinin bölüm
        # beklentisinden DAHA hassas olması iyi değildir). Kategori ve
        # öncelik hesaplaması bu YÖN DÜZELTİLMİŞ farkı kullanır; ham `gap`
        # değeri yalnızca görüntüleme/şeffaflık için saklanır.
        degerlendirme_farki = -self.gap if degisken.ters_yonlu else self.gap
        self.kategori = gap_kategorisi(degerlendirme_farki)
        self.oncelik_skoru = abs(degerlendirme_farki) * (bolum_agirlik / 100.0)  # F2.2
        self.gelisim_karti = gelisim_karti


def gap_analizi_hesapla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru, hedef_bolum_id: int) -> list[GapSatiri]:
    ogrenci_skorlari = {
        s.degisken_id: float(s.puan)
        for s in db.query(OgrenciDegiskenSkoru).filter(
            OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id,
            OgrenciDegiskenSkoru.tur_id == tur.id,
        ).all()
    }
    bolum_agirliklari = (
        db.query(BolumAgirligi)
        .filter(BolumAgirligi.bolum_id == hedef_bolum_id, BolumAgirligi.degisken_id.in_(ogrenci_skorlari.keys()))
        .all()
    )
    # en güncel versiyon
    en_guncel: dict[int, BolumAgirligi] = {}
    for satir in bolum_agirliklari:
        if satir.degisken_id not in en_guncel or satir.versiyon > en_guncel[satir.degisken_id].versiyon:
            en_guncel[satir.degisken_id] = satir

    degiskenler = {d.id: d for d in db.query(Degisken).filter(Degisken.id.in_(en_guncel.keys())).all()}
    havuz = {
        (h.degisken_id, h.aralik): h
        for h in db.query(GelisimYorumHavuzu).filter(GelisimYorumHavuzu.degisken_id.in_(en_guncel.keys())).all()
    }

    satirlar: list[GapSatiri] = []
    for degisken_id, agirlik_satiri in en_guncel.items():
        degisken = degiskenler.get(degisken_id)
        if degisken is None:
            continue
        ogrenci_puan = ogrenci_skorlari[degisken_id]
        bolum_beklenen = float(agirlik_satiri.agirlik_degeri)
        satir = GapSatiri(degisken, ogrenci_puan, bolum_beklenen, bolum_beklenen, None)
        satir.gelisim_karti = havuz.get((degisken_id, satir.kategori))
        satirlar.append(satir)

    return sorted(satirlar, key=lambda s: s.oncelik_skoru, reverse=True)


# ============================= F4 — Gelişim Yol Haritası ============================= #

def yol_haritasi_olustur(gap_satirlari: list[GapSatiri]) -> dict[str, list[GapSatiri]]:
    """
    F4.1 — yalnızca gelişim gerektiren (altinda/belirgin_altinda) satırlar
    tahmini_efor'a göre 3 aşamaya dağıtılır. Gelişim kartı (havuzdan) henüz
    yoksa (içerik yazılmadıysa) o satır "efor bilgisi yok" grubuna düşer.
    """
    gelisim_gerektiren = [s for s in gap_satirlari if s.kategori in ("altinda", "belirgin_altinda")]
    haritasi: dict[str, list[GapSatiri]] = {"simdi": [], "bu_donem": [], "uzun_vadede": [], "efor_belirsiz": []}
    efor_map = {"kisa": "simdi", "orta": "bu_donem", "uzun": "uzun_vadede"}
    for satir in gelisim_gerektiren:
        efor = satir.gelisim_karti.tahmini_efor if satir.gelisim_karti else None
        haritasi[efor_map.get(efor, "efor_belirsiz")].append(satir)
    return haritasi


# ============================= F4.2 — Aksiyon Takibi ============================= #

def aksiyon_durumu_guncelle(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int, degisken_id: int, durum: str) -> OgrenciGelisimAksiyonDurumu:
    if durum not in ("planlandi", "devam_ediyor", "tamamlandi"):
        raise IsKuraliHatasi(f"Geçersiz durum: {durum}")

    kayit = (
        db.query(OgrenciGelisimAksiyonDurumu)
        .filter(
            OgrenciGelisimAksiyonDurumu.ogrenci_id == ogrenci.id,
            OgrenciGelisimAksiyonDurumu.hedef_bolum_id == hedef_bolum_id,
            OgrenciGelisimAksiyonDurumu.degisken_id == degisken_id,
        )
        .first()
    )
    if kayit is None:
        kayit = OgrenciGelisimAksiyonDurumu(
            ogrenci_id=ogrenci.id, hedef_bolum_id=hedef_bolum_id, degisken_id=degisken_id, durum=durum,
        )
        db.add(kayit)
    else:
        kayit.durum = durum
        kayit.guncelleme_zamani = datetime.now(timezone.utc)
    db.flush()
    return kayit


# ============================= F5 — Tur Karşılaştırması ============================= #

def trend_kategorisi(degisim: float) -> str:
    if degisim >= 15:
        return "belirgin_gelisim"
    if degisim >= 5:
        return "gelisim"
    if degisim > -5:
        return "durgun"
    if degisim > -15:
        return "gerileme"
    return "belirgin_gerileme"


class KarsilastirmaSatiri:
    def __init__(self, degisken: Degisken, eski_puan: float, yeni_puan: float, yorum: GelisimKarsilastirmaYorumu | None):
        self.degisken = degisken
        self.eski_puan = eski_puan
        self.yeni_puan = yeni_puan
        self.degisim = yeni_puan - eski_puan  # HAM değişim — şeffaflık için değişmez
        # [DÜZELTME] ters_yonlu değişkenlerde artış (örn. nevrotikliğin
        # yükselmesi) bir "gelişim" değil "gerileme" sayılmalı — F2'deki
        # aynı yön düzeltmesi burada da uygulanıyor.
        degerlendirme_degisimi = -self.degisim if degisken.ters_yonlu else self.degisim
        self.trend = trend_kategorisi(degerlendirme_degisimi)
        self.yorum = yorum


def tur_karsilastirmasi_hesapla(db: Session, ogrenci: Ogrenci) -> list[KarsilastirmaSatiri] | None:
    """F5.2 — en az 2 tamamlanmış tur yoksa None döner (F5.4 ilk-tur davranışı)."""
    turlar = (
        db.query(OgrenciDegerlendirmeTuru)
        .filter(OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id, OgrenciDegerlendirmeTuru.durum == "tamamlandi")
        .order_by(OgrenciDegerlendirmeTuru.tur_no.desc())
        .limit(2)
        .all()
    )
    if len(turlar) < 2:
        return None
    guncel_tur, onceki_tur = turlar[0], turlar[1]

    guncel_skorlar = {s.degisken_id: float(s.puan) for s in db.query(OgrenciDegiskenSkoru).filter(
        OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id, OgrenciDegiskenSkoru.tur_id == guncel_tur.id).all()}
    onceki_skorlar = {s.degisken_id: float(s.puan) for s in db.query(OgrenciDegiskenSkoru).filter(
        OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id, OgrenciDegiskenSkoru.tur_id == onceki_tur.id).all()}

    ortak_degisken_idler = set(guncel_skorlar.keys()) & set(onceki_skorlar.keys())
    degiskenler = {d.id: d for d in db.query(Degisken).filter(Degisken.id.in_(ortak_degisken_idler)).all()}
    yorum_havuzu = {
        (y.degisken_id, y.trend): y
        for y in db.query(GelisimKarsilastirmaYorumu).filter(GelisimKarsilastirmaYorumu.degisken_id.in_(ortak_degisken_idler)).all()
    }

    satirlar = []
    for degisken_id in ortak_degisken_idler:
        degisken = degiskenler.get(degisken_id)
        if degisken is None:
            continue
        satir = KarsilastirmaSatiri(degisken, onceki_skorlar[degisken_id], guncel_skorlar[degisken_id], None)
        satir.yorum = yorum_havuzu.get((degisken_id, satir.trend))
        satirlar.append(satir)

    return sorted(satirlar, key=lambda s: abs(s.degisim), reverse=True)
