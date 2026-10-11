"""
[2026-10-11] Hata kayıtları.

  POST   /istemci-hata                      — tarayıcı hatası (kimliksiz de çalışır; sıkı hız sınırı + 32 KB gövde) → 204
  GET    /admin/hata-kayitlari              — gruplu liste (?durum=acik|cozuldu|hepsi&kaynak=sunucu|istemci&ara=)  [süper admin]
  GET    /admin/hata-kayitlari/{id}         — ayrıntı (yığın izi, son istek kimlikleri)
  POST   /admin/hata-kayitlari/{id}/cozuldu — {cozuldu: bool}
  DELETE /admin/hata-kayitlari?kapsam=cozulenler|eski|hepsi — temizleme (eski = 30 günden uzun süredir görülmeyen)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_super_admin
from app.core.database import get_db
from app.core.hata_izleme import _kullanici_tipi_tokendan, istemci_konumu, kaydet
from app.models import AdminKullanici

router = APIRouter(tags=["Hata kayıtları"])


class IstemciHata(BaseModel):
    mesaj: str = Field(..., max_length=2000)
    yigin: str | None = Field(None, max_length=8000)
    sayfa: str | None = Field(None, max_length=500)
    tur: str | None = Field(None, max_length=40)            # error | unhandledrejection | react
    bilesen_yigini: str | None = Field(None, max_length=4000)


@router.post("/istemci-hata", status_code=204)
def istemci_hatasi(istek: IstemciHata, request: Request):
    yigin = (istek.yigin or "") + (("\n--- React bileşen yığını ---\n" + istek.bilesen_yigini) if istek.bilesen_yigini else "")
    tur = (istek.tur or "error")[:40]
    kaydet(kaynak="istemci", yol=(istek.sayfa or "")[:500], metod=None, durum_kodu=None,
           istisna_turu=f"istemci.{tur}", mesaj=istek.mesaj, yigin=yigin,
           kullanici_tipi=_kullanici_tipi_tokendan(request.headers.get("authorization")),
           istek_kimligi=getattr(request.state, "istek_kimligi", None),
           konum=istemci_konumu(istek.yigin or "", istek.mesaj), tarayici=request.headers.get("user-agent"))
    return Response(status_code=204)


_LISTE_ALANLARI = """id, kaynak, yol, yol_kalibi, metod, durum_kodu, istisna_turu, LEFT(mesaj, 300) AS mesaj, kullanici_tipi,
                     istek_kimligi, sayi, ilk_gorulme, son_gorulme, cozuldu_mu, cozulme_zamani, cozen"""


@router.get("/admin/hata-kayitlari")
def listele(durum: str = Query("acik", pattern="^(acik|cozuldu|hepsi)$"), kaynak: str | None = Query(None, pattern="^(sunucu|istemci)$"),
            ara: str | None = Query(None, max_length=100), limit: int = Query(200, ge=1, le=500),
            db: Session = Depends(get_db), _: AdminKullanici = Depends(get_mevcut_super_admin)):
    kosul, p = ["TRUE"], {"l": limit}
    if durum != "hepsi":
        kosul.append("cozuldu_mu = :c")
        p["c"] = durum == "cozuldu"
    if kaynak:
        kosul.append("kaynak = :k")
        p["k"] = kaynak
    if ara and ara.strip():
        kosul.append("(istisna_turu ILIKE :a OR mesaj ILIKE :a OR yol ILIKE :a OR istek_kimligi = :ak "
                     "OR son_istekler @> CAST(:aj AS jsonb))")
        a = ara.strip()
        import json
        p.update({"a": f"%{a}%", "ak": a, "aj": json.dumps([{"k": a}])})
    satirlar = db.execute(text(f"SELECT {_LISTE_ALANLARI} FROM hata_kayitlari WHERE {' AND '.join(kosul)} "
                               "ORDER BY cozuldu_mu, son_gorulme DESC LIMIT :l"), p).mappings().all()
    ozet = db.execute(text("""
        SELECT COUNT(*) FILTER (WHERE NOT cozuldu_mu) AS acik, COUNT(*) FILTER (WHERE cozuldu_mu) AS cozuldu,
               COALESCE(SUM(sayi) FILTER (WHERE NOT cozuldu_mu), 0) AS acik_tekrar,
               COUNT(*) FILTER (WHERE son_gorulme > now() - interval '24 hours') AS son_24_saat,
               COUNT(*) FILTER (WHERE ilk_gorulme > now() - interval '24 hours') AS yeni_24_saat
          FROM hata_kayitlari""")).mappings().first()
    return {"gruplar": [dict(r) for r in satirlar], "ozet": dict(ozet)}


@router.get("/admin/hata-kayitlari/{kayit_id}")
def ayrinti(kayit_id: int, db: Session = Depends(get_db), _: AdminKullanici = Depends(get_mevcut_super_admin)):
    r = db.execute(text("SELECT * FROM hata_kayitlari WHERE id = :i"), {"i": kayit_id}).mappings().first()
    if r is None:
        raise HTTPException(404, "Hata kaydı bulunamadı.")
    return dict(r)


class CozulduIstek(BaseModel):
    cozuldu: bool = True


@router.post("/admin/hata-kayitlari/{kayit_id}/cozuldu")
def cozuldu_isaretle(kayit_id: int, istek: CozulduIstek, db: Session = Depends(get_db),
                     yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    from app.core.hesap_yonetimi import denetim_yaz
    n = db.execute(text("""UPDATE hata_kayitlari SET cozuldu_mu = :c, cozulme_zamani = CASE WHEN :c THEN now() END,
                                  cozen = CASE WHEN :c THEN :y END WHERE id = :i"""),
                   {"c": istek.cozuldu, "y": yon.ad_soyad, "i": kayit_id}).rowcount
    if not n:
        raise HTTPException(404, "Hata kaydı bulunamadı.")
    denetim_yaz(db, yon, "hata_kaydi_cozuldu" if istek.cozuldu else "hata_kaydi_yeniden_ac", "hata_kayitlari", kayit_id)
    db.commit()
    return {"ok": True}


@router.delete("/admin/hata-kayitlari")
def temizle(kapsam: str = Query("cozulenler", pattern="^(cozulenler|eski|hepsi)$"), db: Session = Depends(get_db),
            yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    from app.core.hesap_yonetimi import denetim_yaz
    kosul = {"cozulenler": "cozuldu_mu", "eski": "son_gorulme < now() - interval '30 days'", "hepsi": "TRUE"}[kapsam]
    n = db.execute(text(f"DELETE FROM hata_kayitlari WHERE {kosul}")).rowcount
    denetim_yaz(db, yon, "hata_kayitlari_temizle", "hata_kayitlari", kapsam, f"{n} grup silindi")
    db.commit()
    return {"silinen": n}
