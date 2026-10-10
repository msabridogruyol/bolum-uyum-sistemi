"""Çalışma programı (haftalık şablon) ve günlük çalışma / soru kayıtları

Revision ID: 0045_calisma
Revises: 0044_okul_denemeleri
Create Date: 2026-10-10
"""
from alembic import op

revision = "0045_calisma"
down_revision = "0044_okul_denemeleri"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS calisma_programi (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    gun SMALLINT NOT NULL,
    baslangic VARCHAR(5) NOT NULL,
    sure_dk INTEGER NOT NULL,
    ders VARCHAR NOT NULL,
    notlar VARCHAR
);
CREATE INDEX IF NOT EXISTS ix_calisma_programi_ogrenci ON calisma_programi (ogrenci_id);
CREATE TABLE IF NOT EXISTS calisma_kayitlari (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    tarih DATE NOT NULL,
    ders VARCHAR NOT NULL,
    sure_dk INTEGER NOT NULL DEFAULT 0,
    soru INTEGER NOT NULL DEFAULT 0,
    dogru INTEGER,
    yanlis INTEGER,
    konu VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_calisma_kayit_ogrenci ON calisma_kayitlari (ogrenci_id, tarih);
UPDATE paketler SET moduller = moduller || '["calisma"]'::jsonb WHERE kod IN ('gelisim', 'tam') AND NOT moduller ? 'calisma'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
