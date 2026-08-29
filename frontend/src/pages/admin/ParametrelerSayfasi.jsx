import { useEffect, useState, useCallback } from 'react'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { api } from '../../api/client'

export default function ParametrelerSayfasi() {
  const [parametreler, setParametreler] = useState(null)
  const [duzenleme, setDuzenleme] = useState({})
  const [hata, setHata] = useState(null)
  const { rol } = useAdminAuth()
  const suAdminMi = rol === 'super_admin'

  const yukle = useCallback(() => {
    api.parametreleriListele().then(setParametreler).catch((e) => setHata(e.detail || 'Parametreler yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  async function kaydet(anahtar) {
    try {
      await api.parametreGuncelle(anahtar, duzenleme[anahtar])
      yukle()
    } catch (err) {
      setHata(err.detail || 'Güncellenemedi.')
    }
  }

  if (!parametreler) return <div className="pg"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Sistem Parametreleri</div>
        <div className="ps">
          {suAdminMi ? 'Koda gömülmeyen, çalışma zamanında değiştirilebilir değerler.' : 'Yalnızca süper admin bu değerleri değiştirebilir — sen görüntüleyebilirsin.'}
        </div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="ll">
        {parametreler.map((p) => (
          <div key={p.anahtar} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{p.anahtar}</div>
              <div className="ld">{p.aciklama}</div>
            </div>
            <input
              className="auth-input"
              style={{ width: 100 }}
              defaultValue={p.deger}
              disabled={!suAdminMi}
              onChange={(e) => setDuzenleme((d) => ({ ...d, [p.anahtar]: e.target.value }))}
            />
            {suAdminMi && (
              <button className="btn sec" onClick={() => kaydet(p.anahtar)} disabled={duzenleme[p.anahtar] === undefined}>
                Kaydet
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
