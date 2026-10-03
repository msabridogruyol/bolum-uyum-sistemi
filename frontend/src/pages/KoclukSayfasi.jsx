import { useEffect, useState, useCallback, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

// ============================================================
// Filiz — AI Kariyer Koçu (sağ panel widget'ı)
// ============================================================
function FilizSohbetWidgeti() {
  const [oturumId, setOturumId] = useState(null)
  const [mesajlar, setMesajlar] = useState([])
  const [girdiMetni, setGirdiMetni] = useState('')
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [durum, setDurum] = useState('yukleniyor') // yukleniyor | hazir | kullanilamiyor
  const [bilgi, setBilgi] = useState(null)
  const sonaKaydirRef = useRef(null)

  useEffect(() => {
    api.aiKocOturumBaslat()
      .then((veri) => { setOturumId(veri.oturum_id); setDurum('hazir') })
      .catch(() => setDurum('kullanilamiyor'))
  }, [])

  useEffect(() => {
    sonaKaydirRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mesajlar])

  async function mesajGonder(e) {
    e.preventDefault()
    const metin = girdiMetni.trim()
    if (!metin || gonderiliyor || !oturumId) return

    setMesajlar((m) => [...m, { rol: 'ogrenci', icerik: metin }])
    setGirdiMetni('')
    setGonderiliyor(true)
    setBilgi(null)

    try {
      const cevap = await api.aiKocMesajGonder(oturumId, metin)
      setMesajlar((m) => [...m, { rol: 'asistan', icerik: cevap.asistan_yaniti }])
      if (cevap.oturum_kapandi_mi) {
        setBilgi('Bu sohbet tamamlandı — sayfayı yenileyip yeni bir sohbet başlatabilirsin.')
      }
    } catch (err) {
      setBilgi(err.detail || 'Mesaj gönderilemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  return (
    <div className="card" style={{ marginBottom: 0, display: 'flex', flexDirection: 'column', height: 560, padding: 0, overflow: 'hidden' }}>
      {/* Başlık — Filiz'in kimliği */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '14px 16px', borderBottom: '1px solid var(--bor)' }}>
        <div style={{
          width: 38, height: 38, borderRadius: '50%', background: 'var(--grl)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 19, flexShrink: 0,
        }}>
          🌱
        </div>
        <div>
          <div style={{ fontFamily: 'var(--fd)', fontSize: 14.5, fontWeight: 700 }}>Filiz</div>
          <div style={{ fontSize: 11, color: 'var(--tx3)', fontWeight: 600 }}>Kariyer Koçun</div>
        </div>
      </div>

      {durum === 'yukleniyor' && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--tx3)', fontSize: 12.5 }}>
          Hazırlanıyor…
        </div>
      )}

      {durum === 'kullanilamiyor' && (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: 24, gap: 6 }}>
          <div style={{ fontSize: 24 }}>🌱</div>
          <div style={{ fontSize: 12.5, color: 'var(--tx3)' }}>Filiz şu anda kullanılamıyor.</div>
        </div>
      )}

      {durum === 'hazir' && (
        <>
          <div style={{ flex: 1, overflowY: 'auto', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
            {mesajlar.length === 0 && (
              <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.6, background: 'var(--sur2)', padding: '12px 14px', borderRadius: 14, borderBottomLeftRadius: 4 }}>
                Merhaba! Ben Filiz 🌱 Hedefin, güçlü yönlerin ya da nereden başlayacağını bilemediğin bir konu hakkında konuşmak ister misin?
              </div>
            )}
            {mesajlar.map((m, i) => (
              <div
                key={i}
                style={{
                  alignSelf: m.rol === 'ogrenci' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  background: m.rol === 'ogrenci' ? 'var(--pu)' : 'var(--sur2)',
                  color: m.rol === 'ogrenci' ? '#fff' : 'var(--tx)',
                  padding: '10px 14px',
                  borderRadius: 14,
                  borderBottomRightRadius: m.rol === 'ogrenci' ? 4 : 14,
                  borderBottomLeftRadius: m.rol === 'asistan' ? 4 : 14,
                  fontSize: 13,
                  lineHeight: 1.55,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {m.icerik}
              </div>
            ))}
            {gonderiliyor && (
              <div style={{ alignSelf: 'flex-start', color: 'var(--tx3)', fontSize: 12, padding: '2px 14px' }}>
                Filiz yazıyor…
              </div>
            )}
            <div ref={sonaKaydirRef} />
          </div>

          {bilgi && <div style={{ fontSize: 11.5, color: 'var(--tx3)', padding: '0 16px 8px' }}>{bilgi}</div>}

          <form onSubmit={mesajGonder} style={{ display: 'flex', gap: 6, padding: '10px 12px', borderTop: '1px solid var(--bor)' }}>
            <input
              className="auth-input"
              style={{ flex: 1, fontSize: 13 }}
              value={girdiMetni}
              onChange={(e) => setGirdiMetni(e.target.value)}
              placeholder="Filiz'e bir şey sor..."
              disabled={gonderiliyor}
            />
            <button className="btn" type="submit" disabled={gonderiliyor || !girdiMetni.trim()} style={{ padding: '10px 14px' }}>
              ➤
            </button>
          </form>
        </>
      )}
    </div>
  )
}

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

