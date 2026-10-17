"""
D4 — TOPLAM_UYUM skor hesaplama motoru.
Kaynak: sistem_genel_anlatim.md D4

[ÇIKARIM — belgede açıkça tanımlanmamış bir nokta]: D4, "öğrencinin 31
değişkenlik profili, her bölümün bolum_agirliklari profiliyle 10 farklı
yöntemle karşılaştırılır" diyor ama METOTLARIN karar matrisine hangi HAM
DEĞERİ koyacağını (öğrenci puanı mı, bölüm ağırlığı mı, ikisinin farkı mı)
belirtmiyor. Klasik ÇKKV yöntemleri "alternatifler × kriterler" matrisi
üzerinde çalışır — burada alternatifler 301 bölüm, kriterler 31 değişken.
Her (bölüm, değişken) hücresi için bir "uyum performans değeri" tanımlamak
gerekiyor. Burada seçilen tanım:

    performans_ij = 100 - |ogrenci_puani_i - bolum_agirligi_ij|

Yani bölümün bir değişkendeki beklentisi öğrencinin puanına ne kadar
yakınsa, o hücre o kadar yüksek (iyi) sayılır — 0-100 ölçekli, "benefit"
(yüksek=iyi) yönlü tek tip bir kriter seti. Bu, tüm 10 yöntemin ortak
girdisidir; yöntemler arası fark yalnızca bu ortak matrisi nasıl
ağırlıklandırıp birleştirdiklerinde ortaya çıkar (D4'ün kendi "sağlamlık
kontrolü" çerçevesiyle tutarlı — bkz. ana belge, "10 yöntemin metodolojik
rolü").

[DÜZELTME 2026-10-03 — katman içi göreli karşılaştırma]
Ham formül (100 - |öğrenci - bölüm|) öğrenci profilinin SEVİYESİNE bakıyordu:
bölüm ağırlıkları ~30-70 bandında, öğrenci puanları 0-100'e yayıldığı için
"genel seviyesi öğrenciye en yakın" bölüm kazanıyor, öğrencinin hangi alanda
öne çıktığı neredeyse hiç yansımıyordu (örn. A2 Sözel=95 olan öğrenciye
Veterinerlik/Uçak Bakım önerildi). Artık karşılaştırmadan önce hem öğrenci
hem her bölüm profili, HER KATMAN İÇİNDE kendi ortalama/std'sine göre
ölçekleniyor (50 + 15·z). Böylece "en güçlü yönün / bölümün en çok istediği
yön" karşılaştırılıyor — kutup sorularının göreli mantığıyla da tutarlı.
10 yöntem, ağırlıklar ve sonraki tüm adımlar değişmedi.

Kriter ağırlıkları: her değişkenin ağırlığı, bağlı olduğu katmanın
normalizasyon_agirligi'nin o katmandaki değişken sayısına eşit
bölünmesiyle bulunur [ÇIKARIM — belgede değişken-bazlı ağırlık
dağılımı tanımlanmamıştı, yalnızca katman-bazlı %20/15/25/40].
"""
from app.core.metin import turkce_kucult
import math
from dataclasses import dataclass

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Ogrenci, Bolum, Degisken, Katman, BolumAgirligi,
    OgrenciDegiskenSkoru, OgrenciDegerlendirmeTuru, OgrenciBolumUyumSkoru, Soru,
)

EPS = 1e-9
IPSATIF_OLCEK = 15.0  # katman içi z-skoru -> 50 ± 15 bandına


def _katman_ici_olcekle(matris: np.ndarray, katman_gruplari: list[list[int]]) -> np.ndarray:
    """matris: (..., m). Her katmanın sütunlarını satır bazında kendi ortalama/std'sine göre ölçekler."""
    sonuc = matris.astype(float).copy()
    for idx in katman_gruplari:
        if len(idx) < 3:
            continue  # 1-2 değişkenli katmanda göreli şekil anlamsız — ham değer kullanılır
        x = sonuc[..., idx]
        ort = x.mean(axis=-1, keepdims=True)
        std = x.std(axis=-1, keepdims=True)
        sonuc[..., idx] = 50.0 + IPSATIF_OLCEK * (x - ort) / (std + EPS)
    return sonuc


@dataclass
class HesaplamaGirdisi:
    bolum_idler: list[int]
    bolum_adlari: dict[int, str]
    degisken_idler: list[int]
    agirliklar: np.ndarray          # (m,) — kriter ağırlıkları, toplamı 1
    performans: np.ndarray          # (n_bolum, m) — 0-100 ölçekli "uyum performansı"
    agirlikli_varyans: dict[int, float]     # bolum_id -> A4'teki güvenilirlik göstergesi (tie-break için)
    etkin_meslek_sayisi: dict[int, int]     # bolum_id -> A4'teki güvenilirlik göstergesi (tie-break için)
    # [2026-10-09] "Neden bu bölüm?" açıklaması için
    degisken_kodlari: list | None = None
    ogrenci_olcekli: np.ndarray | None = None   # (m,) katman içi ölçekli öğrenci profili (50 ± 15)
    bolum_olcekli: np.ndarray | None = None     # (n, m) katman içi ölçekli bölüm profilleri
    bolum_matrisi: np.ndarray | None = None     # (n, m) ham bölüm ağırlıkları (bölümler arası yüzdelik için)


