# -*- coding: utf-8 -*-
"""
[2026-10-10] Raporlar (PDF / Excel).

GET /ogrenci/rapor?tur=ogrenci|veli&bicim=pdf|xlsx                      — öğrenci kendi raporu (ve velisine götüreceği rapor)
GET /yonetim/ogrenci/{id}/rapor?tur=ogrenci|veli|yonetici&bicim=pdf|xlsx — rehber / süper admin (okul kapsamı denetlenir)
GET /yonetim/okul/{okul_id}/rapor?bicim=pdf|xlsx                          — okul genel raporu
Her indirme Audit Log'a (yönetim) / hesap olaylarına (öğrenci) yazılır.
"""
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz, olay_yaz
from app.models import AdminKullanici, Ogrenci

router = APIRouter(tags=["Raporlar"])
TUR_ADI = {"ogrenci": "Ogrenci_Raporu", "veli": "Veli_Raporu", "yonetici": "Yonetici_Raporu"}
MIME = {"pdf": "application/pdf", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}


def _dosya_adi(*parcalar) -> str:
    metin = "_".join(str(p) for p in parcalar if p)
    metin = metin.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU"))
    metin = unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", metin).strip("_")[:120]


def _cevap(icerik: bytes, bicim: str, ad: str) -> Response:
    return Response(content=icerik, media_type=MIME[bicim],
                    headers={"Content-Disposition": f'attachment; filename="{ad}.{bicim}"', "Cache-Control": "no-store"})


def _ogrenci_dosyasi(db: Session, o: Ogrenci, tur: str, bicim: str) -> Response:
    from app.core.rapor.excel import ogrenci_xlsx
    from app.core.rapor.pdf import ogrenci_pdf, veli_pdf, yonetici_pdf
    from app.core.rapor.veri import ogrenci_raporu_verisi
    if tur not in TUR_ADI or bicim not in MIME:
        raise HTTPException(status_code=400, detail="Geçersiz rapor türü ya da biçimi.")
    v = ogrenci_raporu_verisi(db, o)
    if bicim == "xlsx":
        icerik = ogrenci_xlsx(v)
    else:
        icerik = {"ogrenci": ogrenci_pdf, "veli": veli_pdf, "yonetici": yonetici_pdf}[tur](v)
    return _cevap(icerik, bicim, _dosya_adi(TUR_ADI[tur] if bicim == "pdf" else "Sonuclar", o.ad_soyad, v["tarih"].strftime("%Y%m%d")))


@router.get("/ogrenci/rapor")
def ogrenci_kendi_raporu(tur: str = Query("ogrenci"), bicim: str = Query("pdf"), db: Session = Depends(get_db),
                         o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if tur == "yonetici":
        raise HTTPException(status_code=403, detail="Bu rapor türü yalnızca okul yetkililerine açıktır.")
    cevap = _ogrenci_dosyasi(db, o, tur, bicim)
    olay_yaz(db, o.id, "rapor_indirdi", f"{tur} · {bicim}", "Öğrenci")
    db.commit()
    return cevap


@router.get("/yonetim/ogrenci/{ogrenci_id}/rapor")
def ogrenci_raporu(ogrenci_id: str, tur: str = Query("yonetici"), bicim: str = Query("pdf"), db: Session = Depends(get_db),
                   yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.okul_yonetimi import _ogrenci_kapsami
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    cevap = _ogrenci_dosyasi(db, o, tur, bicim)
    denetim_yaz(db, yon, "rapor_indir", "ogrenciler", o.id, f"{o.ad_soyad}: {tur} raporu ({bicim})", o.okul_id)
    db.commit()
    return cevap


@router.get("/yonetim/okul/{okul_id}/rapor")
def okul_raporu(okul_id: int, bicim: str = Query("pdf"), db: Session = Depends(get_db),
                yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.okul_yonetimi import _okul_kapsami
    from app.core.rapor.excel import okul_xlsx
    from app.core.rapor.pdf import okul_pdf
    from app.core.rapor.veri import okul_raporu_verisi
    if bicim not in MIME:
        raise HTTPException(status_code=400, detail="Geçersiz biçim.")
    okul = _okul_kapsami(db, yon, okul_id)
    v = okul_raporu_verisi(db, okul_id, yon)
    icerik = okul_pdf(v) if bicim == "pdf" else okul_xlsx(v)
    denetim_yaz(db, yon, "rapor_indir", "okullar", okul_id, f"Okul genel raporu ({bicim})", okul_id or None)
    db.commit()
    return _cevap(icerik, bicim, _dosya_adi("Okul_Raporu", okul.ad if okul else "Okul_harici", v["tarih"].strftime("%Y%m%d")))
