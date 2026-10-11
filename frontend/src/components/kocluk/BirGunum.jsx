// [2026-10-10] Koçluğum → "Bölümünü tanı" ve "Bir günümü yaşa" sekmeleri.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { BolumBilgiIcerik } from '../BolumBilgiPenceresi'
import { simulasyonAc } from '../MeslekSimulasyonu'

export function BolumunuTani({ hedef }) {
  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <BolumBilgiIcerik bolumId={hedef.bolum_id} ad={hedef.bolum_adi} gomulu />
    </div>
  )
}

const keyifRenk = (k) => (k >= 70 ? 'var(--gr)' : k >= 40 ? 'var(--am)' : 'var(--re)')

export function BirGunumSekmesi({ hedef }) {
  const [v, setV] = useState(null)
  const [gecmis, setGecmis] = useState([])
  const [hata, setHata] = useState(null)
  const yukle = () => {
    api.bolumTanit(hedef.bolum_id).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
    api.simulasyonlarim().then((x) => setGecmis(x.simulasyonlar)).catch(() => {})
  }
  useEffect(() => {
    yukle()
    const tazele = () => window.setTimeout(yukle, 300)
    window.addEventListener('simulasyon-kapandi', tazele)
    return () => window.removeEventListener('simulasyon-kapandi', tazele)
  }, [hedef.bolum_id])   // eslint-disable-line react-hooks/exhaustive-deps
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const diger = gecmis.filter((g) => g.bolum_id !== hedef.bolum_id)
  return (
    <>
      <div className="card ms-tanitim">
        <div className="ms-tanitim-ikon" aria-hidden="true">🎬</div>
        <div>
          <div className="ct" style={{ marginBottom: 4 }}>Bir günümü yaşa</div>
          <div className="ps" style={{ margin: 0 }}>
            <b>{v.bolum.ad}</b> mezunlarının çalıştığı mesleklerden birini seç; sabahtan akşama o mesleğin bir gününü yaşa. Her işe tepki ver,
            karar anlarında ne yapacağını seç. Sonunda bu mesleğin sana ne kadar keyifli geldiğini, kendi güçlü yönlerinle birlikte gör.
          </div>
        </div>
      </div>
      <div className="ms-meslekler">
        {v.meslekler.map((m) => (
          <div key={m.no} className="card ms-meslek">
            <div className="ms-meslek-ust">
              <b>{m.ad}</b>
              {m.keyif != null && <span className="ms-keyif" style={{ color: keyifRenk(m.keyif) }}>%{m.keyif} keyif</span>}
            </div>
            <div className="ms-meslek-ac">{m.aciklama}</div>
            <div className="yp-ince">{m.kararli ? '⚡ Karar anları içerir' : 'Günlük işler'}</div>
            {m.simulasyon
              ? <button className="btn" onClick={() => simulasyonAc(hedef.bolum_id, m.no, m.ad)}>{m.keyif != null ? '↻ Yeniden yaşa' : '🎬 Bir gününü yaşa'}</button>
              : <span className="yp-ince">Bu meslek için yeterli bilgi yok.</span>}
          </div>
        ))}
      </div>
      {diger.length > 0 && (
        <div className="card">
          <div className="ct">Denediğin diğer meslekler</div>
          {diger.map((g) => (
            <div key={`${g.bolum_id}-${g.meslek_ad}`} className="ms-gecmis">
              <span><b>{g.meslek_ad}</b> <span className="yp-ince">{g.bolum_ad}</span></span>
              <span className="ms-keyif" style={{ color: keyifRenk(g.keyif) }}>%{g.keyif}</span>
            </div>
          ))}
        </div>
      )}
      <div className="yp-ince" style={{ marginTop: 6 }}>Başka bölümlerin mesleklerini denemek için Bölümler sayfasında bir bölüme dokun → Meslekler.</div>
    </>
  )
}
