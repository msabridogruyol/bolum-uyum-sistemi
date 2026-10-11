"""Tercih dönemi (öğrencinin tercih listesi + rehber onayı) ve mezun yerleşme takibi

Revision ID: 0049_mezun_tercih
Revises: 0048_anketler
Create Date: 2026-10-10
"""
from alembic import op

revision = "0049_mezun_tercih"
down_revision = "0048_anketler"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS tercih_listesi (
    ogrenci_id UUID PRIMARY KEY REFERENCES ogrenciler(id) ON DELETE CASCADE,
    puan_turu VARCHAR,
    siralama INTEGER,
    puan NUMERIC(7,3),
    durum VARCHAR NOT NULL DEFAULT 'taslak',
    rehber_notu TEXT,
    rehber VARCHAR,
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS tercihler (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    sira INTEGER NOT NULL,
    universite VARCHAR NOT NULL,
    bolum_ad VARCHAR NOT NULL,
    bolum_id INTEGER REFERENCES bolumler(id) ON DELETE SET NULL,
    tur VARCHAR NOT NULL DEFAULT 'devlet',
    burs VARCHAR,
    sehir VARCHAR,
    taban_siralama INTEGER,
    notlar VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_tercihler_ogrenci ON tercihler (ogrenci_id, sira);
CREATE TABLE IF NOT EXISTS mezun_yerlesmeleri (
    id SERIAL PRIMARY KEY,
    okul_id INTEGER NOT NULL REFERENCES okullar(id) ON DELETE CASCADE,
    ogrenci_id UUID REFERENCES ogrenciler(id) ON DELETE SET NULL,
    ad_soyad VARCHAR NOT NULL,
    yil INTEGER NOT NULL,
    durum VARCHAR NOT NULL,
    universite VARCHAR,
    bolum_ad VARCHAR,
    bolum_id INTEGER REFERENCES bolumler(id) ON DELETE SET NULL,
    burs VARCHAR,
    siralama INTEGER,
    hedef_bolum_ad VARCHAR,
    hedefle_ayni BOOLEAN,
    oneri_sirasi INTEGER,
    kaynak VARCHAR NOT NULL DEFAULT 'okul',
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_mezun_okul_yil ON mezun_yerlesmeleri (okul_id, yil);
CREATE UNIQUE INDEX IF NOT EXISTS uq_mezun_ogrenci_yil ON mezun_yerlesmeleri (ogrenci_id, yil) WHERE ogrenci_id IS NOT NULL;
UPDATE paketler SET moduller = moduller || '["tercih"]'::jsonb WHERE kod = 'tam' AND NOT moduller ? 'tercih';
UPDATE paketler SET moduller = moduller || '["mezun_takibi"]'::jsonb WHERE kod = 'tam' AND NOT moduller ? 'mezun_takibi'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
