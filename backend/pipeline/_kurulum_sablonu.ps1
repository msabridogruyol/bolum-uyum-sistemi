# Filizyol pipeline — bu bilgisayara kurulum (admin panelinden indirildi: __OLUSTURMA__, bilgisayar: __CIHAZ_ADI__)
# Çalıştırma: admin paneli → Pipeline Sonuçları → "Bilgisayarlar ve veri deposu" kartındaki 3. adımın komutu (Kopyala)
# Bu dosya 24 saat geçerlidir ve bir kez kullanılabilir. Başka bir bilgisayar için admin panelinden yeni dosya indirin.
# Ne yapar: 1) Python 3.14'ü bulur  2) bu bilgisayarı sisteme bağlar  3) pipeline kodunu indirir
#           4) Python ortamını sabit sürümlerle kurar  5) en son veri sürümünü ve canlı listeleri indirir
# Klasörde zaten pipeline varsa üzerine kurar: veriler korunur, değişen kod dosyaları yedekler\ klasörüne kopyalanır.
param([string]$Klasor = "C:\pipeline")

$ErrorActionPreference = "Stop"
$Api = "__API_ADRESI__"
$KurulumAnahtari = "__KURULUM_ANAHTARI__"
$PythonSurumu = "3.14"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"
function Adim($m) { Write-Host "`n== $m" -ForegroundColor Cyan }
function Dur($m) { Write-Host "`n!!! $m" -ForegroundColor Red; exit 1 }

