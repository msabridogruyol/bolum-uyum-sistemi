"""Pilot hazırlığı: oturum geçersiz kılma, laboratuvar giriş sınırı, sözlük hata bildirimleri

Revision ID: 0066_pilot_hazirlik
Revises: 0065_aktif_gunler
Create Date: 2026-10-11

[2026-10-11]
* ogrenciler / admin_kullanicilar.oturum_gecersiz_zamani — şifre sıfırlanınca / değiştirilince bu zamandan önce verilmiş
  oturum anahtarları reddedilir (app.core.security.token_hesaba_uygun_mu).
* Giriş uçlarının IP sınırı 20/dk → 120/dk, 150/sa → 2000/sa (bir laboratuvar aynı anda girebilsin). Yalnızca eski
  varsayılan değerde kalmışsa güncellenir; yönetimin elle değiştirdiği değere dokunulmaz.
* ix_ods_tur_degisken — okul istatistiklerinde tur bazlı özellik ortalamaları (3.000 öğrencili okulda 3,3 sn → 0,15 sn).
* sozluk_bildirimleri — öğrencinin "Bu tanımda hata var" bildirimi (süper admin Kontrol Paneli'nde görür).
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0066_pilot_hazirlik"
down_revision = "0065_aktif_gunler"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS oturum_gecersiz_zamani TIMESTAMPTZ;
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS oturum_gecersiz_zamani TIMESTAMPTZ;
UPDATE sistem_parametreleri SET deger = '120', aciklama = 'Giriş, 2 adımlı kod, şifre sıfırlama, kayıt, test girişi: IP başına dakikada en çok istek (laboratuvar: aynı IP''den bir sınıf)', guncelleme_zamani = now() WHERE anahtar = 'hiz_siniri_kimlik_dakika' AND deger = '20';
UPDATE sistem_parametreleri SET deger = '2000', guncelleme_zamani = now() WHERE anahtar = 'hiz_siniri_kimlik_saat' AND deger = '150';
CREATE TABLE IF NOT EXISTS sozluk_bildirimleri (
    id BIGSERIAL PRIMARY KEY,
    terim VARCHAR(200) NOT NULL,
    terim_k VARCHAR(40),
    aciklama VARCHAR(500),
    ogrenci_id UUID REFERENCES ogrenciler(id) ON DELETE SET NULL,
    okul_id INTEGER,
    durum VARCHAR(20) NOT NULL DEFAULT 'yeni',
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sozluk_bildirim_durum ON sozluk_bildirimleri (durum, olusturulma_zamani DESC);
CREATE INDEX IF NOT EXISTS ix_ods_tur_degisken ON ogrenci_degisken_skorlari (tur_id, degisken_id) INCLUDE (puan, ogrenci_id)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS sozluk_bildirimleri; "
               "ALTER TABLE ogrenciler DROP COLUMN IF EXISTS oturum_gecersiz_zamani; "
               "ALTER TABLE admin_kullanicilar DROP COLUMN IF EXISTS oturum_gecersiz_zamani")
