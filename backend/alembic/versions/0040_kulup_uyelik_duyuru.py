"""Kulüp üyeliği (öğrenci katılma talebi → okul yetkilisi onayı) ve kulüp duyuruları / etkinlikleri

Revision ID: 0040_kulup_uyelik_duyuru
Revises: 0039_sinav_konulari
Create Date: 2026-10-10
"""
from alembic import op

revision = "0040_kulup_uyelik_duyuru"
down_revision = "0039_sinav_konulari"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS kulup_uyelikleri (
    id SERIAL PRIMARY KEY,
    kulup_id INTEGER NOT NULL REFERENCES okul_kulupleri(id) ON DELETE CASCADE,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    durum VARCHAR NOT NULL DEFAULT 'bekliyor',
    mesaj VARCHAR,
    yanit VARCHAR,
    talep_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    karar_zamani TIMESTAMPTZ,
    karar_veren VARCHAR,
    UNIQUE (kulup_id, ogrenci_id)
);
CREATE INDEX IF NOT EXISTS ix_kulup_uyelik_ogrenci ON kulup_uyelikleri (ogrenci_id);
CREATE TABLE IF NOT EXISTS kulup_duyurulari (
    id SERIAL PRIMARY KEY,
    kulup_id INTEGER NOT NULL REFERENCES okul_kulupleri(id) ON DELETE CASCADE,
    tur VARCHAR NOT NULL DEFAULT 'duyuru',
    baslik VARCHAR NOT NULL,
    metin VARCHAR,
    tarih DATE,
    saat VARCHAR,
    yer VARCHAR,
    herkese BOOLEAN NOT NULL DEFAULT FALSE,
    olusturan VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_kulup_duyuru_kulup ON kulup_duyurulari (kulup_id, olusturulma_zamani)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
