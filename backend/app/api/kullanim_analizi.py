# -*- coding: utf-8 -*-
"""
[2026-11-11] Kullanım analizi: kim, hangi menüde, ne kadar süre geçiriyor. Öğrenciler, okul yetkilileri ve süper
adminler ayrı; okul okul ve toplam. Raporu yalnızca süper admin görür.

Süre nasıl ölçülür (frontend/src/yardimci/kullanimIzleyici.js):
  * aktif süre — sekme ekranda VE kişi son 2 dakikada dokundu / tıkladı / yazdı / kaydırdı. Raporların ana ölçüsü.
  * açık süre  — sekme ekranda (kişi etkin olmasa da). Aktif ≤ açık.
  * ziyaret    — menüye (ya da alt sekmeye) giriş sayısı.
  * oturum     — bir tarayıcı sekmesinde 30 dakikadan uzun ara verilmeden süren kullanım.
Tarayıcı dakikada bir ve sekme kapanırken gönderir; sunucu (oturum, menü, alt sekme, saat dilimi) başına toplar.

Uç noktalar:
  POST /ogrenci/kullanim                       öğrenci sürelerini yazar
  POST /yonetim/kullanim                       okul yetkilisi / süper admin sürelerini yazar
  GET  /admin/kullanim-analizi                 genel tablo: özet, menüler, okullar, günlük seyir, gün × saat, cihaz, sınıf
  GET  /admin/kullanim-analizi/kullanicilar    kişi listesi (hiç kullanmayanlar dahil), sıralı ve sayfalı
  GET  /admin/kullanim-analizi/kullanici       tek kişinin ayrıntısı: menüler, günler, saatler, oturumlar
  GET  /admin/kullanim-analizi/csv             menüler / okullar / kullanıcılar / günlük / sınıflar dışa aktarımı
Test hesapları ve demo okullar varsayılan olarak hesaba katılmaz (test_dahil=true ile katılır).
"""
from __future__ import annotations

import csv
import io
import statistics
import uuid
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_admin, get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.database import get_db
from app.models import AdminKullanici, Ogrenci
from app.schemas.girdi import GirdiModeli

ogrenci_router = APIRouter(prefix="/ogrenci/kullanim", tags=["Kullanım süresi"])
yonetim_router = APIRouter(prefix="/yonetim/kullanim", tags=["Kullanım süresi"])
router = APIRouter(prefix="/admin/kullanim-analizi", tags=["Yönetim — Kullanım Analizi"])

_TR = ZoneInfo("Europe/Istanbul")
TIPLER = ("ogrenci", "okul_yetkilisi", "super_admin")
TIP_ETIKET = {"ogrenci": "Öğrenci", "okul_yetkilisi": "Okul yetkilisi", "super_admin": "Süper admin"}
DILIM_EN_FAZLA_SN = 3600   # bir (oturum, menü, alt sekme) satırı bir saat dilimidir: 3600 sn'yi aşamaz
CIHAZ_ETIKET = {"mobil": "Telefon", "tablet": "Tablet", "masaustu": "Bilgisayar", None: "Bilinmiyor"}


# ============================================================================ yazım
class KullanimKaydi(GirdiModeli):
    menu_kod: str = Field(pattern=r"^[a-z0-9_\-]{1,60}$")
    menu_ad: str | None = Field(None, max_length=120)
    alt_kod: str = Field("", pattern=r"^[a-z0-9_\-]{0,60}$")
    alt_ad: str | None = Field(None, max_length=120)
    aktif_sn: int = Field(0, ge=0, le=DILIM_EN_FAZLA_SN)
    acik_sn: int = Field(0, ge=0, le=DILIM_EN_FAZLA_SN)
    ziyaret: int = Field(0, ge=0, le=500)


class KullanimGovdesi(GirdiModeli):
    oturum_id: uuid.UUID
    cihaz: str | None = Field(None, pattern="^(mobil|tablet|masaustu)$")
    kayitlar: list[KullanimKaydi] = Field(default_factory=list, max_length=80)


_YAZ_SQL = text("""
INSERT INTO kullanim_sureleri (saat, kullanici_tipi, ogrenci_id, yonetici_id, okul_id, test_hesabi, oturum_id, cihaz,
                               menu_kod, menu_ad, alt_kod, alt_ad, aktif_sn, acik_sn, ziyaret, ilk_zaman, son_zaman)
VALUES (date_trunc('hour', now()), :tip, CAST(:ogrenci_id AS uuid), CAST(:yonetici_id AS uuid), :okul_id, :test,
        CAST(:oturum_id AS uuid), :cihaz, :menu_kod, :menu_ad, :alt_kod, :alt_ad, :aktif, :acik, :ziyaret, now(), now())
ON CONFLICT (oturum_id, menu_kod, alt_kod, saat) DO UPDATE SET
    aktif_sn = LEAST(kullanim_sureleri.aktif_sn + EXCLUDED.aktif_sn, 3600),
    acik_sn = LEAST(kullanim_sureleri.acik_sn + EXCLUDED.acik_sn, 3600),
    ziyaret = kullanim_sureleri.ziyaret + EXCLUDED.ziyaret,
    menu_ad = COALESCE(EXCLUDED.menu_ad, kullanim_sureleri.menu_ad),
    alt_ad = COALESCE(EXCLUDED.alt_ad, kullanim_sureleri.alt_ad),
    cihaz = COALESCE(EXCLUDED.cihaz, kullanim_sureleri.cihaz),
    son_zaman = now()
WHERE kullanim_sureleri.ogrenci_id IS NOT DISTINCT FROM EXCLUDED.ogrenci_id
  AND kullanim_sureleri.yonetici_id IS NOT DISTINCT FROM EXCLUDED.yonetici_id
""")


