"""Net takibi: öğrenci deneme sonuçları, konu takibi, hedef program ve YÖK Atlas Net Sihirbazı önbelleği

Revision ID: 0037_net_takibi
Revises: 0036_kocluk_geri_bildirim_olcum
Create Date: 2026-10-10
"""
from alembic import op

revision = "0037_net_takibi"
down_revision = "0036_kocluk_geri_bildirim_olcum"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS ogrenci_denemeleri (
    id BIGSERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    tarih DATE NOT NULL,
    oturum VARCHAR NOT NULL,
    ad VARCHAR,
    dersler JSONB NOT NULL,
    toplam_net NUMERIC(6,2) NOT NULL,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_deneme_ogrenci ON ogrenci_denemeleri (ogrenci_id, tarih);
CREATE TABLE IF NOT EXISTS ogrenci_konu_takibi (
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    ders VARCHAR NOT NULL,
    konu VARCHAR NOT NULL,
    durum VARCHAR NOT NULL,
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ogrenci_id, ders, konu)
);
CREATE TABLE IF NOT EXISTS ogrenci_net_hedefi (
    ogrenci_id UUID PRIMARY KEY REFERENCES ogrenciler(id) ON DELETE CASCADE,
    kilavuz_kodu INTEGER NOT NULL,
    veri JSONB NOT NULL,
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS yokatlas_net_onbellek (
    bolum_id INTEGER PRIMARY KEY REFERENCES bolumler(id) ON DELETE CASCADE,
    veri JSONB,
    guncellenme TIMESTAMPTZ,
    hata VARCHAR
)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
