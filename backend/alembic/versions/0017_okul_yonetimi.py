"""Okul bazlı yönetim: 3 rol (süper admin / okul yetkilisi / öğrenci), öğrenci↔okul bağı,
geçici şifre, hesap olay kaydı, öğrenci silmede bağlı verilerin de silinmesi.

Revision ID: 0017_okul_yonetimi
Revises: 0016_okullar
Create Date: 2026-10-09
"""
from alembic import op

revision = "0017_okul_yonetimi"
down_revision = "0016_okullar"
branch_labels = None
depends_on = None

SQL = r"""
-- ============ 1) Okullar: her okulun amblemi kendi öğrencilerine gösterilir ============
DROP INDEX IF EXISTS okullar_tek_aktif;
COMMENT ON COLUMN okullar.aktif_mi IS 'Amblem/ad bu okulun öğrencilerinin sol menüsünde gösterilsin mi';

-- ============ 2) Öğrenci ↔ okul, geçici şifre, son giriş ============
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS okul_id INTEGER REFERENCES okullar(id) ON DELETE SET NULL;
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS sube TEXT;
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS sifre_degistirmeli BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS son_giris_zamani TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ogrenciler_okul_id_idx ON ogrenciler (okul_id);
-- yazdığı okul adı kayıtlı bir okulla aynı olanlar o okula; elle lise adı yazmış diğerleri ilk okula bağlanır
UPDATE ogrenciler o SET okul_id = k.id, okul = k.ad FROM okullar k
 WHERE o.okul_id IS NULL AND lower(trim(o.okul)) = lower(trim(k.ad));
UPDATE ogrenciler o SET okul_id = k.id, okul = k.ad
  FROM (SELECT id, ad FROM okullar ORDER BY aktif_mi DESC, id LIMIT 1) k
 WHERE o.okul_id IS NULL AND coalesce(trim(o.okul), '') <> '';

-- ============ 3) Yönetim rolleri: super_admin | okul_yetkilisi ============
-- rol kısıtı farklı adla kurulmuş olabilir: 'rol' geçen tüm CHECK kısıtları kaldırılıp yeniden kurulur
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT conname FROM pg_constraint
            WHERE conrelid = 'admin_kullanicilar'::regclass AND contype = 'c' AND pg_get_constraintdef(oid) ILIKE '%rol%'
  LOOP
    EXECUTE format('ALTER TABLE admin_kullanicilar DROP CONSTRAINT %I', r.conname);
  END LOOP;
END $$;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS okul_id INTEGER REFERENCES okullar(id) ON DELETE CASCADE;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS aktif_mi BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS sifre_degistirmeli BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS son_giris_zamani TIMESTAMPTZ;
UPDATE admin_kullanicilar SET rol = 'super_admin' WHERE rol = 'icerik_editoru';
UPDATE admin_kullanicilar SET rol = 'okul_yetkilisi' WHERE rol = 'rehber';
UPDATE admin_kullanicilar SET okul_id = (SELECT id FROM okullar ORDER BY aktif_mi DESC, id LIMIT 1)
 WHERE rol = 'okul_yetkilisi' AND okul_id IS NULL;
ALTER TABLE admin_kullanicilar ADD CONSTRAINT ck_admin_rol CHECK (rol IN ('super_admin','okul_yetkilisi'));
ALTER TABLE admin_kullanicilar ADD CONSTRAINT ck_admin_okul CHECK (rol <> 'okul_yetkilisi' OR okul_id IS NOT NULL);

-- yönetici silinince kayıtları (audit_log vb.) kalsın: bağlar ON DELETE SET NULL olur
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    SELECT c.conname, c.conrelid::regclass AS tablo, a.attname AS kolon, pg_get_constraintdef(c.oid) AS tanim
      FROM pg_constraint c
      JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = c.conkey[1]
     WHERE c.contype = 'f' AND c.confrelid = 'admin_kullanicilar'::regclass
       AND c.conrelid <> 'admin_kullanicilar'::regclass AND c.confdeltype IN ('a','r')
  LOOP
    EXECUTE format('ALTER TABLE %s ALTER COLUMN %I DROP NOT NULL', r.tablo, r.kolon);
    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.tablo, r.conname);
    EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I %s ON DELETE SET NULL', r.tablo, r.conname, regexp_replace(r.tanim, ' ON DELETE (RESTRICT|NO ACTION)', ''));
  END LOOP;
END $$;

-- denetim kaydı: hangi okul, kim yaptı (yönetici silinse de adı kalır)
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS okul_id INTEGER;
ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS yapan_ad TEXT;
CREATE INDEX IF NOT EXISTS audit_log_okul_idx ON audit_log (okul_id, zaman DESC);

-- ============ 4) Öğrenci silinince ona bağlı tüm veriler de silinsin (ON DELETE CASCADE) ============
DO $$
DECLARE r record;
BEGIN
  FOR r IN
    WITH RECURSIVE agac(tablo) AS (
      SELECT 'ogrenciler'::regclass
      UNION
      SELECT c.conrelid::regclass FROM pg_constraint c JOIN agac a ON c.confrelid = a.tablo
       WHERE c.contype = 'f' AND c.conrelid <> c.confrelid
    )
    SELECT DISTINCT c.conname, c.conrelid::regclass AS tablo, pg_get_constraintdef(c.oid) AS tanim
      FROM pg_constraint c JOIN agac a ON c.confrelid = a.tablo
     WHERE c.contype = 'f' AND c.confdeltype IN ('a','r') AND c.conrelid <> c.confrelid
  LOOP
    EXECUTE format('ALTER TABLE %s DROP CONSTRAINT %I', r.tablo, r.conname);
    EXECUTE format('ALTER TABLE %s ADD CONSTRAINT %I %s ON DELETE CASCADE', r.tablo, r.conname, regexp_replace(r.tanim, ' ON DELETE (RESTRICT|NO ACTION)', ''));
  END LOOP;
END $$;

-- ============ 5) Öğrenci hesap olayları (giriş, şifre sıfırlama, hesap açma ...) ============
CREATE TABLE IF NOT EXISTS ogrenci_hesap_olaylari (
    id          BIGSERIAL PRIMARY KEY,
    ogrenci_id  UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    olay        TEXT NOT NULL,
    aciklama    TEXT,
    yapan       TEXT,
    ip          TEXT,
    zaman       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS oho_ogrenci_zaman_idx ON ogrenci_hesap_olaylari (ogrenci_id, zaman DESC);
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    raise NotImplementedError("Geri alma desteklenmiyor — yedekten dönün.")
