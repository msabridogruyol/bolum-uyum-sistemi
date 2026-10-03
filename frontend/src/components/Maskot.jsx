import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../api/client'

/*
 * [2026-10-03] Filiz maskotu — sağ üstte duran, hedef bölüme göre kıyafet değiştiren,
 * ara ara motivasyon cümlesi söyleyen animasyonlu karakter.
 *  - Görünüm: profildeki cinsiyete göre (erkek / kadın / diğer → filiz karakter)
 *  - Kıyafet: aktif hedef bölümün adına göre 24 farklı kıyafet
 *  - Animasyonlar: nefes alma, göz kırpma, imleci takip eden gözler, filiz sallanması, el sallama,
 *    zıplama, dönme, dans, düşünme, başını sallama, konuşurken ağız hareketi, uyuma (Zzz),
 *    kalp ve konfeti efektleri, giriş animasyonu
 *  - Tıklayınca: yeni bir cümle + rastgele animasyon. Küçültülebilir ve sessize alınabilir.
 * Tamamen SVG + CSS; dışarıdan resim dosyası yoktur. Soru ekranlarında görünmez (o sayfalar bu düzenin dışında).
 */

// ----------------------------------------------------------------------------- Kıyafet seçimi
const KIYAFET_KURALLARI = [
  ['ogretmen', ['öğretmenliği', 'çocuk gelişimi', 'okul öncesi', 'özel eğitim', 'rehberlik']],
  ['astronot', ['uzay', 'astronomi']],
  ['pilot', ['pilotaj', 'havacılık', 'uçak', 'hava trafik', 'sivil hava']],
  ['kaptan', ['deniz', 'gemi', 'güverte', 'denizcilik']],
  ['hukuk', ['hukuk']],
  ['dedektif', ['adli']],
  ['veteriner', ['veteriner', 'zootekni']],
  ['dis', ['diş hekimliği']],
  ['eczaci', ['eczacılık']],
  ['doktor', ['tıp', 'hemşirelik', 'ebelik', 'sağlık', 'fizyoterapi', 'ergoterapi', 'odyoloji', 'perfüzyon', 'beslenme', 'konuşma terapisi', 'ortez', 'acil yardım', 'gerontoloji']],
  ['analist', ['ekonometri', 'istatistik', 'veri bilimi', 'aktüerya', 'matematik']],
  ['yazilimci', ['bilgisayar', 'yazılım', 'yapay zeka', 'siber', 'bilişim', 'bilgi güvenliği', 'oyun', 'teknoloji girişimciliği']],
  ['elektrik', ['elektrik', 'elektronik', 'mekatronik', 'kontrol ve otomasyon', 'enerji', 'nükleer', 'fotonik', 'optik']],
  ['mimar', ['mimarlık', 'şehir ve bölge', 'kentsel', 'iç mimarlık']],
  ['insaat', ['inşaat', 'harita', 'maden', 'jeoloji', 'jeofizik', 'petrol', 'hidro', 'cevher', 'su bilimleri']],
  ['makine', ['makine', 'otomotiv', 'endüstri mühendisliği', 'imalat', 'metalurji', 'malzeme', 'polimer', 'raylı', 'tekstil mühendisliği', 'ağaç işleri', 'deri', 'ulaştırma', 'işletme mühendisliği', 'endüstriyel tasarım mühendisliği']],
  ['bilimci', ['kimya', 'biyoloji', 'fizik', 'genetik', 'biyotek', 'moleküler', 'biyokimya', 'biyomühendislik', 'nano', 'biyomedikal', 'gıda', 'meteoroloji', 'iklim', 'tıp mühendisliği']],
  ['sef', ['gastronomi', 'mutfak', 'yiyecek', 'otel', 'turizm', 'konaklama', 'seyahat', 'rekreasyon']],
  ['muzisyen', ['müzik', 'çalgı', 'orkestra', 'koro', 'bestecilik', 'caz', 'ses sanatları']],
  ['sahne', ['tiyatro', 'oyunculuk', 'drama', 'sahne', 'dans', 'halk oyunları']],
  ['gazeteci', ['gazetecilik', 'iletişim', 'medya', 'radyo', 'televizyon', 'sinema', 'film', 'halkla ilişkiler', 'reklam', 'basın']],
  ['ressam', ['resim', 'sanat', 'grafik', 'tasarım', 'heykel', 'seramik', 'cam', 'çini', 'hat sanatı', 'tezhip', 'moda', 'animasyon', 'el sanatları', 'fotoğraf', 'kuyumculuk', 'takı', 'aksesuar', 'ayakkabı', 'halı', 'çizgi film', 'basım', 'baskı']],
  ['sporcu', ['spor', 'antrenörlük', 'egzersiz', 'beden eğitimi']],
  ['ciftci', ['ziraat', 'tarım', 'tarla', 'bahçe', 'bitki', 'orman', 'su ürünleri', 'balıkçılık', 'toprak', 'tohum', 'süt teknolojisi', 'kanatlı', 'hayvansal', 'biyosistem', 'yaban hayatı', 'doğa koruma', 'peyzaj']],
  ['is_insani', ['işletme', 'ekonomi', 'iktisat', 'finans', 'muhasebe', 'bankacılık', 'sigorta', 'aktüerya', 'pazarlama', 'lojistik', 'ticaret', 'gümrük', 'girişimcilik', 'insan kaynakları', 'maliye', 'sermaye', 'gayrimenkul', 'liderlik', 'çalışma ekonomisi', 'elektronik ticaret']],
  ['akademisyen', ['psikoloji', 'sosyoloji', 'felsefe', 'tarih', 'edebiyat', 'dil', 'mütercim', 'arkeoloji', 'antropoloji', 'ilahiyat', 'islam', 'coğrafya', 'halkbilimi', 'müzecilik', 'bilgi ve belge', 'siyaset', 'uluslararası', 'kamu yönetimi', 'sosyal hizmet', 'yerel yönetim', 'kültür', 'avrupa birliği', 'politika']],
]

// [2026-10-04] Önce profildeki HEDEF MESLEĞE bakılır (daha belirleyici), bulunamazsa hedef bölüme.
// Karşılaştırma büyük/küçük harf ve ı/i farkından etkilenmez (fold).
const fold = (t) => ` ${String(t || '').toLocaleLowerCase('tr').replace(/ı/g, 'i')} `

