"""İş Hayatı — Mülakat Simülasyonu sonuçları

Revision ID: 0070_mulakat_simulasyonu
Revises: 0069_sonuc_epostasi
Create Date: 2026-10-13

[2026-10-13]
* is_hayati_mulakat_sim: öğrencinin bir bölümün mülakat simülasyonunda hangi adayı seçtiği ve kaç soruda mülakatçıyla aynı
  düşündüğü. Yalnızca öğrencinin kendi uçlarından okunur.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0070_mulakat_simulasyonu"
down_revision = "0069_sonuc_epostasi"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS is_hayati_mulakat_sim (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    bolum_id INTEGER REFERENCES bolumler(id) ON DELETE SET NULL,
    secimler JSONB NOT NULL DEFAULT '{}',
    dogru INTEGER NOT NULL DEFAULT 0,
    toplam INTEGER NOT NULL DEFAULT 0,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ih_mulakat_sim_ogrenci ON is_hayati_mulakat_sim (ogrenci_id, bolum_id, olusturulma_zamani DESC)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS is_hayati_mulakat_sim")
