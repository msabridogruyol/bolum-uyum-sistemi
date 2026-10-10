// [2026-10-10] Bölümler → Listem: ★ ile işaretlenen bölümler. Buradan 2-3'ü seçilip karşılaştırılabilir.
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FavoriYildiz, { useListem } from './FavoriYildiz'
import BolumAdi from './BolumAdi'

export default function ListemSekmesi() {
  const liste = useListem()
  const [secili, setSecili] = useState([])
  const navigate = useNavigate()

  if (liste === null) return <div className="bos-durum">Yükleniyor…</div>
  if (liste.length === 0) {
    return (
      <div className="veri-yok-grafik" style={{ padding: '36px 18px' }}>
        <div className="vg-ikon">⭐</div>
        <div className="vg-metin" style={{ maxWidth: 440 }}>
          Listen henüz boş. İlgini çeken bir bölümü görünce yanındaki <b>☆</b> işaretine dokun; burada toplanır, sonra yan yana karşılaştırırsın.
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap', justifyContent: 'center' }}>
          <button className="btn" onClick={() => navigate('/bolumler')}>Sana uygun bölümler</button>
          <button className="btn sec" onClick={() => navigate('/bolumler/tum')}>Tüm bölümlerde ara</button>
        </div>
      </div>
    )
  }

  const degistir = (id) => setSecili((s) => (s.includes(id) ? s.filter((x) => x !== id) : s.length >= 3 ? s : [...s, id]))

  return (
    <>
      <div className="listem-ust">
        <span className="yp-ince">{liste.length} bölüm · karşılaştırmak için 2-3 tanesini işaretle</span>
        {(() => {
          const idler = secili.length ? secili : liste.length <= 3 ? liste.map((b) => b.bolum_id) : []
          return (
            <button className="btn" disabled={idler.length < 2} onClick={() => navigate(`/bolumler/karsilastir?ids=${idler.join(',')}`)}>
              ⚖️ {secili.length ? `Seçilenleri karşılaştır (${secili.length})` : idler.length >= 2 ? 'Hepsini karşılaştır' : 'Karşılaştır'}
            </button>
          )
        })()}
      </div>
      <div className="listem-grid">
        {liste.map((b) => {
          const sec = secili.includes(b.bolum_id)
          return (
            <div key={b.bolum_id} className={`listem-kart${sec ? ' secili' : ''}`}>
              <label className="listem-sec" title={sec ? 'Karşılaştırmadan çıkar' : secili.length >= 3 ? 'En fazla 3 bölüm' : 'Karşılaştırmaya ekle'}>
                <input type="checkbox" checked={sec} disabled={!sec && secili.length >= 3} onChange={() => degistir(b.bolum_id)} />
              </label>
              <div className="listem-govde">
                {(b.ust_alan || b.alt_alan) && <div className="listem-alan">{b.alt_alan || b.ust_alan}</div>}
                <div className="listem-ad"><BolumAdi id={b.bolum_id} ad={b.bolum_adi} /></div>
                {b.toplam_uyum != null ? (
                  <div className="listem-uyum">
                    <div className="mini-ilerleme-track" style={{ flex: 1 }}>
                      <div className="mini-ilerleme-fill" style={{ width: `${b.toplam_uyum}%`, background: 'var(--pu)' }} />
                    </div>
                    <b>%{Math.round(b.toplam_uyum)}</b>
                  </div>
                ) : <div className="yp-ince" style={{ marginTop: 6 }}>Uyum, değerlendirme bitince görünür</div>}
                <button className="hg-link" style={{ marginTop: 8 }} onClick={() => navigate(`/profil?hedef=${b.bolum_id}#hedef`)}>Hedefim yap →</button>
              </div>
              <FavoriYildiz id={b.bolum_id} ad={b.bolum_adi} />
            </div>
          )
        })}
      </div>
    </>
  )
}
