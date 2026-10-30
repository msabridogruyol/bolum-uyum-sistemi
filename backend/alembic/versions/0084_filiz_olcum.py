"""Katmanlı Filiz ölçümü: cevabın kaynağı ve süresi

Revision ID: 0084_filiz_olcum
Revises: 0083_filiz_her_pakette
Create Date: 2026-10-31

[2026-10-31] ogrenci_koclugu_mesajlari:
* kaynak  — asistan cevabı hangi katmandan geldi: yz (yapay zekâ) | icerik (sistem içeriği) | rehber (öğrencinin verisi) |
            sabit (gizlilik) | kriz | bilinmiyor. Eski satırlarda boş kalır.
* sure_ms — cevabın hazırlanma süresi (ms).
* İndeksler: oturum_id ve yapay zekâ cevaplarının zamanı (günlük / aylık sınır sayımı her mesajda yapılır).
Süper admin özeti: GET /admin/filiz/kullanim. İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0084_filiz_olcum"
down_revision = "0083_filiz_her_pakette"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenci_koclugu_mesajlari ADD COLUMN IF NOT EXISTS kaynak VARCHAR(12);
ALTER TABLE ogrenci_koclugu_mesajlari ADD COLUMN IF NOT EXISTS sure_ms INTEGER;
CREATE INDEX IF NOT EXISTS ix_koclugu_mesaj_oturum ON ogrenci_koclugu_mesajlari (oturum_id);
CREATE INDEX IF NOT EXISTS ix_koclugu_mesaj_yz_zaman ON ogrenci_koclugu_mesajlari (olusturulma_zamani) WHERE rol = 'asistan' AND yapay_zeka
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    pass
