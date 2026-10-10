import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { api } from '../api/client'

// [2026-10-04] Filiz sohbet paneli — tüm sayfalarda açılabilir.
// Açma yolları: maskotun altındaki "💬 Bana sor" (masaüstü), sağ alttaki baloncuk (telefon),
// menüdeki "Filiz'e Sor", ya da herhangi bir yerden: window.dispatchEvent(new CustomEvent('filiz-ac', { detail: { mesaj } }))
// Panel durumunu 'filiz-durum' olayıyla yayınlar (maskot düşünme/onay animasyonu ve konuşma balonunu susturmak için).
const ONERILER_GENEL = [
  'Bu hafta neye odaklanmalıyım?',
  'Sonuçlarımı bana kısaca anlatır mısın?',
  'Güçlü yönlerimi nasıl kullanabilirim?',
  'Motivasyonum düştü, ne yapabilirim?',
]
const ONERILER_SAYFA = {
  '/koclugu': ['Yol haritamdaki sıradaki adımı nasıl yaparım?', 'Hedef bölümüme ne kadar uygunum?'],
  '/bolumler': ['Önerilen bölümlerin neden bana uygun olduğunu anlatır mısın?'],
  '/bolumler/tum': ['Bir bölümün bana uyup uymadığını nasıl anlarım?'],
  '/bolumler/karsilastir': ['İki bölüm arasında nasıl karar veririm?'],
  '/profilim': ['Güçlü yönlerimi nasıl kullanabilirim?'],
  '/katmanlar': ['Bu testleri neden çözüyorum?'],
}

function durumYayinla(detay) {
  window.dispatchEvent(new CustomEvent('filiz-durum', { detail: detay }))
}

