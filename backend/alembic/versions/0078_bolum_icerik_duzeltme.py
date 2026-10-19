"""[2026-10-18] Bölüm tanıtım içeriği düzeltmeleri

Revision ID: 0078_bolum_icerik_duzeltme
Revises: 0077_bolum_kisa_aciklama

Kaynak: app/data/bolum_detay_duzeltme.json — [{bolum, yol (JSON yol dizisi), eski, yeni, neden}]. Her düzeltme yalnızca
alanın şu anki değeri `eski` ile AYNIYSA uygulanır (yönetim panelinden değiştirilmiş metin ezilmez; tekrar çalıştırılabilir).
Düzeltmeler 278 bölümün içerik denetiminden (olgu doğrulaması kaynaklı) gelir; ör. öğretmen atamasında 2025'ten beri
KPSS yerine MEB-AGS + Milli Eğitim Akademisi (7528 sayılı Öğretmenlik Meslek Kanunu), yanlış puan türleri.
"""
import json
import re
from pathlib import Path

from alembic import op

revision = "0078_bolum_icerik_duzeltme"
down_revision = "0077_bolum_kisa_aciklama"
branch_labels = None
depends_on = None

_VERI = Path(__file__).resolve().parents[2] / "app" / "data" / "bolum_detay_duzeltme.json"

_KALIP = """
DO $$
DECLARE d jsonb := __VERI__::jsonb;
DECLARE r record;
DECLARE yol text[];
BEGIN
  FOR r IN SELECT value AS v FROM jsonb_array_elements(d) LOOP
    yol := ARRAY(SELECT jsonb_array_elements_text(r.v->'yol'));
    UPDATE bolumler SET detay = jsonb_set(detay::jsonb, yol, r.v->'yeni')::json
     WHERE ad = r.v->>'bolum' AND detay IS NOT NULL AND (detay::jsonb #> yol) = r.v->'eski';
  END LOOP;
END
$$;
"""


def sql_uret() -> str:
    veri = json.loads(_VERI.read_text(encoding="utf-8"))["duzeltmeler"]
    s = json.dumps([{k: x[k] for k in ("bolum", "yol", "eski", "yeni")} for x in veri], ensure_ascii=False, separators=(", ", ": "))
    assert "\n" not in s and "$j$" not in s
    s = re.sub(r"(?<![:\w\\]):(?=\w)", r"\\:", s)   # SQLAlchemy text() ':ad' biçimini parametre sanmasın
    return _KALIP.replace("__VERI__", "$j$" + s + "$j$").strip().replace(";\n", "; \n") + ";\n"


SQL = sql_uret()


def upgrade() -> None:
    op.execute(SQL)


def downgrade() -> None:
    pass