def _kaydet(db: Session, govde: KullanimGovdesi, tip: str, ogrenci_id=None, yonetici_id=None, okul_id=None, test=False) -> int:
    birlesik: dict[tuple, dict] = {}
    for k in govde.kayitlar:
        anahtar = (k.menu_kod, k.alt_kod or "")
        b = birlesik.setdefault(anahtar, {"menu_ad": None, "alt_ad": None, "aktif": 0, "acik": 0, "ziyaret": 0})
        b["menu_ad"] = (k.menu_ad or "").strip()[:120] or b["menu_ad"]
        b["alt_ad"] = (k.alt_ad or "").strip()[:120] or b["alt_ad"]
        b["aktif"] += k.aktif_sn
        b["acik"] += max(k.acik_sn, k.aktif_sn)     # aktif süre açık sürenin parçasıdır
        b["ziyaret"] += k.ziyaret
    satirlar = []
    for (menu, alt), b in birlesik.items():
        if not (b["aktif"] or b["acik"] or b["ziyaret"]):
            continue
        satirlar.append({
            "tip": tip, "ogrenci_id": str(ogrenci_id) if ogrenci_id else None,
            "yonetici_id": str(yonetici_id) if yonetici_id else None, "okul_id": okul_id, "test": bool(test),
            "oturum_id": str(govde.oturum_id), "cihaz": govde.cihaz, "menu_kod": menu, "menu_ad": b["menu_ad"],
            "alt_kod": alt, "alt_ad": b["alt_ad"], "aktif": min(b["aktif"], DILIM_EN_FAZLA_SN),
            "acik": min(b["acik"], DILIM_EN_FAZLA_SN), "ziyaret": b["ziyaret"],
        })
    if satirlar:
        db.execute(_YAZ_SQL, satirlar)
        db.commit()
    return len(satirlar)


