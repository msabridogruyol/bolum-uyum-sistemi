# -*- coding: utf-8 -*-
"""
[2026-11-01] Pipeline çıktılarının admin panelinden yüklenmesi: K5 iş türü bağları ve örnek meslekler.

Önceden bu iki dosya Supabase SQL ekranında elle çalıştırılıyordu. Artık süper admin Pipeline Sonuçları ekranında
dosyayı seçer, önizlemeyi görür ve "Canlıya al" der. SQL dosyası ÇALIŞTIRILMAZ: yalnızca içindeki değer satırları
(pipeline'ın ürettiği biçim) okunur ve parametreli sorgularla yazılır.

Kabul edilen biçimler (C:\\pipeline çıktıları):
  * K5 bağları:      cikti/k5_baglari_veri.sql  ya da  veri/bolum_k5_bag_veri.csv  (bolum;alan;eksen;bag)
  * Örnek meslekler: cikti/ornek_meslekler_veri.sql   ('BÖLÜM', 'isco', 'Meslek adı', benzerlik, model_sayisi, sira)

Canlıya almadan önce mevcut kayıtlar veri_yedekleri tablosuna yazılır; ekrandan önceki sürüme dönülebilir.
"""
from __future__ import annotations

import csv
import io
import json
import re

from sqlalchemy import text
from sqlalchemy.orm import Session

TURLER = {"k5_baglari": "K5 iş türü bağları", "ornek_meslekler": "Örnek meslekler"}
_LITERAL = re.compile(r"\s*(?:'((?:[^']|'')*)'|(-?\d+(?:\.\d+)?)|(NULL))\s*(?:,|$)", re.I)
_SATIR = re.compile(r"^\s*\((.*)\)\s*,?\s*$")
EN_FAZLA_SATIR = 20000


class VeriHatasi(ValueError):
    pass


def _tuple_oku(icerik: str) -> list[str]:
    """'(… , …)' satırını SQL literal listesine çevirir; biçim dışı satır VeriHatasi."""
    m = _SATIR.match(icerik)
    if not m:
        raise VeriHatasi("satır")
    govde, deger, poz = m.group(1), [], 0
    while poz < len(govde):
        mm = _LITERAL.match(govde, poz)
        if not mm or mm.end() == poz:
            raise VeriHatasi("satır")
        s, n, bos = mm.groups()
        deger.append(s.replace("''", "'") if s is not None else (None if bos else n))
        poz = mm.end()
    return deger


def _sql_degerleri(metin: str, alan_sayisi: int) -> list[list]:
    """SQL dosyasındaki VALUES satırları (her biri tek satırda; pipeline biçimi). Diğer satırlar yok sayılır."""
    out = []
    for satir in metin.splitlines():
        s = satir.strip()
        if not s.startswith("("):
            continue
        try:
            d = _tuple_oku(s)
        except VeriHatasi:
            continue
        if len(d) == alan_sayisi:
            out.append(d)
    return out


def _sayi(x, tam=False):
    if x is None or str(x).strip() == "":
        return None
    v = float(str(x).replace(",", "."))
    return int(round(v)) if tam else v


def ayristir(tur: str, metin: str) -> list[dict]:
    """Dosya metni → satır sözlükleri. Biçim tanınmazsa VeriHatasi."""
    metin = (metin or "").lstrip("\ufeff")
    if not metin.strip():
        raise VeriHatasi("Dosya boş.")
    satirlar: list[dict] = []
    if tur == "k5_baglari":
        ilk = metin.splitlines()[0].lower()
        if "bolum" in ilk and "eksen" in ilk:                         # bolum_k5_bag_veri.csv
            for r in csv.DictReader(io.StringIO(metin), delimiter=";" if ilk.count(";") >= ilk.count(",") else ","):
                if (r.get("bolum") or "").strip() and (r.get("eksen") or "").strip():
                    satirlar.append({"bolum": r["bolum"].strip(), "kod": r["eksen"].strip(), "bag": _sayi(r.get("bag"))})
        else:                                                         # k5_baglari_veri.sql
            for b, k, g in _sql_degerleri(metin, 3):
                satirlar.append({"bolum": b.strip(), "kod": k.strip(), "bag": _sayi(g)})
        if not satirlar:
            raise VeriHatasi("K5 bağı satırı bulunamadı. C:\\pipeline\\cikti\\k5_baglari_veri.sql dosyasını seçin.")
        for s in satirlar:
            if s["bag"] is None or not (0 < s["bag"] <= 1):
                raise VeriHatasi(f"{s['bolum']} · {s['kod']}: bağ değeri 0 ile 1 arasında olmalı.")
    elif tur == "ornek_meslekler":
        for b, isco, ad, benz, ms, sira in _sql_degerleri(metin, 6):
            satirlar.append({"bolum": b.strip(), "isco": (isco or "").strip() or None, "ad": (ad or "").strip(),
                             "benzerlik": _sayi(benz), "model_sayisi": _sayi(ms, True), "sira": _sayi(sira, True)})
        if not satirlar:
            raise VeriHatasi("Örnek meslek satırı bulunamadı. C:\\pipeline\\cikti\\ornek_meslekler_veri.sql dosyasını seçin.")
        if any(not s["ad"] for s in satirlar):
            raise VeriHatasi("Meslek adı boş olan satır var.")
    else:
        raise VeriHatasi("Bilinmeyen veri türü.")
    if len(satirlar) > EN_FAZLA_SATIR:
        raise VeriHatasi(f"Dosyada {len(satirlar)} satır var; en fazla {EN_FAZLA_SATIR}.")
    return satirlar


