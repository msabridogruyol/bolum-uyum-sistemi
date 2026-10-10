"""Paketler: okul bazında modül seçimi (Temel / Gelişim / Tam + okula özel ekle-çıkar)

Revision ID: 0041_paketler
Revises: 0040_kulup_uyelik_duyuru
Create Date: 2026-10-10
"""
from alembic import op

revision = "0041_paketler"
down_revision = "0040_kulup_uyelik_duyuru"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS paketler (
    kod VARCHAR PRIMARY KEY,
    ad VARCHAR NOT NULL,
    aciklama VARCHAR,
    moduller JSONB NOT NULL DEFAULT '[]',
    sira INTEGER NOT NULL DEFAULT 0
);
INSERT INTO paketler (kod, ad, aciklama, moduller, sira) VALUES
 ('temel', 'Temel', 'Değerlendirme, bölüm önerileri, profil, okul paneli ve temel raporlar', '["takvim"]', 1),
 ('gelisim', 'Gelişim', 'Temel + kişisel koçluk, haftalık görevler, kütüphane, kulüpler ve Filiz', '["takvim","kocluk","kutuphane","kulupler","filiz"]', 2),
 ('tam', 'Tam', 'Tüm modüller: net takibi, şube ve akran analizi, eğitim koçları, toplu raporlar dahil',
  '["takvim","kocluk","kutuphane","kulupler","filiz","net_takibi","akran","egitim_koclari","gelismis_raporlar"]', 3)
ON CONFLICT (kod) DO NOTHING;
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS paket VARCHAR NOT NULL DEFAULT 'tam';
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS modul_ekle JSONB NOT NULL DEFAULT '[]';
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS modul_cikar JSONB NOT NULL DEFAULT '[]'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
