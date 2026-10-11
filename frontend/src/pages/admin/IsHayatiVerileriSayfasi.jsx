// [2026-10-10] İş Hayatı Verileri (süper admin): TÜİK istihdam göstergeleri ve kazanç yapısı yükleme (Excel/CSV → sütun eşleştirme
// → önizleme → kaydet), meslek → ISCO eşleştirmesi, kamu maaşları, asgari ücret ve yaşam giderleri. Her kayıtta kaynak + tarih/yıl zorunlu;
// tüm değişiklikler denetim kaydına yazılır (sunucu tarafı).
import { Fragment, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'
import { tarih } from '../../components/yonetim/ortak'

const SEKMELER = [
  ['istihdam', '📊 TÜİK İstihdam Göstergeleri'],
  ['kazanc', '💰 Kazanç Yapısı (meslek grubu)'],
  ['isco', '🔗 Meslek – ISCO'],
  ['kamu', '🏛️ Kamu Maaşları'],
  ['asgari', '🧾 Asgari Ücret ve Yaşam Giderleri'],
  ['ai', '🔭 Yapay zekâ etkisi'],   // [2026-10-11] Gelecekte Bu Meslek
]
const KAZANC_GRUBU = { cok_yuksek: 'Çok yüksek', yuksek: 'Yüksek', orta: 'Orta', dusuk: 'Düşük', cok_dusuk: 'Çok düşük' }
const DUZEY = { lisans: 'Lisans', onlisans: 'Önlisans' }
const sayi = (v, k = 2) => (v == null || v === '' ? '—' : Number(v).toLocaleString('tr-TR', { maximumFractionDigits: k }))

function dosyayiOku(dosya) {
  return new Promise((coz, reddet) => {
    const r = new FileReader()
    r.onload = () => coz(String(r.result).split(',')[1] || '')
    r.onerror = () => reddet(new Error('Dosya okunamadı.'))
    r.readAsDataURL(dosya)
  })
}

// ----------------------------------------------------------------------------- yükleme sihirbazı (istihdam / kazanç)
function Sihirbaz({ tur, ozet, onBitti }) {
  const [dosya, setDosya] = useState(null)          // { ad, b64 }
  const [okuma, setOkuma] = useState(null)          // /dosya/oku yanıtı
  const [baslikSatiri, setBaslikSatiri] = useState(null)
  const [eslesme, setEslesme] = useState({})
  const [varsayilanDuzey, setVarsayilanDuzey] = useState('lisans')
  const [tutarTuru, setTutarTuru] = useState('yillik')
  const [onizleme, setOnizleme] = useState(null)
  const [satirlar, setSatirlar] = useState([])
  const [filtre, setFiltre] = useState('hepsi')
  const [veriYili, setVeriYili] = useState('')
  const [kaynak, setKaynak] = useState('')
  const [asgariBrut, setAsgariBrut] = useState('')
  const [ayniYil, setAyniYil] = useState(true)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [sonuc, setSonuc] = useState(null)

  const govde = (ek = {}) => ({ tur, dosya_adi: dosya.ad, icerik_base64: dosya.b64, ...ek })
  async function calistir(f) {
    setBekle(true); setHata(null)
    try { await f() } catch (e) { setHata(e.detail || e.message || 'İşlem başarısız.') }
    setBekle(false)
  }
  // [2026-10-10] TÜİK Veri Portalı bağlantısından indir → aynı akış
  const [baglanti, setBaglanti] = useState('')
  const baglantidanIndir = () => calistir(async () => {
    setOkuma(null); setOnizleme(null); setSonuc(null)
    const d = await api.ihBaglantiIndir(baglanti.trim())
    setDosya({ ad: d.dosya_adi, b64: d.icerik_base64 })
    const v = await api.ihDosyaOku({ tur, dosya_adi: d.dosya_adi, icerik_base64: d.icerik_base64 })
    setOkuma(v); setBaslikSatiri(v.baslik_satiri); setEslesme(v.oneri || {})
  })
  async function dosyaSec(e) {
    const f = e.target.files?.[0]
    if (!f) return
    setOkuma(null); setOnizleme(null); setSonuc(null)
    await calistir(async () => {
      const b64 = await dosyayiOku(f)
      setDosya({ ad: f.name, b64 })
      const v = await api.ihDosyaOku({ tur, dosya_adi: f.name, icerik_base64: b64 })
      setOkuma(v); setBaslikSatiri(v.baslik_satiri); setEslesme(v.oneri || {})
    })
  }
  const baslikDegistir = (n) => calistir(async () => {
    const v = await api.ihDosyaOku(govde({ baslik_satiri: n }))
    setOkuma(v); setBaslikSatiri(v.baslik_satiri); setEslesme(v.oneri || {}); setOnizleme(null)
  })
  const onizle = () => calistir(async () => {
    const ek = { baslik_satiri: baslikSatiri, eslesme, varsayilan_duzey: varsayilanDuzey || null, tutar_turu: tutarTuru }
    const v = tur === 'istihdam' ? await api.ihIstihdamOnizle(govde(ek)) : await api.ihKazancOnizle(govde(ek))
    setOnizleme(v); setSatirlar(v.satirlar)
  })
  // Kazanç: veri yılındaki asgari brüt ücretin ay ağırlıklı ortalaması (asgari ücret tablosundan) — öneri
  const asgariOneri = useMemo(() => {
    const y = Number(veriYili)
    if (!y || !ozet?.asgari) return null
    const donemler = ozet.asgari.filter((a) => a.yururluk_tarihi?.startsWith(String(y))).sort((a, b) => a.yururluk_tarihi.localeCompare(b.yururluk_tarihi))
    if (!donemler.length) return null
    let top = 0
    donemler.forEach((d, i) => {
      const bas = Number(d.yururluk_tarihi.slice(5, 7))
      const son = i + 1 < donemler.length ? Number(donemler[i + 1].yururluk_tarihi.slice(5, 7)) : 13
      top += d.brut * (son - bas)
    })
    const basAy = Number(donemler[0].yururluk_tarihi.slice(5, 7))
    return Math.round((top / (13 - basAy)) * 100) / 100
  }, [veriYili, ozet])

  const kaydet = () => calistir(async () => {
    if (!veriYili || !kaynak.trim()) throw new Error('Veri yılı ve kaynak zorunlu.')
    if (tur === 'istihdam') {
      const r = await api.ihIstihdamKaydet({
        dosya_adi: dosya.ad, veri_yili: Number(veriYili), kaynak: kaynak.trim(), ayni_yili_degistir: ayniYil,
        satirlar: satirlar.map((s) => ({ program_adi_kaynak: s.program_adi_kaynak, duzey: s.duzey, istihdam_orani: s.istihdam_orani,
          is_bulma_suresi_ay: s.is_bulma_suresi_ay, alan_uyum_orani: s.alan_uyum_orani, kazanc_grubu: s.kazanc_grubu, kazanc_tl: s.kazanc_tl,
          bolum_id: s.bolum_id || null })),
      })
      setSonuc(`${r.eklenen} satır kaydedildi (${r.eslesen} bölümle eşleşti, ${r.eslesmeyen} eşleşmesiz). ${r.silinen ? `Aynı yılın önceki ${r.silinen} satırı silindi.` : ''}`)
    } else {
      if (!Number(asgariBrut)) throw new Error('O yılın asgari brüt ücreti zorunlu.')
      const gecerli = satirlar.filter((s) => s.isco_kodu && Number(s.brut_aylik_ortalama_tl) > 0)
      const r = await api.ihKazancKaydet({ dosya_adi: dosya.ad, veri_yili: Number(veriYili), kaynak: kaynak.trim(), asgari_brut_o_yil: Number(asgariBrut),
        satirlar: gecerli.map((s) => ({ isco_kodu: String(s.isco_kodu), ad: s.ad, brut_aylik_ortalama_tl: Number(s.brut_aylik_ortalama_tl) })) })
      setSonuc(`${r.kaydedilen} meslek grubu kaydedildi${gecerli.length < satirlar.length ? ` (${satirlar.length - gecerli.length} hatalı satır atlandı)` : ''}.`)
    }
    setOnizleme(null); setOkuma(null); setDosya(null)
    onBitti?.()
  })

  const satirGuncelle = (i, d) => setSatirlar((l) => l.map((s, j) => (j === i ? { ...s, ...d } : s)))
  const gorunen = satirlar.map((s, i) => [s, i]).filter(([s]) => filtre === 'hepsi' || (filtre === 'esle' ? !s.bolum_id : filtre === 'oneri' ? s.durum === 'oneri' : s.hatalar?.length))

  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="ct">{tur === 'istihdam' ? 'Yeni TÜİK istihdam göstergeleri dosyası yükle' : 'Kazanç Yapısı Araştırması tablosu yükle'}</div>
      <div className="yp-ince" style={{ marginBottom: 10 }}>
        {tur === 'istihdam'
          ? 'TÜİK Yükseköğretim İstihdam Göstergeleri tablosunu (.xlsx ya da .csv) seçin. Başlık satırı ve sütunlar otomatik tahmin edilir; kontrol edip düzeltin. Program adları sistemdeki bölümlerle eşleştirilir ("(İngilizce)", "(Burslu)" gibi ekler yok sayılır).'
          : 'TÜİK Kazanç Yapısı Araştırması meslek grubu tablosunu (.xlsx / .csv) seçin. Meslek grubu kodu (ISCO-08) ayrı sütunda değilse adın başındaki rakamdan ya da grup adından bulunur. Yıllık tutarlar 12\'ye bölünür.'}
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 8 }}>
        <input className="yp-sec" style={{ flex: '1 1 340px', minWidth: 0 }} value={baglanti} onChange={(e) => setBaglanti(e.target.value)}
          placeholder="TÜİK Veri Portalı indirme bağlantısı (https://…tuik.gov.tr/…)" aria-label="TÜİK indirme bağlantısı" />
        <button className="btn" disabled={bekle || !baglanti.trim()} onClick={baglantidanIndir}>{bekle ? 'İndiriliyor…' : '🔗 Bağlantıdan al'}</button>
      </div>
      <div className="yp-ince" style={{ marginBottom: 8 }}>
        Portalda tablonun indirme simgesine sağ tıklayıp "Bağlantı adresini kopyala"yı seçin. Yalnızca tuik.gov.tr bağlantıları kabul edilir. Bağlantı çalışmazsa dosyayı indirip aşağıdan seçin.
      </div>
      <input type="file" accept=".xlsx,.xlsm,.csv" onChange={dosyaSec} disabled={bekle} />
      {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}
      {sonuc && <div style={{ marginTop: 10, color: 'var(--gr)', fontWeight: 700, fontSize: 13 }}>✓ {sonuc}</div>}

      {okuma && (
        <div style={{ marginTop: 14 }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 10 }}>
            <label className="yp-ince">Başlık satırı (0'dan):
              <input className="yp-sec" type="number" min={0} max={50} value={baslikSatiri ?? 0} style={{ width: 70, marginLeft: 6 }}
                onChange={(e) => baslikDegistir(Number(e.target.value))} />
            </label>
            <span className="yp-ince">{okuma.satir_sayisi} veri satırı</span>
            {tur === 'istihdam' && (
              <label className="yp-ince">Düzey sütunu yoksa:
                <select className="yp-sec" value={varsayilanDuzey} onChange={(e) => setVarsayilanDuzey(e.target.value)} style={{ marginLeft: 6 }}>
                  <option value="lisans">Lisans</option><option value="onlisans">Önlisans</option><option value="">Belirtme</option>
                </select>
              </label>
            )}
            {tur === 'kazanc' && (
              <label className="yp-ince">Tutar türü:
                <select className="yp-sec" value={tutarTuru} onChange={(e) => setTutarTuru(e.target.value)} style={{ marginLeft: 6 }}>
                  <option value="yillik">Yıllık (12'ye bölünür)</option><option value="aylik">Aylık</option>
                </select>
              </label>
            )}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))', gap: 8, marginBottom: 10 }}>
            {okuma.alanlar.map((a) => (
              <label key={a.kod} style={{ fontSize: 12, fontWeight: 600 }}>
                {a.ad}{a.zorunlu && <span style={{ color: 'var(--re)' }}> *</span>}
                <select className="yp-sec" style={{ width: '100%', marginTop: 3 }} value={eslesme[a.kod] ?? ''}
                  onChange={(e) => setEslesme((m) => ({ ...m, [a.kod]: e.target.value === '' ? null : Number(e.target.value) }))}>
                  <option value="">— yok —</option>
                  {okuma.basliklar.map((b) => <option key={b.i} value={b.i}>{b.i + 1}. {b.ad}</option>)}
                </select>
              </label>
            ))}
          </div>
          <div className="yp-tablo-kap" style={{ maxHeight: 220, marginBottom: 10 }}>
            <table className="yp-tablo">
              <thead><tr>{okuma.basliklar.map((b) => <th key={b.i}>{b.ad}</th>)}</tr></thead>
              <tbody>{okuma.ornek.map((r, i) => <tr key={i}>{okuma.basliklar.map((b) => <td key={b.i}>{r[b.i]}</td>)}</tr>)}</tbody>
            </table>
          </div>
          <button className="btn" disabled={bekle} onClick={onizle}>{bekle ? 'İşleniyor…' : 'Önizle →'}</button>
        </div>
      )}

      {onizleme && (
        <div style={{ marginTop: 16 }}>
          {onizleme.uyarilar?.map((u) => <div key={u} className="yp-ince" style={{ color: 'var(--am)' }}>⚠ {u}</div>)}
          {tur === 'istihdam' && (
            <div className="kc-filtre" style={{ marginTop: 8 }}>
              {[['hepsi', `Tümü (${satirlar.length})`], ['esle', `Bölümsüz (${satirlar.filter((s) => !s.bolum_id).length})`],
                ['oneri', `Öneri — kontrol et (${onizleme.ozet.oneri})`], ['hata', `Uyarılı (${onizleme.ozet.hatali})`]].map(([k, ad]) =>
                <button key={k} className={filtre === k ? 'aktif' : ''} onClick={() => setFiltre(k)}>{ad}</button>)}
            </div>
          )}
          <div className="yp-tablo-kap" style={{ maxHeight: 460 }}>
            {tur === 'istihdam' ? (
              <table className="yp-tablo">
                <thead><tr><th>Program (dosyada)</th><th>Düzey</th><th>İstihdam %</th><th>İş bulma (ay)</th><th>Alan uyumu %</th><th>Kazanç</th><th>Sistemdeki bölüm</th></tr></thead>
                <tbody>
                  {gorunen.map(([s, i]) => (
                    <tr key={i}>
                      <td>{s.program_adi_kaynak}{s.hatalar?.map((h) => <div key={h} className="yp-ince" style={{ color: 'var(--am)' }}>⚠ {h}</div>)}</td>
                      <td>{DUZEY[s.duzey] || '—'}</td><td>{sayi(s.istihdam_orani)}</td><td>{sayi(s.is_bulma_suresi_ay)}</td><td>{sayi(s.alan_uyum_orani)}</td>
                      <td>{KAZANC_GRUBU[s.kazanc_grubu] || (s.kazanc_tl != null ? `${sayi(s.kazanc_tl, 0)} TL` : '—')}</td>
                      <td style={{ minWidth: 260 }}>
                        <select className="yp-sec" style={{ width: '100%' }} value={s.bolum_id || ''} onChange={(e) => satirGuncelle(i, { bolum_id: Number(e.target.value) || null })}>
                          <option value="">— eşleşmesiz bırak —</option>
                          {onizleme.bolumler.map((b) => <option key={b.id} value={b.id}>{b.ad}</option>)}
                        </select>
                        <div className="yp-ince" style={{ marginTop: 3 }}>
                          {s.durum === 'otomatik' && <span className="kc-durum kc-durum-gr">✓ otomatik</span>}
                          {s.durum === 'oneri' && <span className="kc-durum kc-durum-am">öneri %{s.skor}</span>}
                          {!s.bolum_id && s.adaylar?.map((a) => (
                            <button key={a.id} className="kl-ilgi" style={{ marginLeft: 4 }} onClick={() => satirGuncelle(i, { bolum_id: a.id })}>{a.ad} <small>%{a.skor}</small></button>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <table className="yp-tablo">
                <thead><tr><th>ISCO kodu</th><th>Meslek grubu (dosyada)</th><th>ISCO-08 adı</th><th>Aylık brüt ort. (TL)</th><th /></tr></thead>
                <tbody>
                  {satirlar.map((s, i) => (
                    <tr key={i}>
                      <td><input className="yp-sec" style={{ width: 60 }} value={s.isco_kodu || ''} onChange={(e) => satirGuncelle(i, { isco_kodu: e.target.value.replace(/\D/g, '').slice(0, 2) || null })} /></td>
                      <td>{s.ad}</td>
                      <td className="yp-ince">{onizleme.isco?.[s.isco_kodu] || '—'}</td>
                      <td><input className="yp-sec" style={{ width: 110 }} value={s.brut_aylik_ortalama_tl ?? ''} onChange={(e) => satirGuncelle(i, { brut_aylik_ortalama_tl: e.target.value })} /></td>
                      <td>{s.hatalar?.map((h) => <div key={h} className="yp-ince" style={{ color: 'var(--am)' }}>⚠ {h}</div>)}
                        <button className="yp-mini" onClick={() => setSatirlar((l) => l.filter((_, j) => j !== i))}>Çıkar</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end', marginTop: 12 }}>
            <label style={{ fontSize: 12, fontWeight: 600 }}>Veri yılı *<br />
              <input className="yp-sec" type="number" min={2000} max={2100} value={veriYili} onChange={(e) => setVeriYili(e.target.value)} style={{ width: 100 }} /></label>
            <label style={{ fontSize: 12, fontWeight: 600, flex: 1, minWidth: 260 }}>Kaynak * <span className="yp-ince">(ör. "TÜİK, Yükseköğretim İstihdam Göstergeleri, 2024 — yayım tarihi")</span><br />
              <input className="yp-sec" value={kaynak} onChange={(e) => setKaynak(e.target.value)} style={{ width: '100%' }} /></label>
            {tur === 'kazanc' && (
              <label style={{ fontSize: 12, fontWeight: 600 }}>O yılın asgari brüt ücreti (aylık) *<br />
                <input className="yp-sec" value={asgariBrut} onChange={(e) => setAsgariBrut(e.target.value)} style={{ width: 120 }} />
                {asgariOneri && <button className="yp-mini" style={{ marginLeft: 6 }} onClick={() => setAsgariBrut(String(asgariOneri))} title="Asgari ücret tablosundaki dönemlerin ay ağırlıklı ortalaması">Öneri: {sayi(asgariOneri)}</button>}
              </label>
            )}
            {tur === 'istihdam' && (
              <label className="yp-ince" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <input type="checkbox" checked={ayniYil} onChange={(e) => setAyniYil(e.target.checked)} /> Aynı yılın eski verisini sil (yerine yaz)
              </label>
            )}
            <button className="btn" disabled={bekle || !veriYili || !kaynak.trim()} onClick={kaydet}>{bekle ? 'Kaydediliyor…' : 'Kaydet'}</button>
          </div>
        </div>
      )}
    </div>
  )
}

// ----------------------------------------------------------------------------- genel düzenlenebilir tablo
// kolonlar: [{ kod, ad, tip: 'metin'|'sayi'|'tarih'|'liste'|'secim', secenekler?: {deger: etiket}, zorunlu?, genislik? }]
function hucreMetni(k, v) {
  if (v == null || v === '') return '—'
  if (k.tip === 'sayi') return sayi(v)
  if (k.tip === 'liste') return (Array.isArray(v) ? v : []).join(', ') || '—'
  if (k.tip === 'secim') return k.secenekler?.[v] || v
  return String(v)
}
function Girdi({ k, deger, onDegis }) {
  const ortak = { className: 'yp-sec', style: { width: k.genislik || '100%' } }
  if (k.tip === 'secim') {
    return (
      <select {...ortak} value={deger ?? ''} onChange={(e) => onDegis(e.target.value || null)}>
        <option value="">—</option>
        {Object.entries(k.secenekler || {}).map(([d, e]) => <option key={d} value={d}>{e}</option>)}
      </select>
    )
  }
  const v = k.tip === 'liste' && Array.isArray(deger) ? deger.join(', ') : (deger ?? '')
  return <input {...ortak} type={k.tip === 'tarih' ? 'date' : 'text'} value={v} placeholder={k.ipucu || ''} onChange={(e) => onDegis(e.target.value)} />
}

function KayitTablosu({ tablo, baslik, aciklama, kolonlar, varsayilan = {}, filtreler = {}, onDegisti }) {
  const [v, setV] = useState(null)
  const [duzenle, setDuzenle] = useState(null)   // { id|null, veri }
  const [ara, setAra] = useState('')
  const [hata, setHata] = useState(null)
  const yukle = () => api.ihKayitlar(tablo, { q: ara, ...filtreler }).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [tablo, ara, JSON.stringify(filtreler)]) // eslint-disable-line react-hooks/exhaustive-deps

  async function kaydet() {
    setHata(null)
    try {
      if (duzenle.id) await api.ihKayitDuzenle(tablo, duzenle.id, duzenle.veri)
      else await api.ihKayitEkle(tablo, duzenle.veri)
      setDuzenle(null); await yukle(); onDegisti?.()
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
  }
  async function sil(r) {
    if (!window.confirm('Bu kayıt silinsin mi?')) return
    try { await api.ihKayitSil(tablo, r.id); await yukle(); onDegisti?.() } catch (e) { setHata(e.detail || 'Silinemedi.') }
  }
  const formSatiri = (
    <tr className="secili">
      {kolonlar.map((k) => <td key={k.kod}>{k.tip === 'hesap' ? '—' : <Girdi k={k} deger={duzenle?.veri[k.kod]} onDegis={(d) => setDuzenle((x) => ({ ...x, veri: { ...x.veri, [k.kod]: d } }))} />}</td>)}
      <td style={{ whiteSpace: 'nowrap' }}><button className="yp-mini" onClick={kaydet}>Kaydet</button> <button className="yp-mini" onClick={() => setDuzenle(null)}>Vazgeç</button></td>
    </tr>
  )
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
        <div className="ct" style={{ margin: 0 }}>{baslik}{v ? ` (${v.toplam})` : ''}</div>
        <input className="yp-sec" value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Ara…" style={{ marginLeft: 'auto' }} />
        <button className="yp-mini" onClick={() => setDuzenle({ id: null, veri: { ...varsayilan } })}>+ Yeni kayıt</button>
      </div>
      {aciklama && <div className="yp-ince" style={{ marginBottom: 8 }}>{aciklama}</div>}
      {hata && <div className="auth-error">{hata}</div>}
      <div className="yp-tablo-kap" style={{ maxHeight: 520 }}>
        <table className="yp-tablo">
          <thead><tr>{kolonlar.map((k) => <th key={k.kod}>{k.ad}{k.zorunlu ? ' *' : ''}</th>)}<th /></tr></thead>
          <tbody>
            {duzenle && !duzenle.id && formSatiri}
            {(v?.satirlar || []).map((r) => (duzenle?.id === r.id ? <Fragment key={r.id}>{formSatiri}</Fragment> : (
              <tr key={r.id}>
                {kolonlar.map((k) => <td key={k.kod}>{k.goster ? k.goster(r) : hucreMetni(k, r[k.kod])}</td>)}
                <td style={{ whiteSpace: 'nowrap' }}>
                  <button className="yp-mini" onClick={() => setDuzenle({ id: r.id, veri: Object.fromEntries(kolonlar.filter((k) => k.tip !== 'hesap').map((k) => [k.kod, r[k.kod]])) })}>Düzenle</button>{' '}
                  <button className="yp-mini" onClick={() => sil(r)}>Sil</button>
                </td>
              </tr>
            )))}
          </tbody>
        </table>
        {v && v.satirlar.length === 0 && !duzenle && <div className="bos-durum">Kayıt yok.</div>}
      </div>
    </div>
  )
}

// ----------------------------------------------------------------------------- yükleme geçmişi
function Yuklemeler({ tur, yenile, onDegisti }) {
  const [l, setL] = useState(null)
  useEffect(() => { api.ihYuklemeler().then(setL).catch(() => setL([])) }, [yenile])
  const liste = (l || []).filter((y) => y.tur === tur)
  if (!liste.length) return null
  async function geriAl(y) {
    if (!window.confirm(`${y.veri_yili} yılı yüklemesi (${y.dosya_adi || 'dosya'}) ve bu yüklemeyle gelen satırlar silinsin mi?`)) return
    await api.ihYuklemeSil(y.id); setL(await api.ihYuklemeler()); onDegisti?.()
  }
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="ct">Yükleme geçmişi</div>
      <table className="yp-tablo">
        <thead><tr><th>Zaman</th><th>Dosya</th><th>Veri yılı</th><th>Kaynak</th><th>Satır</th><th>Eşleşen</th><th>Yükleyen</th><th /></tr></thead>
        <tbody>{liste.map((y) => (
          <tr key={y.id}>
            <td>{tarih(y.zaman)}</td><td>{y.dosya_adi || '—'}</td><td>{y.veri_yili}</td><td className="yp-ince">{y.kaynak}</td><td>{y.satir}</td>
            <td>{y.eslesen}{y.eslesmeyen?.length ? <div className="yp-ince" title={y.eslesmeyen.join('\n')}>{y.eslesmeyen.length} eşleşmesiz</div> : null}</td>
            <td>{y.yukleyen}</td><td><button className="yp-mini" onClick={() => geriAl(y)}>Geri al</button></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

// ----------------------------------------------------------------------------- sekmeler
function IstihdamSekmesi({ ozet, yenileOzet }) {
  const [yil, setYil] = useState('')
  const [yenile, setYenile] = useState(0)
  const [bolumler, setBolumler] = useState([])
  useEffect(() => { api.bolumleriListele().then((l) => setBolumler(l || [])).catch(() => {}) }, [])
  const bolumSecenek = useMemo(() => Object.fromEntries(bolumler.map((b) => [b.id, b.ad])), [bolumler])
  const bitti = () => { setYenile((x) => x + 1); yenileOzet() }
  return (
    <>
      {ozet?.guncelleme && !ozet.guncelleme.guncel && (
        <div className="card" style={{ marginBottom: 12, borderLeft: '4px solid var(--am)', background: 'color-mix(in srgb, var(--am) 8%, var(--sur))' }}>
          <b>🔔 Güncelleme zamanı:</b> {ozet.guncelleme.son_veri_yili
            ? `Sistemdeki son veri ${ozet.guncelleme.son_veri_yili} yılına ait; TÜİK ${ozet.guncelleme.beklenen_veri_yili} verisini yayımlamış olabilir.`
            : 'Sistemde henüz TÜİK istihdam verisi yok.'} TÜİK genellikle bu tabloyu Temmuz ayında yayımlar; aşağıya portal bağlantısını yapıştırarak yükleyebilirsiniz.
        </div>
      )}
      {ozet?.istihdam?.length > 0 && (
        <div className="yp-kpi-grid">
          {ozet.istihdam.map((y) => (
            <div key={y.veri_yili} className="yp-kpi"><div className="yp-kpi-e">Veri yılı {y.veri_yili}</div>
              <div className="yp-kpi-d">{y.satir}</div><div className="yp-kpi-a">{y.eslesen} satır · {y.bolum} bölüm eşleşti</div></div>
          ))}
        </div>
      )}
      <Sihirbaz tur="istihdam" ozet={ozet} onBitti={bitti} />
      <Yuklemeler tur="istihdam" yenile={yenile} onDegisti={bitti} />
      <div className="kc-filtre">
        <span className="yp-ince">Veri yılı:</span>
        <button className={!yil ? 'aktif' : ''} onClick={() => setYil('')}>Tümü</button>
        {(ozet?.istihdam || []).map((y) => <button key={y.veri_yili} className={yil === y.veri_yili ? 'aktif' : ''} onClick={() => setYil(y.veri_yili)}>{y.veri_yili}</button>)}
      </div>
      <KayitTablosu key={yenile} tablo="istihdam_gostergeleri" baslik="Yüklü istihdam göstergeleri" filtreler={{ veri_yili: yil }} onDegisti={yenileOzet}
        aciklama="Eşleşmesiz satırları buradan da bir bölüme bağlayabilirsiniz. Değerler dosyadakiyle aynı kalmalı; düzeltme gerekiyorsa dosyayı yeniden yükleyin."
        kolonlar={[
          { kod: 'program_adi_kaynak', ad: 'Program (kaynakta)', tip: 'metin', zorunlu: true },
          { kod: 'bolum_id', ad: 'Bölüm', tip: 'secim', secenekler: bolumSecenek, goster: (r) => r.bolum_ad || <span style={{ color: 'var(--am)' }}>eşleşmesiz</span> },
          { kod: 'duzey', ad: 'Düzey', tip: 'secim', secenekler: DUZEY, genislik: 100 },
          { kod: 'istihdam_orani', ad: 'İstihdam %', tip: 'sayi', genislik: 70 },
          { kod: 'is_bulma_suresi_ay', ad: 'İş bulma (ay)', tip: 'sayi', genislik: 70 },
          { kod: 'alan_uyum_orani', ad: 'Alan uyumu %', tip: 'sayi', genislik: 70 },
          { kod: 'kazanc_grubu', ad: 'Kazanç grubu', tip: 'secim', secenekler: KAZANC_GRUBU, genislik: 110 },
          { kod: 'veri_yili', ad: 'Yıl', tip: 'sayi', zorunlu: true, genislik: 70 },
          { kod: 'kaynak', ad: 'Kaynak', tip: 'metin', zorunlu: true },
        ]} />
    </>
  )
}

function KazancSekmesi({ ozet, yenileOzet }) {
  const [yenile, setYenile] = useState(0)
  const bitti = () => { setYenile((x) => x + 1); yenileOzet() }
  return (
    <>
      <div className="card" style={{ marginBottom: 16, fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.55 }}>
        Öğrenciye gösterilen maaş tahmini: <b>meslek grubu ortalama brüt kazancı ÷ o yılın asgari brüt ücreti × güncel asgari brüt</b>; net ≈ güncel net/brüt
        oranıyla. Bu yüzden her satırda <b>o yılın asgari brüt ücreti</b> zorunludur (birden çok dönem varsa ay ağırlıklı ortalama).
        Güncel asgari ücret: {ozet?.guncel_asgari ? <b>{ozet.guncel_asgari.donem} · brüt {sayi(ozet.guncel_asgari.brut)} TL · net {sayi(ozet.guncel_asgari.net)} TL</b> : <b style={{ color: 'var(--am)' }}>tanımlı değil</b>}.
        Meslek eşleşmesi önce 2 haneli ISCO alt ana grubunda aranır, yoksa 1 haneli ana gruba düşer.
      </div>
      <Sihirbaz tur="kazanc" ozet={ozet} onBitti={bitti} />
      <Yuklemeler tur="kazanc" yenile={yenile} onDegisti={bitti} />
      <KayitTablosu key={yenile} tablo="kazanc_meslek_gruplari" baslik="Meslek grubu kazançları" onDegisti={yenileOzet}
        kolonlar={[
          { kod: 'isco_kodu', ad: 'ISCO', tip: 'metin', zorunlu: true, genislik: 60 },
          { kod: 'ad', ad: 'Meslek grubu', tip: 'metin', zorunlu: true },
          { kod: 'brut_aylik_ortalama_tl', ad: 'Aylık brüt ort. (TL)', tip: 'sayi', zorunlu: true, genislik: 110 },
          { kod: 'veri_yili', ad: 'Veri yılı', tip: 'sayi', zorunlu: true, genislik: 70 },
          { kod: 'asgari_brut_o_yil', ad: 'O yılın asgari brütü', tip: 'sayi', zorunlu: true, genislik: 100 },
          { kod: 'kat', ad: 'Asgari ücret katı', tip: 'hesap', goster: (r) => (r.asgari_brut_o_yil ? `${sayi(r.brut_aylik_ortalama_tl / r.asgari_brut_o_yil)}×` : '—') },
          { kod: 'kaynak', ad: 'Kaynak', tip: 'metin', zorunlu: true },
        ]} />
    </>
  )
}

function IscoSekmesi() {
  const [v, setV] = useState(null)
  const [q, setQ] = useState('')
  const [filtre, setFiltre] = useState('bos')
  const [hata, setHata] = useState(null)
  const [mesaj, setMesaj] = useState(null)
  const yukle = () => api.ihMeslekIsco({ q, filtre }).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { const t = setTimeout(yukle, 250); return () => clearTimeout(t) }, [q, filtre]) // eslint-disable-line react-hooks/exhaustive-deps
  async function kaydet(ad, kod) {
    setHata(null)
    try { await api.ihMeslekIscoKaydet(ad, kod); await yukle() } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
  }
  async function jsonYukle() {
    const r = await api.ihMeslekIscoJson(); setMesaj(`${r.eklenen} meslek eklendi.`); await yukle()
  }
  const o = v?.ozet
  return (
    <>
      <div className="card" style={{ marginBottom: 14, fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.55 }}>
        Bölüm detayındaki her meslek adı bir ISCO-08 alt ana grubuna (2 hane) bağlanır; öğrencinin gördüğü maaş tahmini bu gruptan gelir.
        İlk eşleştirme ad + bölüm bağlamına göre otomatik yapıldı (<b>yüksek</b>: ad mesleği açıkça belirliyor, <b>orta</b>: makul ama tartışmalı,
        <b> boş</b>: belirsiz). Elle düzeltilen satırlar açılışta ezilmez.
        <div style={{ marginTop: 6 }}><button className="yp-mini" onClick={jsonYukle}>JSON'daki eksik meslekleri ekle</button>{mesaj && <span className="yp-ince" style={{ marginLeft: 8 }}>{mesaj}</span>}</div>
      </div>
      {o && (
        <div className="yp-kpi-grid">
          <div className="yp-kpi"><div className="yp-kpi-e">Meslek</div><div className="yp-kpi-d">{o.toplam}</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Kodlu</div><div className="yp-kpi-d" style={{ color: 'var(--gr)' }}>{o.kodlu}</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Yüksek güven</div><div className="yp-kpi-d">{o.yuksek}</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Orta güven</div><div className="yp-kpi-d">{o.orta}</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Boş</div><div className="yp-kpi-d" style={{ color: 'var(--am)' }}>{o.bos}</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Elle düzeltilen</div><div className="yp-kpi-d">{o.elle}</div></div>
          {o.eksik > 0 && <div className="yp-kpi"><div className="yp-kpi-e">Tabloda olmayan</div><div className="yp-kpi-d" style={{ color: 'var(--re)' }}>{o.eksik}</div></div>}
        </div>
      )}
      <div className="kc-filtre">
        {[['bos', 'Boş'], ['orta', 'Orta güven'], ['yuksek', 'Yüksek güven'], ['elle', 'Elle'], ['eksik', 'Tabloda olmayan'], ['hepsi', 'Tümü']].map(([k, ad]) =>
          <button key={k} className={filtre === k ? 'aktif' : ''} onClick={() => setFiltre(k)}>{ad}</button>)}
        <input className="yp-sec" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Meslek, bölüm ya da ISCO kodu ara…" style={{ marginLeft: 'auto', minWidth: 240 }} />
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="yp-tablo-kap">
        <table className="yp-tablo">
          <thead><tr><th>Meslek</th><th>Bölümler</th><th>Güven</th><th>ISCO-08 alt ana grup</th></tr></thead>
          <tbody>{(v?.satirlar || []).slice(0, 400).map((s) => (
            <tr key={s.meslek_adi}>
              <td><b>{s.meslek_adi}</b>{!s.kullanimda && <div className="yp-ince">artık bölüm detayında yok</div>}</td>
              <td className="yp-ince">{s.bolumler.join(', ')}{s.bolum_sayisi > s.bolumler.length ? ` +${s.bolum_sayisi - s.bolumler.length}` : ''}</td>
              <td>{s.kaynak === 'elle' ? <span className="kc-durum kc-durum-pu">elle</span> : s.guven === 'yuksek' ? <span className="kc-durum kc-durum-gr">yüksek</span>
                : s.guven === 'orta' ? <span className="kc-durum kc-durum-am">orta</span> : <span className="kc-durum kc-durum-tx3">{s.kaynak === 'eksik' ? 'tabloda yok' : 'boş'}</span>}</td>
              <td style={{ minWidth: 300 }}>
                <select className="yp-sec" style={{ width: '100%' }} value={s.isco_kodu || ''} onChange={(e) => kaydet(s.meslek_adi, e.target.value)}>
                  <option value="">— belirsiz —</option>
                  {(v?.isco || []).map((g) => <option key={g.kod} value={g.kod}>{g.kod} · {g.ad}</option>)}
                </select>
              </td>
            </tr>
          ))}</tbody>
        </table>
        {v && v.satirlar.length > 400 && <div className="yp-ince" style={{ padding: 10 }}>İlk 400 satır gösteriliyor; aramayı daraltın.</div>}
        {v && v.satirlar.length === 0 && <div className="bos-durum">Bu filtrede meslek yok.</div>}
      </div>
    </>
  )
}

const bugun = () => new Date().toISOString().slice(0, 10)

function KamuSekmesi() {
  return (
    <KayitTablosu tablo="kamu_maaslari" baslik="Kamu kadro maaşları"
      aciklama="Anahtar kelimeler bölüm adı ya da meslek adlarında geçiyorsa öğrenci bu kadroyu ilgili bölümde görür (ör. “öğretmen”, “hemşire”, “mühendis”). Net tutarlar resmî maaş tablosundan, dönemiyle birlikte girilmeli."
      varsayilan={{ donem: `${new Date().getFullYear()}-${new Date().getMonth() < 6 ? 1 : 2}` }}
      kolonlar={[
        { kod: 'kadro_adi', ad: 'Kadro', tip: 'metin', zorunlu: true },
        { kod: 'anahtar_kelimeler', ad: 'Anahtar kelimeler (virgülle)', tip: 'liste' },
        { kod: 'net_min', ad: 'Net en az (TL)', tip: 'sayi', genislik: 100 },
        { kod: 'net_max', ad: 'Net en çok (TL)', tip: 'sayi', genislik: 100 },
        { kod: 'donem', ad: 'Dönem', tip: 'metin', zorunlu: true, genislik: 80, ipucu: '2026-1' },
        { kod: 'kaynak', ad: 'Kaynak', tip: 'metin', zorunlu: true },
        { kod: 'aciklama', ad: 'Açıklama', tip: 'metin' },
      ]} />
  )
}

// [2026-10-11] Gelecekte Bu Meslek: meslek_grubu_ai_etkisi (tohum: ILO WP140 Tablo A1; dağılım ve 4 haneli meslekler yalnızca tohumdan gelir)
const AI_DUZEY = { dusuk: 'Az değişecek (düşük)', orta: 'Kısmen değişecek (orta)', yuksek: 'En çok değişecek (yüksek)', belirsiz: 'Belirsiz' }
function AiEtkisiSekmesi() {
  return (
    <KayitTablosu tablo="meslek_grubu_ai_etkisi" baslik="Meslek grubu – üretken yapay zekâ etkisi"
      aciklama="Öğrenci İş Hayatı → Gelecekte Bu Meslek sekmesinde görür. Her ISCO kodu için en yeni veri yılı kullanılır; 2 haneli satır yoksa 1 haneli ana grup aranır. Puan yalnızca kaynak bir grup puanı yayımladıysa girilir (ILO WP140 grup puanı yayımlamaz: boş). Düzey, Tablo A1'deki 4 haneli mesleklerin sayımıyla türetilmiştir (bkz. docs/IS_HAYATI.md). Görev/beceri metinleri backend/app/data/ai_etkisi_gruplar.json'dadır."
      varsayilan={{ duzey: 'belirsiz', veri_yili: new Date().getFullYear() }}
      kolonlar={[
        { kod: 'isco_kodu', ad: 'ISCO', tip: 'metin', zorunlu: true, genislik: 60, ipucu: '25' },
        { kod: 'duzey', ad: 'Düzey', tip: 'secim', secenekler: AI_DUZEY, zorunlu: true, genislik: 170 },
        { kod: 'puan', ad: 'Puan (0–1)', tip: 'sayi', genislik: 80 },
        { kod: 'aciklama', ad: 'Açıklama', tip: 'metin' },
        { kod: 'kaynak', ad: 'Kaynak', tip: 'metin', zorunlu: true },
        { kod: 'kaynak_bolum', ad: 'Tablo / sayfa', tip: 'metin', genislik: 160 },
        { kod: 'veri_yili', ad: 'Yıl', tip: 'sayi', zorunlu: true, genislik: 70 },
      ]} />
  )
}

function AsgariSekmesi({ ozet, yenileOzet }) {
  const kalemler = ozet?.gider_kalemleri || {}
  return (
    <>
      <KayitTablosu tablo="asgari_ucret" baslik="Asgari ücret (aylık, 16 yaş üstü)" onDegisti={yenileOzet}
        aciklama="Öğrenciye gösterilen “güncel” asgari ücret, yürürlük tarihi bugünden önce olan en yeni dönemdir. Kazanç tahmini bu değerle hesaplanır."
        varsayilan={{ yururluk_tarihi: bugun() }}
        kolonlar={[
          { kod: 'donem', ad: 'Dönem', tip: 'metin', zorunlu: true, genislik: 80, ipucu: '2026 / 2026-2' },
          { kod: 'brut', ad: 'Brüt (TL)', tip: 'sayi', zorunlu: true, genislik: 100 },
          { kod: 'net', ad: 'Net (TL)', tip: 'sayi', zorunlu: true, genislik: 100 },
          { kod: 'yururluk_tarihi', ad: 'Yürürlük', tip: 'tarih', zorunlu: true, genislik: 140 },
          { kod: 'kaynak', ad: 'Kaynak', tip: 'metin', zorunlu: true },
        ]} />
      <KayitTablosu tablo="yasam_giderleri" baslik="Yaşam giderleri (aylık)" onDegisti={yenileOzet}
        aciklama={`İl boş bırakılırsa Türkiye geneli sayılır; il satırı varsa öğrenci o ili seçtiğinde Türkiye geneli yerine o kullanılır. Önerilen kalem kodları: ${Object.entries(kalemler).map(([k, a]) => `${k} (${a})`).join(', ')}.`}
        varsayilan={{ tarih: bugun() }}
        kolonlar={[
          { kod: 'il', ad: 'İl (boş = Türkiye)', tip: 'metin', genislik: 120 },
          { kod: 'kalem_kodu', ad: 'Kalem kodu', tip: 'metin', zorunlu: true, genislik: 110, ipucu: 'kira_1_1' },
          { kod: 'ad', ad: 'Ad', tip: 'metin', zorunlu: true },
          { kod: 'aylik_tutar', ad: 'Aylık (TL)', tip: 'sayi', zorunlu: true, genislik: 100 },
          { kod: 'tarih', ad: 'Tarih', tip: 'tarih', zorunlu: true, genislik: 140 },
          { kod: 'kaynak', ad: 'Kaynak', tip: 'metin', zorunlu: true },
        ]} />
    </>
  )
}

export default function IsHayatiVerileriSayfasi() {
  const [params, setParams] = useSearchParams()
  const sekme = SEKMELER.some(([k]) => k === params.get('sekme')) ? params.get('sekme') : 'istihdam'
  const [ozet, setOzet] = useState(null)
  const [hata, setHata] = useState(null)
  const yenileOzet = () => api.ihVeriOzet().then(setOzet).catch((e) => setHata(e.detail || 'Özet yüklenemedi.'))
  useEffect(() => { yenileOzet() }, [])
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">İş Hayatı Verileri</div>
        <div className="ps">Öğrencinin İş Hayatı sayfasındaki resmî veriler. Her kayıtta kaynak ve veri yılı/tarihi zorunludur; öğrenci ekranında
          veri yılı ve kaynak her zaman görünür, tahminler “tahmini” etiketiyle gösterilir. Değişiklikler Audit Log'a yazılır.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="koc-sekmeler" role="tablist">
        {SEKMELER.map(([k, ad]) => (
          <button key={k} role="tab" aria-selected={sekme === k} className={sekme === k ? 'aktif' : ''}
            onClick={() => { const p = new URLSearchParams(params); p.set('sekme', k); setParams(p, { replace: true }) }}>{ad}</button>
        ))}
      </div>
      {sekme === 'istihdam' && <IstihdamSekmesi ozet={ozet} yenileOzet={yenileOzet} />}
      {sekme === 'kazanc' && <KazancSekmesi ozet={ozet} yenileOzet={yenileOzet} />}
      {sekme === 'isco' && <IscoSekmesi />}
      {sekme === 'kamu' && <KamuSekmesi />}
      {sekme === 'asgari' && <AsgariSekmesi ozet={ozet} yenileOzet={yenileOzet} />}
      {sekme === 'ai' && <AiEtkisiSekmesi />}
    </div>
  )
}
