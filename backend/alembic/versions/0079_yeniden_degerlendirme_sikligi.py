"""Yeniden değerlendirme sıklığı sınıfa göre: 12. sınıf ve mezun 70 günde bir, diğer sınıflar yılda 2 kez

Revision ID: 0079_yeniden_degerlendirme_sikligi
Revises: 0078_bolum_icerik_duzeltme
Create Date: 2026-10-19

[2026-10-19]
* sistem_parametreleri.yeniden_degerlendirme_gun_12 = 70 — 12. sınıf ve mezun: geçerli turdan sonra en erken kaç gün.
* sistem_parametreleri.yeniden_degerlendirme_yillik_hak = 2 — diğer sınıflar: yılda kaç değerlendirme (bekleme = 365 / hak gün).
* Tek değerli eski yeniden_degerlendirme_min_gun bu ikisiyle değiştirildi; kod artık okumadığı için kaldırılır.
Yalnızca yoksa eklenir; süper adminin sonradan girdiği değerler ezilmez.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0079_yeniden_degerlendirme_sikligi"
down_revision = "0078_bolum_icerik_duzeltme"
branch_labels = None
depends_on = None

SQL = """
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'yeniden_degerlendirme_gun_12', '70', '12. sınıf ve mezun öğrenciler: geçerli bir değerlendirmeden sonra yeniden değerlendirmeye kaç gün sonra girebilir', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'yeniden_degerlendirme_gun_12');
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'yeniden_degerlendirme_yillik_hak', '2', 'Diğer sınıflar: yılda kaç değerlendirme yapılabilir (iki değerlendirme arası 365 / bu sayı gün)', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'yeniden_degerlendirme_yillik_hak');
DELETE FROM sistem_parametreleri WHERE anahtar = 'yeniden_degerlendirme_min_gun'
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    pass
