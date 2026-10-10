"""Kütüphane: kitap sayfa sayısı (grafikler için)

Revision ID: 0033_kutuphane_sayfa
Revises: 0032_takvim_kutuphane
Create Date: 2026-10-10
"""
from alembic import op

revision = "0033_kutuphane_sayfa"
down_revision = "0032_takvim_kutuphane"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenci_kutuphane ADD COLUMN IF NOT EXISTS sayfa INTEGER
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE ogrenci_kutuphane DROP COLUMN IF EXISTS sayfa")
