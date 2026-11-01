"""onlisans_bolum_kaldirma — yalnızca ön lisans (2 yıl) olan 4 bölüm kaldırılır; sistem lisans bölümleriyle çalışır

Revision ID: 0086_onlisans_bolum_kaldirma
Revises: 0085_veri_kaynagi_kontrol
Create Date: 2026-11-01

[2026-11-01] Kullanıcı kararı: ön lisans programları sistemli olarak ileride ayrı bir geliştirmeyle eklenecek; o zamana kadar
sistemde yalnızca ön lisans olan bölüm bulunmaz. Öğrenim süresi "2 yıl" olan 4 bölüm kaldırılır: Güverte, Ayakkabı Tasarımı
ve Üretimi, Saç ve Güzellik Uygulamaları, Kanatlı Hayvan Yetiştiriciliği. Lisans programı da olan bölümler ("Programa göre
2 veya 4 yıl": El Sanatları, Halı Tasarımı, Takı Tasarımı ve İmalatı, Çini Tasarımı ve Onarımı, Kuyumculuk ve Mücevher Tasarımı;
Basım Teknolojileri) kalır. Silme 0082 ile AYNI yöntemle yapılır (yabancı anahtar grafiği izlenir; NULL olabilen bağlantı NULL
yapılır, olamayan satır silinir). İdempotent. app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
import importlib.util
from pathlib import Path

from alembic import op

revision = "0086_onlisans_bolum_kaldirma"
down_revision = "0085_veri_kaynagi_kontrol"
branch_labels = None
depends_on = None

KALDIRILAN = [
    "GÜVERTE",
    "AYAKKABI TASARIMI VE ÜRETİMİ",
    "SAÇ VE GÜZELLİK UYGULAMALARI",
    "KANATLI HAYVAN YETİŞTİRİCİLİĞİ",
]

_spec = importlib.util.spec_from_file_location("_g0082", Path(__file__).with_name("0082_bolum_kaldirma.py"))
_g0082 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_g0082)

SQL = _g0082.sql_uret(KALDIRILAN)


def upgrade() -> None:
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade() -> None:
    pass   # kaldırılan bölümler geri getirilmez (kullanıcı kararı)