export default function FilizSohbet() {
  const konum = useLocation()
  const [acik, setAcik] = useState(false)
  const [hazir, setHazir] = useState(false)
  const [durum, setDurum] = useState(null)            // { aktif, kalan, gunluk_limit }
  const [oturumId, setOturumId] = useState(null)
  const [mesajlar, setMesajlar] = useState([])        // { rol: 'ogrenci'|'asistan'|'not', icerik }
  const [girdi, setGirdi] = useState('')
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const sonRef = useRef(null)
  const girdiRef = useRef(null)
  const bekleyenMesaj = useRef(null)
  // [2026-10-10] Geçmiş sohbetler: liste → okuma → "bu sohbetten devam et"
  const [gorunum, setGorunum] = useState('sohbet')   // sohbet | sorular | gecmis | okuma
  const [gecmis, setGecmis] = useState(null)
  const [okunan, setOkunan] = useState(null)
  const baglamRef = useRef(null)

  // dışarıdan açma isteği
  useEffect(() => {
    const ac = (e) => {
      setAcik(true)
      if (e.detail?.mesaj) bekleyenMesaj.current = e.detail.mesaj
    }
    window.addEventListener('filiz-ac', ac)
    return () => window.removeEventListener('filiz-ac', ac)
  }, [])

  // ilk açılışta: durum + aktif oturum ve geçmiş mesajlar
  useEffect(() => {
    if (!acik || hazir) return
    Promise.all([
      api.aiKocDurum().catch(() => null),
      api.aiKocOturumBaslat().catch(() => null),
    ]).then(([d, o]) => {
      setDurum(d)
      if (o) { setOturumId(o.oturum_id); setMesajlar(o.mesajlar || []) }
      setHazir(true)
    })
  }, [acik, hazir])

  // açılınca bekleyen mesaj (ör. haftalık karttan "Filiz'e sor") gönderilir
  useEffect(() => {
    if (acik && hazir && bekleyenMesaj.current && durum?.aktif) {
      const m = bekleyenMesaj.current
      bekleyenMesaj.current = null
      gonder(m)
    }
  }, [acik, hazir, durum]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { durumYayinla({ acik, dusunuyor: gonderiliyor }) }, [acik, gonderiliyor])
  useEffect(() => { sonRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [mesajlar, gonderiliyor, acik])
  useEffect(() => { if (acik && hazir) window.setTimeout(() => girdiRef.current?.focus(), 50) }, [acik, hazir])
  useEffect(() => {
    if (!acik) return undefined
    const tus = (e) => { if (e.key === 'Escape') setAcik(false) }
    window.addEventListener('keydown', tus)
    return () => window.removeEventListener('keydown', tus)
  }, [acik])

  async function yeniOturum() {
    const o = await api.aiKocOturumBaslat()
    setOturumId(o.oturum_id)
    return o.oturum_id
  }

  async function gonder(metinParam) {
    const metin = (metinParam ?? girdi).trim()
    if (!metin || gonderiliyor) return
    setGirdi('')
    setMesajlar((m) => [...m, { rol: 'ogrenci', icerik: metin }])
    setGonderiliyor(true)
    try {
      let id = oturumId || await yeniOturum()
      let cevap
      try {
        cevap = await api.aiKocMesajGonder(id, metin, konum.pathname, baglamRef.current)
        baglamRef.current = null
      } catch (e) {
        if (e.status !== 400 || !String(e.detail || '').includes('kapatılmış')) throw e
        id = await yeniOturum()                                   // oturum kapanmışsa sessizce yenisini aç
        cevap = await api.aiKocMesajGonder(id, metin, konum.pathname)
      }
      setMesajlar((m) => [...m, { rol: 'asistan', icerik: cevap.asistan_yaniti, otomatik: cevap.otomatik }])
      setDurum((d) => (d && d.mod !== 'otomatik' ? { ...d, kalan: Math.max(0, d.kalan - 1) } : d))
      if (cevap.oturum_kapandi_mi) {
        setOturumId(null)
        setMesajlar((m) => [...m, { rol: 'not', icerik: 'Bu sohbeti özetledim; kaldığımız yerden yeni bir sohbetle devam edebiliriz.' }])
      }
      durumYayinla({ acik: true, dusunuyor: false, cevaplandi: true })
    } catch (e) {
      const not = e.status === 429 ? e.detail
        : e.status === 503 ? (e.detail || "Filiz'e şu an ulaşılamıyor.")
        : 'Mesaj gönderilemedi, bağlantını kontrol edip tekrar dene.'
      setMesajlar((m) => [...m, { rol: 'not', icerik: not }])
      if (e.status === 429) setDurum((d) => (d ? { ...d, kalan: 0 } : d))
    } finally {
      setGonderiliyor(false)
    }
  }

  async function gecmisiAc() {
    setGorunum('gecmis'); setGecmis(null)
    try { setGecmis(await api.aiKocGecmis()) } catch { setGecmis([]) }
  }
  async function sohbetiAc(id) {
    setGorunum('okuma'); setOkunan(null)
    try { setOkunan(await api.aiKocGecmisDetay(id)) } catch { setOkunan({ hata: true }) }
  }
  async function devamEt() {
    if (!okunan?.oturum_id) return
    try { if (oturumId && mesajlar.length) await api.aiKocOturumuBitir(oturumId) } catch { /* kapalı olabilir */ }
    setOturumId(null)
    baglamRef.current = okunan.oturum_id
    const t = new Date(okunan.baslama_zamani).toLocaleDateString('tr-TR')
    setMesajlar([{ rol: 'not', icerik: `📌 ${t} tarihli sohbetimizden devam ediyoruz. Ne konuştuğumuzu hatırlıyorum; kaldığımız yerden yaz.` }])
    setGorunum('sohbet')
  }

  async function sohbetiSifirla() {
    if (gonderiliyor) return
    try { if (oturumId) await api.aiKocOturumuBitir(oturumId) } catch { /* zaten kapalı olabilir */ }
    setMesajlar([])
    setOturumId(null)
  }

  const otomatik = durum?.mod === 'otomatik'   // [2026-10-10] yapay zekâ bağlı değil: kural tabanlı rehber
  const oneriler = otomatik ? (durum.ornek_sorular || []).slice(0, 5) : [...(ONERILER_SAYFA[konum.pathname] || []), ...ONERILER_GENEL].slice(0, 4)
  const pasif = hazir && durum && !durum.aktif
  const hakBitti = durum?.aktif && durum.kalan <= 0

  return (
    <>
      {!acik && (
        <button className="filiz-balon" onClick={() => setAcik(true)} aria-label="Filiz Gelişim Koçu ile konuş">
          <span style={{ fontSize: 22 }}>🌱</span>
          <span className="filiz-balon-yazi">Filiz'e sor</span>
        </button>
      )}

      {acik && (
        <div className="filiz-panel" role="dialog" aria-label="Filiz Gelişim Koçu ile sohbet">
          <div className="filiz-baslik">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="filiz-avatar">🌱</div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 14.5 }}>Filiz Gelişim Koçu</div>
                <div style={{ fontSize: 11, color: 'var(--tx3)' }}>
                  {gonderiliyor ? 'yazıyor…' : pasif ? 'şu an çevrimdışı' : 'çevrimiçi'}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              {gorunum !== 'sohbet' && <button className="filiz-ikon-btn" title="Sohbete dön" onClick={() => setGorunum('sohbet')}>←</button>}
              {gorunum === 'sohbet' && mesajlar.length > 0 && !pasif && <button className="filiz-ikon-btn" title="Yeni sohbet" onClick={sohbetiSifirla}>↺</button>}
              <button className="filiz-ikon-btn" title="Kapat (Esc)" onClick={() => setAcik(false)}>✕</button>
            </div>
          </div>

          {/* [2026-10-10] Sekmeler: Sohbet · Sorabileceklerin · Geçmiş */}
          {hazir && !pasif && (
            <div className="filiz-sekmeler" role="tablist">
              <button role="tab" aria-selected={gorunum === 'sohbet'} className={gorunum === 'sohbet' ? 'aktif' : ''} onClick={() => setGorunum('sohbet')}>💬 Sohbet</button>
              <button role="tab" aria-selected={gorunum === 'sorular'} className={gorunum === 'sorular' ? 'aktif' : ''} onClick={() => setGorunum('sorular')}>❓ Sorabileceklerin</button>
              <button role="tab" aria-selected={gorunum === 'gecmis' || gorunum === 'okuma'} className={gorunum === 'gecmis' || gorunum === 'okuma' ? 'aktif' : ''} onClick={gecmisiAc}>🕘 Geçmiş</button>
            </div>
          )}

          {gorunum === 'sorular' && (
            <div className="filiz-mesajlar">
              <div className="filiz-sorular-bas">Bir soruya dokun, Filiz hemen cevaplasın.{otomatik ? ' Otomatik rehber modunda bu sorular en iyi sonucu verir.' : ' Kendi cümlelerinle de sorabilirsin.'}</div>
              {(durum?.soru_kategorileri || []).map((k) => (
                <div key={k.ad} className="filiz-soru-grup">
                  <div className="filiz-soru-grup-ad">{k.ikon} {k.ad}</div>
                  {k.sorular.map((q) => (
                    <button key={q} className="filiz-soru" disabled={hakBitti || gonderiliyor} onClick={() => { setGorunum('sohbet'); gonder(q) }}>{q}<span>→</span></button>
                  ))}
                </div>
              ))}
            </div>
          )}

          {gorunum === 'gecmis' && (
            <div className="filiz-mesajlar">
              <div className="filiz-gecmis-bas">🕘 Geçmiş sohbetlerin</div>
              {gecmis === null && <div className="bos-durum" style={{ padding: 20 }}>Yükleniyor…</div>}
              {gecmis?.length === 0 && <div className="filiz-not">Henüz tamamlanmış bir sohbetin yok. Bir sohbeti “↺ Yeni sohbet” ile bitirdiğinde burada özetiyle saklanır.</div>}
              {gecmis?.map((g) => (
                <button key={g.oturum_id} className="filiz-gecmis-oge" onClick={() => sohbetiAc(g.oturum_id)}>
                  <span className="fg-tarih">{new Date(g.baslama_zamani).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' })} · {g.mesaj_sayisi} mesaj</span>
                  <b>{g.baslik || 'Sohbet'}</b>
                  {g.ozet && <span className="fg-ozet">{g.ozet}</span>}
                </button>
              ))}
            </div>
          )}
          {gorunum === 'okuma' && (
            <div className="filiz-mesajlar">
              {!okunan && <div className="bos-durum" style={{ padding: 20 }}>Yükleniyor…</div>}
              {okunan?.hata && <div className="filiz-not">Sohbet açılamadı.</div>}
              {okunan?.mesajlar && (
                <>
                  <div className="filiz-gecmis-bas">{new Date(okunan.baslama_zamani).toLocaleString('tr-TR', { dateStyle: 'long', timeStyle: 'short' })}</div>
                  {okunan.ozet && <div className="filiz-ozet-kutu"><b>Özet:</b> {okunan.ozet}</div>}
                  {okunan.mesajlar.map((m, i) => <div key={i} className={`filiz-mesaj ${m.rol === 'ogrenci' ? 'ogrenci' : 'asistan'}`}>{m.icerik}</div>)}
                  {!pasif && <button className="btn" style={{ alignSelf: 'center', marginTop: 6 }} onClick={devamEt} disabled={hakBitti}>💬 Bu sohbetten devam et</button>}
                </>
              )}
            </div>
          )}
          {gorunum === 'sohbet' && otomatik && (
            <div className="filiz-oto-serit" title="Gerçek yapay zekâ bağlandığında Filiz serbest sohbet edebilecek.">
              🤖 <b>Otomatik rehber modu</b> · Yapay zekâ bağlı değil; sonuçlarına dayanan hazır cevaplar verilir.
            </div>
          )}
          {gorunum === 'sohbet' && (
          <div className="filiz-mesajlar">
            {!hazir && <div className="bos-durum" style={{ padding: 20 }}>Filiz hazırlanıyor…</div>}

            {pasif && (
              <div className="filiz-bos">
                <div style={{ fontSize: 34 }}>😴</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>Filiz şu an dinleniyor</div>
                <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 4, lineHeight: 1.5 }}>
                  Sohbet özelliği okulun tarafından etkinleştirildiğinde burada seninle konuşabilecek. O zamana kadar haftalık görevlerin ana sayfada seni bekliyor.
                </div>
              </div>
            )}

            {hazir && !pasif && mesajlar.length === 0 && (
              <div className="filiz-bos">
                <div style={{ fontSize: 30 }}>👋</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>Merhaba! Ben Filiz, gelişim koçun.</div>
                <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 4, lineHeight: 1.5 }}>
                  Sonuçların, hedef bölümün, haftalık görevlerin ya da kafana takılan her şey hakkında konuşabiliriz.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 14, width: '100%' }}>
                  {oneriler.map((o) => (
                    <button key={o} className="filiz-oneri" onClick={() => gonder(o)} disabled={hakBitti}>{o}</button>
                  ))}
                  {durum?.soru_kategorileri?.length > 0 && <button className="filiz-tum-sorular" onClick={() => setGorunum('sorular')}>❓ Sorabileceğin tüm soruları gör</button>}
                </div>
              </div>
            )}

            {mesajlar.map((m, i) => (
              m.rol === 'not'
                ? <div key={i} className="filiz-not">{m.icerik}</div>
                : <div key={i} className={`filiz-mesaj ${m.rol === 'ogrenci' ? 'ogrenci' : 'asistan'}`}>
                    {m.icerik}
                    {m.rol === 'asistan' && (m.otomatik || (otomatik && m.otomatik !== false)) && <span className="filiz-oto-etiket">🤖 Otomatik yanıt</span>}
                  </div>
            ))}
            {gonderiliyor && <div className="filiz-mesaj asistan filiz-yaziyor"><span /><span /><span /></div>}
            {otomatik && !gonderiliyor && mesajlar.length > 0 && (
              <div className="filiz-cipler">
                {(durum.ornek_sorular || []).filter((o) => !mesajlar.some((m) => m.icerik === o)).slice(0, 3).map((o) => (
                  <button key={o} onClick={() => gonder(o)} disabled={hakBitti}>{o}</button>
                ))}
              </div>
            )}
            <div ref={sonRef} />
          </div>
          )}

          {!pasif && gorunum === 'sohbet' && (
            <form className="filiz-girdi" onSubmit={(e) => { e.preventDefault(); gonder() }}>
              <textarea
                ref={girdiRef}
                rows={1}
                value={girdi}
                maxLength={2000}
                disabled={!hazir || hakBitti}
                placeholder={hakBitti ? 'Bugünlük mesaj hakkın doldu, yarın görüşürüz 🌱' : 'Filiz\'e bir şey yaz…'}
                onChange={(e) => setGirdi(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); gonder() } }}
              />
              <button className="btn" type="submit" disabled={!girdi.trim() || gonderiliyor || !hazir || hakBitti} aria-label="Gönder">➤</button>
            </form>
          )}
          {durum?.aktif && (
            <div className="filiz-alt">
              {otomatik ? '' : (durum.kalan > 0 ? `Bugün ${durum.kalan} mesaj hakkın kaldı · ` : 'Bugünlük mesaj hakkın doldu · ')}{otomatik ? 'Otomatik rehber: cevaplar sistemdeki sonuçlarına göre hazırlanır.' : 'Filiz Gelişim Koçu bir yapay zekâ asistanıdır, hata yapabilir.'}
            </div>
          )}
        </div>
      )}
      <style>{FILIZ_CSS}</style>
    </>
  )
}

