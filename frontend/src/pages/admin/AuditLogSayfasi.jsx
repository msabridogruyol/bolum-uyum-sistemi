import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function AuditLogSayfasi() {
  const [kayitlar, setKayitlar] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.auditLogGetir(100).then(setKayitlar).catch((e) => setHata(e.detail || 'Audit log yüklenemedi.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!kayitlar) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Audit Log</div>
        <div className="ps">Tüm yönetici işlemlerinin geçmişi — kim, ne zaman, ne yaptı.</div>
      </div>
      <div className="ll">
        {kayitlar.map((k) => (
          <div key={k.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{k.islem}</div>
              <div className="ld">
                {k.hedef_tablo} #{k.hedef_id} · {new Date(k.zaman).toLocaleString('tr-TR')}
                {k.gerekce && <> · {k.gerekce}</>}
              </div>
            </div>
          </div>
        ))}
        {kayitlar.length === 0 && <div className="bos-durum">Henüz kayıt yok.</div>}
      </div>
    </div>
  )
}
