import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../api/client'
import { useModuller } from '../yardimci/moduller'
import { dogalSesVarMi, efekt, sesAcikMi, sesAyarla, soyle, sus } from '../yardimci/filizSes'

/*
 * [2026-10-03] Filiz maskotu — sağ üstte duran, hedef bölüme göre kıyafet değiştiren,
 * ara ara motivasyon cümlesi söyleyen animasyonlu karakter.
 *  - Görünüm: profildeki cinsiyete göre (erkek / kadın / diğer → filiz karakter)
 *  - Kıyafet: hedef mesleğe (yoksa hedef bölüme) göre 64 farklı kıyafet
 *  - Animasyonlar: nefes alma, göz kırpma, imleci takip eden gözler, filiz sallanması, el sallama,
 *    zıplama, dönme, dans, düşünme, başını sallama, konuşurken ağız hareketi, uyuma (Zzz),
 *    kalp ve konfeti efektleri, giriş animasyonu
 *  - Tıklayınca: yeni bir cümle + rastgele animasyon. Küçültülebilir ve sessize alınabilir.
 * Tamamen SVG + CSS; dışarıdan resim dosyası yoktur. Soru ekranlarında görünmez (o sayfalar bu düzenin dışında).
 */

// ----------------------------------------------------------------------------- Kıyafet seçimi
const KIYAFET_KURALLARI = [
  ['okuloncesi', ['okul öncesi', 'çocuk gelişimi']],
  ['siber', ['siber', 'bilgi güvenliği', 'adli bilişim']],
  ['oyun', ['oyun tasarım', 'dijital oyun']],
  ['hemsire', ['hemşirelik', 'ebelik']],
  ['fizyoterapist', ['fizyoterapi', 'ergoterapi']],
  ['diyetisyen', ['beslenme', 'diyetetik']],
  ['paramedik', ['acil yardım', 'afet']],
  ['petrol', ['petrol', 'doğalgaz']],
  ['madenci', ['maden', 'cevher']],
  ['jeolog', ['jeoloji', 'jeofizik']],
  ['haritaci', ['harita', 'geomatik']],
  ['metalurji', ['metalurji']],
  ['otomotiv', ['otomotiv']],
  ['endustri', ['endüstri mühendisliği']],
  ['tekstilci', ['tekstil mühendisliği', 'deri mühendisliği']],
  ['modaci', ['moda', 'tekstil tasarımı', 'aksesuar', 'ayakkabı']],
  ['kuyumcu', ['kuyumculuk', 'takı', 'mücevher']],
  ['fotografci', ['fotoğraf']],
  ['tasarimci', ['grafik', 'görsel iletişim', 'animasyon', 'endüstriyel tasarım']],
  ['yonetmen', ['sinema', 'film', 'televizyon']],
  ['pazarlamaci', ['reklam', 'pazarlama', 'halkla ilişkiler']],
  ['dansci', ['dans', 'halk oyunları']],
  ['otelci', ['otel', 'konaklama']],
  ['ormanci', ['orman', 'yaban hayatı', 'doğa koruma']],
  ['balikci', ['su ürünleri', 'balıkçılık']],
  ['mimar', ['peyzaj mimar']],
  ['psikolog', ['aile ve tüketici', 'aile danışmanlığı']],
  ['tekstilci', ['halı', 'kilim']],
  ['bahcivan', ['bahçe', 'peyzaj']],
  ['arkeolog', ['arkeoloji', 'antropoloji']],
  ['kutuphaneci', ['bilgi ve belge', 'müzecilik', 'kütüphane', 'arşiv']],
  ['finansci', ['finans', 'muhasebe', 'bankacılık', 'maliye', 'sigortacılık', 'iktisat', 'ekonomi']],
  ['lojistikci', ['lojistik', 'gümrük', 'ticaret']],
  ['diplomat', ['uluslararası ilişkiler', 'siyaset', 'kamu yönetimi', 'yerel yönetim', 'avrupa birliği', 'politika']],
  ['yazar', ['edebiyat']],
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
  ['psikolog', ['psikoloji', 'psikolojik', 'sosyal hizmet', 'aile danışmanlığı']],
  ['cevirmen', ['mütercim', 'tercüman', 'çeviri', 'işaret dili']],
  ['akademisyen', ['psikoloji', 'sosyoloji', 'felsefe', 'tarih', 'edebiyat', 'dil', 'mütercim', 'arkeoloji', 'antropoloji', 'ilahiyat', 'islam', 'coğrafya', 'halkbilimi', 'müzecilik', 'bilgi ve belge', 'siyaset', 'uluslararası', 'kamu yönetimi', 'sosyal hizmet', 'yerel yönetim', 'kültür', 'avrupa birliği', 'politika']],
]

// [2026-10-04] Önce profildeki HEDEF MESLEĞE bakılır (daha belirleyici), bulunamazsa hedef bölüme.
// Karşılaştırma büyük/küçük harf ve ı/i farkından etkilenmez (fold).
const fold = (t) => ` ${String(t || '').toLocaleLowerCase('tr').replace(/ı/g, 'i')} `

// 301 bölümün her biri tek tek eşlendi (kelime eşleştirmesi 'Gastronomi'yi astronot yapıyordu).
const BOLUM_KIYAFET = {
  'acil yardim ve afet yönetimi': 'paramedik',
  'adli bilimler': 'dedektif',
  'adli bilişim mühendisliği': 'siber',
  'aile ve tüketici bilimleri': 'psikolog',
  'aksesuar tasarimi': 'modaci',
  'aktüerya bilimleri': 'analist',
  'animasyon ve oyun tasarimi': 'oyun',
  'antrenörlük eğitimi': 'sporcu',
  'antropoloji': 'arkeolog',
  'arkeoloji': 'arkeolog',
  'astronomi ve uzay bilimleri': 'astronot',
  'avrupa birliği ilişkileri': 'diplomat',
  'ayakkabi tasarimi ve üretimi': 'modaci',
  'ağaç işleri endüstri mühendisliği': 'makine',
  'bahçe bitkileri': 'bahcivan',
  'balikçilik teknolojisi mühendisliği': 'balikci',
  'bankacilik ve finans': 'finansci',
  'bankacilik ve sigortacilik': 'finansci',
  'basim teknolojileri': 'tasarimci',
  'basin ve yayin': 'gazeteci',
  'baski sanatlari': 'ressam',
  'beslenme ve diyetetik': 'diyetisyen',
  'bestecilik ve orkestra şefliği': 'muzisyen',
  'bileşik sanatlar': 'ressam',
  'bilgi güvenliği mühendisliği': 'siber',
  'bilgi ve belge yönetimi': 'kutuphaneci',
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
  'cevher hazirlama mühendisliği': 'madenci',
  'coğrafya': 'haritaci',
  'coğrafya öğretmenliği': 'ogretmen',
  'deniz ulaştirma işletme mühendisliği': 'kaptan',
  'denizcilik işletmeleri yönetimi': 'kaptan',
  'deri mühendisliği': 'tekstilci',
  'dijital medya ve pazarlama': 'pazarlamaci',
  'dijital oyun tasarimi': 'oyun',
  'dil ve edebiyat': 'yazar',
  'dil ve konuşma terapisi': 'doktor',
  'dil öğretmenliği': 'ogretmen',
  'diş hekimliği': 'dis',
  'doğa koruma ve biyoçeşitlilik yönetimi': 'ormanci',
  'drama ve oyunculuk': 'sahne',
  'drama yazarliği ve dramaturji': 'sahne',
  'ebelik': 'hemsire',
  'eczacilik': 'eczaci',
  'egzersiz ve spor bilimleri': 'sporcu',
  'ekonometri': 'analist',
  'ekonomi': 'finansci',
  'ekonomi ve finans': 'finansci',
  'el sanatlari': 'ressam',
  'elektrik ve elektronik mühendisliği': 'elektrik',
  'elektronik ticaret ve yönetimi': 'pazarlamaci',
  'endüstri mühendisliği': 'endustri',
  'endüstriyel tasarim': 'tasarimci',
  'endüstriyel tasarim mühendisliği': 'makine',
  'enerji sistemleri mühendisliği': 'elektrik',
  'enerji yönetimi': 'elektrik',
  'ergoterapi': 'fizyoterapist',
  'felsefe': 'akademisyen',
  'felsefe grubu öğretmenliği': 'ogretmen',
  'fen bilgisi öğretmenliği': 'ogretmen',
  'film tasarimi ve yazarliği': 'yonetmen',
  'film tasarimi ve yönetmenliği': 'yonetmen',
  'film yapimi ve yayincilik': 'yonetmen',
  'finans ve bankacilik': 'finansci',
  'fizik': 'bilimci',
  'fizik mühendisliği': 'bilimci',
  'fizik öğretmenliği': 'ogretmen',
  'fizyoterapi ve rehabilitasyon': 'fizyoterapist',
  'fotonik': 'elektrik',
  'fotoğraf ve video': 'fotografci',
  'gastronomi ve mutfak sanatlari': 'sef',
  'gayrimenkul geliştirme ve yönetimi': 'is_insani',
  'gazetecilik': 'gazeteci',
  'geleneksel türk sanatlari': 'ressam',
  'gemi inşaati ve gemi makineleri mühendisliği': 'kaptan',
  'gemi makineleri işletme mühendisliği': 'kaptan',
  'gemi ve yat tasarimi': 'kaptan',
  'genetik ve biyomühendislik': 'bilimci',
  'gerontoloji': 'hemsire',
  'gida mühendisliği': 'bilimci',
  'girişimcilik': 'is_insani',
  'grafik tasarimi': 'tasarimci',
  'görsel iletişim tasarimi': 'tasarimci',
  'görsel sanatlar': 'ressam',
  'görsel sanatlar öğretmenliği': 'ogretmen',
  'gümrük işletme': 'lojistikci',
  'güverte': 'kaptan',
  'hali tasarimi': 'tekstilci',
  'hali, kilim ve geleneksel kumaş desenleri': 'tekstilci',
  'halkbilimi': 'akademisyen',
  'halkla ilişkiler ve reklamcilik': 'pazarlamaci',
  'harita mühendisliği': 'haritaci',
  'hassas tarim ve tarimsal robotlar': 'ciftci',
  'hat sanati': 'ressam',
  'hava trafik kontrolü': 'pilot',
  'havacilik elektrik ve elektroniği': 'pilot',
  'havacilik ve uzay mühendisliği': 'pilot',
  'havacilik yönetimi': 'pilot',
  'hayvansal üretim ve teknolojileri': 'ciftci',
  'hemşirelik': 'hemsire',
  'heykel': 'ressam',
  'hidrojeoloji mühendisliği': 'jeolog',
  'hidrolik ve su kaynaklari mühendisliği': 'insaat',
  'hukuk': 'hukuk',
  'iklim bilimi ve meteoroloji mühendisliği': 'bilimci',
  'iktisat': 'finansci',
  'ilahiyat': 'akademisyen',
  'iletişim bilimleri': 'gazeteci',
  'iletişim tasarimi ve yönetimi': 'gazeteci',
  'ilköğretim matematik öğretmenliği': 'ogretmen',
  'imalat mühendisliği': 'makine',
  'insan kaynaklari yönetimi': 'is_insani',
  'inşaat mühendisliği': 'insaat',
  'islam bilimleri': 'akademisyen',
  'islam iktisadi ve finans': 'finansci',
  'istatistik': 'analist',
  'iç mimarlik ve çevre tasarimi': 'mimar',
  'iş sağliği ve güvenliği': 'insaat',
  'işletme': 'is_insani',
  'işletme mühendisliği': 'endustri',
  'jeofizik mühendisliği': 'jeolog',
  'jeoloji mühendisliği': 'jeolog',
  'kamu yönetimi': 'diplomat',
  'kanatli hayvan yetiştiriciliği': 'ciftci',
  'karşilaştirmali edebiyat': 'yazar',
  'kentsel tasarim ve peyzaj mimarliği': 'mimar',
  'kimya': 'bilimci',
  'kimya mühendisliği': 'bilimci',
  'kimya öğretmenliği': 'ogretmen',
  'kimya-biyoloji mühendisliği': 'bilimci',
  'kontrol ve otomasyon mühendisliği': 'elektrik',
  'kurgu, ses ve görüntü yönetimi': 'yonetmen',
  'kuyumculuk ve mücevher tasarimi': 'kuyumcu',
  'kültür varliklarini koruma ve onarim': 'ressam',
  'kültür ve iletişim bilimleri': 'gazeteci',
  'küresel siyaset ve uluslararasi ilişkiler': 'diplomat',
  'liderlik': 'is_insani',
  'lojistik yönetimi': 'lojistikci',
  'maden mühendisliği': 'madenci',
  'makine mühendisliği': 'makine',
  'maliye': 'finansci',
  'malzeme bilimi ve mühendisliği': 'metalurji',
  'malzeme bilimi ve nanoteknoloji mühendisliği': 'metalurji',
  'matematik': 'analist',
  'matematik mühendisliği': 'analist',
  'matematik ve bilgisayar bilimleri': 'analist',
  'matematik öğretmenliği': 'ogretmen',
  'medya ve iletişim': 'gazeteci',
  'mekatronik mühendisliği': 'elektrik',
  'metalurji ve malzeme mühendisliği': 'metalurji',
  'mimarlik': 'mimar',
  'moda tasarimi': 'modaci',
  'modern dans': 'dansci',
  'moleküler biyoloji ve genetik': 'bilimci',
  'moleküler biyoteknoloji': 'bilimci',
  'muhasebe ve denetim': 'finansci',
  'muhasebe ve finans yönetimi': 'finansci',
  'mütercim ve tercümanlik': 'cevirmen',
  'müzecilik': 'kutuphaneci',
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
  'okul öncesi öğretmenliği': 'okuloncesi',
  'optik ve akustik mühendisliği': 'elektrik',
  'organik tarim işletmeciliği': 'ciftci',
  'orkestra ve koro şefliği': 'muzisyen',
  'orman endüstrisi mühendisliği': 'ormanci',
  'orman mühendisliği': 'ormanci',
  'ortez ve protez': 'doktor',
  'otel yöneticiliği': 'otelci',
  'otomotiv mühendisliği': 'otomotiv',
  'oyunculuk': 'sahne',
  'pazarlama': 'pazarlamaci',
  'pazarlama iletişimi': 'pazarlamaci',
  'perfüzyon': 'doktor',
  'petrol ve doğalgaz mühendisliği': 'petrol',
  'peyzaj mimarliği': 'mimar',
  'pilotaj': 'pilot',
  'plastik sanatlar ve resim': 'ressam',
  'polimer malzeme mühendisliği': 'makine',
  'politika ve ekonomi': 'diplomat',
  'psikoloji': 'psikolog',
  'psikolojik danişmanlik ve rehberlik öğretmenliği': 'psikolog',
  'radyo, televizyon ve sinema': 'yonetmen',
  'rayli sistemler mühendisliği': 'makine',
  'rehberlik ve psikolojik danişmanlik': 'psikolog',
  'reklamcilik': 'pazarlamaci',
  'rekreasyon yönetimi': 'sporcu',
  'resim': 'ressam',
  'resim öğretmenliği': 'ogretmen',
  'sahne dekoru ve kostümü': 'sahne',
  'sahne sanatlari': 'sahne',
  'sahne tasarimi': 'sahne',
  'sahne ve gösteri sanatlari yönetimi': 'sahne',
  'sanat tarihi': 'kutuphaneci',
  'sanat ve kültür yönetimi': 'ressam',
  'saç ve güzellik uygulamalari': 'kuafor',
  'sağlik yönetimi': 'is_insani',
  'seramik ve cam': 'ressam',
  'sermaye piyasasi': 'finansci',
  'ses sanatlari tasarimi': 'muzisyen',
  'seyahat işletmeciliği ve turizm rehberliği': 'rehber',
  'siber güvenlik mühendisliği': 'siber',
  'sigortacilik ve aktüerya bilimleri': 'analist',
  'sigortacilik ve risk yönetimi': 'finansci',
  'sinema ve dijital medya': 'yonetmen',
  'sinif öğretmenliği': 'ogretmen',
  'sivil hava ulaştirma işletmeciliği': 'pilot',
  'siyaset bilimi ve kamu yönetimi': 'diplomat',
  'siyaset bilimi ve uluslararasi ilişkiler': 'diplomat',
  'sosyal bilgiler öğretmenliği': 'ogretmen',
  'sosyal hizmet': 'psikolog',
  'sosyoloji': 'akademisyen',
  'spor yöneticiliği': 'sporcu',
  'spor öğretmenliği': 'ogretmen',
  'su bilimleri ve mühendisliği': 'insaat',
  'su ürünleri mühendisliği': 'balikci',
  'süt teknolojisi': 'ciftci',
  'taki tasarimi ve imalati': 'kuyumcu',
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
  'tekstil mühendisliği': 'tekstilci',
  'tekstil tasarimi': 'modaci',
  'tekstil ve moda tasarimi': 'modaci',
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
  'turizm ve konaklama işletmeciliği': 'otelci',
  'türk halk oyunlari': 'dansci',
  'türk halkbilimi': 'akademisyen',
  'ulaştirma ve trafik mühendisliği': 'insaat',
  'uluslararasi ekonomik ilişkiler': 'diplomat',
  'uluslararasi finans': 'finansci',
  'uluslararasi girişimcilik': 'is_insani',
  'uluslararasi hukuk': 'hukuk',
  'uluslararasi ilişkiler': 'diplomat',
  'uluslararasi işletmecilik ve ticaret': 'lojistikci',
  'uluslararasi ticaret ve lojistik': 'lojistikci',
  'uzay bilimleri ve teknolojileri': 'astronot',
  'uzay mühendisliği': 'astronot',
  'uçak bakim ve onarim': 'pilot',
  'uçak mühendisliği': 'pilot',
  'veri bilimi ve analitiği': 'analist',
  'veterinerlik': 'veteriner',
  'yaban hayati ekolojisi ve yönetimi': 'ormanci',
  'yapay zeka mühendisliği': 'yazilimci',
  'yapay zeka ve makine öğrenmesi': 'yazilimci',
  'yapay zeka ve veri mühendisliği': 'yazilimci',
  'yazilim mühendisliği': 'yazilimci',
  'yeni medya ve gazetecilik': 'gazeteci',
  'yeni medya ve iletişim': 'gazeteci',
  'yerel yönetimler': 'diplomat',
  'yiyecek ve içecek işletmeciliği': 'sef',
  'yönetim bilişim sistemleri': 'yazilimci',
  'zootekni': 'ciftci',
  'çalgi teknolojileri': 'muzisyen',
  'çalişma ekonomisi ve endüstri ilişkileri': 'is_insani',
  'çevre mühendisliği': 'insaat',
  'çini tasarimi ve onarimi': 'ressam',
  'çizgi film ve animasyon': 'tasarimci',
  'çocuk gelişimi': 'okuloncesi',
  'özel eğitim öğretmenliği': 'ogretmen',
  'şehir ve bölge planlama': 'mimar',
}

