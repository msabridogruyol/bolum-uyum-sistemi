"""Değerlendirme tamamlanınca sonuç e-postası (+ PDF sonuç raporu)

Revision ID: 0069_sonuc_epostasi
Revises: 0068_toplu_ogrenci_islemleri
Create Date: 2026-10-12

[2026-10-12]
* ogrenci_degerlendirme_turu.sonuc_epostasi_zamani / sonuc_epostasi_durum — bir tamamlanma için e-posta bir kez gider;
  durum: gonderiliyor | gonderildi | hata.
* sistem_parametreleri.sonuc_epostasi_acik = '1' (otomatik gönderimi kapatmak için '0').
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0069_sonuc_epostasi"
down_revision = "0068_toplu_ogrenci_islemleri"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenci_degerlendirme_turu ADD COLUMN IF NOT EXISTS sonuc_epostasi_zamani TIMESTAMPTZ;
ALTER TABLE ogrenci_degerlendirme_turu ADD COLUMN IF NOT EXISTS sonuc_epostasi_durum VARCHAR(20);
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'sonuc_epostasi_acik', '1', 'Değerlendirme tamamlanınca öğrenciye sonuç e-postası (paketinde öğrenci raporları varsa PDF ekli) gönderilsin mi? 1 = evet, 0 = hayır', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'sonuc_epostasi_acik')
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    op.execute("ALTER TABLE ogrenci_degerlendirme_turu DROP COLUMN IF EXISTS sonuc_epostasi_durum")
    op.execute("ALTER TABLE ogrenci_degerlendirme_turu DROP COLUMN IF EXISTS sonuc_epostasi_zamani")
    op.execute("DELETE FROM sistem_parametreleri WHERE anahtar = 'sonuc_epostasi_acik'")
