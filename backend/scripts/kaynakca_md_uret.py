# -*- coding: utf-8 -*-
"""[2026-10-10] backend/app/data/kaynakca.json → docs/KAYNAKCA.md (süper admin görünümü). Çalıştır: python3 backend/scripts/kaynakca_md_uret.py"""
import json
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
d = json.loads((KOK / "backend/app/data/kaynakca.json").read_text(encoding="utf-8"))
K = {k["id"]: k for k in d["kaynaklar"]}
L = ["# Filizyol — Kaynakça (iç kullanım)", "",
     "Sistemde elle hazırlanan her bileşen, ne yaptığı, nasıl hesaplandığı ve dayandığı akademik/resmî kaynaklar.", "",
     "- Uygulamada: **Yönetici Paneli → Sistem → Kaynakça** (tam görünüm) ve **Okul Paneli → Yardım → Kaynakça** (okul görünümü: iç süreç bileşenleri, \"Nasıl\" ayrıntıları ve tasarım notları gösterilmez).",
     "- Veri kaynağı: `backend/app/data/kaynakca.json`; bu dosya `backend/scripts/kaynakca_md_uret.py` ile üretilir.",
     "- Kaynaklar bileşenin **kuramsal dayanağını** gösterir; Filizyol ölçekleri bu kaynaklardaki ölçeklerin birebir uyarlaması değildir.",
     "- **Kurum içi** işaretli bileşenlerde eşik, ağırlık ve sayılar ürün tasarımı kararıdır.", "",
     f"Toplam: {len(d['bilesenler'])} bileşen, {len(d['kaynaklar'])} kaynak.", "", "## İçindekiler", ""]
L += [f"- {g}" for g in d["gruplar"]] + ["- [Tüm kaynaklar (APA 7)](#tüm-kaynaklar-apa-7)", ""]
for g in d["gruplar"]:
    L += [f"## {g}", ""]
    for b in [b for b in d["bilesenler"] if b["g"] == g]:
        L += [f"### {b['b']}" + (" · _Kurum içi_" if b["ic"] else "") + ("" if b.get("okul", True) else " · _Okul görünümünde yok_"), "",
              b["ne"], "", f"**Nasıl:** {b['nasil']}", ""]
        if b["k"]:
            L += ["**Dayanak:**", ""] + [f"- [{r['id']}] {K[r['id']]['kisa']} — {r['destek']}" for r in b["k"]] + [""]
        else:
            L += ["**Dayanak:** Akademik dayanak yok.", ""]
        if b["not"]:
            L += [f"> {b['not']}", ""]
L += ["## Tüm kaynaklar (APA 7)", ""]
for k in d["kaynaklar"]:
    L.append(f"{k['id']}. {k['a']}" + (f" <{k['u']}>" if k["u"] and k["u"] not in k["a"] else ""))
    if k.get("d"):
        L.append(f"   - Doğrulama: {k['d']}")
L += ["", "## Doğrulanamayan ve listeye alınmayan künyeler", "",
      "- Türk Psikologlar Derneği Etik Yönetmeliği (2004) — resmî metne erişilemedi.",
      "- Spielberger (1980) Test Anxiety Inventory el kitabı — katalog kaydı bulunamadı; yerine Zeidner (1998), Hembree (1988), von der Embse ve ark. (2018).",
      "- Super (1970) Work Values Inventory — künye doğrulanamadı.",
      "- Osipow (1987) Career Decision Scale el kitabı — yalnızca ölçeğin kendisi doğrulandı.",
      "- ÖSYM 2026-YKS ana kılavuz PDF'i — sayfa açılamadı; ÖSYM SSS belgesi kullanıldı.",
      "- Kaiser & Overfield (2011), Meade (2004), Gibson (2004), Yeager ve ark. (2019), Edwards (1991), Ong & Weiss (2000) — künye ayrıntıları doğrulanamadığı için eklenmedi.",
      "- Bazı künyelerde DOI veya sayı numarası boş bırakıldı (birincil kaynakta görülemedi).", ""]
(KOK / "docs/KAYNAKCA.md").write_text("\n".join(L), encoding="utf-8")
print("yazıldı", len(L), "satır")
