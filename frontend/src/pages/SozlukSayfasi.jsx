// [2026-10-11] Sistem Sözlüğü — Filizyol'da geçen kelimeler, lise öğrencisinin anlayacağı dilde.
// Arama: kelimeyi yaz, anlamı (ve örneği) çıksın. Arama boşken kelimeler konulara göre listelenir.
// Filiz panelindeki "Sözlük" sekmesinden "Sözlüğün tamamı" bağlantısı buraya ?q=<arama> ile gelir.
import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { GRUPLAR, SOZLUK, sozlukAra } from '../yardimci/sozluk'
import { TerimKarti } from '../components/SozlukArama'

export default function SozlukSayfasi() {
  const [params] = useSearchParams()
  const [ara, setAra] = useState(params.get('q') || '')
  const [grup, setGrup] = useState('')
  const girdi = useRef(null)
  useEffect(() => { girdi.current?.focus() }, [])

  const q = ara.trim()
  const sonuc = useMemo(() => (q ? sozlukAra(q, 60) : null), [q])
  const liste = useMemo(() => SOZLUK.filter((t) => !grup || t.g === grup).sort((a, b) => a.ad.localeCompare(b.ad, 'tr')), [grup])

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">📖 Sistem Sözlüğü</div>
        <div className="ps">Filizyol'da anlamadığın bir kelime mi var? Aşağıya yaz, anlamını ve bir örneğini gör.</div>
      </div>

      <div className="card sz-sayfa-arama">
        <div className="sz-arama buyuk">
          <span aria-hidden="true">🔍</span>
          <input ref={girdi} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Kelime yaz… (ör. net, taban puan, CV, inisiyatif)" aria-label="Sözlükte ara" enterKeyHint="search" />
          {ara && <button className="sz-temizle" onClick={() => { setAra(''); girdi.current?.focus() }} aria-label="Temizle">✕</button>}
        </div>
      </div>

      {sonuc && (
        sonuc.length === 0
          ? <div className="bos-durum">“{q}” sözlükte yok. Başka bir yazılışla dene ya da Filiz'e sor.</div>
          : <div className="sz-liste" aria-live="polite">{sonuc.map((t, i) => <TerimKarti key={t.k} t={t} buyuk={i === 0} />)}</div>
      )}

      {!sonuc && (
        <>
          <div className="kc-cipler" role="tablist" aria-label="Konular">
            <button className={!grup ? 'aktif' : ''} onClick={() => setGrup('')}>Tümü ({SOZLUK.length})</button>
            {GRUPLAR.map((g) => <button key={g} className={grup === g ? 'aktif' : ''} onClick={() => setGrup(g)}>{g}</button>)}
          </div>
          <div className="sz-liste">{liste.map((t) => <TerimKarti key={t.k} t={t} />)}</div>
        </>
      )}
    </div>
  )
}
