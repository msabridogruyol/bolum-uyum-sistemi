"""Kullanım süreleri (hangi menüde ne kadar süre)

Revision ID: 0102_kullanim_sureleri
Revises: 0101_erisim_kayitlari
Create Date: 2026-11-11

[2026-11-11] Kullanıcı isteği: "kullanıcıların hangi menüde ne kadar süre geçirdiğinin analizleri; öğrenciler ayrı,
yetkililer ayrı, her okul ayrı, toplam". Tarayıcı, sekme açık ve kişi etkinken (son 2 dakikada dokunma / tıklama /
yazma / kaydırma) geçen süreyi menü ve alt sekme bazında sayar, dakikada bir gönderir. Sunucu satırı
(oturum, menü, alt sekme, saat dilimi) başına toplar: tablo kişi başı ziyaret sayısıyla değil saat × menü ile büyür.

Kişi bağı yabancı anahtarla (ON DELETE CASCADE): öğrenci ya da yetkili silinince süre kayıtları da silinir (KVKK).
Saklama süresi parametre `kullanim_suresi_saklama_gun` (gece bakımında silinir).
İdempotent; app/core/sema_guncelleme.py OTOMATIK listesinde (yeni ve boş tablo: indeksler açılışta hafif).
"""
from alembic import op

revision = "0102_kullanim_sureleri"
down_revision = "0101_erisim_kayitlari"
branch_labels = None
depends_on = None

SQL = r"""
CREATE TABLE IF NOT EXISTS kullanim_sureleri (
    id BIGSERIAL PRIMARY KEY,
    saat TIMESTAMPTZ NOT NULL,
    kullanici_tipi VARCHAR(20) NOT NULL,
    ogrenci_id UUID REFERENCES ogrenciler(id) ON DELETE CASCADE,
    yonetici_id UUID REFERENCES admin_kullanicilar(id) ON DELETE CASCADE,
    okul_id INTEGER REFERENCES okullar(id) ON DELETE SET NULL,
    test_hesabi BOOLEAN NOT NULL DEFAULT false,
    oturum_id UUID NOT NULL,
    cihaz VARCHAR(10),
    menu_kod VARCHAR(60) NOT NULL,
    menu_ad VARCHAR(120),
    alt_kod VARCHAR(60) NOT NULL DEFAULT '',
    alt_ad VARCHAR(120),
    aktif_sn INTEGER NOT NULL DEFAULT 0,
    acik_sn INTEGER NOT NULL DEFAULT 0,
    ziyaret INTEGER NOT NULL DEFAULT 0,
    ilk_zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    son_zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_kullanim_kisi CHECK ((ogrenci_id IS NULL) <> (yonetici_id IS NULL)),
    CONSTRAINT uq_kullanim_dilim UNIQUE (oturum_id, menu_kod, alt_kod, saat)
);
CREATE INDEX IF NOT EXISTS ix_kullanim_saat ON kullanim_sureleri (saat);
CREATE INDEX IF NOT EXISTS ix_kullanim_ogrenci ON kullanim_sureleri (ogrenci_id, saat) WHERE ogrenci_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_kullanim_yonetici ON kullanim_sureleri (yonetici_id, saat) WHERE yonetici_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_kullanim_okul ON kullanim_sureleri (okul_id, saat);
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'kullanim_suresi_saklama_gun', '730', 'Kullanım sürelerinin (hangi menüde ne kadar süre) saklama süresi, gün. 0 = silinmez.', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'kullanim_suresi_saklama_gun')
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS kullanim_sureleri")
