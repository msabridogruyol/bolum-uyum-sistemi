"""Okul yetkilisinin görevi / unvanı (ör. Psikolojik Danışman) — isteğe bağlı

Revision ID: 0031_yetkili_unvan
Revises: 0030_okul_subeleri
Create Date: 2026-10-10
"""
from alembic import op

revision = "0031_yetkili_unvan"
down_revision = "0030_okul_subeleri"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS unvan VARCHAR
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE admin_kullanicilar DROP COLUMN IF EXISTS unvan")
