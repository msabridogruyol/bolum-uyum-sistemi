"""Bildirimler: uygulama içi bildirim kutusu + isteğe bağlı e-posta kuyruğu; kişi bazında e-posta tercihi

Revision ID: 0046_bildirimler
Revises: 0045_calisma
Create Date: 2026-10-10
"""
from alembic import op

revision = "0046_bildirimler"
down_revision = "0045_calisma"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS bildirimler (
    id BIGSERIAL PRIMARY KEY,
    alici_tipi VARCHAR NOT NULL,
    alici_id UUID NOT NULL,
    okul_id INTEGER,
    tur VARCHAR NOT NULL,
    baslik VARCHAR NOT NULL,
    metin VARCHAR,
    link VARCHAR,
    okundu BOOLEAN NOT NULL DEFAULT FALSE,
    eposta_durum VARCHAR NOT NULL DEFAULT 'yok',
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_bildirim_alici ON bildirimler (alici_tipi, alici_id, olusturulma_zamani DESC);
CREATE INDEX IF NOT EXISTS ix_bildirim_eposta ON bildirimler (eposta_durum) WHERE eposta_durum = 'bekliyor';
CREATE TABLE IF NOT EXISTS bildirim_tercihleri (
    kullanici_id UUID PRIMARY KEY,
    eposta BOOLEAN NOT NULL DEFAULT TRUE
);
UPDATE paketler SET moduller = moduller || '["bildirimler"]'::jsonb WHERE kod IN ('temel', 'gelisim', 'tam') AND NOT moduller ? 'bildirimler'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
