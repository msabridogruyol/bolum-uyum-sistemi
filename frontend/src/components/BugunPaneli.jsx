// [2026-10-10] Ana sayfanın en üstü: "Bugün ne yapmalıyım?" — tek sıradaki adım + YKS geri sayımı + haftalık mesaj.
import { useNavigate } from 'react-router-dom'
import { KATMAN_BILGI, katmanAdi } from '../yardimci/katmanAdlari'

const AY = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
const uzunTarih = (t) => { const d = new Date(t); return `${d.getDate()} ${AY[d.getMonth()]} ${d.getFullYear()}` }

function SiradakiAdim({ ozet, katmanlar, hedef, plan, kocluk = true }) {
  const navigate = useNavigate()
  let ust, baslik, alt, dugme, git
  const bekleyen = (katmanlar || []).find((k) => !k.kosullu_mu && k.durum !== 'tamamlandi')
  if (!ozet.tur_tamamlandi_mi && bekleyen) {
    const b = KATMAN_BILGI[bekleyen.kod] || {}
    ust = `Değerlendirme · ${ozet.tamamlanan_katman_sayisi}/${ozet.toplam_ana_katman_sayisi} tamam`
    baslik = `${b.ikon || '📝'} ${katmanAdi(bekleyen.kod, bekleyen.ad)}`
    alt = `${b.soru || ''} ${b.sure || ''} · Yarıda bırakırsan kaldığın yerden devam edersin.`
    dugme = bekleyen.durum === 'devam_ediyor' ? 'Kaldığın yerden devam et' : 'Başla'; git = '/katmanlar'
  } else if (!ozet.tur_tamamlandi_mi) {
    ust = 'Değerlendirme'; baslik = '🌻 Sana özel alan soruları'; alt = 'Bölüm önerilerin bu adımdan sonra kesinleşir.'; dugme = 'Devam et'; git = '/katmanlar'
  } else if (!hedef) {
    ust = 'Sonuçların hazır'; baslik = '🎯 Bir hedef bölüm seç'; alt = 'Sana uygun bölümlere bak, birini hedef yapınca adım adım planın hazırlanır.'; dugme = 'Bölümlerime bak'; git = '/bolumler'
  } else if (!kocluk) {
    // [2026-10-10] Koçluk okulun paketinde yoksa: hedef bölümü bölüm sayfasında incele
    ust = 'Hedefin'; baslik = `🎯 ${hedef.bolum_adi || hedef.ad || 'Hedef bölümün'}`; alt = 'Bölüm sayfasında gereken yetkinlikleri ve sana uyumunu inceleyebilirsin.'; dugme = 'Bölümlerime bak'; git = '/bolumler'
  } else if (plan?.siradaki_adim) {
    const s = plan.siradaki_adim
    ust = `Koçluk · ${s.degisken_adi} · ⏱ ${s.sure}`
    baslik = s.baslik
    alt = s.kazanim ? `🎁 ${s.kazanim}` : s.aciklama
    dugme = s.durum === 'devam_ediyor' ? 'Devam et' : 'Adımı aç'; git = '/koclugu?sekme=yol'
  } else if (plan) {
    ust = 'Koçluk'; baslik = '🎉 Yol haritanın tamamını bitirdin'; alt = 'Güçlü yönlerini büyütecek adımlara geçebilirsin.'; dugme = 'Güçlü yönlerim'; git = '/koclugu?sekme=guclu'
  } else if (plan === false) {
    ust = 'Koçluk'; baslik = '🎯 Koçluğuna göz at'; alt = 'Planın şu an gösterilemedi; alan soruların bekliyor olabilir.'; dugme = 'Koçluğum'; git = '/koclugu'
  } else return <div className="bugun-adim"><div className="bugun-ust">Yükleniyor…</div></div>
  return (
    <div className="bugun-adim" role="button" tabIndex={0} onClick={() => navigate(git)} onKeyDown={(e) => { if (e.key === 'Enter') navigate(git) }}>
      <div className="bugun-etiket">👉 Sıradaki adımın</div>
      <div className="bugun-ust">{ust}</div>
      <div className="bugun-baslik">{baslik}</div>
      <div className="bugun-alt">{alt}</div>
      {plan?.siradaki_adim?.uyarlama && ozet.tur_tamamlandi_mi && hedef && <div className="bugun-uyarlama">🧭 {plan.siradaki_adim.uyarlama}</div>}
      <span className="btn bugun-dugme">{dugme} →</span>
    </div>
  )
}

function YksSayaci({ yks, mesaj }) {
  if (!yks) return null
  const sonSinif = yks.son_sinif
  return (
    <div className={`bugun-yks${sonSinif ? ' son' : ''}`}>
      <div className="bugun-etiket">⏳ {yks.ad}</div>
      <div className="yks-sayi"><b>{yks.gun}</b><span>gün</span></div>
      <div className="yks-alt">≈ {yks.hafta} hafta · {uzunTarih(yks.tarih)}{!yks.resmi && <em title="ÖSYM henüz açıklamadı; Haziran'ın 3. hafta sonu varsayıldı"> (tahmini)</em>}</div>
      {mesaj && <div className="yks-mesaj">“{mesaj}”</div>}
    </div>
  )
}

export default function BugunPaneli({ ozet, katmanlar, hedef, plan, motivasyon, kocluk = true }) {
  const testBitti = !!ozet?.tur_tamamlandi_mi
  return (
    <div className={`bugun-panel${testBitti && motivasyon?.yks ? '' : ' tek'}`}>
      <SiradakiAdim ozet={ozet} katmanlar={katmanlar} hedef={hedef} plan={plan} kocluk={kocluk} />
      {testBitti && <YksSayaci yks={motivasyon?.yks} mesaj={motivasyon?.mesaj} />}
    </div>
  )
}

export function Rozetler({ motivasyon, kocluk = true }) {
  const navigate = useNavigate()
  if (!motivasyon) return null
  const r = motivasyon.rozetler
  return (
    <div className="card" style={{ marginBottom: 0 }}>
      <div className="ct" style={{ display: 'flex', justifyContent: 'space-between' }}>🏅 Rozetlerin <span className="rozet-sayi">{motivasyon.kazanilan}/{r.length}</span></div>
      <div className="rozet-izgara">
        {r.map((x) => (
          <div key={x.ad} className={`rozet${x.kazanildi ? ' kazanildi' : ''}`} title={x.kazanildi ? x.aciklama : `Nasıl kazanılır: ${x.ipucu}`}>
            <span className="rozet-ikon">{x.ikon}</span>
            <span className="rozet-ad">{x.ad}</span>
            {!x.kazanildi && <span className="rozet-ipucu">{x.ipucu}</span>}
          </div>
        ))}
      </div>
      {kocluk && <button className="hg-link" style={{ marginTop: 8 }} onClick={() => navigate('/koclugu?sekme=yol')}>Yeni rozet için sıradaki adımına git →</button>}
    </div>
  )
}
