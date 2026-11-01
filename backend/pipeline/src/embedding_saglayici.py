# -*- coding: utf-8 -*-
"""
Embedding Sağlayıcı — 3 bağımsız model (Model A, B, C)

sistem_genel_anlatim.md A8'de tanımlanan 3 model:
  Model A: turkish-e5-large
  Model B: emrecan/bert-base-turkish-cased-mean-nli-stsb-tr
  Model C: multilingual-e5-large

Bu dosya sentence-transformers üzerinden HuggingFace'den bu modelleri
indirir. İLK ÇALIŞTIRMADA İNTERNET GEREKİR (model ağırlıkları indirilir,
toplam ~3-4 GB). Sonraki çalıştırmalarda yerel önbellekten okunur, internet
gerekmez.

Bu dosya önceki bir denemede (sandbox ortamında HuggingFace erişimi
olmadığı için) TF-IDF ile simüle edilmişti — BU SÜRÜM O SIMÜLASYONU
İÇERMİYOR, gerçek modelleri kullanıyor. Sizin bilgisayarınızda gerçek
internet erişimi olduğu için buna gerek yok.
"""

import hashlib
import os
from pathlib import Path

import numpy as np

# [2026-10-04 HIZLANDIRMA] Metin önbelleği: her metnin vektörü bir kez hesaplanıp
# onbellek/metin_onbellek/<model>.npz dosyasında saklanır. Sonraki çalıştırmalarda
# yalnızca YENİ ya da DEĞİŞMİŞ metinler modele gönderilir. Sonuçlar aynıdır;
# sadece aynı hesap tekrar yapılmaz.
#  - Klasör onbellek/ altında AYRI bir alt klasörde durur; Pipeline Yönetici'nin
#    "onbellek/*.npy" yedekleme/temizleme adımı buna dokunmaz.
#  - Tamamen sıfırdan hesaplatmak için: Pipeline Yönetici → "Hesap Önbelleğini Sıfırla"
#    ya da onbellek/metin_onbellek klasörünü silin.
#  - Kapatmak için ortam değişkeni: BUS_ONBELLEK_KAPALI=1
METIN_ONBELLEK_DIZINI = Path(__file__).parent.parent / "onbellek" / "metin_onbellek"

MODEL_TANIMLARI = {
    "model_a": "nezahatkorkmaz/turkce-embedding-bge-m3",      # BGE-M3 tabanlı, Türkçe
    "model_b": "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr",  # düz BERT, Türkçe
    "model_c": "BAAI/bge-large-en-v1.5",  # Uluslararası, İngilizce — metinler önce
                                            # ceviri.py ile İngilizceye çevrilir (bkz. m4_meslek_embedding.py)
}

_yuklu_modeller = {}


def model_yukle(model_adi: str):
    """Modeli belleğe yükler (önbellekli — aynı model tekrar tekrar yüklenmez)."""
    from sentence_transformers import SentenceTransformer  # yalnızca gerçekten gerekince yüklenir (yavaş import)
    if model_adi not in _yuklu_modeller:
        hf_adi = MODEL_TANIMLARI[model_adi]
        print(f"[{model_adi}] Yükleniyor: {hf_adi} (ilk seferde internetten iner, birkaç dakika sürebilir)")
        _yuklu_modeller[model_adi] = SentenceTransformer(hf_adi)
    return _yuklu_modeller[model_adi]


