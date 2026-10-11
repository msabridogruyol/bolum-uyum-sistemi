# -*- coding: utf-8 -*-
"""
[2026-10-11] Öğrenci — bölüm karşılaştırma (2–3 bölüm yan yana, tek istekte).

GET /ogrenci/karsilastir?bolumler=1,2,3        — tüm satırlar (eski istemciler için ?ids= de kabul edilir)
GET /ogrenci/karsilastir/pdf?bolumler=1,2,3    — aynı karşılaştırma PDF (reportlab, öğrencinin kendisi için)
GET /ogrenci/karsilastir/varsayilan            — seçim yokken başlangıç: hedef bölüm + ilk öneriler

Veri kaynakları (yalnızca var olan servisler; uydurma yok — veri yoksa alan None döner, arayüz "—" ve kısa açıklama yazar):
  uyum / sıra        → skor_motoru.nihai_uyum_haritasi (Sonuçlar ve Keşfet ile aynı sayı); K5 bitmeden boş
  neden bu bölüm     → skor_motoru.neden_aciklamalari (Sonuçlar sayfasındaki açıklama)
  öne çıkan özellik  → bolum_bilgi._yetkinlik_tablosu + öğrencinin son turdaki özellik puanı (seviye.guclu_mu)
  puan türü / süre / meslekler / günlük işler / çalışma ortamı / beceriler → bolumler.detay (içerik ekibi)
  taban puan / başarı sırası → YÖK Atlas önbelleği (yokatlas_onbellek). Ağa ÇIKILMAZ; önbellek yoksa durum
                       "onbellek_yok" döner ve arayüz /bolumler/{id}/universiteler ile ayrıca çeker.
  istihdam, mesleğe giden yol → İş Hayatı servisleri — yalnızca okulun paketinde is_hayati modülü açıksa
  simülasyon keyfi   → simulasyon_sonuclari — yalnızca kocluk modülü açıksa (simülasyon Koçluk modülüyle gelir)
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.api.listem import _alanlar, _son_tamamlanan_tur, uyum_haritasi
from app.core.database import get_db
from app.core.paketler import okul_modulleri
from app.models import Bolum, Degisken, Ogrenci, OgrenciDegiskenSkoru, YokatlasOnbellek

router = APIRouter(prefix="/ogrenci", tags=["Öğrenci — Bölüm Karşılaştırma"])

EN_FAZLA = 3


def _idler(bolumler: str | None, ids: str | None) -> list[int]:
    ham = bolumler or ids or ""
    try:
        idler = list(dict.fromkeys(int(x) for x in ham.split(",") if x.strip()))[:EN_FAZLA]
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz bölüm listesi.")
    if len(idler) < 2:
        raise HTTPException(status_code=400, detail="Karşılaştırmak için en az 2 bölüm seç.")
    return idler


def _detay(b: Bolum) -> dict:
    d = b.detay
    if isinstance(d, str):
        try:
            d = json.loads(d)
        except Exception:
            d = {}
    return d if isinstance(d, dict) else {}


def _yokatlas_ozeti(db: Session, bolum_id: int) -> dict:
    """Önbellekteki YÖK Atlas programlarından özet. Ağa çıkılmaz."""
    k = db.get(YokatlasOnbellek, bolum_id)
    v = (k.veri if k is not None else None) or {}
    p = v.get("programlar") or []
    if not p:
        return {"durum": "onbellek_yok" if k is None or k.veri is None else "veri_yok"}
    puan = [float(x["taban_puan"]) for x in p if x.get("taban_puan") is not None]
    sira = [int(x["basari_sirasi"]) for x in p if x.get("basari_sirasi") is not None]
    turler = Counter(x.get("puan_turu") for x in p if x.get("puan_turu"))
    return {
        "durum": "tamam", "yil": v.get("yil"), "program": len(p),
        "devlet": sum(1 for x in p if str(x.get("universite_turu") or "").upper().startswith("DEV")),
        "puan_min": min(puan) if puan else None, "puan_max": max(puan) if puan else None,
        "sira_en": min(sira) if sira else None, "sira_son": max(sira) if sira else None,
        "puan_turu": turler.most_common(1)[0][0] if turler else None, "kaynak": "YÖK Atlas",
    }


def _meslek_ozeti(d: dict) -> dict:
    ml = [m for m in (d.get("meslekler") or []) if isinstance(m, dict) and m.get("ad")]
    beceri = Counter()
    for m in ml:
        for x in m.get("gerekli_beceriler") or []:
            if isinstance(x, str) and x.strip():
                beceri[x.strip()] += 1
    return {
        "meslekler": [m["ad"] for m in ml][:6],
        "gunluk": [{"meslek": m["ad"], "isler": (m.get("gunluk_isler") or [])[:2], "ortam": m.get("calisma_ortami")}
                   for m in ml[:2] if m.get("gunluk_isler") or m.get("calisma_ortami")],
        "beceriler": [b for b, _ in beceri.most_common(6)],
    }


def _istihdam(db: Session, bolum_id: int) -> dict | None:
    from app.core import is_hayati_servisi as ihs
    try:
        v = ihs.istihdam_bolum(db, bolum_id)
    except Exception:
        db.rollback()
        return None
    if not v:
        return None
    return {k: v.get(k) for k in ("istihdam_orani", "is_bulma_suresi_ay", "alan_uyum_orani", "kazanc_grubu", "kazanc_grubu_ad",
                                  "veri_yili", "kaynak", "duzey_ad")}


def _yol(db: Session, b: Bolum, d: dict) -> dict | None:
    try:
        from app.api.is_hayati_yol import _ana_alan, yol_birlestir, yol_verisi
        alan = None if b.ad in yol_verisi()["bolumler"] else _ana_alan(db, b.id)
        y = yol_birlestir(b.ad, alan, d.get("ogrenim_suresi"))
    except Exception:
        db.rollback()
        return None
    adimlar = [a.get("baslik") for a in (y.get("adimlar") or []) if isinstance(a, dict) and a.get("zorunlu") and a.get("baslik")]
    if not adimlar and not y.get("ozel"):
        return None
    return {"adimlar": adimlar[:5], "ozel": y.get("ozel"), "regule": y.get("regule"), "oda_kaydi": y.get("oda_kaydi")}


def karsilastirma_verisi(db: Session, o: Ogrenci, idler: list[int]) -> dict:
    bolumler = {b.id: b for b in db.query(Bolum).filter(Bolum.id.in_(idler)).all()}
    if len(bolumler) != len(idler):
        raise HTTPException(status_code=404, detail="Bölümlerden biri bulunamadı.")

    from app.api.bolum_bilgi import _yetkinlik_tablosu
    from app.core.is_hayati_servisi import tr_baslik
    from app.core.meslek_dili_servisi import etkin_surum
    from app.core.seviye import gelisime_acik_mi, guclu_mu

    moduller = set(okul_modulleri(db, o.okul_id))
    is_hayati = "is_hayati" in moduller
    kocluk = "kocluk" in moduller

    uyum = uyum_haritasi(db, o)   # boşsa: değerlendirme / K5 bitmedi
    sira = {bid: i for i, (bid, _) in enumerate(sorted(uyum.items(), key=lambda kv: -kv[1]), 1)}
    alan = _alanlar(db, idler)
    tablo = _yetkinlik_tablosu(db)
    tur = _son_tamamlanan_tur(db, o)

    nedenler: dict = {}
    if uyum and tur is not None:
        try:
            from app.core.skor_motoru import neden_aciklamalari
            nedenler = neden_aciklamalari(db, o, tur, idler) or {}
        except Exception:
            db.rollback()

    ogr_puan: dict[str, float] = {}
    if tur is not None:
        kodlar = {d.id: d.kod for d in db.query(Degisken).all()}
        for s in db.query(OgrenciDegiskenSkoru).filter(OgrenciDegiskenSkoru.ogrenci_id == o.id,
                                                       OgrenciDegiskenSkoru.tur_id == tur.id).all():
            if s.degisken_id in kodlar:
                ogr_puan[kodlar[s.degisken_id]] = float(s.puan)

    def sende_mi(x: dict) -> bool | None:
        p = ogr_puan.get(x["kod"])
        if p is None:
            return None
        return guclu_mu(p) if x.get("uc") != "dusuk" else gelisime_acik_mi(p)

    hedef = db.execute(text("SELECT bolum_id FROM ogrenci_hedef_bolum WHERE ogrenci_id = :o AND aktif_mi "
                            "ORDER BY secim_zamani DESC LIMIT 1"), {"o": o.id}).scalar()

    sim: dict[int, list] = {}
    if kocluk:
        try:
            for r in db.execute(text("""
                SELECT DISTINCT ON (bolum_id, meslek_ad) bolum_id, meslek_ad, keyif, olusturulma_zamani FROM simulasyon_sonuclari
                 WHERE ogrenci_id = :o AND bolum_id = ANY(:b) ORDER BY bolum_id, meslek_ad, olusturulma_zamani DESC"""),
                    {"o": o.id, "b": idler}).all():
                sim.setdefault(r.bolum_id, []).append({"meslek": r.meslek_ad, "keyif": int(r.keyif)})
        except Exception:
            db.rollback()

    sonuc = []
    for bid in idler:
        b = bolumler[bid]
        d = _detay(b)
        satirlar = [x for grup in tablo["tablo"].get(bid, {}).values() for x in grup if x["one_cikan"]]
        satirlar.sort(key=lambda x: -x["guc"])
        ms = _meslek_ozeti(d)
        if not ms["meslekler"]:
            try:
                ms["meslekler"] = [r[0] for r in db.execute(text(
                    "SELECT meslek_adi FROM bolum_ornek_meslekler WHERE bolum_id = :b ORDER BY sira LIMIT 6"), {"b": bid}).all()]
            except Exception:
                db.rollback()
        try:
            jargon = (etkin_surum(db, b, o.okul_id) or {}).get("terimler") or []
        except Exception:
            db.rollback()
            jargon = []
        n = nedenler.get(bid) or {}
        yok = _yokatlas_ozeti(db, bid)
        sonuc.append({
            "bolum_id": bid, "bolum_adi": tr_baslik(b.ad), "kisa_aciklama": b.kisa_aciklama,
            **alan.get(bid, {"ust_alan": None, "alt_alan": None}),
            "hedef": bid == hedef,
            "toplam_uyum": round(float(uyum[bid]), 1) if bid in uyum else None,
            "sira": sira.get(bid),
            # "Dikkat" cümlesi metinlerde de var; ayrı alanda (dikkat) gösterildiği için tekrarlanmaz
            "neden": [m for m in (n.get("metinler") or []) if not str(m).startswith("Dikkat")][:4],
            "dikkat": (n.get("dikkat") or {}).get("metin"),
            "one_cikanlar": [{"kod": x["kod"], "etiket": x["etiket"], "onem": x["onem"], "sende": sende_mi(x)} for x in satirlar[:6]],
            "puan_turu": d.get("puan_turu") or getattr(b, "osym_puan_turu", None) or yok.get("puan_turu"),
            "ogrenim_suresi": d.get("ogrenim_suresi"),
            "yokatlas": yok,
            "istihdam": _istihdam(db, bid) if is_hayati else None,
            "yol": _yol(db, b, d) if is_hayati else None,
            **ms,
            "simulasyon": sorted(sim.get(bid, []), key=lambda x: -x["keyif"]) if kocluk else None,
            "jargon": [{"terim": t.get("terim"), "anlam": t.get("anlam")} for t in jargon[:3] if isinstance(t, dict)],
        })
    return {
        "bolumler": sonuc, "profil_var": bool(ogr_puan), "sonuc_var": bool(uyum), "toplam_bolum": len(uyum) or None,
        "moduller": {"is_hayati": is_hayati, "simulasyon": kocluk},
    }


@router.get("/karsilastir/varsayilan")
def karsilastir_varsayilan(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    """Seçim yokken başlangıç: hedef bölüm + en uyumlu ilk öneriler (en fazla 3 bölüm)."""
    from app.core.is_hayati_servisi import tr_baslik
    hedef = db.execute(text("SELECT b.id, b.ad FROM ogrenci_hedef_bolum h JOIN bolumler b ON b.id = h.bolum_id "
                            "WHERE h.ogrenci_id = :o AND h.aktif_mi ORDER BY h.secim_zamani DESC LIMIT 1"), {"o": o.id}).first()
    uyum = uyum_haritasi(db, o)
    ilk = [bid for bid, _ in sorted(uyum.items(), key=lambda kv: -kv[1])[:4] if not hedef or bid != hedef.id]
    idler = ([hedef.id] if hedef else []) + ilk[:2]
    idler = idler[:EN_FAZLA]
    adlar = {b.id: tr_baslik(b.ad) for b in db.query(Bolum).filter(Bolum.id.in_(idler or [-1])).all()}
    return {"bolumler": [{"bolum_id": i, "bolum_adi": adlar.get(i), "hedef": bool(hedef and i == hedef.id),
                          "toplam_uyum": round(float(uyum[i]), 1) if i in uyum else None} for i in idler]}


@router.get("/karsilastir")
def karsilastir(bolumler: str | None = Query(None, description="virgülle ayrılmış 2-3 bölüm id"),
                ids: str | None = Query(None, include_in_schema=False),
                db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return karsilastirma_verisi(db, o, _idler(bolumler, ids))


@router.get("/karsilastir/pdf")
def karsilastir_pdf(bolumler: str | None = Query(None), ids: str | None = Query(None, include_in_schema=False),
                    db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.api.raporlar import _cevap, _dosya_adi
    from app.core.rapor.veri import okul_bilgisi
    v = karsilastirma_verisi(db, o, _idler(bolumler, ids))
    icerik = karsilastirma_pdf(v, okul_bilgisi(db, o.okul_id), o.ad_soyad)
    return _cevap(icerik, "pdf", _dosya_adi("Bolum_Karsilastirma", o.ad_soyad, datetime.now().strftime("%Y%m%d")))


# ============================================================================= PDF
def _tr(x, kesir=0) -> str:
    if x is None:
        return "—"
    s = f"{x:,.{kesir}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def karsilastirma_pdf(v: dict, okul: dict, ad_soyad: str) -> bytes:
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, Spacer
    from app.core.rapor.pdf import _belge, _e, _tablo

    doc, tampon, st = _belge("Bölüm karşılaştırma", okul, datetime.now())
    kol = v["bolumler"]
    n = len(kol)
    etiket_gen = 34 * mm
    gen = [etiket_gen] + [(174 * mm - etiket_gen) / n] * n

    def liste(l, isaret="• "):
        return "<br/>".join(isaret + _e(x) for x in l) if l else "—"

    satirlar = []

    def satir(etiket, f):
        satirlar.append([Paragraph(f"<b>{_e(etiket)}</b>", st.hucre)] + [Paragraph(f(b), st.hucre) for b in kol])

    if v["sonuc_var"]:
        satir("Uyumun", lambda b: f"<b>%{b['toplam_uyum']:.0f}</b>" + (f" · {b['sira']}. sıra" if b.get("sira") else "")
              if b["toplam_uyum"] is not None else "—")
        satir("Neden bu bölüm", lambda b: liste(b["neden"] + ([f"Dikkat: {b['dikkat']}"] if b.get("dikkat") else [])))
    satir("Alan", lambda b: _e(b.get("alt_alan") or b.get("ust_alan") or "—"))
    satir("Puan türü", lambda b: _e(b.get("puan_turu") or "—"))
    satir("Öğrenim süresi", lambda b: _e(b.get("ogrenim_suresi") or "—"))

    def yok(b, a1, a2, kesir):
        y = b["yokatlas"]
        if y.get("durum") != "tamam" or y.get(a1) is None:
            return "—"
        return f"{_tr(y[a1], kesir)} – {_tr(y[a2], kesir)}" + (f" ({y['yil']})" if y.get("yil") else "")
    satir("Taban puan (YÖK Atlas)", lambda b: yok(b, "puan_min", "puan_max", 2))
    satir("Başarı sırası", lambda b: yok(b, "sira_en", "sira_son", 0))
    if v["moduller"]["is_hayati"]:
        def ist(b):
            i = b.get("istihdam")
            if not i:
                return "—"
            p = []
            if i.get("istihdam_orani") is not None:
                p.append(f"İstihdam: %{_tr(i['istihdam_orani'])}")
            if i.get("is_bulma_suresi_ay") is not None:
                p.append(f"İş bulma: {_tr(i['is_bulma_suresi_ay'], 1)} ay")
            if i.get("alan_uyum_orani") is not None:
                p.append(f"Alanında çalışan: %{_tr(i['alan_uyum_orani'])}")
            if i.get("kazanc_grubu_ad"):
                p.append(f"Kazanç: {_e(i['kazanc_grubu_ad'])}")
            return "<br/>".join(p) + (f"<br/><font size=7>{_e(i.get('kaynak') or '')} {i.get('veri_yili') or ''}</font>" if p else "—")
        satir("İstihdam", ist)
        satir("Mesleğe giden yol", lambda b: liste((b.get("yol") or {}).get("adimlar") or [], "→ "))
    satir("Öne çıkan özellikler (+ sende de güçlü)", lambda b: "<br/>".join(("<b>+ </b>" if x["sende"] else "· ") + _e(x["etiket"]) for x in b["one_cikanlar"]) or "—")
    satir("Meslekler", lambda b: liste(b["meslekler"][:5]))
    satir("Gerekli beceriler", lambda b: liste(b["beceriler"][:5]))
    satir("Çalışma ortamı", lambda b: "<br/>".join(f"<b>{_e(g['meslek'])}:</b> {_e(g['ortam'])}" for g in b["gunluk"] if g.get("ortam")) or "—")
    if v["moduller"]["simulasyon"]:
        satir("Simülasyon keyfin", lambda b: "<br/>".join(f"{_e(s['meslek'])}: %{s['keyif']}" for s in b["simulasyon"] or []) or "—")

    hikaye = [
        st.p("Bölüm karşılaştırma", st.baslik),
        st.p(_e(ad_soyad) + " · " + _e(okul.get("ad") or ""), st.alt),
        _tablo(st, [""] + [b["bolum_adi"] + (" (hedefin)" if b.get("hedef") else "") for b in kol], satirlar, gen),
        Spacer(1, 8),
        st.p("Uyum yüzdesi bir karar desteğidir, kesin hüküm değildir. Taban puan ve başarı sırası YÖK Atlas'ın son yerleştirme "
             "verisidir; yıldan yıla değişir. İstihdam verileri kaynağında belirtilen yıla aittir. '—' o bilginin sistemde olmadığını gösterir.",
             st.not_),
    ]
    doc.build(hikaye)
    return tampon.getvalue()
