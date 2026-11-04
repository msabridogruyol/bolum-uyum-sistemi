"""Gece bakımı, şifre değişikliği onayı, anahtar iptali ve öneri özeti

Revision ID: 0095_gece_bakimi_ve_hesap
Revises: 0094_gece_indeksleri
Create Date: 2026-11-04

[2026-11-04] Hafif (açılışta uygulanan) tablolar ve parametreler:
  * sifre_degisiklik_talepleri — eski şifre + e-posta kodu ile şifre değişikliği (kullanıcı kuralı).
  * iptal_edilen_tokenlar      — çıkışta / yenilemede iptal edilen oturum anahtarları (jti); süresi geçen satırlar gece silinir.
  * tur_oneri_ozeti            — turun ilk 10 bölüm önerisi (rehber paneli 20.000 öğrencide her sayfada yeniden hesaplıyordu).
      Öğrencinin skorları değişince tetikleyici o turun satırını siler (kod yolundan bağımsız).
  * gece_kuyrugu, gece_bakim_kaydi — sistemi yavaşlatan işler (pipeline canlıya alma, katman ağırlığı, skorların yeniden
      hesabı) gece bakımında (varsayılan 03:00, Europe/Istanbul) çalışır; her gecenin sonucu kaydedilir.
  * Parametreler: gece_bakim_saati, sayfa_ziyareti_saklama_gun, filiz_mesaj_saklama_gun.
İdempotent; app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0095_gece_bakimi_ve_hesap"
down_revision = "0094_gece_indeksleri"
branch_labels = None
depends_on = None

SQL = r"""
CREATE TABLE IF NOT EXISTS sifre_degisiklik_talepleri (
    id BIGSERIAL PRIMARY KEY,
    kullanici_tipi VARCHAR NOT NULL,
    kullanici_id UUID NOT NULL,
    yeni_sifre_hash VARCHAR NOT NULL,
    kod_ozeti VARCHAR NOT NULL,
    son_kullanma TIMESTAMPTZ NOT NULL,
    deneme_sayisi INTEGER NOT NULL DEFAULT 0,
    kullanildi BOOLEAN NOT NULL DEFAULT FALSE,
    olusturulma_zamani TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sdt_kullanici ON sifre_degisiklik_talepleri (kullanici_tipi, kullanici_id);
CREATE TABLE IF NOT EXISTS iptal_edilen_tokenlar (
    jti VARCHAR(64) PRIMARY KEY,
    son_kullanma TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS tur_oneri_ozeti (
    tur_id BIGINT PRIMARY KEY REFERENCES ogrenci_degerlendirme_turu(id) ON DELETE CASCADE,
    bolumler INTEGER[] NOT NULL,
    uyumlar NUMERIC[] NOT NULL,
    surum VARCHAR(32) NOT NULL,
    hesaplama_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE OR REPLACE FUNCTION tur_oneri_ozeti_sil_yeni() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN DELETE FROM tur_oneri_ozeti WHERE tur_id IN (SELECT DISTINCT tur_id FROM yeni_satirlar); RETURN NULL; END $f$;
CREATE OR REPLACE FUNCTION tur_oneri_ozeti_sil_eski() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN DELETE FROM tur_oneri_ozeti WHERE tur_id IN (SELECT DISTINCT tur_id FROM eski_satirlar); RETURN NULL; END $f$;
DROP TRIGGER IF EXISTS trg_obus_ozet_ekle ON ogrenci_bolum_uyum_skorlari;
CREATE TRIGGER trg_obus_ozet_ekle AFTER INSERT ON ogrenci_bolum_uyum_skorlari REFERENCING NEW TABLE AS yeni_satirlar FOR EACH STATEMENT EXECUTE FUNCTION tur_oneri_ozeti_sil_yeni();
DROP TRIGGER IF EXISTS trg_obus_ozet_guncelle ON ogrenci_bolum_uyum_skorlari;
CREATE TRIGGER trg_obus_ozet_guncelle AFTER UPDATE ON ogrenci_bolum_uyum_skorlari REFERENCING NEW TABLE AS yeni_satirlar FOR EACH STATEMENT EXECUTE FUNCTION tur_oneri_ozeti_sil_yeni();
DROP TRIGGER IF EXISTS trg_obus_ozet_sil ON ogrenci_bolum_uyum_skorlari;
CREATE TRIGGER trg_obus_ozet_sil AFTER DELETE ON ogrenci_bolum_uyum_skorlari REFERENCING OLD TABLE AS eski_satirlar FOR EACH STATEMENT EXECUTE FUNCTION tur_oneri_ozeti_sil_eski();
DROP TRIGGER IF EXISTS trg_odus_ozet_ekle ON ogrenci_dal_uyum_skorlari;
CREATE TRIGGER trg_odus_ozet_ekle AFTER INSERT ON ogrenci_dal_uyum_skorlari REFERENCING NEW TABLE AS yeni_satirlar FOR EACH STATEMENT EXECUTE FUNCTION tur_oneri_ozeti_sil_yeni();
DROP TRIGGER IF EXISTS trg_odus_ozet_guncelle ON ogrenci_dal_uyum_skorlari;
CREATE TRIGGER trg_odus_ozet_guncelle AFTER UPDATE ON ogrenci_dal_uyum_skorlari REFERENCING NEW TABLE AS yeni_satirlar FOR EACH STATEMENT EXECUTE FUNCTION tur_oneri_ozeti_sil_yeni();
DROP TRIGGER IF EXISTS trg_odus_ozet_sil ON ogrenci_dal_uyum_skorlari;
CREATE TRIGGER trg_odus_ozet_sil AFTER DELETE ON ogrenci_dal_uyum_skorlari REFERENCING OLD TABLE AS eski_satirlar FOR EACH STATEMENT EXECUTE FUNCTION tur_oneri_ozeti_sil_eski();
CREATE TABLE IF NOT EXISTS gece_kuyrugu (
    id BIGSERIAL PRIMARY KEY,
    tur VARCHAR(40) NOT NULL,
    veri JSONB NOT NULL DEFAULT '{}'::jsonb,
    isteyen_id UUID,
    isteyen_ad VARCHAR(200),
    aciklama VARCHAR(400),
    istenme_zamani TIMESTAMPTZ NOT NULL DEFAULT now(),
    durum VARCHAR(16) NOT NULL DEFAULT 'bekliyor',
    sonuc VARCHAR(2000),
    calisma_zamani TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_gece_kuyrugu_durum ON gece_kuyrugu (durum, id);
CREATE TABLE IF NOT EXISTS gece_bakim_kaydi (
    id BIGSERIAL PRIMARY KEY,
    gun DATE NOT NULL,
    baslama TIMESTAMPTZ NOT NULL DEFAULT now(),
    bitis TIMESTAMPTZ,
    durum VARCHAR(16) NOT NULL DEFAULT 'calisiyor',
    ayrinti JSONB NOT NULL DEFAULT '[]'::jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_gece_bakim_gun ON gece_bakim_kaydi (gun);
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'gece_bakim_saati', '03:00', 'Gece bakımının başladığı saat (Türkiye saati, SS:DD). Sistemi yavaşlatan göçler, pipeline canlıya alma, katman ağırlığı değişikliği ve skorların yeniden hesabı bu saatte yapılır.', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'gece_bakim_saati');
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'sayfa_ziyareti_saklama_gun', '180', 'Anonim sayfa ziyareti kayıtları kaç gün saklanır (gece bakımında silinir). 0 = silinmez.', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'sayfa_ziyareti_saklama_gun');
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'filiz_mesaj_saklama_gun', '730', 'Filiz sohbet mesajları kaç gün saklanır (KVKK saklama süresi; gece bakımında silinir). 0 = silinmez.', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'filiz_mesaj_saklama_gun')
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
