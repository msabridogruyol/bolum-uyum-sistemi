"""Toplu öğrenci işlemleri: yeni eğitim yılında sınıf atlatma (geri alınabilir) ve değerlendirmeyi sıfırlama

Revision ID: 0068_toplu_ogrenci_islemleri
Revises: 0067_coklu_dil
Create Date: 2026-10-12

[2026-10-12]
* toplu_islemler — okul genelinde yapılan toplu işlemlerin kaydı (şimdilik 'sinif_atlat'). veri: her öğrencinin eski /
  yeni sınıfı; 30 gün içinde "Geri al" bu kayıttan yapılır.
* ogrenciler.yeni_tur_izni — yönetim değerlendirmeyi sıfırladığında yazılır; öğrenci yeniden değerlendirme bekleme
  süresine takılmadan baştan başlar. Yeni tur açılınca temizlenir.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0068_toplu_ogrenci_islemleri"
down_revision = "0067_coklu_dil"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS yeni_tur_izni TIMESTAMPTZ;
CREATE TABLE IF NOT EXISTS toplu_islemler (
    id BIGSERIAL PRIMARY KEY,
    okul_id INTEGER REFERENCES okullar(id) ON DELETE CASCADE,
    tur VARCHAR(30) NOT NULL,
    yapan_id UUID,
    yapan_ad VARCHAR(200),
    zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    sayi INTEGER NOT NULL DEFAULT 0,
    veri JSONB NOT NULL DEFAULT '[]'::jsonb,
    geri_alindi_zamani TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_toplu_islemler_okul_tur ON toplu_islemler (okul_id, tur, zaman DESC)
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    op.execute("DROP TABLE IF EXISTS toplu_islemler")
    op.execute("ALTER TABLE ogrenciler DROP COLUMN IF EXISTS yeni_tur_izni")