const FILIZ_CSS = `
.filiz-sekmeler{display:flex;gap:2px;padding:6px 8px 0;border-bottom:1px solid var(--bor);background:var(--sur)}
.filiz-sekmeler button{flex:1;background:none;border:0;border-bottom:2.5px solid transparent;padding:8px 4px;font:inherit;font-size:12.5px;font-weight:700;color:var(--tx3);cursor:pointer;white-space:nowrap}
.filiz-sekmeler button.aktif{color:var(--tx);border-bottom-color:var(--pu)}
.filiz-sorular-bas{font-size:12.5px;color:var(--tx2);line-height:1.5;margin-bottom:6px}
.filiz-soru-grup{margin-bottom:10px}
.filiz-soru-grup-ad{font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:var(--pu);margin:6px 0}
.filiz-soru{display:flex;justify-content:space-between;align-items:center;gap:8px;width:100%;text-align:left;font:inherit;font-size:13px;padding:9px 12px;margin-bottom:5px;border:1px solid var(--bor);border-radius:12px;background:var(--sur);color:var(--tx);cursor:pointer}
.filiz-soru:hover{border-color:var(--pu);background:color-mix(in srgb, var(--pu) 6%, var(--sur))}
.filiz-soru span{color:var(--tx3)}
.filiz-tum-sorular{background:none;border:0;font:inherit;font-size:12.5px;font-weight:700;color:var(--pu);cursor:pointer;margin-top:4px}
.filiz-oto-serit{font-size:11.5px;line-height:1.45;color:var(--tx2);background:color-mix(in srgb, var(--tl) 10%, var(--sur));border-bottom:1px solid var(--bor);padding:7px 12px}
.filiz-oto-etiket{display:block;margin-top:6px;font-size:10.5px;font-weight:700;color:var(--tx3)}
.filiz-cipler{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 2px}
.filiz-cipler button{font:inherit;font-size:12px;padding:5px 10px;border-radius:999px;border:1px solid var(--bor2);background:var(--sur);color:var(--tx2);cursor:pointer;text-align:left}
.filiz-cipler button:hover{border-color:var(--pu);color:var(--tx)}
.filiz-gecmis-bas{font-size:12px;font-weight:800;color:var(--tx3);text-transform:uppercase;letter-spacing:.04em;text-align:center}
.filiz-gecmis-oge{display:flex;flex-direction:column;gap:3px;text-align:left;border:1px solid var(--bor2);background:var(--sur);border-radius:12px;padding:10px 12px;cursor:pointer;font-family:inherit;color:var(--tx)}
.filiz-gecmis-oge:hover{border-color:var(--pu);background:var(--pul)}
.filiz-gecmis-oge b{font-size:13px;line-height:1.35}
.fg-tarih{font-size:11px;color:var(--tx3);font-weight:700}
.fg-ozet{font-size:11.5px;color:var(--tx2);line-height:1.45;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.filiz-ozet-kutu{font-size:12px;line-height:1.5;color:var(--tx2);background:var(--pul);border-radius:10px;padding:8px 10px}
.filiz-balon{position:fixed;right:16px;bottom:16px;z-index:70;display:none;align-items:center;gap:6px;padding:10px 16px 10px 12px;border-radius:999px;border:none;background:var(--pu);color:#fff;font-weight:800;font-size:13.5px;box-shadow:0 10px 28px -8px rgba(232,128,74,.7);cursor:pointer;animation:filiz-zipla 3s ease-in-out infinite}
.filiz-panel{position:fixed;top:160px;right:14px;width:370px;height:min(540px,calc(100vh - 176px));z-index:70;display:flex;flex-direction:column;background:var(--sur);border:1px solid var(--bor2);border-radius:18px;box-shadow:0 24px 60px -12px rgba(0,0,0,.28);overflow:hidden;animation:filiz-ac .22s ease-out}
.filiz-baslik{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;border-bottom:1px solid var(--bor);background:var(--pul)}
.filiz-avatar{width:34px;height:34px;border-radius:50%;background:var(--sur);display:flex;align-items:center;justify-content:center;font-size:18px;border:1.5px solid var(--pu)}
.filiz-ikon-btn{width:28px;height:28px;border-radius:50%;border:1px solid var(--bor2);background:var(--sur);color:var(--tx2);cursor:pointer;font-size:13px}
.filiz-mesajlar{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px}
.filiz-bos{display:flex;flex-direction:column;align-items:center;text-align:center;padding:16px 8px}
.filiz-oneri{text-align:left;border:1px solid var(--bor2);background:var(--sur);color:var(--tx);border-radius:12px;padding:9px 12px;font-size:12.5px;cursor:pointer;font-family:inherit}
.filiz-oneri:hover{border-color:var(--pu);background:var(--pul)}
.filiz-mesaj{max-width:85%;padding:9px 13px;border-radius:16px;font-size:13.5px;line-height:1.55;white-space:pre-wrap;word-wrap:break-word}
.filiz-mesaj.ogrenci{align-self:flex-end;background:var(--pu);color:#fff;border-bottom-right-radius:4px}
.filiz-mesaj.asistan{align-self:flex-start;background:var(--sur2);color:var(--tx);border-bottom-left-radius:4px}
.filiz-not{align-self:center;font-size:11.5px;color:var(--tx3);text-align:center;padding:2px 10px}
.filiz-yaziyor{display:flex;gap:4px;padding:12px 14px}
.filiz-yaziyor span{width:7px;height:7px;border-radius:50%;background:var(--tx3);animation:filiz-nokta 1.2s infinite}
.filiz-yaziyor span:nth-child(2){animation-delay:.2s}.filiz-yaziyor span:nth-child(3){animation-delay:.4s}
.filiz-girdi{display:flex;gap:8px;padding:10px 12px;border-top:1px solid var(--bor)}
.filiz-girdi textarea{flex:1;resize:none;border:1px solid var(--bor2);border-radius:12px;padding:9px 12px;font-family:inherit;font-size:13.5px;background:var(--bg);color:var(--tx);max-height:96px;outline:none}
.filiz-girdi textarea:focus{border-color:var(--pu)}
.filiz-girdi .btn{padding:0 14px;border-radius:12px}
.filiz-alt{font-size:10.5px;color:var(--tx3);text-align:center;padding:0 12px 8px}
@keyframes filiz-ac{from{opacity:0;transform:translateY(-8px) scale(.98)}to{opacity:1;transform:none}}
@keyframes filiz-nokta{0%,80%,100%{opacity:.25;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}
@keyframes filiz-zipla{0%,90%,100%{transform:translateY(0)}95%{transform:translateY(-4px)}}
@media (max-width:768px){
  .filiz-balon{display:flex}
  .filiz-balon-yazi{display:inline}
  .filiz-panel{top:auto;left:8px;right:8px;bottom:8px;width:auto;height:min(75vh,600px);border-radius:20px;animation:filiz-alttan .25s ease-out}
  @keyframes filiz-alttan{from{transform:translateY(40px);opacity:0}to{transform:none;opacity:1}}
}
`
