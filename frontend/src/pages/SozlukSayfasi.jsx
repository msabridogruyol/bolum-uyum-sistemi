// [2026-10-11] Sistem Sözlüğü — Filizyol'da geçen kelimeler, lise öğrencisinin anlayacağı dilde.
// Arama: kelimeyi yaz, anlamı (ve örneği) çıksın. Arama boşken kelimeler konulara göre listelenir (100'erli sayfa).
// Kapsam: sistem terimleri + bölüm açıklamaları ve ekranlarda geçen ~3.300 terim + 278 bölüm + meslekler + özellikler.
// Filiz panelindeki "Sözlük" sekmesinden "Sözlüğün tamamı" bağlantısı buraya ?q=<arama> ile gelir.
import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { sozlukAra, tumGruplar, tumTerimler } from '../yardimci/sozluk'
import { TerimKarti, useSozluk } from '../components/SozlukArama'

const SAYFA = 100

export default function SozlukSayfasi() {
  const [params] = useSearchParams()
  const [ara, setAra] = useState(params.get('q') || '')
  const [grup, setGrup] = useState('')
  const [adet, setAdet] = useState(SAYFA)
  const girdi = useRef(null)
  const { hazir, toplam } = useSozluk()
  useEffect(() => { girdi.current?.focus() }, [])
  useEffect(() => { setAdet(SAYFA) }, [grup, ara])

  const q = ara.trim()
  const sonuc = useMemo(() => (q ? sozlukAra(q, 80) : null), [q, hazir])   // eslint-disable-line react-hooks/exhaustive-deps
  const tum = useMemo(() => tumTerimler(), [hazir])   // eslint-disable-line react-hooks/exhaustive-deps
  const sayilar = useMemo(() => tum.reduce((m, t) => { m[t.g] = (m[t.g] || 0) + 1; return m }, {}), [tum])
  const liste = useMemo(() => tum.filter((t) => !grup || t.g === grup).sort((a, b) => a.ad.localeCompare(b.ad, 'tr')), [tum, grup])

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">📖 Sistem Sözlüğü</div>
        <div className="ps">Filizyol'da anlamadığın bir kelime mi var? Aşağıya yaz, anlamını ve bir örneğini gör. Bölüm ve meslek adlarını da arayabilirsin.</div>
      </div>

      <div className="card sz-sayfa-arama">
        <div className="sz-arama buyuk">
          <span aria-hidden="true">🔍</span>
          <input ref={girdi} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Kelime yaz… (ör. net, taban puan, termodinamik, KPSS, staj)" aria-label="Sözlükte ara" enterKeyHint="search" />
          {ara && <button className="sz-temizle" onClick={() => { setAra(''); girdi.current?.focus() }} aria-label="Temizle">✕</button>}
        </div>
        <div className="sz-not" style={{ marginTop: 8 }}>{hazir ? `${toplam.toLocaleString('tr-TR')} kelime` : 'Sözlük hazırlanıyor…'}</div>
      </div>

      {sonuc && (
        sonuc.length === 0
          ? <div className="bos-durum">{hazir ? <>“{q}” sözlükte yok. Başka bir yazılışla dene ya da Filiz'e sor.</> : 'Sözlük hazırlanıyor…'}</div>
          : <div className="sz-liste" aria-live="polite">{sonuc.map((t, i) => <TerimKarti key={t.k} t={t} buyuk={i === 0} />)}</div>
      )}

      {!sonuc && (
        <>
          <div className="kc-cipler" role="tablist" aria-label="Konular">
            <button className={!grup ? 'aktif' : ''} onClick={() => setGrup('')}>Tümü ({tum.length.toLocaleString('tr-TR')})</button>
            {tumGruplar().filter((g) => sayilar[g]).map((g) => <button key={g} className={grup === g ? 'aktif' : ''} onClick={() => setGrup(g)}>{g} ({sayilar[g]})</button>)}
          </div>
          <div className="sz-liste">{liste.slice(0, adet).map((t) => <TerimKarti key={t.k} t={t} />)}</div>
          {liste.length > adet && (
            <div style={{ textAlign: 'center', margin: '14px 0' }}>
              <button className="btn sec" onClick={() => setAdet((n) => n + SAYFA)}>Daha fazla göster ({(liste.length - adet).toLocaleString('tr-TR')} kelime daha)</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
