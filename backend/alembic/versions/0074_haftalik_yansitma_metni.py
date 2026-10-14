"""Haftalık yansıtma görevinin açıklaması: gerçeği yansıtmayan cümle kaldırıldı

Revision ID: 0074_haftalik_yansitma_metni
Revises: 0072_ogrenme_deneyi
Create Date: 2026-10-14

[2026-10-14] Kayıtlı haftalık görevlerde "Filiz, cevaplarına bakarak önerilerini sana uygun hale getirir." cümlesi duruyordu;
Filiz yansıtma cevaplarını okumaz (yalnızca öğrenciye gösterilir). Yeni görevler zaten yeni metinle üretiliyor
(haftalik_servisi); bu güncelleme mevcut kayıtları da düzeltir.
(0073 numarası birleştirilmemiş bir dalda kullanıldığı için atlandı.)
İdempotent: eski cümle yoksa hiçbir satıra dokunmaz; app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0074_haftalik_yansitma_metni"
down_revision = "0072_ogrenme_deneyi"
branch_labels = None
depends_on = None

SQL = """
UPDATE ogrenci_haftalik_gorev
   SET aciklama = replace(aciklama, 'Filiz, cevaplarına bakarak önerilerini sana uygun hale getirir.',
                          'Cevaplarını yalnızca sen görürsün; geçmiş haftalarına dönüp bakabilirsin.')
 WHERE aciklama LIKE '%Filiz, cevaplarına bakarak önerilerini sana uygun hale getirir.%'
"""


def upgrade() -> None:
    op.execute(SQL)


def downgrade() -> None:
    pass
