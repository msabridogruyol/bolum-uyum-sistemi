"""Sınav güvenliği: yeni olay türleri (ikinci ekran, ekran görüntüsü tuşu, kopyalama, kamera kapandı)

Revision ID: 0026_guvenlik_olay_tipleri
Revises: 0025_test_hesaplari
Create Date: 2026-10-10
"""
from alembic import op

revision = "0026_guvenlik_olay_tipleri"
down_revision = "0025_test_hesaplari"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE guvenlik_olaylari DROP CONSTRAINT IF EXISTS ck_go_olay_tipi;
ALTER TABLE guvenlik_olaylari ADD CONSTRAINT ck_go_olay_tipi CHECK (olay_tipi IN (
    'tam_ekrandan_cikti','tam_ekrana_geri_donuldu','sekme_degisti','sekmeye_geri_donuldu',
    'pencere_odagi_kaybedildi','pencere_odagi_geri_kazanildi',
    'kamera_izni_reddedildi','kamera_desteklenmiyor','kamera_rizasi_verilmedi',
    'coklu_ekran','ekran_goruntusu_tusu','kopyalama','kamera_kapandi'));
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