// Meslek kuralları SIRAYLA denenir; özel olan önce, genel olan sonra gelir.
const MESLEK_KURALLARI = [
  // ---- 1) Özel durumlar (sıra önemli: daha belirgin olan önce)
  ['psikolog', ['psikolog', 'psikoterap', 'psikolojik', 'sosyal hizmet', 'kriz', 'rehberlik danışman', 'davranış bilim', 'aile danışman', 'evlilik danışman', 'sosyal pedagog', 'sosyal yardım danışman', 'çocuk refahı', 'eğitim refah']],
  ['cevirmen', ['çevirmen', 'tercüman', 'yerelleştirici', 'işaret dili', 'altyazı', 'kültürlerarası iletişim']],
  // tek tek kontrol sonrası düzeltmeler (2026-10-04)
  ['ciftci', ['ormancılık ve balıkçılık', 'bağcılık']],
  ['insaat', ['sağlık güvenliği ve çevre', 'sağlık ve güvenlik görevli']],
  ['paramedik', ['kurtarma merkezi']],
  ['sporcu', ['teknik direktör']],
  ['balikci', ['deniz biyolo']],
  ['lojistikci', ['demiryolu lojistik']],
  ['ogretmen', ['hapishane eğitmen', 'kurumsal antrenör']],
  ['psikolog', ['topluluk geliştirme']],
  ['is_insani', ['sivil toplum', 'yetenek satın']],
  ['makine', ['silah ustası', 'ürün geliştirme teknik ressam', 'malzeme gerilme', 'malzeme stres']],
  ['dansci', ['koreolog']],
  ['kutuphaneci', ['soybilim']],
  ['yazar', ['teknik iletişimci']],
  ['finansci', ['yatırım bankacı', 'yatırım danışman', 'yatırım yönetici', 'menkul kıymet komisyon']],
  ['diplomat', ['kamu planlama']],
  ['ressam', ['maket']],
  ['insaat', ['ulaştırma mühendis']],
  ['sahne', ['gösteri', 'sahne ışık', 'sahne video']],
  ['elektrik', ['batarya']],
  ['gazeteci', ['hitabet']],
  ['doktor', ['medikal fizik', 'tıbbi kodlama']],
  ['yazilimci', ['veri ambarı', 'kurumsal bt']],
  ['veteriner', ['at diş']],
  ['kaptan', ['tekne', 'gemi trafik']],
  ['finansci', ['maliye']],
  ['dansci', ['dansçı', 'dans ', 'bale', 'balerin', 'koreograf', 'halk oyunları', 'dans repetit', 'dans rptiteur']],
  ['muzisyen', ['müzik terap', 'müzik öğretmen', 'müzik eğitmen', 'konservatuvar', 'koro şef', 'müzik şef', 'elektronik müzik']],
  ['sporcu', ['beden eğitimi']],
  ['sahne', ['oyuncu', ' aktör', 'aktris', 'tiyatro eğitmen', 'drama öğretmen', 'sahne uçuş', 'mekan programcı', 'mekân programcı', 'açık hava animatör']],
  ['ressam', ['görsel sanatlar öğretmen', 'sanat öğretmen', 'güzel sanatlar eğitmen', 'sanat terapist', 'model yapımcı']],
  ['fotografci', ['fotoğraf', 'foto muhabir', 'film banyo']],
  ['okuloncesi', ['okul öncesi', 'ilk yıllar', 'çocuk bakım', 'çocuk yuvası', 'bebek bakıcı', 'kreş', 'çocuk gelişim']],
  ['ciftci', ['tarım, ormancılık']],
  ['balikci', ['su ürünleri', 'balık']],
  ['veteriner', ['veteriner', 'equine', 'hayvanat bahçesi', 'hayvan terapist', 'hayvan tımar', 'evcil hayvan', 'hayvan eğitmen', 'hayvan fizyoterap', 'hayvan osteopat']],
  ['kaptan', ['gemi pilot']],
  ['petrol', ['petrol', 'sondaj', 'doğalgaz', 'doğal gaz', 'rafineri', 'sıvı yakıt']],
  ['madenci', [ 'maden', 'mayın', 'cevher', 'mineral işleme', 'tahlil'], ['ithalat', 'jeolog', 'mücevher']],
  ['insaat', ['iş sağlığı']],
  ['bilimci', ['gıda analist']],
  ['makine', ['tasarım mühendis', 'tipetter', 'baskı makine', 'flekso', 'fleksografik', 'ofset']],
  ['otomotiv', ['motor tasarım', 'araç döşeme', 'otomotiv', 'motorlu taşıt', 'motorlu araç', 'powertrain', 'güç aktarma']],
  ['diyetisyen', ['diyetisyen', 'diyetetik', 'kilo kaybı', 'kilo yönetimi', 'beslenme uzman'], ['hayvan']],
  ['doktor', ['sitoteknolo', 'sağlığ', 'sağlık ve güvenlik']],
  ['siber', ['siber', 'bt güvenlik', 'ict güvenlik', 'bilgi güvenliği', 'etik hacker', 'adli bilişim', 'dijital adli']],
  ['oyun', [' oyun', 'oyunları']],
  ['yazilimci', ['bilgi işlem', 'gömülü sistem', 'veri deposu', 'teknoloji şef', 'kurumsal mimar', 'girişim mimar']],
  ['mimar', ['iç tasarımcı']],
  ['bahcivan', ['iç peyzaj', 'bahçıvan', 'botanik bahçe', 'çiçek', 'fidan', 'sera ']],
  ['otelci', ['ev hizmetçi', 'otel', 'pansiyon', 'konaklama', 'misafirperverlik', 'konsiyerj', 'concierge', 'oda ve kahvaltı', 'kat hizmet', 'garson', 'resepsiyon', 'konukseverlik', 'odalar bölüm']],
  ['is_insani', ['iş değeri', 'özel ilgi grup', 'gayrimenkul', 'işletme meslek']],
  ['gazeteci', ['genel yayın', 'yayın haber']],
  ['yazar', ['kitap yayıncı']],
  // ---- 2) Öğretmenler (meslek liselerindeki öğretmenler alanının kıyafetini alır)
  ['ogretmen', ['öğretmen', 'öğretim tasarım', 'okuryazarlık'], ['meslek öğretmen', 'eczacılık öğretmen']],
  // ---- 3) Genel kurallar
  ['dis', ['diş hekim', 'diş hijyen', 'diş teknisyen', 'diş protez', 'ağız ve diş']],
  ['eczaci', ['eczacı', 'ilaç']],
  ['kuafor', ['kuaför', 'berber', 'manikür', 'güzellik', 'solaryum', 'makyaj', 'cilt bakım', 'estetisyen']],
  ['yazilimci', ['yazılım', 'veritabanı geliştirici', 'programcı', 'veritabanı', 'yapay zeka', 'bilgisayar', ' ict ', ' bt ', ' web', 'uygulama mühendis', 'entegrasyon mühendis', 'teknoloji direktör', 'klinik kodlayıcı', ' iot', 'nesnelerin', 'sistem analist', 'e-öğrenme']],
  ['analist', ['analist', 'istatistik', 'veri bilim', 'veri mühendis', 'aktüer', 'ekonomist', 'ekonometri', 'matematik', 'biyoinformatik', 'hesaplama', 'fiyatlandırma', 'trader', 'hisse', 'döviz', 'yatırım', 'kıymet']],
  ['hukuk', ['avukat', 'hakim', 'savcı', 'hukuk', 'noter', 'arabulucu', 'ombudsman']],
  ['dedektif', ['dedektif', 'kriminolog', 'suç ', 'adli', 'poligraf', 'grafolog']],
  ['polis', ['polis', 'ıslah', 'denetimli serbestlik', 'güvenlik görevli', 'bekçi', 'jandarma']],
  ['astronot', ['astronot', 'astronom', 'kozmolog', 'uzay', 'uydu']],
  ['kabin', ['hostes', 'kabin', 'uçuş görevli']],
  ['pilot', ['pilot', 'hava trafik', 'havacılık', 'havaalanı', 'havalimanı', 'uçak', 'uçuş', 'aviyonik', 'apron']],
  ['paramedik', ['acil müdahale', 'acil durum müdahale', 'paramedik', 'ilk yardım', 'itfaiye', 'acil tıp']],
  ['fizyoterapist', ['fizyoterap', 'ergoterap', 'meslek terapist', 'rehabilitasyon', 'kineziyolog', 'kiropraktör', 'chiropractor', 'osteopat', 'shiatsu', 'rekreasyon terapist', 'rekreasyonel terapist', 'spor terapist']],
  ['hemsire', ['hemşire', ' ebe ', 'ebelik', 'doğum destek', 'bakım personel', 'bakım işçi', 'bakım çalışan', 'evde bakım', 'bakım yardımcı', 'ameliyat asistan', 'sağlık asistan', 'huzurevi', 'yaşlı ev']],
  ['doktor', ['hekim', 'doktor', 'cerrah', 'odyolog', 'paramedik', 'sağlık', 'anestezi', 'perfüzyon', 'radyograf', 'optometrist', 'optikçi', 'ortopedi', 'protez', 'ortez', 'prosthetist', 'solunum', 'konuşma ve dil', 'terapist', 'klinik', 'tıbbi', 'tıp ', 'fizyolog', 'bitkisel terapist', 'pratisyen']],
  ['sef', ['şef', 'aşçı', 'pasta', 'mutfak', 'restoran', 'gıda hizmet', 'kasap', 'kesimci', 'helal', 'barista', 'servis']],
  ['arkeolog', ['arkeolog', 'antropolog', 'paleontolog', 'kazı']],
  ['kutuphaneci', ['kütüphane', 'arşiv', 'müze', 'sergi', 'koleksiyon', 'küratör', 'kitap restoratör'], ['botanik']],
  ['jeolog', ['jeolog', 'jeoloji', 'jeofizik', 'mineralog', 'mineralojist', 'sismolog', 'volkanolog']],
  ['haritaci', ['harita', 'kadastro', 'coğrafi bilgi', 'uzaktan algılama', 'topograf', 'jeodezi', 'fotogrametri', 'coğrafyacı', 'arazi ölçüm']],
  ['yazar', ['yazar', 'editör', 'edebiyat', 'eleştirmen', 'şair', 'kopya düzenleyici', 'redaktör', 'doğruluk kontrol', 'gerçek denetleyici', 'kitap yayıncı'], ['söz yazar', 'metin yazar', 'senaryo', 'haber', 'film', 'video', ' ses ', 'öğretim', 'yayın']],
  ['akademisyen', ['öğretim görevlisi', 'öğretim üyesi', 'araştırmacı', 'araştırma asistan', 'sosyolog', 'tarihçi', 'filozof', 'dilbilimci', 'dil mühendis', 'soybilim', 'siyaset bilim', 'iletişim bilim', 'medya bilim', 'halkbilim', 'teolog', ' din ', ' dini', 'koreolog']],
  ['bilimci', ['kimya', 'biyolog', 'biyoloji', 'fizik', 'genetik', 'mikrobiyolog', 'biyokimya', 'laboratuvar', 'toksikolog', 'zooloji', 'botanik teknisyen', 'botanikçi', 'zoolog', 'meteorolog', 'meteoroloji', 'klimatolog', 'hava tahmin', 'çevre bilim', 'çevre uzman', 'koruma bilim', 'duyu', 'duyusal', 'gıda', 'biyomühendis', 'biyomedikal', 'nanomühendis', 'bilim adam', 'bilim insan', 'bilimci', 'bilgin', 'klinik deneme']],
  ['kaptan', ['kaptan', 'denizci', 'gemi', 'güverte', 'deniz ', 'liman', 'su trafik', 'filo komutan']],
  ['mimar', ['mimar', 'iç mekân', 'iç mekan', 'iç planlayıcı', 'şehir planla', 'arazi kullanım', 'peyzaj tasarım', 'kentsel', 'akıllı şehir']],
  ['insaat', ['inşaat', 'jeoteknik', 'geoteknik', 'petrol', 'hidrolog', 'yeraltı', 'su mühendis', 'su sistemleri', 'su koruma', 'çevre mühendis', 'ray döşeme', 'ray tabakası', 'sulama', 'kurtarma', 'ulaşım planla', 'trafik']],
  ['elektrik', ['elektrik', 'elektronik', 'enerji', 'nükleer', 'otomasyon', 'robot', 'fotonik', 'optik mühendis', 'santral', 'mikrosistem', 'mikroelektronik', 'elektrolitik', 'güvenlik alarm', ' pil ', 'akıllı ev']],
  ['rehber', ['rehber', 'tur organizatör', 'turist', 'seyahat', 'turizm', 'hayatta kalma', 'kamp']],
  ['muzisyen', ['müzik', 'müzisyen', 'besteci', 'şarkıcı', 'koro', 'orkestra', 'çalgı', 'enstrüman', ' ses ', 'kayıt stüdyo', 'podcast', 'lirik', 'söz yazarı', 'aranjör', ' dj ']],
  ['modaci', ['moda', 'terzi', 'dressmaker', 'kostüm tasarım', 'ayakkabı tasarım', 'ayakkabı 3d', 'deri eşya tasarım', 'giyim cad kalıp', 'poz modeli']],
  ['sahne', ['sahne', 'tiyatro', 'komedyen', 'kukla', 'sirk', 'dramaturg', 'performans', 'maske yapım', 'kostüm', 'giydirici', 'varyete', 'dövüş', 'repetitör', 'etkinlik']],
  ['sporcu', ['spor', 'antrenör', 'atlet', 'fitness', 'futbol', 'rekreasyon', 'hakem', 'kondisyon', 'yüzme', 'basketbol', 'voleybol']],
  ['kuyumcu', ['kuyumcu', 'mücevher', 'takı', 'filigran', 'saat ve', 'pırlanta', 'elmas']],
  ['tekstilci', ['tekstil', 'dokuma', 'dokumasız', 'dokunmamış', 'giyim', ' deri', 'ayakkabı', 'apre', 'iplik', 'örme', 'konfeksiyon', 'renkçi', 'dokumacı', 'halı', 'nakış', 'örgü']],
  ['tasarimci', ['grafik', 'illüstratör', 'animatör', 'animasyon', 'dijital sanatçı', 'storyboard', '3d ', 'medya tasarım', 'endüstriyel tasarım', 'ürün tasarım', 'web tasarım', 'baskı öncesi', 'prepress', 'dijital yazıcı', 'tabela', 'işaret yapıcı', 'mobilya tasarım', 'görsel mal', 'set tasarım']],
  ['pazarlamaci', ['reklam', 'pazarlama', 'halkla ilişkiler', 'marka', 'e-ticaret', 'ebusiness', 'online satış', 'tanıtım']],
  ['yonetmen', ['film', 'video', 'sinema', 'kamera', 'görüntü', 'yönetmen', 'yapımcı', 'senaryo', 'post-prodüksiyon', 'kurgu']],
  ['gazeteci', ['gazeteci', 'muhabir', 'spiker', 'sunucu', 'yayın', 'haber', 'medya', 'iletişim', 'sesli betimleme', 'görsel-işitsel', 'konuşma koçu']],
  ['ressam', ['ressam', 'sanatçı', 'sanat', 'heykel', 'seramik', ' cam ', 'çini', 'hattat', 'minyatür', 'tezhip', 'ebru', 'oymacı', 'restoratör', 'konservatör', 'litograf', 'baskı', 'vitrin', 'dekoratif', 'el sanat', 'hasır', 'silah ustası', 'tasarım']],
  ['ormanci', ['orman', 'forester', 'korucu', 'doğa koruma', 'yaban']],
  ['bahcivan', ['bahçe', 'peyzaj']],
  ['ciftci', ['ziraat', 'tarım', 'çiftçi', 'bitki', 'tohum', 'toprak', 'hayvancılık', 'yetiştirici', 'kümes', 'civciv', 'sığır', 'süt', ' yem', 'arıcı', 'şerbetçiotu', 'meyve', 'sebze', 'ekin', 'tarla', 'haşere', 'hayvan yakalama', 'yakalayıcı', 'değirmen', 'miller', 'damıtım', 'yağlı tohum', 'hayvan yemi', 'kırsal', 'köpek']],
  ['ogretmen', ['eğitmen', 'eğitimci', 'headteacher', 'okul müdürü', 'öğrenme', 'mentor', 'eğitim', ' koç', 'pedagoji', 'çocuk', 'özel eğitim', 'okul', 'gönüllü', 'topluluk', 'toplum', 'gerontoloji']],
  ['metalurji', ['metalurji', 'metal', 'fırın', 'döküm', 'kaynakçı', 'kaynak operatör', 'çelik', 'malzeme mühendis', 'malzeme test']],
  ['endustri', ['endüstri mühendis', 'üretim mühendis', 'süreç mühendis', 'üretim planla', 'kalite', 'verimlilik', 'inovasyon mühendis', 'araştırma mühendis']],
  ['makine', ['makine', 'mekanik', 'motor', 'mekatronik', 'endüstri', 'imalat', 'malzeme', 'montaj', 'derleyici', 'birleştirici', 'teknik ressam', 'taslak', 'draftör', 'ürün geliştirme', 'kauçuk', 'plastik', 'polimer', 'tren', 'demiryolu', 'rolling', 'kurulum', 'sıvı yakıt', 'nakliye mühendis', 'metrolog', 'metroloji', 'ahşap', 'kalıp', 'tamirci', 'teknisyen', 'tekniker', 'operatör', 'işletmeci', 'amiri', 'süpervizör', 'usta', 'işçi', 'mühendis']],
  ['finansci', ['muhasebe', 'finans', 'bankacı', 'banka', 'vergi', 'mali ', 'denetçi', 'denetim', 'sigorta', 'kredi', 'broker', 'tüccar', 'kapitalist', 'değerleme', 'risk', 'ekonomi danışman', 'mülkiyet']],
  ['lojistikci', ['lojistik', 'tedarik', 'sevkiyat', 'sevkıyat', 'ithalat', 'ihracat', 'gümrük', 'depo', 'kargo', 'yük ', 'satın alma', 'dağıtım', 'yönlendirme operasyon']],
  ['diplomat', ['diplomat', 'büyükelçi', 'konsolos', 'dışişleri', 'uluslararası ilişkiler', 'belediye', 'vali', 'kamu', 'siyasi', 'politika', 'göçmenlik', 'hükümet', 'kalkınma', 'meclis', 'ekonomi politika']],
  ['pazarlamaci', ['satış', 'satıcı', 'perakende', 'ağ pazarlama', 'online']],
  ['is_insani', ['müdür', 'yönetici', 'girişim', 'danışman', 'insan kaynakları', 'yetenek', 'emlak', 'mülk', 'kiralama', 'iş geliştir', 'merkez bankası', 'koordinatör', 'sorumlu', 'görevli', 'memur', 'planlayıcı', 'uzman', 'direktör', 'başkan', 'müfettiş', 'kâtip', 'katip', 'asistan', 'lider', 'ticaret']],
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
  psikolog: ['İyi bir dinleyici olmak süper güçtür. 💚', 'Bugün birini yargılamadan sonuna kadar dinle.', 'Duyguları anlamak da bir bilim! 🧠'],
  cevirmen: ['Her dil yeni bir dünya demek! 🌍', 'Bugün 10 yeni kelime öğren, yarın 10 tane daha.', 'Çeviri sadece kelime değil, kültür taşır. 🗣️'],
  hemsire: ['Şefkat ve dikkat — hemşireliğin iki kanadı. 💙', 'Biyolojiye bugün 20 dakika ayıralım mı?'],
  fizyoterapist: ['Hareket en iyi ilaçtır! 🏋️', 'Anatomi çalışmak, insanı anlamanın ilk adımı.'],
  diyetisyen: ['Dengeli beslen, dengeli düşün! 🍎', 'Biyoloji ve kimya beslenmenin temelidir.'],
  paramedik: ['Hızlı düşün, sakin kal! 🚑', 'İlk yardım bilgisi herkesin süper gücü olabilir.'],
  finansci: ['Hesaplar tamam! 🧮 Küçük birikimler büyür.', 'Matematik pratiği finansın dilidir.'],
  pazarlamaci: ['Fikrini duyur! 📣', 'İyi pazarlamacı önce insanları dinler.'],
  lojistikci: ['Paketler yolda! 📦 Planlama her şeydir.', 'Bugünün işlerini sırala, en verimli rotayı bul.'],
  diplomat: ['Dünya bir masa, sen de oradasın! 🌍', 'Bir yabancı dil ve güncel bir haber — bugünün görevi.'],
  otelci: ['Hoş geldiniz! 🛎️ Misafirperverlik bir sanattır.', 'Güler yüz ve düzen, iyi hizmetin anahtarı.'],
  okuloncesi: ['Oyun, çocukların en ciddi işidir! 🧸', 'Sabır ve hayal gücü — en güzel öğretmen çantası.'],
  modaci: ['Mezuram boynumda! 📏 Bugün bir eskiz çiz.', 'Moda, kendini ifade etmenin bir yolu.'],
  fotografci: ['Gülümse, çekiyorum! 📸', 'Bugün ışığın en güzel olduğu anı yakala.'],
  tasarimci: ['Renkler hazır, fikirler hazır! 🎨', 'İyi tasarım sade ve anlaşılırdır.'],
  kuyumcu: ['Her detay bir mücevher! 💎', 'İnce el işi sabır ister — sen de sabırlısın.'],
  yonetmen: ['Kamera… motor… başla! 🎬', 'Her film iyi bir hikâyeyle başlar.'],
  yazar: ['Bugün bir sayfa yaz! ✒️', 'Çok okuyan iyi yazar.'],
  tekstilci: ['İplik iplik ilerliyoruz! 🧵', 'Kumaşı anlamak için kimya ve fizik de lazım.'],
  metalurji: ['Ateşte dövülen çelik gibi güçlüsün! 🔥', 'Malzemeyi anlamak için kimya şart.'],
  endustri: ['Süreçleri iyileştirelim! ⚙️', 'Bugünün planını yap, verimliliği ölç.'],
  otomotiv: ['Motorlar çalıştı! 🏎️', 'Fizik ve matematik, hızın formülüdür.'],
  ormanci: ['Bir fidan, bir gelecek! 🌲', 'Doğayı gözlemlemek en iyi derstir.'],
  balikci: ['Denizler bizim! 🐟', 'Su ürünleri biyolojiyle başlar.'],
  bahcivan: ['Çiçekler sabırla açar, sen de öyle! 🌷', 'Bugün bir bitkiyi sula, gelişimini izle.'],
  petrol: ['Enerji derinlerde! 🛢️', 'Jeoloji ve akışkanlar fiziği petrolcülüğün temelidir.'],
  madenci: ['Kafa lambası açık! ⛏️ Derinlerde hazineler var.', 'Yer bilimleri ve matematik — madenciliğin temeli.'],
  jeolog: ['Her taş bir hikâye anlatır! 🪨', 'Bugün çevrendeki bir kayaya dikkatle bak.'],
  haritaci: ['Ölçüyoruz, çiziyoruz! 🗺️', 'Geometri haritacının en iyi dostudur.'],
  arkeolog: ['Kazı başlasın! 🏺 Geçmiş seni bekliyor.', 'Tarih okumak bir zaman yolculuğudur.'],
  kutuphaneci: ['Kitaplar düzenli, bilgi yerinde! 📚', 'Bugün yeni bir kitaba başla.'],
  polis: ['Görev başında! 👮 Disiplin ve adalet.', 'Spor ve dikkat — iyi bir polisin iki silahı.'],
  kabin: ['Kemerlerinizi bağlayın! ✈️', 'Bir yabancı dil, bin yeni yolculuk.'],
  siber: ['Güvenlik duvarı aktif! 🛡️', 'Bugün bir güvenlik kavramını öğren.'],
  oyun: ['Yeni seviye açıldı! 🎮', 'Oyun yapmak hem kod hem hikâye ister.'],
  dansci: ['Ritme kapıl! 💃', 'Düzenli pratik, en güzel koreografi.'],
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
  if (yol === '/bolumler/tum') return 'Bir bölüme tıkla, örnek mesleklerine bak. Beğendiğini ☆ ile listene ekle! 🔍'
  if (yol === '/bolumler/karsilastir') return 'Aklındaki 2-3 bölümü yan yana koy, farkları gör. ⚖️'
  if (yol === '/bolumler/listem') return 'Listendeki bölümler burada. Rehber öğretmenin de görebilir. ⭐'
  if (yol.startsWith('/bolumler')) return 'Sana uygun bölümler burada! Beğendiğini ☆ ile listene ekle. 🌟'
  if (yol.startsWith('/profilim')) return 'Bu senin profilin: güçlü yönlerin ve gelişebileceğin alanlar. 🧭'
  if (yol === '/koclugu') return hedef ? `${hedef} hedefin için bugün yol haritandan bir adımı işaretle!` : 'Henüz hedefin yok. Önerilen bölümlerden birini seçmeye ne dersin?'
  if (yol === '/profil') return 'Profilini doldurursan seni daha iyi tanırım. 😊'
  if (biten === 0) return 'Hazırsan Değerlendirme\'den ilk katmana başlayalım!'
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
    case 'psikolog':
      return <>{govde('#FDF6E3')}<path d="M40 86 Q48 80 54 82 L58 124 Q48 126 37 122 Z M80 86 Q72 80 66 82 L62 124 Q72 126 83 122 Z" fill="#8FB9A8" /><path d="M54 82 Q60 88 66 82" stroke="#E8DCC4" strokeWidth="2" fill="none" /><circle cx="49" cy="104" r="1.4" fill="#5E8C7A" /><circle cx="49" cy="112" r="1.4" fill="#5E8C7A" /><path d="M70 101 c0-2 3-2 3 0 c0-2 3-2 3 0 c0 2-3 4-3 4 c0 0-3-2-3-4z" fill="#E76F51" /></>
    case 'cevirmen':
      return <>{govde('#264653')}<path d="M52 82 L60 98 L68 82 Z" fill="#E9F1F2" /><path d="M52 82 L58 100 M68 82 L62 100" stroke="#1B343D" strokeWidth="1.5" /><rect x="65" y="100" width="13" height="8" rx="1.5" fill="#FFFFFF" stroke="#E9C46A" /><rect x="67" y="102" width="9" height="1.6" fill="#264653" /><rect x="67" y="105" width="6" height="1.4" fill="#9CA3AF" /></>
    case 'akademisyen':
      return <>{govde('#7D5A50')}<path d="M52 82 L60 98 L68 82" fill="#F3E9DC" /><path d="M44 84 Q60 90 76 84 L74 90 Q60 96 46 90 Z" fill="#B5838D" /><rect x="70" y="102" width="7" height="7" rx="1" fill="#6A4A40" /></>
    case 'pilot':
      return <>{govde('#1D3557')}<path d="M52 82 L60 98 L68 82 Z" fill="#FFFFFF" /><path d="M58 85 L62 85 L61.5 97 L60 99 L58.5 97 Z" fill="#111" /><path d="M64 98 L76 96 L70 100 Z M64 98 L76 100 L70 102 Z" fill="#E9C46A" /><rect x="38" y="118" width="44" height="2" fill="#E9C46A" /></>
    case 'kaptan':
      return <>{govde('#FFFFFF', <path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill="none" stroke="#D1D5DB" />)}{[92, 102, 112].map((y) => <rect key={y} x="39" y={y} width="43" height="3" fill="#1D3557" />)}</>
    case 'astronot':
      return <>{govde('#F3F4F6', <path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill="none" stroke="#C9CDD3" />)}<rect x="50" y="94" width="20" height="13" rx="2.5" fill="#D1D5DB" /><circle cx="55" cy="100" r="2" fill="#E63946" /><circle cx="61" cy="100" r="2" fill="#2A9D8F" /><rect x="65" y="98" width="3" height="5" fill="#3A86FF" /><path d="M42 112 L78 112" stroke="#E76F51" strokeWidth="2" /></>
    case 'hemsire':
      return <>{govde('#8ECAE6')}<path d="M52 82 L60 95 L68 82" fill="#6FB1D3" /><rect x="64" y="99" width="10" height="8" rx="1.5" fill="#7DBBDA" /><rect x="66" y="96" width="1.6" height="7" fill="#E63946" /><rect x="69" y="96" width="1.6" height="7" fill="#1D3557" /></>
    case 'fizyoterapist':
      return <>{govde('#118AB2')}<path d="M50 82 L56 91 L60 85 L64 91 L70 82 Z" fill="#FFFFFF" /><line x1="60" y1="86" x2="60" y2="100" stroke="#0B6E8E" strokeWidth="1.4" /><circle cx="60" cy="93" r="1.2" fill="#FFFFFF" /><circle cx="60" cy="98" r="1.2" fill="#FFFFFF" /><path d="M64 104 L67 104 L69 100 L71 108 L73 104 L76 104" stroke="#06D6A0" strokeWidth="1.6" fill="none" /></>
    case 'diyetisyen':
      return <>{onluk('#80B918')}<path d="M68 96 Q72 90 76 96 Q72 100 68 96 Z" fill="#80B918" /></>
    case 'paramedik':
      return <>{govde('#D62828')}<rect x="38" y="104" width="45" height="3.5" fill="#FFD166" /><rect x="38" y="110" width="45" height="2" fill="#E5E7EB" /><rect x="64" y="88" width="11" height="11" rx="2" fill="#FFFFFF" /><rect x="68.4" y="89.5" width="2.2" height="8" fill="#D62828" /><rect x="65.5" y="92.4" width="8" height="2.2" fill="#D62828" /><line x1="60" y1="84" x2="60" y2="124" stroke="#A61E1E" strokeWidth="1.4" /></>
    case 'finansci':
      return <>{govde('#F8F9FA')}<path d="M42 86 L53 82 L60 100 L67 82 L78 86 L81 122 Q60 127 39 122 Z" fill="#495057" /><path d="M58 84 L62 84 L62.5 96 L60 99 L57.5 96 Z" fill="#1D3557" />{[104, 111, 118].map((y) => <circle key={y} cx="60" cy={y} r="1.3" fill="#ADB5BD" />)}<rect x="44" y="104" width="8" height="2" fill="#343A40" /></>
    case 'pazarlamaci':
      return <>{govde('#FFFFFF', <path d="M40 86 Q60 76 80 86 L83 122 Q60 128 37 122 Z" fill="none" stroke="#E5E7EB" />)}<path d="M40 86 Q48 80 53 82 L56 124 Q48 126 37 122 Z M80 86 Q72 80 67 82 L64 124 Q72 126 83 122 Z" fill="#E76F51" /><path d="M55 114 L59 108 L62 111 L66 104" stroke="#2A9D8F" strokeWidth="2" fill="none" strokeLinecap="round" /><path d="M63 104 L66 104 L66 107" stroke="#2A9D8F" strokeWidth="2" fill="none" strokeLinecap="round" /></>
    case 'lojistikci':
      return <>{govde('#6C757D')}<path d="M42 86 L53 82 L56 124 Q48 126 39 122 Z M78 86 L67 82 L64 124 Q72 126 81 122 Z" fill="#C9E265" /><rect x="40" y="104" width="16" height="3" fill="#F1F3F5" /><rect x="64" y="104" width="16" height="3" fill="#F1F3F5" /><rect x="40" y="112" width="16" height="3" fill="#F1F3F5" /><rect x="64" y="112" width="16" height="3" fill="#F1F3F5" /></>
    case 'diplomat':
      return <>{govde('#14213D')}<path d="M52 82 L60 100 L68 82 Z" fill="#FFFFFF" /><path d="M58 85 L62 85 L62.5 98 L60 101 L57.5 98 Z" fill="#457B9D" /><path d="M52 82 L58 102 M68 82 L62 102" stroke="#0B1428" strokeWidth="1.5" /><path d="M70 96 L76 96 L73 91 Z" fill="#FFFFFF" /><circle cx="48" cy="94" r="1.8" fill="#E9C46A" /></>
    case 'otelci':
      return <>{govde('#8D0801')}{[96, 104, 112].map((y) => <g key={y}><circle cx="54" cy={y} r="1.6" fill="#E9C46A" /><circle cx="66" cy={y} r="1.6" fill="#E9C46A" /></g>)}<path d="M54 84 L60 87 L54 90 Z M66 84 L60 87 L66 90 Z" fill="#111" /><circle cx="60" cy="87" r="1.5" fill="#111" /><rect x="37" y="118" width="46" height="2" fill="#E9C46A" /></>
    case 'okuloncesi':
      return <>{govde('#90E0EF')}<path d="M45 90 L75 90 L78 124 Q60 128 42 124 Z" fill="#FFB703" /><path d="M50 90 Q50 84 54 82 M70 90 Q70 84 66 82" stroke="#FFB703" strokeWidth="2.5" fill="none" /><rect x="50" y="104" width="20" height="10" rx="2" fill="#FB8500" /><circle cx="48" cy="96" r="1.8" fill="#E63946" /><circle cx="72" cy="97" r="1.8" fill="#3A86FF" /><circle cx="60" cy="96" r="1.8" fill="#2A9D8F" /></>
    case 'modaci':
      return <>{govde('#212529')}<rect x="51" y="79" width="18" height="7" rx="3.5" fill="#343A40" /><path d="M50 85 Q47 102 50 120" stroke="#FFD166" strokeWidth="3" fill="none" strokeDasharray="1.2 1.6" /><path d="M70 85 Q73 100 69 112" stroke="#FFD166" strokeWidth="3" fill="none" strokeDasharray="1.2 1.6" /><path d="M50 85 Q47 102 50 120" stroke="#E9B949" strokeWidth="3" fill="none" opacity=".35" /></>
    case 'fotografci':
      return <>{govde('#3A5A40')}<path d="M44 84 L76 120" stroke="#111" strokeWidth="3" /><path d="M54 82 Q60 88 66 82" stroke="#2F4A34" strokeWidth="3" fill="none" /></>
    case 'tasarimci':
      return <>{govde('#48CAE4')}<path d="M54 82 Q60 88 66 82" stroke="#2BA7C2" strokeWidth="3" fill="none" /><circle cx="54" cy="104" r="3.5" fill="#F72585" /><path d="M60 108 L64 100 L68 108 Z" fill="#FFD166" /><rect x="63" y="110" width="6" height="6" fill="#7209B7" /></>
    case 'kuyumcu':
      return <>{govde('#F8F9FA')}<path d="M42 86 L53 82 L60 100 L67 82 L78 86 L81 122 Q60 127 39 122 Z" fill="#5A189A" /><path d="M56 84 L60 87 L56 90 Z M64 84 L60 87 L64 90 Z" fill="#E9C46A" />{[104, 111, 118].map((y) => <circle key={y} cx="60" cy={y} r="1.3" fill="#E9C46A" />)}<path d="M70 106 L72 103 L76 103 L78 106 L74 111 Z" fill="#A2D2FF" /></>
    case 'yonetmen':
      return <>{govde('#22223B')}<path d="M48 84 Q60 94 72 84 L70 90 Q60 98 50 90 Z" fill="#C1121F" /><path d="M66 90 L70 112 L64 110 Z" fill="#C1121F" /></>
    case 'yazar':
      return <>{govde('#386641')}<path d="M46 84 Q60 94 74 84 L72 91 Q60 99 48 91 Z" fill="#F2E8CF" /><path d="M52 92 L48 116 L55 115 L56 94 Z" fill="#F2E8CF" />{[100, 106, 112].map((y) => <line key={y} x1="62" y1={y} x2="76" y2={y} stroke="#2F5535" strokeWidth="1" />)}</>
    case 'tekstilci':
      return <>{govde('#CDB4DB')}<path d="M45 92 L75 92 L78 124 Q60 128 42 124 Z" fill="#5E548E" /><path d="M50 92 Q50 84 54 82 M70 92 Q70 84 66 82" stroke="#5E548E" strokeWidth="2.5" fill="none" /><rect x="52" y="100" width="16" height="10" rx="1.5" fill="#4A4272" /><rect x="55" y="96" width="3" height="8" fill="#E63946" /><rect x="60" y="96" width="3" height="8" fill="#FFD166" /><rect x="65" y="97" width="2" height="7" fill="#ADB5BD" /></>
    case 'metalurji':
      return <>{govde('#ADB5BD')}<path d="M44 88 L52 84 L54 124 L42 122 Z" fill="#CED4DA" opacity=".7" /><rect x="38" y="104" width="45" height="3" fill="#FFB703" /><line x1="60" y1="84" x2="60" y2="124" stroke="#868E96" strokeWidth="1.5" /><rect x="64" y="90" width="10" height="7" rx="1.5" fill="#868E96" /></>
    case 'endustri':
      return <>{govde('#ADE8F4')}<path d="M52 82 L56 90 L60 84 L64 90 L68 82" fill="#FFFFFF" stroke="#7CC6DA" strokeWidth="1" /><path d="M58 85 L62 85 L62.5 98 L60 101 L57.5 98 Z" fill="#1D3557" /><g transform="translate(70 104)"><circle r="4" fill="#6C757D" /><circle r="1.6" fill="#ADE8F4" />{[0, 60, 120, 180, 240, 300].map((a) => <rect key={a} x="-1" y="-6" width="2" height="3" fill="#6C757D" transform={`rotate(${a})`} />)}</g></>
    case 'otomotiv':
      return <>{govde('#C1121F')}<line x1="60" y1="82" x2="60" y2="124" stroke="#8D0E17" strokeWidth="2" /><rect x="64" y="92" width="11" height="8" fill="#FFFFFF" /><path d="M64 92 h2.75 v4 h-2.75 Z M69.5 92 h2.75 v4 h-2.75 Z M66.75 96 h2.75 v4 h-2.75 Z M72.25 96 h2.75 v4 h-2.75 Z" fill="#111" /><rect x="37" y="114" width="46" height="4" fill="#111" /></>
    case 'ormanci':
      return <>{govde('#606C38')}<rect x="44" y="94" width="11" height="9" rx="1.5" fill="#4F5A2E" /><rect x="65" y="94" width="11" height="9" rx="1.5" fill="#4F5A2E" /><path d="M70.5 90 L74 96 L67 96 Z" fill="#E9C46A" /><path d="M52 82 L60 92 L68 82" fill="#DDA15E" /><rect x="38" y="116" width="45" height="4" fill="#3B3F22" /></>
    case 'balikci':
      return <>{govde('#FFD60A')}<line x1="60" y1="82" x2="60" y2="124" stroke="#E0B700" strokeWidth="2" />{[94, 104, 114].map((y) => <rect key={y} x="56" y={y} width="8" height="2.6" rx="1.3" fill="#8D6E00" />)}<rect x="66" y="108" width="11" height="9" rx="1.5" fill="#F2C500" /></>
    case 'bahcivan':
      return <>{govde('#FFAFCC')}<path d="M45 90 L75 90 L78 124 Q60 128 42 124 Z" fill="#52B788" /><path d="M50 90 Q50 84 54 82 M70 90 Q70 84 66 82" stroke="#52B788" strokeWidth="2.5" fill="none" /><rect x="50" y="104" width="20" height="10" rx="2" fill="#40916C" /><path d="M64 98 L64 106 M62 98 L66 98" stroke="#ADB5BD" strokeWidth="1.8" /></>
    case 'petrol':
      return <>{govde('#E85D04')}<line x1="60" y1="82" x2="60" y2="124" stroke="#B84A03" strokeWidth="2" /><rect x="38" y="104" width="45" height="3.5" fill="#F1F3F5" /><rect x="38" y="112" width="45" height="3.5" fill="#F1F3F5" /><path d="M70 88 Q74 94 74 96 Q74 99 70 99 Q66 99 66 96 Q66 94 70 88 Z" fill="#111" /></>
    case 'madenci':
      return <>{govde('#343A40')}<rect x="47" y="80" width="5" height="22" fill="#212529" /><rect x="68" y="80" width="5" height="22" fill="#212529" /><rect x="38" y="104" width="45" height="3.5" fill="#F48C06" /><rect x="38" y="112" width="45" height="2" fill="#DEE2E6" /></>
    case 'jeolog':
      return <>{govde('#5E7CE2')}<path d="M42 86 L53 82 L56 124 Q48 126 39 122 Z M78 86 L67 82 L64 124 Q72 126 81 122 Z" fill="#A98467" /><rect x="42" y="100" width="9" height="7" rx="1.2" fill="#8C6A50" /><rect x="69" y="100" width="9" height="7" rx="1.2" fill="#8C6A50" /><rect x="42" y="111" width="9" height="7" rx="1.2" fill="#8C6A50" /><rect x="69" y="111" width="9" height="7" rx="1.2" fill="#8C6A50" /></>
    case 'haritaci':
      return <>{govde('#E9ECEF')}<path d="M42 86 L53 82 L56 124 Q48 126 39 122 Z M78 86 L67 82 L64 124 Q72 126 81 122 Z" fill="#0077B6" /><rect x="40" y="106" width="16" height="2.5" fill="#FFD166" /><rect x="64" y="106" width="16" height="2.5" fill="#FFD166" /><path d="M66 92 L70 90 L74 92 L78 90 L78 98 L74 100 L70 98 L66 100 Z" fill="#FFFFFF" stroke="#005F8F" strokeWidth=".8" /></>
    case 'arkeolog':
      return <>{govde('#D4A373')}<rect x="44" y="94" width="11" height="9" rx="1.5" fill="#BC8A5F" /><rect x="65" y="94" width="11" height="9" rx="1.5" fill="#BC8A5F" /><path d="M52 82 L60 92 L68 82" fill="#FEFAE0" /><path d="M46 84 Q60 92 74 84" stroke="#E63946" strokeWidth="2.5" fill="none" /><rect x="38" y="116" width="45" height="4" fill="#7F5539" /></>
    case 'kutuphaneci':
      return <>{govde('#FEFAE0')}<path d="M40 86 Q48 80 54 82 L57 124 Q48 126 37 122 Z M80 86 Q72 80 66 82 L63 124 Q72 126 83 122 Z" fill="#B5838D" /><path d="M54 82 L60 90 L66 82" fill="#E5989B" />{[100, 108, 116].map((y) => <circle key={y} cx="52" cy={y} r="1.4" fill="#8E5E68" />)}</>
    case 'polis':
      return <>{govde('#1D3557')}<path d="M52 82 L60 96 L68 82 Z" fill="#A8DADC" /><path d="M58 85 L62 85 L61.5 95 L60 97 L58.5 95 Z" fill="#111" /><path d="M70 90 L71.5 93.5 L75 94 L72.5 96.5 L73 100 L70 98.3 L67 100 L67.5 96.5 L65 94 L68.5 93.5 Z" fill="#E9C46A" /><rect x="37" y="114" width="46" height="4" fill="#111" /><rect x="57" y="113.5" width="6" height="5" rx="1" fill="#C0C0C0" /><rect x="40" y="85" width="9" height="3" rx="1.5" fill="#0F1F35" /><rect x="71" y="85" width="9" height="3" rx="1.5" fill="#0F1F35" /></>
    case 'kabin':
      return <>{govde('#003566')}<path d="M50 82 L60 92 L70 82 Q60 86 50 82 Z" fill="#D90429" /><path d="M57 90 L54 100 L60 94 L66 100 L63 90 Z" fill="#D90429" /><path d="M64 98 L76 96 L70 100 Z M64 98 L76 100 L70 102 Z" fill="#E9C46A" />{[106, 114].map((y) => <circle key={y} cx="56" cy={y} r="1.3" fill="#E9C46A" />)}</>
    case 'siber':
      return <>{govde('#0B090A')}<path d="M60 96 L70 100 Q70 112 60 118 Q50 112 50 100 Z" fill="#06D6A0" /><rect x="56" y="104" width="8" height="7" rx="1" fill="#0B090A" /><path d="M57.5 104 Q57.5 100 60 100 Q62.5 100 62.5 104" stroke="#0B090A" strokeWidth="1.5" fill="none" /><line x1="56" y1="88" x2="55" y2="96" stroke="#495057" strokeWidth="1.5" /><line x1="64" y1="88" x2="65" y2="96" stroke="#495057" strokeWidth="1.5" /></>
    case 'oyun':
      return <>{govde('#7209B7')}<path d="M54 82 Q60 88 66 82" stroke="#560BAD" strokeWidth="3" fill="none" /><g fill="#4CC9F0">{[[56, 100], [64, 100], [52, 104], [56, 104], [60, 104], [64, 104], [68, 104], [52, 108], [60, 108], [68, 108], [56, 112], [64, 112]].map(([x, y]) => <rect key={`${x}-${y}`} x={x} y={y} width="4" height="4" />)}</g><rect x="57" y="104" width="2" height="2" fill="#7209B7" /><rect x="61" y="104" width="2" height="2" fill="#7209B7" /></>
    case 'dansci':
      return <>{govde('#F15BB5')}<path d="M48 84 Q60 92 72 84" stroke="#FEE440" strokeWidth="1.5" fill="none" />{[[50, 98], [66, 96], [58, 106], [70, 108], [52, 112], [62, 116]].map(([x, y]) => <path key={`${x}${y}`} d={`M${x} ${y - 2.4} L${x + 0.8} ${y - 0.8} L${x + 2.4} ${y} L${x + 0.8} ${y + 0.8} L${x} ${y + 2.4} L${x - 0.8} ${y + 0.8} L${x - 2.4} ${y} L${x - 0.8} ${y - 0.8} Z`} fill="#FEE440" />)}<path d="M38 116 Q60 124 82 116 L84 122 Q60 130 36 122 Z" fill="#9B5DE5" /></>
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
    case 'cevirmen':
      return <g><path d="M35 52 Q35 24 60 24 Q85 24 85 52" fill="none" stroke="#374151" strokeWidth="3" /><rect x="29" y="46" width="8" height="13" rx="3.5" fill="#2A9D8F" /><rect x="83" y="46" width="8" height="13" rx="3.5" fill="#2A9D8F" /><path d="M33 58 Q36 70 50 70" fill="none" stroke="#374151" strokeWidth="2" /><circle cx="51" cy="70" r="2.6" fill="#111827" /></g>
    case 'muzisyen':
      return <g fill="none" stroke="#2D2D2D" strokeWidth="4"><path d="M34 52 Q34 22 60 22 Q86 22 86 52" /><rect x="28" y="46" width="9" height="14" rx="4" fill="#6C4AB6" stroke="none" /><rect x="83" y="46" width="9" height="14" rx="4" fill="#6C4AB6" stroke="none" /></g>
    case 'hemsire':
      return <g><path d="M43 36 L47 22 Q60 18 73 22 L77 36 Q60 32 43 36 Z" fill="#FFFFFF" stroke="#D1D5DB" /><rect x="58.6" y="23" width="2.8" height="9" fill="#E63946" /><rect x="55.5" y="26.1" width="9" height="2.8" fill="#E63946" /></g>
    case 'lojistikci':
      return <g><path d="M36 38 Q38 20 60 20 Q82 20 84 38 Z" fill="#1D3557" /><path d="M36 38 Q26 38 20 43 L42 42 Z" fill="#14213D" /><circle cx="60" cy="21" r="2" fill="#14213D" /><rect x="52" y="27" width="16" height="6" rx="1" fill="#C9E265" /></g>
    case 'otelci':
      return <g transform="rotate(-8 60 28)"><rect x="47" y="20" width="26" height="13" rx="3" fill="#8D0801" /><rect x="47" y="30" width="26" height="3" fill="#E9C46A" /><ellipse cx="60" cy="20" rx="13" ry="3" fill="#A4161A" /></g>
    case 'yonetmen':
      return <g><ellipse cx="56" cy="30" rx="25" ry="9" fill="#111111" transform="rotate(-10 56 30)" /><circle cx="48" cy="21" r="2.5" fill="#111111" /></g>
    case 'metalurji':
      return <g><path d="M33 46 Q34 20 60 19 Q86 20 87 46 Z" fill="#6C757D" /><rect x="30" y="44" width="60" height="5" rx="2.5" fill="#495057" /><rect x="37" y="45" width="46" height="22" rx="7" fill="#F77F00" fillOpacity=".3" stroke="#495057" strokeWidth="1.5" /></g>
    case 'otomotiv':
      return <g><path d="M36 38 Q38 20 60 20 Q82 20 84 38 Z" fill="#C1121F" /><path d="M84 38 Q94 38 100 43 L78 42 Z" fill="#8D0E17" /><circle cx="60" cy="21" r="2" fill="#8D0E17" /><circle cx="60" cy="30" r="4" fill="#FFFFFF" /><path d="M58 30 L62 30 M60 28 L60 32" stroke="#C1121F" strokeWidth="1.4" /></g>
    case 'ormanci':
      return <g><ellipse cx="60" cy="34" rx="36" ry="6" fill="#7F5539" /><path d="M44 34 L49 17 Q55 21 60 15 Q65 21 71 17 L76 34 Z" fill="#9C6644" /><rect x="44" y="28" width="32" height="4" fill="#3B3F22" /></g>
    case 'balikci':
      return <g><path d="M34 40 Q36 20 60 20 Q84 20 86 40 Q93 44 96 50 L24 50 Q27 44 34 40 Z" fill="#FFC300" /><path d="M34 40 Q60 44 86 40" stroke="#E0A800" strokeWidth="1.5" fill="none" /></g>
    case 'bahcivan':
      return <g><ellipse cx="60" cy="34" rx="37" ry="7" fill="#F2E8CF" /><path d="M42 34 Q43 17 60 17 Q77 17 78 34 Z" fill="#F2E8CF" /><rect x="42" y="27" width="36" height="5" fill="#52B788" /><g transform="translate(73 27)">{[0, 72, 144, 216, 288].map((a) => <circle key={a} cx={3.2 * Math.cos((a * Math.PI) / 180)} cy={3.2 * Math.sin((a * Math.PI) / 180)} r="2.4" fill="#FF8FAB" />)}<circle r="1.8" fill="#FFD166" /></g></g>
    case 'petrol':
      return <g><path d="M33 44 Q34 20 60 19 Q86 20 87 44 Z" fill="#FFFFFF" stroke="#D1D5DB" /><rect x="29" y="42" width="62" height="6" rx="3" fill="#E9ECEF" stroke="#D1D5DB" /><path d="M60 24 Q65 31 65 34 Q65 38 60 38 Q55 38 55 34 Q55 31 60 24 Z" fill="#E85D04" /></g>
    case 'madenci':
      return <g><path d="M33 44 Q34 20 60 19 Q86 20 87 44 Z" fill="#F48C06" /><rect x="29" y="42" width="62" height="6" rx="3" fill="#DC6F00" /><rect x="53" y="24" width="14" height="10" rx="3" fill="#495057" /><circle cx="60" cy="29" r="4" fill="#FFF3B0" stroke="#343A40" /><path className="msk-isik" d="M64 26 L84 16 L84 40 L64 32 Z" fill="#FFF3B0" opacity=".35" /></g>
    case 'arkeolog':
      return <g><ellipse cx="60" cy="38" rx="35" ry="6" fill="#D6C08D" /><path d="M37 38 Q38 16 60 16 Q82 16 83 38 Z" fill="#E9D8A6" /><rect x="38" y="31" width="44" height="4" fill="#7F5539" /><path d="M60 16 L60 31" stroke="#D6C08D" strokeWidth="1.5" /></g>
    case 'polis':
      return <g><path d="M36 30 Q40 16 60 15 Q80 16 84 30 L80 36 L40 36 Z" fill="#1D3557" /><rect x="38" y="33" width="44" height="5" fill="#111" /><path d="M40 37 Q60 46 80 37 L78 41 Q60 47 42 41 Z" fill="#111" /><path d="M60 21 L62 25 L66 25.5 L63 28 L64 32 L60 30 L56 32 L57 28 L54 25.5 L58 25 Z" fill="#E9C46A" /></g>
    case 'kabin':
      return <g transform="rotate(-10 60 28)"><rect x="44" y="21" width="30" height="11" rx="3" fill="#003566" /><rect x="44" y="28" width="30" height="3" fill="#E9C46A" /><ellipse cx="59" cy="21" rx="15" ry="3" fill="#00284D" /></g>
    case 'oyun':
      return <g><path d="M35 52 Q35 24 60 24 Q85 24 85 52" fill="none" stroke="#2B2D42" strokeWidth="3.5" /><rect x="28" y="45" width="10" height="15" rx="4.5" fill="#4CC9F0" stroke="#2B2D42" strokeWidth="1.5" /><rect x="82" y="45" width="10" height="15" rx="4.5" fill="#4CC9F0" stroke="#2B2D42" strokeWidth="1.5" /><path d="M33 59 Q35 72 50 71" fill="none" stroke="#2B2D42" strokeWidth="2" /><circle cx="51" cy="71" r="2.4" fill="#F72585" /></g>
    case 'kuyumcu':
      return <g><path d="M77 56 Q88 52 86 42" stroke="#212529" strokeWidth="1.5" fill="none" /><circle cx="70" cy="56" r="7.5" fill="#BDE0FE" fillOpacity=".45" stroke="#212529" strokeWidth="2.6" /><circle cx="70" cy="56" r="3.6" fill="#2B2D42" opacity=".25" /></g>
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
    case 'psikolog': return <g><rect x="14" y="100" width="18" height="22" rx="2" fill="#F8F4EC" stroke="#8FB9A8" strokeWidth="1.5" /><line x1="17" y1="106" x2="29" y2="106" stroke="#B8C9C1" /><line x1="17" y1="110" x2="29" y2="110" stroke="#B8C9C1" /><line x1="17" y1="114" x2="26" y2="114" stroke="#B8C9C1" /><line x1="30" y1="96" x2="24" y2="116" stroke="#E76F51" strokeWidth="2" strokeLinecap="round" /><g transform="translate(92 70)"><path d="M0 0 h18 a4 4 0 0 1 4 4 v8 a4 4 0 0 1 -4 4 h-12 l-5 4 v-4 a4 4 0 0 1 -1 -3 z" fill="#FFFFFF" stroke="#8FB9A8" /><path d="M7 6 c0-2 3-2 3 0 c0-2 3-2 3 0 c0 2-3 4-3 4 c0 0-3-2-3-4z" fill="#E76F51" /></g></g>
    case 'cevirmen': return <g><g transform="translate(6 78)"><rect width="20" height="13" rx="4" fill="#E9C46A" /><path d="M14 13 L18 18 L10 13 Z" fill="#E9C46A" /><text x="10" y="9.5" fontSize="7" fontWeight="700" textAnchor="middle" fill="#264653" fontFamily="sans-serif">TR</text></g><g transform="translate(94 92)"><rect width="20" height="13" rx="4" fill="#2A9D8F" /><path d="M6 13 L2 18 L10 13 Z" fill="#2A9D8F" /><text x="10" y="9.5" fontSize="7" fontWeight="700" textAnchor="middle" fill="#FFFFFF" fontFamily="sans-serif">EN</text></g></g>
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
    case 'hemsire': return <g><rect x="14" y="104" width="22" height="16" rx="2.5" fill="#FFFFFF" stroke="#D1D5DB" /><rect x="21" y="100" width="8" height="5" rx="1.5" fill="none" stroke="#9CA3AF" strokeWidth="2" /><rect x="23.5" y="107" width="3" height="10" fill="#E63946" /><rect x="20" y="110.5" width="10" height="3" fill="#E63946" /></g>
    case 'fizyoterapist': return <g><rect x="15" y="110" width="22" height="3" rx="1.5" fill="#6C757D" /><rect x="12" y="104" width="5" height="15" rx="1.5" fill="#212529" /><rect x="35" y="104" width="5" height="15" rx="1.5" fill="#212529" /><rect x="9" y="106" width="3" height="11" rx="1" fill="#343A40" /><rect x="40" y="106" width="3" height="11" rx="1" fill="#343A40" /></g>
    case 'diyetisyen': return <g><path d="M24 104 Q17 101 16 110 Q16 120 24 121 Q32 120 32 110 Q31 101 24 104 Z" fill="#E63946" /><path d="M24 104 Q24 99 26 97" stroke="#6B4F3A" strokeWidth="1.6" fill="none" /><path d="M25 100 Q30 96 32 100 Q28 103 25 100 Z" fill="#80B918" /><ellipse cx="20" cy="108" rx="1.5" ry="2.5" fill="#FFFFFF" opacity=".5" /></g>
    case 'paramedik': return <g><rect x="12" y="106" width="26" height="16" rx="3" fill="#F77F00" /><rect x="20" y="102" width="10" height="5" rx="1.5" fill="none" stroke="#C25E00" strokeWidth="2" /><rect x="23.5" y="109" width="3" height="10" fill="#FFFFFF" /><rect x="20" y="112.5" width="10" height="3" fill="#FFFFFF" /></g>
    case 'finansci': return <g><rect x="15" y="98" width="19" height="24" rx="2.5" fill="#343A40" /><rect x="17.5" y="100.5" width="14" height="6" rx="1" fill="#B7E4C7" /><text x="30" y="105.5" fontSize="4.5" textAnchor="end" fill="#1B4332" fontFamily="monospace">1250</text>{[0, 1, 2].map((r) => [0, 1, 2].map((c) => <rect key={`${r}${c}`} x={18 + c * 4.6} y={109 + r * 4.2} width="3.4" height="3" rx=".8" fill={c === 2 && r === 2 ? '#F77F00' : '#ADB5BD'} />))}</g>
    case 'pazarlamaci': return <g><path d="M18 106 L34 98 L34 122 L18 114 Z" fill="#FFD166" stroke="#E0A800" /><rect x="12" y="105" width="7" height="10" rx="1.5" fill="#E76F51" /><path d="M20 115 L22 122" stroke="#6C757D" strokeWidth="2.2" strokeLinecap="round" /><path className="msk-kabarcik" d="M38 104 Q41 110 38 116" stroke="#E76F51" strokeWidth="1.5" fill="none" /></g>
    case 'lojistikci': return <g><rect x="11" y="104" width="26" height="19" rx="1.5" fill="#C8A27A" stroke="#9C7A54" /><rect x="22" y="104" width="4" height="19" fill="#E0C49F" /><path d="M15 112 L17.5 108 L20 112 M17.5 108 L17.5 116" stroke="#6E5236" strokeWidth="1.2" fill="none" /><rect x="29" y="115" width="6" height="5" fill="#FFFFFF" /></g>
    case 'diplomat': return <g><path d="M14 122 L34 122 M24 122 L24 118" stroke="#6E4527" strokeWidth="2.5" /><circle cx="24" cy="108" r="9" fill="#4EA8DE" /><path d="M18 104 Q21 101 24 104 Q22 108 19 107 Z M26 108 Q30 106 31 110 Q28 114 26 112 Z M20 112 Q23 112 22 115 Z" fill="#80B918" /><path d="M14 108 Q14 120 24 120" stroke="#E9C46A" strokeWidth="1.5" fill="none" /></g>
    case 'otelci': return <g><path d="M15 117 Q15 105 25 105 Q35 105 35 117 Z" fill="#E9C46A" stroke="#C9A227" /><rect x="12" y="117" width="26" height="3.5" rx="1.5" fill="#B08968" /><circle cx="25" cy="103" r="2" fill="#C9A227" /><path d="M19 110 Q21 107 24 107" stroke="#FFF3B0" strokeWidth="1.2" fill="none" /></g>
    case 'okuloncesi': return <g><rect x="12" y="110" width="12" height="12" rx="1.5" fill="#E63946" /><rect x="25" y="110" width="12" height="12" rx="1.5" fill="#3A86FF" /><rect x="18" y="97" width="12" height="12" rx="1.5" fill="#2A9D8F" /><text x="18" y="119" fontSize="8" fontWeight="700" textAnchor="middle" fill="#FFFFFF" fontFamily="sans-serif">A</text><text x="31" y="119" fontSize="8" fontWeight="700" textAnchor="middle" fill="#FFFFFF" fontFamily="sans-serif">B</text><text x="24" y="106" fontSize="8" fontWeight="700" textAnchor="middle" fill="#FFFFFF" fontFamily="sans-serif">C</text></g>
    case 'modaci': return <g><path d="M18 98 Q24 96 30 98 L31 104 Q28 108 30 114 Q24 117 18 114 Q20 108 17 104 Z" fill="#E9C46A" stroke="#B08968" /><line x1="24" y1="98" x2="24" y2="95" stroke="#6E4527" strokeWidth="2" /><line x1="24" y1="115" x2="24" y2="123" stroke="#6E4527" strokeWidth="2" /><path d="M18 124 L30 124" stroke="#6E4527" strokeWidth="2.5" strokeLinecap="round" /><path d="M17.5 106 Q24 109 30.5 106" stroke="#E76F51" strokeWidth="1.5" fill="none" /></g>
    case 'fotografci': return <g><rect x="12" y="103" width="26" height="17" rx="2.5" fill="#2B2D42" /><rect x="15" y="100" width="7" height="4" rx="1" fill="#2B2D42" /><circle cx="26" cy="111.5" r="6" fill="#495057" stroke="#ADB5BD" strokeWidth="1.5" /><circle cx="26" cy="111.5" r="3" fill="#90E0EF" /><circle cx="27" cy="110.5" r="1" fill="#FFFFFF" /><circle cx="34" cy="106" r="1.3" fill="#E63946" /></g>
    case 'tasarimci': return <g><rect x="11" y="100" width="26" height="20" rx="2.5" fill="#212529" /><rect x="13.5" y="102.5" width="21" height="15" rx="1" fill="#F8F9FA" /><path d="M15 114 Q20 104 25 112 T33 106" stroke="#F72585" strokeWidth="1.6" fill="none" /><circle cx="18" cy="106" r="1.6" fill="#FFD166" /><line x1="33" y1="96" x2="27" y2="108" stroke="#7209B7" strokeWidth="2.2" strokeLinecap="round" /></g>
    case 'kuyumcu': return <g><path d="M15 106 L20 100 L30 100 L35 106 L25 120 Z" fill="#A2D2FF" stroke="#5390D9" strokeWidth="1.2" /><path d="M15 106 L35 106 M20 100 L23 106 L25 120 M30 100 L27 106 L25 120" stroke="#5390D9" strokeWidth=".9" fill="none" /><path className="msk-kabarcik" d="M36 96 L37 99 L40 100 L37 101 L36 104 L35 101 L32 100 L35 99 Z" fill="#FFD166" /></g>
    case 'yonetmen': return <g><rect x="12" y="107" width="26" height="15" rx="1.5" fill="#212529" /><g transform="rotate(-18 12 106)"><rect x="12" y="101" width="26" height="5" fill="#F8F9FA" />{[0, 1, 2, 3].map((i) => <path key={i} d={`M${14 + i * 6} 101 L${17 + i * 6} 101 L${15 + i * 6} 106 L${12 + i * 6} 106 Z`} fill="#212529" />)}</g><line x1="15" y1="113" x2="35" y2="113" stroke="#F8F9FA" strokeWidth=".8" /><line x1="15" y1="117" x2="30" y2="117" stroke="#F8F9FA" strokeWidth=".8" /></g>
    case 'yazar': return <g><rect x="13" y="100" width="19" height="23" rx="1.5" fill="#FEFAE0" stroke="#D4C9A8" />{[105, 109, 113, 117].map((y) => <line key={y} x1="16" y1={y} x2="29" y2={y} stroke="#B8B08D" strokeWidth=".9" />)}<path d="M38 92 Q30 98 28 112 Q34 104 38 92 Z" fill="#577590" /><line x1="38" y1="92" x2="28" y2="114" stroke="#2B2D42" strokeWidth="1" /></g>
    case 'tekstilci': return <g><rect x="15" y="100" width="18" height="3.5" rx="1" fill="#B08968" /><rect x="15" y="118" width="18" height="3.5" rx="1" fill="#B08968" /><rect x="17" y="103" width="14" height="15" fill="#E63946" />{[106, 109, 112, 115].map((y) => <line key={y} x1="17" y1={y} x2="31" y2={y} stroke="#B5202C" strokeWidth=".8" />)}<path d="M31 108 Q38 110 36 120" stroke="#E63946" strokeWidth="1.2" fill="none" /><line x1="36" y1="114" x2="38" y2="126" stroke="#ADB5BD" strokeWidth="1.4" /></g>
    case 'metalurji': return <g><path d="M30 100 L18 116 M33 102 L22 118" stroke="#495057" strokeWidth="2.2" strokeLinecap="round" /><rect x="12" y="114" width="16" height="8" rx="1.5" fill="#FB8500" /><rect x="14" y="115.5" width="12" height="3" rx="1" fill="#FFD166" /><circle className="msk-kabarcik" cx="14" cy="110" r="1.4" fill="#FFB703" /><circle className="msk-kabarcik msk-gecikme" cx="22" cy="108" r="1.1" fill="#FFB703" /></g>
    case 'endustri': return <g><rect x="13" y="98" width="21" height="25" rx="2" fill="#B08968" /><rect x="15.5" y="101" width="16" height="20" fill="#FFFFFF" /><rect x="20" y="96" width="7" height="4" rx="1" fill="#9CA3AF" /><rect x="17" y="104" width="9" height="2.4" fill="#3A86FF" /><rect x="20" y="108" width="9" height="2.4" fill="#2A9D8F" /><rect x="23" y="112" width="7" height="2.4" fill="#F77F00" /><rect x="17" y="116" width="12" height="2.4" fill="#E63946" /></g>
    case 'otomotiv': return <g><circle cx="24" cy="112" r="10" fill="#212529" /><circle cx="24" cy="112" r="5" fill="#ADB5BD" />{[0, 72, 144, 216, 288].map((a) => <line key={a} x1="24" y1="112" x2={24 + 4.6 * Math.cos((a * Math.PI) / 180)} y2={112 + 4.6 * Math.sin((a * Math.PI) / 180)} stroke="#6C757D" strokeWidth="1.4" />)}<circle cx="24" cy="112" r="1.6" fill="#495057" /></g>
    case 'ormanci': return <g><rect x="22" y="116" width="5" height="6" fill="#7F5539" /><path d="M24.5 94 L33 106 L28 106 L35 116 L14 116 L21 106 L16 106 Z" fill="#2D6A4F" /><path d="M24.5 98 L29 105" stroke="#40916C" strokeWidth="1.2" /></g>
    case 'balikci': return <g><path d="M12 112 Q22 102 32 112 Q22 122 12 112 Z" fill="#4EA8DE" /><path d="M32 112 L40 106 L39 112 L40 118 Z" fill="#3A86C8" /><circle cx="17" cy="110.5" r="1.4" fill="#111" /><path d="M21 108 Q24 112 21 116" stroke="#3A86C8" strokeWidth="1" fill="none" /></g>
    case 'bahcivan': return <g><path d="M14 106 L32 106 L30 122 L16 122 Z" fill="#4EA8DE" /><path d="M32 109 L41 100" stroke="#4EA8DE" strokeWidth="3" strokeLinecap="round" /><circle cx="42" cy="99" r="2.4" fill="#3A86C8" /><path d="M16 106 Q23 96 30 106" stroke="#3A86C8" strokeWidth="2" fill="none" /><circle className="msk-kabarcik" cx="44" cy="103" r="1" fill="#90E0EF" /><circle className="msk-kabarcik msk-gecikme" cx="45" cy="106" r="1" fill="#90E0EF" /></g>
    case 'petrol': return <g><rect x="13" y="100" width="22" height="23" rx="2.5" fill="#1D4E89" /><rect x="13" y="106" width="22" height="2" fill="#163D6B" /><rect x="13" y="116" width="22" height="2" fill="#163D6B" /><ellipse cx="24" cy="100" rx="11" ry="2.5" fill="#2B6CB0" /><path d="M24 107 Q27 111 27 113 Q27 115.5 24 115.5 Q21 115.5 21 113 Q21 111 24 107 Z" fill="#111" /></g>
    case 'madenci': return <g><line x1="16" y1="124" x2="32" y2="98" stroke="#8B5E3C" strokeWidth="3" strokeLinecap="round" /><path d="M20 94 Q32 92 40 102 Q31 97 24 98 Z" fill="#6C757D" /><path d="M22 96 Q16 98 12 104 Q18 99 24 98 Z" fill="#6C757D" /></g>
    case 'jeolog': return <g><line x1="16" y1="122" x2="30" y2="102" stroke="#8B5E3C" strokeWidth="2.6" strokeLinecap="round" /><rect x="24" y="96" width="14" height="5" rx="1" fill="#495057" transform="rotate(35 31 98)" /><path d="M8 118 L13 112 L20 113 L22 120 L14 124 Z" fill="#9CA3AF" stroke="#6B7280" /><path d="M13 117 L15 113 L17 117 L15 121 Z" fill="#9D4EDD" /></g>
    case 'haritaci': return <g><path d="M24 104 L15 126 M24 104 L24 126 M24 104 L33 126" stroke="#6E4527" strokeWidth="1.8" /><rect x="18" y="96" width="12" height="8" rx="1.5" fill="#FFD166" stroke="#C9A227" /><circle cx="31" cy="100" r="2.4" fill="#495057" /><rect x="22" y="93" width="4" height="3" fill="#495057" /></g>
    case 'arkeolog': return <g><rect x="22" y="104" width="4" height="18" rx="1.5" fill="#8B5E3C" transform="rotate(-20 24 113)" /><path d="M24 96 L32 98 L29 106 L21 104 Z" fill="#E9C46A" transform="rotate(-20 26 101)" /><path d="M8 120 Q8 112 14 112 Q20 112 20 120 L18 124 L10 124 Z" fill="#C97B63" /><path d="M10 116 L18 116" stroke="#9C5A44" strokeWidth="1" /></g>
    case 'kutuphaneci': return <g><rect x="12" y="116" width="26" height="6" rx="1" fill="#E63946" /><rect x="14" y="110" width="22" height="6" rx="1" fill="#2A9D8F" /><rect x="13" y="104" width="24" height="6" rx="1" fill="#E9C46A" /><rect x="16" y="98" width="18" height="6" rx="1" fill="#577590" />{[101, 107, 113, 119].map((y) => <line key={y} x1="20" y1={y} x2="30" y2={y} stroke="#FFFFFF" strokeWidth=".8" opacity=".7" />)}</g>
    case 'polis': return <g><rect x="16" y="102" width="13" height="20" rx="2.5" fill="#212529" /><rect x="25" y="92" width="2.5" height="11" rx="1" fill="#212529" /><rect x="18.5" y="105" width="8" height="5" rx="1" fill="#06D6A0" />{[113, 117].map((y) => <line key={y} x1="19" y1={y} x2="26" y2={y} stroke="#6C757D" strokeWidth="1.2" />)}</g>
    case 'kabin': return <g><rect x="12" y="106" width="20" height="16" rx="3" fill="#D90429" /><rect x="14" y="110" width="16" height="2" fill="#A3021F" /><path d="M18 106 L18 98 L26 98 L26 106" stroke="#6C757D" strokeWidth="2" fill="none" /><circle cx="16" cy="123" r="2" fill="#212529" /><circle cx="28" cy="123" r="2" fill="#212529" /></g>
    case 'siber': return <g><path d="M18 106 L18 101 Q18 94 25 94 Q32 94 32 101 L32 106" stroke="#ADB5BD" strokeWidth="3" fill="none" /><rect x="14" y="105" width="22" height="17" rx="3" fill="#06D6A0" /><circle cx="25" cy="112" r="2.5" fill="#0B090A" /><rect x="24" y="113" width="2" height="5" fill="#0B090A" /></g>
    case 'oyun': return <g><path d="M12 108 Q12 102 18 102 L32 102 Q38 102 38 108 L38 114 Q38 122 32 120 L28 116 L22 116 L18 120 Q12 122 12 114 Z" fill="#2B2D42" /><path d="M16 109 L22 109 M19 106 L19 112" stroke="#ADB5BD" strokeWidth="2" /><circle cx="31" cy="107" r="1.6" fill="#F72585" /><circle cx="34" cy="110" r="1.6" fill="#4CC9F0" /><circle cx="28" cy="110" r="1.6" fill="#FEE440" /><circle cx="31" cy="113" r="1.6" fill="#06D6A0" /></g>
    case 'dansci': return <g><line x1="24" y1="100" x2="28" y2="120" stroke="#6C757D" strokeWidth="1.6" /><path className="msk-nota" d="M24 100 Q10 94 14 84 Q20 74 8 70 M24 100 Q36 90 30 80" stroke="#F15BB5" strokeWidth="2.4" fill="none" strokeLinecap="round" /></g>
    default: return null
  }
}

