// [2026-10-10] "Bir günümü yaşa" — meslek simülasyonu.
// Her yerden açılır: window.dispatchEvent(new CustomEvent('simulasyon-ac', { detail: { bolumId, meslek } }))
// Sahne sahne ilerler: işlere tepki (😍 / 🙂 / 😕), karar anlarında seçim + geri bildirim, sonunda özet.
// Filiz'in sesi açıksa ve cihazda doğal Türkçe ses varsa sahneler sesli anlatılır.
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { efekt, soyle, sus } from '../yardimci/filizSes'

const TEPKILER = [
  { d: 2, ikon: '😍', ad: 'Bunu yapmak keyifli' },
  { d: 1, ikon: '🙂', ad: 'Olur, yaparım' },
  { d: 0, ikon: '😕', ad: 'Bana göre değil' },
]
const TUR_IKON = { giris: '🌅', is: '🛠️', karar: '⚡', cikis: '🌙' }

function Gosterge({ yuzde }) {
  const r = 52, c = 2 * Math.PI * r
  const renk = yuzde >= 70 ? 'var(--gr)' : yuzde >= 40 ? 'var(--am)' : 'var(--re)'
  return (
    <svg viewBox="0 0 130 130" width="130" height="130" role="img" aria-label={`Keyif %${yuzde}`}>
      <circle cx="65" cy="65" r={r} fill="none" stroke="var(--sur2)" strokeWidth="12" />
      <circle cx="65" cy="65" r={r} fill="none" stroke={renk} strokeWidth="12" strokeLinecap="round"
        strokeDasharray={`${(c * yuzde) / 100} ${c}`} transform="rotate(-90 65 65)" style={{ transition: 'stroke-dasharray .8s ease' }} />
      <text x="65" y="62" textAnchor="middle" style={{ font: '800 28px var(--fd)', fill: 'var(--tx)' }}>%{yuzde}</text>
      <text x="65" y="82" textAnchor="middle" style={{ font: '600 11px var(--fn)', fill: 'var(--tx3)' }}>keyif</text>
    </svg>
  )
}

function Ozet({ s, onYeniden, onKapat, onBaska }) {
  return (
    <div className="ms-ozet">
      <div className="ms-ozet-ust">
        <Gosterge yuzde={s.keyif} />
        <div style={{ flex: 1, minWidth: 220 }}>
          <div className="ms-ozet-baslik">{s.meslek} olarak bir gün</div>
          <div className="ms-ozet-yorum">{s.yorum}</div>
          {s.uyum && <div className="yp-ince" style={{ marginTop: 6 }}>Filizyol uyumun: <b>%{s.uyum.yuzde}</b> (önerilerinde {s.uyum.sira}. sırada · {s.bolum})</div>}
        </div>
      </div>
      <div className="ms-iki">
        {s.sevdiklerin.length > 0 && <div className="ms-kutu iyi"><b>😍 Keyif aldıkların</b><ul>{s.sevdiklerin.map((x) => <li key={x}>{x}</li>)}</ul></div>}
        {s.sevmediklerin.length > 0 && <div className="ms-kutu"><b>😕 Sana göre olmayanlar</b><ul>{s.sevmediklerin.map((x) => <li key={x}>{x}</li>)}</ul></div>}
      </div>
      {s.kararlar.length > 0 && (
        <div className="ms-kutu" style={{ marginTop: 10 }}>
          <b>⚡ Kararların</b>{s.yaklasimlar.length > 0 && <span className="yp-ince"> · öne çıkan yaklaşımın: {s.yaklasimlar.join(', ')}</span>}
          {s.kararlar.map((k) => (
            <div key={k.baslik} className="ms-karar-ozet">
              <div><b>{k.baslik}:</b> {k.secim}</div>
              {k.onerilen && <div className="ms-onerilen">Meslekte beklenen: {k.onerilen}</div>}
            </div>
          ))}
        </div>
      )}
      <div className="ms-iki" style={{ marginTop: 10 }}>
        <div className="ms-kutu"><b>🧰 Bu meslek ne ister?</b><div className="ms-cipler">{s.gerekli_beceriler.map((b) => <span key={b} className="ms-cip">{b}</span>)}</div></div>
        {s.gucluler.length > 0 && <div className="ms-kutu"><b>💪 Senin güçlü yönlerin</b><div className="ms-cipler">{s.gucluler.map((b) => <span key={b} className="ms-cip guclu">{b}</span>)}</div></div>}
      </div>
      {s.nasil_olunur && <div className="ms-kutu" style={{ marginTop: 10 }}><b>🎓 Nasıl olunur?</b><div style={{ marginTop: 4 }}>{s.nasil_olunur}</div></div>}
      <div className="ms-alt">
        <button className="btn sec" onClick={onYeniden}>↻ Bu günü yeniden yaşa</button>
        {onBaska && <button className="btn sec" onClick={onBaska}>Başka bir meslek dene</button>}
        <button className="btn" onClick={onKapat}>Tamam</button>
      </div>
    </div>
  )
}

