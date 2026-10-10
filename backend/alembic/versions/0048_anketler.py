"""Anket ve envanterler: okulun anketleri, hazır tarama şablonları, yanıtlar (anonim anketlerde öğrenci kimliği yanıtla birlikte tutulmaz)

Revision ID: 0048_anketler
Revises: 0047_portfolyo
Create Date: 2026-10-10
"""
from alembic import op

revision = "0048_anketler"
down_revision = "0047_portfolyo"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS anketler (
    id SERIAL PRIMARY KEY,
    okul_id INTEGER NOT NULL REFERENCES okullar(id) ON DELETE CASCADE,
    baslik VARCHAR NOT NULL,
    aciklama TEXT,
    sablon VARCHAR,
    anonim BOOLEAN NOT NULL DEFAULT TRUE,
    hedef JSONB NOT NULL DEFAULT '{}',
    durum VARCHAR NOT NULL DEFAULT 'taslak',
    baslangic DATE,
    bitis DATE,
    sorular JSONB NOT NULL DEFAULT '[]',
    puanlama JSONB,
    olusturan VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_anket_okul ON anketler (okul_id, durum);
CREATE TABLE IF NOT EXISTS anket_katilim (
    anket_id INTEGER NOT NULL REFERENCES anketler(id) ON DELETE CASCADE,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (anket_id, ogrenci_id)
);
CREATE TABLE IF NOT EXISTS anket_yanitlari (
    id SERIAL PRIMARY KEY,
    anket_id INTEGER NOT NULL REFERENCES anketler(id) ON DELETE CASCADE,
    ogrenci_id UUID REFERENCES ogrenciler(id) ON DELETE SET NULL,
    sinif VARCHAR,
    sube VARCHAR,
    cevaplar JSONB NOT NULL,
    puan NUMERIC(4,2),
    seviye VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_anket_yanit_anket ON anket_yanitlari (anket_id);
UPDATE paketler SET moduller = moduller || '["anketler"]'::jsonb WHERE kod IN ('gelisim', 'tam') AND NOT moduller ? 'anketler'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
