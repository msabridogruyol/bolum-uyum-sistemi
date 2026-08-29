import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const KATMAN_BOYUT_SAYISI = { K1: 7, K2: 8, K3: 7, K4: 9 }
const SANIYE_BASINA_SORU_TAHMINI = 25
function tahminiSureDk(kod) {
  const boyut = KATMAN_BOYUT_SAYISI[kod]
  if (!boyut) return null
  return Math.max(1, Math.round((boyut * SANIYE_BASINA_SORU_TAHMINI) / 60))
}

const IKINCI_BOLUM_BASLIGI = { K1: 'Diğer Boyutların', K2: 'Gelişim Alanların', K3: 'Gelişim Alanların', K4: 'Gelişim Alanların' }
const SONRAKI_KATMAN = { K1: 'K2', K2: 'K3', K3: 'K4', K4: null }
const PROFIL_ETIKETI = { K1: 'MOTİVASYON PROFİLİN', K2: 'KİŞİLİK PROFİLİN', K3: 'İŞ ORTAMI PROFİLİN', K4: 'ALAN EĞİLİMİ PROFİLİN' }

function renkSec(puan) {
  if (puan >= 70) return 'var(--gr)'
  if (puan >= 40) return 'var(--pu)'
  return 'var(--tx3)'
}