@ogrenci_router.post("")
def ogrenci_kullanim(govde: KullanimGovdesi, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return {"yazilan": _kaydet(db, govde, "ogrenci", ogrenci_id=o.id, okul_id=o.okul_id, test=o.test_hesabi)}


@yonetim_router.post("")
def yonetim_kullanim(govde: KullanimGovdesi, db: Session = Depends(get_db), h: AdminKullanici = Depends(get_mevcut_yonetim)):
    return {"yazilan": _kaydet(db, govde, h.rol, yonetici_id=h.id,
                               okul_id=h.okul_id if h.rol == "okul_yetkilisi" else None, test=h.test_hesabi)}


# ============================================================================ süzgeç
@dataclass
class Suzgec:
    bas: date
    bit: date
    okul: int | None        # None = tüm okullar, 0 = okul harici öğrenciler
    test_dahil: bool

    @property
    def gun_sayisi(self) -> int:
        return (self.bit - self.bas).days + 1

    def p(self, **ek) -> dict:
        d = {"bas": datetime.combine(self.bas, time.min, _TR), "bit": datetime.combine(self.bit + timedelta(days=1), time.min, _TR)}
        if self.okul:
            d["okul"] = self.okul
        d.update(ek)
        return d

    def onceki(self) -> "Suzgec":
        n = self.gun_sayisi
        return Suzgec(self.bas - timedelta(days=n), self.bas - timedelta(days=1), self.okul, self.test_dahil)

    def k(self, a: str = "k", tip: bool = False, okul: bool = True) -> str:
        """Süre satırları için WHERE koşulu. okul=False: okul süzgeci uygulanmaz (kişi listesinde okul, hesabın okuludur)."""
        s = [f"{a}.saat >= :bas", f"{a}.saat < :bit"]
        if okul and self.okul is not None:
            s.append(f"{a}.kullanici_tipi <> 'super_admin'")
            s.append(f"{a}.okul_id IS NULL" if self.okul == 0 else f"{a}.okul_id = :okul")
        if not self.test_dahil:
            s.append(f"NOT {a}.test_hesabi AND NOT EXISTS (SELECT 1 FROM okullar d WHERE d.id = {a}.okul_id AND d.demo)")
        if tip:
            s.append(f"{a}.kullanici_tipi = :tip")
        return " AND ".join(s)

    def hesap(self, a: str, okul_sutunu: str = "okul_id") -> str:
        """Kayıtlı hesap tabloları (ogrenciler / admin_kullanicilar) için koşul; `ok` = okullar birleşimi."""
        s = ["TRUE"]
        if self.okul is not None:
            s.append(f"{a}.{okul_sutunu} IS NULL" if self.okul == 0 else f"{a}.{okul_sutunu} = :okul")
        if not self.test_dahil:
            s.append(f"NOT {a}.test_hesabi AND NOT COALESCE(ok.demo, false)")
        return " AND ".join(s)


def _suzgec(
    bas: date | None = None, bit: date | None = None, okul_id: int | None = Query(None, ge=0), test_dahil: bool = False,
) -> Suzgec:
    bugun = datetime.now(_TR).date()
    bit = bit or bugun
    bas = bas or (bit - timedelta(days=29))
    if bit < bas:
        raise HTTPException(status_code=400, detail="Bitiş tarihi başlangıçtan önce olamaz.")
    if (bit - bas).days > 730:
        raise HTTPException(status_code=400, detail="Dönem en fazla 2 yıl olabilir.")
    return Suzgec(bas, bit, okul_id, test_dahil)


_KID = "COALESCE(k.ogrenci_id, k.yonetici_id)"
_GUN = "((k.saat AT TIME ZONE 'Europe/Istanbul')::date)"


def _oran(pay, payda):
    return round(100.0 * pay / payda, 1) if payda else None


def _ort(t, n):
    return round(t / n) if n else 0


def _kovala(degerler: list[int], sinirlar: list[tuple[str, int, int | None]]) -> list[dict]:
    out = []
    for ad, alt, ust in sinirlar:
        out.append({"ad": ad, "sayi": sum(1 for v in degerler if v >= alt and (ust is None or v < ust))})
    return out


KISI_KOVALARI = [("5 dk'dan az", 0, 300), ("5–15 dk", 300, 900), ("15–30 dk", 900, 1800), ("30–60 dk", 1800, 3600),
                 ("1–2 saat", 3600, 7200), ("2–5 saat", 7200, 18000), ("5 saat ve üstü", 18000, None)]
OTURUM_KOVALARI = [("1 dk'dan az", 0, 60), ("1–5 dk", 60, 300), ("5–15 dk", 300, 900), ("15–30 dk", 900, 1800),
                   ("30–60 dk", 1800, 3600), ("1 saat ve üstü", 3600, None)]


def _kayitlilar(db: Session, f: Suzgec):
    """(tip, okul_id) → kayıtlı hesap sayısı; öğrencilerde ayrıca sınıf → sayı."""
    p = f.p()
    kayitli: dict[tuple, int] = {}
    sinif: dict[str, int] = {}
    for r in db.execute(text(f"""
            SELECT o.okul_id, o.sinif, count(*) FROM ogrenciler o LEFT JOIN okullar ok ON ok.id = o.okul_id
             WHERE {f.hesap('o')} GROUP BY 1, 2"""), p):
        kayitli[("ogrenci", r[0])] = kayitli.get(("ogrenci", r[0]), 0) + r[2]
        sinif[r[1] or "Belirtilmemiş"] = sinif.get(r[1] or "Belirtilmemiş", 0) + r[2]
    for r in db.execute(text(f"""
            SELECT a.rol, a.okul_id, count(*) FROM admin_kullanicilar a LEFT JOIN okullar ok ON ok.id = a.okul_id
             WHERE a.aktif_mi AND {f.hesap('a')} {"AND a.rol = 'okul_yetkilisi'" if f.okul is not None else ''}
             GROUP BY 1, 2"""), p):
        kayitli[(r[0], r[1])] = kayitli.get((r[0], r[1]), 0) + r[2]
    return kayitli, sinif


def _kisi_ozetleri(db: Session, f: Suzgec):
    return db.execute(text(f"""
        SELECT k.kullanici_tipi AS tip, {_KID} AS kid, sum(k.aktif_sn) AS aktif, sum(k.acik_sn) AS acik,
               sum(k.ziyaret) AS ziyaret, count(DISTINCT k.oturum_id) AS oturum, count(DISTINCT {_GUN}) AS gun,
               max(k.son_zaman) AS son, (array_agg(k.okul_id ORDER BY k.son_zaman DESC))[1] AS okul_id
          FROM kullanim_sureleri k WHERE {f.k()} GROUP BY 1, 2"""), f.p()).mappings().all()


def _analiz(db: Session, f: Suzgec) -> dict:
    p = f.p()
    kayitli, sinif_kayitli = _kayitlilar(db, f)
    kisiler = _kisi_ozetleri(db, f)
    okullar = {r[0]: {"ad": r[1], "demo": bool(r[2])} for r in db.execute(text("SELECT id, ad, demo FROM okullar"))}

    # ---------------------------------------------------------------- oturumlar
    oturumlar: dict[str, list[int]] = {t: [] for t in TIPLER}
    for r in db.execute(text(f"""
            SELECT k.kullanici_tipi, sum(k.aktif_sn) FROM kullanim_sureleri k WHERE {f.k()}
             GROUP BY k.kullanici_tipi, k.oturum_id"""), p):
        oturumlar.setdefault(r[0], []).append(int(r[1] or 0))

    # ---------------------------------------------------------------- günlük aktif kişi (ortalama günlük aktif kullanıcı)
    gunluk: dict[date, dict] = {}
    for r in db.execute(text(f"""
            SELECT {_GUN} AS gun, k.kullanici_tipi, sum(k.aktif_sn), count(DISTINCT {_KID})
              FROM kullanim_sureleri k WHERE {f.k()} AND k.aktif_sn > 0 GROUP BY 1, 2"""), p):
        g = gunluk.setdefault(r[0], {})
        g[r[1]] = (int(r[2] or 0), int(r[3] or 0))

    # ---------------------------------------------------------------- önceki dönem
    fo = f.onceki()
    onceki = {r[0]: {"toplam_aktif_sn": int(r[1] or 0), "aktif_kullanici": int(r[2] or 0)} for r in db.execute(text(f"""
            SELECT k.kullanici_tipi, sum(k.aktif_sn), count(DISTINCT {_KID}) FILTER (WHERE k.aktif_sn > 0)
              FROM kullanim_sureleri k WHERE {fo.k()} GROUP BY 1"""), fo.p())}

    # ---------------------------------------------------------------- özet
    def ozet_yap(tipler: tuple[str, ...]) -> dict:
        kl = [r for r in kisiler if r["tip"] in tipler and (r["aktif"] or 0) > 0]
        akt = [int(r["aktif"]) for r in kl]
        ot = [s for t in tipler for s in oturumlar.get(t, [])]
        kay = sum(v for (t, _), v in kayitli.items() if t in tipler)
        top = sum(akt)
        gun_kisi = [sum(g.get(t, (0, 0))[1] for t in tipler) for g in gunluk.values()]
        onc = {"toplam_aktif_sn": sum(onceki.get(t, {}).get("toplam_aktif_sn", 0) for t in tipler),
               "aktif_kullanici": sum(onceki.get(t, {}).get("aktif_kullanici", 0) for t in tipler)}
        return {
            "kayitli": kay, "aktif_kullanici": len(kl), "katilim_orani": _oran(len(kl), kay),
            "hic_kullanmayan": max(0, kay - len(kl)),
            "toplam_aktif_sn": top, "toplam_acik_sn": sum(int(r["acik"] or 0) for r in kl),
            "kisi_basi_sn": _ort(top, len(kl)), "medyan_kisi_sn": round(statistics.median(akt)) if akt else 0,
            "oturum": len(ot), "ort_oturum_sn": _ort(sum(ot), len(ot)),
            "medyan_oturum_sn": round(statistics.median(ot)) if ot else 0,
            "kisa_oturum_orani": _oran(sum(1 for s in ot if s < 60), len(ot)),
            "kisi_basi_oturum": round(len(ot) / len(kl), 1) if kl else 0,
            "kisi_basi_aktif_gun": round(sum(int(r["gun"] or 0) for r in kl) / len(kl), 1) if kl else 0,
            "ort_gunluk_aktif_kisi": round(sum(gun_kisi) / f.gun_sayisi, 1),
            "ziyaret": sum(int(r["ziyaret"] or 0) for r in kl),
            "onceki": onc,
            "kisi_dagilimi": _kovala(akt, KISI_KOVALARI),
            "oturum_dagilimi": _kovala(ot, OTURUM_KOVALARI),
        }
    ozet = {t: ozet_yap((t,)) for t in TIPLER}
    ozet["yetkili"] = ozet_yap(("okul_yetkilisi", "super_admin"))
    ozet["toplam"] = ozet_yap(TIPLER)

    # ---------------------------------------------------------------- menüler (menü ve alt sekme; tekil kişi ayrı ayrı)
    menuler: dict[str, dict[str, dict]] = {t: {} for t in TIPLER}
    for r in db.execute(text(f"""
            SELECT k.kullanici_tipi AS tip, k.menu_kod, COALESCE(k.alt_kod, '') AS alt_kod, GROUPING(k.alt_kod) AS menu_satiri,
                   (array_agg(k.menu_ad ORDER BY k.son_zaman DESC) FILTER (WHERE k.menu_ad IS NOT NULL))[1] AS menu_ad,
                   (array_agg(k.alt_ad ORDER BY k.son_zaman DESC) FILTER (WHERE k.alt_ad IS NOT NULL))[1] AS alt_ad,
                   sum(k.aktif_sn) AS aktif, sum(k.ziyaret) AS ziyaret,
                   count(DISTINCT {_KID}) FILTER (WHERE k.aktif_sn > 0) AS kisi
              FROM kullanim_sureleri k WHERE {f.k()}
             GROUP BY GROUPING SETS ((k.kullanici_tipi, k.menu_kod, k.alt_kod), (k.kullanici_tipi, k.menu_kod))"""), p).mappings():
        m = menuler.setdefault(r["tip"], {}).setdefault(r["menu_kod"], {"menu_kod": r["menu_kod"], "menu_ad": None, "altlar": []})
        if r["menu_satiri"]:
            m.update({"menu_ad": r["menu_ad"] or r["menu_kod"], "aktif_sn": int(r["aktif"] or 0),
                      "ziyaret": int(r["ziyaret"] or 0), "kullanici": int(r["kisi"] or 0)})
        elif r["alt_kod"]:
            m["altlar"].append({"alt_kod": r["alt_kod"], "alt_ad": r["alt_ad"] or r["alt_kod"].replace("-", " ").replace("_", " ").capitalize(),
                                "aktif_sn": int(r["aktif"] or 0), "ziyaret": int(r["ziyaret"] or 0), "kullanici": int(r["kisi"] or 0)})
    menu_cikti = {}
    for t in TIPLER:
        top = sum(m.get("aktif_sn", 0) for m in menuler[t].values())
        n_aktif = ozet[t]["aktif_kullanici"]
        l = []
        for m in menuler[t].values():
            a = m.get("aktif_sn", 0)
            alts = sorted(m["altlar"], key=lambda x: -x["aktif_sn"])
            for x in alts:
                x["pay_menude"] = _oran(x["aktif_sn"], a)
            l.append({**m, "altlar": alts, "pay": _oran(a, top), "yayginlik": _oran(m.get("kullanici", 0), n_aktif),
                      "kisi_basi_sn": _ort(a, m.get("kullanici", 0)), "ort_ziyaret_sn": _ort(a, m.get("ziyaret", 0))})
        menu_cikti[t] = sorted(l, key=lambda x: -x.get("aktif_sn", 0))

    # ---------------------------------------------------------------- okullar
    okul_menu: dict[tuple, tuple[str, int]] = {}
    for r in db.execute(text(f"""
            SELECT k.kullanici_tipi, k.okul_id, k.menu_kod,
                   (array_agg(k.menu_ad ORDER BY k.son_zaman DESC) FILTER (WHERE k.menu_ad IS NOT NULL))[1], sum(k.aktif_sn)
              FROM kullanim_sureleri k WHERE {f.k()} AND k.kullanici_tipi <> 'super_admin' GROUP BY 1, 2, 3"""), p):
        anahtar = (r[0], r[1])
        if anahtar not in okul_menu or (r[4] or 0) > okul_menu[anahtar][1]:
            okul_menu[anahtar] = (r[3] or r[2], int(r[4] or 0))
    okul_satir: dict = {}

    def okul_kaydi(oid):
        if oid not in okul_satir:
            bilgi = okullar.get(oid) or {}
            okul_satir[oid] = {"okul_id": oid if oid is not None else 0,
                               "okul_ad": bilgi.get("ad") or ("Okul harici öğrenciler" if oid is None else f"Okul #{oid}"),
                               "demo": bool(bilgi.get("demo")),
                               **{t: {"kayitli": 0, "aktif": 0, "toplam_sn": 0, "oturum": 0, "aktif_gun": 0, "son": None}
                                  for t in ("ogrenci", "okul_yetkilisi")}}
        return okul_satir[oid]
    for (t, oid), n in kayitli.items():
        if t in ("ogrenci", "okul_yetkilisi"):
            okul_kaydi(oid)[t]["kayitli"] += n
    for r in kisiler:
        if r["tip"] not in ("ogrenci", "okul_yetkilisi") or not (r["aktif"] or 0):
            continue
        d = okul_kaydi(r["okul_id"])[r["tip"]]
        d["aktif"] += 1
        d["toplam_sn"] += int(r["aktif"])
        d["oturum"] += int(r["oturum"] or 0)
        d["aktif_gun"] += int(r["gun"] or 0)
        d["son"] = max(filter(None, [d["son"], r["son"]]), default=None)
    okul_cikti = []
    for oid, s in okul_satir.items():
        if f.okul is not None and (oid or 0) != f.okul:
            continue
        if not f.test_dahil and s["demo"]:
            continue
        for t in ("ogrenci", "okul_yetkilisi"):
            d = s[t]
            d["katilim_orani"] = _oran(d["aktif"], d["kayitli"])
            d["kisi_basi_sn"] = _ort(d["toplam_sn"], d["aktif"])
            d["kisi_basi_aktif_gun"] = round(d["aktif_gun"] / d["aktif"], 1) if d["aktif"] else 0
            d["en_cok_menu"] = (okul_menu.get((t, oid)) or (None,))[0]
            d["son"] = d["son"].isoformat() if d["son"] else None
        okul_cikti.append(s)
    okul_cikti.sort(key=lambda s: (-(s["ogrenci"]["toplam_sn"] + s["okul_yetkilisi"]["toplam_sn"]), s["okul_ad"]))

    # ---------------------------------------------------------------- günlük seyir (boş günler 0)
    gunler = []
    g = f.bas
    while g <= f.bit:
        v = gunluk.get(g, {})
        gunler.append({"gun": g.isoformat(), **{f"{t}_sn": v.get(t, (0, 0))[0] for t in TIPLER},
                       **{f"{t}_kisi": v.get(t, (0, 0))[1] for t in TIPLER}})
        g += timedelta(days=1)

    # ---------------------------------------------------------------- gün × saat
    isi = {t: [[0] * 24 for _ in range(7)] for t in TIPLER}
    for r in db.execute(text(f"""
            SELECT k.kullanici_tipi, extract(isodow FROM k.saat AT TIME ZONE 'Europe/Istanbul')::int,
                   extract(hour FROM k.saat AT TIME ZONE 'Europe/Istanbul')::int, sum(k.aktif_sn)
              FROM kullanim_sureleri k WHERE {f.k()} GROUP BY 1, 2, 3"""), p):
        if r[0] in isi:
            isi[r[0]][r[1] - 1][r[2]] = int(r[3] or 0)

    # ---------------------------------------------------------------- cihaz
    cihaz = {t: [] for t in TIPLER}
    for r in db.execute(text(f"""
            SELECT k.kullanici_tipi, k.cihaz, sum(k.aktif_sn), count(DISTINCT {_KID}) FILTER (WHERE k.aktif_sn > 0)
              FROM kullanim_sureleri k WHERE {f.k()} GROUP BY 1, 2 ORDER BY 3 DESC"""), p):
        if r[0] in cihaz:
            cihaz[r[0]].append({"cihaz": r[1] or "bilinmiyor", "ad": CIHAZ_ETIKET.get(r[1], r[1]),
                                "aktif_sn": int(r[2] or 0), "kullanici": int(r[3] or 0)})

    # ---------------------------------------------------------------- sınıflar (öğrencinin bugünkü sınıfı)
    sinif_kullanim = {}
    for r in db.execute(text(f"""
            SELECT COALESCE(o.sinif, 'Belirtilmemiş'), count(DISTINCT k.ogrenci_id) FILTER (WHERE k.aktif_sn > 0), sum(k.aktif_sn)
              FROM kullanim_sureleri k JOIN ogrenciler o ON o.id = k.ogrenci_id
             WHERE {f.k()} AND k.kullanici_tipi = 'ogrenci' GROUP BY 1"""), p):
        sinif_kullanim[r[0]] = (int(r[1] or 0), int(r[2] or 0))
    siniflar = []
    for ad in sorted(set(sinif_kayitli) | set(sinif_kullanim), key=_sinif_sirasi):
        aktif, sn = sinif_kullanim.get(ad, (0, 0))
        kay = sinif_kayitli.get(ad, 0)
        siniflar.append({"sinif": ad, "kayitli": kay, "aktif": aktif, "katilim_orani": _oran(aktif, kay),
                         "toplam_sn": sn, "kisi_basi_sn": _ort(sn, aktif)})

    # ---------------------------------------------------------------- en çok kullananlar
    en_cok = {}
    for t in TIPLER:
        ilk = sorted([r for r in kisiler if r["tip"] == t and (r["aktif"] or 0) > 0], key=lambda r: -r["aktif"])[:10]
        adlar = _adlar(db, t, [r["kid"] for r in ilk])
        en_cok[t] = [{"kullanici_id": str(r["kid"]), "ad": adlar.get(str(r["kid"]), "—"), "aktif_sn": int(r["aktif"]),
                      "oturum": int(r["oturum"] or 0), "okul_ad": (okullar.get(r["okul_id"]) or {}).get("ad")} for r in ilk]

    baslangic = db.execute(text("SELECT min(saat) FROM kullanim_sureleri")).scalar()
    return {
        "donem": {"bas": f.bas.isoformat(), "bit": f.bit.isoformat(), "gun": f.gun_sayisi,
                  "onceki_bas": fo.bas.isoformat(), "onceki_bit": fo.bit.isoformat()},
        "suzgec": {"okul_id": f.okul, "test_dahil": f.test_dahil},
        "olcum_baslangici": baslangic.isoformat() if baslangic else None,
        "ozet": ozet, "menuler": menu_cikti, "okullar": okul_cikti, "gunluk": gunler, "isi": isi, "cihaz": cihaz,
        "siniflar": siniflar, "en_cok": en_cok,
    }


def _sinif_sirasi(ad: str):
    import re
    m = re.match(r"\s*(\d+)", ad or "")
    return (0, int(m.group(1)), ad) if m else (1, 0 if ad == "Mezun" else 1, ad)


def _adlar(db: Session, tip: str, idler) -> dict[str, str]:
    idler = [str(i) for i in idler if i]
    if not idler:
        return {}
    tablo = "ogrenciler" if tip == "ogrenci" else "admin_kullanicilar"
    return {str(r[0]): r[1] for r in db.execute(
        text(f"SELECT id, ad_soyad FROM {tablo} WHERE id = ANY(CAST(:i AS uuid[]))"), {"i": idler})}


@router.get("")
def kullanim_analizi(f: Suzgec = Depends(_suzgec), db: Session = Depends(get_db), _a: AdminKullanici = Depends(get_mevcut_admin)):
    return _analiz(db, f)


# ============================================================================ kişi listesi
_SIRALAR = {
    "aktif_cok": "aktif DESC, ad", "aktif_az": "aktif ASC, ad", "son": "son DESC NULLS LAST, ad",
    "oturum": "oturum DESC, ad", "gun": "gun DESC, ad", "ad": "ad",
}


def _kisi_listesi_sql(f: Suzgec, tip: str, ara: str | None, sinif: str | None, yalniz: str) -> tuple[str, dict]:
    p = f.p(tip=tip)
    if tip == "ogrenci":
        tablo, kol, ek = "ogrenciler", "ogrenci_id", "x.sinif, x.sube, x.son_giris_zamani AS son_giris"
        kosul = [f.hesap("x")]
    else:
        tablo, kol, ek = "admin_kullanicilar", "yonetici_id", "NULL::text AS sinif, NULL::text AS sube, x.son_giris_zamani AS son_giris"
        kosul = ["x.aktif_mi", "x.rol = :tip", f.hesap("x") if tip == "okul_yetkilisi" or f.okul is None else "FALSE"]
    if ara:
        kosul.append("(x.ad_soyad ILIKE :ara OR x.email ILIKE :ara)"); p["ara"] = f"%{ara.strip()}%"
    if sinif and tip == "ogrenci":
        kosul.append("x.sinif = :sinif"); p["sinif"] = sinif
    if yalniz == "kullanan":
        kosul.append("COALESCE(u.aktif, 0) > 0")
    elif yalniz == "kullanmayan":
        kosul.append("COALESCE(u.aktif, 0) = 0")
    kk = f.k(tip=True, okul=False)
    sql = f"""
      WITH u AS (SELECT k.{kol} AS kid, sum(k.aktif_sn) AS aktif, sum(k.acik_sn) AS acik, sum(k.ziyaret) AS ziyaret,
                        count(DISTINCT k.oturum_id) AS oturum, count(DISTINCT {_GUN}) AS gun, max(k.son_zaman) AS son
                   FROM kullanim_sureleri k WHERE {kk} GROUP BY 1),
           m AS (SELECT DISTINCT ON (kid) kid, menu_ad FROM (
                   SELECT k.{kol} AS kid, k.menu_kod,
                          (array_agg(k.menu_ad ORDER BY k.son_zaman DESC) FILTER (WHERE k.menu_ad IS NOT NULL))[1] AS menu_ad,
                          sum(k.aktif_sn) AS s
                     FROM kullanim_sureleri k WHERE {kk} GROUP BY 1, 2) y ORDER BY kid, s DESC)
      SELECT x.id, x.ad_soyad AS ad, x.email, x.okul_id, ok.ad AS okul_ad, x.test_hesabi, {ek},
             COALESCE(u.aktif, 0) AS aktif, COALESCE(u.acik, 0) AS acik, COALESCE(u.ziyaret, 0) AS ziyaret,
             COALESCE(u.oturum, 0) AS oturum, COALESCE(u.gun, 0) AS gun, u.son, m.menu_ad AS en_cok_menu
        FROM {tablo} x LEFT JOIN okullar ok ON ok.id = x.okul_id
        LEFT JOIN u ON u.kid = x.id LEFT JOIN m ON m.kid = x.id
       WHERE {" AND ".join(kosul)}"""
    return sql, p


def _kisi_satiri(r) -> dict:
    return {
        "kullanici_id": str(r["id"]), "ad": r["ad"], "eposta": r["email"], "okul_id": r["okul_id"], "okul_ad": r["okul_ad"],
        "sinif": r["sinif"], "sube": r["sube"], "test_hesabi": bool(r["test_hesabi"]),
        "son_giris": r["son_giris"].isoformat() if r["son_giris"] else None,
        "aktif_sn": int(r["aktif"]), "acik_sn": int(r["acik"]), "ziyaret": int(r["ziyaret"]), "oturum": int(r["oturum"]),
        "aktif_gun": int(r["gun"]), "ort_oturum_sn": _ort(int(r["aktif"]), int(r["oturum"])),
        "son_kullanim": r["son"].isoformat() if r["son"] else None, "en_cok_menu": r["en_cok_menu"],
    }


@router.get("/kullanicilar")
def kullanicilar(
    f: Suzgec = Depends(_suzgec), tip: str = Query("ogrenci", pattern="^(ogrenci|okul_yetkilisi|super_admin)$"),
    ara: str | None = Query(None, max_length=100), sinif: str | None = Query(None, max_length=40),
    yalniz: str = Query("hepsi", pattern="^(hepsi|kullanan|kullanmayan)$"),
    siralama: str = Query("aktif_cok", pattern="^(" + "|".join(_SIRALAR) + ")$"),
    sayfa: int = Query(1, ge=1, le=100000), adet: int = Query(50, ge=10, le=200),
    db: Session = Depends(get_db), _a: AdminKullanici = Depends(get_mevcut_admin),
):
    sql, p = _kisi_listesi_sql(f, tip, ara, sinif, yalniz)
    toplam = db.execute(text(f"SELECT count(*) FROM ({sql}) s"), p).scalar() or 0
    satirlar = db.execute(text(f"SELECT * FROM ({sql}) s ORDER BY {_SIRALAR[siralama]} LIMIT :adet OFFSET :ofs"),
                          {**p, "adet": adet, "ofs": (sayfa - 1) * adet}).mappings().all()
    return {"toplam": toplam, "sayfa": sayfa, "adet": adet, "tip": tip, "kullanicilar": [_kisi_satiri(r) for r in satirlar]}


# ============================================================================ kişi ayrıntısı
@router.get("/kullanici")
def kullanici_ayrintisi(
    kullanici_id: uuid.UUID, tip: str = Query(..., pattern="^(ogrenci|okul_yetkilisi|super_admin)$"),
    bas: date | None = None, bit: date | None = None,
    db: Session = Depends(get_db), _a: AdminKullanici = Depends(get_mevcut_admin),
):
    f = _suzgec(bas, bit, None, True)          # kişi ayrıntısında okul / test süzgeci yok: o kişinin tüm kullanımı
    kol = "ogrenci_id" if tip == "ogrenci" else "yonetici_id"
    if tip == "ogrenci":
        kisi = db.execute(text("""SELECT o.id, o.ad_soyad AS ad, o.email, o.sinif, o.sube, o.okul_id, ok.ad AS okul_ad,
                                         o.son_giris_zamani AS son_giris, o.test_hesabi, NULL::text AS rol
                                    FROM ogrenciler o LEFT JOIN okullar ok ON ok.id = o.okul_id WHERE o.id = :i"""),
                          {"i": kullanici_id}).mappings().first()
    else:
        kisi = db.execute(text("""SELECT a.id, a.ad_soyad AS ad, a.email, NULL::text AS sinif, NULL::text AS sube, a.okul_id,
                                         ok.ad AS okul_ad, a.son_giris_zamani AS son_giris, a.test_hesabi, a.rol
                                    FROM admin_kullanicilar a LEFT JOIN okullar ok ON ok.id = a.okul_id
                                   WHERE a.id = :i AND a.rol = :t"""), {"i": kullanici_id, "t": tip}).mappings().first()
    if not kisi:
        raise HTTPException(status_code=404, detail="Kişi bulunamadı.")
    p = f.p(kid=str(kullanici_id))
    kk = f"k.saat >= :bas AND k.saat < :bit AND k.{kol} = CAST(:kid AS uuid)"
    menuler: dict[str, dict] = {}
    for r in db.execute(text(f"""
            SELECT k.menu_kod, COALESCE(k.alt_kod, '') AS alt_kod, GROUPING(k.alt_kod) AS menu_satiri,
                   (array_agg(k.menu_ad ORDER BY k.son_zaman DESC) FILTER (WHERE k.menu_ad IS NOT NULL))[1] AS menu_ad,
                   (array_agg(k.alt_ad ORDER BY k.son_zaman DESC) FILTER (WHERE k.alt_ad IS NOT NULL))[1] AS alt_ad,
                   sum(k.aktif_sn) AS aktif, sum(k.ziyaret) AS ziyaret, max(k.son_zaman) AS son
              FROM kullanim_sureleri k WHERE {kk}
             GROUP BY GROUPING SETS ((k.menu_kod, k.alt_kod), (k.menu_kod))"""), p).mappings():
        m = menuler.setdefault(r["menu_kod"], {"menu_kod": r["menu_kod"], "altlar": []})
        if r["menu_satiri"]:
            m.update({"menu_ad": r["menu_ad"] or r["menu_kod"], "aktif_sn": int(r["aktif"] or 0), "ziyaret": int(r["ziyaret"] or 0),
                      "son": r["son"].isoformat() if r["son"] else None})
        elif r["alt_kod"]:
            m["altlar"].append({"alt_kod": r["alt_kod"], "alt_ad": r["alt_ad"] or r["alt_kod"], "aktif_sn": int(r["aktif"] or 0),
                                "ziyaret": int(r["ziyaret"] or 0)})
    top = sum(m.get("aktif_sn", 0) for m in menuler.values())
    menu_l = []
    for m in sorted(menuler.values(), key=lambda x: -x.get("aktif_sn", 0)):
        m["altlar"].sort(key=lambda x: -x["aktif_sn"])
        menu_l.append({**m, "pay": _oran(m.get("aktif_sn", 0), top), "ort_ziyaret_sn": _ort(m.get("aktif_sn", 0), m.get("ziyaret", 0))})
    gunluk = {r[0]: int(r[1] or 0) for r in db.execute(text(
        f"SELECT {_GUN}, sum(k.aktif_sn) FROM kullanim_sureleri k WHERE {kk} GROUP BY 1"), p)}
    gunler, g = [], f.bas
    while g <= f.bit:
        gunler.append({"gun": g.isoformat(), "aktif_sn": gunluk.get(g, 0)})
        g += timedelta(days=1)
    saatler = [0] * 24
    for r in db.execute(text(f"""SELECT extract(hour FROM k.saat AT TIME ZONE 'Europe/Istanbul')::int, sum(k.aktif_sn)
                                   FROM kullanim_sureleri k WHERE {kk} GROUP BY 1"""), p):
        saatler[r[0]] = int(r[1] or 0)
    oturumlar = []
    for r in db.execute(text(f"""
            SELECT k.oturum_id, min(k.ilk_zaman) AS bas, max(k.son_zaman) AS bit, sum(k.aktif_sn) AS aktif,
                   max(k.cihaz) AS cihaz, count(DISTINCT k.menu_kod) AS menu_sayisi,
                   (array_agg(k.menu_ad ORDER BY k.aktif_sn DESC) FILTER (WHERE k.menu_ad IS NOT NULL)) AS menuler
              FROM kullanim_sureleri k WHERE {kk} GROUP BY 1 ORDER BY 2 DESC LIMIT 100"""), p).mappings():
        sirali = list(dict.fromkeys(r["menuler"] or []))
        oturumlar.append({"bas": r["bas"].isoformat(), "bit": r["bit"].isoformat(), "aktif_sn": int(r["aktif"] or 0),
                          "cihaz": CIHAZ_ETIKET.get(r["cihaz"], r["cihaz"]), "menu_sayisi": int(r["menu_sayisi"] or 0),
                          "menuler": sirali[:5]})
    ot_say = db.execute(text(f"SELECT count(DISTINCT k.oturum_id), count(DISTINCT {_GUN}), sum(k.ziyaret) FROM kullanim_sureleri k WHERE {kk}"), p).one()
    return {
        "kisi": {"kullanici_id": str(kisi["id"]), "ad": kisi["ad"], "eposta": kisi["email"], "tip": tip,
                 "tip_etiket": TIP_ETIKET[tip], "sinif": kisi["sinif"], "sube": kisi["sube"], "okul_ad": kisi["okul_ad"],
                 "son_giris": kisi["son_giris"].isoformat() if kisi["son_giris"] else None, "test_hesabi": bool(kisi["test_hesabi"])},
        "donem": {"bas": f.bas.isoformat(), "bit": f.bit.isoformat(), "gun": f.gun_sayisi},
        "ozet": {"toplam_aktif_sn": top, "oturum": int(ot_say[0] or 0), "aktif_gun": int(ot_say[1] or 0),
                 "ziyaret": int(ot_say[2] or 0), "ort_oturum_sn": _ort(top, int(ot_say[0] or 0)),
                 "gunluk_ort_sn": _ort(top, int(ot_say[1] or 0))},
        "menuler": menu_l, "gunluk": gunler, "saatler": saatler, "oturumlar": oturumlar,
    }


# ============================================================================ CSV
def _sure(sn) -> str:
    sn = int(sn or 0)
    return f"{sn // 3600}:{sn % 3600 // 60:02d}:{sn % 60:02d}"


@router.get("/csv")
def kullanim_csv(
    tur: str = Query(..., pattern="^(menuler|okullar|kullanicilar|gunluk|siniflar)$"),
    tip: str = Query("ogrenci", pattern="^(ogrenci|okul_yetkilisi|super_admin)$"),
    f: Suzgec = Depends(_suzgec), db: Session = Depends(get_db), _a: AdminKullanici = Depends(get_mevcut_admin),
):
    tampon = io.StringIO()
    tampon.write("﻿")
    w = csv.writer(tampon, delimiter=";")
    if tur == "kullanicilar":
        sql, p = _kisi_listesi_sql(f, tip, None, None, "hepsi")
        w.writerow(["Ad soyad", "E-posta", "Okul", "Sınıf", "Şube", "Aktif süre (sa:dk:sn)", "Aktif süre (dk)", "Oturum",
                    "Ortalama oturum (dk)", "Aktif gün", "Menü ziyareti", "En çok kullandığı menü", "Son kullanım", "Son giriş"])
        for r in db.execute(text(f"SELECT * FROM ({sql}) s ORDER BY aktif DESC, ad LIMIT 100000"), p).mappings():
            k = _kisi_satiri(r)
            w.writerow([k["ad"], k["eposta"], k["okul_ad"] or "", k["sinif"] or "", k["sube"] or "", _sure(k["aktif_sn"]),
                        round(k["aktif_sn"] / 60, 1), k["oturum"], round(k["ort_oturum_sn"] / 60, 1), k["aktif_gun"], k["ziyaret"],
                        k["en_cok_menu"] or "", k["son_kullanim"] or "", k["son_giris"] or ""])
    else:
        a = _analiz(db, f)
        if tur == "menuler":
            w.writerow(["Kullanıcı tipi", "Menü", "Alt sekme", "Aktif süre (sa:dk:sn)", "Aktif süre (dk)", "Pay (%)",
                        "Kullanan kişi", "Yaygınlık (%)", "Kişi başı (dk)", "Ziyaret", "Ziyaret başı (dk)"])
            for t in TIPLER:
                for m in a["menuler"][t]:
                    w.writerow([TIP_ETIKET[t], m["menu_ad"], "", _sure(m.get("aktif_sn")), round(m.get("aktif_sn", 0) / 60, 1),
                                m["pay"], m.get("kullanici", 0), m["yayginlik"], round(m["kisi_basi_sn"] / 60, 1),
                                m.get("ziyaret", 0), round(m["ort_ziyaret_sn"] / 60, 1)])
                    for x in m["altlar"]:
                        w.writerow([TIP_ETIKET[t], m["menu_ad"], x["alt_ad"], _sure(x["aktif_sn"]), round(x["aktif_sn"] / 60, 1),
                                    x["pay_menude"], x["kullanici"], "", round(_ort(x["aktif_sn"], x["kullanici"]) / 60, 1),
                                    x["ziyaret"], round(_ort(x["aktif_sn"], x["ziyaret"]) / 60, 1)])
        elif tur == "okullar":
            w.writerow(["Okul", "Kayıtlı öğrenci", "Kullanan öğrenci", "Öğrenci katılım (%)", "Öğrenci toplam (dk)",
                        "Öğrenci kişi başı (dk)", "Öğrenci oturum", "Öğrencide en çok menü", "Kayıtlı yetkili", "Kullanan yetkili",
                        "Yetkili katılım (%)", "Yetkili toplam (dk)", "Yetkili kişi başı (dk)", "Yetkilide en çok menü"])
            for s in a["okullar"]:
                o, y = s["ogrenci"], s["okul_yetkilisi"]
                w.writerow([s["okul_ad"], o["kayitli"], o["aktif"], o["katilim_orani"], round(o["toplam_sn"] / 60, 1),
                            round(o["kisi_basi_sn"] / 60, 1), o["oturum"], o["en_cok_menu"] or "", y["kayitli"], y["aktif"],
                            y["katilim_orani"], round(y["toplam_sn"] / 60, 1), round(y["kisi_basi_sn"] / 60, 1), y["en_cok_menu"] or ""])
        elif tur == "gunluk":
            w.writerow(["Gün"] + [f"{TIP_ETIKET[t]} — {b}" for t in TIPLER for b in ("aktif kişi", "toplam (dk)")])
            for g in a["gunluk"]:
                w.writerow([g["gun"]] + [v for t in TIPLER for v in (g[f"{t}_kisi"], round(g[f"{t}_sn"] / 60, 1))])
        else:
            w.writerow(["Sınıf", "Kayıtlı öğrenci", "Kullanan öğrenci", "Katılım (%)", "Toplam (dk)", "Kişi başı (dk)"])
            for s in a["siniflar"]:
                w.writerow([s["sinif"], s["kayitli"], s["aktif"], s["katilim_orani"], round(s["toplam_sn"] / 60, 1),
                            round(s["kisi_basi_sn"] / 60, 1)])
    ad = f"kullanim-{tur}{'-' + tip if tur == 'kullanicilar' else ''}-{f.bas.isoformat()}-{f.bit.isoformat()}.csv"
    return Response(content=tampon.getvalue().encode("utf-8"), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{ad}"'})
