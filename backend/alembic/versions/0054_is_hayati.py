"""İş Hayatı modülü: istihdam göstergeleri, kazanç (meslek grubu), meslek→ISCO, kamu maaşları, asgari ücret, yaşam giderleri

Revision ID: 0054_is_hayati
Revises: 0053_sayfa_ziyaretleri
Create Date: 2026-10-10

Not: app/core/sema_guncelleme.py bu SQL'i HER sunucu açılışında yeniden çalıştırır; tüm komutlar idempotenttir.
- Tablolar IF NOT EXISTS.
- meslek_isco tohumu app/data/meslek_isco.json'dan üretilir ve ON CONFLICT DO NOTHING ile eklenir: süper adminin
  düzelttiği satırlar ezilmez; JSON'a sonradan eklenen meslekler bir sonraki açılışta gelir.
- Paket güncellemesi ve asgari ücret tohumu tek seferliktir (tek_seferlik_gocler işareti, bkz. 0052): süper admin
  modülü paketten çıkarırsa ya da bir asgari ücret satırını silerse açılışta geri gelmez.
- Asgari ücret tutarları (brüt / net, 16 yaş üstü, aylık):
    2022-1, 2022-2, 2025: ÇSGB Çalışma Genel Müdürlüğü, "Yıllar İtibarıyla Net ve Brüt Asgari Ücretler" tablosu.
    2026: Asgari Ücret Tespit Komisyonu kararı, Resmî Gazete 26.12.2025 / 33119 (KPMG, TÜRMOB, CottGroup ile doğrulandı).
"""
import json
from pathlib import Path

from alembic import op

revision = "0054_is_hayati"
down_revision = "0053_sayfa_ziyaretleri"
branch_labels = None
depends_on = None

_JSON = Path(__file__).resolve().parents[2] / "app" / "data" / "meslek_isco.json"


def _q(s) -> str:
    return "NULL" if s is None else "'" + str(s).replace("'", "''") + "'"


def _meslek_isco_tohumu() -> str:
    try:
        veri = json.loads(_JSON.read_text(encoding="utf-8"))["eslesme"]
    except Exception:
        return ""
    satirlar = [f"({_q(ad)}, {_q(v.get('isco_kodu'))}, {_q(v.get('guven'))}, 'otomatik')"
                for ad, v in veri.items() if ad and ":" not in ad and "%" not in ad]
    if not satirlar:
        return ""
    return ("INSERT INTO meslek_isco (meslek_adi, isco_kodu, guven, kaynak) VALUES\n" + ",\n".join(satirlar)
            + "\nON CONFLICT (meslek_adi) DO NOTHING")


