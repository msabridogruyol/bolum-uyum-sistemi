# -*- coding: utf-8 -*-
"""
[2026-10-10] Rapor verisi — öğrenci (öğrenci / veli / yönetici raporları) ve okul genel raporu için.
Hiçbir puan burada yeniden hesaplanmaz: ekrandaki sonuçlarla AYNI kaynaklar kullanılır
(ogrenci_degisken_skorlari, siralama_getir + neden_aciklamalari, koçluk planı, güven skoru).
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import (
    Bolum, Dal, Degisken, GuvenlikOlayi, Katman, Ogrenci, OgrenciDalOturumu, OgrenciDegerlendirmeTuru,
    OgrenciDegiskenSkoru, OgrenciFavoriBolum, OgrenciGelisimAdimDurumu, OgrenciHaftalikGorev, Okul,
)


def _seviye(puan: float) -> str:
    return "Çok güçlü" if puan >= 75 else "Güçlü" if puan >= 62 else "Orta" if puan >= 40 else "Gelişime açık"


def _yorumlar(db: Session, satirlar: list[dict]) -> None:
    """gelisim_yorum_havuzu'ndan puan aralığına uygun durum tespiti ve öneriyi ekler (ekrandaki ile aynı)."""
    from app.api.ogrenci import _puan_araligi
    for s in satirlar:
        try:
            r = db.execute(text("SELECT durum_tespiti, aksiyon_onerisi FROM gelisim_yorum_havuzu "
                                "WHERE degisken_id = :d AND aralik = :a"),
                           {"d": s["id"], "a": _puan_araligi(s["puan"])}).mappings().first()
        except Exception:
            db.rollback()
            r = None
        s["yorum"] = (r or {}).get("durum_tespiti")
        s["oneri"] = (r or {}).get("aksiyon_onerisi")


def _baslik(metin: str | None) -> str:
    try:
        from app.core.koclugu_servisi import turkce_baslik
        return turkce_baslik(metin or "")
    except Exception:
        return metin or ""


def okul_bilgisi(db: Session, okul_id: int | None) -> dict:
    o = db.get(Okul, okul_id) if okul_id else None
    return {"ad": o.ad if o else "Okul harici", "alt_baslik": getattr(o, "alt_baslik", None),
            "logo": getattr(o, "logo", None), "renk": getattr(o, "tema_renk", None) or "#E8804A"}


