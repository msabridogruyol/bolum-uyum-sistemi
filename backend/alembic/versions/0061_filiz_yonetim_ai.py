"""Filiz yönetim asistanı — yapay zekâ modu: yönetici başına günlük soru sayacı + günlük sınır parametresi

Revision ID: 0061_filiz_yonetim_ai
Revises: 0060_hata_kayitlari
Create Date: 2026-10-11

app/core/filiz_yonetim_ai.py: sorular KAYDEDİLMEZ; yalnızca (yönetici, gün) başına yapay zekâ çağrısı sayısı tutulur.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0061_filiz_yonetim_ai"
down_revision = "0060_hata_kayitlari"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS filiz_yonetim_sayac (
    admin_id UUID NOT NULL REFERENCES admin_kullanicilar(id) ON DELETE CASCADE,
    gun DATE NOT NULL,
    sayi INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (admin_id, gun)
);
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani) VALUES
    ('filiz_yonetim_gunluk_limit', '50', 'Filiz yönetim asistanı: yönetici başına günlük yapay zekâ sorusu (dolunca rehber modu)', now())
ON CONFLICT (anahtar) DO NOTHING
"""


def upgrade():
    op.execute(SQL)
