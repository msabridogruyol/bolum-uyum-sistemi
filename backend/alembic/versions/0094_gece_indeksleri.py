"""Gece indeksleri — yük altında gereken indeksler (gece bakımında, CONCURRENTLY)

Revision ID: 0094_gece_indeksleri
Revises: 0093_denetim_guvenlik_performans
Create Date: 2026-11-04

[2026-11-04] Kullanıcı kuralı: sistemi yavaşlatacak değişiklikler gece 03:00'te yapılır. Büyük tablolarda düz CREATE INDEX
yazmayı (cevap kaydını) bitene kadar durdurur; bu indeksler açılışta değil gece bakımında (app/core/gece_bakimi.py) ve
CONCURRENTLY ile kurulur (tablo kilitlenmez). sema_guncelleme.OTOMATIK_GECE listesinde; yarım kalan (geçersiz) indeks gece
bakımının başında silinip yeniden kurulur.
  - lower(email): her giriş, şifre sıfırlama ve toplu öğrenci yüklemesinde satır başına 2–3 kez aranıyor.
  - tur_id / ogrenci_id yabancı anahtarları: tur ya da öğrenci silinince CASCADE tam tarama yapıyordu.
  - sorular(katman_id) WHERE ogrenci_id IS NULL: her katman başlangıcında ortak soru bankası okunur.
  - guvenlik_fotograflari(cekim_zamani): saklama süresi temizliği.
"""
from alembic import op

revision = "0094_gece_indeksleri"
down_revision = "0093_denetim_guvenlik_performans"
branch_labels = None
depends_on = None

SQL = """
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_ogrenciler_lower_email ON ogrenciler (lower(email));
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_admin_kullanicilar_lower_email ON admin_kullanicilar (lower(email));
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_ogrenci_cevaplar_tur ON ogrenci_cevaplar (tur_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_ogrenci_dal_uyum_tur ON ogrenci_dal_uyum_skorlari (tur_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_ogrenci_dal_oturum_tur ON ogrenci_dal_oturumlari (tur_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_guvenlik_olay_tur ON guvenlik_olaylari (tur_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_guvenlik_foto_tur ON guvenlik_fotograflari (tur_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_guvenlik_foto_ogrenci ON guvenlik_fotograflari (ogrenci_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_guvenlik_foto_zaman ON guvenlik_fotograflari (cekim_zamani);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_koclugu_oturum_ogrenci ON ogrenci_koclugu_oturumlari (ogrenci_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_koclugu_oturum_tur ON ogrenci_koclugu_oturumlari (tur_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_sorular_tur ON sorular (tur_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_sorular_ortak_katman ON sorular (katman_id) WHERE ogrenci_id IS NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_anket_katilim_ogrenci ON anket_katilim (ogrenci_id)
"""


def upgrade():
    with op.get_context().autocommit_block():
        for komut in [k.strip() for k in SQL.split(";\n") if k.strip()]:
            op.execute(komut)


def downgrade():
    pass
