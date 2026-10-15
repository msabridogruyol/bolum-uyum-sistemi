"""İş Hayatı — Düşünme Atölyesi ilerlemesi

Revision ID: 0071_dusunme_atolyesi
Revises: 0070_mulakat_simulasyonu
Create Date: 2026-10-13

[2026-10-13]
* is_hayati_dusunme: öğrencinin bir düşünme aracı modülünü bitirmesi (öğrenci + araç başına tek satır, son deneme saklanır).
  ilk: aracı öğrenmeden önceki alıştırmada ilk seferde doğru sayısı; son: okulda / iş hayatı sorularının sonucu.
  Yalnızca öğrencinin kendi uçlarından okunur.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0071_dusunme_atolyesi"
down_revision = "0070_mulakat_simulasyonu"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS is_hayati_dusunme (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    arac_kod VARCHAR NOT NULL,
    ilk JSONB NOT NULL DEFAULT '{}',
    son JSONB NOT NULL DEFAULT '{}',
    deneme INTEGER NOT NULL DEFAULT 1,
    tamamlanma_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ogrenci_id, arac_kod)
)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS is_hayati_dusunme")
