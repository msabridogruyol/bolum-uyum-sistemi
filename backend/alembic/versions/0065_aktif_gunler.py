"""Günlük aktiflik kaydı: öğrencinin sistemi açtığı her gün bir satır

Revision ID: 0065_aktif_gunler
Revises: 0064_cevrimici
Create Date: 2026-10-11

[2026-10-11] Öğrenci gün içinde sistemi ilk açtığında (giriş ya da "beni hatırla" ile açık kalan oturumda ilk sayfa sinyali)
o gün işaretlenir (gün: Türkiye saatiyle). Okul yetkilisi "son 30 günde kaç gün aktif" ve son aktif günü görür.
Geçmiş için mevcut giriş olaylarından (ogrenci_hesap_olaylari 'giris') ve son giriş zamanından geriye dönük doldurulur.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0065_aktif_gunler"
down_revision = "0064_cevrimici"
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS ogrenci_aktif_gunler (
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    gun DATE NOT NULL,
    ilk_zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (ogrenci_id, gun)
);
CREATE INDEX IF NOT EXISTS ix_aktif_gun_gun ON ogrenci_aktif_gunler (gun);
INSERT INTO ogrenci_aktif_gunler (ogrenci_id, gun, ilk_zaman)
SELECT ogrenci_id, (zaman AT TIME ZONE 'Europe/Istanbul')::date, min(zaman)
  FROM ogrenci_hesap_olaylari WHERE olay = 'giris' GROUP BY 1, 2
ON CONFLICT DO NOTHING;
INSERT INTO ogrenci_aktif_gunler (ogrenci_id, gun, ilk_zaman)
SELECT id, (son_giris_zamani AT TIME ZONE 'Europe/Istanbul')::date, son_giris_zamani
  FROM ogrenciler WHERE son_giris_zamani IS NOT NULL
ON CONFLICT DO NOTHING
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ogrenci_aktif_gunler")