def _bolumler(db: Session) -> dict[str, int]:
    return {r.ad: r.id for r in db.execute(text("SELECT id, ad FROM bolumler WHERE durum = 'yayinda'"))}


def _k5_kodlari(db: Session) -> dict[str, int]:
    return {r.kod: r.id for r in db.execute(text("SELECT id, kod FROM degiskenler WHERE kod ~ '^U[0-9]{2}_'"))}


def mevcut(db: Session, tur: str) -> list[dict]:
    if tur == "k5_baglari":
        q = ("SELECT b.ad bolum, d.kod kod, kb.bag::float bag FROM bolum_k5_baglari kb JOIN bolumler b ON b.id = kb.bolum_id "
             "JOIN degiskenler d ON d.id = kb.degisken_id WHERE d.kod ~ '^U[0-9]{2}_' ORDER BY b.ad, kb.bag DESC")
    else:
        q = ("SELECT b.ad bolum, om.meslek_isco_kodu isco, om.meslek_adi ad, om.benzerlik_skoru::float benzerlik, "
             "om.model_sayisi, om.sira FROM bolum_ornek_meslekler om JOIN bolumler b ON b.id = om.bolum_id ORDER BY b.ad, om.sira")
    return [dict(r) for r in db.execute(text(q)).mappings().all()]


def onizle(db: Session, tur: str, satirlar: list[dict]) -> dict:
    bol = _bolumler(db)
    kodlar = _k5_kodlari(db) if tur == "k5_baglari" else {}
    eslesmeyen_bolum = sorted({s["bolum"] for s in satirlar if s["bolum"] not in bol})
    eslesmeyen_kod = sorted({s["kod"] for s in satirlar if tur == "k5_baglari" and s["kod"] not in kodlar})
    gecerli = [s for s in satirlar if s["bolum"] in bol and (tur != "k5_baglari" or s["kod"] in kodlar)]
    eski = mevcut(db, tur)
    anahtar = (lambda s: (s["bolum"], s["kod"])) if tur == "k5_baglari" else (lambda s: (s["bolum"], s["ad"]))
    eski_b = {}
    for s in eski:
        eski_b.setdefault(s["bolum"], set()).add(anahtar(s))
    yeni_b = {}
    for s in gecerli:
        yeni_b.setdefault(s["bolum"], set()).add(anahtar(s))
    degisen = sorted(b for b in set(eski_b) | set(yeni_b) if eski_b.get(b) != yeni_b.get(b))
    kapsanmayan = sorted(set(bol) - set(yeni_b))
    ornek = []
    for b in degisen[:6]:
        if tur == "k5_baglari":
            ad = lambda xs: ", ".join(f"{k}" for _, k in sorted(xs)) or "—"
        else:
            ad = lambda xs: ", ".join(m for _, m in sorted(xs))[:160] or "—"
        ornek.append({"bolum": b, "eski": ad(eski_b.get(b, set())), "yeni": ad(yeni_b.get(b, set()))})
    return {"tur": tur, "tur_ad": TURLER[tur], "satir": len(satirlar), "gecerli_satir": len(gecerli),
            "bolum_sayisi": len(yeni_b), "yayindaki_bolum": len(bol), "eslesmeyen_bolumler": eslesmeyen_bolum,
            "eslesmeyen_kodlar": eslesmeyen_kod, "kapsanmayan_bolumler": kapsanmayan,
            "mevcut_satir": len(eski), "mevcut_bolum": len(eski_b), "degisen_bolum": len(degisen), "ornek": ornek,
            "canliya_alinabilir": bool(gecerli) and not eslesmeyen_bolum and not eslesmeyen_kod}