// 301 bölümün her biri tek tek eşlendi (kelime eşleştirmesi 'Gastronomi'yi astronot yapıyordu).
const BOLUM_KIYAFET = {
  'acil yardim ve afet yönetimi': 'doktor',
  'adli bilimler': 'dedektif',
  'adli bilişim mühendisliği': 'yazilimci',
  'aile ve tüketici bilimleri': 'ogretmen',
  'aksesuar tasarimi': 'ressam',
  'aktüerya bilimleri': 'analist',
  'animasyon ve oyun tasarimi': 'yazilimci',
  'antrenörlük eğitimi': 'sporcu',
  'antropoloji': 'akademisyen',
  'arkeoloji': 'akademisyen',
  'astronomi ve uzay bilimleri': 'astronot',
  'avrupa birliği ilişkileri': 'is_insani',
  'ayakkabi tasarimi ve üretimi': 'ressam',
  'ağaç işleri endüstri mühendisliği': 'makine',
  'bahçe bitkileri': 'ciftci',
  'balikçilik teknolojisi mühendisliği': 'ciftci',
  'bankacilik ve finans': 'is_insani',
  'bankacilik ve sigortacilik': 'is_insani',
  'basim teknolojileri': 'ressam',
  'basin ve yayin': 'gazeteci',
  'baski sanatlari': 'ressam',
  'beslenme ve diyetetik': 'doktor',
  'bestecilik ve orkestra şefliği': 'muzisyen',
  'bileşik sanatlar': 'ressam',
  'bilgi güvenliği mühendisliği': 'yazilimci',
  'bilgi ve belge yönetimi': 'akademisyen',
  'bilgisayar bilimleri': 'yazilimci',
  'bilgisayar mühendisliği': 'yazilimci',
  'bilgisayar ve öğretim teknolojileri öğretmenliği': 'ogretmen',
  'bilim tarihi': 'akademisyen',
  'bilişim sistemleri mühendisliği': 'yazilimci',
  'bitki koruma': 'ciftci',
  'bitkisel üretim ve teknolojileri': 'ciftci',
  'biyokimya': 'bilimci',
  'biyoloji': 'bilimci',
  'biyoloji öğretmenliği': 'ogretmen',
  'biyomedikal mühendisliği': 'bilimci',
  'biyomühendislik': 'bilimci',
  'biyosistem mühendisliği': 'ciftci',
  'biyoteknoloji': 'bilimci',
  'cam': 'ressam',
  'caz ve popüler müzik': 'muzisyen',
  'cevher hazirlama mühendisliği': 'insaat',
  'coğrafya': 'akademisyen',
  'coğrafya öğretmenliği': 'ogretmen',
  'deniz ulaştirma işletme mühendisliği': 'kaptan',
  'denizcilik işletmeleri yönetimi': 'kaptan',
  'deri mühendisliği': 'makine',
  'dijital medya ve pazarlama': 'gazeteci',
  'dijital oyun tasarimi': 'yazilimci',
  'dil ve edebiyat': 'akademisyen',
  'dil ve konuşma terapisi': 'doktor',
  'dil öğretmenliği': 'ogretmen',
  'diş hekimliği': 'dis',
  'doğa koruma ve biyoçeşitlilik yönetimi': 'ciftci',
  'drama ve oyunculuk': 'sahne',
  'drama yazarliği ve dramaturji': 'sahne',
  'ebelik': 'doktor',
  'eczacilik': 'eczaci',
  'egzersiz ve spor bilimleri': 'sporcu',
  'ekonometri': 'analist',
  'ekonomi': 'is_insani',
  'ekonomi ve finans': 'is_insani',
  'el sanatlari': 'ressam',
  'elektrik ve elektronik mühendisliği': 'elektrik',
  'elektronik ticaret ve yönetimi': 'is_insani',
  'endüstri mühendisliği': 'makine',
  'endüstriyel tasarim': 'ressam',
  'endüstriyel tasarim mühendisliği': 'makine',
  'enerji sistemleri mühendisliği': 'elektrik',
  'enerji yönetimi': 'elektrik',
  'ergoterapi': 'doktor',
  'felsefe': 'akademisyen',
  'felsefe grubu öğretmenliği': 'ogretmen',
  'fen bilgisi öğretmenliği': 'ogretmen',
  'film tasarimi ve yazarliği': 'gazeteci',
  'film tasarimi ve yönetmenliği': 'gazeteci',
  'film yapimi ve yayincilik': 'gazeteci',
  'finans ve bankacilik': 'is_insani',
  'fizik': 'bilimci',
  'fizik mühendisliği': 'bilimci',
  'fizik öğretmenliği': 'ogretmen',
  'fizyoterapi ve rehabilitasyon': 'doktor',
  'fotonik': 'elektrik',
  'fotoğraf ve video': 'ressam',
  'gastronomi ve mutfak sanatlari': 'sef',
  'gayrimenkul geliştirme ve yönetimi': 'is_insani',
  'gazetecilik': 'gazeteci',
  'geleneksel türk sanatlari': 'ressam',
  'gemi inşaati ve gemi makineleri mühendisliği': 'kaptan',
  'gemi makineleri işletme mühendisliği': 'kaptan',
  'gemi ve yat tasarimi': 'kaptan',
  'genetik ve biyomühendislik': 'bilimci',
  'gerontoloji': 'doktor',
  'gida mühendisliği': 'bilimci',
  'girişimcilik': 'is_insani',
  'grafik tasarimi': 'ressam',
  'görsel iletişim tasarimi': 'ressam',
  'görsel sanatlar': 'ressam',
  'görsel sanatlar öğretmenliği': 'ogretmen',
  'gümrük işletme': 'is_insani',
  'güverte': 'kaptan',
  'hali tasarimi': 'ressam',
  'hali, kilim ve geleneksel kumaş desenleri': 'ressam',
  'halkbilimi': 'akademisyen',
  'halkla ilişkiler ve reklamcilik': 'gazeteci',
  'harita mühendisliği': 'insaat',
  'hassas tarim ve tarimsal robotlar': 'ciftci',
  'hat sanati': 'ressam',
  'hava trafik kontrolü': 'pilot',
  'havacilik elektrik ve elektroniği': 'pilot',
  'havacilik ve uzay mühendisliği': 'pilot',
  'havacilik yönetimi': 'pilot',
  'hayvansal üretim ve teknolojileri': 'ciftci',
  'hemşirelik': 'doktor',
  'heykel': 'ressam',
  'hidrojeoloji mühendisliği': 'insaat',
  'hidrolik ve su kaynaklari mühendisliği': 'insaat',
  'hukuk': 'hukuk',
  'iklim bilimi ve meteoroloji mühendisliği': 'bilimci',
  'iktisat': 'is_insani',
  'ilahiyat': 'akademisyen',
  'iletişim bilimleri': 'gazeteci',
  'iletişim tasarimi ve yönetimi': 'gazeteci',
  'ilköğretim matematik öğretmenliği': 'ogretmen',
  'imalat mühendisliği': 'makine',
  'insan kaynaklari yönetimi': 'is_insani',
  'inşaat mühendisliği': 'insaat',
  'islam bilimleri': 'akademisyen',
  'islam iktisadi ve finans': 'is_insani',
  'istatistik': 'analist',
  'iç mimarlik ve çevre tasarimi': 'mimar',
  'iş sağliği ve güvenliği': 'insaat',
  'işletme': 'is_insani',
  'işletme mühendisliği': 'makine',
  'jeofizik mühendisliği': 'insaat',
  'jeoloji mühendisliği': 'insaat',
  'kamu yönetimi': 'is_insani',
  'kanatli hayvan yetiştiriciliği': 'ciftci',
  'karşilaştirmali edebiyat': 'akademisyen',
  'kentsel tasarim ve peyzaj mimarliği': 'mimar',
  'kimya': 'bilimci',
  'kimya mühendisliği': 'bilimci',
  'kimya öğretmenliği': 'ogretmen',
  'kimya-biyoloji mühendisliği': 'bilimci',
  'kontrol ve otomasyon mühendisliği': 'elektrik',
  'kurgu, ses ve görüntü yönetimi': 'gazeteci',
  'kuyumculuk ve mücevher tasarimi': 'ressam',
  'kültür varliklarini koruma ve onarim': 'ressam',
  'kültür ve iletişim bilimleri': 'gazeteci',
  'küresel siyaset ve uluslararasi ilişkiler': 'is_insani',
  'liderlik': 'is_insani',
  'lojistik yönetimi': 'is_insani',
  'maden mühendisliği': 'insaat',
  'makine mühendisliği': 'makine',
  'maliye': 'is_insani',
  'malzeme bilimi ve mühendisliği': 'makine',
  'malzeme bilimi ve nanoteknoloji mühendisliği': 'makine',
  'matematik': 'analist',
  'matematik mühendisliği': 'analist',
  'matematik ve bilgisayar bilimleri': 'analist',
  'matematik öğretmenliği': 'ogretmen',
  'medya ve iletişim': 'gazeteci',
  'mekatronik mühendisliği': 'elektrik',
  'metalurji ve malzeme mühendisliği': 'makine',
  'mimarlik': 'mimar',
  'moda tasarimi': 'ressam',
  'modern dans': 'sahne',
  'moleküler biyoloji ve genetik': 'bilimci',
  'moleküler biyoteknoloji': 'bilimci',
  'muhasebe ve denetim': 'is_insani',
  'muhasebe ve finans yönetimi': 'is_insani',
  'mütercim ve tercümanlik': 'akademisyen',
  'müzecilik': 'akademisyen',
  'müzik': 'muzisyen',
  'müzik ses ve performans': 'muzisyen',
  'müzik teknolojisi': 'muzisyen',
  'müzik teorisi': 'muzisyen',
  'müzik çalgi': 'muzisyen',
  'müzik öğretmenliği': 'ogretmen',
  'müzikoloji': 'muzisyen',
  'nanobilim ve nanoteknoloji': 'bilimci',
  'nanoteknoloji mühendisliği': 'bilimci',
  'nükleer enerji mühendisliği': 'elektrik',
  'odyoloji': 'doktor',
  'okul öncesi öğretmenliği': 'ogretmen',
  'optik ve akustik mühendisliği': 'elektrik',
  'organik tarim işletmeciliği': 'ciftci',
  'orkestra ve koro şefliği': 'muzisyen',
  'orman endüstrisi mühendisliği': 'ciftci',
  'orman mühendisliği': 'ciftci',
  'ortez ve protez': 'doktor',
  'otel yöneticiliği': 'sef',
  'otomotiv mühendisliği': 'makine',
  'oyunculuk': 'sahne',
  'pazarlama': 'is_insani',
  'pazarlama iletişimi': 'gazeteci',
  'perfüzyon': 'doktor',
  'petrol ve doğalgaz mühendisliği': 'insaat',
  'peyzaj mimarliği': 'ciftci',
  'pilotaj': 'pilot',
  'plastik sanatlar ve resim': 'ressam',
  'polimer malzeme mühendisliği': 'makine',
  'politika ve ekonomi': 'is_insani',
  'psikoloji': 'akademisyen',
  'psikolojik danişmanlik ve rehberlik öğretmenliği': 'ogretmen',
  'radyo, televizyon ve sinema': 'gazeteci',
  'rayli sistemler mühendisliği': 'makine',
  'rehberlik ve psikolojik danişmanlik': 'ogretmen',
  'reklamcilik': 'gazeteci',
  'rekreasyon yönetimi': 'sporcu',
  'resim': 'ressam',
  'resim öğretmenliği': 'ogretmen',
  'sahne dekoru ve kostümü': 'sahne',
  'sahne sanatlari': 'sahne',
  'sahne tasarimi': 'sahne',
  'sahne ve gösteri sanatlari yönetimi': 'sahne',
  'sanat tarihi': 'akademisyen',
  'sanat ve kültür yönetimi': 'ressam',
  'saç ve güzellik uygulamalari': 'kuafor',
  'sağlik yönetimi': 'is_insani',
  'seramik ve cam': 'ressam',
  'sermaye piyasasi': 'is_insani',
  'ses sanatlari tasarimi': 'muzisyen',
  'seyahat işletmeciliği ve turizm rehberliği': 'rehber',
  'siber güvenlik mühendisliği': 'yazilimci',
  'sigortacilik ve aktüerya bilimleri': 'analist',
  'sigortacilik ve risk yönetimi': 'is_insani',
  'sinema ve dijital medya': 'gazeteci',
  'sinif öğretmenliği': 'ogretmen',
  'sivil hava ulaştirma işletmeciliği': 'pilot',
  'siyaset bilimi ve kamu yönetimi': 'is_insani',
  'siyaset bilimi ve uluslararasi ilişkiler': 'is_insani',
  'sosyal bilgiler öğretmenliği': 'ogretmen',
  'sosyal hizmet': 'ogretmen',
  'sosyoloji': 'akademisyen',
  'spor yöneticiliği': 'sporcu',
  'spor öğretmenliği': 'ogretmen',
  'su bilimleri ve mühendisliği': 'insaat',
  'su ürünleri mühendisliği': 'ciftci',
  'süt teknolojisi': 'ciftci',
  'taki tasarimi ve imalati': 'ressam',
  'tarih': 'akademisyen',
  'tarih öğretmenliği': 'ogretmen',
  'tarim ekonomisi': 'ciftci',
  'tarim makineleri ve teknolojileri mühendisliği': 'makine',
  'tarim ticareti ve işletmeciliği': 'ciftci',
  'tarimsal biyoteknoloji': 'bilimci',
  'tarimsal genetik mühendisliği': 'bilimci',
  'tarimsal yapilar ve sulama': 'ciftci',
  'tarla bitkileri': 'ciftci',
  'teknoloji girişimciliği': 'yazilimci',
  'tekstil mühendisliği': 'makine',
  'tekstil tasarimi': 'ressam',
  'tekstil ve moda tasarimi': 'ressam',
  'televizyon haberciliği ve programciliği': 'gazeteci',
  'tezhip-minyatür ve ebru': 'ressam',
  'tip': 'doktor',
  'tip mühendisliği': 'bilimci',
  'tiyatro': 'sahne',
  'tiyatro eleştirmenliği ve dramaturji': 'sahne',
  'tohum bilimi ve teknolojisi': 'ciftci',
  'toprak bilimi ve bitki besleme': 'ciftci',
  'turizm işletmeciliği': 'rehber',
  'turizm rehberliği': 'rehber',
  'turizm ve konaklama işletmeciliği': 'sef',
  'türk halk oyunlari': 'sahne',
  'türk halkbilimi': 'akademisyen',
  'ulaştirma ve trafik mühendisliği': 'insaat',
  'uluslararasi ekonomik ilişkiler': 'is_insani',
  'uluslararasi finans': 'is_insani',
  'uluslararasi girişimcilik': 'is_insani',
  'uluslararasi hukuk': 'hukuk',
  'uluslararasi ilişkiler': 'is_insani',
  'uluslararasi işletmecilik ve ticaret': 'is_insani',
  'uluslararasi ticaret ve lojistik': 'is_insani',
  'uzay bilimleri ve teknolojileri': 'astronot',
  'uzay mühendisliği': 'astronot',
  'uçak bakim ve onarim': 'pilot',
  'uçak mühendisliği': 'pilot',
  'veri bilimi ve analitiği': 'analist',
  'veterinerlik': 'veteriner',
  'yaban hayati ekolojisi ve yönetimi': 'ciftci',
  'yapay zeka mühendisliği': 'yazilimci',
  'yapay zeka ve makine öğrenmesi': 'yazilimci',
  'yapay zeka ve veri mühendisliği': 'yazilimci',
  'yazilim mühendisliği': 'yazilimci',
  'yeni medya ve gazetecilik': 'gazeteci',
  'yeni medya ve iletişim': 'gazeteci',
  'yerel yönetimler': 'is_insani',
  'yiyecek ve içecek işletmeciliği': 'sef',
  'yönetim bilişim sistemleri': 'yazilimci',
  'zootekni': 'ciftci',
  'çalgi teknolojileri': 'muzisyen',
  'çalişma ekonomisi ve endüstri ilişkileri': 'is_insani',
  'çevre mühendisliği': 'insaat',
  'çini tasarimi ve onarimi': 'ressam',
  'çizgi film ve animasyon': 'ressam',
  'çocuk gelişimi': 'ogretmen',
  'özel eğitim öğretmenliği': 'ogretmen',
  'şehir ve bölge planlama': 'mimar',
}

