"""[2026-11-24] TYT Fen'in isteğe bağlı branş kırılımı (Fizik/Kimya/Biyoloji) — rehberlik birimi raporu önerisi.

Geriye dönük uyum: toplu "tyt_fen" girişi aynen çalışır; branş girildiğinde hedef kıyasında TYT Fen'e toplanır;
ikisi bir arada girilemez."""
import pytest

from tests.conftest import db_gerekli


@db_gerekli
def test_brans_bazli_tyt_fen_girilebilir(istemci, db, kisiler):
    h = kisiler["ogrenci"]
    # /yapi branş seçeneğini sunar
    y = istemci.get("/ogrenci/net/yapi", headers=h).json()
    assert "tyt_fen" in y["brans_testleri"]
    kodlar = [t["kod"] for t in y["brans_testleri"]["tyt_fen"]]
    assert kodlar == ["tyt_fiz", "tyt_kim", "tyt_biy"]
    assert [t["soru"] for t in y["brans_testleri"]["tyt_fen"]] == [7, 7, 6]

    # branş bazlı deneme eklenebilir
    r = istemci.post("/ogrenci/net/denemeler", headers=h, json={
        "tarih": "2026-11-20", "oturum": "TYT", "ad": "Deneme 1",
        "dersler": {"tyt_mat": {"d": 30, "y": 4}, "tyt_fiz": {"d": 6, "y": 1}, "tyt_kim": {"d": 5, "y": 0}, "tyt_biy": {"d": 6, "y": 0}}})
    assert r.status_code == 200, r.text
    d = r.json()
    assert set(d["dersler"]) == {"tyt_mat", "tyt_fiz", "tyt_kim", "tyt_biy"}
    assert d["dersler"]["tyt_fiz"]["net"] == 5.75
    # toplam = 29 + 5.75 + 5 + 6 = 45.75
    assert d["toplam_net"] == 45.75


@db_gerekli
def test_toplu_tyt_fen_hala_calisir(istemci, db, kisiler):
    r = istemci.post("/ogrenci/net/denemeler", headers=kisiler["ogrenci"], json={
        "tarih": "2026-11-20", "oturum": "TYT", "dersler": {"tyt_fen": {"d": 15, "y": 4}}})
    assert r.status_code == 200, r.text
    assert r.json()["dersler"]["tyt_fen"]["net"] == 14.0


@db_gerekli
def test_toplu_ve_brans_birlikte_reddedilir(istemci, db, kisiler):
    r = istemci.post("/ogrenci/net/denemeler", headers=kisiler["ogrenci"], json={
        "tarih": "2026-11-20", "oturum": "TYT", "dersler": {"tyt_fen": {"d": 10, "y": 0}, "tyt_fiz": {"d": 5, "y": 0}}})
    assert r.status_code == 400
    assert "ikisini birden değil" in r.json()["detail"]


@db_gerekli
def test_brans_soru_sayisi_asilamaz(istemci, db, kisiler):
    r = istemci.post("/ogrenci/net/denemeler", headers=kisiler["ogrenci"], json={
        "tarih": "2026-11-20", "oturum": "TYT", "dersler": {"tyt_biy": {"d": 7, "y": 0}}})  # biyoloji 6 soru
    assert r.status_code == 400
    assert "en fazla 6" in r.json()["detail"]


@db_gerekli
def test_brans_hedef_kiyasinda_tyt_fene_toplanir(istemci, db, kisiler, monkeypatch):
    # sahte YÖK Atlas hedefi: tytFenNet için bir hedef net
    from app.api import net_takibi
    monkeypatch.setattr(net_takibi, "_net_hedefi", lambda db, o: {
        "puan_turu": "SAY", "son": {"yil": 2025, "netler": {"tyt_fen": 15.0, "tyt_mat": 30.0}}, "gecmis": [], "ortalama": {}})
    istemci.post("/ogrenci/net/denemeler", headers=kisiler["ogrenci"], json={
        "tarih": "2026-11-20", "oturum": "TYT",
        "dersler": {"tyt_fiz": {"d": 6, "y": 1}, "tyt_kim": {"d": 5, "y": 0}, "tyt_biy": {"d": 6, "y": 0}}})
    k = istemci.get("/ogrenci/net/kiyas", headers=kisiler["ogrenci"]).json()
    fen = next(s for s in k["satirlar"] if s["kod"] == "tyt_fen")
    assert fen["ben"] == 16.75   # branşlar toplanıp TYT Fen olarak kıyaslandı
    assert fen["hedef"] == 15.0 and fen["fark"] == 1.75


