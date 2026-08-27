"""E1 (Kontrol Paneli), E2 (Pipeline stub), E3 (Katman Ağırlıkları), E4 (Dallar), E6 (Sorular) testi."""
import os
os.environ["DATABASE_URL"] = "sqlite:///./_test_admin2.db"
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

super_admin = models.AdminKullanici(ad_soyad="Süper Admin", email="super2@ornek.com", sifre_hash=sifre_hashle("sifre1234"), rol="super_admin")
editor = models.AdminKullanici(ad_soyad="Editör", email="editor2@ornek.com", sifre_hash=sifre_hashle("sifre1234"), rol="icerik_editoru")
db.add_all([super_admin, editor]); db.flush()

k1 = models.Katman(kod="K1", ad="K1", sira=1, normalizasyon_agirligi=20, kosullu_mu=False)
k2 = models.Katman(kod="K2", ad="K2", sira=2, normalizasyon_agirligi=15, kosullu_mu=False)
k3 = models.Katman(kod="K3", ad="K3", sira=3, normalizasyon_agirligi=25, kosullu_mu=False)
k4 = models.Katman(kod="K4", ad="K4", sira=4, normalizasyon_agirligi=40, kosullu_mu=False)
db.add_all([k1, k2, k3, k4]); db.flush()
deg = models.Degisken(katman_id=k1.id, kod="D1", ad="D1", sira=1)
db.add(deg); db.flush()

# başlangıç aktif ağırlık versiyonu (v1)
for k, a in [(k1, 20), (k2, 15), (k3, 25), (k4, 40)]:
    db.add(models.KatmanAgirligi(katman_id=k.id, versiyon=1, agirlik=a, aktif_mi=True))

bolum1 = models.Bolum(ad="Yayında Bölüm", durum="yayinda")
bolum2 = models.Bolum(ad="Taslak Bölüm", durum="taslak")
db.add_all([bolum1, bolum2])
db.commit()

client = TestClient(app)
super_r = client.post("/admin/auth/giris", json={"email": "super2@ornek.com", "sifre": "sifre1234"})
super_headers = {"Authorization": f"Bearer {super_r.json()['erisim_tokeni']}"}
editor_r = client.post("/admin/auth/giris", json={"email": "editor2@ornek.com", "sifre": "sifre1234"})
editor_headers = {"Authorization": f"Bearer {editor_r.json()['erisim_tokeni']}"}

# --- E1 — Kontrol Paneli ---
r1 = client.get("/admin/kontrol-paneli", headers=super_headers)
basarili(r1.status_code == 200, f"E1 çalışıyor — {r1.status_code} {r1.text}")
veri1 = r1.json()
basarili(veri1["toplam_bolum_sayisi"] == 2 and veri1["yayinda_bolum_sayisi"] == 1, f"Bölüm sayıları doğru — {veri1}")
basarili(veri1["yarida_birakma_orani"] is None, f"Hiç oturum yokken oran null — gelen: {veri1['yarida_birakma_orani']}")

# --- E2 — Pipeline (stub) ---
r2 = client.get("/admin/pipeline-durumu", headers=super_headers)
basarili(r2.status_code == 200 and r2.json()["durum"] == "baglanti_yok", f"E2 stub dürüstçe 'bağlantı yok' diyor — {r2.json()}")

# --- E3 — Katman Ağırlıkları ---
r3 = client.get("/admin/katman-agirliklari", headers=editor_headers)
basarili(r3.status_code == 200 and len(r3.json()) == 4, f"Aktif ağırlıklar (v1) listelendi — {r3.json()}")

# Toplamı 100 olmayan bir versiyon reddedilmeli
r3b = client.post("/admin/katman-agirliklari", json={"agirliklar": {"K1": 30, "K2": 15, "K3": 25, "K4": 40}}, headers=super_headers)
basarili(r3b.status_code == 400, f"Toplamı 100 olmayan ağırlık reddedildi — {r3b.status_code} {r3b.text}")

# icerik_editoru yeni versiyon oluşturamamalı
r3c = client.post("/admin/katman-agirliklari", json={"agirliklar": {"K1": 25, "K2": 15, "K3": 20, "K4": 40}}, headers=editor_headers)
basarili(r3c.status_code == 403, f"icerik_editoru ağırlık versiyonu oluşturamıyor — {r3c.status_code}")

