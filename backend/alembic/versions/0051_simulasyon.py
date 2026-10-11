"""Meslek simülasyonu sonuçları ("Bir günümü yaşa")

Revision ID: 0051_simulasyon
Revises: 0050_filiz_ai
Create Date: 2026-10-10
"""
from alembic import op

revision = "0051_simulasyon"
down_revision = "0050_filiz_ai"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS simulasyon_sonuclari (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    bolum_id INTEGER REFERENCES bolumler(id) ON DELETE SET NULL,
    meslek_ad VARCHAR NOT NULL,
    keyif INTEGER NOT NULL,
    tepkiler JSONB NOT NULL DEFAULT '{}',
    kararlar JSONB NOT NULL DEFAULT '{}',
    yaklasimlar JSONB NOT NULL DEFAULT '[]',
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_simulasyon_ogrenci ON simulasyon_sonuclari (ogrenci_id, olusturulma_zamani DESC)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
