"""[2026-10-18] Bölüm kısa açıklamaları

Revision ID: 0077_bolum_kisa_aciklama
Revises: 0076_yeni_k5_sorular

Neden: bolumler.kisa_aciklama yerel veritabanlarının hepsinde boştu; bölüm bilgi penceresi, listem ve keşfet ekranı
yedek metni ("Bu bölümün ayrıntılarını …") gösteriyordu. Kaynak tek: pipeline'ın veri/bolumler.csv dosyası (bölüm
embedding'ine giren açıklama) → app/data/bolum_kisa_aciklama.json. Yalnızca BOŞ olan açıklamalar doldurulur; yönetim
panelinden yazılmış açıklamaya dokunulmaz. Tekrar çalıştırılabilir.
"""
import json
import re
from pathlib import Path

from alembic import op

revision = "0077_bolum_kisa_aciklama"
down_revision = "0076_yeni_k5_sorular"
branch_labels = None
depends_on = None

_VERI = Path(__file__).resolve().parents[2] / "app" / "data" / "bolum_kisa_aciklama.json"


def sql_uret() -> str:
    d = json.loads(_VERI.read_text(encoding="utf-8"))["bolumler"]
    s = json.dumps(d, ensure_ascii=False, separators=(", ", ": "))
    assert "\n" not in s and "$j$" not in s and not re.search(r"(?<![:\w]):\w", s)
    return ("UPDATE bolumler b SET kisa_aciklama = v.value FROM jsonb_each_text($j$" + s + "$j$::jsonb) v "
            "WHERE b.ad = v.key AND coalesce(btrim(b.kisa_aciklama), '') = '';\n")


SQL = sql_uret()


def upgrade() -> None:
    op.execute(SQL)


def downgrade() -> None:
    pass
