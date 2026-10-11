"""[2026-10-11] Hata izleme: maskeleme, gruplama, ara katman (veritabansız) + gruplu kayıt (PostgreSQL, geri alınır)."""
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core import hata_izleme as hi
from tests.conftest import db_gerekli


@pytest.mark.parametrize("girdi,olmamali,olmali", [
    ("Kullanıcı ayse.yilmaz@okul.k12.tr bulunamadı", "ayse.yilmaz@okul.k12.tr", "<e-posta>"),
    ("tel: 0532 123 45 67 kayıtlı", "123 45 67", "<telefon>"),
    ("tel +90 532 123 45 67", "532 123", "<telefon>"),
    ("TC 12345678950 geçersiz", "12345678950", "<tc>"),
    ("Authorization: Bearer abc.def-ghi", "abc.def-ghi", "<token>"),
    ("token eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl sızdı", "eyJhbGciOiJIUzI1NiJ9", "<token>"),
    ('{"email": "x", "sifre": "Gizli123!"}', "Gizli123!", "<gizli>"),
    ("password=hunter2&kullanici=a", "hunter2", "<gizli>"),
    ("yeni_sifre: 'Parola99'", "Parola99", "<gizli>"),
    ("foto data:image/png;base64,iVBORw0KGgoAAAANSUhEUg== bozuk", "iVBORw0KGgo", "<base64>"),
    ("(psycopg2.errors.UniqueViolation) duplicate key\n[SQL: INSERT INTO ogrenciler (email) VALUES (%(email)s)]\n"
     "[parameters: {'email': 'ali@x.com', 'ad': 'Ali Veli'}]\n(Background on this error at: https://sqlalche.me/e/20/gkpj)",
     "Ali Veli", "[parameters: <ayıklandı>]"),
])
def test_maskele(girdi, olmamali, olmali):
    m = hi.maskele(girdi)
    assert olmamali not in m and olmali in m


def test_maskele_kisisel_olmayan_metni_bozmaz():
    s = "KeyError: 'katman_kod' at app/api/ogrenci.py line 120; okul_id=42"
    assert hi.maskele(s) == s


def test_maskele_uzunluk():
    assert len(hi.maskele("a b " * 2000, en_fazla=100)) <= 101


def test_yigin_kisalt_son_kismi_korur():
    yigin = "\n".join(f"satır {i}" for i in range(500)) + "\nValueError: kotu@ornek.com"
    k = hi.yigin_kisalt(yigin, en_fazla_satir=20)
    assert "satır 499" in k and "satır 3\n" not in k and "kısaltıldı" in k and "kotu@ornek.com" not in k


def test_parmak_izi_kimlikleri_yok_sayar():
    a = hi.parmak_izi("sunucu", "KeyError", "/yonetim/okul/12/ogrenciler", "api/x.py:f")
    b = hi.parmak_izi("sunucu", "KeyError", "/yonetim/okul/99/ogrenciler", "api/x.py:f")
    c = hi.parmak_izi("sunucu", "ValueError", "/yonetim/okul/99/ogrenciler", "api/x.py:f")
    assert a == b != c
    assert hi.yol_kalibi("/ogrenci/3fa85f64-5717-4562-b3fc-2c963f66afa6/rapor") == "/ogrenci/{id}/rapor"


def test_istemci_konumu_derleme_hashini_yok_sayar():
    y1 = "TypeError: x\n    at f (https://site.app/assets/index-AbC123xy.js:10:20)"
    y2 = "TypeError: x\n    at f (https://site.app/assets/index-ZZZ999qq.js:10:20)"
    assert hi.istemci_konumu(y1, "x is undefined") == hi.istemci_konumu(y2, "x is undefined")


def _hatali_uygulama(kayitlar):
    async def patla(request):
        raise ValueError("ogrenci ali@x.com için hesap yok")

    async def tamam(request):
        return JSONResponse({"ok": True})

    # Gerçek uygulamadaki gibi kullanıcı ara katmanı olarak (Starlette'in ServerErrorMiddleware'inin İÇİNDE)
    from starlette.middleware import Middleware
    return Starlette(routes=[Route("/patla", patla), Route("/tamam", tamam)], middleware=[Middleware(hi.HataYakalamaAraKatmani)])


