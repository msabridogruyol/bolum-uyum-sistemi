# -*- coding: utf-8 -*-
"""[2026-11-01] Pipeline çıktılarının admin panelinden yüklenmesi: dosya ayrıştırma (SQL çalıştırılmaz, değerler okunur)."""
import pytest

from app.core import veri_yukleme as vy

K5_SQL = """-- Filizyol: veriye dayalı K5 iş türü bağları
BEGIN;
DELETE FROM bolum_k5_baglari WHERE degisken_id IN (SELECT id FROM degiskenler WHERE kod ~ '^U[0-9]{2}_');
INSERT INTO bolum_k5_baglari (bolum_id, degisken_id, bag)
SELECT b.id, g.id, v.bag FROM (VALUES
('EKONOMETRİ', 'U03_S', 1),
('ADLİ BİLİMLER', 'U06_P', 0.85),
('KADIN''IN ADI', 'U02_G', 0.4)
) v(ad, deg, bag) JOIN bolumler b ON b.ad = v.ad JOIN degiskenler g ON g.kod = v.deg;
COMMIT;
"""
OM_SQL = """-- bolum_ornek_meslekler (b3) — 2 satır
BEGIN;
DELETE FROM bolum_ornek_meslekler;
INSERT INTO bolum_ornek_meslekler (bolum_id, meslek_isco_kodu, meslek_adi, benzerlik_skoru, model_sayisi, sira)
SELECT b.id, v.isco, v.ad, v.benzerlik, v.model_sayisi, v.sira
FROM (VALUES
  ('EKONOMETRİ', '2631.2', 'Ekonomist', 0.6405, 3, 1),
  ('HUKUK', '2611.1', 'Avukat, ''hukuk'' danışmanı', 0.7, 2, 2)
) AS v(bolum_adi, isco, ad, benzerlik, model_sayisi, sira)
JOIN bolumler b ON b.ad = v.bolum_adi;
COMMIT;
"""


def test_k5_sql_ayristirma():
    s = vy.ayristir("k5_baglari", K5_SQL)
    assert [(x["bolum"], x["kod"], x["bag"]) for x in s] == [
        ("EKONOMETRİ", "U03_S", 1.0), ("ADLİ BİLİMLER", "U06_P", 0.85), ("KADIN'IN ADI", "U02_G", 0.4)]


def test_k5_csv_ayristirma():
    s = vy.ayristir("k5_baglari", "﻿bolum;alan;eksen;bag\nEKONOMETRİ;Temel Bilimler;U03_S;1,0\nHUKUK;Hukuk;U09_H;0,55\n")
    assert [(x["bolum"], x["kod"], x["bag"]) for x in s] == [("EKONOMETRİ", "U03_S", 1.0), ("HUKUK", "U09_H", 0.55)]


def test_ornek_meslek_sql_ayristirma():
    s = vy.ayristir("ornek_meslekler", OM_SQL)
    assert len(s) == 2
    assert s[0] == {"bolum": "EKONOMETRİ", "isco": "2631.2", "ad": "Ekonomist", "benzerlik": 0.6405, "model_sayisi": 3, "sira": 1}
    assert s[1]["ad"] == "Avukat, 'hukuk' danışmanı"


@pytest.mark.parametrize("tur,metin", [("k5_baglari", "merhaba"), ("ornek_meslekler", K5_SQL), ("k5_baglari", ""),
                                       ("k5_baglari", "('X', 'U01_M', 1.5)")])
def test_bicim_disi_dosya_reddedilir(tur, metin):
    with pytest.raises(vy.VeriHatasi):
        vy.ayristir(tur, metin)


def test_sql_komutu_deger_sayilmaz():
    # Değer satırı biçiminde olmayan hiçbir satır (komutlar, yorumlar) okunmaz; yalnızca 3 alanlı demetler.
    s = vy.ayristir("k5_baglari", "('A', 'U01_M', 1);\nDROP TABLE bolumler;\n('B', 'U01_E', 0.5)")
    assert [x["bolum"] for x in s] == ["B"]
