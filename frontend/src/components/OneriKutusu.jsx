// [2026-11-11] Yazarken altta öneri listesi (bölüm, meslek … arama kutuları). Kullanıcı isteği: "bölüm aramalarında yazarken hep
// aşağıdan önizleme isimler çıkmalı". Kutu normal bir <input> gibi davranır (value / onChange); öneriye tıklanınca ya da
// ok tuşlarıyla seçilip Enter'a basılınca onSec(oge) çağrılır. Öneri seçilmeden Enter'a basılırsa form normal gönderilir.
// kaynak: dizi ([{ ad, alt? }]) ya da async (metin) => dizi. Dizi verilirse yerelde süzülür (Türkçe karakterden bağımsız).
import { useEffect, useId, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { suz, vurgula } from '../yardimci/aramaMetni'
import { useYuzenKonum } from '../yardimci/yuzenKonum'

export default function OneriKutusu({ value, onChange, onSec, kaynak, enAz = 1, enFazla = 8, className = 'auth-input', style,
  kapStyle, placeholder, ariaLabel, autoFocus, disabled }) {
  const [oneriler, setOneriler] = useState([])
  const [acik, setAcik] = useState(false)
  const [isaret, setIsaret] = useState(-1)
  const kap = useRef(null)
  const panel = useRef(null)
  const kimlik = useId()
  const istek = useRef(0)

  useEffect(() => {
    const q = (value || '').trim()
    if (q.length < enAz || !kaynak) { setOneriler([]); return undefined }
    if (Array.isArray(kaynak)) { setOneriler(suz(kaynak, q, enFazla)); setIsaret(-1); return undefined }
    const no = ++istek.current
    const t = setTimeout(() => {
      Promise.resolve(kaynak(q)).then((l) => { if (no === istek.current) { setOneriler((l || []).slice(0, enFazla)); setIsaret(-1) } })
        .catch(() => { if (no === istek.current) setOneriler([]) })
    }, 200)
    return () => clearTimeout(t)
  }, [value, kaynak, enAz, enFazla])

  useEffect(() => {
    if (!acik) return undefined
    const disari = (e) => { if (!kap.current?.contains(e.target) && !panel.current?.contains(e.target)) setAcik(false) }
    document.addEventListener('mousedown', disari)
    document.addEventListener('touchstart', disari, { passive: true })
    return () => { document.removeEventListener('mousedown', disari); document.removeEventListener('touchstart', disari) }
  }, [acik])

  const goster = acik && oneriler.length > 0
  const konum = useYuzenKonum(kap, goster, 320)
  function sec(o) { setAcik(false); setIsaret(-1); onSec?.(o) }
  function tus(e) {
    if (!goster) { if (e.key === 'ArrowDown' && oneriler.length) { e.preventDefault(); setAcik(true); setIsaret(0) } return }
    if (e.key === 'ArrowDown') { e.preventDefault(); setIsaret((i) => Math.min(oneriler.length - 1, i + 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setIsaret((i) => Math.max(-1, i - 1)) }
    else if (e.key === 'Enter' && isaret >= 0) { e.preventDefault(); sec(oneriler[isaret]) }
    else if (e.key === 'Escape') { e.preventDefault(); setAcik(false) }
    else if (e.key === 'Tab') setAcik(false)
  }

  return (
    <div ref={kap} className="oneri-kap" style={{ position: 'relative', ...(kapStyle || {}) }}>
      <input className={className} style={style} value={value} placeholder={placeholder} aria-label={ariaLabel || placeholder}
        autoFocus={autoFocus} disabled={disabled} autoComplete="off"
        role="combobox" aria-autocomplete="list" aria-expanded={goster} aria-controls={`${kimlik}-l`}
        aria-activedescendant={goster && isaret >= 0 ? `${kimlik}-${isaret}` : undefined}
        onChange={(e) => { onChange?.(e.target.value); setAcik(true) }} onFocus={() => setAcik(true)} onKeyDown={tus} />
      {goster && konum && createPortal(
        <ul ref={panel} id={`${kimlik}-l`} role="listbox" className="secim-panel secim-liste oneri-liste"
          style={{ ...konum, width: kap.current?.getBoundingClientRect().width }}>
          {oneriler.map((o, i) => (
            <li key={`${o.id ?? o.ad}-${i}`} id={`${kimlik}-${i}`} role="option" aria-selected={i === isaret}
              className={`secim-oge${i === isaret ? ' isaretli' : ''}`}
              onMouseEnter={() => setIsaret(i)} onMouseDown={(e) => e.preventDefault()} onClick={() => sec(o)}>
              <span>{vurgula(o.ad, value)}</span>
              {o.alt && <span className="oneri-alt">{o.alt}</span>}
            </li>
          ))}
        </ul>, document.body,
      )}
    </div>
  )
}
