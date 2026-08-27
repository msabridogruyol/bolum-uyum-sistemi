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

Kriter ağırlıkları: her değişkenin ağırlığı, bağlı olduğu katmanın
normalizasyon_agirligi'nin o katmandaki değişken sayısına eşit
bölünmesiyle bulunur [ÇIKARIM — belgede değişken-bazlı ağırlık
dağılımı tanımlanmamıştı, yalnızca katman-bazlı %20/15/25/40].
"""
import math
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session

from app.models import (
    Ogrenci, Bolum, Degisken, Katman, BolumAgirligi,
    OgrenciDegiskenSkoru, OgrenciDegerlendirmeTuru, OgrenciBolumUyumSkoru,
)

EPS = 1e-9


@dataclass
class HesaplamaGirdisi:
    bolum_idler: list[int]
    bolum_adlari: dict[int, str]
    degisken_idler: list[int]
    agirliklar: np.ndarray          # (m,) — kriter ağırlıkları, toplamı 1
    performans: np.ndarray          # (n_bolum, m) — 0-100 ölçekli "uyum performansı"
    agirlikli_varyans: dict[int, float]     # bolum_id -> A4'teki güvenilirlik göstergesi (tie-break için)
    etkin_meslek_sayisi: dict[int, int]     # bolum_id -> A4'teki güvenilirlik göstergesi (tie-break için)


def girdi_hazirla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> HesaplamaGirdisi | None:
    """Öğrenci profili + yayındaki tüm bölümlerin ağırlık matrisini toplar."""
    ana_katmanlar = db.query(Katman).filter(Katman.kosullu_mu.is_(False)).all()
    ana_katman_idler = [k.id for k in ana_katmanlar]
    katman_agirlik = {k.id: float(k.normalizasyon_agirligi or 0) for k in ana_katmanlar}

    degiskenler = db.query(Degisken).filter(Degisken.katman_id.in_(ana_katman_idler)).all()
    if not degiskenler:
        return None

    # kriter ağırlığı = katmanın % ağırlığı / o katmandaki değişken sayısı
    katman_basi_sayim: dict[int, int] = {}
    for d in degiskenler:
        katman_basi_sayim[d.katman_id] = katman_basi_sayim.get(d.katman_id, 0) + 1

    degisken_idler = [d.id for d in degiskenler]
    agirliklar = np.array([
        katman_agirlik.get(d.katman_id, 0) / max(katman_basi_sayim.get(d.katman_id, 1), 1)
        for d in degiskenler
    ])
    if agirliklar.sum() <= 0:
        return None
    agirliklar = agirliklar / agirliklar.sum()  # toplamı 1'e normalize

    ogrenci_skorlari = {
        s.degisken_id: float(s.puan)
        for s in db.query(OgrenciDegiskenSkoru).filter(
            OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id,
            OgrenciDegiskenSkoru.tur_id == tur.id,
            OgrenciDegiskenSkoru.degisken_id.in_(degisken_idler),
        ).all()
    }
    if len(ogrenci_skorlari) < len(degisken_idler):
        return None  # profil eksik — TOPLAM_UYUM hesaplanamaz (D4 kuralı)

    ogrenci_vektor = np.array([ogrenci_skorlari[did] for did in degisken_idler])

    yayinda_bolumler = db.query(Bolum).filter(Bolum.durum == "yayinda").order_by(Bolum.ad).all()
    if not yayinda_bolumler:
        return None
    bolum_idler = [b.id for b in yayinda_bolumler]
    bolum_adlari = {b.id: b.ad for b in yayinda_bolumler}

    agirlik_satirlari = (
        db.query(BolumAgirligi)
        .filter(BolumAgirligi.bolum_id.in_(bolum_idler), BolumAgirligi.degisken_id.in_(degisken_idler))
        .all()
    )
    # (bolum_id, degisken_id) -> agirlik_degeri ; en güncel versiyon kullanılır
    en_guncel: dict[tuple[int, int], BolumAgirligi] = {}
    for satir in agirlik_satirlari:
        anahtar = (satir.bolum_id, satir.degisken_id)
        if anahtar not in en_guncel or satir.versiyon > en_guncel[anahtar].versiyon:
            en_guncel[anahtar] = satir

    n, m = len(bolum_idler), len(degisken_idler)
    performans = np.zeros((n, m))
    agirlikli_varyans: dict[int, float] = {}
    etkin_meslek_sayisi: dict[int, int] = {}

    for i, bolum_id in enumerate(bolum_idler):
        varyans_listesi = []
        for j, degisken_id in enumerate(degisken_idler):
            satir = en_guncel.get((bolum_id, degisken_id))
            bolum_agirlik = float(satir.agirlik_degeri) if satir else 50.0  # veri yoksa nötr varsayım
            performans[i, j] = max(0.0, 100.0 - abs(ogrenci_vektor[j] - bolum_agirlik))
            if satir and satir.agirlikli_varyans is not None:
                varyans_listesi.append(float(satir.agirlikli_varyans))
            if satir and satir.etkin_meslek_sayisi is not None:
                etkin_meslek_sayisi[bolum_id] = satir.etkin_meslek_sayisi
        agirlikli_varyans[bolum_id] = sum(varyans_listesi) / len(varyans_listesi) if varyans_listesi else 0.0
        etkin_meslek_sayisi.setdefault(bolum_id, 0)

    return HesaplamaGirdisi(
        bolum_idler=bolum_idler, bolum_adlari=bolum_adlari, degisken_idler=degisken_idler,
        agirliklar=agirliklar, performans=performans,
        agirlikli_varyans=agirlikli_varyans, etkin_meslek_sayisi=etkin_meslek_sayisi,
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


def siralama_getir(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru, ilk_n: int = 20) -> list[OgrenciBolumUyumSkoru]:
    """
    D5, Katman 1 — Öneri Listesi. Eşit skor durumunda D4'teki tie-break
    kuralı: agirlikli_varyans artan, etkin_meslek_sayisi azalan, ad alfabetik.
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
    skorlar.sort(key=lambda s: (
        -s.toplam_uyum,
        varyans.get(s.bolum_id, 0.0),
        -meslek_sayisi.get(s.bolum_id, 0),
        adlar.get(s.bolum_id, ""),
    ))
    return skorlar[:ilk_n]
