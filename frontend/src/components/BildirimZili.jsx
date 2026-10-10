// [2026-10-10] Bildirim zili: okunmamış sayısı, açılır liste, tıklayınca ilgili sayfa; e-posta tercihi altta.
// kapsam: 'ogrenci' | 'yonetim'
import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const IKON = { kulup_karar: '🎭', kulup_duyuru: '📣', kulup_etkinlik: '📅', kulup_talep: '🙋', rehberlik_randevu: '🧭', okul_deneme: '📝', anket: '📋' }
function once(z) {
  const fark = (Date.now() - new Date(z).getTime()) / 60000
  if (fark < 1) return 'şimdi'
  if (fark < 60) return `${Math.floor(fark)} dk önce`
  if (fark < 1440) return `${Math.floor(fark / 60)} sa önce`
  if (fark < 10080) return `${Math.floor(fark / 1440)} gün önce`
  return new Date(z).toLocaleDateString('tr-TR')
}

export default function BildirimZili({ kapsam = 'ogrenci' }) {
  const ogr = kapsam === 'ogrenci'
  const [v, setV] = useState(null)
  const [acik, setAcik] = useState(false)
  const [tercih, setTercih] = useState(null)
  const [konum, setKonum] = useState(null)
  const dugme = useRef(null)
  const panel = useRef(null)
  const yer = useLocation()
  const navigate = useNavigate()
  const yukle = useCallback(() => (ogr ? api.bildirimler() : api.yonetimBildirimleri()).then(setV).catch(() => {}), [ogr])
  useEffect(() => { yukle() }, [yukle, yer.pathname])
  useEffect(() => { const t = setInterval(yukle, 60000); return () => clearInterval(t) }, [yukle])
  useEffect(() => {
    if (!acik) return
    const kapat = (e) => { if (!dugme.current?.contains(e.target) && !panel.current?.contains(e.target)) setAcik(false) }
    document.addEventListener('mousedown', kapat)
    return () => document.removeEventListener('mousedown', kapat)
  }, [acik])
  function ac() {
    if (acik) { setAcik(false); return }
    const r = dugme.current.getBoundingClientRect()
    setKonum({ top: Math.min(r.bottom + 8, window.innerHeight - 200), left: Math.max(8, Math.min(r.left, window.innerWidth - 368)) })
    setAcik(true)
    if (!tercih) (ogr ? api.bildirimTercihi() : api.yonetimBildirimTercihi()).then(setTercih).catch(() => {})
  }
  async function tikla(b) {
    if (!b.okundu) setV(await (ogr ? api.bildirimOkundu([b.id]) : api.yonetimBildirimOkundu([b.id])))
    setAcik(false)
    if (b.link) navigate(b.link)
  }
  async function hepsi() { setV(await (ogr ? api.bildirimOkundu() : api.yonetimBildirimOkundu())) }
  async function tercihDegistir() { setTercih(await (ogr ? api.bildirimTercihiKaydet(!tercih.eposta) : api.yonetimBildirimTercihiKaydet(!tercih.eposta))) }
  const sayi = v?.okunmamis || 0
  return (
    <>
      <button ref={dugme} type="button" className="bz-dugme" aria-label={`Bildirimler${sayi ? ` (${sayi} okunmamış)` : ''}`} aria-expanded={acik} onClick={ac}>
        🔔{sayi > 0 && <span className="bz-sayi">{sayi > 9 ? '9+' : sayi}</span>}
      </button>
      {acik && konum && createPortal(
        <div ref={panel} className="bz-panel" style={konum} role="dialog" aria-label="Bildirimler">
          <div className="bz-ust"><b>Bildirimler</b>{sayi > 0 && <button className="hg-link" onClick={hepsi}>Tümünü okundu say</button>}</div>
          <div className="bz-liste">
            {!v?.bildirimler.length ? <div className="bz-bos">Henüz bildirim yok.</div> : v.bildirimler.map((b) => (
              <button key={b.id} className={`bz-satir${b.okundu ? '' : ' yeni'}`} onClick={() => tikla(b)}>
                <span className="bz-ikon" aria-hidden="true">{IKON[b.tur] || '🔔'}</span>
                <span style={{ minWidth: 0, flex: 1 }}>
                  <span className="bz-baslik">{b.baslik}</span>
                  {b.metin && <span className="bz-metin">{b.metin}</span>}
                  <span className="bz-zaman">{once(b.olusturulma_zamani)}</span>
                </span>
                {!b.okundu && <span className="bz-nokta" aria-label="okunmadı" />}
              </button>
            ))}
          </div>
          {tercih && (
            <label className="bz-tercih">
              <input type="checkbox" checked={tercih.eposta} onChange={tercihDegistir} />
              <span>Önemli bildirimleri e-postayla da gönder <small>({ogr ? 'kulüp kararı, rehberlik randevusu, kulüp etkinliği' : 'rehberlik ve kulüp bildirimleri'})</small></span>
            </label>
          )}
        </div>, document.body)}
    </>
  )
}
