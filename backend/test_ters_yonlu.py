"""P4 (ters_yonlu) düzeltmesinin uçtan uca testi — migration zinciri + kod düzeltmesi."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_ters.db"
import sys
sys.path.insert(0, ".")

from sqlalchemy import text
from app.core.database import Base, engine, SessionLocal
from app import models

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

def basarili(kosul, mesaj):
    print(("✓ " if kosul else "✗ ") + mesaj)
    assert kosul, mesaj

# --- Minimal katman + P4 değişkeni + bölüm kur ---
k2 = models.Katman(kod="K2", ad="Kişilik", sira=2, normalizasyon_agirligi=15, kosullu_mu=False)
db.add(k2); db.flush()
p4 = models.Degisken(katman_id=k2.id, kod="P4", ad="Nevrotiklik", sira=4, ters_yonlu=False)  # migration öncesi durum
db.add(p4); db.commit()
p4_id = p4.id

# --- 0004+0005 migration mantığını uygula (gelisim_yorum_havuzu + ters_yonlu güncellemesi) ---
class SahteOp:
    def __init__(self, conn):
        self.conn = conn
    def execute(self, sql):
        self.conn.execute(text(sql))

conn = engine.connect()
op = SahteOp(conn)

for aralik in ["belirgin_ustun", "ustun", "beklenti", "altinda", "belirgin_altinda"]:
    op.execute(f"""
        INSERT INTO gelisim_yorum_havuzu (degisken_id, aralik, durum_tespiti, aksiyon_onerisi, kaynak_tipi, tahmini_efor)
        VALUES ({p4_id}, '{aralik}', 'placeholder', NULL, NULL, NULL)
    """)
conn.commit()

with open("alembic/versions/0005_p4_yon_duzeltmesi.py", encoding="utf-8") as f:
    content = f.read()
namespace = {}
exec(compile(content, "mig0005", "exec"), namespace)
namespace["op"] = op
namespace["upgrade"]()
conn.commit()
conn.close()

db.close()
db = SessionLocal()

# --- 1) ters_yonlu gerçekten TRUE oldu mu ---
p4_guncel = db.query(models.Degisken).filter(models.Degisken.kod == "P4").first()
basarili(p4_guncel.ters_yonlu is True, f"P4.ters_yonlu = TRUE — gelen: {p4_guncel.ters_yonlu}")

# --- 2) belirgin_ustun satırında artık gerçek içerik + aksiyon_onerisi None var mı ---
from app.models import GelisimYorumHavuzu
bu = db.query(GelisimYorumHavuzu).filter(GelisimYorumHavuzu.degisken_id == p4_id, GelisimYorumHavuzu.aralik == "belirgin_ustun").first()
basarili("sakin" in bu.durum_tespiti.lower() or "dengeli" in bu.durum_tespiti.lower(), f"belirgin_ustun içeriği doğru (sakinlik vurgusu) — gelen: {bu.durum_tespiti}")

ba = db.query(GelisimYorumHavuzu).filter(GelisimYorumHavuzu.degisken_id == p4_id, GelisimYorumHavuzu.aralik == "belirgin_altinda").first()
basarili(ba.aksiyon_onerisi is not None, f"belirgin_altinda artık gerçek aksiyon önerisi içeriyor — gelen: {ba.aksiyon_onerisi}")

# --- 3) EN KRİTİK TEST: koclugu_servisi.gap_analizi_hesapla ile GERÇEK yön mantığını doğrula ---
bolum = models.Bolum(ad="Test Bölümü", durum="yayinda")
db.add(bolum); db.flush()
# bölüm P4'te DÜŞÜK puan bekliyor (sakin insan istiyor) -> agirlik_degeri=20
db.add(models.BolumAgirligi(bolum_id=bolum.id, degisken_id=p4_id, agirlik_degeri=20, yakinsama_skoru=0.02, versiyon=1))

ogrenci = models.Ogrenci(ad_soyad="Ters Yön Test", email="tersyon@ornek.com", sifre_hash="x")
db.add(ogrenci); db.flush()
tur = models.OgrenciDegerlendirmeTuru(ogrenci_id=ogrenci.id, tur_no=1, durum="tamamlandi")
db.add(tur); db.flush()

# Öğrenci P4'te YÜKSEK puan aldı (çok hassas) -> puan=80. Ham gap = 80-20 = +60 (büyük pozitif)
# ESKİ (yanlış) mantıkla bu "belirgin_ustun" (güçlü yön) sayılırdı — YANLIŞ.
# YENİ (doğru) mantıkla bu "belirgin_altinda" (gelişim alanı) sayılmalı — DOĞRU.
db.add(models.OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur.id, degisken_id=p4_id, puan=80))
db.commit()

from app.core.koclugu_servisi import gap_analizi_hesapla
sonuc = gap_analizi_hesapla(db, ogrenci, tur, bolum.id)
p4_sonuc = next(s for s in sonuc if s.degisken.kod == "P4")

basarili(p4_sonuc.gap == 60.0, f"Ham gap doğru hesaplandı (+60, şeffaflık için değişmedi) — gelen: {p4_sonuc.gap}")
basarili(p4_sonuc.kategori == "belirgin_altinda", f"KRİTİK: yüksek nevrotiklik puanı doğru şekilde 'belirgin_altinda' (gelişim alanı) sayıldı, 'belirgin_ustun' DEĞİL — gelen kategori: {p4_sonuc.kategori}")
basarili(p4_sonuc.gelisim_karti is not None and p4_sonuc.gelisim_karti.aksiyon_onerisi is not None, "Doğru kategoriye eşleşen gerçek aksiyon önerisi geldi")

print()
print("TÜM TERS_YONLU DÜZELTME TESTLERİ GEÇTİ ✓ (yön mantığı gerçekten doğru çalışıyor)")
