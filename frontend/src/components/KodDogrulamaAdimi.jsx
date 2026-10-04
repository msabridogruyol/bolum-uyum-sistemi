import { useEffect, useState } from 'react'

// [2026-10-04] 2 adımlı doğrulama — e-postaya gelen 6 haneli kodun girildiği adım (öğrenci ve yönetici ortak).
export default function KodDogrulamaAdimi({ maskeliEposta, onDogrula, onTekrarGonder, onGeri }) {
  const [kod, setKod] = useState('')
  const [hatirla, setHatirla] = useState(true)
  const [hata, setHata] = useState(null)
  const [bilgi, setBilgi] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [bekleme, setBekleme] = useState(60)

  useEffect(() => {
    if (bekleme <= 0) return
    const t = setTimeout(() => setBekleme((b) => b - 1), 1000)
    return () => clearTimeout(t)
  }, [bekleme])

  async function gonder(e) {
    e.preventDefault()
    setHata(null); setBilgi(null); setYukleniyor(true)
    try {
      await onDogrula(kod.replace(/\D/g, ''), hatirla)
    } catch (err) {
      setHata(err?.detail || 'Kod doğrulanamadı.')
      if (err?.status === 401) setTimeout(onGeri, 1500)
    } finally {
      setYukleniyor(false)
    }
  }

  async function tekrar() {
    setHata(null); setBilgi(null)
    try {
      await onTekrarGonder()
      setBilgi('Yeni kod gönderildi.')
      setBekleme(60)
      setKod('')
    } catch (err) {
      setHata(err?.detail || 'Kod gönderilemedi.')
    }
  }

  return (
    <>
      <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.6, marginBottom: 16, textAlign: 'center' }}>
        <b>{maskeliEposta}</b> adresine 6 haneli bir doğrulama kodu gönderdik. Kod 10 dakika geçerli.
        <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginTop: 4 }}>Göremiyorsan spam / gereksiz klasörüne bak.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {bilgi && <div className="auth-error" style={{ background: 'var(--grl)', color: 'var(--gr)' }}>{bilgi}</div>}
      <form onSubmit={gonder}>
        <div className="auth-field">
          <label className="auth-label">Doğrulama kodu</label>
          <input className="auth-input" value={kod} autoFocus inputMode="numeric" autoComplete="one-time-code" maxLength={7}
            onChange={(e) => setKod(e.target.value.replace(/[^\d ]/g, ''))} placeholder="123456"
            style={{ fontSize: 22, letterSpacing: 8, textAlign: 'center', fontWeight: 700 }} required />
        </div>
        <label style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 12, color: 'var(--tx2)', marginBottom: 14, cursor: 'pointer' }}>
          <input type="checkbox" checked={hatirla} onChange={(e) => setHatirla(e.target.checked)} style={{ accentColor: 'var(--pu)' }} />
          Bu cihazı 30 gün hatırla (ortak kullanılan bilgisayarda işaretleme)
        </label>
        <button className="btn full" type="submit" disabled={yukleniyor || kod.replace(/\D/g, '').length !== 6}>
          {yukleniyor ? <span className="spin" /> : 'Doğrula ve giriş yap'}
        </button>
      </form>
      <div className="auth-foot" style={{ display: 'flex', justifyContent: 'space-between' }}>
        <button type="button" className="auth-link" onClick={onGeri}>← Geri</button>
        {bekleme > 0
          ? <span>Yeni kod: {bekleme} sn</span>
          : <button type="button" className="auth-link" onClick={tekrar}>Kodu tekrar gönder</button>}
      </div>
    </>
  )
}
