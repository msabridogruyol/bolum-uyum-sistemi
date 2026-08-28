import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const KATMAN_IKON = { K1: '❤️', K2: '🧠', K3: '💡', K4: '🎯' }
const ANA_KATMANLAR = ['K1', 'K2', 'K3', 'K4']

export default function GenelSonuclarSayfasi() {
  const [katmanlar, setKatmanlar] = useState(null)
  const [katmanSonuclari, setKatmanSonuclari] = useState(null) // { K1: {puan_ort, sonuclar}, ... }
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail || 'Katmanlar yüklenemedi.'))
  }, [])

  useEffect(() => {
    if (!katmanlar) return
    Promise.all(ANA_KATMANLAR.map((kod) => api.katmanSonucuGetir(kod).then((r) => [kod, r]).catch(() => [kod, null])))
      .then((sonuclarListesi) => {
        const harita = {}
        sonuclarListesi.forEach(([kod, r]) => {
          if (r && r.tamamlandi_mi && r.sonuclar.length) {
            const ortalama = r.sonuclar.reduce((a, s) => a + s.puan, 0) / r.sonuclar.length
            harita[kod] = { puanOrtalama: Math.round(ortalama), sonuclar: r.sonuclar }
          } else {
            harita[kod] = null
          }
        })
        setKatmanSonuclari(harita)
      })
  }, [katmanlar])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar || !katmanSonuclari) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const tamamlanan = katmanlar.filter((k) => k.durum === 'tamamlandi').length
  const tumTamam = ANA_KATMANLAR.every((kod) => katmanSonuclari[kod] !== null)

  // Tüm katmanlardaki tüm değişken puanlarını tek listede topla
  const tumSonuclar = ANA_KATMANLAR.flatMap((kod) => katmanSonuclari[kod]?.sonuclar || [])
  const genelOrtalama = tumSonuclar.length
    ? Math.round(tumSonuclar.reduce((a, s) => a + s.puan, 0) / tumSonuclar.length)
    : null

  const siraliSonuclar = [...tumSonuclar].sort((a, b) => b.puan - a.puan)
  const guclerListesi = siraliSonuclar.slice(0, 5)
  const gelisimListesi = [...tumSonuclar].sort((a, b) => a.puan - b.puan).slice(0, 4)

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Genel Sonuçlar</div>
        <div className="ps">
          Tüm katmanların özet profili · {tamamlanan}/{katmanlar.length} katman tamamlandı
          {genelOrtalama !== null && <> · Genel ortalama puan: <b>{genelOrtalama}</b></>}
        </div>
      </div>

      {/* --- Katman özet kartları --- */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, marginBottom: 20 }}>
        {ANA_KATMANLAR.map((kod, i) => {
          const k = katmanlar.find((x) => x.kod === kod)
          const sonuc = katmanSonuclari[kod]
          return (
            <div key={kod} className="oc" onClick={() => navigate(`/sonuc/${kod}`)}>
              <div className="oi">{KATMAN_IKON[kod]}</div>
              <div className="ol">Katman {i + 1}</div>
              <div className="op" style={{ color: sonuc ? 'var(--gr)' : 'var(--tx3)' }}>
                {sonuc ? sonuc.puanOrtalama : '—'}
              </div>
              <div className="ob">{k?.ad?.split(' ')[0] || kod}</div>
            </div>
          )
        })}
      </div>

      {!tumTamam ? (
        <div className="veri-yok-grafik">
          <div className="vg-ikon">📊</div>
          <div className="vg-metin">Tam bir özet için önce K1-K4'ün tamamını bitirmelisin.</div>
          <button className="btn" style={{ marginTop: 12 }} onClick={() => navigate('/katmanlar')}>Yol Haritama Git →</button>
        </div>
      ) : (
        <div className="sw">
          <div className="swc">
            <div className="swh">
              <div className="swi" style={{ background: 'var(--grl)' }}>✓</div>
              <div className="swt">Öne Çıkan Güçlerin</div>
            </div>
            {guclerListesi.map((s) => (
              <div key={s.degisken_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--tx2)', padding: '5px 0' }}>
                <span>{s.degisken_adi}</span>
                <b style={{ color: 'var(--gr)' }}>{s.puan}</b>
              </div>
            ))}
          </div>
          <div className="swc">
            <div className="swh">
              <div className="swi" style={{ background: 'var(--aml)' }}>↻</div>
              <div className="swt">Gelişim Alanların</div>
            </div>
            {gelisimListesi.map((s) => (
              <div key={s.degisken_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--tx2)', padding: '5px 0' }}>
                <span>{s.degisken_adi}</span>
                <b style={{ color: 'var(--am)' }}>{s.puan}</b>
              </div>
            ))}
          </div>
        </div>
      )}

      <button className="btn full" onClick={() => navigate('/')}>Ana Sayfaya Dön</button>
    </div>
  )
}
