"""Okullar tablosu (öğrenci sayfalarında gösterilen okul adı + amblemi)

Revision ID: 0016_okullar
Revises: 0015_yokatlas_onbellek
Create Date: 2026-10-09
"""
from alembic import op

revision = "0016_okullar"
down_revision = "0015_yokatlas_onbellek"
branch_labels = None
depends_on = None

SQL = """CREATE TABLE IF NOT EXISTS okullar (
    id                 SERIAL PRIMARY KEY,
    ad                 TEXT NOT NULL,
    alt_baslik         TEXT,
    logo               TEXT,
    aktif_mi           BOOLEAN NOT NULL DEFAULT FALSE,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- aynı anda yalnızca bir okul aktif (gösterilen) olabilir
CREATE UNIQUE INDEX IF NOT EXISTS okullar_tek_aktif ON okullar (aktif_mi) WHERE aktif_mi;
INSERT INTO okullar (ad, alt_baslik, logo, aktif_mi)
SELECT 'Örnek Okul', 'iş birliğiyle', 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMjAgMTIwIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImciIHgxPSIwIiB5MT0iMCIgeDI9IjAiIHkyPSIxIj48c3RvcCBvZmZzZXQ9IjAiIHN0b3AtY29sb3I9IiMyRjVEOEEiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiMxRDNFNjAiLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cGF0aCBkPSJNNjAgNiBMMTA0IDIwIFY1OCBDMTA0IDg2IDg0IDEwNCA2MCAxMTQgQzM2IDEwNCAxNiA4NiAxNiA1OCBWMjAgWiIgZmlsbD0idXJsKCNnKSIgc3Ryb2tlPSIjQzlBMzRBIiBzdHJva2Utd2lkdGg9IjUiLz48cGF0aCBkPSJNMzQgNDYgUTQ3IDQwIDU4IDQ2IFY4MiBRNDcgNzYgMzQgODIgWiIgZmlsbD0iI0ZGRkZGRiIvPjxwYXRoIGQ9Ik04NiA0NiBRNzMgNDAgNjIgNDYgVjgyIFE3MyA3NiA4NiA4MiBaIiBmaWxsPSIjRjRFN0MzIi8+PHBhdGggZD0iTTYwIDIyIGwzLjUgNyA3LjUgMSAtNS41IDUuMyAxLjMgNy42IC02LjgtMy42IC02LjggMy42IDEuMy03LjYgLTUuNS01LjMgNy41LTEgWiIgZmlsbD0iI0M5QTM0QSIvPjx0ZXh0IHg9IjYwIiB5PSIxMDAiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJHZW9yZ2lhLHNlcmlmIiBmb250LXNpemU9IjExIiBmb250LXdlaWdodD0iNzAwIiBmaWxsPSIjRjRFN0MzIj7DllJORUs8L3RleHQ+PC9zdmc+', TRUE
WHERE NOT EXISTS (SELECT 1 FROM okullar);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS okullar;")
