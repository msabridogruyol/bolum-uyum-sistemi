"""[2026-11-02] Öğrenciye görünen içerikte lise düzeyine uygun dil

Revision ID: 0089_icerik_sadelestirme
Revises: 0088_pipeline_paketi

Kaynak: app/data/icerik_sadelestirme.json
  * bolum_detay   — [{bolum, yol, eski, yeni}] bölüm tanıtımlarının (bolumler.detay) metin alanları
  * kisa_aciklama — [{bolum, eski, yeni}] bolumler.kisa_aciklama
  * tablo         — [{tablo, sutun, eski, yeni}] diğer içerik tabloları (ör. meslek_grubu_ai_etkisi.aciklama)
Her değişiklik yalnızca alanın şu anki değeri `eski` ile AYNIYSA uygulanır (yönetim panelinden değiştirilmiş metin ezilmez;
tekrar çalıştırmak güvenlidir). Ağır/akademik sözcükler sadeleştirildi, gerekli teknik terimlere kısa açıklama eklendi,
uzun cümleler bölündü; bilgi, sayı ve adlar değişmedi.
"""
import json
import re
from pathlib import Path

from alembic import op

revision = "0089_icerik_sadelestirme"
down_revision = "0088_pipeline_paketi"
branch_labels = None
depends_on = None

_VERI = Path(__file__).resolve().parents[2] / "app" / "data" / "icerik_sadelestirme.json"
_TABLOLAR = {("meslek_grubu_ai_etkisi", "aciklama")}   # izin verilen tablo/sütunlar (veri dosyasından SQL adı alınmaz)

_DETAY = """
DO $$
DECLARE d jsonb := __VERI__::jsonb;
DECLARE r record;
DECLARE yol text[];
BEGIN
  FOR r IN SELECT value AS v FROM jsonb_array_elements(d) LOOP
    yol := ARRAY(SELECT jsonb_array_elements_text(r.v->'yol'));
    UPDATE bolumler SET detay = jsonb_set(detay::jsonb, yol, to_jsonb(r.v->>'yeni'))::json
     WHERE ad = r.v->>'bolum' AND detay IS NOT NULL AND (detay::jsonb #>> yol) = r.v->>'eski';
  END LOOP;
END
$$;
"""
_KISA = """
DO $$
DECLARE d jsonb := __VERI__::jsonb;
DECLARE r record;
BEGIN
  FOR r IN SELECT value AS v FROM jsonb_array_elements(d) LOOP
    UPDATE bolumler SET kisa_aciklama = r.v->>'yeni' WHERE ad = r.v->>'bolum' AND kisa_aciklama = r.v->>'eski';
  END LOOP;
END
$$;
"""
_TABLO = """
DO $$
DECLARE d jsonb := __VERI__::jsonb;
DECLARE r record;
BEGIN
  FOR r IN SELECT value AS v FROM jsonb_array_elements(d) LOOP
    UPDATE __TABLO__ SET __SUTUN__ = r.v->>'yeni' WHERE __SUTUN__ = r.v->>'eski';
  END LOOP;
END
$$;
"""


def _gom(kayitlar: list, alanlar: tuple) -> str:
    s = json.dumps([{k: x[k] for k in alanlar} for x in kayitlar], ensure_ascii=False, separators=(", ", ": "))
    assert "\n" not in s and "$j$" not in s
    s = re.sub(r"(?<![:\w\\]):(?=\w)", r"\\:", s)   # SQLAlchemy text() ':ad' biçimini parametre sanmasın
    return "$j$" + s + "$j$"


def sql_uret() -> str:
    veri = json.loads(_VERI.read_text(encoding="utf-8"))
    parcalar = [_DETAY.replace("__VERI__", _gom(veri["bolum_detay"], ("bolum", "yol", "eski", "yeni"))),
                _KISA.replace("__VERI__", _gom(veri["kisa_aciklama"], ("bolum", "eski", "yeni")))]
    gruplar: dict = {}
    for x in veri.get("tablo") or []:
        gruplar.setdefault((x["tablo"], x["sutun"]), []).append(x)
    for (tablo, sutun), kayitlar in sorted(gruplar.items()):
        assert (tablo, sutun) in _TABLOLAR, (tablo, sutun)
        parcalar.append(_TABLO.replace("__TABLO__", tablo).replace("__SUTUN__", sutun)
                        .replace("__VERI__", _gom(kayitlar, ("eski", "yeni"))))
    return "".join(p.strip().replace(";\n", "; \n") + ";\n" for p in parcalar)


SQL = sql_uret()


def upgrade() -> None:
    op.execute(SQL)


def downgrade() -> None:
    pass
