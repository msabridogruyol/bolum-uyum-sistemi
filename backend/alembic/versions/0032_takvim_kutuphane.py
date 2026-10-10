"""Takvim (genel / okul / kişisel etkinlikler) + öğrenci kütüphanesi (kitap, film, kurs, etkinlik günlüğü)

Revision ID: 0032_takvim_kutuphane
Revises: 0031_yetkili_unvan
Create Date: 2026-10-10
"""
from alembic import op

revision = "0032_takvim_kutuphane"
down_revision = "0031_yetkili_unvan"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS takvim_etkinlikleri (
    id SERIAL PRIMARY KEY,
    okul_id INTEGER REFERENCES okullar(id) ON DELETE CASCADE,
    ogrenci_id UUID REFERENCES ogrenciler(id) ON DELETE CASCADE,
    baslik VARCHAR NOT NULL,
    aciklama VARCHAR,
    tur VARCHAR NOT NULL DEFAULT 'diger',
    baslangic DATE NOT NULL,
    bitis DATE,
    saat VARCHAR,
    hedef_sinif VARCHAR,
    link VARCHAR,
    olusturan VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_takvim_okul_tarih ON takvim_etkinlikleri (okul_id, baslangic);
CREATE INDEX IF NOT EXISTS ix_takvim_ogrenci ON takvim_etkinlikleri (ogrenci_id) WHERE ogrenci_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS ogrenci_kutuphane (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    kategori VARCHAR NOT NULL,
    alt_tur VARCHAR,
    baslik VARCHAR NOT NULL,
    kisi VARCHAR,
    durum VARCHAR NOT NULL DEFAULT 'bitti',
    puan INTEGER,
    notlar VARCHAR,
    tarih DATE,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    guncelleme_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_kutuphane_ogrenci ON ogrenci_kutuphane (ogrenci_id, kategori)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ogrenci_kutuphane; DROP TABLE IF EXISTS takvim_etkinlikleri;")
