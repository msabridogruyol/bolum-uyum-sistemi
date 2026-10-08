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
    OgrenciGelisimAksiyonDurumu, OgrenciGelisimAdimDurumu,
)
from app.core.katman_servisi import IsKuraliHatasi
from app.core.skor_motoru import _katman_ici_olcekle
from app.core.gelisim_icerigi import ICERIK, TUR_ETIKET, ASAMA_SIRASI, adim_kodu
import numpy as np


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
                 bolum_agirlik: float, gelisim_karti: GelisimYorumHavuzu | None,
                 goreli_fark: float | None = None):
        self.degisken = degisken
        self.ogrenci_puan = ogrenci_puan
        self.bolum_beklenen = bolum_beklenen
        # [DÜZELTME 2026-10-03] Fark artık skor motoruyla AYNI ölçekte (katman içi göreli,
        # 50±15) hesaplanır. Ham fark ölçek farkı yüzünden (bölüm ağırlıkları ~30-70,
        # öğrenci puanları 0-100) çoğu değişkeni yapay olarak "belirgin eksik" gösteriyordu.
        self.gap = goreli_fark if goreli_fark is not None else ogrenci_puan - bolum_beklenen
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

    # Göreli fark: her katman (K5'te her dal) içinde öğrenci ve bölüm profili ayrı ayrı ölçeklenir
    gruplar: dict[tuple, list[int]] = {}
    for degisken_id in en_guncel:
        d = degiskenler.get(degisken_id)
        if d is not None:
            gruplar.setdefault((d.katman_id, d.dal_id), []).append(degisken_id)
    goreli: dict[int, float] = {}
    goreli_deger: dict[int, tuple[float, float]] = {}   # [2026-10-03] ekranda gösterilecek (öğrenci, bölüm) göreli değerleri
    for idler in gruplar.values():
        ogr = np.array([[ogrenci_skorlari[i] for i in idler]])
        blm = np.array([[float(en_guncel[i].agirlik_degeri) for i in idler]])
        tum = [list(range(len(idler)))]
        ogr_o, blm_o = _katman_ici_olcekle(ogr, tum)[0], _katman_ici_olcekle(blm, tum)[0]
        for i, a, b in zip(idler, ogr_o, blm_o):
            goreli[i] = float(a - b)
            goreli_deger[i] = (float(np.clip(a, 0, 100)), float(np.clip(b, 0, 100)))

    satirlar: list[GapSatiri] = []
    for degisken_id, agirlik_satiri in en_guncel.items():
        degisken = degiskenler.get(degisken_id)
        if degisken is None:
            continue
        ogrenci_puan = ogrenci_skorlari[degisken_id]
        bolum_beklenen = float(agirlik_satiri.agirlik_degeri)
        satir = GapSatiri(degisken, ogrenci_puan, bolum_beklenen, bolum_beklenen, None,
                          goreli_fark=goreli.get(degisken_id))
        satir.gelisim_karti = havuz.get((degisken_id, satir.kategori))
        satir.ogrenci_goreli, satir.bolum_goreli = goreli_deger.get(degisken_id, (ogrenci_puan, bolum_beklenen))
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


# ============================= [2026-10-03] Detaylı Gelişim Planı ============================= #

ODAK_ALAN_SAYISI = 3       # yol haritası en öncelikli 3 gelişim alanına odaklanır (odak ilkesi)
GUCLU_YON_SAYISI = 2
ADIM_DURUMLARI = ("planlandi", "devam_ediyor", "tamamlandi")
ASAMA_BILGI = {
    "simdi": ("1. Aşama · Bu hafta başla", "Kısa, hemen yapılabilecek adımlar — 1-2 hafta"),
    "bu_donem": ("2. Aşama · Önümüzdeki 1-3 ay", "Düzenli pratik ve deneyimle becerini oturt"),
    "uzun_vadede": ("3. Aşama · 6-12 ay", "Kalıcı alışkanlık ve büyük adımlar"),
}
_KUCUK = {"ve", "ile", "veya"}


