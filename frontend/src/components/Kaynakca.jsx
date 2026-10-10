import { useEffect, useMemo, useState } from 'react'

// [2026-10-10] Sistemin dayandığı akademik ve resmî kaynaklar (docs/KAYNAKCA.md ile aynı liste).
export default function Kaynakca() {
  const [liste, setListe] = useState(null)
  const [acik, setAcik] = useState(null)
  const [ara, setAra] = useState('')
  useEffect(() => { import('../veri/kaynakca.json').then((m) => setListe(m.default)) }, [])

  const gruplar = useMemo(() => {
    const q = ara.trim().toLocaleLowerCase('tr-TR')
    const m = new Map()
    ;(liste || []).forEach((x) => {
      if (q && !`${x.k} ${x.s} ${x.a}`.toLocaleLowerCase('tr-TR').includes(q)) return
      if (!m.has(x.g)) m.set(x.g, [])
      m.get(x.g).push(x)
    })
    return [...m.entries()]
  }, [liste, ara])

  return (
    <div className="card">
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
        <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>Kaynakça</div>
        <input className="yp-sec" style={{ minWidth: 220 }} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Kaynak ara…" />
      </div>
      <div className="yp-ince" style={{ marginBottom: 12 }}>
        Değerlendirme boyutları, eşleştirme mantığı, koçluk ve rehberlik içerikleri ile resmî verilerin dayandığı kaynaklar (APA 7).
        Kaynaklar kuramsal dayanağı gösterir; Filizyol ölçekleri bu ölçeklerin uyarlaması değildir.
        Meslek simülasyonundaki karar anları kurgusaldır; gerçek kişi, kurum veya istatistik içermez.
      </div>
      {!liste && <div className="bos-durum">Yükleniyor…</div>}
      {liste && gruplar.length === 0 && <div className="bos-durum">Aramana uygun kaynak bulunamadı.</div>}
      {gruplar.map(([g, xs]) => (
        <div key={g} className="sh-grup">
          <div className="sh-grup-ad">{g} <span className="yp-ince">({xs.length})</span></div>
          {xs.map((x) => {
            const id = `${g}|${x.k}`
            return (
              <div key={id} className={`sh-soru${acik === id ? ' acik' : ''}`}>
                <button onClick={() => setAcik(acik === id ? null : id)} aria-expanded={acik === id}>
                  <span>{x.k}</span><span className="sh-ok">{acik === id ? '−' : '+'}</span>
                </button>
                {acik === id && (
                  <div className="sh-cevap">
                    <div style={{ marginBottom: 6 }}>{x.a}</div>
                    <div className="yp-ince"><b>Sistemde kullanımı:</b> {x.s}</div>
                    {x.u && <a href={x.u} target="_blank" rel="noreferrer noopener" style={{ fontSize: 13, color: 'var(--pu)', fontWeight: 600 }}>Kaynağa git ↗</a>}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}
