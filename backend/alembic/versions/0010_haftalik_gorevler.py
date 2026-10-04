"""Haftalık görevler tablosu (seri + Filiz seviyesi bu tablodan hesaplanır)

Revision ID: 0010_haftalik_gorevler
Revises: 0009_gelisim_adim_durumu
Create Date: 2026-10-04
"""
from alembic import op

revision = "0010_haftalik_gorevler"
down_revision = "0009_gelisim_adim_durumu"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS ogrenci_haftalik_gorev (
    id                 BIGSERIAL PRIMARY KEY,
    ogrenci_id         UUID    NOT NULL REFERENCES ogrenciler(id),
    hafta_baslangic    DATE    NOT NULL,
    sira               INTEGER NOT NULL,
    tur                VARCHAR NOT NULL,
    baslik             VARCHAR NOT NULL,
    aciklama           VARCHAR,
    ref_kod            VARCHAR,
    ref_bolum_id       INTEGER REFERENCES bolumler(id),
    link               VARCHAR,
    durum              VARCHAR NOT NULL DEFAULT 'bekliyor',
    yanit              TEXT,
    tamamlanma_zamani  TIMESTAMPTZ,
    olusturulma_zamani TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT ck_ohg_tur CHECK (tur IN ('katman','k5','hedef','plan_adimi','kesif','yansitma')),
    CONSTRAINT ck_ohg_durum CHECK (durum IN ('bekliyor','tamamlandi')),
    CONSTRAINT uq_ohg_ogrenci_hafta_sira UNIQUE (ogrenci_id, hafta_baslangic, sira)
);
CREATE INDEX IF NOT EXISTS ix_ohg_ogrenci_hafta ON ogrenci_haftalik_gorev (ogrenci_id, hafta_baslangic);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ogrenci_haftalik_gorev")