@db_gerekli
def test_okul_excel_brans_sablonu_ve_yukleme(istemci, db, kisiler):
    """Okul, TYT Fen branş sütunlu şablonla toplu deneme yükleyebilir; branşlar denemede ayrı saklanır ve toplam doğru."""
    import base64, io, uuid
    import openpyxl
    from sqlalchemy import text
    okul, h = kisiler["okul_a"], kisiler["yetkili"]
    oid = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, ogrenci_no, sinif, sube, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i,'Deniz Yıldız',:e,'x',:o,'4567','12. Sınıf','A',now(),now())"""),
               {"i": oid, "e": f"deniz.{uuid.uuid4().hex[:6]}@test.invalid", "o": okul})
    db.commit()

    # branş sütunlu şablon iner
    s = istemci.get(f"/yonetim/okul/{okul}/deneme-sablonu?oturum=TYT&brans=1", headers=h).json()
    wb = openpyxl.load_workbook(io.BytesIO(base64.b64decode(s["icerik_base64"])))
    ws = wb.active
    basliklar = [c.value for c in next(r for r in ws.iter_rows() if any((c.value or "") == "Ad Soyad" for c in r))]
    assert "TYT Fizik D" in basliklar and "TYT Kimya D" in basliklar and "TYT Biyoloji D" in basliklar
    assert "Fen Bilimleri D" not in basliklar

    # Deniz'in satırına branş netleri yaz
    for r in ws.iter_rows():
        if any((c.value or "") == "Deniz Yıldız" for c in r):
            kol = {v: i for i, v in enumerate(basliklar)}
            r[kol["TYT Fizik D"]].value, r[kol["TYT Fizik Y"]].value = 6, 1
            r[kol["TYT Kimya D"]].value, r[kol["TYT Kimya Y"]].value = 5, 0
            r[kol["TYT Biyoloji D"]].value, r[kol["TYT Biyoloji Y"]].value = 6, 0
            r[kol["Temel Matematik D"]].value, r[kol["Temel Matematik Y"]].value = 30, 4
    b = io.BytesIO(); wb.save(b)
    govde = {"oturum": "TYT", "dosya_adi": "tyt.xlsx", "icerik_base64": base64.b64encode(b.getvalue()).decode()}

    on = istemci.post(f"/yonetim/okul/{okul}/deneme-onizle", headers=h, json=govde).json()
    assert {t["kod"] for t in on["testler"]} >= {"tyt_fiz", "tyt_kim", "tyt_biy", "tyt_mat"}
    satir = next(s for s in on["satirlar"] if s["ad_soyad"] == "Deniz Yıldız")
    assert not satir["hata"] and satir["dersler"]["tyt_fiz"]["net"] == 5.75
    assert satir["toplam_net"] == 45.75   # 29 + 5.75 + 5 + 6

    kayit = istemci.post(f"/yonetim/okul/{okul}/okul-denemeleri", headers=h,
                         json={**govde, "ad": "Okul TYT 1", "tarih": "2026-11-20"})
    assert kayit.status_code == 201, kayit.text
    did = kayit.json()["id"]
    det = istemci.get(f"/yonetim/okul-deneme/{did}", headers=h).json()
    assert {t["kod"] for t in det["testler"]} >= {"tyt_fiz", "tyt_kim", "tyt_biy"}   # detay branş sütunlarını gösterir
    sonuc = next(s for s in det["sonuclar"] if s["ad_soyad"] == "Deniz Yıldız")
    assert sonuc["dersler"]["tyt_biy"] == 6.0
