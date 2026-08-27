"""D4 — TOPLAM_UYUM'un tam HTTP akışı üzerinden testi."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_d4.db"
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

# --- 4 ana katman, her birinde 1 soru/değişken (basitleştirilmiş) ---
katmanlar, degiskenler, sorular = {}, {}, {}
for kod, agirlik in [("K1", 20), ("K2", 15), ("K3", 25), ("K4", 40)]:
    k = models.Katman(kod=kod, ad=kod, sira=int(kod[1]), normalizasyon_agirligi=agirlik, kosullu_mu=False)
    db.add(k); db.flush()
    katmanlar[kod] = k
    d = models.Degisken(katman_id=k.id, kod=f"{kod}_D", ad=f"{kod} Değişkeni", sira=1)
    db.add(d); db.flush()
    degiskenler[kod] = d
    s = models.Soru(katman_id=k.id, degisken_id=d.id, soru_tipi="likert", soru_metni=f"{kod} sorusu", aktif_mi=True)
    db.add(s); db.flush()
    sorular[kod] = s
    for i, metin in enumerate(["1", "2", "3", "4", "5"], start=1):
        db.add(models.SoruSecenegi(soru_id=s.id, secenek_sirasi=i, secenek_metni=metin))
db.flush()

# --- 2 bölüm: biri öğrenciye çok yakın (yüksek puanlar), biri uzak ---
bolum_yakin = models.Bolum(ad="Bilgisayar Mühendisliği", durum="yayinda")
bolum_uzak = models.Bolum(ad="Güzel Sanatlar", durum="yayinda")
db.add_all([bolum_yakin, bolum_uzak]); db.flush()
for kod in ["K1", "K2", "K3", "K4"]:
    db.add(models.BolumAgirligi(bolum_id=bolum_yakin.id, degisken_id=degiskenler[kod].id, agirlik_degeri=100, yakinsama_skoru=0.02, versiyon=1))
    db.add(models.BolumAgirligi(bolum_id=bolum_uzak.id, degisken_id=degiskenler[kod].id, agirlik_degeri=0, yakinsama_skoru=0.02, versiyon=1))
db.commit(); db.close()

client = TestClient(app)
client.post("/auth/kayit", json={"ad_soyad": "D4 Test", "email": "d4test@ornek.com", "sifre": "sifre1234"})
r = client.post("/auth/giris", json={"email": "d4test@ornek.com", "sifre": "sifre1234"})
headers = {"Authorization": f"Bearer {r.json()['erisim_tokeni']}"}

# 1) K1-K3'ü tamamla (henüz sıralama olmamalı, D4 kuralı: yarım profil)
for kod in ["K1", "K2", "K3"]:
    rb = client.post(f"/ogrenci/katmanlar/{kod}/basla", headers=headers)
    soru_id = rb.json()["sorular"][0]["id"]
    secenek_id = rb.json()["sorular"][0]["secenekler"][4]["id"]  # en yüksek puan (100)
    client.post(f"/ogrenci/katmanlar/{kod}/cevap", json={"soru_id": soru_id, "secenek_id": secenek_id}, headers=headers)
    client.post(f"/ogrenci/katmanlar/{kod}/tamamla", headers=headers)

r_erken = client.get("/ogrenci/sonuc/siralama", headers=headers)
basarili(r_erken.status_code == 200 and r_erken.json() == [], f"K4 bitmeden sıralama boş dönüyor (D4 kuralı) — gelen: {r_erken.json()}")

# 2) K4'ü de tamamla — TOPLAM_UYUM otomatik tetiklenmeli
rb4 = client.post("/ogrenci/katmanlar/K4/basla", headers=headers)
soru4_id = rb4.json()["sorular"][0]["id"]
secenek4_id = rb4.json()["sorular"][0]["secenekler"][4]["id"]
client.post("/ogrenci/katmanlar/K4/cevap", json={"soru_id": soru4_id, "secenek_id": secenek4_id}, headers=headers)
r_tamamla = client.post("/ogrenci/katmanlar/K4/tamamla", headers=headers)
basarili(r_tamamla.json()["tum_katmanlar_tamamlandi_mi"] is True, "K4 sonrası tur tamamlandı")

# 3) Sıralama artık dolu olmalı, doğru sırada, admin-only alan İÇERMEMELİ
r_siralama = client.get("/ogrenci/sonuc/siralama", headers=headers)
basarili(r_siralama.status_code == 200, f"Sıralama uç noktası çalışıyor — {r_siralama.status_code}")
veri = r_siralama.json()
basarili(len(veri) == 2, f"2 bölüm döndü — gelen: {len(veri)}")
basarili(veri[0]["bolum_adi"] == "Bilgisayar Mühendisliği", f"Yakın bölüm 1. sırada — gelen: {veri}")
basarili(veri[0]["toplam_uyum"] > veri[1]["toplam_uyum"], f"Sıralama azalan uyum puanına göre — {veri[0]['toplam_uyum']} vs {veri[1]['toplam_uyum']}")

# --- KRİTİK GÜVENLİK KONTROLÜ: admin-only alanlar response'ta HİÇ olmamalı ---
ham_json_metni = r_siralama.text
basarili("yontem_skorlari" not in ham_json_metni, "yontem_skorlari öğrenci response'unda YOK (kritik kural)")
basarili("kendall_w" not in ham_json_metni, "kendall_w öğrenci response'unda YOK (kritik kural)")
basarili("WSM" not in ham_json_metni and "TOPSIS" not in ham_json_metni, "Yöntem isimleri response'ta YOK (kritik kural)")
basarili(set(veri[0].keys()) == {"bolum_id", "bolum_adi", "toplam_uyum"}, f"Response yalnızca 3 izinli alanı içeriyor — gelen alanlar: {set(veri[0].keys())}")

print()
print("TÜM D4 TESTLERİ GEÇTİ ✓ (admin-only alan sızıntısı yok)")
