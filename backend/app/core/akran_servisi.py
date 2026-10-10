# -*- coding: utf-8 -*-
"""
[2026-10-10] Akran benzerliği, şube dağılımı önerisi ve aday öğrenci şube uyumu.

Profil vektörü: öğrencinin son geçerli turundaki K1–K4 özellik puanları (K5 dal puanları hariç;
onlar yalnızca o dalı seçenlerde var ve kişiliği değil alan yeterliğini ölçer).

Benzerlik: puanlar havuzun (okulun) ortalamasına göre merkezlenip standart sapmaya bölünür, sonra
kosinüs benzerliği alınır. Böylece "herkes 50 civarı" etkisi silinir; iki öğrencinin okul ortalamasından
AYNI YÖNDE ayrışması benzerlik sayılır. Gösterilen yüzde = 50 + 50·cos (0 = tam zıt, 50 = ilişkisiz, 100 = aynı).

Etik sınır: Bu sonuçlar yalnızca rehber öğretmen / okul yetkilisine gösterilir; öğrenciye "şuna benziyorsun"
şeklinde sunulmaz. Şube kararında karar destek amaçlıdır, tek ölçüt değildir.
"""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

MIN_ORTAK = 6           # benzerlik için gereken en az ortak özellik sayısı
GUCLU_ESIK = 62.0       # "güçlü" seviye eşiği (raporlarla aynı)


# ----------------------------------------------------------------------------- veri
def profiller(db: Session, ogrenci_idler: list) -> dict:
    """{ogrenci_id(str): {"puan": {degisken_id: puan}, "tamam": bool, "guven": float|None, "tur_id": int}}
    Öğrenci başına: tamamlanmış en son tur; yoksa puanı olan en son tur."""
    if not ogrenci_idler:
        return {}
    satirlar = db.execute(text("""
        SELECT s.ogrenci_id::text AS oid, s.tur_id, s.degisken_id, s.puan, t.durum, t.guven_skoru, t.tur_no
        FROM ogrenci_degisken_skorlari s
        JOIN degiskenler d ON d.id = s.degisken_id AND d.dal_id IS NULL
        JOIN ogrenci_degerlendirme_turu t ON t.id = s.tur_id
        WHERE s.ogrenci_id::text = ANY(:idler)
    """), {"idler": [str(i) for i in ogrenci_idler]}).mappings().all()
    turlar: dict[str, dict[int, dict]] = defaultdict(dict)
    for r in satirlar:
        t = turlar[r["oid"]].setdefault(r["tur_id"], {"puan": {}, "tamam": r["durum"] == "tamamlandi",
                                                      "guven": float(r["guven_skoru"]) if r["guven_skoru"] is not None else None,
                                                      "tur_no": r["tur_no"], "tur_id": r["tur_id"]})
        t["puan"][r["degisken_id"]] = float(r["puan"])
    sonuc = {}
    for oid, tlar in turlar.items():
        secim = sorted(tlar.values(), key=lambda t: (t["tamam"], t["tur_no"]), reverse=True)[0]
        if len(secim["puan"]) >= MIN_ORTAK:
            sonuc[oid] = secim
    return sonuc


def degisken_adlari(db: Session) -> dict[int, str]:
    try:
        from app.core.koclugu_servisi import turkce_baslik
    except Exception:  # pragma: no cover
        turkce_baslik = lambda x: x  # noqa: E731
    return {r[0]: turkce_baslik(r[1] or "") for r in db.execute(text("SELECT id, ad FROM degiskenler WHERE dal_id IS NULL")).all()}


# ----------------------------------------------------------------------------- matris
class Matris:
    """Havuzdaki profillerden standartlaştırılmış matris (eksik = 0 → ortalamada)."""

    def __init__(self, prof: dict):
        self.idler = list(prof.keys())
        self.degiskenler = sorted({d for p in prof.values() for d in p["puan"]})
        dix = {d: j for j, d in enumerate(self.degiskenler)}
        n, m = len(self.idler), len(self.degiskenler)
        ham = np.full((n, m), np.nan)
        for i, oid in enumerate(self.idler):
            for d, v in prof[oid]["puan"].items():
                ham[i, dix[d]] = v
        self.ham = ham
        self.maske = ~np.isnan(ham)
        with np.errstate(all="ignore"):
            self.ort = np.where(self.maske.any(0), np.nanmean(ham, 0), 50.0)
            sd = np.where(self.maske.sum(0) > 1, np.nanstd(ham, 0), 15.0)
        self.sd = np.maximum(np.nan_to_num(sd, nan=15.0), 6.0)   # çok küçük sapmalar gürültüyü büyütmesin
        self.z = np.where(self.maske, (ham - self.ort) / self.sd, 0.0)
        self.ix = {oid: i for i, oid in enumerate(self.idler)}

    def vektor(self, puan: dict) -> tuple[np.ndarray, np.ndarray]:
        v = np.zeros(len(self.degiskenler))
        mk = np.zeros(len(self.degiskenler), dtype=bool)
        for j, d in enumerate(self.degiskenler):
            if d in puan:
                v[j] = (puan[d] - self.ort[j]) / self.sd[j]
                mk[j] = True
        return v, mk


