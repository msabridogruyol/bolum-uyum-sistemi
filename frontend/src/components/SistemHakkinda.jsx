// [2026-10-10] Sistem Hakkında + Sıkça Sorulan Sorular — teknik olmayan, kullanıcıya yönelik anlatım.
// hedef = 'ogrenci' (öğrenci menüsü) | 'yonetim' (okul yetkilisi / süper admin)
import { useEffect, useMemo, useState } from 'react'
import DilBilgisi from './DilBilgisi'   // [2026-10-12] dil desteği ve çeviri uyarısı
import Gelistirici from './Gelistirici'   // [2026-10-11]
import { api } from '../api/client'

const OGRENCI = {
  baslik: 'Sistem Hakkında',
  giris: 'Filizyol bir kariyer koçluğu sistemidir. Sana en uygun üniversite bölümlerini ve meslekleri keşfetmene yardım eder. Seni bir sınavla ölçmez. Kim olduğunu, neyi sevdiğini ve nasıl çalışmayı sevdiğini anlamaya çalışır. Sonra bunu bölümlerin istedikleriyle karşılaştırır.',
  adimlar: [
    { ikon: '📝', baslik: 'Değerlendirme', metin: 'Dört bölüm soru cevaplarsın: değerlerin, kişiliğin, sevdiğin iş ortamı ve ilgi alanların. Gerekirse beşinci bölümde seçtiğin alanı daha derinden incelersin.' },
    { ikon: '🧭', baslik: 'Profilim ve Bölümler', metin: 'Güçlü yönlerini ve sana en uygun bölümleri görürsün. Her bölümün yanında uyum yüzdesi yazar. Bölümde neler okutulduğuna ve hangi üniversitelerde olduğuna bakabilirsin.' },
    { ikon: '🎯', baslik: 'Hedef ve Koçluğum', metin: 'Bir hedef bölüm seçersin. Kendini bu bölümle karşılaştırırsın. Sonra sana özel yol haritasındaki adımları tamamlarsın.' },
    { ikon: '🌱', baslik: 'Gelişim', metin: 'Haftalık görevler, takvim, kulüp önerileri, kütüphanen, Filiz ve eğitim koçlarıyla yolculuğun devam eder.' },
    { ikon: '💼', baslik: 'İş hayatı', metin: 'Bölümlerin iş hayatını tanırsın: maaşlar, zor günler, CV ve mülakat. Mülakat Simülasyonu ile mesleğe ön bakış yapar, Düşünme Atölyesi\'nde her yerde işine yarayacak düşünme araçlarını denersin.' },
  ],
  bilmen: [
    'Doğru ya da yanlış cevap yoktur. En doğru sonuç, içinden geldiği gibi cevap verdiğinde çıkar.',
    'Sonuçlar sana yol gösterir. Son kararı sen, ailen ve öğretmenlerinle birlikte verirsin.',
    'Sistem sınav puanı tahmini yapmaz. Üniversitelerin taban puanları YÖK Atlas verilerinden alınır.',
    'Sonuçlarını ve kayıtlarını sen ve okulundaki yetkili öğretmenler görür. Diğer öğrenciler göremez.',
  ],
  sss: [
    ['Değerlendirme', 'Değerlendirmeyi tek seferde bitirmem gerekiyor mu?', 'Hayır. Her bölüm ayrıdır. Bir bölümü bitirip ara verebilirsin. Bir bölümün ortasında çıkarsan da cevapların kayıtlı kalır. Döndüğünde kaldığın yerden devam edersin.'],
    ['Değerlendirme', 'Doğru cevap var mı? Nasıl cevaplamalıyım?', 'Doğru cevap yoktur. "Olmak istediğin" kişiye göre değil, şu anki hâline göre cevap ver. Çok düşünme. İlk aklına gelen şık genellikle en doğru sonucu verir.'],
    ['Değerlendirme', 'Neden kamera izni isteniyor?', 'Kamera isteğe bağlıdır. Yalnızca Ayarlar → Gizlilik ve İzinler\'den izin verirsen açılır. Açarsan değerlendirme sırasında ara ara fotoğrafın çekilir. Böylece soruları senin cevapladığın doğrulanır. Video kaydı yapılmaz. Fotoğraflar en geç 6 ay içinde silinir. Kamerayı açmasan da puanın düşmez. Sekme değiştirmek ya da tam ekrandan çıkmak gibi durumlar ise "güven puanını" düşürür. Güven puanın çok düşerse sonuçların geçersiz sayılabilir.'],
    ['Değerlendirme', 'Değerlendirmeyi tekrar yapabilir miyim?', 'Evet. İlgi ve kişilik zamanla değişebilir. Değerlendirmeni tamamladıktan sonra belli bir süre geçince yeni bir tur açılır: 12. sınıftaysan ya da mezunsan daha sık, diğer sınıflarda daha seyrek; tarihini sol menüde "Sonraki tur" olarak görürsün. Önceki sonuçların silinmez, böylece kendindeki değişimi de izleyebilirsin. Daha erken gerekiyorsa okulundaki yetkili öğretmen yeni bir değerlendirme açabilir.'],
    ['Değerlendirme', 'Bazı cevaplarım tutarsız bulunursa ne olur?', 'Güven puanın eşiğin altında kalırsa sonuçların şimdilik ön bilgi sayılır. Beklemen gerekmez: yalnızca sorun çıkan bölümü sakin bir zamanda yeniden yanıtlarsın, diğer bölümlerin silinmez. Bitirdiğinde sonuçların ve önerilerin güncellenir.'],
    ['Sonuçlar', '"%85 uyum" ne demek?', 'Bir bölümün mezunları belli mesleklerde çalışır ve bu meslekler bazı özellikler ister. Sistem senin özelliklerini tüm bölümlerin beklentisiyle karşılaştırır ve bölümleri sana yakınlığına göre sıralar: 100 sana en yakın bölüm, 0 en uzak bölüm. Yani %85, o bölümün tüm bölümler içinde sana en yakınlardan biri olduğunu gösterir. Bu bir başarı tahmini değildir; "bu bölümü kazanırsın" anlamına gelmez.'],
    ['Sonuçlar', 'Güçlü, çok güçlü, gelişime açık ne anlama geliyor?', 'Her özellik 0–100 arasında, kendi profilindeki diğer özelliklerine göre (göreli) puanlanır; bir yetenek ya da zekâ ölçüsü değildir. "Çok güçlü" ve "güçlü", kendi profilinde öne çıkan yönlerin. "Gelişime açık" kendi profilinde geride kalan yönlerin: beceriler çalıştıkça gelişir, ilgiler denenerek keşfedilir; değerlerde ise yalnızca o şeyin senin için daha az önemli olduğunu gösterir. Gelişime açık olmak "kötü" demek değildir.'],
    ['Koçluk', '"Sen ve Bölümün" ekranındaki renkler ne anlama geliyor?', 'Bu ekran, özelliklerini hedef bölümünün beklediği düzeyle karşılaştırır. Yeşil: bölümün beklediği düzeydesin (uyumlu). Turuncu: bölümün beklediğinden biraz fazla ya da az. Kırmızı: fark büyük. Uyum puanı da böyle hesaplanır: bölümün beklentisine yakın olmak uyumu artırır, fazlası da azı da bir farktır. Fazlalık bir eksiklik değildir ama bu yönünü bölümde daha az kullanabilirsin. Değerlerde ise "senin için daha önemli / daha az önemli" yazar; bu bir üstünlük ya da eksik değil, karar verirken dikkate alacağın bir farktır.'],
    ['Sonuçlar', 'Sonuçlarım e-postama da gelir mi?', 'Evet. Değerlendirmenin son bölümünü bitirdiğinde (sana özel iş türü soruları açıldıysa onlar da dahil) hesabındaki e-posta adresine kısa bir sonuç e-postası gider. Okulunda öğrenci raporları açıksa sonuç raporun da PDF olarak eklenir. Bazı cevapların tutarsız bulunduysa e-posta, ilgili bölümü yeniden yanıtladıktan sonra gider. Gelmediyse istenmeyen (spam) klasörüne bak ya da rehber öğretmenine söyle; o yeniden gönderebilir.'],
    ['Sonuçlar', 'Raporlardaki "Kısaca" ve "Bunu yap / Bundan kaçın" bölümleri ne?', 'Sonuçlarındaki sayıların ne anlama geldiğini ve bu dönem neler yapabileceğini anlatan kısa yorumlardır. Profilim\'de, Raporlarım\'da ve PDF raporlarında görünür. Veli raporunda ailen için, öğretmen raporlarında öğretmenlerin için ayrı bir dille yazılır. Yorumlar sonuçlarına dayanan bir özettir, karar değildir; son kararı sen, ailen ve rehber öğretmeninle birlikte verirsin.'],
    ['Sonuçlar', 'Raporumu nasıl alabilirim?', 'Değerlendirmeni bitirince sol menüden Raporlarım sayfasını aç. Oradan üç şey indirebilirsin: kendi raporun, velin için hazırlanan rapor ve sonuçlarının Excel tablosu. Bu sayfayı menüde göremiyorsan rehber öğretmenine sor.'],
    ['Hedef ve koçluk', 'Hedef bölümümü değiştirebilir miyim?', 'Evet, belli sayıda değiştirme hakkın vardır. Hakkın biterse okulundaki yetkili öğretmen sana ek hak verebilir.'],
    ['Hedef ve koçluk', 'Yol haritasındaki adımları nasıl tamamlarım?', 'Her adımın altında ne yapacağın yazar. Bir de "Nasıl anlarsın?" kontrol listesi vardır. Başlayınca "Başladım"ı, bitirince "Yaptım"ı işaretle. İlerlemen Koçluğum sayfasında görünür.'],
    ['Hedef ve koçluk', 'Filiz kimdir?', 'Filiz, sorularını cevaplayan gelişim koçundur. Sonuçlarına, hedef bölümüne ve görevlerine göre sana yol gösterir. Ona bölümler, meslekler ve çalışma alışkanlıkları hakkında soru sorabilirsin. Önemli kararlarını yine de rehber öğretmeninle ve ailenle birlikte ver.'],
    ['Hedef ve koçluk', 'Eğitim koçuyla nasıl görüşürüm?', 'Eğitim Koçları sayfasından bir koç seçip görüşme talebi bırakırsın. Talebin Filizyol koordinatörüne gider. Görüşme planlanınca tarihini ve saatini hem o sayfada hem Takvim\'inde görürsün.'],
    ['İş hayatı', 'Mülakat Simülasyonu nedir?', 'İş Hayatı sayfasında seçtiğin bölüm için kısa bir iş görüşmesi canlandırılır. Mülakatçı o mesleğe özgü bir durum sorar, iki aday farklı cevap verir; sen daha iyi cevap verdiğini düşündüğün adayı seçersin. Sonra iki cevabın neden güçlü ya da zayıf olduğunu ve o meslekte işin nasıl yapıldığını görürsün. Bu bir sınav değildir: alanı bilmen gerekmez, adayların gerekçelerinden mantıkla seçebilirsin. Sonuçlarını yalnızca sen görürsün.'],
    ['İş hayatı', 'Düşünme Atölyesi nedir?', 'Okulda pek öğretilmeyen ama her derste ve meslekte işine yarayacak düşünme araçlarını yaparak öğrendiğin bölümdür: bir sorunun kök nedenini bulmak, birlikte değişen iki şeyin birbirine yol açıp açmadığını anlamak, bir işi adım adım tarif etmek, ikiye bölerek aramak, tercih verisini doğru okumak ve daha kalıcı öğrenmek. Her araç 5–7 dakika sürer: önce kendi bildiğin gibi denersin, sonra aracı öğrenir, okulda ve iş hayatında nasıl kullanıldığını görürsün. Puan verilmez.'],
    ['İş hayatı', '"Öğrenmeyi öğren" deneyinde ikinci ölçüm ne zaman açılır?', 'Deneyi bitirdikten en erken 12 saat sonra. Düşünme Atölyesi\'ni açtığında "İkinci ölçüm hazır" yazısını görürsün. Aynı kelimeleri hiç çalışmadan yeniden test eder, hangi yöntemin sende daha kalıcı olduğunu kendi sonucunda görürsün.'],
    ['İş hayatı', 'İş Hayatı sayfasını menüde göremiyorum.', 'Bu bölüm okulunun kullandığı pakete göre açılır. Menüde göremiyorsan okulunda henüz açık olmayabilir; rehber öğretmenine sorabilirsin.'],
    ['Diğer', 'Filizyol\'u başka bir dilde kullanabilir miyim?', 'Evet. Giriş ekranından ya da Ayarlar\'dan Türkçe dışında 12 dilden birini seçebilirsin; seçimin hesabına kaydedilir. Bazı uzun içerikler ilk açılışta birkaç saniye içinde çevrilir. PDF raporlar, e-postalar ve KVKK metinlerinin asılları Türkçedir.'],
    ['Diğer', 'Kulüp önerileri ve ilgi testi bölüm sonucumu etkiler mi?', 'Hayır. Kısa ilgi testi yalnızca sana uygun kulüpleri önermek içindir. Bölüm önerilerin değişmez.'],
    ['Diğer', 'Kütüphanem ne işe yarar?', 'Okuduğun kitapları, izlediğin belgeselleri, aldığın kursları ve katıldığın etkinlikleri burada toplarsın. Bu liste, kendini anlatman gerektiğinde çok işe yarar: rehber öğretmeninle görüşürken ya da ileride üniversite başvurularında.'],
    ['Diğer', 'Takvimde neler görünür?', 'Sınav ve tercih dönemleri gibi önemli tarihler, okulunun ve kulüplerinin etkinlikleri, eğitim koçu ve rehberlik görüşmelerin ve kendi eklediğin notlar.'],
    ['Hesap', 'Şifremi unuttum, ne yapmalıyım?', 'Giriş ekranındaki "Şifremi unuttum" bağlantısını kullan. Ya da okulundaki yetkili öğretmene söyle; o da şifreni sıfırlayabilir.'],
    ['Hesap', 'Bilgilerimi kimler görebilir?', 'Sonuçlarını, kütüphaneni ve diğer kayıtlarını sen ve okulundaki yetkili öğretmenler görür. Diğer öğrenciler bunları göremez. Yalnızca çevrim içiyken adın, soyadının baş harfi ve sınıfın okulundaki öğrencilerin "Çevrim içi" listesinde görünür; bunu Ayarlar\'dan kapatabilirsin. Haftalık görevlerdeki yansıtma cevaplarını yalnızca sen görürsün. Ayrıntılar Ayarlar\'daki Aydınlatma Metni\'nde.'],
  ],
}

