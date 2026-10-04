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
  '/kesfet': ['Bir bölümün bana uyup uymadığını nasıl anlarım?'],
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
        cevap = await api.aiKocMesajGonder(id, metin, konum.pathname)
      } catch (e) {
        if (e.status !== 400 || !String(e.detail || '').includes('kapatılmış')) throw e
        id = await yeniOturum()                                   // oturum kapanmışsa sessizce yenisini aç
        cevap = await api.aiKocMesajGonder(id, metin, konum.pathname)
      }
      setMesajlar((m) => [...m, { rol: 'asistan', icerik: cevap.asistan_yaniti }])
      setDurum((d) => (d ? { ...d, kalan: Math.max(0, d.kalan - 1) } : d))
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

  async function sohbetiSifirla() {
    if (gonderiliyor) return
    try { if (oturumId) await api.aiKocOturumuBitir(oturumId) } catch { /* zaten kapalı olabilir */ }
    setMesajlar([])
    setOturumId(null)
  }

  const oneriler = [...(ONERILER_SAYFA[konum.pathname] || []), ...ONERILER_GENEL].slice(0, 4)
  const pasif = hazir && durum && !durum.aktif
  const hakBitti = durum?.aktif && durum.kalan <= 0

  return (
    <>
      {!acik && (
        <button className="filiz-balon" onClick={() => setAcik(true)} aria-label="Filiz ile konuş">
          <span style={{ fontSize: 22 }}>🌱</span>
          <span className="filiz-balon-yazi">Filiz'e sor</span>
        </button>
      )}

      {acik && (
        <div className="filiz-panel" role="dialog" aria-label="Filiz ile sohbet">
          <div className="filiz-baslik">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="filiz-avatar">🌱</div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 14.5 }}>Filiz</div>
                <div style={{ fontSize: 11, color: 'var(--tx3)' }}>
                  {gonderiliyor ? 'yazıyor…' : pasif ? 'şu an çevrimdışı' : 'Kariyer koçun'}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 4 }}>
              {mesajlar.length > 0 && !pasif && <button className="filiz-ikon-btn" title="Yeni sohbet" onClick={sohbetiSifirla}>↺</button>}
              <button className="filiz-ikon-btn" title="Kapat (Esc)" onClick={() => setAcik(false)}>✕</button>
            </div>
          </div>

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
                <div style={{ fontWeight: 700, marginTop: 6 }}>Merhaba! Ben Filiz.</div>
                <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 4, lineHeight: 1.5 }}>
                  Sonuçların, hedef bölümün, haftalık görevlerin ya da kafana takılan her şey hakkında konuşabiliriz.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 14, width: '100%' }}>
                  {oneriler.map((o) => (
                    <button key={o} className="filiz-oneri" onClick={() => gonder(o)} disabled={hakBitti}>{o}</button>
                  ))}
                </div>
              </div>
            )}

            {mesajlar.map((m, i) => (
              m.rol === 'not'
                ? <div key={i} className="filiz-not">{m.icerik}</div>
                : <div key={i} className={`filiz-mesaj ${m.rol === 'ogrenci' ? 'ogrenci' : 'asistan'}`}>{m.icerik}</div>
            ))}
            {gonderiliyor && <div className="filiz-mesaj asistan filiz-yaziyor"><span /><span /><span /></div>}
            <div ref={sonRef} />
          </div>

          {!pasif && (
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
              {durum.kalan > 0 ? `Bugün ${durum.kalan} mesaj hakkın kaldı` : 'Bugünlük mesaj hakkın doldu'} · Filiz bir yapay zekâ asistanıdır, hata yapabilir.
            </div>
          )}
        </div>
      )}
      <style>{FILIZ_CSS}</style>
    </>
  )
}

const FILIZ_CSS = `
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
