"""En çok / en az cevap biçimi: sorular.cevap_bicimi, ogrenci_cevaplar.en_az_secenek_id

Revision ID: 0012_encok_enaz
Revises: 0011_hesap_guvenligi
Create Date: 2026-10-08
"""
from alembic import op

revision = "0012_encok_enaz"
down_revision = "0011_hesap_guvenligi"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS cevap_bicimi TEXT NOT NULL DEFAULT 'tek';
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_cevap_bicimi') THEN
    ALTER TABLE sorular ADD CONSTRAINT ck_cevap_bicimi CHECK (cevap_bicimi IN ('tek','encok_enaz'));
  END IF;
END $$;
ALTER TABLE ogrenci_cevaplar ADD COLUMN IF NOT EXISTS en_az_secenek_id INT REFERENCES soru_secenekleri(id);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE ogrenci_cevaplar DROP COLUMN IF EXISTS en_az_secenek_id;")
    op.execute("ALTER TABLE sorular DROP CONSTRAINT IF EXISTS ck_cevap_bicimi;")
    op.execute("ALTER TABLE sorular DROP COLUMN IF EXISTS cevap_bicimi;")
