"""[2026-10-22] Keşfet "öne çıkan özellikler" yalnızca eşleşmede kullanılan K1-K4 özelliklerinden seçilir."""
from sqlalchemy import text

from tests.conftest import db_gerekli


@db_gerekli
def test_on_cikanlar_dal_ve_eslesme_disi_degiskenleri_icermez(db):
    from app.core.kesfet_servisi import bolum_on_cikan_degiskenler
    bolum_id = db.execute(text("""SELECT a.bolum_id FROM bolum_agirliklari a JOIN degiskenler d ON d.id = a.degisken_id
                                  WHERE d.kod = 'P4' LIMIT 1""")).scalar()
    dal_degisken = db.execute(text("SELECT id FROM degiskenler WHERE dal_id IS NOT NULL LIMIT 1")).scalar()
    if bolum_id is None or dal_degisken is None:
        import pytest
        pytest.skip("test şemasında bölüm ağırlığı / dal değişkeni yok")
    v = db.execute(text("SELECT COALESCE(MAX(versiyon), 0) + 1 FROM bolum_agirliklari")).scalar()
    # P4 ve bir dal değişkenini en yüksek değere çek: eski kod ikisini de ilk sıralara koyardı
    db.execute(text("""INSERT INTO bolum_agirliklari (bolum_id, degisken_id, agirlik_degeri, yakinsama_skoru, versiyon,
                                                      olusturulma_zamani)
                       SELECT :b, d.id, 100, 0, :v, now() FROM degiskenler d WHERE d.kod = 'P4' OR d.id = :dd"""),
               {"b": bolum_id, "v": v, "dd": dal_degisken})
    kodlar = [x["degisken_kod"] for x in bolum_on_cikan_degiskenler(db, bolum_id, adet=5)]
    assert len(kodlar) == 5
    assert "P4" not in kodlar
    ana = {k for (k,) in db.execute(text("""SELECT d.kod FROM degiskenler d JOIN katmanlar k ON k.id = d.katman_id
                                            WHERE NOT k.kosullu_mu AND d.dal_id IS NULL""")).all()}
    assert set(kodlar) <= ana
