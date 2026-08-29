import { useEffect, useState, useCallback } from 'react'
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

export default function YoneticilerSayfasi() {
  const [yoneticiler, setYoneticiler] = useState(null)
  const [hata, setHata] = useState(null)
  const [form, setForm] = useState({ ad_soyad: '', email: '', sifre: '', rol: 'icerik_editoru' })
  const { rol: kendiRol, kendiId } = useAdminAuth()

  const yukle = useCallback(() => {
    api.yoneticileriListele().then(setYoneticiler).catch((e) => setHata(e.detail || 'Yöneticiler yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  if (kendiRol !== 'super_admin') {
    return (
      <div className="pg pg-genis">
        <div className="ph"><div className="pt">Yöneticiler</div></div>
        <div className="bos-durum">Bu sayfa yalnızca süper adminlere açık.</div>
      </div>
    )
  }

  async function ekle(e) {
    e.preventDefault()
    try {
      await api.yoneticiEkle(form)
      setForm({ ad_soyad: '', email: '', sifre: '', rol: 'icerik_editoru' })
      yukle()
    } catch (err) {
      setHata(err.detail || 'Eklenemedi.')
    }
  }

  async function rolDegistir(id, yeniRol) {
    try {
      await api.yoneticiRolGuncelle(id, yeniRol)
      yukle()
    } catch (err) {
      setHata(err.detail || 'Rol değiştirilemedi.')
    }
  }

  if (!yoneticiler) return <div className="pg pg-genis"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Yöneticiler</div>
        <div className="ps">Yeni yönetici ekle veya mevcutların rolünü değiştir. Kendi rolünü değiştiremezsin.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <button
        className="btn sec"
        style={{ marginBottom: 14 }}
        onClick={() => csvDisaAktar(
          'yoneticiler_disa_aktarim.csv',
          ['ad_soyad', 'email', 'rol', 'olusturulma_zamani'],
          yoneticiler.map((y) => [y.ad_soyad, y.email, y.rol, y.olusturulma_zamani]),
        )}
        disabled={yoneticiler.length === 0}
      >
        ⬇ CSV Dışa Aktar
      </button>
      <div className="ps" style={{ marginTop: -8, marginBottom: 14, fontSize: 11 }}>
        Şifreler asla dışa aktarılmaz — güvenlik nedeniyle toplu yönetici ekleme (içe aktarma) kasıtlı olarak sunulmuyor.
      </div>

      <form onSubmit={ekle} className="card" style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div><label className="auth-label">Ad Soyad</label><input className="auth-input" value={form.ad_soyad} onChange={(e) => setForm((f) => ({ ...f, ad_soyad: e.target.value }))} required /></div>
        <div><label className="auth-label">E-posta</label><input className="auth-input" type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} required /></div>
        <div><label className="auth-label">Şifre</label><input className="auth-input" type="password" value={form.sifre} onChange={(e) => setForm((f) => ({ ...f, sifre: e.target.value }))} required minLength={8} /></div>
        <div>
          <label className="auth-label">Rol</label>
          <select className="auth-input" value={form.rol} onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value }))}>
            <option value="icerik_editoru">İçerik Editörü</option>
            <option value="super_admin">Süper Admin</option>
          </select>
        </div>
        <button className="btn" type="submit">Ekle</button>
      </form>

      <div className="ll">
        {yoneticiler.map((y) => (
          <div key={y.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{y.ad_soyad}</div>
              <div className="ld">{y.email}</div>
            </div>
            <select
              className="auth-input"
              style={{ width: 160 }}
              value={y.rol}
              disabled={y.id === kendiId}
              title={y.id === kendiId ? 'Kendi rolünü değiştiremezsin' : ''}
              onChange={(e) => rolDegistir(y.id, e.target.value)}
            >
              <option value="icerik_editoru">İçerik Editörü</option>
              <option value="super_admin">Süper Admin</option>
            </select>
          </div>
        ))}
      </div>
    </div>
  )
}
