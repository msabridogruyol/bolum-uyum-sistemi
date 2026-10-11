// [2026-10-11] Sözlük — Filizyol'da geçen terimler, lise öğrencisinin anlayacağı dilde.
// Metinlerde terime dokununca açılan kutudaki "Sözlüğün tamamı" bağlantısı buraya ?t=<anahtar> ile gelir.
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { GRUPLAR, SOZLUK } from '../yardimci/sozluk'
import { sozlukAcikMi, sozlukAyarla } from '../components/SozlukKatmani'

const kucuk = (s) => (s || '').toLocaleLowerCase('tr-TR')

export default function SozlukSayfasi() {
  const [params] = useSearchParams()
  const secili = params.get('t')
  const [ara, setAra] = useState('')
  const [grup, setGrup] = useState('')
  const [ipucu, setIpucu] = useState(sozlukAcikMi)

  const q = kucuk(ara.trim())
  const liste = useMemo(() => SOZLUK
    .filter((t) => (!grup || t.g === grup) && (!q || kucuk(`${t.ad} ${t.t} ${(t.es || []).join(' ')}`).includes(q)))
    .sort((a, b) => a.ad.localeCompare(b.ad, 'tr')), [q, grup])

  useEffect(() => {
    if (!secili) return
    const el = document.getElementById(`terim-${secili}`)
    if (el) window.setTimeout(() => el.scrollIntoView({ behavior: 'smooth', block: 'center' }), 80)
  }, [secili])

  return (
    <div className="pg" data-sozluk-yok>
      <div className="ph">
        <div className="pt">📖 Sözlük</div>
        <div className="ps">Filizyol'da karşına çıkan kelimelerin anlamı. Sayfalarda altı noktalı çizili bir kelimeye dokunursan anlamı orada da açılır.</div>
      </div>

      <div className="card sozluk-arac">
        <input className="auth-input" value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Kelime ara… (ör. net, taban puan, CV)" aria-label="Sözlükte ara" />
        <label className="sozluk-ayar">
          <input type="checkbox" checked={ipucu} onChange={(e) => { setIpucu(e.target.checked); sozlukAyarla(e.target.checked) }} />
          Sayfalarda zor kelimelerin altını çiz
        </label>
      </div>

      <div className="kc-cipler" role="tablist" aria-label="Konular">
        <button className={!grup ? 'aktif' : ''} onClick={() => setGrup('')}>Tümü ({SOZLUK.length})</button>
        {GRUPLAR.map((g) => <button key={g} className={grup === g ? 'aktif' : ''} onClick={() => setGrup(g)}>{g}</button>)}
      </div>

      {liste.length === 0 && <div className="bos-durum">Bu kelimeyi sözlükte bulamadık. Rehber öğretmenine ya da Filiz'e sorabilirsin.</div>}
      <div className="sozluk-liste">
        {liste.map((t) => (
          <div key={t.k} id={`terim-${t.k}`} className={`card sozluk-terim${secili === t.k ? ' secili' : ''}`}>
            <div className="sozluk-terim-ad">{t.ad}</div>
            <div className="sozluk-terim-grup">{t.g}</div>
            <div className="sozluk-terim-tanim">{t.t}</div>
            {t.o && <div className="sozluk-kutu-ornek">Örnek: {t.o}</div>}
          </div>
        ))}
      </div>
    </div>
  )
}
