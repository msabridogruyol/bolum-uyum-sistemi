import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'

export default function GirisSayfasi() {
  const [sekme, setSekme] = useState('giris') // 'giris' | 'kayit'
  const [adSoyad, setAdSoyad] = useState('')
  const [email, setEmail] = useState('')
  const [sifre, setSifre] = useState('')
  const [hata, setHata] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)

  const { girisYap, kayitOl } = useAuth()
  const navigate = useNavigate()

  async function gonder(e) {
    e.preventDefault()
    setHata(null)
    setYukleniyor(true)
    try {
      if (sekme === 'giris') {
        await girisYap(email, sifre)
      } else {
        await kayitOl(adSoyad, email, sifre)
      }
      navigate('/')
    } catch (err) {
      setHata(err instanceof api.ApiHatasi ? err.detail : 'Bir şeyler ters gitti, tekrar dene.')
    } finally {
      setYukleniyor(false)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="auth-logo">Bölüm Uyum Sistemi</div>
        <div className="auth-sub">Kariyer keşif platformu</div>

        <div style={{ display: 'flex', gap: 4, background: 'var(--sur2)', borderRadius: 12, padding: 3, marginBottom: 22 }}>
          <button
            type="button"
            onClick={() => setSekme('giris')}
            style={{
              flex: 1, padding: 8, fontSize: 12, fontWeight: 500, border: 'none', borderRadius: 9, cursor: 'pointer',
              background: sekme === 'giris' ? 'var(--sur)' : 'transparent',
              color: sekme === 'giris' ? 'var(--pu)' : 'var(--tx3)',
            }}
          >
            Giriş Yap
          </button>
          <button
            type="button"
            onClick={() => setSekme('kayit')}
            style={{
              flex: 1, padding: 8, fontSize: 12, fontWeight: 500, border: 'none', borderRadius: 9, cursor: 'pointer',
              background: sekme === 'kayit' ? 'var(--sur)' : 'transparent',
              color: sekme === 'kayit' ? 'var(--pu)' : 'var(--tx3)',
            }}
          >
            Kayıt Ol
          </button>
        </div>

        {hata && <div className="auth-error">{hata}</div>}

        <form onSubmit={gonder}>
          {sekme === 'kayit' && (
            <div className="auth-field">
              <label className="auth-label">Ad Soyad</label>
              <input className="auth-input" value={adSoyad} onChange={(e) => setAdSoyad(e.target.value)} required minLength={2} />
            </div>
          )}
          <div className="auth-field">
            <label className="auth-label">E-posta</label>
            <input className="auth-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ornek@eposta.com" required />
          </div>
          <div className="auth-field">
            <label className="auth-label">Şifre</label>
            <input className="auth-input" type="password" value={sifre} onChange={(e) => setSifre(e.target.value)} placeholder="••••••••" required minLength={8} />
          </div>
          <button className="btn full" type="submit" disabled={yukleniyor}>
            {yukleniyor ? <span className="spin" /> : sekme === 'giris' ? 'Giriş Yap' : 'Kayıt Ol'}
          </button>
        </form>

        <div className="auth-foot">
          {sekme === 'giris' ? (
            <>Hesabın yok mu? <button className="auth-link" onClick={() => setSekme('kayit')}>Kayıt ol</button></>
          ) : (
            <>Zaten hesabın var mı? <button className="auth-link" onClick={() => setSekme('giris')}>Giriş yap</button></>
          )}
        </div>
      </div>
    </div>
  )
}