def _cos(a: np.ndarray, b: np.ndarray, ma: np.ndarray, mb: np.ndarray) -> float | None:
    ortak = ma & mb
    if ortak.sum() < MIN_ORTAK:
        return None
    x, y = a[ortak], b[ortak]
    na, nb = np.linalg.norm(x), np.linalg.norm(y)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(x, y) / (na * nb))


def yuzde(c: float | None) -> int | None:
    return None if c is None else int(round(50 + 50 * c))


def _ortak_ve_fark(pa: dict, pb: dict, adlar: dict, mat: Matris) -> tuple[list[str], list[str]]:
    ortak, fark = [], []
    for j, d in enumerate(mat.degiskenler):
        if d in pa and d in pb:
            if pa[d] >= GUCLU_ESIK and pb[d] >= GUCLU_ESIK:
                ortak.append((pa[d] + pb[d], adlar.get(d, "?")))
            fark.append((abs(pa[d] - pb[d]), adlar.get(d, "?")))
    ortak.sort(reverse=True)
    fark.sort(reverse=True)
    return [a for _, a in ortak[:3]], [a for f, a in fark[:2] if f >= 25]


# ----------------------------------------------------------------------------- benzer akranlar
def benzer_akranlar(db: Session, hedef_id: str, havuz: list, n: int = 5) -> dict:
    """havuz: [(ogrenci_id, ad_soyad, sinif_metni)] — hedef de dahil olabilir."""
    bilgi = {str(i): (ad, sm) for i, ad, sm in havuz}
    bilgi.setdefault(str(hedef_id), ("", ""))
    prof = profiller(db, list(bilgi.keys()))
    if str(hedef_id) not in prof:
        return {"durum": "profil_yok", "akranlar": [], "havuz": len(prof)}
    mat = Matris(prof)
    adlar = degisken_adlari(db)
    hi = mat.ix[str(hedef_id)]
    a, ma = mat.z[hi], mat.maske[hi]
    sonuc = []
    for oid, i in mat.ix.items():
        if oid == str(hedef_id):
            continue
        c = _cos(a, mat.z[i], ma, mat.maske[i])
        if c is None:
            continue
        ortak, fark = _ortak_ve_fark(prof[str(hedef_id)]["puan"], prof[oid]["puan"], adlar, mat)
        sonuc.append({"id": oid, "ad_soyad": bilgi[oid][0], "sinif": bilgi[oid][1], "benzerlik": yuzde(c),
                      "ortak_guclu": ortak, "farkli": fark, "dusuk_guven": _dusuk_guven(prof[oid])})
    sonuc.sort(key=lambda x: -x["benzerlik"])
    return {"durum": "tamam", "akranlar": sonuc[:n], "havuz": len(prof) - 1,
            "dusuk_guven": _dusuk_guven(prof[str(hedef_id)]), "tamamlanmamis": not prof[str(hedef_id)]["tamam"]}


def _dusuk_guven(p: dict) -> bool:
    return p.get("guven") is not None and p["guven"] < 50


# ----------------------------------------------------------------------------- k-ortalamalar
def _kmeans(X: np.ndarray, k: int, tohum: int = 7, tekrar: int = 8, adim: int = 60) -> tuple[np.ndarray, np.ndarray]:
    n = len(X)
    k = max(1, min(k, n))
    en_iyi = None
    rnd = np.random.default_rng(tohum)
    for _ in range(tekrar):
        # k-means++ başlangıcı
        c = [X[rnd.integers(n)]]
        for _ in range(1, k):
            d2 = np.min(((X[:, None, :] - np.array(c)[None]) ** 2).sum(-1), 1)
            p = d2 / d2.sum() if d2.sum() > 0 else np.full(n, 1 / n)
            c.append(X[rnd.choice(n, p=p)])
        C = np.array(c)
        for _ in range(adim):
            et = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(-1), 1)
            yeni = np.array([X[et == j].mean(0) if (et == j).any() else C[j] for j in range(k)])
            if np.allclose(yeni, C):
                break
            C = yeni
        hata = float(((X - C[et]) ** 2).sum())
        if en_iyi is None or hata < en_iyi[0]:
            en_iyi = (hata, et, C)
    return en_iyi[1], en_iyi[2]


