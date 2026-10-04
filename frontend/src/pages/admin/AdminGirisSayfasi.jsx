import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { api } from '../../api/client'
import KodDogrulamaAdimi from '../../components/KodDogrulamaAdimi'

// [2026-10-04] 2 adımlı doğrulama + şifremi unuttum
export default function AdminGirisSayfasi() {
  const [email, setEmail] = useState('')
  const [sifre, setSifre] = useState('')
  const [hata, setHata] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [ikiAdim, setIkiAdim] = useState(null)

  const { girisYap, ikiAdimDogrula } = useAdminAuth()
  const navigate = useNavigate()

  function yonlendir(sonuc) {
    if (sonuc?.iki_adim_gerekli) {
      setIkiAdim({ gecici_token: sonuc.gecici_token, maskeli_eposta: sonuc.maskeli_eposta })
      return
    }
    navigate('/admin')
  }

  async function gonder(e) {
    e.preventDefault()
    setHata(null)
    setYukleniyor(true)
    try {
      yonlendir(await girisYap(email, sifre))
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
        <div className="auth-sub">{ikiAdim ? 'Yönetici Paneli · giriş doğrulaması' : 'Yönetici Paneli'}</div>

        {ikiAdim ? (
          <KodDogrulamaAdimi
            maskeliEposta={ikiAdim.maskeli_eposta}
            onDogrula={async (kod, hatirla) => yonlendir(await ikiAdimDogrula(ikiAdim.gecici_token, kod, hatirla))}
            onTekrarGonder={() => api.adminKodTekrarGonder(ikiAdim.gecici_token)}
            onGeri={() => { setIkiAdim(null); setSifre('') }}
          />
        ) : (
          <>
            {hata && <div className="auth-error">{hata}</div>}
            <form onSubmit={gonder}>
              <div className="auth-field">
                <label className="auth-label">E-posta</label>
                <input className="auth-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
              </div>
              <div className="auth-field">
                <label className="auth-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Şifre</span>
                  <Link to="/admin/sifremi-unuttum" className="auth-link" style={{ fontSize: 11.5 }}>Şifremi unuttum</Link>
                </label>
                <input className="auth-input" type="password" value={sifre} onChange={(e) => setSifre(e.target.value)} required autoComplete="current-password" />
              </div>
              <button className="btn full" type="submit" disabled={yukleniyor}>
                {yukleniyor ? <span className="spin" /> : 'Giriş Yap'}
              </button>
            </form>
            <div className="auth-foot">
              Rehber öğretmenler <Link to="/giris" className="auth-link">öğrenci giriş sayfasından</Link> giriş yapar.
            </div>
          </>
        )}
      </div>
    </div>
  )
}
