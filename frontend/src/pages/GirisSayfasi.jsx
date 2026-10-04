import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../api/client'
import TemaAnahtari from '../components/TemaAnahtari'
import KodDogrulamaAdimi from '../components/KodDogrulamaAdimi'
import { KvkkOnayKutulari, AydinlatmaMetniPenceresi, useKvkkMetinleri, zorunlularTamamMi } from '../components/KvkkBilesenleri'

// [2026-10-04] Kayıtta KVKK onayları, girişte 2 adımlı doğrulama, "Şifremi unuttum" bağlantısı.
// Rehber öğretmenler de bu sayfadan giriş yapar.
export default function GirisSayfasi() {
  const [sekme, setSekme] = useState('giris') // 'giris' | 'kayit'
  const [adSoyad, setAdSoyad] = useState('')
  const [email, setEmail] = useState('')
  const [sifre, setSifre] = useState('')
  const [onaylar, setOnaylar] = useState({})
  const [metinAcik, setMetinAcik] = useState(false)
  const [hata, setHata] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [ikiAdim, setIkiAdim] = useState(null) // { gecici_token, maskeli_eposta }

  const kvkk = useKvkkMetinleri()
  const { girisYap, kayitOl, ikiAdimDogrula } = useAuth()
  const navigate = useNavigate()

  function yonlendir(sonuc) {
    if (sonuc?.iki_adim_gerekli) {
      setIkiAdim({ gecici_token: sonuc.gecici_token, maskeli_eposta: sonuc.maskeli_eposta })
      return
    }
    navigate(sonuc?.kullanici_tipi === 'rehber' ? '/rehber' : '/')
  }

  async function gonder(e) {
    e.preventDefault()
    setHata(null)
    if (sekme === 'kayit' && kvkk && !zorunlularTamamMi(kvkk.maddeler, onaylar)) {
      setHata('Kayıt olmak için zorunlu (*) onay kutularını işaretlemelisin.')
      return
    }
    setYukleniyor(true)
    try {
      const sonuc = sekme === 'giris'
        ? await girisYap(email, sifre)
        : await kayitOl(adSoyad, email, sifre, kvkk ? onaylar : undefined)
      yonlendir(sonuc)
    } catch (err) {
      setHata(err instanceof api.ApiHatasi ? err.detail : 'Bir şeyler ters gitti, tekrar dene.')
      if (sekme === 'kayit' && err?.status === 503) setSekme('giris') // hesap açıldı ama kod gönderilemedi
    } finally {
      setYukleniyor(false)
    }
  }

  const sekmeStili = (aktif) => ({
    flex: 1, padding: 9, fontSize: 12.5, fontWeight: 700, border: 'none', borderRadius: 11, cursor: 'pointer',
    fontFamily: 'var(--fd)', background: aktif ? 'var(--pu)' : 'transparent', color: aktif ? '#fff' : 'var(--tx3)',
  })

  return (
    <div className="auth-wrap">
      <TemaAnahtari />
      <div className="auth-card" style={sekme === 'kayit' && !ikiAdim ? { maxWidth: 460 } : undefined}>
        <span className="auth-emoji">🌱</span>
        <div className="auth-logo">Filizyol</div>
        <div className="auth-sub">{ikiAdim ? 'Giriş doğrulaması' : 'Kendi yolunu filizlendir'}</div>

        {ikiAdim ? (
          <KodDogrulamaAdimi
            maskeliEposta={ikiAdim.maskeli_eposta}
            onDogrula={async (kod, hatirla) => yonlendir(await ikiAdimDogrula(ikiAdim.gecici_token, kod, hatirla))}
            onTekrarGonder={() => api.kodTekrarGonder(ikiAdim.gecici_token)}
            onGeri={() => { setIkiAdim(null); setSekme('giris'); setSifre('') }}
          />
        ) : (
          <>
            <div style={{ display: 'flex', gap: 4, background: 'var(--sur2)', borderRadius: 14, padding: 4, marginBottom: 22 }}>
              <button type="button" onClick={() => { setSekme('giris'); setHata(null) }} style={sekmeStili(sekme === 'giris')}>Giriş Yap</button>
              <button type="button" onClick={() => { setSekme('kayit'); setHata(null) }} style={sekmeStili(sekme === 'kayit')}>Kayıt Ol</button>
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
                <input className="auth-input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="ornek@eposta.com" required autoComplete="email" />
              </div>
              <div className="auth-field">
                <label className="auth-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Şifre</span>
                  {sekme === 'giris' && <Link to="/sifremi-unuttum" className="auth-link" style={{ fontSize: 11.5 }}>Şifremi unuttum</Link>}
                </label>
                <input className="auth-input" type="password" value={sifre} onChange={(e) => setSifre(e.target.value)} placeholder="••••••••" required minLength={8}
                  autoComplete={sekme === 'giris' ? 'current-password' : 'new-password'} />
              </div>

              {sekme === 'kayit' && kvkk && (
                <div style={{ background: 'var(--sur2)', borderRadius: 12, padding: '12px 14px', marginBottom: 16 }}>
                  <KvkkOnayKutulari maddeler={kvkk.maddeler} onaylar={onaylar} setOnaylar={setOnaylar} metniAc={() => setMetinAcik(true)} />
                </div>
              )}

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
          </>
        )}
      </div>
      {metinAcik && kvkk && <AydinlatmaMetniPenceresi metin={kvkk.aydinlatma_metni} onKapat={() => setMetinAcik(false)} />}
    </div>
  )
}