const YONETIM = {
  baslik: 'Sistem Hakkında',
  giris: 'Filizyol, öğrencilerin kendilerini tanıyıp kendilerine uygun bölüm ve meslekleri keşfetmelerine yardım eden bir kariyer koçluğu sistemidir. Okul yetkilisi olarak öğrencilerinizin hesaplarını yönetir, ilerlemelerini izler, raporlar alır ve rehberlik çalışmalarınızı planlarsınız.',
  adimlar: [
    { ikon: '👥', baslik: 'Hesapları açın', metin: 'Öğrencileri Excel ile toplu yükleyin. Her öğrenci geçici şifreyle girer ve ilk girişte kendi şifresini belirler.' },
    { ikon: '📝', baslik: 'Değerlendirme', metin: 'Öğrenciler dört bölümlük değerlendirmeyi kendi hızlarında çözer. İlerlemeyi Özet ve Sınıflar sekmelerinden izlersiniz.' },
    { ikon: '📊', baslik: 'Sonuç ve rapor', metin: 'Her öğrencinin profilini, bölüm önerilerini ve güven puanını görür; öğrenci, veli, şube ve okul raporları alırsınız.' },
    { ikon: '🤝', baslik: 'Rehberlik', metin: 'Akran eşleştirme, şube dağılımı, kulüpler, eğitim koçları ve takvimle rehberlik çalışmalarınızı destekleyin.' },
  ],
  bilmen: [
    'Sonuçlar karar destek amaçlıdır; tek başına yönlendirme ya da yerleştirme kararı için kullanılmamalıdır.',
    'Öğrencilere ait veriler kişisel veridir; raporları yalnızca öğrenci, veli ve okulun yetkili personeliyle paylaşın.',
    'Güven puanı düşük sonuçlarda öğrenci yalnızca sorunlu bölümü yeniden yanıtlar; sonucu öğrenciyle konuşarak değerlendirin.',
    'Raporlardaki yorumlar ve "Ne yapılmalı?" önerileri raporun kendi verilerinden üretilir; rehberlik servisinizin okulun koşullarına göre uyarlaması önerilir.',
    'Yeni eğitim yılında Öğrenciler sekmesindeki "Sınıf atlat (yeni yıl)" ile bütün öğrencileri bir üst sınıfa geçirebilirsiniz; işlem 30 gün içinde geri alınabilir.',
  ],
  // [2026-10-11] SSS'in tek kaynağı sunucuda: backend/app/core/filiz_yonetim_rehber.py (YONETIM_SSS) — Filiz de aynı listeden
  // cevaplar. Sayfa açılınca GET /yonetim/filiz/sss ile yüklenir.
  sss: null,
}

