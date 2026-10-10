"""Okul şubeleri: sınıf öğretmeni bilgisi (12-A → öğretmen adı / e-posta)

Revision ID: 0030_okul_subeleri
Revises: 0029_egitim_koclari
Create Date: 2026-10-10
"""
from alembic import op

revision = "0030_okul_subeleri"
down_revision = "0029_egitim_koclari"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS okul_subeleri (
    okul_id INTEGER NOT NULL REFERENCES okullar(id) ON DELETE CASCADE,
    sinif VARCHAR NOT NULL,
    sube VARCHAR NOT NULL,
    ogretmen_ad VARCHAR,
    ogretmen_eposta VARCHAR,
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (okul_id, sinif, sube)
)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS okul_subeleri")
