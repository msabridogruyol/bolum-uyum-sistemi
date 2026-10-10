"""Koçluk motoru: adım geri bildirimi (ne yaptım / ne öğrendim / fayda / zorluk) ve alan tekrar ölçümü

Revision ID: 0036_kocluk_geri_bildirim_olcum
Revises: 0035_koc_aracilik
Create Date: 2026-10-10
"""
from alembic import op

revision = "0036_kocluk_geri_bildirim_olcum"
down_revision = "0035_koc_aracilik"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenci_gelisim_adim_durumu ADD COLUMN IF NOT EXISTS ne_yaptim VARCHAR;
ALTER TABLE ogrenci_gelisim_adim_durumu ADD COLUMN IF NOT EXISTS ne_ogrendim VARCHAR;
ALTER TABLE ogrenci_gelisim_adim_durumu ADD COLUMN IF NOT EXISTS fayda INTEGER;
ALTER TABLE ogrenci_gelisim_adim_durumu ADD COLUMN IF NOT EXISTS zorluk VARCHAR;
CREATE TABLE IF NOT EXISTS ogrenci_alan_olcumleri (
    id BIGSERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    degisken_id INTEGER NOT NULL REFERENCES degiskenler(id),
    hedef_bolum_id INTEGER REFERENCES bolumler(id),
    onceki_puan NUMERIC(5,1) NOT NULL,
    yeni_puan NUMERIC(5,1) NOT NULL,
    soru_sayisi INTEGER NOT NULL,
    cevaplar JSONB,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_alan_olcum_ogrenci ON ogrenci_alan_olcumleri (ogrenci_id, degisken_id)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
