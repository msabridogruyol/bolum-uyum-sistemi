"""hata_kayitlari (gruplu hata izleme) + istek sıklığı sınırı parametreleri

Revision ID: 0060_hata_kayitlari
Revises: 0058_ai_etkisi
Create Date: 2026-10-11

app/core/hata_izleme.py yakalanmamış sunucu istisnalarını ve POST /istemci-hata ile gelen tarayıcı hatalarını
parmak izine göre tek satırda gruplar (sayi, ilk/son görülme, son 20 istek kimliği). Kişisel veri yazılmadan önce
maskelenir. sistem_parametreleri'ne istek sıklığı sınırı (app/core/hiz_siniri.py) anahtarları eklenir (varsa dokunulmaz).
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
NOT: 0059 başka bir çalışmaya ayrıldı; o eklenince down_revision ona çevrilmeli (sema_guncelleme sırayı umursamaz).
"""
from alembic import op

revision = "0060_hata_kayitlari"
down_revision = "0058_ai_etkisi"   # 0059 eklenirse "0059_..." yapılmalı (tek alembic başı)
branch_labels = None
depends_on = None

SQL = """
CREATE TABLE IF NOT EXISTS hata_kayitlari (
    id BIGSERIAL PRIMARY KEY,
    parmak_izi VARCHAR(40) NOT NULL,
    kaynak VARCHAR(20) NOT NULL DEFAULT 'sunucu',
    yol VARCHAR(500),
    yol_kalibi VARCHAR(300),
    metod VARCHAR(10),
    durum_kodu INTEGER,
    istisna_turu VARCHAR(200),
    mesaj TEXT,
    yigin_izi TEXT,
    kullanici_tipi VARCHAR(30),
    istek_kimligi VARCHAR(64),
    tarayici VARCHAR(300),
    sayi INTEGER NOT NULL DEFAULT 1,
    son_istekler JSONB NOT NULL DEFAULT '[]'::jsonb,
    ilk_gorulme TIMESTAMPTZ NOT NULL DEFAULT now(),
    son_gorulme TIMESTAMPTZ NOT NULL DEFAULT now(),
    cozuldu_mu BOOLEAN NOT NULL DEFAULT FALSE,
    cozulme_zamani TIMESTAMPTZ,
    cozen VARCHAR(200)
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_hata_kayitlari_parmak_izi ON hata_kayitlari (parmak_izi);
CREATE INDEX IF NOT EXISTS ix_hata_kayitlari_son_gorulme ON hata_kayitlari (son_gorulme DESC);
CREATE TABLE IF NOT EXISTS tek_seferlik_gocler (ad VARCHAR PRIMARY KEY, uygulanma_zamani TIMESTAMPTZ NOT NULL DEFAULT now());
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani) VALUES
    ('hiz_siniri', 'acik', 'İstek sıklığı sınırı: acik / kapali', now()),
    ('hiz_siniri_kimlik_dakika', '20', 'Giriş, 2 adımlı kod, şifre sıfırlama, kayıt, test girişi: IP başına dakikada en çok istek', now()),
    ('hiz_siniri_kimlik_saat', '150', 'Kimlik uçları: IP başına saatte en çok istek', now()),
    ('hiz_siniri_agir_dakika', '20', 'Dosya yükleme, toplu yükleme, PDF/Excel, Filiz AI: kişi (yoksa IP) başına dakikada en çok istek', now()),
    ('hiz_siniri_agir_saat', '300', 'Ağır uçlar: kişi (yoksa IP) başına saatte en çok istek', now()),
    ('hiz_siniri_genel_dakika', '300', 'Diğer tüm API: kişi (yoksa IP) başına dakikada en çok istek', now()),
    ('hiz_siniri_istemci_hata_dakika', '10', 'Tarayıcı hata bildirimi (/istemci-hata): IP başına dakikada en çok', now()),
    ('hiz_siniri_istemci_hata_saat', '60', 'Tarayıcı hata bildirimi: IP başına saatte en çok', now())
ON CONFLICT (anahtar) DO NOTHING
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS hata_kayitlari")
