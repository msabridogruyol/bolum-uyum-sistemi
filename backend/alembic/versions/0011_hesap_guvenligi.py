"""KVKK onayları, 2 adımlı doğrulama kodları, şifre sıfırlama tokenleri, güvenilir cihazlar

Revision ID: 0011_hesap_guvenligi
Revises: 0010_haftalik_gorevler
Create Date: 2026-10-04
"""
from alembic import op

revision = "0011_hesap_guvenligi"
down_revision = "0010_haftalik_gorevler"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS kvkk_onaylari (
    id             BIGSERIAL PRIMARY KEY,
    kullanici_tipi VARCHAR NOT NULL,
    kullanici_id   UUID    NOT NULL,
    onay_kodu      VARCHAR NOT NULL,
    metin_surumu   VARCHAR NOT NULL,
    verildi        BOOLEAN NOT NULL,
    ip_adresi      VARCHAR,
    zaman          TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT ck_kvkk_tip CHECK (kullanici_tipi IN ('ogrenci','yonetim'))
);
CREATE INDEX IF NOT EXISTS ix_kvkk_kullanici ON kvkk_onaylari (kullanici_tipi, kullanici_id);

CREATE TABLE IF NOT EXISTS dogrulama_kodlari (
    id                 BIGSERIAL PRIMARY KEY,
    kullanici_tipi     VARCHAR NOT NULL,
    kullanici_id       UUID    NOT NULL,
    kod_ozeti          VARCHAR NOT NULL,
    son_kullanma       TIMESTAMPTZ NOT NULL,
    deneme_sayisi      INTEGER NOT NULL DEFAULT 0,
    kullanildi         BOOLEAN NOT NULL DEFAULT FALSE,
    olusturulma_zamani TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_dk_kullanici ON dogrulama_kodlari (kullanici_tipi, kullanici_id);

CREATE TABLE IF NOT EXISTS sifre_sifirlama_tokenleri (
    id                 BIGSERIAL PRIMARY KEY,
    kullanici_tipi     VARCHAR NOT NULL,
    kullanici_id       UUID    NOT NULL,
    token_ozeti        VARCHAR NOT NULL,
    amac               VARCHAR NOT NULL DEFAULT 'sifirlama',
    son_kullanma       TIMESTAMPTZ NOT NULL,
    kullanilma_zamani  TIMESTAMPTZ,
    olusturulma_zamani TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT ck_sst_amac CHECK (amac IN ('sifirlama','davet'))
);
CREATE INDEX IF NOT EXISTS ix_sst_ozet ON sifre_sifirlama_tokenleri (token_ozeti);

CREATE TABLE IF NOT EXISTS guvenilir_cihazlar (
    id                 BIGSERIAL PRIMARY KEY,
    kullanici_tipi     VARCHAR NOT NULL,
    kullanici_id       UUID    NOT NULL,
    cihaz_ozeti        VARCHAR NOT NULL,
    son_kullanma       TIMESTAMPTZ NOT NULL,
    olusturulma_zamani TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_gc_ozet ON guvenilir_cihazlar (cihaz_ozeti);

-- guvenlik_olaylari: KVKK kamera onayı vermeyen öğrenci için yeni olay tipi
DO $$
DECLARE k record;
BEGIN
  FOR k IN SELECT conname FROM pg_constraint
           WHERE conrelid = 'guvenlik_olaylari'::regclass AND contype = 'c'
             AND pg_get_constraintdef(oid) ILIKE '%olay_tipi%'
  LOOP
    EXECUTE format('ALTER TABLE guvenlik_olaylari DROP CONSTRAINT %I', k.conname);
  END LOOP;
END $$;
ALTER TABLE guvenlik_olaylari ADD CONSTRAINT ck_go_olay_tipi CHECK (olay_tipi IN (
    'tam_ekrandan_cikti','tam_ekrana_geri_donuldu','sekme_degisti','sekmeye_geri_donuldu',
    'pencere_odagi_kaybedildi','pencere_odagi_geri_kazanildi',
    'kamera_izni_reddedildi','kamera_desteklenmiyor','kamera_rizasi_verilmedi'));
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS guvenilir_cihazlar; DROP TABLE IF EXISTS sifre_sifirlama_tokenleri; "
               "DROP TABLE IF EXISTS dogrulama_kodlari; DROP TABLE IF EXISTS kvkk_onaylari;")