# ============================================================================= öğrenci
def ogrenci_raporu_verisi(db: Session, o: Ogrenci) -> dict:
    simdi = datetime.now(timezone.utc)
    turlar = (db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id)
              .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).all())
    tur = turlar[0] if turlar else None
    tamam = next((t for t in turlar if t.durum == "tamamlandi"), None)
    v: dict = {
        "kisi": {"ad_soyad": o.ad_soyad, "email": o.email, "sinif": o.sinif, "sube": o.sube,
                 "ogrenci_no": getattr(o, "ogrenci_no", None)},
        "okul": okul_bilgisi(db, o.okul_id),
        "tarih": simdi,
        "tur": None, "katmanlar": [], "k5": [], "gucluler": [], "gelisim": [], "bolumler": [],
        "hedef": None, "listem": [], "guvenlik": {"ihlaller": [], "kamera": None}, "aktivite": {},
        "swot": {"S": [], "W": [], "O": [], "T": []}, "durum": "baslamadi",
    }
    if tur is None:
        return v
    kaynak = tamam or tur
    v["tur"] = {"no": kaynak.tur_no, "durum": kaynak.durum, "baslama": kaynak.baslama_zamani,
                "tamamlanma": kaynak.tamamlanma_zamani,
                "guven": float(kaynak.guven_skoru) if kaynak.guven_skoru is not None else None,
                "gecerli": bool(kaynak.sonuc_gecerli_mi), "gecersizlik": kaynak.gecersizlik_nedeni,
                "tur_sayisi": len(turlar)}
    v["durum"] = "tamamlandi" if tamam else "devam"

    # Özellik puanları (K1-K4 + K5 dalları)
    katmanlar = {k.id: k for k in db.query(Katman).all()}
    degiskenler = {d.id: d for d in db.query(Degisken).all()}
    dallar = {d.id: d.ad for d in db.query(Dal).all()}
    skorlar = db.query(OgrenciDegiskenSkoru).filter(OgrenciDegiskenSkoru.ogrenci_id == o.id,
                                                    OgrenciDegiskenSkoru.tur_id == kaynak.id).all()
    gruplar: dict[int, list[dict]] = defaultdict(list)
    k5: dict[str, list[float]] = defaultdict(list)
    ana: list[dict] = []
    for s in skorlar:
        d = degiskenler.get(s.degisken_id)
        if d is None:
            continue
        satir = {"id": d.id, "kod": d.kod, "ad": d.ad, "aciklama": d.aciklama, "puan": round(float(s.puan), 1),
                 "seviye": _seviye(float(s.puan))}
        if d.dal_id:
            k5[dallar.get(d.dal_id, "Alan")].append(float(s.puan))
            continue
        gruplar[d.katman_id].append(satir)
        ana.append(satir)
    _yorumlar(db, ana)
    for kid, satirlar in sorted(gruplar.items(), key=lambda kv: katmanlar[kv[0]].sira if kv[0] in katmanlar else 99):
        k = katmanlar.get(kid)
        satirlar.sort(key=lambda x: -x["puan"])
        v["katmanlar"].append({"kod": k.kod if k else "?", "ad": k.ad if k else "?",
                               "ortalama": round(sum(x["puan"] for x in satirlar) / len(satirlar), 1),
                               "ozellikler": satirlar})
    v["k5"] = [{"ad": a, "puan": round(sum(p) / len(p), 1)} for a, p in sorted(k5.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))]
    sirali = sorted(ana, key=lambda x: -x["puan"])
    v["gucluler"] = [x for x in sirali if x["puan"] >= 62][:6] or sirali[:3]
    v["gelisim"] = [x for x in reversed(sirali) if x["puan"] < 45][:5]

    # Bölüm önerileri + nedenleri (tamamlanmış ve K5 bitmiş tur)
    from app.core.dal_servisi import bekleyen_dal_var_mi
    if tamam is not None and not bekleyen_dal_var_mi(db, o, tamam):
        try:
            from app.core.skor_motoru import neden_aciklamalari, siralama_getir
            sira = siralama_getir(db, o, tamam, ilk_n=10)
            adlar = {b.id: b.ad for b in db.query(Bolum).filter(Bolum.id.in_([s.bolum_id for s in sira] or [-1])).all()}
            try:
                nedenler = neden_aciklamalari(db, o, tamam, [s.bolum_id for s in sira])
            except Exception:
                db.rollback()
                nedenler = {}
            for i, s in enumerate(sira, 1):
                n = nedenler.get(s.bolum_id) or {}
                v["bolumler"].append({
                    "sira": i, "bolum_id": s.bolum_id, "ad": _baslik(adlar.get(s.bolum_id)), "alan": s.alan,
                    "uyum": round(float(s.toplam_uyum), 1),
                    "ortusen": [x.get("ozellik") for x in (n.get("ortusen") or [])][:3],
                    "dikkat": (n.get("dikkat") or {}).get("metin"),
                })
        except Exception:
            db.rollback()
    else:
        v["durum"] = "devam" if tamam is None else "k5_bekliyor"

    # Hedef + koçluk ilerlemesi
    try:
        from app.core.koclugu_servisi import aktif_hedef_getir, gelisim_plani_olustur
        h = aktif_hedef_getir(db, o)
        if h is not None:
            b = db.get(Bolum, h.bolum_id)
            hedef = {"ad": _baslik(b.ad if b else "?"), "secim": h.secim_zamani, "ilerleme": None, "odak": [],
                     "sira": next((x["sira"] for x in v["bolumler"] if x["bolum_id"] == h.bolum_id), None),
                     "uyum": next((x["uyum"] for x in v["bolumler"] if x["bolum_id"] == h.bolum_id), None)}
            try:
                from app.api.koclugu import _gap_satirlarini_hazirla
                plan = gelisim_plani_olustur(db, o, h.bolum_id, _gap_satirlarini_hazirla(db, o))
                hedef["ilerleme"] = plan["ilerleme"]
                hedef["odak"] = [{"ad": x["degisken_adi"], "neden": x.get("neden_onemli"), "kategori": x.get("kategori")}
                                 for x in plan["odak_alanlari"]]
                hedef["siradaki"] = (plan.get("siradaki_adim") or {}).get("baslik")
            except Exception:
                db.rollback()
            if hedef["uyum"] is None and tamam is not None:
                try:
                    from app.core.skor_motoru import nihai_uyum_haritasi
                    u = nihai_uyum_haritasi(db, o, tamam).get(h.bolum_id)
                    hedef["uyum"] = round(float(u), 1) if u is not None else None
                except Exception:
                    db.rollback()
            v["hedef"] = hedef
    except Exception:
        db.rollback()

    v["listem"] = [_baslik(b.ad) for _, b in db.query(OgrenciFavoriBolum, Bolum).join(Bolum, Bolum.id == OgrenciFavoriBolum.bolum_id)
                   .filter(OgrenciFavoriBolum.ogrenci_id == o.id).all()]

    # Güvenlik (yalnızca yönetici raporunda ayrıntılı gösterilir)
    try:
        from app.core.guvenlik_servisi import OLAY_ADI, OLAY_CEZASI
        sayim = Counter(t for (t,) in db.query(GuvenlikOlayi.olay_tipi).filter(
            GuvenlikOlayi.ogrenci_id == o.id, GuvenlikOlayi.tur_id == kaynak.id).all())
        v["guvenlik"]["ihlaller"] = [{"ad": OLAY_ADI.get(t, t), "sayi": n} for t, n in sayim.items() if OLAY_CEZASI.get(t, 0) > 0]
        v["guvenlik"]["kamera"] = not any(t in sayim for t in ("kamera_rizasi_verilmedi", "kamera_izni_reddedildi", "kamera_desteklenmiyor"))
    except Exception:
        db.rollback()

    # Etkinlik
    gorev = db.query(OgrenciHaftalikGorev).filter(OgrenciHaftalikGorev.ogrenci_id == o.id).all()
    v["aktivite"] = {
        "son_giris": o.son_giris_zamani,
        "gorev_tamam": sum(1 for g in gorev if g.durum == "tamamlandi"),
        "gorev_toplam": len(gorev),
        "son4_hafta": sum(1 for g in gorev if g.durum == "tamamlandi" and g.tamamlanma_zamani
                          and g.tamamlanma_zamani >= simdi - timedelta(days=28)),
        "adim": db.query(OgrenciGelisimAdimDurumu).filter(OgrenciGelisimAdimDurumu.ogrenci_id == o.id,
                                                          OgrenciGelisimAdimDurumu.durum == "tamamlandi").count(),
    }
    v["swot"] = swot(v)
    v["netler"] = net_verisi(db, o)   # [2026-10-10] deneme / net takibi
    return v


