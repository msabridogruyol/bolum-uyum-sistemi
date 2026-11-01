"""bolum_kaldirma — Türkiye'de lisans programı olmayan ya da 3'ten az üniversitede okutulan 12 bölüm kaldırılır

Revision ID: 0082_bolum_kaldirma
Revises: 0081_ek_olcme_sorulari
Create Date: 2026-10-29

[2026-10-29] Resmî ders planı taraması ve YÖK Atlas kontrolü sonucu (kullanıcı kararı):
  * Bu adla lisans programı yok: Liderlik, Hidrolik ve Su Kaynakları Müh., Teknoloji Girişimciliği,
    Ulaştırma ve Trafik Müh., Caz ve Popüler Müzik, Müzik Çalgı, Aksesuar Tasarımı.
  * 3'ten az üniversitede (ya da yalnızca yurt dışında / önlisans olarak): Uluslararası Ekonomik İlişkiler,
    Uluslararası Hukuk, Bileşik Sanatlar, Müzik Ses ve Performans, Çalgı Teknolojileri.
Bölüm ve ona bağlı tüm satırlar 0075 ile AYNI yöntemle silinir: yabancı anahtar grafiği izlenir; NULL olabilen
bağlantı (ör. hedef bölüm) NULL yapılır, olamayan satır silinir. Diğer bölümlerin profiline dokunulmaz.
İdempotent: bölümler artık yoksa hiçbir şey yapmaz. app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
import importlib.util
from pathlib import Path

from alembic import op

revision = "0082_bolum_kaldirma"
down_revision = "0081_ek_olcme_sorulari"
branch_labels = None
depends_on = None

KALDIRILAN = [
    "LİDERLİK",
    "HİDROLİK VE SU KAYNAKLARI MÜHENDİSLİĞİ",
    "TEKNOLOJİ GİRİŞİMCİLİĞİ",
    "ULAŞTIRMA VE TRAFİK MÜHENDİSLİĞİ",
    "CAZ VE POPÜLER MÜZİK",
    "MÜZİK ÇALGI",
    "AKSESUAR TASARIMI",
    "ULUSLARARASI EKONOMİK İLİŞKİLER",
    "ULUSLARARASI HUKUK",
    "BİLEŞİK SANATLAR",
    "MÜZİK SES VE PERFORMANS",
    "ÇALGI TEKNOLOJİLERİ",
]

_spec = importlib.util.spec_from_file_location("_g0075", Path(__file__).with_name("0075_bolum_birlestirme.py"))
_g0075 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_g0075)

_KALDIR_KALIP = """
DO $$
DECLARE idler int[];
BEGIN
  idler := ARRAY(SELECT id FROM bolumler WHERE ad = ANY(ARRAY[__ADLAR__]::text[]));
  IF cardinality(idler) > 0 THEN
    PERFORM pg_temp.bb_sil('bolumler'::regclass, format('id = ANY(%L::int[])', idler));
  END IF;
END
$$
"""


def sql_uret(adlar: list[str]) -> str:
    """sema_guncelleme ";\\n" ile böler: fonksiyon/blok gövdesindeki satır sonları bölünmeyecek hale getirilir."""
    blok = _KALDIR_KALIP.replace("__ADLAR__", ", ".join("'" + a.replace("'", "''") + "'" for a in adlar))
    return _g0075._SIL_FONKSIYONU.strip().replace(";\n", "; \n") + ";\n" + blok.strip().replace(";\n", "; \n") + ";\n"


SQL = sql_uret(KALDIRILAN)


def upgrade() -> None:
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade() -> None:
    pass   # kaldırılan bölümler geri getirilmez (kullanıcı kararı)
