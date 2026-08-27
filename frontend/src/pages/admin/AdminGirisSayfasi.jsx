import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { api } from '../../api/client'

export default function AdminGirisSayfasi() {
  const [email, setEmail] = useState('')
  const [sifre, setSifre] = useState('')
  const [hata, setHata] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)

  const { girisYap } = useAdminAuth()
  const navigate = useNavigate()

  async function gonder(e) {
    e.preventDefault()
    setHata(null)
    setYukleniyor(true)
    try {
      await girisYap(email, sifre)
      navigate('/admin')
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
        <div className="auth-sub">Yönetici Paneli</div>

        {hata && <div className="auth-error">{hata}</div>}

        <form onSubmit={gonder}>
          <div className="auth-field">
            <label className="auth-label">E-posta</label>
            <input className="auth-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="auth-field">
            <label className="auth-label">Şifre</label>
            <input className="auth-input" type="password" value={sifre} onChange={(e) => setSifre(e.target.value)} required />
          </div>
          <button className="btn full" type="submit" disabled={yukleniyor}>
            {yukleniyor ? <span className="spin" /> : 'Giriş Yap'}
          </button>
        </form>

        <div className="auth-foot">
          Yönetici hesabın yoksa mevcut bir süper admin seni <code>/admin/yoneticiler</code> üzerinden eklemeli.
        </div>
      </div>
    </div>
  )
}
