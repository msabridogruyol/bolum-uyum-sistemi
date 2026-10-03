"""Koçluk yol haritası — adım bazlı ilerleme tablosu

Revision ID: 0009_gelisim_adim_durumu
Revises: 0008_ekim_duzeltmeleri
Create Date: 2026-10-03

Adım içerikleri veritabanında değil app/core/gelisim_icerigi.py dosyasındadır;
bu tablo yalnızca öğrencinin her adım için işaretlediği durumu saklar.
"""
from alembic import op

revision = "0009_gelisim_adim_durumu"
down_revision = "0008_ekim_duzeltmeleri"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS ogrenci_gelisim_adim_durumu (
            id                BIGSERIAL PRIMARY KEY,
            ogrenci_id        UUID    NOT NULL REFERENCES ogrenciler(id),
            hedef_bolum_id    INTEGER NOT NULL REFERENCES bolumler(id),
            adim_kodu         VARCHAR NOT NULL,
            durum             VARCHAR NOT NULL DEFAULT 'planlandi',
            guncelleme_zamani TIMESTAMPTZ DEFAULT now(),
            CONSTRAINT ck_ogadim_durum CHECK (durum IN ('planlandi','devam_ediyor','tamamlandi')),
            CONSTRAINT uq_ogadim_ogrenci_bolum_adim UNIQUE (ogrenci_id, hedef_bolum_id, adim_kodu)
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ogrenci_gelisim_adim_durumu")
