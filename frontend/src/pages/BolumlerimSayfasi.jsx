// [2026-10-10] Bölümler — "Bölüm Uyumum" + "Tüm Bölümleri Keşfet" + yeni "Karşılaştır" ve "Listem" tek sayfada sekmeler.
import { Suspense } from 'react'
import { tembel } from '../yardimci/tembelYukle'   // [2026-10-11] eski sürüm parçası yüklenemezse sayfayı yeniler
import { NavLink, Navigate, useParams } from 'react-router-dom'
import { useListem } from '../components/FavoriYildiz'
import { KarsilastirCubugu } from '../components/KarsilastirSepeti'

const SonucSayfasi = tembel(() => import('./SonucSayfasi'))
const KesfetSayfasi = tembel(() => import('./KesfetSayfasi'))
const KarsilastirmaSayfasi = tembel(() => import('./KarsilastirmaSayfasi'))   // [2026-10-11] genişletilmiş karşılaştırma
const ListemSekmesi = tembel(() => import('../components/ListemSekmesi'))

const SEKMELER = [
  { kod: '', ad: 'Sana uygun', ikon: '🌟', alt: 'Bölümler profiline yakınlığına göre sıralandı (100 = sana en yakın). Burada sana en yakın 10 bölüm ve nedenleri var.' },
  { kod: 'tum', ad: 'Tüm bölümler', ikon: '🔍', alt: 'Bütün bölümler burada. Ara, incele, beğendiğini ☆ ile listene ekle.' },
  { kod: 'karsilastir', ad: 'Karşılaştır', ikon: '⚖️', alt: 'Aklındaki 2-3 bölümü yan yana koy. Uyumunu ve nedenlerini, puan ve sıralamayı, iş hayatını, meslekleri ve günlük işleri karşılaştır.' },
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
        <Suspense fallback={<div className="bos-durum yukleniyor">Yükleniyor…</div>}>
          {s.kod === '' && <SonucSayfasi gomulu />}
          {s.kod === 'tum' && <KesfetSayfasi gomulu />}
          {s.kod === 'karsilastir' && <KarsilastirmaSayfasi gomulu />}
          {s.kod === 'listem' && <ListemSekmesi />}
        </Suspense>
      </div>
      {s.kod !== 'karsilastir' && <KarsilastirCubugu />}
    </div>
  )
}
