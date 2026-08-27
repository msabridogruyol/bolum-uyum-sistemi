import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function PipelineDurumuSayfasi() {
  const [veri, setVeri] = useState(null)

  useEffect(() => {
    api.pipelineDurumu().then(setVeri).catch(() => {})
  }, [])

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Pipeline Durumu</div>
        <div className="ps">Meslek↔bölüm eşleştirme motorunun (offline hesaplama) çalışma durumu.</div>
      </div>
      <div className="card" style={{ borderColor: 'var(--am)', background: 'var(--aml)' }}>
        <div className="ct">Durum: {veri?.durum ?? '—'}</div>
        <div style={{ fontSize: 13 }}>{veri?.aciklama}</div>
      </div>
    </div>
  )
}
