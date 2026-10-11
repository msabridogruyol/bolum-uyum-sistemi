"""Rehberlik görüşme kayıtları (randevu + not + takip) ve erken uyarı ertelemeleri

Revision ID: 0042_rehberlik
Revises: 0041_paketler
Create Date: 2026-10-10
"""
from alembic import op

revision = "0042_rehberlik"
down_revision = "0041_paketler"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS rehberlik_gorusmeleri (
    id SERIAL PRIMARY KEY,
    okul_id INTEGER REFERENCES okullar(id) ON DELETE CASCADE,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    zaman TIMESTAMPTZ NOT NULL,
    durum VARCHAR NOT NULL DEFAULT 'yapildi',
    tur VARCHAR NOT NULL DEFAULT 'bireysel',
    konu VARCHAR NOT NULL DEFAULT 'akademik',
    baslik VARCHAR,
    notlar TEXT,
    takip_tarihi DATE,
    takip_tamam BOOLEAN NOT NULL DEFAULT FALSE,
    ogrenciye_goster BOOLEAN NOT NULL DEFAULT TRUE,
    olusturan_id UUID,
    olusturan VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_rg_okul_zaman ON rehberlik_gorusmeleri (okul_id, zaman);
CREATE INDEX IF NOT EXISTS ix_rg_ogrenci ON rehberlik_gorusmeleri (ogrenci_id, zaman);
CREATE TABLE IF NOT EXISTS risk_ertelemeleri (
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    kural VARCHAR NOT NULL,
    bitis DATE NOT NULL,
    olusturan VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ogrenci_id, kural)
);
UPDATE paketler SET moduller = moduller || '["rehberlik"]'::jsonb
 WHERE kod IN ('gelisim', 'tam') AND NOT moduller ? 'rehberlik'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
