// [2026-10-11] Sağ altta "şu an çevrim içi" listesi. Etkileşim yok: yalnızca ad ve sınıf görünür (mesaj, profil, puan yok).
// Öğrenci: sayfa açıkken dakikada bir "buradayım" sinyali gönderir ve okulundaki çevrim içi öğrencileri (ad + soyad baş harfi) görür.
// Yönetim: okul yetkilisi kendi okulunu, süper admin seçili okulu ya da okul başına sayıları görür (tam ad).
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

const ARALIK_MS = 60_000

function Satir({ k }) {
  return (
    <li className="cv-satir">
      <span className="cv-nokta" aria-hidden="true" />
      <span className="cv-ad">{k.ad}</span>
      {k.sinif && <span className="cv-sinif">{k.sinif}</span>}
    </li>
  )
}

export default function CevrimiciPanel({ kapsam = 'ogrenci', okulId = null }) {
  const [veri, setVeri] = useState(null)
  const [acik, setAcik] = useState(false)

  const yukle = useCallback(() => {
    if (document.visibilityState !== 'visible') return
    const istek = kapsam === 'ogrenci' ? api.cevrimiciBuradayim() : api.yonetimCevrimici(okulId)
    istek.then(setVeri).catch(() => {})
  }, [kapsam, okulId])

  useEffect(() => {
    yukle()
    const t = window.setInterval(yukle, ARALIK_MS)
    const gorunur = () => { if (document.visibilityState === 'visible') yukle() }
    document.addEventListener('visibilitychange', gorunur)
    return () => { window.clearInterval(t); document.removeEventListener('visibilitychange', gorunur) }
  }, [yukle])

  useEffect(() => {
    if (!acik) return undefined
    const kapat = (e) => { if (e.key === 'Escape') setAcik(false) }
    document.addEventListener('keydown', kapat)
    return () => document.removeEventListener('keydown', kapat)
  }, [acik])

  if (!veri) return null
  const toplam = veri.toplam || 0
  const ogrenci = kapsam === 'ogrenci'

  return (
    <div className="cv-kap" data-sozluk-yok>
      {acik && (
        <div className="cv-panel" role="dialog" aria-label="Çevrim içi öğrenciler">
          <div className="cv-ust">
            <b>🟢 Şu an çevrim içi</b>
            <button className="cv-kapat" onClick={() => setAcik(false)} aria-label="Kapat">✕</button>
          </div>
          <div className="cv-icerik">
            {ogrenci ? (
              <>
                {toplam === 0 && <div className="cv-bos">Okulundan şu an çevrim içi kimse yok.</div>}
                {veri.sinifim?.length > 0 && (<><div className="cv-baslik">Sınıfından</div><ul>{veri.sinifim.map((k, i) => <Satir key={`s${i}`} k={k} />)}</ul></>)}
                {veri.digerleri?.length > 0 && (<><div className="cv-baslik">Okulundan</div><ul>{veri.digerleri.map((k, i) => <Satir key={`d${i}`} k={k} />)}</ul></>)}
                {veri.kesildi && <div className="cv-not">Listede en fazla 60 kişi görünür.</div>}
                <div className="cv-not">
                  {veri.gizli
                    ? 'Sen gizlisin: başkalarının listesinde görünmüyorsun.'
                    : 'Başkaları da senin yalnızca adını ve sınıfını görür.'}{' '}
                  <Link to="/profil" onClick={() => setAcik(false)}>Ayarlar'dan değiştir</Link>
                </div>
              </>
            ) : veri.okullar?.length ? (
              <ul>{veri.okullar.map((o) => (
                <li key={o.id} className="cv-satir"><span className="cv-nokta" aria-hidden="true" /><span className="cv-ad">{o.ad}</span><span className="cv-sinif">{o.sayi} öğrenci</span></li>
              ))}</ul>
            ) : (
              <>
                {toplam === 0 && <div className="cv-bos">Şu an çevrim içi öğrenci yok.</div>}
                {veri.ogrenciler?.length > 0 && <ul>{veri.ogrenciler.map((k) => <Satir key={k.id} k={k} />)}</ul>}
                {veri.gizli_sayisi > 0 && <div className="cv-not">{veri.gizli_sayisi} öğrenci listede görünmemeyi seçti; sayıya dahil.</div>}
                {veri.kesildi && <div className="cv-not">Listede en fazla 200 kişi görünür.</div>}
              </>
            )}
          </div>
        </div>
      )}
      <button className="cv-hap" onClick={() => setAcik((a) => !a)} aria-expanded={acik} title="Şu an çevrim içi olanlar">
        <span className="cv-nokta" aria-hidden="true" /> {toplam} çevrim içi
      </button>
    </div>
  )
}
