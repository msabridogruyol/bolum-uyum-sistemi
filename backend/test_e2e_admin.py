"""Admin uç noktaları testi — E5, E7, E8, E9 + yetkilendirme sınırları."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_admin.db"
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from app.core.database import Base, engine, SessionLocal
from app.core.security import sifre_hashle
from app import models
from app.main import app

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

def basarili(kosul, mesaj):
    print(("✓ " if kosul else "✗ ") + mesaj)
    assert kosul, mesaj

# --- 2 admin: biri super_admin, biri icerik_editoru ---
super_admin = models.AdminKullanici(ad_soyad="Süper Admin", email="super@ornek.com", sifre_hash=sifre_hashle("sifre1234"), rol="super_admin")
editor = models.AdminKullanici(ad_soyad="İçerik Editörü", email="editor@ornek.com", sifre_hash=sifre_hashle("sifre1234"), rol="icerik_editoru")
db.add_all([super_admin, editor]); db.flush()

# --- 1 sistem parametresi, 1 bölüm ---
db.add(models.SistemParametresi(anahtar="k5_esik_puani", deger="80", aciklama="test"))
bolum = models.Bolum(ad="Test Bölümü", durum="taslak")
db.add(bolum); db.flush()
bolum_id = bolum.id
db.commit(); db.close()

client = TestClient(app)

# --- Öğrenci hesabı da kayıt edelim (yetkisiz erişim testi için) ---
client.post("/auth/kayit", json={"ad_soyad": "Öğrenci", "email": "ogr@ornek.com", "sifre": "sifre1234"})
ogr_r = client.post("/auth/giris", json={"email": "ogr@ornek.com", "sifre": "sifre1234"})
ogr_headers = {"Authorization": f"Bearer {ogr_r.json()['erisim_tokeni']}"}

super_r = client.post("/admin/auth/giris", json={"email": "super@ornek.com", "sifre": "sifre1234"})
basarili(super_r.status_code == 200, f"Super admin girişi başarılı — {super_r.status_code} {super_r.text}")
super_headers = {"Authorization": f"Bearer {super_r.json()['erisim_tokeni']}"}

editor_r = client.post("/admin/auth/giris", json={"email": "editor@ornek.com", "sifre": "sifre1234"})
editor_headers = {"Authorization": f"Bearer {editor_r.json()['erisim_tokeni']}"}

# --- YETKİLENDİRME SINIRLARI ---

# 1) Öğrenci token'ıyla admin uç noktasına erişim REDDEDİLMELİ
r1 = client.get("/admin/parametreler", headers=ogr_headers)
basarili(r1.status_code == 401, f"Öğrenci token'ı admin uç noktasında reddedildi — {r1.status_code}")

# 2) Tokensız admin erişimi de reddedilmeli
r2 = client.get("/admin/parametreler")
basarili(r2.status_code == 401, f"Tokensız admin erişimi reddedildi — {r2.status_code}")

# 3) icerik_editoru parametre GÜNCELLEYEMEMELİ (yalnızca super_admin)
r3 = client.put("/admin/parametreler/k5_esik_puani", json={"deger": "85"}, headers=editor_headers)
basarili(r3.status_code == 403, f"icerik_editoru parametre güncelleyemiyor — {r3.status_code} {r3.text}")

# 4) icerik_editoru parametreyi GÖRÜNTÜLEYEBİLMELİ (herhangi bir admin rolü)
r4 = client.get("/admin/parametreler", headers=editor_headers)
basarili(r4.status_code == 200, f"icerik_editoru parametreleri görebiliyor — {r4.status_code}")

# --- E8 — Sistem Parametreleri ---

# 5) super_admin parametreyi güncelleyebilmeli
r5 = client.put("/admin/parametreler/k5_esik_puani", json={"deger": "85"}, headers=super_headers)
basarili(r5.status_code == 200 and r5.json()["deger"] == "85", f"super_admin parametreyi güncelledi — {r5.json()}")

# 6) Var olmayan parametre 404 dönmeli
r6 = client.put("/admin/parametreler/olmayan_parametre", json={"deger": "x"}, headers=super_headers)
basarili(r6.status_code == 404, f"Var olmayan parametre 404 — {r6.status_code}")

# --- E5 — Bölüm Durum Geçişi ---

# 7) taslak -> yayinda (ara adım atlanarak) REDDEDİLMELİ
r7 = client.post(f"/admin/bolumler/{bolum_id}/durum", json={"yeni_durum": "yayinda", "gerekce": "test"}, headers=super_headers)
basarili(r7.status_code == 400, f"taslak->yayinda geçişi reddedildi (ara adım atlanamaz) — {r7.status_code} {r7.text}")

# 8) Gerekçesiz geçiş reddedilmeli
r8 = client.post(f"/admin/bolumler/{bolum_id}/durum", json={"yeni_durum": "test_ediliyor", "gerekce": ""}, headers=super_headers)
basarili(r8.status_code == 400, f"Gerekçesiz geçiş reddedildi — {r8.status_code}")

# 9) taslak -> test_ediliyor geçerli olmalı
r9 = client.post(f"/admin/bolumler/{bolum_id}/durum", json={"yeni_durum": "test_ediliyor", "gerekce": "Pipeline'dan geçirildi"}, headers=super_headers)
basarili(r9.status_code == 200 and r9.json()["durum"] == "test_ediliyor", f"taslak->test_ediliyor geçişi başarılı — {r9.json()}")

# 10) test_ediliyor -> yayinda geçerli olmalı (icerik_editoru da yapabilmeli, E5'te rol kısıtı yok)
r10 = client.post(f"/admin/bolumler/{bolum_id}/durum", json={"yeni_durum": "yayinda", "gerekce": "Test kanıtları temiz"}, headers=editor_headers)
basarili(r10.status_code == 200 and r10.json()["durum"] == "yayinda", f"test_ediliyor->yayinda geçişi başarılı — {r10.json()}")

# 11) yayinda'dan başka bir duruma geçiş şu an desteklenmiyor (AÇIK KARAR olarak işaretlenmişti)
r11 = client.post(f"/admin/bolumler/{bolum_id}/durum", json={"yeni_durum": "taslak", "gerekce": "geri al"}, headers=super_headers)
basarili(r11.status_code == 400, f"yayinda'dan geri dönüş şu an desteklenmiyor (beklenen davranış) — {r11.status_code}")

# --- E9 — Audit Log ---

# 12) Yukarıdaki 3 geçerli işlem (parametre güncelleme + 2 durum geçişi) audit_log'a yazılmış olmalı
r12 = client.get("/admin/audit-log", headers=super_headers)
basarili(r12.status_code == 200, f"Audit log görüntülenebiliyor — {r12.status_code}")
basarili(len(r12.json()) == 3, f"3 audit log kaydı var (1 parametre + 2 durum geçişi) — gelen: {len(r12.json())}")
islemler = {log["islem"] for log in r12.json()}
basarili(islemler == {"parametre_guncelleme", "bolum_durum_degisikligi"}, f"İşlem türleri doğru — gelen: {islemler}")

# 13) Öğrenci listesi görüntülenebilmeli
r13 = client.get("/admin/ogrenciler", headers=super_headers)
basarili(r13.status_code == 200 and len(r13.json()) == 1, f"Öğrenci listesi doğru — gelen: {r13.json()}")

# --- E7 — Admin-only skor detayı (öğrenci API'sinden gizlenenin admin'e göründüğünün kanıtı) ---

# 14) Bir öğrenci profili + bölüm ağırlığı kurup TOPLAM_UYUM hesaplatalım
db2 = SessionLocal()
k1 = models.Katman(kod="K1", ad="K1", sira=1, normalizasyon_agirligi=100, kosullu_mu=False)
db2.add(k1); db2.flush()
deg = models.Degisken(katman_id=k1.id, kod="D1", ad="D1", sira=1)
db2.add(deg); db2.flush()
bolum_e7 = models.Bolum(ad="E7 Test Bölümü", durum="yayinda")
db2.add(bolum_e7); db2.flush()
db2.add(models.BolumAgirligi(bolum_id=bolum_e7.id, degisken_id=deg.id, agirlik_degeri=80, yakinsama_skoru=0.02, versiyon=1))
ogrenci_e7 = db2.query(models.Ogrenci).filter(models.Ogrenci.email == "ogr@ornek.com").first()
tur_e7 = models.OgrenciDegerlendirmeTuru(ogrenci_id=ogrenci_e7.id, tur_no=1, durum="tamamlandi")
db2.add(tur_e7); db2.flush()
db2.add(models.OgrenciDegiskenSkoru(ogrenci_id=ogrenci_e7.id, tur_id=tur_e7.id, degisken_id=deg.id, puan=80))
db2.commit()

from app.core.skor_motoru import toplam_uyum_hesapla
toplam_uyum_hesapla(db2, ogrenci_e7, tur_e7)
db2.commit()
ogrenci_e7_id = str(ogrenci_e7.id)
bolum_e7_id = bolum_e7.id
db2.close()

r14 = client.get(f"/admin/uyum-detay/{ogrenci_e7_id}/{bolum_e7_id}", headers=super_headers)
basarili(r14.status_code == 200, f"E7 admin-only detay uç noktası çalışıyor — {r14.status_code} {r14.text}")
veri14 = r14.json()
basarili(veri14["yontem_skorlari"] is not None and len(veri14["yontem_skorlari"]) == 10, f"yontem_skorlari admin'e TAM olarak görünüyor — gelen: {veri14['yontem_skorlari']}")
basarili(veri14["kendall_w"] is not None, f"kendall_w admin'e görünüyor — gelen: {veri14['kendall_w']}")
basarili("WSM" in veri14["yontem_skorlari"] and "TOPSIS" in veri14["yontem_skorlari"], "Yöntem isimleri admin response'unda tam olarak var")

# 15) Öğrenci token'ıyla bu uç noktaya erişim REDDEDİLMELİ (çift kontrol)
r15 = client.get(f"/admin/uyum-detay/{ogrenci_e7_id}/{bolum_e7_id}", headers=ogr_headers)
basarili(r15.status_code == 401, f"Öğrenci token'ı E7 uç noktasında da reddedildi — {r15.status_code}")

# --- Yönetici Yönetimi (yeni) ---

# 16) icerik_editoru yönetici EKLEYEMEMELİ (yalnızca super_admin)
r16 = client.post("/admin/yoneticiler", json={"ad_soyad": "Yeni Kişi", "email": "yeni@ornek.com", "sifre": "sifre1234", "rol": "icerik_editoru"}, headers=editor_headers)
basarili(r16.status_code == 403, f"icerik_editoru yönetici ekleyemiyor — {r16.status_code}")

# 17) super_admin yeni bir icerik_editoru ekleyebilmeli
r17 = client.post("/admin/yoneticiler", json={"ad_soyad": "Yeni Editör", "email": "yenieditor@ornek.com", "sifre": "sifre1234", "rol": "icerik_editoru"}, headers=super_headers)
basarili(r17.status_code == 201, f"super_admin yönetici ekledi — {r17.status_code} {r17.text}")
yeni_yonetici_id = r17.json()["id"]

# 18) Aynı e-posta ile tekrar eklemek reddedilmeli
r18 = client.post("/admin/yoneticiler", json={"ad_soyad": "Tekrar", "email": "yenieditor@ornek.com", "sifre": "sifre1234", "rol": "icerik_editoru"}, headers=super_headers)
basarili(r18.status_code == 400, f"Yinelenen yönetici e-postası reddedildi — {r18.status_code}")

# 19) Yeni eklenen yönetici gerçekten giriş yapabilmeli
r19 = client.post("/admin/auth/giris", json={"email": "yenieditor@ornek.com", "sifre": "sifre1234"})
basarili(r19.status_code == 200, f"Yeni eklenen yönetici giriş yapabiliyor — {r19.status_code}")

# 20) Yönetici listesi görüntülenebilmeli (en az 3: super_admin, editor, yenieditor)
r20 = client.get("/admin/yoneticiler", headers=super_headers)
basarili(r20.status_code == 200 and len(r20.json()) == 3, f"Yönetici listesi doğru — gelen: {len(r20.json())}")

# 21) Rol güncelleme — super_admin başka birinin rolünü değiştirebilmeli
r21 = client.put(f"/admin/yoneticiler/{yeni_yonetici_id}/rol", json={"yeni_rol": "super_admin"}, headers=super_headers)
basarili(r21.status_code == 200 and r21.json()["rol"] == "super_admin", f"Rol güncellendi — {r21.json()}")

# 22) KRİTİK: super_admin KENDİ rolünü değiştirememeli (kilitlenme koruması)
super_admin_id = super_r.json()  # token'dan id çıkaramayız, DB'den çekelim
db3 = SessionLocal()
super_admin_db_id = str(db3.query(models.AdminKullanici).filter(models.AdminKullanici.email == "super@ornek.com").first().id)
db3.close()
r22 = client.put(f"/admin/yoneticiler/{super_admin_db_id}/rol", json={"yeni_rol": "icerik_editoru"}, headers=super_headers)
basarili(r22.status_code == 400, f"super_admin kendi rolünü değiştiremiyor (kilitlenme koruması) — {r22.status_code} {r22.text}")

# 23) icerik_editoru rol güncelleyememeli
r23 = client.put(f"/admin/yoneticiler/{yeni_yonetici_id}/rol", json={"yeni_rol": "icerik_editoru"}, headers=editor_headers)
basarili(r23.status_code == 403, f"icerik_editoru rol güncelleyemiyor — {r23.status_code}")

# 24) Bu işlemler audit_log'a yazılmış olmalı
r24 = client.get("/admin/audit-log?limit=100", headers=super_headers)
islemler24 = {log["islem"] for log in r24.json()}
basarili("yonetici_ekleme" in islemler24 and "yonetici_rol_degisikligi" in islemler24, f"Yönetici işlemleri audit_log'da — gelen: {islemler24}")

print()
print("TÜM ADMIN TESTLERİ GEÇTİ ✓ (yetkilendirme sınırları + E7 simetri + yönetici yönetimi dahil)")
