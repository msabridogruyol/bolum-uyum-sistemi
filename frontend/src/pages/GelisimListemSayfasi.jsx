// [2026-11-05] Gelişim listem — haftalık görevlerin yerine: hedef bölüm için geliştirilecek alanlar, yapılacak maddeler,
// durumları ve öğrencinin tarihli kayıtları; altta geçmiş öz değerlendirmeler (eski haftalık yansıtmalar dahil).
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import GelisimListesi, { tarihMetni } from '../components/GelisimListesi'

export default function GelisimListemSayfasi() {
  const [g, setG] = useState(null)
  const [acik, setAcik] = useState(false)
  useEffect(() => { api.ozDegerlendirmeler().then(setG).catch(() => setG({ kayitlar: [], sorular: [] })) }, [])
  const soru = Object.fromEntries((g?.sorular || []).map((x) => [x.anahtar, x.soru]))
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Gelişim listem</div>
        <div className="ps">Hedef bölümün için geliştirmen gereken alanlar ve her alanda yapabileceklerin. Bir maddeyi yaptıkça tarihiyle ne yaptığını yaz.</div>
      </div>
      <GelisimListesi />
      {g?.kayitlar?.length > 0 && (
        <div className="card">
          <button className="gl-alan-bas" aria-expanded={acik} onClick={() => setAcik(!acik)}>
            <div className="ct" style={{ margin: 0, flex: 1, textAlign: 'left' }}>Önceki öz değerlendirmelerin ({g.kayitlar.length})</div>
            <span className="yp-ince" aria-hidden="true">{acik ? '▲' : '▼'}</span>
          </button>
          {acik && (
            <ul className="gv-liste">
              {g.kayitlar.map((k, i) => (
                <li key={i}>
                  <span>✍️</span>
                  <div>
                    <b>{tarihMetni(k.zaman)}</b>
                    {Object.entries(k.yanit || {}).map(([a, m]) => (
                      <div key={a} className="gv-yanit"><small>{soru[a] || a}</small><div>{m}</div></div>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
