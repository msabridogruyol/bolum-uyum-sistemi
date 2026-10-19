"""[2026-10-19] Türkiye Yüzyılı Maarif Modeli ilişkilendirmesi (yorumsal; puanlamayı etkilemez).

Veri: app/data/maarif_eslesme.json — özellik kodu → [(tür, ad, kod?)]. Türler: değer (Erdem-Değer-Eylem çerçevesi),
eğilim (Beceri çerçevesi → Eğilimler), sdb (Sosyal-duygusal öğrenme becerisi), kavramsal (Kavramsal beceri).
Ekranlarda ve raporlarda "Maarif Modeli'nde ilişkili: …" diye gösterilir; birebir ölçüm ya da MEB onayı iddiası yoktur.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DOSYA = Path(__file__).resolve().parents[1] / "data" / "maarif_eslesme.json"
TUR_ADI = {"deger": "değer", "egilim": "eğilim", "sdb": "sosyal-duygusal beceri", "kavramsal": "kavramsal beceri"}
NOT = ("Maarif Modeli ilişkilendirmesi yorumsaldır: sonuçların, Türkiye Yüzyılı Maarif Modeli'nin değer, eğilim ve "
       "beceri çerçeveleriyle hangi kavramlara yakın olduğunu gösterir; puanlamayı etkilemez ve MEB onayı anlamına gelmez.")


@lru_cache(maxsize=1)
def _veri() -> dict:
    return json.loads(_DOSYA.read_text(encoding="utf-8"))["ozellikler"]


def karsiliklar(kod: str | None) -> list[dict]:
    """[{tur, tur_adi, ad, kod}] — eşleşme yoksa boş liste."""
    return [{"tur": x[0], "tur_adi": TUR_ADI.get(x[0], x[0]), "ad": x[1], "kod": x[2] if len(x) > 2 else None}
            for x in _veri().get(kod or "", [])]


def kisa_metin(kod: str | None) -> str:
    """'Merak · Açık fikirlilik' — eşleşme yoksa ''."""
    return " · ".join(x["ad"] for x in karsiliklar(kod))
