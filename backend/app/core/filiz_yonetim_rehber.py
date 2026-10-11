# -*- coding: utf-8 -*-
"""
[2026-10-11] Filiz — yönetim paneli asistanının KURAL TABANLI rehber modu (okul yetkilisi ve süper admin).

Bu modül yapay zekâ servisine HİÇBİR veri göndermez ve soruları kaydetmez. Cevaplar yalnızca (1) aşağıdaki SSS ve sayfa
dizini, (2) niyet kalıpları, (3) sayısal panel özeti (filiz_ozeti) üzerinden üretilir. Özet ve cevaplarda öğrenci adı
YOKTUR — yalnızca sayılar (ekranı başkaları görebilir). Yapay zekâ modu, kişiye özel soruların yerel cevabı ve maskeleme
app/core/filiz_yonetim_ai.py'dedir; o modül yapay zekâ kapalıyken / hata verince buradaki yanitla()'ya düşer.

Tek kaynak: okul yetkilisi SSS'i (YONETIM_SSS) burada durur; Sistem Hakkında & SSS sayfası onu GET /yonetim/filiz/sss
ile okur (frontend'de ikinci kopya yoktur).

Bağlantılar: "sayfa" ya mutlak bir yönetim yolu ("/admin/istatistikler") ya da okul paneli bölüm anahtarıdır
("ogrenciler"). Bölüm anahtarı okul yetkilisinde /admin/okul/{okul_id}?sekme=… olur; süper adminde okullar listesine
gider. Paketinde kapalı olan bölümlere giden bağlantıları arayüz (okulBolumleri.js) ayıklar.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.filiz_rehber import _sade

# ============================================================================= SSS (tek kaynak)
# (grup, soru, cevap, sayfa | None)
YONETIM_SSS: list[tuple[str, str, str, str | None]] = [
    ('Hesaplar', 'Öğrencileri sisteme nasıl eklerim?', 'Okul Paneli → Öğrenciler → "Öğrenci ekle / Excel yükle". Şablonu indirip ad soyad, e-posta, sınıf (ör. 12-A) ve isteğe bağlı öğrenci numarası ile şifreyi doldurun. Yüklemeden önce önizleme gösterilir; hatalı satırlar işaretlenir.', 'ogrenciler'),
    ('Hesaplar', 'Öğrencilerin şifrelerini nasıl dağıtırım?', 'Geçici şifreler Öğrenciler tablosunda "geçici" etiketiyle görünür. "Giriş listesi (Excel)" ile tüm listeyi indirip sınıflara dağıtabilirsiniz. Öğrenci kendi şifresini belirleyince geçici şifre listeden kalkar.', 'ogrenciler'),
    ('Hesaplar', 'Öğrenci şifresini unuttu.', 'Öğrenciyi seçip "Şifrelerini sıfırla" deyin; yeni geçici şifre tabloda görünür. Öğrenci giriş ekranındaki "Şifremi unuttum" bağlantısını da kullanabilir.', 'ogrenciler'),
    ('Hesaplar', 'Okulumuza birden fazla yetkili eklenebilir mi?', 'Evet. Yeni yetkili hesabı sistem yöneticisi (Filizyol) tarafından açılır; ad soyad, görev / unvan ve e-posta bilgisini iletmeniz yeterli. Okulunuzun yetkilileri Okul Yetkilileri sekmesinde listelenir. Tüm okul yetkilileri aynı yetkiye sahiptir.', 'yetkililer'),
    ('Sonuçlar', 'Bir öğrencinin sonuçlarını nerede görürüm?', 'Öğrenciler listesinde öğrencinin adına tıklayın. Açılan pencerede test ilerlemesi, sonuçlar, koçluk ilerlemesi, netler, benzer akranlar, ilgi ve kulüp sonuçları, kütüphanesi ve tüm işlem kayıtları yer alır (okulunuzun paketindeki modüllere göre).', 'ogrenciler'),
    ('Sonuçlar', 'Güven puanı nedir, düşükse ne yapmalıyım?', 'Değerlendirme sırasında sekme değiştirme, tam ekrandan çıkma, kamerayı kapatma gibi durumlar ve tutarlılık kontrolleri güven puanını belirler. Puan düşükse öğrenciyle konuşun; sonuçları dikkatle yorumlayın ve gerekirse yeniden değerlendirme planlayın.', None),
    ('Raporlar', 'Hangi raporları alabilirim?', 'Öğrenci bazında: yönetim (ayrıntılı), öğrenci, veli ve sınıf öğretmeni raporu (PDF) ile Excel. Şube bazında: sınıf raporu, Excel tablosu ve şubedeki tüm öğrencilerin veli / öğrenci / yönetim / sınıf öğretmeni raporları tek dosyada. Ayrıca sınıf düzeyi ve okul genel raporu. Toplu ve sınıf öğretmeni raporları Gelişmiş raporlar modülüyle gelir. Okulunuzun paketinde Öğrenci raporları modülü varsa öğrenciler de Raporlarım sayfasından kendi öğrenci ve veli raporlarını indirebilir.', 'raporlar'),
    ('Raporlar', 'İstatistikler ekranında neler var?', 'Raporlar ve İstatistikler → İstatistikler: katılım (haftalık giriş ve tamamlama, değerlendirme hunisi, şubelere göre durum), profil (katman ortalamaları, en güçlü ve en az öne çıkan özellikler, şube × katman, puan dağılımı), bölüm ve meslek, koçluk, akademik ve rehberlik göstergeleri. Sınıf düzeyi, şube ve tarih aralığına göre süzebilir, her grafiği tablo olarak görüp CSV, tümünü Excel olarak indirebilirsiniz. Paketinizde olmayan modüllerin istatistikleri görünmez; test hesapları sayılmaz.', 'istatistik'),
    ('Raporlar', 'Rapor Merkezi ne işe yarar?', 'İki sekmesi var. Tek Bakışta: öne çıkan bulgular, temel göstergeler, kritik öğrenciler, deneme sıralamaları, ısı renkli şube karşılaştırması ve grafikler; sınıf ve şubeye göre süzülür, "Yönetici özeti" PDF\'i olarak indirilir. Rapor İndir: okulunuzun indirebileceği tüm raporları tek yerde toplar: okul genel, sınıf düzeyi ve şube raporları (PDF / Excel), toplu veli / öğrenci / yönetim / sınıf öğretmeni PDF\'leri (Gelişmiş raporlar modülüyle), istatistikler Excel\'i ve paketinize göre deneme, anket, rehberlik görüşmesi, tercih ve mezun tabloları. Şube raporları Sınıflar sekmesinde de alınabilir.', 'raporlar'),
    ('Raporlar', 'Veli toplantısı için en pratik yol nedir?', 'Sınıflar sekmesinde ilgili şubenin "Rapor" menüsündeki "Veli (toplu)" seçeneği, şubedeki tüm öğrencilerin veli raporlarını öğrenci numarasına göre sıralı olarak tek PDF\'te verir.', 'siniflar'),
    ('Sınıflar', 'Sınıf öğretmenini nereye yazarım?', 'Sınıflar sekmesinde her şubenin satırındaki "Sınıf öğretmeni ekle" alanına. Bu bilgi şube raporlarında görünür.', 'siniflar'),
    ('Sınıflar', 'Şube dağılımı ve akran benzerliği nasıl kullanılmalı?', 'Şube & Akran sekmesi öğrencilerin profillerine göre öneri sunar. "Dengeli dağıt" her şubede farklı profillerin bulunmasını sağlar; "Benzerleri grupla" proje ve etüt grupları içindir. Öneriler karar destek amaçlıdır ve öğrencilere gösterilmez.', 'akran'),
    ('Sınıflar', 'Aday öğrenci nedir?', 'Okula kayıt için gelen öğrencileri sınıfı "Aday" olarak ekleyebilirsiniz. Aday testi çözünce hangi şubenin profiline daha yakın olduğunu görür, tek tıkla şubeye atayabilirsiniz.', 'akran'),
    ('Diğer', 'Kulüp listesini nasıl oluştururum?', 'Kulüpler sekmesinde "Hazır listeden ekle" ile yaygın lise kulüplerini ekleyip okulunuzda olmayanları silebilir ya da pasif yapabilirsiniz. Öğrenciler kısa ilgi testini çözdükçe her kulübe kaç öğrencinin uygun olduğunu görürsünüz.', 'kulupler'),
    ('Diğer', 'Eğitim koçları nasıl çalışır?', 'Eğitim koçlarıyla anlaşmayı ve okullara atamayı sistem yöneticisi (Filizyol) yapar; öğrencilerin görüşme taleplerini de o yönetir. Okulunuzda çalışmasını istemediğiniz bir koç olursa sistem yöneticisine bildirmeniz yeterli. Öğrenciler koçların iletişim bilgilerini görmez.', None),
    ('Diğer', 'Takvime ne eklemeliyim?', 'Veli toplantıları, üniversite gezileri, kulüp günleri, deneme sınavları gibi okul etkinliklerini. İsterseniz yalnızca belirli bir sınıf düzeyine gösterebilirsiniz. Sınav ve tercih dönemleri gibi genel tarihler sistem yöneticisi tarafından eklenir.', 'takvim'),
    ('Diğer', 'Okulumuzun rengi ve logosu nasıl değişir?', 'Renk, Okul Paneli → Görünüm sekmesinden seçilir; öğrenci ekranlarında, grafiklerde ve raporlarda kullanılır. Logoyu değiştirmek için sistem yöneticisine başvurun.', 'gorunum'),
    ('Diğer', 'Filiz panelde ne yapar?', 'Filiz, panelin sağ üstündeki asistandır. Açılışta günün en önemli 1–3 konusunu (ör. görüşme bekleyen yüksek uyarılı öğrenci sayısı, bekleyen kulüp talebi, incelemedeki tercih listesi, yaklaşan takvim etkinliği, yeni anket yanıtları) yalnızca sayılarla söyler ve ilgili sayfaya götürür; Filiz\'e tıklayınca sıradaki konuya geçer. "Bana sor" ile "rapor nereden alırım", "şifre sıfırla", "bugün ne var" gibi sorular sorabilirsiniz. Okulunuzun paketinde Filiz yapay zekâ modülü varsa cevapları yapay zekâ asistanı hazırlar (başlıkta "Yapay zekâ asistanı"); yoksa cevaplar bu SSS\'ten ve kural tabanlı eşleştirmeden gelir ("Rehber modu"). Belirli bir öğrenciyi (ad, e-posta, numara) ya da öğrenci listesini sorarsanız soru yapay zekâya gönderilmez: Filiz yalnızca kendi okulunuzun öğrencileri arasında arar, kısa özet ve öğrenci detayına bağlantı verir. Yapay zekâya giden sorularda öğrenci adları, e-posta, telefon, TC kimlik ve öğrenci numaraları önceden gizlenir; sorularınız kaydedilmez, yalnızca günlük soru sayısı tutulur. Balonda öğrenci adı gösterilmez. Küçültmek için Filiz\'in üzerine gelip "–" düğmesine basın; ses varsayılan olarak kapalıdır. Filiz, okulunuzun paketinde Filiz modülü açıksa görünür.', None),
]

# Süper admin: Sistem Hakkında sayfasının bölüm dizini (sayfadaki numaralı başlıklar; bağlantı #sh-N bölümü açar)
SISTEM_HAKKINDA = [
    (1, "Sistemin Genel Amacı", "amac genel asama surec nasil calisir"),
    (2, "Öğrenci Değerlendirmesi (K1-K5)", "degerlendirme katman k1 k2 k3 k4 k5 deger kisilik ilgi alan derinlesme degisken"),
    (3, "Bölüm-Meslek Eşleştirme Pipeline'ı", "pipeline esco meslek eslestirme agirlik taslak onet yukleme bolum profili"),
    (4, "Uyum Hesaplama (10 Yöntemli Karar Motoru)", "uyum skor hesaplama motor yontem puan formul"),
    (5, "Sonuç Sunumu ve Gizlilik Kuralları", "sonuc sunum gizlilik kural siralama kesfet"),
    (6, "Koçluk Modülü (Hedef Bölüm)", "kocluk hedef yol haritasi gap gelisim plani"),
    (7, "Soru Tipleri ve Puanlama Mantığı", "soru tipi likert sjt kutup kontrol puanlama"),
    (8, "Soru Geçerlilik Testi — Metodoloji", "gecerlilik soru testi metodoloji esik baseline"),
    (9, "Güvenlik & Tutarlılık Sistemi", "guvenlik tutarlilik guven puani kamera tam ekran gecersiz"),
    (10, "Admin Süreçleri — Veri Nasıl Yönetiliyor", "admin surec veri yonetim yukleme parametre"),
    (11, "Okul Modülleri ve Paketler", "modul paket rehberlik anket tercih filiz net takibi portfolyo bildirim"),
    (12, "Son Güncellemeler", "son guncelleme yenilik degisiklik surum"),
]

# ============================================================================= niyetler
# kod → (roller, anahtar kalıpları, cevap, [(etiket, sayfa)])
# Kalıp: boşlukla ayrılmış KÖKLER; bir kalıbın tüm kökleri soruda geçmeli (kelime başı eşleşmesi, Türkçe normalize).
OKUL, SUPER = "okul_yetkilisi", "super_admin"
HER = (OKUL, SUPER)

NIYETLER: list[dict] = [
    {"k": "veli_rapor", "rol": HER, "kalip": ["veli rapor", "veli toplanti", "veli pdf"],
     "metin": "Veli raporları: tek öğrenci için öğrencinin penceresindeki Raporlar menüsünden; bir şubenin tümü için Sınıflar → şube → Rapor → \"Veli (toplu)\".",
     "bag": [("Sınıflar", "siniflar"), ("Öğrenciler", "ogrenciler")]},
    {"k": "rapor", "rol": (OKUL,), "kalip": ["rapor", "pdf", "excel indir", "yonetici ozeti"],
     "metin": "Okulunuzun tüm raporları Rapor Merkezi'nde: \"Tek Bakışta\" yönetici özeti ve \"Rapor İndir\" (okul, sınıf düzeyi, şube, toplu PDF'ler, Excel tabloları).",
     "bag": [("Rapor Merkezi", "raporlar"), ("Sınıflar", "siniflar")]},
    {"k": "rapor", "rol": (SUPER,), "kalip": ["rapor", "pdf", "excel indir"],
     "metin": "Sistem geneli raporlar ve dışa aktarımlar Rapor Merkezi'nde; okula özel raporlar o okulun paneli → Rapor Merkezi'nde.",
     "bag": [("Rapor Merkezi", "/admin/raporlar"), ("Okullar", "/admin/okullar")]},
    {"k": "sifre", "rol": (OKUL,), "kalip": ["sifre", "parola", "giris yapamiyor", "giremiyor"],
     "metin": "Öğrenciler sekmesinde öğrenciyi seçip \"Şifrelerini sıfırla\" deyin; yeni geçici şifre tabloda görünür. Toplu dağıtım için \"Giriş listesi (Excel)\".",
     "bag": [("Öğrenciler", "ogrenciler")]},
    {"k": "sifre", "rol": (SUPER,), "kalip": ["sifre", "parola", "giris yapamiyor", "giremiyor"],
     "metin": "Okul yetkilisi şifreleri Okullar → okul → Okul Yetkilileri'nden, öğrenci şifreleri okulun paneli → Öğrenciler'den sıfırlanır. Süper admin hesapları Süper Adminler sayfasında.",
     "bag": [("Okullar", "/admin/okullar"), ("Süper Adminler", "/admin/yoneticiler")]},
    {"k": "ogrenci_ekle", "rol": (OKUL,), "kalip": ["ogrenci ekle", "ogrenci yukle", "toplu yukle", "hesap ac", "yeni ogrenci", "excel yukle"],
     "metin": "Öğrenciler → \"Öğrenci ekle / Excel yükle\": şablonu doldurun, önizlemede hatalı satırları düzeltin, yükleyin. Her öğrenci geçici şifreyle girer.",
     "bag": [("Öğrenciler", "ogrenciler")]},
    {"k": "ogrenci_ekle", "rol": (SUPER,), "kalip": ["ogrenci ekle", "ogrenci yukle", "toplu yukle", "yeni ogrenci", "okul ekle", "yeni okul"],
     "metin": "Okul ve öğrenci hesapları okul bazlıdır: Okullar → okulu seçin (ya da yeni okul ekleyin) → Öğrenciler sekmesi. Okulsuz öğrenciler \"Okul Harici Öğrenciler\"de.",
     "bag": [("Okullar", "/admin/okullar"), ("Okul Harici Öğrenciler", "/admin/okul/0")]},
    {"k": "kritik", "rol": (OKUL,), "kalip": ["kritik", "risk", "erken uyari", "dikkat gerek", "takip edil", "gorusme"],
     "metin": "Dikkat gerektiren öğrenciler Rehberlik → erken uyarı listesinde (seviye, neden ve son görüşme ile); özet hâli Rapor Merkezi → Tek Bakışta.",
     "bag": [("Rehberlik", "rehberlik"), ("Rapor Merkezi", "raporlar")]},
    {"k": "kritik", "rol": (SUPER,), "kalip": ["kritik", "risk", "erken uyari", "dikkat gerek"],
     "metin": "Öğrenci düzeyindeki erken uyarı listeleri okulların panelindedir (Okullar → okul → Rehberlik). Sistem genelinde dikkat gerektirenler Kontrol Paneli'nde; okul bazında yüksek uyarılı öğrenci sayıları Okul Karşılaştırması'nda.",
     "bag": [("Kontrol Paneli", "/admin"), ("Okul Karşılaştırması", "/admin/karsilastirma")]},
    {"k": "istatistik", "rol": (OKUL,), "kalip": ["istatistik", "grafik", "katilim", "tamamlama oran"],
     "metin": "İstatistikler: katılım, profil, bölüm ve meslek, koçluk, akademik ve rehberlik göstergeleri; sınıf, şube ve tarihe göre süzülür, Excel'e aktarılır.",
     "bag": [("İstatistikler", "istatistik")]},
    {"k": "istatistik", "rol": (SUPER,), "kalip": ["istatistik", "grafik", "katilim", "tamamlama oran", "kac ogrenci"],
     "metin": "Sistem geneli istatistikler (dönem, okul ve test hesabı filtresiyle) İstatistikler sayfasında; okulları yan yana görmek için Okul Karşılaştırması.",
     "bag": [("İstatistikler", "/admin/istatistikler"), ("Okul Karşılaştırması", "/admin/karsilastirma")]},
    {"k": "anket", "rol": (OKUL,), "kalip": ["anket", "tarama form", "olcek"],
     "metin": "Anketler sekmesinde \"Yeni anket\" ile kendi anketinizi oluşturun ya da hazır tarama formlarından birini seçin. Anonim sonuçlar en az 5 yanıtla gösterilir.",
     "bag": [("Anketler", "anketler")]},
    {"k": "anket", "rol": (SUPER,), "kalip": ["anket", "tarama form", "psikometri", "cronbach"],
     "metin": "Anketleri okullar kendi panellerinden oluşturur (Okullar → okul → Anketler). Tarama formlarının güvenirlik istatistikleri Anket Psikometrisi'nde.",
     "bag": [("Anket Psikometrisi", "/admin/anket-psikometri"), ("Okullar", "/admin/okullar")]},
    {"k": "deneme", "rol": (OKUL,), "kalip": ["deneme", "net", "tyt", "ayt"],
     "metin": "Okul Denemeleri sekmesinde Excel şablonunu indirip sonuçları yükleyin; netler öğrencilerin Net Takibi'ne düşer, şube ve ders ortalamaları hesaplanır.",
     "bag": [("Okul Denemeleri", "denemeler")]},
    {"k": "deneme", "rol": (SUPER,), "kalip": ["deneme", "tyt", "ayt", "konu listesi"],
     "metin": "Deneme sonuçlarını okullar kendi panelinden yükler (Okullar → okul → Okul Denemeleri). Net Takibi'nin konu listesi Konu Listesi sayfasında.",
     "bag": [("Okullar", "/admin/okullar"), ("Konu Listesi", "/admin/konular")]},
    {"k": "kaynakca", "rol": HER, "kalip": ["kaynakca", "kaynak", "referans", "bilimsel", "literatur"],
     "metin": "Sistemin bileşenleri, dayandığı kaynaklar ve hangi sayıların kurum içi karar olduğu Kaynakça sayfasında.",
     "bag": [("Kaynakça", "/admin/kaynakca")]},
    {"k": "paket", "rol": (OKUL,), "kalip": ["paket", "modul", "ozellik ac", "kapali"],
     "metin": "Okulunuzun paketi ve açık modüller Paket sekmesinde. Yeni bir modül için sistem yöneticisine (Filizyol) başvurun.",
     "bag": [("Paket", "paket")]},
    {"k": "paket", "rol": (SUPER,), "kalip": ["paket", "modul"],
     "metin": "Paket içerikleri Paketler sayfasında; bir okula paket atamak ya da modül eklemek/çıkarmak için Okullar → okul → Paket.",
     "bag": [("Paketler", "/admin/paketler"), ("Okullar", "/admin/okullar")]},
    {"k": "hata", "rol": (SUPER,), "kalip": ["hata", "sentry", "hata log", "cokme", "500", "bug"],
     "metin": "Sunucu ve tarayıcı hataları gruplu olarak Hata Kayıtları'nda (çözüldü işaretleme, yığın izi, istek kimliği). Yönetim işlemleri Audit Log'da.",
     "bag": [("Hata Kayıtları", "/admin/hata-kayitlari"), ("Audit Log", "/admin/audit-log")]},
    {"k": "tuik", "rol": (SUPER,), "kalip": ["tuik", "istihdam", "maas", "kazanc", "is hayati veri", "asgari ucret"],
     "metin": "TÜİK istihdam göstergeleri, Kazanç Yapısı, kamu maaşları ve asgari ücret İş Hayatı Verileri sayfasından yüklenir/güncellenir.",
     "bag": [("İş Hayatı Verileri", "/admin/is-hayati-verileri")]},
    {"k": "pipeline", "rol": (SUPER,), "kalip": ["pipeline", "agirlik", "taslak", "esco"],
     "metin": "Bölüm ağırlığı yüklemeleri ve onay bekleyen taslaklar Pipeline Durumu sayfasında; onaylanana kadar skor motorunda kullanılmaz.",
     "bag": [("Pipeline Durumu", "/admin/pipeline")]},
    {"k": "parametre", "rol": (SUPER,), "kalip": ["parametre", "katman agirlik", "esik", "ayar"],
     "metin": "Sistem parametreleri (katman ağırlıkları, eşikler, süreler) Parametreler sayfasında; değişiklikler denetim kaydına yazılır.",
     "bag": [("Parametreler", "/admin/parametreler")]},
    {"k": "audit", "rol": (OKUL,), "kalip": ["audit", "denetim kayd", "islem gecmis", "islem kayd", "kim yapti"],
     "metin": "Okul panelindeki işlemlerin geçmişi (kim, ne zaman, ne yaptı) Kayıtlar sekmesinde.",
     "bag": [("Kayıtlar", "kayitlar")]},
    {"k": "audit", "rol": (SUPER,), "kalip": ["audit", "denetim kayd", "islem gecmis", "kim yapti"],
     "metin": "Tüm yönetim işlemleri Audit Log'da (Excel'e aktarılabilir).",
     "bag": [("Audit Log", "/admin/audit-log")]},
    {"k": "soru", "rol": (SUPER,), "kalip": ["soru banka", "soru ekle", "soru duzenle", "gecerlilik"],
     "metin": "Değerlendirme soruları Soru Bankası'nda; soruların geçerlilik analizi Soru Geçerlilik Testi'nde.",
     "bag": [("Soru Bankası", "/admin/sorular"), ("Soru Geçerlilik Testi", "/admin/soru-gecerlilik")]},
    {"k": "bolum", "rol": (SUPER,), "kalip": ["bolum ekle", "bolum duzenle", "bolumler", "yok atlas", "yokatlas"],
     "metin": "Bölümler sayfasında bölüm içeriği ve yayın durumu; YÖK Atlas eşleştirmeleri ayrı sayfada.",
     "bag": [("Bölümler", "/admin/bolumler"), ("YÖK Atlas Eşleştirme", "/admin/yokatlas")]},
    {"k": "takvim", "rol": (OKUL,), "kalip": ["takvim", "etkinlik", "toplanti tarih"],
     "metin": "Okul etkinliklerini Takvim sekmesinden ekleyin; isterseniz yalnızca belirli bir sınıf düzeyine gösterin.",
     "bag": [("Takvim", "takvim")]},
    {"k": "takvim", "rol": (SUPER,), "kalip": ["takvim", "etkinlik", "sinav tarih"],
     "metin": "Tüm okullarda görünen sınav / tercih dönemi gibi tarihler Genel Takvim'de.",
     "bag": [("Genel Takvim", "/admin/takvim")]},
    {"k": "kulup", "rol": (OKUL,), "kalip": ["kulup"],
     "metin": "Kulüpler sekmesinde kulüp listesi, ilgi testi sonuçları ve katılma talepleri (onay / ret).",
     "bag": [("Kulüpler", "kulupler")]},
    {"k": "tercih", "rol": (OKUL,), "kalip": ["tercih", "yerlesme", "mezun"],
     "metin": "12. sınıf ve mezunların tercih listeleri Tercih Dönemi sekmesinde (inceleme, onay, düzeltme isteği); yerleşmeler Mezunlar'da.",
     "bag": [("Tercih Dönemi", "tercih"), ("Mezunlar", "mezunlar")]},
    {"k": "sinif", "rol": (OKUL,), "kalip": ["sinif ogretmen", "sube", "sinif ata"],
     "metin": "Şubeler, sınıf öğretmenleri ve şube raporları Sınıflar sekmesinde; şube dağılımı önerileri Şube & Akran'da.",
     "bag": [("Sınıflar", "siniflar"), ("Şube & Akran", "akran")]},
    {"k": "yetkili", "rol": (OKUL,), "kalip": ["yetkili ekle", "yeni yetkili", "okul yetkili"],
     "metin": "Okulunuzun yetkilileri Okul Yetkilileri sekmesinde listelenir; yeni yetkili hesabını sistem yöneticisi açar.",
     "bag": [("Okul Yetkilileri", "yetkililer")]},
    {"k": "yetkili", "rol": (SUPER,), "kalip": ["yetkili ekle", "yeni yetkili", "okul yetkili", "super admin ekle"],
     "metin": "Okul yetkilisi: Okullar → okul → Okul Yetkilileri. Süper admin: Süper Adminler sayfası.",
     "bag": [("Okullar", "/admin/okullar"), ("Süper Adminler", "/admin/yoneticiler")]},
    {"k": "test_hesap", "rol": (SUPER,), "kalip": ["test hesab", "demo"],
     "metin": "Süreli giriş bağlantılı test hesapları Test Hesapları sayfasında; istatistiklerde sayılmaz.",
     "bag": [("Test Hesapları", "/admin/test-hesaplari")]},
    {"k": "koc", "rol": (SUPER,), "kalip": ["egitim koc", "koc talep", "koclar"],
     "metin": "Eğitim koçları, okul atamaları ve görüşme talepleri Eğitim Koçları sayfasında.",
     "bag": [("Eğitim Koçları", "/admin/koclar")]},
    {"k": "sss", "rol": HER, "kalip": ["sss", "sikca sorulan", "yardim", "kullanim kilavuz"],
     "metin": "Kullanım rehberi ve sıkça sorulan sorular Sistem Hakkında & SSS sayfasında.",
     "bag": [("Sistem Hakkında & SSS", "/admin/sss")]},
]

DURUM_KALIPLARI = ["durum", "ozet", "bugun", "ne var", "neler var", "gundem", "onemli ne", "ilgilen", "bekleyen", "yapilacak"]
SELAM_KALIPLARI = ["merhaba", "selam", "gunaydin", "iyi gunler", "nasilsin"]
TESEKKUR_KALIPLARI = ["tesekkur", "sagol", "eyvallah", "super"]
KIM_KALIPLARI = ["sen kimsin", "filiz kim", "filiz ne", "ne yaparsin", "neler yapabilir", "panelde ne yapar"]

ONERILER = {
    OKUL: ["Bugün ne var?", "Raporu nereden alırım?", "Veli raporu nasıl alınır?", "Öğrenci şifresi nasıl sıfırlanır?",
           "Öğrenci nasıl eklenir?", "Kritik öğrenciler nerede?", "Anket nasıl oluşturulur?", "Deneme sonucu nasıl yüklenir?"],
    SUPER: ["Bugün ne var?", "Hata kayıtları nerede?", "TÜİK verisi nasıl güncellenir?", "İstatistikler nerede?",
            "Paketler nasıl düzenlenir?", "Pipeline taslağı nerede?", "Okul nasıl eklenir?", "Kaynakça nerede?"],
}

_DURAK = set("""ne neden nasil nerede nereden nereye hangi hangisi kac bir bu su o ve ile ya da veya mi mu mı mü icin ben beni bana benim
biz bizim siz sizin var yok ki de da den dan te ta ise olarak gibi daha en cok cok az acaba lutfen filiz bana sor
yapilir yaparim yapabilirim yapariz edebilirim alabilirim alirim gorebilirim gorurum bulurum bulabilirim olur olmali
nedir neler nelerdir istiyorum lazim gerek gerekiyor olustur olusturulur olustururum yapmaliyim yapmali alinir guncellenir guncellerim""".split())


def normalize(m: str) -> str:
    """Türkçe küçük harf + aksan sadeleştirme + noktalama temizliği (filiz_rehber._sade üzerine)."""
    return " ".join(re.sub(r"[^0-9a-z]+", " ", _sade(m or "")).split())


def _kokler(m: str) -> list[str]:
    """Anlamlı kelimelerin kökleri (Türkçe ekler için ilk 5 harf; çok kısa kelimeler aynen)."""
    return [t[:5] for t in normalize(m).split() if t not in _DURAK and len(t) >= 2]


def _kalip_uyar(n: str, kalip: str) -> bool:
    """Kalıptaki her kök, normalize edilmiş metinde bir kelimenin BAŞINDA geçmeli."""
    kelimeler = n.split()
    return all(any(k.startswith(p) for k in kelimeler) for p in kalip.split())


def _herhangi(n: str, kaliplar: list[str]) -> bool:
    return any(_kalip_uyar(n, k) for k in kaliplar)


# ----------------------------------------------------------------------------- bağlantılar
def yol_coz(sayfa: str | None, rol: str, okul_id: int | None) -> str | None:
    if not sayfa:
        return None
    if sayfa.startswith("/"):
        return sayfa
    if rol == OKUL and okul_id:
        return f"/admin/okul/{okul_id}" + ("" if sayfa == "ozet" else f"?sekme={sayfa}")
    return "/admin/okullar"


def _bag(etiket: str, sayfa: str | None, rol: str, okul_id: int | None) -> dict | None:
    y = yol_coz(sayfa, rol, okul_id)
    if not y:
        return None
    if rol == SUPER and sayfa and not sayfa.startswith("/"):
        etiket = f"Okullar → {etiket}"
    return {"etiket": etiket, "yol": y}


def sss_listesi(rol: str, okul_id: int | None) -> list[dict]:
    return [{"grup": g, "soru": s, "cevap": c, "baglanti": _bag(_SAYFA_ADI.get(p, "Aç"), p, rol, okul_id) if p else None}
            for g, s, c, p in YONETIM_SSS]


_SAYFA_ADI = {"ogrenciler": "Öğrenciler", "yetkililer": "Okul Yetkilileri", "raporlar": "Rapor Merkezi", "istatistik": "İstatistikler",
              "siniflar": "Sınıflar", "akran": "Şube & Akran", "kulupler": "Kulüpler", "takvim": "Takvim", "gorunum": "Görünüm",
              "rehberlik": "Rehberlik", "anketler": "Anketler", "tercih": "Tercih Dönemi", "paket": "Paket", "denemeler": "Okul Denemeleri"}


# ----------------------------------------------------------------------------- SSS eşleştirme (ağırlıklı kök örtüşmesi)
def _belgeler(rol: str) -> list[dict]:
    # "Filiz panelde ne yapar?" cevabı birçok sayfayı sayar; yalnızca başlığıyla eşleşsin (her soruya çıkmasın)
    b = [{"tur": "sss", "soru": s, "cevap": c, "sayfa": p, "bas": _kokler(s), "govde": _kokler(s if "Filiz" in s else f"{g} {c}")}
         for g, s, c, p in YONETIM_SSS]
    if rol == SUPER:
        b += [{"tur": "sh", "soru": f"Sistem Hakkında — {no}. {bas}", "cevap": f"Teknik ayrıntılar Sistem Hakkında sayfasının {no}. bölümünde.",
               "sayfa": f"/admin/sistem-hakkinda#sh-{no}", "bas": _kokler(bas), "govde": _kokler(anahtar)}
              for no, bas, anahtar in SISTEM_HAKKINDA]
    return b


def _idf(belgeler: list[dict]) -> dict:
    df = Counter(k for d in belgeler for k in set(d["bas"]) | set(d["govde"]))
    n = len(belgeler)
    return {k: math.log(1 + n / v) for k, v in df.items()}


def sss_eslestir(metin: str, rol: str, okul_id: int | None = None, en_fazla: int = 3) -> list[dict]:
    sorgu = set(_kokler(metin))
    if not sorgu:
        return []
    belgeler = _belgeler(rol)
    idf = _idf(belgeler)
    puanli = []
    for d in belgeler:
        bas, govde = set(d["bas"]), set(d["govde"])
        bas_n = sum(1 for k in sorgu if k in bas)
        govde_n = sum(1 for k in sorgu if k in govde and k not in bas)
        if not bas_n and govde_n < 2:   # yalnızca cevap metninde geçen tek kelime tesadüftür
            continue
        p = sum(idf.get(k, 0) * (2.0 if k in bas else 1.0 if k in govde else 0) for k in sorgu)
        puanli.append((p, bas_n, d))
    if not puanli:
        return []
    puanli.sort(key=lambda x: -x[0])
    en_iyi = puanli[0][0]
    esik = max(1.6, en_iyi * 0.55)   # zayıf eşleşmeleri at; en iyinin çok gerisindekileri gösterme
    sonuc = []
    for p, bas_n, d in puanli:
        if p < esik or len(sonuc) >= en_fazla:
            break
        etiket = "Sistem Hakkında" if d["tur"] == "sh" else _SAYFA_ADI.get(d["sayfa"], "Aç")
        sonuc.append({"soru": d["soru"], "cevap": d["cevap"], "puan": round(p, 2), "baslikta": bas_n > 0,
                      "baglanti": _bag(etiket, d["sayfa"], rol, okul_id) if d["sayfa"] else None})
    return sonuc


def niyet_bul(metin: str, rol: str) -> list[dict]:
    n = normalize(metin)
    bulunan = []
    for niy in NIYETLER:
        if rol not in niy["rol"]:
            continue
        uzunluk = max((len(k.split()) for k in niy["kalip"] if _kalip_uyar(n, k)), default=0)
        if uzunluk:
            bulunan.append((uzunluk, niy))
    bulunan.sort(key=lambda x: -x[0])   # daha özel (çok kelimeli) kalıp önce: "veli raporu" > "rapor"
    gorulen, sonuc = set(), []
    for _, niy in bulunan:
        if niy["k"] in gorulen:
            continue
        gorulen.add(niy["k"])
        sonuc.append(niy)
    return sonuc[:2]


# ============================================================================= panel özeti (yalnızca sayılar)
def _guvenli(db: Session, fn, varsayilan):
    try:
        with db.begin_nested():
            return fn()
    except Exception:
        return varsayilan


def _tarih(d: date) -> str:
    aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    return f"{d.day} {aylar[d.month - 1]}"


SEVIYE_SIRA = {"yuksek": 0, "uyari": 1, "bilgi": 2, "olumlu": 3}


def okul_ozeti(db: Session, okul_id: int, bugun: date | None = None) -> list[dict]:
    from app.core.paketler import okul_modulleri
    bugun = bugun or date.today()
    mod = set(okul_modulleri(db, okul_id))
    B: list[dict] = []

    def ekle(k, seviye, ikon, metin, sayfa, etiket):
        B.append({"k": k, "seviye": seviye, "ikon": ikon, "metin": metin, "baglanti": _bag(etiket, sayfa, OKUL, okul_id)})

    def uyarilar():
        from app.api.rehberlik import uyarilari_hesapla
        return uyarilari_hesapla(db, okul_id)
    ham = _guvenli(db, uyarilar, [])
    if "rehberlik" in mod:
        yuksek = [s for s in ham if s["seviye"] == "yuksek"]
        gorusmesiz = [s for s in yuksek if not s.get("son_gorusme") and not s.get("yaklasan_gorusme")]
        if gorusmesiz:
            ekle("gorusmesiz", "yuksek", "🧭", f"{len(gorusmesiz)} öğrenci yüksek seviyede uyarıda ve henüz görüşme yapılmadı ya da planlanmadı.",
                 "rehberlik", "Rehberlik")
        elif yuksek:
            ekle("yuksek", "bilgi", "🧭", f"Yüksek seviyede uyarıdaki {len(yuksek)} öğrencinin tamamıyla görüşme yapıldı ya da planlandı.",
                 "rehberlik", "Rehberlik")
    kural = Counter(u["kural"] for s in ham for u in s["uyarilar"])
    if kural.get("yarim_test"):
        ekle("yarim", "uyari", "⏸️", f"{kural['yarim_test']} öğrenci değerlendirmeyi yarıda bıraktı (bir haftadır devam etmiyor).",
             "rehberlik" if "rehberlik" in mod else "raporlar", "Rehberlik" if "rehberlik" in mod else "Rapor Merkezi")
    if "tercih" in mod:
        n = _guvenli(db, lambda: db.execute(text("""
            SELECT count(*) FROM tercih_listesi t JOIN ogrenciler o ON o.id = t.ogrenci_id
             WHERE o.okul_id = :ok AND t.durum = 'incelemede' AND NOT coalesce(o.test_hesabi, false)"""), {"ok": okul_id}).scalar() or 0, 0)
        if n:
            ekle("tercih", "uyari", "🎓", f"{n} tercih listesi incelemenizi bekliyor.", "tercih", "Tercih Dönemi")
    if "kulupler" in mod:
        n = _guvenli(db, lambda: db.execute(text("""
            SELECT count(*) FROM kulup_uyelikleri u JOIN okul_kulupleri k ON k.id = u.kulup_id
             WHERE k.okul_id = :ok AND u.durum = 'bekliyor'"""), {"ok": okul_id}).scalar() or 0, 0)
        if n:
            ekle("kulup", "uyari", "🎭", f"{n} kulüp katılma talebi yanıt bekliyor.", "kulupler", "Kulüpler")
    if "takvim" in mod:
        r = _guvenli(db, lambda: db.execute(text("""
            SELECT count(*) OVER () AS n, baslik, baslangic FROM takvim_etkinlikleri
             WHERE ogrenci_id IS NULL AND (okul_id = :ok OR okul_id IS NULL) AND baslangic BETWEEN :b AND :s
             ORDER BY baslangic, id LIMIT 1"""), {"ok": okul_id, "b": bugun, "s": bugun + timedelta(days=7)}).first(), None)
        if r:
            ne = "Bugün" if r.baslangic == bugun else _tarih(r.baslangic)
            ekle("takvim", "bilgi", "📅", f"Önümüzdeki 7 günde {r.n} takvim etkinliği var; en yakını: {r.baslik} ({ne}).", "takvim", "Takvim")
    if "anketler" in mod:
        n = _guvenli(db, lambda: db.execute(text("""
            SELECT count(*) FROM anket_katilim k JOIN anketler a ON a.id = k.anket_id
             WHERE a.okul_id = :ok AND k.zaman >= now() - interval '7 days'"""), {"ok": okul_id}).scalar() or 0, 0)
        if n:
            ekle("anket", "bilgi", "📋", f"Son 7 günde anketlerinize {n} yeni yanıt geldi.", "anketler", "Anketler")
    if kural.get("giris_yok"):
        ekle("giris_yok", "bilgi", "🔑", f"{kural['giris_yok']} öğrenci hesabı açıldığı hâlde henüz hiç giriş yapmadı.", "ogrenciler", "Öğrenciler")
    B.sort(key=lambda b: SEVIYE_SIRA[b["seviye"]])   # kararlı sıralama: aynı seviyede yukarıdaki öncelik korunur
    return B


_SUPER_SAYFA = {"/admin/pipeline": "Pipeline Durumu", "/admin/guvenlik": "Güvenlik / Tutarlılık", "/admin/karsilastirma": "Okul Karşılaştırması",
                "/admin/okullar": "Okullar", "/admin/koclar": "Eğitim Koçları", "/admin/test-hesaplari": "Test Hesapları", "/admin/bolumler": "Bölümler"}
SUPER_ONCELIK = ["pipeline", "yetkilisiz", "gecersiz", "koc", "yarim", "giris_yok", "yetkili_sifre", "test_suresi", "paketsiz", "bolum_taslak"]


def sistem_ozeti(db: Session, yon) -> list[dict]:
    from app.api.sistem_istatistik import dikkat_gerektirenler
    from app.core.tuik_baglanti import guncelleme_durumu
    B: list[dict] = []

    def ekle(k, seviye, ikon, metin, yol, etiket):
        B.append({"k": k, "seviye": seviye, "ikon": ikon, "metin": metin, "baglanti": {"etiket": etiket, "yol": yol}})

    h = _guvenli(db, lambda: db.execute(text("""
        SELECT COUNT(*) FILTER (WHERE NOT cozuldu_mu) AS acik,
               COUNT(*) FILTER (WHERE NOT cozuldu_mu AND ilk_gorulme > now() - interval '24 hours') AS yeni
          FROM hata_kayitlari""")).mappings().first(), None)
    if h and h["yeni"]:
        ekle("hata_yeni", "yuksek", "🐞", f"Son 24 saatte {h['yeni']} yeni hata grubu görüldü (açık toplam {h['acik']}).", "/admin/hata-kayitlari", "Hata Kayıtları")
    elif h and h["acik"]:
        ekle("hata_acik", "bilgi", "🐞", f"{h['acik']} hata grubu çözüm bekliyor.", "/admin/hata-kayitlari", "Hata Kayıtları")
    t = _guvenli(db, lambda: guncelleme_durumu(db), None)
    if t and not t["guncel"]:
        ekle("tuik", "uyari", "📈", f"TÜİK {t['beklenen_veri_yili']} istihdam verisi yayımlanmış olabilir; sistemdeki son veri "
             + (f"{t['son_veri_yili']} yılına ait." if t["son_veri_yili"] else "henüz yok."), "/admin/is-hayati-verileri", "İş Hayatı Verileri")
    d = _guvenli(db, lambda: dikkat_gerektirenler(db=db, yon=yon), {"maddeler": []})
    sira = {k: i for i, k in enumerate(SUPER_ONCELIK)}
    for m in sorted(d.get("maddeler") or [], key=lambda m: sira.get(m["k"], 99)):
        seviye = "uyari" if m["seviye"] == "uyari" else "bilgi"
        ekle(m["k"], seviye, m["ikon"], f"{m['baslik']}: {m['sayi']}.", m["link"], _SUPER_SAYFA.get(m["link"], "Aç"))
    B.sort(key=lambda b: SEVIYE_SIRA[b["seviye"]])
    return B


def filiz_ozeti(db: Session, yon) -> dict:
    if yon.rol == SUPER:
        bulgular = sistem_ozeti(db, yon)
    else:
        bulgular = okul_ozeti(db, yon.okul_id) if yon.okul_id else []
    return {"rol": yon.rol, "bulgular": bulgular, "oneriler": ONERILER[yon.rol]}


# ============================================================================= cevap
def yanitla(db: Session, yon, metin: str) -> dict:
    rol, okul_id = yon.rol, yon.okul_id
    n = normalize(metin)
    oneriler = ONERILER[rol]
    bos = {"cevaplar": [], "baglantilar": [], "bulgular": [], "oneriler": []}

    if not n:
        return {**bos, "tur": "anlamadim", "metin": "Bir soru yazın ya da aşağıdakilerden birini seçin.", "oneriler": oneriler}
    if _herhangi(n, KIM_KALIPLARI):
        s = next(x for x in sss_listesi(rol, okul_id) if x["soru"] == "Filiz panelde ne yapar?")
        return {**bos, "tur": "yanit", "metin": s["cevap"], "oneriler": oneriler[:4]}
    if _herhangi(n, DURUM_KALIPLARI):
        bul = filiz_ozeti(db, yon)["bulgular"]
        m = (f"Bugün öne çıkan {len(bul)} konu var:" if bul else "Şu an ilgilenmeniz gereken bir konu görünmüyor. ✓")
        return {**bos, "tur": "durum", "metin": m, "bulgular": bul[:6], "oneriler": [o for o in oneriler if o != "Bugün ne var?"][:3]}

    niyetler = niyet_bul(metin, rol)
    cevaplar = sss_eslestir(metin, rol, okul_id)
    if niyetler or cevaplar:
        baglantilar, gorulen = [], set()
        for niy in niyetler:
            for etiket, sayfa in niy["bag"]:
                b = _bag(etiket, sayfa, rol, okul_id)
                if b and b["yol"] not in gorulen:
                    gorulen.add(b["yol"])
                    baglantilar.append(b)
        m = " ".join(niy["metin"] for niy in niyetler) if niyetler else "Şunlar işinize yarayabilir:"
        if niyetler:   # niyet cevabı zaten verildi: SSS'ten yalnızca başlığı eşleşen 1–2 madde
            cevaplar = [c for c in cevaplar if c["baslikta"]][:2]
        return {**bos, "tur": "yanit", "metin": m, "baglantilar": baglantilar[:4], "cevaplar": cevaplar}

    if _herhangi(n, SELAM_KALIPLARI):
        return {**bos, "tur": "selam", "metin": "Merhaba! Panelde bir şeyi nerede bulacağınızı ya da nasıl yapacağınızı sorabilirsiniz. 🌱",
                "oneriler": oneriler[:4]}
    if _herhangi(n, TESEKKUR_KALIPLARI):
        return {**bos, "tur": "selam", "metin": "Rica ederim! Başka bir şey olursa buradayım. 🌱", "oneriler": oneriler[:3]}
    return {**bos, "tur": "anlamadim",
            "metin": "Bunu tam anlayamadım. Sorunuzu birkaç anahtar kelimeyle yazmayı deneyin (ör. \"veli raporu\", \"şifre sıfırla\") ya da birini seçin:",
            "oneriler": oneriler}
