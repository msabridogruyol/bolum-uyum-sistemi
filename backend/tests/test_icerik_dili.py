"""[2026-11-02] Öğrenciye görünen içerikte lise düzeyine uygun dil (kalıcı denetim).

Kurallar (öğrenciye gösterilen veri dosyaları + bölüm tanıtımı düzeltmeleri):
  1. Ağır / resmî / akademik sözcükler (tetkik, minimal, konsept, metodoloji…) açıklamasız kullanılmaz: ya günlük karşılığı
     yazılır ya da hemen ardından parantez içinde kısa bir açıklama gelir. Ders, kanun ve sözlük terimi adları istisnadır.
  2. Cümleler 34 sözcüğü geçmez (uzun cümleler bölünür).
  3. Bilinen yazım hataları ("diyalogu", "pilic") geri gelmez.
Yeni içerik eklenince bu test kırılırsa metin sadeleştirilir; test gevşetilmez.
"""
import json
import re
from pathlib import Path

VERI = Path(__file__).resolve().parents[1] / "app" / "data"
DOSYALAR = ["meslek_senaryolari.json", "mulakat_simulasyonu.json", "zor_gunler.json", "meslege_yol.json", "is_hayati_dersler.json",
            "dusunme_atolyesi.json", "cv_rehberi.json", "rapor_yorumlari.json", "is_hayati_mulakat.json", "sozluk_temel.json",
            "sozluk_genis.json", "k5_soru_bankasi.json", "ornek_ilanlar.json"]
META = {"aciklama", "surum", "kaynak", "kaynaklar", "not", "notlar", "yontem", "lisans", "kapsam", "turler", "genel_not"}
AGIR = ("tetkik", "mukayese", "minimal", "konsept", "metodoloji", "operasyonel", "spesifikasyon", "epistemoloji", "ontoloji",
        "binaenaleyh", "mütevellit", "hasebiyle", "işbu", "mezkur", "nezdinde", "teemmül", "muhteva", "istihsal", "paradigma",
        "sosyoekonomik", "psikososyal", "enstrümantal", "tahakkuk", "mukabil")
CUMLE = re.compile(r"(?<=[.!?…])\s+(?=[A-ZÇĞİÖŞÜ0-9“\"'(])")
TOK = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüâîûÂÎÛ]+")
EN_UZUN = 34


