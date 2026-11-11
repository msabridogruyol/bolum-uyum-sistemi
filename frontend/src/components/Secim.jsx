// [2026-11-11] Açılır liste. Kullanıcı isteği: "yazarken aşağıdan önizleme isimler çıkmalı; bu yalnızca bölümlerde değil
// sistemdeki tüm liste açılır pencerelerinde olmalı". Kısa listeler (en çok ESIK seçenek) olduğu gibi yerel <select> kalır;
// daha uzun listeler yazarak aranabilir: tıklayınca altta bir arama kutusu ve süzülen seçenekler açılır.
// <select> ile aynı kullanılır (<option>, <optgroup>, value, onChange, disabled, className, style); onChange'e
// { target: { value, name } } gider, değer yerel select'teki gibi metindir.
import { Children, Fragment, isValidElement, useEffect, useId, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { suz, vurgula } from '../yardimci/aramaMetni'
import { useYuzenKonum } from '../yardimci/yuzenKonum'

export const ESIK = 8
const DUZEN = new Set(['flex', 'flexGrow', 'flexShrink', 'flexBasis', 'width', 'maxWidth', 'minWidth', 'margin', 'marginTop',
  'marginBottom', 'marginLeft', 'marginRight', 'alignSelf', 'gridColumn', 'justifySelf', 'order'])

function metin(c) {
  if (c == null || typeof c === 'boolean') return ''
  if (typeof c === 'string' || typeof c === 'number') return String(c)
  if (Array.isArray(c)) return c.map(metin).join('')
  if (isValidElement(c)) return metin(c.props.children)
  return ''
}

function topla(children, grup = null, out = []) {
  Children.forEach(children, (c) => {
    if (!isValidElement(c)) return
    if (c.type === 'option') {
      const ad = metin(c.props.children)
      out.push({ value: c.props.value !== undefined ? String(c.props.value) : ad, ad, disabled: !!c.props.disabled, grup })
    } else if (c.type === 'optgroup') topla(c.props.children, c.props.label ?? null, out)
    else if (c.type === Fragment) topla(c.props.children, grup, out)
  })
  return out
}

export default function Secim(props) {
  const { children, value, defaultValue, onChange, disabled, className, style, name, id, title, required } = props
  const secenekler = useMemo(() => topla(children), [children])
  if (secenekler.length <= ESIK) {
    return <select {...props}>{children}</select>
  }
  return (
    <AranabilirSecim secenekler={secenekler} value={value ?? defaultValue} onChange={onChange} disabled={disabled}
      className={className} style={style} name={name} id={id} title={title} required={required}
      ariaLabel={props['aria-label']} />
  )
}

function AranabilirSecim({ secenekler, value, onChange, disabled, className, style = {}, name, id, title, ariaLabel }) {
  const [acik, setAcik] = useState(false)
  const [q, setQ] = useState('')
  const [isaret, setIsaret] = useState(0)
  const kap = useRef(null)
  const panel = useRef(null)
  const dugme = useRef(null)
  const liste = useRef(null)
  const konum = useYuzenKonum(kap, acik)
  const kimlik = useId()
  const secili = secenekler.find((s) => s.value === String(value ?? ''))

  const duzen = {}
  const gorunum = {}
  for (const [k, v] of Object.entries(style)) (DUZEN.has(k) ? duzen : gorunum)[k] = v
  const blok = /\bauth-input\b/.test(className || '')
  const sonuc = useMemo(() => (q ? suz(secenekler, q, 200) : secenekler), [secenekler, q])

  useEffect(() => {
    if (!acik) return undefined
    const disari = (e) => { if (!kap.current?.contains(e.target) && !panel.current?.contains(e.target)) setAcik(false) }
    document.addEventListener('mousedown', disari)
    document.addEventListener('touchstart', disari, { passive: true })
    return () => { document.removeEventListener('mousedown', disari); document.removeEventListener('touchstart', disari) }
  }, [acik])
  useEffect(() => {
    if (!acik) return
    const i = q ? 0 : Math.max(0, sonuc.findIndex((s) => s.value === secili?.value))
    setIsaret(i)
  }, [acik, q])   // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    const el = liste.current?.querySelector(`[data-i="${isaret}"]`)
    el?.scrollIntoView?.({ block: 'nearest' })
  }, [isaret, acik])

  function ac(ilk = '') { if (disabled) return; setQ(ilk); setAcik(true) }
  function sec(s) {
    if (!s || s.disabled) return
    setAcik(false); setQ('')
    dugme.current?.focus()
    if (s.value !== String(value ?? '')) onChange?.({ target: { value: s.value, name }, currentTarget: { value: s.value, name } })
  }
  function tus(e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); setIsaret((i) => Math.min(sonuc.length - 1, i + 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setIsaret((i) => Math.max(0, i - 1)) }
    else if (e.key === 'Enter') { e.preventDefault(); sec(sonuc[isaret]) }
    else if (e.key === 'Escape') { e.preventDefault(); setAcik(false); dugme.current?.focus() }
    else if (e.key === 'Tab') setAcik(false)
  }

  let sonGrup
  return (
    <div ref={kap} className="secim-kap" style={{ position: 'relative', display: blok ? 'block' : 'inline-block', verticalAlign: 'middle',
      ...(blok && duzen.width === undefined ? { width: '100%' } : {}), ...duzen }}>
      <button ref={dugme} type="button" id={id} title={title} className={`${className || ''} secim-dugme`} disabled={disabled}
        style={{ ...gorunum, width: '100%', margin: 0 }}
        aria-haspopup="listbox" aria-expanded={acik} aria-label={ariaLabel}
        onClick={() => (acik ? setAcik(false) : ac())}
        onKeyDown={(e) => {
          if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) { e.preventDefault(); ac() }
          else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); ac(e.key) }
        }}>
        <span className="secim-deger">{secili ? secili.ad : (secenekler[0]?.ad ?? '')}</span>
        <span className="secim-ok" aria-hidden="true">▾</span>
      </button>
      {name && <input type="hidden" name={name} value={value ?? ''} />}
      {acik && konum && createPortal(
        <div ref={panel} className="secim-panel" style={{ ...konum, display: 'flex', flexDirection: 'column' }}>
          <input className="secim-ara" autoFocus value={q} placeholder="Yazarak ara…" aria-label="Listede ara"
            role="combobox" aria-expanded="true" aria-controls={`${kimlik}-l`} aria-activedescendant={sonuc[isaret] ? `${kimlik}-${isaret}` : undefined}
            onChange={(e) => setQ(e.target.value)} onKeyDown={tus} />
          <ul ref={liste} id={`${kimlik}-l`} role="listbox" className="secim-liste">
            {sonuc.length === 0 && <li className="secim-bos">Eşleşen yok</li>}
            {sonuc.map((s, i) => {
              const baslik = !q && s.grup && s.grup !== sonGrup
              sonGrup = s.grup
              return (
                <Fragment key={`${s.value}-${i}`}>
                  {baslik && <li className="secim-grup" role="presentation">{s.grup}</li>}
                  <li id={`${kimlik}-${i}`} data-i={i} role="option" aria-selected={s.value === secili?.value} aria-disabled={s.disabled || undefined}
                    className={`secim-oge${i === isaret ? ' isaretli' : ''}${s.value === secili?.value ? ' secili' : ''}${s.disabled ? ' kapali' : ''}`}
                    onMouseEnter={() => setIsaret(i)} onMouseDown={(e) => e.preventDefault()} onClick={() => sec(s)}>
                    <span>{vurgula(s.ad, q)}</span>
                  </li>
                </Fragment>
              )
            })}
          </ul>
        </div>, document.body,
      )}
    </div>
  )
}
