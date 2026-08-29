import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function K5SonucSayfasi() {
  const [k5Durum, setK5Durum] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.k5Durumu().then(setK5Durum).catch((e) => setHata(e.detail || 'K5 durumu alınamadı.'))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!k5Durum) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const hicDalYok = k5Durum.acilan.length === 0 && k5Durum.ilgi_gosterilen.length === 0

  return (
    <div className="pg">
      <button className="back" onClick={() => navigate('/sonuc/genel')}>← Genel sonuçlara dön</button>

      <div className="ph">
        <div className="pt">Dal Derinleşme — Sonuçların</div>
        <div className="ps">
          K4 (Alan Eğilimi) sonucuna göre eşiği (%{k5Durum.esik}) geçtiğin dallar burada, kendi sonuçlarıyla listelenir.
        </div>
      </div>

      {hicDalYok ? (
        <div className="taslak-onizleme">
          <div className="taslak-onizleme-icerik">
            <div className="ll">
              {[92, 84, 76].map((p, i) => (
                <div key={i} className="lc" style={{ cursor: 'default' }}>
                  <div className="ln" style={{ background: 'var(--pul)', color: 'var(--pu)' }}>🌟</div>
                  <div className="lb-wrap">
                    <div className="iskelet-satir" style={{ width: 160, marginBottom: 6 }} />
                    <div className="iskelet-satir" style={{ width: 90, height: 10 }} />
                  </div>
                  <div style={{ fontFamily: 'var(--fd)', fontWeight: 700, fontSize: 18, color: 'var(--pu)' }}>{p}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="taslak-onizleme-overlay">
            <div className="to-ikon">🌻</div>
            <div className="to-metin">
              K4'ü tamamlayıp eşiği geçince, sana özel açılan dallar ve sonuçları burada görünecek.
            </div>
          </div>
        </div>
      ) : (
        <>
          {k5Durum.acilan.length > 0 && (
            <>
              <div className="ct">Açılan Dalların</div>
              <div className="ll" style={{ marginBottom: 20 }}>
                {k5Durum.acilan.map((d) => (
                  <div key={d.dal_kodu} className="lc" onClick={() => navigate(`/k5/${d.dal_kodu}`)}>
                    <div className="ln" style={{ background: 'var(--pul)', color: 'var(--pu)' }}>🌟</div>
                    <div className="lb-wrap">
                      <div className="lt">{d.dal_adi}</div>
                      <span className="bdg bdg-prog">Açık — sorularını cevapla</span>
                    </div>
                    <div style={{ fontFamily: 'var(--fd)', fontWeight: 700, fontSize: 18, color: 'var(--pu)' }}>{d.puan}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          {k5Durum.ilgi_gosterilen.length > 0 && (
            <div className="card">
              <div className="ct">Ayrıca İlgi Gösterdiğin Alanlar</div>
              <div className="ps" style={{ margin: 0 }}>
                {k5Durum.ilgi_gosterilen.map((d) => `${d.dal_adi} (${d.puan} puan)`).join(', ')} —
                bu alanlar için ek soru sorulmadı ama eşiğe yakınsın.
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
