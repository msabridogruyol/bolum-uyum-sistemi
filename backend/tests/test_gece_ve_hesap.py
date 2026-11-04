"""[2026-11-04] Kullanıcı kuralları ve 20.000 öğrenci yük düzeltmeleri:
* şifre değişikliği: eski şifre + e-posta onay kodu (öğrenci ve yönetim);
* ad soyad en fazla 30 karakter;
* sistemi yavaşlatan değişiklikler gece bakımında (pipeline onayı, katman ağırlığı, ağır göçler);
* çıkışta / yenilemede anahtar iptali; test bağlantı süresi ve test yetkilisi; öneri özeti tetikleyicisi."""
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


def _ogrenci_id(db):
    return db.execute(text("SELECT id FROM ogrenciler WHERE email LIKE 'ogr.%@test.invalid' ORDER BY olusturulma_zamani DESC LIMIT 1")).scalar()


@pytest.fixture
def eposta(monkeypatch):
    """E-posta altyapısı açıkmış gibi; gönderilen kodlar yakalanır."""
    from app.core import eposta_servisi as ep
    giden = []
    monkeypatch.setattr(ep, "eposta_yapilandirildi_mi", lambda: True)
    monkeypatch.setattr(ep, "eposta_gonder", lambda alici, konu, html, metin, ekler=None: giden.append((alici, konu)) or True)
    return giden


# ----------------------------------------------------------------------------- şifre değişikliği
@db_gerekli
def test_ogrenci_sifre_degisikligi_kodla(istemci, db, kisiler, eposta):
    from app.core.security import sifre_dogrula, sifre_hashle
    oid = _ogrenci_id(db)
    db.execute(text("UPDATE ogrenciler SET sifre_hash = :h WHERE id = :i"), {"h": sifre_hashle("EskiSifre1!"), "i": oid})
    db.commit()
    h = kisiler["ogrenci"]
    assert istemci.post("/ogrenci/profil/sifre-degistir", json={"eski_sifre": "yanlis", "yeni_sifre": "YeniSifre1!"}, headers=h).status_code == 400
    r = istemci.post("/ogrenci/profil/sifre-degistir", json={"eski_sifre": "EskiSifre1!", "yeni_sifre": "YeniSifre1!"}, headers=h)
    assert r.status_code == 200 and r.json()["kod_gonderildi"] is True
    kod = eposta[-1][1].split(": ")[-1]
    # kod girilmeden şifre değişmez
    assert sifre_dogrula("EskiSifre1!", db.execute(text("SELECT sifre_hash FROM ogrenciler WHERE id = :i"), {"i": oid}).scalar())
    assert istemci.post("/ogrenci/profil/sifre-degistir/onayla", json={"kod": "000000" if kod != "000000" else "111111"}, headers=h).status_code == 400
    r = istemci.post("/ogrenci/profil/sifre-degistir/onayla", json={"kod": kod}, headers=h)
    assert r.status_code == 200 and r.json()["erisim_tokeni"]
    db.expire_all()
    assert sifre_dogrula("YeniSifre1!", db.execute(text("SELECT sifre_hash FROM ogrenciler WHERE id = :i"), {"i": oid}).scalar())
    assert any("değiştirildi" in k for _, k in eposta)   # bilgi e-postası
    # kod tek kullanımlık
    assert istemci.post("/ogrenci/profil/sifre-degistir/onayla", json={"kod": kod}, headers={"Authorization": f"Bearer {r.json()['erisim_tokeni']}"}).status_code == 400


@db_gerekli
def test_yonetim_sifre_degisikligi_kodla(istemci, db, kisiler, eposta):
    from app.core.security import sifre_hashle
    db.execute(text("UPDATE admin_kullanicilar SET sifre_hash = :h WHERE email LIKE 'okul_yetkilisi.%@test.invalid'"), {"h": sifre_hashle("EskiSifre1!")})
    db.commit()
    r = istemci.post("/yonetim/ben/sifre-degistir", json={"eski_sifre": "EskiSifre1!", "yeni_sifre": "YeniSifre1!"}, headers=kisiler["yetkili"])
    assert r.status_code == 200 and r.json()["kod_gonderildi"]
    kod = eposta[-1][1].split(": ")[-1]
    assert istemci.post("/yonetim/ben/sifre-degistir/onayla", json={"kod": kod}, headers=kisiler["yetkili"]).status_code == 200


