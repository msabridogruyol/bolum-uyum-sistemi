"""Filiz kriz: okula bildirim parametresi (varsayılan kapalı)

Revision ID: 0091_kriz_okul_bildirimi
Revises: 0090_soru_sadelestirme
Create Date: 2026-11-03

[2026-11-03] filiz_kriz_okul_bildirimi: Filiz'e yazılan bir mesajda KESİN kriz ifadesi algılandığında öğrencinin okulundaki
okul yetkililerine (uygulama içi + e-posta) "öğrenciyle görüşün" bildirimi gider; mesajın içeriği paylaşılmaz.
Değer: boş = kapalı (varsayılan) · '*' = bütün okullar · '3,7' = yalnızca bu okul numaraları.
Açmadan önce: KVKK aydınlatma metni bu aktarımı kapsayacak biçimde güncellenmeli ve okulla kriz protokolü yazılmalı.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0091_kriz_okul_bildirimi"
down_revision = "0090_soru_sadelestirme"
branch_labels = None
depends_on = None

SQL = """
INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
SELECT 'filiz_kriz_okul_bildirimi', '', 'Filiz kriz ifadesinde okul yetkilisine bildirim (mesaj içeriği paylaşılmaz). Boş = kapalı, * = bütün okullar, 3,7 = bu okullar. Açmadan önce KVKK aydınlatma metni ve okulun kriz protokolü güncellenmeli.', now()
WHERE NOT EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'filiz_kriz_okul_bildirimi')
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