# [2026-10-11] Bölüm tarafı (değişkenler, katman ağırlıkları, 301 bölüm × ~130 değişken ağırlık matrisi) her öğrencide
# aynıdır; önceden her istekte (sıralama isteğinde iki kez) ~39 bin satır okunup yeniden kuruluyordu (uzak veritabanında
# saniyeler). Süreç içinde ONBELLEK_SN saniye saklanır; ağırlık / bölüm durumu değişince bolum_onbellegini_temizle() çağrılır.
import threading as _threading
import time as _time

ONBELLEK_SN = 600
_onbellek: dict = {"zaman": 0.0, "anahtar": None, "veri": None}
_onbellek_kilit = _threading.Lock()


def bolum_onbellegini_temizle() -> None:
    with _onbellek_kilit:
        _onbellek.update(zaman=0.0, anahtar=None, veri=None)


def _bolum_verisi(db: Session) -> dict | None:
    from app.core.katman_servisi import parametre_oku
    haric = frozenset(k.strip() for k in (parametre_oku(db, "eslesme_disi_degiskenler", "P4") or "").split(",") if k.strip())
    with _onbellek_kilit:
        if _onbellek["veri"] is not None and _onbellek["anahtar"] == haric and _time.time() - _onbellek["zaman"] < ONBELLEK_SN:
            return _onbellek["veri"]
    v = _bolum_verisi_hesapla(db, haric)
    with _onbellek_kilit:
        _onbellek.update(zaman=_time.time(), anahtar=haric, veri=v)
    return v


def _bolum_verisi_hesapla(db: Session, haric: frozenset) -> dict | None:
    ana_katmanlar = db.query(Katman).filter(Katman.kosullu_mu.is_(False)).all()
    ana_katman_idler = [k.id for k in ana_katmanlar]
    katman_agirlik = {k.id: float(k.normalizasyon_agirligi or 0) for k in ana_katmanlar}

    degiskenler = db.query(Degisken).filter(Degisken.katman_id.in_(ana_katman_idler)).order_by(Degisken.id).all()
    # [2026-10-07] Bölüm eşleşmesine girmeyen değişkenler (varsayılan P4 — kaygı/duygusal hassasiyet).
    # Doğrulama simülasyonu: yalnızca kaygı puanı değişince ilk 10'daki ~4 bölüm değişiyor, kaygılı
    # öğrenciler terapi/psikoloji bölümlerine itiliyordu. Kaygı bir mesleki ilgi değildir; öğrencinin
    # kişilik sonucunda ve koçlukta kullanılmaya devam eder. Parametre: eslesme_disi_degiskenler ("P4,X1").
    degiskenler = [(d.id, d.kod, d.katman_id) for d in degiskenler if d.kod not in haric]
    if not degiskenler:
        return None

    # kriter ağırlığı = katmanın % ağırlığı / o katmandaki değişken sayısı
    katman_basi_sayim: dict[int, int] = {}
    for _, _, kid in degiskenler:
        katman_basi_sayim[kid] = katman_basi_sayim.get(kid, 0) + 1

    degisken_idler = [d[0] for d in degiskenler]
    agirliklar = np.array([
        katman_agirlik.get(kid, 0) / max(katman_basi_sayim.get(kid, 1), 1)
        for _, _, kid in degiskenler
    ])
    if agirliklar.sum() <= 0:
        return None
    agirliklar = agirliklar / agirliklar.sum()  # toplamı 1'e normalize

    yayinda_bolumler = db.query(Bolum.id, Bolum.ad).filter(Bolum.durum == "yayinda").order_by(Bolum.ad).all()
    if not yayinda_bolumler:
        return None
    bolum_idler = [b.id for b in yayinda_bolumler]
    bolum_adlari = {b.id: b.ad for b in yayinda_bolumler}

    agirlik_satirlari = (
        db.query(BolumAgirligi.bolum_id, BolumAgirligi.degisken_id, BolumAgirligi.versiyon, BolumAgirligi.agirlik_degeri,
                 BolumAgirligi.agirlikli_varyans, BolumAgirligi.etkin_meslek_sayisi)
        .filter(BolumAgirligi.bolum_id.in_(bolum_idler), BolumAgirligi.degisken_id.in_(degisken_idler))
        .all()
    )
    # (bolum_id, degisken_id) -> agirlik_degeri ; en güncel versiyon kullanılır
    en_guncel: dict[tuple[int, int], object] = {}
    for satir in agirlik_satirlari:
        anahtar = (satir.bolum_id, satir.degisken_id)
        if anahtar not in en_guncel or satir.versiyon > en_guncel[anahtar].versiyon:
            en_guncel[anahtar] = satir

    n, m = len(bolum_idler), len(degisken_idler)
    bolum_matrisi = np.zeros((n, m))
    agirlikli_varyans: dict[int, float] = {}
    etkin_meslek_sayisi: dict[int, int] = {}

    for i, bolum_id in enumerate(bolum_idler):
        varyans_listesi = []
        for j, degisken_id in enumerate(degisken_idler):
            satir = en_guncel.get((bolum_id, degisken_id))
            bolum_matrisi[i, j] = float(satir.agirlik_degeri) if satir else 50.0  # veri yoksa nötr varsayım
            if satir and satir.agirlikli_varyans is not None:
                varyans_listesi.append(float(satir.agirlikli_varyans))
            if satir and satir.etkin_meslek_sayisi is not None:
                etkin_meslek_sayisi[bolum_id] = satir.etkin_meslek_sayisi
        agirlikli_varyans[bolum_id] = sum(varyans_listesi) / len(varyans_listesi) if varyans_listesi else 0.0
        etkin_meslek_sayisi.setdefault(bolum_id, 0)

    # [DÜZELTME 2026-10-03] Katman içi göreli karşılaştırma (bkz. modül docstring'i)
    katman_gruplari: dict[int, list[int]] = {}
    for j, (_, _, kid) in enumerate(degiskenler):
        katman_gruplari.setdefault(kid, []).append(j)
    gruplar = list(katman_gruplari.values())
    bolum_olcekli = _katman_ici_olcekle(bolum_matrisi, gruplar)
    return {"degisken_idler": degisken_idler, "degisken_kodlari": [d[1] for d in degiskenler], "agirliklar": agirliklar,
            "bolum_idler": bolum_idler, "bolum_adlari": bolum_adlari, "bolum_matrisi": bolum_matrisi,
            "agirlikli_varyans": agirlikli_varyans, "etkin_meslek_sayisi": etkin_meslek_sayisi,
            "gruplar": gruplar, "bolum_olcekli": bolum_olcekli}


