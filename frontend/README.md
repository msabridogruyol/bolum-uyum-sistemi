# Bölüm Uyum Sistemi — Frontend (Öğrenci Arayüzü)

React + Vite. Bu, mockup'lardan (`kullanici_mockup.html`) devralınan CSS
token setiyle, ama gerçek bir React uygulaması olarak backend'e bağlı
çalışan ilk sürüm.

## Kurulum

```bash
npm install
npm run dev   # http://localhost:5173, backend'in localhost:8000'de çalıştığını varsayar
```

`vite.config.js`'deki proxy ayarı `/api/*` isteklerini `http://127.0.0.1:8000`'e yönlendirir.

## Kapsam — Ne Var, Ne Yok

**Var (gerçek backend'e karşı Playwright ile test edildi):**
- D1 — Kayıt/Giriş (JWT, localStorage'da saklanıyor)
- D2 — Katman akışı: liste (**gerçek ilerleme durumuyla — tamamlandı/devam
  ediyor rozetleri**), soru sorma, cevaplama, tamamlama
- Sidebar'da genel ilerleme özeti (kaç katman tamamlandı, K5 dal durumu,
  sonraki tur tarihi) — `GET /ogrenci/durum-ozeti`
- D3 — K5 dal derinleşme akışı
- D5 — Öneri Listesi, Tüm Bölümleri Keşfet
- Bölüm F — Koçluk: hedef seçme/değiştirme (onay akışı dahil), gelişim
  analizi, yol haritası, tur karşılaştırması
- **Yönetici paneli (E1-E9 + yönetici yönetimi)** — ayrı giriş (`/admin/giris`),
  ayrı token kapsamı (admin ve öğrenci aynı tarayıcıda eşzamanlı oturum
  açabilir), kontrol paneli, bölüm durum geçişi (gerekçe zorunlu),
  dallar, soru bankası, katman ağırlıkları, sistem parametreleri
  (rol bazlı düzenleme kısıtı), öğrenciler, audit log, yönetici
  ekleme/rol değiştirme — **kendi rolünü değiştirememe kuralı arayüzde
  de doğrulandı** (dropdown gerçekten disabled, yalnızca backend hatası
  değil)

**Yok:**
- Görsel tasarım — bu sürüm bilinçli olarak eski mockup'ın (mor tema,
  DM Sans) sade token setini kullanıyor; "Konum" tasarım yönü (bkz.
  proje geçmişi) henüz uygulanmadı, kullanıcı bunu ertelemişti
- Yükleniyor/hata durumları çok temel (yalnızca metin, spinner yok
  büyük ekranlarda)
- Form validasyonu minimal (yalnızca HTML5 `required`/`minLength`)

## Test Sırasında Bulunan ve Düzeltilen Gerçek Hatalar

| Sorun | Neden | Çözüm |
|---|---|---|
| Kayıt sonrası katman sayfasına geçmiyordu | Test locator'ı yanlış butona tıklıyordu (sekme butonu ile submit butonu aynı metni paylaşıyordu) — bu bir TEST hatasıydı, koddaki değil | Test `button[type=submit]` ile düzeltildi |
| **Katmanı başlatırken 500 hatası (gerçek backend hatası)** | React'in geliştirme modunda (`StrictMode`) `useEffect`'i kasıtlı iki kez tetiklemesi, aynı anda iki "katmanı başlat" isteği yolladı; backend'deki tur oluşturma mantığı bunu bir yarış durumuna (race condition) açık bırakmıştı — ikinci istek aynı `tur_no`'yu oluşturmaya çalışıp `UNIQUE` kısıtına takılıyordu | `app/core/katman_servisi.py`'de `IntegrityError` yakalanıp, diğer isteğin oluşturduğu satır bulunup döndürülüyor artık — kullanıcı hiçbir şey fark etmiyor. Bu, yalnızca StrictMode'a özgü değil, gerçek kullanıcıda çift tıklama/çoklu sekme senaryosunda da olabilecek bir hatanın düzeltilmesiydi |
| Admin+öğrenci aynı tarayıcıda çakışıyordu | İlk tasarımda tek bir `erisim_tokeni` localStorage anahtarı kullanılıyordu — admin girişi öğrenci oturumunu silerdi | Token'lar kapsamlı hale getirildi (`admin_erisim_tokeni` / `ogrenci_erisim_tokeni`), ikisi aynı anda açık kalabiliyor |
| İki adet test-yazım hatası (uygulama hatası değil) | "Bölüm listesi" ve "Kontrol paneli" testlerinde yanlış metin arandı (sayfada olmayan bir string'i arıyordum) | Ekran görüntüsüyle doğrulanıp test assertion'ları düzeltildi |

## Kalan İş

- Görsel tasarım güncellemesi (kullanıcı isteğiyle ertelendi)
- Gerçek `bolum_agirliklari` verisi olmadan Sonuç/Keşfet/Koçluk ekranları
  boş/anlamsız veri gösterecektir — bu frontend'in değil, backend'in
  bilinen bir sınırlaması (bkz. backend README ve pipeline README)
- Admin panelinde soru ekleme formu (E6) henüz yok — yalnızca listeleme
  ve aktif/pasif değiştirme var
