"""Güncel adlar: K5 katman adı ve kullanılmayan eski parametreler

Revision ID: 0092_guncel_adlar
Revises: 0091_kriz_okul_bildirimi
Create Date: 2026-11-03

[2026-11-03] Bilgi denetimi:
  1) katmanlar.ad (K5) ilk kurulumdan (0002) beri "Dal Derinleşme Modülü" idi; K5 2026-10-18'den beri tek adımlı
     "İş türü tercihleri"dir. Ad öğrencinin Değerlendirme ekranında, Cevap Analizi'nde ve katman listelerinde
     veritabanından gösterildiği için eski sistemi anlatıyordu. Yalnızca ad hâlâ ilk kurulumdaki değerse değişir.
  2) 0002'deki dört parametre hiçbir hesapta okunmuyor ama Parametreler ekranında değiştirilebilir görünüyordu:
       k5_esik_puani (eski alan K5 eşiği 80; gerçek eşik dal_servisi.KUME_ESIK = 70),
       k5_max_dal_sayisi (eski "en fazla 3 dal"; K5 artık tek adım),
       yakinsama_esik_sigma (eski pipeline güven eşiği; pipeline artık bu değeri sistemden almıyor),
       yeniden_degerlendirme_min_gun (120; yerini yeniden_degerlendirme_gun_12 ve yeniden_degerlendirme_yillik_hak aldı).
     Etkisiz ayar yanıltıcı olduğu için kaldırılır.
İdempotent: app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0092_guncel_adlar"
down_revision = "0091_kriz_okul_bildirimi"
branch_labels = None
depends_on = None

SQL = """
UPDATE katmanlar SET ad = 'İş türü tercihleri' WHERE kod = 'K5' AND ad = 'Dal Derinleşme Modülü';
DELETE FROM sistem_parametreleri
 WHERE anahtar IN ('k5_esik_puani', 'k5_max_dal_sayisi', 'yakinsama_esik_sigma', 'yeniden_degerlendirme_min_gun')
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("UPDATE katmanlar SET ad = 'Dal Derinleşme Modülü' WHERE kod = 'K5' AND ad = 'İş türü tercihleri'")
