"""İş Hayatı → Beklenti ve Gerçek: öğrencinin bölüm için iş hayatı tahminleri

Revision ID: 0055_is_hayati_beklenti
Revises: 0054_is_hayati
Create Date: 2026-10-10

Her deneme ayrı satırdır (öğrenci tekrar deneyebilir; önceki tahminle karşılaştırılır).
tahminler: {"istihdam_orani": 0-100, "is_bulma_suresi_ay": ay, "alan_uyum_orani": 0-100, "ilk_net_maas": TL}
— yalnızca öğrencinin girdiği alanlar bulunur. gercek: gönderim anındaki gerçek verinin özeti (kaynak + yıl), sonradan veri
değişse de öğrencinin neyle karşılaştırdığı kaybolmasın diye saklanır.

Not: app/core/sema_guncelleme.py bu SQL'i HER sunucu açılışında yeniden çalıştırır; komutlar idempotenttir.
"""
from alembic import op

revision = "0055_is_hayati_beklenti"
down_revision = "0054_is_hayati"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS is_hayati_beklentiler (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    bolum_id INTEGER NOT NULL REFERENCES bolumler(id) ON DELETE CASCADE,
    tahminler JSONB NOT NULL DEFAULT '{}',
    gercek JSONB,
    zaman TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_is_hayati_beklentiler_ogr_bolum ON is_hayati_beklentiler (ogrenci_id, bolum_id, zaman DESC)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS is_hayati_beklentiler")
