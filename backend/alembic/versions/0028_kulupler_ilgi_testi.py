"""Okul kulüpleri (öğrenci toplulukları) + kısa ilgi testi

Revision ID: 0028_kulupler_ilgi_testi
Revises: 0027_gecici_sifre_ogrenci_no
Create Date: 2026-10-10
"""
from alembic import op

revision = "0028_kulupler_ilgi_testi"
down_revision = "0027_gecici_sifre_ogrenci_no"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS okul_kulupleri (
    id SERIAL PRIMARY KEY,
    okul_id INTEGER NOT NULL REFERENCES okullar(id) ON DELETE CASCADE,
    ad VARCHAR NOT NULL,
    aciklama VARCHAR,
    ilgiler VARCHAR NOT NULL DEFAULT '',
    sorumlu VARCHAR,
    bulusma VARCHAR,
    aktif BOOLEAN NOT NULL DEFAULT TRUE,
    sira INTEGER NOT NULL DEFAULT 0,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_okul_kulupleri_okul ON okul_kulupleri (okul_id);
CREATE TABLE IF NOT EXISTS ogrenci_ilgi_testleri (
    ogrenci_id UUID PRIMARY KEY REFERENCES ogrenciler(id) ON DELETE CASCADE,
    cevaplar JSONB NOT NULL,
    puanlar JSONB NOT NULL,
    tamamlanma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ogrenci_ilgi_testleri; DROP TABLE IF EXISTS okul_kulupleri;")
