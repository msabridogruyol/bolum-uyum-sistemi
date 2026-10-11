// [2026-10-10] İş Hayatı → 'maas' sekmesi: İlk Maaşla Bir Ay.
// Gelir: bölüm mesleklerinin TAHMİNİ ortalama neti (TÜİK, asgari ücretle güncellenmiş) / kamu kadrosu / asgari ücret / öğrencinin girdiği tutar.
// Gider: GET /ogrenci/is-hayati/giderler?il= (süper admin verisi). Veri yoksa kalem BOŞ gelir; öğrenci kendisi doldurur — varsayılan uydurulmaz.
// Kaydetme yok; her şey sayfa içi state.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { tl, TahminEtiketi } from './ortak'

const SAYI = (v) => Math.round(Number(v)).toLocaleString('tr-TR')
const KONUT = [
  { kod: 'aile', ad: 'Ailemle', ikon: '🏠', not: 'Kira yok; eve katkını “Aileye katkı” satırına yazabilirsin.' },
  { kod: 'arkadas', ad: 'Ev arkadaşıyla', ikon: '👥', not: '2+1 bir evin kira, aidat ve faturalarını ikiye bölüyoruz.' },
  { kod: 'tek', ad: 'Tek başıma', ikon: '🔑', not: '1+1 bir evin kira, aidat ve faturaları tamamen senin.' },
]
const ULASIM = [
  { kod: 'toplu', ad: 'Toplu taşıma', ikon: '🚌' },
  { kod: 'arac', ad: 'Kendi aracım', ikon: '🚗' },
  { kod: 'yuruyus', ad: 'Yürüyüş / bisiklet', ikon: '🚲' },
]
const BILINEN = ['kira_1_1', 'kira_2_1', 'aidat', 'fatura', 'mutfak', 'ulasim', 'iletisim', 'giyim', 'saglik', 'sosyal']

// Yaşam tarzına göre kalem listesi: [{kod, ad, kaynakKod, carpan}] — carpan: veriden gelen tutara uygulanan oran (ev arkadaşı → 1/2)
function kalemPlani(konut, ulasim) {
  const k = []
  if (konut === 'tek') k.push({ kod: 'kira', ad: 'Kira (1+1)', kaynakKod: 'kira_1_1', carpan: 1 })
  if (konut === 'arkadas') k.push({ kod: 'kira', ad: 'Kira payın (2+1’in yarısı)', kaynakKod: 'kira_2_1', carpan: 0.5 })
  if (konut !== 'aile') {
    k.push({ kod: 'aidat', ad: konut === 'arkadas' ? 'Aidat payın' : 'Aidat', kaynakKod: 'aidat', carpan: konut === 'arkadas' ? 0.5 : 1 })
    k.push({ kod: 'fatura', ad: konut === 'arkadas' ? 'Faturalar (payın)' : 'Faturalar (elektrik, su, doğalgaz)', kaynakKod: 'fatura', carpan: konut === 'arkadas' ? 0.5 : 1 })
  } else {
    k.push({ kod: 'aile_katki', ad: 'Aileye katkı', kaynakKod: null, carpan: 1 })
  }
  k.push({ kod: 'mutfak', ad: 'Mutfak / gıda', kaynakKod: 'mutfak', carpan: 1 })
  if (ulasim === 'toplu') k.push({ kod: 'ulasim', ad: 'Toplu taşıma (aylık)', kaynakKod: 'ulasim', carpan: 1 })
  if (ulasim === 'arac') k.push({ kod: 'arac', ad: 'Araç (yakıt, sigorta, bakım, otopark)', kaynakKod: null, carpan: 1 })
  k.push({ kod: 'iletisim', ad: 'Telefon ve internet', kaynakKod: 'iletisim', carpan: 1 })
  k.push({ kod: 'giyim', ad: 'Giyim', kaynakKod: 'giyim', carpan: 1 })
  k.push({ kod: 'saglik', ad: 'Sağlık ve kişisel bakım', kaynakKod: 'saglik', carpan: 1 })
  k.push({ kod: 'sosyal', ad: 'Sosyal yaşam', kaynakKod: 'sosyal', carpan: 1 })
  return k
}

