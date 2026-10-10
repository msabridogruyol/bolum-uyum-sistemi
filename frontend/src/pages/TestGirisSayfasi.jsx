// [2026-10-10] Test hesabı bağlantısı: /test-giris?k=<anahtar>
// Süper adminin ürettiği süreli bağlantıyla, şifre ve 2 adımlı doğrulama olmadan test hesabını açar.
// Okul yetkilisi bağlantısı bu tarayıcıdaki yönetim oturumunun yerine geçer → önce onay istenir.
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

async function anahtarlaGiris(anahtar) {
  const cevap = await fetch('/api/auth/test-giris', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ anahtar }),
  })
  const veri = await cevap.json().catch(() => ({}))
  if (!cevap.ok) throw new Error(veri.detail || 'Bağlantı açılamadı.')
  return veri
}

function oturumuKaydet(v) {
  localStorage.setItem(`${v.kapsam}_erisim_tokeni`, v.erisim_tokeni)
  localStorage.setItem(`${v.kapsam}_yenileme_tokeni`, v.yenileme_tokeni)
  window.location.replace(v.kapsam === 'admin' ? '/admin' : '/')
}

export default function TestGirisSayfasi() {
  const [params] = useSearchParams()
  const [hata, setHata] = useState(null)
  const [onay, setOnay] = useState(null)   // yönetim oturumunun üzerine yazılacaksa sonuç burada bekler

  useEffect(() => {
    const k = params.get('k')
    if (!k) { setHata('Bağlantıda anahtar yok.'); return }
    anahtarlaGiris(k).then((v) => {
      const mevcutYonetim = localStorage.getItem('admin_erisim_tokeni')
      if (v.kapsam === 'admin' && mevcutYonetim) setOnay(v)
      else oturumuKaydet(v)
    }).catch((e) => setHata(e.message))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="auth-wrap">
      <div className="auth-card" style={{ maxWidth: 440, textAlign: 'center' }}>
        <div style={{ fontSize: 34 }}>🧪</div>
        <div className="pt" style={{ fontSize: 20, margin: '6px 0' }}>Test hesabı</div>
        {hata ? (
          <>
            <div className="auth-error" style={{ textAlign: 'left' }}>{hata}</div>
            <a className="btn sec" href="/" style={{ display: 'inline-block', marginTop: 10 }}>Giriş sayfasına dön</a>
          </>
        ) : onay ? (
          <>
            <div className="ps" style={{ margin: '4px 0 14px', lineHeight: 1.55 }}>
              <b>{onay.ad_soyad}</b> (okul yetkilisi test hesabı) olarak açılacak. Bu tarayıcıdaki mevcut <b>yönetim oturumunuz kapanır</b>.
              Kendi oturumunuzu korumak için bağlantıyı gizli pencerede açabilirsiniz.
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button className="btn" onClick={() => oturumuKaydet(onay)}>Devam et</button>
              <a className="btn sec" href="/admin">Vazgeç</a>
            </div>
          </>
        ) : (
          <div className="ps" style={{ margin: '8px 0' }}><span className="spin" /> Hesap açılıyor…</div>
        )}
      </div>
    </div>
  )
}
