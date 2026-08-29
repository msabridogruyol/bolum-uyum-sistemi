import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const ORNEK_ARAMALAR = ['Tıp', 'Bilgisayar Mühendisliği', 'Psikoloji', 'Hukuk', 'İşletme', 'Mimarlık']
const KATMAN_ADI = { K1: 'Değerler', K2: 'Kişilik', K3: 'İş Ortamı', K4: 'Alan Eğilimi' }
const KATMAN_RENK = { K1: 'var(--pu)', K2: 'var(--gr)', K3: 'var(--am)', K4: 'var(--tl, var(--pu))' }

export default function KesfetSayfasi() {
  const [sorgu, setSorgu] = useState('')
  const [sonuclar, setSonuclar] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [secili, setSecili] = useState(null)
  const [meslekler, setMeslekler] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!secili) { setMeslekler(null); return }
    setMeslekler(null)
    api.bolumOrnekMeslekleriGetir(secili.bolum_id).then(setMeslekler).catch(() => setMeslekler([]))
  }, [secili])

  async function aramaYap(terim) {
    const t = (terim ?? sorgu).trim()
    if (t.length < 2) {
      setHata('Arama terimi en az 2 karakter olmalı.')
      return
    }
    setHata(null)
    setYukleniyor(true)
    setSorgu(t)
    setSecili(null)
    try {
      setSonuclar(await api.kesfetAra(t))
    } catch (err) {
      setHata(err.detail || 'Arama yapılamadı.')
    } finally {
      setYukleniyor(false)
    }
  }

  function ara(e) {
    e.preventDefault()
    aramaYap()
  }

  return (
    <div className={`pg${secili ? ' pg-genis' : ''}`}>
      <div className="ph">
        <div className="pt">Tüm Bölümleri Keşfet</div>
        <div className="ps">301 bölümün tamamı elinin altında — bir bölüme tıkla, genel profilini ve örnek mesleklerini incele.</div>
      </div>

      <form onSubmit={ara} style={{ display: 'flex', gap: 8, marginBottom: sonuclar ? 20 : 14 }}>
        <input
          className="auth-input"
          style={{ flex: 1 }}
          value={sorgu}
          onChange={(e) => setSorgu(e.target.value)}
          placeholder="örn. Tıp, Ekonometri, Hukuk..."
          autoFocus
        />
        <button className="btn" type="submit" disabled={yukleniyor}>
          {yukleniyor ? <span className="spin" /> : '🔍 Ara'}
        </button>
      </form>

      {hata && <div className="auth-error">{hata}</div>}

      {!sonuclar && !yukleniyor && (
        <div>
          <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--tx3)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.04em' }}>
            Popüler Aramalar
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 24 }}>
            {ORNEK_ARAMALAR.map((ornek) => (
              <button
                key={ornek}
                type="button"
                className="bdg bdg-prog"
                style={{ fontSize: 13, padding: '8px 16px', cursor: 'pointer', border: 'none' }}
                onClick={() => aramaYap(ornek)}
              >
                {ornek}
              </button>
            ))}
          </div>
          <div className="veri-yok-grafik">
            <div className="vg-ikon">🔍</div>
            <div className="vg-metin">Yukarıdan bir örneğe tıkla ya da yukarıya kendi aramanı yaz.</div>
          </div>
        </div>
      )}

      {sonuclar && sonuclar.length === 0 && (
        <div className="veri-yok-grafik">
          <div className="vg-ikon">🌱</div>
          <div className="vg-metin">"{sorgu}" için sonuç bulunamadı — farklı bir kelimeyle dene.</div>
        </div>
      )}

      {sonuclar && sonuclar.length > 0 && (
        <>
          <div className="ps" style={{ marginBottom: 12, fontSize: 12 }}>{sonuclar.length} sonuç bulundu — birine tıkla</div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginBottom: secili ? 20 : 0 }}>
            {sonuclar.map((s) => (
              <div
                key={s.bolum_id}
                className="ob-card"
                onClick={() => setSecili(s)}
                style={{ borderColor: secili?.bolum_id === s.bolum_id ? 'var(--pu)' : undefined, background: secili?.bolum_id === s.bolum_id ? 'var(--pul)' : undefined }}
              >
                <div className="ob-top">
                  <div className="ob-body"><div className="ob-name">{s.bolum_adi}</div></div>
                  <div className="ob-score">{s.toplam_uyum !== null ? `%${Math.round(s.toplam_uyum)}` : '—'}</div>
                </div>
              </div>
            ))}
          </div>

          {secili && (
            <>
              <div style={{ height: 1, background: 'var(--bor)', margin: '20px 0' }} />

              <div className="yol-duzen">
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                    <div style={{ fontSize: 11, color: 'var(--tx3)', fontWeight: 700, textTransform: 'uppercase' }}>Seçilen Bölüm</div>
                    {secili.toplam_uyum !== null && (
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: 11, color: 'var(--tx3)' }}>Senin uyumun</div>
                        <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--pu)', fontFamily: 'var(--fd)' }}>%{Math.round(secili.toplam_uyum)}</div>
                      </div>
                    )}
                  </div>
                  <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 14 }}>{secili.bolum_adi}</div>

                  <div className="card">
                    <div className="ct">Bölüm Hakkında</div>
                    <div style={{ fontSize: 13.5, color: 'var(--tx2)', lineHeight: 1.6 }}>
                      {secili.kisa_aciklama || 'Bu bölüm için henüz açıklama eklenmedi.'}
                    </div>
                  </div>

                  {Object.keys(secili.katman_ortalamalari).length > 0 && (
                    <div className="card">
                      <div className="ct">Bu Bölümün Genel Profili</div>
                      <div className="ps" style={{ margin: '0 0 12px', fontSize: 12 }}>
                        Bu bölüme genelde uyum sağlayan öğrencilerin katman ortalamaları — kendi puanınla karşılaştırma değil, bölümün genel eğilimi.
                      </div>
                      {Object.entries(secili.katman_ortalamalari).map(([kod, deger]) => (
                        <div key={kod} className="dr">
                          <div className="dl">{KATMAN_ADI[kod] || kod}</div>
                          <div className="db"><div className="df" style={{ width: `${deger}%`, background: KATMAN_RENK[kod] || 'var(--pu)' }} /></div>
                          <div className="ds" style={{ color: KATMAN_RENK[kod] || 'var(--pu)' }}>{deger}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  <button className="btn full" onClick={() => navigate('/koclugu')}>
                    Bu Bölümü Hedef Olarak Seç ve Kişisel Karşılaştırmamı Gör →
                  </button>
                </div>

                {/* ============ SAĞ PANEL — Örnek Meslekler ============ */}
                <div className="yan-panel">
                  <div className="card" style={{ marginBottom: 0 }}>
                    <div className="ct">Örnek Meslekler</div>
                    {meslekler === null ? (
                      <div className="taslak-onizleme">
                        <div className="taslak-onizleme-icerik">
                          {[85, 72, 64, 58, 50].map((p, i) => (
                            <div key={i} className="mini-cubuk-satir">
                              <div className="iskelet-satir" style={{ width: 100, height: 12 }} />
                              <div className="mini-cubuk-track"><div className="mini-cubuk-fill" style={{ width: `${p}%`, background: 'var(--pu)' }} /></div>
                            </div>
                          ))}
                        </div>
                        <div className="taslak-onizleme-overlay">
                          <div className="to-metin" style={{ fontSize: 11.5 }}>Yükleniyor…</div>
                        </div>
                      </div>
                    ) : meslekler.length === 0 ? (
                      <div className="ps" style={{ margin: 0 }}>Bu bölüm için henüz örnek meslek eşleşmesi yok.</div>
                    ) : (
                      meslekler.map((m, i) => (
                        <div key={i} className="mini-cubuk-satir">
                          <div style={{ fontSize: 12, color: 'var(--tx2)', fontWeight: 600, flex: '0 0 auto', width: 'auto', maxWidth: '55%' }}>{m.meslek_adi}</div>
                          <div className="mini-cubuk-track">
                            <div className="mini-cubuk-fill" style={{ width: `${Math.round(m.benzerlik_skoru * 100)}%`, background: 'var(--pu)' }} />
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
