# -*- coding: utf-8 -*-
"""
[2026-10-10] Öğrenci özellik puanı (0–100) → düzey etiketi: TEK KAYNAK.

Öğrencinin değişken / katman puanlarını "Çok güçlü / Güçlü / ..." diye adlandıran her yer
(ekran açıklamaları, PDF / Excel raporları, "Neden bu bölüm?", "sende de güçlü" işareti,
gelişim yorum havuzu aralığı) bu modülü kullanır. Frontend karşılığı: frontend/src/yardimci/seviye.js
— bantlar değişirse İKİSİ birlikte güncellenmelidir.

Kapsam DIŞI (farklı kavramlar): anket şablonlarının kendi kesme puanları (anket_sablonlari.py),
bölüm uyum yüzdesi bantları, bölüm yüzdelik düzeyleri ("Bölüm: Yüksek"), koçluk gap kategorileri
(öğrenci − bölüm farkı).
"""

# Alt sınırlar (dahil), yüksekten düşüğe. "grup": güçlü / orta / gelişim (sayım ve renk için).
BANTLAR: list[dict] = [
    {"kod": "cok_guclu", "ad": "Çok güçlü", "alt": 75, "grup": "guclu"},
    {"kod": "guclu", "ad": "Güçlü", "alt": 62, "grup": "guclu"},
    {"kod": "ortanin_ustu", "ad": "Ortanın üstü", "alt": 50, "grup": "orta"},
    {"kod": "orta", "ad": "Orta", "alt": 40, "grup": "orta"},
    {"kod": "gelisime_acik", "ad": "Gelişime açık", "alt": 0, "grup": "gelisim"},
]
_KOD = {b["kod"]: b for b in BANTLAR}

COK_GUCLU_ESIK = _KOD["cok_guclu"]["alt"]   # 75
GUCLU_ESIK = _KOD["guclu"]["alt"]           # 62 — bu ve üstü "güçlü yön"
ORTA_ESIK = _KOD["orta"]["alt"]             # 40 — bunun altı "gelişime açık"

# Gelişim yorum havuzu (gelisim_yorum_havuzu.aralik) 5 kategori tutar; "gelişime açık" bandı
# içerikte ikiye ayrılır. Bu alt sınır yalnızca hangi yorumun seçileceğini belirler, etiket değildir.
YORUM_BELIRGIN_ALTINDA_ESIK = 20


def seviye_bandi(puan: float | None) -> dict | None:
    if puan is None:
        return None
    p = float(puan)
    for b in BANTLAR:
        if p >= b["alt"]:
            return b
    return BANTLAR[-1]


def seviye_etiketi(puan: float | None) -> str:
    b = seviye_bandi(puan)
    return b["ad"] if b else "—"


def seviye_grubu(puan: float | None) -> str | None:
    b = seviye_bandi(puan)
    return b["grup"] if b else None


def guclu_mu(puan: float | None) -> bool:
    return puan is not None and float(puan) >= GUCLU_ESIK


def gelisime_acik_mi(puan: float | None) -> bool:
    return puan is not None and float(puan) < ORTA_ESIK


def yorum_araligi(puan: float) -> str:
    """Bantları gelisim_yorum_havuzu.aralik değerlerine eşler (belirgin_ustun ... belirgin_altinda)."""
    kod = seviye_bandi(puan)["kod"]
    if kod == "cok_guclu":
        return "belirgin_ustun"
    if kod == "guclu":
        return "ustun"
    if kod in ("ortanin_ustu", "orta"):
        return "beklenti"
    return "altinda" if float(puan) >= YORUM_BELIRGIN_ALTINDA_ESIK else "belirgin_altinda"
