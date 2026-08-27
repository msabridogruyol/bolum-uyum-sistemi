"""Bölüm F — Koçluk modülü uçtan uca testi."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_f.db"
import sys
sys.path.insert(0, ".")

from datetime import datetime, timedelta, timezone
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

# --- İçerik: 1 katman, 2 değişken (biri güçlü, biri gelişim alanı) ---
k1 = models.Katman(kod="K1", ad="K1", sira=1, normalizasyon_agirligi=100, kosullu_mu=False)
db.add(k1); db.flush()
deg_guclu = models.Degisken(katman_id=k1.id, kod="GUCLU", ad="Analitik Düşünce", sira=1)
deg_zayif = models.Degisken(katman_id=k1.id, kod="ZAYIF", ad="Zaman Yönetimi", sira=2)
db.add_all([deg_guclu, deg_zayif]); db.flush()

# --- Gelişim kartı havuzu — yalnızca ZAYIF/belirgin_altinda için bir satır ekleyelim (içerik kısmi) ---
db.add(models.GelisimYorumHavuzu(
    degisken_id=deg_zayif.id, aralik="belirgin_altinda",
    durum_tespiti="Zaman yönetiminde belirgin bir gelişim alanın var.",
    aksiyon_onerisi="Küçük projelerde son teslim tarihi belirle.",
    kaynak_tipi="aliskanlik", tahmini_efor="orta",
))
db.commit()

# --- Bölüm: GUCLU'da yüksek beklenti (öğrenci zaten güçlü), ZAYIF'ta yüksek beklenti (öğrenci zayıf, büyük gap) ---
bolum = models.Bolum(ad="Bilgisayar Mühendisliği", durum="yayinda")
db.add(bolum); db.flush()
db.add(models.BolumAgirligi(bolum_id=bolum.id, degisken_id=deg_guclu.id, agirlik_degeri=80, yakinsama_skoru=0.02, versiyon=1))
db.add(models.BolumAgirligi(bolum_id=bolum.id, degisken_id=deg_zayif.id, agirlik_degeri=90, yakinsama_skoru=0.02, versiyon=1))

bolum2 = models.Bolum(ad="Edebiyat", durum="yayinda")
db.add(bolum2); db.flush()
db.add(models.BolumAgirligi(bolum_id=bolum2.id, degisken_id=deg_guclu.id, agirlik_degeri=50, yakinsama_skoru=0.02, versiyon=1))
db.add(models.BolumAgirligi(bolum_id=bolum2.id, degisken_id=deg_zayif.id, agirlik_degeri=50, yakinsama_skoru=0.02, versiyon=1))
db.commit()

bolum_id = bolum.id
bolum2_id = bolum2.id
deg_guclu_id = deg_guclu.id
deg_zayif_id = deg_zayif.id

# --- Öğrenciyi API üzerinden kayıt ettir (gerçek bcrypt hash için), sonra
#     DB'den çekip tur/skor verisini buna bağla ---
client = TestClient(app)
client.post("/auth/kayit", json={"ad_soyad": "F Test", "email": "ftest@ornek.com", "sifre": "sifre1234"})
ogrenci = db.query(models.Ogrenci).filter(models.Ogrenci.email == "ftest@ornek.com").first()

simdi = datetime.now(timezone.utc)
tur1 = models.OgrenciDegerlendirmeTuru(ogrenci_id=ogrenci.id, tur_no=1, durum="tamamlandi",
                                        baslama_zamani=simdi - timedelta(days=200), tamamlanma_zamani=simdi - timedelta(days=190))
db.add(tur1); db.flush()
db.add(models.OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur1.id, degisken_id=deg_guclu.id, puan=70))
db.add(models.OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur1.id, degisken_id=deg_zayif.id, puan=30))

tur2 = models.OgrenciDegerlendirmeTuru(ogrenci_id=ogrenci.id, tur_no=2, durum="tamamlandi",
                                        baslama_zamani=simdi - timedelta(days=10), tamamlanma_zamani=simdi - timedelta(days=1))
db.add(tur2); db.flush()
# GUCLU: 70->90 (öğrenci gerçekten güçlü, bölüm beklentisi 80 -> gap=+10 "üstün")
# ZAYIF: 30->45 (gelişim var ama hâlâ düşük, bölüm beklentisi 90 -> gap=-45 "belirgin_altinda")
db.add(models.OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur2.id, degisken_id=deg_guclu.id, puan=90))
db.add(models.OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur2.id, degisken_id=deg_zayif.id, puan=45))
db.commit(); db.close()

r = client.post("/auth/giris", json={"email": "ftest@ornek.com", "sifre": "sifre1234"})
headers = {"Authorization": f"Bearer {r.json()['erisim_tokeni']}"}

# 1) Hiç hedef yokken aktif hedef null dönmeli
r1 = client.get("/koclugu/hedef", headers=headers)
basarili(r1.status_code == 200 and r1.json() is None, f"Hiç hedef yokken null dönüyor — gelen: {r1.json()}")

# 2) İlk hedefi seç — onaysız da çalışmalı (henüz aktif hedef yok)
r2 = client.post("/koclugu/hedef", json={"bolum_id": bolum_id}, headers=headers)
basarili(r2.status_code == 200, f"İlk hedef seçimi başarılı — {r2.status_code} {r2.text}")
basarili(r2.json()["bolum_adi"] == "Bilgisayar Mühendisliği", "Doğru bölüm aktif hedef oldu")

# 3) Aynı bölümü tekrar seçmek no-op olmalı (200, hata değil)
r3 = client.post("/koclugu/hedef", json={"bolum_id": bolum_id}, headers=headers)
basarili(r3.status_code == 200, f"Aynı bölümü tekrar seçmek hata vermiyor — {r3.status_code}")

# 4) Farklı bölüme onaysız geçiş REDDEDİLMELİ (F8 — odaklanma ilkesi)
r4 = client.post("/koclugu/hedef", json={"bolum_id": bolum2_id, "onay": False}, headers=headers)
basarili(r4.status_code == 409, f"Onaysız hedef değişimi reddedildi — {r4.status_code} {r4.text}")

# 5) Onaylı geçiş kabul edilmeli
r5 = client.post("/koclugu/hedef", json={"bolum_id": bolum2_id, "onay": True}, headers=headers)
basarili(r5.status_code == 200 and r5.json()["bolum_adi"] == "Edebiyat", f"Onaylı hedef değişimi başarılı — {r5.json()}")

# 6) Eski hedefe geri dön (F8.2 — geçmiş silinmez, geri dönülebilir)
r6 = client.post("/koclugu/hedef", json={"bolum_id": bolum_id, "onay": True}, headers=headers)
basarili(r6.status_code == 200 and r6.json()["bolum_adi"] == "Bilgisayar Mühendisliği", "Eski hedefe geri dönülebiliyor")

# 7) Gap analizi — GUCLU'da üstün, ZAYIF'ta belirgin altında olmalı; öncelik ZAYIF'ta yüksek olmalı
r7 = client.get("/koclugu/hedef/gelisim", headers=headers)
basarili(r7.status_code == 200, f"Gap analizi çalışıyor — {r7.status_code} {r7.text}")
gap_veri = {g["degisken_adi"]: g for g in r7.json()}
basarili(gap_veri["Analitik Düşünce"]["kategori"] == "ustun", f"GUCLU kategorisi doğru (gap=+10) — gelen: {gap_veri['Analitik Düşünce']}")
basarili(gap_veri["Zaman Yönetimi"]["kategori"] == "belirgin_altinda", f"ZAYIF kategorisi doğru (gap=-45) — gelen: {gap_veri['Zaman Yönetimi']}")
basarili(gap_veri["Zaman Yönetimi"]["oncelik_skoru"] > gap_veri["Analitik Düşünce"]["oncelik_skoru"], "Büyük gap + yüksek bölüm ağırlığı -> yüksek öncelik")
basarili(gap_veri["Zaman Yönetimi"]["durum_tespiti"] is not None, "Havuzdaki gelişim kartı doğru eşleşti")
basarili(gap_veri["Analitik Düşünce"]["durum_tespiti"] is None, "Havuzda olmayan kategori için kart None (içerik henüz yazılmadı, hata değil)")

# 8) Yol haritası — ZAYIF (efor=orta) "bu_donem" grubunda olmalı
r8 = client.get("/koclugu/hedef/yol-haritasi", headers=headers)
basarili(r8.status_code == 200, f"Yol haritası çalışıyor — {r8.status_code}")
harita = r8.json()
basarili(len(harita["bu_donem"]) == 1 and harita["bu_donem"][0]["degisken_adi"] == "Zaman Yönetimi", f"ZAYIF 'bu_donem' grubunda — gelen: {harita}")
basarili(len(harita["simdi"]) == 0, "GUCLU gelişim gerektirmediği için hiçbir grupta yok (üstün kategori)")

# 9) Aksiyon durumu güncelleme
r9 = client.post(f"/koclugu/hedef/aksiyon/{deg_zayif_id}", json={"durum": "devam_ediyor"}, headers=headers)
basarili(r9.status_code == 204, f"Aksiyon durumu güncellendi — {r9.status_code}")
r9b = client.post(f"/koclugu/hedef/aksiyon/{deg_zayif_id}", json={"durum": "gecersiz_deger"}, headers=headers)
basarili(r9b.status_code == 400, f"Geçersiz durum reddedildi — {r9b.status_code}")

# 10) Tur karşılaştırması — GUCLU gelişim gösterdi (+20), ZAYIF de gelişim gösterdi (+15)
r10 = client.get("/koclugu/karsilastirma", headers=headers)
basarili(r10.status_code == 200, f"Tur karşılaştırması çalışıyor — {r10.status_code} {r10.text}")
karsilastirma = {k["degisken_adi"]: k for k in r10.json()}
basarili(abs(karsilastirma["Analitik Düşünce"]["degisim"] - 20.0) < 0.01, f"GUCLU değişimi doğru (+20) — gelen: {karsilastirma['Analitik Düşünce']}")
basarili(karsilastirma["Analitik Düşünce"]["trend"] == "belirgin_gelisim", f"GUCLU trend doğru — gelen: {karsilastirma['Analitik Düşünce']['trend']}")
basarili(abs(karsilastirma["Zaman Yönetimi"]["degisim"] - 15.0) < 0.01, f"ZAYIF değişimi doğru (+15) — gelen: {karsilastirma['Zaman Yönetimi']}")

print()
print("TÜM BÖLÜM F TESTLERİ GEÇTİ ✓")
