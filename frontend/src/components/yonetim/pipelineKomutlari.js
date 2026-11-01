// [2026-11-01] Pipeline komutları tek yerde: Pipeline Sonuçları ekranı ve Yönetim Rehberi aynı metni gösterir.
// Kaynak: backend/pipeline/pipeline_calistir.ps1, _kurulum_sablonu.ps1, src/s2_sisteme_gonder.py
export const CALISTIR_KOMUTU = 'powershell -ExecutionPolicy Bypass -File C:\\pipeline\\pipeline_calistir.ps1'
export const MESLEK_KOMUTU = `${CALISTIR_KOMUTU} -MeslekHazirla`
export const SISTEMDEKINI_AL_KOMUTU = `${CALISTIR_KOMUTU} -SistemdekiniAl`
export const ZORLA_KOMUTU = 'C:\\pipeline\\venv\\Scripts\\python.exe C:\\pipeline\\src\\s2_sisteme_gonder.py --zorla'
// İndirilenler'deki en yeni pipeline_kurulum*.ps1 çalışır: tarayıcı aynı adlı dosyayı "pipeline_kurulum (1).ps1" diye kaydetse de
// doğru dosya bulunur; dosya yoksa ne yapılacağı yazılır. (cmd'de çift tırnak içinde; iç metin tek tırnaklı ve ASCII.)
export const KURULUM_KOMUTU = "powershell -ExecutionPolicy Bypass -Command \"$f = Get-ChildItem (Join-Path $env:USERPROFILE 'Downloads') -Filter 'pipeline_kurulum*.ps1' | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if ($f) { & $f.FullName } else { Write-Host 'pipeline_kurulum.ps1 Indirilenler klasorunde yok: once admin panelinden indirin.' -ForegroundColor Red }\""

export const CIKTI = {
  profil: 'C:\\pipeline\\cikti\\bolum_agirliklari.xlsx',
  k5: 'C:\\pipeline\\cikti\\k5_baglari_veri.sql',
  ornek: 'C:\\pipeline\\cikti\\ornek_meslekler_veri.sql',
  kayit: 'C:\\pipeline\\cikti\\calistirma_log.txt',
}
