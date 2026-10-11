// [2026-10-10] İş Hayatı → 'cv' sekmesi (CV Atölyesi): CV oluşturucu (portfolyodan otomatik dolar), kontrol listesi (/100),
// ön yazı şablonu, ilan okuma egzersizi. Uçlar: app/api/is_hayati_cv.py. Sözleşme: props { bolum, veri, ogrenci }.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import CvDuzenleyici, { yeniId } from './cv/CvDuzenleyici'
import AtsKontrol from './cv/AtsKontrol'
import CvKontrol, { puanRengi } from './cv/CvKontrol'
import CvOnizleme from './cv/CvOnizleme'
import CvRehberi from './cv/CvRehberi'
import IlanOkuma from './cv/IlanOkuma'
import OnYazi from './cv/OnYazi'

// [2026-10-11] 'rehber' (ilk; CV'si kayıtlı olmayan öğrenciyi karşılar) ve 'ats' alt sekmeleri eklendi.
const ALT = [
  { kod: 'rehber', ad: '📚 CV Rehberi' },
  { kod: 'olustur', ad: '✏️ CV\'ni oluştur' },
  { kod: 'kontrol', ad: '✅ Kontrol listesi' },
  { kod: 'ats', ad: '🤖 ATS kontrolü' },
  { kod: 'onyazi', ad: '✉️ Ön yazı' },
  { kod: 'ilan', ad: '🔎 İlan okuma' },
]

// Taslakta olup CV'de olmayan portfolyo kayıtlarını / kulüpleri ilgili bölüme ekler (CV'deki düzenlemeler korunur).
function portfolyodanEkle(icerik, taslak) {
  let eklenen = 0
  const bolumler = icerik.bolumler.map((b) => {
    const t = taslak.bolumler.find((x) => x.kod === b.kod)
    if (!t || !Array.isArray(b.ogeler) || !t.ogeler.length || typeof t.ogeler[0] !== 'object' || 'dil' in t.ogeler[0]) return b
    const yeni = t.ogeler.filter((o) => (o.portfolyo_id ? !icerik.bolumler.some((x) => x.ogeler.some((y) => y?.portfolyo_id === o.portfolyo_id))
      : o.kulup && !b.ogeler.some((y) => y.baslik === o.baslik)))
    eklenen += yeni.length
    return yeni.length ? { ...b, ogeler: [...b.ogeler, ...yeni.map((o) => ({ ...o, id: yeniId() }))] } : b
  })
  return [{ ...icerik, bolumler }, eklenen]
}

