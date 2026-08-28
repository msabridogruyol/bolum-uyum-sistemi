import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const KATMAN_IKON = { K1: '❤️', K2: '🧠', K3: '💡', K4: '🎯', K5: '🔭' }
const ANA_KATMANLAR = ['K1', 'K2', 'K3', 'K4']

export default function GenelSonuclarSayfasi() {
  const [katmanlar, setKatmanlar] = useState(null)
  const [katmanSonuclari, setKatmanSonuclari] = useState(null)
  const [k5Durum, setK5Durum] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail || 'Katmanlar yüklenemedi.'))
    api.k5Durumu().then(setK5Durum).catch(() => setK5Durum({ acilan: [], ilgi_gosterilen: [] }))
  }, [])

  useEffect(() => {
    if (!katmanlar) return
    Promise.all(ANA_KATMANLAR.map((kod) => api.katmanSonucuGetir(kod).then((r) => [kod, r]).catch(() => [kod, null])))
      .then((sonuclarListesi) => {
        const harita = {}
        sonuclarListesi.forEach(([kod, r]) => {
          if (r && r.tamamlandi_mi && r.sonuclar.length) {
            const ortalama = r.sonuclar.reduce((a, s) => a + s.puan, 0) / r.sonuclar.length
            harita[kod] = {
              puanOrtalama: Math.round(ortalama),
              sonuclar: r.sonuclar.map((s) => ({ ...s, katmanKod: kod })),
            }
          } else {
            harita[kod] = null
          }
        })
        setKatmanSonuclari(harita)
      })
  }, [katmanlar])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar || !katmanSonuclari || !k5Durum) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const tamamlanan = katmanlar.filter((k) => k.durum === 'tamamlandi').length
  const tumTamam = ANA_KATMANLAR.every((kod) => katmanSonuclari[kod] !== null)

  const k5OrtalamaPuan = k5Durum.acilan.length > 0
    ? Math.round(k5Durum.acilan.reduce((a, d) => a + d.puan, 0) / k5Durum.acilan.length)
    : null

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

      {/* --- Katman özet kartları (K1-K5) --- */}
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
        <div className="oc" onClick={() => navigate('/katmanlar')}>
          <div className="oi">{KATMAN_IKON.K5}</div>
          <div className="ol">Katman 5</div>
          <div className="op" style={{ color: k5OrtalamaPuan !== null ? 'var(--gr)' : 'var(--tx3)' }}>
            {k5OrtalamaPuan !== null ? k5OrtalamaPuan : '—'}
          </div>
          <div className="ob">Derinleşme</div>
        </div>
      </div>

      {!tumTamam ? (
        <>
          <div className="taslak-onizleme">
            <div className="taslak-onizleme-icerik sw">
              <div className="swc">
                <div className="swh"><div className="swi" style={{ background: 'var(--grl)' }}>✓</div><div className="swt">Öne Çıkan Güçlerin</div></div>
                {['Entelektüel Merak', 'Sistemik Düşünce', 'Sosyal Etki', 'Özerklik', 'Yaratıcılık'].map((ad, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--tx2)', padding: '5px 0' }}>
                    <span>{ad}</span><b style={{ color: 'var(--gr)' }}>{90 - i * 6}</b>
                  </div>
                ))}
              </div>
              <div className="swc">
                <div className="swh"><div className="swi" style={{ background: 'var(--aml)' }}>↻</div><div className="swt">Gelişim Alanların</div></div>
                {['Dışadönüklük', 'Risk Toleransı', 'Rekabet', 'Statü'].map((ad, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--tx2)', padding: '5px 0' }}>
                    <span>{ad}</span><b style={{ color: 'var(--am)' }}>{35 - i * 4}</b>
                  </div>
                ))}
              </div>
            </div>
            <div className="taslak-onizleme-overlay">
              <div className="to-ikon">📊</div>
              <div className="to-metin">
                Güçlerin ve gelişim alanların, K1-K4'ün tamamı bitince burada görünecek — şu an {tamamlanan}/{katmanlar.length} katman tamamlandı.
              </div>
            </div>
          </div>
          <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/katmanlar')}>
            {tamamlanan === 0 ? 'Yolculuğuna Başla' : 'Kaldığın Yerden Devam Et'} →
          </button>
        </>
      ) : (
        <div className="sw">
          <div className="swc">
            <div className="swh">
              <div className="swi" style={{ background: 'var(--grl)' }}>✓</div>
              <div className="swt">Öne Çıkan Güçlerin</div>
            </div>
            {guclerListesi.map((s) => (
              <div key={s.degisken_id} style={{ padding: '9px 0', borderBottom: '1px solid var(--bor)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 600 }}>
                    <span style={{ fontSize: 9.5, fontWeight: 800, color: 'var(--pu)', background: 'var(--pul)', padding: '2px 7px', borderRadius: 20 }}>{s.katmanKod}</span>
                    {s.degisken_adi}
                  </span>
                  <b style={{ color: 'var(--gr)' }}>{s.puan}</b>
                </div>
                {s.durum_tespiti && <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginTop: 4, lineHeight: 1.5 }}>{s.durum_tespiti}</div>}
              </div>
            ))}
          </div>
          <div className="swc">
            <div className="swh">
              <div className="swi" style={{ background: 'var(--aml)' }}>↻</div>
              <div className="swt">Gelişim Alanların</div>
            </div>
            {gelisimListesi.map((s) => (
              <div key={s.degisken_id} style={{ padding: '9px 0', borderBottom: '1px solid var(--bor)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12.5, fontWeight: 600 }}>
                    <span style={{ fontSize: 9.5, fontWeight: 800, color: 'var(--am)', background: 'var(--aml)', padding: '2px 7px', borderRadius: 20 }}>{s.katmanKod}</span>
                    {s.degisken_adi}
                  </span>
                  <b style={{ color: 'var(--am)' }}>{s.puan}</b>
                </div>
                {s.aksiyon_onerisi && (
                  <div style={{ fontSize: 11.5, color: 'var(--tx2)', marginTop: 4, lineHeight: 1.5 }}>💡 {s.aksiyon_onerisi}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/')}>Ana Sayfaya Dön</button>
    </div>
  )
}
