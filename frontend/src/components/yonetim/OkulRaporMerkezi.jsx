// [2026-10-10] Okul paneli → Rapor Merkezi: okulun indirebileceği tüm raporlar tek yerde.
// Yalnızca var olan uç noktalar kullanılır (api/client.js). Paketteki modülü kapalı raporlar gösterilmez;
// toplu ve sınıf öğretmeni raporları 'gelismis_raporlar' modülüne bağlıdır (backend raporlar._paket_kontrol ile aynı).
// Sınıflar sekmesindeki şube "Rapor" menüleri ayrıca yerinde durur.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { csvIndir } from '../istatistik'
import { useOkulModulleri } from '../../yardimci/moduller'
import { base64Indir } from './ortak'

const GERCEK_SINIF = ['9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf']
const tarihTR = (iso) => (iso ? new Date(`${String(iso).slice(0, 10)}T00:00:00`).toLocaleDateString('tr-TR') : '')
const bugun = () => new Date().toLocaleDateString('sv-SE')
const geri = (gun) => { const d = new Date(); d.setDate(d.getDate() - gun + 1); return d.toLocaleDateString('sv-SE') }

function RaporKarti({ ikon, baslik, aciklama, kapsam, ek, dugmeler, not }) {
  const [bekle, setBekle] = useState(null)
  const [hata, setHata] = useState(null)
  async function calistir(d) {
    setBekle(d.ad); setHata(null)
    try { await d.fn() } catch (e) { setHata(e.detail || e.message || 'Rapor indirilemedi.') } finally { setBekle(null) }
  }
  return (
    <div className="card orm-kart">
      <div className="orm-ust">
        <span className="orm-ikon" aria-hidden="true">{ikon}</span>
        <div style={{ minWidth: 0 }}>
          <h3 className="orm-baslik">{baslik}</h3>
          <p className="orm-aciklama">{aciklama}</p>
        </div>
      </div>
      {(kapsam || ek) && <div className="orm-secim">{kapsam}{ek}</div>}
      {not && <div className="yp-ince">{not}</div>}
      {hata && <div className="auth-error" style={{ margin: 0 }}>{hata}</div>}
      <div className="orm-dugmeler">
        {dugmeler.map((d) => (
          <button key={d.ad} type="button" className={d.ikincil ? 'btn sec' : 'btn'} disabled={!!bekle || d.pasif} title={d.ipucu} onClick={() => calistir(d)}>
            {bekle === d.ad ? <span className="spin" /> : d.ad}
          </button>
        ))}
      </div>
    </div>
  )
}

function Grup({ baslik, aciklama, children }) {
  const ic = (Array.isArray(children) ? children : [children]).filter(Boolean)
  if (!ic.length) return null
  return (
    <section className="orm-grup">
      <h2 className="ois-bolum-baslik">{baslik}</h2>
      {aciklama && <p className="ois-bolum-aciklama">{aciklama}</p>}
      <div className="orm-izgara">{ic}</div>
    </section>
  )
}

// sınıf düzeyi + şube seçimi; deger: '' | 's:<sınıf>' | 'b:<sınıf>|<şube>'
const kapsamCoz = (d) => {
  if (!d) return { sinif: null, sube: null }
  if (d.startsWith('s:')) return { sinif: d.slice(2), sube: null }
  const [sinif, sube] = d.slice(2).split('|')
  return { sinif, sube }
}