const KOL_RENK = {
  hukuk: '#1F1F24', dedektif: '#9C7A54', doktor: '#FFFFFF', dis: '#FFFFFF', eczaci: '#FFFFFF', veteriner: '#FFFFFF',
  bilimci: '#FFFFFF', yazilimci: '#3A3F58', analist: '#2A9D8F', elektrik: '#2F5D8A', makine: '#2F5D8A', insaat: '#9CA3AF', mimar: '#2B2B2B',
  ogretmen: '#C97B63', sef: '#FFFFFF', muzisyen: '#6C4AB6', sahne: '#9B2335', gazeteci: '#F1F1F1', ressam: '#E9C46A',
  sporcu: '#E63946', ciftci: '#E9EDC9', is_insani: '#2C3E50', akademisyen: '#7D5A50', pilot: '#1D3557', kaptan: '#FFFFFF',
  astronot: '#F3F4F6', gunluk: '#7FB069', kuafor: '#F4ACB7', rehber: '#F1FAEE', psikolog: '#8FB9A8', cevirmen: '#264653',
  hemsire: '#8ECAE6', fizyoterapist: '#118AB2', diyetisyen: '#FFFFFF', paramedik: '#D62828', finansci: '#F8F9FA', pazarlamaci: '#E76F51',
  lojistikci: '#6C757D', diplomat: '#14213D', otelci: '#8D0801', okuloncesi: '#90E0EF', modaci: '#212529', fotografci: '#3A5A40',
  tasarimci: '#48CAE4', kuyumcu: '#F8F9FA', yonetmen: '#22223B', yazar: '#386641', tekstilci: '#CDB4DB', metalurji: '#ADB5BD',
  endustri: '#ADE8F4', otomotiv: '#C1121F', ormanci: '#606C38', balikci: '#FFD60A', bahcivan: '#FFAFCC', madenci: '#343A40', petrol: '#E85D04',
  jeolog: '#5E7CE2', haritaci: '#E9ECEF', arkeolog: '#D4A373', kutuphaneci: '#B5838D', polis: '#1D3557', kabin: '#003566',
  siber: '#0B090A', oyun: '#7209B7', dansci: '#F15BB5',
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

// [2026-10-04] Filiz öğrenci ilerledikçe büyür: 1 Tohum → 2 Filiz → 3 Fidan → 4 Genç Ağaç → 5 Çiçek → 6 Ulu Çınar
function Filiz({ seviye }) {
  const sv = Math.max(1, Math.min(6, seviye || 2))
  if (sv === 1) {
    return (
      <g className="msk-filiz">
        <path d="M60 28 Q60 23 60 19" stroke="#4F772D" strokeWidth="2.2" fill="none" strokeLinecap="round" />
        <path d="M60 21 Q54 15 50 20 Q55 24 60 21 Z" fill="#90A955" />
      </g>
    )
  }
  const boy = { 2: 10, 3: 4, 4: -2, 5: -4, 6: -6 }[sv]   // gövdenin tepe noktası (küçük = daha uzun)
  const altin = sv === 6
  return (
    <g className="msk-filiz">
      <path d={`M60 28 Q60 ${18 - (10 - boy) / 2} 60 ${boy}`} stroke={altin ? '#7A6A1F' : '#4F772D'} strokeWidth={sv >= 4 ? 3 : 2.5} fill="none" strokeLinecap="round" />
      <path d={`M60 ${boy + 4} Q50 ${boy - 6} 44 ${boy + 2} Q52 ${boy + 8} 60 ${boy + 4} Z`} fill={altin ? '#E9C46A' : '#90A955'} />
      <path d={`M60 ${boy + 2} Q70 ${boy - 10} 78 ${boy - 2} Q70 ${boy + 6} 60 ${boy + 2} Z`} fill={altin ? '#D4A72C' : '#6A994E'} />
      {sv >= 3 && <path d="M60 22 Q50 18 46 23 Q53 27 60 22 Z" fill={altin ? '#E9C46A' : '#A7C957'} />}
      {sv >= 4 && <path d="M60 18 Q69 13 74 18 Q67 22 60 18 Z" fill={altin ? '#D4A72C' : '#7FB069'} />}
      {sv >= 5 && (
        <g transform={`translate(60 ${boy - 1})`}>
          {[0, 72, 144, 216, 288].map((a) => (
            <ellipse key={a} cx={4.2 * Math.cos((a * Math.PI) / 180)} cy={4.2 * Math.sin((a * Math.PI) / 180)} rx="3.4" ry="2.4"
              transform={`rotate(${a} ${4.2 * Math.cos((a * Math.PI) / 180)} ${4.2 * Math.sin((a * Math.PI) / 180)})`} fill={altin ? '#FFD23F' : '#FF8FAB'} />
          ))}
          <circle r="2.6" fill={altin ? '#FB8500' : '#FFD166'} />
        </g>
      )}
      {altin && <path className="msk-parilti" d={`M74 ${boy - 6} l1.2 3 3 1.2 -3 1.2 -1.2 3 -1.2 -3 -3 -1.2 3 -1.2 Z`} fill="#FFD23F" />}
    </g>
  )
}

export function Karakter({ cinsiyet, kiyafet, gozGoz, kirp, uyku, konusuyor, seviye = 2 }) {
  const kolRenk = KOL_RENK[kiyafet] || '#7FB069'
  const elRenk = kiyafet === 'astronot' ? '#D1D5DB' : TEN
  const sacli = cinsiyet === 'erkek' || cinsiyet === 'kadin'
  const kafaRenk = sacli ? TEN : '#9BD18B'
  const gozluk = ['mimar', 'ogretmen', 'akademisyen', 'analist', 'finansci', 'endustri', 'yazar', 'kutuphaneci'].includes(kiyafet)
  const goggles = kiyafet === 'bilimci'
  const kapuson = kiyafet === 'yazilimci' || kiyafet === 'siber'
  const sapkaVar = !['hukuk', 'yazilimci', 'analist', 'kuafor', 'psikolog', 'gunluk', 'doktor', 'dis', 'eczaci', 'veteriner', 'bilimci', 'ogretmen', 'akademisyen', 'mimar', 'is_insani', 'gazeteci', 'sahne', 'astronot', 'fizyoterapist', 'diyetisyen', 'paramedik', 'finansci', 'pazarlamaci', 'diplomat', 'okuloncesi', 'modaci', 'fotografci', 'tasarimci', 'kuyumcu', 'yazar', 'tekstilci', 'endustri', 'jeolog', 'haritaci', 'kutuphaneci', 'siber', 'dansci'].includes(kiyafet)
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
        {kapuson && <path d="M44 84 Q60 70 76 84 Q60 78 44 84 Z" fill={kiyafet === 'siber' ? '#212529' : '#2A2E42'} />}
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
          <Filiz seviye={seviye} />
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
  const filizAcik = useModuller()('filiz')   // [2026-10-10] paket
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
  // [2026-10-10] 🔊 artık gerçek sesi açar / kapatır (varsayılan kapalı); konuşma balonları her zaman görünür
  const [sesAcik, setSesAcik] = useState(sesAcikMi)
  const [efektler, setEfektler] = useState([])
  const [haftalik, setHaftalik] = useState(null)
  const [sohbetAcik, setSohbetAcik] = useState(false)
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

  // [2026-10-04] haftalık görevler: ilk açılışta çekilir, görev tamamlanınca ana sayfadaki kart olay yayınlar
  useEffect(() => {
    api.haftalikGetir().then(setHaftalik).catch(() => {})
    const dinle = (e) => setHaftalik(e.detail)
    window.addEventListener('haftalik-guncellendi', dinle)
    return () => window.removeEventListener('haftalik-guncellendi', dinle)
  }, [])
  const seviye = haftalik?.seviye?.no || 1

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
    if (haftalik) {
      const kalan = haftalik.toplam - haftalik.tamamlanan
      if (kalan > 0) havuz.push(`Bu hafta ${kalan} görevin kaldı. Ana sayfada seni bekliyorlar! ✅`, `Bu haftanın görevlerinden biri: “${haftalik.gorevler.find((g) => g.durum !== 'tamamlandi')?.baslik}”`)
      if (haftalik.seri.guncel >= 2) havuz.push(`🔥 ${haftalik.seri.guncel} haftalık serin var, harika gidiyorsun!`)
      if (haftalik.seviye.sonraki_ad) havuz.push(`${haftalik.seviye.sonraki_ad} olmama ${haftalik.seviye.sonraki_esik - haftalik.seviye.puan} puan kaldı. Bana yardım eder misin? 🌱`)
    }
    mesajSirasi.current = (mesajSirasi.current + 1 + Math.floor(Math.random() * 3)) % havuz.length
    return havuz[mesajSirasi.current]
  }, [konum.pathname, ozet, hedef, kiyafet, ilkAd, haftalik])

  // sesli: true → cümle sesli okunur (yalnızca öğrencinin bir eylemine karşılık; ara ara gelen sözler sessizdir)
  const konus = useCallback((metin, sesli = false) => {
    if (kucuk || sohbetAcik) return
    setBalon(metin)
    if (sesli && sesAcik) soyle(metin)
  }, [kucuk, sohbetAcik, sesAcik])

  // [2026-10-04] sohbet paneli: Filiz yazarken düşünür, cevap gelince başını sallar
  useEffect(() => {
    const dinle = (e) => {
      const d = e.detail || {}
      setSohbetAcik(!!d.acik)
      if (d.acik) setBalon('')
      if (d.dusunuyor) setAnimasyon('dusun')
      else if (d.cevaplandi) oynat('onayla')
      else setAnimasyon((a) => (a === 'dusun' ? '' : a))
    }
    window.addEventListener('filiz-durum', dinle)
    return () => window.removeEventListener('filiz-durum', dinle)
  }, [oynat])

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
    const t2 = window.setTimeout(() => konus(ilkAd ? `Merhaba ${ilkAd}! Ben Filiz, gelişim koçun 🌱` : 'Merhaba! Ben Filiz, gelişim koçun 🌱'), 1100)
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
      window.setTimeout(() => { oynat('kutla'); efekt('kutla'); efektEkle('konfeti', 18); konus(`Bir katman daha bitti! ${biten}/${ozet.toplam_ana_katman_sayisi} 🎉`, true) }, 1800)
    }
    depoYaz('maskot_biten_katman', String(biten))
  }, [ozet]) // eslint-disable-line react-hooks/exhaustive-deps

  // seviye atlayınca ve haftanın görevleri bitince kutla
  const oncekiHaftalik = useRef(null)
  useEffect(() => {
    if (!haftalik) return
    const kayitli = Number(depoOku('maskot_seviye', '0'))
    if (kayitli > 0 && haftalik.seviye.no > kayitli) {
      window.setTimeout(() => { oynat('kutla'); efektEkle('yildiz', 14); efektEkle('konfeti', 18); efekt('kutla'); konus(`Büyüdüm! Artık bir ${haftalik.seviye.ad}'ım ${haftalik.seviye.ikon} Teşekkürler!`, true) }, 600)
    } else if (oncekiHaftalik.current && haftalik.tamamlanan > oncekiHaftalik.current.tamamlanan) {
      if (haftalik.tamamlanan === haftalik.toplam) { oynat('kutla'); efekt('kutla'); efektEkle('konfeti', 20); konus('Bu haftanın tüm görevleri tamam! 🎉 Pazartesi yenileri gelecek.', true) }
      else { oynat('zipla'); efekt('zipla'); efektEkle('kalp', 6); konus(haftalik.tamamlanan === haftalik.seri_esigi ? 'Bu haftaki serin güvende! 🔥' : 'Bir görev daha bitti, süpersin! ✅', true) }
    }
    depoYaz('maskot_seviye', String(haftalik.seviye.no))
    oncekiHaftalik.current = haftalik
  }, [haftalik]) // eslint-disable-line react-hooks/exhaustive-deps

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
      if (uyku) { setUyku(false); oynat('zipla'); efekt('uyan'); konus('Uyumuyordum, sadece gözlerimi dinlendiriyordum 😅') }
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
    efekt(secim === 'kutla' ? 'kutla' : secim === 'zipla' ? 'zipla' : secim === 'don' ? 'don' : 'kalp')
    konus(mesajSec(), true)
  }

  function kucukDegistir(v) { setKucuk(v); depoYaz('maskot_kucuk', v ? '1' : '0'); if (v) { setBalon(''); sus() } }
  async function sesDegistir() {
    const v = !sesAcik
    sesAyarla(v); setSesAcik(v)
    if (!v) { sus(); setBalon('Sesimi kapattım 🤫'); return }
    efekt('ac', true)
    const dogal = await dogalSesVarMi()
    const m = dogal ? (ilkAd ? `Merhaba ${ilkAd}! Artık beni duyabilirsin 🌱` : 'Artık beni duyabilirsin 🌱')
      : 'Bu cihazda doğal bir Türkçe ses bulamadım; robotik konuşmak yerine yalnızca küçük sesler çıkaracağım 🎵'
    setBalon(m)
    if (dogal) soyle(m)
  }

  if (kucuk) {
    return (
      <button className="msk-mini" onClick={() => { kucukDegistir(false); oynat('salla'); setTimeout(() => konus('Geri döndüm! 🌱'), 200) }} title="Filiz Gelişim Koçu'nu göster">
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
        <Karakter cinsiyet={cinsiyet} kiyafet={kiyafet} gozGoz={gozGoz} kirp={kirp} uyku={uyku} konusuyor={!!konusuyor} seviye={seviye} />
        {haftalik && <div className="msk-rozet" title={`${haftalik.seviye.ad} · ${haftalik.seviye.puan} puan`}>{haftalik.seviye.no}</div>}
        {animasyon === 'dusun' && <div className="msk-dusunce">💭</div>}
        {uyku && <div className="msk-zzz"><span>z</span><span>z</span><span>Z</span></div>}
        {efektler.map((e) => (
          <span key={e.id} className={`msk-efekt msk-${e.tur}`} style={{ left: `calc(50% + ${e.x}px)`, animationDelay: `${e.gecikme}ms`, color: e.renk, background: e.tur === 'konfeti' ? e.renk : undefined, '--dx': `${e.x * 1.6}px` }}>
            {e.tur === 'kalp' ? '❤' : e.tur === 'yildiz' ? '✦' : ''}
          </span>
        ))}
      </div>
      {!sohbetAcik && filizAcik && (
        <button className="msk-sor" onClick={() => window.dispatchEvent(new CustomEvent('filiz-ac'))} title="Filiz Gelişim Koçu ile sohbet et">💬 Bana sor</button>
      )}
      <div className="msk-araclar">
        <button onClick={sesDegistir} title={sesAcik ? 'Sesi kapat' : 'Sesi aç'} aria-pressed={sesAcik}>{sesAcik ? '🔊' : '🔇'}</button>
        <button onClick={() => kucukDegistir(true)} title="Küçült">–</button>
      </div>
    </div>
  )
}

