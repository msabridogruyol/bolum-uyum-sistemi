# Filizyol pipeline — çalıştırma talimatı (2026-11-01)

Pipeline'ın kodu sistemin deposunda (`backend/pipeline/`), verisi sistemin deposunda (Supabase Storage) durur. Her bilgisayara admin panelinden kurulur ve her çalıştırmada kendini günceller. Hiçbir adım canlıya dokunmaz; çıktılar yalnızca admin panelinden canlıya alınır.

## 1. Yeni bir bilgisayara kurulum

1. Bilgisayarda **Python 3.14** kurulu olmalı. Kurulu değilse <https://www.python.org/downloads/> adresinden kurun ve kurulumda "Add python.exe to PATH" kutusunu işaretleyin.
2. Admin paneli → **Pipeline Sonuçları** → **Bu bilgisayara kur** → bilgisayara bir ad verin → `pipeline_kurulum.ps1` iner.
3. cmd'ye yapıştırın:
   `powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\Downloads\pipeline_kurulum.ps1"`

Kurulum dosyası 24 saat geçerlidir ve tek kullanımlıktır. İlk kurulumda kütüphaneler (~2–3 GB) ve ilk çalıştırmada embedding modelleri (~3–4 GB) iner. Kurulum varsayılan olarak `C:\pipeline` klasörüne yapılır. Bilgisayarın erişimi admin panelindeki **Kayıtlı bilgisayarlar** listesinden kaldırılabilir.

## 2. Ne zaman, hangi komut?

| Durum | Komut (cmd'ye yapıştırın) |
|---|---|
| Sayaç uyarı verdiğinde ya da bölüm verisi değiştiğinde | `powershell -ExecutionPolicy Bypass -File C:\pipeline\pipeline_calistir.ps1` |
| ESCO meslek listesi değiştiğinde | Aynı komut, sonuna `-MeslekHazirla` eklenir |
| Başka bir bilgisayarın daha yeni sonucu ile çakışma uyarısı çıktığında (sistemdekini kullanmak için) | Aynı komut, sonuna `-SistemdekiniAl` eklenir |
| Çakışmada bu bilgisayarın sonucunu en yeni yapmak için (diğeri sürüm geçmişinde kalır) | `C:\pipeline\venv\Scripts\python.exe C:\pipeline\src\s2_sisteme_gonder.py --zorla` |

## 3. Adımlar (`src`)

| Adım | Ne yapar |
|---|---|
| `s1_sistemden_al.py` | Güncel kodu, en son veri sürümünü ve canlı bölüm / özellik / K5 listelerini alır. Bölüm adı değiştiyse ya da bölüm eklendiyse veya kaldırıldıysa listeyi eşitler. |
| m1–m5 | Meslek hazırlığı. Yalnızca `-MeslekHazirla` ile çalışır: ESCO çevirisi, düzeltmeler, çeviri kontrolü, meslek embedding'i, meslek × özellik skorları. |
| `b1_bolum_esitle.py` | Bölüm adlarındaki değişiklikleri ve kaldırmaları bütün veri dosyalarına uygular. |
| `b2_bolum_ders_metni.py` | Bölüm metni (resmî ders planı) ve bölüm embedding'leri |
| `b3_tuik_esle.py` | TÜİK istihdam ve kazanç eşleşmesi |
| `b4_bolum_profili.py` | Bölüm profilleri → `cikti\bolum_agirliklari.xlsx` |
| `b5_k5_baglari.py` | K5 iş türü bağları → `cikti\k5_baglari_veri.sql` |
| `b6_ornek_meslekler.py` | Örnek meslekler → `cikti\ornek_meslekler_veri.sql` |
| `b7_kontrol.py` | Kalite ölçümü → `cikti\rapor\b7_kontrol.csv` |
| `s2_sisteme_gonder.py` | Veri, önbellek ve çıktıları sisteme gönderir; yalnızca değişen parçalar gider. Canlıya almaz. |

**Ortak dosyalar** (tek başına çalıştırılmaz):

- `sistem_baglanti.py` — sistemle bağlantı
- `bolum_meslek.py` — b4, b5 ve b6'nın tek bölüm → meslek kuralı
- `meslek_adlari.py`
- `embedding_saglayici.py`
- `ceviri.py` — s1 ve b2'nin kullandığı Türkçe → İngilizce çeviri

`soru_gecerlilik_testi.py` pipeline'ın parçası değildir; ayrı bir araçtır.

## 4. Yükleme

Admin paneli → **Pipeline Sonuçları** ekranında üç adım sırayla yapılır. Her adımda önce önizleme gelir, sonra "Canlıya al" seçilir. Önceki hâl otomatik yedeklenir.

1. `cikti\bolum_agirliklari.xlsx`
2. `cikti\k5_baglari_veri.sql`
3. `cikti\ornek_meslekler_veri.sql`

## 5. Veri deposu

Veri, önbellek ve çıktılar sistemin deposunda durur. Depo türü sunucudaki `PIPELINE_DEPO` ayarıyla seçilir:

- `supabase` (varsayılan): Supabase Storage. `SUPABASE_URL` (`https://<proje-kodu>.supabase.co`) ve `SUPABASE_SERVICE_KEY` gerekir. Anahtar olarak Supabase → Project Settings → API Keys sayfasındaki gizli anahtar (`sb_secret_…`) ya da eski service_role anahtarı (`eyJ…`) kullanılabilir.
- `disk`: kendi sunucuda bir klasör (`PIPELINE_DEPO_DIZINI`). Bilgisayar parçaları backend üzerinden gönderir ve alır.

Bilgisayardaki pipeline için ikisi arasında fark yoktur. Depo değiştirildikten sonra pipeline'ı en son veri gönderen bilgisayarda bir kez çalıştırmak bütün veriyi yeni depoya taşır.

## 6. Sayaç

Pipeline Sonuçları ekranındaki sayaç, bölüm profillerinin en son canlıya alındığı tarihten itibaren 365 günü sayar ve son 30 günde uyarır. Şu durumlarda süre dolmadan "gerekli" der:

- Yayındaki bir bölümün profili, K5 bağı ya da örnek meslek listesi yok.
- Son çalıştırmadan sonra bölüm listesi veya bölüm kısa açıklamaları değişti.
- Son çalıştırmadan sonra K5 iş türleri veya etkinlik cümleleri değişti.
- Son çalıştırmanın çıktıları henüz canlıya alınmadı.

Özellik adı ya da tanımı değişirse yalnızca not düşülür. Puanlar `veri\degisken_kutuplari.csv` dosyasındaki kutup cümlelerinden hesaplandığı için yeniden çalıştırma gerekmez; kutup cümlelerinin yeni tanıma uygun olup olmadığı kontrol edilmelidir.

## 7. Raporlar (`cikti\rapor\`)

Rapor dosyalarının adı, onları üreten adımın adıyla başlar: `b3_tuik_eslesme.csv`, `b4_bolum_kaynaklari.csv`, `b4_regresyon_basarisi.csv`, `b5_k5_baglari_raporu.csv`, `b5_ozet.txt`, `b6_ornek_meslekler.csv`, `b7_kontrol.csv`.