# ----------------------------------------------------------------------------- ad soyad
@db_gerekli
def test_ad_soyad_en_fazla_30(istemci, kisiler):
    h = kisiler["ogrenci"]
    assert istemci.put("/ogrenci/profil", json={"ad_soyad": "A" * 31}, headers=h).status_code in (400, 422)
    assert istemci.put("/ogrenci/profil", json={"ad_soyad": "Ayşe Nur Yılmaz"}, headers=h).status_code == 200


def test_toplu_yuklemede_uzun_ad_satir_hatasi(db):
    from app.api.okul_yonetimi import _dogrula
    satir = [{"satir": 2, "ad_soyad": "Ç" * 31, "email": "uzun.ad@okul.test", "sinif": "9. Sınıf", "sube": "A", "sifre": "", "ogrenci_no": ""}]
    sonuc = _dogrula(db, satir, None)
    assert "30 karakter" in (sonuc[0]["hata"] or "")


# ----------------------------------------------------------------------------- gece bakımı
@db_gerekli
def test_katman_agirligi_gece_uygulanir(istemci, db, kisiler):
    from app.core.database import engine
    from app.core.gece_bakimi import _kuyruk
    once = {r.kod: float(r.normalizasyon_agirligi or 0) for r in db.execute(text("SELECT kod, normalizasyon_agirligi FROM katmanlar WHERE kod IN ('K1','K2','K3','K4')")).all()}
    if len(once) < 4:
        pytest.skip("test şemasında K1–K4 katmanları yok")
    yeni = {"K1": 40, "K2": 20, "K3": 20, "K4": 20}
    if once == {k: float(v) for k, v in yeni.items()}:
        yeni = {"K1": 25, "K2": 25, "K3": 25, "K4": 25}
    r = istemci.put("/admin/katman-agirliklari", json={"agirliklar": yeni}, headers=kisiler["super"])
    assert r.status_code == 200
    db.expire_all()
    simdi = {x.kod: float(x.normalizasyon_agirligi) for x in db.execute(text("SELECT kod, normalizasyon_agirligi FROM katmanlar WHERE kod IN ('K1','K2','K3','K4')")).all()}
    assert simdi == once, "ağırlık gündüz değişmemeli"
    assert db.execute(text("SELECT count(*) FROM gece_kuyrugu WHERE tur = 'katman_agirliklari' AND durum = 'bekliyor'")).scalar() == 1
    _kuyruk(db, engine)
    db.expire_all()
    simdi = {x.kod: float(x.normalizasyon_agirligi) for x in db.execute(text("SELECT kod, normalizasyon_agirligi FROM katmanlar WHERE kod IN ('K1','K2','K3','K4')")).all()}
    assert simdi == {k: float(v) for k, v in yeni.items()}
    db.rollback()


def test_gece_penceresi(monkeypatch):
    from datetime import datetime
    from app.core.gece_bakimi import YEREL, calismali_mi

    class Db:
        def __init__(self, var): self.var = var
        def execute(self, *a, **k):
            class R:
                def __init__(s, v): s.v = v
                def first(s): return 1 if s.v else None
                def scalar(s): return None
            return R(self.var)
    import app.core.gece_bakimi as gb
    monkeypatch.setattr(gb, "bakim_saati", lambda db: (3, 0))
    assert calismali_mi(Db(False), datetime(2026, 11, 5, 3, 1, tzinfo=YEREL))
    assert calismali_mi(Db(False), datetime(2026, 11, 5, 5, 59, tzinfo=YEREL))
    assert not calismali_mi(Db(False), datetime(2026, 11, 5, 6, 0, tzinfo=YEREL))
    assert not calismali_mi(Db(False), datetime(2026, 11, 5, 14, 0, tzinfo=YEREL))
    assert not calismali_mi(Db(True), datetime(2026, 11, 5, 3, 30, tzinfo=YEREL)), "aynı gün ikinci kez çalışmaz"


