# Filizyol pipeline — TEK çalıştırma dosyası (2026-11-01)
# Normal kullanım:                  powershell -ExecutionPolicy Bypass -File C:\pipeline\pipeline_calistir.ps1
# ESCO meslek listesi değiştiyse:   powershell -ExecutionPolicy Bypass -File C:\pipeline\pipeline_calistir.ps1 -MeslekHazirla
# Başka bilgisayarın sonucu ile çakışırsa sistemdekini almak için: ... pipeline_calistir.ps1 -SistemdekiniAl
# Ekrana yazılanlar ayrıca cikti\calistirma_log.txt dosyasına kaydedilir. Bir adım hata verirse sonraki adımlar ÇALIŞMAZ.
# Hiçbir adım canlıya yükleme yapmaz: çıktılar admin → Pipeline Sonuçları ekranından canlıya alınır.
# Adlar: s1 / s2 = sistemle alışveriş, m1–m5 = meslek hazırlığı (yalnızca -MeslekHazirla), b1–b7 = bölüm adımları.
param([switch]$MeslekHazirla, [switch]$SistemdekiniAl)

$Kok = Split-Path -Parent $MyInvocation.MyCommand.Path
$Py  = Join-Path $Kok "venv\Scripts\python.exe"
$Log = Join-Path $Kok "cikti\calistirma_log.txt"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUNBUFFERED = "1"
Set-Location $Kok
New-Item -ItemType Directory -Force -Path (Join-Path $Kok "cikti") | Out-Null

function Yaz($m, $renk = "White") { Write-Host $m -ForegroundColor $renk; Add-Content -Path $Log -Value $m -Encoding UTF8 }
function Calistir([string[]]$argumanlar) {
  & $Py @argumanlar 2>&1 | ForEach-Object { $s = "$_"; Write-Host $s; Add-Content -Path $Log -Value $s -Encoding UTF8 }
  return $LASTEXITCODE
}
function Adim($ad, [string[]]$argumanlar) {
  $bas = Get-Date
  Yaz "`n========== $ad  ($(Get-Date -Format 'HH:mm:ss')) ==========" "Cyan"
  $kod = Calistir $argumanlar
  if ($kod -ne 0) {
    Yaz "`n!!! $ad HATA VERDİ (çıkış kodu $kod). Sonraki adımlar çalıştırılmadı." "Red"
    Yaz "Kayıt: $Log" "Red"
    exit 1
  }
  Yaz ("--- {0} tamam ({1:hh\:mm\:ss})" -f $ad, ((Get-Date) - $bas)) "Green"
}

if (-not (Test-Path (Join-Path $Kok "ayar.json"))) {
  Write-Host "Bu bilgisayar sisteme bağlı değil. Admin paneli → Pipeline Sonuçları → 'Bu bilgisayara kur' ile kurulum dosyasını indirip çalıştırın." -ForegroundColor Red
  exit 1
}
"Filizyol pipeline kaydı — $(Get-Date -Format s)" | Out-File $Log -Encoding utf8

# s1: sistemden güncel kod + veri + canlı listeler. Bu dosya güncellendiyse yeni hâliyle yeniden başlar (çıkış kodu 10).
Yaz "`n========== s1) Sistemden güncel kod, veri ve canlı listeler  ($(Get-Date -Format 'HH:mm:ss')) ==========" "Cyan"
$s1 = @("src\s1_sistemden_al.py"); if ($SistemdekiniAl) { $s1 += "--sistemdekini-al" }
$kod = Calistir $s1
if ($kod -eq 10) {
  Yaz "Çalıştırma dosyası güncellendi; yeni hâliyle yeniden başlatılıyor." "Yellow"
  $yeniden = @("-ExecutionPolicy", "Bypass", "-File", $MyInvocation.MyCommand.Path)
  if ($MeslekHazirla) { $yeniden += "-MeslekHazirla" }
  if ($SistemdekiniAl) { $yeniden += "-SistemdekiniAl" }
  & powershell @yeniden
  exit $LASTEXITCODE
}
if ($kod -ne 0) { Yaz "`n!!! s1 HATA VERDİ (çıkış kodu $kod). Hiçbir adım çalıştırılmadı. Kayıt: $Log" "Red"; exit 1 }
Yaz "--- s1 tamam" "Green"

if ($MeslekHazirla) {
  # m4, önbellekte meslek vektörü varsa hesaplamayı atlar. Liste değiştiği için eski vektörler önce yedeğe alınır;
  # metni değişmeyen meslekler metin önbelleğinden (onbellek\metin_onbellek) okunur, yalnızca yeniler hesaplanır.
  $Yedek = Join-Path $Kok ("yedekler\meslek_vektorleri_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
  New-Item -ItemType Directory -Force -Path $Yedek | Out-Null
  Get-ChildItem (Join-Path $Kok "onbellek") -File | Where-Object { $_.Name -match '^(meslekler|degiskenler)_model_.\.npy$|^(meslek_isimleri|degisken_kodlari)\.npy$' } |
    ForEach-Object { Move-Item $_.FullName $Yedek }
  # m1'in ara kayıtları sıra numarasıyla tutulur; liste değişince eski kayıt yanlış satırlara düşer.
  # Bu yüzden önceki ara kayıtlar da yedeğe alınır ve çeviri yeni listeyle baştan yapılır (uzun sürer).
  Get-ChildItem (Join-Path $Kok "veri") -File -Filter "_esco_*_checkpoint.json" | ForEach-Object { Move-Item $_.FullName $Yedek }
  Yaz "Eski meslek/değişken vektörleri ve çeviri ara kayıtları yedeğe alındı: $Yedek" "Yellow"

  Adim "m1) ESCO meslekleri Türkçeye"        @("src\m1_esco_ceviri.py")
  Adim "m2) Bilinen meslek düzeltmeleri"     @("src\m2_meslek_temizle.py")
  Adim "m3) Çeviri hatası raporu"            @("src\m3_ceviri_kontrolu.py")
  Adim "m4) Meslek ve değişken embedding'i"  @("src\m4_meslek_embedding.py")
  Adim "m5) Meslek × değişken skorları"      @("src\m5_meslek_degisken_skorlama.py")
}

Adim "b1) Bölüm adlarını canlıyla eşitle"    @("src\b1_bolum_esitle.py")
Adim "b2) Bölüm metni ve embedding'i"        @("src\b2_bolum_ders_metni.py")
Adim "b3) TÜİK eşleşmesi"                    @("src\b3_tuik_esle.py")
Adim "b4) Bölüm profilleri"                  @("src\b4_bolum_profili.py")
Adim "b5) K5 bağları"                        @("src\b5_k5_baglari.py")
Adim "b6) Örnek meslekler"                   @("src\b6_ornek_meslekler.py")
Adim "b7) Kalite ölçümü"                     @("src\b7_kontrol.py")
Adim "s2) Sonuçları sisteme gönder (canlıya almaz)" @("src\s2_sisteme_gonder.py")

Yaz "`nHEPSİ TAMAM. Hiçbir şey canlıya yüklenmedi." "Green"
Yaz "Yüklenecek 3 dosya (admin → Pipeline Sonuçları, sırayla):" "Green"
Yaz "  1) $Kok\cikti\bolum_agirliklari.xlsx" "Green"
Yaz "  2) $Kok\cikti\k5_baglari_veri.sql" "Green"
Yaz "  3) $Kok\cikti\ornek_meslekler_veri.sql" "Green"
Yaz "Kayıt: $Log" "Green"
