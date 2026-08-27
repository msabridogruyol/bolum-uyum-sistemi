import { useEffect, useState, useCallback } from 'react'
import { api } from '../../api/client'

const DURUMLAR = ['taslak', 'guclu_kanitli', 'gozden_gecirilmeli']

export default function DallarSayfasi() {
  const [dallar, setDallar] = useState(null)
  const [hata, setHata] = useState(null)
  const [yeniKod, setYeniKod] = useState('')
  const [yeniAd, setYeniAd] = useState('')

  const yukle = useCallback(() => {
    api.dallariListele().then(setDallar).catch((e) => setHata(e.detail || 'Dallar yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  async function dalEkle(e) {
    e.preventDefault()
    try {
      await api.dalEkle({ kod: yeniKod, ad: yeniAd })
      setYeniKod(''); setYeniAd('')
      yukle()
    } catch (err) {
      setHata(err.detail || 'Dal eklenemedi.')
    }
  }

  async function durumGuncelle(dalId, yeniDurum) {
    try {
      await api.dalDurumGuncelle(dalId, yeniDurum)
      yukle()
    } catch (err) {
      setHata(err.detail || 'Durum güncellenemedi.')
    }
  }

  if (!dallar) return <div className="pg"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Dallar (K5)</div>
        <div className="ps">K5'te açılabilecek dal derinleşme alanları.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <form onSubmit={dalEkle} className="card" style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
        <div style={{ flex: '0 0 100px' }}>
          <label className="auth-label">Kod</label>
          <input className="auth-input" value={yeniKod} onChange={(e) => setYeniKod(e.target.value)} placeholder="D22" required />
        </div>
        <div style={{ flex: 1 }}>
          <label className="auth-label">Ad</label>
          <input className="auth-input" value={yeniAd} onChange={(e) => setYeniAd(e.target.value)} placeholder="Yeni dal adı" required />
        </div>
        <button className="btn" type="submit">Ekle</button>
      </form>

      <div className="ll">
        {dallar.map((d) => (
          <div key={d.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{d.kod} — {d.ad}</div>
              <span className="bdg bdg-prog">{d.dogrulama_durumu}</span>
            </div>
            <select className="auth-input" style={{ width: 160 }} value={d.dogrulama_durumu} onChange={(e) => durumGuncelle(d.id, e.target.value)}>
              {DURUMLAR.map((du) => <option key={du} value={du}>{du}</option>)}
            </select>
          </div>
        ))}
      </div>
    </div>
  )
}