// Meslek kuralları SIRAYLA denenir; özel olan önce, genel olan sonra gelir.
const MESLEK_KURALLARI = [
  // 1) Özel durumlar — genel kurallardan önce yakalanmalı
  ['muzisyen', ['müzik öğretmen', 'müzik eğitmen', 'konservatuvar', 'koro şef', 'müzik şef', 'elektronik müzik']],
  ['sporcu', ['beden eğitimi']],
  ['sahne', ['oyuncu', ' aktör', 'aktris', 'dans öğretmen', 'dans eğitmen', 'tiyatro eğitmen', 'drama öğretmen', 'sahne uçuş', 'mekan programcı', 'mekân programcı']],
  ['ressam', ['görsel sanatlar öğretmen', 'sanat öğretmen', 'güzel sanatlar eğitmen', 'fotoğrafçılık öğretmen', 'model yapımcı']],
  ['ciftci', ['su ürünleri', 'tarım, ormancılık']],
  ['veteriner', ['equine', 'hayvanat bahçesi']],
  ['kaptan', ['gemi pilot']],
  ['insaat', ['sondaj', 'iş sağlığı']],
  ['bilimci', ['gıda analist']],
  ['makine', ['tasarım mühendis', 'motor tasarım', 'araç döşeme', 'tipetter']],
  ['doktor', ['kilo kaybı', 'kilo yönetimi', 'yaşlı ev', 'sitoteknolo', 'sağlığ']],
  ['yazilimci', ['bilgi işlem', 'gömülü sistem', 'veri deposu', 'teknoloji şef', 'kurumsal mimar', 'girişim mimar']],
  ['mimar', ['iç peyzaj']],
  ['sef', ['ev hizmetçi']],
  ['is_insani', ['iş değeri', 'özel ilgi grup', 'gayrimenkul']],
  // 2) Öğretmenler (meslek öğretmenleri alanının kıyafetini alır)
  ['ogretmen', ['öğretmen', 'öğretim tasarım', 'okuryazarlık', 'rehberlik danışman', 'bebek bakıcı'], ['meslek öğretmen', 'eczacılık öğretmen']],
  // 3) Genel kurallar
  ['ressam', ['sanat terapist']], ['muzisyen', ['müzik terapist']], ['sahne', ['dans terap']], ['sporcu', ['spor terapist']],
  ['insaat', ['iş sağlığı']],
  ['dis', ['diş hekim', 'diş hijyen', 'diş teknisyen', 'diş protez', 'ağız ve diş']],
  ['eczaci', ['eczacı', 'ilaç']],
  ['veteriner', ['veteriner', 'hayvan terapist', 'hayvan tımar', 'evcil hayvan', 'hayvan eğitmen', 'hayvan fizyoterap', 'hayvan osteopat']],
  ['kuafor', ['kuaför', 'berber', 'manikür', 'güzellik', 'solaryum', 'makyaj', 'cilt bakım', 'estetisyen']],
  ['yazilimci', ['yazılım', 'veritabanı geliştirici', 'programcı', 'siber', 'veritabanı', 'yapay zeka', 'bilgisayar', ' oyun', 'dijital oyun', ' ict ', ' bt ', 'bilgi güvenliği', 'etik hacker', ' web', 'uygulama mühendis', 'entegrasyon mühendis', 'teknoloji direktör', 'klinik kodlayıcı', ' iot', 'nesnelerin', 'sistem analist', 'e-öğrenme']],
  ['analist', ['analist', 'istatistik', 'veri bilim', 'veri mühendis', 'aktüer', 'ekonomist', 'ekonometri', 'matematik', 'biyoinformatik', 'hesaplama', 'fiyatlandırma', 'trader', 'hisse', 'döviz', 'yatırım', 'kıymet']],
  ['hukuk', ['avukat', 'hakim', 'savcı', 'hukuk', 'noter', 'arabulucu', 'ombudsman']],
  ['dedektif', ['dedektif', 'kriminolog', 'suç ', 'adli', 'poligraf', 'grafolog', 'polis', 'ıslah', 'denetimli serbestlik']],
  ['astronot', ['astronot', 'astronom', 'kozmolog', 'uzay', 'uydu']],
  ['pilot', ['pilot', 'hava trafik', 'kabin', 'havacılık', 'havaalanı', 'havalimanı', 'uçak', 'uçuş', 'aviyonik', 'apron', 'hostes']],
  ['doktor', ['hekim', 'doktor', 'hemşire', 'cerrah', ' ebe', 'doğum', 'fizyoterap', 'diyetisyen', 'diyetetik', 'odyolog', 'ergoterap', 'meslek terapist', 'paramedik', 'sağlık', 'ameliyat', 'anestezi', 'perfüzyon', 'radyograf', 'optometrist', 'optikçi', 'ortopedi', 'osteopat', 'kiropraktör', 'chiropractor', 'protez', 'ortez', 'prosthetist', 'solunum', 'konuşma ve dil', 'terapist', 'klinik', 'tıbbi', 'tıp ', 'bakım personel', 'bakım işçi', 'bakım çalışan', 'evde bakım', 'bakım yardımcı', 'ilk yardım', 'shiatsu', 'rehabilitasyon', 'kineziyolog', 'fizyolog', 'bitkisel terapist', 'pratisyen']],
  ['sef', ['şef', 'aşçı', 'pasta', 'mutfak', 'garson', 'restoran', 'gıda hizmet', 'kasap', 'kesimci', 'helal', 'otel', 'pansiyon', 'konaklama', 'misafirperverlik', 'konsiyerj', 'concierge', 'oda ve kahvaltı', 'kat hizmet', 'barista', 'servis']],
  ['akademisyen', ['öğretim görevlisi', 'öğretim üyesi', 'araştırmacı', 'araştırma asistan', 'psikolog', 'sosyolog', 'tarihçi', 'filozof', 'dilbilimci', 'dil mühendis', 'çevirmen', 'tercüman', 'yerelleştirici', 'arkeolog', 'antropolog', 'coğrafyacı', 'soybilim', 'kütüphaneci', 'arşiv', 'müze', 'sergi', 'eleştirmen', 'edebiyat', 'siyaset bilim', 'davranış bilim', 'iletişim bilim', 'medya bilim', 'halkbilim', 'teolog', ' din ', ' dini', 'koreolog']],
  ['bilimci', ['kimya', 'biyolog', 'biyoloji', 'fizik', 'genetik', 'mikrobiyolog', 'biyokimya', 'laboratuvar', 'toksikolog', 'botanik teknisyen', 'botanikçi', 'zoolog', 'paleontolog', 'meteorolog', 'meteoroloji', 'klimatolog', 'hava tahmin', 'çevre bilim', 'çevre uzman', 'koruma bilim', 'duyu', 'duyusal', 'gıda', 'biyomühendis', 'biyomedikal', 'nanomühendis', 'bilim adam', 'bilim insan', 'bilimci', 'bilgin', 'klinik deneme']],
  ['kaptan', ['kaptan', 'denizci', 'gemi', 'güverte', 'deniz ', 'liman', 'su trafik', 'filo komutan']],
  ['mimar', ['mimar', 'iç mekân', 'iç mekan', 'iç planlayıcı', 'şehir planla', 'arazi kullanım', 'peyzaj tasarım', 'kentsel', 'akıllı şehir']],
  ['insaat', ['inşaat', 'harita', 'kadastro', 'jeolog', 'jeoloji', 'jeofizik', 'jeoteknik', 'geoteknik', 'maden', 'petrol', 'sondaj', 'hidrolog', 'hidrojeolog', 'yeraltı', 'su mühendis', 'su sistemleri', 'su koruma', 'çevre mühendis', 'sismolog', 'mineral', 'ray döşeme', 'ray tabakası', 'tahlil', 'uzaktan algılama', 'coğrafi bilgi', 'sulama', 'mayın', 'kurtarma', 'ulaşım planla', 'trafik']],
  ['elektrik', ['elektrik', 'elektronik', 'enerji', 'nükleer', 'otomasyon', 'robot', 'fotonik', 'optik mühendis', 'santral', 'mikrosistem', 'mikroelektronik', 'elektrolitik', 'güvenlik alarm', ' pil ', 'akıllı ev']],
  ['rehber', ['rehber', 'tur organizatör', 'turist', 'seyahat', 'turizm', 'hayatta kalma', 'kamp']],
  ['muzisyen', ['müzik', 'müzisyen', 'besteci', 'şarkıcı', 'koro', 'orkestra', 'çalgı', 'enstrüman', ' ses ', 'kayıt stüdyo', 'podcast', 'lirik', 'söz yazarı', 'aranjör', 'dj']],
  ['sahne', ['oyuncu', ' aktör', 'aktris', 'dansçı', 'dans ', 'koreograf', 'komedyen', 'sahne', 'tiyatro', 'kukla', 'sirk', 'dramaturg', 'performans', 'maske yapım', 'kostüm', 'giydirici', 'varyete', 'dövüş', 'repetitör', 'etkinlik']],
  ['sporcu', ['spor', 'antrenör', 'atlet', 'fitness', 'futbol', 'rekreasyon', 'beden eğitimi', 'hakem', 'kondisyon', 'yüzme', 'basketbol', 'voleybol']],
  ['gazeteci', ['gazeteci', 'muhabir', 'spiker', 'editör', 'sunucu', 'yayın', 'haber', 'medya', 'reklam', 'halkla ilişkiler', 'iletişim', 'yönetmen', 'yapımcı', 'senaryo', 'kamera', 'görüntü', 'film', 'video', 'sinema', 'post-prodüksiyon', 'metin yazar', 'yazar', 'doğruluk kontrol', 'gerçek denetleyici', 'kopya düzenleyici', 'sesli betimleme', 'görsel-işitsel', 'konuşma koçu']],
  ['ressam', ['ressam', 'tasarımcı', 'tasarım', 'grafik', 'illüstratör', 'fotoğraf', 'sanatçı', 'sanat', 'animatör', 'animasyon', 'heykel', 'seramik', ' cam ', 'çini', 'hattat', 'minyatür', 'tezhip', 'ebru', 'kuyumcu', 'mücevher', 'takı', 'filigran', 'nakış', 'örgü', 'halı', 'dokumacı', 'terzi', 'dressmaker', 'moda', 'model', 'oymacı', 'restoratör', 'konservatör', 'konservatuvar', 'storyboard', '3d ', 'tabela', 'işaret yapıcı', 'litograf', 'baskı', 'ofset', 'prepress', 'dijital yazıcı', 'vitrin', 'görsel mal', 'dekoratif', 'el sanat', 'hasır', 'saat ', 'silah ustası']],
  ['ciftci', ['ziraat', 'tarım', 'orman', 'forester', 'çiftçi', 'bahçıvan', 'bahçe', 'bitki', 'çiçek', 'tohum', 'toprak', 'hayvancılık', 'yetiştirici', 'kümes', 'civciv', 'sığır', 'süt', ' yem', 'su ürünleri', 'balık', 'arıcı', 'şerbetçiotu', 'meyve', 'sebze', 'ekin', 'tarla', 'haşere', 'doğa koruma', 'yaban', 'hayvan yakalama', 'yakalayıcı', 'değirmen', 'miller', 'damıtım', 'yağlı tohum', 'hayvan yemi', 'kırsal', 'hayvanat bahçesi', 'köpek', 'veteriner']],
  ['ogretmen', ['öğretmen', 'eğitmen', 'eğitimci', 'headteacher', 'okul müdürü', 'öğrenme', 'mentor', 'eğitim', ' koç', 'sosyal hizmet', 'sosyal pedagog', 'pedagoji', 'çocuk', 'refah', 'özel eğitim', 'okul', 'gönüllü', 'topluluk', 'toplum', 'kriz', 'gerontoloji']],
  ['makine', ['makine', 'mekanik', 'otomotiv', 'motor', 'mekatronik', 'endüstri', 'üretim mühendis', 'imalat', 'metalurji', 'metal', 'malzeme', 'montaj', 'derleyici', 'birleştirici', 'teknik ressam', 'taslak', 'draftör', 'tasarım mühendis', 'ürün geliştirme', 'süreç mühendis', 'kauçuk', 'plastik', 'polimer', 'tekstil', 'deri', 'ayakkabı', 'giyim', 'tren', 'demiryolu', 'rolling', 'kurulum', 'araştırma mühendis', 'inovasyon mühendis', 'güç aktarma', 'powertrain', 'sıvı yakıt', 'nakliye mühendis', 'metrolog', 'metroloji', 'ahşap', 'dokuma', 'kalıp', 'apre', 'renkçi', 'tamirci', 'teknisyen', 'tekniker', 'operatör', 'işletmeci', 'amiri', 'süpervizör', 'usta', 'işçi', 'mühendis']],
  ['is_insani', ['müdür', 'yönetici', 'muhasebe', 'bankacı', 'banka', 'pazarlama', 'finans', 'girişim', 'denetçi', 'denetim', 'danışman', 'satış', 'satıcı', 'satın alma', 'ithalat', 'ihracat', 'ticaret', 'tüccar', 'lojistik', 'tedarik', 'insan kaynakları', 'yetenek', 'sigorta', 'risk', 'vergi', 'mali ', 'gayrimenkul', 'emlak', 'mülk', 'değerleme', 'kiralama', 'iş geliştir', 'marka', 'politika', 'belediye', 'vali', 'kamu', 'siyasi', 'konsolos', 'dışişleri', 'büyükelçi', 'diplomat', 'uluslararası', 'merkez bankası', 'sevkiyat', 'sevkıyat', 'koordinatör', 'sorumlu', 'görevli', 'memur', 'planlayıcı', 'uzman', 'direktör', 'başkan', 'müfettiş', 'kâtip', 'katip', 'asistan', 'lider', 'kapitalist']],
].map(([k, l, haric = []]) => [k, l.map((x) => fold(x).slice(1, -1)), haric.map((x) => fold(x).slice(1, -1))])

function meslektenKiyafet(meslek) {
  if (!meslek) return null
  const t = fold(meslek)
  for (const [kiyafet, kelimeler, haric] of MESLEK_KURALLARI) {
    if (haric.some((k) => t.includes(k))) continue
    if (kelimeler.some((k) => t.includes(k))) return kiyafet
  }
  return null
}

