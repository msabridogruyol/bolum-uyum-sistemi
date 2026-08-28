import { useEffect, useState, useRef } from 'react'
import { api } from '../api/client'

const CINSIYET_SECENEKLERI = [
  { deger: '', etiket: 'Belirtilmedi' },
  { deger: 'kadin', etiket: 'Kadın' },
  { deger: 'erkek', etiket: 'Erkek' },
  { deger: 'diger', etiket: 'Diğer' },
  { deger: 'belirtmek_istemiyorum', etiket: 'Belirtmek istemiyorum' },
]

export default function ProfilAyarlariSayfasi() {
  const [profil, setProfil] = useState(null)
  const [taslak, setTaslak] = useState(null)
  const [hata, setHata] = useState(null)
  const [basari, setBasari] = useState(null)
  const [kaydediliyor, setKaydediliyor] = useState(false)

  const [mesleklAramaMetni, setMesleklAramaMetni] = useState('')
  const [meslekSonuclari, setMeslekSonuclari] = useState(null)

  const [eskiSifre, setEskiSifre] = useState('')
  const [yeniSifre, setYeniSifre] = useState('')
  const [yeniSifreTekrar, setYeniSifreTekrar] = useState('')
  const [sifreHata, setSifreHata] = useState(null)
  const [sifreBasari, setSifreBasari] = useState(false)
  const [sifreKaydediliyor, setSifreKaydediliyor] = useState(false)

  const fotoInputRef = useRef(null)
  const [fotoYukleniyor, setFotoYukleniyor] = useState(false)

  useEffect(() => {
    api.profilGetir().then((p) => { setProfil(p); setTaslak(p) }).catch((e) => setHata(e.detail || 'Profil yüklenemedi.'))
  }, [])

  function alanGuncelle(alan, deger) {
    setTaslak((t) => ({ ...t, [alan]: deger }))
  }

  async function kaydet(e) {
    e.preventDefault()
    setHata(null)
    setBasari(null)
    setKaydediliyor(true)
    try {
      const guncellenmis = await api.profilGuncelle({
        ad_soyad: taslak.ad_soyad,
        okul: taslak.okul || null,
        sinif: taslak.sinif || null,
        dogum_tarihi: taslak.dogum_tarihi || null,
        cinsiyet: taslak.cinsiyet || null,
        ilgi_alanlari: taslak.ilgi_alanlari || null,
        hedef_universite: taslak.hedef_universite || null,
        hedef_meslek_id: taslak.hedef_meslek_id ?? null,
      })
      setProfil(guncellenmis)
      setTaslak(guncellenmis)
      setBasari('Profil bilgilerin kaydedildi.')
    } catch (err) {
      setHata(err.detail || 'Kaydedilemedi.')
    } finally {
      setKaydediliyor(false)
    }
  }

  async function meslekAra(e) {
    e.preventDefault()
    if (mesleklAramaMetni.trim().length < 2) return
    try {
      setMeslekSonuclari(await api.meslekAra(mesleklAramaMetni.trim()))
    } catch (err) {
      setHata(err.detail || 'Meslek araması yapılamadı.')
    }
  }

  function meslekSec(meslek) {
    setTaslak((t) => ({ ...t, hedef_meslek_id: meslek.id, hedef_meslek_adi: meslek.ad }))
    setMeslekSonuclari(null)
    setMesleklAramaMetni('')
  }

  async function fotoSecildi(e) {
    const dosya = e.target.files?.[0]
    if (!dosya) return
    if (dosya.size > 2_000_000) {
      setHata('Fotoğraf çok büyük — en fazla 2MB olmalı.')
      return
    }
    setFotoYukleniyor(true)
    setHata(null)
    try {
      const base64 = await new Promise((resolve, reject) => {
        const okuyucu = new FileReader()
        okuyucu.onload = () => resolve(okuyucu.result)
        okuyucu.onerror = () => reject(new Error('Dosya okunamadı.'))
        okuyucu.readAsDataURL(dosya)
      })
      const guncellenmis = await api.profilFotografiGuncelle(base64)
      setProfil(guncellenmis)
      setTaslak(guncellenmis)
      setBasari('Profil fotoğrafın güncellendi.')
    } catch (err) {
      setHata(err.detail || 'Fotoğraf yüklenemedi.')
    } finally {
      setFotoYukleniyor(false)
      if (fotoInputRef.current) fotoInputRef.current.value = ''
    }
  }

  async function sifreyiDegistir(e) {
    e.preventDefault()
    setSifreHata(null)
    setSifreBasari(false)
    if (yeniSifre.length < 8) {
      setSifreHata('Yeni şifre en az 8 karakter olmalı.')
      return
    }
    if (yeniSifre !== yeniSifreTekrar) {
      setSifreHata('Yeni şifreler birbiriyle uyuşmuyor.')
      return
    }
    setSifreKaydediliyor(true)
    try {
      await api.sifreDegistir({ eski_sifre: eskiSifre, yeni_sifre: yeniSifre })
      setSifreBasari(true)
      setEskiSifre('')
      setYeniSifre('')
      setYeniSifreTekrar('')
    } catch (err) {
      setSifreHata(err.detail || 'Şifre değiştirilemedi.')
    } finally {
      setSifreKaydediliyor(false)
    }
  }

  if (hata && !profil) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!taslak) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Ayarlar</div>
        <div className="ps">Profilini, hedeflerini ve hesap güvenliğini buradan yönet.</div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}
      {basari && <div style={{ background: 'var(--grl)', color: 'var(--gr)', fontSize: 12.5, fontWeight: 600, padding: '10px 13px', borderRadius: 8, marginBottom: 14 }}>{basari}</div>}

      {/* --- Fotoğraf --- */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
        <div className="av" style={{ width: 64, height: 64, fontSize: 28, overflow: 'hidden' }}>
          {taslak.profil_foto_base64
            ? <img src={taslak.profil_foto_base64} alt="Profil" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : '🎓'}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 700 }}>{taslak.ad_soyad}</div>
          <div style={{ fontSize: 12.5, color: 'var(--tx2)' }}>{taslak.email}</div>
        </div>
        <label className="btn sec" style={{ cursor: fotoYukleniyor ? 'not-allowed' : 'pointer', opacity: fotoYukleniyor ? 0.6 : 1 }}>
          {fotoYukleniyor ? 'Yükleniyor...' : 'Fotoğraf Değiştir'}
          <input ref={fotoInputRef} type="file" accept="image/*" onChange={fotoSecildi} disabled={fotoYukleniyor} style={{ display: 'none' }} />
        </label>
      </div>

      {/* --- Kişisel Bilgiler --- */}
      <form onSubmit={kaydet}>
        <div className="card">
          <div className="ct">Kişisel Bilgiler</div>

          <div className="auth-field">
            <label className="auth-label">Ad Soyad</label>
            <input className="auth-input" value={taslak.ad_soyad} onChange={(e) => alanGuncelle('ad_soyad', e.target.value)} required minLength={2} />
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Okul</label>
              <input className="auth-input" value={taslak.okul || ''} onChange={(e) => alanGuncelle('okul', e.target.value)} placeholder="Örn. Atatürk Lisesi" />
            </div>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Sınıf</label>
              <input className="auth-input" value={taslak.sinif || ''} onChange={(e) => alanGuncelle('sinif', e.target.value)} placeholder="Örn. 12. Sınıf" />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Doğum Tarihi <span style={{ color: 'var(--tx3)', fontWeight: 500 }}>(opsiyonel)</span></label>
              <input className="auth-input" type="date" value={taslak.dogum_tarihi || ''} onChange={(e) => alanGuncelle('dogum_tarihi', e.target.value)} />
            </div>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Cinsiyet <span style={{ color: 'var(--tx3)', fontWeight: 500 }}>(opsiyonel)</span></label>
              <select className="auth-input" value={taslak.cinsiyet || ''} onChange={(e) => alanGuncelle('cinsiyet', e.target.value)}>
                {CINSIYET_SECENEKLERI.map((c) => <option key={c.deger} value={c.deger}>{c.etiket}</option>)}
              </select>
            </div>
          </div>

          <div className="auth-field">
            <label className="auth-label">Sevdiğin Şeyler / İlgi Alanların</label>
            <textarea
              className="auth-input"
              style={{ minHeight: 60, resize: 'vertical', fontFamily: 'var(--fn)' }}
              value={taslak.ilgi_alanlari || ''}
              onChange={(e) => alanGuncelle('ilgi_alanlari', e.target.value)}
              placeholder="Örn. resim yapmayı, satranç oynamayı ve bilim kurgu okumayı severim..."
            />
          </div>
        </div>

        {/* --- Hedefler --- */}
        <div className="card">
          <div className="ct">Hedeflerin</div>

          <div className="auth-field">
            <label className="auth-label">Hedef Üniversite <span style={{ color: 'var(--tx3)', fontWeight: 500 }}>(opsiyonel)</span></label>
            <input className="auth-input" value={taslak.hedef_universite || ''} onChange={(e) => alanGuncelle('hedef_universite', e.target.value)} placeholder="Örn. Boğaziçi Üniversitesi" />
          </div>

          <div className="auth-field">
            <label className="auth-label">Hedef Meslek</label>
            {taslak.hedef_meslek_adi && (
              <div className="bdg bdg-prog" style={{ marginBottom: 8, display: 'inline-flex' }}>
                {taslak.hedef_meslek_adi}
                <button type="button" onClick={() => alanGuncelle('hedef_meslek_id', null)} style={{ marginLeft: 6, background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}>✕</button>
              </div>
            )}
            <div style={{ display: 'flex', gap: 8 }}>
              <input className="auth-input" style={{ flex: 1 }} value={mesleklAramaMetni} onChange={(e) => setMesleklAramaMetni(e.target.value)} placeholder="Meslek ara... (örn. Yazılım Mühendisi)" />
              <button type="button" className="btn sec" onClick={meslekAra}>Ara</button>
            </div>
            {meslekSonuclari && (
              <div className="ll" style={{ marginTop: 8 }}>
                {meslekSonuclari.length === 0 && <div className="bos-durum" style={{ padding: 12 }}>Sonuç bulunamadı.</div>}
                {meslekSonuclari.map((m) => (
                  <div key={m.id} className="lc" onClick={() => meslekSec(m)}>
                    <div className="lb-wrap"><div className="lt">{m.ad}</div></div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="ps" style={{ margin: '10px 0 0' }}>
            Bölüm bazlı hedefin ve gelişim takibin için <b>Hedef Bölüm Koçluğu</b> sayfasını kullan — orası sistemin gerçek karşılaştırma motoruna bağlı.
          </div>
        </div>

        <button className="btn" type="submit" disabled={kaydediliyor}>
          {kaydediliyor ? <span className="spin" /> : 'Bilgileri Kaydet'}
        </button>
      </form>

      {/* --- Şifre Değiştir --- */}
      <div className="card" style={{ marginTop: 20 }}>
        <div className="ct">Şifreni Değiştir</div>
        {sifreHata && <div className="auth-error">{sifreHata}</div>}
        {sifreBasari && <div style={{ background: 'var(--grl)', color: 'var(--gr)', fontSize: 12.5, fontWeight: 600, padding: '10px 13px', borderRadius: 8, marginBottom: 14 }}>Şifren güncellendi.</div>}
        <form onSubmit={sifreyiDegistir}>
          <div className="auth-field">
            <label className="auth-label">Mevcut Şifre</label>
            <input className="auth-input" type="password" value={eskiSifre} onChange={(e) => setEskiSifre(e.target.value)} required />
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Yeni Şifre</label>
              <input className="auth-input" type="password" value={yeniSifre} onChange={(e) => setYeniSifre(e.target.value)} required minLength={8} />
            </div>
            <div className="auth-field" style={{ flex: 1 }}>
              <label className="auth-label">Yeni Şifre (Tekrar)</label>
              <input className="auth-input" type="password" value={yeniSifreTekrar} onChange={(e) => setYeniSifreTekrar(e.target.value)} required minLength={8} />
            </div>
          </div>
          <button className="btn sec" type="submit" disabled={sifreKaydediliyor}>
            {sifreKaydediliyor ? <span className="spin" /> : 'Şifreyi Güncelle'}
          </button>
        </form>
      </div>

      {/* --- Hukuki not --- */}
      <div className="ps" style={{ marginTop: 16, color: 'var(--tx3)', fontSize: 11.5 }}>
        Doğum tarihi ve cinsiyet bilgisi tamamen opsiyoneldir, doldurmak zorunda değilsin.
      </div>
    </div>
  )
}
