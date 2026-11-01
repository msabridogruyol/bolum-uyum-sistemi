"""Admin panelinden veri yönetimi (yedek / geri al) ve demo okul

Revision ID: 0087_veri_yonetimi_demo
Revises: 0086_onlisans_bolum_kaldirma
Create Date: 2026-11-01

[2026-11-01]
  * veri_yedekleri: Pipeline Sonuçları ekranından K5 iş türü bağları ve örnek meslekler yüklenirken önceki hâl buraya
    yazılır; ekrandan "önceki sürüme dön" yapılabilir (Supabase SQL ekranı gerekmez).
  * bolum_ornek_meslekler: canlıda elle oluşturulmuştu, göç dosyası yoktu. Yoksa aynı sütunlarla oluşturulur
    (varsa dokunulmaz).
  * bolum_agirliklari_taslak: Pipeline Sonuçları 1. adımın taslak tablosu; o da canlıda elle oluşturulmuştu. Yoksa
    oluşturulur (varsa dokunulmaz).
  * okullar.demo: Test Hesapları ekranından açılan tanıtım okulu işareti; yalnızca demo okul tek tuşla silinebilir.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0087_veri_yonetimi_demo"
down_revision = "0086_onlisans_bolum_kaldirma"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS veri_yedekleri (
    id SERIAL PRIMARY KEY,
    tur VARCHAR(40) NOT NULL,
    satir_sayisi INTEGER NOT NULL DEFAULT 0,
    veri JSONB NOT NULL,
    aciklama TEXT,
    admin_id UUID,
    kaydeden VARCHAR(200),
    zaman TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_veri_yedekleri_tur_zaman ON veri_yedekleri (tur, zaman DESC);
CREATE TABLE IF NOT EXISTS bolum_ornek_meslekler (
    id SERIAL PRIMARY KEY,
    bolum_id INTEGER NOT NULL REFERENCES bolumler(id) ON DELETE CASCADE,
    meslek_isco_kodu VARCHAR(40),
    meslek_adi VARCHAR(300) NOT NULL,
    benzerlik_skoru NUMERIC(6,4),
    model_sayisi INTEGER,
    sira INTEGER
);
CREATE TABLE IF NOT EXISTS bolum_agirliklari_taslak (
    id BIGSERIAL PRIMARY KEY,
    yukleme_grubu VARCHAR(64) NOT NULL,
    bolum_adi_ham VARCHAR,
    degisken_kod_ham VARCHAR,
    bolum_id INTEGER REFERENCES bolumler(id) ON DELETE CASCADE,
    degisken_id INTEGER REFERENCES degiskenler(id),
    agirlik_degeri NUMERIC(5,2) NOT NULL,
    yakinsama_skoru NUMERIC(10,4),
    agirlikli_varyans NUMERIC(12,4),
    etkin_meslek_sayisi INTEGER,
    yukleyen_admin_id UUID,
    durum VARCHAR(20) NOT NULL DEFAULT 'bekliyor',
    yuklenme_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_bolum_agirliklari_taslak_grup ON bolum_agirliklari_taslak (yukleme_grubu);
ALTER TABLE okullar ADD COLUMN IF NOT EXISTS demo BOOLEAN NOT NULL DEFAULT FALSE
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    op.execute("ALTER TABLE okullar DROP COLUMN IF EXISTS demo")
    op.execute("DROP TABLE IF EXISTS veri_yedekleri")
