import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const DURUM_ETIKET = { baslamadi: null, devam_ediyor: 'Devam Ediyor', tamamlandi: 'Tamamlandı' }
const DURUM_RENK = { devam_ediyor: 'bdg-prog', tamamlandi: 'bdg-done' }

export default function KatmanlarSayfasi() {
  const [katmanlar, setKatmanlar] = useState(null)
  const [k5Durum, setK5Durum] = useState(null) // null = henüz kontrol edilmedi/uygun değil
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail || 'Katmanlar yüklenemedi.'))
    // K5, ancak K4 tamamlandıysa anlamlı olur — hata verirse (henüz uygun değilse) sessizce yok sayıyoruz
    api.k5Durumu().then(setK5Durum).catch(() => setK5Durum(null))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const tamamlanan = katmanlar.filter((k) => k.durum === 'tamamlandi').length
  const k5AcikMi = k5Durum && (k5Durum.acilan?.length > 0 || k5Durum.ilgi_gosterilen?.length > 0)

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Yol Haritan</div>
        <div className="ps">
          Katmanları sırayla tamamla; son katman (Alan Eğilimi) sonucuna göre sana özel derinleşme dalları burada, aynı listede açılır.
          {' '}<b>{tamamlanan}/{katmanlar.length} tamamlandı.</b>
        </div>
      </div>

      <div className="ll">
        {katmanlar.map((k) => (
          <div
            key={k.id}
            className={`lc${k.durum === 'tamamlandi' ? ' done' : k.durum === 'devam_ediyor' ? ' cur' : ''}`}
            onClick={() => navigate(`/katmanlar/${k.kod}`)}
          >
            <div className="ln">{k.durum === 'tamamlandi' ? '✓' : k.sira}</div>
            <div className="lb-wrap">
              <div className="lt">{k.ad}</div>
              <div className="ld">{k.kosullu_mu ? 'Koşullu / Dinamik — önceki katmana bağlı' : `Ağırlık: %${k.normalizasyon_agirligi}`}</div>
              {DURUM_ETIKET[k.durum] && <span className={`bdg ${DURUM_RENK[k.durum]}`}>{DURUM_ETIKET[k.durum]}</span>}
            </div>
          </div>
        ))}

        {/* K5 dalları — ayrı bir sayfa değil, aynı listenin devamı */}
        {k5Durum?.acilan?.map((d) => (
          <div key={d.dal_kodu} className="lc" onClick={() => navigate(`/k5/${d.dal_kodu}`)}>
            <div className="ln" style={{ background: 'var(--pul)', color: 'var(--pu)' }}>◆</div>
            <div className="lb-wrap">
              <div className="lt">{d.dal_adi}</div>
              <div className="ld">Derinleşme dalı — Puanın: {d.puan}</div>
              <span className="bdg bdg-prog">Açık — sorularını cevapla</span>
            </div>
          </div>
        ))}
      </div>

      {k5Durum?.ilgi_gosterilen?.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="ct">Ayrıca İlgi Gösterdiğin Alanlar</div>
          <div className="ps" style={{ margin: 0 }}>
            {k5Durum.ilgi_gosterilen.map((d) => `${d.dal_adi} (${d.puan} puan)`).join(', ')} —
            bu alanlar için ek soru sorulmadı ama eşiğe yakınsın.
          </div>
        </div>
      )}

      {!k5AcikMi && tamamlanan === katmanlar.length && (
        <div className="bos-durum" style={{ marginTop: 14 }}>
          Şu an için açılmış bir derinleşme dalın yok — bu, profiline uygun dal olmadığı anlamına gelebilir.
        </div>
      )}
    </div>
  )
}