function bolumdenKiyafet(bolum) {
  if (!bolum) return null
  const anahtar = fold(bolum).trim()
  if (BOLUM_KIYAFET[anahtar]) return BOLUM_KIYAFET[anahtar]
  // listede olmayan (yeni eklenmiş) bölüm: kelime kuralları
  const t = fold(bolum)
  for (const [kiyafet, kelimeler] of KIYAFET_KURALLARI) {
    if (kelimeler.some((k) => t.includes(fold(k).trim()))) return kiyafet
  }
  return null
}

export function kiyafetBul(bolumAdi, meslekAdi) {
  return meslektenKiyafet(meslekAdi) || bolumdenKiyafet(bolumAdi) || 'gunluk'
}

// ----------------------------------------------------------------------------- Mesajlar
const KIYAFET_MESAJLARI = {
  hukuk: ['Cübbem nasıl? ⚖️ Hukukçular çok okur — bugün bir sayfa fazla oku!', 'Bir avukatın en güçlü silahı iyi kurulmuş bir argümandır.'],
  dedektif: ['İpucu: en iyi dedektifler ayrıntıyı kaçırmaz. 🔎', 'Merak et, sor, araştır — adli bilimler böyle başlar.'],
  veteriner: ['Patili dostlar için hazırım! 🐾', 'Biyoloji çalışmak, her canlıya iyi bakmanın ilk adımı.'],
  dis: ['Gülümse! 😁 Diş hekimleri sabırlı ve dikkatlidir.', 'İnce el becerisi pratikle gelişir — bugün bir şey çiz!'],
  eczaci: ['Kimya bilgisi şifanın formülüdür. 💊', 'Her gün biraz kimya, uzun vadede büyük fark!'],
  doktor: ['Beyaz önlük yakıştı mı? 🩺', 'Biyoloji ve kimyaya her gün 20 dakika ayır — gerisi gelir.', 'İyi bir sağlıkçı önce iyi bir dinleyicidir.'],
  yazilimci: ['Kod yazmak bir dil öğrenmek gibi: her gün biraz! 💻', 'Bug değil, öğrenme fırsatı. 🐛➡️🦋'],
  kuafor: ['Makaslar hazır! ✂️ Güzellik sabır ve dikkat ister.', 'İnsanlara iyi hissettirmek de bir meslek sanatı. 💇'],
  rehber: ['Yola çıkıyoruz! 🗺️ İyi bir rehber önce iyi bir anlatıcıdır.', 'Bir yabancı dile her gün 15 dakika — rehberliğin anahtarı!'],
  analist: ['Veriler konuşur, iyi analist dinler. 📊', 'İstatistik dersine bugün 20 dakika ayıralım mı?', 'Her grafik bir hikâye anlatır — sen hangisini anlatacaksın?'],
  elektrik: ['Enerjimiz tam! ⚡', 'Fizik formülleri devrelerin dilidir — bir tanesini bugün tekrar et.'],
  mimar: ['Her büyük yapı küçük bir eskizle başlar. ✏️', 'Bugün çevrendeki bir binayı inceleyip çizmeye ne dersin?'],
  insaat: ['Baretim hazır! 👷 Sağlam temel, sağlam gelecek.', 'Matematik bir yapının iskeleti gibidir.'],
  makine: ['Anahtarım elimde! 🔧 Bir şey nasıl çalışır, merak et.', 'Mühendislik problemleri adım adım çözülür — senin gibi!'],
  bilimci: ['Deney zamanı! 🧪', 'Bilim insanları cevaptan çok soruyu sever.', 'Bugün bir “neden?” sorusunun cevabını araştır.'],
  ogretmen: ['Öğretmek, iki kez öğrenmektir. 📚', 'Bir konuyu arkadaşına anlatmayı dene — en iyi tekrar budur.'],
  sef: ['Şef şapkası takıldı! 👨‍🍳 Lezzet sabır ister.', 'Her tarif bir deney, her deney bir öğrenme.'],
  muzisyen: ['Ritim tutuyorum 🎵 Düzenli pratik, en güzel melodi.', 'Her gün 15 dakika enstrüman, bir yılda büyük fark!'],
  sahne: ['Sahne senin! 🎭', 'Topluluk önünde konuşmak bir kas gibi, çalıştıkça güçlenir.'],
  gazeteci: ['Mikrofon sende! 🎤 Bugün bir haberi iki kaynaktan oku.', 'İyi gazeteci önce iyi soru sorar.'],
  ressam: ['Paletim hazır! 🎨 Bugün 10 dakika eskiz?', 'Yaratıcılık bir alışkanlıktır, her gün biraz besle.'],
  sporcu: ['Isınma hareketleri başlasın! 🏃', 'Disiplin, yeteneği yener — hem sporda hem derste.'],
  ciftci: ['Filizler sabırla büyür, sen de öyle. 🌾', 'Doğayı anlamak için önce gözlem yap.'],
  is_insani: ['Kravatımı taktım! 💼 Bugünün hedefi ne?', 'Küçük yatırımlar büyür — zamanına da yatırım yap.'],
  akademisyen: ['Kitaplar en sadık dostlardır. 📖', 'Bugün merak ettiğin bir konuda tek bir makale oku.'],
  pilot: ['Kalkışa hazırız! ✈️ Hedefe odaklan.', 'Pilotlar kontrol listesi kullanır — sen de günün listesini yap.'],
  kaptan: ['Rota belirlendi! ⚓', 'Fırtınalı denizler iyi kaptan yetiştirir.'],
  astronot: ['Hedef: yıldızlar! 🚀', 'Uzaya giden yol fizik ve matematikle döşenir.'],
  gunluk: ['Bir hedef bölüm seçersen ona göre giyinirim! 👕', 'Koçluk sayfasından bir hedef seçmeye ne dersin?'],
}
const GENEL_MESAJLAR = [
  'Doğru cevap yok, samimi cevap var. 🌱',
  'Büyük kararlar küçük adımlarla verilir.',
  'Yavaş ilerlemek de ilerlemektir. 🐢',
  'Kendini tanımak en değerli yatırımdır.',
  'Merak etmek keşfetmenin ilk adımı!',
  'Bugün kendin için küçük bir şey yap.',
  'Hata yapmak öğrenmenin bir parçası.',
  'Sen düşündüğünden daha güçlüsün! 💪',
  'Mola vermek de çalışmanın bir parçası. ☕',
  'Her uzman bir zamanlar acemiydi.',
]

function sayfaMesaji(yol, ozet, hedef) {
  const biten = ozet?.tamamlanan_katman_sayisi ?? 0
  const toplam = ozet?.toplam_ana_katman_sayisi ?? 4
  if (yol === '/katmanlar') {
    if (biten === 0) return 'İlk katmanla başlayalım: Değerler! 🌱'
    if (biten < toplam) return `${biten}/${toplam} katman tamam, harika gidiyorsun! Sıradaki seni bekliyor.`
    return 'Tüm katmanlar bitti! 🎉 Alan sorularını da tamamlarsan sonuçların hazır.'
  }
  if (yol.startsWith('/sonuc')) return 'Sonuçların burada! Merak ettiğin bölümü Keşfet\'te de inceleyebilirsin. 🌟'
  if (yol === '/kesfet') return 'Bir bölüme tıkla, örnek mesleklerine bak. 🔍'
  if (yol === '/koclugu') return hedef ? `${hedef} hedefin için bugün yol haritandan bir adımı işaretle!` : 'Henüz hedefin yok. Önerilen bölümlerden birini seçmeye ne dersin?'
  if (yol === '/profil') return 'Profilini doldurursan seni daha iyi tanırım. 😊'
  if (biten === 0) return 'Hazırsan Yol Haritam\'dan ilk katmana başlayalım!'
  return null
}

function baslikDuzelt(ad) {
  return String(ad || '').toLocaleLowerCase('tr').split(' ').map((k) => (['ve', 'ile'].includes(k) ? k : k.charAt(0).toLocaleUpperCase('tr') + k.slice(1))).join(' ')
}

// ----------------------------------------------------------------------------- Çizim yardımcıları
const TEN = '#F2C9A0'
const SAC = '#4A2E1F'

