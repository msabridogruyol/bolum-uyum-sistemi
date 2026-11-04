"""Veri Kaynakları eksikleri: yaşam maliyeti referansı, kamu maaşları, YKS 2027 tarihleri

Revision ID: 0097_veri_kaynaklari_tohumu
Revises: 0096_sistem_surumleri
Create Date: 2026-11-04

[2026-11-04] Süper admin › Veri Kaynakları'nda "Sistemde yok" görünen üç kaynak için ilk, kaynaklı veri.
Her tohum tek_seferlik_gocler işaretiyle bir kez yazılır; yönetici sonra sildiyse ya da değiştirdiyse geri yazılmaz.

1) yasam_maliyeti_referans (yeni tablo): kalem kalem gider verisi yerine resmî/kurumsal TOPLAM yaşam maliyeti.
   Kullanıcı kararı: gider kalemlerini öğrenci kendisi doldurur; sistem yalnızca karşılaştırma için kaynaklı bir toplam verir.
   Kaynak: TÜRK-İŞ Açlık ve Yoksulluk Sınırı Araştırması, Ekim 2026 (Ankara fiyatları; 30.10.2026).
2) kamu_maaslari: AA, "Zamlı memur maaşları belli oldu" (03.07.2026; Hazine ve Maliye Bakanlığı bilgileri).
   Tutarlar tek değerdir (net_min = net_max); varsayımlar ve derece/kademe açıklamada.
3) takvim_etkinlikleri: ÖSYM 2027 Sınav Takvimi (28.10.2026) — TYT 19.06.2027, AYT ve YDT 20.06.2027.
İdempotent; app/core/sema_guncelleme.py OTOMATIK listesinde.
"""
from alembic import op

revision = "0097_veri_kaynaklari_tohumu"
down_revision = "0096_sistem_surumleri"
branch_labels = None
depends_on = None

_TURKIS = ("TÜRK-İŞ, Açlık ve Yoksulluk Sınırı Araştırması, Ekim 2026 (Ankara fiyatlarıyla; yayım 30.10.2026)")
_AA = ("AA, \"Zamlı memur maaşları belli oldu\", 03.07.2026 (Hazine ve Maliye Bakanlığı bilgileri) — "
       "https://www.aa.com.tr/tr/ekonomi/zamli-memur-maaslari-belli-oldu/3985004")
_VARSAYIM = ("Temmuz–Aralık 2026 net aylık. Varsayım: evli, eşi çalışmayan, 2 çocuklu (biri 0–6 yaş) memur; aile ve çocuk yardımı "
             "dahil; ek ders, nöbet, döner sermaye, bölgesel ödeme, yabancı dil tazminatı hariç. Bekâr ve çocuksuz bir memur "
             "bundan daha az alır.")
_KIDEMLI = " 1. derece 4. kademe kıdemli bir kadronun maaşıdır; mesleğe yeni başlayan daha düşük alır."


def _kamu(kadro, kelimeler, tutar, ek=""):
    import json
    return (kadro, json.dumps(kelimeler, ensure_ascii=False), tutar, _VARSAYIM + ek)


KAMU = [
    _kamu("Öğretmen (1. derece 4. kademe)", ["ogretmen", "rehberlik ve psikolojik"], 83254, _KIDEMLI),
    _kamu("Uzman öğretmen (1. derece 4. kademe)", ["ogretmen", "rehberlik ve psikolojik"], 92166, _KIDEMLI),
    _kamu("Memur, üniversite mezunu (9. derece 1. kademe)", ["kamu yonetimi", "yerel yonetimler", "maliye", "memur"], 73070,
          " Lisans mezunu bir memurun başlangıç kadrosudur."),
    _kamu("Polis memuru (8. derece 1. kademe)", ["polis"], 92618),
    _kamu("Uzman doktor (1. derece 4. kademe)", ["=tip", "uzman hekim", "uzman doktor"], 170730, _KIDEMLI),
    _kamu("Hemşire, üniversite mezunu (5. derece 1. kademe)", ["hemsire"], 84845),
    _kamu("Mühendis (1. derece 4. kademe)", ["muhendis"], 109185, _KIDEMLI),
    _kamu("Araştırma görevlisi (7. derece 1. kademe)", ["arastirma gorevlisi", "akademisyen"], 102779),
    _kamu("Vaiz (1. derece 4. kademe)", ["ilahiyat", "islam bilimleri", "vaiz"], 86983, _KIDEMLI),
    _kamu("Avukat (1. derece 4. kademe)", ["hukuk", "avukat"], 102135, _KIDEMLI),
]

def _q(v) -> str:
    """SQL metin sabiti (tek tırnak kaçışlı). Değerler bu dosyadaki sabit, kaynaklı metinlerdir; dışarıdan girdi yok."""
    return "'" + str(v).replace("'", "''") + "'"


