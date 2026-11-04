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

SQL_TABLO = r"""
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
"""


def upgrade():
    op.execute(SQL_TABLO)
    bag = op.get_bind()
    from sqlalchemy import text

    def ilk_kez(ad: str) -> bool:
        return bag.execute(text("INSERT INTO tek_seferlik_gocler (ad) VALUES (:a) ON CONFLICT (ad) DO NOTHING RETURNING ad"),
                           {"a": ad}).first() is not None

    if ilk_kez("0097_yasam_maliyeti_turkis_2026_10"):
        for kod, ad, tutar, kapsam in (
                ("bekar_yasam", "Bekâr bir çalışanın aylık yaşama maliyeti", 49124.30,
                 "Tek yaşayan bir çalışanın gıda, kira, ulaşım, fatura, giyim, sağlık, eğitim gibi tüm zorunlu harcamaları"),
                ("aclik_siniri", "Açlık sınırı (4 kişilik ailenin aylık gıda harcaması)", 38024.03,
                 "Dört kişilik bir ailenin sağlıklı beslenmesi için gereken aylık mutfak harcaması"),
                ("yoksulluk_siniri", "Yoksulluk sınırı (4 kişilik ailenin tüm zorunlu harcamaları)", 123856.80,
                 "Dört kişilik bir ailenin gıda ve gıda dışı tüm zorunlu aylık harcamaları")):
            bag.execute(text("INSERT INTO yasam_maliyeti_referans (kod, ad, aylik_tutar, kapsam, donem, kaynak, tarih) "
                             "VALUES (:k, :a, :t, :c, '2026-10', :s, DATE '2026-10-30') ON CONFLICT (kod, donem) DO NOTHING"),
                        {"k": kod, "a": ad, "t": tutar, "c": kapsam, "s": _TURKIS})

    if ilk_kez("0097_kamu_maaslari_2026_2"):
        for kadro, kel, tutar, aciklama in KAMU:
            if bag.execute(text("SELECT 1 FROM kamu_maaslari WHERE kadro_adi = :k AND donem = '2026-2'"), {"k": kadro}).first():
                continue
            bag.execute(text("INSERT INTO kamu_maaslari (kadro_adi, anahtar_kelimeler, net_min, net_max, donem, kaynak, aciklama) "
                             "VALUES (:k, CAST(:w AS JSONB), :t, :t, '2026-2', :s, :a)"),
                        {"k": kadro, "w": kel, "t": tutar, "s": _AA, "a": aciklama})

    if ilk_kez("0097_yks_2027"):
        for baslik, gun in (("YKS 2027 – TYT (Temel Yeterlilik Testi)", "2027-06-19"),
                            ("YKS 2027 – AYT ve YDT", "2027-06-20")):
            if bag.execute(text("SELECT 1 FROM takvim_etkinlikleri WHERE okul_id IS NULL AND ogrenci_id IS NULL "
                                "AND baslangic = CAST(:g AS DATE) AND baslik ILIKE '%YKS%'"), {"g": gun}).first():
                continue
            bag.execute(text("INSERT INTO takvim_etkinlikleri (okul_id, ogrenci_id, baslik, aciklama, tur, baslangic, olusturan) "
                             "VALUES (NULL, NULL, :b, :a, 'sinav', CAST(:g AS DATE), 'Sistem (ÖSYM takvimi)')"),
                        {"b": baslik, "g": gun,
                         "a": "ÖSYM 2027 Sınav Takvimi (açıklanma 28.10.2026). Başvurular 2–16 Mart 2027, geç başvuru 16–18 Mart 2027; "
                              "sonuçlar 21 Temmuz 2027 (planlanan)."})


def downgrade():
    pass
