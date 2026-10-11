# -*- coding: utf-8 -*-
"""
[2026-10-10] e-Portfolyo (modül: portfolyo) — öğrencinin sertifika, yarışma, gönüllülük, proje, staj … kayıtları,
okulun onaylı kulüp üyelikleri ve "Hakkımda / yetenekler / diller" profili. Okul yetkilisi kayıtları doğrular (✓).
PDF özgeçmiş: burs, yaz okulu, yurt dışı ve üniversite başvuruları için.

Öğrenci:  GET /ogrenci/portfolyo · PUT /ogrenci/portfolyo/profil · POST /ogrenci/portfolyo/kayit ·
          PUT/DELETE /ogrenci/portfolyo/kayit/{kayit_id} · GET /ogrenci/portfolyo/kayit/{kayit_id}/belge · GET /ogrenci/portfolyo/pdf
Yönetim:  GET /yonetim/ogrenci/{ogrenci_id}/portfolyo · GET /yonetim/ogrenci/{ogrenci_id}/portfolyo/pdf ·
          POST /yonetim/portfolyo-kayit/{portfolyo_id}/dogrula · GET /yonetim/portfolyo-kayit/{portfolyo_id}/belge
"""
import base64
import io
import json
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci, get_mevcut_yonetim
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.models import AdminKullanici, Ogrenci

ogrenci_router = APIRouter(prefix="/ogrenci/portfolyo", tags=["e-Portfolyo"])
yonetim_router = APIRouter(prefix="/yonetim", tags=["e-Portfolyo"])

TURLER = {
    "sertifika": {"ad": "Sertifika / kurs", "ikon": "📜"},
    "yarisma": {"ad": "Yarışma / ödül", "ikon": "🏆"},
    "gonullu": {"ad": "Gönüllülük / sosyal sorumluluk", "ikon": "🤝"},
    "proje": {"ad": "Proje", "ikon": "🛠️"},
    "staj": {"ad": "Staj / iş deneyimi", "ikon": "💼"},
    "spor_sanat": {"ad": "Spor / sanat", "ikon": "🎨"},
    "gorev": {"ad": "Görev / liderlik", "ikon": "⭐"},
    "diger": {"ad": "Diğer", "ikon": "📌"},
}
DIL_SEVIYE = ["A1", "A2", "B1", "B2", "C1", "C2", "Ana dil"]
EN_BUYUK_BELGE = 1_500_000   # data URL karakter sayısı (~1,1 MB dosya)
ALANLAR = "id, tur, baslik, kurum, baslangic, bitis, aciklama, saat, derece, link, belge_adi, (belge IS NOT NULL) AS belge_var, dogrulandi, dogrulayan, dogrulama_zamani"


def _kayit(r) -> dict:
    d = dict(r._mapping)
    for k in ("baslangic", "bitis"):
        d[k] = d[k].isoformat() if d[k] else None
    d["tur_ad"] = TURLER.get(d["tur"], {}).get("ad", d["tur"])
    d["ikon"] = TURLER.get(d["tur"], {}).get("ikon", "📌")
    return d


def _profil(db: Session, oid) -> dict:
    r = db.execute(text("SELECT hakkimda, yetenekler, diller, eposta_goster FROM portfolyo_profil WHERE ogrenci_id = :o"), {"o": oid}).first()
    if r is None:
        return {"hakkimda": "", "yetenekler": [], "diller": [], "eposta_goster": False}
    j = lambda v: v if isinstance(v, list) else json.loads(v or "[]")  # noqa: E731
    return {"hakkimda": r.hakkimda or "", "yetenekler": j(r.yetenekler), "diller": j(r.diller), "eposta_goster": bool(r.eposta_goster)}


def _kulupler(db: Session, oid) -> list[dict]:
    try:
        rows = db.execute(text("""
            SELECT k.ad, u.karar_zamani, u.durum FROM kulup_uyelikleri u JOIN okul_kulupleri k ON k.id = u.kulup_id
             WHERE u.ogrenci_id = :o AND u.durum IN ('onaylandi', 'ayrildi') AND u.karar_zamani IS NOT NULL ORDER BY u.karar_zamani
        """), {"o": oid}).all()
    except Exception:
        db.rollback()
        return []
    return [{"ad": r.ad, "baslangic": r.karar_zamani.date().isoformat() if r.durum == "onaylandi" else None, "aktif": r.durum == "onaylandi"}
            for r in rows if r.durum == "onaylandi"]


