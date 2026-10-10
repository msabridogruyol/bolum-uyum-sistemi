# -*- coding: utf-8 -*-
"""
[2026-10-10] Raporlar (PDF / Excel).

GET /yonetim/ogrenci/{id}/rapor?tur=ogrenci|veli|yonetici&bicim=pdf|xlsx — rehber / süper admin (okul kapsamı denetlenir)
GET /yonetim/okul/{okul_id}/rapor?bicim=pdf|xlsx                          — okul genel raporu
Her indirme Audit Log'a (yönetim) / hesap olaylarına (öğrenci) yazılır.
"""
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
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


# [2026-10-10] Öğrencinin kendi raporunu indirmesi kaldırıldı: raporları yalnızca okul yetkilisi ve süper admin indirir
# (veli raporu da okul üzerinden verilir).


@router.get("/yonetim/ogrenci/{ogrenci_id}/rapor")
def ogrenci_raporu(ogrenci_id: str, tur: str = Query("yonetici"), bicim: str = Query("pdf"), db: Session = Depends(get_db),
                   yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.okul_yonetimi import _ogrenci_kapsami
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    cevap = _ogrenci_dosyasi(db, o, tur, bicim)
    denetim_yaz(db, yon, "rapor_indir", "ogrenciler", o.id, f"{o.ad_soyad}: {tur} raporu ({bicim})", o.okul_id)
    db.commit()
    return cevap


TOPLU_SINIR = 80
TOPLU_TUR = {"toplu_ogrenci": ("ogrenci", "Ogrenci_Raporlari"), "toplu_veli": ("veli", "Veli_Raporlari"),
             "toplu_yonetici": ("yonetici", "Yonetici_Raporlari")}


@router.get("/yonetim/okul/{okul_id}/rapor")
def okul_raporu(okul_id: int, bicim: str = Query("pdf"), sinif: str | None = Query(None), sube: str | None = Query(None),
                tur: str = Query("ozet"), db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    """tur = ozet (okul / sınıf düzeyi / şube özeti, PDF ya da Excel)
           | toplu_ogrenci | toplu_veli | toplu_yonetici (sınıftaki herkesin bireysel raporu tek PDF'te — veli toplantısı için)"""
    from app.api.okul_yonetimi import _okul_kapsami, sube_etiketi
    from app.core.rapor.excel import okul_xlsx
    from app.core.rapor.pdf import okul_pdf
    from app.core.rapor.veri import okul_raporu_verisi
    if bicim not in MIME:
        raise HTTPException(status_code=400, detail="Geçersiz biçim.")
    okul = _okul_kapsami(db, yon, okul_id)
    sinif = (sinif or "").strip() or None
    sube = ((sube or "").strip().upper() or None) if sinif else None
    kapsam_adi = sube_etiketi(sinif, sube) if sinif else None
    okul_adi = okul.ad if okul else "Okul_harici"

    if tur in TOPLU_TUR:
        if not sinif:
            raise HTTPException(status_code=400, detail="Toplu rapor için sınıf / şube seçin.")
        if bicim != "pdf":
            raise HTTPException(status_code=400, detail="Toplu rapor yalnızca PDF olarak alınabilir.")
        from pypdf import PdfWriter
        from io import BytesIO
        ogrenciler = [o for o in db.query(Ogrenci).filter(
            Ogrenci.okul_id.is_(None) if okul_id == 0 else Ogrenci.okul_id == okul_id).all()
            if o.sinif == sinif and (not sube or (o.sube or "") == sube)]
        ogrenciler.sort(key=lambda o: (int(o.ogrenci_no) if (o.ogrenci_no or "").isdigit() else 10**9, o.ad_soyad))
        if not ogrenciler:
            raise HTTPException(status_code=404, detail="Bu sınıfta öğrenci yok.")
        if len(ogrenciler) > TOPLU_SINIR:
            raise HTTPException(status_code=400, detail=f"Toplu rapor en fazla {TOPLU_SINIR} öğrenci için alınabilir; şube seçin.")
        from app.core.rapor.pdf import ogrenci_pdf, veli_pdf, yonetici_pdf
        from app.core.rapor.veri import ogrenci_raporu_verisi
        uret = {"ogrenci": ogrenci_pdf, "veli": veli_pdf, "yonetici": yonetici_pdf}[TOPLU_TUR[tur][0]]
        yazici = PdfWriter()
        for o in ogrenciler:
            yazici.append(BytesIO(uret(ogrenci_raporu_verisi(db, o))), outline_item=o.ad_soyad)
        cikti = BytesIO()
        yazici.write(cikti)
        denetim_yaz(db, yon, "rapor_indir", "okullar", okul_id, f"{kapsam_adi}: toplu {TOPLU_TUR[tur][0]} raporu ({len(ogrenciler)} öğrenci)", okul_id or None)
        db.commit()
        from datetime import datetime
        return _cevap(cikti.getvalue(), "pdf", _dosya_adi(TOPLU_TUR[tur][1], kapsam_adi, datetime.now().strftime("%Y%m%d")))

    if tur != "ozet":
        raise HTTPException(status_code=400, detail="Geçersiz rapor türü.")
    v = okul_raporu_verisi(db, okul_id, yon, sinif=sinif, sube=sube)
    icerik = okul_pdf(v) if bicim == "pdf" else okul_xlsx(v)
    denetim_yaz(db, yon, "rapor_indir", "okullar", okul_id,
                f"{(kapsam_adi + ' sınıf') if kapsam_adi else 'Okul genel'} raporu ({bicim})", okul_id or None)
    db.commit()
    return _cevap(icerik, bicim, _dosya_adi(f"{kapsam_adi}_Sinif_Raporu" if kapsam_adi else "Okul_Raporu", okul_adi,
                                            v["tarih"].strftime("%Y%m%d")))
