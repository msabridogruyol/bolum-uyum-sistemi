"""Okul tanıtım bilgileri: kuruluş yılı, öğrenci sayısı, kısa tanıtım, iletişim ve kadro (müdür, rehber öğretmen ...)

Revision ID: 0018_okul_bilgileri
Revises: 0017_okul_yonetimi
Create Date: 2026-10-09
"""
from alembic import op

revision = "0018_okul_bilgileri"
down_revision = "0017_okul_yonetimi"
branch_labels = None
depends_on = None

SQL = r"""
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS kurulus_yili INTEGER;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS ogrenci_sayisi INTEGER;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS tanitim TEXT;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS adres TEXT;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS telefon TEXT;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS eposta TEXT;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS web TEXT;
-- kadro: [{"gorev": "Müdür", "ad": "...", "eposta": "...", "telefon": "..."}]
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS kadro JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS bilgi_guncelleme_zamani TIMESTAMPTZ;
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE okullar DROP COLUMN IF EXISTS kurulus_yili, DROP COLUMN IF EXISTS ogrenci_sayisi, "
               "DROP COLUMN IF EXISTS tanitim, DROP COLUMN IF EXISTS adres, DROP COLUMN IF EXISTS telefon, "
               "DROP COLUMN IF EXISTS eposta, DROP COLUMN IF EXISTS web, DROP COLUMN IF EXISTS kadro, "
               "DROP COLUMN IF EXISTS bilgi_guncelleme_zamani;")
