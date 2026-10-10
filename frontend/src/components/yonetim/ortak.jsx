// [2026-10-09] Okul bazlı yönetim ekranlarının ortak parçaları.
import { useState } from 'react'

export const ROL_ADI = { super_admin: 'Süper Admin', okul_yetkilisi: 'Okul Yetkilisi' }

export function tarih(z, saatli = true) {
  if (!z) return '—'
  const d = new Date(z)
  return saatli
    ? d.toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
    : d.toLocaleDateString('tr-TR')
}

export function onceSure(z) {
  if (!z) return 'hiç'
  const dk = Math.round((Date.now() - new Date(z).getTime()) / 60000)
  if (dk < 1) return 'az önce'
  if (dk < 60) return `${dk} dk önce`
  const sa = Math.round(dk / 60)
  if (sa < 24) return `${sa} sa önce`
  const gun = Math.round(sa / 24)
  return gun < 30 ? `${gun} gün önce` : tarih(z, false)
}

// Sunucunun base64 olarak verdiği Excel dosyasını indirir
export function base64Indir(dosyaAdi, b64, tur = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') {
  const ikili = atob(b64)
  const dizi = new Uint8Array(ikili.length)
  for (let i = 0; i < ikili.length; i++) dizi[i] = ikili.charCodeAt(i)
  const url = URL.createObjectURL(new Blob([dizi], { type: tur }))
  const a = document.createElement('a')
  a.href = url
  a.download = dosyaAdi
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function Pencere({ baslik, altBaslik, onKapat, genis, sinif, children, alt }) {
  return (
    <div className="yp-ortu" onMouseDown={(e) => { if (e.target === e.currentTarget) onKapat?.() }}>
      <div className={`yp-pencere${genis ? ' genis' : ''}${sinif ? ` ${sinif}` : ''}`} role="dialog" aria-modal="true">
        <div className="yp-baslik">
          <div style={{ minWidth: 0 }}>
            <div className="yp-bt">{baslik}</div>
            {altBaslik && <div className="yp-ab">{altBaslik}</div>}
          </div>
          {onKapat && <button className="yp-kapat" onClick={onKapat} aria-label="Kapat">×</button>}
        </div>
        <div className="yp-govde">{children}</div>
        {alt && <div className="yp-alt">{alt}</div>}
      </div>
    </div>
  )
}

const DURUM_SINIF = { tamamlandi: 'yp-d-yesil', devam: 'yp-d-mor', baslamadi: 'yp-d-gri', giris_yok: 'yp-d-amber' }
// [2026-10-10] Şifre hücresi: geçici şifre tabloda görünür (geçici olarak işaretli); kişi kendi şifresini belirleyince 'Belirlendi'
export function SifreHucresi({ gecici, degistirmeli }) {
  const [goster, setGoster] = useState(false)
  if (!degistirmeli) return <span className="yp-durum yp-d-yesil">✓ Kendi şifresi</span>
  if (!gecici) return <span className="yp-durum yp-d-amber" title="Eski kayıt: geçici şifre saklanmamış. Şifre sıfırlayarak yenisini alın.">Geçici · görünmüyor</span>
  return (
    <span className="sifre-hucre" onClick={(e) => e.stopPropagation()}>
      <code>{goster ? gecici : '••••-••••'}</code>
      <button type="button" className="yp-mini" onClick={() => setGoster(!goster)} title={goster ? 'Gizle' : 'Göster'}>{goster ? '🙈' : '👁'}</button>
      {goster && <button type="button" className="yp-mini" title="Kopyala" onClick={() => navigator.clipboard?.writeText(gecici).catch(() => {})}>📋</button>}
      <span className="yp-durum yp-d-amber">geçici</span>
    </span>
  )
}

export function DurumRozeti({ kod, etiket }) {
  return <span className={`yp-durum ${DURUM_SINIF[kod] || 'yp-d-gri'}`}>{etiket}</span>
}

// Geçici şifreyle ilk girişte yeni şifre belirleme (öğrenci ve yönetim için ortak)
export function IlkSifrePenceresi({ kaydet, onTamam, onCikis, rolMetni = 'hesabın' }) {
  const [s1, setS1] = useState('')
  const [s2, setS2] = useState('')
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  async function gonder(e) {
    e.preventDefault()
    if (s1.length < 8) { setHata('Şifre en az 8 karakter olmalı.'); return }
    if (s1 !== s2) { setHata('Şifreler aynı değil.'); return }
    setBekle(true); setHata(null)
    try { await kaydet(s1); onTamam?.() } catch (err) { setHata(err.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  return (
    <Pencere baslik="Kendi şifreni belirle" altBaslik={`Bu ${rolMetni} için verilen geçici şifreyle giriş yaptın. Devam etmek için kendine yeni bir şifre belirle.`}>
      <form onSubmit={gonder}>
        {hata && <div className="auth-error">{hata}</div>}
        <div className="auth-field">
          <label className="auth-label">Yeni şifre</label>
          <input className="auth-input" type="password" value={s1} onChange={(e) => setS1(e.target.value)} autoComplete="new-password" minLength={8} required autoFocus />
        </div>
        <div className="auth-field">
          <label className="auth-label">Yeni şifre (tekrar)</label>
          <input className="auth-input" type="password" value={s2} onChange={(e) => setS2(e.target.value)} autoComplete="new-password" minLength={8} required />
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginBottom: 14 }}>En az 8 karakter. Geçici şifreni tekrar kullanamazsın.</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn" type="submit" disabled={bekle}>{bekle ? <span className="spin" /> : 'Şifremi kaydet'}</button>
          {onCikis && <button className="btn sec" type="button" onClick={onCikis}>Çıkış yap</button>}
        </div>
      </form>
    </Pencere>
  )
}

// Geçici şifre(ler)i bir kez gösteren kutu
export function SifreListesi({ kayitlar, dosya, aciklama }) {
  const [kopyalandi, setKopyalandi] = useState(null)
  function kopyala(k) {
    navigator.clipboard?.writeText(`${k.email}  ${k.gecici_sifre}`).then(() => { setKopyalandi(k.email); setTimeout(() => setKopyalandi(null), 1500) })
  }
  return (
    <div>
      <div className="yp-uyari">
        <b>Şifreler yalnızca şimdi gösteriliyor.</b> {aciklama || 'Excel dosyasını indirip öğrencilere dağıtın; öğrenci ilk girişte kendi şifresini belirler.'}
      </div>
      {dosya?.icerik_base64 && (
        <button className="btn" style={{ marginBottom: 12 }} onClick={() => base64Indir(dosya.dosya_adi, dosya.icerik_base64)}>⬇ Giriş bilgilerini Excel olarak indir</button>
      )}
      <div className="yp-tablo-kap" style={{ maxHeight: 320 }}>
        <table className="yp-tablo">
          <thead><tr><th>Ad Soyad</th><th>Sınıf</th><th>E-posta</th><th>Geçici şifre</th><th /></tr></thead>
          <tbody>
            {kayitlar.map((k) => (
              <tr key={k.email}>
                <td>{k.ad_soyad}</td>
                <td>{[k.sinif?.replace('. Sınıf', ''), k.sube].filter(Boolean).join('-') || '—'}</td>
                <td className="yp-ince">{k.email}</td>
                <td><code className="yp-sifre">{k.gecici_sifre}</code></td>
                <td><button className="yp-mini" onClick={() => kopyala(k)}>{kopyalandi === k.email ? '✓' : 'Kopyala'}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
