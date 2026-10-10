"""Geçici şifrenin (şifreli) saklanması + öğrenci numarası

Revision ID: 0027_gecici_sifre_ogrenci_no
Revises: 0026_guvenlik_olay_tipleri
Create Date: 2026-10-10
"""
from alembic import op

revision = "0027_gecici_sifre_ogrenci_no"
down_revision = "0026_guvenlik_olay_tipleri"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS gecici_sifre_sifreli VARCHAR;
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS ogrenci_no VARCHAR;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS gecici_sifre_sifreli VARCHAR;
CREATE INDEX IF NOT EXISTS ix_ogrenciler_okul_no ON ogrenciler (okul_id, ogrenci_no) WHERE ogrenci_no IS NOT NULL;
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
