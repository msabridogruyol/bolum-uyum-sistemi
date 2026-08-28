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
        <div className="pt">Bölüm Ağırlıkları — Hesaplama Durumu</div>
        <div className="ps">
          Her bölümün hangi değişkenlerde ne kadar öne çıktığını belirleyen arka plan hesaplaması burada
          takip edilir. Bu, sorularla veya günlük içerik yönetimiyle ilgili bir ekran değil — teknik ekip
          için bir durum göstergesidir.
        </div>
      </div>
      <div className="card" style={{ borderColor: 'var(--am)', background: 'var(--aml)' }}>
        <div className="ct">Durum: {veri?.durum ?? '—'}</div>
        <div style={{ fontSize: 13 }}>{veri?.aciklama || 'Bu özellik henüz devrede değil.'}</div>
      </div>
    </div>
  )
}