function Kiyafet({ tip }) {
  // Gövde: x 38–82, y 80–122 · eller: sol (31,112) sağ (89,112)
  const govde = (renk, ek = null) => (
    <>
      <path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill={renk} />
      {ek}
    </>
  )
  const onluk = (alt = '#5B8DB8') => (
    <>
      <path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill="#FFFFFF" stroke="#D8DEE6" />
      <path d="M52 82 L60 100 L68 82" fill={alt} />
      <path d="M52 82 L58 104 M68 82 L62 104" stroke="#D8DEE6" strokeWidth="1.5" fill="none" />
      <rect x="66" y="104" width="9" height="7" rx="1.5" fill="#EEF2F6" stroke="#D8DEE6" />
    </>
  )
  switch (tip) {
    case 'hukuk':
      return <>{govde('#1F1F24')}<path d="M52 82 L60 98 L68 82 Z" fill="#FFFFFF" /><path d="M55 83 L60 92 L65 83" fill="#B33A3A" /><path d="M36 122 L33 134 L87 134 L84 122" fill="#1F1F24" /></>
    case 'dedektif':
      return <>{govde('#9C7A54')}<path d="M52 82 L60 100 L68 82" fill="#E8D9C0" /><line x1="60" y1="100" x2="60" y2="124" stroke="#6E5236" strokeWidth="1.5" /><circle cx="64" cy="108" r="1.6" fill="#6E5236" /><circle cx="64" cy="116" r="1.6" fill="#6E5236" /><rect x="38" y="112" width="44" height="4" fill="#6E5236" /></>
    case 'doktor': case 'dis': case 'eczaci':
      return <>{onluk()}<path d="M50 84 Q47 104 56 108 M70 84 Q73 104 64 108" stroke="#6B7280" strokeWidth="2" fill="none" /><circle cx="60" cy="109" r="3.2" fill="#9CA3AF" stroke="#6B7280" /></>
    case 'veteriner':
      return <>{onluk('#6BAA75')}<g transform="translate(70 106)" fill="#8B5E3C"><circle cx="0" cy="2" r="2.2" /><circle cx="-2.5" cy="-1.5" r="1" /><circle cx="0" cy="-2.5" r="1" /><circle cx="2.5" cy="-1.5" r="1" /></g></>
    case 'bilimci':
      return <>{onluk('#8EC5FC')}<rect x="44" y="104" width="7" height="2" rx="1" fill="#E76F51" /><rect x="44" y="108" width="7" height="2" rx="1" fill="#2A9D8F" /></>
    case 'kuafor':
      return <>{govde('#F4ACB7')}<path d="M44 92 L76 92 L79 124 Q60 128 41 124 Z" fill="#2B2B2B" /><path d="M50 92 Q50 84 54 82 M70 92 Q70 84 66 82" stroke="#2B2B2B" strokeWidth="2.5" fill="none" /><rect x="52" y="102" width="16" height="9" rx="1.5" fill="#3D3D3D" /><rect x="55" y="99" width="2" height="8" fill="#C0C0C0" /><rect x="59" y="98" width="2" height="9" fill="#E76F51" /><rect x="63" y="99" width="2" height="8" fill="#C0C0C0" /></>
    case 'rehber':
      return <>{govde('#F1FAEE')}<path d="M41 86 L54 83 L55 124 L39 122 Z M79 86 L66 83 L65 124 L81 122 Z" fill="#B08968" /><rect x="42" y="100" width="9" height="7" rx="1.2" fill="#9C7356" /><rect x="69" y="100" width="9" height="7" rx="1.2" fill="#9C7356" /><rect x="42" y="112" width="9" height="7" rx="1.2" fill="#9C7356" /><rect x="69" y="112" width="9" height="7" rx="1.2" fill="#9C7356" /><circle cx="60" cy="94" r="2" fill="#E76F51" /></>
    case 'analist':
      return <>{govde('#2A9D8F')}<path d="M52 82 L56 90 L60 84 L64 90 L68 82" fill="#E9F5F3" stroke="#1F7A6F" strokeWidth="1" /><line x1="60" y1="86" x2="60" y2="124" stroke="#1F7A6F" strokeWidth="1.2" /><rect x="64" y="98" width="9" height="8" rx="1.5" fill="#23867B" /><rect x="66" y="94" width="1.6" height="8" fill="#FFD23F" /><rect x="69" y="95" width="1.6" height="7" fill="#E63946" /></>
    case 'yazilimci':
      return <>{govde('#3A3F58')}<path d="M48 82 Q60 92 72 82" stroke="#2A2E42" strokeWidth="4" fill="none" /><line x1="56" y1="88" x2="55" y2="100" stroke="#DADDE8" strokeWidth="1.5" /><line x1="64" y1="88" x2="65" y2="100" stroke="#DADDE8" strokeWidth="1.5" /><path d="M46 110 L74 110 L72 120 L48 120 Z" fill="#2A2E42" /><text x="60" y="118" fontSize="7" textAnchor="middle" fill="#7EE787" fontFamily="monospace">{'</>'}</text></>
    case 'elektrik':
      return <>{govde('#2F5D8A')}<path d="M62 92 L56 104 L61 104 L57 114 L66 100 L61 100 L64 92 Z" fill="#FFD23F" /><rect x="38" y="116" width="44" height="3" fill="#FFD23F" /></>
    case 'makine':
      return <>{govde('#2F5D8A')}<rect x="47" y="80" width="5" height="24" fill="#24496D" /><rect x="68" y="80" width="5" height="24" fill="#24496D" /><rect x="47" y="100" width="26" height="22" rx="3" fill="#24496D" /><rect x="54" y="104" width="12" height="7" rx="1.5" fill="#1C3A57" /></>
    case 'insaat':
      return <>{govde('#9CA3AF')}<path d="M42 86 L54 84 L56 124 L40 122 Z M78 86 L66 84 L64 124 L80 122 Z" fill="#F28C28" /><rect x="40" y="104" width="16" height="3" fill="#F5F5F5" /><rect x="64" y="104" width="16" height="3" fill="#F5F5F5" /></>
    case 'mimar':
      return <>{govde('#2B2B2B')}<rect x="52" y="80" width="16" height="7" rx="3.5" fill="#1C1C1C" /></>
    case 'ogretmen':
      return <>{govde('#C97B63')}<path d="M54 82 L60 96 L66 82" fill="#F6EFE6" /><line x1="60" y1="96" x2="60" y2="124" stroke="#A35F49" strokeWidth="1.5" />{[102, 110, 118].map((y) => <circle key={y} cx="63" cy={y} r="1.4" fill="#F6EFE6" />)}</>
    case 'sef':
      return <>{govde('#FFFFFF', <><path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill="none" stroke="#E5E7EB" />{[[54, 96], [54, 106], [54, 116], [66, 96], [66, 106], [66, 116]].map(([x, y]) => <circle key={`${x}${y}`} cx={x} cy={y} r="1.6" fill="#9CA3AF" />)}<path d="M52 82 Q60 88 68 82" stroke="#E63946" strokeWidth="3" fill="none" /></>)}</>
    case 'muzisyen':
      return <>{govde('#6C4AB6')}<g transform="translate(60 104)" fill="#F5F0FF"><circle cx="-3" cy="5" r="3" /><rect x="-0.5" y="-7" width="2" height="12" /><path d="M1.5 -7 Q7 -5 6 0" stroke="#F5F0FF" strokeWidth="2" fill="none" /></g></>
    case 'sahne':
      return <>{govde('#9B2335')}<path d="M54 84 L60 88 L54 92 Z M66 84 L60 88 L66 92 Z" fill="#111" /><circle cx="60" cy="88" r="1.6" fill="#111" /></>
    case 'gazeteci':
      return <>{govde('#F1F1F1', <path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill="none" stroke="#D1D5DB" />)}<rect x="64" y="96" width="12" height="9" rx="1.5" fill="#3B82F6" /><text x="70" y="102.5" fontSize="4.5" textAnchor="middle" fill="#fff" fontWeight="700">BASIN</text><line x1="70" y1="86" x2="70" y2="96" stroke="#3B82F6" strokeWidth="1" /></>
    case 'ressam':
      return <>{govde('#E9C46A')}{[['#E63946', 50, 100], ['#2A9D8F', 66, 108], ['#3A86FF', 56, 116], ['#8338EC', 70, 96]].map(([c, x, y]) => <circle key={c} cx={x} cy={y} r="2.4" fill={c} />)}</>
    case 'sporcu':
      return <>{govde('#E63946')}<line x1="42" y1="88" x2="40" y2="122" stroke="#fff" strokeWidth="2" /><line x1="78" y1="88" x2="80" y2="122" stroke="#fff" strokeWidth="2" /><path d="M52 82 Q60 96 68 82" stroke="#E5E7EB" strokeWidth="1.3" fill="none" /><circle cx="60" cy="97" r="3" fill="#C0C0C0" stroke="#888" /></>
    case 'ciftci':
      return <>{govde('#E9EDC9')}<rect x="45" y="94" width="30" height="30" rx="3" fill="#6B8F71" /><rect x="47" y="80" width="5" height="16" fill="#6B8F71" /><rect x="68" y="80" width="5" height="16" fill="#6B8F71" /><circle cx="49.5" cy="96" r="1.6" fill="#E9C46A" /><circle cx="70.5" cy="96" r="1.6" fill="#E9C46A" /></>
    case 'is_insani':
      return <>{govde('#2C3E50')}<path d="M52 82 L60 102 L68 82 Z" fill="#FFFFFF" /><path d="M58 85 L62 85 L63 100 L60 104 L57 100 Z" fill="#C0392B" /><path d="M52 82 L58 100 M68 82 L62 100" stroke="#1B2836" strokeWidth="1.5" /></>
    case 'akademisyen':
      return <>{govde('#7D5A50')}<path d="M52 82 L60 98 L68 82" fill="#F3E9DC" /><path d="M44 84 Q60 90 76 84 L74 90 Q60 96 46 90 Z" fill="#B5838D" /><rect x="70" y="102" width="7" height="7" rx="1" fill="#6A4A40" /></>
    case 'pilot':
      return <>{govde('#1D3557')}<path d="M52 82 L60 98 L68 82 Z" fill="#FFFFFF" /><path d="M58 85 L62 85 L61.5 97 L60 99 L58.5 97 Z" fill="#111" /><path d="M64 98 L76 96 L70 100 Z M64 98 L76 100 L70 102 Z" fill="#E9C46A" /><rect x="38" y="118" width="44" height="2" fill="#E9C46A" /></>
    case 'kaptan':
      return <>{govde('#FFFFFF', <path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill="none" stroke="#D1D5DB" />)}{[92, 102, 112].map((y) => <rect key={y} x="39" y={y} width="43" height="3" fill="#1D3557" />)}</>
    case 'astronot':
      return <>{govde('#F3F4F6', <path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill="none" stroke="#C9CDD3" />)}<rect x="50" y="94" width="20" height="13" rx="2.5" fill="#D1D5DB" /><circle cx="55" cy="100" r="2" fill="#E63946" /><circle cx="61" cy="100" r="2" fill="#2A9D8F" /><rect x="65" y="98" width="3" height="5" fill="#3A86FF" /><path d="M42 112 L78 112" stroke="#E76F51" strokeWidth="2" /></>
    default:
      return <>{govde('#7FB069')}<path d="M60 108 Q54 100 60 94 Q66 100 60 108 Z" fill="#E9F5DB" /><line x1="60" y1="108" x2="60" y2="112" stroke="#E9F5DB" strokeWidth="1.5" /></>
  }
}

function Sapka({ tip }) {
  // Kafa merkezi (60,52) r=26
  switch (tip) {
    case 'insaat': case 'elektrik':
      return <g><path d="M33 44 Q34 20 60 19 Q86 20 87 44 Z" fill="#FFD23F" /><rect x="29" y="42" width="62" height="6" rx="3" fill="#F5B700" /><rect x="57" y="19" width="6" height="25" fill="#F5B700" /></g>
    case 'makine':
      return <g><path d="M34 40 Q36 22 60 22 Q84 22 86 40 Z" fill="#F3F4F6" stroke="#D1D5DB" /><rect x="31" y="38" width="58" height="6" rx="3" fill="#E5E7EB" /></g>
    case 'sef':
      return <g stroke="#CBD2D9" strokeWidth="1.2"><circle cx="46" cy="22" r="9" fill="#fff" /><circle cx="74" cy="22" r="9" fill="#fff" /><circle cx="60" cy="16" r="11" fill="#fff" /><rect x="40" y="24" width="40" height="13" rx="2" fill="#fff" /><line x1="50" y1="26" x2="50" y2="36" /><line x1="60" y1="26" x2="60" y2="36" /><line x1="70" y1="26" x2="70" y2="36" /></g>
    case 'ressam':
      return <g><ellipse cx="54" cy="30" rx="24" ry="9" fill="#C1121F" transform="rotate(-12 54 30)" /><circle cx="44" cy="22" r="2.5" fill="#C1121F" /></g>
    case 'ciftci':
      return <g><ellipse cx="60" cy="34" rx="38" ry="8" fill="#E9C46A" /><path d="M40 34 Q42 16 60 16 Q78 16 80 34 Z" fill="#E9C46A" /><rect x="40" y="28" width="40" height="5" fill="#BC6C25" /></g>
    case 'dedektif':
      return <g><ellipse cx="60" cy="33" rx="34" ry="6" fill="#5C4033" /><path d="M42 33 Q44 14 60 15 Q76 14 78 33 Z" fill="#6E5236" /><rect x="42" y="27" width="36" height="4" fill="#2B1D14" /></g>
    case 'pilot':
      return <g><path d="M36 34 Q38 18 60 18 Q82 18 84 34 Z" fill="#1D3557" /><rect x="34" y="32" width="52" height="5" rx="2.5" fill="#111827" /><rect x="40" y="28" width="40" height="3" fill="#E9C46A" /><circle cx="60" cy="25" r="3" fill="#E9C46A" /></g>
    case 'kaptan':
      return <g><path d="M34 34 Q36 18 60 17 Q84 18 86 34 Z" fill="#FFFFFF" stroke="#D1D5DB" /><rect x="34" y="32" width="52" height="5" rx="2.5" fill="#1D3557" /><text x="60" y="29" fontSize="10" textAnchor="middle">⚓</text></g>
    case 'sporcu':
      return <rect x="34" y="32" width="52" height="6" rx="3" fill="#FFFFFF" stroke="#E63946" />
    case 'rehber':
      return <g><ellipse cx="60" cy="33" rx="33" ry="6" fill="#C2A878" /><path d="M42 33 Q42 18 60 18 Q78 18 78 33 Z" fill="#D4BE94" /><rect x="42" y="27" width="36" height="4" fill="#8B6B4A" /></g>
    case 'muzisyen':
      return <g fill="none" stroke="#2D2D2D" strokeWidth="4"><path d="M34 52 Q34 22 60 22 Q86 22 86 52" /><rect x="28" y="46" width="9" height="14" rx="4" fill="#6C4AB6" stroke="none" /><rect x="83" y="46" width="9" height="14" rx="4" fill="#6C4AB6" stroke="none" /></g>
    case 'hukuk':
      return null
    default:
      return null
  }
}