export default function SistemHakkinda({ hedef = 'ogrenci' }) {
  const v = hedef === 'yonetim' ? YONETIM : OGRENCI
  const [ara, setAra] = useState('')
  const [acik, setAcik] = useState(null)
  const [uzakSss, setUzakSss] = useState(null)
  useEffect(() => {
    if (hedef !== 'yonetim') return
    api.filizYonetimSss().then((r) => setUzakSss(r.sss.map((x) => [x.grup, x.soru, x.cevap]))).catch(() => setUzakSss([]))
  }, [hedef])
  const sss = v.sss || uzakSss
  const gruplar = useMemo(() => {
    const q = ara.trim().toLocaleLowerCase('tr-TR')
    const m = new Map()
    ;(sss || []).forEach(([g, s, c], i) => {
      if (q && !`${s} ${c}`.toLocaleLowerCase('tr-TR').includes(q)) return
      if (!m.has(g)) m.set(g, [])
      m.get(g).push({ i, s, c })
    })
    return [...m.entries()]
  }, [sss, ara])

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">{v.baslik}</div>
        <div className="ps">{v.giris}</div>
      </div>
      <div className="sh-adimlar">
        {v.adimlar.map((a, i) => (
          <div key={a.baslik} className="sh-adim">
            <div className="sh-adim-no">{i + 1}</div>
            <div className="sh-adim-ikon">{a.ikon}</div>
            <b>{a.baslik}</b>
            <p>{a.metin}</p>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="ct">{hedef === 'yonetim' ? 'Bilmeniz gerekenler' : 'Bilmen gerekenler'}</div>
        <ul className="sh-bilgi">{v.bilmen.map((b) => <li key={b}>{b}</li>)}</ul>
      </div>
      <div className="card">
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
          <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>Sıkça sorulan sorular</div>
          <input className="yp-sec" style={{ minWidth: 220 }} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Soru ara…" />
        </div>
        {sss === null && <div className="bos-durum yukleniyor">Yükleniyor…</div>}
        {sss !== null && gruplar.length === 0 && <div className="bos-durum">{sss.length ? 'Aramana uygun soru bulunamadı.' : 'Sorular yüklenemedi.'}</div>}
        {gruplar.map(([g, liste]) => (
          <div key={g} className="sh-grup">
            <div className="sh-grup-ad">{g}</div>
            {liste.map(({ i, s, c }) => (
              <div key={i} className={`sh-soru${acik === i ? ' acik' : ''}`}>
                <button onClick={() => setAcik(acik === i ? null : i)} aria-expanded={acik === i}>
                  <span>{s}</span><span className="sh-ok">{acik === i ? '−' : '+'}</span>
                </button>
                {acik === i && <div className="sh-cevap">{c}</div>}
              </div>
            ))}
          </div>
        ))}
        <div className="yp-ince" style={{ marginTop: 12 }}>
          {hedef === 'yonetim' ? 'Sorunuzun cevabını bulamadıysanız sistem yöneticinizle iletişime geçin.' : 'Sorunun cevabını bulamadıysan Filiz\'e sorabilir ya da rehber öğretmenine danışabilirsin.'}
        </div>
      </div>
      <Gelistirici />
      <DilBilgisi />
    </div>
  )
}
