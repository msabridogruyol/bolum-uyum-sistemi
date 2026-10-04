import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import TemaAnahtari from '../components/TemaAnahtari'

// [2026-10-04] E-postadaki bağlantıdan açılır: /sifre-sifirla?token=...  (rehber daveti de bu sayfayı kullanır)
export default function SifreSifirlaSayfasi({ kapsam = 'ogrenci' }) {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [bilgi, setBilgi] = useState(null)
  const [hata, setHata] = useState(null)
  const [sifre, setSifre] = useState('')
  const [sifre2, setSifre2] = useState('')
  const [tamam, setTamam] = useState(false)
  const [yukleniyor, setYukleniyor] = useState(false)
  const girisYolu = kapsam === 'admin' ? '/admin/giris' : '/giris'

  useEffect(() => {
    if (!token) { setHata('Bağlantı eksik. E-postadaki bağlantıyı tam olarak açtığından emin ol.'); return }
    api.sifreBaglantiBilgisi(token).then(setBilgi).catch((e) => setHata(e?.detail || 'Bağlantı geçersiz.'))
  }, [token])

  async function gonder(e) {
    e.preventDefault()
    setHata(null)
    if (sifre !== sifre2) { setHata('Şifreler aynı değil.'); return }
    setYukleniyor(true)
    try {
      await api.sifreSifirla(token, sifre)
      setTamam(true)
    } catch (err) {
      setHata(typeof err?.detail === 'string' ? err.detail : 'Şifre en az 8 karakter olmalı.')
    } finally {
      setYukleniyor(false)
    }
  }

  const davet = bilgi?.amac === 'davet'
  return (
    <div className="auth-wrap">
      {kapsam !== 'admin' && <TemaAnahtari />}
      <div className="auth-card">
        <span className="auth-emoji">{davet ? '👋' : '🔒'}</span>
        <div className="auth-logo">{davet ? 'Hoş geldin' : 'Yeni şifre belirle'}</div>
        <div className="auth-sub">
          {bilgi ? `${bilgi.ad} · ${bilgi.maskeli_eposta}` : ' '}
        </div>
        {tamam ? (
          <>
            <div className="auth-error" style={{ background: 'var(--grl)', color: 'var(--gr)' }}>
              Şifren kaydedildi. Artık yeni şifrenle giriş yapabilirsin.
            </div>
            <Link to={girisYolu} className="btn full" style={{ display: 'block', textAlign: 'center', textDecoration: 'none' }}>Giriş yap</Link>
          </>
        ) : (
          <>
            {hata && <div className="auth-error">{hata}</div>}
            {bilgi && (
              <form onSubmit={gonder}>
                <div className="auth-field">
                  <label className="auth-label">Yeni şifre (en az 8 karakter)</label>
                  <input className="auth-input" type="password" value={sifre} onChange={(e) => setSifre(e.target.value)} required minLength={8} autoFocus autoComplete="new-password" />
                </div>
                <div className="auth-field">
                  <label className="auth-label">Yeni şifre (tekrar)</label>
                  <input className="auth-input" type="password" value={sifre2} onChange={(e) => setSifre2(e.target.value)} required minLength={8} autoComplete="new-password" />
                </div>
                <button className="btn full" type="submit" disabled={yukleniyor}>
                  {yukleniyor ? <span className="spin" /> : 'Şifremi kaydet'}
                </button>
              </form>
            )}
            {!bilgi && hata && (
              <div className="auth-foot"><Link to={kapsam === 'admin' ? '/admin/sifremi-unuttum' : '/sifremi-unuttum'} className="auth-link">Yeni bağlantı iste</Link></div>
            )}
          </>
        )}
        <div className="auth-foot"><Link to={girisYolu} className="auth-link">← Giriş sayfasına dön</Link></div>
      </div>
    </div>
  )
}