function BoyutSatiri({ s }) {
  const [acik, setAcik] = useState(false)
  const detayVarMi = s.durum_tespiti || s.aksiyon_onerisi

  return (
    <div className={`boyut-satir${acik ? ' acik' : ''}`} onClick={() => detayVarMi && setAcik((a) => !a)}>
      <div className="boyut-satir-ust">
        {detayVarMi && <span className="ok">▶</span>}
        <div className="dr" style={{ flex: 1, marginBottom: 0 }}>
          <div className="dl">{s.degisken_adi}</div>
          <div className="db"><div className="df" style={{ width: `${s.puan}%`, background: renkSec(s.puan) }} /></div>
          <div className="ds" style={{ color: renkSec(s.puan) }}>{s.puan}</div>
        </div>
      </div>
      {detayVarMi && (
        <div className="boyut-detay">
          {s.durum_tespiti && (
            <div style={{ fontSize: 12, color: 'var(--tx2)', lineHeight: 1.55, paddingLeft: 18 }}>{s.durum_tespiti}</div>
          )}
          {s.aksiyon_onerisi && (
            <div style={{
              marginTop: 6, marginLeft: 18, fontSize: 11.5, color: 'var(--am)', background: 'var(--aml)',
              padding: '7px 10px', borderRadius: 8, display: 'flex', gap: 6, alignItems: 'flex-start',
            }}>
              <span>💡</span><span>{s.aksiyon_onerisi}</span>
            </div>
          )}
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
  const [hedef, setHedef] = useState(undefined)
  const [gelisim, setGelisim] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    setKatman(null)
    setSonuc(null)
    setHata(null)
    setHedef(undefined)
    setGelisim(null)

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

    api.aktifHedefGetir().then(setHedef).catch(() => setHedef(null))
  }, [kod])

  useEffect(() => {
    if (!hedef) { setGelisim([]); return }
    api.gelisimAnaliziGetir().then(setGelisim).catch(() => setGelisim([]))
  }, [hedef])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katman || !sonuc || hedef === undefined || gelisim === null) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const siraliSonuclar = [...sonuc.sonuclar].sort((a, b) => b.puan - a.puan)
  const guclu = siraliSonuclar.filter((s) => s.puan >= 60)
  const digerleri = siraliSonuclar.filter((s) => s.puan < 60)
  const enUst4Etiket = siraliSonuclar.slice(0, 4)
  const sonrakiKod = SONRAKI_KATMAN[kod]

  // Hedef karşılaştırması — yalnızca BU katmanın değişkenleriyle sınırlı
  const buKatmanDegiskenIdleri = new Set(sonuc.sonuclar.map((s) => s.degisken_id))
  const hedefKarsilastirma = gelisim.filter((g) => buKatmanDegiskenIdleri.has(g.degisken_id))

  return (
    <div className={`pg${hedef ? ' pg-genis' : ''}`}>
      <button className="back" onClick={() => navigate('/sonuc/genel')}>← Genel sonuçlara dön</button>

      <div className="ph">
        <div className="ph-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div className="pt">{katman.ad}</div>
            <div className="ps">
              {katman.kod} katmanı
              {KATMAN_BOYUT_SAYISI[kod] && <> · {KATMAN_BOYUT_SAYISI[kod]} boyut · ~{tahminiSureDk(kod)} dakika</>}
            </div>
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
        <div className={hedef ? 'yol-duzen' : undefined}>
          <div>
            {siraliSonuclar.length >= 2 && (
              <div className="card">
                <div className="ct" style={{ color: 'var(--pu)' }}>{PROFIL_ETIKETI[kod] || 'PROFİLİN'}</div>
                <div style={{ fontSize: 14.5, fontWeight: 600, lineHeight: 1.55 }}>
                  Bu katmanda en güçlü çıkan boyutların: <b style={{ color: 'var(--pu)' }}>{siraliSonuclar[0].degisken_adi}</b>
                  {' '}(puan {siraliSonuclar[0].puan}) ve <b style={{ color: 'var(--pu)' }}>{siraliSonuclar[1].degisken_adi}</b>
                  {' '}(puan {siraliSonuclar[1].puan}).
                </div>
              </div>
            )}

            {enUst4Etiket.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                {enUst4Etiket.map((s) => (
                  <span key={s.degisken_id} className="bdg bdg-prog" style={{ fontSize: 12, padding: '6px 14px' }}>
                    {s.degisken_adi}
                  </span>
                ))}
              </div>
            )}

            <div className="ps" style={{ marginBottom: 14, fontSize: 12 }}>
              Bir boyuta tıklayınca detaylı açıklaması açılır. 60 ve üzeri puan alan boyutlar "Güçlü", altındakiler "{IKINCI_BOLUM_BASLIGI[kod] || 'Diğer'}" olarak gruplanır.
            </div>

            <div className="two">
              {guclu.length > 0 ? (
                <div className="card" style={{ marginBottom: 0 }}>
                  <div className="ct">Güçlü Boyutların</div>
                  {guclu.map((s) => <BoyutSatiri key={s.degisken_id} s={s} />)}
                </div>
              ) : (
                <div className="card taslak-onizleme" style={{ marginBottom: 0 }}>
                  <div className="taslak-onizleme-icerik">
                    <div className="ct">Güçlü Boyutların</div>
                    {[88, 76, 65].map((p, i) => (
                      <div key={i} className="boyut-satir">
                        <div className="boyut-satir-ust">
                          <div className="dr" style={{ flex: 1, marginBottom: 0 }}>
                            <div className="iskelet-satir" style={{ width: 90 }} />
                            <div className="db"><div className="df" style={{ width: `${p}%`, background: 'var(--gr)' }} /></div>
                            <div className="ds" style={{ color: 'var(--gr)' }}>{p}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="taslak-onizleme-overlay">
                    <div className="to-metin" style={{ fontSize: 11.5 }}>Henüz 60+ çıkan bir boyutun yok</div>
                  </div>
                </div>
              )}

              {digerleri.length > 0 ? (
                <div className="card" style={{ marginBottom: 0 }}>
                  <div className="ct">{IKINCI_BOLUM_BASLIGI[kod] || 'Diğer Boyutların'}</div>
                  {digerleri.map((s) => <BoyutSatiri key={s.degisken_id} s={s} />)}
                </div>
              ) : (
                <div className="card taslak-onizleme" style={{ marginBottom: 0 }}>
                  <div className="taslak-onizleme-icerik">
                    <div className="ct">{IKINCI_BOLUM_BASLIGI[kod] || 'Diğer Boyutların'}</div>
                    {[45, 30, 18].map((p, i) => (
                      <div key={i} className="boyut-satir">
                        <div className="boyut-satir-ust">
                          <div className="dr" style={{ flex: 1, marginBottom: 0 }}>
                            <div className="iskelet-satir" style={{ width: 90 }} />
                            <div className="db"><div className="df" style={{ width: `${p}%`, background: 'var(--tx3)' }} /></div>
                            <div className="ds" style={{ color: 'var(--tx3)' }}>{p}</div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="taslak-onizleme-overlay">
                    <div className="to-metin" style={{ fontSize: 11.5 }}>Henüz 60 altı çıkan bir boyutun yok</div>
                  </div>
                </div>
              )}
            </div>

            {sonuc.sonuclar.length === 0 && (
              <div className="veri-yok-grafik">
                <div className="vg-ikon">📊</div>
                <div className="vg-metin">Bu katman için sonuç bulunamadı.</div>
              </div>
            )}

            <button
              className="btn full"
              style={{ marginTop: 16 }}
              onClick={() => navigate(sonrakiKod ? `/sonuc/${sonrakiKod}` : '/sonuc/genel')}
            >
              {sonrakiKod ? `Katman ${sonrakiKod} Sonuçlarına Git →` : 'Genel Sonuçlara Git →'}
            </button>
          </div>

          {hedef && (
            <div className="yan-panel">
              <div className="card" style={{ marginBottom: 0 }}>
                <div className="ct">🎯 {hedef.bolum_adi} İle Karşılaştırma</div>
                {hedefKarsilastirma.length === 0 ? (
                  <div className="ps" style={{ margin: 0 }}>Bu katman için henüz karşılaştırma verisi yok.</div>
                ) : (
                  <>
                    <div className="drl" style={{ marginBottom: 12 }}>
                      <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
                      <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
                    </div>
                    {hedefKarsilastirma.map((g) => (
                      <div key={g.degisken_id} className="dcr">
                        <div className="dcl" style={{ width: 130, minWidth: 130, fontSize: 11.5 }}>{g.degisken_adi}</div>
                        <div className="dcb">
                          <div className="dcf" style={{ width: `${g.ogrenci_puan}%`, background: 'var(--pu)' }} />
                          <div className="dcf" style={{ width: `${g.bolum_beklenen}%`, background: 'var(--gr)' }} />
                        </div>
                      </div>
                    ))}
                    <button className="btn sec" style={{ width: '100%', marginTop: 12 }} onClick={() => navigate('/koclugu')}>
                      Koçluk Detayına Git
                    </button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
