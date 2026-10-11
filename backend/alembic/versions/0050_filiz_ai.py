"""Filiz yapay zekâ ayrı modül: yalnızca Tam pakette; diğer paketlerde Filiz otomatik rehber modunda çalışır

Revision ID: 0050_filiz_ai
Revises: 0049_mezun_tercih
Create Date: 2026-10-10
"""
from alembic import op

revision = "0050_filiz_ai"
down_revision = "0049_mezun_tercih"
branch_labels = None
depends_on = None

SQL = """
UPDATE paketler SET moduller = moduller || '["filiz_ai"]'::jsonb WHERE kod = 'tam' AND NOT moduller ? 'filiz_ai'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
