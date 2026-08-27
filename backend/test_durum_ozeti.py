"""Katman durumu + durum özeti uç noktalarının testi (kullanıcı sorusu üzerine eklendi)."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_durum.db"
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from app.core.database import Base, engine, SessionLocal
from app import models
from app.main import app

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

def basarili(kosul, mesaj):
    print(("✓ " if kosul else "✗ ") + mesaj)
    assert kosul, mesaj

k1 = models.Katman(kod="K1", ad="K1", sira=1, normalizasyon_agirligi=50, kosullu_mu=False)
k2 = models.Katman(kod="K2", ad="K2", sira=2, normalizasyon_agirligi=50, kosullu_mu=False)
db.add_all([k1, k2]); db.flush()
d1 = models.Degisken(katman_id=k1.id, kod="D1", ad="D1", sira=1)
d2 = models.Degisken(katman_id=k2.id, kod="D2", ad="D2", sira=1)
db.add_all([d1, d2]); db.flush()
for k, d in [(k1, d1), (k2, d2)]:
    s = models.Soru(katman_id=k.id, degisken_id=d.id, soru_tipi="likert", soru_metni=f"{k.kod} sorusu", aktif_mi=True)
    db.add(s); db.flush()
    for i, m in enumerate(["1", "2", "3", "4", "5"], start=1):
        db.add(models.SoruSecenegi(soru_id=s.id, secenek_sirasi=i, secenek_metni=m))
db.commit(); db.close()

client = TestClient(app)
client.post("/auth/kayit", json={"ad_soyad": "Durum Test", "email": "durum@ornek.com", "sifre": "sifre1234"})
r = client.post("/auth/giris", json={"email": "durum@ornek.com", "sifre": "sifre1234"})
headers = {"Authorization": f"Bearer {r.json()['erisim_tokeni']}"}

# 1) Hiç tur başlamadan: tüm katmanlar 'baslamadi', durum özeti sıfır
r1 = client.get("/ogrenci/katmanlar", headers=headers)
basarili(all(k["durum"] == "baslamadi" for k in r1.json()), f"Başlangıçta tüm katmanlar 'baslamadi' — gelen: {[k['durum'] for k in r1.json()]}")

r1b = client.get("/ogrenci/durum-ozeti", headers=headers)
basarili(r1b.json()["tur_no"] is None, f"Hiç tur yokken tur_no None — gelen: {r1b.json()}")
basarili(r1b.json()["tamamlanan_katman_sayisi"] == 0, "Tamamlanan katman sayısı 0")

# 2) K1'i tamamla
rb = client.post("/ogrenci/katmanlar/K1/basla", headers=headers)
soru_id = rb.json()["sorular"][0]["id"]
secenek_id = rb.json()["sorular"][0]["secenekler"][3]["id"]
client.post("/ogrenci/katmanlar/K1/cevap", json={"soru_id": soru_id, "secenek_id": secenek_id}, headers=headers)
client.post("/ogrenci/katmanlar/K1/tamamla", headers=headers)

# 3) K1 artık 'tamamlandi', K2 hâlâ 'baslamadi' olmalı — TAM DA BULUNAN HATA BURADA DÜZELTİLDİ
r3 = client.get("/ogrenci/katmanlar", headers=headers)
durumlar = {k["kod"]: k["durum"] for k in r3.json()}
basarili(durumlar["K1"] == "tamamlandi", f"K1 durumu 'tamamlandi' olarak dönüyor — gelen: {durumlar}")
basarili(durumlar["K2"] == "baslamadi", f"K2 hâlâ 'baslamadi' — gelen: {durumlar}")

r3b = client.get("/ogrenci/durum-ozeti", headers=headers)
basarili(r3b.json()["tur_no"] == 1, f"Tur no doğru — gelen: {r3b.json()}")
basarili(r3b.json()["tamamlanan_katman_sayisi"] == 1, f"1 katman tamamlandı özeti doğru — gelen: {r3b.json()}")
basarili(r3b.json()["toplam_ana_katman_sayisi"] == 2, "Toplam ana katman sayısı doğru (2)")
basarili(r3b.json()["tur_tamamlandi_mi"] is False, "Tur henüz tamamlanmadı (K2 kaldı)")
basarili(r3b.json()["sonraki_tur_tarihi"] is None, "Tur bitmeden sonraki tur tarihi yok")

# 4) K2'yi de tamamla — tur bitsin
rb2 = client.post("/ogrenci/katmanlar/K2/basla", headers=headers)
soru2_id = rb2.json()["sorular"][0]["id"]
secenek2_id = rb2.json()["sorular"][0]["secenekler"][3]["id"]
client.post("/ogrenci/katmanlar/K2/cevap", json={"soru_id": soru2_id, "secenek_id": secenek2_id}, headers=headers)
client.post("/ogrenci/katmanlar/K2/tamamla", headers=headers)

r4 = client.get("/ogrenci/durum-ozeti", headers=headers)
basarili(r4.json()["tur_tamamlandi_mi"] is True, f"Tur artık tamamlandı — gelen: {r4.json()}")
basarili(r4.json()["tamamlanan_katman_sayisi"] == 2, "2/2 katman tamamlandı")
basarili(r4.json()["sonraki_tur_tarihi"] is not None, f"Tur bitince sonraki tur tarihi hesaplandı — gelen: {r4.json()['sonraki_tur_tarihi']}")

r4b = client.get("/ogrenci/katmanlar", headers=headers)
durumlar2 = {k["kod"]: k["durum"] for k in r4b.json()}
basarili(durumlar2["K1"] == "tamamlandi" and durumlar2["K2"] == "tamamlandi", f"Her iki katman da 'tamamlandi' — gelen: {durumlar2}")

print()
print("TÜM DURUM ÖZETİ TESTLERİ GEÇTİ ✓")
