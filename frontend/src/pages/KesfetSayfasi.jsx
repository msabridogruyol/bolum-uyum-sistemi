import { useState } from 'react'
import { api } from '../api/client'

const ORNEK_ARAMALAR = ['Tıp', 'Bilgisayar Mühendisliği', 'Psikoloji', 'Hukuk', 'İşletme', 'Mimarlık']

const KATMAN_RENK = { K1: 'var(--pu)', K2: 'var(--gr)', K3: 'var(--am)', K4: 'var(--tl, var(--pu))' }

export default function KesfetSayfasi() {
  const [sorgu, setSorgu] = useState('')
  const [sonuclar, setSonuclar] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState(null)

  async function aramaYap(terim) {
    const t = (terim ?? sorgu).trim()
    if (t.length < 2) {
      setHata('Arama terimi en az 2 karakter olmalı.')
      return
    }
    setHata(null)
    setYukleniyor(true)
    setSorgu(t)
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
    <div className="pg">
      <div className="ph">
        <div className="pt">Tüm Bölümleri Keşfet</div>
        <div className="ps">301 bölümün tamamı elinin altında — herhangi bir bölümü ara, katman bazlı uyumunu gör.</div>
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
          <div className="ps" style={{ marginBottom: 12, fontSize: 12 }}>{sonuclar.length} sonuç bulundu</div>
          <div className="ob-grid">
            {sonuclar.map((s) => (
              <div key={s.bolum_id} className="ob-card" style={{ cursor: 'default' }}>
                <div className="ob-top">
                  <div className="ob-body">
                    <div className="ob-name">{s.bolum_adi}</div>
                    {s.kisa_aciklama && <div className="ld" style={{ marginTop: 3 }}>{s.kisa_aciklama}</div>}
                  </div>
                  <div className="ob-score">{s.toplam_uyum !== null ? `%${Math.round(s.toplam_uyum)}` : '—'}</div>
                </div>
                {Object.keys(s.katman_ortalamalari).length > 0 && (
                  <div style={{ display: 'flex', gap: 10, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)', flexWrap: 'wrap' }}>
                    {Object.entries(s.katman_ortalamalari).map(([kod, deger]) => (
                      <div key={kod} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                        <span style={{ fontSize: 10.5, fontWeight: 700, color: KATMAN_RENK[kod] || 'var(--tx3)' }}>{kod}</span>
                        <div style={{ width: 36, height: 5, background: 'var(--sur2)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${deger}%`, height: '100%', background: KATMAN_RENK[kod] || 'var(--tx3)', borderRadius: 3 }} />
                        </div>
                        <span style={{ fontSize: 10.5, color: 'var(--tx3)', fontWeight: 600 }}>{deger}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
