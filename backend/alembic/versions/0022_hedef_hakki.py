"""Hedef bölüm değiştirme hakkı: öğrenci en fazla 3 kez değiştirebilir (ilk seçim sayılmaz); yönetim ek hak verebilir

Revision ID: 0022_hedef_hakki
Revises: 0021_okul_tema
Create Date: 2026-10-09
"""
from alembic import op

revision = "0022_hedef_hakki"
down_revision = "0021_okul_tema"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS hedef_degisim_sayisi INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS hedef_degisim_hakki INTEGER NOT NULL DEFAULT 3;
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE ogrenciler DROP COLUMN IF EXISTS hedef_degisim_sayisi, DROP COLUMN IF EXISTS hedef_degisim_hakki;")
