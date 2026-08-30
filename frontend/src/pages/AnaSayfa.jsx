import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const KATMAN_IKON = { K1: '🌱', K2: '🌿', K3: '🍃', K4: '🌸' }
const ANA_KATMANLAR = ['K1', 'K2', 'K3', 'K4']

export default function AnaSayfa() {
  const [ozet, setOzet] = useState(null)
  const [katmanlar, setKatmanlar] = useState(null)
  const [siralama, setSiralama] = useState(null)
  const [profil, setProfil] = useState(null)
  const [katmanSonuclari, setKatmanSonuclari] = useState(null)
  const [k5Durum, setK5Durum] = useState(null)
  const [hedef, setHedef] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.durumOzetiGetir().then(setOzet).catch(() => {})
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail))
    api.profilGetir().then(setProfil).catch(() => {})
    api.k5Durumu().then(setK5Durum).catch(() => setK5Durum({ acilan: [], ilgi_gosterilen: [] }))
    api.aktifHedefGetir().then(setHedef).catch(() => setHedef(null))
  }, [])

  useEffect(() => {
    if (!ozet) return
    if (ozet.tur_tamamlandi_mi) {
      api.siralamaGetir(10).then(setSiralama).catch(() => setSiralama([]))
    } else {
      setSiralama([])
    }
    // Katman sonuçlarını her durumda tek tek çek — tur tamamlanmamış olsa bile
    // bireysel katmanlar bitmiş olabilir.
    Promise.all(ANA_KATMANLAR.map((kod) => api.katmanSonucuGetir(kod).then((r) => [kod, r]).catch(() => [kod, null])))
      .then((liste) => {
        const harita = {}
        liste.forEach(([kod, r]) => {
          harita[kod] = (r && r.tamamlandi_mi && r.sonuclar.length)
            ? { puanOrtalama: Math.round(r.sonuclar.reduce((a, s) => a + s.puan, 0) / r.sonuclar.length), sonuclar: r.sonuclar }
            : null
        })
        setKatmanSonuclari(harita)
      })
  }, [ozet])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar || !ozet || !katmanSonuclari || !k5Durum) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const ilkAd = (profil?.ad_soyad || 'Öğrenci').split(' ')[0]
  const tamamlananYuzde = katmanlar.length ? Math.round((ozet.tamamlanan_katman_sayisi / ozet.toplam_ana_katman_sayisi) * 100) : 0

  // K5 — dal bazlı, açılan dalların ortalama puanı (varsa)
  const k5OrtalamaPuan = k5Durum.acilan.length > 0
    ? Math.round(k5Durum.acilan.reduce((a, d) => a + d.puan, 0) / k5Durum.acilan.length)
    : null

  // Gerçek "profil skoru" — en yüksek bölüm uyum puanı
  const profilSkoru = siralama && siralama.length > 0 ? Math.round(siralama[0].toplam_uyum) : null

  // Gerçek "etiketler" — tüm katmanlardaki en yüksek puanlı 3 değişken (uydurma tip adı değil)
  const tumSonuclar = ANA_KATMANLAR.flatMap((kod) => katmanSonuclari[kod]?.sonuclar || [])
  const enYuksek3 = [...tumSonuclar].sort((a, b) => b.puan - a.puan).slice(0, 3)

  // Güç dağılımı — güçlü/orta/gelişim sayıları (gerçek puanlardan)
  const guclu = tumSonuclar.filter((s) => s.puan >= 70).length
  const gelisimSayisi = tumSonuclar.filter((s) => s.puan < 40).length
  const orta = tumSonuclar.length - guclu - gelisimSayisi
  const toplamBoyut = tumSonuclar.length || 1 // 0'a bölünmeyi önle

  const hedefBolumAdi = hedef?.bolum_adi || null
  const hedefUniversite = profil?.hedef_universite || null

  return (
    <div className="pg pg-genis">
      <div className="ph anasayfa-duzen" style={{ alignItems: 'flex-start' }}>
        <div>
          <div className="pt">Merhaba, {ilkAd} 👋</div>
          <div className="ps">
            {ozet.tur_tamamlandi_mi
              ? 'Tüm katmanlar tamamlandı — işte senin bölüm uyum profilin.'
              : `Yolculuğunun %${tamamlananYuzde}'ini tamamladın.`}
          </div>
        </div>

        {hedefBolumAdi && (
          <div
            onClick={() => navigate('/koclugu')}
            style={{
              cursor: 'pointer',
              background: 'linear-gradient(135deg, var(--pu) 0%, #f0a868 100%)',
              borderRadius: 16,
              padding: '14px 22px',
              boxShadow: '0 6px 18px -6px rgba(232, 128, 74, 0.55)',
              width: '100%',
            }}
          >
            <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.85)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
              🎯 Hedef
            </div>
            <div style={{ fontSize: 19, fontWeight: 800, color: '#fff', marginTop: 3, lineHeight: 1.25 }}>
              {hedefBolumAdi}
            </div>
            {hedefUniversite && (
              <div style={{ fontSize: 14, fontWeight: 700, color: 'rgba(255,255,255,0.92)', marginTop: 3 }}>
                {hedefUniversite}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="anasayfa-duzen">
        {/* ============ SOL SÜTUN — ana içerik ============ */}
        <div>
          {/* --- Profil kartı --- */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
              <div className="av" style={{ width: 56, height: 56, fontSize: 24, overflow: 'hidden' }}>
                {profil?.profil_foto_base64
                  ? <img src={profil.profil_foto_base64} alt="Profil" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : '🎓'}
              </div>
              <div style={{ flex: 1, minWidth: 160 }}>
                <div style={{ fontSize: 17, fontWeight: 700 }}>{profil?.ad_soyad || 'Öğrenci'}</div>
                <div style={{ fontSize: 12, color: 'var(--tx3)', marginBottom: 8 }}>
                  {[profil?.okul, profil?.sinif].filter(Boolean).join(' · ') || 'Okul bilgisi eklenmedi'}
                </div>
                {enYuksek3.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {enYuksek3.map((s) => (
                      <span key={s.degisken_id} className="bdg bdg-prog">{s.degisken_adi}</span>
                    ))}
                  </div>
                )}
              </div>
              {profilSkoru !== null && (
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 10.5, color: 'var(--tx3)', marginBottom: 2 }}>En yüksek uyum</div>
                  <div style={{ fontFamily: 'var(--fd)', fontSize: 32, fontWeight: 700, color: 'var(--pu)', lineHeight: 1 }}>{profilSkoru}</div>
                  <div style={{ fontSize: 10, color: 'var(--tx3)' }}>/ 100</div>
                </div>
              )}
              <button className="btn sec" onClick={() => navigate('/profil')}>Profili Düzenle</button>
            </div>

            <div style={{ display: 'flex', gap: 8, marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--bor)', flexWrap: 'wrap' }}>
              {ANA_KATMANLAR.map((kod) => {
                const k = katmanlar.find((x) => x.kod === kod)
                const sonuc = katmanSonuclari[kod]
                return (
                  <div key={kod} onClick={() => navigate(`/sonuc/${kod}`)} style={{ flex: '1 1 90px', textAlign: 'center', cursor: 'pointer' }}>
                    <div style={{ fontSize: 18 }}>{KATMAN_IKON[kod]}</div>
                    <div style={{ fontSize: 9.5, color: 'var(--tx3)', marginTop: 3, fontWeight: 600 }}>{k?.ad?.split('/')[0]?.split('&')[0]?.trim() || kod}</div>
                    <div style={{ fontSize: 13, fontWeight: 700, marginTop: 1, color: sonuc ? 'var(--gr)' : k?.durum === 'devam_ediyor' ? 'var(--pu)' : 'var(--tx3)' }}>
                      {sonuc ? `${sonuc.puanOrtalama}%` : k?.durum === 'devam_ediyor' ? 'Devam ediyor' : 'Henüz başlanmadı'}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* --- Önerilen bölümler --- */}
          <div className="ct" style={{ marginTop: 20 }}>Sana Önerilen Bölümler</div>
          {!ozet.tur_tamamlandi_mi ? (
            <>
              <div className="taslak-onizleme">
                <div className="taslak-onizleme-icerik" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
                  {[92, 87, 81, 76, 70, 65, 60, 55, 50, 46, 42, 38].map((genislik, i) => (
                    <div key={i} className="ob-card" style={{ cursor: 'default' }}>
                      <div className="ob-top">
                        <div className="ob-rank">{i + 1}</div>
                        <div className="ob-body">
                          <div className="iskelet-satir" style={{ width: '70%', marginBottom: 8 }} />
                          <div className="mini-ilerleme-track" style={{ width: '100%' }}>
                            <div className="mini-ilerleme-fill" style={{ width: `${genislik}%`, background: 'var(--pu)' }} />
                          </div>
                        </div>
                        <div className="ob-score">%{genislik}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="taslak-onizleme-overlay">
                  <div className="to-ikon">🌱</div>
                  <div className="to-metin">
                    Bölüm önerilerin, K1-K4'ün tamamı bitince burada görünecek — şu an {ozet.tamamlanan_katman_sayisi}/{ozet.toplam_ana_katman_sayisi} katman tamamlandı.
                  </div>
                </div>
              </div>
              <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/katmanlar')}>
                {ozet.tamamlanan_katman_sayisi === 0 ? 'Yolculuğuna Başla' : 'Kaldığın Yerden Devam Et'} →
              </button>
            </>
          ) : siralama === null ? (
            <div className="bos-durum">Yükleniyor…</div>
          ) : siralama.length === 0 ? (
            <div className="veri-yok-grafik">
              <div className="vg-ikon">🌱</div>
              <div className="vg-metin">Henüz önerilecek bölüm hesaplanmadı.</div>
            </div>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
                {siralama.map((s, i) => (
                  <div key={s.bolum_id} className="ob-card" style={{ cursor: 'default' }}>
                    <div className="ob-top">
                      <div className={`ob-rank${i < 3 ? ' top' : ''}`}>{i + 1}</div>
                      <div className="ob-body">
                        <div className="ob-name">{s.bolum_adi}</div>
                        <div className="mini-ilerleme-track" style={{ width: '100%', marginTop: 6 }}>
                          <div className="mini-ilerleme-fill" style={{ width: `${s.toplam_uyum}%`, background: 'var(--pu)' }} />
                        </div>
                      </div>
                      <div className="ob-score">%{Math.round(s.toplam_uyum)}</div>
                    </div>
                  </div>
                ))}
              </div>
              <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/koclugu')}>
                Bölüm Karşılaştırmasına Git →
              </button>
            </>
          )}
        </div>

        {/* ============ SAĞ SÜTUN — yan panel widget'ları ============ */}
        <div className="yan-panel">
          <div className="card" style={{ marginBottom: 0 }}>
            <div className="ct">Güç Dağılımın</div>
            {tumSonuclar.length === 0 ? (
              <div className="taslak-onizleme">
                <div className="taslak-onizleme-icerik">
                  <div className="donut-wrap">
                    <div className="donut" style={{ background: 'conic-gradient(var(--sur2) 0deg 360deg)' }} />
                    <div className="donut-legend">
                      <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--sur2)' }} /><span className="donut-legend-etiket">Güçlü</span></div>
                      <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--sur2)' }} /><span className="donut-legend-etiket">Orta</span></div>
                      <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--sur2)' }} /><span className="donut-legend-etiket">Gelişim</span></div>
                    </div>
                  </div>
                </div>
                <div className="taslak-onizleme-overlay">
                  <div className="to-metin" style={{ fontSize: 11.5 }}>Katmanlar tamamlandıkça burada dolacak</div>
                </div>
              </div>
            ) : (
              <div className="donut-wrap">
                <div
                  className="donut"
                  style={{
                    background: `conic-gradient(var(--gr) 0deg ${(guclu / toplamBoyut) * 360}deg, var(--pu) ${(guclu / toplamBoyut) * 360}deg ${((guclu + orta) / toplamBoyut) * 360}deg, var(--am) ${((guclu + orta) / toplamBoyut) * 360}deg 360deg)`,
                  }}
                >
                  <div className="donut-ortasi">
                    <div className="sayi">{toplamBoyut}</div>
                    <div className="etiket">BOYUT</div>
                  </div>
                </div>
                <div className="donut-legend">
                  <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--gr)' }} /><span className="donut-legend-etiket">Güçlü (70+)</span><span className="donut-legend-sayi" style={{ color: 'var(--gr)' }}>{guclu}</span></div>
                  <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--pu)' }} /><span className="donut-legend-etiket">Orta (40-69)</span><span className="donut-legend-sayi" style={{ color: 'var(--pu)' }}>{orta}</span></div>
                  <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--am)' }} /><span className="donut-legend-etiket">Gelişim (&lt;40)</span><span className="donut-legend-sayi" style={{ color: 'var(--am)' }}>{gelisimSayisi}</span></div>
                </div>
              </div>
            )}
          </div>

          <div className="card" style={{ marginBottom: 0 }}>
            <div className="ct">Katman Ortalamaların</div>

            {/* Genel tamamlama oranı — ayrı, vurgulu satır */}
            <div className="mini-cubuk-satir" style={{ marginBottom: 14, paddingBottom: 12, borderBottom: '1px solid var(--bor)' }}>
              <div className="mini-cubuk-etiket" style={{ width: 78 }}>🎯 Genel</div>
              <div className="mini-cubuk-track">
                <div className="mini-cubuk-fill" style={{ width: `${tamamlananYuzde}%`, background: 'var(--pu)' }} />
              </div>
              <div className="mini-cubuk-deger" style={{ color: 'var(--pu)' }}>{tamamlananYuzde}%</div>
            </div>

            {ANA_KATMANLAR.map((kod) => {
              const sonuc = katmanSonuclari[kod]
              const k = katmanlar.find((x) => x.kod === kod)
              const deger = sonuc ? sonuc.puanOrtalama : 0
              return (
                <div key={kod} className="mini-cubuk-satir">
                  <div className="mini-cubuk-etiket">{KATMAN_IKON[kod]} {kod}</div>
                  <div className="mini-cubuk-track">
                    <div
                      className={`mini-cubuk-fill${!sonuc ? ' df-placeholder' : ''}`}
                      style={{ width: sonuc ? `${deger}%` : '100%', background: sonuc ? 'var(--gr)' : 'transparent' }}
                    />
                  </div>
                  <div className="mini-cubuk-deger" style={{ color: sonuc ? 'var(--gr)' : 'var(--tx3)' }}>
                    {sonuc ? `${deger}%` : '—'}
                  </div>
                </div>
              )
            })}

            {/* K5 — dal bazlı, farklı mantık */}
            <div className="mini-cubuk-satir">
              <div className="mini-cubuk-etiket">🌻 K5</div>
              <div className="mini-cubuk-track">
                <div
                  className={`mini-cubuk-fill${k5OrtalamaPuan === null ? ' df-placeholder' : ''}`}
                  style={{ width: k5OrtalamaPuan !== null ? `${k5OrtalamaPuan}%` : '100%', background: k5OrtalamaPuan !== null ? 'var(--gr)' : 'transparent' }}
                />
              </div>
              <div className="mini-cubuk-deger" style={{ color: k5OrtalamaPuan !== null ? 'var(--gr)' : 'var(--tx3)', width: k5OrtalamaPuan === null ? 74 : 32, fontSize: k5OrtalamaPuan === null ? 9.5 : 11.5, textAlign: 'right' }}>
                {k5OrtalamaPuan !== null ? `${k5OrtalamaPuan}%` : 'Henüz kapalı'}
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 0 }}>
            <div className="ct">Yolculuk Bilgisi</div>
            <div className="mini-satir"><span className="mini-ad">Tur</span><span className="mini-deger">#{ozet.tur_no ?? '—'}</span></div>
            <div className="mini-satir"><span className="mini-ad">Tamamlanan Katman</span><span className="mini-deger">{ozet.tamamlanan_katman_sayisi}/{ozet.toplam_ana_katman_sayisi}</span></div>
            {ozet.k5_acilan_dal_sayisi > 0 && (
              <div className="mini-satir"><span className="mini-ad">Derinleşme Dalı</span><span className="mini-deger">{ozet.k5_tamamlanan_dal_sayisi}/{ozet.k5_acilan_dal_sayisi}</span></div>
            )}
            {ozet.sonraki_tur_tarihi ? (
              <div className="mini-satir"><span className="mini-ad">Sonraki Tur</span><span className="mini-deger">{new Date(ozet.sonraki_tur_tarihi).toLocaleDateString('tr-TR')}</span></div>
            ) : (
              <div className="mini-satir"><span className="mini-ad">Sonraki Tur</span><span className="mini-deger" style={{ color: 'var(--tx3)' }}>Tur bitince belirlenir</span></div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
