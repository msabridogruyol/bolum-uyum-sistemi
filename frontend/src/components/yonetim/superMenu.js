// [2026-11-11] AdminSayfaDuzeni'nden taşındı: kenar menüsü ve Kullanım Analizi (menü adları) aynı listeyi kullanır.
// [2026-10-10] Süper admin menüsü: [yol, ikon, ad]. Sayfa adları değişmez; yalnızca gruplama.
export const SUPER_MENU = [
  { grup: 'Genel', baglantilar: [['/admin', '🏠', 'Kontrol Paneli']] },
  { grup: 'Raporlar ve İstatistikler', baglantilar: [
    ['/admin/istatistikler', '📊', 'İstatistikler'],
    ['/admin/raporlar', '📄', 'Rapor Merkezi'],
    ['/admin/karsilastirma', '⚖️', 'Okul Karşılaştırması'],
    ['/admin/kullanim-analizi', '⏱️', 'Kullanım Analizi'],   // [2026-11-11] hangi menüde ne kadar süre
    ['/admin/anket-psikometri', '📐', 'Anket Psikometrisi'],
  ] },
  { grup: 'Okullar ve Kullanıcılar', baglantilar: [
    ['/admin/okullar', '🏫', 'Okullar'],
    ['/admin/okul/0', '🎒', 'Okul Harici Öğrenciler'],
    ['/admin/onaylar', '✍️', 'Onay Formları'],   // [2026-11-05]
    ['/admin/paketler', '📦', 'Paketler'],
    ['/admin/koclar', '👩‍🏫', 'Eğitim Koçları'],
    ['/admin/yoneticiler', '🛠️', 'Süper Adminler'],
    ['/admin/test-hesaplari', '🧪', 'Test Hesapları'],
  ] },
  { grup: 'İçerik', baglantilar: [
    ['/admin/bolumler', '🎓', 'Bölümler'],
    ['/admin/yokatlas', '🔗', 'YÖK Atlas Eşleştirme'],
    ['/admin/is-hayati-verileri', '💼', 'İş Hayatı Verileri'],
    ['/admin/meslek-dili', '🗣️', 'Meslek Dili Sözlüğü'],
    ['/admin/konular', '📝', 'Konu Listesi (Net Takibi)'],
    ['/admin/dallar', '🌿', 'Üst Alanlar'],
    ['/admin/sorular', '❔', 'Soru Bankası'],
    ['/admin/gelisim-kaynak', '🌱', 'Gelişim Kaynak Havuzu'],
    ['/admin/takvim', '🗓️', 'Genel Takvim'],
  ] },
  { grup: 'Ölçme ve Kalite', baglantilar: [
    ['/admin/soru-gecerlilik', '🎯', 'Soru Geçerlilik Testi'],
    ['/admin/guvenlik', '🛡️', 'Güvenlik / Tutarlılık'],
    ['/admin/pipeline', '⚙️', 'Pipeline Sonuçları'],   // [2026-11-01] sayfa başlığıyla aynı ad
  ] },
  { grup: 'Sistem', baglantilar: [
    ['/admin/veri-kaynaklari', '🗂️', 'Veri Kaynakları'],   // [2026-11-01]
    ['/admin/parametreler', '🎛️', 'Parametreler'],
    ['/admin/erisim-kayitlari', '🔎', 'Erişim Kayıtları'],   // [2026-11-05] kim, ne zaman, kimin verisine
    ['/admin/audit-log', '📜', 'Audit Log'],
    ['/admin/hata-kayitlari', '🐞', 'Hata Kayıtları'],
    ['/admin/gece-bakimi', '🌙', 'Gece Bakımı'],   // [2026-11-04]
  ] },
  { grup: 'Yardım', baglantilar: [
    ['/admin/yonetim-rehberi', '🧭', 'Yönetim Rehberi'],   // [2026-11-01] adım adım: neyin nasıl yapıldığı
    ['/admin/sistem-hakkinda', 'ℹ️', 'Sistem Hakkında'],
    ['/admin/sss', '❓', 'Okul Yetkilisi SSS'],
    ['/admin/kaynakca', '📚', 'Kaynakça'],
  ] },
]