def _yedekle(db: Session, tur: str, aciklama: str, admin) -> int:
    eski = mevcut(db, tur)
    return db.execute(text("INSERT INTO veri_yedekleri (tur, satir_sayisi, veri, aciklama, admin_id, kaydeden) "
                           "VALUES (:t, :n, CAST(:v AS JSONB), :a, :i, :k) RETURNING id"),
                      {"t": tur, "n": len(eski), "v": json.dumps(eski, ensure_ascii=False), "a": aciklama,
                       "i": getattr(admin, "id", None), "k": getattr(admin, "ad_soyad", None)}).scalar()


def _yaz(db: Session, tur: str, satirlar: list[dict]) -> int:
    bol = _bolumler(db)
    if tur == "k5_baglari":
        kodlar = _k5_kodlari(db)
        db.execute(text("DELETE FROM bolum_k5_baglari WHERE degisken_id IN (SELECT id FROM degiskenler WHERE kod ~ '^U[0-9]{2}_')"))
        p = [{"b": bol[s["bolum"]], "d": kodlar[s["kod"]], "g": s["bag"]} for s in satirlar
             if s["bolum"] in bol and s["kod"] in kodlar]
        if p:
            db.execute(text("INSERT INTO bolum_k5_baglari (bolum_id, degisken_id, bag) VALUES (:b, :d, :g)"), p)
    else:
        db.execute(text("DELETE FROM bolum_ornek_meslekler"))
        p = [{"b": bol[s["bolum"]], "i": s.get("isco"), "a": s["ad"], "s": s.get("benzerlik"), "m": s.get("model_sayisi"),
              "r": s.get("sira")} for s in satirlar if s["bolum"] in bol]
        if p:
            db.execute(text("INSERT INTO bolum_ornek_meslekler (bolum_id, meslek_isco_kodu, meslek_adi, benzerlik_skoru, "
                            "model_sayisi, sira) VALUES (:b, :i, :a, :s, :m, :r)"), p)
    return len(p)


def uygula(db: Session, tur: str, satirlar: list[dict], admin, dosya_adi: str | None = None) -> dict:
    o = onizle(db, tur, satirlar)
    if not o["canliya_alinabilir"]:
        raise VeriHatasi("Eşleşmeyen bölüm ya da iş türü var; dosya canlıya alınamaz (önizlemeye bakın).")
    yedek = _yedekle(db, tur, f"{dosya_adi or 'dosya'} yüklenmeden önceki hâl", admin)
    n = _yaz(db, tur, satirlar)
    return {"yazilan": n, "yedek_id": yedek, "bolum_sayisi": o["bolum_sayisi"]}


def yedekler(db: Session, tur: str, adet: int = 10) -> list[dict]:
    rows = db.execute(text("SELECT id, satir_sayisi, aciklama, kaydeden, zaman FROM veri_yedekleri WHERE tur = :t "
                           "ORDER BY zaman DESC, id DESC LIMIT :a"), {"t": tur, "a": adet}).mappings().all()
    return [{"id": r["id"], "satir_sayisi": r["satir_sayisi"], "aciklama": r["aciklama"], "kaydeden": r["kaydeden"],
             "zaman": r["zaman"].isoformat() if r["zaman"] else None} for r in rows]


def geri_yukle(db: Session, yedek_id: int, admin) -> dict:
    r = db.execute(text("SELECT tur, veri FROM veri_yedekleri WHERE id = :i"), {"i": yedek_id}).mappings().first()
    if not r:
        raise VeriHatasi("Yedek bulunamadı.")
    tur, veri = r["tur"], r["veri"]
    if isinstance(veri, str):
        veri = json.loads(veri)
    yeni = _yedekle(db, tur, f"{yedek_id} numaralı yedeğe dönülmeden önceki hâl", admin)
    n = _yaz(db, tur, veri)
    return {"tur": tur, "yazilan": n, "yedek_id": yeni}


def son_yukleme(db: Session, tur: str):
    """Veri Kaynakları ekranı için: en son ne zaman canlıya alındı (yedek kaydı = yükleme anı)."""
    try:
        return db.execute(text("SELECT MAX(zaman) FROM veri_yedekleri WHERE tur = :t"), {"t": tur}).scalar()
    except Exception:
        db.rollback()
        return None