function Aksesuar({ tip }) {
  // Sol elin yanındaki nesne (≈ 22-38, 100-130)
  switch (tip) {
    case 'hukuk': return <g transform="translate(24 104) rotate(-20)"><rect x="0" y="0" width="16" height="7" rx="2" fill="#8B5E3C" /><rect x="6.5" y="6" width="3" height="14" fill="#6E4527" /></g>
    case 'dedektif': return <g><circle cx="27" cy="104" r="7" fill="#BFE3FF" fillOpacity=".5" stroke="#5C4033" strokeWidth="2.5" /><line x1="31" y1="110" x2="36" y2="118" stroke="#5C4033" strokeWidth="3" strokeLinecap="round" /></g>
    case 'doktor': return <g><rect x="18" y="100" width="15" height="19" rx="2" fill="#B08968" /><rect x="20" y="103" width="11" height="14" fill="#fff" /><rect x="22" y="98" width="7" height="4" rx="1" fill="#9CA3AF" /><line x1="22" y1="108" x2="29" y2="108" stroke="#9CA3AF" /><line x1="22" y1="112" x2="29" y2="112" stroke="#9CA3AF" /></g>
    case 'dis': return <path d="M20 102 Q20 96 26 97 Q28 98 30 97 Q36 96 36 102 Q36 108 33 116 Q31 120 29 112 Q28 109 27 112 Q25 120 23 116 Q20 108 20 102 Z" fill="#fff" stroke="#9CA3AF" />
    case 'eczaci': return <g><rect x="20" y="102" width="13" height="17" rx="3" fill="#F4A261" /><rect x="19" y="98" width="15" height="5" rx="1.5" fill="#fff" stroke="#E5E7EB" /><rect x="22" y="107" width="9" height="6" fill="#fff" /><text x="26.5" y="112" fontSize="5" textAnchor="middle" fill="#E63946">+</text></g>
    case 'veteriner': return <g><rect x="16" y="108" width="20" height="5" rx="2.5" fill="#F3E9DC" /><circle cx="16" cy="107" r="3" fill="#F3E9DC" /><circle cx="16" cy="114" r="3" fill="#F3E9DC" /><circle cx="36" cy="107" r="3" fill="#F3E9DC" /><circle cx="36" cy="114" r="3" fill="#F3E9DC" /></g>
    case 'bilimci': return <g><path d="M24 96 L30 96 L30 104 L36 118 Q37 122 33 122 L21 122 Q17 122 18 118 L24 104 Z" fill="#E6F4F1" stroke="#9CA3AF" /><path d="M20 114 L34 114 L36 118 Q37 122 33 122 L21 122 Q17 122 18 118 Z" fill="#52B788" /><circle className="msk-kabarcik" cx="26" cy="112" r="1.6" fill="#B7E4C7" /><circle className="msk-kabarcik msk-gecikme" cx="30" cy="115" r="1.2" fill="#B7E4C7" /></g>
    case 'yazilimci': return null
    case 'kuafor': return <g transform="translate(14 98)"><circle cx="4" cy="16" r="3.6" fill="none" stroke="#E63946" strokeWidth="2" /><circle cx="13" cy="16" r="3.6" fill="none" stroke="#E63946" strokeWidth="2" /><path d="M6 13 L20 -2 M11 13 L-1 -2" stroke="#9CA3AF" strokeWidth="2.2" strokeLinecap="round" /></g>
    case 'rehber': return <g><line x1="24" y1="92" x2="24" y2="124" stroke="#6B4F3A" strokeWidth="2" /><path d="M24 92 L40 96 L24 101 Z" fill="#F77F00" /><circle cx="24" cy="92" r="1.6" fill="#6B4F3A" /></g>
    case 'analist': return <g><rect x="12" y="96" width="24" height="20" rx="2" fill="#FFFFFF" stroke="#9CA3AF" /><rect x="15" y="108" width="3.5" height="6" fill="#2A9D8F" /><rect x="20" y="104" width="3.5" height="10" fill="#3A86FF" /><rect x="25" y="100" width="3.5" height="14" fill="#E76F51" /><path d="M15 106 L21 102 L26 98 L33 99" stroke="#E63946" strokeWidth="1.3" fill="none" /><circle className="msk-kabarcik msk-gecikme" cx="33" cy="99" r="1.4" fill="#E63946" /></g>
    case 'elektrik': return <g><rect x="18" y="100" width="14" height="20" rx="2.5" fill="#FFD23F" stroke="#B08900" /><rect x="20.5" y="103" width="9" height="6" fill="#2D3748" /><text x="25" y="108" fontSize="4.5" textAnchor="middle" fill="#7EE787" fontFamily="monospace">12V</text><circle cx="25" cy="114" r="2.5" fill="#2D3748" /></g>
    case 'makine': return <g transform="translate(18 98) rotate(25)"><rect x="4" y="4" width="4" height="22" rx="1.5" fill="#9CA3AF" /><path d="M0 4 Q0 -2 6 -2 Q12 -2 12 4 L9 4 L9 1 L3 1 L3 4 Z" fill="#9CA3AF" /></g>
    case 'insaat': return <g><rect x="14" y="108" width="24" height="6" rx="1.5" fill="#F4A261" /><circle cx="26" cy="111" r="2" fill="#90E0EF" stroke="#264653" strokeWidth=".8" /></g>
    case 'mimar': return <g><rect x="16" y="98" width="8" height="24" rx="4" fill="#5DADE2" transform="rotate(-15 20 110)" /><circle cx="17" cy="99" r="3.5" fill="#3498DB" /></g>
    case 'ogretmen': case 'akademisyen': return <g><rect x="16" y="102" width="20" height="16" rx="1.5" fill={tip === 'ogretmen' ? '#3A86FF' : '#7D5A50'} /><rect x="18" y="104" width="16" height="12" fill="#FDFCF7" /><line x1="26" y1="104" x2="26" y2="116" stroke={tip === 'ogretmen' ? '#3A86FF' : '#7D5A50'} /></g>
    case 'sef': return <g><ellipse cx="22" cy="104" rx="6" ry="4" fill="#9CA3AF" /><rect x="26" y="103" width="3" height="20" rx="1.5" fill="#9CA3AF" transform="rotate(20 27 104)" /></g>
    case 'muzisyen': return <g className="msk-nota"><path d="M24 96 L24 112" stroke="#6C4AB6" strokeWidth="2" /><ellipse cx="21.5" cy="112" rx="3.5" ry="2.6" fill="#6C4AB6" /><path d="M24 96 Q30 98 30 103" stroke="#6C4AB6" strokeWidth="2" fill="none" /></g>
    case 'sahne': return <g><path d="M16 100 Q26 96 36 100 Q36 114 26 118 Q16 114 16 100 Z" fill="#F4D35E" /><circle cx="22" cy="105" r="1.8" fill="#333" /><circle cx="30" cy="105" r="1.8" fill="#333" /><path d="M21 110 Q26 114 31 110" stroke="#333" strokeWidth="1.5" fill="none" /></g>
    case 'gazeteci': return <g><circle cx="26" cy="100" r="5.5" fill="#4B5563" /><rect x="24" y="104" width="4" height="16" rx="2" fill="#111827" /><rect x="22" y="106" width="8" height="5" fill="#E63946" /></g>
    case 'ressam': return <g><path d="M14 108 Q14 98 26 98 Q38 98 38 108 Q38 116 30 115 Q27 114 28 118 Q28 122 22 120 Q14 116 14 108 Z" fill="#E9D8A6" stroke="#B08968" /><circle cx="21" cy="104" r="2" fill="#E63946" /><circle cx="27" cy="102" r="2" fill="#3A86FF" /><circle cx="33" cy="105" r="2" fill="#2A9D8F" /><circle cx="32" cy="111" r="2" fill="#FFD23F" /></g>
    case 'sporcu': return <g className="msk-top"><circle cx="24" cy="116" r="7" fill="#FFFFFF" stroke="#333" /><path d="M24 109 L27 113 L25 118 L21 118 L20 113 Z" fill="#333" /></g>
    case 'ciftci': return <g><path d="M24 122 L24 100" stroke="#6B8F71" strokeWidth="2" />{[102, 106, 110].map((y) => <ellipse key={y} cx={y % 4 ? 21 : 27} cy={y} rx="3.5" ry="1.8" fill="#E9C46A" transform={`rotate(${y % 4 ? -30 : 30} ${y % 4 ? 21 : 27} ${y})`} />)}</g>
    case 'is_insani': return <g><rect x="14" y="106" width="22" height="16" rx="2.5" fill="#6E4527" /><rect x="21" y="102" width="8" height="5" rx="1.5" fill="none" stroke="#6E4527" strokeWidth="2" /><rect x="14" y="112" width="22" height="2" fill="#4E3019" /></g>
    case 'pilot': return <g><path d="M14 112 L36 108 L38 110 L16 116 Z" fill="#9CA3AF" /><path d="M24 110 L28 102 L31 103 L29 110 Z M24 113 L27 120 L30 119 L29 112 Z" fill="#9CA3AF" /></g>
    case 'kaptan': return <g><circle cx="25" cy="110" r="9" fill="none" stroke="#8B5E3C" strokeWidth="3" />{[0, 45, 90, 135].map((a) => <line key={a} x1="25" y1="110" x2={25 + 12 * Math.cos((a * Math.PI) / 180)} y2={110 + 12 * Math.sin((a * Math.PI) / 180)} stroke="#8B5E3C" strokeWidth="2" />)}</g>
    case 'astronot': return <g><line x1="26" y1="96" x2="26" y2="122" stroke="#6B7280" strokeWidth="2" /><path d="M26 96 L40 99 L26 104 Z" fill="#E63946" /></g>
    default: return null
  }
}

const KOL_RENK = {
  hukuk: '#1F1F24', dedektif: '#9C7A54', doktor: '#FFFFFF', dis: '#FFFFFF', eczaci: '#FFFFFF', veteriner: '#FFFFFF',
  bilimci: '#FFFFFF', yazilimci: '#3A3F58', analist: '#2A9D8F', elektrik: '#2F5D8A', makine: '#2F5D8A', insaat: '#9CA3AF', mimar: '#2B2B2B',
  ogretmen: '#C97B63', sef: '#FFFFFF', muzisyen: '#6C4AB6', sahne: '#9B2335', gazeteci: '#F1F1F1', ressam: '#E9C46A',
  sporcu: '#E63946', ciftci: '#E9EDC9', is_insani: '#2C3E50', akademisyen: '#7D5A50', pilot: '#1D3557', kaptan: '#FFFFFF',
  astronot: '#F3F4F6', gunluk: '#7FB069', kuafor: '#F4ACB7', rehber: '#F1FAEE',
}

function Kol({ x1, y1, x2, y2, renk, el }) {
  return (
    <>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(0,0,0,.14)" strokeWidth="10.5" strokeLinecap="round" />
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={renk} strokeWidth="8.5" strokeLinecap="round" />
      <circle cx={x2} cy={y2 + 1} r="5" fill={el} />
    </>
  )
}

