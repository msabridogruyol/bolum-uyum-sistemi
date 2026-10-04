import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import TemaAnahtari from '../components/TemaAnahtari'

// [2026-10-04] Şifremi unuttum — kapsam="ogrenci" (öğrenci + rehber) veya "admin" (yönetim paneli)
export default function SifremiUnuttumSayfasi({ kapsam = 'ogrenci' }) {
  const [email, setEmail] = useState('')
  const [mesaj, setMesaj] = useState(null)
  const [hata, setHata] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const girisYolu = kapsam === 'admin' ? '/admin/giris' : '/giris'

  async function gonder(e) {
    e.preventDefault()
    setHata(null); setYukleniyor(true)
    try {
      const c = kapsam === 'admin' ? await api.adminSifremiUnuttum(email) : await api.sifremiUnuttum(email)
      setMesaj(c?.mesaj || 'Bağlantı gönderildi.')
    } catch (err) {
      setHata(err?.detail && typeof err.detail === 'string' ? err.detail : 'Geçerli bir e-posta adresi gir.')
    } finally {
      setYukleniyor(false)
    }
  }

  return (
    <div className="auth-wrap">
      {kapsam !== 'admin' && <TemaAnahtari />}
      <div className="auth-card">
        <span className="auth-emoji">🔑</span>
        <div className="auth-logo">Şifremi unuttum</div>
        <div className="auth-sub">E-posta adresini yaz, sana şifre sıfırlama bağlantısı gönderelim.</div>
        {mesaj ? (
          <div className="auth-error" style={{ background: 'var(--grl)', color: 'var(--gr)', lineHeight: 1.55 }}>{mesaj}</div>
        ) : (
          <>
            {hata && <div className="auth-error">{hata}</div>}
            <form onSubmit={gonder}>
              <div className="auth-field">
                <label className="auth-label">E-posta</label>
                <input className="auth-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus autoComplete="email" />
              </div>
              <button className="btn full" type="submit" disabled={yukleniyor}>
                {yukleniyor ? <span className="spin" /> : 'Bağlantı gönder'}
              </button>
            </form>
          </>
        )}
        <div className="auth-foot"><Link to={girisYolu} className="auth-link">← Giriş sayfasına dön</Link></div>
      </div>
    </div>
  )
}