def embed_et(metinler: list[str], model_adi: str, batch_size: int = 64,
             onek: str = "query") -> np.ndarray:
    """
    Bir metin listesini embedding matrisine çevirir.
    Dönüş: (len(metinler), embedding_boyutu) şeklinde numpy array, L2-normalize edilmiş
    (normalize edilmiş vektörlerin nokta çarpımı = kosinüs benzerliği).

    `onek` parametresi "query" veya "passage" olabilir — görevimiz meslek
    (query) ↔ bölüm/değişken (passage) eşleştirmesi olduğu için ASİMETRİK,
    çağıran kod meslekler için "query", bölüm/değişken için "passage" geçmeli.

    Model ailesine göre farklı önek kuralları uygulanır:
    - E5 ailesi (intfloat/...-e5-...): "query: "/"passage: " öneki zorunlu.
    - BGE İngilizce ailesi (BAAI/bge-...-en-...): yalnızca query tarafına
      özel bir arama talimatı eklenir, passage tarafına önek eklenmez
      (model kartındaki resmi kullanım kuralı).
    - Diğer modeller (düz BERT tabanlı Model B, BGE-M3 tabanlı Model A):
      önek gerektirmiyor, metin olduğu gibi kullanılır.
    """
    hf_adi = MODEL_TANIMLARI[model_adi]
    hf_adi_kucuk = hf_adi.lower()

    if "e5" in hf_adi_kucuk:
        metinler = [f"{onek}: {m}" for m in metinler]
    elif "bge" in hf_adi_kucuk and "-en" in hf_adi_kucuk:
        if onek == "query":
            metinler = [f"Represent this sentence for searching relevant passages: {m}" for m in metinler]
        # passage tarafına önek eklenmiyor — BAAI/bge-large-en-v1.5 model kartı kuralı

    return _onbellekli_encode(metinler, model_adi, batch_size)


def _onbellek_yolu(model_adi: str) -> Path:
    return METIN_ONBELLEK_DIZINI / f"{MODEL_TANIMLARI[model_adi].replace('/', '__')}.npz"


def _onbellek_oku(yol: Path) -> dict:
    if not yol.exists():
        return {}
    try:
        with np.load(yol, allow_pickle=False) as veri:
            return dict(zip(veri["anahtarlar"].tolist(), veri["vektorler"]))
    except Exception as hata:  # bozuk dosya: sessizce baştan hesapla
        print(f"  UYARI: metin önbelleği okunamadı ({hata}) — yeniden oluşturulacak.")
        return {}


def _onbellek_yaz(yol: Path, sozluk: dict):
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_name(yol.stem + "_yaziliyor.npz")
    np.savez(gecici,
             anahtarlar=np.array(list(sozluk.keys())),
             vektorler=np.stack(list(sozluk.values())).astype(np.float32))
    os.replace(gecici, yol)  # yarım yazılmış dosya asıl önbelleğin yerine geçmez


def _model_ile_encode(metinler: list[str], model_adi: str, batch_size: int) -> np.ndarray:
    model = model_yukle(model_adi)
    return model.encode(
        metinler,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )


def _onbellekli_encode(metinler: list[str], model_adi: str, batch_size: int) -> np.ndarray:
    if os.environ.get("BUS_ONBELLEK_KAPALI") == "1":
        return _model_ile_encode(metinler, model_adi, batch_size)

    yol = _onbellek_yolu(model_adi)
    sozluk = _onbellek_oku(yol)
    anahtarlar = [hashlib.sha1(m.encode("utf-8")).hexdigest() for m in metinler]

    eksik = {}  # anahtar -> metin (aynı metin iki kez varsa bir kez hesaplanır)
    for anahtar, metin in zip(anahtarlar, metinler):
        if anahtar not in sozluk and anahtar not in eksik:
            eksik[anahtar] = metin

    hazir = sum(1 for a in anahtarlar if a in sozluk)
    print(f"  [önbellek] {hazir}/{len(metinler)} metin önbellekten alındı, "
          f"{len(eksik)} metin yeni hesaplanacak.")
    if eksik:
        yeni = _model_ile_encode(list(eksik.values()), model_adi, batch_size)
        for anahtar, vektor in zip(eksik.keys(), yeni):
            sozluk[anahtar] = np.asarray(vektor, dtype=np.float32)
        _onbellek_yaz(yol, sozluk)

    return np.stack([sozluk[a] for a in anahtarlar]).astype(np.float32)


def kosinus_benzerlik_matrisi(vektor_a: np.ndarray, vektor_b: np.ndarray) -> np.ndarray:
    """
    İki embedding matrisi arasında tüm çift kombinasyonların kosinüs benzerliğini
    tek matris çarpımıyla hesaplar (vektörler zaten normalize edildiği için
    nokta çarpımı = kosinüs benzerliği).
    Dönüş şekli: (len(vektor_a), len(vektor_b))
    """
    return vektor_a @ vektor_b.T
