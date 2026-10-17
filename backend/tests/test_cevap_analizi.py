"""
[2026-10-17] Cevap ve uyum matrisleri:
  * erişim: süper admin + okul yetkilisi (yalnızca kendi okulu); öğrenci erişemez;
  * yöntem matrisi yalnızca süper admine döner;
  * katkı = "bu özellik olmasaydı" (gösterilen puanla aynı hesap);
  * Excel: beklenen sayfalar, yöntem sayfası yalnızca süper admin.
"""
import io
import uuid

import numpy as np
from sqlalchemy import text

from app.core import uyum_aciklama as ua
from tests.conftest import db_gerekli


def test_katki_birakmali_ve_tutarli():
    rng = np.random.default_rng(7)
    X = rng.uniform(20, 100, size=(40, 6))
    w = rng.uniform(0.5, 2, size=6)
    K = ua.ozellik_katkilari(X, w)
    assert K.shape == X.shape
    tam = ua._ortalama(X, w)
    # j. sütun = tam puan − j. özellik çıkarılınca hesaplanan puan
    j = 3
    maske = np.arange(6) != j
    assert np.allclose(K[:, j], tam - ua._ortalama(X[:, maske], w[maske]))
    # bir bölümde bir özellik çok iyiyse (diğer bölümlere göre) o özelliğin katkısı o bölümde pozitif olmalı
    X2 = np.full((10, 4), 60.0) + rng.uniform(-3, 3, size=(10, 4))
    X2[0, 2] = 100.0
    X2[1:, 2] = 30.0
    K2 = ua.ozellik_katkilari(X2, np.ones(4))
    assert K2[0, 2] > 0
    assert K2[0, 2] == K2[0].max()


def _ogrenci(db, okul_id):
    oid = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Başka Okul Öğrencisi', :e, 'x', :o, now(), now())"""),
               {"i": oid, "e": f"bo.{oid.hex[:8]}@test.invalid", "o": okul_id})
    db.commit()
    return oid


def _kendi_ogrencisi(db, okul_id):
    return db.execute(text("SELECT id FROM ogrenciler WHERE okul_id=:o LIMIT 1"), {"o": okul_id}).scalar()


@db_gerekli
def test_yetkili_kendi_okulu_gorur_baska_okulu_goremez(istemci, db, kisiler):
    kendi = _kendi_ogrencisi(db, kisiler["okul_a"])
    r = istemci.get(f"/yonetim/ogrenci/{kendi}/cevap-analizi", headers=kisiler["yetkili"])
    assert r.status_code == 200, r.text
    assert r.json()["tur"] is None                                   # teste başlamamış öğrenci
    baska = _ogrenci(db, kisiler["okul_b"])
    for yol in ("cevap-analizi", "cevap-analizi.xlsx"):
        r = istemci.get(f"/yonetim/ogrenci/{baska}/{yol}", headers=kisiler["yetkili"])
        assert r.status_code == 403, (yol, r.text)
    assert istemci.get(f"/yonetim/ogrenci/{baska}/cevap-analizi", headers=kisiler["super"]).status_code == 200


@db_gerekli
def test_ogrenci_erisemez(istemci, db, kisiler):
    kendi = _kendi_ogrencisi(db, kisiler["okul_a"])
    for yol in ("cevap-analizi", "cevap-analizi.xlsx"):
        r = istemci.get(f"/yonetim/ogrenci/{kendi}/{yol}", headers=kisiler["ogrenci"])
        assert r.status_code in (401, 403), (yol, r.status_code)


def _tamamlanmis(db):
    """Son turu tamamlanmış ve uyum skoru kayıtlı, okula bağlı bir öğrenci."""
    return db.execute(text("""SELECT o.id, o.okul_id FROM ogrenciler o
                              JOIN LATERAL (SELECT id, durum FROM ogrenci_degerlendirme_turu t WHERE t.ogrenci_id = o.id
                                            ORDER BY t.tur_no DESC LIMIT 1) son ON TRUE
                              WHERE o.okul_id IS NOT NULL AND son.durum = 'tamamlandi'
                                AND EXISTS (SELECT 1 FROM ogrenci_bolum_uyum_skorlari s WHERE s.tur_id = son.id)
                              LIMIT 1""")).first()


