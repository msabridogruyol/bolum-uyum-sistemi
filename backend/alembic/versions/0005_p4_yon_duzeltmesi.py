"""P4 (Nevrotiklik) yön düzeltmesi — ters_yonlu bayrağı + doğru içerik

Revision ID: 0005_p4_yon_duzeltmesi
Revises: 0004_gelisim_yorum_havuzu
Create Date: 2026-08-13

P4 (Nevrotiklik) icin yuksek ogrenci puani bolum beklentisinden
yuksekse bu OLUMLU degil - tam tersi tercih edilir. Bu migration:
  1. degiskenler.ters_yonlu = TRUE yapar (P4 icin)
  2. gelisim_yorum_havuzu'ndaki P4 satirlarini DOGRU yonde icerikle
     gunceller (0004'te aksiyon_onerisi bilincli NULL birakilmisti)
"""
from alembic import op

revision = "0005_p4_yon_duzeltmesi"
down_revision = "0004_gelisim_yorum_havuzu"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE degiskenler SET ters_yonlu = TRUE WHERE kod = 'P4'")

    _guncellemeler = [
        r"""UPDATE gelisim_yorum_havuzu SET durum_tespiti = 'Duygusal olarak oldukça dengeli ve dirençlisin, yüksek baskı altında bile sakinliğini koruyabiliyorsun.', aksiyon_onerisi = NULL, kaynak_tipi = NULL, tahmini_efor = NULL WHERE degisken_id = (SELECT id FROM degiskenler WHERE kod = 'P4') AND aralik = 'belirgin_ustun'""",
        r"""UPDATE gelisim_yorum_havuzu SET durum_tespiti = 'Stres ve kaygıya karşı nispeten dirençlisin, duygusal iniş çıkışlar seni fazla etkilemiyor.', aksiyon_onerisi = NULL, kaynak_tipi = NULL, tahmini_efor = NULL WHERE degisken_id = (SELECT id FROM degiskenler WHERE kod = 'P4') AND aralik = 'ustun'""",
        r"""UPDATE gelisim_yorum_havuzu SET durum_tespiti = 'Duygusal hassasiyetin dengeli düzeyde — bazı durumlarda etkilenirsin, bazılarında değil.', aksiyon_onerisi = NULL, kaynak_tipi = NULL, tahmini_efor = NULL WHERE degisken_id = (SELECT id FROM degiskenler WHERE kod = 'P4') AND aralik = 'beklenti'""",
        r"""UPDATE gelisim_yorum_havuzu SET durum_tespiti = 'Stres ve baskı karşısında zaman zaman zorlanabiliyorsun — yoğun tempolu, yüksek baskılı ortamlar enerjini hızlı tüketebilir.', aksiyon_onerisi = 'Basit stres yönetimi tekniklerini (kısa molalar, nefes çalışmaları) günlük rutine eklemek faydalı olabilir.', kaynak_tipi = 'aliskanlik', tahmini_efor = 'orta' WHERE degisken_id = (SELECT id FROM degiskenler WHERE kod = 'P4') AND aralik = 'altinda'""",
        r"""UPDATE gelisim_yorum_havuzu SET durum_tespiti = 'Stres ve kaygıya karşı hassasiyetin belirgin bir gelişim alanı — yüksek baskılı, hızlı karar gerektiren ortamlar (acil müdahale, kriz yönetimi) seni ciddi şekilde zorlayabilir.', aksiyon_onerisi = 'Stres yönetimi konusunda yapılandırılmış bir kaynaktan (kitap, kısa kurs) faydalanmak iyi bir başlangıç olabilir; yoğunluğu fazla hissettiğinde bir uzmandan destek almak da düşünülebilir.', kaynak_tipi = 'okuma', tahmini_efor = 'orta' WHERE degisken_id = (SELECT id FROM degiskenler WHERE kod = 'P4') AND aralik = 'belirgin_altinda'""",
    ]
    for statement in _guncellemeler:
        op.execute(statement)


def downgrade():
    op.execute("UPDATE degiskenler SET ters_yonlu = FALSE WHERE kod = 'P4'")
