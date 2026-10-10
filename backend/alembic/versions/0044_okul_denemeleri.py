"""Okul denemeleri: rehber Excel şablonuyla tüm öğrencilerin deneme sonuçlarını tek seferde yükler

Revision ID: 0044_okul_denemeleri
Revises: 0043_ogrenci_raporlari
Create Date: 2026-10-10
"""
from alembic import op

revision = "0044_okul_denemeleri"
down_revision = "0043_ogrenci_raporlari"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS okul_denemeleri (
    id SERIAL PRIMARY KEY,
    okul_id INTEGER NOT NULL REFERENCES okullar(id) ON DELETE CASCADE,
    ad VARCHAR NOT NULL,
    tarih DATE NOT NULL,
    oturum VARCHAR NOT NULL,
    olusturan VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_okul_deneme_okul ON okul_denemeleri (okul_id, tarih);
ALTER TABLE ogrenci_denemeleri ADD COLUMN IF NOT EXISTS okul_deneme_id INTEGER REFERENCES okul_denemeleri(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_ogr_deneme_okul_deneme ON ogrenci_denemeleri (okul_deneme_id);
UPDATE paketler SET moduller = moduller || '["okul_denemeleri"]'::jsonb WHERE kod = 'tam' AND NOT moduller ? 'okul_denemeleri'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
