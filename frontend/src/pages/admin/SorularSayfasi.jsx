import { useEffect, useState, useCallback } from 'react'
import { api } from '../../api/client'

export default function SorularSayfasi() {
  const [sorular, setSorular] = useState(null)
  const [katmanFiltre, setKatmanFiltre] = useState('')
  const [hata, setHata] = useState(null)

  const yukle = useCallback((kod) => {
    api.sorulariListele(kod || undefined).then(setSorular).catch((e) => setHata(e.detail || 'Sorular yüklenemedi.'))
  }, [])

  useEffect(() => { yukle(katmanFiltre) }, [yukle, katmanFiltre])

  async function aktiflikDegistir(soruId, aktifMi) {
    try {
      await api.soruAktiflikGuncelle(soruId, !aktifMi)
      yukle(katmanFiltre)
    } catch (err) {
      setHata(err.detail || 'Güncellenemedi.')
    }
  }

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Soru Bankası</div>
        <div className="ps">Sorular silinmez, yalnızca pasife alınır — geçmiş öğrenci oturumları bozulmasın diye.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div style={{ marginBottom: 14 }}>
        <select className="auth-input" style={{ width: 160 }} value={katmanFiltre} onChange={(e) => setKatmanFiltre(e.target.value)}>
          <option value="">Tüm katmanlar</option>
          {['K1', 'K2', 'K3', 'K4', 'K5'].map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
      </div>

      {!sorular ? <div className="bos-durum">Yükleniyor…</div> : (
        <div className="ll">
          {sorular.map((s) => (
            <div key={s.id} className="lc" style={{ cursor: 'default', opacity: s.aktif_mi ? 1 : 0.5 }}>
              <div className="lb-wrap">
                <div className="lt">{s.soru_metni}</div>
                <div className="ld">{s.katman_kod} · {s.soru_tipi}</div>
              </div>
              <span className={`bdg ${s.aktif_mi ? 'bdg-done' : 'bdg-lock'}`}>{s.aktif_mi ? 'Aktif' : 'Pasif'}</span>
              <button className="btn sec" onClick={() => aktiflikDegistir(s.id, s.aktif_mi)}>
                {s.aktif_mi ? 'Pasife Al' : 'Aktifleştir'}
              </button>
            </div>
          ))}
          {sorular.length === 0 && <div className="bos-durum">Bu katmanda soru yok.</div>}
        </div>
      )}
    </div>
  )
}
