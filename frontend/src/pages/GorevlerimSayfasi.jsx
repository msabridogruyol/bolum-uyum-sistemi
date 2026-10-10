// [2026-10-10] Görevlerim — bu haftanın görevleri + önceki haftalar ve yansıtma cevapları
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import HaftalikGorevler from '../components/HaftalikGorevler'

const haftaMetni = (h) => {
  const b = new Date(h); const s = new Date(b); s.setDate(b.getDate() + 6)
  const f = (d) => d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' })
  return `${f(b)} – ${f(s)}`
}

export default function GorevlerimSayfasi() {
  const [g, setG] = useState(null)
  const [acik, setAcik] = useState(null)
  useEffect(() => { api.haftalikGecmis().then(setG).catch(() => setG({ haftalar: [], yansitma_sorulari: [] })) }, [])
  const soru = Object.fromEntries((g?.yansitma_sorulari || []).map((x) => [x.anahtar, x.soru]))
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Görevlerim</div>
        <div className="ps">Her hafta sana özel 3 küçük görev. Tamamladıkça serin uzar ve Filiz büyür.</div>
      </div>
      <HaftalikGorevler />
      <div className="card">
        <div className="ct">Önceki haftalar</div>
        {!g ? <div className="bos-durum">Yükleniyor…</div> : g.haftalar.length === 0 ? (
          <div className="bos-durum">Henüz önceki hafta yok. Bu haftanın görevlerini tamamladıkça burada birikecek.</div>
        ) : g.haftalar.map((h) => (
          <div key={h.hafta} className="gv-hafta">
            <button className="gv-hafta-b" onClick={() => setAcik(acik === h.hafta ? null : h.hafta)}>
              <span>{haftaMetni(h.hafta)}</span>
              <span className="gv-noktalar">{h.gorevler.map((x, i) => <i key={i} className={x.durum === 'tamamlandi' ? 'tamam' : ''} />)}</span>
              <b>{h.tamamlanan}/{h.gorevler.length}</b>
              <span className="yp-ince">{acik === h.hafta ? '▲' : '▼'}</span>
            </button>
            {acik === h.hafta && (
              <ul className="gv-liste">
                {h.gorevler.map((x, i) => (
                  <li key={i} className={x.durum === 'tamamlandi' ? 'tamam' : ''}>
                    <span>{x.durum === 'tamamlandi' ? '✓' : '○'}</span>
                    <div>
                      <b>{x.baslik}</b>
                      {x.yanit && Object.entries(x.yanit).map(([k, v]) => (
                        <div key={k} className="gv-yanit"><small>{soru[k] || k}</small><div>{v}</div></div>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
