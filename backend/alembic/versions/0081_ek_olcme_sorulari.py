"""[2026-10-19] K1-K4'e ek ölçme soruları ve dikkat (kontrol) soruları — YALNIZCA EKLEME

Revision ID: 0081_ek_olcme_sorulari
Revises: 0080_kocluk_cekirdek

Ne yapar:
  * app/data/olcme_sorulari_ek.json'daki soruları mevcut 60 sorunun YANINA ekler (16 en çok/en az + katman başına
    2 dikkat sorusu). Hiçbir soru, cevap ya da değerlendirme turu silinmez; yarıda kalan katman oturumları kendi
    kilitli soru listesiyle devam eder, yeni sorular yeni başlatılan katmanlarda görünür.
  * Tekrar çalıştırılabilir (sema_guncelleme her açılışta çalıştırır): tek_seferlik_gocler işareti varsa hiçbir şey
    yapmaz; işaret yoksa da aynı katmanda aynı metinli soru zaten varsa o soruyu atlar (çift kayıt olmaz).
  * Boş kurulumda (katman / değişken yoksa) hiçbir şey yapmaz ve işaret yazmaz.
  * Admin bir ek soruyu pasife alırsa işaret sayesinde bir sonraki açılışta yeniden eklenmez.
"""
import json
import re
from pathlib import Path

from alembic import op

revision = "0081_ek_olcme_sorulari"
down_revision = "0080_kocluk_cekirdek"
branch_labels = None
depends_on = None

_VERI = Path(__file__).resolve().parents[2] / "app" / "data"

def _json_literal(veri) -> str:
    """0076 ile aynı güvenli gömme: tek satır JSON ($j$…$j$); ";\\n" ve ':kelime' (text() parametresi sanılır) olmamalı."""
    s = json.dumps(veri, ensure_ascii=False, separators=(", ", ": "))
    assert "\n" not in s and "$j$" not in s, "JSON tek satır olmalı"
    assert not re.search(r"(?<![:\w]):\w", s), "metinde ':kelime' kalıbı var"
    return "$j$" + s + "$j$"


_SQL = """
DO $$
DECLARE d jsonb := __SORULAR__::jsonb;
DECLARE q record;
DECLARE o record;
DECLARE kid int;
DECLARE va int;
DECLARE sid int;
DECLARE secid int;
BEGIN
  IF EXISTS (SELECT 1 FROM tek_seferlik_gocler WHERE ad = '0081_ek_sorular___SURUM__') THEN RETURN; END IF;
  IF NOT EXISTS (SELECT 1 FROM katmanlar WHERE kod = 'K1') OR NOT EXISTS (SELECT 1 FROM degiskenler) THEN RETURN; END IF;
  FOR q IN SELECT value AS v FROM jsonb_array_elements(d) LOOP
    SELECT id INTO kid FROM katmanlar WHERE kod = q.v->>'katman';
    IF kid IS NULL THEN RAISE EXCEPTION 'katman yok %', q.v->>'katman'; END IF;
    CONTINUE WHEN EXISTS (SELECT 1 FROM sorular WHERE katman_id = kid AND ogrenci_id IS NULL AND soru_metni = q.v->>'metin');
    IF q.v->>'tip' = 'kontrol' THEN
      INSERT INTO sorular (katman_id, soru_tipi, soru_metni, ters_kodlanmis_mi, aktif_mi, cevap_bicimi, olusturulma_zamani,
                           beklenen_secenek_sira)
      VALUES (kid, 'kontrol', q.v->>'metin', false, true, 'tek', now(), (q.v->>'beklenen')::int) RETURNING id INTO sid;
      INSERT INTO soru_secenekleri (soru_id, secenek_sirasi, secenek_metni)
      SELECT sid, ordinality::int, value #>> '{}' FROM jsonb_array_elements(q.v->'secenekler') WITH ORDINALITY;
    ELSE
      INSERT INTO sorular (katman_id, soru_tipi, soru_metni, ters_kodlanmis_mi, aktif_mi, cevap_bicimi, olusturulma_zamani)
      VALUES (kid, 'sjt', q.v->>'metin', false, true, CASE WHEN q.v->>'tip' = 'encok' THEN 'encok_enaz' ELSE 'tek' END, now())
      RETURNING id INTO sid;
      FOR o IN SELECT value AS s, ordinality::int AS i FROM jsonb_array_elements(q.v->'secenekler') WITH ORDINALITY LOOP
        SELECT id INTO va FROM degiskenler WHERE kod = o.s->>'degisken' AND dal_id IS NULL;
        IF va IS NULL THEN RAISE EXCEPTION 'seçenek değişkeni yok %', o.s->>'degisken'; END IF;
        INSERT INTO soru_secenekleri (soru_id, secenek_sirasi, secenek_metni) VALUES (sid, o.i, o.s->>'metin') RETURNING id INTO secid;
        INSERT INTO sjt_secenek_degisken_agirlik (secenek_id, degisken_id, agirlik) VALUES (secid, va, 1);
      END LOOP;
    END IF;
  END LOOP;
  INSERT INTO tek_seferlik_gocler (ad) VALUES ('0081_ek_sorular___SURUM__') ON CONFLICT (ad) DO NOTHING;
END
$$;
"""


def sql_uret() -> str:
    veri = json.loads((_VERI / "olcme_sorulari_ek.json").read_text(encoding="utf-8"))
    govde = (_SQL.replace("__SORULAR__", _json_literal(veri["sorular"]))
             .replace("__SURUM__", str(veri["surum"]).replace("'", "")))
    isaret = ("CREATE TABLE IF NOT EXISTS tek_seferlik_gocler (ad VARCHAR PRIMARY KEY, "
              "uygulanma_zamani TIMESTAMPTZ NOT NULL DEFAULT now());\n")
    # DO bloğu tek komut kalsın (sema_guncelleme komutları ";\n" ile böler)
    return isaret + govde.strip().replace(";\n", "; \n") + ";\n"


SQL = sql_uret()


def upgrade() -> None:
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade() -> None:
    pass   # eklenen sorular admin panelinden pasife alınabilir; silme yapılmaz (verilmiş cevaplar korunur)
