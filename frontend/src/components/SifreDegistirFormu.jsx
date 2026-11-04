// [2026-11-04] Şifre değişikliği: 1) şu anki şifre + yeni şifre → 2) e-postaya giden 6 haneli onay kodu → şifre değişir.
// Öğrenci Ayarlar sayfası ve yönetim paneli aynı bileşeni kullanır. Sunucu kod adımı gerektirmezse (test hesabı ya da
// e-posta altyapısı kapalı) şifre ilk adımda değişir.
import { useState } from 'react'

export default function SifreDegistirFormu({ degistir, onayla, onTamam, hitap = 'sen' }) {
  const sen = hitap === 'sen'
  const [eski, setEski] = useState('')
  const [yeni, setYeni] = useState('')
  const [tekrar, setTekrar] = useState('')
  const [kod, setKod] = useState('')
  const [kodAdimi, setKodAdimi] = useState(null)   // { maskeli_eposta }
  const [hata, setHata] = useState(null)
  const [basari, setBasari] = useState(false)
  const [bekle, setBekle] = useState(false)

  function bitti() {
    setBasari(true); setKodAdimi(null); setEski(''); setYeni(''); setTekrar(''); setKod('')
    onTamam?.()
  }

  async function baslat(e) {
    e.preventDefault()
    setHata(null); setBasari(false)
    if (yeni.length < 8) { setHata('Yeni şifre en az 8 karakter olmalı.'); return }
    if (yeni !== tekrar) { setHata(sen ? 'Yazdığın iki yeni şifre aynı değil.' : 'Yeni şifreler aynı değil.'); return }
    setBekle(true)
    try {
      const r = await degistir({ eski_sifre: eski, yeni_sifre: yeni })
      if (r?.kod_gonderildi) setKodAdimi({ maskeli_eposta: r.maskeli_eposta })
      else bitti()
    } catch (err) {
      setHata(err.detail || 'Şifre değiştirilemedi.')
    } finally {
      setBekle(false)
    }
  }

  async function kodOnayla(e) {
    e.preventDefault()
    setHata(null)
    setBekle(true)
    try {
      await onayla(kod)
      bitti()
    } catch (err) {
      setHata(err.detail || 'Kod doğrulanamadı.')
    } finally {
      setBekle(false)
    }
  }

  return (
    <>
      {hata && <div className="auth-error">{hata}</div>}
      {basari && <div style={{ background: 'var(--grl)', color: 'var(--gr)', fontSize: 12.5, fontWeight: 600, padding: '10px 13px', borderRadius: 8, marginBottom: 14 }}>
        {sen ? 'Şifren güncellendi. Diğer cihazlardaki oturumların kapatıldı.' : 'Şifreniz güncellendi. Diğer cihazlardaki oturumlar kapatıldı.'}
      </div>}
      {kodAdimi ? (
        <form onSubmit={kodOnayla}>
          <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.55, marginBottom: 10 }}>
            <b>{kodAdimi.maskeli_eposta}</b> {sen ? 'adresine 6 haneli bir onay kodu gönderdik. Kodu girince şifren değişir. Kod 10 dakika geçerlidir.'
              : 'adresine 6 haneli bir onay kodu gönderildi. Kodu girdiğinizde şifre değişir. Kod 10 dakika geçerlidir.'}
          </div>
          <div className="auth-field">
            <label className="auth-label">Onay kodu</label>
            <input className="auth-input" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={kod}
              onChange={(e) => setKod(e.target.value.replace(/\D/g, ''))} required autoFocus />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn" type="submit" disabled={bekle || kod.length !== 6}>{bekle ? <span className="spin" /> : 'Onayla'}</button>
            <button className="btn sec" type="button" onClick={() => { setKodAdimi(null); setKod(''); setHata(null) }}>Vazgeç</button>
          </div>
        </form>
      ) : (
        <form onSubmit={baslat}>
          <div className="auth-field">
            <label className="auth-label">{sen ? 'Şu Anki Şifren' : 'Şu Anki Şifre'}</label>
            <input className="auth-input" type="password" autoComplete="current-password" maxLength={200} value={eski} onChange={(e) => setEski(e.target.value)} required />
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <div className="auth-field" style={{ flex: '1 1 180px' }}>
              <label className="auth-label">Yeni Şifre</label>
              <input className="auth-input" type="password" autoComplete="new-password" maxLength={72} value={yeni} onChange={(e) => setYeni(e.target.value)} required minLength={8} />
            </div>
            <div className="auth-field" style={{ flex: '1 1 180px' }}>
              <label className="auth-label">Yeni Şifre (Tekrar)</label>
              <input className="auth-input" type="password" autoComplete="new-password" maxLength={72} value={tekrar} onChange={(e) => setTekrar(e.target.value)} required minLength={8} />
            </div>
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginBottom: 12 }}>
            {sen ? 'Onay için e-posta adresine bir kod göndereceğiz.' : 'Onay için e-posta adresinize bir kod gönderilecek.'}
          </div>
          <button className="btn sec" type="submit" disabled={bekle}>{bekle ? <span className="spin" /> : (sen ? 'Kodu Gönder' : 'Kodu gönder')}</button>
        </form>
      )}
    </>
  )
}
