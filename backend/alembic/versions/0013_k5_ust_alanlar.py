"""K5 yeni yapı: bolum_dal_eslesme.alt_alan, bolum_k5_baglari tablosu

Revision ID: 0013_k5_ust_alanlar
Revises: 0012_encok_enaz
Create Date: 2026-10-08
"""
from alembic import op

revision = "0013_k5_ust_alanlar"
down_revision = "0012_encok_enaz"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE bolum_dal_eslesme ADD COLUMN IF NOT EXISTS alt_alan TEXT;
CREATE TABLE IF NOT EXISTS bolum_k5_baglari (
    id          SERIAL PRIMARY KEY,
    bolum_id    INT NOT NULL REFERENCES bolumler(id),
    degisken_id INT NOT NULL REFERENCES degiskenler(id),
    bag         NUMERIC(3,2) NOT NULL,
    CONSTRAINT uq_bk5_bolum_degisken UNIQUE (bolum_id, degisken_id)
);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS bolum_k5_baglari;")
    op.execute("ALTER TABLE bolum_dal_eslesme DROP COLUMN IF EXISTS alt_alan;")
