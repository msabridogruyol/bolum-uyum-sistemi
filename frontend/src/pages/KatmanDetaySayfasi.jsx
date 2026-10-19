import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { GUCLU_ESIK, ORTA_ESIK, gelisimeAcikMi, gucluMu, seviyeEtiketi, seviyeRengi } from '../yardimci/seviye'
import { katmanAdi } from '../yardimci/katmanAdlari'

const KATMAN_BOYUT_SAYISI = { K1: 7, K2: 8, K3: 7, K4: 9 }

// [2026-10-10] İkinci sütunda Orta ve Gelişime açık boyutlar birlikte durur; "Gelişim" başlığı Orta puanları da
// gelişim alanı gibi gösterdiği için tüm katmanlarda tarafsız başlık kullanılır.
const IKINCI_BOLUM_BASLIGI = { K1: 'Diğer Boyutların', K2: 'Diğer Boyutların', K3: 'Diğer Boyutların', K4: 'Diğer Boyutların' }
const SONRAKI_KATMAN = { K1: 'K2', K2: 'K3', K3: 'K4', K4: null }

const renkSec = seviyeRengi   // [2026-10-10] tek kaynak bantlar (yardimci/seviye.js)

function BoyutSatiri({ s }) {
  const [acik, setAcik] = useState(false)
  const detayVarMi = s.durum_tespiti || s.aksiyon_onerisi || s.maarif?.length

  return (
    <div className={`boyut-satir${acik ? ' acik' : ''}`} onClick={() => detayVarMi && setAcik((a) => !a)}>
      <div className="boyut-satir-ust">
        {detayVarMi && <span className="ok">▶</span>}
        <div className="dr" style={{ flex: 1, marginBottom: 0 }}>
          <div className="dl">{s.degisken_adi}</div>
          <div className="db"><div className="df" style={{ width: `${s.puan}%`, background: renkSec(s.puan) }} /></div>
          <div className="ds" style={{ color: renkSec(s.puan) }} title={seviyeEtiketi(s.puan)}>{Math.round(s.puan)}</div>
        </div>
      </div>
      {detayVarMi && (
        <div className="boyut-detay">
          {s.durum_tespiti && (
            <div style={{ fontSize: 12, color: 'var(--tx2)', lineHeight: 1.55, paddingLeft: 18 }}>{s.durum_tespiti}</div>
          )}
          {s.maarif?.length > 0 && (
            <div className="maarif-satir" style={{ paddingLeft: 18 }}>Maarif Modeli'nde ilişkili: <span translate="no">{s.maarif.join(' · ')}</span></div>
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

export default function KatmanDetaySayfasi({ gomulu = false }) {
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
  if (!katman || !sonuc || hedef === undefined || gelisim === null) return <div className="pg"><div className="bos-durum yukleniyor">Yükleniyor…</div></div>

  // [2026-10-18] Sade düzen: tek sıralı liste, bantlara göre gruplu. Puanlar katman içinde görelidir.
  // Değerler (K1) güçlü/gelişim diye değil önem düzeyiyle adlandırılır; P4 ters yönlüdür, ayrı gösterilir.
  const siraliSonuclar = [...sonuc.sonuclar].sort((a, b) => b.puan - a.puan)
  const p4 = siraliSonuclar.filter((s) => s.degisken_kod === 'P4')
  const liste = siraliSonuclar.filter((s) => s.degisken_kod !== 'P4')
  const deger = kod === 'K1'
  const GRUPLAR = [
    { ad: deger ? 'Senin için en önemliler' : 'Güçlü yönlerin', alt: `${GUCLU_ESIK} ve üstü`, f: (s) => gucluMu(s.puan) },
    { ad: 'Orta', alt: `${ORTA_ESIK}–${GUCLU_ESIK - 1}`, f: (s) => !gucluMu(s.puan) && !gelisimeAcikMi(s.puan) },
    { ad: deger ? 'Senin için daha az belirleyici' : 'Gelişime açık yönlerin', alt: `${ORTA_ESIK}'ın altı`, f: (s) => gelisimeAcikMi(s.puan) },
  ]
  const sonrakiKod = SONRAKI_KATMAN[kod]

  // Hedef karşılaştırması — yalnızca BU katmanın değişkenleriyle sınırlı
  const buKatmanDegiskenIdleri = new Set(sonuc.sonuclar.map((s) => s.degisken_id))
  const hedefKarsilastirma = gelisim.filter((g) => buKatmanDegiskenIdleri.has(g.degisken_id))

  return (
    <div className="pg pg-genis">
      {!gomulu && <button className="back" onClick={() => navigate('/profilim')}>← Profilime dön</button>}

      <div className="ph">
        <div className="ph-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div className="pt">{katmanAdi(kod, katman.ad)}</div>
            <div className="ps">
              {sonuc.sonuclar.length || KATMAN_BOYUT_SAYISI[kod]} özellik · Puanlar bu katmandaki diğer özelliklerine göre görelidir; bir yetenek ölçüsü değildir.
            </div>
          </div>
          <span className={`bdg ${katman.durum === 'tamamlandi' ? 'bdg-done' : 'bdg-lock'}`} style={{ fontSize: 11, padding: '4px 10px' }}>
            {katman.durum === 'tamamlandi' ? 'Tamamlandı' : 'Devam Ediyor'}
          </span>
        </div>
      </div>

      <div className="yol-duzen">
        <div>
          {!sonuc.tamamlandi_mi ? (
            <>
              <div className="taslak-onizleme">
                <div className="taslak-onizleme-icerik two">
                  <div className="card" style={{ marginBottom: 0 }}>
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
                  <div className="card" style={{ marginBottom: 0 }}>
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
                </div>
                <div className="taslak-onizleme-overlay">
                  <div className="to-ikon">📊</div>
                  <div className="to-metin">Bu katmanı henüz tamamlamadın.</div>
                </div>
              </div>
              <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate(`/katmanlar/${kod}`)}>
                {katman.durum === 'devam_ediyor' ? 'Kaldığın Yerden Devam Et' : 'Bu Katmana Başla'}
              </button>
            </>
          ) : (
            <>
              <div className="card">
                <div className="ct">Özelliklerin — yüksekten düşüğe</div>
                {siraliSonuclar.some((s) => s.durum_tespiti || s.aksiyon_onerisi) && (
                  <div className="ps" style={{ margin: '-4px 0 10px', fontSize: 12 }}>Açıklamasını görmek için ▶ işaretli bir özelliğe dokun.</div>
                )}
                {GRUPLAR.map((g) => {
                  const ogeler = liste.filter(g.f)
                  if (!ogeler.length) return null
                  return (
                    <div key={g.ad} className="kd-grup">
                      <div className="kd-grup-baslik">{g.ad} <small>{g.alt}</small></div>
                      {ogeler.map((s) => <BoyutSatiri key={s.degisken_id} s={s} />)}
                    </div>
                  )
                })}
                {p4.length > 0 && (
                  <div className="kd-grup">
                    <div className="kd-grup-baslik">Ters yönlü özellik <small>yüksek puan = strese daha açık; düşük puan = daha sakin</small></div>
                    {p4.map((s) => <BoyutSatiri key={s.degisken_id} s={s} />)}
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
                onClick={() => navigate(sonrakiKod ? `/profilim/${sonrakiKod}` : '/profilim')}
              >
                {sonrakiKod ? `Sonraki: ${katmanAdi(sonrakiKod)} →` : 'Genel bakışa dön →'}
              </button>
            </>
          )}
        </div>

        {/* ============ SAĞ PANEL — her zaman görünür ============ */}
        <div className="yan-panel">
          {(!hedef || !sonuc.tamamlandi_mi) && (
            <div className="card" style={{ marginBottom: 0 }}>
              <div className="ct">Nasıl okunur?</div>
              <div className="ps" style={{ margin: 0, fontSize: 12 }}>
                {GUCLU_ESIK} ve üstü kendi profilinde öne çıkan, {ORTA_ESIK}'ın altı geride kalan özelliklerindir.
                {hedef ? '' : ' Bir hedef bölüm seçersen burada o bölümün beklentisiyle karşılaştırma da görürsün.'}
              </div>
            </div>
          )}

          {hedef && sonuc.tamamlandi_mi && (
            <div className="card" style={{ marginBottom: 0 }}>
              <div className="ct">🎯 {hedef.bolum_adi} ile karşılaştırma</div>
              {hedefKarsilastirma.length === 0 ? (
                <div className="ps" style={{ margin: 0 }}>Bu katman için henüz karşılaştırma verisi yok.</div>
              ) : (
                <>
                  <div className="drl" style={{ marginBottom: 12 }}>
                    <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
                    <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
                  </div>
                  {hedefKarsilastirma.map((g) => (
                    <div key={g.degisken_id} className="dcr" title={`Sen ${Math.round(g.ogrenci_puan)} · Bölüm ${Math.round(g.bolum_beklenen)}`}>
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
          )}
        </div>
      </div>
    </div>
  )
}
