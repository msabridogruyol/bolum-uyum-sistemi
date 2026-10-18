"""[2026-10-18] Yeni ölçme soruları (K1-K4) ve yeni K5 (iş türü kapıştırma)

Revision ID: 0076_yeni_k5_sorular
Revises: 0075_bolum_birlestirme

Ne yapar (hepsi tekrar çalıştırılabilir; sema_guncelleme her açılışta çalıştırır):
  1. sorular: ogrenci_id / tur_id (öğrenciye özel üretilen K5 soruları), uc_a_metni / uc_b_metni (uçlar sorusu).
  2. Seçenek ve seçenek-ağırlık bağları ON DELETE CASCADE: öğrenciye özel sorular tur / öğrenci silinince temizlenir.
  3. k5_cumleleri (iş türü başına etkinlik cümleleri) ve k5_soru_kokleri tabloları; tek K5 adımı için dal 'K5N'.
  4. K5 soru bankası app/data/k5_soru_bankasi.json'dan yüklenir (listede olmayan cümle / kök pasife alınır) — yalnızca
     dosyadaki "surum" sistem_parametreleri 'k5_banka_surumu'ndan farklıysa (admin düzeltmeleri her açılışta ezilmez).
  5. TEK SEFERLİK (sistem_parametreleri 'olcme_soru_seti' = SORU_SETI değilse): eski K1-K5 soru bankası ve tüm
     değerlendirme turları silinir, app/data/olcme_sorulari.json'daki 60 yeni K1-K4 sorusu eklenir. Kullanıcı kararı
     (2026-10-18): "eskileri komple silip yeni sorular olarak ekleyeceğiz… canlıya almadık henüz". Eski sorulara
     verilmiş cevaplar yeni puanlamayla anlamsız olacağından turlar da silinir (öğrenciler baştan başlar).
     Tamamı tek DO bloğunda = tek işlem: yarıda kalırsa hiçbir şey değişmez.
"""
import json
import re
from pathlib import Path

from alembic import op

revision = "0076_yeni_k5_sorular"
down_revision = "0075_bolum_birlestirme"
branch_labels = None
depends_on = None

SORU_SETI = "2026-10-18"
_VERI = Path(__file__).resolve().parents[2] / "app" / "data"


def _json_literal(veri) -> str:
    """JSON'u $j$…$j$ ile SQL'e gömer. sema_guncelleme komutları ";\\n" ile böler ve SQLAlchemy text() ':ad' biçimini
    parametre sanar: ikisi de metinde olmamalı (tek satırlık döküm + kontrol)."""
    s = json.dumps(veri, ensure_ascii=False, separators=(", ", ": "))
    assert "\n" not in s and "$j$" not in s, "JSON tek satır olmalı"
    assert not re.search(r"(?<![:\w]):\w", s), "metinde ':kelime' kalıbı var (text() parametresi sanılır)"
    return "$j$" + s + "$j$"


_SEMA = """
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS ogrenci_id uuid;
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS tur_id bigint;
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS uc_a_metni varchar;
ALTER TABLE sorular ADD COLUMN IF NOT EXISTS uc_b_metni varchar;
CREATE INDEX IF NOT EXISTS ix_sorular_ogrenci_tur ON sorular (ogrenci_id, tur_id) WHERE ogrenci_id IS NOT NULL;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'sorular_ogrenci_id_fkey') THEN
    ALTER TABLE sorular ADD CONSTRAINT sorular_ogrenci_id_fkey FOREIGN KEY (ogrenci_id) REFERENCES ogrenciler(id) ON DELETE CASCADE; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'sorular_tur_id_fkey') THEN
    ALTER TABLE sorular ADD CONSTRAINT sorular_tur_id_fkey FOREIGN KEY (tur_id) REFERENCES ogrenci_degerlendirme_turu(id) ON DELETE CASCADE; END IF;
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'soru_secenekleri_soru_id_fkey' AND confdeltype <> 'c') THEN
    ALTER TABLE soru_secenekleri DROP CONSTRAINT soru_secenekleri_soru_id_fkey; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'soru_secenekleri_soru_id_fkey') THEN
    ALTER TABLE soru_secenekleri ADD CONSTRAINT soru_secenekleri_soru_id_fkey FOREIGN KEY (soru_id) REFERENCES sorular(id) ON DELETE CASCADE; END IF;
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'sjt_secenek_degisken_agirlik_secenek_id_fkey' AND confdeltype <> 'c') THEN
    ALTER TABLE sjt_secenek_degisken_agirlik DROP CONSTRAINT sjt_secenek_degisken_agirlik_secenek_id_fkey; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'sjt_secenek_degisken_agirlik_secenek_id_fkey') THEN
    ALTER TABLE sjt_secenek_degisken_agirlik ADD CONSTRAINT sjt_secenek_degisken_agirlik_secenek_id_fkey FOREIGN KEY (secenek_id) REFERENCES soru_secenekleri(id) ON DELETE CASCADE; END IF;
END $$;
CREATE TABLE IF NOT EXISTS k5_cumleleri (
  id serial PRIMARY KEY,
  degisken_id integer NOT NULL REFERENCES degiskenler(id),
  sira integer NOT NULL,
  metin varchar NOT NULL,
  aktif_mi boolean NOT NULL DEFAULT true,
  CONSTRAINT uq_k5c_degisken_sira UNIQUE (degisken_id, sira)
);
CREATE TABLE IF NOT EXISTS k5_soru_kokleri (
  id serial PRIMARY KEY,
  tip varchar NOT NULL,
  metin varchar NOT NULL,
  aktif_mi boolean NOT NULL DEFAULT true,
  CONSTRAINT ck_k5k_tip CHECK (tip IN ('encok','tek','kutup')),
  CONSTRAINT uq_k5k_tip_metin UNIQUE (tip, metin)
);
INSERT INTO dallar (kod, ad, dogrulama_durumu, olusturulma_zamani)
VALUES ('K5N', 'İş türü tercihleri', 'taslak', now()) ON CONFLICT (kod) DO NOTHING;
"""

