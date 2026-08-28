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
          <span>
            {s.aksiyon_onerisi}
            {s.tahmini_efor && (
              <span style={{ opacity: 0.75, marginLeft: 6, fontWeight: 600 }}>
                ({s.tahmini_efor === 'kisa' ? 'kısa vadeli' : s.tahmini_efor === 'orta' ? 'orta vadeli' : 'uzun vadeli'})
              </span>
            )}
          </span>
        </div>
      )}
    </div>
  )
}

export default function KatmanDetaySayfasi() {
  const { kod } = useParams()
  const navigate = useNavigate()
  const [katman, setKatman] = useState(null)
  const [sonuc, setSonuc] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    setKatman(null)
    setSonuc(null)
    setHata(null)

    api.katmanlariListele()
      .then((liste) => {
        const bulunan = liste.find((k) => k.kod === kod)
        if (!bulunan) throw new Error('Katman bulunamadı.')
        setKatman(bulunan)
      })
      .catch((e) => setHata(e.detail || e.message || 'Katman bilgisi alınamadı.'))

    api.katmanSonucuGetir(kod)
      .then(setSonuc)
      .catch((e) => setHata(e.detail || 'Sonuç alınamadı.'))
  }, [kod])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katman || !sonuc) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const siraliSonuclar = [...sonuc.sonuclar].sort((a, b) => b.puan - a.puan)
  const guclu = siraliSonuclar.filter((s) => s.puan >= 60)
  const digerleri = siraliSonuclar.filter((s) => s.puan < 60)

  return (
    <div className="pg">
      <button className="back" onClick={() => navigate('/sonuc/genel')}>← Genel sonuçlara dön</button>

      <div className="ph">
        <div className="ph-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div className="pt">{katman.ad}</div>
            <div className="ps">{katman.kod} katmanı — detaylı sonuçların</div>
          </div>
          <span className={`bdg ${katman.durum === 'tamamlandi' ? 'bdg-done' : 'bdg-lock'}`} style={{ fontSize: 11, padding: '4px 10px' }}>
            {katman.durum === 'tamamlandi' ? 'Tamamlandı' : 'Devam Ediyor'}
          </span>
        </div>
      </div>

      {!sonuc.tamamlandi_mi ? (
        <div className="veri-yok-grafik">
          <div className="vg-ikon">📊</div>
          <div className="vg-metin">Bu katmanı henüz tamamlamadın.</div>
          <button className="btn" style={{ marginTop: 12 }} onClick={() => navigate(`/katmanlar/${kod}`)}>
            {katman.durum === 'devam_ediyor' ? 'Kaldığın Yerden Devam Et' : 'Bu Katmana Başla'}
          </button>
        </div>
      ) : (
        <>
          {guclu.length > 0 && (
            <div className="card">
              <div className="ct">Öne Çıkan Yönlerin</div>
              {guclu.map((s) => <DegiskenKarti key={s.degisken_id} s={s} />)}
            </div>
          )}

          {digerleri.length > 0 && (
            <div className="card">
              <div className="ct">Gelişim Alanların</div>
              {digerleri.map((s) => <DegiskenKarti key={s.degisken_id} s={s} />)}
            </div>
          )}

          {sonuc.sonuclar.length === 0 && (
            <div className="veri-yok-grafik">
              <div className="vg-ikon">📊</div>
              <div className="vg-metin">Bu katman için sonuç bulunamadı.</div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