export function Karakter({ cinsiyet, kiyafet, gozGoz, kirp, uyku, konusuyor }) {
  const kolRenk = KOL_RENK[kiyafet] || '#7FB069'
  const elRenk = kiyafet === 'astronot' ? '#D1D5DB' : TEN
  const sacli = cinsiyet === 'erkek' || cinsiyet === 'kadin'
  const kafaRenk = sacli ? TEN : '#9BD18B'
  const gozluk = ['mimar', 'ogretmen', 'akademisyen', 'analist'].includes(kiyafet)
  const goggles = kiyafet === 'bilimci'
  const kapuson = kiyafet === 'yazilimci'
  const sapkaVar = !['hukuk', 'yazilimci', 'analist', 'kuafor', 'gunluk', 'doktor', 'dis', 'eczaci', 'veteriner', 'bilimci', 'ogretmen', 'akademisyen', 'mimar', 'is_insani', 'gazeteci', 'sahne', 'astronot'].includes(kiyafet)
  return (
    <svg viewBox="0 0 120 160" width="100%" height="100%" style={{ overflow: 'visible' }}>
      <ellipse className="msk-golge" cx="60" cy="150" rx="26" ry="4.5" fill="rgba(0,0,0,.15)" />
      <g className="msk-beden">
        {/* bacaklar */}
        <rect x="46" y="120" width="11" height="22" rx="5" fill={kiyafet === 'sporcu' ? '#E63946' : '#3D405B'} />
        <rect x="63" y="120" width="11" height="22" rx="5" fill={kiyafet === 'sporcu' ? '#E63946' : '#3D405B'} />
        <ellipse cx="50" cy="145" rx="8" ry="4" fill="#2B2D42" />
        <ellipse cx="70" cy="145" rx="8" ry="4" fill="#2B2D42" />
        {cinsiyet === 'kadin' && !['hukuk', 'astronot'].includes(kiyafet) && <path d="M40 116 L80 116 L86 132 Q60 138 34 132 Z" fill="#3D405B" opacity=".9" />}
        {/* gövde + kıyafet */}
        <Kiyafet tip={kiyafet} />
        {kapuson && <path d="M44 84 Q60 70 76 84 Q60 78 44 84 Z" fill="#2A2E42" />}
        {/* sol kol + aksesuar */}
        <g className="msk-solkol">
          <Kol x1={41} y1={88} x2={31} y2={110} renk={kolRenk} el={elRenk} />
          <Aksesuar tip={kiyafet} />
        </g>
        {/* sağ kol (el sallar) */}
        <g className="msk-sagkol">
          <Kol x1={79} y1={88} x2={89} y2={110} renk={kolRenk} el={elRenk} />
        </g>
        {kiyafet === 'yazilimci' && (
          <g>
            <rect x="34" y="104" width="34" height="20" rx="2.5" fill="#9CA3AF" />
            <rect x="36.5" y="106.5" width="29" height="15" rx="1" fill="#0D1117" />
            <text className="msk-imlec" x="51" y="116.5" fontSize="7" textAnchor="middle" fill="#7EE787" fontFamily="monospace">{'{ }_'}</text>
            <rect x="30" y="124" width="42" height="3.5" rx="1.5" fill="#6B7280" />
          </g>
        )}
        {/* kafa */}
        <g className="msk-kafa">
          {cinsiyet === 'kadin' && <path d="M32 52 Q30 86 42 92 L78 92 Q90 86 88 52 Q86 26 60 26 Q34 26 32 52 Z" fill={SAC} />}
          <circle cx="60" cy="54" r="26" fill={kafaRenk} />
          {sacli && <><circle cx="34.5" cy="57" r="4" fill={TEN} /><circle cx="85.5" cy="57" r="4" fill={TEN} /></>}
          {cinsiyet === 'erkek' && <path d="M35 50 Q34 26 60 26 Q86 26 85 50 Q80 38 70 37 Q64 42 52 39 Q42 40 35 50 Z" fill={SAC} />}
          {cinsiyet === 'kadin' && (
            <>
              <path d="M34 54 Q32 28 60 27 Q88 28 86 54 Q82 40 74 36 Q66 44 50 40 Q40 44 34 54 Z" fill={SAC} />
              {!sapkaVar && <g transform="translate(78 32)"><path d="M0 0 L-6 -5 L-6 5 Z M0 0 L6 -5 L6 5 Z" fill="#E76F51" /><circle r="2" fill="#C44536" /></g>}
            </>
          )}
          {!sacli && <path d="M40 40 Q50 30 60 32" stroke="#7CB86B" strokeWidth="2" fill="none" opacity=".6" />}
          {/* gözler */}
          <g className="msk-gozler" style={{ transform: kirp || uyku ? 'scaleY(0.12)' : 'scaleY(1)', transformBox: 'fill-box', transformOrigin: 'center' }}>
            <ellipse cx="50" cy="56" rx="4.6" ry="5.4" fill="#fff" />
            <ellipse cx="70" cy="56" rx="4.6" ry="5.4" fill="#fff" />
            <circle cx={50 + gozGoz.x} cy={57 + gozGoz.y} r="2.9" fill="#2B2D42" />
            <circle cx={70 + gozGoz.x} cy={57 + gozGoz.y} r="2.9" fill="#2B2D42" />
            <circle cx={51 + gozGoz.x} cy={55.8 + gozGoz.y} r="1" fill="#fff" />
            <circle cx={71 + gozGoz.x} cy={55.8 + gozGoz.y} r="1" fill="#fff" />
          </g>
          {cinsiyet === 'kadin' && !uyku && <><path d="M44.5 51 L43 49 M55.5 51 L57 49 M64.5 51 L63 49 M75.5 51 L77 49" stroke="#2B2D42" strokeWidth="1.2" strokeLinecap="round" /></>}
          {gozluk && <g fill="none" stroke="#2B2D42" strokeWidth="1.6"><circle cx="50" cy="56" r="7" /><circle cx="70" cy="56" r="7" /><line x1="57" y1="56" x2="63" y2="56" /></g>}
          {goggles && <g><rect x="38" y="36" width="44" height="9" rx="4.5" fill="#6B7280" /><circle cx="50" cy="40.5" r="5" fill="#BDE0FE" stroke="#4B5563" strokeWidth="1.5" /><circle cx="70" cy="40.5" r="5" fill="#BDE0FE" stroke="#4B5563" strokeWidth="1.5" /></g>}
          {/* yanaklar + ağız */}
          <ellipse cx="43" cy="65" rx="4" ry="2.4" fill="#F4A3A3" opacity=".7" />
          <ellipse cx="77" cy="65" rx="4" ry="2.4" fill="#F4A3A3" opacity=".7" />
          {uyku
            ? <path d="M55 68 Q60 70 65 68" stroke="#2B2D42" strokeWidth="1.8" fill="none" strokeLinecap="round" />
            : konusuyor
              ? <ellipse className="msk-agiz-konus" cx="60" cy="68.5" rx="4" ry="3" fill="#9B2C2C" />
              : <path d="M53 66 Q60 73 67 66" stroke="#2B2D42" strokeWidth="2" fill="#fff" strokeLinecap="round" />}
          {kiyafet === 'sporcu' && <rect x="34" y="40" width="52" height="5" rx="2.5" fill="#E63946" />}
          {/* şapka */}
          <Sapka tip={kiyafet} />
          {kiyafet === 'astronot' && <circle cx="60" cy="54" r="33" fill="#BDE0FE" fillOpacity=".25" stroke="#E5E7EB" strokeWidth="3" />}
          {/* filiz (her zaman en üstte) */}
          <g className="msk-filiz">
            <path d="M60 28 Q60 18 60 10" stroke="#4F772D" strokeWidth="2.5" fill="none" strokeLinecap="round" />
            <path d="M60 14 Q50 4 44 12 Q52 18 60 14 Z" fill="#90A955" />
            <path d="M60 12 Q70 0 78 8 Q70 16 60 12 Z" fill="#6A994E" />
          </g>
        </g>
      </g>
    </svg>
  )
}

// ----------------------------------------------------------------------------- Ana bileşen
const ANIMASYONLAR = ['salla', 'zipla', 'don', 'dans', 'dusun', 'onayla']
const SURE = { salla: 1600, zipla: 900, don: 1100, dans: 2000, dusun: 2200, onayla: 1200, kutla: 1800, giris: 900 }
const depoOku = (k, v) => { try { return localStorage.getItem(k) ?? v } catch { return v } }
const depoYaz = (k, v) => { try { localStorage.setItem(k, v) } catch { /* yok */ } }

