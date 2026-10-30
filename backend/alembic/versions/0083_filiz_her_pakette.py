"""Filiz her pakette; yapay zekâ her pakette, günlük mesaj sınırı pakete göre

Revision ID: 0083_filiz_her_pakette
Revises: 0082_bolum_kaldirma
Create Date: 2026-10-30

[2026-10-30] Karar (B seçeneği): Filiz koçluğun sesi olduğu için her pakette zorunlu (rehber modu); yapay zekâ modu
(filiz_ai) her pakete eklenir, fark günlük mesaj sınırıyla korunur. Kod tarafı: app/core/paketler.py (filiz zorunlu),
app/api/ai_koc.py (pakete göre sınır, okul aylık üst sınırı, sınır dolunca rehber moduna geçiş).
* Her paketin modül listesine 'filiz' ve 'filiz_ai' eklenir (yoksa).
* Okullara özel "çıkarılan modüller"den 'filiz' silinir (zorunlu). Bir okul 'filiz_ai'yi bilerek çıkardıysa dokunulmaz.
* ogrenci_koclugu_mesajlari.yapay_zeka: cevabın yapay zekâdan gelip gelmediği (sınırlar yalnızca bunları sayar).
* Sistem parametreleri (süper admin değiştirebilir; yalnızca yoksa eklenir): günlük sınır Temel 5 / Gelişim 20 /
  Tam ve okulsuz 40; okul aylık üst sınırı = öğrenci sayısı × (Temel 30 / Gelişim 60 / Tam 120) (0 = sınırsız).
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0083_filiz_her_pakette"
down_revision = "0082_bolum_kaldirma"
branch_labels = None
depends_on = None

SQL = """
UPDATE paketler SET moduller = coalesce(moduller, '[]'::jsonb) || '["filiz"]'::jsonb
 WHERE NOT coalesce(moduller, '[]'::jsonb) ? 'filiz';
UPDATE paketler SET moduller = coalesce(moduller, '[]'::jsonb) || '["filiz_ai"]'::jsonb
 WHERE NOT coalesce(moduller, '[]'::jsonb) ? 'filiz_ai';
UPDATE okullar SET modul_cikar = modul_cikar - 'filiz' WHERE modul_cikar ? 'filiz';
UPDATE okullar SET modul_ekle = modul_ekle - 'filiz' WHERE modul_ekle ? 'filiz';
ALTER TABLE ogrenci_koclugu_mesajlari ADD COLUMN IF NOT EXISTS yapay_zeka BOOLEAN NOT NULL DEFAULT FALSE;
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'filiz_gunluk_mesaj_limiti_temel', '5', 'Filiz yapay zekâ: Temel paketteki öğrenci için günlük mesaj sınırı (dolunca Filiz rehber modunda cevaplar)', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'filiz_gunluk_mesaj_limiti_temel');
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'filiz_gunluk_mesaj_limiti_gelisim', '20', 'Filiz yapay zekâ: Gelişim paketteki öğrenci için günlük mesaj sınırı (dolunca Filiz rehber modunda cevaplar)', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'filiz_gunluk_mesaj_limiti_gelisim');
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'filiz_gunluk_mesaj_limiti', '40', 'Filiz yapay zekâ: Tam paketteki ve okula bağlı olmayan öğrenci için günlük mesaj sınırı (dolunca Filiz rehber modunda cevaplar)', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'filiz_gunluk_mesaj_limiti');
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'filiz_okul_aylik_ogrenci_basi_temel', '30', 'Filiz yapay zekâ, Temel paket: okulun aylık üst sınırı = okuldaki öğrenci sayısı × bu değer (0 = sınırsız); dolunca ay sonuna kadar rehber modu', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'filiz_okul_aylik_ogrenci_basi_temel');
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'filiz_okul_aylik_ogrenci_basi_gelisim', '60', 'Filiz yapay zekâ, Gelişim paket: okulun aylık üst sınırı = okuldaki öğrenci sayısı × bu değer (0 = sınırsız); dolunca ay sonuna kadar rehber modu', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'filiz_okul_aylik_ogrenci_basi_gelisim');
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'filiz_okul_aylik_ogrenci_basi', '120', 'Filiz yapay zekâ, Tam (ve diğer) paket: okulun aylık üst sınırı = okuldaki öğrenci sayısı × bu değer (0 = sınırsız); dolunca ay sonuna kadar rehber modu', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'filiz_okul_aylik_ogrenci_basi');
UPDATE paketler SET aciklama = 'Değerlendirme, bölüm önerileri, profil, hedef bölüm ve koçluk, Filiz asistanı, okul paneli ve temel raporlar'
 WHERE kod = 'temel' AND aciklama = 'Değerlendirme, bölüm önerileri, profil, hedef bölüm ve koçluk, okul paneli ve temel raporlar';
UPDATE paketler SET aciklama = 'Temel + kütüphane, kulüpler, rehberlik ve diğer gelişim modülleri'
 WHERE kod = 'gelisim' AND aciklama = 'Temel + kütüphane, kulüpler, Filiz ve diğer gelişim modülleri'
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    pass
