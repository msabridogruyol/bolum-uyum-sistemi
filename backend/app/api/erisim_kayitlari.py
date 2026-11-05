# -*- coding: utf-8 -*-
"""
[2026-11-05] Süper admin › Erişim Kayıtları: kim, ne zaman giriş yaptı; kimin verisine, hangi bölümde eriştiyse.
Yalnızca süper admin. Kayıtlar app/core/erisim_kaydi.py tarafından yazılır; liste açılırken kuyruktakiler hemen yazılır.
  GET /admin/erisim-kayitlari        süzgeçli, sayfalı liste + özet sayılar
  GET /admin/erisim-kayitlari/csv    aynı süzgeçlerle dışa aktarım (en çok 50.000 satır)
"""
from __future__ import annotations

import csv
import io
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_admin
from app.core.database import get_db
from app.core.erisim_kaydi import bosalt
from app.models import AdminKullanici

router = APIRouter(prefix="/admin/erisim-kayitlari", tags=["Yönetim — Erişim Kayıtları"])
_TR = ZoneInfo("Europe/Istanbul")

OLAY_ETIKET = {
    "giris": "Giriş", "giris_hatali": "Hatalı giriş", "giris_engellendi": "Engellenen giriş",
    "iki_adim_hatali": "Hatalı doğrulama kodu", "goruntuleme": "Görüntüleme", "indirme": "İndirme", "islem": "İşlem",
}
TIP_ETIKET = {"ogrenci": "Öğrenci", "okul_yetkilisi": "Okul yetkilisi", "super_admin": "Süper admin", "bilinmiyor": "Bilinmeyen hesap"}


def _suzgec(bas, bit, kullanici_tipi, okul_id, olay, kisi, hedef, kullanici_id, hedef_ogrenci_id, yalniz_hata):
    kosul, p = [], {}
    if bas:
        kosul.append("e.zaman >= :bas"); p["bas"] = datetime.combine(bas, time.min, _TR)
    if bit:
        kosul.append("e.zaman < :bit"); p["bit"] = datetime.combine(bit + timedelta(days=1), time.min, _TR)
    if kullanici_tipi:
        kosul.append("e.kullanici_tipi = :tip"); p["tip"] = kullanici_tipi
    if okul_id is not None:
        kosul.append("(e.okul_id = :okul OR e.hedef_okul_id = :okul)"); p["okul"] = okul_id
    if olay == "giris_hepsi":
        kosul.append("e.olay IN ('giris', 'giris_hatali', 'giris_engellendi', 'iki_adim_hatali')")
    elif olay:
        kosul.append("e.olay = :olay"); p["olay"] = olay
    if kisi:
        kosul.append("(e.kullanici_ad ILIKE :kisi OR e.kullanici_eposta ILIKE :kisi)"); p["kisi"] = f"%{kisi.strip()}%"
    if hedef:
        kosul.append("e.hedef_ad ILIKE :hedef"); p["hedef"] = f"%{hedef.strip()}%"
    if kullanici_id:
        kosul.append("e.kullanici_id = CAST(:kid AS uuid)"); p["kid"] = kullanici_id
    if hedef_ogrenci_id:
        kosul.append("e.hedef_ogrenci_id = CAST(:hid AS uuid)"); p["hid"] = hedef_ogrenci_id
    if yalniz_hata:
        kosul.append("(e.durum_kodu >= 400 OR e.olay IN ('giris_hatali', 'giris_engellendi', 'iki_adim_hatali'))")
    return ("WHERE " + " AND ".join(kosul)) if kosul else "", p


def _parametreler(
    bas: date | None = None, bit: date | None = None,
    kullanici_tipi: str | None = Query(None, pattern="^(ogrenci|okul_yetkilisi|super_admin|bilinmiyor)$"),
    okul_id: int | None = None,
    olay: str | None = Query(None, pattern="^(giris|giris_hatali|giris_engellendi|iki_adim_hatali|goruntuleme|indirme|islem|giris_hepsi)$"),
    kisi: str | None = Query(None, max_length=100), hedef: str | None = Query(None, max_length=100),
    kullanici_id: str | None = Query(None, max_length=40), hedef_ogrenci_id: str | None = Query(None, max_length=40),
    yalniz_hata: bool = False,
):
    if bas and bit and bit < bas:
        raise HTTPException(status_code=400, detail="Bitiş tarihi başlangıçtan önce olamaz.")
    return _suzgec(bas, bit, kullanici_tipi, okul_id, olay, kisi, hedef, kullanici_id, hedef_ogrenci_id, yalniz_hata)


_SECIM = """
SELECT e.id, e.zaman, e.kullanici_tipi, e.kullanici_id, e.kullanici_ad, e.kullanici_eposta, e.okul_id, ok.ad AS okul_ad,
       e.olay, e.bolum, e.yontem, e.yol, e.hedef_ogrenci_id, e.hedef_ad, e.hedef_okul_id, hok.ad AS hedef_okul_ad,
       e.durum_kodu, e.ip
  FROM erisim_kayitlari e
  LEFT JOIN okullar ok ON ok.id = e.okul_id
  LEFT JOIN okullar hok ON hok.id = e.hedef_okul_id
"""