def turkce_baslik(metin: str) -> str:
    """'BİLGİSAYAR VE ÖĞRETİM TEKNOLOJİLERİ' -> 'Bilgisayar ve Öğretim Teknolojileri'"""
    def kucuk(k): return k.replace("İ", "i").replace("I", "ı").lower()
    def buyuk_ilk(k): return ({"i": "İ", "ı": "I"}.get(k[0]) or k[0].upper()) + k[1:] if k else k
    kelimeler = [kucuk(k) for k in str(metin).split()]
    return " ".join(k if (i > 0 and k in _KUCUK) else buyuk_ilk(k) for i, k in enumerate(kelimeler))


def _grup(kategori: str) -> str:
    return "gelisim" if kategori in ("altinda", "belirgin_altinda") else "guclu" if kategori in ("ustun", "belirgin_ustun") else "uyumlu"


def adim_durumlari_getir(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int) -> dict[str, str]:
    return {
        a.adim_kodu: a.durum
        for a in db.query(OgrenciGelisimAdimDurumu).filter(
            OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id,
            OgrenciGelisimAdimDurumu.hedef_bolum_id == hedef_bolum_id,
        ).all()
    }


def adim_durumu_guncelle(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int, kod: str, durum: str | None):
    """durum=None -> işaret kaldırılır (adım 'başlanmadı' durumuna döner)."""
    parcalar = kod.split("-")
    if len(parcalar) != 3 or parcalar[0] not in ICERIK or parcalar[1] not in ("G", "U"):
        raise IsKuraliHatasi(f"Geçersiz adım kodu: {kod}")
    if durum is not None and durum not in ADIM_DURUMLARI:
        raise IsKuraliHatasi(f"Geçersiz durum: {durum}")
    kayit = db.query(OgrenciGelisimAdimDurumu).filter(
        OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id,
        OgrenciGelisimAdimDurumu.hedef_bolum_id == hedef_bolum_id,
        OgrenciGelisimAdimDurumu.adim_kodu == kod,
    ).first()
    if durum is None:
        if kayit is not None:
            db.delete(kayit)
    elif kayit is None:
        db.add(OgrenciGelisimAdimDurumu(ogrenci_id=ogrenci.id, hedef_bolum_id=hedef_bolum_id, adim_kodu=kod, durum=durum))
    else:
        kayit.durum = durum
        kayit.guncelleme_zamani = datetime.now(timezone.utc)
    db.flush()


def _adim(kod_deg: str, ad: str, grup: str, sira: int, ham: tuple, bolum: str, durumlar: dict) -> dict:
    asama, baslik, aciklama, tur, sure, olcut = ham
    kod = adim_kodu(kod_deg, grup, sira)
    return {
        "kod": kod, "degisken_kod": kod_deg, "degisken_adi": ad, "asama": asama,
        "baslik": baslik, "aciklama": aciklama.replace("{bolum}", bolum),
        "tur": tur, "tur_etiket": TUR_ETIKET.get(tur, tur), "sure": sure,
        "olcut": olcut.replace("{bolum}", bolum), "durum": durumlar.get(kod),
    }


AYIRT_ESIGI = 40.0        # [2026-10-07] bölümün bu özellikte bölümler arası yüzdeliği bunun altındaysa odak alanı olmaz
AYIRT_GUCLU_ESIK = 75.0   # bunun üstündeyse "bölüm bu alanda talepkâr" cümlesi kullanılır
AYIRT_MIN_BOLUM = 20      # daha az yayındaki bölüm varsa (test/kurulum) ayırt edicilik hesaplanmaz