def girdi_hazirla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> HesaplamaGirdisi | None:
    """Öğrenci profili + yayındaki tüm bölümlerin ağırlık matrisini toplar (bölüm tarafı önbellekten)."""
    v = _bolum_verisi(db)
    if v is None:
        return None
    degisken_idler = v["degisken_idler"]
    ogrenci_skorlari = {
        s.degisken_id: float(s.puan)
        for s in db.query(OgrenciDegiskenSkoru.degisken_id, OgrenciDegiskenSkoru.puan).filter(
            OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id,
            OgrenciDegiskenSkoru.tur_id == tur.id,
            OgrenciDegiskenSkoru.degisken_id.in_(degisken_idler),
        ).all()
    }
    if len(ogrenci_skorlari) < len(degisken_idler):
        return None  # profil eksik — TOPLAM_UYUM hesaplanamaz (D4 kuralı)

    ogrenci_vektor = np.array([ogrenci_skorlari[did] for did in degisken_idler])
    ogrenci_olcekli = _katman_ici_olcekle(ogrenci_vektor[None, :], v["gruplar"])[0]
    bolum_olcekli = v["bolum_olcekli"]
    performans = np.maximum(0.0, 100.0 - np.abs(ogrenci_olcekli[None, :] - bolum_olcekli))

    return HesaplamaGirdisi(
        bolum_idler=v["bolum_idler"], bolum_adlari=v["bolum_adlari"], degisken_idler=degisken_idler,
        agirliklar=v["agirliklar"], performans=performans,
        agirlikli_varyans=v["agirlikli_varyans"], etkin_meslek_sayisi=v["etkin_meslek_sayisi"],
        degisken_kodlari=v["degisken_kodlari"], ogrenci_olcekli=ogrenci_olcekli,
        bolum_olcekli=bolum_olcekli, bolum_matrisi=v["bolum_matrisi"],
    )


# ============================================================================
# 10 ÇKKV YÖNTEMİ — her biri (n_bolum,) uzunluğunda ham skor dizisi döner.
# Tüm kriterler "benefit" (yüksek=iyi) yönlüdür (bkz. modül docstring'i).
# ============================================================================

