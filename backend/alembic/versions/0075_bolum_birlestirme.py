"""bolum_birlestirme — profili ayırt edilemeyen 21 bölüm grubunu tek bölümde birleştirir (23 bölüm silinir)

Revision ID: 0075_bolum_birlestirme
Revises: 0074_haftalik_yansitma_metni
Create Date: 2026-10-18

[2026-10-18] Analiz (iki bağımsız profil kaynağında r ≥ 0,95 + kullanıcı kararı) sonucu birbirinin aynısı olan bölümler
tek bölümde toplanır. Her grupta İLK ad kalır (ana bölüm); diğerleri tamamen silinir (ad hiçbir yerde görünmez).
  1) Ana bölümün bolum_agirliklari değerleri = grup üyelerinin ortalaması (aynı değişken + sürüm için).
  2) Üye bölümlere bağlı tüm satırlar silinir. Bağlantı NULL olabiliyorsa NULL yapılır (ör. hedef_bolum_id);
     olamıyorsa satır silinir (bağlı alt tablolar dahil, yabancı anahtar grafiği izlenerek). Ardından üye bölüm silinir.
İdempotent: üye bölümler artık yoksa hiçbir şey yapmaz (ortalama tekrar alınmaz).
app/core/sema_guncelleme.py OTOMATIK listesinde (sunucu açılışında bir kez uygulanır).
"""
from alembic import op

revision = "0075_bolum_birlestirme"
down_revision = "0074_haftalik_yansitma_metni"
branch_labels = None
depends_on = None

# Her satır: ana bölüm | silinecek üyeler
GRUPLAR = [
    "FİNANS VE BANKACILIK|BANKACILIK VE FİNANS",
    "EKONOMİ|İKTİSAT",
    "SİBER GÜVENLİK MÜHENDİSLİĞİ|BİLGİ GÜVENLİĞİ MÜHENDİSLİĞİ",
    "SİYASET BİLİMİ VE ULUSLARARASI İLİŞKİLER|KÜRESEL SİYASET VE ULUSLARARASI İLİŞKİLER",
    "SERAMİK VE CAM|CAM",
    "YAPAY ZEKA MÜHENDİSLİĞİ|YAPAY ZEKA VE MAKİNE ÖĞRENMESİ|YAPAY ZEKA VE VERİ MÜHENDİSLİĞİ",
    "HAVACILIK VE UZAY MÜHENDİSLİĞİ|UÇAK MÜHENDİSLİĞİ|UZAY MÜHENDİSLİĞİ",
    "NANOTEKNOLOJİ MÜHENDİSLİĞİ|MALZEME BİLİMİ VE NANOTEKNOLOJİ MÜHENDİSLİĞİ",
    "RESİM ÖĞRETMENLİĞİ|GÖRSEL SANATLAR ÖĞRETMENLİĞİ",
    "REHBERLİK VE PSİKOLOJİK DANIŞMANLIK|PSİKOLOJİK DANIŞMANLIK VE REHBERLİK ÖĞRETMENLİĞİ",
    "TURİZM VE KONAKLAMA İŞLETMECİLİĞİ|OTEL YÖNETİCİLİĞİ",
    "TİYATRO|SAHNE SANATLARI",
    "TÜRK HALKBİLİMİ|HALKBİLİMİ",
    "OYUNCULUK|DRAMA VE OYUNCULUK",
    "GİRİŞİMCİLİK|ULUSLARARASI GİRİŞİMCİLİK",
    "HAT SANATI|TEZHİP-MİNYATÜR VE EBRU",
    "MATEMATİK VE BİLGİSAYAR BİLİMLERİ|BİLGİSAYAR BİLİMLERİ",
    "AKTÜERYA BİLİMLERİ|SİGORTACILIK VE AKTÜERYA BİLİMLERİ",
    "PAZARLAMA|PAZARLAMA İLETİŞİMİ",
    "MATEMATİK ÖĞRETMENLİĞİ|İLKÖĞRETİM MATEMATİK ÖĞRETMENLİĞİ",
    "BİYOTEKNOLOJİ|MOLEKÜLER BİYOTEKNOLOJİ",
]
SILINEN_ADLAR = [ad for g in GRUPLAR for ad in g.split("|")[1:]]

