import { useEffect, useState, useCallback, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import BolumAdi from '../components/BolumAdi'

// ============================================================
// Ana sayfa
// ============================================================
// [2026-10-03] Kategori etiketleri — grafik, kartlar ve plan AYNI göreli ölçekten gelir
const KATEGORI = {
  belirgin_ustun: { etiket: 'Belirgin güçlü', renk: 'var(--gr)', zemin: 'var(--grl)', grup: 'guclu' },
  ustun: { etiket: 'Güçlü', renk: 'var(--gr)', zemin: 'var(--grl)', grup: 'guclu' },
  beklenti: { etiket: 'Uyumlu', renk: 'var(--pu)', zemin: 'var(--pul)', grup: 'uyumlu' },
  altinda: { etiket: 'Gelişime açık', renk: 'var(--am)', zemin: 'var(--aml)', grup: 'gelisim' },
  belirgin_altinda: { etiket: 'Öncelikli gelişim', renk: 'var(--re)', zemin: 'var(--rel)', grup: 'gelisim' },
}
const DURUMLAR = [
  { kod: 'planlandi', etiket: 'Plana ekledim' },
  { kod: 'devam_ediyor', etiket: 'Yapıyorum' },
  { kod: 'tamamlandi', etiket: 'Tamamladım' },
]

function KategoriRozeti({ kategori }) {
  const k = KATEGORI[kategori] || KATEGORI.beklenti
  return (
    <span style={{ fontSize: 10.5, fontWeight: 700, color: k.renk, background: k.zemin, padding: '2px 8px', borderRadius: 20, whiteSpace: 'nowrap' }}>
      {k.etiket}
    </span>
  )
}

function Cip({ children, renk = 'var(--tx2)', zemin = 'var(--sur2)' }) {
  return <span style={{ fontSize: 10.5, fontWeight: 600, color: renk, background: zemin, padding: '2px 8px', borderRadius: 20, whiteSpace: 'nowrap' }}>{children}</span>
}

function KarsilastirmaSatiri({ g }) {
  const [acik, setAcik] = useState(false)
  return (
    <div style={{ marginBottom: 12 }}>
      <div onClick={() => setAcik(!acik)} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 5, cursor: 'pointer' }}>
        <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--tx2)' }}>{g.degisken_adi} <span style={{ color: 'var(--tx3)', fontWeight: 400 }}>{acik ? '▴' : 'ⓘ'}</span></div>
        <KategoriRozeti kategori={g.kategori} />
      </div>
      {acik && (
        <div style={{ fontSize: 11.5, color: 'var(--tx3)', margin: '0 0 6px', lineHeight: 1.45 }}>
          {g.nedir}{g.durum_tespiti ? <><br /><span style={{ color: 'var(--tx2)' }}>{g.durum_tespiti}</span></> : null}
        </div>
      )}
      <div className="mini-cubuk-track" style={{ width: '100%', marginBottom: 3 }}>
        <div className="mini-cubuk-fill" style={{ width: `${g.ogrenci_goreli ?? g.ogrenci_puan}%`, background: 'var(--pu)' }} />
      </div>
      <div className="mini-cubuk-track" style={{ width: '100%' }}>
        <div className="mini-cubuk-fill" style={{ width: `${g.bolum_goreli ?? g.bolum_beklenen}%`, background: 'var(--gr)' }} />
      </div>
    </div>
  )
}

