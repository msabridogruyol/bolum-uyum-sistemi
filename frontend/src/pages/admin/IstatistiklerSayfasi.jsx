// [2026-10-10] Süper admin — İstatistikler: sistem geneli katılım, sonuçlar, modül kullanımı ve okullar.
// Veri tek istekte: GET /yonetim/istatistik/genel (backend/app/api/sistem_istatistik.py). Grafikler: components/istatistik.
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import {
  GrafikKarti, KpiKarti, KpiSatiri, YatayCubuk, SutunGrafik, YiginSutun, CizgiGrafik,
  Huni, Histogram, IsiHaritasi, Halka, histogramTablosu, KATEGORIK, sayi, DURUM, DIGER } from '../../components/istatistik'

// [2026-10-10] Erken uyarı seviyeleri durum renkleriyle (yüksek = kritik)
const SEVIYE_RENK = { 'Yüksek': DURUM.kritik.renk, 'Orta': DURUM.uyari.renk, 'Düşük': DURUM.iyi.renk }
import { BANTLAR } from '../../yardimci/seviye'

const DONEMLER = [['30', 'Son 30 gün'], ['90', 'Son 90 gün'], ['yil', 'Bu eğitim yılı'], ['tum', 'Tümü']]
const GIZLI = "5'ten az öğrenci"
const yuzde = (v) => (v == null ? null : `%${sayi(v)}`)
const tarihEtiketi = (iso, birim) => {
  const [y, m, g] = iso.split('-')
  if (birim === 'ay') return `${m}.${y.slice(2)}`
  return `${g}.${m}`
}

// Okul tablosu sütunları (sıralanabilir)
const OKUL_SUTUN = [
  { k: 'ad', ad: 'Okul', metin: true },
  { k: 'paket', ad: 'Paket', metin: true },
  { k: 'ogrenci', ad: 'Öğrenci' },
  { k: 'tamamlayan', ad: 'Tamamlayan' },
  { k: 'giris', ad: 'Giriş yapan', yuzde: true },
  { k: 'aktif7', ad: '7 gün aktif', yuzde: true },
  { k: 'aktif30', ad: '30 gün aktif', yuzde: true },
  { k: 'tamamlama', ad: 'Tamamlama', yuzde: true },
  { k: 'hedef', ad: 'Hedef seçen', yuzde: true },
  { k: 'guven', ad: 'Ort. güven' },
  { k: 'gecersiz', ad: 'Geçersiz tur', yuzde: true },
  { k: 'yetkili', ad: 'Yetkili' },
]
const ISI_METRIK = [['giris', 'Giriş'], ['aktif30', '30 gün aktif'], ['tamamlama', 'Tamamlama'], ['hedef', 'Hedef seçen']]

function Bolum({ baslik, aciklama }) {
  return (
    <div className="sis-bolum-baslik">
      <h2>{baslik}</h2>
      {aciklama && <p>{aciklama}</p>}
    </div>
  )
}