def swot(v: dict) -> dict:
    """Güçlü yönler (S) · gelişim alanları (W) · fırsatlar (O) · dikkat edilecekler (T). Kurallı, veriye dayalı."""
    S, W, O, T = [], [], [], []
    for x in v["gucluler"][:5]:
        S.append(f"{x['ad']} — {x['seviye'].lower()} ({x['puan']:.0f})")
    hedef = v.get("hedef") or {}
    odak = [x for x in hedef.get("odak", [])]
    if odak:
        for x in odak[:4]:
            W.append(f"{x['ad']} — {hedef['ad']} bölümünün beklentisinin altında")
    for x in v["gelisim"][:4]:
        if len(W) >= 5:
            break
        if not any(x["ad"] in w for w in W):
            W.append(f"{x['ad']} — şu an daha az tercih edilen bir yön ({x['puan']:.0f})")
    if v["bolumler"]:
        ilk = v["bolumler"][:3]
        O.append("En uyumlu bölümler: " + ", ".join(f"{b['ad']} (%{b['uyum']:.0f})" for b in ilk))
        alanlar = Counter(b["alan"] for b in v["bolumler"] if b.get("alan"))
        if alanlar:
            O.append("Öne çıkan alan(lar): " + ", ".join(a for a, _ in alanlar.most_common(2)))
        ortusen = Counter(o for b in v["bolumler"][:5] for o in b.get("ortusen") or [])
        if ortusen:
            O.append("Önerilerinde tekrar eden güçlü yönler: " + ", ".join(a for a, _ in ortusen.most_common(3)))
    if v["k5"]:
        O.append(f"Alan sorularında öne çıkan alan: {v['k5'][0]['ad']}")
    if v["listem"]:
        O.append("İlgilendiği bölümler (Listem): " + ", ".join(v["listem"][:4]))
    if hedef:
        if hedef.get("sira") is None and v["bolumler"]:
            T.append(f"Hedef bölüm ({hedef['ad']}) ilk 10 önerisi arasında değil"
                     + (f"; uyumu %{hedef['uyum']:.0f}" if hedef.get("uyum") is not None else "")
                     + ". Hedef ile profil arasındaki farklar birlikte konuşulmalı.")
        oncelikli = [x["ad"] for x in odak if x.get("kategori") == "belirgin_altinda"]
        if oncelikli:
            T.append("Hedef bölüm için öncelikli gelişim gereken alanlar: " + ", ".join(oncelikli[:3]))
        il = hedef.get("ilerleme") or {}
        if il.get("toplam") and il.get("tamamlanan", 0) == 0:
            T.append("Yol haritasında henüz tamamlanmış adım yok")
    elif v["durum"] == "tamamlandi":
        T.append("Henüz hedef bölüm seçilmedi; koçluk planı başlamadı")
    for b in v["bolumler"][:3]:
        if b.get("dikkat"):
            T.append(f"{b['ad']}: {b['dikkat']}")
            break
    tur = v.get("tur") or {}
    if tur and not tur.get("gecerli", True):
        T.append("Son değerlendirmenin güven puanı eşiğin altında; sonuçlar temkinli yorumlanmalı, yeniden değerlendirme önerilir")
    a = v.get("aktivite") or {}
    if v["durum"] == "tamamlandi" and a.get("son4_hafta", 0) == 0:
        T.append("Son 4 haftada haftalık görev tamamlanmadı; düzenli takip önerilir")
    if v["durum"] != "tamamlandi":
        T.append("Değerlendirme henüz tamamlanmadı; bölüm önerileri tamamlanınca oluşur")
    return {"S": S, "W": W, "O": O, "T": T}


