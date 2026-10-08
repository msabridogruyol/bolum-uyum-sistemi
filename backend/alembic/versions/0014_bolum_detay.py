"""Bölümlerin detaylı tanıtımı: bolumler.detay (JSONB)

Revision ID: 0014_bolum_detay
Revises: 0013_k5_ust_alanlar
Create Date: 2026-10-08
"""
from alembic import op

revision = "0014_bolum_detay"
down_revision = "0013_k5_ust_alanlar"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE bolumler ADD COLUMN IF NOT EXISTS detay JSONB;
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE bolumler DROP COLUMN IF EXISTS detay;")
