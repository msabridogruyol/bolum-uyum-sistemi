import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

export default function SoruSayfasi() {
  const { kod } = useParams()
  const navigate = useNavigate()

  const [sorular, setSorular] = useState(null)
  const [aktifIndex, setAktifIndex] = useState(0)
  const [cevaplar, setCevaplar] = useState({}) // { soru_id: secenek_id }
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [tamamlandi, setTamamlandi] = useState(null) // katman tamamlama cevabı

  useEffect(() => {
    setSorular(null)
    setAktifIndex(0)
    setCevaplar({})
    setTamamlandi(null)
    api.katmaniBaslat(kod)
      .then((veri) => setSorular(veri.sorular))
      .catch((e) => setHata(e.detail || 'Katman başlatılamadı.'))
  }, [kod])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!sorular) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  if (tamamlandi) {
    return (
      <div className="pg">
        <div className="qwrap">
          <div className="ph">
            <div className="pt">{kod} tamamlandı 🎉</div>
            <div className="ps">Bu katmandaki değişken puanların:</div>
          </div>
          <div className="ob-grid">
            {tamamlandi.sonuclar.map((s) => (
              <div key={s.degisken_id} className="ob-card">
                <div className="ob-top">
                  <div className="ob-body">
                    <div className="ob-name">{s.degisken_adi}</div>
                  </div>
                  <div className="ob-score">{s.puan}</div>
                </div>
              </div>
            ))}
          </div>
          <button className="btn full" onClick={() => navigate(tamamlandi.tum_katmanlar_tamamlandi_mi ? '/sonuc' : '/katmanlar')}>
            {tamamlandi.tum_katmanlar_tamamlandi_mi ? 'Sonuçlarımı Gör →' : 'Katmanlara Dön'}
          </button>
        </div>
      </div>
    )
  }

  const aktifSoru = sorular[aktifIndex]
  const secilenSecenek = cevaplar[aktifSoru.id]
  const ilerlemeYuzde = Math.round((aktifIndex / sorular.length) * 100)

  async function secenekSec(secenekId) {
    setCevaplar((onceki) => ({ ...onceki, [aktifSoru.id]: secenekId }))
    setGonderiliyor(true)
    try {
      await api.soruyuCevapla(kod, aktifSoru.id, secenekId)
    } catch (e) {
      setHata(e.detail || 'Cevap kaydedilemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  async function ileriGit() {
    if (aktifIndex < sorular.length - 1) {
      setAktifIndex((i) => i + 1)
    } else {
      setGonderiliyor(true)
      try {
        const sonuc = await api.katmaniTamamla(kod)
        setTamamlandi(sonuc)
      } catch (e) {
        setHata(e.detail || 'Katman tamamlanamadı.')
      } finally {
        setGonderiliyor(false)
      }
    }
  }

  return (
    <div className="pg">
      <div className="qwrap">
        <div className="qmeta">
          <span>Soru {aktifIndex + 1} / {sorular.length}</span>
          <span>{kod}</span>
        </div>
        <div className="qtrack"><div className="qfill" style={{ width: `${ilerlemeYuzde}%` }} /></div>
        <div className="qtext">{aktifSoru.soru_metni}</div>
        <div className="qopts">
          {aktifSoru.secenekler.map((sec) => (
            <button
              key={sec.id}
              className={`qopt${secilenSecenek === sec.id ? ' sel' : ''}`}
              onClick={() => secenekSec(sec.id)}
              disabled={gonderiliyor}
            >
              {sec.secenek_metni}
            </button>
          ))}
        </div>
        <div className="qnav">
          <button className="btn sec" onClick={() => navigate('/katmanlar')}>← Katmanlara dön</button>
          <button className="btn" onClick={ileriGit} disabled={!secilenSecenek || gonderiliyor}>
            {gonderiliyor ? <span className="spin" /> : aktifIndex < sorular.length - 1 ? 'Sonraki soru →' : 'Katmanı tamamla'}
          </button>
        </div>
      </div>
    </div>
  )
}