# ============================================================================= okul
def _katman_ortalamalari(db: Session, tur_idler: list[int]) -> list[dict]:
    if not tur_idler:
        return []
    satir = db.execute(text("""
        SELECT k.kod, k.ad, avg(s.puan) FROM ogrenci_degisken_skorlari s
          JOIN degiskenler d ON d.id = s.degisken_id JOIN katmanlar k ON k.id = d.katman_id
         WHERE s.tur_id = ANY(:t) AND d.dal_id IS NULL AND NOT k.kosullu_mu
         GROUP BY k.kod, k.ad, k.sira ORDER BY k.sira"""), {"t": tur_idler}).all()
    return [{"kod": r[0], "ad": r[1], "ortalama": round(float(r[2]), 1)} for r in satir]


def okul_raporu_verisi(db: Session, okul_id: int, yonetici, sinif: str | None = None, sube: str | None = None) -> dict:
    """[2026-10-10] sinif (ve sube) verilirse sınıf düzeyi / şube raporu: yalnızca o öğrenciler + okul ortalamasıyla karşılaştırma."""
    from app.api.okul_yonetimi import _durum, _ilerleme, okul_ozeti
    ozet = okul_ozeti(okul_id, db, yonetici, sinif=sinif, sube=sube)
    ogrenciler = db.query(Ogrenci).filter(Ogrenci.okul_id.is_(None) if okul_id == 0 else Ogrenci.okul_id == okul_id) \
        .order_by(Ogrenci.sinif, Ogrenci.sube, Ogrenci.ad_soyad).all()
    il_okul = _ilerleme(db, okul_id)
    if sinif:
        ogrenciler = [o for o in ogrenciler if o.sinif == sinif and (not sube or (o.sube or "") == sube)]
        if sube:   # şube listesinde okul numarası sırası daha kullanışlı
            ogrenciler.sort(key=lambda o: (int(o.ogrenci_no) if (o.ogrenci_no or "").isdigit() else 10**9, o.ad_soyad))
    secili = {o.id for o in ogrenciler}
    il = {k: v for k, v in il_okul.items() if k in secili}
    bolum = {b.id: b for b in db.query(Bolum).all()}
    turlar = {t.id: t for t in db.query(OgrenciDegerlendirmeTuru).filter(
        OgrenciDegerlendirmeTuru.id.in_([x["tur_id"] for x in il.values() if x.get("tur_id")] or [-1])).all()}

    # Alan dağılımı (1. öneri) ve katman ortalamaları (tamamlayanlar)
    from app.models import BolumDalEslesme
    alan_of = {}
    dallar = {d.id: d for d in db.query(Dal).all()}
    for e in db.query(BolumDalEslesme).all():
        d = dallar.get(e.dal_id)
        if d and d.kod.startswith("U") and e.bolum_id not in alan_of:
            alan_of[e.bolum_id] = d.ad
    alan = Counter()
    tamam_turlar = [x["tur_id"] for x in il.values() if x.get("durum") == "tamamlandi" and x.get("tur_id")]
    for x in il.values():
        if x.get("durum") == "tamamlandi" and x.get("ilk_bolum"):
            alan[alan_of.get(x["ilk_bolum"], "Diğer")] += 1
    katman_ort = _katman_ortalamalari(db, tamam_turlar)
    okul_katman_ort = []
    if sinif:
        okul_katman_ort = _katman_ortalamalari(db, [x["tur_id"] for x in il_okul.values()
                                                    if x.get("durum") == "tamamlandi" and x.get("tur_id")])
    if tamam_turlar:
        guclu = db.execute(text("""
            SELECT d.ad, avg(s.puan) AS o FROM ogrenci_degisken_skorlari s JOIN degiskenler d ON d.id = s.degisken_id
             WHERE s.tur_id = ANY(:t) AND d.dal_id IS NULL GROUP BY d.ad ORDER BY o DESC"""), {"t": tamam_turlar}).all()
    else:
        guclu = []
    liste = []
    gecersiz = 0
    for o in ogrenciler:
        x = il.get(o.id) or {}
        kod, etiket = _durum(o, x)
        t = turlar.get(x.get("tur_id"))
        if t is not None and t.durum == "tamamlandi" and not t.sonuc_gecerli_mi:
            gecersiz += 1
        liste.append({
            "ad_soyad": o.ad_soyad, "sinif": " / ".join(filter(None, [o.sinif, o.sube])) or "—", "durum": etiket,
            "no": o.ogrenci_no or "",
            "ilk_bolum": _baslik(bolum[x["ilk_bolum"]].ad) if x.get("ilk_bolum") in bolum and kod == "tamamlandi" else "",
            "hedef": _baslik(bolum[x["hedef"]].ad) if x.get("hedef") in bolum else "",
            "guven": float(t.guven_skoru) if t is not None and t.guven_skoru is not None else None,
            "son_giris": o.son_giris_zamani, "test": bool(getattr(o, "test_hesabi", False)),
        })
    # [2026-10-10] Deneme / net özeti ve öğrenci başına son TYT / AYT neti
    net = okul_net_ozeti(db, [o.id for o in ogrenciler])
    for o, x in zip(ogrenciler, liste):
        n = net["ogrenci"].get(o.id) or {}
        x["son_tyt"], x["son_ayt"], x["deneme"] = n.get("TYT"), n.get("AYT"), n.get("sayi", 0)
    for anahtar in ("en_cok_onerilen", "en_cok_hedeflenen"):
        ozet[anahtar] = [{**x, "bolum": _baslik(x["bolum"])} for x in ozet.get(anahtar, [])]
    return {
        "okul": okul_bilgisi(db, okul_id), "tarih": datetime.now(timezone.utc), "ozet": ozet,
        "alanlar": [{"alan": a, "sayi": n} for a, n in alan.most_common(8)],
        "katman_ort": katman_ort, "okul_katman_ort": okul_katman_ort, "kapsam": ozet.get("kapsam") or {},
        "ortak_guclu": [{"ad": r[0], "ortalama": round(float(r[1]), 1)} for r in guclu[:6]],
        "ortak_gelisim": [{"ad": r[0], "ortalama": round(float(r[1]), 1)} for r in list(reversed(guclu))[:6]],
        "gecersiz": gecersiz, "ogrenciler": liste,
        "net": {k: v for k, v in net.items() if k != "ogrenci"},
    }


