# -*- coding: utf-8 -*-
"""
[2026-10-10] Okul denemeleri — rehber öğretmen, okulun yaptığı denemenin sonuçlarını Excel şablonuyla tek seferde yükler.
Sonuçlar her öğrencinin Net Takibi'ne "Okul denemesi" olarak düşer (öğrenci silemez); okul ve şube ortalamaları hesaplanır.

Modül: okul_denemeleri (Net takibi gerekir)
  GET    /yonetim/okul/{okul_id}/deneme-sablonu?oturum=TYT|AYT|YDT&sinif=12. Sınıf   — öğrenci listesi dolu şablon
  POST   /yonetim/okul/{okul_id}/deneme-onizle      — {oturum, dosya_adi, icerik_base64} → eşleşen / eşleşmeyen / hatalı satırlar
  POST   /yonetim/okul/{okul_id}/okul-denemeleri    — {ad, tarih, oturum, dosya_adi, icerik_base64} → kaydet
  GET    /yonetim/okul/{okul_id}/okul-denemeleri    — denemeler + katılım + ortalamalar
  GET    /yonetim/okul-deneme/{deneme_id}           — sonuç listesi, ders ve şube ortalamaları
  DELETE /yonetim/okul-deneme/{deneme_id}           — deneme ve öğrencilere düşen sonuçları siler
"""
import json
import re
from collections import defaultdict
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_yonetimi import _dosyadan_satirlar, _norm, _okul_kapsami, _sinif_metni, _xlsx_b64
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.sinav_yapisi import TESTLER, net_hesapla
from app.models import AdminKullanici, Ogrenci

router = APIRouter(prefix="/yonetim", tags=["Okul denemeleri"])

OTURUMLAR = ("TYT", "AYT", "YDT")
# Başlıkta tanınan ders adları (normalize edilmiş) → test kodu
DERS_ADLARI = {
    "TYT": {"tyt_trk": ["turkce", "trk", "tur"], "tyt_sos": ["sosyal", "sosyalbilimler", "sos"],
            "tyt_mat": ["temelmatematik", "matematik", "mat"], "tyt_fen": ["fen", "fenbilimleri"]},
    "AYT": {"ayt_mat": ["matematik", "mat"], "ayt_fiz": ["fizik", "fiz"], "ayt_kim": ["kimya", "kim"], "ayt_bio": ["biyoloji", "bio", "biy"],
            "ayt_tde": ["turkdilivedebiyati", "edebiyat", "tde", "turkdiliedebiyat"], "ayt_trh1": ["tarih1"], "ayt_cog1": ["cografya1", "cog1"],
            "ayt_trh2": ["tarih2"], "ayt_cog2": ["cografya2", "cog2"], "ayt_fel": ["felsefegrubu", "felsefe", "fel"],
            "ayt_din": ["dinkulturu", "din", "dinkulturuveahlakbilgisi"]},
    "YDT": {"ydt_ydil": ["yabancidil", "ingilizce", "ydt", "dil"]},
}
EKLER = (("dogru", "d"), ("yanlis", "y"), ("net", "net"), ("d", "d"), ("y", "y"), ("n", "net"))


def _testler(oturum: str) -> list[str]:
    return [k for k, v in TESTLER.items() if v[0] == oturum]


def _baslik_coz(baslik: list) -> tuple[dict, dict]:
    """→ (kimlik sütunları {ogrenci_no, ad_soyad, sinif}, ders sütunları {(test, d|y|net): index}) — tüm oturumlar için"""
    kimlik, ders = {}, {}
    for i, h in enumerate(_norm(c) for c in baslik):
        if not h:
            continue
        if h in ("ogrencino", "no", "numara", "okulno", "ogrencinumarasi") and "ogrenci_no" not in kimlik:
            kimlik["ogrenci_no"] = i
            continue
        if h in ("adsoyad", "adisoyadi", "ogrenci", "ogrenciadisoyadi", "isimsoyisim", "adsoyadi") and "ad_soyad" not in kimlik:
            kimlik["ad_soyad"] = i
            continue
        if h in ("sinif", "sinifsube", "sube") and "sinif" not in kimlik:
            kimlik["sinif"] = i
            continue
        for oturum, dersler in DERS_ADLARI.items():
            for kod, adlar in dersler.items():
                for ad in sorted(adlar, key=len, reverse=True):
                    for ek, alan in EKLER:
                        if h == ad + ek or h == ad + "_" + ek:
                            ders.setdefault((oturum, kod, alan), i)
    return kimlik, ders