// Tek bir yol haritası adımı: ne yapacağın, ne kadar sürer + [2026-10-09] adım adım "Nasıl yaparsın?",
// kontrol listesi olarak "Nasıl anlarsın?" ve ipucu (açılır-kapanır; sıradaki adımda açık gelir) + durum düğmeleri
function AdimKarti({ adim, onDurum, vurgulu = false, alanGoster = true }) {
  const bitti = adim.durum === 'tamamlandi'
  const detayVar = (adim.nasil && adim.nasil.length > 0) || (adim.kontrol && adim.kontrol.length > 0)
  const [acik, setAcik] = useState(vurgulu)
  return (
    <div className={`adim-kart${vurgulu ? ' vurgulu' : ''}${bitti && !vurgulu ? ' bitti' : ''}`}>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
        {alanGoster && <Cip renk="var(--pu)" zemin="var(--pul)">{adim.degisken_adi}</Cip>}
        <Cip>{adim.tur_etiket}</Cip>
        <Cip>⏱ {adim.sure}</Cip>
      </div>
      <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 4, textDecoration: bitti ? 'line-through' : 'none' }}>{bitti ? '✓ ' : ''}{adim.baslik}</div>
      <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5, marginBottom: 8 }}>{adim.aciklama}</div>

      {detayVar ? (
        <>
          <button type="button" className="adim-ac" aria-expanded={acik} onClick={() => setAcik(!acik)}>
            <span>{acik ? '▾' : '▸'}</span> {acik ? 'Ayrıntıları gizle' : `Nasıl yaparsın? · ${adim.nasil.length} adım`}
          </button>
          {acik ? (
            <div className="adim-detay">
              <div className="adim-detay-baslik">🛠️ Nasıl yaparsın?</div>
              <ol className="adim-nasil">
                {adim.nasil.map((m, i) => <li key={i}>{m}</li>)}
              </ol>
              {adim.kontrol.length > 0 && (
                <>
                  <div className="adim-detay-baslik">✅ Nasıl anlarsın? <span>Bunları yapabiliyorsan bu adım tamam:</span></div>
                  <ul className="adim-kontrol">
                    {adim.kontrol.map((m, i) => <li key={i}>{m}</li>)}
                  </ul>
                </>
              )}
              {adim.ipucu && <div className="adim-ipucu">💡 {adim.ipucu}</div>}
            </div>
          ) : (
            <div style={{ fontSize: 11.5, color: 'var(--tx3)', margin: '6px 0 8px' }}><b>Nasıl anlarsın?</b> {adim.olcut}</div>
          )}
        </>
      ) : (
        <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginBottom: 8 }}><b>Nasıl anlarsın?</b> {adim.olcut}</div>
      )}

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {DURUMLAR.map((d) => (
          <button key={d.kod} className={adim.durum === d.kod ? 'btn' : 'btn sec'} style={{ fontSize: 11.5, padding: '5px 10px' }}
            onClick={() => onDurum(adim.kod, adim.durum === d.kod ? null : d.kod)}>
            {adim.durum === d.kod ? '✓ ' : ''}{d.etiket}
          </button>
        ))}
      </div>
    </div>
  )
}

// ============================================================
// [2026-10-09] Sayfa başlık başlık sekmelere bölündü:
//   Özet · Yol Haritası · Güçlü Yönlerin · Bölümle Karşılaştırma · Gelişimin
// Hedef seçimi/değiştirme üstteki hedef kartının içinden açılır.
// ============================================================
const SEKMELER = [
  { kod: 'ozet', ad: 'Özet', ikon: '🧭' },
  { kod: 'yol', ad: 'Yol Haritası', ikon: '🗺️' },
  { kod: 'guclu', ad: 'Güçlü Yönlerin', ikon: '💪' },
  { kod: 'karsilastirma', ad: 'Bölümle Karşılaştırma', ikon: '📊' },
  { kod: 'gelisim', ad: 'Gelişimin', ikon: '📈' },
]

function Bolum({ baslik, alt, children, sag }) {
  return (
    <section className="koc-bolum">
      <div className="koc-bolum-bas">
        <div>
          <h2 className="koc-bolum-baslik">{baslik}</h2>
          {alt && <div className="koc-bolum-alt">{alt}</div>}
        </div>
        {sag}
      </div>
      {children}
    </section>
  )
}

function IlerlemeCubugu({ ilerleme }) {
  const { toplam, tamamlanan, devam_eden: devam } = ilerleme
  const yuzde = toplam ? Math.round((100 * tamamlanan) / toplam) : 0
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
        <span>Yol haritası ilerlemen{devam ? ` · ${devam} adım devam ediyor` : ''}</span>
        <span style={{ fontWeight: 700 }}>{tamamlanan} / {toplam} adım · %{yuzde}</span>
      </div>
      <div className="mini-cubuk-track" style={{ width: '100%', height: 10 }}>
        <div className="mini-cubuk-fill" style={{ width: `${yuzde}%`, background: 'var(--gr)' }} />
      </div>
    </div>
  )
}