def _yetkili_tokeni(db, okul_id):
    from app.core.security import erisim_tokeni_uret
    kid = uuid.uuid4()
    db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, olusturulma_zamani)
                       VALUES (:i, 'Test yetkili', :e, 'x', 'okul_yetkilisi', :o, TRUE, now())"""),
               {"i": kid, "e": f"yet.{kid.hex[:8]}@test.invalid", "o": okul_id})
    db.commit()
    return {"Authorization": f"Bearer {erisim_tokeni_uret(kid, 'okul_yetkilisi')}"}


@db_gerekli
def test_matris_ve_yontem_kapsami(istemci, db, kisiler):
    satir = _tamamlanmis(db)
    if satir is None:
        return
    oid, okul = satir
    sa = istemci.get(f"/yonetim/ogrenci/{oid}/cevap-analizi", headers=kisiler["super"]).json()
    m = sa["matris"]
    assert m and m["yontem_adlari"] and len(m["yontem_adlari"]) == 10
    assert all("yontemler" in b for b in m["bolumler"])
    sira = [b["sira"] for b in m["bolumler"]]
    assert sira[:10] == list(range(1, 11))                          # varsayılan: ilk 10 (+ hedef) + son 3
    b0 = m["bolumler"][0]
    assert len(b0["hucreler"]) == len(m["ozellikler"])
    assert all(x["katki"] > 0 for x in b0["yukselten"]) and all(x["katki"] < 0 for x in b0["dusuren"])
    assert all(h["sinif"] in {"uyumlu", "fazla", "eksik", "belirgin_fazla", "belirgin_eksik"} for h in b0["hucreler"])

    yt = istemci.get(f"/yonetim/ogrenci/{oid}/cevap-analizi", headers=_yetkili_tokeni(db, okul)).json()
    assert yt["matris"] and yt["matris"]["yontem_adlari"] is None
    assert all("yontemler" not in b and "kendall_w" not in b for b in yt["matris"]["bolumler"])
    assert yt["cevaplar"] and yt["okuma_notu"]

    # bölüm seçimi
    secim = [m["bolumler"][-1]["bolum_id"], m["bolumler"][0]["bolum_id"]]
    r = istemci.get(f"/yonetim/ogrenci/{oid}/cevap-analizi?bolumler={secim[0]},{secim[1]}", headers=kisiler["super"]).json()
    assert [b["bolum_id"] for b in r["matris"]["bolumler"]] == secim


@db_gerekli
def test_excel_sayfalari(istemci, db, kisiler):
    from openpyxl import load_workbook
    satir = _tamamlanmis(db)
    if satir is None:
        return
    oid, okul = satir
    temel = ["Okuma notu", "Cevaplar", "Özellikler", "Uyum (fark)", "Katkılar", "Bölüm beklentisi"]
    r = istemci.get(f"/yonetim/ogrenci/{oid}/cevap-analizi.xlsx", headers=kisiler["super"])
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert load_workbook(io.BytesIO(r.content)).sheetnames == temel + ["Yöntemler"]
    r = istemci.get(f"/yonetim/ogrenci/{oid}/cevap-analizi.xlsx", headers=_yetkili_tokeni(db, okul))
    assert r.status_code == 200
    wb = load_workbook(io.BytesIO(r.content))
    assert wb.sheetnames == temel
    assert wb["Uyum (fark)"].max_row > 100                          # öğrenci satırı + tüm bölümler


def test_hedef_kiyasi_isaret_ve_yapi():
    """Hedef kıyası: fark = hedef − bölüm; özellik etkisi = hedef katkısı − bölüm katkısı."""
    def bolum(i, uyum, katkilar, hedef=False):
        return {"bolum_id": i, "bolum": f"B{i}", "sira": i, "uyum": uyum, "hedef": hedef,
                "hucreler": [{"katki": k, "sinif": "uyumlu"} for k in katkilar], "yukselten": [], "dusuren": []}
    m = {"ozellikler": [{"kod": f"X{j}", "ad": f"Ö{j}"} for j in range(3)], "bolum_sayisi": 301,
         "bolumler": [bolum(5, 60.0, [1.0, 0.0, -2.0], hedef=True), bolum(1, 70.0, [0.0, 0.1, 1.0])]}
    k = ua.hedef_kiyasi(m)
    assert k["hedef"]["bolum_id"] == 5 and len(k["satirlar"]) == 1
    s = k["satirlar"][0]
    assert s["fark"] == -10.0
    assert [x["kod"] for x in s["geride_birakan"]] == ["X2"] and s["geride_birakan"][0]["etki"] == -3.0
    assert [x["kod"] for x in s["one_cikaran"]] == ["X0"]
    m["bolumler"][0]["hedef"] = False
    k2 = ua.hedef_kiyasi(m)
    assert k2["hedef"] is None and len(k2["satirlar"]) == 2 and "yukselten" in k2["satirlar"][0]


@db_gerekli
def test_rapor_secimi_hedef_ilk_ve_sinir(db):
    from app.models import Ogrenci, OgrenciHedefBolum
    h = db.query(OgrenciHedefBolum).filter(OgrenciHedefBolum.aktif_mi.is_(True)).all()
    for x in h:
        o = db.get(Ogrenci, x.ogrenci_id)
        tur = ua.son_tamamlanan_tur(db, o)
        if tur is None:
            continue
        tum = [r.bolum_id for r in ua.rapor_secimi(db, o, tur)["sira"]]
        s = ua.rapor_secimi(db, o, tur, tum[-20:])
        assert s["secim"][0] == x.bolum_id == s["hedef_id"]
        assert len(s["secim"]) == ua.RAPOR_BOLUM_SINIRI and s["kirpildi"]
        v = ua.rapor_secimi(db, o, tur)
        assert v["secim"][0] == x.bolum_id and len(v["secim"]) <= ua.RAPOR_BOLUM_SINIRI
        return


@db_gerekli
def test_rapor_bolum_secimi_uc_noktalari(istemci, db, kisiler):
    satir = _tamamlanmis(db)
    if satir is None:
        return
    oid, okul = satir
    yt = _yetkili_tokeni(db, okul)
    r = istemci.get(f"/yonetim/ogrenci/{oid}/rapor-bolumleri", headers=yt)
    assert r.status_code == 200 and r.json()["sinir"] == ua.RAPOR_BOLUM_SINIRI
    ids = ",".join(str(x["id"]) for x in r.json()["varsayilan"][:2])
    for tur in ("ogrenci", "veli", "yonetici"):
        r = istemci.get(f"/yonetim/ogrenci/{oid}/rapor?tur={tur}&bicim=pdf&bolumler={ids}", headers=yt)
        assert r.status_code == 200 and r.content[:4] == b"%PDF", tur
    baska = _ogrenci(db, kisiler["okul_b"])
    assert istemci.get(f"/yonetim/ogrenci/{baska}/rapor-bolumleri", headers=kisiler["yetkili"]).status_code == 403
