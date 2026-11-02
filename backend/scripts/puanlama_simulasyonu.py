"""[2026-11-02] 50.000+ sanal öğrencilik puanlama/eşleştirme simülasyonu.

Kullanım: DATABASE_URL=... python scripts/puanlama_simulasyonu.py [tam|deneme] [cikti.json]

Sistemin KENDİ fonksiyonları kullanılır (kopya mantık yok):
  katman_servisi.cevaplari_puanla      -> cevaptan değişken puanı (likert / sjt / en çok-en az / kutup)
  skor_motoru._bolum_verisi_hesapla    -> bölüm matrisi, ağırlıklar, katman içi ölçek
  skor_motoru._katman_ici_olcekle, YONTEMLER, _min_max_0_100, _kendall_w  -> 10 yöntem, ortalama
  dal_servisi.soru_plani, bolum_k5_puanlari, KUME_*  -> K5 soruları ve K5 puanı
  skor_motoru.k5_nihai                 -> K5 küme içi yeniden sıralama
Veritabanına yazılmaz; yalnızca okunur.

Sanal öğrenci: bir "gerçek bölüm" b* seçilir. Öğrencinin gerçek profili = b* bölümünün katman içi ölçekli profili
+ kişisel sapma N(0, sp). Cevaplar bu profilden gürültüyle üretilir (likert: N(0, sr); seçmeli: Gumbel, sıcaklık tau).
K5: b*'nin bağlı iş türleri bağ ağırlığıyla tercih edilir (+ gürültü). Öz-isabet = b*'nin öğrencinin listesindeki sırası.
"""
import json
import math
import random
import sys
import time
from collections import Counter, defaultdict
from types import SimpleNamespace

import numpy as np

import os  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
if "DATABASE_URL" not in os.environ:
    sys.exit("DATABASE_URL gerekli (içerikli bir veritabanı; yalnızca okunur).")
from app.core.database import SessionLocal  # noqa: E402
from app.core import skor_motoru as sm, dal_servisi as ds  # noqa: E402
from app.core.katman_servisi import cevaplari_puanla, puanlama_onbellegi, parametre_oku  # noqa: E402
from app.models import Soru, Katman, Degisken  # noqa: E402

db = SessionLocal()
haric = frozenset(k.strip() for k in (parametre_oku(db, "eslesme_disi_degiskenler", "P4") or "").split(",") if k.strip())
V = sm._bolum_verisi_hesapla(db, haric)
did = V["degisken_idler"]; jx = {d: j for j, d in enumerate(did)}
B = V["bolum_idler"]; nB = len(B); bix = {b: i for i, b in enumerate(B)}
BO = V["bolum_olcekli"]; W = V["agirliklar"]; G = V["gruplar"]
adlar = V["bolum_adlari"]
# profil komşuları: b*'ye ağırlıklı uzaklıkça en yakın 10 bölüm (alan verisi bu kopyada yok)
_D = np.sqrt((((BO[:, None, :] - BO[None, :, :]) ** 2) * W[None, None, :]).sum(-1))
KOMSU10 = {B[i]: {B[j] for j in np.argsort(_D[i])[1:11]} for i in range(nB)}

ana = [k.id for k in db.query(Katman).filter(Katman.kosullu_mu.is_(False)).all()]
sorular = db.query(Soru).filter(Soru.katman_id.in_(ana), Soru.aktif_mi.is_(True), Soru.ogrenci_id.is_(None)).order_by(Soru.id).all()
sdict = {s.id: s for s in sorular}
onb = puanlama_onbellegi(db, list(sdict))
for s in sorular:
    db.expunge(s)
SQ = []
for s in sorular:
    secs = sorted(onb["soru_secenekleri"].get(s.id, []), key=lambda x: x.secenek_sirasi)
    SQ.append((s, secs, [[(a.degisken_id, float(a.agirlik)) for a in onb["agirlik"].get(x.id, [])] for x in secs]))

# K5 verisi (tüm bölümler için bir kez)
baglar_hepsi = ds._baglar(db, B)
cumleler = ds._cumleler(db, {e for d in baglar_hepsi.values() for e in d})
kokler = ds._kokler(db)
db.close()
print(f"bölüm {nB} · eşleşme değişkeni {len(did)} · soru {len(SQ)} · K5 bağlı bölüm {len(baglar_hepsi)}", flush=True)


def gumbel(r):
    return -math.log(-math.log(r.random() + 1e-12) + 1e-12)


