"""Okul rengi: paletteki 'Mor' (#6D28D9) mavimsi görünüyordu; belirgin mor (#8E24AA) yapıldı, kayıtlı okullar taşınır

Revision ID: 0038_mor_renk
Revises: 0037_net_takibi
Create Date: 2026-10-10
"""
from alembic import op

revision = "0038_mor_renk"
down_revision = "0037_net_takibi"
branch_labels = None
depends_on = None

SQL = """
UPDATE okullar SET tema_renk = '#8E24AA' WHERE upper(tema_renk) = '#6D28D9'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
