// [2026-10-12] Yeniden değerlendirme açılır penceresi (öğrenci).
// Kurallar (backend: katman_servisi.degerlendirme_durumu):
//  - guven_sorunu: son değerlendirmede güven puanı düşük → yalnızca sorunlu bölüm(ler) tekrar çözülebilir
//  - bekleme: güven sorunu yok → sınıfa göre bekleme süresi (12. sınıf / mezun 70 gün, diğerleri yılda 2) sonunda yeniden açılır; bu süre içinde durum gösterilir
//  - acik: süre doldu ya da okul yetkilisi yeniden değerlendirme açtı → yeni tur başlatılabilir
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { Pencere } from './yonetim/ortak'
import { katmanAdi } from '../yardimci/katmanAdlari'

const tarihYaz = (t) => (t ? new Date(t).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' }) : '—')

export default function YenidenDegerlendirmePenceresi({ durum, onKapat }) {
  const navigate = useNavigate()
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  if (!durum) return null

  async function tekrarCoz(kod) {
    setBekle(true); setHata(null)
    try {
      await api.katmanTekrar(kod)
      navigate(`/katmanlar/${kod}`)
    } catch (e) { setHata(e.detail || 'Bölüm açılamadı.'); setBekle(false) }
  }

  if (durum.durum === 'guven_sorunu') {
    const sorunlu = durum.sorunlu_katmanlar || []
    return (
      <Pencere baslik="🛡️ Bu bölümü yeniden çözmen gerekiyor" onKapat={onKapat}
        alt={<button className="btn sec" onClick={onKapat}>Kapat</button>}>
        <div className="yd-metin">
          Son değerlendirmende güven puanın düşük çıktı. Bu yüzden sonuçların henüz tam güvenilir sayılmıyor.
          Tüm değerlendirmeyi baştan çözmene gerek yok: yalnızca aşağıdaki bölümü yeniden çözmen yeterli.
        </div>
        <div className="yd-liste">
          {sorunlu.map((k) => (
            <div key={k.kod} className="yd-satir">
              <div><b>{katmanAdi(k.kod, k.ad)}</b></div>
              <button className="btn" disabled={bekle} onClick={() => tekrarCoz(k.kod)}>Bu bölümü tekrar çöz</button>
            </div>
          ))}
        </div>
        <div className="yp-ince" style={{ marginTop: 10 }}>
          Diğer bölümlerdeki cevapların korunur. Çözerken sekme değiştirmemeye ve soruları dikkatle okumaya özen göster.
        </div>
        {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}
      </Pencere>
    )
  }

  if (durum.durum === 'bekleme') {
    return (
      <Pencere baslik="⏳ Değerlendirmeni tamamladın" onKapat={onKapat}
        alt={<button className="btn" onClick={onKapat}>Tamam</button>}>
        <div className="yd-ozet">
          <div><span className="yp-ince">Tamamlama tarihi</span><b>{tarihYaz(durum.tamamlanma)}</b></div>
          <div><span className="yp-ince">Yeniden açılış</span><b>{tarihYaz(durum.yeniden_acilis)}</b></div>
          <div><span className="yp-ince">Kalan süre</span><b>{`${durum.kalan_gun} gün`}</b></div>
        </div>
        <div className="yd-metin">
          {`İlgi ve eğilimler kısa sürede pek değişmez. Sonuçların anlamlı bir karşılaştırma sunması için yeniden değerlendirme, tamamladığın tarihten ${durum.bekleme_gun} gün sonra açılır.`}
        </div>
        <div className="yp-ince" style={{ marginTop: 10 }}>
          Gerekli görülürse okulunun rehber öğretmeni değerlendirmeyi daha erken açabilir. Bu sırada sonuçlarını ve bölüm önerilerini incelemeye devam edebilirsin.
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
          <button className="btn sec" onClick={() => navigate('/profilim')}>Sonuçlarıma git</button>
        </div>
      </Pencere>
    )
  }

  if (durum.durum === 'acik') {
    return (
      <Pencere baslik="🔁 Yeni değerlendirme açık" onKapat={onKapat}
        alt={<>
          <button className="btn sec" onClick={onKapat}>Vazgeç</button>
          <button className="btn" onClick={() => navigate('/katmanlar/K1')}>Yeni değerlendirmeyi başlat</button>
        </>}>
        <div className="yd-metin">
          {durum.yonetim_izni
            ? 'Okulun yeni bir değerlendirme yapmana izin verdi.'
            : 'Son değerlendirmenin üzerinden yeterli süre geçti; yeniden değerlendirme yapabilirsin.'}
        </div>
        <div className="yp-ince" style={{ marginTop: 10 }}>
          Yeni değerlendirme ilk bölümden başlar. Önceki sonuçların silinmez; gelişimini karşılaştırmak için saklanır.
        </div>
      </Pencere>
    )
  }
  return null
}
