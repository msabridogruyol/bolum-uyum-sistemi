"""D3 — K5 dal derinleşme tetikleme + dal soru akışı testi."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_k5.db"

import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from app.core.database import Base, engine, SessionLocal
from app import models
from app.main import app

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

k4 = models.Katman(kod="K4", ad="Alan Eğilimi", sira=4, normalizasyon_agirligi=40, kosullu_mu=False)
k5 = models.Katman(kod="K5", ad="Dal Derinleşme", sira=5, normalizasyon_agirligi=None, kosullu_mu=True)
db.add_all([k4, k5]); db.flush()
k5.tetikleyici_katman_id = k4.id
db.flush()

deg_sayisal = models.Degisken(katman_id=k4.id, kod="K4_SAYISAL", ad="Sayısal", sira=1)
db.add(deg_sayisal); db.flush()

soru_k4 = models.Soru(katman_id=k4.id, degisken_id=deg_sayisal.id, soru_tipi="likert",
                       soru_metni="Sayısal problem çözmekten keyif alırım.", aktif_mi=True)
db.add(soru_k4); db.flush()
for i, metin in enumerate(["Kesinlikle katılmıyorum", "Katılmıyorum", "Kararsızım", "Katılıyorum", "Kesinlikle katılıyorum"], start=1):
    db.add(models.SoruSecenegi(soru_id=soru_k4.id, secenek_sirasi=i, secenek_metni=metin))
db.flush()

dal_d01 = models.Dal(kod="D01", ad="Mühendislik — Sayısal", bagli_degisken_id=deg_sayisal.id, dogrulama_durumu="taslak")
db.add(dal_d01); db.flush()

deg_d01_ozel = models.Degisken(katman_id=k5.id, kod="D01_OZEL", ad="Mekanizma Merakı", sira=1, dal_id=dal_d01.id)
db.add(deg_d01_ozel); db.flush()

soru_k5 = models.Soru(katman_id=k5.id, degisken_id=deg_d01_ozel.id, soru_tipi="likert",
                       soru_metni="Bir mekanizmanın nasıl çalıştığını elimle keşfetmek beni çeker.", aktif_mi=True)
db.add(soru_k5); db.flush()
for i, metin in enumerate(["Kesinlikle katılmıyorum", "Katılmıyorum", "Kararsızım", "Katılıyorum", "Kesinlikle katılıyorum"], start=1):
    db.add(models.SoruSecenegi(soru_id=soru_k5.id, secenek_sirasi=i, secenek_metni=metin))
db.commit()
soru_k5_id = soru_k5.id
db.close()

client = TestClient(app)

def basarili(kosul, mesaj):
    print(("✓ " if kosul else "✗ ") + mesaj)
    assert kosul, mesaj

client.post("/auth/kayit", json={"ad_soyad": "K5 Test", "email": "k5test@ornek.com", "sifre": "sifre1234"})
r = client.post("/auth/giris", json={"email": "k5test@ornek.com", "sifre": "sifre1234"})
headers = {"Authorization": f"Bearer {r.json()['erisim_tokeni']}"}

# 1) K4 tamamlanmadan K5 durumu — hiçbir şey açılmamış olmalı
r1 = client.get("/ogrenci/k5/durum", headers=headers)
basarili(r1.status_code == 200, f"K5 durum uç noktası çalışıyor — {r1.status_code}")
basarili(r1.json()["acilan"] == [], f"K4 tamamlanmadan hiçbir dal açılmamış — gelen: {r1.json()}")

# 2) K4'ü başlat ve en yüksek puanla (100) cevapla — eşik (80) rahatça geçilsin
rb = client.post("/ogrenci/katmanlar/K4/basla", headers=headers)
soru_id = rb.json()["sorular"][0]["id"]
secenek_id_5 = rb.json()["sorular"][0]["secenekler"][4]["id"]  # sıra=5 -> puan=100
client.post("/ogrenci/katmanlar/K4/cevap", json={"soru_id": soru_id, "secenek_id": secenek_id_5}, headers=headers)

rt = client.post("/ogrenci/katmanlar/K4/tamamla", headers=headers)
basarili(rt.status_code == 200, f"K4 tamamlandı — {rt.status_code} {rt.text}")
basarili(rt.json()["tum_katmanlar_tamamlandi_mi"] is True, "Tek ana katman (K4) olduğu için tur tamamlandı")

# 3) K5 durumu — D01 şimdi açılmış olmalı (puan 100 >= eşik 80)
r3 = client.get("/ogrenci/k5/durum", headers=headers)
acilan = r3.json()["acilan"]
basarili(len(acilan) == 1 and acilan[0]["dal_kodu"] == "D01", f"D01 açıldı — gelen: {acilan}")
basarili(abs(acilan[0]["puan"] - 100.0) < 0.01, f"Açılan dalın puanı doğru taşındı — gelen: {acilan[0]['puan']}")

# 4) Açılmamış bir dalı başlatmaya çalışmak reddedilmeli
r4 = client.post("/ogrenci/dallar/D99/basla", headers=headers)
basarili(r4.status_code == 400, f"Var olmayan dal reddedildi — {r4.status_code}")

# 5) D01'i başlat — K5'e özgü soru dönmeli (K4'teki soru DEĞİL)
r5 = client.post("/ogrenci/dallar/D01/basla", headers=headers)
basarili(r5.status_code == 200, f"D01 başlatıldı — {r5.status_code} {r5.text}")
d01_sorular = r5.json()["sorular"]
basarili(len(d01_sorular) == 1 and d01_sorular[0]["id"] == soru_k5_id, f"K5'e özgü soru döndü — gelen: {d01_sorular}")

# 6) D01'in sorusunu cevapla (sıra=4 -> puan=75) ve tamamla
secenek_id_4 = d01_sorular[0]["secenekler"][3]["id"]
client.post("/ogrenci/dallar/D01/cevap", json={"soru_id": soru_k5_id, "secenek_id": secenek_id_4}, headers=headers)
r6 = client.post("/ogrenci/dallar/D01/tamamla", headers=headers)
basarili(r6.status_code == 200, f"D01 tamamlandı — {r6.status_code} {r6.text}")
sonuc_puan = r6.json()["sonuclar"][0]["puan"]
basarili(abs(sonuc_puan - 75.0) < 0.01, f"Dal-içi puan doğru hesaplandı (75 bekleniyor) — gelen: {sonuc_puan}")

# 7) Tamamlanan dalı tekrar tamamlamaya çalışmak reddedilmeli
r7 = client.post("/ogrenci/dallar/D01/basla", headers=headers)
basarili(r7.status_code == 400, f"Tamamlanan dal tekrar başlatılamaz — {r7.status_code}")

print()
print("TÜM D3/K5 TESTLERİ GEÇTİ ✓")
