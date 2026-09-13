import { useEffect, useState, useCallback, useRef } from 'react'
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
export default function KoclukSayfasi() {
  const [hedef, setHedef] = useState(undefined) // undefined=yükleniyor, null=yok
  const [gelisim, setGelisim] = useState(null)
  const [yolHaritasi, setYolHaritasi] = useState(null)
  const [karsilastirma, setKarsilastirma] = useState(null)
  const [hata, setHata] = useState(null)

  // hedef değiştirme akışı
  const [sorgu, setSorgu] = useState('')
  const [aramaSonuclari, setAramaSonuclari] = useState(null)
  const [onayBekleyenBolum, setOnayBekleyenBolum] = useState(null)

  const yukle = useCallback(() => {
    api.aktifHedefGetir().then(setHedef).catch(() => setHedef(null))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  useEffect(() => {
    if (!hedef) return
    api.gelisimAnaliziGetir().then(setGelisim).catch((e) => setHata(e.detail))
    api.yolHaritasiGetir().then(setYolHaritasi).catch(() => {})
    api.turKarsilastirmasiGetir().then(setKarsilastirma).catch(() => {})
  }, [hedef])

  async function ara(e) {
    e.preventDefault()
    if (sorgu.trim().length < 2) return
    try {
      setAramaSonuclari(await api.kesfetAra(sorgu.trim(), 8))
    } catch (err) {
      setHata(err.detail || 'Arama yapılamadı.')
    }
  }

  async function hedefSecmeyeCalis(bolumId) {
    try {
      const sonuc = await api.hedefSec(bolumId, false)
      setHedef(sonuc)
      setAramaSonuclari(null)
      setSorgu('')
    } catch (err) {
      if (err.status === 409) {
        setOnayBekleyenBolum(bolumId)
      } else {
        setHata(err.detail || 'Hedef seçilemedi.')
      }
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

  if (hedef === undefined) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Hedef Bölüm Koçluğu</div>
        <div className="ps">İstediğin bir bölümü hedef seç, kendini onunla karşılaştır. Aynı anda yalnızca 1 aktif hedefin olabilir — odaklanman için.</div>
      </div>

      <div className="yol-duzen">
        {/* ============ SOL SÜTUN — mevcut koçluk içeriği ============ */}
        <div>
          {hedef && (
            <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div className="ct" style={{ marginBottom: 4 }}>Şu anki hedefin</div>
                <div style={{ fontSize: 16, fontWeight: 600 }}>{hedef.bolum_adi}</div>
              </div>
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
            <form onSubmit={ara} style={{ display: 'flex', gap: 8, marginBottom: aramaSonuclari ? 14 : 0 }}>
              <input className="auth-input" style={{ flex: 1 }} value={sorgu} onChange={(e) => setSorgu(e.target.value)} placeholder="Bölüm ara..." />
              <button className="btn sec" type="submit">Ara</button>
            </form>
            {aramaSonuclari && (
              <div className="ll">
                {aramaSonuclari.map((s) => (
                  <div key={s.bolum_id} className="lc" onClick={() => hedefSecmeyeCalis(s.bolum_id)}>
                    <div className="lb-wrap"><div className="lt">{s.bolum_adi}</div></div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {hata && <div className="auth-error">{hata}</div>}

          {hedef && gelisim && (
            <>
              <div className="ct" style={{ marginTop: 20 }}>Gelişim Analizi</div>
              {gelisim.length === 0 ? (
                <div className="taslak-onizleme">
                  <div className="taslak-onizleme-icerik card">
                    <div className="drl">
                      <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
                      <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
                    </div>
                    {[[78, 65], [55, 80], [70, 50]].map((cift, i) => (
                      <div key={i} className="dcr">
                        <div className="dcl"><div className="iskelet-satir" style={{ width: 110 }} /></div>
                        <div className="dcb">
                          <div className="dcf" style={{ width: `${cift[0]}%`, background: 'var(--pu)' }} />
                          <div className="dcf" style={{ width: `${cift[1]}%`, background: 'var(--gr)' }} />
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="taslak-onizleme-overlay">
                    <div className="to-ikon">📊</div>
                    <div className="to-metin">Bu hedef için henüz karşılaştırılacak veri yok — önce katmanlarını tamamla.</div>
                  </div>
                </div>
              ) : (
                <div className="card">
                  <div className="drl">
                    <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
                    <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
                  </div>
                  {gelisim.map((g) => (
                    <div key={g.degisken_id} className="dcr">
                      <div className="dcl">{g.degisken_adi}</div>
                      <div className="dcb">
                        <div className="dcf" style={{ width: `${g.ogrenci_puan}%`, background: 'var(--pu)' }} />
                        <div className="dcf" style={{ width: `${g.bolum_beklenen}%`, background: 'var(--gr)' }} />
                      </div>
                    </div>
                  ))}
                  <div className="sw" style={{ marginTop: 16, marginBottom: 0 }}>
                    {gelisim.filter((g) => g.durum_tespiti || g.aksiyon_onerisi).slice(0, 4).map((g) => (
                      <div key={g.degisken_id} className="swc">
                        <div className="swh">
                          <div className="swi" style={{ background: g.kategori.includes('ustun') ? 'var(--grl)' : g.kategori === 'beklenti' ? 'var(--pul)' : 'var(--aml)' }}>
                            {g.kategori.includes('ustun') ? '✓' : g.kategori === 'beklenti' ? '≈' : '↻'}
                          </div>
                          <div className="swt">{g.degisken_adi}</div>
                        </div>
                        {g.durum_tespiti && <div className="swb">{g.durum_tespiti}</div>}
                        {g.aksiyon_onerisi && <div className="swb" style={{ marginTop: 4, fontStyle: 'italic' }}>{g.aksiyon_onerisi}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {hedef && yolHaritasi && (yolHaritasi.simdi.length + yolHaritasi.bu_donem.length + yolHaritasi.uzun_vadede.length > 0) && (
            <>
              <div className="ct" style={{ marginTop: 20 }}>Gelişim Yol Haritası</div>
              {['simdi', 'bu_donem', 'uzun_vadede'].map((asama) => (
                yolHaritasi[asama].length > 0 && (
                  <div key={asama} className="card">
                    <div className="ct">{asama === 'simdi' ? 'Şimdi' : asama === 'bu_donem' ? 'Bu Dönem' : 'Uzun Vadede'}</div>
                    {yolHaritasi[asama].map((g) => <div key={g.degisken_id} className="ld" style={{ marginBottom: 4 }}>• {g.degisken_adi}</div>)}
                  </div>
                )
              ))}
            </>
          )}

          {hedef && karsilastirma && (
            <>
              <div className="ct" style={{ marginTop: 20 }}>Turlar Arası Karşılaştırma</div>
              {karsilastirma.length === 0 ? (
                <div className="taslak-onizleme">
                  <div className="taslak-onizleme-icerik ll">
                    {[72, 65, 58].map((p, i) => (
                      <div key={i} className="ob-card">
                        <div className="ob-top">
                          <div className="ob-body"><div className="iskelet-satir" style={{ width: 130 }} /></div>
                          <span className="bdg bdg-prog">değişim</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="taslak-onizleme-overlay">
                    <div className="to-ikon">📈</div>
                    <div className="to-metin">Henüz karşılaştırılacak ikinci bir tur yok.</div>
                  </div>
                </div>
              ) : (
                <div className="ll">
                  {karsilastirma.map((k) => (
                    <div key={k.degisken_id} className="ob-card">
                      <div className="ob-top">
                        <div className="ob-body">
                          <div className="ob-name">{k.degisken_adi}</div>
                          <div className="ld">{k.eski_puan} → {k.yeni_puan} ({k.degisim > 0 ? '+' : ''}{k.degisim})</div>
                        </div>
                        <span className="bdg bdg-prog">{k.trend.replaceAll('_', ' ')}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
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