function OdakKartlari({ plan }) {
  return (
    <div className="koc-grid">
      {plan.odak_alanlari.map((o) => (
        <div key={o.degisken_kod} className="card" style={{ margin: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <Cip renk="var(--pu)" zemin="var(--pul)">{o.oncelik_sirasi}. öncelik</Cip>
            <KategoriRozeti kategori={o.kategori} />
          </div>
          <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>{o.degisken_adi}</div>
          <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginBottom: 8 }}>{o.nedir}</div>
          {o.durum_tespiti && <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginBottom: 8, lineHeight: 1.5 }}>{o.durum_tespiti}</div>}
          <div style={{ fontSize: 12, lineHeight: 1.5 }}><b>Neden önemli?</b> {o.neden_onemli}</div>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------- 1) Özet
function OzetSekmesi({ plan, sayac, onDurum, sekmeyeGit }) {
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  return (
    <>
      <div className="koc-ozet-kutular">
        <button className="koc-ozet-kutu" onClick={() => sekmeyeGit('guclu')}>
          <b style={{ color: 'var(--gr)' }}>{sayac.guclu}</b><span>güçlü yön</span>
        </button>
        <button className="koc-ozet-kutu" onClick={() => sekmeyeGit('karsilastirma')}>
          <b style={{ color: 'var(--pu)' }}>{sayac.uyumlu}</b><span>bölümle uyumlu</span>
        </button>
        <button className="koc-ozet-kutu" onClick={() => sekmeyeGit('yol')}>
          <b style={{ color: 'var(--am)' }}>{sayac.gelisim}</b><span>gelişime açık</span>
        </button>
      </div>

      <Bolum baslik="👉 Sıradaki adımın" alt="Yol haritandaki en öncelikli adım. Tamamladıkça bir sonraki otomatik gelir.">
        <div className="card" style={{ margin: 0 }}>
          {plan.odak_alanlari.length > 0 && <div style={{ marginBottom: 14 }}><IlerlemeCubugu ilerleme={plan.ilerleme} /></div>}
          {plan.siradaki_adim
            ? <AdimKarti adim={plan.siradaki_adim} onDurum={onDurum} vurgulu />
            : <div className="ps" style={{ margin: 0 }}>🎉 Yol haritandaki tüm adımları tamamladın! Bir sonraki değerlendirme turunda gelişimini birlikte görelim.</div>}
          <button className="koc-link" onClick={() => sekmeyeGit('yol')}>Tüm yol haritasını gör →</button>
        </div>
      </Bolum>

      {plan.odak_alanlari.length > 0 ? (
        <Bolum baslik="🎯 Odak alanların" alt={`${plan.hedef_bolum_adi} için seni en çok ileri taşıyacak ${plan.odak_alanlari.length} alan.`}>
          <OdakKartlari plan={plan} />
        </Bolum>
      ) : (
        <div className="card">
          <div className="ps" style={{ margin: 0 }}>
            Harika — {plan.hedef_bolum_adi} için belirgin bir gelişim alanın görünmüyor. “Güçlü Yönlerin” sekmesindeki adımlarla bu avantajını büyütebilirsin.
          </div>
        </div>
      )}
    </>
  )
}

// ---------------------------------------------------------------- 2) Yol haritası
function YolHaritasiSekmesi({ plan, onDurum }) {
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  if (plan.odak_alanlari.length === 0) {
    return <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedef için belirgin bir gelişim alanın yok; “Güçlü Yönlerin” sekmesine göz at.</div></div>
  }
  return (
    <>
      <div className="card">
        <div className="ps" style={{ margin: '0 0 12px', fontSize: 12.5 }}>
          Her odak alanı için 3 aşamada somut adımlar var: önce bu hafta yapabileceğin küçük adımlar, sonra 1–3 ayda oturacak çalışmalar, en sonda kalıcı alışkanlıklar.
        </div>
        <IlerlemeCubugu ilerleme={plan.ilerleme} />
      </div>
      {plan.asamalar.map((a) => (
        <Bolum key={a.kod} baslik={a.baslik} alt={a.alt}
          sag={<span className="koc-asama-sayac">{a.tamamlanan}/{a.toplam} tamamlandı</span>}>
          {a.once_oncekine_odaklan && (
            <div className="koc-ipucu">İpucu: Önce bir önceki aşamanın adımlarına odaklan; bu aşamadaki adımlar onların üzerine kurulu.</div>
          )}
          <div className="koc-adim-grid">
            {a.adimlar.map((adim) => <AdimKarti key={adim.kod} adim={adim} onDurum={onDurum} />)}
          </div>
        </Bolum>
      ))}
      {plan.sonraki_alanlar.length > 0 && (
        <Bolum baslik="Sonra odaklanılacak alanlar" alt="Odak alanlarındaki adımları bitirdikçe bunlara geçebilirsin. Bir sonraki değerlendirme turunda öncelikler yeniden hesaplanır.">
          <div className="card" style={{ margin: 0, display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            {plan.sonraki_alanlar.map((s) => <span key={s.degisken_id} style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: 12.5 }}>{s.degisken_adi} <KategoriRozeti kategori={s.kategori} /></span>)}
          </div>
        </Bolum>
      )}
    </>
  )
}

// ---------------------------------------------------------------- 3) Güçlü yönler
function GucluSekmesi({ plan, onDurum }) {
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  if (!plan.guclu_yonler.length) return <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedefe göre öne çıkan güçlü yönün henüz yok. Katmanları yeniden değerlendirdiğinde güncellenir.</div></div>
  return (
    <>
      <div className="ps" style={{ marginBottom: 14 }}>Bu özelliklerin {plan.hedef_bolum_adi} için avantaj. Aşağıdaki adımlarla onları görünür bir başarıya dönüştürebilirsin.</div>
      {plan.guclu_yonler.map((g) => (
        <Bolum key={g.degisken_kod} baslik={`✓ ${g.degisken_adi}`} alt={g.neden_onemli} sag={<KategoriRozeti kategori={g.kategori} />}>
          <div className="koc-adim-grid">
            {g.adimlar.map((adim) => <AdimKarti key={adim.kod} adim={adim} onDurum={onDurum} alanGoster={false} />)}
          </div>
        </Bolum>
      ))}
    </>
  )
}

// ---------------------------------------------------------------- 4) Karşılaştırma
function KarsilastirmaSekmesi({ gelisim, hedef }) {
  const gruplar = {}
  gelisim.forEach((g) => {
    const anahtar = g.katman_kod || '?'
    if (!gruplar[anahtar]) gruplar[anahtar] = { ad: g.katman_adi || anahtar, satirlar: [] }
    gruplar[anahtar].satirlar.push(g)
  })
  const sira = Object.keys(gruplar).sort()
  const [secili, setSecili] = useState(sira[0])
  const grup = gruplar[secili] || gruplar[sira[0]]
  return (
    <div className="card">
      <div className="drl" style={{ marginBottom: 6 }}>
        <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
        <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
      </div>
      <div className="ps" style={{ margin: '0 0 14px', fontSize: 11.5 }}>
        Her katmanda, özelliklerinin kendi içindeki ağırlığı bölümün beklentisiyle karşılaştırılır. Çubuklar aynı ölçekte; etiket farkın yönünü gösterir. Açıklama için özelliğin adına dokun.
      </div>
      <div className="koc-katman-cipler">
        {sira.map((kod) => {
          const n = gruplar[kod].satirlar.filter((g) => KATEGORI[g.kategori]?.grup === 'gelisim').length
          return (
            <button key={kod} className={kod === secili ? 'aktif' : ''} onClick={() => setSecili(kod)}>
              {gruplar[kod].ad}{n > 0 && <span className="koc-cip-sayi">{n}</span>}
            </button>
          )
        })}
      </div>
      <div className="koc-karsilastirma-liste">
        {grup.satirlar.slice().sort((a, b) => a.degisken_adi.localeCompare(b.degisken_adi, 'tr')).map((g) => <KarsilastirmaSatiri key={g.degisken_id} g={g} />)}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- 5) Turlar arası gelişim
function GelisimSekmesi({ karsilastirma }) {
  if (!karsilastirma || karsilastirma.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 30 }}>
        <div style={{ fontSize: 30 }}>📈</div>
        <div style={{ fontWeight: 700, margin: '6px 0 4px' }}>Gelişimin ikinci değerlendirme turunda burada görünecek</div>
        <div className="ps" style={{ margin: 0 }}>Bir sonraki turu tamamladığında her özelliğindeki değişimi ilk turla karşılaştırıp burada göstereceğiz.</div>
      </div>
    )
  }
  return (
    <div className="ll">
      {karsilastirma.map((k) => (
        <div key={k.degisken_id} className="ob-card">
          <div className="ob-top">
            <div className="ob-body">
              <div className="ob-name">{k.degisken_adi}</div>
              <div className="ld">{k.eski_puan} → {k.yeni_puan} ({k.degisim > 0 ? '+' : ''}{k.degisim})</div>
              {k.yorum_metni && <div className="ld" style={{ marginTop: 4 }}>{k.yorum_metni}</div>}
            </div>
            <span className="bdg bdg-prog">{k.trend.replaceAll('_', ' ')}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function KoclukSayfasi() {
  const [hedef, setHedef] = useState(undefined) // undefined=yükleniyor, null=yok
  const [gelisim, setGelisim] = useState(null)
  const [plan, setPlan] = useState(null)
  const [karsilastirma, setKarsilastirma] = useState(null)
  const [hata, setHata] = useState(null)
  const [kilit, setKilit] = useState(null) // K5 bitmediyse backend 409 döner
  const [oneriler, setOneriler] = useState([])
  const [seciciAcik, setSeciciAcik] = useState(false)

  const [sorgu, setSorgu] = useState('')
  const [aramaSonuclari, setAramaSonuclari] = useState(null)
  const [onayBekleyenBolum, setOnayBekleyenBolum] = useState(null)
  const [params, setParams] = useSearchParams()
  const urlIslendi = useRef(false)
  const sekme = SEKMELER.some((s) => s.kod === params.get('sekme')) ? params.get('sekme') : 'ozet'
  function sekmeyeGit(kod) {
    const p = new URLSearchParams(params); p.set('sekme', kod); setParams(p, { replace: true })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  useEffect(() => {
    api.aktifHedefGetir().then(setHedef).catch(() => setHedef(null))
    api.siralamaGetir(5).then((l) => setOneriler(Array.isArray(l) ? l : [])).catch(() => setOneriler([]))
  }, [])

  const analiziYukle = useCallback(() => {
    setGelisim(null); setPlan(null); setKilit(null); setHata(null)
    api.gelisimAnaliziGetir().then(setGelisim).catch((e) => (e.status === 409 ? setKilit(e.detail) : setHata(e.detail)))
    api.gelisimPlaniGetir().then(setPlan).catch(() => {})
    api.turKarsilastirmasiGetir().then(setKarsilastirma).catch(() => {})
  }, [])

  useEffect(() => { if (hedef) analiziYukle() }, [hedef, analiziYukle])

  async function hedefSecmeyeCalis(bolumId) {
    setHata(null)
    try {
      const sonuc = await api.hedefSec(bolumId, false)
      setHedef(sonuc)
      setAramaSonuclari(null)
      setSorgu('')
      setSeciciAcik(false)
    } catch (err) {
      if (err.status === 409) setOnayBekleyenBolum(bolumId)
      else setHata(err.detail || 'Hedef seçilemedi.')
    }
  }

  // Keşfet'teki "Bu bölümü hedef olarak seç" butonu /koclugu?hedef=ID ile gelir
  useEffect(() => {
    const id = Number(params.get('hedef'))
    if (!urlIslendi.current && id && hedef !== undefined) {
      urlIslendi.current = true
      if (!hedef || hedef.bolum_id !== id) hedefSecmeyeCalis(id)
      params.delete('hedef'); setParams(params, { replace: true })
    }
  }, [params, hedef]) // eslint-disable-line react-hooks/exhaustive-deps

  async function ara(e) {
    e.preventDefault()
    if (sorgu.trim().length < 2) return
    try {
      setAramaSonuclari(await api.kesfetAra(sorgu.trim(), 8))
    } catch (err) {
      setHata(err.detail || 'Arama yapılamadı.')
    }
  }

  async function degisikligiOnayla() {
    try {
      const sonuc = await api.hedefSec(onayBekleyenBolum, true)
      setHedef(sonuc)
      setOnayBekleyenBolum(null)
      setAramaSonuclari(null)
      setSorgu('')
      setSeciciAcik(false)
    } catch (err) {
      setHata(err.detail || 'Hedef değiştirilemedi.')
    }
  }

  async function adimDurumu(kod, durum) {
    try {
      await api.adimDurumuGuncelle(kod, durum)
      setPlan(await api.gelisimPlaniGetir()) // ilerleme, sıradaki adım ve aşama uyarıları sunucuda yeniden hesaplanır
    } catch (err) {
      setHata(err.detail || 'Durum kaydedilemedi.')
    }
  }

  if (hedef === undefined) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const sayac = { guclu: 0, uyumlu: 0, gelisim: 0 }
  ;(gelisim || []).forEach((g) => { sayac[(KATEGORI[g.kategori] || KATEGORI.beklenti).grup] += 1 })
  const veriVar = hedef && gelisim && gelisim.length > 0

  const secici = (
    <div className="koc-secici">
      {oneriler.length > 0 && (
        <>
          <div className="ps" style={{ margin: '0 0 8px', fontSize: 12 }}>Sana en uygun bölümlerden seç:</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
            {oneriler.map((o) => (
              <button key={o.bolum_id} className="btn sec" style={{ fontSize: 12, padding: '6px 10px', opacity: hedef?.bolum_id === o.bolum_id ? 0.5 : 1 }}
                disabled={hedef?.bolum_id === o.bolum_id} onClick={() => hedefSecmeyeCalis(o.bolum_id)}>
                {o.bolum_adi} · %{Math.round(o.toplam_uyum)}
              </button>
            ))}
          </div>
          <div className="ps" style={{ margin: '0 0 8px', fontSize: 12 }}>ya da başka bir bölüm ara:</div>
        </>
      )}
      <form onSubmit={ara} style={{ display: 'flex', gap: 8, marginBottom: aramaSonuclari ? 14 : 0 }}>
        <input className="auth-input" style={{ flex: 1, margin: 0 }} value={sorgu} onChange={(e) => setSorgu(e.target.value)} placeholder="Bölüm ara..." />
        <button className="btn sec" type="submit">Ara</button>
      </form>
      {aramaSonuclari && (
        <div className="ll">
          {aramaSonuclari.length === 0 && <div className="ps" style={{ margin: 0 }}>Sonuç bulunamadı.</div>}
          {aramaSonuclari.map((s) => (
            <div key={s.bolum_id} className="lc" onClick={() => hedefSecmeyeCalis(s.bolum_id)}>
              <div className="lb-wrap"><div className="lt"><BolumAdi id={s.bolum_id} ad={s.bolum_adi} /></div></div>
              {s.toplam_uyum !== null && s.toplam_uyum !== undefined && <div className="ob-score">%{Math.round(s.toplam_uyum)}</div>}
            </div>
          ))}
        </div>
      )}
    </div>
  )

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Hedef Bölüm Koçluğu</div>
        <div className="ps">İstediğin bir bölümü hedef seç, kendini onunla karşılaştır ve adım adım gelişim planını takip et. Aynı anda yalnızca 1 aktif hedefin olabilir — odaklanman için.</div>
      </div>

      <div className="koc-kap">
        {/* --- Hedef kartı (hedef değiştirme bunun içinden açılır) --- */}
        {hedef ? (
          <div className="card koc-hedef">
            <div className="koc-hedef-ust">
              <div style={{ minWidth: 0 }}>
                <div className="ct" style={{ marginBottom: 4 }}>🎯 Şu anki hedefin</div>
                <div className="koc-hedef-ad"><BolumAdi id={hedef.bolum_id} ad={hedef.bolum_adi} /></div>
                {plan && plan.odak_alanlari.length > 0 && (
                  <div className="ps" style={{ margin: '6px 0 0', fontSize: 12 }}>
                    Yol haritası: {plan.ilerleme.tamamlanan}/{plan.ilerleme.toplam} adım tamamlandı
                  </div>
                )}
              </div>
              <button className="btn sec" onClick={() => setSeciciAcik(!seciciAcik)}>{seciciAcik ? 'Kapat ▲' : 'Hedefi değiştir'}</button>
            </div>
            {seciciAcik && <div style={{ borderTop: '1px solid var(--bor)', marginTop: 14, paddingTop: 14 }}>{secici}</div>}
          </div>
        ) : (
          <div className="card">
            <div className="ct">🎯 Bir hedef bölüm seç</div>
            <div className="ps" style={{ margin: '0 0 12px', fontSize: 12.5 }}>Hedef seçtiğinde seni o bölümle karşılaştırıp adım adım bir gelişim planı hazırlarız.</div>
            {secici}
          </div>
        )}

        {onayBekleyenBolum && (
          <div className="card" style={{ borderColor: 'var(--am)', background: 'var(--aml)' }}>
            <div style={{ fontSize: 13, marginBottom: 10 }}>
              Hedefini değiştirmek üzeresin. Eski hedefindeki ilerlemen silinmez, istersen ileride tekrar seçebilirsin. Devam etmek istiyor musun?
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn" onClick={degisikligiOnayla}>Evet, değiştir</button>
              <button className="btn sec" onClick={() => setOnayBekleyenBolum(null)}>Vazgeç</button>
            </div>
          </div>
        )}

        {hata && <div className="auth-error">{hata}</div>}

        {hedef && kilit && (
          <div className="card" style={{ borderColor: 'var(--am)', background: 'var(--aml)' }}>
            <div style={{ fontSize: 13 }}>{kilit}</div>
          </div>
        )}

        {hedef && gelisim && gelisim.length === 0 && (
          <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedef için henüz karşılaştırılacak veri yok — önce katmanlarını tamamla.</div></div>
        )}

        {/* --- Başlıklar --- */}
        {veriVar && (
          <>
            <div className="koc-sekmeler" role="tablist">
              {SEKMELER.map((s) => (
                <button key={s.kod} role="tab" aria-selected={sekme === s.kod} className={sekme === s.kod ? 'aktif' : ''} onClick={() => sekmeyeGit(s.kod)}>
                  <span aria-hidden="true">{s.ikon}</span> {s.ad}
                  {s.kod === 'yol' && plan && plan.ilerleme.toplam > 0 && <span className="koc-cip-sayi">{plan.ilerleme.tamamlanan}/{plan.ilerleme.toplam}</span>}
                </button>
              ))}
            </div>
            {sekme === 'ozet' && <OzetSekmesi plan={plan} sayac={sayac} onDurum={adimDurumu} sekmeyeGit={sekmeyeGit} />}
            {sekme === 'yol' && <YolHaritasiSekmesi plan={plan} onDurum={adimDurumu} />}
            {sekme === 'guclu' && <GucluSekmesi plan={plan} onDurum={adimDurumu} />}
            {sekme === 'karsilastirma' && <KarsilastirmaSekmesi gelisim={gelisim} hedef={hedef} />}
            {sekme === 'gelisim' && <GelisimSekmesi karsilastirma={karsilastirma} />}
          </>
        )}
      </div>
    </div>
  )
}