def cevapla(r, L, sr, tau, rastgele):
    """L: degisken_id -> gerçek profil (0-100). Dönen: cevap listesi (SimpleNamespace)."""
    out = []
    for s, secs, ag in SQ:
        if not secs:
            continue
        k = len(secs)
        if rastgele:
            if (s.cevap_bicimi == "encok_enaz") and k >= 2:
                a, b = r.sample(range(k), 2)
                out.append(SimpleNamespace(soru_id=s.id, secenek_id=secs[a].id, en_az_secenek_id=secs[b].id))
            else:
                out.append(SimpleNamespace(soru_id=s.id, secenek_id=secs[r.randrange(k)].id, en_az_secenek_id=None))
            continue
        t = s.soru_tipi
        if t == "likert":
            hedef = L.get(s.degisken_id, 50.0)
            if s.ters_kodlanmis_mi:
                hedef = 100 - hedef
            i = int(round(min(100, max(0, hedef + r.gauss(0, sr))) / 100 * (k - 1)))
            out.append(SimpleNamespace(soru_id=s.id, secenek_id=secs[i].id, en_az_secenek_id=None))
        elif t == "kutup":
            d = L.get(s.degisken_id, 50.0) - L.get(s.b_ucu_degisken_id, 50.0) + r.gauss(0, sr * 1.2)
            i = 0 if d > 12 else 1 if d > 0 else 2 if d > -12 else 3
            out.append(SimpleNamespace(soru_id=s.id, secenek_id=secs[min(i, k - 1)].id, en_az_secenek_id=None))
        elif t == "sjt":
            u = [sum(w * (L.get(v, 50.0) - 50.0) for v, w in a) / 15.0 for a in ag]
            if s.cevap_bicimi == "encok_enaz" and k >= 2:
                g1 = [x / tau + gumbel(r) for x in u]
                m = max(range(k), key=lambda i: g1[i])
                g2 = [(-x) / tau + gumbel(r) for x in u]
                n = max((i for i in range(k) if i != m), key=lambda i: g2[i])
                out.append(SimpleNamespace(soru_id=s.id, secenek_id=secs[m].id, en_az_secenek_id=secs[n].id))
            else:
                g1 = [x / tau + gumbel(r) for x in u]
                m = max(range(k), key=lambda i: g1[i])
                out.append(SimpleNamespace(soru_id=s.id, secenek_id=secs[m].id, en_az_secenek_id=None))
        # kontrol: puana girmez, cevap üretilmez
    return out


def k1k4_uyum(cevaplar):
    dp = cevaplari_puanla(None, sdict, cevaplar, onb)
    vek = np.array([max(0.0, min(100.0, round(sum(dp[d]) / len(dp[d]), 2))) if d in dp else 50.0 for d in did])
    ol = sm._katman_ici_olcekle(vek[None, :], G)[0]
    X = np.maximum(0.0, 100.0 - np.abs(ol[None, :] - BO))
    norm, ranks = [], []
    for f in sm.YONTEMLER.values():
        z = sm._min_max_0_100(f(X, W))
        norm.append(z)
        ranks.append((-z).argsort().argsort() + 1)
    ort = np.round(np.mean(norm, axis=0), 2)
    return ort, sm._kendall_w(np.array(ranks))


