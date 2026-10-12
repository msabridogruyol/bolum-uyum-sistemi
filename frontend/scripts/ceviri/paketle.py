"""Çeviri parçalarını (ceviri/<dil>/<parca>_*.json, {id: çeviri}) katalog.json ile eşleyip
frontend/src/dil/<dil>.json paketini üretir/günceller: {"tr metni": "çeviri"}.
Kullanım: python3 paketle.py <katalog.json> <ceviri_klasoru> <dil> [<dil> ...]
(ceviri_klasoru boş/yok olabilir: yalnızca ek_ceviriler.json uygulanır)
Var olan paketteki çeviriler korunur; yeni parçalar üstüne yazılır. Kaynakla aynı olan çeviriler pakete konmaz."""
import json, glob, os, re, sys

BURASI = os.path.dirname(os.path.abspath(__file__))
HEDEF = os.path.join(BURASI, "..", "..", "src", "dil")
katalog = {str(x["i"]): x["tr"] for x in json.load(open(sys.argv[1]))}
yt = lambda m: sorted(re.findall(r"\{\d+\}", m))
for dil in sys.argv[3:]:
    yol = os.path.join(HEDEF, f"{dil}.json")
    paket = json.load(open(yol)) if os.path.exists(yol) else {}
    sayi = atla = 0
    for f in sorted(glob.glob(os.path.join(sys.argv[2], dil, "*.json"))):
        for i, c in json.load(open(f)).items():
            tr = katalog.get(str(i))
            c = (c or "").strip()
            if not tr or not c or yt(tr) != yt(c):
                atla += 1; continue
            if c == tr:
                paket.pop(tr, None); continue
            paket[tr] = c; sayi += 1
    # "1. Aşama · Bu hafta başla" gibi " · " ile birleşik metinler ekranda parça parça da görünür: parça çiftleri eklenir
    for tr, c in list(paket.items()):
        if " · " in tr and "{" not in tr:
            pt, pc = tr.split(" · "), c.split(" · ")
            if len(pt) == len(pc):
                for a_, b_ in zip(pt, pc):
                    a_, b_ = a_.strip(), b_.strip()
                    if len(a_) >= 3 and re.search(r"[^\W\d_]{3,}", a_) and a_ not in paket and a_ != b_:
                        paket[a_] = b_
    # Elle yazılmış ek çeviriler (ek_ceviriler.json) her zaman en son uygulanır
    ek = json.load(open(os.path.join(BURASI, "ek_ceviriler.json")))
    for tr, ceviriler in ek.items():
        if tr.startswith("_") or not isinstance(ceviriler, dict) or not ceviriler.get(dil):
            continue
        paket[tr] = ceviriler[dil]
    json.dump(dict(sorted(paket.items())), open(yol, "w"), ensure_ascii=False, separators=(",", ":"))
    print(dil, "çeviri", len(paket), "eklenen", sayi, "atlanan", atla, f"{os.path.getsize(yol)//1024} KB")
