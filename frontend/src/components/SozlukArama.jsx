// [2026-10-11] Sistem sözlüğü — arama kutusu + sonuçlar. Filiz panelindeki "Sözlük" sekmesinde, Sözlük penceresinde
// ve /sozluk sayfasında aynı bileşen kullanılır. Kelime yazılınca anlamı, varsa örnekle birlikte görünür.
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { SOZLUK, sozlukAra } from '../yardimci/sozluk'

const ONERILER = ['net', 'taban puan', 'başarı sırası', 'TYT', 'uyum', 'güçlü yön', 'CV', 'brüt maaş']

export function TerimKarti({ t, buyuk = false }) {
  return (
    <div className={`sz-kart${buyuk ? ' buyuk' : ''}`}>
      <div className="sz-ad">{t.ad}</div>
      <div className="sz-grup">{t.g}</div>
      <div className="sz-tanim">{t.t}</div>
      {t.o && <div className="sz-ornek"><b>Örnek:</b> {t.o}</div>}
    </div>
  )
}

export default function SozlukArama({ baslangic = '', otomatikOdak = true, kompakt = false, onSayfayaGit }) {
  const [ara, setAra] = useState(baslangic)
  const girdi = useRef(null)
  useEffect(() => { if (otomatikOdak) window.setTimeout(() => girdi.current?.focus(), 60) }, [otomatikOdak])
  useEffect(() => { setAra(baslangic) }, [baslangic])
  const sonuc = useMemo(() => sozlukAra(ara, kompakt ? 6 : 40), [ara, kompakt])
  const q = ara.trim()

  return (
    <div className={`sz${kompakt ? ' kompakt' : ''}`}>
      <div className="sz-arama">
        <span aria-hidden="true">🔍</span>
        <input ref={girdi} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Anlamını merak ettiğin kelimeyi yaz…"
               aria-label="Sözlükte ara" enterKeyHint="search" />
        {ara && <button className="sz-temizle" onClick={() => { setAra(''); girdi.current?.focus() }} aria-label="Temizle">✕</button>}
      </div>

      {!q && (
        <div className="sz-oneri">
          <div className="sz-oneri-bas">Sık aranan kelimeler</div>
          <div className="sz-cipler">
            {ONERILER.map((o) => <button key={o} onClick={() => setAra(o)}>{o}</button>)}
          </div>
          <div className="sz-not">Sözlükte {SOZLUK.length} kelime var: değerlendirme, özelliklerin, sınav ve tercih, iş hayatı ve daha fazlası.</div>
        </div>
      )}

      {q && sonuc.length === 0 && (
        <div className="sz-bos">
          “{q}” sözlükte yok. Başka bir yazılışla dene{kompakt ? ' ya da Filiz\'e sor' : ''}.
        </div>
      )}
      {q && sonuc.length > 0 && (
        <div className="sz-sonuclar" aria-live="polite">
          {sonuc.map((t, i) => <TerimKarti key={t.k} t={t} buyuk={i === 0} />)}
        </div>
      )}

      {kompakt && (
        <Link to={q ? `/sozluk?q=${encodeURIComponent(q)}` : '/sozluk'} className="sz-tumu" onClick={onSayfayaGit}>📖 Sözlüğün tamamı →</Link>
      )}
    </div>
  )
}