def _sayi(v):
    if v is None or str(v).strip() in ("", "-"):
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return "hata"


def _ayikla(db: Session, okul_id: int, oturum: str, dosya_adi: str, icerik: str) -> dict:
    if oturum not in OTURUMLAR:
        raise HTTPException(400, "Oturum TYT, AYT ya da YDT olmalı.")
    # Excel satır numarası korunur (boş satırlar atlansa da hata mesajı doğru satırı göstersin)
    numarali = [(i, r) for i, r in enumerate(_dosyadan_satirlar(dosya_adi, icerik), start=1) if any(str(c).strip() for c in r)]
    satirlar = [r for _, r in numarali]
    bas_no, kimlik, ders = None, {}, {}
    for n, aday in enumerate(satirlar[:8]):
        k, d = _baslik_coz(aday)
        d = {(kod, alan): i for (ot, kod, alan), i in d.items() if ot == oturum}
        if ("ogrenci_no" in k or "ad_soyad" in k) and d:
            bas_no, kimlik, ders = n, k, d
            break
    if bas_no is None:
        raise HTTPException(400, f"Başlık satırı tanınmadı. {oturum} şablonunu indirip sütun adlarını değiştirmeden kullanın "
                                 "(ör. “Öğrenci No”, “Ad Soyad”, “Türkçe D”, “Türkçe Y”).")
    ogrenciler = db.query(Ogrenci).filter(Ogrenci.okul_id == okul_id).all()
    no_ile = {(o.ogrenci_no or "").strip(): o for o in ogrenciler if (o.ogrenci_no or "").strip()}
    ad_ile = defaultdict(list)
    for o in ogrenciler:
        ad_ile[_norm(o.ad_soyad)].append(o)
    al = lambda r, i: r[i] if i is not None and i < len(r) else None  # noqa: E731
    sonuc, gorulen = [], set()
    for no, r in numarali[bas_no + 1:]:
        ham_no = str(al(r, kimlik.get("ogrenci_no")) or "").strip()
        if ham_no.endswith(".0"):
            ham_no = ham_no[:-2]
        ham_ad = re.sub(r"\s+", " ", str(al(r, kimlik.get("ad_soyad")) or "")).strip()
        hatalar, uyarilar = [], []
        o = no_ile.get(ham_no) if ham_no else None
        if o is None and ham_ad:
            adaylar = ad_ile.get(_norm(ham_ad), [])
            if len(adaylar) == 1:
                o = adaylar[0]
                if ham_no:
                    uyarilar.append("Numara eşleşmedi, ad soyadla eşleştirildi")
            elif len(adaylar) > 1:
                hatalar.append("Bu adla birden fazla öğrenci var; öğrenci numarasını yazın")
        dersler, toplam, bos = {}, 0.0, True
        for kod in _testler(oturum):
            d, y, n = (_sayi(al(r, ders.get((kod, a)))) for a in ("d", "y", "net"))
            if "hata" in (d, y, n):
                hatalar.append(f"{TESTLER[kod][1]}: sayı değil")
                continue
            if d is None and y is None and n is None:
                continue
            bos = False
            soru = TESTLER[kod][2]
            if d is not None or y is not None:
                d, y = int(d or 0), int(y or 0)
                if d < 0 or y < 0 or d + y > soru:
                    hatalar.append(f"{TESTLER[kod][1]}: doğru + yanlış {soru}'ı geçemez")
                    continue
                net = net_hesapla(d, y)
                if n is not None and abs(n - net) > 0.3:
                    uyarilar.append(f"{TESTLER[kod][1]}: dosyadaki net ({n}) D/Y ile uyuşmuyor; {net} kullanıldı")
                dersler[kod] = {"d": d, "y": y, "net": net}
            else:
                if n < -soru / 4 or n > soru:
                    hatalar.append(f"{TESTLER[kod][1]}: net geçersiz")
                    continue
                dersler[kod] = {"d": None, "y": None, "net": round(n, 2)}
            toplam += dersler[kod]["net"]
        if bos and not ham_no and not ham_ad:
            continue
        if bos:
            uyarilar.append("Sonuç yok — sınava girmemiş sayılır, atlanacak")
        elif o is None and not hatalar:
            hatalar.append("Öğrenci bulunamadı (numara ve ad soyad eşleşmedi)")
        if o is not None and o.id in gorulen:
            hatalar.append("Bu öğrenci dosyada birden fazla kez geçiyor")
        if o is not None:
            gorulen.add(o.id)
        sonuc.append({"satir": no, "ogrenci_no": ham_no, "ad_soyad": ham_ad, "ogrenci_id": str(o.id) if o else None,
                      "eslesen_ad": o.ad_soyad if o else None, "sinif_metni": _sinif_metni(o) if o else None,
                      "dersler": dersler, "toplam_net": round(toplam, 2), "bos": bos,
                      "hata": "; ".join(hatalar) or None, "uyari": "; ".join(uyarilar) or None})
    if not sonuc:
        raise HTTPException(400, "Dosyada öğrenci satırı bulunamadı.")
    gecerli = [s for s in sonuc if not s["hata"] and not s["bos"]]
    return {"satirlar": sonuc, "testler": [{"kod": k, "ad": TESTLER[k][1], "soru": TESTLER[k][2]} for k in _testler(oturum)],
            "ozet": {"toplam": len(sonuc), "gecerli": len(gecerli), "hatali": sum(1 for s in sonuc if s["hata"]),
                     "bos": sum(1 for s in sonuc if s["bos"] and not s["hata"]),
                     "ortalama": round(sum(s["toplam_net"] for s in gecerli) / len(gecerli), 2) if gecerli else None},
            "taninan_dersler": sorted({TESTLER[k][1] for (k, _a) in ders})}


