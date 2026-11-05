"""Veli onay formu kayıtları

Revision ID: 0100_veli_onaylari
Revises: 0099_gelisim_listesi
Create Date: 2026-11-05

[2026-11-05] 18 yaş altı öğrenciler için veli onayı (kullanıcı kararı: basılı form + panelden işaret; onay gelene
kadar kişisel veri işleyen asıl işlemler kilitli). Sistem öğrencinin adıyla doldurulmuş veli onay formunu PDF olarak
üretir; okul imzalı formu alınca okul yetkilisi (okul harici öğrencide süper admin) panelden işaretler.
Kayıtlar yalnızca eklenir (geri alma da bir satırdır); en son satır geçerli durumdur.
  islem: alindi (veli formu imzalı alındı) | resit (öğrenci 18 yaşını doldurmuş; veli onayı gerekmez) | geri_alindi
İdempotent; app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0100_veli_onaylari"
down_revision = "0099_gelisim_listesi"
branch_labels = None
depends_on = None

SQL = r"""
CREATE TABLE IF NOT EXISTS veli_onaylari (
    id BIGSERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    islem VARCHAR(20) NOT NULL CHECK (islem IN ('alindi', 'resit', 'geri_alindi')),
    form_tarihi DATE,
    veli_ad_soyad VARCHAR(120),
    kamera BOOLEAN NOT NULL DEFAULT FALSE,
    form_surumu VARCHAR(40),
    aciklama VARCHAR(300),
    yapan_id UUID,
    yapan_ad VARCHAR(200),
    zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (islem <> 'alindi' OR form_tarihi IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS ix_veli_onaylari_ogrenci ON veli_onaylari (ogrenci_id, zaman DESC, id DESC)
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
