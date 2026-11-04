"""TÜFE endeksi: eski tutarların güncel tahmini için

Revision ID: 0098_tufe_endeksi
Revises: 0097_veri_kaynaklari_tohumu
Create Date: 2026-11-04

[2026-11-04] Kullanıcı isteği: eski tarihli TL verileri (TÜİK kazanç 2023, ileride yaşam maliyeti / kamu maaşı) güncel
enflasyonla çarpılarak bugünün TAHMİNİ olarak gösterilsin, hesaplama mantığı açıklamada yazsın.
- tufe_endeksi: TÜİK TÜFE genel endeksi (2025=100, COICOP 2018; Veri Portalı DF_TUFE_SDMX_TT10), aylık. Yönetici her ay ekler.
- kazanc_meslek_gruplari.referans_donem: verinin ait olduğu ay (Kazanç Yapısı 2023'te referans ay Kasım 2023).
Canlıda yalnızca SQL metni çalışır (app/core/sema_guncelleme.py); tohum tek_seferlik_gocler işaretiyle bir kez yazılır.
"""
from alembic import op

revision = "0098_tufe_endeksi"
down_revision = "0097_veri_kaynaklari_tohumu"
branch_labels = None
depends_on = None

_KAYNAK = ("TÜİK, Tüketici Fiyat Endeksi (2025=100), Veri Portalı tablo DF_TUFE_SDMX_TT10 — "
           "https://databrowser2.tuik.gov.tr/#/tr/tuik/TR,DF_TUFE_SDMX_TT10,1.0")

SQL = r"""
CREATE TABLE IF NOT EXISTS tufe_endeksi (
    id SERIAL PRIMARY KEY,
    donem VARCHAR(7) NOT NULL UNIQUE CHECK (donem ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'),
    endeks NUMERIC(14,6) NOT NULL CHECK (endeks > 0),
    yillik_degisim NUMERIC(8,2),
    kaynak VARCHAR NOT NULL,
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE kazanc_meslek_gruplari ADD COLUMN IF NOT EXISTS referans_donem VARCHAR(7);
UPDATE kazanc_meslek_gruplari SET referans_donem = '2023-11'
 WHERE referans_donem IS NULL AND veri_yili = 2023 AND kaynak ILIKE '%Kazanç Yapısı%';
WITH isaret AS (
    INSERT INTO tek_seferlik_gocler (ad) VALUES ('0098_tufe_2022_01_2026_10') ON CONFLICT (ad) DO NOTHING RETURNING ad
)
INSERT INTO tufe_endeksi (donem, endeks, yillik_degisim, kaynak)
SELECT v.donem, v.endeks, v.yillik, '""" + _KAYNAK + r"""' FROM (VALUES
    ('2022-01', 23.976596, 48.69),
    ('2022-02', 25.129513, 54.44),
    ('2022-03', 26.502647, 61.14),
    ('2022-04', 28.423653, 69.97),
    ('2022-05', 29.270905, 73.5),
    ('2022-06', 30.720377, 78.62),
    ('2022-07', 31.446998, 79.6),
    ('2022-08', 31.90628, 80.21),
    ('2022-09', 32.887673, 83.45),
    ('2022-10', 34.05347, 85.51),
    ('2022-11', 35.035492, 84.39),
    ('2022-12', 35.449851, 64.27),
    ('2023-01', 37.806892, 57.68),
    ('2023-02', 38.995936, 55.18),
    ('2023-03', 39.88874, 50.51),
    ('2023-04', 40.840289, 43.68),
    ('2023-05', 40.857881, 39.59),
    ('2023-06', 42.459714, 38.21),
    ('2023-07', 46.488642, 47.83),
    ('2023-08', 50.712968, 58.94),
    ('2023-09', 53.123414, 61.53),
    ('2023-10', 54.947662, 61.36),
    ('2023-11', 56.750548, 61.98),
    ('2023-12', 58.411754, 64.77),
    ('2024-01', 62.327275, 64.86),
    ('2024-02', 65.150195, 67.07),
    ('2024-03', 67.210681, 68.5),
    ('2024-04', 69.347819, 69.8),
    ('2024-05', 71.683497, 75.45),
    ('2024-06', 72.859662, 71.6),
    ('2024-07', 75.209791, 61.78),
    ('2024-08', 77.070794, 51.97),
    ('2024-09', 79.358408, 49.38),
    ('2024-10', 81.643823, 48.58),
    ('2024-11', 83.475925, 47.09),
    ('2024-12', 84.334173, 44.38),
    ('2025-01', 88.578291, 42.12),
    ('2025-02', 90.59197, 39.05),
    ('2025-03', 92.820524, 38.1),
    ('2025-04', 95.601977, 37.86),
    ('2025-05', 97.063071, 35.41),
    ('2025-06', 98.395995, 35.05),
    ('2025-07', 100.421925, 33.52),
    ('2025-08', 102.465761, 32.95),
    ('2025-09', 105.780006, 33.29),
    ('2025-10', 108.477581, 32.87),
    ('2025-11', 109.415936, 31.07),
    ('2025-12', 110.386963, 30.89),
    ('2026-01', 115.73, 30.65),
    ('2026-02', 119.16, 31.53),
    ('2026-03', 121.47, 30.87),
    ('2026-04', 126.55, 32.37),
    ('2026-05', 128.72, 32.61),
    ('2026-06', 129.99, 32.11),
    ('2026-07', 132.31, 31.75),
    ('2026-08', 134.75, 31.51),
    ('2026-09', 137.23, 29.73),
    ('2026-10', 140.77, 29.77)
) AS v(donem, endeks, yillik)
WHERE EXISTS (SELECT 1 FROM isaret)
ON CONFLICT (donem) DO NOTHING
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
