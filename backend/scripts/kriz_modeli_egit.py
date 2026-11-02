"""[2026-11-03] Kriz algılama sınıflandırıcısını eğitir → app/data/kriz_modeli.json (app/core/kriz_modeli.py okur).

Veri:
  * tests/veri/kriz_ornekleri.jsonl — dört kör set (kodu görmemiş ayrı yazarlar): kriz cümleleri + zor yakın örnekler
    (karanlık sözcüklü kariyer soruları, abartı ve deyimler, oyun/film/spor). 'set' alanı yoksa satır sırasından bulunur.
  * scripts/veri/kriz_normal_ornekler.txt — Filiz'e sorulan sıradan sorular (simülasyon ve kör test; kriz değil).
Ölçüm: son kör set dışarıda bırakılarak eğitilir ve o sette ölçülür (görülmemiş ifadeler); ardından tüm veriyle son model.
Eşik: dışarıdaki sette normal sorularda yanlış alarm ≤ %0,3 olacak biçimde seçilir (yalnızca "olası" katman; yumuşak cevap).

Kullanım: python scripts/kriz_modeli_egit.py      (scikit-learn gerekir; yalnızca geliştirmede)
"""
import json
import random
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402

from app.core.ai_koc_servisi import kriz_mesaji_mi  # noqa: E402
from app.core.kriz_modeli import ngramlar  # noqa: E402

SET_BOYUT = [180, 140, 120, 100]       # kriz_ornekleri.jsonl'deki dört setin satır sayısı (sırayla)
NORMAL_FP_HEDEF = 0.003


def veri():
    satir = [json.loads(s) for s in (KOK / "tests" / "veri" / "kriz_ornekleri.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
    setler, i = [], 0
    for n in SET_BOYUT:
        setler.append(satir[i:i + n])
        i += n
    normal = [s for s in (KOK / "scripts" / "veri" / "kriz_normal_ornekler.txt").read_text(encoding="utf-8").splitlines() if s.strip()]
    return setler, normal


def egit(X, y):
    v = TfidfVectorizer(analyzer=ngramlar, min_df=2, sublinear_tf=True, norm="l2", smooth_idf=True)
    m = LogisticRegression(C=4.0, class_weight="balanced", max_iter=4000)
    m.fit(v.fit_transform(X), y)
    return v, m


def main():
    setler, normal = veri()
    random.seed(11)
    random.shuffle(normal)
    n_test = len(normal) // 3
    normal_test, normal_egitim = normal[:n_test], normal[n_test:]

    # 1) görülmemiş set ölçümü: son set dışarıda
    egitim = [o for s in setler[:-1] for o in s]
    test = setler[-1]
    v, m = egit([o["metin"] for o in egitim] + normal_egitim, [int(o["kriz"]) for o in egitim] + [0] * len(normal_egitim))
    p_test = m.predict_proba(v.transform([o["metin"] for o in test]))[:, 1]
    p_norm = sorted(m.predict_proba(v.transform(normal_test))[:, 1], reverse=True)
    esik = max(0.5, float(p_norm[int(len(p_norm) * NORMAL_FP_HEDEF)]) + 1e-6)
    kriz = [o for o in test if o["kriz"]]
    yakin = [o for o in test if not o["kriz"]]
    tut = lambda o, p: p >= esik or kriz_mesaji_mi(o["metin"])  # noqa: E731
    print(f"eşik {esik:.3f}")
    print(f"görülmemiş set: kural {sum(kriz_mesaji_mi(o['metin']) for o in kriz)}/{len(kriz)} · "
          f"kural+model {sum(tut(o, p) for o, p in zip(test, p_test) if o['kriz'])}/{len(kriz)} · "
          f"yakın örnekte alarm {sum(tut(o, p) for o, p in zip(test, p_test) if not o['kriz'])}/{len(yakin)} · "
          f"normal soruda model alarmı {sum(p >= esik for p in p_norm)}/{len(p_norm)}")

    # 2) son model: bütün veri
    hepsi = [o for s in setler for o in s]
    v, m = egit([o["metin"] for o in hepsi] + normal, [int(o["kriz"]) for o in hepsi] + [0] * len(normal))
    idf = dict(zip(v.get_feature_names_out(), v.idf_))
    katsayi = {g: round(float(k), 5) for g, k in zip(v.get_feature_names_out(), m.coef_[0]) if abs(k) >= 1e-4}
    model = {"surum": "2026-11-03", "en_az": 3, "en_cok": 5, "esik": round(esik, 4), "sabit": round(float(m.intercept_[0]), 5),
             "idf": {g: round(float(x), 4) for g, x in idf.items()}, "katsayi": katsayi,
             "aciklama": "scripts/kriz_modeli_egit.py ile üretildi; elle değiştirmeyin."}
    yol = KOK / "app" / "data" / "kriz_modeli.json"
    yol.write_text(json.dumps(model, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"yazıldı: {yol} ({yol.stat().st_size // 1024} KB, {len(idf)} özellik)")


if __name__ == "__main__":
    main()
