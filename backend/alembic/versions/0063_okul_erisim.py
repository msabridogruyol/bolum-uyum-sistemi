"""Okul bazında sistem erişimi aç/kapat

Revision ID: 0063_okul_erisim
Revises: 0062_performans_indeksleri
Create Date: 2026-10-11

[2026-10-11] Süper admin bir okulun sistemini kapatabilir: o okulun öğrencileri ve okul yetkilileri giriş yapamaz,
açık oturumları da bir sonraki istekte "Sisteminiz şu anda kapalıdır" uyarısıyla sonlanır.
okullar.aktif_mi bu iş için KULLANILMAZ: o alan "amblem öğrencilere gösterilsin mi" anlamına geliyor.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0063_okul_erisim"
down_revision = "0062_performans_indeksleri"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS erisim_acik BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS kapali_mesaji VARCHAR(300);
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS erisim_guncelleme_zamani TIMESTAMPTZ
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE okullar DROP COLUMN IF EXISTS erisim_acik; ALTER TABLE okullar DROP COLUMN IF EXISTS kapali_mesaji; "
               "ALTER TABLE okullar DROP COLUMN IF EXISTS erisim_guncelleme_zamani")