def k5_uygula(r, ort, bstar, sr, tau, rastgele, tohum):
    toplam = {B[i]: float(ort[i]) for i in range(nB)}
    sat = sorted(toplam.items(), key=lambda x: (-x[1], x[0]))
    ust = [x for x in sat if x[1] >= ds.KUME_ESIK][:ds.KUME_EN_FAZLA]
    kume = sat[:ds.KUME_EN_AZ] if len(ust) < ds.KUME_EN_AZ else ust
    bag = {b: baglar_hepsi.get(b, {}) for b, _ in kume}
    plan = ds.soru_plani(kume, bag, cumleler, kokler, tohum=tohum)
    if not plan:
        return toplam, kume, 0
    # iş türü tercihi: b*'nin bağları
    bb = baglar_hepsi.get(bstar, {})
    mx = max(bb.values()) if bb else 1.0
    pref = {}
    # K5 soruları sistemde nasıl kuruluyorsa öyle: sjt şıkları ağırlık 1 ile tek iş türüne, kutup iki uca
    soru_d, cev = {}, []
    sid = -1
    secenekler = {}
    soru_secenekleri = {}
    agirlik = {}
    sec_id = -1
    for p in plan:
        for e, _ in p["secenekler"]:
            if e not in pref:
                pref[e] = 50.0 + (35.0 * bb[e] / mx if e in bb else 0.0) + r.gauss(0, 8)
        if p["tip"] == "kutup":
            (ea, _), (eb, _) = p["secenekler"]
            s = SimpleNamespace(id=sid, soru_tipi="kutup", degisken_id=ea, b_ucu_degisken_id=eb, cevap_bicimi="tek", ters_kodlanmis_mi=False)
            ids = []
            for i in range(1, 5):
                o = SimpleNamespace(id=sec_id, soru_id=sid, secenek_sirasi=i)
                secenekler[sec_id] = o; soru_secenekleri.setdefault(sid, []).append(o); ids.append(sec_id); sec_id -= 1
            if rastgele:
                i = r.randrange(4)
            else:
                d = pref[ea] - pref[eb] + r.gauss(0, sr * 1.2)
                i = 0 if d > 12 else 1 if d > 0 else 2 if d > -12 else 3
            cev.append(SimpleNamespace(soru_id=sid, secenek_id=ids[i], en_az_secenek_id=None))
        else:
            s = SimpleNamespace(id=sid, soru_tipi="sjt", degisken_id=None, b_ucu_degisken_id=None,
                                cevap_bicimi="encok_enaz" if p["tip"] == "encok" else "tek", ters_kodlanmis_mi=False)
            ids, u = [], []
            for i, (e, _) in enumerate(p["secenekler"], start=1):
                o = SimpleNamespace(id=sec_id, soru_id=sid, secenek_sirasi=i)
                secenekler[sec_id] = o; soru_secenekleri.setdefault(sid, []).append(o)
                agirlik[sec_id] = [SimpleNamespace(degisken_id=e, agirlik=1)]
                ids.append(sec_id); u.append((pref[e] - 50.0) / 15.0); sec_id -= 1
            k = len(ids)
            if rastgele:
                if s.cevap_bicimi == "encok_enaz":
                    a, b = r.sample(range(k), 2)
                else:
                    a, b = r.randrange(k), None
            else:
                g1 = [x / tau + gumbel(r) for x in u]
                a = max(range(k), key=lambda i: g1[i])
                b = None
                if s.cevap_bicimi == "encok_enaz":
                    g2 = [(-x) / tau + gumbel(r) for x in u]
                    b = max((i for i in range(k) if i != a), key=lambda i: g2[i])
            cev.append(SimpleNamespace(soru_id=sid, secenek_id=ids[a], en_az_secenek_id=ids[b] if b is not None else None))
        soru_d[sid] = s
        sid -= 1
    k5onb = {"secenek": secenekler, "soru_secenekleri": soru_secenekleri, "agirlik": agirlik}
    dp = cevaplari_puanla(None, soru_d, cev, k5onb)
    puan = {e: round(sum(v) / len(v), 2) for e, v in dp.items()}
    k5 = ds.bolum_k5_puanlari([b for b, _ in kume], bag, puan)
    return sm.k5_nihai(toplam, k5), kume, len(plan)


def sirala(skor):
    # _satirlari_sirala ile aynı anahtar
    var, ms = V["agirlikli_varyans"], V["etkin_meslek_sayisi"]
    return sorted(skor, key=lambda b: (-skor[b], var.get(b, 0.0), -ms.get(b, 0), adlar.get(b, "")))


def ogrenci(r, bstar, sp, sr, tau, rastgele=False, profil=None):
    if profil is None:
        if rastgele:
            profil = {d: 50.0 for d in did}
        else:
            i = bix[bstar]
            profil = {d: float(min(100, max(0, BO[i, j] + r.gauss(0, sp)))) for j, d in enumerate(did)}
    cv = cevapla(r, profil, sr, tau, rastgele)
    ort, kw = k1k4_uyum(cv)
    s14 = {B[i]: float(ort[i]) for i in range(nB)}
    nihai, kume, nk5 = k5_uygula(r, ort, bstar, sr, tau, rastgele, tohum=r.randrange(10**9))
    return profil, sirala(s14), sirala(nihai), kw, len(kume), nk5


KOSULLAR = {
    "dusuk": dict(sp=6, sr=15, tau=0.7),
    "orta": dict(sp=10, sr=20, tau=1.0),
    "yuksek": dict(sp=15, sr=28, tau=1.5),
}


