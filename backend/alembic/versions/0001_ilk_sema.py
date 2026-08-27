"""İlk şema — 33 tablo (schema.sql ile birebir aynı, tek doğruluk kaynağı)

Revision ID: 0001_ilk_sema
Revises:
Create Date: 2026-08-12
"""
from alembic import op

revision = "0001_ilk_sema"
down_revision = None
branch_labels = None
depends_on = None

_DDL = r"""
-- ============================================================================
-- Bölüm-Öğrenci Uyum Sistemi — Konsolide Veritabanı Şeması
-- ============================================================================
-- Bu dosya, üç kaynak belgede (sistem_genel_anlatim.md, veritabani_taslagi.md,
-- koclugu_karsilastirma_modulu.md) dağınık halde geçen tüm tablo/kolon
-- tanımlarını TEK bir tutarlı şemada toplar.
--
-- ÖNEMLİ NOT (okumadan geçmeyin): Kaynak belgelerde birçok tablo yalnızca
-- İSİM olarak anılıyordu (örn. B) Veritabanı tablosundaki "ogrenciler",
-- "bolumler", "degiskenler" vb.) — tam CREATE TABLE tanımı hiçbir belgede
-- yoktu, yalnızca birkaç ALTER TABLE eklentisi vardı. Bu dosyada o temel
-- tabloların TAM tanımı ilk kez yapılıyor; kolon adları/tipleri belgelerdeki
-- anlatımdan çıkarım yoluyla belirlendi. Bu tür satırlar "-- [ÇIKARIM]"
-- yorumuyla işaretlendi — ekip tarafından gözden geçirilmeli.
--
-- Motor: PostgreSQL 15+ | Migration aracı: Alembic (versiyonlama bu araçla)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid() için

-- ============================================================================
-- BÖLÜM 1 — KİMLİK
-- ============================================================================

CREATE TABLE ogrenciler (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_soyad            TEXT NOT NULL,                          -- [ÇIKARIM]
    email               TEXT NOT NULL UNIQUE,
    sifre_hash          TEXT NOT NULL,                          -- bcrypt/argon2 (veritabani_taslagi.md 3.2)
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now(),
    guncelleme_zamani   TIMESTAMPTZ NOT NULL DEFAULT now()
    -- NOT: yaş/doğum tarihi bilinçli olarak yok — KVKK/veli onayı konusu
    -- ertelendi (sistem_genel_anlatim.md, Ertelenen Konular #2).
);

CREATE TABLE admin_kullanicilar (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_soyad            TEXT NOT NULL,                          -- [ÇIKARIM]
    email               TEXT NOT NULL UNIQUE,
    sifre_hash          TEXT NOT NULL,                          -- veritabani_taslagi.md 3.3
    rol                 TEXT NOT NULL CHECK (rol IN ('super_admin','icerik_editoru')),  -- veritabani_taslagi.md 3.5
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- BÖLÜM 2 — İÇERİK YAPISI (K1-K5, 301 bölüm, dallar)
-- ============================================================================

CREATE TABLE katmanlar (
    id                      SERIAL PRIMARY KEY,
    kod                     TEXT NOT NULL UNIQUE,               -- 'K1'..'K5'
    ad                      TEXT NOT NULL,
    sira                    INT NOT NULL,
    normalizasyon_agirligi  NUMERIC(5,2),                        -- % ağırlık; K5 için NULL (D3/B)
    kosullu_mu              BOOLEAN NOT NULL DEFAULT FALSE,      -- B) — K5 = TRUE
    tetikleyici_katman_id   INT REFERENCES katmanlar(id)         -- B) — K5 -> K4
);

CREATE TABLE degiskenler (
    id          SERIAL PRIMARY KEY,
    katman_id   INT NOT NULL REFERENCES katmanlar(id),
    kod         TEXT NOT NULL UNIQUE,                            -- [ÇIKARIM] örn. 'K1_ANLAM'
    ad          TEXT NOT NULL,                                   -- örn. "Anlam"
    aciklama    TEXT,
    sira        INT NOT NULL
    -- dal_id kolonu aşağıda, dallar tablosu tanımlandıktan SONRA
    -- ALTER TABLE ile eklenir (FK sıralaması nedeniyle).
);

CREATE TABLE sorular (
    id                      SERIAL PRIMARY KEY,
    katman_id               INT NOT NULL REFERENCES katmanlar(id),
    degisken_id             INT REFERENCES degiskenler(id),      -- likert sorular için tekil değişken; SJT'de NULL, ağırlıklar ayrı tabloda
    soru_tipi               TEXT NOT NULL CHECK (soru_tipi IN ('likert','sjt')),  -- D2
    soru_metni              TEXT NOT NULL,
    ters_kodlanmis_mi       BOOLEAN NOT NULL DEFAULT FALSE,      -- D2 — puan = 100 - puan
    aktif_mi                BOOLEAN NOT NULL DEFAULT TRUE,
    olusturulma_zamani      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE soru_secenekleri (
    id              SERIAL PRIMARY KEY,
    soru_id         INT NOT NULL REFERENCES sorular(id),
    secenek_sirasi  INT NOT NULL,                                 -- likert: 1-5
    secenek_metni   TEXT NOT NULL,
    UNIQUE (soru_id, secenek_sirasi)
);

-- SJT sorularında bir seçenek birden fazla değişkene farklı ağırlıkta puan katabilir (D2)
CREATE TABLE sjt_secenek_degisken_agirlik (
    id          SERIAL PRIMARY KEY,
    secenek_id  INT NOT NULL REFERENCES soru_secenekleri(id),
    degisken_id INT NOT NULL REFERENCES degiskenler(id),
    agirlik     NUMERIC(4,3) NOT NULL,
    UNIQUE (secenek_id, degisken_id)
);

CREATE TABLE bolumler (
    id                  SERIAL PRIMARY KEY,
    ad                  TEXT NOT NULL UNIQUE,                    -- Bölüm_Listesi.xlsx, 301 satır
    osym_puan_turu      TEXT,                                    -- E5 mockup formu (opsiyonel)
    kisa_aciklama       TEXT,                                    -- D5 Katman-2 "Keşfet" için (yeni eklendi)
    durum               TEXT NOT NULL CHECK (durum IN ('taslak','test_ediliyor','yayinda')) DEFAULT 'taslak',  -- E5
    test_notu           TEXT,                                     -- E5 — yöneticinin onay/red gerekçesi
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE dallar (
    id                  SERIAL PRIMARY KEY,
    kod                 TEXT NOT NULL UNIQUE,                    -- 'D01'..'D21' (taslak)
    ad                  TEXT NOT NULL,
    bagli_degisken_id   INT REFERENCES degiskenler(id),          -- yönetici mockup "Bağlı Değişken" kolonu
    dogrulama_durumu    TEXT NOT NULL DEFAULT 'taslak'
                            CHECK (dogrulama_durumu IN ('taslak','guclu_kanitli','gozden_gecirilmeli')),  -- A6
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- [EKSİK/EKLENDİ] — sistem_genel_anlatim.md "Ertelenen Konular #1" burada
-- çözüldü: K5'e özgü değişkenler, K1-K4 ile aynı `degiskenler` tablosunda
-- yaşar (D3 — "aynı mekanizma" ilkesi), yalnızca dal_id ile hangi dala ait
-- olduğu işaretlenir. Soru tablosu ayrıca değiştirilmez; soru zaten
-- degisken_id üzerinden dalını miras alır. K1-K4 değişkenlerinde NULL kalır.
ALTER TABLE degiskenler ADD COLUMN dal_id INT REFERENCES dallar(id);

-- [EKSİK/EKLENDİ — içerik yazılırken bulundu] Bazı değişkenlerde (örn. P4
-- Nevrotiklik) öğrencinin bölüm beklentisinden YÜKSEK puan alması iyi bir
-- şey değildir — tam tersi tercih edilir. F2 (gap) ve F5 (trend)
-- hesaplamaları, ham puan farkının yönünü bu bayrağa göre çevirir. D4
-- (TOPLAM_UYUM) buna ihtiyaç duymaz çünkü zaten mutlak farkla çalışır
-- (yöne duyarsız). Varsayılan FALSE — yalnızca gerçekten ters yönlü olan
-- değişkenlerde TRUE işaretlenir.
ALTER TABLE degiskenler ADD COLUMN ters_yonlu BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE bolum_dal_eslesme (
    id                          SERIAL PRIMARY KEY,
    bolum_id                    INT NOT NULL REFERENCES bolumler(id),
    dal_id                      INT NOT NULL REFERENCES dallar(id),
    kaynak1_model_a_dal_id      INT REFERENCES dallar(id),       -- A6 Kaynak 1 — çoklu-model konsensüsü
    kaynak1_model_b_dal_id      INT REFERENCES dallar(id),
    kaynak1_model_c_dal_id      INT REFERENCES dallar(id),
    kaynak2_kumeleme_dal_id     INT REFERENCES dallar(id),       -- A6 Kaynak 2 — embedding kümeleme
    dogrulama_durumu            TEXT NOT NULL DEFAULT 'gozden_gecirilmeli'
                                    CHECK (dogrulama_durumu IN ('guclu_kanitli','gozden_gecirilmeli')),
    UNIQUE (bolum_id)   -- bir bölüm tek bir ana dala aittir
);

CREATE TABLE bolum_kumeleme_sonuclari (
    id              SERIAL PRIMARY KEY,
    bolum_id        INT NOT NULL REFERENCES bolumler(id),
    kume_no         INT NOT NULL,
    silhouette_skoru NUMERIC(5,4),                                -- A6 — optimal küme sayısı belirleme
    olusturulma_zamani TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- BÖLÜM 3 — MESLEK VERİSİ (A1, A2b, A4b)
-- ============================================================================

CREATE TABLE meslekler (
    id                  BIGSERIAL PRIMARY KEY,
    isco_kodu           TEXT NOT NULL,                           -- örn. '2521.07'
    ad                  TEXT NOT NULL,                           -- meslek_listesi_resmi_7764.xlsx
    alt_grup_kodu       TEXT NOT NULL,                           -- 43 alt-ana grup, ör. '21'
    alt_grup_adi        TEXT NOT NULL,
    ana_grup_kodu       TEXT NOT NULL,                           -- 10 ana grup
    kaynak              TEXT NOT NULL CHECK (kaynak IN ('tmss_resmi','ek_guncel')) DEFAULT 'tmss_resmi',  -- A4b
    UNIQUE (isco_kodu)
);

CREATE TABLE kategoriler (                                       -- [ÇIKARIM] A2b'de adı geçen "sistemin kendi 20 kategorisi"
    id          SERIAL PRIMARY KEY,
    ad          TEXT NOT NULL UNIQUE,
    aciklama    TEXT NOT NULL                                     -- A2b — DDL eşlemesi için kapsam açıklaması gerekli
);

CREATE TABLE alt_grup_kategori_eslesme (
    id                  SERIAL PRIMARY KEY,
    alt_grup_kodu       TEXT NOT NULL UNIQUE,                    -- 43 satır (A2b)
    kategori_id         INT NOT NULL REFERENCES kategoriler(id),
    model_a_skor        NUMERIC(5,4),
    model_b_skor        NUMERIC(5,4),
    model_c_skor        NUMERIC(5,4),
    guven_seviyesi      TEXT NOT NULL CHECK (guven_seviyesi IN ('yuksek','dusuk')),  -- A2b
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- A2/A3 ARA ÇIKTILARI — [ÇIKARIM/EKSİK]: Kaynak belgeler A2'de "meslek × bölüm ×
-- model × benzerlik skoru" ve A3'te "meslek × değişken × model × skor" çıktısından
-- bahsediyor (E7'de "model bazında ayrı ayrı görüntülenir" dendiği için bu ham
-- veri BİR YERDE saklanmalı) ama B) Veritabanı tablo listesinde bu ara tablolar
-- adlandırılmamıştı. Admin panelin (E7) model bazlı inceleme yapabilmesi için
-- burada resmi olarak tanımlandı:

CREATE TABLE meslek_bolum_eslesme_aday (                          -- A2 ham çıktısı
    id                  BIGSERIAL PRIMARY KEY,
    meslek_id           BIGINT NOT NULL REFERENCES meslekler(id),
    bolum_id            INT NOT NULL REFERENCES bolumler(id),
    model               TEXT NOT NULL CHECK (model IN ('model_a','model_b','model_c')),
    benzerlik_skoru     NUMERIC(5,4) NOT NULL,
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE meslek_degisken_skorlari (                            -- A3 ham çıktısı
    id                  BIGSERIAL PRIMARY KEY,
    meslek_id           BIGINT NOT NULL REFERENCES meslekler(id),
    degisken_id         INT NOT NULL REFERENCES degiskenler(id),
    model               TEXT NOT NULL CHECK (model IN ('model_a','model_b','model_c')),
    skor                NUMERIC(5,2) NOT NULL,
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- BÖLÜM 4 — HESAPLAMA ÇIKTILARI (statik, A4/A5 nihai sonucu)
-- ============================================================================

CREATE TABLE bolum_agirliklari (
    id                  BIGSERIAL PRIMARY KEY,
    bolum_id            INT NOT NULL REFERENCES bolumler(id),
    degisken_id         INT NOT NULL REFERENCES degiskenler(id),
    agirlik_degeri      NUMERIC(5,2) NOT NULL,                   -- A5 — ORTALAMA(model_A,B,C)
    yakinsama_skoru     NUMERIC(6,4) NOT NULL,                   -- A5 — STD_SAPMA(model_A,B,C)
    agirlikli_varyans   NUMERIC(6,4),                            -- A4 — mesleklerin dağılımı ne kadar geniş
    etkin_meslek_sayisi INT,                                     -- A4 — >0.5 benzerlikle bağlı meslek sayısı
    versiyon            INT NOT NULL DEFAULT 1,                  -- pipeline her çalıştığında yeni versiyon
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (bolum_id, degisken_id, versiyon)
);

-- ============================================================================
-- BÖLÜM 5 — ÖĞRENCİ VERİSİ (dinamik, tur bazlı — D2c)
-- ============================================================================

CREATE TABLE ogrenci_degerlendirme_turu (
    id                  BIGSERIAL PRIMARY KEY,
    ogrenci_id          UUID NOT NULL REFERENCES ogrenciler(id),
    tur_no              INT NOT NULL,
    baslama_zamani      TIMESTAMPTZ NOT NULL DEFAULT now(),
    tamamlanma_zamani   TIMESTAMPTZ,
    durum               TEXT NOT NULL CHECK (durum IN ('devam_ediyor','tamamlandi')) DEFAULT 'devam_ediyor',
    UNIQUE (ogrenci_id, tur_no)
);

CREATE TABLE ogrenci_katman_oturumlari (
    id                          BIGSERIAL PRIMARY KEY,
    ogrenci_id                  UUID NOT NULL REFERENCES ogrenciler(id),
    tur_id                      BIGINT NOT NULL REFERENCES ogrenci_degerlendirme_turu(id),
    katman_id                   INT NOT NULL REFERENCES katmanlar(id),
    durum                       TEXT NOT NULL CHECK (durum IN ('baslamadi','devam_ediyor','yarida_birakildi','tamamlandi')) DEFAULT 'baslamadi',  -- D4
    kilitlenen_soru_id_listesi  JSON,                             -- D2 — katman başlarken donan soru seti [DÜZELTME: INT[] -> JSON, backend geliştirme/test ortamında SQLite uyumluluğu için; PostgreSQL'de de JSON geçerlidir]
    baslama_zamani              TIMESTAMPTZ,
    tamamlanma_zamani           TIMESTAMPTZ,
    UNIQUE (ogrenci_id, tur_id, katman_id)
);

CREATE TABLE ogrenci_dal_oturumlari (
    id                  BIGSERIAL PRIMARY KEY,
    ogrenci_id          UUID NOT NULL REFERENCES ogrenciler(id),
    tur_id              BIGINT NOT NULL REFERENCES ogrenci_degerlendirme_turu(id),
    dal_id              INT NOT NULL REFERENCES dallar(id),
    durum               TEXT NOT NULL CHECK (durum IN ('baslamadi','devam_ediyor','tamamlandi')) DEFAULT 'baslamadi',
    baslama_zamani      TIMESTAMPTZ,
    tamamlanma_zamani   TIMESTAMPTZ,
    UNIQUE (ogrenci_id, tur_id, dal_id)
);

CREATE TABLE ogrenci_degisken_skorlari (
    id                  BIGSERIAL PRIMARY KEY,
    ogrenci_id          UUID NOT NULL REFERENCES ogrenciler(id),
    tur_id              BIGINT NOT NULL REFERENCES ogrenci_degerlendirme_turu(id),  -- D2c
    degisken_id         INT NOT NULL REFERENCES degiskenler(id),
    puan                NUMERIC(5,2) NOT NULL CHECK (puan BETWEEN 0 AND 100),
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ogrenci_id, tur_id, degisken_id)
);

-- [EKSİK/EKLENDİ — backend geliştirilirken fark edildi] Katman tamamlanıp
-- ogrenci_degisken_skorlari'na agregatif puan yazılana kadar öğrencinin HAM
-- (soru bazlı) cevaplarının tutulacağı bir tablo hiçbir belgede yoktu.
-- Bu olmadan "kaldığı yerden devam et" (D4) ve tek değişkene bağlı birden
-- fazla sorunun ortalamasını alma (D2) mekanizmaları çalışamaz.
CREATE TABLE ogrenci_cevaplar (
    id                  BIGSERIAL PRIMARY KEY,
    ogrenci_id          UUID NOT NULL REFERENCES ogrenciler(id),
    tur_id              BIGINT NOT NULL REFERENCES ogrenci_degerlendirme_turu(id),
    soru_id             INT NOT NULL REFERENCES sorular(id),
    secenek_id          INT NOT NULL REFERENCES soru_secenekleri(id),
    cevap_zamani        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ogrenci_id, tur_id, soru_id)
);

-- ============================================================================
-- BÖLÜM 6 — SONUÇLAR (tur bazlı — D2c)
-- ============================================================================

CREATE TABLE ogrenci_bolum_uyum_skorlari (
    id                  BIGSERIAL PRIMARY KEY,
    ogrenci_id          UUID NOT NULL REFERENCES ogrenciler(id),
    tur_id              BIGINT NOT NULL REFERENCES ogrenci_degerlendirme_turu(id),
    bolum_id            INT NOT NULL REFERENCES bolumler(id),
    toplam_uyum         NUMERIC(5,2) NOT NULL,                   -- D4 — 10 yöntemin normalize ortalaması
    yontem_skorlari     JSON,                                     -- D4 — 10 ÇKKV sonucu, YALNIZCA admin API'sinde döner [DÜZELTME: JSONB -> JSON, taşınabilirlik]
    kendall_w           NUMERIC(4,3),                             -- D4 — yöntemler arası tutarlılık, admin only
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ogrenci_id, tur_id, bolum_id)
);

CREATE TABLE ogrenci_dal_uyum_skorlari (
    id                  BIGSERIAL PRIMARY KEY,
    ogrenci_id          UUID NOT NULL REFERENCES ogrenciler(id),
    tur_id              BIGINT NOT NULL REFERENCES ogrenci_degerlendirme_turu(id),
    dal_id              INT NOT NULL REFERENCES dallar(id),
    bolum_id            INT NOT NULL REFERENCES bolumler(id),    -- D3 — dal-içi karşılaştırma o dal içindeki bölümlerle sınırlı
    dal_ici_uyum        NUMERIC(5,2) NOT NULL,
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ogrenci_id, tur_id, dal_id, bolum_id)
);

-- ============================================================================
-- BÖLÜM 7 — SİSTEM YÖNETİMİ
-- ============================================================================

CREATE TABLE sistem_parametreleri (
    id                  SERIAL PRIMARY KEY,
    anahtar             TEXT NOT NULL UNIQUE,                    -- 'k5_esik_puani', 'yeniden_degerlendirme_min_gun' vb.
    deger               TEXT NOT NULL,
    aciklama            TEXT,
    guncelleme_zamani   TIMESTAMPTZ NOT NULL DEFAULT now(),
    guncelleyen_admin_id UUID REFERENCES admin_kullanicilar(id)
);

CREATE TABLE katman_agirliklari (
    id                  SERIAL PRIMARY KEY,
    versiyon            INT NOT NULL,
    katman_id           INT NOT NULL REFERENCES katmanlar(id),
    agirlik             NUMERIC(5,2) NOT NULL,
    aktif_mi            BOOLEAN NOT NULL DEFAULT FALSE,          -- E3 — yalnızca 1 versiyon aktif olmalı
    olusturulma_zamani  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (versiyon, katman_id)
);

-- ============================================================================
-- BÖLÜM 8 — DOĞRULAMA (A7)
-- ============================================================================

CREATE TABLE gecerlilik_sonuclari (
    id                      SERIAL PRIMARY KEY,
    soru_id                 INT NOT NULL REFERENCES sorular(id),
    model                   TEXT NOT NULL CHECK (model IN ('model_a','model_b','model_c')),
    tahmin_edilen_degisken_id INT NOT NULL REFERENCES degiskenler(id),  -- A7 — kör tahmin
    gercek_degisken_id      INT NOT NULL REFERENCES degiskenler(id),
    eslesme_skoru           NUMERIC(5,4) NOT NULL,
    olusturulma_zamani      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gecerlilik_ozet (
    id                  SERIAL PRIMARY KEY,
    soru_id             INT NOT NULL REFERENCES sorular(id) UNIQUE,
    dogruluk_orani      NUMERIC(5,4) NOT NULL,
    guven_seviyesi      TEXT NOT NULL CHECK (guven_seviyesi IN ('yuksek','dusuk'))
);

-- ============================================================================
-- BÖLÜM 9 — İZLEME
-- ============================================================================

CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    admin_id        UUID NOT NULL REFERENCES admin_kullanicilar(id),
    islem           TEXT NOT NULL,                                -- örn. 'bolum_onay', 'parametre_guncelleme'
    hedef_tablo     TEXT NOT NULL,
    hedef_id        TEXT NOT NULL,
    gerekce         TEXT,                                         -- E5 — onay/red gerekçesi
    zaman           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- BÖLÜM 10 — KOÇLUK MODÜLÜ (Bölüm F, ayrı belge: koclugu_karsilastirma_modulu.md)
-- ============================================================================

CREATE TABLE ogrenci_hedef_bolum (
    id              BIGSERIAL PRIMARY KEY,
    ogrenci_id      UUID NOT NULL REFERENCES ogrenciler(id),
    bolum_id        INT NOT NULL REFERENCES bolumler(id),
    secim_zamani    TIMESTAMPTZ NOT NULL DEFAULT now(),
    pasif_zamani    TIMESTAMPTZ,                                  -- F8 — hedef değiştiğinde doldurulur, kayıt silinmez
    aktif_mi        BOOLEAN NOT NULL DEFAULT TRUE
);

-- F8 — Odaklanma ilkesi: bir öğrencinin aynı anda yalnızca 1 aktif hedefi olabilir
CREATE UNIQUE INDEX ux_ogrenci_tek_aktif_hedef
    ON ogrenci_hedef_bolum (ogrenci_id) WHERE aktif_mi = TRUE;

CREATE TABLE gelisim_yorum_havuzu (
    id                  SERIAL PRIMARY KEY,
    degisken_id         INT NOT NULL REFERENCES degiskenler(id),
    aralik              TEXT NOT NULL CHECK (aralik IN ('belirgin_ustun','ustun','beklenti','altinda','belirgin_altinda')),
    durum_tespiti       TEXT NOT NULL,
    aksiyon_onerisi     TEXT,                                     -- yalnızca 'altinda'/'belirgin_altinda' satırlarında dolu
    kaynak_tipi         TEXT CHECK (kaynak_tipi IN ('kurs','proje','okuma','staj_deneyim','aliskanlik')),
    tahmini_efor        TEXT CHECK (tahmini_efor IN ('kisa','orta','uzun')),
    UNIQUE (degisken_id, aralik)
);

CREATE TABLE gelisim_karsilastirma_yorumu (
    id                  SERIAL PRIMARY KEY,
    degisken_id         INT NOT NULL REFERENCES degiskenler(id),
    trend               TEXT NOT NULL CHECK (trend IN ('belirgin_gelisim','gelisim','durgun','gerileme','belirgin_gerileme')),
    yorum_metni         TEXT NOT NULL,
    UNIQUE (degisken_id, trend)
);

CREATE TABLE ogrenci_gelisim_aksiyon_durumu (
    id                  BIGSERIAL PRIMARY KEY,
    ogrenci_id          UUID NOT NULL REFERENCES ogrenciler(id),
    hedef_bolum_id      INT NOT NULL REFERENCES bolumler(id),
    degisken_id         INT NOT NULL REFERENCES degiskenler(id),
    durum               TEXT NOT NULL CHECK (durum IN ('planlandi','devam_ediyor','tamamlandi')) DEFAULT 'planlandi',
    guncelleme_zamani   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (ogrenci_id, hedef_bolum_id, degisken_id)
);

-- ============================================================================"""


def upgrade():
    for statement in _DDL.split(";"):
        s = statement.strip()
        if s:
            op.execute(s)


def downgrade():
    op.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