def _kucuk(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def _metinler(x, yol=()):
    if isinstance(x, str):
        yield yol, x
    elif isinstance(x, dict):
        for k, v in x.items():
            if (not yol and k in META) or k in ("kaynaklar", "kaynak"):
                continue
            yield from _metinler(v, yol + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _metinler(v, yol + (i,))


def _tum():
    for ad in DOSYALAR:
        yield from ((ad, yol, m) for yol, m in _metinler(json.loads((VERI / ad).read_text(encoding="utf-8"))))
    jargon = json.loads((VERI.parent / "core" / "meslek_jargonu.json").read_text(encoding="utf-8"))
    for bolum, liste in jargon.items():
        for i, t in enumerate(liste):
            for k in ("anlam", "ornek"):
                if t.get(k):
                    yield "meslek_jargonu.json", (bolum, i, k, t.get("terim", "")), t[k]
    veri = json.loads((VERI / "icerik_sadelestirme.json").read_text(encoding="utf-8"))
    for i, x in enumerate(veri["bolum_detay"] + veri["kisa_aciklama"] + veri["tablo"]):
        yield "icerik_sadelestirme.json", (i, "yeni"), x["yeni"]


def _aciklamali(m: str, bas: int, son: int) -> bool:
    """Sözcüğün hemen ardından (en çok iki sözcük sonra) parantezli açıklama gelir, sözcük parantez içindedir ya da cümle
    onu tanımlar ("…; buna psikososyal değerlendirme denir")."""
    sonrasi = m[son:son + 40]
    return (bool(re.match(r"^\w*(?:\s+\w+){0,2}\s*\(", sonrasi)) or "(" in m[max(0, bas - 40):bas].split(")")[-1]
            or m[max(0, bas - 8):bas].strip().lower().endswith("buna"))


def _ad_mi(ad: str, yol: tuple, m: str) -> bool:
    """Ders / bölüm / sözlük terimi adı (başlık biçiminde kısa metin) ya da sözlükte tanımlanan terimin kendisi."""
    if ad == "sozluk_genis.json" and len(yol) >= 3 and yol[2] in (0, 4):
        return True
    if ad == "sozluk_temel.json" and yol and yol[-1] in ("ad", "es", "k") or (len(yol) >= 2 and yol[-2] == "es"):
        return True
    return len(m.split()) <= 4 and all(w[:1].isupper() for w in m.split() if len(w) > 3)


def _sozluk_terimleri() -> dict:
    """sozluk_genis: terim sırası → terim adı ve eş adlarındaki sözcükler (örnek cümlede terimin kendisi geçebilir)."""
    d = json.loads((VERI / "sozluk_genis.json").read_text(encoding="utf-8"))
    return {i: {_kucuk(w) for w in TOK.findall(" ".join([str(t[0])] + [str(x) for x in (t[4] if len(t) > 4 else [])]))}
            for i, t in enumerate(d["terimler"])}


def test_agir_sozcuk_aciklamasiz_kullanilmaz():
    hatalar = []
    terim = _sozluk_terimleri()
    for ad, yol, m in _tum():
        if _ad_mi(ad, yol, m):
            continue
        for t in TOK.finditer(m):
            w = _kucuk(t.group(0))
            if ad == "sozluk_genis.json" and len(yol) >= 2 and any(w.startswith(x[:6]) for x in terim.get(yol[1], ()) if len(x) >= 6):
                continue   # sözlük maddesinin örnek cümlesinde tanımlanan terimin kendisi
            if ad == "meslek_jargonu.json" and any(w.startswith(_kucuk(x)[:6]) for x in TOK.findall(yol[3]) if len(x) >= 6):
                continue   # meslek dili maddesinin tanımında / örneğinde tanımlanan terimin kendisi
            if any(w.startswith(a) for a in AGIR) and not _aciklamali(m, t.start(), t.end()):
                # Ders adı içinde ("Tarih Metodolojisi dersinde") ya da resmî ad ("Tebliğ") olarak büyük harfle geçiyorsa geçer
                if t.group(0)[0].isupper() and t.start() > 0 and m[t.start() - 2] not in ".!?":
                    continue
                hatalar.append(f"{ad} {list(yol)[:5]}: {t.group(0)} | {m[:120]}")
    assert not hatalar, "Açıklamasız ağır sözcük:\n" + "\n".join(hatalar[:30])


def test_cumleler_cok_uzun_degil():
    uzun = [f"{ad} {list(yol)[:4]}: {len(TOK.findall(c))} sözcük | {c[:100]}"
            for ad, yol, m in _tum() for c in CUMLE.split(m) if len(TOK.findall(c)) > EN_UZUN]
    assert not uzun, "Çok uzun cümle (bölünmeli):\n" + "\n".join(uzun[:30])


def test_bilinen_yazim_hatalari_geri_gelmez():
    kotu = re.compile(r"\b(diyalogu|pilic|seperatör|rettin)\b", re.I)
    hatalar = [f"{ad} {list(yol)[:4]}: {m[:100]}" for ad, yol, m in _tum() if kotu.search(m)]
    assert not hatalar, "\n".join(hatalar)


def test_sadelestirme_goc_verisi_tutarli():
    """Her düzeltmede eski ≠ yeni, sayılar korunmuş; göç SQL'i üretilebiliyor."""
    import importlib.util
    veri = json.loads((VERI / "icerik_sadelestirme.json").read_text(encoding="utf-8"))
    sayi = re.compile(r"\d+(?:[.,]\d+)?")
    for x in veri["bolum_detay"] + veri["kisa_aciklama"] + veri["tablo"]:
        assert x["eski"] != x["yeni"]
        assert sorted(sayi.findall(x["eski"])) == sorted(sayi.findall(x["yeni"])) or \
            set(sayi.findall(x["eski"])) <= set(sayi.findall(x["yeni"])), x
    yol = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0089_icerik_sadelestirme.py"
    spec = importlib.util.spec_from_file_location("g0089", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert "UPDATE bolumler SET detay" in m.SQL and "meslek_grubu_ai_etkisi" in m.SQL
