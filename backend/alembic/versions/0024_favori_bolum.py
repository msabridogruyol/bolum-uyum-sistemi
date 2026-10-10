"""Öğrenci "Listem" — favori bölümler (★)

Revision ID: 0024_favori_bolum
Revises: 0023_kaynak_olay
Create Date: 2026-10-10
"""
from alembic import op

revision = "0024_favori_bolum"
down_revision = "0023_kaynak_olay"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS ogrenci_favori_bolumler (
  id BIGSERIAL PRIMARY KEY,
  ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
  bolum_id INTEGER NOT NULL REFERENCES bolumler(id) ON DELETE CASCADE,
  eklenme_zamani TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT uq_ofb_ogrenci_bolum UNIQUE (ogrenci_id, bolum_id)
);
CREATE INDEX IF NOT EXISTS ix_ogrenci_favori_bolumler_ogrenci_id ON ogrenci_favori_bolumler (ogrenci_id);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ogrenci_favori_bolumler;")
