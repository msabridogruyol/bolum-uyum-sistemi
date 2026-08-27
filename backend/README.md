# Bölüm Uyum Sistemi — Backend İskeleti

FastAPI + SQLAlchemy + Alembic. Bu iskelet, proje belgelerinden derlenen
`schema.sql`'in (33 tablo) doğrudan koda dökülmüş halidir — iki dosya
birbirinden sapmamalıdır.

## Kurulum

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # DATABASE_URL'i kendi PostgreSQL bağlantınıza göre düzenleyin
alembic upgrade head    # 33 tabloyu + başlangıç verisini oluşturur
python scripts/ilk_admin_olustur.py --email sen@ornek.com --ad-soyad "Adın Soyadın"  # ilk (ve şu an tek) admin hesabın
uvicorn app.main:app --reload
```

## Klasör Yapısı

```
app/
├── core/
│   ├── config.py           # ayarlar (ortam değişkenlerinden)
│   ├── database.py         # SQLAlchemy engine + session
│   ├── security.py         # bcrypt hash + JWT üretim/doğrulama
│   └── katman_servisi.py   # D2 iş mantığı: tur yönetimi, soru kilitleme,
│                           # Likert/SJT puanlama, katman tamamlama
├── models/                 # SQLAlchemy ORM — sistem_genel_anlatim.md'deki
│                           # tablo gruplarıyla birebir aynı dosya bölünmesi
├── schemas/                # Pydantic — auth.py, ogrenci.py (admin.py HENÜZ YOK)
├── api/
│   ├── deps.py              # JWT doğrulama dependency
│   ├── auth.py               # POST /auth/kayit, /giris, /yenile
│   └── ogrenci.py            # D2 katman akışı uç noktaları
└── main.py                  # Uygulama giriş noktası, router bağlama