def _ozellik_adlari_ust(mat: Matris, satirlar: np.ndarray, adlar: dict, kac: int = 3) -> list[str]:
    """Bir grubun okul ortalamasına göre en belirgin (z ortalaması en yüksek) özellikleri."""
    if len(satirlar) == 0:
        return []
    zm = mat.z[satirlar].mean(0)
    sira = np.argsort(-zm)
    return [adlar.get(mat.degiskenler[j], "?") for j in sira[:kac] if zm[j] > 0.15]


def _ic_benzerlik(mat: Matris, satirlar: list[int]) -> int | None:
    if len(satirlar) < 2:
        return None
    toplam, say = 0.0, 0
    for x in range(len(satirlar)):
        for y in range(x + 1, len(satirlar)):
            c = _cos(mat.z[satirlar[x]], mat.z[satirlar[y]], mat.maske[satirlar[x]], mat.maske[satirlar[y]])
            if c is not None:
                toplam += c
                say += 1
    return yuzde(toplam / say) if say else None


# ----------------------------------------------------------------------------- şube dağılımı
def sube_dagilimi(db: Session, ogrenciler: list[dict], subeler: list[str], mod: str = "dengeli",
                  cinsiyet_dengele: bool = True) -> dict:
    """
    ogrenciler: [{"id","ad_soyad","sube","cinsiyet"}]
    mod = 'dengeli'  → her şubeye farklı profil tiplerinden eşit sayıda öğrenci (şubeler birbirine benzer, içleri çeşitli)
    mod = 'benzer'   → benzer profiller aynı şubede (eşit kapasiteli kümeleme; proje/etüt grupları için)
    Profili olmayanlar en kalabalık olmayan şubelere sırayla eklenir.
    """
    k = len(subeler)
    prof = profiller(db, [o["id"] for o in ogrenciler])
    adlar = degisken_adlari(db)
    profilli = [o for o in ogrenciler if str(o["id"]) in prof]
    profilsiz = [o for o in ogrenciler if str(o["id"]) not in prof]
    atama: dict[str, int] = {}
    tip: dict[str, int] = {}
    mat = Matris({str(o["id"]): prof[str(o["id"])] for o in profilli}) if profilli else None
    kapasite = math.ceil(len(ogrenciler) / k) if k else 0

    if mat is not None and len(profilli) >= k:
        X = mat.z
        if mod == "benzer":
            et, C = _kmeans(X, k)
            # eşit kapasiteli atama: merkeze en net yakın olan önce yerleşir
            d = ((X[:, None, :] - C[None]) ** 2).sum(-1)
            kap = math.ceil(len(profilli) / k)
            dolu = [0] * k
            tercih = np.sort(d, 1)
            netlik = (tercih[:, 1] - tercih[:, 0]) if k > 1 else np.zeros(len(X))
            for i in np.argsort(-netlik):
                for j in np.argsort(d[i]):
                    if dolu[j] < kap:
                        atama[mat.idler[i]] = int(j)
                        tip[mat.idler[i]] = int(j)
                        dolu[j] += 1
                        break
        else:
            tip_say = max(2, min(k * 2, len(profilli) // 3 or 1, 8))
            et, C = _kmeans(X, tip_say)
            # ana eksen: en büyük varyans yönü (tip içinde sıralama için)
            try:
                _, _, vt = np.linalg.svd(X - X.mean(0), full_matrices=False)
                pc1 = X @ vt[0]
            except Exception:
                pc1 = np.zeros(len(X))
            dolu = [0] * k
            kap_p = math.ceil(len(profilli) / k)
            tip_dolu = defaultdict(int)          # (şube, tip) → sayı
            cins = defaultdict(int)              # (şube, cinsiyet) → sayı
            cins_bilgi = {str(o["id"]): (o.get("cinsiyet") or "") for o in profilli}
            for t in sorted(set(et.tolist()), key=lambda t: -(et == t).sum()):
                uyeler = [i for i in range(len(X)) if et[i] == t]
                uyeler.sort(key=lambda i: pc1[i])
                for i in uyeler:
                    oid = mat.idler[i]
                    cn = cins_bilgi.get(oid, "")

                    def puan(j):
                        return (tip_dolu[(j, t)], dolu[j], cins[(j, cn)] if (cinsiyet_dengele and cn) else 0, j)
                    uygun = [j for j in range(k) if dolu[j] < kap_p] or list(range(k))
                    j = min(uygun, key=puan)
                    atama[oid] = j
                    tip[oid] = int(t)
                    dolu[j] += 1
                    tip_dolu[(j, t)] += 1
                    if cn:
                        cins[(j, cn)] += 1
    elif mat is not None:
        for i, oid in enumerate(mat.idler):
            atama[oid] = i % k

    dolu = [0] * k
    for j in atama.values():
        dolu[j] += 1
    for o in profilsiz:
        j = min(range(k), key=lambda j: (dolu[j], j))
        atama[str(o["id"])] = j
        dolu[j] += 1

    # özet
    gruplar = []
    for j, ad in enumerate(subeler):
        uye = [o for o in ogrenciler if atama.get(str(o["id"])) == j]
        satir = [mat.ix[str(o["id"])] for o in uye if mat is not None and str(o["id"]) in mat.ix]
        cins_say = defaultdict(int)
        for o in uye:
            cins_say[o.get("cinsiyet") or "belirtilmemis"] += 1
        gruplar.append({
            "sube": ad, "sayi": len(uye), "profilli": len(satir),
            "belirgin": _ozellik_adlari_ust(mat, np.array(satir, dtype=int), adlar) if satir else [],
            "ic_benzerlik": _ic_benzerlik(mat, satir) if mat is not None else None,
            "cinsiyet": dict(cins_say),
            "ogrenciler": [{"id": str(o["id"]), "ad_soyad": o["ad_soyad"], "eski_sube": o.get("sube"),
                            "profil": str(o["id"]) in prof, "tip": tip.get(str(o["id"]))} for o in sorted(uye, key=lambda x: x["ad_soyad"].lower())],
        })
    # şubeler arası denge: şube merkezlerinin okul ortalamasına uzaklığı (düşük = şubeler birbirine benzer)
    sapma = None
    if mat is not None:
        uz = []
        for g in gruplar:
            satir = [mat.ix[o["id"]] for o in g["ogrenciler"] if o["id"] in mat.ix]
            if satir:
                uz.append(float(np.linalg.norm(mat.z[satir].mean(0))) / math.sqrt(max(1, len(mat.degiskenler))))
        sapma = round(sum(uz) / len(uz), 2) if uz else None
    return {"mod": mod, "subeler": gruplar, "profilsiz": len(profilsiz), "profilli": len(profilli),
            "kapasite": kapasite, "subeler_arasi_fark": sapma}


# ----------------------------------------------------------------------------- aday öğrenci
def aday_uyumu(db: Session, aday_id: str, sinif_ogrencileri: list[dict]) -> dict:
    """sinif_ogrencileri: [{"id","ad_soyad","sube"}] (hedef sınıf düzeyindeki mevcut öğrenciler)."""
    idler = [str(o["id"]) for o in sinif_ogrencileri] + [str(aday_id)]
    prof = profiller(db, idler)
    if str(aday_id) not in prof:
        return {"durum": "profil_yok", "subeler": [], "akranlar": []}
    mat = Matris(prof)
    adlar = degisken_adlari(db)
    a, ma = mat.z[mat.ix[str(aday_id)]], mat.maske[mat.ix[str(aday_id)]]
    sube_uyeler: dict[str, list[int]] = defaultdict(list)
    for o in sinif_ogrencileri:
        if str(o["id"]) in mat.ix and o.get("sube"):
            sube_uyeler[o["sube"]].append(mat.ix[str(o["id"])])
    subeler = []
    for s, uye in sorted(sube_uyeler.items()):
        merkez = mat.z[uye].mean(0)
        mk = mat.maske[uye].any(0)
        c = _cos(a, merkez, ma, mk)
        bireysel = [c2 for c2 in (_cos(a, mat.z[i], ma, mat.maske[i]) for i in uye) if c2 is not None]
        yakin = sum(1 for c2 in bireysel if c2 >= 0.3)
        subeler.append({"sube": s, "uyum": yuzde(c), "profilli": len(uye), "yakin_akran": yakin,
                        "belirgin": _ozellik_adlari_ust(mat, np.array(uye), adlar)})
    subeler.sort(key=lambda x: -(x["uyum"] or 0))
    akran = benzer_akranlar(db, aday_id, [(o["id"], o["ad_soyad"], o.get("etiket") or o.get("sube") or "") for o in sinif_ogrencileri], n=3)
    ap = prof[str(aday_id)]["puan"]
    gucluler = sorted(((v, adlar.get(d, "?")) for d, v in ap.items()), reverse=True)[:4]
    return {"durum": "tamam", "subeler": subeler, "akranlar": akran.get("akranlar", []),
            "gucluler": [{"ad": a2, "puan": round(v)} for v, a2 in gucluler],
            "tamamlanmamis": not prof[str(aday_id)]["tamam"], "dusuk_guven": _dusuk_guven(prof[str(aday_id)])}
