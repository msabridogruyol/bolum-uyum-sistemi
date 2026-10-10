"""Test hesapları: 2 adımsız giriş + giriş bağlantısı (yalnızca süper admin açar)

Revision ID: 0025_test_hesaplari
Revises: 0024_favori_bolum
Create Date: 2026-10-10
"""
from alembic import op

revision = "0025_test_hesaplari"
down_revision = "0024_favori_bolum"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS test_hesabi BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS test_giris_anahtari VARCHAR;
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS test_giris_bitis TIMESTAMPTZ;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS test_hesabi BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS test_giris_anahtari VARCHAR;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS test_giris_bitis TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_ogrenciler_test_giris_anahtari ON ogrenciler (test_giris_anahtari) WHERE test_giris_anahtari IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_admin_test_giris_anahtari ON admin_kullanicilar (test_giris_anahtari) WHERE test_giris_anahtari IS NOT NULL;
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