export default function Maskot({ profil, ozet }) {
  const konum = useLocation()
  const [hedef, setHedef] = useState(null)
  const [hedefYuklendi, setHedefYuklendi] = useState(false)
  const [animasyon, setAnimasyon] = useState('giris')
  const [kirp, setKirp] = useState(false)
  const [uyku, setUyku] = useState(false)
  const [gozGoz, setGozGoz] = useState({ x: 0, y: 0 })
  const [balon, setBalon] = useState('')
  const [yazilan, setYazilan] = useState('')
  const [kucuk, setKucuk] = useState(() => depoOku('maskot_kucuk', '0') === '1')
  const [sessiz, setSessiz] = useState(() => depoOku('maskot_sessiz', '0') === '1')
  const [efektler, setEfektler] = useState([])
  const kutu = useRef(null)
  const sonHareket = useRef(Date.now())
  const mesajSirasi = useRef(0)

  const kiyafet = useMemo(() => kiyafetBul(hedef, profil?.hedef_meslek_adi), [hedef, profil?.hedef_meslek_adi])
  const cinsiyet = profil?.cinsiyet === 'erkek' || profil?.cinsiyet === 'kadin' ? profil.cinsiyet : 'notr'
  const ilkAd = profil?.ad_soyad?.trim().split(/\s+/)[0]

  // hedef bölüm: sayfa değiştikçe tazelenir (koçlukta hedef değişince kıyafet hemen değişsin)
  useEffect(() => {
    api.aktifHedefGetir().then((h) => setHedef(h?.bolum_adi || null)).catch(() => setHedef(null)).finally(() => setHedefYuklendi(true))
  }, [konum.pathname])

  const oynat = useCallback((ad) => {
    setAnimasyon(ad)
    window.clearTimeout(oynat.zaman)
    oynat.zaman = window.setTimeout(() => setAnimasyon(''), SURE[ad] || 1200)
  }, [])

  const efektEkle = useCallback((tur, adet) => {
    const yeni = Array.from({ length: adet }, (_, i) => ({ id: `${Date.now()}-${i}-${Math.random()}`, tur, x: Math.random() * 80 - 40, gecikme: i * 70, renk: ['#E63946', '#FFD23F', '#2A9D8F', '#3A86FF', '#8338EC'][i % 5] }))
    setEfektler((e) => [...e, ...yeni])
    window.setTimeout(() => setEfektler((e) => e.filter((x) => !yeni.includes(x))), 1800)
  }, [])

  const mesajSec = useCallback(() => {
    const havuz = []
    const sayfa = sayfaMesaji(konum.pathname, ozet, hedef ? baslikDuzelt(hedef) : null)
    if (sayfa) havuz.push(sayfa, sayfa)
    havuz.push(...(KIYAFET_MESAJLARI[kiyafet] || []), ...GENEL_MESAJLAR)
    if (ilkAd) havuz.push(`${ilkAd}, bugün kendin için küçük bir adım atalım mı? 🌱`)
    mesajSirasi.current = (mesajSirasi.current + 1 + Math.floor(Math.random() * 3)) % havuz.length
    return havuz[mesajSirasi.current]
  }, [konum.pathname, ozet, hedef, kiyafet, ilkAd])

  const konus = useCallback((metin) => {
    if (sessiz || kucuk) return
    setBalon(metin)
  }, [sessiz, kucuk])

  // yazı makinesi efekti (konuşurken ağız hareket eder)
  useEffect(() => {
    if (!balon) { setYazilan(''); return undefined }
    let i = 0
    const t = window.setInterval(() => {
      i += 1
      setYazilan(balon.slice(0, i))
      if (i >= balon.length) window.clearInterval(t)
    }, 28)
    const kapat = window.setTimeout(() => setBalon(''), Math.max(5500, balon.length * 90))
    return () => { window.clearInterval(t); window.clearTimeout(kapat) }
  }, [balon])
  const konusuyor = balon && yazilan.length < balon.length

  // ilk açılış: selam + sayfa mesajı
  useEffect(() => {
    const t1 = window.setTimeout(() => oynat('salla'), 900)
    const t2 = window.setTimeout(() => konus(ilkAd ? `Merhaba ${ilkAd}! Ben Filiz 🌱` : 'Merhaba! Ben Filiz 🌱'), 1100)
    return () => { window.clearTimeout(t1); window.clearTimeout(t2) }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // sayfa değişince o sayfaya özel cümle (hedef bilgisi yüklendikten sonra, en güncel verilerle)
  const guncel = useRef({})
  guncel.current = { ozet, hedef }
  useEffect(() => {
    if (!hedefYuklendi) return undefined
    const t = window.setTimeout(() => {
      const { ozet: o, hedef: h } = guncel.current
      const m = sayfaMesaji(konum.pathname, o, h ? baslikDuzelt(h) : null)
      if (m) { konus(m); oynat('onayla') }
    }, 1600)
    return () => window.clearTimeout(t)
  }, [konum.pathname, hedefYuklendi]) // eslint-disable-line react-hooks/exhaustive-deps

  // kıyafet değişince kutla
  const oncekiKiyafet = useRef(null)
  useEffect(() => {
    if (!hedefYuklendi) return
    if (oncekiKiyafet.current !== null && oncekiKiyafet.current !== kiyafet && kiyafet !== 'gunluk') {
      oynat('don'); efektEkle('yildiz', 10)
      konus(`Yeni kıyafetim nasıl? ${hedef ? baslikDuzelt(hedef) + ' için hazırım!' : ''}`)
    }
    oncekiKiyafet.current = kiyafet
  }, [kiyafet, hedefYuklendi]) // eslint-disable-line react-hooks/exhaustive-deps

  // yeni bir katman bitince konfeti
  useEffect(() => {
    const biten = ozet?.tamamlanan_katman_sayisi
    if (biten == null) return
    const kayitli = Number(depoOku('maskot_biten_katman', '-1'))
    if (kayitli >= 0 && biten > kayitli) {
      window.setTimeout(() => { oynat('kutla'); efektEkle('konfeti', 18); konus(`Bir katman daha bitti! ${biten}/${ozet.toplam_ana_katman_sayisi} 🎉`) }, 1800)
    }
    depoYaz('maskot_biten_katman', String(biten))
  }, [ozet]) // eslint-disable-line react-hooks/exhaustive-deps

  // göz kırpma (rastgele aralıklarla, bazen çift)
  useEffect(() => {
    let t
    const dongu = () => {
      t = window.setTimeout(() => {
        setKirp(true)
        window.setTimeout(() => setKirp(false), 140)
        if (Math.random() < 0.25) window.setTimeout(() => { setKirp(true); window.setTimeout(() => setKirp(false), 120) }, 300)
        dongu()
      }, 2200 + Math.random() * 3800)
    }
    dongu()
    return () => window.clearTimeout(t)
  }, [])

  // gözler imleci takip eder + hareketsizlikte uyur
  useEffect(() => {
    const hareket = (e) => {
      sonHareket.current = Date.now()
      if (uyku) { setUyku(false); oynat('zipla'); konus('Uyumuyordum, sadece gözlerimi dinlendiriyordum 😅') }
      const r = kutu.current?.getBoundingClientRect()
      if (!r) return
      const dx = e.clientX - (r.left + r.width / 2)
      const dy = e.clientY - (r.top + r.height * 0.35)
      const uz = Math.max(1, Math.hypot(dx, dy))
      setGozGoz({ x: (dx / uz) * 1.8, y: (dy / uz) * 1.6 })
    }
    window.addEventListener('mousemove', hareket)
    const kontrol = window.setInterval(() => {
      if (!uyku && Date.now() - sonHareket.current > 75000) { setUyku(true); setBalon('') }
    }, 5000)
    return () => { window.removeEventListener('mousemove', hareket); window.clearInterval(kontrol) }
  }, [uyku, oynat, konus])

  // ara ara: rastgele animasyon + motivasyon cümlesi
  useEffect(() => {
    const anim = window.setInterval(() => { if (!uyku) oynat(ANIMASYONLAR[Math.floor(Math.random() * ANIMASYONLAR.length)]) }, 17000)
    const soz = window.setInterval(() => { if (!uyku) { konus(mesajSec()); oynat(Math.random() < 0.5 ? 'onayla' : 'salla') } }, 55000)
    return () => { window.clearInterval(anim); window.clearInterval(soz) }
  }, [uyku, oynat, konus, mesajSec])

  function tiklandi() {
    if (uyku) { setUyku(false); sonHareket.current = Date.now() }
    const secim = ['zipla', 'don', 'dans', 'salla', 'kutla'][Math.floor(Math.random() * 5)]
    oynat(secim)
    efektEkle(secim === 'kutla' ? 'konfeti' : 'kalp', secim === 'kutla' ? 16 : 5)
    if (!sessiz) setBalon(mesajSec())
  }

  function kucukDegistir(v) { setKucuk(v); depoYaz('maskot_kucuk', v ? '1' : '0'); if (v) setBalon('') }
  function sessizDegistir() { const v = !sessiz; setSessiz(v); depoYaz('maskot_sessiz', v ? '1' : '0'); setBalon(v ? '' : 'Tekrar konuşabilirim! 🗣️') }

  if (kucuk) {
    return (
      <button className="msk-mini" onClick={() => { kucukDegistir(false); oynat('salla'); setTimeout(() => konus('Geri döndüm! 🌱'), 200) }} title="Filiz'i göster">
        <span style={{ fontSize: 22 }}>🌱</span>
        <style>{MASKOT_CSS}</style>
      </button>
    )
  }

  return (
    <div className="msk-kap" ref={kutu}>
      <style>{MASKOT_CSS}</style>
      {balon && (
        <div className="msk-balon">
          {yazilan}
          <span className="msk-balon-kuyruk" />
        </div>
      )}
      <div className={`msk-karakter msk-${animasyon}`} onClick={tiklandi} title="Bana tıkla!">
        <Karakter cinsiyet={cinsiyet} kiyafet={kiyafet} gozGoz={gozGoz} kirp={kirp} uyku={uyku} konusuyor={!!konusuyor} />
        {animasyon === 'dusun' && <div className="msk-dusunce">💭</div>}
        {uyku && <div className="msk-zzz"><span>z</span><span>z</span><span>Z</span></div>}
        {efektler.map((e) => (
          <span key={e.id} className={`msk-efekt msk-${e.tur}`} style={{ left: `calc(50% + ${e.x}px)`, animationDelay: `${e.gecikme}ms`, color: e.renk, background: e.tur === 'konfeti' ? e.renk : undefined, '--dx': `${e.x * 1.6}px` }}>
            {e.tur === 'kalp' ? '❤' : e.tur === 'yildiz' ? '✦' : ''}
          </span>
        ))}
      </div>
      <div className="msk-araclar">
        <button onClick={sessizDegistir} title={sessiz ? 'Konuşmayı aç' : 'Sessize al'}>{sessiz ? '🔇' : '🔊'}</button>
        <button onClick={() => kucukDegistir(true)} title="Küçült">–</button>
      </div>
    </div>
  )
}

const MASKOT_CSS = `
.msk-kap{position:fixed;top:8px;right:14px;width:92px;height:122px;z-index:60;user-select:none}
.msk-kap:hover .msk-araclar{opacity:1}
.msk-karakter{width:100%;height:100%;cursor:pointer;position:relative;animation:msk-giris .9s ease-out}
.msk-beden{animation:msk-nefes 3.2s ease-in-out infinite;transform-origin:60px 150px}
.msk-golge{animation:msk-golge 3.2s ease-in-out infinite;transform-origin:60px 150px}
.msk-filiz{animation:msk-filiz 2.6s ease-in-out infinite;transform-origin:60px 28px}
.msk-kafa{transform-origin:60px 78px;transition:transform .3s}
.msk-sagkol{transform-origin:79px 88px}
.msk-solkol{transform-origin:41px 88px}
.msk-gozler{transition:transform .08s}
.msk-agiz-konus{animation:msk-konus .18s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:center}
.msk-kabarcik{animation:msk-kabarcik 1.6s ease-in infinite}
.msk-gecikme{animation-delay:.8s}
.msk-nota{animation:msk-nota 1.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.msk-imlec{animation:msk-imlec 1s steps(2) infinite}
.msk-top{animation:msk-top 1.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
.msk-salla .msk-sagkol{animation:msk-salla 1.6s ease-in-out}
.msk-zipla{animation:msk-zipla .9s cubic-bezier(.3,1.6,.5,1)}
.msk-don{animation:msk-don 1.1s ease-in-out}
.msk-dans .msk-beden{animation:msk-dans 2s ease-in-out}
.msk-dans .msk-sagkol{animation:msk-salla 2s ease-in-out}
.msk-dans .msk-solkol{animation:msk-solsalla 2s ease-in-out}
.msk-dusun .msk-kafa{transform:rotate(-10deg)}
.msk-onayla .msk-kafa{animation:msk-onayla 1.2s ease-in-out}
.msk-kutla{animation:msk-zipla .9s cubic-bezier(.3,1.6,.5,1) 2}
.msk-kutla .msk-sagkol,.msk-kutla .msk-solkol{animation:msk-kollar 1.8s ease-in-out}
.msk-balon{position:absolute;right:100px;top:14px;width:max-content;max-width:230px;background:var(--sur,#fff);color:var(--tx,#222);border:1.5px solid var(--pu,#E07A3F);border-radius:14px;padding:9px 12px;font-size:12.5px;line-height:1.45;font-weight:600;box-shadow:0 8px 24px rgba(0,0,0,.12);animation:msk-balon .25s ease-out}
.msk-balon-kuyruk{position:absolute;right:-8px;top:18px;width:14px;height:14px;background:var(--sur,#fff);border-right:1.5px solid var(--pu,#E07A3F);border-top:1.5px solid var(--pu,#E07A3F);transform:rotate(45deg)}
.msk-araclar{position:absolute;left:-26px;bottom:6px;display:flex;flex-direction:column;gap:4px;opacity:0;transition:opacity .2s}
.msk-araclar button,.msk-mini{border:1px solid var(--bor,#ddd);background:var(--sur,#fff);border-radius:50%;width:22px;height:22px;font-size:11px;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0}
.msk-mini{position:fixed;top:12px;right:14px;width:42px;height:42px;z-index:60;box-shadow:0 4px 14px rgba(0,0,0,.12);animation:msk-filiz 2.6s ease-in-out infinite}
.msk-dusunce{position:absolute;top:-6px;left:-6px;font-size:20px;animation:msk-yuksel 2.2s ease-out}
.msk-zzz{position:absolute;top:4px;right:-4px;font-weight:800;color:var(--pu,#E07A3F)}
.msk-zzz span{display:inline-block;animation:msk-zzz 2.4s ease-in-out infinite;opacity:0}
.msk-zzz span:nth-child(2){animation-delay:.6s;font-size:13px}
.msk-zzz span:nth-child(3){animation-delay:1.2s;font-size:16px}
.msk-efekt{position:absolute;top:40%;pointer-events:none;font-size:14px;animation:msk-efekt 1.6s ease-out forwards;opacity:0}
.msk-konfeti{width:6px;height:9px;border-radius:2px;animation:msk-konfeti 1.7s ease-out forwards}
@keyframes msk-giris{0%{transform:translateX(130px) rotate(20deg);opacity:0}70%{transform:translateX(-8px) rotate(-4deg);opacity:1}100%{transform:none}}
@keyframes msk-nefes{0%,100%{transform:translateY(0) scale(1,1)}50%{transform:translateY(-3px) scale(1.01,.99)}}
@keyframes msk-golge{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.88)}}
@keyframes msk-filiz{0%,100%{transform:rotate(-7deg)}50%{transform:rotate(7deg)}}
@keyframes msk-konus{from{transform:scaleY(.35)}to{transform:scaleY(1.1)}}
@keyframes msk-salla{0%,100%{transform:rotate(0)}15%{transform:rotate(-150deg)}30%{transform:rotate(-115deg)}45%{transform:rotate(-150deg)}60%{transform:rotate(-115deg)}75%{transform:rotate(-150deg)}}
@keyframes msk-solsalla{0%,100%{transform:rotate(0)}25%,75%{transform:rotate(60deg)}50%{transform:rotate(20deg)}}
@keyframes msk-kollar{0%,100%{transform:rotate(0)}30%,70%{transform:rotate(var(--k,-140deg))}}
.msk-kutla .msk-solkol{--k:140deg}
@keyframes msk-zipla{0%,100%{transform:translateY(0) scale(1)}20%{transform:translateY(4px) scale(1.08,.9)}50%{transform:translateY(-22px) scale(.95,1.06)}80%{transform:translateY(2px) scale(1.04,.96)}}
@keyframes msk-don{0%{transform:rotateY(0)}100%{transform:rotateY(360deg)}}
@keyframes msk-dans{0%,100%{transform:rotate(0)}20%{transform:rotate(-8deg) translateX(-3px)}40%{transform:rotate(8deg) translateX(3px)}60%{transform:rotate(-8deg) translateX(-3px)}80%{transform:rotate(8deg) translateX(3px)}}
@keyframes msk-onayla{0%,100%{transform:rotate(0)}25%{transform:translateY(3px)}50%{transform:translateY(0)}75%{transform:translateY(3px)}}
@keyframes msk-kabarcik{0%{transform:translateY(0);opacity:1}100%{transform:translateY(-14px);opacity:0}}
@keyframes msk-nota{0%,100%{transform:translateY(0) rotate(-8deg)}50%{transform:translateY(-5px) rotate(8deg)}}
@keyframes msk-imlec{0%{opacity:1}100%{opacity:.35}}
@keyframes msk-top{0%,100%{transform:translateY(0)}50%{transform:translateY(-4px)}}
@keyframes msk-balon{from{transform:scale(.6) translateX(20px);opacity:0}to{transform:none;opacity:1}}
@keyframes msk-yuksel{0%{transform:translateY(8px);opacity:0}30%{opacity:1}100%{transform:translateY(-10px);opacity:0}}
@keyframes msk-zzz{0%{transform:translate(0,0);opacity:0}30%{opacity:1}100%{transform:translate(10px,-18px);opacity:0}}
@keyframes msk-efekt{0%{transform:translateY(0) scale(.6);opacity:0}20%{opacity:1}100%{transform:translateY(-60px) scale(1.2);opacity:0}}
@keyframes msk-konfeti{0%{transform:translate(0,0) rotate(0);opacity:1}100%{transform:translate(var(--dx,0),70px) rotate(540deg);opacity:0}}
@media (max-width: 760px){.msk-kap{width:64px;height:86px;top:6px;right:8px}.msk-balon{right:70px;max-width:180px;font-size:11.5px}}
@media (prefers-reduced-motion: reduce){.msk-kap *{animation-duration:0s!important}}
`
