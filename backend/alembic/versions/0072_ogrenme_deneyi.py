"""İş Hayatı — Düşünme Atölyesi "Öğrenmeyi öğren" deneyi (ertesi gün 2. ölçüm)

Revision ID: 0072_ogrenme_deneyi
Revises: 0071_dusunme_atolyesi
Create Date: 2026-10-13

[2026-10-13]
* is_hayati_ogrenme_deneyi: öğrencinin "tekrar okuma" ile "kendini sınama" listelerini karşılaştırdığı küçük deneyin sonuçları.
  olcum1: aynı oturumdaki test; olcum2: en erken 12 saat sonraki test. Öğrenci başına tek satır; deney yeniden yapılırsa sıfırlanır.
  Yalnızca öğrencinin kendi uçlarından okunur.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0072_ogrenme_deneyi"
down_revision = "0071_dusunme_atolyesi"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS is_hayati_ogrenme_deneyi (
    ogrenci_id UUID PRIMARY KEY REFERENCES ogrenciler(id) ON DELETE CASCADE,
    sinama_listesi INTEGER NOT NULL DEFAULT 1,
    olcum1 JSONB NOT NULL,
    olcum1_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    olcum2 JSONB,
    olcum2_zamani TIMESTAMPTZ
)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS is_hayati_ogrenme_deneyi")
