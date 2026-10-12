# Çoklu dil — çeviri araçları

[2026-10-12] Filizyol arayüzü Türkçe yazılır; 12 dil desteklenir: en, de, fr, ru, es, it, ar (sağdan sola), zh, hi, uz, az, ko. Diğer diller, Türkçe metinlerin dil paketlerinden ekranda değiştirilmesiyle gösterilir.
Bu klasör paketlerin nasıl üretildiğini ve nasıl güncelleneceğini tutar.

## Nasıl çalışır

| Parça | Dosya | Görevi |
|---|---|---|
| Dil paketi | `src/dil/<kod>.json` | `{"Türkçe metin": "çeviri"}`. `{0}` içeren anahtarlar kalıptır ("{0} öğrenci"). |
| Ekran katmanı | `src/yardimci/dil.js` | Seçili dil Türkçe değilse sayfadaki metinleri ve placeholder/title/aria-label/alt değerlerini paketten çevirir (MutationObserver). |
| Dil seçici | `src/components/DilSecici.jsx` | Giriş ekranları, öğrenci Ayarlar sayfası ve yönetim menüsünde bulunur. Seçim hesaba kaydedilir (`ogrenciler.dil`, `admin_kullanicilar.dil`). |
| İçerik çevirisi | `backend/app/core/ceviri_servisi.py` | Pakette olmayan uzun sistem içeriği (bölüm açıklamaları, sözlük, iş hayatı verileri) `POST /ceviri/icerik` ile yapay zekâya çevirtilir ve `ceviri_onbellek` tablosunda saklanır. Yalnızca içerik havuzundaki metinler gönderilir; kişisel veri gönderilmez. |
| Filiz | `openai_ile_konus` | `X-Dil` başlığına göre cevabı seçili dilde verir. |

Çevrilmeyenler:
- Öğrenci, okul ve kullanıcı adları ile kullanıcıların yazdığı metinler.
- KVKK metinleri. Hukuken bağlayıcı olan Türkçe asılları gösterilir, yanlarında bir not bulunur.
- PDF raporlar ve e-postalar. Bunlar şimdilik Türkçe kalır.

## Yeni metin eklendiğinde

1. Metinleri çıkarın:
   - `node cikar.mjs ../../src fe.json`. Bu adım `@babel/parser@7` ve `@babel/traverse@7` ister; bunları geçici bir klasöre kurun.
   - `python3 cikar_be.py ../../../backend/app be.json`
2. `python3 birlestir.py` komutunu çalıştırın. Komut yerel veritabanından soru, bölüm ve özellik adlarını da ekler ve `katalog.json` dosyasını üretir.
3. Katalogda olmayan yeni metinleri parçalara bölün. Her parçayı `YONERGE.md`'deki yönergeyle her dile çevirin. Çeviriler `ceviri/<dil>/<parça>_*.json` dosyalarına yazılır.
4. Her parçayı `python3 denetle.py <calisma> <dil> <parça>` ile denetleyin.
5. `python3 paketle.py katalog.json <calisma>/ceviri en de fr ru es it ar zh hi uz az ko` komutu paketleri günceller. Paketteki eski çeviriler korunur.
6. Kısa ve elle yazılacak ekler için `ek_ceviriler.json` dosyasını kullanın. Bu dosya her paketlemede en son uygulanır.

Pakette olmayan bir metin ekranda Türkçe kalır; sistem hata vermez.

## Yeni dil eklemek

1. Kataloğu çevirip `src/dil/<kod>.json` paketini üretin.
2. Dili `DILLER` listelerine ekleyin:
   - `src/yardimci/dil.js`;
   - backend tarafında `ceviri_servisi.DILLER` (backend'de 13 dilin tamamı zaten tanımlı).
3. Sağdan sola diller (`SAG_SOL`, şimdilik yalnızca `ar`) için sayfa yönü `dir="rtl"` olur. Fiziksel konumlu öğelerin (Filiz maskotu, sabit rozetler, mobil menü) aynalanması `index.css` sonundaki `[dir="rtl"]` kurallarındadır.

## Bilinen sınırlar

- Kalın yazılmış bir kelimenin çevresindeki parçalar (`<b>…</b> metin.`) ayrı ayrı çevrilir; bazı dillerde söz dizimi bozulabilir. Bunun çözümü cümleyi kaynakta tek parça yazmaktır.
- Ölçme sorularının çevirileri yapay zekâ ile yapılmıştır. Türkçe dışındaki dillerde soru ekranında bir uyarı notu gösterilir. Geçerlilik çalışması yalnızca Türkçe sürümle yapılmıştır.
- Paket boyutu dil başına yaklaşık 1,6–2,2 MB (gzip ile ~0,6–0,7 MB). Paket yalnızca Türkçe dışında bir dil seçildiğinde indirilir.