# Yabancı anahtar grafiğini izleyerek siler (NULL olabilen bağlantıyı NULL yapar).
_SIL_FONKSIYONU = """
CREATE OR REPLACE FUNCTION pg_temp.bb_sil(t regclass, kosul text) RETURNS void LANGUAGE plpgsql AS $$
DECLARE c record;
DECLARE alt_kosul text;
BEGIN
  FOR c IN
    SELECT con.conrelid::regclass AS cocuk,
           (SELECT string_agg(quote_ident(a.attname), ',' ORDER BY k.n) FROM unnest(con.conkey) WITH ORDINALITY k(att, n)
              JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.att) AS ccols,
           (SELECT string_agg(quote_ident(a.attname), ',' ORDER BY k.n) FROM unnest(con.confkey) WITH ORDINALITY k(att, n)
              JOIN pg_attribute a ON a.attrelid = con.confrelid AND a.attnum = k.att) AS pcols,
           (SELECT bool_and(NOT a.attnotnull) FROM unnest(con.conkey) k(att)
              JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.att) AS bos_olabilir,
           (SELECT string_agg(quote_ident(a.attname) || ' = NULL', ', ') FROM unnest(con.conkey) k(att)
              JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.att) AS null_yap
      FROM pg_constraint con
     WHERE con.contype = 'f' AND con.confrelid = t AND con.conrelid <> t
  LOOP
    alt_kosul := format('(%s) IN (SELECT %s FROM %s WHERE %s)', c.ccols, c.pcols, t, kosul);
    IF c.bos_olabilir THEN
      EXECUTE format('UPDATE %s SET %s WHERE %s', c.cocuk, c.null_yap, alt_kosul);
    ELSE
      PERFORM pg_temp.bb_sil(c.cocuk, alt_kosul);
    END IF;
  END LOOP;
  EXECUTE format('DELETE FROM %s WHERE %s', t, kosul);
END
$$
"""

_BIRLESTIR_KALIP = """
DO $$
DECLARE s text;
DECLARE g text[];
DECLARE ana int;
DECLARE uyeler int[];
BEGIN
  FOREACH s IN ARRAY ARRAY[__GRUPLAR__]::text[] LOOP
    g := string_to_array(s, '|');
    SELECT id INTO ana FROM bolumler WHERE ad = g[1];
    uyeler := ARRAY(SELECT id FROM bolumler WHERE ad = ANY(g[2:cardinality(g)]));
    IF ana IS NULL OR cardinality(uyeler) = 0 THEN
      CONTINUE;
    END IF;
    UPDATE bolum_agirliklari a
       SET agirlik_degeri = o.ort_a, yakinsama_skoru = o.ort_y, agirlikli_varyans = o.ort_v, etkin_meslek_sayisi = o.en_e
      FROM (SELECT degisken_id, versiyon,
                   round(avg(agirlik_degeri), 2) AS ort_a, round(avg(yakinsama_skoru), 4) AS ort_y,
                   round(avg(agirlikli_varyans), 4) AS ort_v, max(etkin_meslek_sayisi) AS en_e
              FROM bolum_agirliklari WHERE bolum_id = ANY(ana || uyeler) GROUP BY degisken_id, versiyon) o
     WHERE a.bolum_id = ana AND a.degisken_id = o.degisken_id AND a.versiyon = o.versiyon;
    PERFORM pg_temp.bb_sil('bolumler'::regclass, format('id = ANY(%L::int[])', uyeler));
  END LOOP;
END
$$
"""


def sql_uret(gruplar: list[str]) -> str:
    """sema_guncelleme ";\\n" ile böler: fonksiyon/blok gövdesindeki satır sonları bölünmeyecek hale getirilir."""
    blok = _BIRLESTIR_KALIP.replace("__GRUPLAR__", ", ".join("'" + g.replace("'", "''") + "'" for g in gruplar))
    return _SIL_FONKSIYONU.strip().replace(";\n", "; \n") + ";\n" + blok.strip().replace(";\n", "; \n") + ";\n"


SQL = sql_uret(GRUPLAR)


def upgrade() -> None:
    for komut in SQL.split(";\n"):
        if komut.strip():
            op.execute(komut)


def downgrade() -> None:
    pass   # silinen bölümler geri getirilmez (kullanıcı kararı)