Adim "1/5 Python $PythonSurumu aranıyor"
$Python = $null
try { $s = & py "-$PythonSurumu" -c "import sys; print(sys.executable)" 2>$null; if ($LASTEXITCODE -eq 0 -and $s) { $Python = "$s".Trim() } } catch {}
if (-not $Python) {
  try { $s = & python -c "import sys; print('%d.%d' % sys.version_info[:2], sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and "$s".StartsWith("$PythonSurumu ")) { $Python = "$s".Substring($PythonSurumu.Length + 1).Trim() } } catch {}
}
if (-not $Python) {
  Dur ("Python $PythonSurumu bulunamadı. https://www.python.org/downloads/ adresinden Python $PythonSurumu'ü kurun " +
       "(kurulumda 'Add python.exe to PATH' kutusunu işaretleyin), sonra bu dosyayı yeniden çalıştırın. Dosya 24 saat geçerli.")
}
Write-Host "  $Python"

Adim "2/5 Bu bilgisayar sisteme bağlanıyor"
New-Item -ItemType Directory -Force -Path $Klasor | Out-Null
$AyarYolu = Join-Path $Klasor "ayar.json"
$cevap = $null
if (Test-Path $AyarYolu) {
  # Kurulum yarıda kaldıysa: bu bilgisayar zaten bağlı, aynı dosya yeniden çalıştırılabilir
  try {
    $eski = Get-Content $AyarYolu -Raw -Encoding UTF8 | ConvertFrom-Json
    Invoke-RestMethod -Uri "$Api/pipeline-istemci/manifest" -Headers @{ "X-Pipeline-Anahtari" = $eski.anahtar } | Out-Null
    $cevap = [pscustomobject]@{ cihaz_anahtari = $eski.anahtar; cihaz_adi = $eski.cihaz_adi }
    Write-Host "  Bu bilgisayar zaten bağlı: $($eski.cihaz_adi)"
  } catch { $cevap = $null }
}
if (-not $cevap) {
  try {
    $cevap = Invoke-RestMethod -Method Post -Uri "$Api/pipeline-istemci/etkinlestir" -ContentType "application/json; charset=utf-8" `
             -Body ([Text.Encoding]::UTF8.GetBytes((@{ kurulum_anahtari = $KurulumAnahtari } | ConvertTo-Json)))
  } catch {
    $ayrinti = $_.ErrorDetails.Message
    Dur "Sisteme bağlanılamadı. $ayrinti"
  }
  $ayar = @{ api = $Api; anahtar = $cevap.cihaz_anahtari; cihaz_adi = $cevap.cihaz_adi } | ConvertTo-Json
  [IO.File]::WriteAllText($AyarYolu, $ayar, (New-Object Text.UTF8Encoding $false))
  # Bilgisayar anahtarını yalnızca bu Windows kullanıcısı okuyabilsin (klasörden devralınan izinler kaldırılır)
  try { & icacls $AyarYolu /inheritance:r /grant:r "$($env:USERDOMAIN)\$($env:USERNAME):(R,W)" | Out-Null } catch {}
  Write-Host "  Bağlandı: $($cevap.cihaz_adi)"
}
$Baslik = @{ "X-Pipeline-Anahtari" = $cevap.cihaz_anahtari }

Adim "3/5 Pipeline kodu indiriliyor"
$manifest = Invoke-RestMethod -Uri "$Api/pipeline-istemci/manifest" -Headers $Baslik
$Damga = Get-Date -Format "yyyyMMdd_HHmmss"
foreach ($d in $manifest.kod) {
  $hedef = Join-Path $Klasor ($d.yol -replace "/", "\")
  if ((Test-Path $hedef) -and ((Get-FileHash $hedef -Algorithm SHA256).Hash.ToLower() -eq $d.sha256)) { continue }
  New-Item -ItemType Directory -Force -Path (Split-Path $hedef) | Out-Null
  if (Test-Path $hedef) {
    $yedek = Join-Path $Klasor ("yedekler\kod_$Damga\" + ($d.yol -replace "/", "\"))
    New-Item -ItemType Directory -Force -Path (Split-Path $yedek) | Out-Null
    Copy-Item $hedef $yedek
  }
  $gecici = "$hedef.tmp"
  Invoke-WebRequest -Uri ("$Api/pipeline-istemci/kod?yol=" + [Uri]::EscapeDataString($d.yol)) -Headers $Baslik -OutFile $gecici -UseBasicParsing
  if ((Get-FileHash $gecici -Algorithm SHA256).Hash.ToLower() -ne $d.sha256) { Remove-Item $gecici; Dur "İndirilen dosya doğrulanamadı: $($d.yol)" }
  Move-Item $gecici $hedef -Force
  Write-Host "  $($d.yol)"
}
Write-Host "  Kod sürümü: $($manifest.kod_surumu) ($($manifest.kod.Count) dosya)"

Adim "4/5 Python ortamı kuruluyor (ilk kurulumda 10-30 dakika sürebilir; ~2-3 GB iner)"
$Venv = Join-Path $Klasor "venv"
$VenvPy = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $VenvPy)) { & $Python -m venv $Venv; if ($LASTEXITCODE -ne 0) { Dur "Python ortamı oluşturulamadı." } }
& $VenvPy -m pip install --upgrade pip --quiet
& $VenvPy -m pip install -r (Join-Path $Klasor "requirements_kilit.txt")
if ($LASTEXITCODE -ne 0) { Dur "Kütüphaneler kurulamadı (yukarıdaki hata). İnternet bağlantısını kontrol edip bu dosyayı yeniden çalıştırın." }

Adim "5/5 Veri ve canlı listeler indiriliyor (sistemde veri varsa ~220 MB)"
foreach ($k in "cikti", "yedekler", "veri", "onet", "onbellek") { New-Item -ItemType Directory -Force -Path (Join-Path $Klasor $k) | Out-Null }
$env:PYTHONIOENCODING = "utf-8"
& $VenvPy (Join-Path $Klasor "src\s1_sistemden_al.py") --kurulum
if ($LASTEXITCODE -ne 0) { Dur "Veri alınamadı (yukarıdaki mesaj). Bağlantı kuruldu; sorunu giderip pipeline_calistir.ps1 ile devam edebilirsiniz." }

Write-Host "`nKURULUM TAMAM." -ForegroundColor Green
Write-Host "Embedding modelleri (~3-4 GB) ilk çalıştırmada kendiliğinden iner." -ForegroundColor Green
Write-Host "Çalıştırmak için cmd'ye yapıştırın:" -ForegroundColor Green
Write-Host "  powershell -ExecutionPolicy Bypass -File $Klasor\pipeline_calistir.ps1" -ForegroundColor Green
