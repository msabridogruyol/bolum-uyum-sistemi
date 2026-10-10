"""İş Hayatı — Zor Günler seçimleri, Okulda Öğretilmeyenler ilerlemesi, Mülakat Pratiği geçmişi

Revision ID: 0056_is_hayati_pratik
Revises: 0055_is_hayati_beklenti
Create Date: 2026-10-10

Not: app/core/sema_guncelleme.py bu SQL'i her açılışta yeniden çalıştırır; tüm komutlar idempotenttir.
- is_hayati_zor_gun: öğrencinin bir "zor günler" turunda yaptığı seçimler ve öne çıkan yaklaşımları.
- is_hayati_ders_ilerleme: tamamlanan dersler ve mini sınav puanı (öğrenci + ders başına tek satır, en iyi puan saklanır).
- is_hayati_mulakat: mülakat pratiği geçmişi. Cevap metni yalnızca öğrencinin kendi uçlarından okunur; okul/yönetim ucu yoktur. Öğrenci
  sildiğinde metinler boşaltılır; yalnızca Filiz kullanımı günlük hak sayımı için (silindi = true) satır olarak kalır.
"""
from alembic import op

revision = "0056_is_hayati_pratik"
down_revision = "0055_is_hayati_beklenti"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS is_hayati_zor_gun (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    bolum_id INTEGER REFERENCES bolumler(id) ON DELETE SET NULL,
    alan_kod VARCHAR,
    meslek_ad VARCHAR,
    secimler JSONB NOT NULL DEFAULT '{}',
    yaklasimlar JSONB NOT NULL DEFAULT '[]',
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ih_zor_gun_ogrenci ON is_hayati_zor_gun (ogrenci_id, olusturulma_zamani DESC);
CREATE TABLE IF NOT EXISTS is_hayati_ders_ilerleme (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    ders_kod VARCHAR NOT NULL,
    sinav_puani INTEGER,
    sinav_toplam INTEGER,
    deneme INTEGER NOT NULL DEFAULT 0,
    tamamlanma_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ogrenci_id, ders_kod)
);
CREATE TABLE IF NOT EXISTS is_hayati_mulakat (
    id SERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    soru_id VARCHAR NOT NULL,
    soru_metni VARCHAR NOT NULL,
    cevap TEXT NOT NULL,
    kontrol JSONB NOT NULL DEFAULT '[]',
    sure_sn INTEGER,
    ai_geri_bildirim TEXT,
    ai_zamani TIMESTAMPTZ,
    silindi BOOLEAN NOT NULL DEFAULT false,
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ih_mulakat_ogrenci ON is_hayati_mulakat (ogrenci_id, olusturulma_zamani DESC);
CREATE INDEX IF NOT EXISTS ix_ih_mulakat_ai ON is_hayati_mulakat (ogrenci_id, ai_zamani) WHERE ai_zamani IS NOT NULL
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS is_hayati_mulakat; DROP TABLE IF EXISTS is_hayati_ders_ilerleme; DROP TABLE IF EXISTS is_hayati_zor_gun")
