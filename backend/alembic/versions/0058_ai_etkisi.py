"""İş Hayatı → Gelecekte Bu Meslek: meslek gruplarının üretken yapay zekâya maruz kalma düzeyi (meslek_grubu_ai_etkisi)

Revision ID: 0058_ai_etkisi
Revises: 0057_is_hayati_cv_mezun
Create Date: 2026-10-11

Not: app/core/sema_guncelleme.py bu SQL'i HER sunucu açılışında yeniden çalıştırır; tüm komutlar idempotenttir.
- meslek_grubu_ai_etkisi: ISCO-08 kodu (1–2 hane) başına düzey (dusuk/orta/yuksek/belirsiz), puan (kaynak yayımlamadıysa NULL),
  açıklama, kaynak, kaynak_bolum (tablo/sayfa), veri_yili; dagilim / meslekler (jsonb) kaynağın 4 haneli meslek satırları.
- Tohum tek seferliktir (tek_seferlik_gocler işareti '0058_ai_etkisi_ilo2025'): süper admin bir satırı silerse ya da düzenlerse
  açılışta geri gelmez / ezilmez. Kaynak: app/data/ai_etkisi_gruplar.json → ILO Working Paper 140 (2025), Tablo A1 (s. 48–61).
  Grup düzeyi ILO'nun yayımladığı bir değer değildir; 4 haneli meslek sınıflandırmalarının sayımıyla türetilir (JSON 'duzey_kurali').
"""
import json
import re
from pathlib import Path

from alembic import op

revision = "0058_ai_etkisi"
down_revision = "0057_is_hayati_cv_mezun"
branch_labels = None
depends_on = None

_JSON = Path(__file__).resolve().parents[2] / "app" / "data" / "ai_etkisi_gruplar.json"
_BAG = re.compile(r":(?=\w)")   # SQLAlchemy ':ad' bağ parametresi sanmasın


def _q(s) -> str:
    if s is None:
        return "NULL"
    return "'" + _BAG.sub(": ", str(s)).replace("'", "''") + "'"


def _tohum() -> str:
    try:
        v = json.loads(_JSON.read_text(encoding="utf-8"))
        kaynak = v["kaynak"]["atif"]
        yil = int(v["kaynak"]["veri_yili"])
        gruplar = v["gruplar"]
    except Exception:
        return ""
    satirlar = []
    for kod, g in sorted(gruplar.items()):
        if not re.fullmatch(r"[0-9]{1,2}", kod) or g.get("duzey") not in ("dusuk", "orta", "yuksek", "belirsiz"):
            continue
        meslekler = [{k: m.get(k) for k in ("kod", "ad", "kategori", "ort", "ss", "sayfa")} for m in g.get("meslekler") or []]
        satirlar.append(f"({_q(kod)}, {_q(g['duzey'])}, NULL::numeric, {_q(g.get('aciklama'))}, {_q(kaynak)}, {_q(g.get('kaynak_bolum'))}, {yil}, "
                        f"CAST({_q(json.dumps(g.get('dagilim') or {}, ensure_ascii=False))} AS JSONB), "
                        f"CAST({_q(json.dumps(meslekler, ensure_ascii=False))} AS JSONB))")
    if not satirlar:
        return ""
    return ("WITH isaret AS (\n    INSERT INTO tek_seferlik_gocler (ad) VALUES ('0058_ai_etkisi_ilo2025')\n    ON CONFLICT (ad) DO NOTHING\n"
            "    RETURNING ad\n)\nINSERT INTO meslek_grubu_ai_etkisi (isco_kodu, duzey, puan, aciklama, kaynak, kaynak_bolum, veri_yili, dagilim, meslekler)\n"
            "SELECT v.* FROM (VALUES\n" + ",\n".join(satirlar)
            + "\n) AS v(isco_kodu, duzey, puan, aciklama, kaynak, kaynak_bolum, veri_yili, dagilim, meslekler)\n"
              "WHERE EXISTS (SELECT 1 FROM isaret)\nON CONFLICT (isco_kodu, veri_yili) DO NOTHING")


SQL = """
CREATE TABLE IF NOT EXISTS tek_seferlik_gocler (
    ad VARCHAR PRIMARY KEY,
    uygulanma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS meslek_grubu_ai_etkisi (
    id SERIAL PRIMARY KEY,
    isco_kodu VARCHAR(2) NOT NULL,
    duzey VARCHAR NOT NULL DEFAULT 'belirsiz' CHECK (duzey IN ('dusuk', 'orta', 'yuksek', 'belirsiz')),
    puan NUMERIC(6,3),
    aciklama TEXT,
    kaynak VARCHAR NOT NULL,
    kaynak_bolum VARCHAR,
    veri_yili INTEGER NOT NULL,
    dagilim JSONB NOT NULL DEFAULT '{}',
    meslekler JSONB NOT NULL DEFAULT '[]',
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now(),
    guncelleme TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (isco_kodu, veri_yili)
)
"""

_T = _tohum()
if _T:
    SQL = SQL.rstrip() + ";\n" + _T + "\n"


def upgrade():
    op.execute(SQL)


def downgrade():
    op.execute("DROP TABLE IF EXISTS meslek_grubu_ai_etkisi")
