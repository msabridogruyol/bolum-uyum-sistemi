// [2026-10-10] Sistem Hakkında + Sıkça Sorulan Sorular — teknik olmayan, kullanıcıya yönelik anlatım.
// hedef = 'ogrenci' (öğrenci menüsü) | 'yonetim' (okul yetkilisi / süper admin)
import { useMemo, useState } from 'react'

const OGRENCI = {
  baslik: 'Sistem Hakkında',
  giris: 'Filizyol, sana en uygun üniversite bölümlerini ve meslekleri keşfetmen için hazırlanmış bir kariyer koçluğu sistemidir. Seni bir sınavla ölçmez; kim olduğunu, neyi sevdiğini ve nasıl çalışmaktan hoşlandığını anlamaya çalışır, sonra bunu bölümlerin gerektirdikleriyle karşılaştırır.',
  adimlar: [
    { ikon: '📝', baslik: 'Değerlendirme', metin: 'Dört bölümlük soruları çözersin: değerlerin, kişiliğin, sevdiğin iş ortamı ve ilgi alanların. Gerekirse beşinci bölümde seçtiğin alanı derinleştirirsin.' },
    { ikon: '🧭', baslik: 'Profilim ve Bölümler', metin: 'Güçlü yönlerini ve sana en uyumlu bölümleri yüzde uyumla görürsün. Her bölümün ne okuttuğunu, hangi üniversitelerde olduğunu inceleyebilirsin.' },
    { ikon: '🎯', baslik: 'Hedef ve Koçluğum', metin: 'Bir hedef bölüm seçersin. Kendinle bölümü karşılaştırır, sana özel yol haritasındaki adımları tamamlarsın.' },
    { ikon: '🌱', baslik: 'Gelişim', metin: 'Haftalık görevler, takvim, kulüp önerileri, kütüphanen, Filiz ve eğitim koçlarıyla yolculuğun devam eder.' },
  ],
  bilmen: [
    'Doğru ya da yanlış cevap yoktur. En doğru sonuç, içinden geldiği gibi cevap verdiğinde çıkar.',
    'Sonuçlar sana yol gösterir; son kararı sen, ailen ve öğretmenlerinle birlikte verirsin.',
    'Sistem sınav puanı tahmini yapmaz. Üniversite taban puanları YÖK Atlas verilerinden gösterilir.',
    'Bilgilerini yalnızca sen ve okulunun yetkili öğretmenleri görür.',
  ],
  sss: [
    ['Değerlendirme', 'Testi bir oturumda bitirmem gerekiyor mu?', 'Hayır. Her bölüm ayrıdır; bir bölümü bitirip ara verebilirsin. Bir bölümün ortasında çıkarsan verdiğin cevaplar kaydedilir ve döndüğünde kaldığın yerden devam edersin.'],
    ['Değerlendirme', 'Doğru cevap var mı? Nasıl cevaplamalıyım?', 'Doğru cevap yoktur. "Olmak istediğin" kişiye göre değil, şu anki hâline göre cevap ver. Çok düşünmeden, ilk aklına gelene göre seçmek genellikle en doğru sonucu verir.'],
    ['Değerlendirme', 'Neden kamera izni isteniyor?', 'Kamera yalnızca değerlendirme sırasında testi senin çözdüğünü doğrulamak içindir; görüntü kaydı yapılmaz, yalnızca zaman zaman kontrol amaçlı küçük bir fotoğraf alınabilir. Sekme değiştirmek, tam ekrandan çıkmak gibi durumlar "güven puanını" düşürür. Güven puanı çok düşerse sonuçların geçersiz sayılabilir.'],
    ['Değerlendirme', 'Testi tekrar çözebilir miyim?', 'Evet. İlgi ve kişilik zamanla değişebildiği için belli bir süre sonra yeni değerlendirme turu açılır. Tarihi sol menüde "Sonraki tur" olarak görürsün. Böylece kendindeki değişimi de izleyebilirsin.'],
    ['Sonuçlar', '"%85 uyum" ne demek?', 'Profilinin, o bölümde başarılı ve mutlu olan kişilerin özelliklerine ne kadar benzediğini gösterir. Bir başarı tahmini ya da "bu bölümü kazanırsın" anlamına gelmez.'],
    ['Sonuçlar', 'Güçlü, çok güçlü, gelişime açık ne anlama geliyor?', 'Her özellik 0–100 arasında puanlanır. "Çok güçlü" ve "güçlü" seni öne çıkaran yönlerin, "gelişime açık" ise üzerinde çalışarak ilerletebileceğin yönlerindir. Gelişime açık olmak "kötü" demek değildir.'],
    ['Sonuçlar', 'Raporumu nasıl alabilirim?', 'Raporlar okulun yetkili öğretmenleri tarafından hazırlanır. Sana ve velin için rapor istersen rehber öğretmenine başvurabilirsin.'],
    ['Hedef ve koçluk', 'Hedef bölümümü değiştirebilir miyim?', 'Evet, belirli sayıda değiştirme hakkın vardır. Hakkın biterse okulunun yetkili öğretmeni sana ek hak tanıyabilir.'],
    ['Hedef ve koçluk', 'Yol haritasındaki adımları nasıl tamamlarım?', 'Her adımın altında ne yapacağın ve "Nasıl anlarsın?" kontrol listesi vardır. Başladığında "Başladım"ı, bitirdiğinde "Tamamladım"ı işaretle. İlerlemen Koçluğum sayfasında görünür.'],
    ['Hedef ve koçluk', 'Filiz kimdir?', 'Filiz, sorularını yanıtlayan yapay zekâ koçundur. Bölümler, meslekler ve çalışma alışkanlıkları hakkında sohbet edebilirsin. Bazen yanılabilir; önemli kararlarda öğretmenlerine de danış.'],
    ['Hedef ve koçluk', 'Eğitim koçuyla nasıl görüşürüm?', 'Eğitim Koçları sayfasından bir koç seçip görüşme talebi bırakırsın. Talebin önce rehber öğretmenine gider; görüşme planlanınca tarih ve saati hem o sayfada hem Takvim\'inde görürsün.'],
    ['Diğer', 'Kulüp önerileri ve ilgi testi bölüm sonucumu etkiler mi?', 'Hayır. Kısa ilgi testi yalnızca sana uygun kulüpleri önermek içindir; bölüm önerilerin değişmez.'],
    ['Diğer', 'Kütüphanem ne işe yarar?', 'Okuduğun kitapları, izlediğin belgeselleri, aldığın kursları ve katıldığın etkinlikleri burada biriktirirsin. Rehber öğretmeninle görüşürken ve ileride üniversite başvurularında kendini anlatmak için çok işe yarar.'],
    ['Diğer', 'Takvimde neler görünür?', 'Sınav ve tercih dönemleri gibi önemli tarihler, okulunun etkinlikleri, eğitim koçu görüşmelerin ve kendi eklediğin notlar.'],
    ['Hesap', 'Şifremi unuttum, ne yapmalıyım?', 'Giriş ekranındaki "Şifremi unuttum" bağlantısını kullan ya da okulunun yetkili öğretmenine başvur; şifreni sıfırlayabilir.'],
    ['Hesap', 'Bilgilerimi kimler görebilir?', 'Sonuçlarını, notlarını ve kütüphaneni yalnızca sen ve okulunun yetkili öğretmenleri görür. Diğer öğrenciler senin bilgilerini göremez.'],
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
    'Güven puanı düşük sonuçları öğrenciyle konuşarak değerlendirin; gerekirse yeni bir değerlendirme planlayın.',
  ],
  sss: [
    ['Hesaplar', 'Öğrencileri sisteme nasıl eklerim?', 'Okul Paneli → Öğrenciler → "Öğrenci ekle / Excel yükle". Şablonu indirip ad soyad, e-posta, sınıf (ör. 12-A) ve isteğe bağlı öğrenci numarası ile şifreyi doldurun. Yüklemeden önce önizleme gösterilir; hatalı satırlar işaretlenir.'],
    ['Hesaplar', 'Öğrencilerin şifrelerini nasıl dağıtırım?', 'Geçici şifreler Öğrenciler tablosunda "geçici" etiketiyle görünür. "Giriş listesi (Excel)" ile tüm listeyi indirip sınıflara dağıtabilirsiniz. Öğrenci kendi şifresini belirleyince geçici şifre listeden kalkar.'],
    ['Hesaplar', 'Öğrenci şifresini unuttu.', 'Öğrenciyi seçip "Şifrelerini sıfırla" deyin; yeni geçici şifre tabloda görünür. Öğrenci giriş ekranındaki "Şifremi unuttum" bağlantısını da kullanabilir.'],
    ['Hesaplar', 'Okulumuza birden fazla yetkili eklenebilir mi?', 'Evet. Okul Yetkilileri sekmesinde her kişi için ad soyad, görev / unvan ve e-posta girilir. Tüm okul yetkilileri aynı yetkiye sahiptir.'],
    ['Sonuçlar', 'Bir öğrencinin sonuçlarını nerede görürüm?', 'Öğrenciler listesinde öğrencinin adına tıklayın. Açılan pencerede test ilerlemesi, sonuçlar, benzer akranlar, ilgi ve kulüp sonuçları, kütüphanesi ve tüm işlem kayıtları yer alır.'],
    ['Sonuçlar', 'Güven puanı nedir, düşükse ne yapmalıyım?', 'Değerlendirme sırasında sekme değiştirme, tam ekrandan çıkma, kamerayı kapatma gibi durumlar ve tutarlılık kontrolleri güven puanını belirler. Puan düşükse öğrenciyle konuşun; sonuçları dikkatle yorumlayın ve gerekirse yeniden değerlendirme planlayın.'],
    ['Raporlar', 'Hangi raporları alabilirim?', 'Öğrenci bazında: yönetici (ayrıntılı), öğrenci ve veli raporu (PDF) ile Excel. Şube bazında: şube özeti ve tüm şubenin veli / öğrenci / rehber raporları tek dosyada. Ayrıca sınıf düzeyi ve okul genel raporu. Raporları yalnızca okul yetkilileri indirebilir.'],
    ['Raporlar', 'Veli toplantısı için en pratik yol nedir?', 'Sınıflar sekmesinde ilgili şubenin "Veli" düğmesi, şubedeki tüm öğrencilerin veli raporlarını tek PDF\'te, isimlere göre sıralı olarak verir.'],
    ['Sınıflar', 'Sınıf öğretmenini nereye yazarım?', 'Sınıflar sekmesinde her şubenin satırındaki "Sınıf öğretmeni ekle" alanına. Bu bilgi şube raporlarında görünür.'],
    ['Sınıflar', 'Şube dağılımı ve akran benzerliği nasıl kullanılmalı?', 'Şube & Akran sekmesi öğrencilerin profillerine göre öneri sunar. "Dengeli dağıt" her şubede farklı profillerin bulunmasını sağlar; "Benzerleri grupla" proje ve etüt grupları içindir. Öneriler karar destek amaçlıdır ve öğrencilere gösterilmez.'],
    ['Sınıflar', 'Aday öğrenci nedir?', 'Okula kayıt için gelen öğrencileri sınıfı "Aday" olarak ekleyebilirsiniz. Aday testi çözünce hangi şubenin profiline daha yakın olduğunu görür, tek tıkla şubeye atayabilirsiniz.'],
    ['Diğer', 'Kulüp listesini nasıl oluştururum?', 'Kulüpler sekmesinde "Hazır listeden ekle" ile yaygın lise kulüplerini ekleyip okulunuzda olmayanları silebilir ya da pasif yapabilirsiniz. Öğrenciler kısa ilgi testini çözdükçe her kulübe kaç öğrencinin uygun olduğunu görürsünüz.'],
    ['Diğer', 'Eğitim koçu talepleri nasıl işler?', 'Öğrencinin talebi Koçlar sekmesine düşer. Koçla iletişime geçip durumu ("Görüşme planlandı" vb.) ve randevu zamanını girersiniz; öğrenci bunu kendi ekranında ve takviminde görür. Öğrenciler koçların iletişim bilgilerini görmez.'],
    ['Diğer', 'Takvime ne eklemeliyim?', 'Veli toplantıları, üniversite gezileri, kulüp günleri, deneme sınavları gibi okul etkinliklerini. İsterseniz yalnızca belirli bir sınıf düzeyine gösterebilirsiniz. Sınav ve tercih dönemleri gibi genel tarihler sistem yöneticisi tarafından eklenir.'],
    ['Diğer', 'Okulumuzun rengi ve logosu nasıl değişir?', 'Renk, Okul Paneli → Görünüm sekmesinden seçilir; öğrenci ekranlarında, grafiklerde ve raporlarda kullanılır. Logoyu değiştirmek için sistem yöneticisine başvurun.'],
  ],
}

export default function SistemHakkinda({ hedef = 'ogrenci' }) {
  const v = hedef === 'yonetim' ? YONETIM : OGRENCI
  const [ara, setAra] = useState('')
  const [acik, setAcik] = useState(null)
  const gruplar = useMemo(() => {
    const q = ara.trim().toLocaleLowerCase('tr-TR')
    const m = new Map()
    v.sss.forEach(([g, s, c], i) => {
      if (q && !`${s} ${c}`.toLocaleLowerCase('tr-TR').includes(q)) return
      if (!m.has(g)) m.set(g, [])
      m.get(g).push({ i, s, c })
    })
    return [...m.entries()]
  }, [v, ara])

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
        <div className="ct">Bilmeniz gerekenler</div>
        <ul className="sh-bilgi">{v.bilmen.map((b) => <li key={b}>{b}</li>)}</ul>
      </div>
      <div className="card">
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
          <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>Sıkça sorulan sorular</div>
          <input className="yp-sec" style={{ minWidth: 220 }} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Soru ara…" />
        </div>
        {gruplar.length === 0 && <div className="bos-durum">Aramana uygun soru bulunamadı.</div>}
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
    </div>
  )
}
