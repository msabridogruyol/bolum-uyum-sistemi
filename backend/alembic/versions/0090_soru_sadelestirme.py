"""[2026-11-02] K1–K4 soruları: lise düzeyinde sade dil ve gündelik hayata dengeli dağılım

Revision ID: 0090_soru_sadelestirme
Revises: 0089_icerik_sadelestirme

Kaynak: app/data/soru_sadelestirme.json — [{katman, eski_metin, yeni_metin, uc_a, uc_b, secenekler}]
  * Soru kökü, iki uçlu soruların uç metinleri ve şık metinleri değişir. Soru tipi, şık sayısı, şık sırası ve her şıkkın
    ölçtüğü değişken AYNEN kalır (soru kimliği, verilmiş cevaplar ve puanlama etkilenmez).
  * Her alan yalnızca şu anki değeri `eski` ile AYNIYSA değişir: yönetim panelinden düzeltilmiş metin ezilmez,
    tekrar çalıştırmak güvenlidir. Boş kurulumda (soru yoksa) hiçbir şey yapmaz.
  * Yeni kurulumlar için app/data/olcme_sorulari.json ve olcme_sorulari_ek.json da yeni metinlerle günceldir; K5
    bankasındaki (k5_soru_bankasi.json) değişiklikler 0076'nın sürüm kontrolüyle yüklenir.
"""
import json
import re
from pathlib import Path

from alembic import op

revision = "0090_soru_sadelestirme"
down_revision = "0089_icerik_sadelestirme"
branch_labels = None
depends_on = None

_VERI = Path(__file__).resolve().parents[2] / "app" / "data" / "soru_sadelestirme.json"

_SQL = """
DO $$
DECLARE d jsonb := __VERI__::jsonb;
DECLARE q record;
DECLARE o record;
DECLARE s record;
BEGIN
  FOR q IN SELECT value AS v FROM jsonb_array_elements(d) LOOP
    FOR s IN SELECT so.id FROM sorular so JOIN katmanlar k ON k.id = so.katman_id
              WHERE k.kod = q.v->>'katman' AND so.ogrenci_id IS NULL
                AND so.soru_metni IN (q.v->>'eski_metin', q.v->>'yeni_metin') LOOP
      FOR o IN SELECT value AS x FROM jsonb_array_elements(q.v->'secenekler') LOOP
        UPDATE soru_secenekleri SET secenek_metni = o.x->>'yeni'
         WHERE soru_id = s.id AND secenek_sirasi = (o.x->>'sira')::int AND secenek_metni = o.x->>'eski';
      END LOOP;
      IF q.v->'uc_a' <> 'null'::jsonb THEN
        UPDATE sorular SET uc_a_metni = q.v->'uc_a'->>1 WHERE id = s.id AND uc_a_metni = q.v->'uc_a'->>0;
      END IF;
      IF q.v->'uc_b' <> 'null'::jsonb THEN
        UPDATE sorular SET uc_b_metni = q.v->'uc_b'->>1 WHERE id = s.id AND uc_b_metni = q.v->'uc_b'->>0;
      END IF;
      UPDATE sorular SET soru_metni = q.v->>'yeni_metin' WHERE id = s.id AND soru_metni = q.v->>'eski_metin';
    END LOOP;
  END LOOP;
END
$$;
"""


def _gom(veri) -> str:
    s = json.dumps(veri, ensure_ascii=False, separators=(", ", ": "))
    assert "\n" not in s and "$j$" not in s
    s = re.sub(r"(?<![:\w\\]):(?=\w)", r"\\:", s)   # SQLAlchemy text() ':ad' biçimini parametre sanmasın
    return "$j$" + s + "$j$"


def sql_uret() -> str:
    veri = json.loads(_VERI.read_text(encoding="utf-8"))
    return _SQL.strip().replace("__VERI__", _gom(veri["sorular"])).replace(";\n", "; \n") + ";\n"


SQL = sql_uret()


def upgrade() -> None:
    op.execute(SQL)


def downgrade() -> None:
    pass