def test_agir_goc_acilista_calismaz():
    from app.core.sema_guncelleme import OTOMATIK, OTOMATIK_GECE, _sql_oku
    assert "0094_gece_indeksleri" in OTOMATIK_GECE and "0094_gece_indeksleri" not in OTOMATIK
    for ad in OTOMATIK_GECE:
        assert "CONCURRENTLY" in _sql_oku(ad)
    assert _sql_oku("0093_denetim_guvenlik_performans").count("CREATE INDEX") == 1   # yalnızca yeni tablonun kendi indeksi


# ----------------------------------------------------------------------------- oturum anahtarları
@db_gerekli
def test_cikista_anahtar_iptal(istemci, db, kisiler):
    from app.core.security import erisim_tokeni_uret
    oid = _ogrenci_id(db)
    t = erisim_tokeni_uret(oid, "ogrenci")
    h = {"Authorization": f"Bearer {t}"}
    assert istemci.get("/ogrenci/profil", headers=h).status_code == 200
    assert istemci.post("/auth/cikis", json={}, headers=h).status_code == 204
    assert istemci.get("/ogrenci/profil", headers=h).status_code == 401


@db_gerekli
def test_yenileme_anahtari_tek_kullanimlik(istemci, db, kisiler):
    from app.core.security import yenileme_tokeni_uret
    oid = _ogrenci_id(db)
    y = yenileme_tokeni_uret(oid, "ogrenci")
    assert istemci.post("/auth/yenile", json={"yenileme_tokeni": y}).status_code == 200
    assert istemci.post("/auth/yenile", json={"yenileme_tokeni": y}).status_code == 401


# ----------------------------------------------------------------------------- test hesapları
@db_gerekli
def test_test_yetkilisi_yalniz_demo_okulda(istemci, kisiler):
    r = istemci.post("/yonetim/test-hesaplari", json={"tip": "okul_yetkilisi", "ad_soyad": "Deneme Yetkili", "okul_id": kisiler["okul_a"]},
                     headers=kisiler["super"])
    assert r.status_code == 400 and "demo" in r.json()["detail"]


def test_test_baglantisi_en_fazla_7_gun():
    from datetime import datetime, timezone
    from app.core.test_hesabi_servisi import giris_anahtari_uret

    class H:
        pass
    h = H()
    giris_anahtari_uret(h, 24 * 30)
    assert (h.test_giris_bitis - datetime.now(timezone.utc)).days <= 7


# ----------------------------------------------------------------------------- öneri özeti
@db_gerekli
def test_oneri_ozeti_skor_degisince_gecersiz(db, kisiler):
    """Skor yazılınca turun sürüm sayacı artar; eski sayaçla yazılmış özet artık eşleşmez (eşzamanlı okuma yarışı)."""
    oid = _ogrenci_id(db)
    tur = db.execute(text("""INSERT INTO ogrenci_degerlendirme_turu (ogrenci_id, tur_no, baslama_zamani, tamamlanma_zamani, durum, sonuc_gecerli_mi)
                             VALUES (:o, 1, now(), now(), 'tamamlandi', TRUE) RETURNING id"""), {"o": oid}).scalar()
    bid = db.execute(text("SELECT id FROM bolumler LIMIT 1")).scalar()
    if bid is None:
        bid = db.execute(text("INSERT INTO bolumler (ad, durum) VALUES ('Deneme Bölümü', 'yayinda') RETURNING id")).scalar()
    db.execute(text("INSERT INTO tur_oneri_ozeti (tur_id, bolumler, uyumlar, surum, kaynak_n) VALUES (:t, ARRAY[1], ARRAY[50], 'x', 0)"), {"t": tur})
    n = lambda: db.execute(text("SELECT COALESCE((SELECT n FROM tur_skor_surumu WHERE tur_id = :t), 0)"), {"t": tur}).scalar()
    assert n() == 0
    db.execute(text("""INSERT INTO ogrenci_bolum_uyum_skorlari (ogrenci_id, tur_id, bolum_id, toplam_uyum, olusturulma_zamani)
                       VALUES (:o, :t, :b, 70, now())"""), {"o": oid, "t": tur, "b": bid})
    assert n() == 1
    db.execute(text("UPDATE ogrenci_bolum_uyum_skorlari SET toplam_uyum = 71 WHERE tur_id = :t"), {"t": tur})
    db.execute(text("DELETE FROM ogrenci_bolum_uyum_skorlari WHERE tur_id = :t"), {"t": tur})
    assert n() == 3
    eslesen = db.execute(text("""SELECT count(*) FROM tur_oneri_ozeti z LEFT JOIN tur_skor_surumu v ON v.tur_id = z.tur_id
                                  WHERE z.tur_id = :t AND z.kaynak_n = COALESCE(v.n, 0)"""), {"t": tur}).scalar()
    assert eslesen == 0
    db.rollback()


