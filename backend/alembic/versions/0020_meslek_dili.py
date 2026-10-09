"""Meslek dili (jargon) sözlüğünün düzenlenebilir sürümleri: genel (süper admin) + okula özel (okul yetkilisi)

Satır yoksa backend/app/core/meslek_jargonu.json'daki varsayılan içerik gösterilir; bu yüzden veri taşıma yok.

Revision ID: 0020_meslek_dili
Revises: 0019_yetkinlik_adlari
Create Date: 2026-10-09
"""
from alembic import op

revision = "0020_meslek_dili"
down_revision = "0019_yetkinlik_adlari"
branch_labels = None
depends_on = None

SQL = r"""
CREATE TABLE IF NOT EXISTS meslek_dili (
    id SERIAL PRIMARY KEY,
    bolum_id INTEGER NOT NULL REFERENCES bolumler(id) ON DELETE CASCADE,
    okul_id INTEGER NULL REFERENCES okullar(id) ON DELETE CASCADE,
    terimler JSONB NOT NULL DEFAULT '[]'::jsonb,
    guncelleyen_ad TEXT,
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Bir bölüm için en fazla bir genel (okul_id NULL) ve okul başına bir özel sürüm
CREATE UNIQUE INDEX IF NOT EXISTS ux_meslek_dili_bolum_okul ON meslek_dili (bolum_id, COALESCE(okul_id, 0));
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS meslek_dili;")