function Secenek({ secili, onClick, children }) {
  return (
    <button type="button" onClick={onClick} aria-pressed={secili}
      style={{ border: `1.5px solid ${secili ? 'var(--okul-c)' : 'var(--bor)'}`, background: secili ? 'color-mix(in srgb, var(--okul-c) 10%, var(--sur))' : 'var(--sur)',
        color: 'var(--tx)', borderRadius: 12, padding: '8px 12px', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', textAlign: 'left' }}>
      {children}
    </button>
  )
}

function Baslik({ no, children }) {
  return <div style={{ fontWeight: 800, fontSize: 14, margin: '2px 0 10px', display: 'flex', gap: 8, alignItems: 'center' }}>
    <span style={{ width: 22, height: 22, borderRadius: 999, background: 'var(--okul-c)', color: '#fff', display: 'inline-grid', placeItems: 'center', fontSize: 12 }}>{no}</span>{children}</div>
}

// Yatay şelale: gelirden başlayıp her gider kalemini düşer
function Selale({ gelir, kalemler }) {
  const adimlar = []
  let kalan = gelir
  for (const k of kalemler) { adimlar.push({ ad: k.ad, bas: kalan - k.tutar, son: kalan, tutar: k.tutar }); kalan -= k.tutar }
  const dmin = Math.min(0, kalan), dmax = Math.max(gelir, 1)
  const x = (v) => ((v - dmin) / (dmax - dmin)) * 100
  const Satir = ({ ad, a, b, renk, metin, kalin }) => (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(80px, 30%) 1fr auto', gap: 8, alignItems: 'center', margin: '3px 0' }}>
      <div style={{ fontSize: 12, color: 'var(--tx2)', fontWeight: kalin ? 800 : 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={ad}>{ad}</div>
      <div style={{ position: 'relative', height: 18 }}>
        <div style={{ position: 'absolute', left: `${x(Math.min(a, b))}%`, width: `${Math.max(0.6, Math.abs(x(b) - x(a)))}%`, top: 2, bottom: 2, background: renk, borderRadius: 4 }} />
      </div>
      <div style={{ fontSize: 11.5, fontWeight: 800, minWidth: 64, textAlign: 'right', whiteSpace: 'nowrap' }}>{metin}</div>
    </div>
  )
  return (
    <div role="img" aria-label={`Gelir ${SAYI(gelir)} TL, giderler toplamı ${SAYI(gelir - kalan)} TL, kalan ${SAYI(kalan)} TL`}>
      <Satir ad="Gelir" a={0} b={gelir} renk="var(--gr)" metin={tl(gelir)} kalin />
      {adimlar.map((s) => <Satir key={s.ad} ad={s.ad} a={s.bas} b={s.son} renk="color-mix(in srgb, var(--re) 70%, transparent)" metin={`−${SAYI(s.tutar)}`} />)}
      <Satir ad="Kalan" a={0} b={kalan} renk={kalan >= 0 ? 'var(--okul-c)' : 'var(--re)'} metin={tl(kalan)} kalin />
    </div>
  )
}

export default function IlkMaas({ veri, ogrenci }) {
  const meslekler = veri.kazanc?.meslekler || []
  const veriliMeslek = meslekler.filter((m) => m.guncel_tahmin_net_tl)
  const [kaynak, setKaynak] = useState(veriliMeslek.length ? 'meslek' : veri.asgari ? 'asgari' : 'kendi')
  const [meslekAd, setMeslekAd] = useState(veriliMeslek[0]?.meslek || '')
  const [kamuId, setKamuId] = useState(veri.kamu?.[0]?.id || '')
  const [kamuUc, setKamuUc] = useState('alt')
  const [kendi, setKendi] = useState('')
  const [il, setIl] = useState('')
  const [gider, setGider] = useState(null)
  const [hata, setHata] = useState(null)
  const [konut, setKonut] = useState('arkadas')
  const [ulasim, setUlasim] = useState('toplu')
  const [elle, setElle] = useState({})   // kalem kodu → öğrencinin girdiği tutar ('' = boş)
  const [ayirma, setAyirma] = useState('')
  const [hedef, setHedef] = useState('')

  useEffect(() => {
    let iptal = false
    api.isHayatiGiderler(il || undefined).then((g) => {
      if (iptal) return
      setGider(g)
      if (!il && ogrenci?.il && g.iller?.includes(ogrenci.il)) setIl(ogrenci.il)
    }).catch((e) => { if (!iptal) setHata(e.detail || 'Gider verileri yüklenemedi.') })
    return () => { iptal = true }
  }, [il]) // eslint-disable-line react-hooks/exhaustive-deps

  // Gelir
  const gelirBilgi = useMemo(() => {
    if (kaynak === 'meslek') {
      const m = veriliMeslek.find((x) => x.meslek === meslekAd)
      return m ? { tutar: m.guncel_tahmin_net_tl, tahmin: true, aciklama: `${m.meslek}: “${m.veri_grup_adi || m.grup_adi}” grubunun ortalama kazancı (ilk maaş değil, ortalama)`, kaynak: `${m.kaynak} · TÜİK veri yılı ${m.veri_yili} · ${m.guncel_donem} asgari ücretiyle güncellendi` } : null
    }
    if (kaynak === 'kamu') {
      const k = (veri.kamu || []).find((x) => String(x.id) === String(kamuId))
      if (!k) return null
      const t = kamuUc === 'alt' ? k.net_min : kamuUc === 'ust' ? k.net_max : (k.net_min != null && k.net_max != null ? (k.net_min + k.net_max) / 2 : null)
      return t == null ? null : { tutar: t, tahmin: false, aciklama: `${k.kadro_adi} (${kamuUc === 'alt' ? 'aralığın alt ucu' : kamuUc === 'ust' ? 'aralığın üst ucu' : 'aralığın ortası'})`, kaynak: `${k.kaynak} · dönem ${k.donem}` }
    }
    if (kaynak === 'asgari' && veri.asgari) return { tutar: veri.asgari.net, tahmin: false, aciklama: `Net asgari ücret (${veri.asgari.donem})`, kaynak: veri.asgari.kaynak }
    if (kaynak === 'kendi' && Number(kendi) > 0) return { tutar: Number(kendi), tahmin: false, aciklama: 'Senin girdiğin tutar', kaynak: null }
    return null
  }, [kaynak, meslekAd, kamuId, kamuUc, kendi, veri, veriliMeslek])

  // Giderler: veriden gelen değer (yaşam tarzı çarpanıyla) ya da öğrencinin girdiği; ikisi de yoksa boş
  const plan = useMemo(() => kalemPlani(konut, ulasim), [konut, ulasim])
  const veriKalem = useMemo(() => Object.fromEntries((gider?.kalemler || []).map((k) => [k.kalem_kodu, k])), [gider])
  const ekKalemler = useMemo(() => (gider?.kalemler || []).filter((k) => !BILINEN.includes(k.kalem_kodu))
    .map((k) => ({ kod: `ek_${k.kalem_kodu}`, ad: k.ad, kaynakKod: k.kalem_kodu, carpan: 1 })), [gider])
  const satirlar = [...plan, ...ekKalemler].map((p) => {
    const d = p.kaynakKod ? veriKalem[p.kaynakKod] : null
    const veridenTutar = d?.aylik_tutar != null ? Math.round(d.aylik_tutar * p.carpan) : null
    const girilen = elle[p.kod]
    const tutar = girilen !== undefined ? (girilen === '' ? null : Number(girilen)) : veridenTutar
    return { ...p, veri: d, veridenTutar, girilen, tutar }
  })
  const doluSatirlar = satirlar.filter((s) => s.tutar != null && s.tutar > 0)
  const bosSayisi = satirlar.filter((s) => s.tutar == null).length
  const veriYok = !gider?.kalemler?.length
  const toplamGider = doluSatirlar.reduce((a, s) => a + s.tutar, 0)
  const gelir = gelirBilgi?.tutar || 0
  const kalan = gelir - toplamGider
  const ayirmaSayi = Number(ayirma) > 0 ? Number(ayirma) : null
  const hedefSayi = Number(hedef) > 0 ? Number(hedef) : null

  const kaynakListesi = [...new Map(satirlar.filter((s) => s.veri && s.tutar === s.veridenTutar)
    .map((s) => [`${s.veri.kaynak}|${s.veri.tarih}`, s.veri])).values()]

  return (
    <div>
      <div className="card" style={{ padding: '16px 18px' }}>
        <Baslik no="1">Gelirin: ilk maaşın ne olsun?</Baslik>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          <Secenek secili={kaynak === 'meslek'} onClick={() => setKaynak('meslek')}>💼 Bölümün meslekleri</Secenek>
          {veri.kamu?.length > 0 && <Secenek secili={kaynak === 'kamu'} onClick={() => setKaynak('kamu')}>🏛️ Kamu kadrosu</Secenek>}
          {veri.asgari && <Secenek secili={kaynak === 'asgari'} onClick={() => setKaynak('asgari')}>⚖️ Asgari ücret</Secenek>}
          <Secenek secili={kaynak === 'kendi'} onClick={() => setKaynak('kendi')}>✏️ Kendi tutarım</Secenek>
        </div>
        <div style={{ marginTop: 10 }}>
          {kaynak === 'meslek' && (veriliMeslek.length ? (
            <select className="yp-sec" style={{ width: '100%', maxWidth: 460 }} value={meslekAd} onChange={(e) => setMeslekAd(e.target.value)} aria-label="Meslek seç">
              {meslekler.map((m) => <option key={m.meslek} value={m.meslek} disabled={!m.guncel_tahmin_net_tl}>{m.meslek}{m.guncel_tahmin_net_tl ? ` — ~${SAYI(m.guncel_tahmin_net_tl)} TL (tahmini)` : ' — veri yok'}</option>)}
            </select>
          ) : <div style={{ fontSize: 12.5, color: 'var(--tx2)' }}>📭 Bu bölümün meslekleri için henüz kazanç verisi yok. Asgari ücretle ya da kendi gireceğin bir tutarla hesaplayabilirsin.</div>)}
          {kaynak === 'kamu' && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <select className="yp-sec" style={{ flex: '1 1 240px' }} value={kamuId} onChange={(e) => setKamuId(e.target.value)} aria-label="Kamu kadrosu">
                {veri.kamu.map((k) => <option key={k.id} value={k.id}>{k.kadro_adi} ({tl(k.net_min)} – {tl(k.net_max)})</option>)}
              </select>
              <select className="yp-sec" value={kamuUc} onChange={(e) => setKamuUc(e.target.value)} aria-label="Aralıkta nerede">
                <option value="alt">Alt uç</option><option value="orta">Orta</option><option value="ust">Üst uç</option>
              </select>
            </div>
          )}
          {kaynak === 'kendi' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input className="yp-sec" type="number" inputMode="numeric" min={0} step={500} value={kendi} onChange={(e) => setKendi(e.target.value)} placeholder="Aylık net TL" style={{ width: 170 }} aria-label="Aylık net maaş" />
              <span className="yp-ince">TL / ay (net)</span>
            </div>
          )}
          {gelirBilgi && (
            <div style={{ marginTop: 8, fontSize: 13 }}>
              <b style={{ fontSize: 18 }}>{tl(gelirBilgi.tutar)}</b>{gelirBilgi.tahmin && <TahminEtiketi />}
              <div className="yp-ince" style={{ marginTop: 2 }}>{gelirBilgi.aciklama}{gelirBilgi.kaynak ? ` · Kaynak: ${gelirBilgi.kaynak}` : ''}</div>
              {gelirBilgi.tahmin && <div className="yp-ince" style={{ marginTop: 2 }}>İlk iş maaşı çoğu zaman bu ortalamanın altındadır; daha temkinli bir hesap için asgari ücreti de dene.</div>}
            </div>
          )}
        </div>
      </div>

      <div className="card" style={{ padding: '16px 18px' }}>
        <Baslik no="2">Nerede ve nasıl yaşıyorsun?</Baslik>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 10 }}>
          <label htmlFor="ihm-il" style={{ fontSize: 13, fontWeight: 700 }}>Şehir</label>
          <select id="ihm-il" className="yp-sec" value={il} onChange={(e) => { setIl(e.target.value); setElle({}) }}>
            <option value="">Türkiye geneli</option>
            {(gider?.iller || []).map((x) => <option key={x} value={x}>{x}</option>)}
          </select>
          {gider && !gider.iller?.length && <span className="yp-ince">Henüz il bazında veri yüklenmedi.</span>}
        </div>
        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--tx3)', marginBottom: 4 }}>KONUT</div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {KONUT.map((k) => <Secenek key={k.kod} secili={konut === k.kod} onClick={() => { setKonut(k.kod); setElle({}) }}>{k.ikon} {k.ad}</Secenek>)}
        </div>
        <div className="yp-ince" style={{ marginTop: 4 }}>{KONUT.find((k) => k.kod === konut).not}</div>
        <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--tx3)', margin: '10px 0 4px' }}>ULAŞIM</div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {ULASIM.map((k) => <Secenek key={k.kod} secili={ulasim === k.kod} onClick={() => setUlasim(k.kod)}>{k.ikon} {k.ad}</Secenek>)}
        </div>
      </div>

      <div className="card" style={{ padding: '16px 18px' }}>
        <Baslik no="3">Aylık giderlerin</Baslik>
        {hata && <div className="auth-error">{hata}</div>}
        {(veriYok || bosSayisi > 0) && (
          <div style={{ fontSize: 12.5, lineHeight: 1.55, background: 'var(--aml)', color: 'var(--tx)', padding: '8px 10px', borderRadius: 10, marginBottom: 10 }}>
            {veriYok ? '📭 Bu şehir için henüz gider verisi yüklenmedi; kalemler boş geliyor.' : `📝 ${bosSayisi} kalem için veri yok, boş bıraktık.`}{' '}
            Bu kalemleri <b>rehber öğretmeninle ya da ailenle birlikte doldurun</b> — evdeki faturalar ve market fişleri iyi bir başlangıç.
          </div>
        )}
        <div style={{ display: 'grid', gap: 6 }}>
          {satirlar.map((s) => (
            <div key={s.kod} style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8, alignItems: 'center', borderBottom: '1px dashed var(--bor)', paddingBottom: 6 }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{s.ad}</div>
                <div className="yp-ince">
                  {s.veri && s.tutar === s.veridenTutar
                    ? `${s.veri.turkiye_geneli ? 'Türkiye geneli' : s.veri.il} · ${s.veri.kaynak}${s.veri.tarih ? ` (${new Date(s.veri.tarih).toLocaleDateString('tr-TR')})` : ''}${s.carpan !== 1 ? ' · yarısı' : ''}`
                    : s.tutar != null ? 'senin girdiğin' : 'veri yok — sen doldur'}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <input className="yp-sec" type="number" inputMode="numeric" min={0} step={50} aria-label={s.ad}
                  value={s.tutar ?? ''} placeholder="—" style={{ width: 104, textAlign: 'right' }}
                  onChange={(e) => setElle((x) => ({ ...x, [s.kod]: e.target.value === '' ? '' : Math.max(0, Number(e.target.value)) }))} />
                <span className="yp-ince">TL</span>
              </div>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 13.5, fontWeight: 800 }}>
          <span>Toplam gider</span><span>{tl(toplamGider)}</span>
        </div>
      </div>

      <div className="card" style={{ padding: '16px 18px', borderLeft: `4px solid ${kalan >= 0 ? 'var(--okul-c)' : 'var(--re)'}` }}>
        <Baslik no="4">Ay sonunda ne kalıyor?</Baslik>
        {!gelirBilgi ? (
          <div style={{ fontSize: 12.5, color: 'var(--tx2)' }}>Önce 1. adımda bir gelir seç ya da gir.</div>
        ) : !doluSatirlar.length ? (
          <div style={{ fontSize: 12.5, color: 'var(--tx2)' }}>Hesap için en az bir gider kalemini doldur.</div>
        ) : (
          <>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 10 }}>
              <div><div className="yp-kpi-e">Gelir</div><div style={{ fontSize: 18, fontWeight: 800 }}>{tl(gelir)}{gelirBilgi.tahmin && <TahminEtiketi />}</div></div>
              <div><div className="yp-kpi-e">Gider</div><div style={{ fontSize: 18, fontWeight: 800 }}>{tl(toplamGider)}</div></div>
              <div><div className="yp-kpi-e">Kalan</div><div style={{ fontSize: 18, fontWeight: 800, color: kalan >= 0 ? 'var(--gr)' : 'var(--re)' }}>{tl(kalan)}</div></div>
            </div>
            <Selale gelir={gelir} kalemler={doluSatirlar} />
            <div style={{ marginTop: 10, fontSize: 12.5, lineHeight: 1.55, color: 'var(--tx2)', background: 'var(--sur2)', padding: '8px 10px', borderRadius: 10 }}>
              {kalan < 0
                ? 'Bu düzende ay sonunu getirmek zor görünüyor. Bu çok yaygın bir ilk yıl gerçeği: birçok genç çalışan ilk yıllarda ailesiyle ya da ev arkadaşıyla yaşayarak, toplu taşıma kullanarak ve sosyal harcamaları planlayarak dengeyi kuruyor. Yukarıdaki seçimleri değiştirip farkı gör.'
                : bosSayisi > 0
                  ? `Şimdilik ${tl(kalan)} kalıyor, ama ${bosSayisi} kalem boş. Onları doldurunca tablo değişebilir.`
                  : 'Dengeyi kurabiliyorsun. Küçük de olsa düzenli birikim, ilk iş değişikliği ya da beklenmedik bir gider için en iyi güvencedir.'}
            </div>
          </>
        )}
      </div>

      <div className="card" style={{ padding: '16px 18px' }}>
        <Baslik no="5">Birikim hesabı</Baslik>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', fontSize: 13 }}>
          <span>Ayda</span>
          <input className="yp-sec" type="number" inputMode="numeric" min={0} step={100} value={ayirma} onChange={(e) => setAyirma(e.target.value)} placeholder={kalan > 0 ? SAYI(kalan) : 'TL'} style={{ width: 120 }} aria-label="Aylık ayıracağın tutar" />
          <span>TL ayırırsam,</span>
          <input className="yp-sec" type="number" inputMode="numeric" min={0} step={1000} value={hedef} onChange={(e) => setHedef(e.target.value)} placeholder="hedef TL" style={{ width: 130 }} aria-label="Hedef tutar" />
          <span>TL'lik hedefe kaç ayda ulaşırım?</span>
        </div>
        {ayirmaSayi && (
          <div style={{ marginTop: 10, fontSize: 13.5, lineHeight: 1.6 }}>
            {hedefSayi && <div>🎯 <b>{Math.ceil(hedefSayi / ayirmaSayi)} ayda</b> {tl(hedefSayi)} biriktirirsin.</div>}
            <div>📅 1 yılda {tl(ayirmaSayi * 12)}, 3 yılda {tl(ayirmaSayi * 36)} birikir.</div>
            {gelirBilgi && kalan >= 0 && ayirmaSayi > kalan && <div style={{ color: 'var(--re)', fontSize: 12.5 }}>Bu tutar ay sonunda kalan paradan ({tl(kalan)}) fazla.</div>}
            <div className="yp-ince">Faiz, enflasyon ve maaş artışı hesaba katılmadı; basit toplam.</div>
          </div>
        )}
      </div>

      {(kaynakListesi.length > 0 || gelirBilgi?.kaynak) && (
        <div className="yp-ince" style={{ lineHeight: 1.6 }}>
          <b>Kaynaklar:</b> {gelirBilgi?.kaynak && <>Gelir — {gelirBilgi.kaynak}. </>}
          {kaynakListesi.map((k, i) => <span key={i}>Gider — {k.kaynak}{k.tarih ? ` (${new Date(k.tarih).toLocaleDateString('tr-TR')})` : ''}. </span>)}
        </div>
      )}
    </div>
  )
}
