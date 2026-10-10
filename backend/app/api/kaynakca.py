# -*- coding: utf-8 -*-
"""
[2026-10-10] Kaynakça — sistemde elle hazırlanan bileşenler ve dayandıkları kaynaklar.

Veri: app/data/kaynakca.json (docs/KAYNAKCA.md ile aynı içerik).
- Süper admin: tüm alanlar ("nasıl hesaplanıyor", ayrıntılı tasarım notları, künye doğrulama bilgisi).
- Okul yetkilisi: bileşen adı, açıklama ve kaynaklar; iç tasarım ayrıntıları (eşik, ceza puanı, güvenlik
  uygulaması vb.) yerine genel bir not gösterilir. Bu ayrıntılar frontend paketine de konmaz.
"""
import copy
import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends

from app.api.deps import get_mevcut_yonetim
from app.models import AdminKullanici

router = APIRouter(prefix="/yonetim", tags=["Kaynakça"])

_YOL = Path(__file__).resolve().parent.parent / "data" / "kaynakca.json"
GENEL_NOT_IC = "Bu bileşendeki eşik, ağırlık ve sayısal değerler kurum içi tasarım kararıdır; akademik bir kesme noktasına dayanmaz."
GENEL_NOT_KISMI = "Kaynaklar kavramsal dayanak sağlar; bileşendeki sayısal değerler kurum içi tasarım kararıdır."


@lru_cache(maxsize=1)
def _veri() -> dict:
    return json.loads(_YOL.read_text(encoding="utf-8"))


def okul_gorunumu(v: dict) -> dict:
    v = copy.deepcopy(v)
    for b in v["bilesenler"]:
        b.pop("nasil", None)
        b["not"] = GENEL_NOT_IC if b.get("ic") else (GENEL_NOT_KISMI if b.get("not") else "")
    for k in v["kaynaklar"]:
        k.pop("d", None)
    return v


@router.get("/kaynakca")
def kaynakca(admin: AdminKullanici = Depends(get_mevcut_yonetim)):
    v = _veri()
    return {**v, "ayrinti": True} if admin.rol == "super_admin" else {**okul_gorunumu(v), "ayrinti": False}