def test_ara_katman_500_genel_mesaj_ve_istek_kimligi(monkeypatch):
    yakalanan = []
    monkeypatch.setattr(hi, "kaydet", lambda **k: yakalanan.append(k))
    c = TestClient(_hatali_uygulama(yakalanan), raise_server_exceptions=False)
    r = c.get("/patla")
    assert r.status_code == 500
    kimlik = r.headers["x-istek-kimligi"]
    assert kimlik and r.json()["istek_kimligi"] == kimlik
    assert "Beklenmeyen bir hata" in r.json()["detail"] and kimlik in r.json()["detail"]
    assert "ali@x.com" not in r.text                 # ayrıntı kullanıcıya sızmaz
    assert yakalanan and yakalanan[0]["istisna_turu"] == "ValueError" and yakalanan[0]["istek_kimligi"] == kimlik
    assert yakalanan[0]["durum_kodu"] == 500 and yakalanan[0]["yol"] == "/patla"


def test_ara_katman_her_yanita_istek_kimligi():
    c = TestClient(_hatali_uygulama([]))
    r = c.get("/tamam")
    assert r.status_code == 200 and len(r.headers["x-istek-kimligi"]) >= 8
    r2 = c.get("/tamam", headers={"X-Istek-Kimligi": "istemci-kimligi-123"})
    assert r2.headers["x-istek-kimligi"] == "istemci-kimligi-123"
    r3 = c.get("/tamam", headers={"X-Istek-Kimligi": "<script>"})
    assert r3.headers["x-istek-kimligi"] != "<script>"


def test_kaydet_veritabani_yoksa_sessiz():
    def bozuk():
        raise RuntimeError("bağlantı yok")
    assert hi.kaydet(kaynak="sunucu", yol="/x", metod="GET", durum_kodu=500, istisna_turu="E", mesaj="m", yigin="",
                     kullanici_tipi="anonim", istek_kimligi="k", konum="benzersiz-konum-1", db_fabrikasi=bozuk) is None