SQL = """
CREATE TABLE IF NOT EXISTS tek_seferlik_gocler (
    ad VARCHAR PRIMARY KEY,
    uygulanma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS veri_yuklemeleri (
    id SERIAL PRIMARY KEY,
    tur VARCHAR NOT NULL,
    dosya_adi VARCHAR,
    satir INTEGER NOT NULL DEFAULT 0,
    eslesen INTEGER NOT NULL DEFAULT 0,
    eslesmeyen JSONB NOT NULL DEFAULT '[]',
    veri_yili INTEGER,
    kaynak VARCHAR,
    yukleyen VARCHAR,
    zaman TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS istihdam_gostergeleri (
    id SERIAL PRIMARY KEY,
    bolum_id INTEGER REFERENCES bolumler(id) ON DELETE SET NULL,
    program_adi_kaynak VARCHAR NOT NULL,
    duzey VARCHAR CHECK (duzey IS NULL OR duzey IN ('lisans', 'onlisans')),
    istihdam_orani NUMERIC(5,2),
    is_bulma_suresi_ay NUMERIC(5,2),
    alan_uyum_orani NUMERIC(5,2),
    kazanc_grubu VARCHAR CHECK (kazanc_grubu IS NULL OR kazanc_grubu IN ('cok_yuksek', 'yuksek', 'orta', 'dusuk', 'cok_dusuk')),
    kazanc_tl NUMERIC(12,2),
    veri_yili INTEGER NOT NULL,
    kaynak VARCHAR NOT NULL,
    yukleme_id INTEGER REFERENCES veri_yuklemeleri(id) ON DELETE CASCADE,
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_istihdam_bolum_yil ON istihdam_gostergeleri (bolum_id, veri_yili DESC);
CREATE TABLE IF NOT EXISTS kazanc_meslek_gruplari (
    id SERIAL PRIMARY KEY,
    isco_kodu VARCHAR(2) NOT NULL CHECK (isco_kodu ~ '^[0-9]{1,2}$'),
    ad VARCHAR NOT NULL,
    brut_aylik_ortalama_tl NUMERIC(12,2) NOT NULL,
    veri_yili INTEGER NOT NULL,
    asgari_brut_o_yil NUMERIC(12,2) NOT NULL CHECK (asgari_brut_o_yil > 0),
    kaynak VARCHAR NOT NULL,
    yukleme_id INTEGER REFERENCES veri_yuklemeleri(id) ON DELETE SET NULL,
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (isco_kodu, veri_yili)
);
CREATE TABLE IF NOT EXISTS meslek_isco (
    meslek_adi VARCHAR PRIMARY KEY,
    isco_kodu VARCHAR(2) CHECK (isco_kodu IS NULL OR isco_kodu ~ '^[0-9]{1,2}$'),
    guven VARCHAR CHECK (guven IS NULL OR guven IN ('yuksek', 'orta')),
    kaynak VARCHAR NOT NULL DEFAULT 'otomatik',
    guncelleyen VARCHAR,
    guncelleme TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS kamu_maaslari (
    id SERIAL PRIMARY KEY,
    kadro_adi VARCHAR NOT NULL,
    anahtar_kelimeler JSONB NOT NULL DEFAULT '[]',
    net_min NUMERIC(12,2),
    net_max NUMERIC(12,2),
    donem VARCHAR NOT NULL,
    kaynak VARCHAR NOT NULL,
    aciklama TEXT,
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now(),
    guncelleme TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS asgari_ucret (
    id SERIAL PRIMARY KEY,
    donem VARCHAR NOT NULL UNIQUE,
    brut NUMERIC(12,2) NOT NULL CHECK (brut > 0),
    net NUMERIC(12,2) NOT NULL CHECK (net > 0),
    kaynak VARCHAR NOT NULL,
    yururluk_tarihi DATE NOT NULL,
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS yasam_giderleri (
    id SERIAL PRIMARY KEY,
    il VARCHAR,
    kalem_kodu VARCHAR NOT NULL,
    ad VARCHAR NOT NULL,
    aylik_tutar NUMERIC(12,2) NOT NULL CHECK (aylik_tutar >= 0),
    kaynak VARCHAR NOT NULL,
    tarih DATE NOT NULL,
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_yasam_giderleri_il_kalem ON yasam_giderleri ((COALESCE(il, '')), kalem_kodu);
WITH isaret AS (
    INSERT INTO tek_seferlik_gocler (ad) VALUES ('0054_is_hayati_paket')
    ON CONFLICT (ad) DO NOTHING
    RETURNING ad
)
UPDATE paketler SET moduller = moduller || '["is_hayati"]'::jsonb
 WHERE kod = 'tam' AND NOT moduller ? 'is_hayati' AND EXISTS (SELECT 1 FROM isaret);
WITH isaret AS (
    INSERT INTO tek_seferlik_gocler (ad) VALUES ('0054_is_hayati_asgari_ucret')
    ON CONFLICT (ad) DO NOTHING
    RETURNING ad
)
INSERT INTO asgari_ucret (donem, brut, net, kaynak, yururluk_tarihi)
SELECT v.donem, v.brut, v.net, v.kaynak, v.yururluk FROM (VALUES
  ('2022-1', 5004.00, 4253.40, 'ÇSGB Çalışma Genel Müdürlüğü — Yıllar İtibarıyla Net ve Brüt Asgari Ücretler (01.01.2022–30.06.2022)', DATE '2022-01-01'),
  ('2022-2', 6471.00, 5500.35, 'ÇSGB Çalışma Genel Müdürlüğü — Yıllar İtibarıyla Net ve Brüt Asgari Ücretler (01.07.2022–31.12.2022); Resmî Gazete 01.07.2022 / 31883 mükerrer', DATE '2022-07-01'),
  ('2025', 26005.50, 22104.67, 'ÇSGB Çalışma Genel Müdürlüğü — Yıllar İtibarıyla Net ve Brüt Asgari Ücretler (2025); Asgari Ücret Tespit Komisyonu 24.12.2024 tarih 2024/1 sayılı karar', DATE '2025-01-01'),
  ('2026', 33030.00, 28075.50, 'Asgari Ücret Tespit Komisyonu kararı — Resmî Gazete 26.12.2025 / 33119 (günlük brüt 1.101,00 TL)', DATE '2026-01-01')
) AS v(donem, brut, net, kaynak, yururluk)
WHERE EXISTS (SELECT 1 FROM isaret)
ON CONFLICT (donem) DO NOTHING
"""

_TOHUM = _meslek_isco_tohumu()
if _TOHUM:
    SQL = SQL.rstrip() + ";\n" + _TOHUM + "\n"


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
