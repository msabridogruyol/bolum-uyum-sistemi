"""Öğrenci raporları modülü (Raporlarım) Temel, Gelişim ve Tam paketlerine

Revision ID: 0043_ogrenci_raporlari
Revises: 0042_rehberlik
Create Date: 2026-10-10
"""
from alembic import op

revision = "0043_ogrenci_raporlari"
down_revision = "0042_rehberlik"
branch_labels = None
depends_on = None

SQL = """
UPDATE paketler SET moduller = moduller || '["ogrenci_raporlari"]'::jsonb
 WHERE kod IN ('temel', 'gelisim', 'tam') AND NOT moduller ? 'ogrenci_raporlari'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
