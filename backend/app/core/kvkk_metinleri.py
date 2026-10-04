"""
[2026-10-04] KVKK aydınlatma metni ve onay maddeleri.

ÖNEMLİ: Bu metin bir ŞABLONDUR. Köşeli parantezli alanlar ([VERİ SORUMLUSU] vb.) şirket
bilgilerinizle doldurulmalı ve yayına almadan önce bir hukukçuya kontrol ettirilmelidir.
Metinde değişiklik yaptığınızda KVKK_SURUM değerini değiştirin (ör. "2026-10-v2"):
böylece tüm kullanıcılardan bir sonraki girişte yeniden onay istenir.
"""

KVKK_SURUM = "2026-10-v1"

VERI_SORUMLUSU = "[VERİ SORUMLUSU — ŞİRKET UNVANI]"
ADRES = "[ŞİRKET ADRESİ]"
ILETISIM_EPOSTA = "[KVKK BAŞVURU E-POSTA ADRESİ]"

AYDINLATMA_METNI = f"""KİŞİSEL VERİLERİN İŞLENMESİNE İLİŞKİN AYDINLATMA METNİ

{VERI_SORUMLUSU} ("Şirket") olarak, 6698 sayılı Kişisel Verilerin Korunması Kanunu ("KVKK") kapsamında veri sorumlusu sıfatıyla Filizyol bölüm ve kariyer uyum sistemini ("Sistem") kullanan öğrencilerin kişisel verilerini aşağıda açıklanan şekilde işlemekteyiz.

1. İşlenen kişisel veriler
• Kimlik ve iletişim: ad soyad, e-posta adresi.
• Eğitim bilgileri: okul, sınıf; isteğe bağlı olarak doğum tarihi, cinsiyet, hedef üniversite ve meslek.
• Değerlendirme verileri: değerler, kişilik, iş ortamı tercihleri ve alan eğilimi sorularına verdiğin cevaplar ve bunlardan hesaplanan sonuçlar, bölüm uyum puanları, hedef bölüm, gelişim planı ilerlemen, haftalık görevlerin ve yansıtma cevapların, deneme sınavı sonuçların.
• Koçluk sohbetleri: Filiz (yapay zekâ koçluk asistanı) ile yazıştığın mesajlar.
• Görsel kayıt (yalnızca ayrıca onay verirsen): değerlendirme sırasında kimlik doğrulama amacıyla çekilen kamera fotoğrafları.
• İşlem güvenliği: giriş kayıtları, IP adresi, değerlendirme sırasındaki sekme/tam ekran değişikliği kayıtları.

2. İşleme amaçları
Sana uygun üniversite bölümlerinin belirlenmesi ve sıralanması; hedef bölümüne yönelik kişisel gelişim planı ve haftalık görevlerin hazırlanması; yapay zekâ koçluk asistanının sana özel cevap verebilmesi; değerlendirme sonuçlarının güvenilirliğinin sağlanması; hesabının güvenliği (2 adımlı doğrulama, şifre sıfırlama); onay vermen halinde sonuçlarının okulundaki rehber öğretmenle paylaşılması; yasal yükümlülüklerin yerine getirilmesi.

3. Hukuki sebepler
Hizmetin sunulması için zorunlu veriler KVKK md. 5/2-(c) (sözleşmenin kurulması ve ifası) ve 5/2-(f) (meşru menfaat); kişilik ve ilgi analizine dayanan değerlendirme sonuçları, kamera fotoğrafları, rehber öğretmenle paylaşım ve yurt dışına aktarım ise md. 5/1 ve 9 kapsamında AÇIK RIZAN ile işlenir.

4. Aktarım
Verilerin; Sistem'in barındırıldığı bulut hizmet sağlayıcılarına (veritabanı, sunucu ve web barındırma), e-posta gönderimi için kullanılan e-posta hizmetine ve koçluk sohbetleri için yapay zekâ hizmet sağlayıcısına (OpenAI) aktarılır. Bu sağlayıcıların sunucuları yurt dışında bulunabilir. Onay vermen halinde değerlendirme sonuçların ve ilerleme bilgilerin okulundaki yetkili rehber öğretmenle paylaşılır. Yasal zorunluluk halinde yetkili kamu kurumlarıyla paylaşılabilir.

5. Toplama yöntemi
Veriler Sistem'e kayıt olurken, profilini doldururken, değerlendirmeleri çözerken ve Sistem'i kullanırken elektronik ortamda toplanır.

6. Saklama süresi
Veriler hesabın açık kaldığı sürece ve ilgili mevzuatta öngörülen süreler boyunca saklanır; hesabını silmen halinde makul süre içinde silinir veya anonim hale getirilir. Kamera fotoğrafları değerlendirmenin güvenilirliği incelendikten sonra en geç 6 ay içinde silinir.

7. Hakların (KVKK md. 11)
Verilerinin işlenip işlenmediğini öğrenme, bilgi talep etme, amacına uygun kullanılıp kullanılmadığını öğrenme, aktarıldığı üçüncü kişileri bilme, eksik/yanlış işlenmişse düzeltilmesini, silinmesini veya yok edilmesini isteme, otomatik analiz sonucu aleyhine bir sonuç çıkmasına itiraz etme ve zarara uğraman halinde zararın giderilmesini talep etme haklarına sahipsin. Açık rızanı dilediğin zaman Ayarlar sayfasından geri çekebilirsin.
Başvuruların için: {ILETISIM_EPOSTA} — {ADRES}

18 yaşından küçük kullanıcılar: Sistem'i velinin bilgisi ve onayıyla kullanmalısın. Bu metni velinle birlikte okumanı öneririz.
"""

# kod, kısa başlık, açıklama, zorunlu mu
ONAY_MADDELERI = [
    ("aydinlatma", "Aydınlatma metnini okudum ve anladım.",
     "Kişisel verilerinin nasıl işlendiğini anlatan metni okuduğunu belirtir.", True),
    ("acik_riza_analiz", "Değerlendirme cevaplarımın ve kişilik/ilgi analizimin yapılmasına ve saklanmasına açık rıza veriyorum.",
     "Bölüm önerileri ve koçluk bu analize dayandığı için sistemi kullanmak için gereklidir.", True),
    ("yurt_disi_aktarim", "Verilerimin, yurt dışında sunucuları bulunabilen bulut ve yapay zekâ hizmet sağlayıcılarına aktarılmasına açık rıza veriyorum.",
     "Sistem bulutta çalıştığı ve Filiz bir yapay zekâ hizmeti kullandığı için gereklidir.", True),
    ("veli_beyani", "18 yaşından küçüksem, sistemi velimin bilgisi ve onayıyla kullandığımı beyan ederim.",
     "Reşit olmayan kullanıcılar için veli bilgisi gereklidir.", True),
    ("rehber_paylasim", "Sonuçlarımın ve ilerleme bilgilerimin okulumdaki rehber öğretmenle paylaşılmasına açık rıza veriyorum.",
     "İsteğe bağlı. Vermezsen rehber öğretmenin yalnızca hesabının var olduğunu görür, sonuçlarını göremez.", False),
    ("kamera", "Değerlendirme sırasında kimlik doğrulama amacıyla kameramla fotoğraf çekilmesine açık rıza veriyorum.",
     "İsteğe bağlı. Vermezsen değerlendirmeler kamera kullanılmadan yapılır.", False),
]
ZORUNLU_KODLAR = {k for k, _b, _a, z in ONAY_MADDELERI if z}
TUM_KODLAR = {k for k, *_ in ONAY_MADDELERI}