_BANKA = """
DO $$
DECLARE b jsonb := __BANKA__::jsonb;
DECLARE e record;
DECLARE c record;
DECLARE k record;
DECLARE vid int;
BEGIN
  IF EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'k5_banka_surumu' AND deger = '__BSURUM__') THEN
    RETURN;
  END IF;
  FOR e IN SELECT key, value FROM jsonb_each(b->'cumleler') LOOP
    SELECT id INTO vid FROM degiskenler WHERE kod = e.key;
    IF vid IS NULL THEN RAISE EXCEPTION 'K5 bankası: değişken yok %', e.key; END IF;
    FOR c IN SELECT value #>> '{}' AS metin, ordinality::int AS sira FROM jsonb_array_elements(e.value) WITH ORDINALITY LOOP
      INSERT INTO k5_cumleleri (degisken_id, sira, metin, aktif_mi) VALUES (vid, c.sira, c.metin, true)
      ON CONFLICT (degisken_id, sira) DO UPDATE SET metin = EXCLUDED.metin, aktif_mi = true;
    END LOOP;
    UPDATE k5_cumleleri SET aktif_mi = false WHERE degisken_id = vid AND sira > jsonb_array_length(e.value);
  END LOOP;
  UPDATE k5_cumleleri SET aktif_mi = false
   WHERE degisken_id NOT IN (SELECT v.id FROM degiskenler v WHERE v.kod IN (SELECT jsonb_object_keys(b->'cumleler')));
  FOR k IN SELECT t.key AS tip, m.value #>> '{}' AS metin FROM jsonb_each(b->'kokler') t, jsonb_array_elements(t.value) m LOOP
    INSERT INTO k5_soru_kokleri (tip, metin, aktif_mi) VALUES (k.tip, k.metin, true)
    ON CONFLICT (tip, metin) DO UPDATE SET aktif_mi = true;
  END LOOP;
  UPDATE k5_soru_kokleri s SET aktif_mi = false WHERE NOT EXISTS (
    SELECT 1 FROM jsonb_each(b->'kokler') t, jsonb_array_elements(t.value) m WHERE t.key = s.tip AND m.value #>> '{}' = s.metin);
  INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
  VALUES ('k5_banka_surumu', '__BSURUM__', 'Yüklü K5 soru bankası sürümü (app/data/k5_soru_bankasi.json)', now())
  ON CONFLICT (anahtar) DO UPDATE SET deger = EXCLUDED.deger, guncelleme_zamani = now();
END
$$;
"""