# ============================================================================= [2026-10-10] deneme / net verisi
def net_verisi(db: Session, o: Ogrenci) -> dict | None:
    """Öğrencinin deneme sonuçları, ders ders son/ortalama, konu ilerlemesi ve hedef program kıyası. Hiç veri yoksa None."""
    from app.core.sinav_yapisi import KONU_DERSLERI, TESTLER
    try:
        rows = db.execute(text("SELECT tarih, oturum, ad, dersler, toplam_net FROM ogrenci_denemeleri WHERE ogrenci_id = :o "
                               "ORDER BY tarih, id"), {"o": o.id}).all()
        konu = db.execute(text("SELECT ders, durum, count(*) FROM ogrenci_konu_takibi WHERE ogrenci_id = :o GROUP BY ders, durum"),
                          {"o": o.id}).all()
    except Exception:
        db.rollback()
        return None
    if not rows and not konu:
        return None
    denemeler = [{"tarih": r.tarih, "oturum": r.oturum, "ad": r.ad, "dersler": r.dersler or {}, "toplam": float(r.toplam_net)}
                 for r in rows]
    oturumlar = []
    for ot in ("TYT", "AYT", "YDT"):
        l = [d for d in denemeler if d["oturum"] == ot]
        if not l:
            continue
        son3 = [d["toplam"] for d in l[-3:]]
        oturumlar.append({"oturum": ot, "sayi": len(l), "ilk": l[0]["toplam"], "son": l[-1]["toplam"],
                          "en_iyi": max(d["toplam"] for d in l), "ort3": round(sum(son3) / len(son3), 2),
                          "degisim": round(l[-1]["toplam"] - l[0]["toplam"], 2), "seri": [(d["tarih"], d["toplam"]) for d in l]})
    dersler = []
    for kod, (ot, ad, soru, _) in TESTLER.items():
        v = [d["dersler"][kod]["net"] for d in denemeler if kod in d["dersler"]]
        if v:
            dersler.append({"kod": kod, "oturum": ot, "ad": ad, "soru": soru, "son": v[-1], "onceki": v[-2] if len(v) > 1 else None,
                            "ort3": round(sum(v[-3:]) / len(v[-3:]), 2)})
    konu_d: dict[str, dict] = {}
    for ders, durum, n in konu:
        x = konu_d.setdefault(ders, {"biten": 0, "calisiyor": 0})
        if durum in ("bitti", "tekrar"):
            x["biten"] += n
        elif durum == "calisiyor":
            x["calisiyor"] += n
    try:
        from app.core.konu_servisi import etkin_konular
        etkin = etkin_konular(db, o.okul_id)
    except Exception:
        db.rollback()
        etkin = {k: v[2] for k, v in KONU_DERSLERI.items()}
    konu_ozet = [{"ad": f"{KONU_DERSLERI[k][0]} {KONU_DERSLERI[k][1]}", "biten": x["biten"], "calisiyor": x["calisiyor"],
                  "toplam": len(etkin.get(k, []))} for k, x in konu_d.items() if k in KONU_DERSLERI]
    kiyas = None
    if denemeler:
        try:
            from app.api.net_takibi import kiyas_hesapla
            k = kiyas_hesapla(db, o)
            if k.get("hedef") and k.get("toplam_ben") is not None:
                kiyas = k
        except Exception:
            db.rollback()
    return {"denemeler": denemeler, "oturumlar": oturumlar, "dersler": dersler, "konu": konu_ozet,
            "konu_biten": sum(x["biten"] for x in konu_ozet), "konu_calisiyor": sum(x["calisiyor"] for x in konu_ozet),
            "kiyas": kiyas}


