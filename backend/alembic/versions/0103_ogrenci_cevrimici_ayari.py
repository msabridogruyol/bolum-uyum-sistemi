"""Öğrencilerde çevrim içi listesi: okul ayarı (varsayılan kapalı)

Revision ID: 0103_ogrenci_cevrimici_ayari
Revises: 0102_kullanim_sureleri
Create Date: 2026-11-11

[2026-11-11] Kullanıcı kararı: öğrenciler "şu an çevrim içi" listesini görmez; okul yetkilisi Okul Ayarları › Görünüm'den
açabilir. Yetkili her zaman görür. Mevcut okullar için de kapalı başlar (sütun varsayılanı false).
İdempotent; app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0103_ogrenci_cevrimici_ayari"
down_revision = "0102_kullanim_sureleri"
branch_labels = None
depends_on = None

SQL = "ALTER TABLE okullar ADD COLUMN IF NOT EXISTS ogrenci_cevrimici_acik BOOLEAN NOT NULL DEFAULT false"


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("ALTER TABLE okullar DROP COLUMN IF EXISTS ogrenci_cevrimici_acik")
