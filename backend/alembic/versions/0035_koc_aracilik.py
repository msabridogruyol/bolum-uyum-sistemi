"""Koç aracılığı: görünen ad (öğrenci tam adı görmez), görüşme bağlantısı (yönetim girer), görüşme sonrası değerlendirme

Revision ID: 0035_koc_aracilik
Revises: 0034_koc_okullari
Create Date: 2026-10-10
"""
from alembic import op

revision = "0035_koc_aracilik"
down_revision = "0034_koc_okullari"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE egitim_koclari ADD COLUMN IF NOT EXISTS gorunen_ad VARCHAR;
ALTER TABLE koc_gorusme_talepleri ADD COLUMN IF NOT EXISTS gorusme_linki VARCHAR;
ALTER TABLE koc_gorusme_talepleri ADD COLUMN IF NOT EXISTS degerlendirme_puan INTEGER;
ALTER TABLE koc_gorusme_talepleri ADD COLUMN IF NOT EXISTS degerlendirme_yorum VARCHAR;
ALTER TABLE koc_gorusme_talepleri ADD COLUMN IF NOT EXISTS degerlendirme_zamani TIMESTAMPTZ
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
