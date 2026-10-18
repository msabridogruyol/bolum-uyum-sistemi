import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

// [2026-10-18] Yeni K5: ilk dört katmanda sana en uygun çıkan bölümler (en fazla 20) iş türü sorularıyla kendi
// aralarında karşılaştırılır. Bu sayfa K5 adımının durumunu ve iş türü puanlarını gösterir (eski "alan derinleşme"
// sayfasının yerine; düzen aynı).
export default function K5SonucSayfasi({ gomulu = false }) {
  const [k5Durum, setK5Durum] = useState(null)
  const [sonuc, setSonuc] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.k5Durumu().then(setK5Durum).catch((e) => setHata(e.detail || 'K5 durumu alınamadı.'))
    api.katmanSonucuGetir('K5').then(setSonuc).catch(() => setSonuc(null))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!k5Durum) return <div className="pg"><div className="bos-durum yukleniyor">Yükleniyor…</div></div>

  const adim = k5Durum.acilan[0]
  const isTurleri = sonuc?.tamamlandi_mi ? [...sonuc.sonuclar].sort((a, b) => b.puan - a.puan) : []
  const bitti = adim?.durum === 'tamamlandi' || isTurleri.length > 0

  return (
    <div className="pg pg-genis">
      {!gomulu && <button className="back" onClick={() => navigate('/profilim')}>← Profilime dön</button>}

      <div className="ph">
        <div className="pt">İş Türü Tercihleri — Sonuçların</div>
        <div className="ps">
          İlk dört katmanda sana en uygun çıkan bölümler, bu bölümlerde yapılan işlerle ilgili sorularla kendi aralarında
          karşılaştırılır. Burada hangi işleri daha çok seçtiğini görürsün.
        </div>
      </div>

      <div className="yol-duzen">
        <div>
          {!adim ? (
            <div className="taslak-onizleme">
              <div className="taslak-onizleme-icerik">
                <div className="ll">
                  {[78, 64, 52].map((p, i) => (
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
                  İlk dört katmanı bitirince sana özel iş türü soruları açılır; sonuçların burada görünecek.
                </div>
              </div>
            </div>
          ) : !bitti ? (
            <div className="ll" style={{ marginBottom: 20 }}>
              <div className="lc" onClick={() => navigate(`/k5/${adim.dal_kodu}`)}>
                <div className="ln" style={{ background: 'var(--pul)', color: 'var(--pu)' }}>🌟</div>
                <div className="lb-wrap">
                  <div className="lt">{adim.dal_adi}</div>
                  <div className="ld">Sana en uygun {Math.round(adim.puan)} bölüm kendi aralarında karşılaştırılacak.</div>
                  <span className="bdg bdg-prog">{adim.durum === 'devam_ediyor' ? 'Devam et — sorularını cevapla' : 'Açık — sorularını cevapla'}</span>
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="ct">Hangi işleri ne kadar seçtin</div>
              <div className="ll" style={{ marginBottom: 20 }}>
                {isTurleri.map((x) => (
                  <div key={x.degisken_id} className="lc" style={{ cursor: 'default' }}>
                    <div className="ln" style={{ background: 'var(--pul)', color: 'var(--pu)' }}>🌟</div>
                    <div className="lb-wrap">
                      <div className="lt">{x.degisken_adi}</div>
                    </div>
                    <div style={{ fontFamily: 'var(--fd)', fontWeight: 700, fontSize: 18, color: 'var(--pu)' }}>{Math.round(x.puan)}</div>
                  </div>
                ))}
              </div>
              <div className="ps" style={{ margin: 0 }}>
                Puan 0-100 arasıdır; 50 bu işi ne öne çıkardığını ne de geri plana attığını gösterir. Bu tercihler yalnızca sana en
                uygun çıkan bölümlerin kendi aralarındaki sırasını değiştirebilir; asıl belirleyici ilk dört katmandır.
              </div>
            </>
          )}
        </div>

        {/* ============ SAĞ PANEL — Öne Çıkanlar ============ */}
        <div className="yan-panel">
          <div className="card" style={{ marginBottom: 0 }}>
            <div className="ct">Öne Çıkanlar</div>
            {isTurleri.length > 0 ? (
              <>
                <div style={{ marginBottom: 14 }}>
                  <div style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--gr)', marginBottom: 6 }}>✓ En çok seçtiğin iş</div>
                  <div style={{ fontSize: 12, color: 'var(--tx2)', lineHeight: 1.5 }}>
                    <b style={{ color: 'var(--tx)' }}>{isTurleri[0].degisken_adi}</b>
                  </div>
                </div>
                {isTurleri.length > 1 && (
                  <div>
                    <div style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--am)', marginBottom: 6 }}>↻ En az seçtiğin iş</div>
                    <div style={{ fontSize: 12, color: 'var(--tx2)', lineHeight: 1.5 }}>
                      <b style={{ color: 'var(--tx)' }}>{isTurleri[isTurleri.length - 1].degisken_adi}</b>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="ps" style={{ margin: 0 }}>
                {adim ? 'İş türü sorularını bitirince sana özel yorumlar burada görünecek.' : 'Henüz veri yok.'}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