const MASKOT_CSS = `
.msk-kap{position:absolute;top:14px;right:26px;width:92px;height:122px;z-index:60;user-select:none}
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
.msk-mini{position:absolute;top:18px;right:26px;width:42px;height:42px;z-index:60;box-shadow:0 4px 14px rgba(0,0,0,.12);animation:msk-filiz 2.6s ease-in-out infinite}
.msk-dusunce{position:absolute;top:-6px;left:-6px;font-size:20px;animation:msk-yuksel 2.2s ease-out}
.msk-sor{position:absolute;left:50%;transform:translateX(-50%);bottom:-24px;white-space:nowrap;border:1.5px solid var(--pu,#E8804A);background:var(--sur,#fff);color:var(--pu,#E8804A);border-radius:999px;padding:3px 10px;font-size:11px;font-weight:800;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,.08)}
.msk-sor:hover{background:var(--pu,#E8804A);color:#fff}
@media (max-width:768px){.msk-sor{display:none}}
.msk-rozet{position:absolute;left:2px;bottom:4px;width:18px;height:18px;border-radius:50%;background:var(--gr,#5E8A54);color:#fff;font-size:10.5px;font-weight:800;display:flex;align-items:center;justify-content:center;border:2px solid var(--sur,#fff);box-shadow:0 2px 6px rgba(0,0,0,.15)}
.msk-parilti{animation:msk-parilti 1.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
@keyframes msk-parilti{0%,100%{opacity:.3;transform:scale(.7)}50%{opacity:1;transform:scale(1.2)}}
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
@media (max-width: 760px){.msk-kap{position:absolute;width:64px;height:86px;top:8px;right:8px}.msk-mini{position:absolute;top:12px;right:14px}.msk-balon{right:70px;max-width:180px;font-size:11.5px}}
@media (prefers-reduced-motion: reduce){.msk-kap *{animation-duration:0s!important}}
`