def calistir(ad, n, kosul, rastgele=False, tekrar=0, tohum=1):
    r = random.Random(tohum)
    p = KOSULLAR[kosul]
    sira = []
    while len(sira) < n:
        x = list(B); r.shuffle(x); sira += x
    sira = sira[:n]
    st = defaultdict(list)
    bolum_hit10 = defaultdict(list)
    ilk1 = Counter(); ilk10 = Counter()
    ayni_alan = []
    t0 = time.time()
    for k, bstar in enumerate(sira):
        prof, l14, lnh, kw, kn, nk5 = ogrenci(r, bstar, **p, rastgele=rastgele)
        st["kendall_w"].append(kw); st["kume"].append(kn); st["k5_soru"].append(nk5)
        ilk1[lnh[0]] += 1
        for b in lnh[:10]:
            ilk10[b] += 1
        if not rastgele:
            r14 = l14.index(bstar) + 1; rn = lnh.index(bstar) + 1
            st["sira14"].append(r14); st["sira"].append(rn)
            bolum_hit10[bstar].append(rn <= 10)
            if rn > 1:
                ayni_alan.append(lnh[0] in KOMSU10[bstar])
            if k < tekrar:
                _, l14b, lnhb, _, _, _ = ogrenci(r, bstar, **p, profil=prof)
                st["tekrar_ilk1_ayni"].append(lnh[0] == lnhb[0])
                st["tekrar_ilk5_ortak"].append(len(set(lnh[:5]) & set(lnhb[:5])))
                st["tekrar_ilk10_ortak"].append(len(set(lnh[:10]) & set(lnhb[:10])))
                st["tekrar_ilk1_ilk5te"].append(lnh[0] in lnhb[:5])
        if (k + 1) % 2000 == 0:
            print(f"{ad}: {k + 1}/{n} · {time.time() - t0:.0f} sn", flush=True)
    a = lambda x: np.array(x, dtype=float)
    sonuc = {"ad": ad, "n": n, "kosul": kosul, "rastgele": rastgele, "sure_sn": round(time.time() - t0),
             "ms_ogrenci": round((time.time() - t0) / n * 1000, 1),
             "kendall_w_ort": round(float(a(st["kendall_w"]).mean()), 3),
             "kendall_w_p05": round(float(np.percentile(st["kendall_w"], 5)), 3),
             "kume_ort": round(float(a(st["kume"]).mean()), 1), "k5_soru_ort": round(float(a(st["k5_soru"]).mean()), 1),
             "ilk1_farkli_bolum": len(ilk1), "ilk10_farkli_bolum": len(ilk10),
             "ilk1_en_sik_pay": round(max(ilk1.values()) / n * 100, 2),
             "ilk1_en_sik": [(adlar[b], round(c / n * 100, 2)) for b, c in ilk1.most_common(5)],
             "ilk10_en_sik": [(adlar[b], round(c / n * 100, 1)) for b, c in ilk10.most_common(5)],
             "ilk10_hic_cikmayan": nB - len(ilk10)}
    if not rastgele:
        s, s14 = a(st["sira"]), a(st["sira14"])
        for etiket, x in (("k1k4", s14), ("nihai", s)):
            sonuc[etiket] = {f"ilk{t}": round(float((x <= t).mean() * 100), 1) for t in (1, 3, 5, 10, 20)}
            sonuc[etiket]["medyan_sira"] = float(np.median(x))
            sonuc[etiket]["p90_sira"] = float(np.percentile(x, 90))
        sonuc["yanlis_ilk1_profil_komsusu"] = round(float(np.mean(ayni_alan) * 100), 1) if ayni_alan else None
        h = {b: float(np.mean(v)) for b, v in bolum_hit10.items()}
        hv = np.array(list(h.values()))
        sonuc["bolum_ilk10_isabet"] = {"bolum_sayisi": len(h), "ortanca": round(float(np.median(hv) * 100), 1),
                                       "en_az_%50": int((hv >= 0.5).sum()), "en_az_%80": int((hv >= 0.8).sum()),
                                       "%20_alti": int((hv < 0.2).sum()),
                                       "en_zor_10": [(adlar[b], round(v * 100)) for b, v in sorted(h.items(), key=lambda x: x[1])[:10]]}
        if tekrar:
            sonuc["tekrar"] = {"n": len(st["tekrar_ilk1_ayni"]),
                               "ilk1_ayni_%": round(float(np.mean(st["tekrar_ilk1_ayni"]) * 100), 1),
                               "ilk1_digerinin_ilk5inde_%": round(float(np.mean(st["tekrar_ilk1_ilk5te"]) * 100), 1),
                               "ilk5_ortak_ort": round(float(np.mean(st["tekrar_ilk5_ortak"])), 2),
                               "ilk10_ortak_ort": round(float(np.mean(st["tekrar_ilk10_ortak"])), 2)}
    print(json.dumps(sonuc, ensure_ascii=False), flush=True)
    return sonuc


if __name__ == "__main__":
    plan = sys.argv[1] if len(sys.argv) > 1 else "tam"
    cikti = sys.argv[2] if len(sys.argv) > 2 else "puan_sim_sonuc.json"
    if plan == "deneme":
        isler = [("orta", 300, "orta", False, 100, 5)]
    else:
        isler = [("ana_orta", 50000, "orta", False, 5000, 1),
                 ("dusuk_gurultu", 10000, "dusuk", False, 0, 2),
                 ("yuksek_gurultu", 10000, "yuksek", False, 0, 3),
                 ("rastgele_cevap", 10000, "orta", True, 0, 4)]
    hepsi = []
    for ad, n, k, rs, tk, th in isler:
        hepsi.append(calistir(ad, n, k, rs, tk, th))
        json.dump(hepsi, open(cikti, "w"), ensure_ascii=False, indent=1)
