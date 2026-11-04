"""Denetim: eksik soru geçerlilik tablosu ve yük altında gereken indeksler

Revision ID: 0093_denetim_guvenlik_performans
Revises: 0092_guncel_adlar
Create Date: 2026-11-04

[2026-11-04] Ekran ve yük denetimi:
  1) soru_gecerlilik_sonuclari hiçbir göçte oluşturulmamıştı; Süper yönetici → Soru Geçerliliği ekranı ve
     /admin/gecerlilik-girdisi-v2/analiz 500 veriyordu (tablo yok). Sütunlar admin.py yükleme ve okuma sorgularıyla aynı.
  2) (Taşındı: indeksler göç 0094'te, gece bakımında CONCURRENTLY kurulur.) Büyük okulda (3.000 öğrenci, ~100 bin öğrenci sistem geneli) sıralı tarama yapan sorgular için indeksler:
     - lower(email): her giriş, şifre sıfırlama ve toplu öğrenci yüklemesinde satır başına 2–3 kez aranıyor.
     - tur_id / ogrenci_id yabancı anahtarları: tur ya da öğrenci silinince (değerlendirme sıfırlama, toplu silme) ilişkili
       tablolarda CASCADE tam tarama yapıyordu (ogrenci_cevaplar on milyonlarca satıra çıkar).
     - sorular(katman_id) WHERE ogrenci_id IS NULL: her katman başlangıcında ortak soru bankası okunur; öğrenciye özel
       K5 soruları biriktikçe tablo büyür.
     - guvenlik_fotograflari(cekim_zamani): saklama süresi temizliği.
  3) ogrenciler.sinif tek biçim: sistem "9. Sınıf"…"12. Sınıf", "Mezun", "Aday" yazar (okul_yonetimi.sinif_ayir) ve tercih,
     istatistik, hazır raporlar bu değerlerle süzer; elle ya da eski betiklerle yazılmış "12" / "mezun" / "12-A" biçimindeki
     öğrenciler Tercih ekranında hiç görünmüyordu (12. sınıf + mezun: 0). Yalnızca tanınan biçimler dönüştürülür.
İdempotent (IF NOT EXISTS): app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0093_denetim_guvenlik_performans"
down_revision = "0092_guncel_adlar"
branch_labels = None
depends_on = None

SQL = r"""
CREATE TABLE IF NOT EXISTS soru_gecerlilik_sonuclari (
    id SERIAL PRIMARY KEY,
    soru_id INTEGER NOT NULL REFERENCES sorular(id) ON DELETE CASCADE,
    secenek_id INTEGER REFERENCES soru_secenekleri(id) ON DELETE CASCADE,
    gercek_degisken_kod VARCHAR(50) NOT NULL,
    model_a_tahmin VARCHAR(50), model_a_dogru BOOLEAN NOT NULL DEFAULT FALSE, model_a_benzerlik NUMERIC(6,4) NOT NULL DEFAULT 0,
    model_b_tahmin VARCHAR(50), model_b_dogru BOOLEAN NOT NULL DEFAULT FALSE, model_b_benzerlik NUMERIC(6,4) NOT NULL DEFAULT 0,
    model_c_tahmin VARCHAR(50), model_c_dogru BOOLEAN NOT NULL DEFAULT FALSE, model_c_benzerlik NUMERIC(6,4) NOT NULL DEFAULT 0,
    test_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sgs_soru_secenek ON soru_gecerlilik_sonuclari (soru_id, secenek_id, test_zamani DESC);
UPDATE ogrenciler SET sinif = 'Mezun' WHERE lower(btrim(sinif)) LIKE 'mezun%' AND sinif <> 'Mezun';
UPDATE ogrenciler SET sinif = 'Aday' WHERE lower(btrim(sinif)) = 'aday' AND sinif <> 'Aday';
UPDATE ogrenciler SET sube = upper(regexp_replace(btrim(sinif), '^(9|10|11|12)\s*[-/ ]\s*([A-Za-z])$', '\2'))
 WHERE btrim(sinif) ~ '^(9|10|11|12)\s*[-/ ]\s*[A-Za-z]$' AND COALESCE(sube, '') = '';
UPDATE ogrenciler SET sinif = substring(btrim(sinif) FROM '^(9|10|11|12)') || '. Sınıf'
 WHERE btrim(sinif) ~ '^(9|10|11|12)(\s*[-/ ]\s*[A-Za-z])?$'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