def test_sentry_dsn_yoksa_atlanir(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    assert hi.sentry_baslat() is False


# ------------------------------------------------------------------ PostgreSQL ile (işlem sonunda geri alınır)
@db_gerekli
def test_kaydet_gruplar_ve_maskeler(db, db_fabrikasi, monkeypatch):
    from sqlalchemy import text
    monkeypatch.setattr(hi, "YAZIM_ARALIGI_SN", 0)
    ortak = dict(kaynak="sunucu", metod="POST", durum_kodu=500, istisna_turu="ZeroDivisionError", yigin="Traceback\n  sifre=abc123",
                 kullanici_tipi="ogrenci", konum="api/test.py:fonk-gruplama", db_fabrikasi=db_fabrikasi)
    r1 = hi.kaydet(yol="/yonetim/okul/1/x", mesaj="bölme hatası ayse@x.com", istek_kimligi="k1", **ortak)
    r2 = hi.kaydet(yol="/yonetim/okul/2/x", mesaj="bölme hatası 05321234567", istek_kimligi="k2", **ortak)
    assert r1["yeni"] is True and r2["yeni"] is False and r1["id"] == r2["id"]
    k = db.execute(text("SELECT * FROM hata_kayitlari WHERE id = :i"), {"i": r1["id"]}).mappings().first()
    assert k["sayi"] == 2 and k["istek_kimligi"] == "k2" and k["yol_kalibi"] == "/yonetim/okul/{id}/x"
    assert "05321234567" not in k["mesaj"] and "abc123" not in k["yigin_izi"]
    assert [s["k"] for s in k["son_istekler"]] == ["k2", "k1"]
    # çözüldü işaretlenmiş grup yeniden görülürse yeniden açılır ve "yeni" sayılır
    db.execute(text("UPDATE hata_kayitlari SET cozuldu_mu = TRUE WHERE id = :i"), {"i": r1["id"]})
    db.commit()
    r3 = hi.kaydet(yol="/yonetim/okul/3/x", mesaj="m", istek_kimligi="k3", **ortak)
    assert r3["yeni"] is True
    assert db.execute(text("SELECT cozuldu_mu FROM hata_kayitlari WHERE id = :i"), {"i": r1["id"]}).scalar() is False


@db_gerekli
def test_gunluk_bildirim_en_cok_bir_kez(db, db_fabrikasi, kisiler, monkeypatch):
    from sqlalchemy import text
    import app.core.bildirim as bildirim
    monkeypatch.setattr(bildirim, "kuyruk_tetikle", lambda *a, **k: None)
    monkeypatch.setattr(hi, "YAZIM_ARALIGI_SN", 0)
    db.execute(text("DELETE FROM tek_seferlik_gocler WHERE ad LIKE 'hata_bildirimi_%'"))
    db.commit()
    once = db.execute(text("SELECT count(*) FROM bildirimler WHERE baslik = 'Yeni hata kaydı'")).scalar()
    for i in range(3):   # üç FARKLI yeni grup
        hi.kaydet(kaynak="sunucu", yol=f"/x{i}", metod="GET", durum_kodu=500, istisna_turu=f"Hata{i}", mesaj="m", yigin="",
                  kullanici_tipi="anonim", istek_kimligi=f"b{i}", konum=f"bildirim-{i}", db_fabrikasi=db_fabrikasi)
    sonra = db.execute(text("SELECT count(*) FROM bildirimler WHERE baslik = 'Yeni hata kaydı'")).scalar()
    sa_sayisi = db.execute(text("SELECT count(*) FROM admin_kullanicilar WHERE rol = 'super_admin' AND COALESCE(aktif_mi, TRUE)")).scalar()
    assert sonra - once == sa_sayisi      # her süper admine bir bildirim, üç grup için tek tur


@db_gerekli
def test_istemci_hata_ucu_ve_admin_listesi(istemci, kisiler, db, monkeypatch):
    monkeypatch.setattr(hi, "YAZIM_ARALIGI_SN", 0)
    import app.core.bildirim as bildirim
    monkeypatch.setattr(bildirim, "kuyruk_tetikle", lambda *a, **k: None)
    from sqlalchemy.orm import sessionmaker
    # /istemci-hata kendi SessionLocal'ını kullanır → test bağlantısına yönlendir
    monkeypatch.setattr("app.core.database.SessionLocal", sessionmaker(bind=db.get_bind(), join_transaction_mode="create_savepoint"))
    r = istemci.post("/istemci-hata", json={"mesaj": "TypeError: x is undefined (veli@x.com)", "yigin": "at f (a.js:1:2)",
                                            "sayfa": "/profil", "tur": "error"})
    assert r.status_code == 204
    assert istemci.post("/istemci-hata", json={"mesaj": "a" * 3000}).status_code == 422          # alan sınırı
    assert istemci.post("/istemci-hata", content=b"x" * 40_000,
                        headers={"Content-Type": "application/json"}).status_code == 413          # gövde sınırı
    liste = istemci.get("/admin/hata-kayitlari?kaynak=istemci&durum=hepsi", headers=kisiler["super"])
    assert liste.status_code == 200
    g = [x for x in liste.json()["gruplar"] if x["istisna_turu"] == "istemci.error" and "TypeError" in (x["mesaj"] or "")]
    assert g and "veli@x.com" not in g[0]["mesaj"]
    ayr = istemci.get(f"/admin/hata-kayitlari/{g[0]['id']}", headers=kisiler["super"])
    assert ayr.status_code == 200 and ayr.json()["kaynak"] == "istemci"
    assert istemci.post(f"/admin/hata-kayitlari/{g[0]['id']}/cozuldu", json={"cozuldu": True}, headers=kisiler["super"]).status_code == 200
    assert istemci.delete("/admin/hata-kayitlari?kapsam=cozulenler", headers=kisiler["super"]).json()["silinen"] >= 1
