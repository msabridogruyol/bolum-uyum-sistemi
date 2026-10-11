# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı modülü — veri katmanı yardımcıları (öğrenci uçları ve süper admin yükleme ekranı ortak kullanır).

- Türkçe metin normalize / program adı → bölüm eşleştirme (YÖK Atlas eşleştirme anahtarı yeniden kullanılır)
- Kazanç grubu metni normalize ('Çok yüksek' → 'cok_yuksek')
- Sayı ayrıştırma ('%85,3', '1.234,5', 0.853 …)
- Güncel asgari ücret, meslek → ISCO, kazanç tahmini (asgari ücret katı × güncel asgari ücret)
- Bölüm için iş hayatı verisinin derlenmesi (GET /ogrenci/is-hayati/bolum/{id} yanıtı)

Tahmin olan her değer yanıtta 'tahmin': True ile işaretlenir. Hiçbir sayı burada uydurulmaz: veri yoksa None döner
ve 'eksik' listesine yazılır.
"""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.yokatlas_servisi import _anahtar, _kelime_kumesi, _normalize

_JSON = Path(__file__).resolve().parents[1] / "data" / "meslek_isco.json"

KAZANC_GRUPLARI = {
    "cok_yuksek": "Çok yüksek", "yuksek": "Yüksek", "orta": "Orta", "dusuk": "Düşük", "cok_dusuk": "Çok düşük",
}
DUZEYLER = {"lisans": "Lisans", "onlisans": "Önlisans"}
# Sık kullanılan yaşam gideri kalemleri (yönetim ekranında öneri; serbest kod da girilebilir)
GIDER_KALEMLERI = {
    "kira_1_1": "Kira (1+1)", "kira_2_1": "Kira (2+1)", "aidat": "Aidat", "ulasim": "Toplu taşıma (aylık)",
    "mutfak": "Mutfak / gıda", "fatura": "Faturalar (elektrik, su, doğalgaz)", "iletisim": "Telefon ve internet",
    "giyim": "Giyim", "saglik": "Sağlık ve kişisel bakım", "sosyal": "Sosyal yaşam",
}


def tr_kucuk(m: str) -> str:
    """Türkçe küçük harf ('İ' → 'i', 'I' → 'ı'); meslek adı anahtarı."""
    return " ".join((m or "").replace("I", "ı").replace("İ", "i").lower().split())


def tr_baslik(ad: str) -> str:
    """'MADEN MÜHENDİSLİĞİ' → 'Maden Mühendisliği'."""
    if not ad or not ad.isupper():
        return ad
    return " ".join(tr_kucuk(w) if tr_kucuk(w) in ("ve", "ile") else w[:1] + tr_kucuk(w[1:]) for w in ad.split())


@lru_cache(maxsize=1)
def isco_sozlugu() -> dict:
    try:
        v = json.loads(_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {"ana": {}, "alt": {}, "eslesme": {}}
    return {"ana": v.get("isco08_ana_gruplar") or {}, "alt": v.get("isco08_alt_ana_gruplar") or {}, "eslesme": v.get("eslesme") or {}}


def isco_adi(kod: str | None) -> str | None:
    if not kod:
        return None
    s = isco_sozlugu()
    return (s["alt"] if len(kod) == 2 else s["ana"]).get(kod)


# ---------------------------------------------------------------- ayrıştırma

def sayi(v) -> float | None:
    """'%85,3' → 85.3 · '1.234,50' → 1234.5 · '12 345' → 12345 · 0.85 → 0.85 · '-'/'' → None."""
    if v is None:
        return None
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).strip().replace("%", "").replace("TL", "").replace("₺", "").replace(" ", "").replace(" ", "")
    if not t or t in ("-", "—", "..", "...", "x", "X"):
        return None
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") else t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    elif t.count(".") > 1 or re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return None


def kazanc_grubu_coz(v) -> str | None:
    """'Çok yüksek' / 'COK YUKSEK' / 'çok_yüksek' → 'cok_yuksek'. Tanınmayan metin → None (uydurma yok)."""
    if v is None:
        return None
    t = " ".join(re.sub(r"[^a-z ]", " ", _normalize(str(v)).replace("_", " ")).split())
    if not t:
        return None
    tablo = {"cok yuksek": "cok_yuksek", "yuksek": "yuksek", "orta": "orta", "dusuk": "dusuk", "cok dusuk": "cok_dusuk",
             "en yuksek": "cok_yuksek", "en dusuk": "cok_dusuk"}
    return tablo.get(t)


def duzey_coz(v) -> str | None:
    t = _normalize(str(v or "")).replace(" ", "").replace("-", "")
    if not t:
        return None
    if "onlisans" in t:
        return "onlisans"
    if "lisans" in t and "yuksek" not in t:
        return "lisans"
    return None


# Program adlarından atılacak ekler (parantez içi zaten atılır): burs/indirim, dil, öğretim türü vb.
_PROGRAM_GURULTU = re.compile(r"\b(programi|bolumu|ikinci ogretim|io|uzaktan ogretim|acikogretim|ingilizce|almanca|fransizca|arapca|burslu|ucretli|indirimli)\b")


def program_anahtari(ad: str) -> str:
    t = _anahtar(ad)
    return " ".join(_PROGRAM_GURULTU.sub(" ", t).split())


def _benzerlik(a: str, b: str) -> float:
    ka, kb = frozenset(a.split()) - {"ve"}, frozenset(b.split()) - {"ve"}
    oran = SequenceMatcher(None, a, b).ratio()
    ortak = len(ka & kb) / max(1, len(ka | kb))
    icerme = 0.6 if ka and kb and (ka <= kb or kb <= ka) else 0.0
    return max(oran, ortak, icerme)


def bolum_adaylari(db: Session) -> list[dict]:
    """Eşleştirme için bölüm adları: bölüm adı + elle girilmiş YÖK Atlas program grupları (detay.yokatlas_gruplari)."""
    out = []
    for r in db.execute(text("SELECT id, ad, detay FROM bolumler WHERE durum = 'yayinda' ORDER BY ad")).all():
        d = r.detay if isinstance(r.detay, dict) else json.loads(r.detay or "{}")
        adlar = [r.ad] + [x for x in (d.get("yokatlas_gruplari") or []) if isinstance(x, str)]
        out.append({"id": r.id, "ad": tr_baslik(r.ad), "anahtarlar": list({program_anahtari(a) for a in adlar if a})})
    return out


def program_eslestir(program_adi: str, adaylar: list[dict], n: int = 4) -> dict:
    """{'bolum_id', 'bolum_ad', 'skor', 'durum': 'otomatik'|'oneri'|'yok', 'adaylar': [...]}.
    otomatik: anahtar birebir aynı (Türkçe-normalize, parantez içi ve '(İngilizce)' vb. atılmış) ya da aynı kelime kümesi.
    oneri: bulanık skor ≥ 0.85 (ön seçili gelir, yönetici onaylar). Altı: yalnızca aday listesi."""
    a = program_anahtari(program_adi)
    if not a:
        return {"bolum_id": None, "bolum_ad": None, "skor": 0, "durum": "yok", "adaylar": []}
    ka = frozenset(a.split())
    puanli = []
    for b in adaylar:
        en = 0.0
        for k in b["anahtarlar"]:
            if k == a or (ka and frozenset(k.split()) == ka):
                en = 1.0
                break
            en = max(en, _benzerlik(a, k))
        puanli.append((en, b))
    puanli.sort(key=lambda x: -x[0])
    ilk = puanli[0] if puanli else (0, None)
    adaylar_cikti = [{"id": b["id"], "ad": b["ad"], "skor": round(p * 100)} for p, b in puanli[:n] if p >= 0.5]
    if ilk[1] is not None and ilk[0] >= 0.999:
        return {"bolum_id": ilk[1]["id"], "bolum_ad": ilk[1]["ad"], "skor": 100, "durum": "otomatik", "adaylar": adaylar_cikti}
    if ilk[1] is not None and ilk[0] >= 0.85:
        return {"bolum_id": ilk[1]["id"], "bolum_ad": ilk[1]["ad"], "skor": round(ilk[0] * 100), "durum": "oneri", "adaylar": adaylar_cikti}
    return {"bolum_id": None, "bolum_ad": None, "skor": round(ilk[0] * 100), "durum": "yok", "adaylar": adaylar_cikti}


# ---------------------------------------------------------------- veri okuma

def _f(v):
    return None if v is None else float(v)


def guncel_asgari(db: Session) -> dict | None:
    r = db.execute(text("""SELECT donem, brut, net, kaynak, yururluk_tarihi FROM asgari_ucret
                            WHERE yururluk_tarihi <= CURRENT_DATE ORDER BY yururluk_tarihi DESC LIMIT 1""")).mappings().first()
    if r is None:
        r = db.execute(text("SELECT donem, brut, net, kaynak, yururluk_tarihi FROM asgari_ucret ORDER BY yururluk_tarihi LIMIT 1")).mappings().first()
    if r is None:
        return None
    return {"donem": r["donem"], "brut": _f(r["brut"]), "net": _f(r["net"]), "kaynak": r["kaynak"],
            "yururluk_tarihi": r["yururluk_tarihi"].isoformat() if r["yururluk_tarihi"] else None}


def meslek_isco_haritasi(db: Session, adlar: list[str]) -> dict:
    anahtar = list({tr_kucuk(a) for a in adlar if a})
    if not anahtar:
        return {}
    rows = db.execute(text("SELECT meslek_adi, isco_kodu, guven FROM meslek_isco WHERE meslek_adi = ANY(:a)"), {"a": anahtar}).all()
    return {r.meslek_adi: (r.isco_kodu, r.guven) for r in rows}


def kazanc_tablosu(db: Session) -> dict:
    """{isco_kodu: satır} — her kod için en yeni veri yılı."""
    rows = db.execute(text("""SELECT DISTINCT ON (isco_kodu) isco_kodu, ad, brut_aylik_ortalama_tl, veri_yili, asgari_brut_o_yil, kaynak
                                FROM kazanc_meslek_gruplari ORDER BY isco_kodu, veri_yili DESC""")).mappings().all()
    return {r["isco_kodu"]: dict(r) for r in rows}


def istihdam_bolum(db: Session, bolum_id: int) -> dict | None:
    rows = db.execute(text("""SELECT program_adi_kaynak, duzey, istihdam_orani, is_bulma_suresi_ay, alan_uyum_orani, kazanc_grubu,
                                     kazanc_tl, veri_yili, kaynak
                                FROM istihdam_gostergeleri WHERE bolum_id = :b
                               ORDER BY veri_yili DESC, (duzey = 'lisans') DESC NULLS LAST, id""" ), {"b": bolum_id}).mappings().all()
    if not rows:
        return None
    yil = rows[0]["veri_yili"]
    programlar = [{
        "program_adi_kaynak": r["program_adi_kaynak"], "duzey": r["duzey"], "duzey_ad": DUZEYLER.get(r["duzey"]),
        "istihdam_orani": _f(r["istihdam_orani"]), "is_bulma_suresi_ay": _f(r["is_bulma_suresi_ay"]),
        "alan_uyum_orani": _f(r["alan_uyum_orani"]), "kazanc_grubu": r["kazanc_grubu"],
        "kazanc_grubu_ad": KAZANC_GRUPLARI.get(r["kazanc_grubu"]), "kazanc_tl": _f(r["kazanc_tl"]), "kaynak": r["kaynak"],
    } for r in rows if r["veri_yili"] == yil]
    onceki = sorted({r["veri_yili"] for r in rows if r["veri_yili"] != yil}, reverse=True)
    return {**programlar[0], "veri_yili": yil, "programlar": programlar, "onceki_yillar": onceki, "tahmin": False}


def kazanc_meslekleri(db: Session, meslekler: list[dict], asgari: dict | None) -> list[dict]:
    """Bölümün meslekleri için kazanç: meslek → ISCO (2 hane; yoksa 1 haneli ana gruba düşer) → TÜİK ortalama brüt.
    Güncel tahmin = (veri yılı brüt / o yılın asgari brütü) × güncel asgari brüt; net ≈ × (güncel net / güncel brüt)."""
    adlar = [m.get("ad") for m in meslekler if m.get("ad")]
    harita = meslek_isco_haritasi(db, adlar)
    tablo = kazanc_tablosu(db)
    out = []
    for ad in adlar:
        kod, guven = harita.get(tr_kucuk(ad), (None, None))
        satir, duzey = None, None
        if kod:
            if kod in tablo:
                satir, duzey = tablo[kod], "alt_ana_grup"
            elif kod[:1] in tablo:
                satir, duzey = tablo[kod[:1]], "ana_grup"
        o = {"meslek": ad, "isco_kodu": kod, "isco_guven": guven, "grup_adi": isco_adi(kod), "grup_duzeyi": duzey,
             "brut_veri_yili_tl": None, "veri_yili": None, "asgari_kat": None, "guncel_tahmin_brut_tl": None,
             "guncel_tahmin_net_tl": None, "kaynak": None, "tahmin": True}
        if satir:
            brut = _f(satir["brut_aylik_ortalama_tl"])
            kat = brut / _f(satir["asgari_brut_o_yil"]) if satir["asgari_brut_o_yil"] else None
            o.update({"brut_veri_yili_tl": brut, "veri_yili": satir["veri_yili"], "kaynak": satir["kaynak"],
                      "veri_grup_kodu": satir["isco_kodu"], "veri_grup_adi": satir["ad"],
                      "asgari_kat": round(kat, 2) if kat else None})
            if kat and asgari:
                tb = kat * asgari["brut"]
                o["guncel_tahmin_brut_tl"] = round(tb, -1)
                o["guncel_tahmin_net_tl"] = round(tb * asgari["net"] / asgari["brut"], -1)
                o["guncel_donem"] = asgari["donem"]
        out.append(o)
    return out


def kamu_eslesen(db: Session, bolum_ad: str, meslek_adlari: list[str]) -> list[dict]:
    hedef = [_normalize(bolum_ad)] + [_normalize(m) for m in meslek_adlari]
    out = []
    for r in db.execute(text("SELECT * FROM kamu_maaslari ORDER BY kadro_adi")).mappings().all():
        kel = r["anahtar_kelimeler"] if isinstance(r["anahtar_kelimeler"], list) else json.loads(r["anahtar_kelimeler"] or "[]")
        kel = [_normalize(k) for k in kel if isinstance(k, str) and k.strip()]
        if any(k in h for k in kel for h in hedef):
            out.append({"id": r["id"], "kadro_adi": r["kadro_adi"], "net_min": _f(r["net_min"]), "net_max": _f(r["net_max"]),
                        "donem": r["donem"], "kaynak": r["kaynak"], "aciklama": r["aciklama"], "tahmin": False})
    return out


def veri_kaynaklari(db: Session) -> list[dict]:
    """'Veriler hakkında' notu için: hangi veri, hangi kaynak, hangi yıl."""
    out = []
    for r in db.execute(text("SELECT kaynak, veri_yili, COUNT(*) n FROM istihdam_gostergeleri GROUP BY 1, 2 ORDER BY 2 DESC")).all():
        out.append({"veri": "istihdam", "ad": "Mezun istihdamı, iş bulma süresi, alan uyumu, kazanç grubu", "kaynak": r.kaynak, "yil": r.veri_yili, "kayit": r.n})
    for r in db.execute(text("SELECT kaynak, veri_yili, COUNT(*) n FROM kazanc_meslek_gruplari GROUP BY 1, 2 ORDER BY 2 DESC")).all():
        out.append({"veri": "kazanc", "ad": "Meslek gruplarına göre ortalama brüt kazanç", "kaynak": r.kaynak, "yil": r.veri_yili, "kayit": r.n})
    for r in db.execute(text("SELECT kaynak, donem, COUNT(*) n FROM kamu_maaslari GROUP BY 1, 2 ORDER BY 2 DESC")).all():
        out.append({"veri": "kamu", "ad": "Kamu kadro maaşları", "kaynak": r.kaynak, "yil": r.donem, "kayit": r.n})
    a = guncel_asgari(db)
    if a:
        out.append({"veri": "asgari", "ad": "Asgari ücret", "kaynak": a["kaynak"], "yil": a["donem"], "kayit": 1})
    for r in db.execute(text("SELECT kaynak, MAX(tarih) AS son_tarih, COUNT(*) n FROM yasam_giderleri GROUP BY 1 ORDER BY 2 DESC")).all():
        out.append({"veri": "giderler", "ad": "Yaşam giderleri", "kaynak": r.kaynak, "yil": r.son_tarih.isoformat() if r.son_tarih else None, "kayit": r.n})
    return out


def bolum_verisi(db: Session, bolum_id: int) -> dict | None:
    r = db.execute(text("SELECT id, ad, detay FROM bolumler WHERE id = :i AND durum = 'yayinda'"), {"i": bolum_id}).first()
    if r is None:
        return None
    d = r.detay if isinstance(r.detay, dict) else json.loads(r.detay or "{}")
    meslekler = [m for m in (d.get("meslekler") or []) if isinstance(m, dict)]
    asgari = guncel_asgari(db)
    istihdam = istihdam_bolum(db, r.id)
    kazanc = kazanc_meslekleri(db, meslekler, asgari)
    kamu = kamu_eslesen(db, r.ad, [m.get("ad") or "" for m in meslekler])
    eksik = []
    if istihdam is None:
        eksik.append("istihdam")
    if not any(k["brut_veri_yili_tl"] is not None for k in kazanc):
        eksik.append("kazanc")
    if not kamu:
        eksik.append("kamu")
    if asgari is None:
        eksik.append("asgari")
    return {
        "bolum": {"id": r.id, "ad": tr_baslik(r.ad), "ogrenim_suresi": d.get("ogrenim_suresi"), "meslek_sayisi": len(meslekler)},
        "istihdam": istihdam,
        "kazanc": {"meslekler": kazanc,
                   "aciklama": "Meslek grubunun TÜİK ortalama brüt kazancı, veri yılındaki asgari ücrete oranlanıp güncel asgari "
                               "ücretle çarpılarak bugüne taşınır. Bu bir TAHMİNDİR; ilk iş maaşı genellikle ortalamanın altındadır."},
        "kamu": kamu,
        "asgari": asgari,
        "eksik": eksik,
        "veri_kaynaklari": veri_kaynaklari(db),
    }

