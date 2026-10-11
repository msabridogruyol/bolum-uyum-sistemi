# -*- coding: utf-8 -*-
"""
[2026-10-11] Okul paneli → Rapor Merkezi → Rapor İndir → "Veli toplantısı sunumu (PowerPoint)".

GET /yonetim/okul/{okul_id}/veli-sunumu?sinif=&sube=   → .pptx (python-pptx; app/core/rapor/veli_sunumu.py)

Yetki: okul_yonetimi._okul_kapsami (okul yetkilisi yalnızca kendi okulu). Modül: 'gelismis_raporlar' — Rapor Merkezi'ndeki
toplu (veli toplantısı) raporlarıyla aynı kapı (raporlar._paket_kontrol); süper admin her zaman geçer. Her indirme denetim
kaydına yazılır. Test hesapları sayılmaz.

GİZLİLİK — sunum veli toplantısında topluca gösterilir:
  * öğrenci adı, öğrenci bazlı veri, kritik / erken uyarı listesi, net ve net sıralaması YOKTUR (hiç hesaplanmaz);
  * kişilik / değer puanına göre öğrenci sıralaması yoktur — yalnızca kapsamın ortalaması;
  * küçük grup gizleme (app/core/kucuk_grup.py): 5'ten az öğrenciye dayanan hiçbir toplu değer yazılmaz; dağılımlarda
    küçük kalemler "Diğer" altında birleşir; kapsamın toplam öğrencisi 5'ten azsa yalnızca genel anlatım slaytları üretilir.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_istatistik import _baslik, _sinif_sira, _yuzde, ogrenci_kumesi
from app.api.okul_yonetimi import _durum, _ilerleme, _okul_kapsami, sube_etiketi
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.kucuk_grup import EN_AZ_GRUP, gizle, grup_birlestir, kirilim_gizle, yeterli
from app.core.paketler import MODULLER, okul_modulleri
from app.models import AdminKullanici

router = APIRouter(prefix="/yonetim", tags=["Okul raporları"])
TR = ZoneInfo("Europe/Istanbul")
MIME_PPTX = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
REHBER_ANAHTAR = ("rehber", "psikolojik", "danışman", "danisman")


def _iletisim(okul) -> dict:
    kadro = [k for k in (getattr(okul, "kadro", None) or []) if isinstance(k, dict) and k.get("ad")]
    rehber = [k for k in kadro if any(a in (k.get("gorev") or "").lower() for a in REHBER_ANAHTAR)]
    return {
        "rehberler": [{"ad": k.get("ad"), "gorev": k.get("gorev"), "eposta": k.get("eposta"), "telefon": k.get("telefon")}
                      for k in rehber[:3]],
        "telefon": getattr(okul, "telefon", None), "eposta": getattr(okul, "eposta", None),
        "web": getattr(okul, "web", None), "adres": getattr(okul, "adres", None),
    }


def _takvim(db: Session, okul_id: int, sinif: str | None) -> list[dict]:
    bugun = datetime.now(TR).date()
    try:
        rows = db.execute(text("""
            SELECT baslik, aciklama, tur, baslangic, bitis, saat FROM takvim_etkinlikleri
             WHERE ogrenci_id IS NULL AND (okul_id = :ok OR okul_id IS NULL) AND COALESCE(bitis, baslangic) >= :b
               AND baslangic <= :s AND (hedef_sinif IS NULL OR CAST(:sf AS VARCHAR) IS NULL OR hedef_sinif = :sf)
             ORDER BY baslangic, (okul_id IS NULL), id LIMIT 6"""),
            {"ok": okul_id, "b": bugun, "s": bugun + timedelta(days=150), "sf": sinif}).mappings().all()
    except Exception:
        db.rollback()
        return []
    return [{"baslik": r["baslik"], "tarih": r["baslangic"], "bitis": r["bitis"], "saat": r["saat"]} for r in rows]


def veli_sunumu_verisi(db: Session, okul, okul_id: int, sinif: str | None, sube: str | None) -> dict:
    from app.api.listem import _alanlar
    from app.core.rapor.veri import okul_bilgisi

    moduller = set(okul_modulleri(db, okul_id or None))
    kume = ogrenci_kumesi(db, okul_id, sinif, sube)
    ogr, tum = kume["ogr"], kume["tum"]
    kapsam_tur = "sube" if kume["sube"] else "sinif" if kume["sinif"] else "okul"
    toplam = len(ogr)
    v: dict = {
        "okul": okul_bilgisi(db, okul_id or None), "kapsam": kume["etiket"], "kapsam_tur": kapsam_tur,
        "tarih": datetime.now(TR), "esik": EN_AZ_GRUP, "moduller": sorted(moduller),
        "toplu": yeterli(toplam),                     # False → yalnızca genel anlatım slaytları
        "iletisim": _iletisim(okul) if okul else {"rehberler": []},
        "takvim": _takvim(db, okul_id, kume["sinif"]) if "takvim" in moduller else [],
    }
    if not v["toplu"]:
        return v

    il_tum = _ilerleme(db, okul_id)
    il = {o.id: il_tum.get(o.id) or {} for o in ogr}
    durum = {o.id: _durum(o, il[o.id])[0] for o in ogr}
    tamam_tur = {i: x["tur_id"] for i, x in il.items() if x.get("durum") == "tamamlandi" and x.get("tur_id")}
    tamamlayan = len(tamam_tur)
    baslayan = sum(1 for k in durum.values() if k in ("tamamlandi", "devam"))
    hedef_secen = sum(1 for x in il.values() if x.get("hedef"))

    # ---------------------------------------------------------------- katılım (toplam ≥ 5 olduğu için oranlar gösterilebilir)
    dagilim = grup_birlestir({"Tamamladı": tamamlayan, "Devam ediyor": baslayan - tamamlayan,
                              "Henüz başlamadı": toplam - baslayan}, "ad", "sayi", diger_etiketi="Diğer")
    v["katilim"] = {
        "toplam": toplam, "tamamlayan": gizle(tamamlayan, toplam), "tamamlama_orani": gizle(_yuzde(tamamlayan, toplam), toplam),
        "baslama_orani": gizle(_yuzde(baslayan, toplam), toplam),
        "dagilim": [x for x in dagilim if x["sayi"] is not None and x["sayi"] > 0],
    }
    # alt kırılım: okul → sınıf düzeyleri, sınıf düzeyi → şubeler (şube kapsamında yok)
    if kapsam_tur != "sube":
        grup = defaultdict(lambda: [0, 0])
        for o in ogr:
            if not o.sinif or o.sinif in ("Mezun", "Aday"):
                continue
            k = (_sinif_sira(o.sinif), "" if kapsam_tur == "okul" else (o.sube or ""),
                 o.sinif if kapsam_tur == "okul" else sube_etiketi(o.sinif, o.sube))
            grup[k][0] += 1
            grup[k][1] += durum[o.id] == "tamamlandi"
        satir = [{"ad": k[2], "ogrenci": n, "oran": _yuzde(t, n)} for k, (n, t) in sorted(grup.items())]
        kirilim_gizle(satir, ["oran"])
        v["katilim"]["kirilim"] = [s for s in satir if s.get("oran") is not None]
        v["katilim"]["kirilim_gizli"] = sum(1 for s in satir if s.get("gizli"))
        v["katilim"]["kirilim_adi"] = "Sınıf düzeyi" if kapsam_tur == "okul" else "Şube"

    v["profil_yeterli"] = yeterli(tamamlayan)
    # ---------------------------------------------------------------- öne çıkan özellikler (kapsam ortalaması; öğrenci sıralaması YOK)
    if v["profil_yeterli"]:
        # duygusal hassasiyet (P4) ve eşleşme dışı özellikler veli sunumunda yer almaz (psikolojik ayrıntı)
        from app.core.katman_servisi import parametre_oku
        haric = sorted({"P4"} | {x.strip() for x in (parametre_oku(db, "eslesme_disi_degiskenler", "P4") or "").split(",") if x.strip()})
        sql = """SELECT d.ad, avg(s.puan) AS ort, count(DISTINCT s.ogrenci_id) AS n FROM ogrenci_degisken_skorlari s
                   JOIN degiskenler d ON d.id = s.degisken_id JOIN katmanlar k ON k.id = d.katman_id
                  WHERE s.tur_id = ANY(:t) AND d.dal_id IS NULL AND NOT k.kosullu_mu AND d.kod <> ALL(:haric) GROUP BY d.ad"""
        kapsam_ort = {r.ad: (float(r.ort), r.n) for r in db.execute(text(sql), {"t": list(tamam_tur.values()), "haric": haric}).all()}
        ilk5 = sorted(((a, o) for a, (o, n) in kapsam_ort.items() if yeterli(n)), key=lambda x: -x[1])[:5]
        okul_ort = {}
        if kapsam_tur != "okul":
            okul_tur = [x["tur_id"] for oid, x in il_tum.items() if x.get("durum") == "tamamlandi" and x.get("tur_id")
                        and oid in {o.id for o in tum}]
            if yeterli(len(okul_tur)):
                okul_ort = {r.ad: float(r.ort) for r in db.execute(text(sql), {"t": okul_tur, "haric": haric}).all() if yeterli(r.n)}
        v["guclu"] = [{"ad": a, "ort": round(o, 1), "okul": round(okul_ort[a], 1) if a in okul_ort else None} for a, o in ilk5]

        # ------------------------------------------------------------ alanlar ve bölümler (toplu)
        bolum_ad = {r.id: _baslik(r.ad) for r in db.execute(text("SELECT id, ad FROM bolumler")).all()}
        ilk = [x["ilk_bolum"] for i, x in il.items() if i in tamam_tur and x.get("ilk_bolum")]
        alan_of = {k: (a.get("ust_alan") or "Diğer") for k, a in _alanlar(db, list(set(ilk))).items()}
        v["alanlar"] = grup_birlestir(Counter(alan_of.get(b, "Diğer") for b in ilk), "ad", "sayi", ilk_n=6)
        ilk10 = Counter()
        ust = defaultdict(set)
        for r in db.execute(text("""
            SELECT tur_id, bolum_id FROM (
                SELECT s.tur_id, s.bolum_id, row_number() OVER (PARTITION BY s.tur_id ORDER BY s.toplam_uyum DESC) AS sira
                  FROM ogrenci_bolum_uyum_skorlari s WHERE s.tur_id = ANY(:t)) x WHERE sira <= 10"""),
                {"t": list(tamam_tur.values())}).all():
            ilk10[r.bolum_id] += 1
            ust[r.tur_id].add(r.bolum_id)
        v["bolumler"] = [{"ad": bolum_ad.get(b, "?"), "sayi": n, "oran": _yuzde(n, tamamlayan)}
                         for b, n in ilk10.most_common(12) if yeterli(n)][:6]
        hedefli = {i: x["hedef"] for i, x in il.items() if x.get("hedef") and i in tamam_tur}
        uyumlu = sum(1 for i, b in hedefli.items() if b in ust[tamam_tur[i]])
        v["hedef"] = {"secen": gizle(hedef_secen, hedef_secen), "oran": gizle(_yuzde(hedef_secen, toplam), hedef_secen),
                      "ilk10_oran": gizle(_yuzde(uyumlu, len(hedefli)), len(hedefli)),
                      "hedefli": len(hedefli)}
        h_alan = _alanlar(db, list(set(hedefli.values()))) if hedefli else {}
        hedef_alan = Counter((h_alan.get(b) or {}).get("ust_alan") or "Diğer" for b in hedefli.values())
        v["hedef"]["alanlar"] = [x for x in grup_birlestir(hedef_alan, "ad", "sayi", ilk_n=4) if x["sayi"] is not None]
    else:
        v["hedef"] = {"secen": gizle(hedef_secen, hedef_secen), "oran": gizle(_yuzde(hedef_secen, toplam), hedef_secen)}

    # ---------------------------------------------------------------- koçluk ve İş Hayatı (yalnızca toplu sayılar, ≥ 5)
    ids = [o.id for o in ogr]
    ek: dict = {}
    if "kocluk" in moduller and ids:
        try:
            adim = db.execute(text("SELECT count(DISTINCT ogrenci_id) FROM ogrenci_gelisim_adim_durumu "
                                   "WHERE ogrenci_id = ANY(:i) AND durum = 'tamamlandi'"), {"i": ids}).scalar() or 0
            gorev = db.execute(text("SELECT count(DISTINCT ogrenci_id) FROM ogrenci_haftalik_gorev "
                                    "WHERE ogrenci_id = ANY(:i) AND durum = 'tamamlandi'"), {"i": ids}).scalar() or 0
            sim = db.execute(text("SELECT count(*), count(DISTINCT ogrenci_id) FROM simulasyon_sonuclari WHERE ogrenci_id = ANY(:i)"),
                             {"i": ids}).first()
            ek["kocluk"] = {"adim": gizle(adim, adim), "gorev": gizle(gorev, gorev),
                            "simulasyon": gizle(sim[0] or 0, sim[1] or 0), "simulasyon_ogr": gizle(sim[1] or 0, sim[1] or 0)}
        except Exception:
            db.rollback()
            ek["kocluk"] = {}
    if "is_hayati" in moduller:
        ek["is_hayati"] = {}
    v["etkinlik"] = ek
    return v


@router.get("/okul/{okul_id}/veli-sunumu")
def veli_sunumu(okul_id: int, sinif: str | None = None, sube: str | None = None,
                db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.raporlar import _dosya_adi
    from app.core.rapor.veli_sunumu import veli_sunumu_pptx
    okul = _okul_kapsami(db, yon, okul_id)
    if yon.rol != "super_admin" and "gelismis_raporlar" not in okul_modulleri(db, okul_id or None):
        raise HTTPException(status_code=403, detail=f"“{MODULLER['gelismis_raporlar']['ad']}” okulunuzun paketinde yer almıyor.")
    v = veli_sunumu_verisi(db, okul, okul_id, sinif, sube)
    icerik = veli_sunumu_pptx(v)
    denetim_yaz(db, yon, "rapor_indir", "okullar", okul_id,
                f"Veli toplantısı sunumu ({v['kapsam']}{'' if v['toplu'] else ', yalnızca genel slaytlar'})", okul_id or None)
    db.commit()
    ad = _dosya_adi("Veli_Toplantisi", okul.ad if okul else "Okul_harici",
                                             v["kapsam"] if v["kapsam_tur"] != "okul" else None, date.today().strftime("%Y%m%d"))
    return Response(content=icerik, media_type=MIME_PPTX,
                    headers={"Content-Disposition": f'attachment; filename="{ad}.pptx"', "Cache-Control": "no-store"})