alembic/versions/
├── 0001_ilk_sema.py            # 33 tablo — schema.sql'in DDL kısmı
└── 0002_baslangic_verisi.py    # K1-K5 + başlangıç sistem parametreleri
```

## Çalışır Durumda Olan (Uçtan Uca Test Edildi)

Bu iskelet, yedi ayrı test dosyasıyla (75+ doğrulama, toplamda) doğrulandı
(SQLite üzerinde, `TestClient` ile; PostgreSQL dialekt farkları
`.with_variant()` ile ayrıca ele alındı):

- **D1 — Kimlik doğrulama:** kayıt, yinelenen e-posta reddi, yanlış şifre
  reddi, giriş (access+refresh JWT), tokensız istek reddi, token yenileme
- **D2 — Katman akışı:** katman listeleme, katman başlatma (soru seti
  kilitleme), eksik cevapla tamamlama reddi, cevaplama, katman tamamlama
- **Likert puanlama formülü** gerçek değerlerle doğrulandı (sıra=4/5 → 75, sıra=1/5 → 0)
- **D2c — Tur mekanizması:** 120 günlük kısıt doğru reddediyor
- **D3 — K5 dal derinleşme:** K4 tamamlanınca otomatik tetikleme, eşiği
  geçen dalın açılması, dal-özel soru sunumu, dal tamamlama + puanlama
- **D4 — TOPLAM_UYUM (10 ÇKKV):** matematiksel doğruluk, min-max
  normalizasyon, Kendall's W, K4 bitmeden sıralamanın boş dönmesi,
  admin-only alanların öğrenci response'unda hiç bulunmaması
- **D5, Katman 1 — Öneri Listesi**, **Katman 2 — Keşfet** (arama, katman
  ortalaması, taslak bölümlerin gizliliği), **Katman 3 — Bölüm F Koçluk**
  (tek aktif hedef, onay akışı, gap analizi, yol haritası, tur karşılaştırması)
- **E5, E7, E8, E9 — Admin uç noktaları:**
  - Yetkilendirme sınırları: öğrenci token'ı admin uç noktalarında
    reddediliyor, `icerik_editoru` rolü `super_admin`-only işlemleri
    (parametre güncelleme) yapamıyor
  - E8 — sistem parametresi güncelleme (yalnızca `super_admin`), audit
    log'a yazılması
  - E5 — bölüm durum geçişi (`taslak→test_ediliyor→yayinda`), ara adım
    atlanamaması, gerekçesiz geçişin reddi, `yayinda`'dan geri dönüşün
    şu an desteklenmemesi
  - **E7 — admin-only skor detayı: `yontem_skorlari`/`kendall_w`'nin
    admin response'unda TAM olarak göründüğü** — D4 testindeki "öğrenciye
    gizli" kanıtının simetrik doğrulaması (aynı veri, iki farklı response
    şeması, iki farklı görünürlük)
  - E9 — audit log ve öğrenci listeleme
  - **Yönetici yönetimi (yeni):** yalnızca `super_admin` yeni yönetici
    ekleyebiliyor/rol değiştirebiliyor, `icerik_editoru` bu işlemleri
    yapamıyor, yinelenen e-posta reddediliyor, yeni eklenen yönetici
    gerçekten giriş yapabiliyor, **ve kritik bir güvenlik kuralı: bir
    `super_admin` kendi rolünü değiştiremiyor** (tek admin kazayla kendi
    yetkisini düşürüp sistemi kilitleyemez), tüm işlemler audit_log'a yazılıyor
- **E1, E3, E4, E6 — Admin CRUD tamamlandı:**
  - E1 — kontrol paneli özet metrikleri (bölüm/dal/öğrenci/tur sayıları,
    yarıda bırakma oranı — hiç oturum yokken `null` dönmesi test edildi)
  - E3 — katman ağırlık versiyonlama: toplamı %100 olmayan versiyonun
    reddi, yalnızca `super_admin`'in yeni versiyon oluşturabilmesi, yeni
    versiyon eklenince eskisinin otomatik pasife düşmesi
  - E4 — dal ekleme/durum güncelleme, yinelenen kod reddi
  - E6 — soru ekleme (seçenekleriyle), tek seçenekli sorunun reddi,
    katmana göre filtreleme, **soruların silinmeyip yalnızca pasife
    alınması** (geçmiş öğrenci oturumları `kilitlenen_soru_id_listesi`
    ile dondurulduğu için silme geçmiş veriyi bozardı)
  - E2 — **bilinçli olarak stub**: gerçek iş kuyruğu (Celery/Redis)
    kurulmadığı için `/admin/pipeline-durumu` yalnızca "bağlantı yok"
    döner, sahte bir "çalışıyor" durumu üretmez

## Test Sırasında Bulunan ve Düzeltilen Gerçek Hatalar

| Sorun | Çözüm |
|---|---|
| `email-validator` eksikti | `requirements.txt`'e eklendi |
| `ARRAY`/`JSONB` (PostgreSQL'e özel) test ortamında çalışmıyordu | `JSON`'a çevrildi — hem model hem `schema.sql`, senkron |
| `passlib`+`bcrypt` sürüm çakışması (bilinen ekosistem sorunu) | `passlib` kaldırıldı, doğrudan `bcrypt` kullanıldı |
| `BigInteger` PK'lar SQLite'ta autoincrement olmuyordu | Dialekt varyantı: SQLite'ta `INTEGER`, PostgreSQL'de hâlâ `BIGSERIAL` |
| Timezone-aware/naive datetime karşılaştırma hatası | Karşılaştırma öncesi normalize edildi |
| **`ogrenci_cevaplar` tablosu hiçbir belgede yoktu** | Ham (soru bazlı) cevapları tutacak tablo eklendi — "kaldığı yerden devam et" ve çoklu soru→tek değişken ortalaması mekanizmaları bu olmadan çalışamazdı |
| **`aktif_veya_yeni_tur_getir`, K5 akışlarında yanlışlıkla yeni tur açmaya çalışıyordu** | K4 tamamlanınca tur.durum='tamamlandi' olur; K5 bu turun ÜZERİNDE devam eder ama "yalnızca devam_ediyor turu bul" mantığı bunu bulamayıp 120 günlük kısıta yanlışlıkla takılıyordu. Ayrı bir `son_tur_getir` (tamamlanmış turu da bulan, yeni tur açmayan) fonksiyonu eklendi — yalnızca K5/dal uç noktaları bunu kullanır |
| **K5 sorularının şema bağlantısı hiç tasarlanmamıştı** | `sistem_genel_anlatim.md`'nin kendi "Ertelenen Konular #1" maddesiydi. `degiskenler.dal_id` (nullable) eklendi — K5'e özgü değişkenler K1-K4 ile aynı tabloda yaşar, yalnızca hangi dala ait olduğu işaretlenir; soru zaten `degisken_id` üzerinden bunu miras alır |
| **D4'ün karar matrisi girdisi belgede tanımsızdı** | Belge "10 yöntemle karşılaştırılır" diyordu ama hangi ham değerin (öğrenci puanı mı, bölüm ağırlığı mı, farkı mı) karar matrisine gireceğini belirtmiyordu. `performans = 100 - |öğrenci_puanı - bölüm_ağırlığı|` (gap-bazlı uyum performansı) tanımı seçildi — **✅ Onaylandı**, `skor_motoru.py` başında gerekçesiyle işaretli |
| **Değişken bazlı kriter ağırlığı da tanımsızdı** | Belgede yalnızca katman bazlı %20/15/25/40 vardı, 31 değişkenin kendi arasında nasıl bölüneceği yoktu. Her katmanın ağırlığı, o katmandaki değişken sayısına eşit bölünüyor — **✅ Onaylandı** |
| **Keşfet'teki "katman ortalaması" ne anlama geliyor belirsizdi** | Belgede "% uyum + katman bazlı ortalamalar" deniyordu ama bunun öğrencinin kendi K1-K4 puanları mı (her aramada aynı kalır, anlamsız) yoksa bölümün kendi katman bazlı ortalama beklentisi mi olduğu belirsizdi. İkincisi seçildi — her bölüm için farklı, arama sonucuna gerçekten bilgi katan bir değer — **✅ Onaylandı** |
| **SJT seçenek ağırlığının ölçeği belirsizdi** | `sjt_secenek_degisken_agirlik.agirlik` (NUMERIC(4,3)) 0-1 aralığında varsayılıp ×100 ile puan katkısına çevriliyor — **✅ Onaylandı**, `katman_servisi.py` içinde işaretli |
| **En kritik: P4 (Nevrotiklik) gibi "ters yönlü" değişkenlerde F2/F5 yön mantığı yanlış çalışıyordu** | Bazı değişkenlerde öğrencinin bölüm beklentisinden YÜKSEK puan alması iyi bir şey değildir (örn. daha hassas/kaygılı olmak). İçerik yazılırken fark edildi: eski mantıkla yüksek nevrotiklik puanı yanlışlıkla "güçlü yön" (belirgin_ustun) sayılıyordu. Genel bir `degiskenler.ters_yonlu` bayrağı eklendi (yalnızca P4'e özel değil, herhangi bir ters yönlü değişken için kullanılabilir); F2 (gap) ve F5 (trend) hesaplamaları bu bayrağa göre yön çeviriyor. **D4 (TOPLAM_UYUM) etkilenmedi** — zaten mutlak fark kullanıyor. `test_ters_yonlu.py` ile uçtan uca doğrulandı: yüksek nevrotiklik puanı artık doğru şekilde "belirgin_altinda" (gelişim alanı) kategorisine düşüyor |
| **`GET /ogrenci/katmanlar` öğrencinin ilerleme durumunu hiç döndürmüyordu** | Kullanıcının "önyüz tam mı" sorusu üzerine fark edildi — uç nokta yalnızca statik katman bilgisi (isim, sıra, ağırlık) döndürüyordu, öğrencinin o katmanı tamamlayıp tamamlamadığı bilgisi hiç yoktu. Bu yüzden frontend "tamamlandı" rozeti gösteremiyordu — veri kaynağında yoktu | `KatmanOut`'a `durum` alanı eklendi (`son_tur_getir` ile hesaplanıyor); yeni `GET /ogrenci/durum-ozeti` uç noktası eklendi (kaç katman tamamlandı, K5 dal durumu, sonraki tur tarihi). `test_durum_ozeti.py` ile 12 doğrulamayla test edildi |

## İçerik — Artık Gerçek Veri İçeren Kısımlar

- **31 değişkenin tamamı** gerçek isim/açıklamayla veritabanında (`0003_31_degisken_icerik.py`) — kaynağı `SONUÇ.xlsx`, K3/K4 sırası kullanıcıyla doğrulandı ve düzeltildi (Excel'de ters yazılıydı)
- **Gelişim yorum havuzunun (F3) tamamı** — 155 satır (31 değişken × 5 aralık), `0004_gelisim_yorum_havuzu.py` + P4 düzeltmesi `0005_p4_yon_duzeltmesi.py`
- **Gelişim karşılaştırma yorumunun (F5.3) tamamı** — 155 satır (31 değişken × 5 trend), `0006_gelisim_karsilastirma_yorumu.py` — K1'deki değer tipi değişkenlerde bilinçli olarak nötr "arttı/azaldı" dili, beceri tipi değişkenlerde "gelişim/gerileme" dili kullanıldı; P4 doğru yönde test edildi
- **301 bölümün tamamının kısa açıklaması (D5 Katman 2 — Keşfet)** —
  `0007_bolum_aciklamalari.py`. Bölüm adlarının kaynak `Bölüm_Listesi.xlsx`
  ile karakter karakter birebir eşleştiği otomatik doğrulandı (301/301,
  eksik/fazla yok); gerçek 301 satırlık test veritabanına karşı çalıştırılıp
  **hiçbir bölümün açıklamasının boş kalmadığı** teyit edildi

## Yok (Bir Sonraki Adım)

**Backend'in tüm bölümleri (D1-D5, E1-E9) artık API seviyesinde kapandı.**
Kalan gerçek boşluklar kod eksikliği değil, veri/altyapı eksikliği:

- **Gerçek `bolum_agirliklari` verisi yok** — tüm hesaplama motorları
  matematiksel olarak doğrulandı ama test verisi elle uydurulmuş; gerçek
  301 bölüm × 31 değişken verisi ancak offline pipeline çalıştırıldıktan
  sonra var olacak (bkz. proje kökündeki `pipeline/` klasörü — A2 gerçek
  veriyle prototiplendi, A3/A4/A6 içerik eksikliği yüzünden yapılamadı)
- **İş kuyruğu (Celery/Redis)** henüz kurulmadı — E2 stub, pipeline
  tetikleme gerçek değil
- `yayinda` durumundaki bir bölümün geri (`test_ediliyor`/`taslak`)
  alınıp alınamayacağı belgede tanımsızdı — şimdilik desteklenmiyor
  (yalnızca ileri yönlü geçişler var)
- `gelisim_yorum_havuzu` (F3), `gelisim_karsilastirma_yorumu` (F5) ve
  bölüm `kisa_aciklama` (301 bölüm) içeriğinin **hepsi artık tam** —
  kalan içerik boşluğu yalnızca K1-K4 soru metinleri
- SJT puanlama mantığı yazıldı ama gerçek veriyle hiç test edilmedi
- K5'in "0 aday" ve "3'ten fazla aday" senaryoları test edilmedi
- Öğrenci frontend'i ayrı bir pakette (`frontend_ogrenci.zip`) — gerçek
  backend'e karşı Playwright ile test edildi; admin panel arayüzü hâlâ yok

## Bilinen Sınırlama

Gerçek bir PostgreSQL sunucusu bu ortamda kurulamadı (paket deposu erişim
sorunu). Tüm testler SQLite üzerinden geçti; PostgreSQL dialektinde DDL
üretimi ayrıca doğrulandı (bkz. yukarıdaki BIGSERIAL notu) ama migration'lar
**gerçek bir PostgreSQL'e karşı hiç çalıştırılmadı**. İlk `alembic upgrade
head` komutunu kendi ortamınızda çalıştırıp doğrulamanız önemle tavsiye
edilir.

