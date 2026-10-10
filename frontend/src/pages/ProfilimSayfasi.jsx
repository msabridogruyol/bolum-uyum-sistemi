// [2026-10-10] Profilim — eskiden menüde 6 ayrı satır olan "Genel Sonuçlar · K1 · K2 · K3 · K4 · K5" tek sayfada sekmeler.
// Sekme içerikleri mevcut sayfaların kendisi (gömülü modda: kendi başlıkları/geri butonları gizli).
import { lazy, Suspense } from 'react'
import { NavLink, Navigate, useParams } from 'react-router-dom'
import PuanRehberi from '../components/PuanRehberi'

const GenelSonuclarSayfasi = lazy(() => import('./GenelSonuclarSayfasi'))
const KatmanDetaySayfasi = lazy(() => import('./KatmanDetaySayfasi'))
const K5SonucSayfasi = lazy(() => import('./K5SonucSayfasi'))

const SEKMELER = [
  { kod: '', ad: 'Genel bakış', ikon: '🧭' },
  { kod: 'K1', ad: 'Değerler', ikon: '🌱' },
  { kod: 'K2', ad: 'Kişilik', ikon: '🌿' },
  { kod: 'K3', ad: 'İş ortamı', ikon: '🍃' },
  { kod: 'K4', ad: 'Alan eğilimi', ikon: '🌸' },
  { kod: 'K5', ad: 'Derinleşme', ikon: '🌻' },
]

export default function ProfilimSayfasi() {
  const { kod } = useParams()
  const k = (kod || '').toUpperCase()
  if (kod && !SEKMELER.some((s) => s.kod === k)) return <Navigate to="/profilim" replace />

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Profilim</div>
        <div className="ps">Değerlendirmene göre değerlerin, kişiliğin, sevdiğin iş ortamı ve ilgi alanların — güçlü yönlerin ve gelişebileceğin alanlarla.</div>
      </div>
      <nav className="sayfa-sekmeleri" aria-label="Profil bölümleri">
        {SEKMELER.map((s) => (
          <NavLink key={s.kod || 'genel'} to={s.kod ? `/profilim/${s.kod}` : '/profilim'} end
            className={({ isActive }) => (isActive ? 'aktif' : '')}>
            <span aria-hidden="true">{s.ikon}</span> {s.ad}{s.kod && <small>{s.kod}</small>}
          </NavLink>
        ))}
      </nav>
      <PuanRehberi bolumlu={false} baslik="Güçlü, çok güçlü, gelişime açık ne demek? Profilini nasıl okumalısın?" />
      <div className="gomulu-sayfa" key={k || 'genel'}>
        <Suspense fallback={<div className="bos-durum">Yükleniyor…</div>}>
          {!k && <GenelSonuclarSayfasi gomulu />}
          {['K1', 'K2', 'K3', 'K4'].includes(k) && <KatmanDetaySayfasi gomulu />}
          {k === 'K5' && <K5SonucSayfasi gomulu />}
        </Suspense>
      </div>
    </div>
  )
}
