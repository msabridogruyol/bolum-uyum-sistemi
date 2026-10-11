"""Katman ağırlıkları: K1–K4 eşit %25 (ürün kararı)

Revision ID: 0052_katman_agirliklari
Revises: 0051_simulasyon
Create Date: 2026-10-10

Not: app/core/sema_guncelleme.py bu SQL'i HER sunucu açılışında yeniden çalıştırır. UPDATE'in süper
adminin /admin/katman-agirliklari ekranından sonradan yaptığı değişikliği ezmemesi için tek seferlik
işaret tablosu (tek_seferlik_gocler) kullanılır: işaret satırı eklenebildiyse (ilk çalışma) UPDATE
uygulanır; işaret zaten varsa CTE boş döner ve UPDATE hiçbir satıra dokunmaz. İkisi tek komut olduğu
için atomiktir. Ağırlıklar gerçekten değiştiyse 'bekleyen_skor_hesabi' işareti eklenir; sunucu açılışında
tüm tamamlanmış turların uyum skorları arka planda yeniden hesaplanır ve işaret silinir (app/main.py).
"""
from alembic import op

revision = "0052_katman_agirliklari"
down_revision = "0051_simulasyon"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS tek_seferlik_gocler (
    ad VARCHAR PRIMARY KEY,
    uygulanma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
WITH isaret AS (
    INSERT INTO tek_seferlik_gocler (ad) VALUES ('0052_katman_agirliklari')
    ON CONFLICT (ad) DO NOTHING
    RETURNING ad
), guncel AS (
    UPDATE katmanlar SET normalizasyon_agirligi = 25
    WHERE kod IN ('K1','K2','K3','K4')
      AND normalizasyon_agirligi IS DISTINCT FROM 25
      AND EXISTS (SELECT 1 FROM isaret)
    RETURNING kod
)
INSERT INTO tek_seferlik_gocler (ad)
SELECT 'bekleyen_skor_hesabi' WHERE EXISTS (SELECT 1 FROM guncel)
ON CONFLICT (ad) DO NOTHING
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
