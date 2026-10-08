"""YÖK Atlas önbellek tablosu

Revision ID: 0015_yokatlas_onbellek
Revises: 0014_bolum_detay
Create Date: 2026-10-08
"""
from alembic import op

revision = "0015_yokatlas_onbellek"
down_revision = "0014_bolum_detay"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS yokatlas_onbellek (
    bolum_id    INT PRIMARY KEY REFERENCES bolumler(id),
    veri        JSONB,
    guncellenme TIMESTAMPTZ,
    hata        TEXT
);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS yokatlas_onbellek;")