@db_gerekli
def test_sifre_kodu_gitmezse_hak_yanmaz(istemci, db, kisiler, monkeypatch):
    from app.core import eposta_servisi as ep
    from app.core.security import sifre_hashle
    monkeypatch.setattr(ep, "eposta_yapilandirildi_mi", lambda: True)
    monkeypatch.setattr(ep, "eposta_gonder", lambda *a, **k: False)
    oid = _ogrenci_id(db)
    db.execute(text("UPDATE ogrenciler SET sifre_hash = :h WHERE id = :i"), {"h": sifre_hashle("EskiSifre1!"), "i": oid})
    db.execute(text("DELETE FROM sifre_degisiklik_talepleri WHERE kullanici_tipi = 'ogrenci' AND kullanici_id = :i"), {"i": oid})
    db.commit()
    r = istemci.post("/ogrenci/profil/sifre-degistir", json={"eski_sifre": "EskiSifre1!", "yeni_sifre": "YeniSifre1!"}, headers=kisiler["ogrenci"])
    assert r.status_code == 400 and "gönderilemedi" in r.json()["detail"]
    db.expire_all()
    assert db.execute(text("SELECT count(*) FROM sifre_degisiklik_talepleri WHERE kullanici_tipi = 'ogrenci' AND kullanici_id = :i"), {"i": oid}).scalar() == 0


def test_hedef_nihai_uyum_k5_yuvasi():
    from app.core.skor_motoru import k5_nihai
    # K5 kümesindeki bölümler yuvaları değiş tokuş eder; hedef bölümün nihai uyumu küme içi yuvadan gelir
    assert k5_nihai({1: 43.0, 2: 38.0, 3: 10.0}, {1: 50, 2: 90})[2] == 43.0


# ----------------------------------------------------------------------------- [2026-11-04] PDF hızı, Excel metin tarih, sürüm
def test_hizli_tablo_sayfalara_bolunur_basliği_tekrarlar():
    from reportlab.lib import colors as _c
    from app.core.rapor import pdf as P
    P._belge("Deneme", {"ad": "Okul"}, None)   # yazı tiplerini kaydeder
    t = P.HizliTablo(["Ad", "Bölüm"], [[f"Öğrenci {i}", "Bilgisayar ve Öğretim Teknolojileri Öğretmenliği"] for i in range(500)],
                     [100, 60], _c.black)
    gen, yuk = t.wrap(160, 700)
    parca = t.split(160, 700)
    assert len(parca) == 2 and parca[0].wrap(160, 700)[1] <= 700
    assert len(parca[0].satirlar) + len(parca[1].satirlar) == 500 and parca[1].ilk == len(parca[0].satirlar)
    assert all(len(h) >= 2 for h in [t.satirlar[0][0][1]])   # uzun bölüm adı alt satıra geçer


def test_excel_tarihleri_metin_ve_saniyeli():
    from datetime import datetime, timezone
    from openpyxl import Workbook
    from app.core.excel_guvenligi import tarihleri_metne_cevir
    wb = Workbook()
    wb.active.append([datetime(2026, 11, 4, 8, 48, 7, tzinfo=timezone.utc), datetime(2026, 11, 4, 11, 0, 5)])
    tarihleri_metne_cevir(wb)
    assert [c.value for c in wb.active[1]] == ["04.11.2026 11:48:07", "04.11.2026 11:00:05"]


@db_gerekli
def test_sistem_surumu_herkese_acik(istemci):
    r = istemci.get("/sistem/surum")
    assert r.status_code == 200 and r.json()["sunucu_guncelleme"]
    assert "surum" not in r.json()   # kod özeti / commit gösterilmez
