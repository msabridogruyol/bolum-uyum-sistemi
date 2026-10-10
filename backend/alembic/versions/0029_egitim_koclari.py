"""Dışarıdan anlaşmalı eğitim koçları + öğrenci/veli görüşme talepleri

Revision ID: 0029_egitim_koclari
Revises: 0028_kulupler_ilgi_testi
Create Date: 2026-10-10
"""
from alembic import op

revision = "0029_egitim_koclari"
down_revision = "0028_kulupler_ilgi_testi"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS egitim_koclari (
    id SERIAL PRIMARY KEY,
    okul_id INTEGER REFERENCES okullar(id) ON DELETE CASCADE,
    ad_soyad VARCHAR NOT NULL,
    unvan VARCHAR,
    hakkinda VARCHAR,
    alanlar VARCHAR NOT NULL DEFAULT '',
    konular VARCHAR NOT NULL DEFAULT '',
    deneyim_yil INTEGER,
    gorusme_sekli VARCHAR NOT NULL DEFAULT 'online',
    ucret_bilgisi VARCHAR,
    eposta VARCHAR,
    telefon VARCHAR,
    foto VARCHAR,
    aktif BOOLEAN NOT NULL DEFAULT TRUE,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_egitim_koclari_okul ON egitim_koclari (okul_id);
CREATE TABLE IF NOT EXISTS koc_gorusme_talepleri (
    id SERIAL PRIMARY KEY,
    koc_id INTEGER NOT NULL REFERENCES egitim_koclari(id) ON DELETE CASCADE,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    okul_id INTEGER REFERENCES okullar(id) ON DELETE SET NULL,
    talep_eden VARCHAR NOT NULL DEFAULT 'ogrenci',
    veli_ad VARCHAR,
    iletisim VARCHAR,
    konu VARCHAR NOT NULL,
    tercih_zamani VARCHAR,
    mesaj VARCHAR,
    durum VARCHAR NOT NULL DEFAULT 'beklemede',
    randevu_zamani TIMESTAMPTZ,
    ogrenciye_not VARCHAR,
    ic_not VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_koc_talep_okul ON koc_gorusme_talepleri (okul_id, durum);
CREATE INDEX IF NOT EXISTS ix_koc_talep_ogrenci ON koc_gorusme_talepleri (ogrenci_id)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS koc_gorusme_talepleri; DROP TABLE IF EXISTS egitim_koclari;")
