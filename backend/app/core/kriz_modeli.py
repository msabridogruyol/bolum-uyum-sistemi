# -*- coding: utf-8 -*-
"""
[2026-11-03] Kriz algılamanın ikinci katmanı: harf n-gram'lı küçük bir sınıflandırıcı (yapay zekâ servisi değildir,
sunucuda yerel çalışır, internete çıkmaz, ek kütüphane gerektirmez).

Neden: kural desenleri (ai_koc_servisi._KRIZ_DESENLERI) açık ifadeleri yakalar ama hiç görmediği örtük ifadelerde
yaklaşık yarısını kaçırıyordu (kör setlerde düzeltme öncesi %47–59). Sınıflandırıcı sözcük parçalarından (3–5 harf)
öğrendiği için yazım hatasına ve yeni ifadelere daha dayanıklıdır; ama yanlış alarmı da daha fazladır. Bu yüzden:
  * kural tutarsa → kesin kriz (sabit kriz cevabı; okul ayarı açıksa okul yetkilisine bildirim),
  * yalnız sınıflandırıcı tutarsa → "olası" (yumuşak destek cevabı; bildirim YOK, öğrenciden açıklama istenir).

Model: app/data/kriz_modeli.json — scripts/kriz_modeli_egit.py ile üretilir (eğitim scikit-learn ister; çalışma anında
bu dosya yalnızca sözlük, ağırlık ve eşik okur). Özellikler eğitimdekiyle aynı fonksiyondan (ngramlar) çıkar.
"""
from __future__ import annotations

import json
import math
import re
import threading
from collections import Counter
from pathlib import Path

_YOL = Path(__file__).resolve().parents[1] / "data" / "kriz_modeli.json"
_model: dict | None = None
_kilit = threading.Lock()


def sadelestir(metin: str | None) -> str:
    t = str(metin or "").replace("İ", "i").replace("I", "ı").lower().replace("i̇", "i")
    t = t.translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def ngramlar(metin: str, en_az: int = 3, en_cok: int = 5) -> list[str]:
    """Sözcük sınırlı harf n-gram'ları (scikit-learn 'char_wb' ile aynı kural): her sözcük boşlukla çevrilir."""
    out: list[str] = []
    for w in sadelestir(metin).split():
        w = f" {w} "
        for n in range(en_az, en_cok + 1):
            if len(w) < n:
                out.append(w)
                break
            out.extend(w[i:i + n] for i in range(len(w) - n + 1))
    return out


def _yukle() -> dict | None:
    global _model
    if _model is None:
        with _kilit:
            if _model is None:
                try:
                    _model = json.loads(_YOL.read_text(encoding="utf-8"))
                except FileNotFoundError:
                    _model = {}
    return _model or None


def olasilik(metin: str | None) -> float:
    """Mesajın kriz olma olasılığı (0–1). Model dosyası yoksa 0."""
    m = _yukle()
    if not m or not metin:
        return 0.0
    tf = Counter(g for g in ngramlar(metin, m["en_az"], m["en_cok"]) if g in m["idf"])
    if not tf:
        return 1.0 / (1.0 + math.exp(-m["sabit"]))
    agirlik = {g: (1.0 + math.log(n)) * m["idf"][g] for g, n in tf.items()}       # sublinear tf × idf
    norm = math.sqrt(sum(v * v for v in agirlik.values())) or 1.0
    z = m["sabit"] + sum(v / norm * m["katsayi"].get(g, 0.0) for g, v in agirlik.items())
    return 1.0 / (1.0 + math.exp(-z))


def olasi_kriz_mi(metin: str | None) -> bool:
    m = _yukle()
    return bool(m) and olasilik(metin) >= m["esik"]