def bolum_ayirt_ediciligi(db: Session, hedef_bolum_id: int, degisken_idler: list[int]) -> dict[int, float] | None:
    """
    [2026-10-07] Hedef bölümün her özellikte, yayındaki tüm bölümler arasındaki yüzdeliği (0-100).
    Karşılaştırma katman içi ölçeklenmiş profillerle yapılır (skor motoruyla aynı ölçek).
    Örn. Felsefe'de "sayısal eğilim" yüzdeliği düşükse, öğrencinin sayısal puanı ne kadar düşük
    olursa olsun bu alan Felsefe için odak alanı yapılmaz.
    """
    satirlar = (db.query(BolumAgirligi)
                .join(Bolum, Bolum.id == BolumAgirligi.bolum_id)
                .filter(Bolum.durum == "yayinda", BolumAgirligi.degisken_id.in_(degisken_idler)).all())
    en_guncel: dict[tuple[int, int], BolumAgirligi] = {}
    for r in satirlar:
        k = (r.bolum_id, r.degisken_id)
        if k not in en_guncel or r.versiyon > en_guncel[k].versiyon:
            en_guncel[k] = r
    bolum_idler = sorted({b for b, _ in en_guncel})
    if len(bolum_idler) < AYIRT_MIN_BOLUM or hedef_bolum_id not in bolum_idler:
        return None
    degiskenler = {d.id: d for d in db.query(Degisken).filter(Degisken.id.in_(degisken_idler)).all()}
    idler = [d for d in degisken_idler if d in degiskenler]
    M = np.array([[float(en_guncel[(b, d)].agirlik_degeri) if (b, d) in en_guncel else 50.0 for d in idler] for b in bolum_idler])
    gruplar: dict[tuple, list[int]] = {}
    for j, d in enumerate(idler):
        gruplar.setdefault((degiskenler[d].katman_id, degiskenler[d].dal_id), []).append(j)
    M = _katman_ici_olcekle(M, list(gruplar.values()))
    h = bolum_idler.index(hedef_bolum_id)
    n = len(bolum_idler)
    return {d: float((M[:, j] < M[h, j]).sum() / (n - 1) * 100) for j, d in enumerate(idler)}


