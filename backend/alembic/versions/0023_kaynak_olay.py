"""Gelişim kaynak havuzuna 'olay' türü (önemli olay / keşif / dönüm noktası)

Revision ID: 0023_kaynak_olay
Revises: 0022_hedef_hakki
Create Date: 2026-10-09
"""
from alembic import op

revision = "0023_kaynak_olay"
down_revision = "0022_hedef_hakki"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE gelisim_kaynak_onerileri DROP CONSTRAINT IF EXISTS ck_gko_kaynak_tipi;
ALTER TABLE gelisim_kaynak_onerileri ADD CONSTRAINT ck_gko_kaynak_tipi
  CHECK (kaynak_tipi IN ('kitap','film','rol_model','psikolojik_yaklasim','aktivite','olay'));
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
