"""Eğitim koçu ↔ okul ataması (süper admin yönetir; okul bazında aktif / onay bekliyor / okul reddetti)

Revision ID: 0034_koc_okullari
Revises: 0033_kutuphane_sayfa
Create Date: 2026-10-10
"""
from alembic import op

revision = "0034_koc_okullari"
down_revision = "0033_kutuphane_sayfa"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS koc_okullari (
    koc_id INTEGER NOT NULL REFERENCES egitim_koclari(id) ON DELETE CASCADE,
    okul_id INTEGER NOT NULL REFERENCES okullar(id) ON DELETE CASCADE,
    durum VARCHAR NOT NULL DEFAULT 'aktif',
    notlar VARCHAR,
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (koc_id, okul_id)
);
ALTER TABLE egitim_koclari ADD COLUMN IF NOT EXISTS okullar_tasindi BOOLEAN NOT NULL DEFAULT FALSE;
INSERT INTO koc_okullari (koc_id, okul_id, durum)
SELECT k.id, k.okul_id, 'aktif' FROM egitim_koclari k WHERE k.okul_id IS NOT NULL AND NOT k.okullar_tasindi
ON CONFLICT DO NOTHING;
INSERT INTO koc_okullari (koc_id, okul_id, durum)
SELECT k.id, o.id, 'aktif' FROM egitim_koclari k CROSS JOIN okullar o WHERE k.okul_id IS NULL AND NOT k.okullar_tasindi
ON CONFLICT DO NOTHING;
UPDATE egitim_koclari SET okullar_tasindi = TRUE WHERE NOT okullar_tasindi
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS koc_okullari")
