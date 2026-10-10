// [2026-10-10] Seçenekli rapor: kime (öğrenci / veli / yönetim / sınıf öğretmeni …), biçim ve "deneme ve net bilgileri" seçeneği.
// turler: [{ k, ad, ikon, aciklama, indir: ({ netler }) => Promise }]
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useOkulModulleri } from '../yardimci/moduller'

// [2026-10-10] tur.modul: okulun paketinde o modül yoksa seçenek gösterilmez; Net Takibi yoksa net seçeneği de yok.
export default function RaporSecici({ turler: tumTurler, etiket = 'Rapor al', kucuk = false, varsayilan, hiza = 'sag' }) {
  const modulAcik = useOkulModulleri()
  const turler = tumTurler.filter((t) => modulAcik(t.modul))
  const netVar = modulAcik('net_takibi')
  const [acik, setAcik] = useState(false)
  const [tur, setTur] = useState(varsayilan || turler[0]?.k)
  const [netler, setNetler] = useState(true)
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const kap = useRef(null)
  const panel = useRef(null)
  const [konum, setKonum] = useState(null)
  // Panel sayfanın en üst katmanında (portal) açılır: kartların / pencerelerin altında kalmaz, kırpılmaz
  function ac() {
    if (acik) { setAcik(false); return }
    const r = kap.current.getBoundingClientRect()
    const asagi = window.innerHeight - r.bottom, yukari = r.top
    const k = { maxHeight: Math.max(260, Math.min(560, (asagi > 420 || asagi >= yukari ? asagi : yukari) - 16)) }
    if (asagi > 420 || asagi >= yukari) k.top = r.bottom + 6; else k.bottom = window.innerHeight - r.top + 6
    if (hiza === 'sol') k.left = Math.max(8, r.left); else k.right = Math.max(8, window.innerWidth - r.right)
    setKonum(k); setAcik(true)
  }
  useEffect(() => {
    if (!acik) return
    const kapat = (e) => { if (!kap.current?.contains(e.target) && !panel.current?.contains(e.target)) setAcik(false) }
    const kaydir = (e) => { if (!panel.current?.contains(e.target)) setAcik(false) }
    document.addEventListener('mousedown', kapat)
    window.addEventListener('scroll', kaydir, true)
    window.addEventListener('resize', kaydir)
    return () => { document.removeEventListener('mousedown', kapat); window.removeEventListener('scroll', kaydir, true); window.removeEventListener('resize', kaydir) }
  }, [acik])
  const secili = turler.find((t) => t.k === tur) || turler[0]
  async function indir() {
    setBekle(true); setHata(null)
    try { await secili.indir({ netler: netler && netVar }); setAcik(false) } catch (e) { setHata(e.detail || 'Rapor indirilemedi.') } finally { setBekle(false) }
  }
  if (!turler.length) return null
  return (
    <div className={`rs-kap${kucuk ? ' kucuk' : ''}`} ref={kap}>
      <button type="button" className="rd-dugme" aria-expanded={acik} onClick={ac}>📄 {etiket} ▾</button>
      {acik && konum && createPortal(
        <div className="rs-panel" ref={panel} style={konum} role="dialog" aria-label="Rapor seçenekleri">
          <div className="rs-baslik">Kime / ne için?</div>
          <div className="rs-turler">
            {turler.map((t) => (
              <label key={t.k} className={`rs-tur${tur === t.k ? ' secili' : ''}`}>
                <input type="radio" name="rapor-turu" checked={tur === t.k} onChange={() => setTur(t.k)} />
                <span className="rs-ikon">{t.ikon}</span>
                <span><b>{t.ad}</b><small>{t.aciklama}</small></span>
              </label>
            ))}
          </div>
          {netVar && <label className="rs-secenek">
            <input type="checkbox" checked={netler} onChange={(e) => setNetler(e.target.checked)} />
            <span><b>📈 Deneme ve net bilgilerini ekle</b><small>Deneme sonuçları, net gidişatı, hedef üniversiteye göre kıyas ve konu takibi</small></span>
          </label>}
          {hata && <div className="auth-error" style={{ margin: 0 }}>{hata}</div>}
          <button className="btn" style={{ width: '100%' }} disabled={bekle} onClick={indir}>{bekle ? <span className="spin" /> : `${secili.ikon} ${secili.ad} raporunu indir`}</button>
        </div>,
        document.body,
      )}
    </div>
  )
}