export default function CvAtolyesi({ bolum }) {
  const [v, setV] = useState(null)
  const [icerik, setIcerikHam] = useState(null)
  const [degisti, setDegisti] = useState(false)
  const [altSecim, setAlt] = useState(null)   // null → kayıtlı CV yoksa rehber, varsa oluşturucu
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const [mesaj, setMesaj] = useState(null)
  const [onizleme, setOnizleme] = useState(false)
  const [sifirOnay, setSifirOnay] = useState(false)

  function yukle(x) { setV(x); setIcerikHam(x.cv ? x.cv.icerik : x.taslak); setDegisti(false) }
  useEffect(() => { api.isHayatiCv().then(yukle).catch((e) => setHata(e.detail || 'CV yüklenemedi.')) }, [])
  useEffect(() => {
    if (!degisti) return undefined
    const uyar = (e) => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', uyar)
    return () => window.removeEventListener('beforeunload', uyar)
  }, [degisti])

  const setIcerik = (x) => { setIcerikHam(x); setDegisti(true); setMesaj(null) }
  const paylas = !!v?.cv?.paylas

  async function kaydet(yeniPaylas = paylas, govde = icerik) {
    setBekle(true); setHata(null)
    try { yukle(await api.isHayatiCvKaydet(govde, yeniPaylas)); setMesaj(yeniPaylas !== paylas ? (yeniPaylas ? 'CV\'n okulunla paylaşıldı.' : 'Paylaşım kapatıldı; okulun artık CV\'ni göremez.') : 'Kaydedildi.') } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  async function pdf() {
    setHata(null)
    if (degisti || !v.cv) await kaydet()
    try { await api.isHayatiCvPdf() } catch (e) { setHata(e.detail || 'PDF hazırlanamadı.') }
  }
  async function sifirla() {
    setSifirOnay(false); setBekle(true)
    try { yukle(await api.isHayatiCvSil()); setMesaj('CV\'n portfolyondan yeniden oluşturuldu.') } catch (e) { setHata(e.detail || 'Sıfırlanamadı.') } finally { setBekle(false) }
  }

  if (!v || !icerik) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const k = v.kontrol
  const alt = altSecim || (v.cv ? 'olustur' : 'rehber')
  const git = (kod) => { setAlt(kod); window.scrollTo?.({ top: Math.max(0, (document.querySelector('.cva-alt')?.getBoundingClientRect().top || 0) + window.scrollY - 80), behavior: 'smooth' }) }

  return (
    <div className="cva">
      <div className="card cva-ust">
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ fontWeight: 800, fontSize: 15 }}>📄 {v.cv ? 'CV\'n' : 'CV taslağın hazır'}</div>
          <div className="yp-ince" style={{ lineHeight: 1.55, marginTop: 2 }}>
            {v.cv ? `Son kayıt: ${new Date(v.cv.guncelleme).toLocaleString('tr-TR', { dateStyle: 'medium', timeStyle: 'short' })}.` : 'Portfolyondaki kayıtlardan otomatik dolduruldu; düzenleyip kaydet.'}
            {' '}Portfolyonda {v.oneriler.portfolyo_kayit} kayıt, {v.oneriler.portfolyo_onayli} okul onaylı · <Link to="/portfolyo" className="hg-link" style={{ fontSize: 11.5 }}>Portfolyoma git →</Link>
          </div>
        </div>
        <button type="button" className="cva-mini-puan" onClick={() => setAlt('kontrol')} title="Kontrol listesini aç">
          <b style={{ color: puanRengi(k.puan) }}>{k.puan}</b><span>/100</span>
        </button>
        <div className="cva-dugmeler">
          <button className="btn" disabled={bekle || (!degisti && v.cv)} onClick={() => kaydet()}>{bekle ? <span className="spin" /> : degisti || !v.cv ? 'Kaydet' : '✓ Kaydedildi'}</button>
          <button className="btn sec" disabled={bekle} onClick={pdf}>📄 PDF indir</button>
        </div>
      </div>

      <label className="cva-paylas">
        <input type="checkbox" checked={paylas} disabled={bekle} onChange={(e) => kaydet(e.target.checked)} />
        <span><b>CV'mi okulumla paylaş</b> — işaretlersen rehber öğretmenin ve okul yetkililerin CV'ni öğrenci detayında görebilir (ön yazın paylaşılmaz).
          İşaretlemezsen CV'n yalnızca sende kalır. İstediğin zaman kapatabilirsin.</span>
      </label>
      {hata && <div className="auth-error">{hata}</div>}
      {mesaj && <div className="cva-mesaj" role="status">{mesaj}</div>}

      <div className="eu-filtre cva-alt" role="tablist">
        {ALT.map((a) => <button key={a.kod} role="tab" aria-selected={alt === a.kod} className={alt === a.kod ? 'secili' : ''} onClick={() => setAlt(a.kod)}>
          {a.ad}{a.kod === 'kontrol' && <b style={{ color: puanRengi(k.puan) }}>{k.puan}</b>}</button>)}
      </div>

      {alt === 'olustur' && (
        <div className="cva-duzen">
          <div>
            <div className="cva-arac">
              <button type="button" className="hg-link" onClick={() => { const [yeni, n] = portfolyodanEkle(icerik, v.taslak); if (n) setIcerik(yeni); setMesaj(n ? `Portfolyondan ${n} yeni kayıt eklendi.` : 'Portfolyonda CV\'ye eklenmemiş yeni kayıt yok.') }}>↻ Portfolyodaki yeni kayıtları ekle</button>
              {sifirOnay
                ? <span className="yp-ince">Tüm düzenlemelerin silinecek. <button type="button" className="hg-link" style={{ color: 'var(--re)' }} onClick={sifirla}>Evet, baştan oluştur</button> · <button type="button" className="hg-link" onClick={() => setSifirOnay(false)}>Vazgeç</button></span>
                : v.cv && <button type="button" className="hg-link" onClick={() => setSifirOnay(true)}>Baştan oluştur</button>}
              <button type="button" className="hg-link cva-onizle-dugme" onClick={() => setOnizleme(!onizleme)}>{onizleme ? 'Düzenlemeye dön' : '👁 Önizleme'}</button>
            </div>
            {onizleme ? <div className="cva-mobil-onizleme"><CvOnizleme icerik={icerik} /></div>
              : <CvDuzenleyici icerik={icerik} setIcerik={setIcerik} sabitler={v.sabitler} oneriler={v.oneriler} />}
          </div>
          <div className="cva-yapiskan cva-masaustu">
            <div className="ct" style={{ marginBottom: 8 }}>Önizleme</div>
            <CvOnizleme icerik={icerik} kucuk />
            <div className="yp-ince" style={{ marginTop: 8, lineHeight: 1.5 }}>PDF sade ve tek sayfa olacak şekilde hazırlanır: tablo ve görsel yok, böylece başvuru sistemleri (ATS) metni doğru okur.{' '}
              <button type="button" className="hg-link" style={{ fontSize: 11.5, color: 'var(--okul-c)' }} onClick={() => git('ats')}>ATS'nin gördüğünü göster →</button></div>
          </div>
        </div>
      )}
      {alt === 'rehber' && <CvRehberi onGit={git} />}
      {alt === 'kontrol' && <CvKontrol kontrol={k} degisti={degisti} kayitli={!!v.cv} kaydediliyor={bekle} onKaydet={() => kaydet()} onGit={git} />}
      {alt === 'ats' && <AtsKontrol icerik={icerik} degisti={degisti} bolum={bolum} onGit={git} />}
      {alt === 'onyazi' && <OnYazi onYazi={icerik.on_yazi} setOnYazi={(x) => setIcerik({ ...icerik, on_yazi: x })} ad={icerik.kisisel.ad} eposta={icerik.kisisel.eposta} />}
      {alt === 'ilan' && <IlanOkuma bolum={bolum} />}
    </div>
  )
}
