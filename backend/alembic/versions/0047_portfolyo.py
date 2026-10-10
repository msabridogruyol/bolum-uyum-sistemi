"""e-Portfolyo: sertifika, yarışma, gönüllülük, proje … kayıtları (rehber doğrulamalı) ve özgeçmiş profili

Revision ID: 0047_portfolyo
Revises: 0046_bildirimler
Create Date: 2026-10-10
"""
from alembic import op

revision = "0047_portfolyo"
down_revision = "0046_bildirimler"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS portfolyo_kayitlari (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    tur VARCHAR NOT NULL,
    baslik VARCHAR NOT NULL,
    kurum VARCHAR,
    baslangic DATE,
    bitis DATE,
    aciklama TEXT,
    saat INTEGER,
    derece VARCHAR,
    link VARCHAR,
    belge TEXT,
    belge_adi VARCHAR,
    dogrulandi BOOLEAN NOT NULL DEFAULT FALSE,
    dogrulayan VARCHAR,
    dogrulama_zamani TIMESTAMPTZ,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_portfolyo_ogrenci ON portfolyo_kayitlari (ogrenci_id);
CREATE TABLE IF NOT EXISTS portfolyo_profil (
    ogrenci_id UUID PRIMARY KEY REFERENCES ogrenciler(id) ON DELETE CASCADE,
    hakkimda TEXT,
    yetenekler JSONB NOT NULL DEFAULT '[]',
    diller JSONB NOT NULL DEFAULT '[]',
    eposta_goster BOOLEAN NOT NULL DEFAULT FALSE
);
UPDATE paketler SET moduller = moduller || '["portfolyo"]'::jsonb WHERE kod IN ('gelisim', 'tam') AND NOT moduller ? 'portfolyo'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
