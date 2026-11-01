"""Pipeline'ın sistemden kurulması: bilgisayar anahtarları ve veri sürümleri

Revision ID: 0088_pipeline_paketi
Revises: 0087_veri_yonetimi_demo
Create Date: 2026-11-01

[2026-11-01] Süper admin, pipeline'ı her bilgisayara Pipeline Sonuçları ekranından kurar.
  * pipeline_anahtarlari: tek kullanımlık kurulum anahtarı (24 saat) ve bilgisayar anahtarı.
    Anahtarın kendisi saklanmaz, yalnızca SHA-256 özeti tutulur. Ekrandan iptal edilebilir.
  * pipeline_surumleri: her çalıştırmanın sonunda Supabase Storage'a gönderilen veri ve önbellek
    dosyalarının listesi (yol → parça özetleri). Ayrıca çalıştırmada kullanılan canlı listelerin özeti
    (bölüm, özellik, K5 cümleleri) tutulur; sayaç "son çalıştırmadan beri değişti mi" sorusunu buna bakarak yanıtlar.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0088_pipeline_paketi"
down_revision = "0087_veri_yonetimi_demo"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS pipeline_anahtarlari (
    id SERIAL PRIMARY KEY,
    tur VARCHAR(20) NOT NULL,
    ozet VARCHAR(64) NOT NULL UNIQUE,
    cihaz_adi VARCHAR(120) NOT NULL,
    olusturan_admin_id UUID,
    olusturan VARCHAR(200),
    olusturma_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    son_gecerlilik TIMESTAMPTZ,
    kullanilma_zamani TIMESTAMPTZ,
    son_kullanim TIMESTAMPTZ,
    iptal_zamani TIMESTAMPTZ,
    kurulum_anahtari_id INTEGER
);
CREATE INDEX IF NOT EXISTS ix_pipeline_anahtarlari_tur ON pipeline_anahtarlari (tur);
CREATE TABLE IF NOT EXISTS pipeline_surumleri (
    id SERIAL PRIMARY KEY,
    zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    cihaz_id INTEGER,
    cihaz_adi VARCHAR(120),
    dosyalar JSONB NOT NULL,
    girdi_ozeti JSONB,
    toplam_bayt BIGINT NOT NULL DEFAULT 0,
    aciklama TEXT
);
CREATE INDEX IF NOT EXISTS ix_pipeline_surumleri_zaman ON pipeline_surumleri (zaman DESC);
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    op.execute("DROP TABLE IF EXISTS pipeline_surumleri; DROP TABLE IF EXISTS pipeline_anahtarlari;")
