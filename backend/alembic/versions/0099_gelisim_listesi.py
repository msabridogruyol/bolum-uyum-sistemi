"""Gelişim listesi: isteğe bağlı keşif ve öz değerlendirme kayıtları

Revision ID: 0099_gelisim_listesi
Revises: 0098_tufe_endeksi
Create Date: 2026-11-05

[2026-11-05] Kullanıcı kararı: haftalık 3 görev kaldırıldı; yerine gelişim alanlarına göre yapılacaklar listesi
(app/core/gelisim_listesi.py). Bölüm keşfi ve 3 soruluk öz değerlendirme isteğe bağlı maddeler olarak; öğrencinin her gelişim maddesi için girdiği
"şu tarihte şunu yaptım" kayıtları (tur = 'adim_kaydi': hedef bölüm + adım kodu + tarih + açıklama) bu tabloya yazılır.
Eski ogrenci_haftalik_gorev tablosu silinmez (geçmiş kayıt). Canlıda yalnızca SQL metni çalışır (sema_guncelleme).
"""
from alembic import op

revision = "0099_gelisim_listesi"
down_revision = "0098_tufe_endeksi"
branch_labels = None
depends_on = None

SQL = r"""
CREATE TABLE IF NOT EXISTS ogrenci_gelisim_kayitlari (
    id BIGSERIAL PRIMARY KEY,
    ogrenci_id UUID NOT NULL REFERENCES ogrenciler(id) ON DELETE CASCADE,
    tur VARCHAR(20) NOT NULL CHECK (tur IN ('kesif', 'oz_degerlendirme', 'adim_kaydi')),
    ref_bolum_id INTEGER REFERENCES bolumler(id) ON DELETE SET NULL,
    adim_kodu VARCHAR(40),
    tarih DATE,
    aciklama TEXT,
    yanit JSONB,
    zaman TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (tur <> 'adim_kaydi' OR (adim_kodu IS NOT NULL AND ref_bolum_id IS NOT NULL AND tarih IS NOT NULL AND aciklama IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS ix_ogk_ogrenci_tur ON ogrenci_gelisim_kayitlari (ogrenci_id, tur, zaman DESC);
CREATE INDEX IF NOT EXISTS ix_ogk_adim ON ogrenci_gelisim_kayitlari (ogrenci_id, ref_bolum_id, adim_kodu) WHERE tur = 'adim_kaydi';
CREATE UNIQUE INDEX IF NOT EXISTS ux_ogk_kesif ON ogrenci_gelisim_kayitlari (ogrenci_id, ref_bolum_id) WHERE tur = 'kesif'
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
