"""Konu takibi listesi veritabanına taşındı: genel liste (süper admin) + okula özel konular ve okulda gizlenen genel konular

Revision ID: 0039_sinav_konulari
Revises: 0038_mor_renk
Create Date: 2026-10-10
"""
from alembic import op

revision = "0039_sinav_konulari"
down_revision = "0038_mor_renk"
branch_labels = None
depends_on = None


def _ilk_liste() -> str:
    """Genel liste boşsa sinav_yapisi.KONU_DERSLERI'ndeki başlangıç konularıyla doldurulur (bir kez)."""
    from app.core.sinav_yapisi import KONU_DERSLERI
    degerler = []
    for ders, (_, _, konular) in KONU_DERSLERI.items():
        for i, k in enumerate(konular, 1):
            degerler.append("('%s', '%s', %d)" % (ders, k.replace("'", "''"), i * 10))
    return ("INSERT INTO sinav_konulari (ders, ad, sira) SELECT v.ders, v.ad, v.sira FROM (VALUES "
            + ", ".join(degerler) + ") AS v(ders, ad, sira) WHERE NOT EXISTS (SELECT 1 FROM sinav_konulari WHERE okul_id IS NULL)")


SQL = """
CREATE TABLE IF NOT EXISTS sinav_konulari (
    id SERIAL PRIMARY KEY,
    ders VARCHAR NOT NULL,
    ad VARCHAR NOT NULL,
    sira INTEGER NOT NULL DEFAULT 0,
    okul_id INTEGER REFERENCES okullar(id) ON DELETE CASCADE,
    olusturan VARCHAR,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sinav_konulari_ders ON sinav_konulari (ders, okul_id);
CREATE TABLE IF NOT EXISTS okul_konu_gizleme (
    okul_id INTEGER NOT NULL REFERENCES okullar(id) ON DELETE CASCADE,
    konu_id INTEGER NOT NULL REFERENCES sinav_konulari(id) ON DELETE CASCADE,
    PRIMARY KEY (okul_id, konu_id)
);
""" + _ilk_liste()


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
