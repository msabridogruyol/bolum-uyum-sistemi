import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

function renkSec(puan) {
  if (puan >= 70) return 'var(--gr)'
  if (puan >= 40) return 'var(--pu)'
  return 'var(--tx3)'
}

function DegiskenKarti({ s }) {
  return (
    <div style={{ padding: '14px 0', borderBottom: '1px solid var(--bor)' }}>
      <div className="dr" style={{ marginBottom: s.durum_tespiti ? 8 : 0 }}>
        <div className="dl">{s.degisken_adi}</div>
        <div className="db"><div className="df" style={{ width: `${s.puan}%`, background: renkSec(s.puan) }} /></div>
        <div className="ds" style={{ color: renkSec(s.puan) }}>{s.puan}</div>
      </div>
      {s.durum_tespiti && (
        <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.6, marginTop: 4 }}>{s.durum_tespiti}</div>
      )}
      {s.aksiyon_onerisi && (
        <div style={{
          marginTop: 8, fontSize: 12, color: 'var(--am)', background: 'var(--aml)',
          padding: '8px 12px', borderRadius: 10, display: 'flex', gap: 8, alignItems: 'flex-start',
        }}>
          <span>💡</span>
          <span>{s.aksiyon_onerisi}</span>
        </div>
      )}
    </div>
  )
}

export default function SoruSayfasi() {
  const { kod } = useParams()
  const navigate = useNavigate()

  const [sorular, setSorular] = useState(null)
  const [aktifIndex, setAktifIndex] = useState(0)
  const [cevaplar, setCevaplar] = useState({})
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [tamamlandi, setTamamlandi] = useState(null)

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
    const siraliSonuclar = [...tamamlandi.sonuclar].sort((a, b) => b.puan - a.puan)

    return (
      <div className="pg">
        <div className="qwrap" style={{ maxWidth: 640 }}>
          <div className="ph">
            <div className="pt">{kod} tamamlandı 🎉</div>
            <div className="ps">Bu katmandaki değişken puanların ve ne anlama geldikleri:</div>
          </div>

          {siraliSonuclar.length === 0 ? (
            <div className="veri-yok-grafik">
              <div className="vg-ikon">📊</div>
              <div className="vg-metin">Bu katman için henüz sonuç hesaplanmadı.</div>
            </div>
          ) : (
            <div className="card">
              {siraliSonuclar.map((s) => <DegiskenKarti key={s.degisken_id} s={s} />)}
            </div>
          )}

          <button className="btn full" onClick={() => navigate(tamamlandi.tum_katmanlar_tamamlandi_mi ? '/sonuc/genel' : '/katmanlar')}>
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