_SORULAR = """
DO $$
DECLARE d jsonb := __SORULAR__::jsonb;
DECLARE q record;
DECLARE o record;
DECLARE kid int;
DECLARE va int;
DECLARE vb int;
DECLARE sid int;
DECLARE secid int;
DECLARE eski int[];
BEGIN
  IF EXISTS (SELECT 1 FROM sistem_parametreleri WHERE anahtar = 'olcme_soru_seti' AND deger = '__SURUM__') THEN
    RETURN;
  END IF;
  DELETE FROM ogrenci_degerlendirme_turu;
  eski := ARRAY(SELECT s.id FROM sorular s JOIN katmanlar k ON k.id = s.katman_id
                 WHERE k.kod IN ('K1','K2','K3','K4','K5'));
  DELETE FROM ogrenci_cevaplar WHERE soru_id = ANY(eski);
  DELETE FROM gecerlilik_ozet WHERE soru_id = ANY(eski);
  DELETE FROM gecerlilik_sonuclari WHERE soru_id = ANY(eski);
  DELETE FROM sjt_secenek_degisken_agirlik WHERE secenek_id IN (SELECT id FROM soru_secenekleri WHERE soru_id = ANY(eski));
  DELETE FROM soru_secenekleri WHERE soru_id = ANY(eski);
  DELETE FROM sorular WHERE id = ANY(eski);
  FOR q IN SELECT value AS v FROM jsonb_array_elements(d) LOOP
    SELECT id INTO kid FROM katmanlar WHERE kod = q.v->>'katman';
    IF kid IS NULL THEN RAISE EXCEPTION 'katman yok %', q.v->>'katman'; END IF;
    IF q.v->>'tip' = 'kutup' THEN
      SELECT id INTO va FROM degiskenler WHERE kod = q.v->>'a';
      SELECT id INTO vb FROM degiskenler WHERE kod = q.v->>'b';
      IF va IS NULL OR vb IS NULL THEN RAISE EXCEPTION 'kutup değişkeni yok %', q.v->>'metin'; END IF;
      INSERT INTO sorular (katman_id, degisken_id, b_ucu_degisken_id, soru_tipi, soru_metni, ters_kodlanmis_mi, aktif_mi,
                           cevap_bicimi, olusturulma_zamani, uc_a_metni, uc_b_metni)
      VALUES (kid, va, vb, 'kutup', q.v->>'metin', false, true, 'tek', now(), q.v->>'uc_a', q.v->>'uc_b') RETURNING id INTO sid;
      INSERT INTO soru_secenekleri (soru_id, secenek_sirasi, secenek_metni)
      SELECT sid, i, x FROM unnest(ARRAY[__KUTUP__]::text[]) WITH ORDINALITY u(x, i);
    ELSE
      INSERT INTO sorular (katman_id, soru_tipi, soru_metni, ters_kodlanmis_mi, aktif_mi, cevap_bicimi, olusturulma_zamani)
      VALUES (kid, 'sjt', q.v->>'metin', false, true, CASE WHEN q.v->>'tip' = 'encok' THEN 'encok_enaz' ELSE 'tek' END, now())
      RETURNING id INTO sid;
      FOR o IN SELECT value AS s, ordinality::int AS i FROM jsonb_array_elements(q.v->'secenekler') WITH ORDINALITY LOOP
        SELECT id INTO va FROM degiskenler WHERE kod = o.s->>'degisken';
        IF va IS NULL THEN RAISE EXCEPTION 'seçenek değişkeni yok %', o.s->>'degisken'; END IF;
        INSERT INTO soru_secenekleri (soru_id, secenek_sirasi, secenek_metni) VALUES (sid, o.i, o.s->>'metin') RETURNING id INTO secid;
        INSERT INTO sjt_secenek_degisken_agirlik (secenek_id, degisken_id, agirlik) VALUES (secid, va, 1);
      END LOOP;
    END IF;
  END LOOP;
  INSERT INTO sistem_parametreleri (anahtar, deger, aciklama, guncelleme_zamani)
  VALUES ('olcme_soru_seti', '__SURUM__', 'Yüklü K1-K4 soru seti (0076_yeni_k5_sorular)', now())
  ON CONFLICT (anahtar) DO UPDATE SET deger = EXCLUDED.deger, guncelleme_zamani = now();
END
$$;
"""


def sql_uret() -> str:
    from app.core.dal_servisi import KUTUP_SECENEKLERI  # noqa: E402  (tek kaynak: puanlama sırası buna bağlı)
    banka = json.loads((_VERI / "k5_soru_bankasi.json").read_text(encoding="utf-8"))
    sorular = json.loads((_VERI / "olcme_sorulari.json").read_text(encoding="utf-8"))
    # Banka yalnızca sürümü değişince yeniden yüklenir: admin ekranından yapılan metin düzeltmeleri her açılışta ezilmesin
    banka_sql = (_BANKA.replace("__BANKA__", _json_literal({"cumleler": banka["cumleler"], "kokler": banka["kokler"]}))
                 .replace("__BSURUM__", str(banka["surum"]).replace("'", "")))
    soru_sql = (_SORULAR.replace("__SORULAR__", _json_literal(sorular["sorular"])).replace("__SURUM__", SORU_SETI)
                .replace("__KUTUP__", ", ".join("'" + s.replace("'", "''") + "'" for s in KUTUP_SECENEKLERI)))
    # DO blokları içindeki ";\n" bölünmesin (sema_guncelleme komutları ";\n" ile ayırır)
    bloklar = [banka_sql, soru_sql]
    return _SEMA.strip() + "\n" + "".join(b.strip().replace(";\n", "; \n") + ";\n" for b in bloklar)


def _sema_bloklari_tek_satir() -> str:
    # _SEMA içindeki DO bloğu da tek komut olmalı
    bas, do, son = _SEMA.partition("DO $$")
    govde, ayrac, kalan = son.partition("END $$;\n")
    return bas + do + govde.replace(";\n", "; \n") + ayrac + kalan


_SEMA = _sema_bloklari_tek_satir()
SQL = sql_uret()


def upgrade() -> None:
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade() -> None:
    pass   # eski soru bankası geri getirilmez (kullanıcı kararı)
