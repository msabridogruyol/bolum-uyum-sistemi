import { useState } from 'react'
import { api } from '../api/client'

export default function KesfetSayfasi() {
  const [sorgu, setSorgu] = useState('')
  const [sonuclar, setSonuclar] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState(null)

  async function ara(e) {
    e.preventDefault()
    if (sorgu.trim().length < 2) {
      setHata('Arama terimi en az 2 karakter olmalı.')
      return
    }
    setHata(null)
    setYukleniyor(true)
    try {
      setSonuclar(await api.kesfetAra(sorgu.trim()))
    } catch (err) {
      setHata(err.detail || 'Arama yapılamadı.')
    } finally {
      setYukleniyor(false)
    }
  }

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Tüm Bölümleri Keşfet</div>
        <div className="ps">301 bölümün tamamı elinin altında — herhangi bir bölümü ara, katman bazlı uyumunu gör.</div>
      </div>

      <form onSubmit={ara} style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
        <input
          className="auth-input"
          style={{ flex: 1 }}
          value={sorgu}
          onChange={(e) => setSorgu(e.target.value)}
          placeholder="örn. Tıp, Ekonometri, Hukuk..."
        />
        <button className="btn" type="submit" disabled={yukleniyor}>
          {yukleniyor ? <span className="spin" /> : 'Ara'}
        </button>
      </form>

      {hata && <div className="auth-error">{hata}</div>}

      {sonuclar && sonuclar.length === 0 && <div className="bos-durum">Sonuç bulunamadı.</div>}

      {sonuclar && sonuclar.length > 0 && (
        <div className="ob-grid">
          {sonuclar.map((s) => (
            <div key={s.bolum_id} className="ob-card">
              <div className="ob-top">
                <div className="ob-body">
                  <div className="ob-name">{s.bolum_adi}</div>
                  {s.kisa_aciklama && <div className="ld">{s.kisa_aciklama}</div>}
                </div>
                <div className="ob-score">{s.toplam_uyum !== null ? `%${Math.round(s.toplam_uyum)}` : '—'}</div>
              </div>
              {Object.keys(s.katman_ortalamalari).length > 0 && (
                <div style={{ display: 'flex', gap: 14, marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--bor)' }}>
                  {Object.entries(s.katman_ortalamalari).map(([kod, deger]) => (
                    <span key={kod} style={{ fontSize: 11, color: 'var(--tx3)' }}>
                      {kod}: <b style={{ color: 'var(--tx2)' }}>{deger}</b>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
