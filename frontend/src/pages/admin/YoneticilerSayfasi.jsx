import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { api } from '../../api/client'

function csvDisaAktar(dosyaAdi, basliklar, satirlar) {
  const kacisla = (deger) => `"${String(deger ?? '').replace(/"/g, '""')}"`
  const icerik = [basliklar.join(','), ...satirlar.map((s) => s.map(kacisla).join(','))].join('\r\n')
  const blob = new Blob(['\uFEFF' + icerik], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = dosyaAdi
  a.click()
  URL.revokeObjectURL(url)
}

// [2026-10-09] Sistemde 3 rol var: Süper Admin (bu sayfa), Okul Yetkilisi (okulun panelinden), Öğrenci (okulun panelinden).
export default function YoneticilerSayfasi() {
  const [yoneticiler, setYoneticiler] = useState(null)
  const [hata, setHata] = useState(null)
  const [form, setForm] = useState({ ad_soyad: '', email: '', sifre: '' })
  const [silinecek, setSilinecek] = useState(null)
  const { rol: kendiRol, kendiId } = useAdminAuth()

  const yukle = useCallback(() => {
    api.yoneticileriListele().then(setYoneticiler).catch((e) => setHata(e.detail || 'Yöneticiler yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  if (kendiRol !== 'super_admin') {
    return (
      <div className="pg pg-genis">
        <div className="ph"><div className="pt">Süper Adminler</div></div>
        <div className="bos-durum">Bu sayfa yalnızca süper adminlere açık.</div>
      </div>
    )
  }

  async function ekle(e) {
    e.preventDefault()
    try {
      await api.yoneticiEkle({ ...form, rol: 'super_admin' })
      setForm({ ad_soyad: '', email: '', sifre: '' })
      setHata(null)
      yukle()
    } catch (err) {
      setHata(err.detail || 'Eklenemedi.')
    }
  }

  async function sil(id) {
    try { await api.yoneticiSil(id); setSilinecek(null); yukle() } catch (err) { setHata(err.detail || 'Silinemedi.') }
  }

  if (!yoneticiler) return <div className="pg pg-genis"><div className="bos-durum">Yükleniyor…</div></div>
  const superler = yoneticiler.filter((y) => y.rol === 'super_admin')
  const yetkililer = yoneticiler.filter((y) => y.rol === 'okul_yetkilisi')

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Süper Adminler</div>
        <div className="ps">
          Süper admin tüm sisteme erişir (içerik, okullar, tüm öğrenciler). Okul yetkilileri ve öğrenci hesapları ilgili okulun
          panelinden açılır (Okullar → Paneli aç).
        </div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <form onSubmit={ekle} className="card" style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div><label className="auth-label">Ad Soyad</label><input className="auth-input" value={form.ad_soyad} onChange={(e) => setForm((f) => ({ ...f, ad_soyad: e.target.value }))} required /></div>
        <div><label className="auth-label">E-posta</label><input className="auth-input" type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} required /></div>
        <div><label className="auth-label">Şifre</label><input className="auth-input" type="password" value={form.sifre} onChange={(e) => setForm((f) => ({ ...f, sifre: e.target.value }))} required minLength={8} autoComplete="new-password" /></div>
        <button className="btn" type="submit">+ Süper admin ekle</button>
      </form>

      <div className="ll">
        {superler.map((y) => (
          <div key={y.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap" style={{ flex: 1 }}>
              <div className="lt">{y.ad_soyad}{y.id === kendiId && <span className="bdg bdg-prog" style={{ marginLeft: 8 }}>Sen</span>}</div>
              <div className="ld">{y.email} · son giriş {y.son_giris_zamani ? new Date(y.son_giris_zamani).toLocaleString('tr-TR') : '—'}</div>
            </div>
            {y.id !== kendiId && (silinecek === y.id
              ? <><button className="btn yp-tehlike" onClick={() => sil(y.id)}>Evet, sil</button><button className="btn sec" onClick={() => setSilinecek(null)}>Vazgeç</button></>
              : <button className="btn sec" onClick={() => setSilinecek(y.id)}>Sil</button>)}
          </div>
        ))}
      </div>

      <div className="ct" style={{ marginTop: 22 }}>Okul Yetkilileri ({yetkililer.length})</div>
      <div className="ps" style={{ marginTop: -6, marginBottom: 10, fontSize: 12 }}>Eklemek, şifre sıfırlamak ve silmek için ilgili okulun panelini açın.</div>
      <button
        className="btn sec" style={{ marginBottom: 10 }} disabled={yoneticiler.length === 0}
        onClick={() => csvDisaAktar('yonetim_hesaplari.csv', ['ad_soyad', 'email', 'rol', 'okul', 'son_giris'],
          yoneticiler.map((y) => [y.ad_soyad, y.email, y.rol === 'super_admin' ? 'Süper Admin' : 'Okul Yetkilisi', y.okul_ad || '', y.son_giris_zamani || '']))}
      >⬇ Tüm yönetim hesaplarını CSV indir</button>
      <div className="ll">
        {yetkililer.map((y) => (
          <Link key={y.id} to={`/admin/okul/${y.okul_id}`} className="lc" style={{ textDecoration: 'none', color: 'inherit' }}>
            <div className="lb-wrap" style={{ flex: 1 }}>
              <div className="lt">{y.ad_soyad}{y.unvan && <span className="yp-ince" style={{ fontWeight: 500 }}> · {y.unvan}</span>}</div>
              <div className="ld">{y.email} · {y.okul_ad}</div>
            </div>
            <span className="yp-ince">Okul paneli →</span>
          </Link>
        ))}
        {yetkililer.length === 0 && <div className="bos-durum">Henüz okul yetkilisi yok.</div>}
      </div>
    </div>
  )
}
