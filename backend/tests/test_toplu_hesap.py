"""[2026-11-11] Toplu hesap açma (öğrenci + okul yetkilisi), markalı giriş bilgileri Excel'i ve hoş geldin e-postaları."""
import base64
import io
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


@pytest.fixture
def ortam(db, monkeypatch):
    from app.core.security import erisim_tokeni_uret
    from app.api import toplu_hesap
    monkeypatch.setenv("TEST_EPOSTA_KAYDI", "1")
    # arka plan e-posta işi test işlemindeki verileri görsün (kendi oturumunu açmak yerine testin oturumu)
    monkeypatch.setattr(toplu_hesap, "_oturum_ac", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)
    ek = uuid.uuid4().hex[:6]
    a = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"Toplu Fen Lisesi {ek}"}).scalar()
    b = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"Toplu Anadolu Lisesi {ek}"}).scalar()
    s, y = uuid.uuid4(), uuid.uuid4()
    for i, rol, okul in ((s, "super_admin", None), (y, "okul_yetkilisi", a)):
        db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, sifre_degistirmeli,
                           olusturulma_zamani) VALUES (:i, 'TH Kisi', :e, 'x', :r, :o, TRUE, FALSE, now())"""),
                   {"i": i, "e": f"{i.hex[:8]}@th-test.com", "r": rol, "o": okul})
    db.commit()
    return {"a": a, "b": b, "ek": ek, "super": {"Authorization": f"Bearer {erisim_tokeni_uret(s, 'super_admin')}"},
            "yet": {"Authorization": f"Bearer {erisim_tokeni_uret(y, 'okul_yetkilisi')}"}}


def _dosya(istemci, h, satirlar):
    """Sistemin kendi markalı şablonunu indirip örnek satırların yerine verilen satırları yazar (amblem/açıklama satırları
    olduğu gibi kalır: geri yüklemede başlık satırının bulunması da sınanır)."""
    import openpyxl
    r = istemci.get("/yonetim/toplu-hesap/sablon", headers=h)
    assert r.status_code == 200
    wb = openpyxl.load_workbook(io.BytesIO(base64.b64decode(r.json()["icerik_base64"])))
    ws = wb.active
    bas = next(c.row for c in ws["A"] if c.value == "Ad Soyad")
    assert bas > 6                                           # başlık, amblem ve açıklamanın altında
    ws.delete_rows(bas + 1, 10)
    for i, s in enumerate(satirlar, start=bas + 1):
        for j, v in enumerate(s, start=1):
            ws.cell(row=i, column=j, value=v)
    b = io.BytesIO()
    wb.save(b)
    return {"dosya_adi": "hesaplar.xlsx", "icerik_base64": base64.b64encode(b.getvalue()).decode()}


@db_gerekli
def test_super_admin_toplu_acar_excel_ve_eposta(istemci, db, ortam):
    from app.core import eposta_servisi as ep
    ek = ortam["ek"]
    ep.GONDERILENLER.clear()
    govde = _dosya(istemci, ortam["super"], [
        ["Ali Yılmaz", f"ali.{ek}@th-test.com", "Öğrenci", "toplu fen", 11, "A"],
        ["Zeynep Kaya", f"zeynep.{ek}@th-test.com", "Rehber Öğretmen", "", "", ""],
        ["Can Demir", f"can.{ek}@th-test.com", "", f"Toplu Anadolu Lisesi {ek}", "12", "B"],
        ["Hata Satırı", "gecersiz", "Öğrenci", "", "", ""],
        ["Yok Okul", f"yok.{ek}@th-test.com", "Öğrenci", "Olmayan Koleji", "", ""],
    ])
    r = istemci.post("/yonetim/toplu-hesap/onizle", headers=ortam["super"], json={**govde, "okul_id": ortam["a"]})
    assert r.status_code == 200, r.text
    s = {x["ad_soyad"]: x for x in r.json()["satirlar"]}
    assert s["Ali Yılmaz"]["okul_id"] == ortam["a"] and s["Ali Yılmaz"]["tur"] == "ogrenci"   # kısa ad eşleşir
    assert s["Zeynep Kaya"]["tur"] == "yetkili" and s["Zeynep Kaya"]["unvan"] == "Rehber Öğretmen"
    assert s["Zeynep Kaya"]["okul_id"] == ortam["a"]                                          # boş okul → seçili okul
    assert s["Can Demir"]["okul_id"] == ortam["b"] and "Görev boş" in s["Can Demir"]["uyari"]
    assert "E-posta geçersiz" in s["Hata Satırı"]["hata"] and "Okul bulunamadı" in s["Yok Okul"]["hata"]
    assert r.json()["ozet"]["acilacak_ogrenci"] == 2 and r.json()["ozet"]["acilacak_yetkili"] == 1

    r = istemci.post("/yonetim/toplu-hesap/olustur", headers=ortam["super"], json={**govde, "okul_id": ortam["a"], "eposta_gonder": True})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["olusturulan"] == 3 and len(j["atlanan"]) == 2
    db.expire_all()
    y = db.execute(text("SELECT rol, unvan, okul_id, sifre_degistirmeli FROM admin_kullanicilar WHERE email = :e"),
                   {"e": f"zeynep.{ek}@th-test.com"}).first()
    assert tuple(y) == ("okul_yetkilisi", "Rehber Öğretmen", ortam["a"], True)
    o = db.execute(text("SELECT okul_id, sinif, sube FROM ogrenciler WHERE email = :e"), {"e": f"can.{ek}@th-test.com"}).first()
    assert o[0] == ortam["b"] and o[2] == "B"

    # markalı Excel: amblem resmi, Filizyol başlığı, geçici şifreler
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(base64.b64decode(j["icerik_base64"])))
    ws = wb.active
    assert ws["B1"].value == "Filizyol" and len(ws._images) == 1
    bas = next(c.row for c in ws["A"] if c.value == "Ad Soyad")
    basliklar = [c.value for c in ws[bas]]
    assert "Geçici Şifre" in basliklar
    sifreler = {ws.cell(row=i, column=1).value: ws.cell(row=i, column=basliklar.index("Geçici Şifre") + 1).value
                for i in range(bas + 1, bas + 4)}
    assert set(sifreler) == {"Ali Yılmaz", "Zeynep Kaya", "Can Demir"} and all(len(v) >= 6 for v in sifreler.values())

    # hoş geldin e-postaları: yetkiliye "siz", öğrenciye "sen" dili; geçici şifre içerir
    gidenler = {g["alici"]: g for g in ep.GONDERILENLER}
    assert set(gidenler) == {f"ali.{ek}@th-test.com", f"zeynep.{ek}@th-test.com", f"can.{ek}@th-test.com"}
    assert "aktif hale getirilmiştir" in gidenler[f"zeynep.{ek}@th-test.com"]["konu"]
    assert sifreler["Zeynep Kaya"] in gidenler[f"zeynep.{ek}@th-test.com"]["metin"]
    assert "Hoş geldin, Ali Yılmaz" in gidenler[f"ali.{ek}@th-test.com"]["html"]
    assert sifreler["Ali Yılmaz"] in gidenler[f"ali.{ek}@th-test.com"]["metin"]

    # aynı dosya tekrar: hesaplar kayıtlı, yeniden açılmaz
    r = istemci.post("/yonetim/toplu-hesap/olustur", headers=ortam["super"], json={**govde, "okul_id": ortam["a"]})
    assert r.status_code == 400


@db_gerekli
def test_okul_yetkilisi_yalniz_kendi_okuluna_ogrenci_acar(istemci, db, ortam):
    ek = ortam["ek"]
    govde = _dosya(istemci, ortam["yet"], [
        ["Ece Tan", f"ece.{ek}@th-test.com", "Öğrenci", "", 9, "C"],
        ["Mert Ak", f"mert.{ek}@th-test.com", "Müdür Yardımcısı", "", "", ""],
        ["Deniz Su", f"deniz.{ek}@th-test.com", "Öğrenci", f"Toplu Anadolu Lisesi {ek}", "", ""],
    ])
    r = istemci.post("/yonetim/toplu-hesap/onizle", headers=ortam["yet"], json={**govde, "okul_id": ortam["b"]})
    s = {x["ad_soyad"]: x for x in r.json()["satirlar"]}
    assert s["Ece Tan"]["okul_id"] == ortam["a"] and not s["Ece Tan"]["hata"]   # seçilen okul değil, kendi okulu
    assert "yalnızca süper admin" in s["Mert Ak"]["hata"]
    assert "kendi okulunuza" in s["Deniz Su"]["hata"]
    r = istemci.post("/yonetim/toplu-hesap/olustur", headers=ortam["yet"], json={**govde, "eposta_gonder": False})
    assert r.status_code == 200 and r.json()["olusturulan"] == 1
    # hoş geldin: okul yetkilisi başka okula ve yetkililere gönderemez
    assert istemci.post("/yonetim/toplu-hesap/hosgeldin", headers=ortam["yet"], json={"okul_id": ortam["b"]}).status_code == 403
    assert istemci.post("/yonetim/toplu-hesap/hosgeldin", headers=ortam["yet"],
                        json={"okul_id": ortam["a"], "kime": "yetkili"}).status_code == 403


@db_gerekli
def test_tek_tusla_okulun_tamamina_hosgeldin(istemci, db, ortam):
    from app.core import eposta_servisi as ep
    from app.core.gizli_metin import sifrele
    ek, a = ortam["ek"], ortam["a"]
    for ad, sd in (("Gecici", True), ("Kendi", False)):
        db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, sifre_degistirmeli, gecici_sifre_sifreli,
                           olusturulma_zamani, guncelleme_zamani) VALUES (:i, :ad, :e, 'x', :o, :sd, :g, now(), now())"""),
                   {"i": uuid.uuid4(), "ad": f"{ad} Ogrenci", "e": f"{ad.lower()}.{ek}@th-test.com", "o": a, "sd": sd,
                    "g": sifrele("abcd-2345") if sd else None})
    db.commit()

    oz = istemci.get(f"/yonetim/toplu-hesap/hosgeldin/ozet?okul_id={a}", headers=ortam["super"]).json()
    assert oz["ogrenci"]["toplam"] == 2 and oz["ogrenci"]["gonderilmis"] == 0 and oz["yetkili"]["toplam"] == 1

    ep.GONDERILENLER.clear()
    r = istemci.post("/yonetim/toplu-hesap/hosgeldin", headers=ortam["super"], json={"okul_id": a, "kime": "hepsi"})
    assert r.status_code == 200, r.text
    assert r.json()["toplam"] == 3
    d = istemci.get(f"/yonetim/toplu-hesap/hosgeldin/durum/{r.json()['is_id']}", headers=ortam["super"]).json()
    assert d["bitti"] and d["gonderilen"] == 3
    g = {x["alici"]: x for x in ep.GONDERILENLER}
    assert "abcd-2345" in g[f"gecici.{ek}@th-test.com"]["metin"]
    assert "Şifremi unuttum" in g[f"kendi.{ek}@th-test.com"]["metin"]              # şifresini değiştirmiş: şifre yazılmaz

    oz = istemci.get(f"/yonetim/toplu-hesap/hosgeldin/ozet?okul_id={a}", headers=ortam["super"]).json()
    assert oz["ogrenci"]["gonderilmis"] == 2 and oz["yetkili"]["gonderilmis"] == 1
    # yalnız gönderilmemişler: kimse kalmadı
    r = istemci.post("/yonetim/toplu-hesap/hosgeldin", headers=ortam["super"], json={"okul_id": a, "yalniz_gonderilmemis": True})
    assert r.status_code == 400 and "daha önce" in r.json()["detail"]


