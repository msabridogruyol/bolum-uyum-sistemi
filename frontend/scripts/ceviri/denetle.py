"""Bir çeviri parçasını denetler: eksik id, yer tutucu ({0}) uyuşmazlığı, bozuk JSON.
Kullanım: python3 denetle.py <calisma_klasoru> <dil> <parca_no>
  <calisma_klasoru>/parca/<parca_no>.json        — kaynak (birlestir.py çıktısından bölünmüş)
  <calisma_klasoru>/ceviri/<dil>/<parca_no>_*.json — çeviri ({id: çeviri})"""
import glob, json, os, re, sys

kok, dil, n = sys.argv[1], sys.argv[2], sys.argv[3]
d, bozuk = {}, []
for f in sorted(glob.glob(os.path.join(kok, "ceviri", dil, f"{n}_*.json"))):
    try:
        d.update(json.load(open(f)))
    except Exception as e:
        bozuk.append(f"{f}: {e}")
s = json.load(open(os.path.join(kok, "parca", f"{n}.json")))
eksik = [x["i"] for x in s if not str(d.get(str(x["i"]), "")).strip()]
yt = lambda m: sorted(re.findall(r"\{\d+\}", m))
hatali = [x["i"] for x in s if str(x["i"]) in d and yt(x["tr"]) != yt(str(d[str(x["i"])]))]
print(f"{dil} parça {n}: {len(d)}/{len(s)} · eksik {len(eksik)} {eksik[:30]} · yer tutucu hatası {len(hatali)} {hatali[:30]} · bozuk dosya {bozuk}")
