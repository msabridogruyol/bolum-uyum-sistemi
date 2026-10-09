"""Okul rengi (tema_renk): öğrenci ve okul paneli arayüzündeki ayırıcı ve vurgu çizgilerinin rengi

Revision ID: 0021_okul_tema
Revises: 0020_meslek_dili
Create Date: 2026-10-09
"""
from alembic import op

revision = "0021_okul_tema"
down_revision = "0020_meslek_dili"
branch_labels = None
depends_on = None

SQL = "ALTER TABLE okullar ADD COLUMN IF NOT EXISTS tema_renk TEXT;"


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE okullar DROP COLUMN IF EXISTS tema_renk;")
