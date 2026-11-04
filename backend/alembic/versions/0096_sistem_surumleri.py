"""Sistem sürümleri (güncellenme zamanı)

Revision ID: 0096_sistem_surumleri
Revises: 0095_gece_bakimi_ve_hesap
Create Date: 2026-11-04

[2026-11-04] Kullanıcı kuralı: sistemin güncellenme tarihi (gün.ay.yıl saat:dakika:saniye) ekranda görünmeli.
Sunucu her açılışta kod sürümünü (Render'da RENDER_GIT_COMMIT, yoksa kaynak dosyaların özeti) yazar; sürüm ilk kez
görüldüğünde satır eklenir, ilk_calisma o sürümün yayına girdiği andır. Ücretsiz planda sunucu uyuyup uyanınca yeni satır
eklenmez (sürüm aynı). İdempotent; app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0096_sistem_surumleri"
down_revision = "0095_gece_bakimi_ve_hesap"
branch_labels = None
depends_on = None

SQL = r"""
CREATE TABLE IF NOT EXISTS sistem_surumleri (
    id BIGSERIAL PRIMARY KEY,
    surum VARCHAR(64) NOT NULL UNIQUE,
    ilk_calisma TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