function OkulTablosu({ okullar }) {
  const [sirala, setSirala] = useState({ k: 'ogrenci', azalan: true })
  const sirali = useMemo(() => {
    const s = OKUL_SUTUN.find((x) => x.k === sirala.k)
    return [...okullar].sort((a, b) => {
      const va = a[sirala.k], vb = b[sirala.k]
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      const f = s.metin ? String(va).localeCompare(String(vb), 'tr') : va - vb
      return sirala.azalan ? -f : f
    })
  }, [okullar, sirala])
  const tikla = (k) => setSirala((s) => ({ k, azalan: s.k === k ? !s.azalan : !OKUL_SUTUN.find((x) => x.k === k).metin }))
  return (
    <div className="yp-tablo-kap" style={{ maxHeight: 520 }}>
      <table className="yp-tablo sis-okul-tablo">
        <thead>
          <tr>
            {OKUL_SUTUN.map((s) => (
              <th key={s.k} aria-sort={sirala.k === s.k ? (sirala.azalan ? 'descending' : 'ascending') : 'none'}>
                <button type="button" className="sis-siralama" onClick={() => tikla(s.k)}>
                  {s.ad}{sirala.k === s.k ? (sirala.azalan ? ' ▼' : ' ▲') : ''}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sirali.map((o) => (
            <tr key={o.id} className={o.aktif ? '' : 'sis-pasif'}>
              {OKUL_SUTUN.map((s) => {
                const v = o[s.k]
                if (s.k === 'ad') return <td key={s.k}><Link to={`/admin/okul/${o.id}`} className="ak-link">{v}</Link>{!o.aktif && <span className="yp-ince"> (pasif)</span>}</td>
                if (s.metin) return <td key={s.k} className="yp-ince">{v}</td>
                if (v == null) return <td key={s.k} className="sayi yp-ince" title={o.gizli ? 'Gizlilik için gösterilmez' : undefined}>{o.gizli && s.k !== 'yetkili' ? GIZLI : '—'}</td>
                return <td key={s.k} className="sayi">{s.yuzde ? yuzde(v) : sayi(v)}</td>
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function IstatistiklerSayfasi() {
  const [filtre, setFiltre] = useState({ donem: '30', okul_id: '', test: false })
  const [v, setV] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(true)
  const [hata, setHata] = useState(null)
  const [katman, setKatman] = useState(null)
  const [kullanim, setKullanim] = useState(null)
  const [excelBekle, setExcelBekle] = useState(false)

  useEffect(() => {
    let iptal = false
    setYukleniyor(true); setHata(null)
    api.sistemIstatistik({ donem: filtre.donem, okul_id: filtre.okul_id, test: filtre.test })
      .then((d) => { if (!iptal) setV(d) })
      .catch((e) => { if (!iptal) setHata(e.detail || 'İstatistikler alınamadı.') })
      .finally(() => { if (!iptal) setYukleniyor(false) })
    return () => { iptal = true }
  }, [filtre])
  // [2026-10-10] Kontrol Paneli'nden taşındı: sayfa isteği sayıları (anonim, kişi bazlı değil; filtre uygulanmaz)
  useEffect(() => { api.kullanimIstatistikleriGetir().then(setKullanim).catch(() => setKullanim(null)) }, [])

  const degis = (k, deger) => setFiltre((f) => ({ ...f, [k]: deger }))
  async function excel() {
    setExcelBekle(true)
    try { await api.sistemIstatistikExcel({ donem: filtre.donem, okul_id: filtre.okul_id, test: filtre.test }) } catch (e) { setHata(e.detail || 'Excel indirilemedi.') } finally { setExcelBekle(false) }
  }

  const filtreSatiri = (
    <div className="sis-filtreler" role="group" aria-label="Filtreler">
      <div className="eu-filtre" style={{ margin: 0 }}>
        {DONEMLER.map(([k, ad]) => (
          <button key={k} type="button" className={filtre.donem === k ? 'secili' : ''} aria-pressed={filtre.donem === k} onClick={() => degis('donem', k)}>{ad}</button>
        ))}
      </div>
      <select className="yp-sec" aria-label="Okul" value={filtre.okul_id} onChange={(e) => degis('okul_id', e.target.value)}>
        <option value="">Tüm okullar</option>
        {(v?.okul_secenekleri || []).map((o) => <option key={o.id} value={o.id}>{o.ad}{o.aktif ? '' : ' (pasif)'}</option>)}
        <option value="0">Okul harici öğrenciler</option>
      </select>
      <label className="sis-onay">
        <input type="checkbox" checked={filtre.test} onChange={(e) => degis('test', e.target.checked)} /> Test hesaplarını dahil et
      </label>
      <span style={{ flex: 1 }} />
      {yukleniyor && v && <span className="spin" aria-label="Yükleniyor" />}
      <button type="button" className="rd-dugme" disabled={excelBekle || !v} onClick={excel}>{excelBekle ? <span className="spin" /> : '📊'} Excel</button>
    </div>
  )

  if (!v) {
    return (
      <div className="pg pg-genis">
        <div className="ph"><div className="pt">İstatistikler</div></div>
        {filtreSatiri}
        <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
      </div>
    )
  }

  const k = v.kpi
  const gizliSayfa = v.kucuk_grup?.sayfa_gizli
  const z = v.zaman
  const xEt = z.x.map((x) => tarihEtiketi(x, z.birim))
  const secKatman = katman && v.katmanlar.find((x) => x.kod === katman) ? katman : v.katmanlar[0]?.kod
  const kat = v.katmanlar.find((x) => x.kod === secKatman)
  const ay = v.ayrinti || {}
  const modulVeri = v.moduller.map((m) => ({ ad: `${m.ikon} ${m.ad}`, deger: m.ogrenci, alt: `${sayi(m.sayi)} ${m.olay}${m.donemli ? '' : ' · güncel'}` }))
  const isiOkullar = v.okullar.filter((o) => o.ogrenci > 0).slice(0, 25)
  const katKod = v.katmanlar.map((x) => x.kod)
  const hedefYigin = v.hedeflenen.slice(0, 10)
  const donemMetni = v.filtre.baslangic ? `${v.filtre.donem_ad} (${v.filtre.baslangic.split('-').reverse().join('.')} itibarıyla)` : 'tüm zamanlar'

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">İstatistikler</div>
        <div className="ps">Sistem geneli katılım, sonuçlar ve modül kullanımı. Her kartta “Tablo olarak gör” ve CSV; tamamı için Excel.</div>
      </div>
      {filtreSatiri}
      <div className="yp-ince" style={{ margin: '-4px 0 12px' }}>
        Dönem ({donemMetni}) olay tarihlerine uygulanır: tamamlanan turlar, girişler, modül kullanımı ve zaman serileri. Öğrenci sayıları, huni ve okul tablosu güncel durumdur.
        {gizliSayfa && <> <b>Seçili kapsamda {v.kucuk_grup.esik}’ten az öğrenci olduğu için oran, ortalama ve dağılımlar gizlilik nedeniyle gösterilmiyor.</b></>}
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <KpiSatiri min={160}>
        <KpiKarti etiket="Aktif okul" deger={k.okul} ikon="🏫" alt={`${sayi(k.okul_paketli)} tanesine paket atanmış`} />
        <KpiKarti etiket="Öğrenci" deger={k.ogrenci} ikon="🎓" alt={filtre.test ? 'Test hesapları dahil' : 'Test hesapları hariç'} />
        <KpiKarti etiket="Son 7 günde aktif" deger={k.aktif7} ikon="⚡" alt={`Son 30 gün: ${sayi(k.aktif30)}`} />
        <KpiKarti etiket="Testi tamamlayan" deger={k.tamamlayan} ikon="✅" ton="iyi" alt="En az bir K1–K4 turu" />
        <KpiKarti etiket="Tamamlama oranı" deger={k.tamamlama_orani ?? (gizliSayfa ? GIZLI : '—')} birim={k.tamamlama_orani != null ? '%' : undefined} ikon="📈" />
        <KpiKarti etiket="Ortalama güven puanı" deger={k.guven_ort ?? (gizliSayfa ? GIZLI : '—')} ikon="🛡️" alt={`${sayi(k.tur)} tamamlanan tur (dönem)`} />
        <KpiKarti etiket="Geçersiz tur oranı" deger={k.gecersiz_orani ?? (gizliSayfa ? GIZLI : '—')} birim={k.gecersiz_orani != null ? '%' : undefined} ikon="⚠️"
          ton={k.gecersiz ? 'uyari' : 'notr'} alt={`${sayi(k.gecersiz)} geçersiz tur`} />
        <KpiKarti etiket="Hedef bölüm seçen" deger={k.hedef} ikon="🎯" />
        <KpiKarti etiket="Okul yetkilisi" deger={k.yetkili} ikon="🧑‍💼" />
      </KpiSatiri>

      <Bolum baslik="Katılım" aciklama="Hesap açılışından koçluğa kadar öğrencilerin ilerleyişi." />
      <div className="ist-kartlar">
        <GrafikKarti genis baslik={`Zaman içinde etkinlik (${z.birim}lük)`} aciklama="Yeni açılan öğrenci hesabı, giriş yapan farklı öğrenci ve tamamlanan K1–K4 turu"
          tablo={{ sutunlar: [`Dönem başı (${z.birim})`, 'Yeni hesap', 'Giriş yapan öğrenci', 'Tamamlanan tur'], satirlar: z.x.map((x, i) => [x, z.yeni_hesap[i], z.giris[i], z.tur[i]]) }}>
          <CizgiGrafik x={xEt} seriler={[
            { ad: 'Yeni hesap', degerler: z.yeni_hesap, renk: KATEGORIK[0] },
            { ad: 'Giriş yapan', degerler: z.giris, renk: KATEGORIK[1] },
            { ad: 'Tamamlanan tur', degerler: z.tur, renk: KATEGORIK[2] },
          ]} />
        </GrafikKarti>
        <GrafikKarti baslik="Öğrenci hunisi" aciklama="Güncel durum; her adımda o adıma ulaşan öğrenci"
          tablo={{ sutunlar: ['Adım', 'Öğrenci', 'İlk adıma göre'], satirlar: v.huni.map((h) => [h.ad, h.deger, v.huni[0].deger ? `%${sayi((100 * h.deger) / v.huni[0].deger)}` : '—']) }}>
          <Huni adimlar={v.huni} birim="öğrenci" />
        </GrafikKarti>
        <GrafikKarti baslik="Sınıf düzeyine göre durum" aciklama="Güncel değerlendirme durumu"
          tablo={{ sutunlar: ['Sınıf düzeyi', ...v.siniflar.seriler.map((s) => s.ad)], satirlar: v.siniflar.kategoriler.map((c, i) => [c, ...v.siniflar.seriler.map((s) => s.degerler[i])]) }}>
          <YiginSutun kategoriler={v.siniflar.kategoriler} seriler={v.siniflar.seriler} birim="öğrenci" />
        </GrafikKarti>
      </div>

      <Bolum baslik="Sonuçlar" aciklama="Öğrencinin dönem içinde tamamladığı son tur esas alınır." />
      <div className="ist-kartlar">
        <GrafikKarti baslik="Katman ortalamaları" aciklama="K1–K4: katmandaki özellik puanlarının öğrenci ortalaması (0–100)"
          tablo={{ sutunlar: ['Katman', 'Ortalama', 'Öğrenci'], satirlar: v.katmanlar.map((x) => [x.kod, x.ortalama, x.n]) }}>
          <SutunGrafik veri={v.katmanlar.map((x) => ({ ad: x.kod, deger: x.ortalama }))} maks={100} birim="puan" />
        </GrafikKarti>
        <GrafikKarti baslik={`Puan dağılımı — ${secKatman || ''}`} aciklama="Arka plan bantları: düzey etiketleri (Gelişime açık … Çok güçlü)"
          sag={<div className="sis-mini-sec" role="group" aria-label="Katman seç">{katKod.map((kk) => (
            <button key={kk} type="button" className="ist-dugme" aria-pressed={kk === secKatman} onClick={() => setKatman(kk)}>{kk}</button>
          ))}</div>}
          tablo={histogramTablosu(kat?.degerler || [])} csv={`puan-dagilimi-${secKatman}`}>
          <Histogram degerler={kat?.degerler || []} aralik={[0, 100]} kova={10} bantlar={BANTLAR} />
        </GrafikKarti>
        <GrafikKarti baslik="Güven puanı dağılımı" aciklama="Dönemde tamamlanan tüm turlar; düşük güven puanı tur geçersiz sayılabilir"
          tablo={histogramTablosu(v.guven_degerleri, { birim: 'tur' })} csv="guven-puani">
          <Histogram degerler={v.guven_degerleri} aralik={[0, 100]} kova={10} birim="tur" />
        </GrafikKarti>
        <GrafikKarti baslik="En çok 1. sırada önerilen bölümler" aciklama="Öğrencinin en yüksek uyumlu bölümü"
          tablo={{ sutunlar: ['Bölüm', 'Öğrenci'], satirlar: v.onerilen.map((x) => [x.ad, x.deger]) }}>
          <YatayCubuk veri={v.onerilen} birim="öğrenci" enFazla={10} />
        </GrafikKarti>
        <GrafikKarti baslik="Üst alan dağılımı" aciklama="1. sıradaki bölümün K5 üst alanı"
          tablo={{ sutunlar: ['Üst alan', 'Öğrenci'], satirlar: v.alanlar.map((x) => [x.ad, x.deger]) }}>
          <YatayCubuk veri={v.alanlar} birim="öğrenci" enFazla={10} renk={KATEGORIK[1]} />
        </GrafikKarti>
        <GrafikKarti baslik="En çok hedeflenen bölümler" aciklama="Aktif hedef bölüm (güncel)"
          tablo={{ sutunlar: ['Bölüm', 'Hedefleyen'], satirlar: v.hedeflenen.map((x) => [x.ad, x.deger]) }}>
          <YatayCubuk veri={v.hedeflenen} birim="öğrenci" enFazla={10} renk={KATEGORIK[2]} />
        </GrafikKarti>
        <GrafikKarti genis baslik="Hedef bölümde uyum durumu" aciklama="Hedefleyenlerin son tamamlanan turundaki uyum: yetiyor 70+, sınırda 40–69, yetmiyor <40"
          tablo={{ sutunlar: ['Bölüm', 'Yetiyor (70+)', 'Sınırda (40–69)', 'Yetmiyor (<40)', 'Hesaplanmadı'], satirlar: v.hedeflenen.map((x) => [x.ad, x.yetiyor, x.sinirda, x.yetmiyor, x.yok]) }}>
          <YiginSutun kategoriler={hedefYigin.map((x) => x.ad)} birim="öğrenci" seriler={[
            { ad: 'Yetiyor (70+)', degerler: hedefYigin.map((x) => x.yetiyor), renk: DURUM.iyi.renk },
            { ad: 'Sınırda (40–69)', degerler: hedefYigin.map((x) => x.sinirda), renk: DURUM.uyari.renk },
            { ad: 'Yetmiyor (<40)', degerler: hedefYigin.map((x) => x.yetmiyor), renk: DURUM.kritik.renk },
            { ad: 'Hesaplanmadı', degerler: hedefYigin.map((x) => x.yok), renk: DIGER },
          ]} />
        </GrafikKarti>
      </div>

      <Bolum baslik="Modül Kullanımı" aciklama="Dönem içinde modülü kullanan farklı öğrenci (tercih listesi güncel durumdur)." />
      <KpiSatiri min={170}>
        <KpiKarti etiket="Filiz sohbeti" deger={ay.filiz?.oturum ?? '—'} ikon="💬" alt={`${sayi(v.moduller.find((m) => m.k === 'filiz')?.sayi || 0)} öğrenci mesajı · yapay zekâ / rehber modu ayrımı kaydedilmez`} />
        <KpiKarti etiket="Haftalık görev tamamlama" deger={ay.haftalik?.toplam ? Math.round((100 * ay.haftalik.tamam) / ay.haftalik.toplam) : '—'} birim={ay.haftalik?.toplam ? '%' : undefined}
          ikon="✅" alt={ay.haftalik ? `${sayi(ay.haftalik.tamam)} / ${sayi(ay.haftalik.toplam)} görev` : 'Veri yok'} />
        <KpiKarti etiket="Meslek simülasyonu" deger={ay.simulasyon?.sayi ?? '—'} ikon="🎬" alt={ay.simulasyon?.keyif != null ? `Ortalama keyif ${sayi(ay.simulasyon.keyif)} / 100` : 'Ortalama keyif —'} />
        <KpiKarti etiket="Rehberlik görüşmesi" deger={ay.rehberlik?.yapildi ?? '—'} ikon="🧭" alt={ay.rehberlik ? `${sayi(ay.rehberlik.planlandi)} planlandı` : 'Veri yok'} />
        <KpiKarti etiket="Portfolyo kaydı" deger={ay.portfolyo?.toplam ?? '—'} ikon="🗂️" alt={ay.portfolyo ? `${sayi(ay.portfolyo.dogrulanan)} rehber doğruladı` : 'Veri yok'} />
        <KpiKarti etiket="Kulüp talebi" deger={Object.values(ay.kulup || {}).reduce((a, b) => a + b, 0)} ikon="🎭"
          alt={`${sayi(ay.kulup?.onaylandi || 0)} onaylı · ${sayi(ay.kulup?.bekliyor || 0)} bekliyor`} />
        <KpiKarti etiket="Tercih listesi" deger={Object.values(ay.tercih_listesi || {}).reduce((a, b) => a + b, 0)} ikon="🎓"
          alt={Object.entries(ay.tercih_listesi || {}).map(([d, n]) => `${d}: ${n}`).join(' · ') || 'Güncel'} />
      </KpiSatiri>
      <div className="ist-kartlar">
        <GrafikKarti genis baslik="Modülü kullanan öğrenci" aciklama="Her satırın altında dönemdeki toplam olay sayısı"
          tablo={{ sutunlar: ['Modül', 'Öğrenci', 'Olay', 'Birim'], satirlar: v.moduller.map((m) => [m.ad, m.ogrenci, m.sayi, m.olay + (m.donemli ? '' : ' (güncel)')]) }}>
          <YatayCubuk veri={modulVeri} birim="öğrenci" />
        </GrafikKarti>
        <GrafikKarti baslik="En çok simüle edilen meslekler" aciklama="Simülasyon sayısı; satır altında ortalama keyif (0–100)"
          tablo={{ sutunlar: ['Meslek', 'Simülasyon', 'Ortalama keyif'], satirlar: (ay.simulasyon_meslekler || []).map((x) => [x.ad, x.deger, x.keyif]) }}>
          <YatayCubuk veri={(ay.simulasyon_meslekler || []).map((x) => ({ ...x, alt: x.keyif != null ? `keyif ${sayi(x.keyif)}` : undefined }))} birim="simülasyon" enFazla={10} renk={KATEGORIK[3]} />
        </GrafikKarti>
        {v.erken_uyari ? (
          <>
            <GrafikKarti baslik="Erken uyarı seviyeleri" aciklama="Rehberlik modülü açık okullar; öğrencinin en yüksek uyarısı (güncel)"
              tablo={{ sutunlar: ['Seviye', 'Öğrenci'], satirlar: v.erken_uyari.seviye.map((x) => [x.ad, x.deger]) }}>
              <Halka veri={v.erken_uyari.seviye.filter((x) => x.deger > 0).map((x) => ({ ...x, renk: SEVIYE_RENK[x.ad] }))} birim="öğrenci" />
            </GrafikKarti>
            <GrafikKarti baslik="Erken uyarı nedenleri" aciklama="Bir öğrencide birden çok neden olabilir"
              tablo={{ sutunlar: ['Neden', 'Öğrenci'], satirlar: v.erken_uyari.kural.map((x) => [x.ad, x.deger]) }}>
              <YatayCubuk veri={v.erken_uyari.kural} birim="öğrenci" renk={KATEGORIK[4]} />
            </GrafikKarti>
          </>
        ) : (
          <GrafikKarti baslik="Erken uyarı" aciklama="Bu kapsamda rehberlik modülü açık okul yok ya da gizlilik nedeniyle gösterilmiyor."><div className="ist-bos">Veri yok</div></GrafikKarti>
        )}
      </div>

      <Bolum baslik="Okullar" aciklama={`Okul başına güncel durum. ${v.kucuk_grup.dipnot}`} />
      <div className="ist-kartlar">
        <GrafikKarti genis baslik="Okul tablosu" aciklama="Sütun başlığına tıklayarak sıralayın; okul adına tıklayınca okul paneli açılır"
          tablo={{ sutunlar: OKUL_SUTUN.map((s) => s.ad + (s.yuzde ? ' (%)' : '')), satirlar: v.okullar.map((o) => OKUL_SUTUN.map((s) => (o[s.k] == null && o.gizli && !s.metin && s.k !== 'yetkili' ? GIZLI : o[s.k]))) }}
          csv="okul-tablosu">
          <OkulTablosu okullar={v.okullar} />
        </GrafikKarti>
        <GrafikKarti baslik="Okul × katılım (%)" aciklama={isiOkullar.length < v.okullar.filter((o) => o.ogrenci > 0).length ? 'En kalabalık 25 okul' : 'Öğrencisi olan okullar'}
          tablo={{ sutunlar: ['Okul', ...ISI_METRIK.map(([, a]) => `${a} (%)`)], satirlar: isiOkullar.map((o) => [o.ad, ...ISI_METRIK.map(([m]) => o[m])]) }} csv="okul-katilim">
          <IsiHaritasi satirBasligi="Okul" satirlar={isiOkullar.map((o) => o.ad)} sutunlar={ISI_METRIK.map(([, a]) => a)}
            degerler={isiOkullar.map((o) => ISI_METRIK.map(([m]) => o[m]))} bicim="%" aralik={[0, 100]} />
        </GrafikKarti>
        <GrafikKarti baslik="Okul × katman ortalaması" aciklama="Dönemde tamamlanan son turlar; 5'ten az tamamlayanı olan okulda gösterilmez"
          tablo={{ sutunlar: ['Okul', ...katKod], satirlar: isiOkullar.map((o) => [o.ad, ...katKod.map((kk) => o.katman[kk])]) }} csv="okul-katman">
          <IsiHaritasi satirBasligi="Okul" satirlar={isiOkullar.map((o) => o.ad)} sutunlar={katKod}
            degerler={isiOkullar.map((o) => katKod.map((kk) => o.katman[kk]))} bicim="puan" aralik={[0, 100]} />
        </GrafikKarti>
        <GrafikKarti baslik="Paket dağılımı" aciklama="Aktif okulların paketi; öğrenci sayıları tabloda"
          tablo={{ sutunlar: ['Paket', 'Aktif okul', 'Öğrenci'], satirlar: v.paketler.map((x) => [x.ad, x.deger, x.ogrenci]) }}>
          <Halka veri={v.paketler} birim="okul" />
        </GrafikKarti>
      </div>

      <Bolum baslik="Sistem Kullanımı" aciklama="Sayfa isteği sayıları (son 7 gün). Anonim sayım; kişi bazlı değildir ve filtreler uygulanmaz." />
      {!kullanim ? (
        <div className="bos-durum">Ziyaret verisi toplanmaya yeni başladı ya da bu sunucuda kayıt tutulmuyor.</div>
      ) : (
        <div className="ist-kartlar">
          <GrafikKarti baslik="Günlük istek" aciklama={`Bugün ${sayi(kullanim.bugun_toplam)} · son 7 gün ${sayi(kullanim.son_7_gun_toplam)} · öğrenci ${sayi(kullanim.ogrenci_ziyaret)} · yönetim ${sayi(kullanim.admin_ziyaret)} · anonim ${sayi(kullanim.anonim_ziyaret)}`}
            tablo={{ sutunlar: ['Tarih', 'İstek'], satirlar: kullanim.gunluk_dagilim.map((g) => [g.tarih, g.sayi]) }}>
            <SutunGrafik veri={kullanim.gunluk_dagilim.map((g) => ({ ad: g.tarih.slice(5).split('-').reverse().join('.'), deger: g.sayi }))} birim="istek" />
          </GrafikKarti>
          <GrafikKarti baslik="En çok istek alan yollar"
            tablo={{ sutunlar: ['Yol', 'İstek'], satirlar: kullanim.en_cok_ziyaret_edilen.map((e) => [e.yol, e.sayi]) }}>
            <YatayCubuk veri={kullanim.en_cok_ziyaret_edilen.map((e) => ({ ad: e.yol, deger: e.sayi }))} birim="istek" />
          </GrafikKarti>
        </div>
      )}
    </div>
  )
}
