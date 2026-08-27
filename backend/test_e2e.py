"""Uçtan uca entegrasyon testi — D1 (auth) + D2 (katman akışı)."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test.db"
import sys
sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from app.core.database import Base, engine, SessionLocal
from app import models
from app.main import app

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()
k1 = models.Katman(kod="K1", ad="Değerler / Motivasyon", sira=1, normalizasyon_agirligi=20, kosullu_mu=False)
db.add(k1); db.flush()
deg_anlam = models.Degisken(katman_id=k1.id, kod="K1_ANLAM", ad="Anlam", sira=1)
deg_guvence = models.Degisken(katman_id=k1.id, kod="K1_GUVENCE", ad="Güvence", sira=2)
db.add_all([deg_anlam, deg_guvence]); db.flush()
soru1 = models.Soru(katman_id=k1.id, degisken_id=deg_anlam.id, soru_tipi="likert",
                     soru_metni="İşimin bir anlam taşıması benim için önemlidir.", aktif_mi=True)
soru2 = models.Soru(katman_id=k1.id, degisken_id=deg_guvence.id, soru_tipi="likert",
                     soru_metni="İş güvencesi benim için önceliklidir.", aktif_mi=True)
db.add_all([soru1, soru2]); db.flush()
for soru in (soru1, soru2):
    for i, metin in enumerate(["Kesinlikle katılmıyorum", "Katılmıyorum", "Kararsızım", "Katılıyorum", "Kesinlikle katılıyorum"], start=1):
        db.add(models.SoruSecenegi(soru_id=soru.id, secenek_sirasi=i, secenek_metni=metin))
db.commit(); db.close()

client = TestClient(app)
def basarili(kosul, mesaj):
    print(("✓ " if kosul else "✗ ") + mesaj); assert kosul, mesaj

r = client.post("/auth/kayit", json={"ad_soyad": "Test Öğrenci", "email": "test@ornek.com", "sifre": "sifre1234"})
basarili(r.status_code == 201, f"Kayıt başarılı — {r.status_code}")
r2 = client.post("/auth/kayit", json={"ad_soyad": "Test Öğrenci", "email": "test@ornek.com", "sifre": "sifre1234"})
basarili(r2.status_code == 400, f"Yinelenen e-posta reddedildi — {r2.status_code}")
r3 = client.post("/auth/giris", json={"email": "test@ornek.com", "sifre": "yanlissifre"})
basarili(r3.status_code == 401, f"Yanlış şifre reddedildi — {r3.status_code}")
r4 = client.post("/auth/giris", json={"email": "test@ornek.com", "sifre": "sifre1234"})
basarili(r4.status_code == 200, f"Giriş başarılı — {r4.status_code}")
tokenlar = r4.json()
headers = {"Authorization": f"Bearer {tokenlar['erisim_tokeni']}"}
r5 = client.get("/ogrenci/katmanlar")
basarili(r5.status_code == 401, f"Tokensız istek reddedildi — {r5.status_code}")
r6 = client.get("/ogrenci/katmanlar", headers=headers)
basarili(r6.status_code == 200 and len(r6.json()) == 1, f"Katman listesi döndü")
r7 = client.post("/ogrenci/katmanlar/K1/basla", headers=headers)
basarili(r7.status_code == 200, f"Katman başlatıldı — {r7.status_code} {r7.text}")
veri = r7.json()
basarili(len(veri["sorular"]) == 2, "2 soru döndü")
r7b = client.post("/ogrenci/katmanlar/K1/basla", headers=headers)
basarili(veri["sorular"][0]["id"] == r7b.json()["sorular"][0]["id"], "Kilitlenen soru seti tutarlı")
soru1_id = veri["sorular"][0]["id"]; soru2_id = veri["sorular"][1]["id"]
secenek1_id = veri["sorular"][0]["secenekler"][3]["id"]
secenek2_id = veri["sorular"][1]["secenekler"][0]["id"]
r9 = client.post("/ogrenci/katmanlar/K1/tamamla", headers=headers)
basarili(r9.status_code == 400, f"Eksik cevapla tamamlama reddedildi — {r9.status_code}")
c1 = client.post("/ogrenci/katmanlar/K1/cevap", json={"soru_id": soru1_id, "secenek_id": secenek1_id}, headers=headers)
c2 = client.post("/ogrenci/katmanlar/K1/cevap", json={"soru_id": soru2_id, "secenek_id": secenek2_id}, headers=headers)
basarili(c1.status_code == 204 and c2.status_code == 204, "Cevaplar kaydedildi")
r11 = client.post("/ogrenci/katmanlar/K1/tamamla", headers=headers)
basarili(r11.status_code == 200, f"Katman tamamlandı — {r11.status_code} {r11.text}")
sonuc = r11.json()
puanlar = {s["degisken_adi"]: s["puan"] for s in sonuc["sonuclar"]}
basarili(abs(puanlar["Anlam"] - 75.0) < 0.01, f"Likert formülü doğru (Anlam=75) — {puanlar['Anlam']}")
basarili(abs(puanlar["Güvence"] - 0.0) < 0.01, f"Likert formülü doğru (Güvence=0) — {puanlar['Güvence']}")
basarili(sonuc["tum_katmanlar_tamamlandi_mi"] is True, "Tur tamamlandı")
r12 = client.post("/ogrenci/katmanlar/K1/basla", headers=headers)
basarili(r12.status_code == 400, f"120 gün kısıtı doğru çalışıyor — {r12.status_code}")
r13 = client.post("/auth/yenile", json={"yenileme_tokeni": tokenlar["yenileme_tokeni"]})
basarili(r13.status_code == 200, f"Token yenileme başarılı — {r13.status_code}")
print("\nTÜM D1/D2 TESTLERİ GEÇTİ ✓")