def test_eposta_sablonlari_hedef_kitleye_gore():
    from app.core import eposta_servisi as ep
    k1, h1, m1 = ep.ogrenci_hosgeldin_epostasi("Ayşe", "X Lisesi", "a@b.com", "kemr-4827", "https://site/giris")
    k2, h2, m2 = ep.yetkili_hosgeldin_epostasi("Zeynep", "X Lisesi", "Müdür", "z@b.com", None, "https://site/giris")
    assert "hoş geldin" in k1.lower() and "kemr-4827" in h1 and "https://site/giris" in h1
    assert "aktif hale getirilmiştir" in k2 and "Sayın Zeynep (Müdür)" in m2 and "Şifremi unuttum" in m2
    assert "<script" not in ep.ogrenci_hosgeldin_epostasi("<script>", None, "a@b.com", None, "u")[1]
    # okulun paketinde olmayan özellik e-postada anılmaz; madde listesi / iç işlem metni yok
    _, _, m3 = ep.ogrenci_hosgeldin_epostasi("Ayşe", "X", "a@b.com", None, "u", ["kocluk", "net_takibi"])
    assert "Net Takibi" in m3 and "İş Hayatı" not in m3
    _, _, m4 = ep.yetkili_hosgeldin_epostasi("Zeynep", "X", None, "z@b.com", "kemr-4827", "u", ["kocluk"])
    assert "paketinde" not in m4 and "Excel" not in m4 and "geçici şifre listesi" not in m4
