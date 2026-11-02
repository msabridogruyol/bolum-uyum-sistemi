"""[2026-11-02] Değerlendirme soruları (K1–K5): lise düzeyi, tekrar etmeme ve 0090 göç verisinin tutarlılığı.

Genel dil kuralları (ağır sözcük, uzun cümle) test_icerik_dili.py'de; burada soruya özgü kurallar var:
  1. Soru kökleri birbirinin tekrarı değildir (aynı katmanda iki kök ≥ %50 aynı içerik sözcüğü taşımaz).
  2. Şıklar kısa kalır (≤ 22 sözcük) ve K5 etkinlik cümleleri ≤ 16 sözcüktür.
  3. 0090 verisi: her yeni metin kaynak dosyada vardır, eski metin kalmamıştır; değişken eşlemesi göçte taşınmaz.
"""
import itertools
import json
import re
from pathlib import Path

VERI = Path(__file__).resolve().parents[1] / "app" / "data"
TOK = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüâîûÂÎÛ]+")
_BOS = {"hangisi", "hangi", "sana", "daha", "yakın", "uyar", "bir", "olur", "yapar", "ister", "seçer", "almak", "işi",
        "seçec", "olsan", "senin", "yaparsın", "isters", "hangis"}


def _sorular():
    return (json.loads((VERI / "olcme_sorulari.json").read_text(encoding="utf-8"))["sorular"]
            + json.loads((VERI / "olcme_sorulari_ek.json").read_text(encoding="utf-8"))["sorular"])


def _kokler(m: str) -> set:
    return {w.lower()[:5] for w in TOK.findall(m) if len(w) > 3} - _BOS


def test_soru_kokleri_birbirini_tekrar_etmez():
    benzer = []
    for a, b in itertools.combinations([q for q in _sorular() if q["tip"] != "kontrol"], 2):
        if a["katman"] != b["katman"]:
            continue
        x, y = _kokler(a["metin"]), _kokler(b["metin"])
        if x and y and len(x & y) / len(x | y) >= 0.5:
            benzer.append(f"{a['metin']}  ~  {b['metin']}")
    assert not benzer, "\n".join(benzer)


def test_siklar_kisa():
    uzun = []
    for q in _sorular():
        sec = [q.get("uc_a"), q.get("uc_b")] if q["tip"] == "kutup" else \
            [s["metin"] if isinstance(s, dict) else s for s in q["secenekler"]]
        uzun += [m for m in sec if m and len(TOK.findall(m)) > 22]
    banka = json.loads((VERI / "k5_soru_bankasi.json").read_text(encoding="utf-8"))
    uzun += [m for l in banka["cumleler"].values() for m in l if len(TOK.findall(m)) > 16]
    assert not uzun, "\n".join(uzun)


def test_sadelestirme_goc_verisi_kaynakla_tutarli():
    import importlib.util
    veri = json.loads((VERI / "soru_sadelestirme.json").read_text(encoding="utf-8"))["sorular"]
    kaynak = (VERI / "olcme_sorulari.json").read_text(encoding="utf-8") + (VERI / "olcme_sorulari_ek.json").read_text(encoding="utf-8")
    for x in veri:
        ciftler = [(x["eski_metin"], x["yeni_metin"])] + [tuple(u) for u in (x["uc_a"], x["uc_b"]) if u] + \
                  [(s["eski"], s["yeni"]) for s in x["secenekler"]]
        for e, y in ciftler:
            assert json.dumps(y, ensure_ascii=False) in kaynak, y
            if e != y:
                assert json.dumps(e, ensure_ascii=False) not in kaynak, e
        assert "degisken" not in json.dumps(x), "göç değişken eşlemesine dokunmaz"
    yol = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0090_soru_sadelestirme.py"
    spec = importlib.util.spec_from_file_location("g0090", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert "UPDATE soru_secenekleri" in m.SQL and ";\n" not in m.SQL.rstrip()[:-1]


def test_k5_kokleri_her_cumleye_uyar():
    """Kökler rastgele iş türü cümleleriyle eşleşir: belirli bir mesleğe/ortama bağlı kök olmamalı."""
    banka = json.loads((VERI / "k5_soru_bankasi.json").read_text(encoding="utf-8"))
    for tip, liste in banka["kokler"].items():
        assert len(liste) == len(set(liste)) and len(liste) >= 4, tip
        for k in liste:
            assert k.rstrip().endswith("?"), k
            if tip == "encok":
                assert "en çok" in k and "en az" in k, k
