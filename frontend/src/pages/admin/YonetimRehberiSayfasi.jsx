// [2026-11-01] Yönetim Rehberi (süper admin): sık yapılan işlerin adım adım anlatımı — her an menüden açılır.
// Metinler sistemin gerçek davranışına göre yazıldı (ekran adları menüdeki adlarla aynı). Ekran / pipeline değişirse burası da
// güncellenmeli. Komutlar tek kaynaktan: components/yonetim/pipelineKomutlari.js
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Komut } from './PipelineDurumuSayfasi'
import { CALISTIR_KOMUTU, CIKTI, KURULUM_KOMUTU, MESLEK_KOMUTU, SISTEMDEKINI_AL_KOMUTU, ZORLA_KOMUTU } from '../../components/yonetim/pipelineKomutlari'

const E = ({ to, children }) => <Link to={to} className="ak-link">{children}</Link>

// Her konu: grup, başlık, ne zaman, adımlar (metin; isteğe bağlı komut), not
const KONULAR = [
  // ------------------------------------------------------------------ Bölüm verisi (pipeline)
  {
    id: 'yillik', grup: 'Bölüm verisi (pipeline)', baslik: 'Yıllık bölüm verisi güncellemesi',
    ne_zaman: <>Pipeline Sonuçları'ndaki sayaç <b>"Yaklaşıyor"</b> ya da <b>"Pipeline çalıştırılmalı"</b> dediğinde (yılda bir, ayrıca bölüm / B5 değişikliğinde). Sayaç <b>"Çıktılar canlıya alınmalı"</b> diyorsa pipeline'ı yeniden çalıştırmayın; yalnızca Pipeline Sonuçları'ndaki 1–3. adımları (aşağıda 3–5. maddeler) yapın.</>,
    adimlar: [
      { m: <>Pipeline'ın kurulu olduğu bilgisayarda masaüstündeki <b>Filizyol Pipeline</b> kısayoluna çift tıklayın (ya da Komut İstemi'ne şu komutu yapıştırın). Güncel kodu, en son veriyi ve canlı bölüm / B5 listelerini kendisi alır.</>, k: CALISTIR_KOMUTU },
      { m: <>Bitmesini bekleyin (genellikle 10–20 dakika; bir bilgisayardaki ilk gönderim daha uzun sürer). Sonda yeşil <b>"HEPSİ TAMAM"</b> yazar. Kırmızı bir hata çıkarsa adımlar durur; ekrandaki mesajı ve <code>{CIKTI.kayit}</code> dosyasını kontrol edin.</> },
      { m: <><E to="/admin/pipeline">Pipeline Sonuçları</E> → <b>1. adım</b>: <code>{CIKTI.profil}</code> dosyasını seçin. Önizlemeye bakın, ardından aşağıdaki <b>Geçmiş Yüklemeler</b> listesinde <b>Yayına Al</b> deyin. Sonuç hemen değil, o geceki <E to="/admin/gece-bakimi">Gece Bakımı</E>'nda (varsayılan 03:00) canlıya alınır ve tüm öğrencilerin sonuçları aynı gece yeniden hesaplanır.</> },
      { m: <><b>2. adım</b>: <code>{CIKTI.k5}</code> → önizleme → <b>Canlıya al</b> → <b>Eminim, canlıya al</b>.</> },
      { m: <><b>3. adım</b>: <code>{CIKTI.ornek}</code> → önizleme → <b>Canlıya al</b> → <b>Eminim, canlıya al</b>.</> },
      { m: <>Gece bakımından sonra sayaç <b>"Güncel"</b> olur; bir sonraki yıllık güncellemeye yaklaşık 365 gün kalır. O zamana kadar sayaç <b>"Çıktılar canlıya alınmalı"</b> gösterebilir.</> },
    ],
    not: <>Hiçbir pipeline adımı canlıya kendiliğinden yazmaz; canlıya alma yalnızca bu 3 adımla olur. 2. ve 3. adımın önizlemesinde "Sistemde olmayan bölüm" ya da "Sistemde olmayan iş türü kodları" uyarısı çıkarsa dosya canlıya alınamaz; 1. adımda eşleşmeyen satırlar önizlemede listelenir.</>,
  },
  {
    id: 'kurulum', grup: 'Bölüm verisi (pipeline)', baslik: 'Pipeline\'ı yeni bir bilgisayara kurmak',
    ne_zaman: 'Yeni ya da başka bir Windows bilgisayarda çalıştırmak istediğinizde.',
    adimlar: [
      { m: <>O bilgisayarda <b>Python 3.14</b> kurulu olmalı. Değilse <a href="https://www.python.org/downloads/" target="_blank" rel="noreferrer" className="ak-link">python.org</a>'dan kurun; kurulumda <b>"Add python.exe to PATH"</b> kutusunu işaretleyin.</> },
      { m: <><E to="/admin/pipeline">Pipeline Sonuçları</E> → <b>Bilgisayarlar ve veri deposu</b> → bilgisayara bir ad verin → <b>Kurulum dosyasını indir</b>. Dosya 24 saat geçerlidir ve tek kullanımlıktır. Tarayıcı "tehlikeli olabilir" uyarısı verirse İndirilenler listesinden <b>Sakla / Keep</b> seçin.</> },
      { m: <>İndirilen dosyaya sağ tıklayıp <b>PowerShell ile çalıştır</b> deyin (Windows 11'de önce "Diğer seçenekleri göster"). Ya da cmd'ye şu komutu yapıştırın; İndirilenler'deki en yeni kurulum dosyasını bulup çalıştırır:</>, k: KURULUM_KOMUTU },
      { m: <>Kurulum kodu ve en son veriyi indirir, kütüphaneleri kurar. İlk seferde uzun sürer (kütüphaneler ~2–3 GB; embedding modelleri ilk çalıştırmada ~3–4 GB). Bitince <b>"KURULUM TAMAM"</b> yazar ve masaüstüne <b>Filizyol Pipeline</b> kısayolu konur.</> },
      { m: <>Bilgisayar <b>Kayıtlı bilgisayarlar</b> listesinde görünür. Artık "Yıllık bölüm verisi güncellemesi" adımlarıyla çalıştırılabilir.</> },
    ],
    not: <>Klasörde zaten pipeline varsa kurulum üzerine yazar: veriler korunur, değişen kod dosyaları <code>yedekler</code> klasörüne kopyalanır.</>,
  },
  {
    id: 'erisim', grup: 'Bölüm verisi (pipeline)', baslik: 'Bir bilgisayarın erişimini kaldırmak (kayıp / değişen bilgisayar)',
    ne_zaman: 'Bilgisayar kaybolduğunda, el değiştirdiğinde ya da artık kullanılmayacağında.',
    adimlar: [
      { m: <><E to="/admin/pipeline">Pipeline Sonuçları</E> → <b>Kayıtlı bilgisayarlar</b> → o satırda <b>Erişimi kaldır</b> → <b>Eminim, erişimi kaldır</b>.</> },
      { m: <>O bilgisayar sisteme bir daha bağlanamaz. Yeniden kullanmak için "Pipeline'ı yeni bir bilgisayara kurmak" adımları uygulanır.</> },
    ],
  },
  {
    id: 'cakisma', grup: 'Bölüm verisi (pipeline)', baslik: 'İki bilgisayar çakıştığında',
    ne_zaman: <>Pipeline <b>"Biri ötekinin üzerine yazmasın diye durdu"</b> ya da <b>"başka bir bilgisayar daha yeni sonuç gönderdi"</b> dediğinde.</>,
    adimlar: [
      { m: <>Diğer bilgisayarın sonucunu kullanmak için (bu bilgisayardakiler önce <code>yedekler</code> klasörüne kopyalanır):</>, k: SISTEMDEKINI_AL_KOMUTU },
      { m: <>Ya da bu bilgisayarın sonucunu en yeni yapmak için (diğeri sürüm geçmişinde kalır):</>, k: ZORLA_KOMUTU },
    ],
    not: 'Son 5 veri sürümü ve son 30 günün sürümleri saklanır. Hiçbir durumda canlı sistem etkilenmez.',
  },
  {
    id: 'liste', grup: 'Bölüm verisi (pipeline)', baslik: 'Bölüm listesi ya da B5 cümleleri değiştiğinde',
    ne_zaman: 'Bölüm eklendiğinde, adı değiştirildiğinde, kaldırıldığında ya da Soru Bankası\'nda B5 iş türü cümleleri değiştirildiğinde.',
    adimlar: [
      { m: <>Sayaç bunu kendisi yakalar ve <b>"Pipeline çalıştırılmalı"</b> der.</> },
      { m: <>"Yıllık bölüm verisi güncellemesi" adımlarını uygulayın. Pipeline yeni listeyi canlıdan alır: adı değişen bölümün verisi yeni adına taşınır, yeni bölüm eklenir, kaldırılan bölüm çıkarılır.</> },
    ],
    not: 'Resmî ders planı olmayan yeni bölümün metni kısa açıklamasından kurulur.',
  },
  {
    id: 'ozellik', grup: 'Bölüm verisi (pipeline)', baslik: 'Bir özelliğin adı ya da tanımı değiştiğinde',
    ne_zaman: 'Özelliklerden birinin adı ya da açıklama metni değiştiğinde.',
    adimlar: [
      { m: <>Pipeline'ı yeniden çalıştırmak <b>gerekmez</b>: puanlar tanım metninden değil, özelliğin kutup cümlelerinden hesaplanır. Sayaç bu durumda yalnızca not düşer.</> },
      { m: <>Kutup cümlelerinin (pipeline'da <code>veri\degisken_kutuplari.csv</code>) yeni tanıma uygun olup olmadığı kontrol ettirilmelidir.</> },
    ],
    not: 'Yeni bir özellik eklenirse pipeline durur ve yöntem güncellemesi ister.',
  },
  {
    id: 'esco', grup: 'Bölüm verisi (pipeline)', baslik: 'ESCO meslek listesinin yeni sürümü',
    ne_zaman: 'ESCO yeni bir meslek listesi sürümü yayımladığında (seyrek).',
    adimlar: [
      { m: <>Yeni ESCO dosyaları pipeline'ın <code>veri</code> klasörüne konduktan sonra komutu <b>-MeslekHazirla</b> ile çalıştırın. Çeviri baştan yapıldığı için saatler sürebilir.</>, k: MESLEK_KOMUTU },
      { m: <>Bitince 3 adımla canlıya alın. Meslek listesi değiştiyse Pipeline Sonuçları → <b>Gelişmiş: meslek listesi</b> alanından <code>C:\pipeline\veri\meslekler_esco.csv</code> dosyasını da yükleyin.</> },
    ],
  },
  {
    id: 'geri', grup: 'Bölüm verisi (pipeline)', baslik: 'Yanlış veri canlıya alındıysa geri dönmek',
    ne_zaman: 'Canlıya aldığınız bir çıktının hatalı olduğunu fark ettiğinizde.',
    adimlar: [
      { m: <><b>B5 bağları / örnek meslekler:</b> Pipeline Sonuçları → ilgili adımda <b>Önceki sürümler</b> → <b>Bu sürüme dön</b> → <b>Eminim, bu sürüme dön</b>. Dönmeden önceki hâl de yedeklenir.</> },
      { m: <><b>Bölüm profilleri:</b> pipeline her çalıştırmada önceki çıktıyı <code>C:\pipeline\yedekler\bolum_agirliklari_&lt;tarih&gt;.xlsx</code> olarak saklar. Önceki dosyayı 1. adımla yükleyip <b>Yayına Al</b> deyin.</> },
    ],
  },
  // ------------------------------------------------------------------ Diğer veriler
  {
    id: 'kaynaklar', grup: 'Diğer veriler', baslik: 'TÜİK, asgari ücret, kamu maaşları, YKS tarihi ve diğer veriler',
    ne_zaman: <>Bir veri yeni dönem yayımladığında ya da <E to="/admin/veri-kaynaklari">Veri Kaynakları</E> ekranı bir kaynak için "kontrol zamanı" dediğinde.</>,
    adimlar: [
      { m: <><E to="/admin/veri-kaynaklari">Veri Kaynakları</E> → kaynağın satırında <b>Ayrıntı / kontrol</b>.</> },
      { m: <><b>Nasıl güncellenir?</b> bölümündeki numaralı adımları uygulayın. Her kaynağın hangi ekrandan, hangi dosyayla güncellendiği orada yazar.</> },
      { m: <>Bitince aynı yerde <b>Güncelledim</b> (ya da yalnızca baktıysanız <b>Kontrol ettim, güncel</b>) seçip <b>Kaydet</b> deyin. Kayıt Audit Log'a da yazılır.</> },
    ],
    not: 'Bölüm profilleri, B5 bağları, örnek meslekler ve meslekler de bu ekranda görünür; onların güncellemesi pipeline adımlarıyla yapılır.',
  },
  // ------------------------------------------------------------------ Hesaplar ve tanıtım
  {
    id: 'demo', grup: 'Hesaplar ve tanıtım', baslik: 'Tanıtım için demo okul açmak ve silmek',
    ne_zaman: 'Bir okula ya da kişiye sistemi verisiyle birlikte göstermek istediğinizde.',
    adimlar: [
      { m: <><E to="/admin/test-hesaplari">Test Hesapları</E> → <b>🏫 Demo okul</b> kartı: okul adı, paket, öğrenci sayısı ve yetkili adını girip <b>+ Demo okul oluştur</b>. Öğrencilerin değerlendirmeleri gerçek akışla cevaplanır; öğrenci başına 1–2 saniye sürer.</> },
      { m: <>Çıkan okul yetkilisi bağlantısını kopyalayıp paylaşın. Şifre yalnızca o an gösterilir. Bağlantıyı gizli pencerede açın.</> },
      { m: <>İşiniz bitince aynı ekrandaki <b>Demo okullar</b> listesinde <b>Sil</b> → <b>Eminim, okulu ve tüm verisini sil</b>. Yalnızca demo olarak açılmış okullar bu şekilde silinebilir. Demo okul <E to="/admin/okullar">Okullar</E> ekranındaki 🗑 → <b>Sil</b> ile de bütün verisiyle silinir.</> },
    ],
  },
  {
    id: 'testhesap', grup: 'Hesaplar ve tanıtım', baslik: 'Tek tek test hesabı açmak',
    ne_zaman: 'Bir ekranı belirli bir öğrenci ya da okul yetkilisi gözünden denemek istediğinizde.',
    adimlar: [
      { m: <><E to="/admin/test-hesaplari">Test Hesapları</E> → <b>Tek tek test hesabı</b>: Öğrenci ya da Okul yetkilisi seçin, ad soyad, okul ve sınıfı girip <b>+ Test hesabı aç</b>. Şifre yalnızca o an gösterilir.</> },
      { m: <>Satırdaki süre seçimiyle (1 saat – 1 hafta) <b>Bağlantı üret</b>; bağlantıyı gizli pencerede açın.</> },
      { m: <>Öğrencide <b>İlerlemeyi ayarla →</b> ile aşama ve eğilim seçip <b>Uygula</b>; değerlendirme gerçek akışla cevaplanır.</> },
    ],
    not: 'Okul yetkilisi test hesabı yalnızca demo okullarda açılabilir. Test hesapları KVKK, veli onayı ve iki adımlı doğrulamadan muaftır, istatistiklerde sayılmaz.',
  },
  {
    id: 'okulsil', grup: 'Hesaplar ve tanıtım', baslik: 'Gerçek bir okulu silmek',
    ne_zaman: 'Bir okul sistemden çıktığında.',
    adimlar: [
      { m: <><E to="/admin/okullar">Okullar</E> → okulun satırında 🗑 → gerçek öğrencilerin aktarılacağı yeri seçin (<b>Okul harici</b> ya da başka bir okul) → <b>Sil</b>.</> },
      { m: <>Okuldaki test öğrencileri aktarılmaz, verileriyle silinir; okul yetkilisi hesapları da silinir. İşlem Audit Log'a yazılır.</> },
    ],
    not: 'Silmeden önce okulun raporlarını almak isterseniz okulun panelinden Rapor Merkezi\'ni kullanın.',
  },
  // ------------------------------------------------------------------ Onaylar ve kayıtlar
  {
    id: 'onay', grup: 'Onaylar ve kayıtlar', baslik: 'Veli onay formlarını takip etmek',
    ne_zaman: 'Okula yeni öğrenci yüklendiğinde ve uygulama başlamadan önce.',
    adimlar: [
      { m: <><E to="/admin/onaylar">Onay Formları</E>: okul okul KVKK onayı ve veli onay formu tamamlanma durumu. <b>Yalnızca eksiği olanlar</b> kutusuyla süzün.</> },
      { m: <>Okulun satırında <b>Aç →</b> ile okul panelindeki <b>Onay Formları</b> bölümüne gidin; formları öğrenci adlarıyla indirin, imzalı formu alınca işaretleyin.</> },
    ],
    not: '18 yaşından küçük öğrenci, veli formu işaretlenmeden değerlendirmeye başlayamaz; 18 yaşını doldurmuş öğrenci resmî belgeden doğrulanıp "18 yaşını doldurmuş" olarak işaretlenir. Test hesapları muaftır.',
  },
  {
    id: 'erisimkayit', grup: 'Onaylar ve kayıtlar', baslik: 'Kim ne zaman girdi, kimin verisine baktı',
    ne_zaman: 'Bir giriş sorununu, yetkisiz erişim denemesini ya da bir öğrencinin verisine kimlerin baktığını incelemek istediğinizde.',
    adimlar: [
      { m: <><E to="/admin/erisim-kayitlari">Erişim Kayıtları</E>: tarih aralığı ya da <b>Bugün / 7 gün / 30 gün</b> seçin; kişi türü, olay ve okula göre süzün.</> },
      { m: <>Bir kişiye tıklayınca onun bütün kayıtları, bir öğrenciye tıklayınca o öğrencinin verisine kimlerin baktığı listelenir. <b>CSV indir</b> ile dışa aktarın.</> },
    ],
    not: 'Haftada bir "Başarısız giriş" ve "Reddedilen erişim" sayılarına bakmanız önerilir. Kayıtlar 365 gün saklanır (Parametreler → erisim_kaydi_saklama_gun).',
  },
  {
    id: 'kullanimanalizi', grup: 'Onaylar ve kayıtlar', baslik: 'Kim hangi menüde ne kadar süre geçiriyor',
    ne_zaman: 'Sistemin ne kadar ve nasıl kullanıldığını görmek; hangi okulda, hangi sınıfta ya da hangi menüde kullanımın düşük kaldığını bulmak istediğinizde.',
    adimlar: [
      { m: <><E to="/admin/kullanim-analizi">Kullanım Analizi</E>: dönemi (<b>7 / 30 / 90 gün, 1 yıl</b> ya da tarih) ve gerekirse okulu seçin. Rakamlar önceki eşit dönemle karşılaştırılır.</> },
      { m: <><b>Genel bakış</b>: öğrenci, okul yetkilisi ve süper admin yan yana (kayıtlı, kullanan, katılım, toplam ve kişi başı süre, oturum). <b>Öğrenciler / Okul yetkilileri / Süper adminler</b>: menü › alt sekme › içerik tablosu (ör. İş Hayatı › Okulda Öğretilmeyenler › tek tek dersler), gün × saat, süre dağılımı, cihaz, sınıflar.</> },
      { m: <><b>Okullar</b>: okul okul öğrenci ve yetkili kullanımı; okula tıklayınca bütün rapor o okula süzülür. <b>Kişiler</b>: herkes, hiç kullanmayanlar dahil; kişiye tıklayınca menüleri, günleri, saatleri ve oturumları açılır. Her tablo CSV olarak indirilebilir.</> },
    ],
    not: 'Süre "aktif süre"dir: sekme ekranda açık ve kişi son 2 dakikada dokunmuş / tıklamış / yazmış / kaydırmışsa sayılır. Ölçüm bu özellik canlıya alındığı andan başlar; önceki dönemler boş görünür. Test hesapları ve demo okullar varsayılan olarak hariçtir. Kayıtlar 730 gün saklanır (Parametreler → kullanim_suresi_saklama_gun).',
  },
  // ------------------------------------------------------------------ Sistem ve sunucu
  {
    id: 'depo', grup: 'Sistem ve sunucu', baslik: 'Pipeline veri deposunu bağlamak (Supabase)',
    ne_zaman: <>Pipeline Sonuçları <b>"Pipeline deposu henüz bağlı değil"</b> dediğinde (bir kez).</>,
    adimlar: [
      { m: <><b>Proje adresi:</b> Supabase'de projenizi açın. Tarayıcının adres çubuğunda <code>supabase.com/dashboard/project/<b>proje-kodu</b></code> yazar. Proje adresiniz <code>https://<b>proje-kodu</b>.supabase.co</code> olur.</> },
      { m: <><b>Gizli anahtar:</b> Project Settings → <b>API Keys</b> → <b>Secret keys</b> bölümündeki <code>sb_secret_…</code> ile başlayan anahtarı kopyalayın. (Yoksa aynı sayfanın <b>Legacy API Keys</b> sekmesindeki <b>service_role</b> anahtarı da olur; <code>eyJ…</code> ile başlar.) <b>anon / publishable</b> anahtarı çalışmaz.</> },
      { m: <>Render → backend servisi → <b>Environment</b> → <b>Add Environment Variable</b>: <code>SUPABASE_URL</code> = proje adresi, <code>SUPABASE_SERVICE_KEY</code> = gizli anahtar → <b>Save Changes</b>. Servis yeniden başlar (birkaç dakika).</> },
      { m: <>Pipeline Sonuçları'nda <b>"Veri deposu: Supabase Storage · bağlı ✓"</b> görünür.</> },
    ],
    not: 'Anahtarlar yalnızca sunucu ortam değişkenlerinde durur; koda ya da bu ekrana yazılmaz.',
  },
  {
    id: 'sunucu', grup: 'Sistem ve sunucu', baslik: 'Kendi sunucunuza taşınmak',
    ne_zaman: 'Render / Vercel / Supabase yerine kendi sunucunuzu kullanmaya geçtiğinizde.',
    adimlar: [
      { m: <><b>Veritabanı:</b> PostgreSQL kurun, Supabase'deki veriyi <code>pg_dump</code> ile alıp <code>pg_restore</code> ile yükleyin. Yeni tablolar backend açılırken kendiliğinden kurulur.</> },
      { m: <><b>Backend:</b> aynı uygulamayı çalıştırın. Ortam değişkenleri: <code>DATABASE_URL</code>, <code>JWT_SECRET_KEY</code> (64+ karakter), <code>CORS_ALLOWED_ORIGINS</code>, <code>FRONTEND_URL</code>, <code>OPENAI_API_KEY</code> (Filiz yapay zekâsı), <code>ORTAM=uretim</code>.</> },
      { m: <><b>E-posta:</b> <code>SMTP_SUNUCU</code>, <code>SMTP_PORT</code>, <code>SMTP_KULLANICI</code>, <code>SMTP_SIFRE</code> girin; Vercel e-posta ayarlarını boş bırakın.</> },
      { m: <><b>Pipeline deposu:</b> <code>PIPELINE_DEPO=disk</code> ve <code>PIPELINE_DEPO_DIZINI=/var/lib/filizyol/pipeline_depo</code> (ya da istediğiniz klasör). Klasörü backend'in yazabileceği izinle oluşturun. Supabase anahtarları artık gerekmez.</> },
      { m: <><b>Frontend:</b> derlenmiş dosyaları web sunucusunda (ör. nginx) yayınlayın; <code>/api/</code> isteklerini backend'e yönlendiren tek bir kural ekleyin.</> },
      { m: <>Taşındıktan sonra pipeline'ı, <b>en son veri gönderen</b> bilgisayarda bir kez çalıştırın: bütün veri yeni depoya kendiliğinden gönderilir.</>, k: CALISTIR_KOMUTU },
    ],
    not: <>Aynı alan adını ve <code>/api</code> yolunu kullanırsanız kurulu bilgisayarlara hiçbir şey yapmanız gerekmez. Alan adı değişirse her bilgisayara kurulum dosyası yeniden indirilir (veriler korunur).</>,
  },
]

const EKRANLAR = [
  ['Bölüm verisini yenilemek, canlıya almak, bilgisayar kurmak', '/admin/pipeline', 'Pipeline Sonuçları'],
  ['TÜİK, asgari ücret, kamu maaşları, YKS tarihi gibi verilerin güncelliği', '/admin/veri-kaynaklari', 'Veri Kaynakları'],
  ['Demo okul, test hesapları', '/admin/test-hesaplari', 'Test Hesapları'],
  ['Veli onay formu ve KVKK onayı tamamlanma durumu', '/admin/onaylar', 'Onay Formları'],
  ['Kim ne zaman girdi, kimin verisine baktı', '/admin/erisim-kayitlari', 'Erişim Kayıtları'],
  ['Kim hangi menüde ne kadar süre geçiriyor', '/admin/kullanim-analizi', 'Kullanım Analizi'],
  ['Gece çalışan işlerin sırası ve sonraki bakım saati', '/admin/gece-bakimi', 'Gece Bakımı'],
  ['Puanlama ve sistem ayarları', '/admin/parametreler', 'Parametreler'],
  ['Kim ne zaman hangi yönetim işlemini yaptı', '/admin/audit-log', 'Audit Log'],
  ['Sistem hataları', '/admin/hata-kayitlari', 'Hata Kayıtları'],
]

function Konu({ k, acik, onAc }) {
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }} id={k.id}>
      <button type="button" onClick={onAc} aria-expanded={acik}
        style={{ width: '100%', textAlign: 'left', background: 'none', border: 0, padding: '14px 16px', cursor: 'pointer', display: 'flex', gap: 10, alignItems: 'center' }}>
        <span style={{ fontWeight: 800, flex: 1 }}>{k.baslik}</span>
        <span className="yp-ince">{acik ? 'Kapat ▲' : 'Aç ▼'}</span>
      </button>
      {acik && (
        <div style={{ padding: '0 16px 14px' }}>
          <div className="yp-ince" style={{ marginBottom: 8 }}><b>Ne zaman:</b> {k.ne_zaman}</div>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            {k.adimlar.map((a, i) => (
              <li key={i} style={{ marginBottom: 8, lineHeight: 1.5 }}>{a.m}{a.k && <Komut metin={a.k} />}</li>
            ))}
          </ol>
          {k.not && <div className="yp-ince" style={{ marginTop: 6, background: 'var(--bg)', borderRadius: 8, padding: '8px 10px' }}>ℹ {k.not}</div>}
        </div>
      )}
    </div>
  )
}

export default function YonetimRehberiSayfasi() {
  const [acik, setAcik] = useState(() => (typeof window !== 'undefined' && window.location.hash ? window.location.hash.slice(1) : 'yillik'))
  const gruplar = useMemo(() => [...new Set(KONULAR.map((k) => k.grup))], [])
  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Yönetim Rehberi</div>
        <div className="ps">Sık yapılan işlerin adım adım anlatımı. Bir başlığa tıklayın; adımları sırayla uygulayın. Komutların yanındaki <b>Kopyala</b> ile
          cmd'ye yapıştırabilirsiniz.</div>
      </div>

      <div className="card">
        <div className="ct">Hangi iş hangi ekranda?</div>
        <table className="yp-tablo">
          <tbody>{EKRANLAR.map(([is_, yol, ad]) => (
            <tr key={yol}><td>{is_}</td><td><Link to={yol} className="ak-link">{ad}</Link></td></tr>
          ))}</tbody>
        </table>
      </div>

      {gruplar.map((g) => (
        <div key={g} style={{ marginTop: 18 }}>
          <div className="ct" style={{ marginBottom: 8 }}>{g}</div>
          {KONULAR.filter((k) => k.grup === g).map((k) => (
            <Konu key={k.id} k={k} acik={acik === k.id} onAc={() => setAcik(acik === k.id ? null : k.id)} />
          ))}
        </div>
      ))}
    </div>
  )
}
