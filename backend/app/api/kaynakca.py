# -*- coding: utf-8 -*-
"""
[2026-10-10] Kaynakça — sistemde elle hazırlanan bileşenler ve dayandıkları kaynaklar.

Veri: app/data/kaynakca.json (docs/KAYNAKCA.md ile aynı içerik).
- Süper admin: tüm alanlar ("nasıl hesaplanıyor", ayrıntılı tasarım notları, künye doğrulama bilgisi).
- Okul yetkilisi: okulun kullandığı bileşenler, okul için yazılmış açıklama (ne_o) ve destek cümleleri (destek_o).
  İç süreçler (okul=false), tasarım notları ve hesaplama ayrıntıları gönderilmez; frontend paketinde de yoktur.
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


@lru_cache(maxsize=1)
def _veri() -> dict:
    return json.loads(_YOL.read_text(encoding="utf-8"))


def okul_gorunumu(v: dict) -> dict:
    """Okul yetkilisi görünümü: yalnızca okulun kullandığı bileşenler, okul için yazılmış açıklama ve destek cümleleri.
    İç tasarım notları, hesaplama ayrıntıları ve künye doğrulama notları gönderilmez."""
    bilesenler = []
    for b in v["bilesenler"]:
        if not b.get("okul"):
            continue
        k = [{"id": r["id"], "destek": r["destek_o"]} for r in b["k"] if r.get("destek_o")]
        if not k:
            continue
        bilesenler.append({"g": b["g"], "b": b["b"], "ne": b.get("ne_o") or b["ne"], "k": k, "not": "", "ic": False})
    kullanilan = {r["id"] for b in bilesenler for r in b["k"]}
    kaynaklar = [{x: k[x] for x in ("id", "a", "u", "kisa")} for k in v["kaynaklar"] if k["id"] in kullanilan]
    return {"gruplar": v["gruplar"], "bilesenler": bilesenler, "kaynaklar": kaynaklar}


def admin_gorunumu(v: dict) -> dict:
    v = copy.deepcopy(v)
    for b in v["bilesenler"]:
        b.pop("ne_o", None)
        b.pop("okul", None)
        for r in b["k"]:
            r.pop("destek_o", None)
    return v


@router.get("/kaynakca")
def kaynakca(admin: AdminKullanici = Depends(get_mevcut_yonetim)):
    v = _veri()
    return {**admin_gorunumu(v), "ayrinti": True} if admin.rol == "super_admin" else {**okul_gorunumu(v), "ayrinti": False}