# ----------------------------------------------------------------------------- şablon
@router.get("/okul/{okul_id}/deneme-sablonu")
def deneme_sablonu(okul_id: int, oturum: str = Query("TYT"), sinif: str | None = Query(None), db: Session = Depends(get_db),
                   yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    okul = _okul_kapsami(db, yon, okul_id)
    if oturum not in OTURUMLAR or okul is None:
        raise HTTPException(400, "Geçersiz oturum.")
    q = db.query(Ogrenci).filter(Ogrenci.okul_id == okul_id)
    if sinif:
        q = q.filter(Ogrenci.sinif == sinif)
    ogrenciler = sorted([o for o in q.all() if not getattr(o, "test_hesabi", False)], key=lambda o: (o.sinif or "", o.sube or "", o.ad_soyad.lower()))
    kolonlar = ["Öğrenci No", "Ad Soyad", "Sınıf"]
    for k in _testler(oturum):
        kolonlar += [f"{TESTLER[k][1]} D", f"{TESTLER[k][1]} Y"]
    satirlar = [[o.ogrenci_no or "", o.ad_soyad, _sinif_metni(o)] + [""] * (len(kolonlar) - 3) for o in ogrenciler]
    not_metni = (f"{oturum} denemesi: her ders için doğru (D) ve yanlış (Y) sayısını yazın; net otomatik hesaplanır. "
                 "Sınava girmeyen öğrencinin satırını boş bırakın. Yayınevi dosyanızdaki sütunları buraya kopyalayabilirsiniz. "
                 "Yalnızca net varsa “Türkçe Net” gibi bir sütun da eklenebilir.")
    ek = f"_{sinif.replace('. Sınıf', '').replace(' ', '')}" if sinif else ""
    return {"dosya_adi": f"{oturum}_deneme_sablonu{ek}.xlsx", "icerik_base64": _xlsx_b64(f"{oturum} denemesi", kolonlar, satirlar, not_metni)}


class DosyaIstek(BaseModel):
    oturum: str
    dosya_adi: str
    icerik_base64: str


class KaydetIstek(DosyaIstek):
    ad: str = Field(min_length=2, max_length=80)
    tarih: date


@router.post("/okul/{okul_id}/deneme-onizle")
def deneme_onizle(okul_id: int, istek: DosyaIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    if _okul_kapsami(db, yon, okul_id) is None:
        raise HTTPException(400, "Okul harici öğrenciler için okul denemesi yüklenemez.")
    return _ayikla(db, okul_id, istek.oturum, istek.dosya_adi, istek.icerik_base64)


@router.post("/okul/{okul_id}/okul-denemeleri", status_code=201)
def deneme_kaydet(okul_id: int, istek: KaydetIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    if _okul_kapsami(db, yon, okul_id) is None:
        raise HTTPException(400, "Okul harici öğrenciler için okul denemesi yüklenemez.")
    if istek.tarih > date.today() + timedelta(days=1) or istek.tarih < date.today() - timedelta(days=730):
        raise HTTPException(400, "Tarih geçersiz.")
    v = _ayikla(db, okul_id, istek.oturum, istek.dosya_adi, istek.icerik_base64)
    gecerli = [s for s in v["satirlar"] if not s["hata"] and not s["bos"]]
    if not gecerli:
        raise HTTPException(400, "Kaydedilecek geçerli satır yok.")
    d_id = db.execute(text("INSERT INTO okul_denemeleri (okul_id, ad, tarih, oturum, olusturan) VALUES (:ok, :ad, :t, :ot, :y) RETURNING id"),
                      {"ok": okul_id, "ad": istek.ad.strip(), "t": istek.tarih, "ot": istek.oturum, "y": yon.ad_soyad}).scalar()
    for s in gecerli:
        db.execute(text("INSERT INTO ogrenci_denemeleri (ogrenci_id, tarih, oturum, ad, dersler, toplam_net, okul_deneme_id) "
                        "VALUES (CAST(:o AS UUID), :t, :ot, :ad, CAST(:d AS JSONB), :tn, :di)"),
                   {"o": s["ogrenci_id"], "t": istek.tarih, "ot": istek.oturum, "ad": istek.ad.strip(), "d": json.dumps(s["dersler"]),
                    "tn": s["toplam_net"], "di": d_id})
    denetim_yaz(db, yon, "okul_deneme_yukle", "okul_denemeleri", d_id, f"{istek.ad} ({istek.oturum}) · {len(gecerli)} öğrenci", okul_id)
    from app.core.bildirim import bildir   # [2026-10-10] uygulama içi bildirim (e-posta yok: toplu gönderim sınırı)
    bildir(db, "ogrenci", [s["ogrenci_id"] for s in gecerli], "okul_deneme", f"{istek.ad} sonuçların yüklendi",
           f"{istek.oturum} netlerin Net Takibi'ne eklendi; okul ortalamasıyla karşılaştırabilirsin.", "/netlerim", okul_id)
    db.commit()
    return {"id": d_id, "kaydedilen": len(gecerli), "atlanan": len(v["satirlar"]) - len(gecerli)}


def _istatistik(db: Session, deneme_ids: list[int]) -> dict:
    if not deneme_ids:
        return {}
    rows = db.execute(text("""
        SELECT d.okul_deneme_id, d.toplam_net, d.dersler, o.sinif, o.sube, o.id AS ogrenci_id, o.ad_soyad, o.ogrenci_no
          FROM ogrenci_denemeleri d JOIN ogrenciler o ON o.id = d.ogrenci_id WHERE d.okul_deneme_id = ANY(:i)
    """), {"i": deneme_ids}).all()
    g = defaultdict(list)
    for r in rows:
        g[r.okul_deneme_id].append(r)
    return g


def _ort(liste):
    liste = [x for x in liste if x is not None]
    return round(sum(liste) / len(liste), 2) if liste else None


@router.get("/okul/{okul_id}/okul-denemeleri")
def okul_denemeleri(okul_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    rows = db.execute(text("SELECT * FROM okul_denemeleri WHERE okul_id = :ok ORDER BY tarih DESC, id DESC"), {"ok": okul_id}).mappings().all()
    ist = _istatistik(db, [r["id"] for r in rows])
    return {"denemeler": [{
        "id": r["id"], "ad": r["ad"], "tarih": r["tarih"].isoformat(), "oturum": r["oturum"], "olusturan": r["olusturan"],
        "katilim": len(ist.get(r["id"], [])), "ortalama": _ort([float(x.toplam_net) for x in ist.get(r["id"], [])]),
        "en_yuksek": max([float(x.toplam_net) for x in ist.get(r["id"], [])], default=None),
    } for r in rows], "oturumlar": list(OTURUMLAR)}


@router.get("/okul-deneme/{deneme_id}")
def okul_deneme_detay(deneme_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = db.execute(text("SELECT * FROM okul_denemeleri WHERE id = :i"), {"i": deneme_id}).mappings().first()
    if r is None:
        raise HTTPException(404, "Deneme bulunamadı.")
    _okul_kapsami(db, yon, r["okul_id"])
    satirlar = sorted(_istatistik(db, [deneme_id]).get(deneme_id, []), key=lambda x: -float(x.toplam_net))
    testler = _testler(r["oturum"])
    sube = defaultdict(list)
    for x in satirlar:
        sube[f"{(x.sinif or '').replace('. Sınıf', '')}-{x.sube}" if x.sube and x.sinif != "Mezun" else (x.sinif or "—")].append(x)
    ders_ort = lambda grup, k: _ort([(x.dersler or {}).get(k, {}).get("net") for x in grup])  # noqa: E731
    return {
        "deneme": {"id": r["id"], "ad": r["ad"], "tarih": r["tarih"].isoformat(), "oturum": r["oturum"], "olusturan": r["olusturan"]},
        "testler": [{"kod": k, "ad": TESTLER[k][1], "soru": TESTLER[k][2]} for k in testler],
        "okul": {"katilim": len(satirlar), "ortalama": _ort([float(x.toplam_net) for x in satirlar]),
                 "dersler": {k: ders_ort(satirlar, k) for k in testler}},
        "subeler": sorted([{"sube": s, "katilim": len(l), "ortalama": _ort([float(x.toplam_net) for x in l]),
                            "dersler": {k: ders_ort(l, k) for k in testler}} for s, l in sube.items()], key=lambda s: -(s["ortalama"] or 0)),
        "sonuclar": [{"sira": i, "ogrenci_id": str(x.ogrenci_id), "ad_soyad": x.ad_soyad, "ogrenci_no": x.ogrenci_no,
                      "sinif_metni": f"{(x.sinif or '').replace('. Sınıf', '')}-{x.sube}" if x.sube and x.sinif != "Mezun" else (x.sinif or ""),
                      "toplam_net": float(x.toplam_net), "dersler": {k: (x.dersler or {}).get(k, {}).get("net") for k in testler}}
                     for i, x in enumerate(satirlar, 1)],
    }


@router.delete("/okul-deneme/{deneme_id}", status_code=204)
def okul_deneme_sil(deneme_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r = db.execute(text("SELECT id, okul_id, ad FROM okul_denemeleri WHERE id = :i"), {"i": deneme_id}).first()
    if r is None:
        raise HTTPException(404, "Deneme bulunamadı.")
    _okul_kapsami(db, yon, r.okul_id)
    n = db.execute(text("DELETE FROM ogrenci_denemeleri WHERE okul_deneme_id = :i"), {"i": deneme_id}).rowcount
    db.execute(text("DELETE FROM okul_denemeleri WHERE id = :i"), {"i": deneme_id})
    denetim_yaz(db, yon, "okul_deneme_sil", "okul_denemeleri", deneme_id, f"{r.ad} · {n} öğrenci sonucu silindi", r.okul_id)
    db.commit()