def _wsm(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    Xn = X / (X.max(axis=0, keepdims=True) + EPS)
    return Xn @ w


def _wpm(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    Xn = X / (X.max(axis=0, keepdims=True) + EPS)
    Xn = np.clip(Xn, EPS, None)  # log(0) önlemi
    return np.exp(np.log(Xn) @ w)


def _waspas(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    return 0.5 * _wsm(X, w) + 0.5 * _wpm(X, w)


def _topsis(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    r = X / (np.sqrt((X ** 2).sum(axis=0, keepdims=True)) + EPS)
    v = r * w
    ideal_best = v.max(axis=0)
    ideal_worst = v.min(axis=0)
    d_best = np.sqrt(((v - ideal_best) ** 2).sum(axis=1))
    d_worst = np.sqrt(((v - ideal_worst) ** 2).sum(axis=1))
    return d_worst / (d_best + d_worst + EPS)


def _vikor(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    f_star = X.max(axis=0)
    f_minus = X.min(axis=0)
    aralik = (f_star - f_minus) + EPS
    S = ((f_star - X) / aralik * w).sum(axis=1)
    R = ((f_star - X) / aralik * w).max(axis=1)
    S_star, S_minus = S.min(), S.max()
    R_star, R_minus = R.min(), R.max()
    v = 0.5
    Q = v * (S - S_star) / (S_minus - S_star + EPS) + (1 - v) * (R - R_star) / (R_minus - R_star + EPS)
    return 1.0 - Q  # düşük Q = iyi -> yüksek=iyi'ye çevrildi


def _gra(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    ideal = X.max(axis=0)
    delta = np.abs(ideal - X)
    delta_min, delta_max = delta.min(), delta.max()
    xi = 0.5
    gamma = (delta_min + xi * delta_max) / (delta + xi * delta_max + EPS)
    return gamma @ w


def _moora(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    r = X / (np.sqrt((X ** 2).sum(axis=0, keepdims=True)) + EPS)
    return r @ w


def _copras(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    r = X / (X.sum(axis=0, keepdims=True) + EPS)
    v = r * w
    return v.sum(axis=1)  # tüm kriterler benefit -> Q_j = S+_j


def _edas(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    AV = X.mean(axis=0)
    PDA = np.maximum(0, X - AV) / (AV + EPS)
    NDA = np.maximum(0, AV - X) / (AV + EPS)
    SP = (PDA * w).sum(axis=1)
    SN = (NDA * w).sum(axis=1)
    NSP = SP / (SP.max() + EPS)
    NSN = 1 - SN / (SN.max() + EPS)
    return 0.5 * (NSP + NSN)


def _mabac(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    r = (X - X.min(axis=0)) / (X.max(axis=0) - X.min(axis=0) + EPS)
    v = (r + 1) * w
    g = np.exp(np.log(np.clip(v, EPS, None)).mean(axis=0))  # geometrik ortalama (sınır yaklaşım alanı)
    Q = v - g
    return Q.sum(axis=1)


YONTEMLER = {
    "WSM": _wsm, "WPM": _wpm, "WASPAS": _waspas, "TOPSIS": _topsis,
    "VIKOR": _vikor, "GRA": _gra, "MOORA": _moora, "COPRAS": _copras,
    "EDAS": _edas, "MABAC": _mabac,
}


def _min_max_0_100(x: np.ndarray) -> np.ndarray:
    lo, hi = x.min(), x.max()
    if hi - lo < EPS:
        return np.full_like(x, 50.0)  # tüm bölümler eşit çıktıysa nötr orta değer
    return (x - lo) / (hi - lo) * 100


def _kendall_w(siralamalar: np.ndarray) -> float:
    """
    siralamalar: (n_yontem, n_bolum) — her satır bir yöntemin verdiği rank (1=en iyi).
    Kendall's W = 12*S / (m^2 * (n^3 - n)), S = sum((R_j - Rbar)^2)
    """
    m, n = siralamalar.shape
    R = siralamalar.sum(axis=0)  # her bölümün toplam rank'i
    R_bar = R.mean()
    S = ((R - R_bar) ** 2).sum()
    payda = m ** 2 * (n ** 3 - n)
    if payda == 0:
        return 1.0
    return float(12 * S / payda)


# [2026-10-17] Sıralamaya sonradan müdahale YOK. Uyum puanı = 10 ÇKKV yönteminin ortalaması (+ K5 dal katkısı);
# öneri sırası bu puana göredir. Kaldırılanlar: alan tutarlılığı cezası (puana yazılıp 0'a kırpıyordu: öğrenci başına
# ortalama 301 bölümün 200'ü 0 görünüyordu), alan komşuluğu gruplaması (ana alan + komşuları puana bakılmadan öne
# alınıyordu; ör. 54 puanlı bölüm 90 puanlının önüne geçiyordu). Konu olarak uzak görünen iki bölüm birlikte çıkıyorsa
# bu, öğrencinin ölçülen özelliklerinde gerçek bir ortaklıktır; ayrım ölçümün kendisinden (değişkenler, K5) gelmelidir.
UYUM_SKOR_SURUMU = "2026-10-17"   # bu sürümden eski kayıtlar açılışta bir kez yeniden hesaplanır


def toplam_uyum_hesapla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> int:
    """
    D4'ün tamamı — girdi hazırlar, 10 yöntemi çalıştırır, min-max normalize
    eder, ortalamasını alır, Kendall's W hesaplar, ogrenci_bolum_uyum_skorlari'na
    yazar. Dönen değer: kaç bölüm için skor üretildiği (0 ise hesaplanamadı).
    """
    girdi = girdi_hazirla(db, ogrenci, tur)
    if girdi is None:
        return 0

    X, w = girdi.performans, girdi.agirliklar
    n = X.shape[0]

    normalize_skorlar: dict[str, np.ndarray] = {}
    siralama_matrisi = []
    for ad, fonksiyon in YONTEMLER.items():
        ham = fonksiyon(X, w)
        normalize = _min_max_0_100(ham)
        normalize_skorlar[ad] = normalize
        # rank: 1 = en yüksek skor (en iyi)
        rank = (-normalize).argsort().argsort() + 1
        siralama_matrisi.append(rank)

    siralama_matrisi = np.array(siralama_matrisi)
    kendall_w = _kendall_w(siralama_matrisi)

    ortalama = np.mean([normalize_skorlar[a] for a in YONTEMLER], axis=0)

    # eski skorları temizle (bu tur için varsa) — tur bazlı, tekrar hesaplama idempotent olsun
    db.query(OgrenciBolumUyumSkoru).filter(
        OgrenciBolumUyumSkoru.ogrenci_id == ogrenci.id,
        OgrenciBolumUyumSkoru.tur_id == tur.id,
    ).delete()

    for i, bolum_id in enumerate(girdi.bolum_idler):
        yontem_skorlari = {ad: round(float(normalize_skorlar[ad][i]), 2) for ad in YONTEMLER}
        db.add(OgrenciBolumUyumSkoru(
            ogrenci_id=ogrenci.id, tur_id=tur.id, bolum_id=bolum_id,
            toplam_uyum=round(float(ortalama[i]), 2),
            yontem_skorlari=yontem_skorlari,   # admin-only alan (API şemasında hariç tutulur)
            kendall_w=round(kendall_w, 3),      # admin-only alan
        ))
    db.flush()
    return n


K5_SIRALAMA_ETKISI = 0.50  # dal_ici_uyum 50'den her 1 puan sapma → nihai skorda 0.50 puan (en fazla ±25)
# [2026-10-08] 0.30 → 0.50: iki aşamalı doğrulama simülasyonunda (K1-K4 + dal soruları) öğrenci tiplerinin
# ilk 3 doğruluğu %75,5 → %76,5, Finans tipi %34 → %42. 0.70'te en zayıf tip (Spor) bozulduğu için 0.50 seçildi.


@dataclass
class SiralamaSatiri:
    bolum_id: int
    toplam_uyum: float
    kendall_w: float | None = None        # admin/test amaçlı; öğrenci API şemasına girmez
    yontem_skorlari: dict | None = None   # admin/test amaçlı; öğrenci API şemasına girmez
    alan: str | None = None               # [2026-10-09] bölümün üst alanı


def nihai_uyum_haritasi(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict[int, float]:
    """
    [YENİ 2026-10-03] bolum_id -> öğrenciye GÖSTERİLEN nihai uyum. Sonuç listesi ve Keşfet
    aynı sayıyı göstersin diye tek yerde hesaplanır:
    nihai = TOPLAM_UYUM + 0.50 × (dal_ici_uyum − 50)  (yalnızca tamamlanan dalların bölümleri için)
    """
    from app.models import OgrenciDalUyumSkoru  # döngüsel import olmasın diye burada

    dal_ici: dict[int, float] = {}
    for d in db.query(OgrenciDalUyumSkoru).filter(
        OgrenciDalUyumSkoru.ogrenci_id == ogrenci.id, OgrenciDalUyumSkoru.tur_id == tur.id
    ).all():
        dal_ici[d.bolum_id] = float(d.dal_ici_uyum)

    harita: dict[int, float] = {}
    for s in db.query(OgrenciBolumUyumSkoru).filter(
        OgrenciBolumUyumSkoru.ogrenci_id == ogrenci.id, OgrenciBolumUyumSkoru.tur_id == tur.id
    ).all():
        harita[s.bolum_id] = _nihai(s.toplam_uyum, dal_ici.get(s.bolum_id))
    return harita


def siralama_getir(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru, ilk_n: int = 20) -> list[SiralamaSatiri]:
    """
    D5, Katman 1 — Öneri Listesi. Eşit skor durumunda D4'teki tie-break
    kuralı: agirlikli_varyans artan, etkin_meslek_sayisi azalan, ad alfabetik.

    [YENİ 2026-10-03] K5: öğrencinin tamamladığı dal(lar)ın bölümleri için
    nihai skor = TOPLAM_UYUM + 0.50 × (dal_ici_uyum − 50). 50 = nötr (K5 bilgi vermediyse
    sıralama değişmez); en fazla ±25 puan (K5_SIRALAMA_ETKISI × 50). Diğer bölümler değişmez.
    Veritabanındaki TOPLAM_UYUM kaydı değiştirilmez; birleştirme okunurken yapılır.
    """
    girdi = girdi_hazirla(db, ogrenci, tur)
    varyans = girdi.agirlikli_varyans if girdi else {}
    meslek_sayisi = girdi.etkin_meslek_sayisi if girdi else {}
    adlar = girdi.bolum_adlari if girdi else {}

    skorlar = (
        db.query(OgrenciBolumUyumSkoru)
        .filter(OgrenciBolumUyumSkoru.ogrenci_id == ogrenci.id, OgrenciBolumUyumSkoru.tur_id == tur.id)
        .all()
    )
    nihai_harita = nihai_uyum_haritasi(db, ogrenci, tur)
    satirlar = []
    for s in skorlar:
        satirlar.append(SiralamaSatiri(bolum_id=s.bolum_id, toplam_uyum=nihai_harita.get(s.bolum_id, float(s.toplam_uyum)),
                                      kendall_w=float(s.kendall_w) if s.kendall_w is not None else None,
                                      yontem_skorlari=s.yontem_skorlari))

    _satirlari_sirala(satirlar, bolum_alan_haritasi(db), varyans, meslek_sayisi, adlar)
    return satirlar[:ilk_n]


def _nihai(toplam_uyum: float, dal_ici_uyum: float | None) -> float:
    """Tek bölüm için nihai uyum (nihai_uyum_haritasi ile aynı formül ve yuvarlama)."""
    nihai = float(toplam_uyum)
    if dal_ici_uyum is not None:
        nihai = min(100.0, max(0.0, nihai + K5_SIRALAMA_ETKISI * (float(dal_ici_uyum) - 50.0)))
    return round(nihai, 2)


def _satirlari_sirala(satirlar: list[SiralamaSatiri], alan_of: dict[int, str], varyans: dict, meslek_sayisi: dict,
                      adlar: dict, ilk_n: int | None = None) -> list[SiralamaSatiri]:
    """Öğrencinin sonuç ekranındaki sıralama; siralama_getir ve toplu_siralama ortak kullanır.
    [2026-10-17] Yalnızca gösterilen uyum puanına göre (büyükten küçüğe). Eşitlikte D4 kuralı: ağırlıklı varyans
    artan, etkin meslek sayısı azalan, ad alfabetik. alan yalnızca bilgi olarak doldurulur, sırayı etkilemez.
    ilk_n yoksa liste yerinde sıralanır; varsa yalnızca ilk ilk_n satır döner."""
    for st in satirlar:
        st.alan = alan_of.get(st.bolum_id)

    def anahtar(s):
        return (-s.toplam_uyum, varyans.get(s.bolum_id, 0.0), -meslek_sayisi.get(s.bolum_id, 0), adlar.get(s.bolum_id, ""))
    if ilk_n is not None:
        import heapq
        return heapq.nsmallest(ilk_n, satirlar, key=anahtar)   # sort ile aynı (kararlı) sıra
    satirlar.sort(key=anahtar)
    return satirlar


def eski_uyum_skorlarini_guncelle(db: Session) -> int:
    """[2026-10-17] Alan cezasıyla 0'a kırpılmış eski TOPLAM_UYUM kayıtlarını bir kez yeniden hesaplar (açılışta).
    Öğrenci cevapları, K5 dalları ve dal içi uyum değişmez; yalnızca ogrenci_bolum_uyum_skorlari yeniden yazılır."""
    from sqlalchemy import text as _text

    from app.models import SistemParametresi
    db.execute(_text("SELECT pg_advisory_xact_lock(20261017)"))   # çok işçili sunucuda tek işçi çalışsın
    p = db.query(SistemParametresi).filter(SistemParametresi.anahtar == "uyum_skor_surumu").first()
    if p is not None and p.deger == UYUM_SKOR_SURUMU:
        db.rollback()
        return 0
    cift = db.query(OgrenciBolumUyumSkoru.ogrenci_id, OgrenciBolumUyumSkoru.tur_id).distinct().all()
    sayi = 0
    for ogrenci_id, tur_id in cift:
        o, t = db.get(Ogrenci, ogrenci_id), db.get(OgrenciDegerlendirmeTuru, tur_id)
        if o is not None and t is not None and toplam_uyum_hesapla(db, o, t):
            sayi += 1
    if p is None:
        db.add(SistemParametresi(anahtar="uyum_skor_surumu", deger=UYUM_SKOR_SURUMU,
                                 aciklama="Bölüm uyum puanı hesaplama sürümü (otomatik; elle değiştirmeyin)"))
    else:
        p.deger = UYUM_SKOR_SURUMU
    db.commit()
    return sayi


# [2026-10-14] Tek kaynak: okul/rehber ekranları, tercih ve toplu istatistikler öğrencinin gördüğü NİHAİ uyumu ve
# sıralamayı kullansın diye toplu (çok tur için tek seferde) sürümler. Ham toplam_uyum yalnızca admin/denetim içindir.
def toplu_nihai_uyum(db: Session, tur_idler, bolum_idler=None) -> dict[int, dict[int, float]]:
    """tur_id -> {bolum_id -> nihai uyum}; nihai_uyum_haritasi'nın çok turlu hâli (tek sorgu, tur sayısından bağımsız).
    bolum_idler verilirse yalnızca o bölümler okunur (ör. hedef bölüm uyumu)."""
    from sqlalchemy import Float, and_, cast, select

    from app.models import OgrenciDalUyumSkoru as D
    S = OgrenciBolumUyumSkoru
    tur_idler = sorted({int(t) for t in tur_idler if t is not None})
    if not tur_idler:
        return {}
    # numeric → float8 dönüşümü Python'daki float(Decimal) ile aynı değeri verir; Decimal nesnesi üretmemek ~3 kat hızlı.
    q = (select(S.tur_id, S.bolum_id, cast(S.toplam_uyum, Float), cast(D.dal_ici_uyum, Float))
         .outerjoin(D, and_(D.tur_id == S.tur_id, D.bolum_id == S.bolum_id))
         .where(S.tur_id.in_(tur_idler)))
    if bolum_idler is not None:
        q = q.where(S.bolum_id.in_(sorted({int(b) for b in bolum_idler})))
    sonuc: dict[int, dict[int, float]] = {}
    for t, b, u, d in db.execute(q).all():
        sonuc.setdefault(t, {})[b] = _nihai(u, d)
    return sonuc


def toplu_siralama(db: Session, tur_idler, ilk_n: int | None = None) -> dict[int, list[SiralamaSatiri]]:
    """tur_id -> öğrencinin sonuç ekranındaki sıralama (siralama_getir ile aynı skor ve sıra; kendall_w /
    yontem_skorlari doldurulmaz). Bölüm tarafı (alan haritası, tie-break verisi) bir kez okunur."""
    harita = toplu_nihai_uyum(db, tur_idler)
    if not harita:
        return {}
    v = _bolum_verisi(db) or {}
    varyans, meslek_sayisi, adlar = v.get("agirlikli_varyans", {}), v.get("etkin_meslek_sayisi", {}), v.get("bolum_adlari", {})
    alan_of = bolum_alan_haritasi(db)
    sonuc: dict[int, list[SiralamaSatiri]] = {}
    for t, skorlar in harita.items():
        satirlar = [SiralamaSatiri(bolum_id=b, toplam_uyum=u) for b, u in skorlar.items()]
        sonuc[t] = _satirlari_sirala(satirlar, alan_of, varyans, meslek_sayisi, adlar, ilk_n)
    return sonuc


# ============================================================================
# [2026-10-09] Alan haritası ve "Neden bu bölüm?" açıklamaları
# ============================================================================

def bolum_alan_haritasi(db: Session) -> dict[int, str]:
    """bolum_id -> üst alan adı (K5 'U' dalları)."""
    from app.models import BolumDalEslesme, Dal
    return {
        e.bolum_id: d.ad
        for e, d in db.query(BolumDalEslesme, Dal).join(Dal, Dal.id == BolumDalEslesme.dal_id)
        .filter(Dal.kod.like("U%")).all()
    }


# Öğrenciye gösterilen kısa adlar (cümle içinde okunacak biçimde)
KISA_AD = {
    "D1": "iş güvencesi", "D2": "yüksek gelir hedefi", "D3": "saygınlık", "D4": "anlamlı iş arayışı",
    "D5": "topluma katkı", "D6": "özerklik", "D7": "estetik ve yaratıcılık",
    "P1": "insanlarla iletişim", "P2": "iş birliği ve empati", "P3": "disiplin ve titizlik",
    "P5": "yeniliğe açıklık", "P6": "dinamik ortam tercihi", "P7": "risk alabilme", "P8": "liderlik",
    "I1": "zaman yönetimi", "I2": "anlaşmazlık çözme", "I3": "baskı altında karar verme", "I4": "etik duyarlılık",
    "I5": "inisiyatif alma", "I6": "öğrenmeye açıklık", "I7": "stratejik düşünme",
    "A1": "sayısal düşünme", "A2": "sözel ifade", "A3": "insanlarla çalışma", "A4": "tasarım ve görsel düşünme",
    "A5": "doğa ve bilim ilgisi", "A6": "fiziksel aktivite", "A7": "planlı ve sistematik çalışma",
    "A8": "büyük resmi görme", "A9": "girişimcilik ve ikna",
}
NEDEN_ORTUSEN_SAYI = 3
NEDEN_BOLUM_YUZDELIK = 60.0      # bölüm bu özellikte bölümlerin en az %40'ından yüksekse "bölümün aradığı" sayılır
NEDEN_OGRENCI_ESIK = 55.0        # öğrencinin kendi profilinde ortalamanın üstü (katman içi ölçek)
NEDEN_DIKKAT_BOLUM = 85.0       # bölüm bu özellikte bölümlerin en üst %15'inde
NEDEN_DIKKAT_OGRENCI = 40.0     # öğrencinin kendi profilinde belirgin şekilde geride
NEDEN_DIKKAT_TEKRAR = 3         # aynı dikkat notu bu kadar bölümde çıkıyorsa bölüme özgü değildir → gösterilmez


def _liste_metni(adlar: list[str]) -> str:
    return adlar[0] if len(adlar) == 1 else ", ".join(adlar[:-1]) + " ve " + adlar[-1]


def _kisalt(metin: str, n: int = 110) -> str:
    metin = " ".join((metin or "").split())
    if len(metin) <= n:
        return metin
    kes = metin[:n].rsplit(" ", 1)[0]
    return kes.rstrip(",;:.") + "…"


def _cevap_kanitlari(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict[int, list[str]]:
    """degisken_id -> öğrencinin o yönü öne çıkaran seçimleri (seçtiği şık metinleri).
    En çok / en az ve tek seçimli senaryolarda: en çok seçilen şık bu değişkene ≥0,5 ağırlıkla bağlıysa.
    Likert'te güçlü katılım (ters kodlamaya göre), kutup sorularında belirgin taraf."""
    from app.models import OgrenciCevap, SoruSecenegi, SjtSecenekDegiskenAgirlik
    cevaplar = db.query(OgrenciCevap).filter(OgrenciCevap.ogrenci_id == ogrenci.id, OgrenciCevap.tur_id == tur.id).all()
    if not cevaplar:
        return {}
    sorular = {s.id: s for s in db.query(Soru).filter(Soru.id.in_({c.soru_id for c in cevaplar})).all()}
    secenekler = {x.id: x for x in db.query(SoruSecenegi).filter(SoruSecenegi.id.in_({c.secenek_id for c in cevaplar})).all()}
    agirliklar: dict[int, list[tuple[int, float]]] = {}
    for a in db.query(SjtSecenekDegiskenAgirlik).filter(SjtSecenekDegiskenAgirlik.secenek_id.in_(list(secenekler))).all():
        agirliklar.setdefault(a.secenek_id, []).append((a.degisken_id, float(a.agirlik)))
    secenek_sayisi = dict(
        db.query(SoruSecenegi.soru_id, func.count(SoruSecenegi.id))
        .filter(SoruSecenegi.soru_id.in_(list(sorular))).group_by(SoruSecenegi.soru_id).all()
    )
    kanit: dict[int, list[str]] = {}

    def ekle(did, metin):
        if did is None or not metin:
            return
        liste = kanit.setdefault(did, [])
        if metin not in liste:
            liste.append(metin)

    for c in sorted(cevaplar, key=lambda x: x.id):
        soru, sec = sorular.get(c.soru_id), secenekler.get(c.secenek_id)
        if soru is None or sec is None:
            continue
        if soru.soru_tipi == "sjt":
            for did, w in agirliklar.get(sec.id, []):
                if w >= 0.5:
                    ekle(did, _kisalt(sec.secenek_metni))
        elif soru.soru_tipi == "likert" and soru.degisken_id:
            n = secenek_sayisi.get(soru.id, 5) or 5
            sira = sec.secenek_sirasi if not soru.ters_kodlanmis_mi else (n + 1 - sec.secenek_sirasi)
            if sira >= n - 0.5:   # en güçlü katılım
                ekle(soru.degisken_id, _kisalt(soru.soru_metni))
        elif soru.soru_tipi == "kutup":
            if sec.secenek_sirasi == 1:
                ekle(soru.degisken_id, _kisalt(sec.secenek_metni))
            elif sec.secenek_sirasi == 4:
                ekle(getattr(soru, "b_ucu_degisken_id", None), _kisalt(sec.secenek_metni))
    return kanit


def _buyuk_bas(metin: str) -> str:
    """Türkçe uyumlu ilk harf büyütme (i → İ)."""
    if not metin:
        return metin
    ilk = {"i": "İ", "ı": "I"}.get(metin[0], metin[0].upper())
    return ilk + metin[1:]


def _seviye_ogrenci(puan: float) -> str:
    from app.core.seviye import seviye_etiketi   # [2026-10-10] tek kaynak düzey bantları
    return seviye_etiketi(puan)


def _seviye_bolum(yuzde: float) -> str:
    return "Çok yüksek" if yuzde >= 85 else "Yüksek" if yuzde >= 70 else "Ortanın üstü"


def neden_aciklamalari(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru, bolum_idler: list[int]) -> dict[int, dict]:
    """[2026-10-09] Her bölüm için yapılandırılmış "Neden bu bölüm?" açıklaması:
    {"ortusen": [{"ozellik", "sen", "bolum", "kanitlar": [seçtiğin şıklar], "kanit_sayisi"}],
     "k5": {"is_turu", "durum": "uyumlu"|"az", "kanit"} | None,
     "dikkat": {"ozellik", "metin"} | None,
     "metinler": [düz cümleler — eski istemciler için]}"""
    from app.models import BolumK5Bag
    girdi = girdi_hazirla(db, ogrenci, tur)
    if girdi is None or girdi.bolum_olcekli is None:
        return {}
    satir_of = {b: i for i, b in enumerate(girdi.bolum_idler)}
    H = girdi.bolum_matrisi
    n = H.shape[0]
    yuzdelik = (np.argsort(np.argsort(H, axis=0), axis=0) + 0.5) / n * 100.0
    o = girdi.ogrenci_olcekli
    kodlar = girdi.degisken_kodlari
    ham_puan = {
        s.degisken_id: float(s.puan)
        for s in db.query(OgrenciDegiskenSkoru).filter(
            OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id, OgrenciDegiskenSkoru.tur_id == tur.id,
        ).all()
    }
    kanitlar = _cevap_kanitlari(db, ogrenci, tur)

    # K5: bölüm bağları + öğrencinin eksen puanları
    baglar: dict[int, list[tuple[int, float]]] = {}
    for b in db.query(BolumK5Bag).filter(BolumK5Bag.bolum_id.in_(bolum_idler)).all():
        baglar.setdefault(b.bolum_id, []).append((b.degisken_id, float(b.bag)))
    eksen_idler = {d for l in baglar.values() for d, _ in l}
    eksen_ad = {d.id: d.ad for d in db.query(Degisken).filter(Degisken.id.in_(eksen_idler or [-1])).all()}

    sonuc: dict[int, dict] = {}
    dikkat_of: dict[int, int] = {}
    for bid in bolum_idler:
        i = satir_of.get(bid)
        if i is None:
            continue
        b = girdi.bolum_olcekli[i]
        aday = [
            (float((o[j] - 50) + (b[j] - 50)), j) for j in range(len(kodlar))
            if kodlar[j] in KISA_AD and yuzdelik[i, j] >= NEDEN_BOLUM_YUZDELIK and o[j] >= NEDEN_OGRENCI_ESIK
        ]
        aday.sort(reverse=True)
        ortusen = []
        sira_no = bolum_idler.index(bid)
        for _, j in aday[:NEDEN_ORTUSEN_SAYI]:
            did = girdi.degisken_idler[j]
            k = kanitlar.get(did, [])
            if len(k) > 2:   # aynı yön birçok bölümde çıkınca her kartta farklı örnek seçimler gösterilir
                kay = (2 * sira_no) % len(k)
                k = k[kay:] + k[:kay]
            ortusen.append({
                "ozellik": _buyuk_bas(KISA_AD[kodlar[j]]),
                "sen": _seviye_ogrenci(ham_puan.get(did, 50.0)),
                "bolum": _seviye_bolum(float(yuzdelik[i, j])),
                "kanitlar": k[:2],
                "kanit_sayisi": len(k),
            })
        k5 = None
        bl = [(d, w) for d, w in baglar.get(bid, []) if d in ham_puan]
        if bl:
            d_ana = max(bl, key=lambda x: (x[1], ham_puan[x[0]]))[0]
            p = ham_puan[d_ana]
            from app.core.seviye import gelisime_acik_mi, guclu_mu   # [2026-10-10] ortak bantlar (62 / 40)
            if guclu_mu(p) or gelisime_acik_mi(p):
                k = kanitlar.get(d_ana, [])
                k5 = {"is_turu": eksen_ad.get(d_ana, ""), "durum": "uyumlu" if guclu_mu(p) else "az",
                      "kanit": k[0] if (k and guclu_mu(p)) else None}
        dikkat = [(float(o[j]), j) for j in range(len(kodlar))
                  if kodlar[j] in KISA_AD and yuzdelik[i, j] >= NEDEN_DIKKAT_BOLUM and o[j] <= NEDEN_DIKKAT_OGRENCI]
        if dikkat:
            dikkat_of[bid] = min(dikkat)[1]
        sonuc[bid] = {"ortusen": ortusen, "k5": k5, "dikkat": None}

    # dikkat notu: yalnızca bölüme özgüyse (listede az tekrar ediyorsa) eklenir
    from collections import Counter
    tekrar = Counter(dikkat_of.values())
    for bid, j in dikkat_of.items():
        if tekrar[j] < NEDEN_DIKKAT_TEKRAR:
            sonuc[bid]["dikkat"] = {"ozellik": KISA_AD[kodlar[j]],
                                    "metin": f"Bu bölüm yüksek düzeyde {KISA_AD[kodlar[j]]} bekliyor; senin cevaplarında bu yön daha geri planda."}

    # eski istemciler için düz cümleler
    for bid, d in sonuc.items():
        m = []
        if d["ortusen"]:
            m.append("Örtüşen güçlü yönlerin: " + ", ".join(turkce_kucult(x["ozellik"]) for x in d["ortusen"]) + ".")
        if d["k5"]:
            m.append(f"Alan sorularında «{d['k5']['is_turu']}» işlerini "
                     + ("öne çıkardın." if d["k5"]["durum"] == "uyumlu" else "daha az seçtin."))
        if d["dikkat"]:
            m.append("Dikkat: " + d["dikkat"]["metin"])
        d["metinler"] = m
    return sonuc