// Tek bir yol haritası adımı: ne yapacağın, ne kadar sürer, bunu yaptığını nasıl anlarsın + durum
function AdimKarti({ adim, onDurum, vurgulu = false, alanGoster = true }) {
  const bitti = adim.durum === 'tamamlandi'
  return (
    <div style={{
      border: vurgulu ? '2px solid var(--pu)' : '1px solid var(--bor)', background: vurgulu ? 'var(--pul)' : 'var(--sur)',
      borderRadius: 12, padding: 12, marginBottom: 10, opacity: bitti && !vurgulu ? 0.6 : 1,
    }}>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
        {alanGoster && <Cip renk="var(--pu)" zemin="var(--pul)">{adim.degisken_adi}</Cip>}
        <Cip>{adim.tur_etiket}</Cip>
        <Cip>⏱ {adim.sure}</Cip>
      </div>
      <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 4, textDecoration: bitti ? 'line-through' : 'none' }}>{bitti ? '✓ ' : ''}{adim.baslik}</div>
      <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5, marginBottom: 6 }}>{adim.aciklama}</div>
      <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginBottom: 8 }}><b>Nasıl anlarsın?</b> {adim.olcut}</div>
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

function GelisimPlani({ plan, onDurum }) {
  const siradakiAsama = plan.siradaki_adim?.asama || 'simdi'
  const [acikAsama, setAcikAsama] = useState(siradakiAsama)
  const { toplam, tamamlanan, devam_eden: devam } = plan.ilerleme
  const yuzde = toplam ? Math.round((100 * tamamlanan) / toplam) : 0

  if (plan.odak_alanlari.length === 0) {
    return (
      <div className="card" style={{ marginTop: 20 }}>
        <div className="ct">Gelişim Yol Haritan</div>
        <div className="ps" style={{ margin: 0 }}>
          Harika — {plan.hedef_bolum_adi} için belirgin bir gelişim alanın görünmüyor. Aşağıdaki güçlü yön adımlarıyla bu avantajını büyütebilirsin.
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="ct" style={{ marginTop: 20 }}>Gelişim Yol Haritan</div>
      <div className="card">
        <div className="ps" style={{ margin: '0 0 12px', fontSize: 12.5 }}>
          {plan.hedef_bolum_adi} için seni en çok ileri taşıyacak <b>{plan.odak_alanlari.length} odak alanı</b> seçtik. Her alan için 3 aşamada somut adımlar var: önce bu hafta yapabileceğin küçük adımlar, sonra 1-3 ayda oturacak çalışmalar, en sonda kalıcı alışkanlıklar.
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
          <span>İlerlemen{devam ? ` · ${devam} adım devam ediyor` : ''}</span>
          <span style={{ fontWeight: 700 }}>{tamamlanan} / {toplam} adım · %{yuzde}</span>
        </div>
        <div className="mini-cubuk-track" style={{ width: '100%', height: 10 }}>
          <div className="mini-cubuk-fill" style={{ width: `${yuzde}%`, background: 'var(--gr)' }} />
        </div>
        {plan.siradaki_adim && (
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--pu)', marginBottom: 6 }}>👉 SIRADAKİ ADIMIN</div>
            <AdimKarti adim={plan.siradaki_adim} onDurum={onDurum} vurgulu />
          </div>
        )}
        {!plan.siradaki_adim && <div className="ps" style={{ marginTop: 12 }}>🎉 Yol haritandaki tüm adımları tamamladın! Bir sonraki değerlendirme turunda gelişimini birlikte görelim.</div>}
      </div>

      {/* Odak alanları — neden bu alanlar? */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12 }}>
        {plan.odak_alanlari.map((o) => (
          <div key={o.degisken_kod} className="card" style={{ marginBottom: 0 }}>
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

      {/* 3 aşama */}
      {plan.asamalar.map((a) => {
        const acik = acikAsama === a.kod
        return (
          <div key={a.kod} className="card" style={{ marginTop: 12 }}>
            <div onClick={() => setAcikAsama(acik ? '' : a.kod)} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', gap: 8 }}>
              <div>
                <div className="ct" style={{ marginBottom: 2 }}>{a.baslik}</div>
                <div className="ps" style={{ margin: 0, fontSize: 11.5 }}>{a.alt}</div>
              </div>
              <div style={{ textAlign: 'right', flex: '0 0 auto' }}>
                <div style={{ fontSize: 12, fontWeight: 700 }}>{a.tamamlanan}/{a.toplam}</div>
                <div style={{ fontSize: 11, color: 'var(--tx3)' }}>{acik ? 'Gizle ▲' : 'Göster ▼'}</div>
              </div>
            </div>
            {acik && (
              <div style={{ marginTop: 12 }}>
                {a.once_oncekine_odaklan && (
                  <div style={{ fontSize: 12, background: 'var(--aml)', color: 'var(--tx2)', borderRadius: 10, padding: '8px 10px', marginBottom: 10 }}>
                    İpucu: Önce bir önceki aşamanın adımlarına odaklan; bu aşamadaki adımlar onların üzerine kurulu.
                  </div>
                )}
                {a.adimlar.map((adim) => <AdimKarti key={adim.kod} adim={adim} onDurum={onDurum} />)}
              </div>
            )}
          </div>
        )
      })}

      {plan.sonraki_alanlar.length > 0 && (
        <div className="card" style={{ marginTop: 12 }}>
          <div className="ct">Sonra odaklanılacak alanlar</div>
          <div className="ps" style={{ margin: '0 0 8px', fontSize: 11.5 }}>Odak alanlarındaki adımları bitirdikçe bunlara geçebilirsin. Bir sonraki değerlendirme turunda öncelikler yeniden hesaplanır.</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {plan.sonraki_alanlar.map((s) => <span key={s.degisken_id} style={{ display: 'inline-flex', gap: 6, alignItems: 'center', fontSize: 12 }}>{s.degisken_adi} <KategoriRozeti kategori={s.kategori} /></span>)}
          </div>
        </div>
      )}
    </>
  )
}

function GucluYonler({ plan, onDurum }) {
  if (!plan.guclu_yonler.length) return null
  return (
    <>
      <div className="ct" style={{ marginTop: 20 }}>Güçlü Yönlerini Kullan</div>
      {plan.guclu_yonler.map((g) => (
        <div key={g.degisken_kod} className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <div style={{ fontSize: 14, fontWeight: 700 }}>✓ {g.degisken_adi}</div>
            <KategoriRozeti kategori={g.kategori} />
          </div>
          <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5, marginBottom: 10 }}>{g.neden_onemli}</div>
          {g.adimlar.map((adim) => <AdimKarti key={adim.kod} adim={adim} onDurum={onDurum} alanGoster={false} />)}
        </div>
      ))}
    </>
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
  const [acikKatman, setAcikKatman] = useState(null)

  const [sorgu, setSorgu] = useState('')
  const [aramaSonuclari, setAramaSonuclari] = useState(null)
  const [onayBekleyenBolum, setOnayBekleyenBolum] = useState(null)
  const [params, setParams] = useSearchParams()
  const urlIslendi = useRef(false)

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

  const gruplar = {}
  ;(gelisim || []).forEach((g) => {
    const anahtar = g.katman_kod || '?'
    if (!gruplar[anahtar]) gruplar[anahtar] = { ad: g.katman_adi || anahtar, satirlar: [] }
    gruplar[anahtar].satirlar.push(g)
  })
  const katmanSirasi = Object.keys(gruplar).sort()
  const sayac = { guclu: 0, uyumlu: 0, gelisim: 0 }
  ;(gelisim || []).forEach((g) => { sayac[(KATEGORI[g.kategori] || KATEGORI.beklenti).grup] += 1 })

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Hedef Bölüm Koçluğu</div>
        <div className="ps">İstediğin bir bölümü hedef seç, kendini onunla karşılaştır ve adım adım gelişim planını takip et. Aynı anda yalnızca 1 aktif hedefin olabilir — odaklanman için.</div>
      </div>

      <div className="yol-duzen">
        <div>
          {hedef && (
            <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
              <div>
                <div className="ct" style={{ marginBottom: 4 }}>Şu anki hedefin</div>
                <div style={{ fontSize: 16, fontWeight: 600 }}>{hedef.bolum_adi}</div>
              </div>
              {gelisim && gelisim.length > 0 && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                  <span className="bdg" style={{ background: 'var(--grl)', color: 'var(--gr)' }}>{sayac.guclu} güçlü</span>
                  <span className="bdg" style={{ background: 'var(--pul)', color: 'var(--pu)' }}>{sayac.uyumlu} uyumlu</span>
                  <span className="bdg" style={{ background: 'var(--aml)', color: 'var(--am)' }}>{sayac.gelisim} gelişime açık</span>
                </div>
              )}
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

          <div className="card">
            <div className="ct">{hedef ? 'Hedefi Değiştir' : 'Bir Hedef Seç'}</div>
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
              <input className="auth-input" style={{ flex: 1 }} value={sorgu} onChange={(e) => setSorgu(e.target.value)} placeholder="Bölüm ara..." />
              <button className="btn sec" type="submit">Ara</button>
            </form>
            {aramaSonuclari && (
              <div className="ll">
                {aramaSonuclari.length === 0 && <div className="ps" style={{ margin: 0 }}>Sonuç bulunamadı.</div>}
                {aramaSonuclari.map((s) => (
                  <div key={s.bolum_id} className="lc" onClick={() => hedefSecmeyeCalis(s.bolum_id)}>
                    <div className="lb-wrap"><div className="lt">{s.bolum_adi}</div></div>
                    {s.toplam_uyum !== null && s.toplam_uyum !== undefined && <div className="ob-score">%{Math.round(s.toplam_uyum)}</div>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {hata && <div className="auth-error">{hata}</div>}

          {hedef && kilit && (
            <div className="card" style={{ borderColor: 'var(--am)', background: 'var(--aml)' }}>
              <div style={{ fontSize: 13 }}>{kilit}</div>
            </div>
          )}

          {hedef && gelisim && gelisim.length === 0 && (
            <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedef için henüz karşılaştırılacak veri yok — önce katmanlarını tamamla.</div></div>
          )}

          {hedef && plan && <GelisimPlani plan={plan} onDurum={adimDurumu} />}
          {hedef && plan && <GucluYonler plan={plan} onDurum={adimDurumu} />}

          {hedef && gelisim && gelisim.length > 0 && (
            <>
              <div className="ct" style={{ marginTop: 20 }}>Detaylı Karşılaştırma</div>
              <div className="card">
                <div className="drl" style={{ marginBottom: 6 }}>
                  <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
                  <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
                </div>
                <div className="ps" style={{ margin: '0 0 14px', fontSize: 11.5 }}>
                  Her katmanda, özelliklerinin kendi içindeki ağırlığı bölümün beklentisiyle karşılaştırılır. Çubuklar aynı ölçekte; etiket farkın yönünü gösterir. Açıklama için özelliğin adına dokun.
                </div>
                {katmanSirasi.map((kod) => {
                  const acik = acikKatman === null ? kod === katmanSirasi[0] : acikKatman === kod
                  const grup = gruplar[kod]
                  const gelisimSayisi = grup.satirlar.filter((g) => KATEGORI[g.kategori]?.grup === 'gelisim').length
                  return (
                    <div key={kod} style={{ borderTop: '1px solid var(--bor)', paddingTop: 10, marginTop: 10 }}>
                      <div onClick={() => setAcikKatman(acik ? '' : kod)} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', marginBottom: acik ? 12 : 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 700 }}>{grup.ad}</div>
                        <div style={{ fontSize: 11.5, color: 'var(--tx3)' }}>
                          {gelisimSayisi > 0 ? `${gelisimSayisi} gelişim alanı · ` : ''}{acik ? 'Gizle ▲' : 'Göster ▼'}
                        </div>
                      </div>
                      {acik && grup.satirlar.slice().sort((a, b) => a.degisken_adi.localeCompare(b.degisken_adi, 'tr')).map((g) => <KarsilastirmaSatiri key={g.degisken_id} g={g} />)}
                    </div>
                  )
                })}
              </div>
            </>
          )}

          {hedef && karsilastirma && karsilastirma.length > 0 && (
            <>
              <div className="ct" style={{ marginTop: 20 }}>Turlar Arası Karşılaştırma</div>
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
            </>
          )}
        </div>

        {/* ============ SAĞ SÜTUN — Filiz sohbet widget'ı ============ */}
        <div className="yan-panel">
          <FilizSohbetWidgeti />
        </div>
      </div>
    </div>
  )
}
