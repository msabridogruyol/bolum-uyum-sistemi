"""Gelecekteki sana mektup

Revision ID: 0073_gelecek_mektup
Revises: 0072_ogrenme_deneyi
Create Date: 2026-10-13

[2026-10-13]
* gelecek_mektuplari: öğrencinin ileri bir tarihte kendine e-postayla gelecek mektubu. Metin ve kişisel e-posta şifreli saklanır
  (app/core/gelecek_mektup.py, Fernet). Yalnızca öğrencinin kendi uçlarından okunur; okul / yönetim ucu yoktur, yapay zekâya
  gönderilmez. durum: bekliyor | gonderildi | hata | eposta_yok.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0073_gelecek_mektup"
down_revision = "0072_ogrenme_deneyi"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS gelecek_mektuplari (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    metin_sifreli TEXT NOT NULL,
    kisisel_eposta_sifreli TEXT,
    teslim_tarihi DATE NOT NULL,
    durum VARCHAR NOT NULL DEFAULT 'bekliyor',
    gonderim_zamani TIMESTAMPTZ,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_gelecek_mektup_teslim ON gelecek_mektuplari (teslim_tarihi) WHERE durum = 'bekliyor';
CREATE INDEX IF NOT EXISTS ix_gelecek_mektup_ogrenci ON gelecek_mektuplari (ogrenci_id)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS gelecek_mektuplari")
