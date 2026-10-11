// [2026-10-10] Öğrenci detayı → Portfolyo yanında küçük "CV" görünümü: yalnızca öğrenci CV Atölyesi'nde "okulumla paylaş" dediyse görünür.
// Uçlar: GET /yonetim/ogrenci/{id}/is-hayati-cv (+ /pdf) — modül kapısı okul_modulu("is_hayati").
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import CvOnizleme from '../isHayati/cv/CvOnizleme'

export default function OgrenciCv({ ogrenciId }) {
  const [v, setV] = useState(null)
  const [acik, setAcik] = useState(false)
  const [hata, setHata] = useState(null)
  useEffect(() => { api.isHayatiOgrenciCv(ogrenciId).then(setV).catch(() => setV(null)) }, [ogrenciId])
  if (!v) return null
  if (!v.paylasildi) return <div className="yp-ince" style={{ marginBottom: 10 }}>📄 CV: öğrenci, İş Hayatı → CV Atölyesi'ndeki CV'sini okulla paylaşmadı.</div>
  return (
    <div className="yp-kutu" style={{ marginBottom: 12, padding: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <div><b>📄 CV</b> <span className="yp-ince">öğrenci paylaştı{v.guncelleme ? ` · güncelleme ${new Date(v.guncelleme).toLocaleDateString('tr-TR')}` : ''}</span></div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="yp-mini" onClick={() => setAcik(!acik)}>{acik ? 'Gizle' : 'Görüntüle'}</button>
          <button className="yp-mini" onClick={() => api.isHayatiOgrenciCvPdf(ogrenciId).catch((e) => setHata(e.detail || 'İndirilemedi.'))}>PDF</button>
        </div>
      </div>
      {hata && <div className="auth-error" style={{ marginTop: 8 }}>{hata}</div>}
      {acik && <div style={{ marginTop: 10 }}><CvOnizleme icerik={v.icerik} kucuk /></div>}
    </div>
  )
}
