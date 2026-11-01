"""[2026-10-19] Bağımsız denetimde bulunan sorunların düzeltmeleri."""
import uuid

from sqlalchemy import text

from tests.conftest import db_gerekli


def test_guven_kontrol_yoksa_olaylara_gore():
    from app.core.guvenlik_servisi import birlesik_guven
    assert birlesik_guven(None, 100) == 100 and birlesik_guven(None, 40) == 40      # önceden 70 → hiç geçersiz olamıyordu
    assert birlesik_guven(80, 40) == 60


def test_sik_sirasi_tohumlu_ve_yalniz_sjt():
    from types import SimpleNamespace as N
    from app.api.ogrenci import _sik_sirasi
    sec = [N(id=i) for i in range(101, 105)]
    a = [s.id for s in _sik_sirasi(N(soru_tipi="sjt"), sec, 7)]
    assert a == [s.id for s in _sik_sirasi(N(soru_tipi="sjt"), sec, 7)]           # aynı turda hep aynı sıra
    farkli = {tuple(s.id for s in _sik_sirasi(N(soru_tipi="sjt"), sec, t)) for t in range(1, 30)}
    assert len(farkli) > 5 and sorted(a) == [101, 102, 103, 104]
    assert [s.id for s in _sik_sirasi(N(soru_tipi="kutup"), sec, 7)] == [101, 102, 103, 104]   # kutup sırası anlamlı


@db_gerekli
def test_kvkk_onayi_olmadan_degerlendirme_ve_ai_baslamaz(istemci, db, kisiler):
    from app.core.security import erisim_tokeni_uret
    oid = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Onaysız', :e, 'x', :o, now(), now())"""), {"i": oid, "e": f"onaysiz.{oid.hex[:6]}@test.invalid",
                                                                              "o": kisiler["okul_a"]})
    db.commit()
    h = {"Authorization": f"Bearer {erisim_tokeni_uret(oid, 'ogrenci')}"}
    for yol in ("/ogrenci/katmanlar/K1/basla", "/ogrenci/dallar/K5N/basla"):
        r = istemci.post(yol, headers=h)
        assert r.status_code == 403 and "Kişisel Verilerin Korunması" in r.json()["detail"], yol


@db_gerekli
def test_kamera_rizasi_geri_alininca_fotograflar_silinir(db, kisiler):
    from app.core.hesap_guvenligi_servisi import kvkk_kaydet
    oid = db.execute(text("SELECT id FROM ogrenciler WHERE email LIKE 'ogr.%@test.invalid' ORDER BY olusturulma_zamani DESC LIMIT 1")).scalar()
    kvkk_kaydet(db, "ogrenci", oid, {"kamera": True}, None, tam_kayit=False)
    tid = db.execute(text("""INSERT INTO ogrenci_degerlendirme_turu (ogrenci_id, tur_no, durum, baslama_zamani, sonuc_gecerli_mi)
                             VALUES (:o, 1, 'devam_ediyor', now(), TRUE) RETURNING id"""), {"o": oid}).scalar()
    db.execute(text("""INSERT INTO guvenlik_fotograflari (ogrenci_id, tur_id, depolama_yolu, cekim_zamani)
                       VALUES (:o, :t, 'data:image/jpeg;base64,AA', now())"""), {"o": oid, "t": tid})
    kvkk_kaydet(db, "ogrenci", oid, {"kamera": False}, None, tam_kayit=False)
    assert db.execute(text("SELECT count(*) FROM guvenlik_fotograflari WHERE ogrenci_id = :o"), {"o": oid}).scalar() == 0
    db.rollback()


@db_gerekli
def test_surum_parametreleri_elle_degismez(istemci, db, kisiler):
    db.execute(text("""INSERT INTO sistem_parametreleri (anahtar, deger, guncelleme_zamani) VALUES ('olcme_soru_seti', 'x', now())
                       ON CONFLICT (anahtar) DO NOTHING"""))
    db.commit()
    r = istemci.put("/admin/parametreler/olcme_soru_seti", headers=kisiler["super"], json={"deger": "2099-01-01"})
    assert r.status_code == 400


@db_gerekli
def test_meslektasin_gecici_sifresi_donmez(istemci, db, kisiler):
    ek = uuid.uuid4().hex[:6]
    b = uuid.uuid4()
    db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, olusturulma_zamani,
                       sifre_degistirmeli, gecici_sifre_sifreli)
                       VALUES (:i, 'Meslektaş B', :e, 'x', 'okul_yetkilisi', :o, TRUE, now(), TRUE, 'gizli-deger')"""),
               {"i": b, "e": f"b.{ek}@test.invalid", "o": kisiler["okul_a"]})
    db.commit()
    r = istemci.put(f"/yonetim/yetkili/{b}", headers=kisiler["yetkili"], json={})
    assert r.status_code == 200 and r.json()["gecici_sifre"] == "(gizli)"


def test_0076_tek_seferlik_isaretle_korunur():
    import importlib.util
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "alembic" / "versions" / "0076_yeni_k5_sorular.py"
    s = importlib.util.spec_from_file_location("g0076", p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    i = m.SQL.index("DELETE FROM ogrenci_degerlendirme_turu")
    once = m.SQL[:i]
    assert "tek_seferlik_gocler WHERE ad = '0076_soru_seti_" in once                   # silmeden önce kalıcı işaret kontrolü
    assert "anahtar = 'olcme_soru_seti') THEN" in once                                # eski kurulum: işaret yazılır, silinmez