function Simulasyon({ bolumId, meslek, onKapat }) {
  const navigate = useNavigate()
  const [v, setV] = useState(null)
  const [i, setI] = useState(0)
  const [tepki, setTepki] = useState({})
  const [karar, setKarar] = useState({})
  const [ozet, setOzet] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  useEffect(() => {
    setV(null); setI(0); setTepki({}); setKarar({}); setOzet(null)
    api.simulasyon(bolumId, meslek).then(setV).catch((e) => setHata(e.detail || 'Simülasyon açılamadı.'))
    return () => sus()
  }, [bolumId, meslek])
  const sahne = v?.sahneler[i]
  useEffect(() => {
    if (!sahne) return
    efekt(sahne.tur === 'karar' ? 'uyan' : 'konus')
    soyle(`${sahne.saat.replace(':', '.')} . ${sahne.baslik}. ${sahne.metin}`)
  }, [sahne])
  if (hata) return <div className="ms-govde"><div className="auth-error">{hata}</div><button className="btn sec" onClick={onKapat}>Kapat</button></div>
  if (!v) return <div className="ms-govde"><div className="bos-durum">Gün hazırlanıyor…</div></div>
  if (ozet) {
    return (
      <div className="ms-govde">
        <Ozet s={ozet} onKapat={onKapat} onYeniden={() => { setOzet(null); setI(0); setTepki({}); setKarar({}) }}
          onBaska={() => { onKapat(); navigate('/koclugu?sekme=gun') }} />
      </div>
    )
  }
  const son = i === v.sahneler.length - 1
  const ilerleyebilir = sahne.tur === 'is' ? tepki[sahne.id] != null : sahne.tur === 'karar' ? karar[sahne.id] != null : true
  async function bitir() {
    setBekle(true); setHata(null)
    try {
      const r = await api.simulasyonKaydet({ bolum_id: bolumId, meslek, tepkiler: tepki, kararlar: karar })
      efekt('kutla'); setOzet(r); soyle(`Günün bitti. Bu mesleğin keyif puanın yüzde ${r.keyif}.`)
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  const secilen = sahne.tur === 'karar' && karar[sahne.id] != null ? sahne.secenekler[karar[sahne.id]] : null
  return (
    <div className="ms-govde">
      <div className="ms-zaman" aria-label="Günün akışı">
        {v.sahneler.map((s, j) => (
          <div key={s.id} className={`ms-nokta ${s.tur}${j === i ? ' simdi' : j < i ? ' gecti' : ''}`} title={`${s.saat} · ${s.baslik}`}>
            <span>{s.saat}</span>
          </div>
        ))}
      </div>
      <div key={sahne.id} className={`ms-sahne ${sahne.tur}`}>
        <div className="ms-saat"><span className="ms-ikon" aria-hidden="true">{TUR_IKON[sahne.tur]}</span>{sahne.saat}<span className="ms-sahne-baslik">{sahne.baslik}</span></div>
        <div className="ms-metin">{sahne.metin}</div>
        {sahne.tur === 'is' && (
          <div className="ms-tepkiler" role="radiogroup" aria-label="Bu işe tepkin">
            {TEPKILER.map((t) => (
              <button key={t.d} role="radio" aria-checked={tepki[sahne.id] === t.d} className={tepki[sahne.id] === t.d ? 'secili' : ''}
                onClick={() => { setTepki({ ...tepki, [sahne.id]: t.d }); efekt(t.d === 2 ? 'kalp' : 'konus') }}>
                <span className="ms-emoji">{t.ikon}</span>{t.ad}
              </button>
            ))}
          </div>
        )}
        {sahne.tur === 'karar' && (
          <div className="ms-secenekler">
            <div className="ms-soru">Ne yaparsın?</div>
            {sahne.secenekler.map((x) => (
              <button key={x.no} disabled={secilen != null} className={`ms-secenek${karar[sahne.id] === x.no ? ' secili' : ''}`}
                onClick={() => { setKarar({ ...karar, [sahne.id]: x.no }); efekt(x.onerilen ? 'kutla' : 'konus'); soyle(x.sonuc) }}>
                {x.metin}
              </button>
            ))}
            {secilen && (
              <div className={`ms-geri ${secilen.onerilen ? 'iyi' : sahne.onerilen_var ? 'dikkat' : ''}`}>
                <div className="ms-geri-ust">{secilen.onerilen ? '✓ Meslekte beklenen davranış' : sahne.onerilen_var ? '⚠️ Bir daha düşün' : `Yaklaşımın: ${secilen.yaklasim}`}</div>
                {secilen.sonuc}
              </div>
            )}
          </div>
        )}
        {sahne.tur === 'giris' && v.meslek.gerekli_beceriler.length > 0 && (
          <div className="ms-cipler" style={{ marginTop: 10 }}>{v.meslek.gerekli_beceriler.map((b) => <span key={b} className="ms-cip">{b}</span>)}</div>
        )}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="ms-alt">
        {i > 0 && <button className="btn sec" onClick={() => setI(i - 1)}>← Geri</button>}
        <span className="yp-ince" style={{ marginRight: 'auto' }}>{i + 1} / {v.sahneler.length}</span>
        {son
          ? <button className="btn" disabled={bekle} onClick={bitir}>{bekle ? <span className="spin" /> : 'Günü bitir ve sonucumu gör'}</button>
          : <button className="btn" disabled={!ilerleyebilir} onClick={() => setI(i + 1)}>{sahne.tur === 'giris' ? 'Güne başla →' : 'Devam →'}</button>}
      </div>
    </div>
  )
}

/** Öğrenci düzenine bir kez yerleştirilir; 'simulasyon-ac' olayıyla açılır. */
export default function SimulasyonKatmani() {
  const [acik, setAcik] = useState(null)   // { bolumId, meslek, ad }
  useEffect(() => {
    window.__filizSimulasyon = true
    const ac = (e) => setAcik(e.detail)
    window.addEventListener('simulasyon-ac', ac)
    return () => { window.__filizSimulasyon = false; window.removeEventListener('simulasyon-ac', ac) }
  }, [])
  useEffect(() => {
    if (!acik) return undefined
    const esc = (e) => { if (e.key === 'Escape') setAcik(null) }
    window.addEventListener('keydown', esc)
    return () => window.removeEventListener('keydown', esc)
  }, [acik])
  if (!acik) return null
  const kapat = () => { setAcik(null); sus(); window.dispatchEvent(new CustomEvent('simulasyon-kapandi')) }
  return createPortal(
    <div className="yp-ortu ms-ortu" onMouseDown={(e) => { if (e.target === e.currentTarget) kapat() }}>
      <div className="yp-pencere genis ms-pencere" role="dialog" aria-modal="true" aria-label="Bir günümü yaşa">
        <div className="yp-baslik">
          <div style={{ minWidth: 0 }}>
            <div className="yp-bt">🎬 Bir günümü yaşa{acik.ad ? `: ${acik.ad}` : ''}</div>
            <div className="yp-ab">Gün boyunca yaptığın işlere tepki ver, karar anlarında seçim yap; sonunda bu mesleğin sana ne kadar uyduğunu gör.</div>
          </div>
          <button className="yp-kapat" onClick={kapat} aria-label="Kapat">×</button>
        </div>
        <Simulasyon bolumId={acik.bolumId} meslek={acik.meslek} onKapat={kapat} />
      </div>
    </div>, document.body)
}

export const simulasyonAc = (bolumId, meslek, ad) => window.dispatchEvent(new CustomEvent('simulasyon-ac', { detail: { bolumId, meslek, ad } }))