def gelisim_plani_olustur(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int, gap_satirlari: list[GapSatiri]) -> dict:
    """
    Yol haritası mantığı:
      1. Gelişime açık (altinda / belirgin_altinda) özellikler öncelik skoruna göre sıralanır
         (öncelik = fark büyüklüğü × bölümün o özelliğe verdiği ağırlık).
      2. İçeriği olan ilk 3 özellik "odak alanı" olur; diğerleri "sonra odaklanılacak" listesine girer.
         Böylece öğrenci 31 şeyle değil, en çok fark yaratacak 3 alanla uğraşır.
      3. Her odak alanın adımları 3 aşamaya dağıtılır: Bu hafta → 1-3 ay → 6-12 ay.
         Bir aşamada odak sırasına göre (en öncelikli alan önce) dizilir.
      4. Güçlü yönlerden en belirgin 2'si için "bu gücü kullan" adımları eklenir.
      5. Sıradaki adım = en erken aşamadaki, en öncelikli alanın tamamlanmamış ilk adımı.
         Bir önceki aşamanın yarısı bitmeden sonraki aşama "önce öncekine odaklan" uyarısı taşır (kilit değil).
    """
    bolum = db.get(Bolum, hedef_bolum_id)
    bolum_adi = turkce_baslik(bolum.ad) if bolum else "Hedef bölüm"
    durumlar = adim_durumlari_getir(db, ogrenci, hedef_bolum_id)

    # Öncelik = fark × bölümün o özelliğe ağırlığı × katman ağırlığı (K4 = 40, diğerleri 20):
    # uyumu en çok etkileyecek açık en başa gelir.
    from app.models import Katman
    katman_w = {k.id: float(k.normalizasyon_agirligi or 20) for k in db.query(Katman).all()}
    # [2026-10-07] Öncelik ayrıca bölümün o özellikteki ayırt ediciliğiyle çarpılır; bölüm için belirgin
    # olmayan özellik (yüzdelik < AYIRT_ESIGI) odak alanı yapılmaz, "sonra odaklanılacak" listesine düşer.
    ayirt = bolum_ayirt_ediciligi(db, hedef_bolum_id, [s.degisken.id for s in gap_satirlari])
    def _ayirt(s):
        return 100.0 if ayirt is None else ayirt.get(s.degisken.id, 50.0)
    gelisim = sorted([s for s in gap_satirlari if _grup(s.kategori) == "gelisim"],
                     key=lambda s: s.oncelik_skoru * katman_w.get(s.degisken.katman_id, 20.0) * (_ayirt(s) / 100.0), reverse=True)
    icerikli = [s for s in gelisim if s.degisken.kod in ICERIK and _ayirt(s) >= AYIRT_ESIGI]
    odak = icerikli[:ODAK_ALAN_SAYISI]
    odak_kodlar = {s.degisken.kod for s in odak}
    sonraki = [s for s in gelisim if s.degisken.kod not in odak_kodlar]

    def duzeltilmis(s):
        return -s.gap if s.degisken.ters_yonlu else s.gap
    guclu = sorted([s for s in gap_satirlari if _grup(s.kategori) == "guclu" and s.degisken.kod in ICERIK],
                   key=duzeltilmis, reverse=True)[:GUCLU_YON_SAYISI]

    odak_alanlari = []
    asama_adimlari = {a: [] for a in ASAMA_SIRASI}
    for oncelik_sirasi, s in enumerate(odak, 1):
        ic = ICERIK[s.degisken.kod]
        odak_alanlari.append({
            "degisken_id": s.degisken.id, "degisken_kod": s.degisken.kod, "degisken_adi": s.degisken.ad,
            "kategori": s.kategori, "oncelik_sirasi": oncelik_sirasi,
            "nedir": ic["nedir"],
            "neden_onemli": (ic["gelisim_neden"].replace("{bolum}", bolum_adi) if _ayirt(s) >= AYIRT_GUCLU_ESIK else
                             f"{bolum_adi} için bu alan orta düzeyde önemli. Senin bu alandaki eğilimin bölümün beklentisinin "
                             f"altında; küçük ve düzenli adımlarla güçlendirmek bölümde işini kolaylaştırır."),
            "durum_tespiti": s.gelisim_karti.durum_tespiti if s.gelisim_karti else None,
        })
        for sira, ham in enumerate(ic["gelisim"], 1):
            adim = _adim(s.degisken.kod, s.degisken.ad, "G", sira, ham, bolum_adi, durumlar)
            adim["oncelik_sirasi"] = oncelik_sirasi
            asama_adimlari[adim["asama"]].append(adim)

    asamalar, onceki_oran = [], 1.0
    for a in ASAMA_SIRASI:
        adimlar = sorted(asama_adimlari[a], key=lambda x: x["oncelik_sirasi"])
        biten = sum(1 for x in adimlar if x["durum"] == "tamamlandi")
        baslik, alt = ASAMA_BILGI[a]
        asamalar.append({
            "kod": a, "baslik": baslik, "alt": alt, "adimlar": adimlar,
            "tamamlanan": biten, "toplam": len(adimlar),
            "once_oncekine_odaklan": onceki_oran < 0.5 and biten == 0,
        })
        onceki_oran = (biten / len(adimlar)) if adimlar else 1.0

    guclu_yonler = []
    for s in guclu:
        ic = ICERIK[s.degisken.kod]
        guclu_yonler.append({
            "degisken_id": s.degisken.id, "degisken_kod": s.degisken.kod, "degisken_adi": s.degisken.ad,
            "kategori": s.kategori, "nedir": ic["nedir"],
            "neden_onemli": ic["guclu_neden"].replace("{bolum}", bolum_adi),
            "adimlar": [_adim(s.degisken.kod, s.degisken.ad, "U", i, ham, bolum_adi, durumlar) for i, ham in enumerate(ic["guclu"], 1)],
        })

    tum = [x for a in asamalar for x in a["adimlar"]]
    siradaki = next((x for x in tum if x["durum"] != "tamamlandi"), None)
    return {
        "hedef_bolum_adi": bolum_adi,
        "odak_alanlari": odak_alanlari,
        "sonraki_alanlar": [{"degisken_id": s.degisken.id, "degisken_adi": s.degisken.ad, "kategori": s.kategori} for s in sonraki],
        "asamalar": asamalar,
        "guclu_yonler": guclu_yonler,
        "siradaki_adim": siradaki,
        "ilerleme": {
            "toplam": len(tum),
            "tamamlanan": sum(1 for x in tum if x["durum"] == "tamamlandi"),
            "devam_eden": sum(1 for x in tum if x["durum"] == "devam_ediyor"),
        },
    }
