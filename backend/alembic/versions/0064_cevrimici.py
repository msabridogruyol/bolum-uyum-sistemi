"""Çevrim içi öğrenciler: son görülme zamanı ve gizlilik tercihi

Revision ID: 0064_cevrimici
Revises: 0063_okul_erisim
Create Date: 2026-10-11

[2026-10-11] Öğrenci sayfası açıkken dakikada bir "buradayım" sinyali gönderir (son_gorulme). Son 2 dakikada
sinyal gönderen öğrenci çevrim içi sayılır. Öğrenci isterse kendini gizler (cevrimici_gizli): başkalarının listesinde görünmez.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0064_cevrimici"
down_revision = "0063_okul_erisim"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS son_gorulme TIMESTAMPTZ;
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS cevrimici_gizli BOOLEAN NOT NULL DEFAULT FALSE;
CREATE INDEX IF NOT EXISTS ix_ogrenci_okul_son_gorulme ON ogrenciler (okul_id, son_gorulme)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_ogrenci_okul_son_gorulme; "
               "ALTER TABLE ogrenciler DROP COLUMN IF EXISTS son_gorulme; ALTER TABLE ogrenciler DROP COLUMN IF EXISTS cevrimici_gizli")