export default function OkulRaporMerkezi({ okulId, oz }) {
  const acik = useOkulModulleri()
  const [netler, setNetler] = useState(true)
  const net = acik('net_takibi') && netler

  // şube ve sınıf düzeyleri (Sınıflar sekmesiyle aynı kaynak: okul özeti)
  const { siniflar, subeler } = useMemo(() => {
    const sf = [], sb = []
    for (const s of oz.subeler || []) {
      if (!GERCEK_SINIF.includes(s.sinif)) continue
      if (!sf.includes(s.sinif)) sf.push(s.sinif)
      if (s.sube) sb.push(s)
    }
    return { siniflar: sf, subeler: sb }
  }, [oz])
  const [sinif, setSinif] = useState('')
  const [sube, setSube] = useState('')
  const [toplu, setToplu] = useState('')
  const [istKapsam, setIstKapsam] = useState('')
  const [istGun, setIstGun] = useState(90)
  useEffect(() => { setSinif((x) => x || siniflar[0] || ''); setSube((x) => x || (subeler[0] ? `b:${subeler[0].sinif}|${subeler[0].sube}` : '')); setToplu((x) => x || (subeler[0] ? `b:${subeler[0].sinif}|${subeler[0].sube}` : '')) }, [siniflar, subeler])

  // modül listeleri (yalnızca açık modüller için yüklenir)
  const [denemeler, setDenemeler] = useState(null)
  const [deneme, setDeneme] = useState('')
  const [anketler, setAnketler] = useState(null)
  const [anket, setAnket] = useState('')
  useEffect(() => {
    if (acik('okul_denemeleri')) api.okulDenemeleri(okulId).then((d) => { setDenemeler(d.denemeler); setDeneme(String(d.denemeler[0]?.id || '')) }).catch(() => setDenemeler([]))
    if (acik('anketler')) api.okulAnketleri(okulId).then((d) => { const l = d.anketler.filter((a) => a.durum !== 'taslak'); setAnketler(l); setAnket(String(l[0]?.id || '')) }).catch(() => setAnketler([]))
  }, [okulId])   // eslint-disable-line react-hooks/exhaustive-deps

  const subeSecici = (deger, setDeger, sinifDahil = false) => (
    <select className="yp-sec" value={deger} onChange={(e) => setDeger(e.target.value)} aria-label="Kapsam">
      {sinifDahil && siniflar.map((s) => <option key={s} value={`s:${s}`}>{s} (tüm şubeler)</option>)}
      {subeler.map((s) => <option key={s.etiket} value={`b:${s.sinif}|${s.sube}`}>{s.etiket}{s.ogretmen?.ad ? ` · ${s.ogretmen.ad}` : ''} ({s.ogrenci})</option>)}
    </select>
  )
  const sinifRaporu = (d, tur, bicim) => { const k = kapsamCoz(d); return api.sinifRaporuIndir(okulId, k.sinif, k.sube, tur, bicim, net) }

  // ---------------------------------------------------------------- istemci tarafı tablo (CSV, Excel'de açılır)
  async function denemeCsv() {
    const d = await api.okulDenemesi(Number(deneme))
    csvIndir({
      sutunlar: ['Sıra', 'Ad Soyad', 'Okul no', 'Sınıf', ...d.testler.map((t) => t.ad), 'Toplam net'],
      satirlar: d.sonuclar.map((r) => [r.sira, r.ad_soyad, r.ogrenci_no || '', r.sinif_metni, ...d.testler.map((t) => r.dersler[t.kod] ?? null), r.toplam_net]),
    }, `deneme-${d.deneme.ad}-${d.deneme.tarih}`)
  }
  async function tercihCsv() {
    const d = await api.okulTercihleri(okulId)
    csvIndir({
      sutunlar: ['Ad Soyad', 'Sınıf', 'Liste durumu', 'Tercih sayısı', 'Güvenli', 'Dengeli', 'Riskli', 'Başarı sırası', 'Uyarı', 'Yerleşme'],
      satirlar: d.ogrenciler.map((o) => [o.ad_soyad, o.sinif_metni, o.durum_adi, o.sayilar?.toplam ?? 0, o.sayilar?.guvenli ?? 0, o.sayilar?.dengeli ?? 0,
        o.sayilar?.riskli ?? 0, o.siralama ?? null, o.uyari, o.yerlesme || '']),
    }, `tercih-listeleri-${bugun()}`)
  }
  async function mezunCsv() {
    const d = await api.mezunlar(okulId)
    csvIndir({
      sutunlar: ['Yıl', 'Ad Soyad', 'Durum', 'Üniversite', 'Bölüm', 'Burs', 'Başarı sırası', 'Hedef bölüm', 'Hedefiyle aynı', 'Öneri sırası'],
      satirlar: d.kayitlar.map((m) => [String(m.yil), m.ad_soyad, m.durum_adi, m.universite || '', m.bolum_ad || '', m.burs || '', m.siralama ?? null,
        m.hedef_bolum_ad || '', m.hedefle_ayni == null ? '' : m.hedefle_ayni ? 'Evet' : 'Hayır', m.oneri_sirasi ?? null]),
    }, `mezun-yerlesmeleri-${bugun()}`)
  }

  const kapsamYok = <span className="yp-ince">Henüz şube yok — öğrencilere sınıf / şube atayın.</span>
  return (
    <div className="orm">
      <div className="yp-ince" style={{ marginBottom: 12 }}>
        Okulunuzun tüm raporları burada; her indirme işlem kayıtlarına yazılır. Okul, sınıf düzeyi ve şube özet raporlarında 5'ten az öğrencili kırılımlar gizlenir (kişisel verilerin korunması).
        Şubeye özel raporlar Sınıflar sekmesindeki <b>Rapor</b> menüsünde de var.
        {acik('net_takibi') && (
          <label className="orm-net">
            <input type="checkbox" checked={netler} onChange={(e) => setNetler(e.target.checked)} />
            <span><b>📈 PDF/Excel raporlara deneme ve net bilgilerini ekle</b></span>
          </label>
        )}
      </div>

      <Grup baslik="Okul ve sınıflar" aciklama="Katılım, alan dağılımı, ortak güçlü yönler, okul ortalamasıyla karşılaştırma ve öğrenci listesi.">
        <RaporKarti ikon="🏫" baslik="Okul genel raporu" aciklama="Tamamlama oranları, sınıflar, alan dağılımı, ortak güçlü yönler, deneme özeti, öğrenci listesi. Excel: özet, sınıflar ve tüm öğrenciler."
          dugmeler={[{ ad: '📄 PDF', fn: () => api.okulRaporuIndir(okulId, 'pdf', net) }, { ad: '📊 Excel', ikincil: true, fn: () => api.okulRaporuIndir(okulId, 'xlsx', net) }]} />
        <RaporKarti ikon="🏷️" baslik="Sınıf düzeyi raporu" aciklama="Bir sınıf düzeyinin şube karşılaştırması, alanlar, ortak güçlü yönler ve deneme özeti."
          kapsam={siniflar.length ? <select className="yp-sec" value={sinif} onChange={(e) => setSinif(e.target.value)} aria-label="Sınıf düzeyi">{siniflar.map((s) => <option key={s}>{s}</option>)}</select> : kapsamYok}
          dugmeler={[{ ad: '📄 PDF', pasif: !sinif, fn: () => api.sinifRaporuIndir(okulId, sinif, null, 'ozet', 'pdf', net) },
            { ad: '📊 Excel', ikincil: true, pasif: !sinif, fn: () => api.sinifRaporuIndir(okulId, sinif, null, 'ozet', 'xlsx', net) }]} />
        <RaporKarti ikon="👥" baslik="Şube raporu" aciklama="Şubenin durumu, alanları, okul ortalamasıyla karşılaştırması ve öğrenci listesi (okul numarası sırasıyla)."
          kapsam={subeler.length ? subeSecici(sube, setSube) : kapsamYok}
          dugmeler={[{ ad: '📄 PDF', pasif: !sube, fn: () => sinifRaporu(sube, 'ozet', 'pdf') }, { ad: '📊 Excel', ikincil: true, pasif: !sube, fn: () => sinifRaporu(sube, 'ozet', 'xlsx') }]} />
      </Grup>

      {acik('gelismis_raporlar') && (
        <Grup baslik="Toplu öğrenci raporları" aciklama="Seçilen şubedeki (ya da sınıf düzeyindeki) her öğrencinin bireysel raporu, öğrenci numarasına göre sıralı tek PDF'te — veli toplantısı ve sınıf öğretmenleri için. En fazla 80 öğrenci.">
          <RaporKarti ikon="📚" baslik="Toplu PDF raporlar" aciklama="Veli: velinin anlayacağı dille sonuç ve öneriler. Öğrenci: öğrencinin kendi raporu. Yönetim: ayrıntılı rapor. Sınıf öğretmeni: katılım, öne çıkanlar, hedef ve denemeler; psikolojik ayrıntı içermez."
            kapsam={subeler.length || siniflar.length ? subeSecici(toplu, setToplu, true) : kapsamYok}
            dugmeler={[
              { ad: '👪 Veli', pasif: !toplu, fn: () => sinifRaporu(toplu, 'toplu_veli', 'pdf') },
              { ad: '📘 Öğrenci', ikincil: true, pasif: !toplu, fn: () => sinifRaporu(toplu, 'toplu_ogrenci', 'pdf') },
              { ad: '🗂️ Yönetim', ikincil: true, pasif: !toplu, fn: () => sinifRaporu(toplu, 'toplu_yonetici', 'pdf') },
              { ad: '🧑‍🏫 Sınıf öğretmeni', ikincil: true, pasif: !toplu, fn: () => sinifRaporu(toplu, 'toplu_sinif_ogretmeni', 'pdf') },
            ]} />
        </Grup>
      )}

      <Grup baslik="İstatistikler" aciklama="İstatistikler ekranındaki tüm göstergeler, sayfa sayfa.">
        <RaporKarti ikon="📊" baslik="İstatistikler (Excel)" aciklama="Özet göstergeler, haftalık katılım, huni, şubeler, katman ve özellik ortalamaları, bölümler, K5 alanları ve paketinizdeki modüllere göre koçluk, deneme, rehberlik, anket, tercih, mezun ve kulüp sayfaları."
          kapsam={<select className="yp-sec" value={istKapsam} onChange={(e) => setIstKapsam(e.target.value)} aria-label="Kapsam">
            <option value="">Tüm okul</option>
            {siniflar.map((s) => <option key={s} value={`s:${s}`}>{s}</option>)}
            {subeler.map((s) => <option key={s.etiket} value={`b:${s.sinif}|${s.sube}`}>{s.etiket}</option>)}
          </select>}
          ek={<select className="yp-sec" value={istGun} onChange={(e) => setIstGun(Number(e.target.value))} aria-label="Tarih aralığı">
            {[[30, 'Son 30 gün'], [90, 'Son 90 gün'], [180, 'Son 6 ay'], [365, 'Son 1 yıl']].map(([g, a]) => <option key={g} value={g}>{a}</option>)}
          </select>}
          dugmeler={[{ ad: '📊 Excel', fn: () => api.okulIstatistikExcel(okulId, { ...kapsamCoz(istKapsam), bas: geri(istGun), bit: bugun() }) }]} />
      </Grup>

      <Grup baslik="Modül raporları" aciklama="Okulunuzun paketindeki modüllerin sonuç tabloları.">
        {acik('okul_denemeleri') && (
          <RaporKarti ikon="📝" baslik="Okul denemesi sonuçları" aciklama="Seçilen denemede öğrenci başına ders netleri ve toplam net, sıralı. CSV dosyası Excel'de açılır."
            kapsam={denemeler == null ? <span className="yp-ince">Yükleniyor…</span> : denemeler.length ? (
              <select className="yp-sec" value={deneme} onChange={(e) => setDeneme(e.target.value)} aria-label="Deneme">
                {denemeler.map((d) => <option key={d.id} value={d.id}>{tarihTR(d.tarih)} · {d.ad} ({d.oturum}, {d.katilim} öğrenci)</option>)}
              </select>) : <span className="yp-ince">Henüz yüklenmiş deneme yok.</span>}
            dugmeler={[{ ad: '📊 Excel (CSV)', pasif: !deneme, fn: denemeCsv }]} />
        )}
        {acik('anketler') && (
          <RaporKarti ikon="📋" baslik="Anket sonuçları" aciklama="Seçilen anketin yanıtları. Anonim anketlerde isim ve tarih yer almaz, küçük sınıflar birleştirilir; yanıt sayısı eşiğin altındaysa dosya verilmez."
            kapsam={anketler == null ? <span className="yp-ince">Yükleniyor…</span> : anketler.length ? (
              <select className="yp-sec" value={anket} onChange={(e) => setAnket(e.target.value)} aria-label="Anket">
                {anketler.map((a) => <option key={a.id} value={a.id}>{a.baslik} ({a.katilim} yanıt)</option>)}
              </select>) : <span className="yp-ince">Yayınlanmış anket yok.</span>}
            dugmeler={[{ ad: '📊 Excel', pasif: !anket, fn: () => api.anketExcel(Number(anket)) }]} />
        )}
        {acik('rehberlik') && (
          <RaporKarti ikon="🧭" baslik="Rehberlik görüşmeleri" aciklama="Son 1 yılın görüşme kayıtları (tarih, öğrenci, tür, konu, notlar, takip) ve konu × ay özeti — yıl sonu rehberlik raporu için."
            dugmeler={[{ ad: '📊 Excel', fn: () => api.gorusmeExcel(okulId) }]} />
        )}
        {acik('tercih') && (
          <RaporKarti ikon="🎓" baslik="Tercih listeleri" aciklama="12. sınıf ve mezunların tercih listesi durumu, güvenli / dengeli / riskli tercih sayıları ve uyarılar. CSV dosyası Excel'de açılır."
            dugmeler={[{ ad: '📊 Excel (CSV)', fn: tercihCsv }]} />
        )}
        {acik('mezun_takibi') && (
          <RaporKarti ikon="🎉" baslik="Mezun yerleşmeleri" aciklama="Mezunların yerleştiği üniversite ve bölümler, hedefle ve Filizyol önerileriyle uyum. CSV dosyası Excel'de açılır."
            dugmeler={[{ ad: '📊 Excel (CSV)', fn: mezunCsv }]} />
        )}
        <RaporKarti ikon="🔑" baslik="Öğrenci giriş listesi" aciklama="Tüm öğrenciler: ad soyad, numara, sınıf, e-posta ve (henüz değiştirilmediyse) geçici şifre. Düzenleyip Öğrenciler sekmesinden geri yükleyebilirsiniz."
          not="Geçici şifre içerir; yalnızca yetkili personelle paylaşın."
          dugmeler={[{ ad: '📊 Excel', ikincil: true, fn: async () => { const r = await api.girisListesi(okulId); base64Indir(r.dosya_adi, r.icerik_base64) } }]} />
      </Grup>
    </div>
  )
}
