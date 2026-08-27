import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function K5Sayfasi() {
  const [durum, setDurum] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.k5Durumu().then(setDurum).catch((e) => setHata(e.detail || 'K5 durumu alınamadı.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!durum) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Dal Derinleşme — Sana Özel</div>
        <div className="ps">Alan Eğilimi (K4) katmanı tamamlanınca, eşiği (%{durum.esik}) geçtiğin dallar burada açılır.</div>
      </div>

      {durum.acilan.length === 0 && durum.ilgi_gosterilen.length === 0 && (
        <div className="bos-durum">
          Henüz açık bir dal yok — önce K4 (Alan Eğilimi) katmanını tamamlamalısın.
        </div>
      )}

      {durum.acilan.length > 0 && (
        <div className="ll" style={{ marginBottom: 20 }}>
          {durum.acilan.map((d) => (
            <div key={d.dal_kodu} className="lc" onClick={() => navigate(`/k5/${d.dal_kodu}`)}>
              <div className="ln" style={{ background: 'var(--pul)', color: 'var(--pu)' }}>◆</div>
              <div className="lb-wrap">
                <div className="lt">{d.dal_adi}</div>
                <div className="ld">Puanın: {d.puan}</div>
                <span className="bdg bdg-prog">Açık — sorularını cevapla</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {durum.ilgi_gosterilen.length > 0 && (
        <div className="card">
          <div className="ct">Ayrıca İlgi Gösterdiğin Alanlar</div>
          <div className="ps" style={{ margin: 0 }}>
            {durum.ilgi_gosterilen.map((d) => `${d.dal_adi} (${d.puan} puan)`).join(', ')} —
            bu alanlar için ek soru sorulmadı ama eşiğe yakınsın.
          </div>
        </div>
      )}
    </div>
  )
}