def okul_net_ozeti(db: Session, ogrenci_idler: list) -> dict:
    """Okul / şube raporu için: deneme giren öğrenci sayısı, son TYT/AYT ortalamaları ve öğrenci başına son netler."""
    from app.core.sinav_yapisi import TESTLER
    if not ogrenci_idler:
        return {"ogrenci": {}, "giren": 0}
    try:
        rows = db.execute(text("""
            SELECT DISTINCT ON (ogrenci_id, oturum) ogrenci_id, oturum, toplam_net, dersler, tarih
              FROM ogrenci_denemeleri WHERE ogrenci_id = ANY(:ids)
             ORDER BY ogrenci_id, oturum, tarih DESC, id DESC"""), {"ids": list(ogrenci_idler)}).all()
        sayilar = dict(db.execute(text("SELECT ogrenci_id, count(*) FROM ogrenci_denemeleri WHERE ogrenci_id = ANY(:ids) "
                                       "GROUP BY ogrenci_id"), {"ids": list(ogrenci_idler)}).all())
    except Exception:
        db.rollback()
        return {"ogrenci": {}, "giren": 0}
    ogr: dict = {}
    ders_top: dict[str, list[float]] = {}
    for r in rows:
        x = ogr.setdefault(r.ogrenci_id, {"sayi": sayilar.get(r.ogrenci_id, 0)})
        x[r.oturum] = float(r.toplam_net)
        for kod, v in (r.dersler or {}).items():
            ders_top.setdefault(kod, []).append(float(v.get("net", 0)))
    def ort(ot):
        v = [x[ot] for x in ogr.values() if ot in x]
        return (round(sum(v) / len(v), 2), len(v)) if v else (None, 0)
    return {"ogrenci": ogr, "giren": len(ogr), "toplam_deneme": sum(sayilar.values()),
            "tyt": ort("TYT"), "ayt": ort("AYT"),
            "dersler": [{"ad": f"{TESTLER[k][0]} {TESTLER[k][1]}", "soru": TESTLER[k][2], "ort": round(sum(v) / len(v), 2), "n": len(v)}
                        for k, v in ders_top.items() if k in TESTLER]}