# super_admin geçerli bir v2 oluşturabilmeli, eskisi pasife düşmeli
r3d = client.post("/admin/katman-agirliklari", json={"agirliklar": {"K1": 25, "K2": 15, "K3": 20, "K4": 40}}, headers=super_headers)
basarili(r3d.status_code == 201, f"v2 oluşturuldu — {r3d.status_code} {r3d.text}")
r3e = client.get("/admin/katman-agirliklari", headers=super_headers)
aktif_versiyonlar = {v["versiyon"] for v in r3e.json()}
basarili(aktif_versiyonlar == {2}, f"Yalnızca v2 aktif, v1 pasife düştü — gelen: {aktif_versiyonlar}")

# --- E4 — Dallar ---
r4 = client.post("/admin/dallar", json={"kod": "D01", "ad": "Test Dalı", "bagli_degisken_id": deg.id}, headers=editor_headers)
basarili(r4.status_code == 201, f"Dal eklendi (herhangi bir admin rolü) — {r4.status_code} {r4.text}")
dal_id = r4.json()["id"]

r4b = client.post("/admin/dallar", json={"kod": "D01", "ad": "Tekrar", "bagli_degisken_id": None}, headers=editor_headers)
basarili(r4b.status_code == 400, f"Yinelenen dal kodu reddedildi — {r4b.status_code}")

r4c = client.post(f"/admin/dallar/{dal_id}/durum", json={"yeni_durum": "guclu_kanitli"}, headers=super_headers)
basarili(r4c.status_code == 200 and r4c.json()["dogrulama_durumu"] == "guclu_kanitli", f"Dal durumu güncellendi — {r4c.json()}")

r4d = client.post(f"/admin/dallar/{dal_id}/durum", json={"yeni_durum": "gecersiz"}, headers=super_headers)
basarili(r4d.status_code == 400, f"Geçersiz dal durumu reddedildi — {r4d.status_code}")

# --- E6 — Soru Bankası ---
r6 = client.post("/admin/sorular", json={
    "katman_id": k1.id, "degisken_id": deg.id, "soru_tipi": "likert",
    "soru_metni": "Test sorusu?", "ters_kodlanmis_mi": False,
    "secenekler": ["Kesinlikle katılmıyorum", "Katılmıyorum", "Kararsızım", "Katılıyorum", "Kesinlikle katılıyorum"],
}, headers=editor_headers)
basarili(r6.status_code == 201, f"Soru eklendi — {r6.status_code} {r6.text}")
soru_id = r6.json()["id"]
basarili(r6.json()["katman_kod"] == "K1", f"Katman kodu doğru döndü — {r6.json()}")

r6b = client.post("/admin/sorular", json={
    "katman_id": k1.id, "degisken_id": deg.id, "soru_tipi": "likert",
    "soru_metni": "Tek seçenekli soru", "secenekler": ["yalnızca bir"],
}, headers=editor_headers)
basarili(r6b.status_code == 400, f"Tek seçenekli soru reddedildi — {r6b.status_code}")

r6c = client.get(f"/admin/sorular?katman_kod=K1", headers=editor_headers)
basarili(r6c.status_code == 200 and len(r6c.json()) == 1, f"Katmana göre filtreleme çalışıyor — {r6c.json()}")

# Soru silinmiyor, yalnızca pasife alınıyor
r6d = client.post(f"/admin/sorular/{soru_id}/aktiflik", json={"aktif_mi": False}, headers=editor_headers)
basarili(r6d.status_code == 200 and r6d.json()["aktif_mi"] is False, f"Soru pasife alındı (silinmedi) — {r6d.json()}")

# --- Audit log'da yeni işlemler var mı ---
r_audit = client.get("/admin/audit-log?limit=100", headers=super_headers)
islemler = {log["islem"] for log in r_audit.json()}
beklenen = {"katman_agirlik_versiyonu", "dal_ekleme", "dal_durum_degisikligi", "soru_ekleme", "soru_aktiflik_degisikligi"}
basarili(beklenen.issubset(islemler), f"Yeni işlemler audit_log'da — eksik: {beklenen - islemler}")

print()
print("TÜM E1/E2/E3/E4/E6 TESTLERİ GEÇTİ ✓")
