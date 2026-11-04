"""[2026-11-04] Eski tarihli tutarların TÜFE ile güncel tahmini (0098): tutar × (son TÜFE / verinin ayındaki TÜFE)."""
from sqlalchemy import text

from tests.conftest import db_gerekli


@db_gerekli
def test_tufe_carpani_ve_hesaplama_metni(db):
    from app.core import is_hayati_servisi as ihs
    assert db.execute(text("SELECT endeks FROM tufe_endeksi WHERE donem = '2023-11'")).scalar() is not None
    son = db.execute(text("SELECT MAX(donem) FROM tufe_endeksi")).scalar()
    c = ihs.enflasyon_carpani(db, "2023-11")
    e23 = float(db.execute(text("SELECT endeks FROM tufe_endeksi WHERE donem = '2023-11'")).scalar())
    es = float(db.execute(text("SELECT endeks FROM tufe_endeksi WHERE donem = :d"), {"d": son}).scalar())
    assert abs(c["carpan"] - es / e23) < 1e-9 and c["son_donem"] == son
    g = ihs.enflasyonla_guncelle(db, 40608.10, "2023-11", "TÜİK ortalama brüt kazanç")
    assert g["tutar"] == round(40608.10 * es / e23, -1)
    assert "Kasım 2023" in g["hesaplama"] and "×" in g["hesaplama"] and "tahmin" in g["hesaplama"]
    assert ihs.enflasyonla_guncelle(db, 1000, son) is None, "son aydan sonrası/aynı ay güncellenmez"
    assert ihs.enflasyonla_guncelle(db, 1000, "1990-01") is None, "endeksi olmayan ay için uydurma yok"


def test_kamu_donem_ve_donem_metni():
    from app.core import is_hayati_servisi as ihs
    assert ihs.kamu_donem_bitisi("2026-2") == ("2026-06", "2026-12")
    assert ihs.kamu_donem_bitisi("2027-1") == ("2026-12", "2027-06")
    assert ihs.kamu_donem_bitisi("2026") is None
    assert ihs.donem_metni("2026-10") == "Ekim 2026"


@db_gerekli
def test_kazanc_tufe_ile_guncellenir(db):
    from app.core import is_hayati_servisi as ihs
    db.execute(text("INSERT INTO kazanc_meslek_gruplari (isco_kodu, ad, brut_aylik_ortalama_tl, veri_yili, asgari_brut_o_yil, kaynak, referans_donem) "
                    "VALUES ('98', 'Deneme grubu', 10000, 2093, 5000, 'test', '2023-11') ON CONFLICT DO NOTHING"))
    db.execute(text("INSERT INTO meslek_isco (meslek_adi, isco_kodu, guven, kaynak) VALUES ('deneme meslek tufe', '98', 'yuksek', 'test') "
                    "ON CONFLICT (meslek_adi) DO UPDATE SET isco_kodu = '98'"))
    db.commit()
    try:
        asgari = {"donem": "2026", "brut": 33030.0, "net": 28075.5}
        m = ihs.kazanc_meslekleri(db, [{"ad": "Deneme meslek tufe"}], asgari)[0]
        c = ihs.enflasyon_carpani(db, "2023-11")["carpan"]
        assert m["guncelleme_yontemi"] == "tufe" and m["guncel_tahmin_brut_tl"] == round(10000 * c, -1)
        assert m["guncel_tahmin_net_tl"] == round(m["guncel_tahmin_brut_tl"] * 28075.5 / 33030.0, -1)
        assert "Nete çevirme" in m["hesaplama"] and m["asgari_kat"] == 2.0
    finally:
        db.execute(text("DELETE FROM kazanc_meslek_gruplari WHERE veri_yili = 2093"))
        db.execute(text("DELETE FROM meslek_isco WHERE meslek_adi = 'deneme meslek tufe'"))
        db.commit()
