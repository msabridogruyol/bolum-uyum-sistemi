"""Çoklu dil: kişisel dil tercihi ve içerik çeviri önbelleği

Revision ID: 0067_coklu_dil
Revises: 0066_pilot_hazirlik
Create Date: 2026-10-12

[2026-10-12]
* ogrenciler / admin_kullanicilar.dil — kişinin seçtiği arayüz dili (NULL = hiç seçmedi; Türkçe görünür ve tarayıcıdaki seçim hesaba yazılır). Her kullanıcı kendisi seçer.
* ceviri_onbellek — bölüm açıklaması, sözlük, iş hayatı içerikleri gibi sistem içeriğinin yapay zekâ çevirisi.
  Bir metin bir dile bir kez çevrilir, sonra buradan okunur. Yalnızca sistemin kendi içeriği saklanır (kişisel veri yok).
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde, her açılışta yeniden çalışır.
"""
from alembic import op

revision = "0067_coklu_dil"
down_revision = "0066_pilot_hazirlik"
branch_labels = None
depends_on = None

SQL = """
ALTER TABLE ogrenciler ADD COLUMN IF NOT EXISTS dil VARCHAR(5);
ALTER TABLE admin_kullanicilar ADD COLUMN IF NOT EXISTS dil VARCHAR(5);
CREATE TABLE IF NOT EXISTS ceviri_onbellek (
    id BIGSERIAL PRIMARY KEY,
    dil VARCHAR(5) NOT NULL,
    kaynak_ozet CHAR(64) NOT NULL,
    kaynak TEXT NOT NULL,
    ceviri TEXT NOT NULL,
    olusturma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_ceviri_onbellek_dil_ozet ON ceviri_onbellek (dil, kaynak_ozet)
"""


def upgrade():
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade():
    op.execute("DROP TABLE IF EXISTS ceviri_onbellek")
    op.execute("ALTER TABLE admin_kullanicilar DROP COLUMN IF EXISTS dil")
    op.execute("ALTER TABLE ogrenciler DROP COLUMN IF EXISTS dil")
