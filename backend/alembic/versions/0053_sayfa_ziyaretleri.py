"""sayfa_ziyaretleri tablosu (toplu/anonim sayfa sayımı) — hiçbir göçte oluşturulmuyordu

Revision ID: 0053_sayfa_ziyaretleri
Revises: 0052_katman_agirliklari
Create Date: 2026-10-10

app/main.py ara katmanı her istekte bu tabloya yazar, /admin/kullanim-istatistikleri okur. Tablo
elle oluşturulmuş bir veritabanında zaten vardır (IF NOT EXISTS ile dokunulmaz); yoksa oluşturulur.
"""
from alembic import op

revision = "0053_sayfa_ziyaretleri"
down_revision = "0052_katman_agirliklari"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS sayfa_ziyaretleri (
    id BIGSERIAL PRIMARY KEY,
    yol VARCHAR(255) NOT NULL,
    metod VARCHAR(10) NOT NULL,
    kullanici_tipi VARCHAR(30),
    durum_kodu INTEGER,
    zaman TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sayfa_ziyaretleri_zaman ON sayfa_ziyaretleri (zaman)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
