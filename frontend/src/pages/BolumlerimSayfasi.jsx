// [2026-10-10] Bölümler — "Bölüm Uyumum" + "Tüm Bölümleri Keşfet" + yeni "Karşılaştır" ve "Listem" tek sayfada sekmeler.
import { lazy, Suspense } from 'react'
import { NavLink, Navigate, useParams } from 'react-router-dom'
import { useListem } from '../components/FavoriYildiz'

const SonucSayfasi = lazy(() => import('./SonucSayfasi'))
const KesfetSayfasi = lazy(() => import('./KesfetSayfasi'))
const BolumKarsilastir = lazy(() => import('../components/BolumKarsilastir'))
const ListemSekmesi = lazy(() => import('../components/ListemSekmesi'))

const SEKMELER = [
  { kod: '', ad: 'Sana uygun', ikon: '🌟', alt: 'Değerlendirmene göre en uyumlu 10 bölüm ve nedenleri.' },
  { kod: 'tum', ad: 'Tüm bölümler', ikon: '🔍', alt: '301 bölümün tamamı — ara, incele, beğendiğini ☆ ile listene ekle.' },
  { kod: 'karsilastir', ad: 'Karşılaştır', ikon: '⚖️', alt: 'Aklındaki 2-3 bölümü yan yana koy: uyum, süre, puan türü, taban puan, meslekler.' },
  { kod: 'listem', ad: 'Listem', ikon: '⭐', alt: 'İlgini çeken bölümler. Rehber öğretmenin de görüşmelerde bu listeyi görür.' },
]

export default function BolumlerimSayfasi() {
  const { sekme } = useParams()
  const s = SEKMELER.find((x) => x.kod === (sekme || ''))
  const liste = useListem()
  if (!s) return <Navigate to="/bolumler" replace />

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Bölümler</div>
        <div className="ps">{s.alt}</div>
      </div>
      <nav className="sayfa-sekmeleri" aria-label="Bölüm sekmeleri">
        {SEKMELER.map((x) => (
          <NavLink key={x.kod || 'uygun'} to={x.kod ? `/bolumler/${x.kod}` : '/bolumler'} end
            className={({ isActive }) => (isActive ? 'aktif' : '')}>
            <span aria-hidden="true">{x.ikon}</span> {x.ad}
            {x.kod === 'listem' && liste?.length > 0 && <span className="ss-sayi">{liste.length}</span>}
          </NavLink>
        ))}
      </nav>
      <div className="gomulu-sayfa" key={s.kod || 'uygun'}>
        <Suspense fallback={<div className="bos-durum">Yükleniyor…</div>}>
          {s.kod === '' && <SonucSayfasi gomulu />}
          {s.kod === 'tum' && <KesfetSayfasi gomulu />}
          {s.kod === 'karsilastir' && <BolumKarsilastir />}
          {s.kod === 'listem' && <ListemSekmesi />}
        </Suspense>
      </div>
    </div>
  )
}
