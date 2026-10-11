// [2026-10-10] Sistem Hakkında + Sıkça Sorulan Sorular — teknik olmayan, kullanıcıya yönelik anlatım.
// hedef = 'ogrenci' (öğrenci menüsü) | 'yonetim' (okul yetkilisi / süper admin)
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

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
    'Bilgilerini sen ve okulunun yetkili öğretmenleri görür; diğer öğrenciler göremez.',
  ],
  sss: [
    ['Değerlendirme', 'Testi bir oturumda bitirmem gerekiyor mu?', 'Hayır. Her bölüm ayrıdır; bir bölümü bitirip ara verebilirsin. Bir bölümün ortasında çıkarsan verdiğin cevaplar kaydedilir ve döndüğünde kaldığın yerden devam edersin.'],
    ['Değerlendirme', 'Doğru cevap var mı? Nasıl cevaplamalıyım?', 'Doğru cevap yoktur. "Olmak istediğin" kişiye göre değil, şu anki hâline göre cevap ver. Çok düşünmeden, ilk aklına gelene göre seçmek genellikle en doğru sonucu verir.'],
    ['Değerlendirme', 'Neden kamera izni isteniyor?', 'Kamera isteğe bağlıdır; yalnızca Ayarlar → Gizlilik ve İzinler\'den izin verirsen açılır. Açarsan değerlendirme sırasında testi senin çözdüğünü doğrulamak için aralıklarla fotoğraf çekilir (video kaydı yapılmaz) ve fotoğraflar en geç 6 ay içinde silinir. Kamerayı açmasan da puanın düşmez. Sekme değiştirmek, tam ekrandan çıkmak gibi durumlar ise "güven puanını" düşürür; güven puanı çok düşerse sonuçların geçersiz sayılabilir.'],
    ['Değerlendirme', 'Testi tekrar çözebilir miyim?', 'Evet. İlgi ve kişilik zamanla değişebildiği için belli bir süre sonra yeni değerlendirme turu açılır. Tarihi sol menüde "Sonraki tur" olarak görürsün. Böylece kendindeki değişimi de izleyebilirsin.'],
    ['Sonuçlar', '"%85 uyum" ne demek?', 'Profilinin, o bölümün mezunlarının çalıştığı mesleklerin gerektirdiği özelliklerle ne kadar örtüştüğünü gösterir; bölümleri birbiriyle karşılaştırarak hesaplanır. Bir başarı tahmini ya da "bu bölümü kazanırsın" anlamına gelmez.'],
    ['Sonuçlar', 'Güçlü, çok güçlü, gelişime açık ne anlama geliyor?', 'Her özellik 0–100 arasında puanlanır. "Çok güçlü" ve "güçlü" seni öne çıkaran yönlerin, "gelişime açık" ise üzerinde çalışarak ilerletebileceğin yönlerindir. Gelişime açık olmak "kötü" demek değildir.'],
    ['Sonuçlar', 'Raporumu nasıl alabilirim?', 'Değerlendirmeni tamamladıktan sonra sol menüdeki Raporlarım sayfasından kendi raporunu, velin için hazırlanmış raporu ve sonuçlarının Excel tablosunu indirebilirsin. Bu sayfayı menünde göremiyorsan rehber öğretmenine başvurabilirsin.'],
    ['Hedef ve koçluk', 'Hedef bölümümü değiştirebilir miyim?', 'Evet, belirli sayıda değiştirme hakkın vardır. Hakkın biterse okulunun yetkili öğretmeni sana ek hak tanıyabilir.'],
    ['Hedef ve koçluk', 'Yol haritasındaki adımları nasıl tamamlarım?', 'Her adımın altında ne yapacağın ve "Nasıl anlarsın?" kontrol listesi vardır. Başladığında "Başladım"ı, bitirdiğinde "Tamamladım"ı işaretle. İlerlemen Koçluğum sayfasında görünür.'],
    ['Hedef ve koçluk', 'Filiz kimdir?', 'Filiz, sorularını yanıtlayan gelişim koçundur. Sonuçlarına, hedef bölümüne ve görevlerine göre sana yol gösterir; bölümler, meslekler ve çalışma alışkanlıkları hakkında soru sorabilirsin. Önemli kararlarını rehber öğretmeninle ve ailenle birlikte ver.'],
    ['Hedef ve koçluk', 'Eğitim koçuyla nasıl görüşürüm?', 'Eğitim Koçları sayfasından bir koç seçip görüşme talebi bırakırsın. Talebin Filizyol koordinatörüne gider; görüşme planlanınca tarih ve saati hem o sayfada hem Takvim\'inde görürsün.'],
    ['Diğer', 'Kulüp önerileri ve ilgi testi bölüm sonucumu etkiler mi?', 'Hayır. Kısa ilgi testi yalnızca sana uygun kulüpleri önermek içindir; bölüm önerilerin değişmez.'],
    ['Diğer', 'Kütüphanem ne işe yarar?', 'Okuduğun kitapları, izlediğin belgeselleri, aldığın kursları ve katıldığın etkinlikleri burada biriktirirsin. Rehber öğretmeninle görüşürken ve ileride üniversite başvurularında kendini anlatmak için çok işe yarar.'],
    ['Diğer', 'Takvimde neler görünür?', 'Sınav ve tercih dönemleri gibi önemli tarihler, okulunun etkinlikleri, eğitim koçu görüşmelerin ve kendi eklediğin notlar.'],
    ['Hesap', 'Şifremi unuttum, ne yapmalıyım?', 'Giriş ekranındaki "Şifremi unuttum" bağlantısını kullan ya da okulunun yetkili öğretmenine başvur; şifreni sıfırlayabilir.'],
    ['Hesap', 'Bilgilerimi kimler görebilir?', 'Sonuçlarını, kütüphaneni ve diğer kayıtlarını sen ve okulunun yetkili öğretmenleri görür. Diğer öğrenciler senin bilgilerini göremez. Haftalık görevlerdeki yansıtma cevaplarını yalnızca sen görürsün. Ayrıntılar Ayarlar\'daki Aydınlatma Metni\'nde.'],
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
        <div className="ct">Bilmeniz gerekenler</div>
        <ul className="sh-bilgi">{v.bilmen.map((b) => <li key={b}>{b}</li>)}</ul>
      </div>
      <div className="card">
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
          <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>Sıkça sorulan sorular</div>
          <input className="yp-sec" style={{ minWidth: 220 }} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Soru ara…" />
        </div>
        {sss === null && <div className="bos-durum">Yükleniyor…</div>}
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
    </div>
  )
}
