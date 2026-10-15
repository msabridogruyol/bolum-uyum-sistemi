"""fe.json + be.json + veritabanı etiketleri → katalog.json [{i, tr, tur, yer}] ve çeviri parçaları."""
import json, re, psycopg2, sys, os

fe = json.load(open("fe.json"))
be = json.load(open("be.json"))
ATLA_BE = ("core/rapor/", "core/eposta_servisi.py", "core/kvkk_metinleri.py", "core/meslek_senaryolari.py")

def adli_yer_tutucu(m):
    sayac = {}
    def r(x):
        ad = x.group(1)
        if ad not in sayac: sayac[ad] = len(sayac)
        return "{%d}" % sayac[ad]
    return re.sub(r"\{([a-z_][a-z_0-9]*)\}", r, m)

kat = {}
def ekle(m, tur, yer):
    m = re.sub(r"\s+", " ", m).strip()
    if not m or not re.search(r"[^\W\d_]", re.sub(r"\{\d+\}", "", m)):
        return
    if m not in kat:
        kat[m] = {"tr": m, "tur": tur, "yer": yer}
    elif tur == "soru":
        kat[m]["tur"] = "soru"

for m, fs in fe.items():
    ekle(m, "arayuz", fs[0])
for m, fs in be.items():
    fs = [f for f in fs if not f.startswith(ATLA_BE)]
    if not fs: continue
    ekle(adli_yer_tutucu(m), "icerik" if fs[0].startswith("core/gelisim") else "arayuz", "be:" + fs[0])

c = psycopg2.connect("postgresql://postgres:pg@localhost/k5test2"); cur = c.cursor()
SORGULAR = [
    ("select soru_metni from sorular", "soru", "db:sorular"),
    ("select secenek_metni from soru_secenekleri", "soru", "db:soru_secenekleri"),
    ("select ad from degiskenler union select aciklama from degiskenler", "etiket", "db:degiskenler"),
    ("select ad from bolumler", "etiket", "db:bolumler"),
    ("select ad from sinav_konulari union select ders from sinav_konulari", "etiket", "db:sinav_konulari"),
    ("select ad from dallar union select alt_alan from bolum_dal_eslesme", "etiket", "db:dallar"),
    ("select meslek_adi from meslek_isco", "etiket", "db:meslek_isco"),
    ("select ad from katmanlar", "etiket", "db:katmanlar"),
    ("select baslik from gelisim_kaynak_onerileri union select aciklama from gelisim_kaynak_onerileri", "etiket", "db:gelisim_kaynak"),
    ("select ad from paketler union select aciklama from paketler", "etiket", "db:paketler"),
    ("select aciklama from meslek_grubu_ai_etkisi union select kaynak_bolum from meslek_grubu_ai_etkisi", "etiket", "db:ai_etkisi"),
]
for q, tur, yer in SORGULAR:
    cur.execute(q)
    for (m,) in cur.fetchall():
        if m: ekle(m, tur, yer)

liste = sorted(kat.values(), key=lambda x: (x["yer"], x["tr"]))
for i, x in enumerate(liste): x["i"] = i
json.dump(liste, open("katalog.json", "w"), ensure_ascii=False)
from collections import Counter
print(len(liste), sum(len(x["tr"]) for x in liste), Counter(x["tur"] for x in liste))
print({t: sum(len(x["tr"]) for x in liste if x["tur"] == t) for t in ("arayuz", "icerik", "soru", "etiket")})