YASAM = [
    ("bekar_yasam", "Bekâr bir çalışanın aylık yaşama maliyeti", "49124.30",
     "Tek yaşayan bir çalışanın gıda, kira, ulaşım, fatura, giyim, sağlık, eğitim gibi tüm zorunlu harcamaları"),
    ("aclik_siniri", "Açlık sınırı (4 kişilik ailenin aylık gıda harcaması)", "38024.03",
     "Dört kişilik bir ailenin sağlıklı beslenmesi için gereken aylık mutfak harcaması"),
    ("yoksulluk_siniri", "Yoksulluk sınırı (4 kişilik ailenin tüm zorunlu harcamaları)", "123856.80",
     "Dört kişilik bir ailenin gıda ve gıda dışı tüm zorunlu aylık harcamaları"),
]
YKS = [("YKS 2027 – TYT (Temel Yeterlilik Testi)", "2027-06-19"), ("YKS 2027 – AYT ve YDT", "2027-06-20")]
_YKS_ACIKLAMA = ("ÖSYM 2027 Sınav Takvimi (açıklanma 28.10.2026). Başvurular 2–16 Mart 2027, geç başvuru 16–18 Mart 2027; "
                 "sonuçlar 21 Temmuz 2027 (planlanan).")

# [2026-11-04] Canlıda göçler app/core/sema_guncelleme.py ile yalnızca bu modülün SQL metninden uygulanır (upgrade() çalışmaz).
# Bu yüzden tohumlar da SQL'dedir. Her tohum tek ifadedir: tek_seferlik_gocler işareti ilk kez eklenirse satırlar yazılır.
SQL = r"""
CREATE TABLE IF NOT EXISTS yasam_maliyeti_referans (
    id SERIAL PRIMARY KEY,
    kod VARCHAR(40) NOT NULL,
    ad VARCHAR(200) NOT NULL,
    aylik_tutar NUMERIC(12,2) NOT NULL CHECK (aylik_tutar > 0),
    kapsam VARCHAR(300),
    donem VARCHAR(20) NOT NULL,
    kaynak VARCHAR NOT NULL,
    tarih DATE,
    olusturulma TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (kod, donem)
);
WITH isaret AS (
    INSERT INTO tek_seferlik_gocler (ad) VALUES ('0097_yasam_maliyeti_turkis_2026_10') ON CONFLICT (ad) DO NOTHING RETURNING ad
)
INSERT INTO yasam_maliyeti_referans (kod, ad, aylik_tutar, kapsam, donem, kaynak, tarih)
SELECT v.kod, v.ad, v.tutar, v.kapsam, '2026-10', """ + _q(_TURKIS) + r""", DATE '2026-10-30' FROM (VALUES
""" + ",\n".join(f"    ({_q(k)}, {_q(a)}, {t}, {_q(c)})" for k, a, t, c in YASAM) + r"""
) AS v(kod, ad, tutar, kapsam)
WHERE EXISTS (SELECT 1 FROM isaret)
ON CONFLICT (kod, donem) DO NOTHING;
WITH isaret AS (
    INSERT INTO tek_seferlik_gocler (ad) VALUES ('0097_kamu_maaslari_2026_2') ON CONFLICT (ad) DO NOTHING RETURNING ad
)
INSERT INTO kamu_maaslari (kadro_adi, anahtar_kelimeler, net_min, net_max, donem, kaynak, aciklama)
SELECT v.kadro, CAST(v.kel AS JSONB), v.tutar, v.tutar, '2026-2', """ + _q(_AA) + r""", v.aciklama FROM (VALUES
""" + ",\n".join(f"    ({_q(k)}, {_q(w)}, {t}, {_q(a)})" for k, w, t, a in KAMU) + r"""
) AS v(kadro, kel, tutar, aciklama)
WHERE EXISTS (SELECT 1 FROM isaret)
  AND NOT EXISTS (SELECT 1 FROM kamu_maaslari m WHERE m.kadro_adi = v.kadro AND m.donem = '2026-2');
WITH isaret AS (
    INSERT INTO tek_seferlik_gocler (ad) VALUES ('0097_yks_2027') ON CONFLICT (ad) DO NOTHING RETURNING ad
)
INSERT INTO takvim_etkinlikleri (okul_id, ogrenci_id, baslik, aciklama, tur, baslangic, olusturan)
SELECT NULL, NULL, v.baslik, """ + _q(_YKS_ACIKLAMA) + r""", 'sinav', CAST(v.gun AS DATE), 'Sistem (ÖSYM takvimi)' FROM (VALUES
""" + ",\n".join(f"    ({_q(b)}, {_q(g)})" for b, g in YKS) + r"""
) AS v(baslik, gun)
WHERE EXISTS (SELECT 1 FROM isaret)
  AND NOT EXISTS (SELECT 1 FROM takvim_etkinlikleri t WHERE t.okul_id IS NULL AND t.ogrenci_id IS NULL
                  AND t.baslangic = CAST(v.gun AS DATE) AND t.baslik ILIKE '%YKS%')
"""


def upgrade():
    op.execute(SQL)


def downgrade():
    pass
