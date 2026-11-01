"""Veri kaynakları takibi: süper adminin kontrol kayıtları

Revision ID: 0085_veri_kaynagi_kontrol
Revises: 0084_filiz_olcum
Create Date: 2026-11-01

[2026-11-01] Sistemdeki dış veriler (TÜİK, YÖK Atlas, asgari ücret, kamu maaşları, bölüm profilleri…) için süper admin
"Veri Kaynakları" ekranından "kontrol ettim / güncelledim / sorun var" kaydı bırakır. Verinin kendi son güncelleme zamanı
ilgili tablolardan okunur (app/core/veri_kaynaklari.py); bu tablo yalnızca elle yapılan kontrolleri tutar.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0085_veri_kaynagi_kontrol"
down_revision = "0084_filiz_olcum"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS veri_kaynagi_kontrolleri (
    id SERIAL PRIMARY KEY,
    kaynak_kodu VARCHAR(40) NOT NULL,
    sonuc VARCHAR(12) NOT NULL,
    notlar TEXT,
    kontrol_eden VARCHAR(200),
    admin_id UUID,
    zaman TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_veri_kaynagi_kontrol_kod_zaman ON veri_kaynagi_kontrolleri (kaynak_kodu, zaman DESC)
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    op.execute("DROP TABLE IF EXISTS veri_kaynagi_kontrolleri")