def portfolyo_verisi(db: Session, o: Ogrenci) -> dict:
    kayitlar = [_kayit(r) for r in db.execute(text(f"SELECT {ALANLAR} FROM portfolyo_kayitlari WHERE ogrenci_id = :o "
                                                     "ORDER BY coalesce(bitis, baslangic, olusturulma_zamani::date) DESC, id DESC"), {"o": o.id}).all()]
    return {"profil": _profil(db, o.id), "kayitlar": kayitlar, "kulupler": _kulupler(db, o.id),
            "turler": [{"kod": k, **v} for k, v in TURLER.items()], "dil_seviyeleri": DIL_SEVIYE,
            "ozet": {"toplam": len(kayitlar), "dogrulanan": sum(1 for k in kayitlar if k["dogrulandi"]),
                     "gonullu_saat": sum(k["saat"] or 0 for k in kayitlar if k["tur"] == "gonullu")}}


# ----------------------------------------------------------------------------- öğrenci
@ogrenci_router.get("")
def portfolyom(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return portfolyo_verisi(db, o)


class DilIstek(BaseModel):
    dil: str = Field(min_length=2, max_length=30)
    seviye: str


class ProfilIstek(BaseModel):
    hakkimda: str | None = Field(default=None, max_length=1200)
    yetenekler: list[str] = Field(default_factory=list)
    diller: list[DilIstek] = Field(default_factory=list)
    eposta_goster: bool = False


@ogrenci_router.put("/profil")
def profil_kaydet(istek: ProfilIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    yetenek = [y.strip()[:40] for y in istek.yetenekler if y and y.strip()][:20]
    diller = [{"dil": d.dil.strip(), "seviye": d.seviye} for d in istek.diller if d.seviye in DIL_SEVIYE][:8]
    db.execute(text("""
        INSERT INTO portfolyo_profil (ogrenci_id, hakkimda, yetenekler, diller, eposta_goster)
        VALUES (:o, :h, CAST(:y AS JSONB), CAST(:d AS JSONB), :e)
        ON CONFLICT (ogrenci_id) DO UPDATE SET hakkimda = EXCLUDED.hakkimda, yetenekler = EXCLUDED.yetenekler,
            diller = EXCLUDED.diller, eposta_goster = EXCLUDED.eposta_goster
    """), {"o": o.id, "h": (istek.hakkimda or "").strip() or None, "y": json.dumps(yetenek, ensure_ascii=False),
           "d": json.dumps(diller, ensure_ascii=False), "e": istek.eposta_goster})
    db.commit()
    return portfolyo_verisi(db, o)


class KayitIstek(BaseModel):
    tur: str
    baslik: str = Field(min_length=2, max_length=140)
    kurum: str | None = Field(default=None, max_length=120)
    baslangic: date | None = None
    bitis: date | None = None
    aciklama: str | None = Field(default=None, max_length=1000)
    saat: int | None = Field(default=None, ge=0, le=5000)
    derece: str | None = Field(default=None, max_length=80)
    link: str | None = Field(default=None, max_length=400)
    belge: str | None = None          # data URL (PDF / görsel); "" → belgeyi kaldır; None → değiştirme
    belge_adi: str | None = Field(default=None, max_length=120)


def _dogrula(istek: KayitIstek) -> dict:
    if istek.tur not in TURLER:
        raise HTTPException(400, "Geçersiz kayıt türü.")
    if istek.baslangic and istek.bitis and istek.bitis < istek.baslangic:
        raise HTTPException(400, "Bitiş tarihi başlangıçtan önce olamaz.")
    if istek.baslangic and istek.baslangic > date.today():
        raise HTTPException(400, "Başlangıç tarihi gelecekte olamaz.")
    link = (istek.link or "").strip() or None
    if link and not re.match(r"^https?://", link):
        link = "https://" + link
    if istek.belge:
        if not re.match(r"^data:(application/pdf|image/(png|jpeg|webp));base64,", istek.belge):
            raise HTTPException(400, "Belge PDF, PNG, JPG ya da WEBP olmalı.")
        if len(istek.belge) > EN_BUYUK_BELGE:
            raise HTTPException(400, "Belge en fazla 1 MB olabilir.")
    t = lambda v: (v or "").strip() or None  # noqa: E731
    return {"tu": istek.tur, "ba": istek.baslik.strip(), "ku": t(istek.kurum), "bs": istek.baslangic, "bt": istek.bitis,
            "ac": t(istek.aciklama), "sa": istek.saat if istek.tur == "gonullu" else None, "de": t(istek.derece), "li": link}


@ogrenci_router.post("/kayit", status_code=201)
def kayit_ekle(istek: KayitIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if db.execute(text("SELECT count(*) FROM portfolyo_kayitlari WHERE ogrenci_id = :o"), {"o": o.id}).scalar() >= 100:
        raise HTTPException(400, "Portfolyoda en fazla 100 kayıt olabilir.")
    v = _dogrula(istek)
    db.execute(text("""
        INSERT INTO portfolyo_kayitlari (ogrenci_id, tur, baslik, kurum, baslangic, bitis, aciklama, saat, derece, link, belge, belge_adi)
        VALUES (:o, :tu, :ba, :ku, :bs, :bt, :ac, :sa, :de, :li, :be, :bn)
    """), {**v, "o": o.id, "be": istek.belge or None, "bn": (istek.belge_adi or None) if istek.belge else None})
    db.commit()
    return portfolyo_verisi(db, o)


@ogrenci_router.put("/kayit/{kayit_id}")
def kayit_duzenle(kayit_id: int, istek: KayitIstek, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    v = _dogrula(istek)
    belge = "" if istek.belge is None else ", belge = :be, belge_adi = :bn"
    # içerik değişince rehber doğrulaması düşer
    n = db.execute(text(f"""
        UPDATE portfolyo_kayitlari SET tur = :tu, baslik = :ba, kurum = :ku, baslangic = :bs, bitis = :bt, aciklama = :ac, saat = :sa,
               derece = :de, link = :li{belge}, dogrulandi = FALSE, dogrulayan = NULL, dogrulama_zamani = NULL
         WHERE id = :i AND ogrenci_id = :o
    """), {**v, "i": kayit_id, "o": o.id, "be": istek.belge or None, "bn": (istek.belge_adi or None) if istek.belge else None}).rowcount
    if not n:
        raise HTTPException(404, "Kayıt bulunamadı.")
    db.commit()
    return portfolyo_verisi(db, o)


@ogrenci_router.delete("/kayit/{kayit_id}")
def kayit_sil(kayit_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    if not db.execute(text("DELETE FROM portfolyo_kayitlari WHERE id = :i AND ogrenci_id = :o"), {"i": kayit_id, "o": o.id}).rowcount:
        raise HTTPException(404, "Kayıt bulunamadı.")
    db.commit()
    return portfolyo_verisi(db, o)


def _belge_cevabi(r) -> Response:
    if r is None or not r.belge:
        raise HTTPException(404, "Belge yok.")
    tur, veri = r.belge.split(",", 1)
    mime = tur[5:].split(";")[0]
    uzanti = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(mime, "bin")
    ad = re.sub(r"[^A-Za-z0-9_.-]+", "_", (r.belge_adi or "belge").rsplit(".", 1)[0])[:60] or "belge"
    return Response(base64.b64decode(veri), media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{ad}.{uzanti}"', "Cache-Control": "no-store"})


@ogrenci_router.get("/kayit/{kayit_id}/belge")
def kendi_belgem(kayit_id: int, db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    return _belge_cevabi(db.execute(text("SELECT belge, belge_adi FROM portfolyo_kayitlari WHERE id = :i AND ogrenci_id = :o"),
                                    {"i": kayit_id, "o": o.id}).first())


@ogrenci_router.get("/pdf")
def ozgecmis_pdf(db: Session = Depends(get_db), o: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.core.hesap_yonetimi import olay_yaz
    icerik = _pdf(db, o)
    olay_yaz(db, o.id, "ozgecmis_indir", "e-Portfolyo PDF", yapan="ogrenci")
    db.commit()
    return _pdf_cevap(icerik, o)


# ----------------------------------------------------------------------------- yönetim
@yonetim_router.get("/ogrenci/{ogrenci_id}/portfolyo")
def ogrenci_portfolyosu(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.okul_yonetimi import _ogrenci_kapsami
    return portfolyo_verisi(db, _ogrenci_kapsami(db, yon, ogrenci_id))


@yonetim_router.get("/ogrenci/{ogrenci_id}/portfolyo/pdf")
def ogrenci_ozgecmisi(ogrenci_id: str, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.okul_yonetimi import _ogrenci_kapsami
    o = _ogrenci_kapsami(db, yon, ogrenci_id)
    icerik = _pdf(db, o)
    denetim_yaz(db, yon, "ozgecmis_indir", "ogrenciler", o.id, o.ad_soyad, o.okul_id)
    db.commit()
    return _pdf_cevap(icerik, o)


def _yonetim_kaydi(db: Session, yon: AdminKullanici, portfolyo_id: int):
    from app.api.okul_yonetimi import _ogrenci_kapsami
    r = db.execute(text("SELECT id, ogrenci_id, baslik, belge, belge_adi FROM portfolyo_kayitlari WHERE id = :i"), {"i": portfolyo_id}).first()
    if r is None:
        raise HTTPException(404, "Kayıt bulunamadı.")
    return r, _ogrenci_kapsami(db, yon, str(r.ogrenci_id))


class DogrulaIstek(BaseModel):
    dogrula: bool = True


@yonetim_router.post("/portfolyo-kayit/{portfolyo_id}/dogrula", status_code=204)
def kayit_dogrula(portfolyo_id: int, istek: DogrulaIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r, o = _yonetim_kaydi(db, yon, portfolyo_id)
    db.execute(text("UPDATE portfolyo_kayitlari SET dogrulandi = :d, dogrulayan = :y, dogrulama_zamani = CASE WHEN :d THEN now() END WHERE id = :i"),
               {"d": istek.dogrula, "y": yon.ad_soyad if istek.dogrula else None, "i": r.id})
    denetim_yaz(db, yon, "portfolyo_dogrula" if istek.dogrula else "portfolyo_dogrulama_kaldir", "portfolyo_kayitlari", r.id,
                f"{o.ad_soyad}: {r.baslik}", o.okul_id)
    db.commit()


@yonetim_router.get("/portfolyo-kayit/{portfolyo_id}/belge")
def kayit_belgesi(portfolyo_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    r, _o = _yonetim_kaydi(db, yon, portfolyo_id)
    return _belge_cevabi(r)


# ----------------------------------------------------------------------------- PDF özgeçmiş
def _pdf_cevap(icerik: bytes, o: Ogrenci) -> Response:
    from app.api.raporlar import _dosya_adi
    return Response(icerik, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{_dosya_adi("Ozgecmis", o.ad_soyad)}.pdf"', "Cache-Control": "no-store"})


def _ay_yil(d: str | None) -> str:
    if not d:
        return ""
    AY = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    y, m, _g = d.split("-")
    return f"{AY[int(m) - 1]} {y}"


def _donem(k: dict) -> str:
    a, b = _ay_yil(k.get("baslangic")), _ay_yil(k.get("bitis"))
    if a and b:
        return a if a == b else f"{a} – {b}"
    return a + (" – devam ediyor" if a and k.get("tur") in ("gonullu", "staj", "gorev", "proje", "spor_sanat") else "") or b


def _pdf(db: Session, o: Ogrenci) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import KeepTogether, Spacer, Table, TableStyle

    from app.core.rapor.pdf import _belge, _e
    from app.core.rapor.veri import ogrenci_raporu_verisi
    v = portfolyo_verisi(db, o)
    rv = ogrenci_raporu_verisi(db, o)
    doc, tampon, st = _belge("Özgeçmiş", rv["okul"], rv["tarih"])
    p = _profil(db, o.id)
    sinif = " / ".join(filter(None, [o.sinif, o.sube]))
    h = [st.p(_e(o.ad_soyad), st.baslik),
         st.p(" · ".join(filter(None, [_e(rv["okul"]["ad"]), _e(sinif), _e(o.email) if p["eposta_goster"] else None])), st.alt)]
    if p["hakkimda"]:
        h += [st.p("Hakkımda", st.h2), st.p(_e(p["hakkimda"]).replace("\n", "<br/>"), st.govde)]
    if rv.get("hedef") or rv.get("gucluler"):
        h.append(st.p("Hedef ve güçlü yönler", st.h2))
        if rv.get("hedef"):
            h.append(st.p(f"<b>Hedef bölüm:</b> {_e(rv['hedef']['ad'])}", st.govde))
        if rv.get("gucluler"):
            h.append(st.p("<b>Güçlü yönler (Filizyol değerlendirmesi):</b> " + ", ".join(_e(x["ad"]) for x in rv["gucluler"][:5]), st.govde))
    sira = ["yarisma", "sertifika", "proje", "gonullu", "staj", "gorev", "spor_sanat", "diger"]
    for tur in sira:
        liste = [k for k in v["kayitlar"] if k["tur"] == tur]
        if not liste:
            continue
        h.append(st.p(TURLER[tur]["ad"], st.h2))
        for k in liste:
            sag = _donem(k)
            ust = f"<b>{_e(k['baslik'])}</b>" + (f" — {_e(k['kurum'])}" if k.get("kurum") else "")
            ek = [x for x in (k.get("derece"), f"{k['saat']} saat" if k.get("saat") else None) if x]
            satir = Table([[st.p(ust + (" · " + _e(" · ".join(ek)) if ek else ""), st.govde), st.p(_e(sag), st.kucuk)]],
                          colWidths=[126 * mm, 42 * mm])
            satir.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                                       ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                       ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
            parca = [satir]
            if k.get("aciklama"):
                parca.append(st.p(_e(k["aciklama"]), st.kucuk))
            alt = []
            if k["dogrulandi"]:
                alt.append(f'<font color="#4E8A4F"><b>OKUL ONAYLI</b></font> ({_e(k["dogrulayan"] or "")})')
            if k.get("link"):
                alt.append(f'<link href="{_e(k["link"])}" color="#2A78D6">{_e(k["link"][:70])}</link>')
            if alt:
                parca.append(st.p(" · ".join(alt), st.kucuk))
            parca.append(Spacer(1, 5))
            h.append(KeepTogether(parca))
    if v["kulupler"]:
        h += [st.p("Okul kulüpleri", st.h2),
              st.p(" · ".join(f"{_e(k['ad'])} ({_ay_yil(k['baslangic'])}’dan beri)" for k in v["kulupler"]), st.govde)]
    if p["diller"] or p["yetenekler"]:
        h.append(st.p("Diller ve yetenekler", st.h2))
        if p["diller"]:
            h.append(st.p("<b>Diller:</b> " + ", ".join(f"{_e(d['dil'])} ({_e(d['seviye'])})" for d in p["diller"]), st.govde))
        if p["yetenekler"]:
            h.append(st.p("<b>Yetenekler:</b> " + ", ".join(_e(y) for y in p["yetenekler"]), st.govde))
    if not v["kayitlar"] and not p["hakkimda"] and not v["kulupler"]:
        h.append(st.p("Portfolyoda henüz kayıt yok.", st.govde))
    h += [Spacer(1, 10), st.p("Bu özgeçmiş öğrencinin Filizyol e-Portfolyosundan oluşturulmuştur. “Okul onaylı” kayıtlar okul tarafından "
                              "belgesiyle doğrulanmıştır; diğerleri öğrencinin beyanıdır.", st.kucuk)]
    _ = colors
    doc.build(h)
    return tampon.getvalue()
