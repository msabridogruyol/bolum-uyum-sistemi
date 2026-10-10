// [2026-10-10] Okul paneli bölümleri — okul yetkilisinin sol menüsü ve süper adminin sekme çubuğu aynı listeden beslenir.
// okul: true → yalnızca gerçek okulda (okulId > 0) görünür.
export const OKUL_BOLUMLERI = [
  { k: 'ozet', ad: 'Özet', ikon: '🏠', grup: 'Genel', aciklama: 'Okulunuzdaki katılım ve sonuçların genel görünümü' },
  { k: 'ogrenciler', ad: 'Öğrenciler', ikon: '👥', grup: 'Öğrenciler', aciklama: 'Öğrenci hesapları, şifreler, sınıf atama ve öğrenci detayları' },
  { k: 'siniflar', ad: 'Sınıflar', ikon: '🏷️', grup: 'Öğrenciler', aciklama: 'Şubeler, sınıf öğretmenleri ve şube raporları' },
  { k: 'akran', ad: 'Şube & Akran', ikon: '🤝', grup: 'Öğrenciler', modul: 'akran', aciklama: 'Profili birbirine yakın öğrenciler ve şube dağılımı' },
  { k: 'kulupler', ad: 'Kulüpler', ikon: '🎭', grup: 'Okul Yaşamı', okul: true, modul: 'kulupler', aciklama: 'Okul kulüpleri ve öğrencilerin ilgi testi sonuçları' },
  { k: 'takvim', ad: 'Takvim', ikon: '📅', grup: 'Okul Yaşamı', okul: true, modul: 'takvim', aciklama: 'Öğrencilerin takviminde görünen okul etkinlikleri' },
  { k: 'bilgiler', ad: 'Okul Bilgileri', ikon: '🏫', grup: 'Okul Ayarları', okul: true, aciklama: 'Okulun tanıtım bilgileri' },
  { k: 'yetkililer', ad: 'Okul Yetkilileri', ikon: '🔑', grup: 'Okul Ayarları', okul: true, aciklama: 'Panele erişebilen yetkililer' },
  { k: 'meslekdili', ad: 'Meslek Dili', ikon: '💬', grup: 'Okul Ayarları', okul: true, aciklama: 'Öğrencilere gösterilen meslek ifadelerinin okulunuza özel hâli' },
  { k: 'konular', ad: 'Konu Listesi', ikon: '📚', grup: 'Okul Ayarları', okul: true, modul: 'net_takibi', aciklama: 'Öğrencilerin Net Takibi → Konu Takibi ekranında gördüğü konular' },
  { k: 'gorunum', ad: 'Görünüm', ikon: '🎨', grup: 'Okul Ayarları', okul: true, aciklama: 'Logo ve okul rengi' },
  { k: 'paket', ad: 'Paket', ikon: '📦', grup: 'Okul Ayarları', okul: true, aciklama: 'Okulunuzun Filizyol paketi ve açık modüller' },
  { k: 'kayitlar', ad: 'Kayıtlar', ikon: '🧾', grup: 'Okul Ayarları', aciklama: 'Paneldeki işlemlerin geçmişi' },
]

// [2026-10-10] moduller: okulun paketindeki modüller; bağlı modülü kapalı bölüm gösterilmez (verilmezse hepsi açık)
export const okulBolumleri = (okulId, moduller) => OKUL_BOLUMLERI.filter((b) => (!b.okul || okulId > 0) && (!b.modul || !moduller || moduller.includes(b.modul)))
