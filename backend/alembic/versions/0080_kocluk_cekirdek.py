"""Koçluk her pakette zorunlu (bölüm yönlendirme + koçluk sistemin omurgası)

Revision ID: 0080_kocluk_cekirdek
Revises: 0079_yeniden_degerlendirme_sikligi
Create Date: 2026-10-19

[2026-10-19] Kod tarafı (app/core/paketler.py ZORUNLU) koçluğu zaten her okulda açar; bu göç veriyi de tutarlı yapar:
* Her paketin modül listesine 'kocluk' eklenir (yoksa).
* Okullara özel "çıkarılan modüller" listesinden 'kocluk' silinir; "eklenen modüller"deki gereksiz 'kocluk' de temizlenir.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0080_kocluk_cekirdek"
down_revision = "0079_yeniden_degerlendirme_sikligi"
branch_labels = None
depends_on = None

SQL = """
UPDATE paketler SET moduller = coalesce(moduller, '[]'::jsonb) || '["kocluk"]'::jsonb
 WHERE NOT coalesce(moduller, '[]'::jsonb) ? 'kocluk';
UPDATE okullar SET modul_cikar = modul_cikar - 'kocluk' WHERE modul_cikar ? 'kocluk';
UPDATE okullar SET modul_ekle = modul_ekle - 'kocluk' WHERE modul_ekle ? 'kocluk'
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    pass
