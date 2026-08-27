"""31 değişkenin gerçek içeriği — SONUÇ.xlsx'ten alındı

Revision ID: 0003_31_degisken_icerik
Revises: 0002_baslangic_verisi
Create Date: 2026-08-13

ÖNEMLİ: Kaynak Excel dosyasında (SONUÇ.xlsx) "Katman 3" ve "Katman 4"
etiketleri BİRBİRİNE KARIŞMIŞTI — Excel'de Katman 3 = Alan Eğilimi (%40),
Katman 4 = İş Ortamı (%25) olarak yazılıydı. Kullanıcıyla doğrulandı:
DOĞRU sıra sistemin baştan beri kullandığı sıra — K3 = İş Ortamı (%25),
K4 = Alan Eğilimi (%40, K5'i tetikleyen katman). Bu migration, içeriği
Excel'deki yanlış numaralandırmaya göre DEĞİL, doğrulanmış sıraya göre
ekliyor: I1-I7 -> K3, A1-A9 -> K4.
"""
from alembic import op

revision = "0003_31_degisken_icerik"
down_revision = "0002_baslangic_verisi"
branch_labels = None
depends_on = None

_DEGISKENLER = [
    # (katman_kod, kod, ad, aciklama, sira)
    ("K1", "D1", "Güvence / güvenlik", "İşsizlik riski düşük, düzenli maaş, kurallı ve öngörülebilir hayat isteği.", 1),
    ("K1", "D2", "Ekonomik getiri / yüksek gelir", "Yüksek maaş, prim, finansal imkanlar ve maddi konforu ön planda tutma.", 2),
    ("K1", "D3", "Statü / prestij", "Toplumda saygın, \u201cadı bilinen\u201d bir meslek/kurumda olma isteği.", 3),
    ("K1", "D4", "Anlam / yaşam amacı", "Yaptığı işin kişisel anlam ve amaç taşıması, içsel tatmin sağlaması.", 4),
    ("K1", "D5", "Sosyal etki / topluma katkı", "İnsanlara, topluma, dünyaya somut fayda üretme motivasyonu.", 5),
    ("K1", "D6", "Özerklik / özgürlük", "Kendi kararlarını verebilmek, esnek çalışma, kendi işini kurabilme isteği.", 6),
    ("K1", "D7", "Estetik / yaratıcılık değeri", "Güzellik, tasarım, sanat ve özgün üretimin hayatında önemli olması.", 7),

    ("K2", "P1", "Dışadönüklük / insanla çalışma isteği", "İnsanlarla yüz yüze iletişim, ekip içinde olma, sosyal ortamdan enerji alma eğilimi.", 1),
    ("K2", "P2", "Uyumluluk / işbirliği eğilimi", "Uzlaşma, empati, ekipte uyum sağlama, çatışmadan kaçınma veya yönetebilme.", 2),
    ("K2", "P3", "Sorumluluk / disiplin", "Planlı çalışma, işleri zamanında tamamlama, görev bilinci yüksek olma düzeyi.", 3),
    ("K2", "P4", "Nevrotiklik / duygusal hassasiyet", "Stres, kaygı, duygusal iniş çıkışlara karşı ne kadar hassas olunduğu.", 4),
    ("K2", "P5", "Deneyime açıklık / yeniliğe açıklık", "Yeni fikirler, farklı alanlar, değişen koşullara merak ve uyum isteği.", 5),
    ("K2", "P6", "Rutin ↔ dinamik tercih", "Tekrarlayan, sabit işlerden mi, yoksa değişken ve sürprizli işlerden mi hoşlanma.", 6),
    ("K2", "P7", "Belirsizlik & risk toleransı", "Kuralların net olmadığı, sonuçların belirsiz olduğu durumlara tahammül ve risk alma isteği.", 7),
    ("K2", "P8", "Yönetme / liderlik isteği", "Sorumluluk alma, ekibe yön verme, karar verici pozisyonda olma arzusu.", 8),

    # [DÜZELTME] Excel'de "Katman 4" idi -> doğrulanmış sıraya göre K3 (İş Ortamı, %25)
    ("K3", "I1", "Zaman yönetimi / önceliklendirme", "Birden fazla işi planlama, öncelik sıralama ve deadline yönetme becerisi.", 1),
    ("K3", "I2", "Ekip / çatışma yönetimi", "Takım içi anlaşmazlıkları çözme, farklı görüşleri yönetebilme yetkinliği.", 2),
    ("K3", "I3", "Baskı / kriz anında karar verme", "Stres altında, eksik bilgiyle bile makul karar verebilme kapasitesi.", 3),
    ("K3", "I4", "Etik / dürüstlük duyarlılığı", "Adalet, dürüstlük, etik ilkelere bağlı kalma hassasiyeti.", 4),
    ("K3", "I5", "İnisiyatif / harekete geçme", "Beklemeden sorumluluk alma, sorun gördüğünde adım atma, proaktiflik.", 5),
    ("K3", "I6", "Geri bildirim / eleştiriye açıklık", "Yapıcı eleştiriyi kabul etme, hatadan öğrenme, savunmaya kapanmama eğilimi.", 6),
    ("K3", "I7", "Yönetim / strateji & iş dünyası yetkinliği", "Stratejik düşünme, süreç ve insan yönetimi, finansal ve ticari farkındalık, müşteri/pazar anlayışı.", 7),

    # [DÜZELTME] Excel'de "Katman 3" idi -> doğrulanmış sıraya göre K4 (Alan Eğilimi, %40, K5 tetikleyicisi)
    ("K4", "A1", "Sayısal / veri / sistem eğilimi", "Matematik, istatistik, veri analizi, formül ve sistem mantığına kuvvetli ilgi/yatkınlık.", 1),
    ("K4", "A2", "Sözel / dil / argüman eğilimi", "Metin okuma-yazma, hukuki/kavramsal düşünme, tartışma ve ikna süreçlerinden keyif alma.", 2),
    ("K4", "A3", "Sosyal / insan odaklı eğilim", "İnsan davranışı, psikoloji, eğitim, sosyal hizmet gibi insan merkezli alanlara ilgi.", 3),
    ("K4", "A4", "Yaratıcı / uzamsal / tasarım", "Mimari, tasarım, çizim, görsel üretim, görsel-estetik problem çözme eğilimi.", 4),
    ("K4", "A5", "Doğa / canlı / laboratuvar eğilimi", "Biyoloji, kimya, tarım, çevre, laboratuvar deneyleri ve saha çalışmalarına ilgi.", 5),
    ("K4", "A6", "Fiziksel / hareket eğilimi", "Spor, beden kullanımı, sahada aktif olma, hareket gerektiren işlere yatkınlık.", 6),
    ("K4", "A7", "Adım adım / yapılandırılmış stil", "Kuralları net, aşamaları belli, planlı ve sistematik öğrenme ve çalışma tarzı.", 7),
    ("K4", "A8", "Sezgisel / genel çerçeve stili", "Önce büyük resmi görme, sezgiyle ilerleme, görsel/şematik düşünmeye yatkınlık.", 8),
    ("K4", "A9", "Girişimcilik / pazarlama / ikna eğilimi", "Fırsat görme, satış/pazarlık yapma, risk alarak iş kurma isteği.", 9),
]


def upgrade():
    for katman_kod, kod, ad, aciklama, sira in _DEGISKENLER:
        ad_e = ad.replace("'", "''")
        aciklama_e = aciklama.replace("'", "''")
        op.execute(
            f"""
            INSERT INTO degiskenler (katman_id, kod, ad, aciklama, sira)
            SELECT id, '{kod}', '{ad_e}', '{aciklama_e}', {sira}
            FROM katmanlar WHERE kod = '{katman_kod}'
            """
        )


def downgrade():
    kodlar = "', '".join(kod for _, kod, _, _, _ in _DEGISKENLER)
    op.execute(f"DELETE FROM degiskenler WHERE kod IN ('{kodlar}')")
