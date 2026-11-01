// [2026-11-01] Pipeline komutları tek yerde: Pipeline Sonuçları ekranı ve Yönetim Rehberi aynı metni gösterir.
// Kaynak: backend/pipeline/pipeline_calistir.ps1, _kurulum_sablonu.ps1, src/s2_sisteme_gonder.py
export const CALISTIR_KOMUTU = 'powershell -ExecutionPolicy Bypass -File C:\\pipeline\\pipeline_calistir.ps1'
export const MESLEK_KOMUTU = `${CALISTIR_KOMUTU} -MeslekHazirla`
export const SISTEMDEKINI_AL_KOMUTU = `${CALISTIR_KOMUTU} -SistemdekiniAl`
export const ZORLA_KOMUTU = 'C:\\pipeline\\venv\\Scripts\\python.exe C:\\pipeline\\src\\s2_sisteme_gonder.py --zorla'
export const KURULUM_KOMUTU = 'powershell -ExecutionPolicy Bypass -File "%USERPROFILE%\\Downloads\\pipeline_kurulum.ps1"'
export const CIKTI = {
  profil: 'C:\\pipeline\\cikti\\bolum_agirliklari.xlsx',
  k5: 'C:\\pipeline\\cikti\\k5_baglari_veri.sql',
  ornek: 'C:\\pipeline\\cikti\\ornek_meslekler_veri.sql',
  kayit: 'C:\\pipeline\\cikti\\calistirma_log.txt',
}
