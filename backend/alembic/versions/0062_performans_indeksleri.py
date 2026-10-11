"""Performans indeksleri — okul paneli, rehberlik, istatistik ve Filiz özetinin dayandığı sorgular

Revision ID: 0062_performans_indeksleri
Revises: 0061_filiz_yonetim_ai
Create Date: 2026-10-11

[2026-10-11] 10.000 öğrencilik simülasyonda okul_yonetimi._ilerleme (okul başına öğrenci ilerlemesi) 3.000 öğrencili
okulda 5 dakikada bitmedi: ilişkili alt sorgular ogrenci_bolum_uyum_skorlari (2,35 milyon satır) ve
ogrenci_katman_oturumlari tablolarında tur_id ile arıyor, mevcut tekil indeksler ise ogrenci_id ile başlıyor.
Bu indekslerle aynı sorgu 0,25 saniyede bitti.
İdempotent (IF NOT EXISTS): app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0062_performans_indeksleri"
down_revision = "0061_filiz_yonetim_ai"
branch_labels = None
depends_on = None

SQL = """
CREATE INDEX IF NOT EXISTS ix_obus_tur_uyum ON ogrenci_bolum_uyum_skorlari (tur_id, toplam_uyum DESC);
CREATE INDEX IF NOT EXISTS ix_oko_tur ON ogrenci_katman_oturumlari (tur_id);
CREATE INDEX IF NOT EXISTS ix_ohb_ogrenci_aktif ON ogrenci_hedef_bolum (ogrenci_id) WHERE aktif_mi;
CREATE INDEX IF NOT EXISTS ix_guvenlik_olay_ogrenci ON guvenlik_olaylari (ogrenci_id, tur_id)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_obus_tur_uyum; DROP INDEX IF EXISTS ix_oko_tur; "
               "DROP INDEX IF EXISTS ix_ohb_ogrenci_aktif; DROP INDEX IF EXISTS ix_guvenlik_olay_ogrenci")
