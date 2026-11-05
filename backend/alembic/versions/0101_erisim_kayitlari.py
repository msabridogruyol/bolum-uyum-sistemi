"""Erişim kayıtları (kim, ne zaman, kimin verisine, hangi bölümde)

Revision ID: 0101_erisim_kayitlari
Revises: 0100_veli_onaylari
Create Date: 2026-11-05

[2026-11-05] Kullanıcı isteği: "kim ne zaman girmiş, kime girmiş, neyine girmiş" — öğrenci, okul yetkilisi ve süper
admin dahil herkes için; yalnızca süper admin görür. Girişler (başarılı / hatalı / engellenen / iki adım hatası) ve
oturum açık kullanıcının her isteği (görüntüleme, indirme, işlem) yazılır. Hedef öğrenci yol parametresinden çözülür.
Kişi ve hedef adları yazım anında kopyalanır (kişi silinse de kayıt okunur kalır); kayıtlar yalnızca eklenir, saklama
süresi dolanlar gece bakımında silinir (parametre erisim_kaydi_saklama_gun).
İdempotent; app/core/sema_guncelleme.py OTOMATIK listesinde (yeni ve boş tablo: indeksler açılışta hafif).
"""
from alembic import op

revision = "0101_erisim_kayitlari"
down_revision = "0100_veli_onaylari"
branch_labels = None
depends_on = None

SQL = r"""
CREATE TABLE IF NOT EXISTS erisim_kayitlari (
    id BIGSERIAL PRIMARY KEY,
    zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    kullanici_tipi VARCHAR(20) NOT NULL,
    kullanici_id UUID,
    kullanici_ad VARCHAR(200),
    kullanici_eposta VARCHAR(254),
    okul_id INTEGER,
    olay VARCHAR(30) NOT NULL,
    bolum VARCHAR(120),
    yontem VARCHAR(10),
    yol VARCHAR(255),
    hedef_ogrenci_id UUID,
    hedef_ad VARCHAR(200),
    hedef_okul_id INTEGER,
    durum_kodu SMALLINT,
    ip VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS ix_erisim_zaman ON erisim_kayitlari (zaman DESC);
CREATE INDEX IF NOT EXISTS ix_erisim_kullanici ON erisim_kayitlari (kullanici_id, zaman DESC);
CREATE INDEX IF NOT EXISTS ix_erisim_hedef ON erisim_kayitlari (hedef_ogrenci_id, zaman DESC) WHERE hedef_ogrenci_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_erisim_okul ON erisim_kayitlari (okul_id, zaman DESC);
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'erisim_kaydi_saklama_gun', '365', 'Erişim kayıtlarının (kim, ne zaman, kimin verisine girdi) saklama süresi, gün. 0 = silinmez.', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'erisim_kaydi_saklama_gun')
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
