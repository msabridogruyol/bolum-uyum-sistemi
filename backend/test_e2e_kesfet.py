"""D5, Katman 2 — Tüm Bölümleri Keşfet testi."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_kesfet.db"
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

# --- 2 katman, her birinde 1 değişken ---
k1 = models.Katman(kod="K1", ad="K1", sira=1, normalizasyon_agirligi=50, kosullu_mu=False)
k2 = models.Katman(kod="K2", ad="K2", sira=2, normalizasyon_agirligi=50, kosullu_mu=False)
db.add_all([k1, k2]); db.flush()
d1 = models.Degisken(katman_id=k1.id, kod="D1", ad="D1", sira=1)
d2a = models.Degisken(katman_id=k2.id, kod="D2A", ad="D2A", sira=1)
d2b = models.Degisken(katman_id=k2.id, kod="D2B", ad="D2B", sira=2)
db.add_all([d1, d2a, d2b]); db.flush()

# --- Bölümler: "Bilgisayar Mühendisliği", "Bilgisayar Bilimleri", "Tarih" ---
b1 = models.Bolum(ad="Bilgisayar Mühendisliği", durum="yayinda", kisa_aciklama="Yazılım ve donanım sistemleri.")
b2 = models.Bolum(ad="Bilgisayar Bilimleri", durum="yayinda", kisa_aciklama="Teorik bilgisayar bilimi.")
b3 = models.Bolum(ad="Tarih", durum="yayinda", kisa_aciklama=None)
b4_taslak = models.Bolum(ad="Bilgisayar Oyunları Tasarımı", durum="taslak")  # yayında değil
db.add_all([b1, b2, b3, b4_taslak]); db.flush()

# b1: K1=90, K2 ortalaması=(80+60)/2=70
db.add(models.BolumAgirligi(bolum_id=b1.id, degisken_id=d1.id, agirlik_degeri=90, yakinsama_skoru=0.02, versiyon=1))
db.add(models.BolumAgirligi(bolum_id=b1.id, degisken_id=d2a.id, agirlik_degeri=80, yakinsama_skoru=0.02, versiyon=1))
db.add(models.BolumAgirligi(bolum_id=b1.id, degisken_id=d2b.id, agirlik_degeri=60, yakinsama_skoru=0.02, versiyon=1))
# b2: K1=50, K2 ortalaması=(40+40)/2=40
db.add(models.BolumAgirligi(bolum_id=b2.id, degisken_id=d1.id, agirlik_degeri=50, yakinsama_skoru=0.02, versiyon=1))
db.add(models.BolumAgirligi(bolum_id=b2.id, degisken_id=d2a.id, agirlik_degeri=40, yakinsama_skoru=0.02, versiyon=1))
db.add(models.BolumAgirligi(bolum_id=b2.id, degisken_id=d2b.id, agirlik_degeri=40, yakinsama_skoru=0.02, versiyon=1))
db.commit()

client = TestClient(app)
client.post("/auth/kayit", json={"ad_soyad": "Keşfet Test", "email": "kesfet@ornek.com", "sifre": "sifre1234"})
r = client.post("/auth/giris", json={"email": "kesfet@ornek.com", "sifre": "sifre1234"})
headers = {"Authorization": f"Bearer {r.json()['erisim_tokeni']}"}

# 1) K1-K4 tamamlanmadan bile arama çalışmalı, ama toplam_uyum null olmalı
r1 = client.get("/ogrenci/sonuc/kesfet?q=Bilgisayar", headers=headers)
basarili(r1.status_code == 200, f"Arama çalışıyor — {r1.status_code} {r1.text}")
veri = r1.json()
basarili(len(veri) == 2, f"2 'Bilgisayar' içeren yayında bölüm bulundu (taslak hariç) — gelen: {[v['bolum_adi'] for v in veri]}")
basarili(all(v["toplam_uyum"] is None for v in veri), f"Profil tamamlanmadan toplam_uyum null — gelen: {[v['toplam_uyum'] for v in veri]}")

# 2) Katman ortalamaları doğru hesaplanmalı
b1_veri = next(v for v in veri if v["bolum_adi"] == "Bilgisayar Mühendisliği")
basarili(abs(b1_veri["katman_ortalamalari"]["K1"] - 90.0) < 0.01, f"K1 ortalaması doğru — gelen: {b1_veri['katman_ortalamalari']}")
basarili(abs(b1_veri["katman_ortalamalari"]["K2"] - 70.0) < 0.01, f"K2 ortalaması doğru (80,60 ortalaması) — gelen: {b1_veri['katman_ortalamalari']}")
basarili(b1_veri["kisa_aciklama"] == "Yazılım ve donanım sistemleri.", "Kısa açıklama doğru döndü")

# 3) "Tarih" araması yalnızca Tarih'i bulmalı, kısa_aciklama None olabilir (sorun değil)
r3 = client.get("/ogrenci/sonuc/kesfet?q=Tarih", headers=headers)
veri3 = r3.json()
basarili(len(veri3) == 1 and veri3[0]["bolum_adi"] == "Tarih", f"Tarih araması doğru sonuç veriyor — gelen: {veri3}")
basarili(veri3[0]["kisa_aciklama"] is None, "Kısa açıklaması olmayan bölüm hata vermiyor, null dönüyor")

# 4) Kısa arama terimi reddedilmeli
r4 = client.get("/ogrenci/sonuc/kesfet?q=B", headers=headers)
basarili(r4.status_code == 400, f"Çok kısa arama terimi reddedildi — {r4.status_code}")

# 5) Taslak bölüm hiçbir aramada çıkmamalı
r5 = client.get("/ogrenci/sonuc/kesfet?q=Oyunları", headers=headers)
basarili(r5.json() == [], f"Taslak bölüm arama sonucunda yok — gelen: {r5.json()}")

print()
print("TÜM KEŞFET TESTLERİ GEÇTİ ✓")
