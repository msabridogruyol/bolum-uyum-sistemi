"""Skor motoru izole testi — API katmanı olmadan, doğrudan fonksiyon çağrılarıyla."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_skor.db"
import sys
sys.path.insert(0, ".")

from app.core.database import Base, engine, SessionLocal
from app import models
from app.core.skor_motoru import toplam_uyum_hesapla, siralama_getir, girdi_hazirla

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

def basarili(kosul, mesaj):
    print(("✓ " if kosul else "✗ ") + mesaj)
    assert kosul, mesaj

# --- 4 ana katman, her birinde 1 değişken (basitleştirilmiş) ---
katmanlar = {}
for kod, agirlik in [("K1", 20), ("K2", 15), ("K3", 25), ("K4", 40)]:
    k = models.Katman(kod=kod, ad=kod, sira=int(kod[1]), normalizasyon_agirligi=agirlik, kosullu_mu=False)
    db.add(k)
    katmanlar[kod] = k
db.flush()

degiskenler = {}
for kod, katman_kod in [("D1", "K1"), ("D2", "K2"), ("D3", "K3"), ("D4", "K4")]:
    d = models.Degisken(katman_id=katmanlar[katman_kod].id, kod=kod, ad=kod, sira=1)
    db.add(d)
    degiskenler[kod] = d
db.flush()

# --- 3 bölüm: biri öğrenciyle NEREDEYSE AYNI, biri ORTA, biri TAMAMEN ZIT ---
bolum_yakin = models.Bolum(ad="Yakın Bölüm", durum="yayinda")
bolum_orta = models.Bolum(ad="Orta Bölüm", durum="yayinda")
bolum_zit = models.Bolum(ad="Zıt Bölüm", durum="yayinda")
bolum_taslak = models.Bolum(ad="Taslak Bölüm", durum="taslak")  # yayında değil -> hesaba katılmamalı
db.add_all([bolum_yakin, bolum_orta, bolum_zit, bolum_taslak])
db.flush()

# Öğrenci profili: D1=80, D2=60, D3=40, D4=90
ogrenci_profili = {"D1": 80, "D2": 60, "D3": 40, "D4": 90}
# Yakın bölüm: öğrenciyle neredeyse aynı (küçük gap'ler)
bolum_profilleri = {
    bolum_yakin.id: {"D1": 82, "D2": 58, "D3": 42, "D4": 88},
    bolum_orta.id:  {"D1": 60, "D2": 60, "D3": 60, "D4": 60},
    bolum_zit.id:   {"D1": 20, "D2": 90, "D3": 90, "D4": 10},
    bolum_taslak.id: {"D1": 82, "D2": 58, "D3": 42, "D4": 88},  # yakın olsa da yayında değil
}
for bolum_id, profil in bolum_profilleri.items():
    for kod, deger in profil.items():
        db.add(models.BolumAgirligi(
            bolum_id=bolum_id, degisken_id=degiskenler[kod].id,
            agirlik_degeri=deger, yakinsama_skoru=0.05, versiyon=1,
        ))
db.flush()

# --- Öğrenci + tur + değişken skorları ---
ogrenci = models.Ogrenci(ad_soyad="Skor Test", email="skor@ornek.com", sifre_hash="x")
db.add(ogrenci); db.flush()
tur = models.OgrenciDegerlendirmeTuru(ogrenci_id=ogrenci.id, tur_no=1, durum="tamamlandi")
db.add(tur); db.flush()
for kod, puan in ogrenci_profili.items():
    db.add(models.OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur.id, degisken_id=degiskenler[kod].id, puan=puan))
db.commit()

# ============ TESTLER ============

girdi = girdi_hazirla(db, ogrenci, tur)
basarili(girdi is not None, "Girdi hazırlama başarılı")
basarili(len(girdi.bolum_idler) == 3, f"Yalnızca 'yayinda' bölümler alındı (3 bekleniyor) — gelen: {len(girdi.bolum_idler)}")
basarili(abs(girdi.agirliklar.sum() - 1.0) < 1e-6, f"Kriter ağırlıkları toplamı 1 — gelen: {girdi.agirliklar.sum()}")

n = toplam_uyum_hesapla(db, ogrenci, tur)
db.commit()
basarili(n == 3, f"3 bölüm için skor üretildi — gelen: {n}")

siralama = siralama_getir(db, ogrenci, tur, ilk_n=10)
basarili(len(siralama) == 3, f"Sıralama 3 bölüm döndürüyor — gelen: {len(siralama)}")

isimler_sirali = [girdi.bolum_adlari[s.bolum_id] for s in siralama]
basarili(isimler_sirali[0] == "Yakın Bölüm", f"En yakın bölüm 1. sırada — gelen sıra: {isimler_sirali}")
basarili(isimler_sirali[-1] == "Zıt Bölüm", f"En zıt bölüm son sırada — gelen sıra: {isimler_sirali}")
basarili(isimler_sirali[1] == "Orta Bölüm", f"Orta bölüm ortada — gelen sıra: {isimler_sirali}")

skor_yakin = next(s for s in siralama if s.bolum_id == bolum_yakin.id)
skor_zit = next(s for s in siralama if s.bolum_id == bolum_zit.id)
basarili(float(skor_yakin.toplam_uyum) > float(skor_zit.toplam_uyum), f"Yakın bölümün skoru zıttan yüksek — {float(skor_yakin.toplam_uyum)} vs {float(skor_zit.toplam_uyum)}")
basarili(abs(float(skor_yakin.toplam_uyum) - 100.0) < 1.0, f"En yakın bölüm ~100 puan almalı (min-max normalize) — gelen: {float(skor_yakin.toplam_uyum)}")
basarili(abs(float(skor_zit.toplam_uyum) - 0.0) < 1.0, f"En zıt bölüm ~0 puan almalı — gelen: {float(skor_zit.toplam_uyum)}")

basarili(skor_yakin.kendall_w is not None and 0 <= skor_yakin.kendall_w <= 1, f"Kendall's W [0,1] aralığında — gelen: {skor_yakin.kendall_w}")
basarili(isinstance(skor_yakin.yontem_skorlari, dict) and len(skor_yakin.yontem_skorlari) == 10, f"10 yöntemin hepsi skor üretti — gelen: {list(skor_yakin.yontem_skorlari.keys()) if skor_yakin.yontem_skorlari else None}")

# --- İdempotentlik: tekrar çalıştırınca eski skorlar silinip yeniden yazılmalı, çoğalmamalı ---
n2 = toplam_uyum_hesapla(db, ogrenci, tur)
db.commit()
from app.models import OgrenciBolumUyumSkoru
toplam_kayit = db.query(OgrenciBolumUyumSkoru).filter(OgrenciBolumUyumSkoru.ogrenci_id == ogrenci.id, OgrenciBolumUyumSkoru.tur_id == tur.id).count()
basarili(toplam_kayit == 3, f"Tekrar hesaplama eski kayıtları çoğaltmıyor (3 bekleniyor) — gelen: {toplam_kayit}")

print()
print("TÜM SKOR MOTORU TESTLERİ GEÇTİ ✓")