def _satir(r) -> dict:
    return {
        "id": r.id, "zaman": r.zaman.isoformat() if r.zaman else None,
        "kullanici_tipi": r.kullanici_tipi, "kullanici_tipi_etiket": TIP_ETIKET.get(r.kullanici_tipi, r.kullanici_tipi),
        "kullanici_id": str(r.kullanici_id) if r.kullanici_id else None, "kullanici_ad": r.kullanici_ad,
        "kullanici_eposta": r.kullanici_eposta, "okul_id": r.okul_id, "okul_ad": r.okul_ad,
        "olay": r.olay, "olay_etiket": OLAY_ETIKET.get(r.olay, r.olay), "bolum": r.bolum, "yontem": r.yontem, "yol": r.yol,
        "hedef_ogrenci_id": str(r.hedef_ogrenci_id) if r.hedef_ogrenci_id else None, "hedef_ad": r.hedef_ad,
        "hedef_okul_id": r.hedef_okul_id, "hedef_okul_ad": r.hedef_okul_ad, "durum_kodu": r.durum_kodu,
        "basarili": r.olay not in ("giris_hatali", "giris_engellendi", "iki_adim_hatali") and (r.durum_kodu or 200) < 400,
        "ip": r.ip,
    }


@router.get("")
def erisim_kayitlari(
    suzgec=Depends(_parametreler),
    sayfa: int = Query(1, ge=1, le=100000), adet: int = Query(50, ge=10, le=200),
    db: Session = Depends(get_db), _admin: AdminKullanici = Depends(get_mevcut_admin),
):
    bosalt(db)
    db.commit()
    nerede, p = suzgec
    toplam = db.execute(text(f"SELECT count(*) FROM erisim_kayitlari e {nerede}"), p).scalar() or 0
    satirlar = db.execute(text(f"{_SECIM} {nerede} ORDER BY e.zaman DESC, e.id DESC LIMIT :adet OFFSET :ofs"),
                          {**p, "adet": adet, "ofs": (sayfa - 1) * adet}).all()
    ozet = db.execute(text(f"""
        SELECT count(*) FILTER (WHERE e.olay = 'giris') AS giris,
               count(*) FILTER (WHERE e.olay IN ('giris_hatali', 'giris_engellendi', 'iki_adim_hatali')) AS hatali_giris,
               count(*) FILTER (WHERE e.olay = 'indirme') AS indirme,
               count(*) FILTER (WHERE e.durum_kodu IN (401, 403)) AS reddedilen,
               count(DISTINCT e.kullanici_id) AS kisi,
               count(DISTINCT e.hedef_ogrenci_id) FILTER (WHERE e.kullanici_tipi <> 'ogrenci') AS bakilan_ogrenci
          FROM erisim_kayitlari e {nerede}"""), p).mappings().one()
    from app.core.katman_servisi import parametre_oku
    return {"toplam": toplam, "sayfa": sayfa, "adet": adet, "ozet": dict(ozet),
            "saklama_gun": parametre_oku(db, "erisim_kaydi_saklama_gun", "365"),
            "kayitlar": [_satir(r) for r in satirlar]}


@router.get("/csv")
def erisim_kayitlari_csv(suzgec=Depends(_parametreler), db: Session = Depends(get_db),
                         _admin: AdminKullanici = Depends(get_mevcut_admin)):
    bosalt(db)
    db.commit()
    nerede, p = suzgec
    satirlar = db.execute(text(f"{_SECIM} {nerede} ORDER BY e.zaman DESC, e.id DESC LIMIT 50000"), p).all()
    tampon = io.StringIO()
    y = csv.writer(tampon, delimiter=";")
    y.writerow(["Zaman", "Kişi", "Kişi türü", "E-posta", "Kişinin okulu", "Olay", "Bölüm", "Hedef öğrenci", "Hedef okul",
                "Sonuç", "IP", "Yöntem", "Yol"])
    for r in satirlar:
        s = _satir(r)
        z = r.zaman.astimezone(_TR).strftime("%d.%m.%Y %H:%M:%S") if r.zaman else ""
        y.writerow([z, s["kullanici_ad"] or "", s["kullanici_tipi_etiket"], s["kullanici_eposta"] or "", s["okul_ad"] or "",
                    s["olay_etiket"], s["bolum"] or "", s["hedef_ad"] or "", s["hedef_okul_ad"] or "",
                    "Başarılı" if s["basarili"] else ("Başarısız" + (f" ({s['durum_kodu']})" if s["durum_kodu"] else "")), s["ip"] or "",
                    s["yontem"] or "", s["yol"] or ""])
    ad = f"erisim_kayitlari_{datetime.now(timezone.utc).astimezone(_TR):%Y%m%d_%H%M}.csv"
    return Response(content="﻿" + tampon.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{ad}"'})
