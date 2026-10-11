"""İş Hayatı: CV Atölyesi (is_hayati_cv) ve okulun gerçek mezun hikâyeleri (mezun_hikayeleri)

Revision ID: 0057_is_hayati_cv_mezun
Revises: 0056_is_hayati_pratik
Create Date: 2026-10-10

Not: app/core/sema_guncelleme.py bu SQL'i HER sunucu açılışında yeniden çalıştırır; tüm komutlar idempotenttir.
- is_hayati_cv: öğrencinin CV içeriği (jsonb). Yalnızca öğrenci görür; paylas = TRUE ise okul yetkilisi öğrenci
  detayında okuyabilir (öğrencinin açık seçimi).
- mezun_hikayeleri: yalnızca okul yetkilisinin eklediği, mezunun açık rızası alınmış gerçek anlatılar.
  riza_alindi = TRUE zorunlu (CHECK) ve rıza tarihi tutulur.
"""
from alembic import op

revision = "0057_is_hayati_cv_mezun"
down_revision = "0056_is_hayati_pratik"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS is_hayati_cv (
    ogrenci_id UUID PRIMARY KEY REFERENCES ogrenciler(id) ON DELETE CASCADE,
    icerik JSONB NOT NULL DEFAULT '{}',
    paylas BOOLEAN NOT NULL DEFAULT FALSE,
    paylasim_zamani TIMESTAMPTZ,
    guncelleme TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS mezun_hikayeleri (
    id SERIAL PRIMARY KEY,
    okul_id INTEGER NOT NULL REFERENCES okullar(id) ON DELETE CASCADE,
    mezun_ad VARCHAR NOT NULL,
    ad_bicimi VARCHAR NOT NULL DEFAULT 'bas_harf' CHECK (ad_bicimi IN ('tam', 'bas_harf')),
    mezuniyet_yili INTEGER NOT NULL,
    bolum_id INTEGER REFERENCES bolumler(id) ON DELETE SET NULL,
    bolum_ad VARCHAR,
    universite VARCHAR,
    su_anki_is VARCHAR,
    cevaplar JSONB NOT NULL DEFAULT '{}',
    riza_alindi BOOLEAN NOT NULL CHECK (riza_alindi),
    riza_tarihi DATE NOT NULL,
    riza_kaydeden VARCHAR,
    riza_kayit_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    durum VARCHAR NOT NULL DEFAULT 'taslak' CHECK (durum IN ('taslak', 'yayinda')),
    olusturan VARCHAR,
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now(),
    guncelleme TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_mezun_hikayeleri_okul ON mezun_hikayeleri (okul_id, durum)
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    op.execute("DROP TABLE IF EXISTS mezun_hikayeleri")
    op.execute("DROP TABLE IF EXISTS is_hayati_cv")
