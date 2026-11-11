// [2026-11-11] Hoş geldin e-postası: seçilen okulun tamamına (öğrenciler / okul yetkilileri) tek tuşla.
// Öğrenciye "sen", yetkiliye "siz" diliyle ayrı şablon; geçici şifresi olan herkese giriş bilgileri, şifresini
// değiştirmiş olanlara "Şifremi unuttum" yolu yazılır. Gönderim arka planda sürer; ilerleme 2 sn'de bir okunur.
// Okul yetkilisi yalnızca kendi okulunun öğrencilerine gönderir (sunucu da denetler).
import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { Pencere } from './ortak'

export function EpostaOnizleme({ tur, okulId, onKapat }) {
  const [veri, setVeri] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => { api.hosgeldinOnizleme(tur, okulId).then(setVeri).catch((e) => setHata(e.detail || 'Önizleme açılamadı.')) }, [tur, okulId])
  return (
    <Pencere genis baslik={tur === 'ogrenci' ? 'Öğrenci e-postası (örnek)' : 'Okul yetkilisi e-postası (örnek)'}
      altBaslik={veri ? `Konu: ${veri.konu}` : null} onKapat={onKapat} alt={<button className="btn" onClick={onKapat}>Kapat</button>}>
      {hata && <div className="auth-error">{hata}</div>}
      {veri ? <iframe title="E-posta önizlemesi" srcDoc={veri.html} sandbox="" style={{ width: '100%', height: 'min(520px, 56vh)', border: '1px solid var(--bor)', borderRadius: 12, background: '#FAF7EF' }} />
        : !hata && <div className="bos-durum yukleniyor">Yükleniyor…</div>}
      <div className="yp-ince" style={{ marginTop: 8 }}>Örnek kişi ve şifreyle gösterilir; gerçek e-postada her kişinin kendi bilgileri yer alır.</div>
    </Pencere>
  )
}

export function GonderimIlerlemesi({ isId, onBitti }) {
  const [d, setD] = useState(null)
  const [hata, setHata] = useState(null)
  const bitti = useRef(false)
  useEffect(() => {
    if (!isId) return undefined
    let iptal = false
    const oku = async () => {
      try {
        const r = await api.hosgeldinDurum(isId)
        if (iptal) return
        setD(r)
        if (r.bitti && !bitti.current) { bitti.current = true; onBitti?.(r) }
      } catch (e) { if (!iptal) setHata(e.detail || 'Durum okunamadı.') }
    }
    oku()
    const t = setInterval(() => { if (!bitti.current) oku() }, 2000)
    return () => { iptal = true; clearInterval(t) }
  }, [isId, onBitti])
  if (hata) return <div className="yp-ince">{hata}</div>
  if (!d) return <div className="yp-ince">Gönderim başlıyor…</div>
  const yapilan = d.gonderilen + d.hatali
  const oran = d.toplam ? Math.round((yapilan / d.toplam) * 100) : 100
  return (
    <div className="hg-ilerleme" aria-live="polite">
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, marginBottom: 4 }}>
        <span>{d.bitti ? '✓ Gönderim tamamlandı' : '✉ E-postalar gönderiliyor…'}</span>
        <span><b>{yapilan}</b> / {d.toplam}</span>
      </div>
      <div style={{ height: 8, background: 'var(--sur2)', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--bor)' }}>
        <div style={{ width: `${oran}%`, height: '100%', background: 'var(--gr)', transition: 'width .4s' }} />
      </div>
      <div className="yp-ince" style={{ marginTop: 4 }}>
        {d.gonderilen} gönderildi{d.hatali > 0 && <span style={{ color: 'var(--re)' }}> · {d.hatali} gönderilemedi{d.hatalilar?.length ? `: ${d.hatalilar.slice(0, 5).join(', ')}${d.hatalilar.length > 5 ? '…' : ''}` : ''}</span>}
        {!d.bitti && ' · Bu pencereyi kapatabilirsiniz; gönderim sürer.'}
      </div>
    </div>
  )
}

export default function HosgeldinKarti({ okulId, baslik = true }) {
  const [oz, setOz] = useState(null)
  const [hata, setHata] = useState(null)
  const [kime, setKime] = useState('hepsi')
  const [yalnizYeni, setYalnizYeni] = useState(true)
  const [onay, setOnay] = useState(false)
  const [bekle, setBekle] = useState(false)
  const [isId, setIsId] = useState(null)
  const [isBitti, setIsBitti] = useState(false)
  const [onizleme, setOnizleme] = useState(null)

  const yukle = useCallback(() => {
    if (!okulId) return
    api.hosgeldinOzet(okulId).then((r) => { setOz(r); if (r.calisan_is) { setIsBitti(false); setIsId(r.calisan_is.is_id) } }).catch((e) => setHata(e.detail || 'Bilgi alınamadı.'))
  }, [okulId])
  useEffect(() => { yukle() }, [yukle])   // okul değişince bileşen yeniden kurulur (key={okulId})

  const kime_ = oz && !oz.yetkili_gonderebilir ? 'ogrenci' : kime   // okul yetkilisi yalnız öğrencilere
  const sayi = (g) => (oz ? (yalnizYeni ? g.toplam - g.gonderilmis : g.toplam) : 0)
  const hedef = oz ? (kime_ !== 'yetkili' ? sayi(oz.ogrenci) : 0) + (kime_ !== 'ogrenci' ? sayi(oz.yetkili) : 0) : 0

  async function gonder() {
    setBekle(true); setHata(null)
    try {
      const r = await api.hosgeldinGonder({ okul_id: okulId, kime: kime_, yalniz_gonderilmemis: yalnizYeni })
      setIsBitti(false); setIsId(r.is_id); setOnay(false)
    } catch (e) { setHata(e.detail || 'Gönderim başlatılamadı.') } finally { setBekle(false) }
  }

  const bittiginde = useCallback(() => { setIsBitti(true); setTimeout(yukle, 300) }, [yukle])

  if (!okulId) return <div className="yp-ince">Önce bir okul seçin.</div>
  return (
    <div className="hg-kart">
      {baslik && <div className="yp-kb">✉ Hoş geldin e-postası</div>}
      <div className="yp-ince" style={{ marginBottom: 10 }}>
        “Hoş geldiniz, sisteminiz aktif hale getirilmiştir” e-postası: kısa sistem tanıtımı, giriş adresi, e-posta ve (hesap hâlâ geçici
        şifredeyse) geçici şifre. Öğrencilere ve okul yetkililerine ayrı şablon gider.
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {oz && !oz.eposta_hazir && <div className="auth-error">E-posta gönderimi yapılandırılmamış; gönderim yapılamaz.</div>}
      {oz && (
        <>
          <div className="hg-sayilar">
            <div><b>{oz.ogrenci.toplam}</b> öğrenci<span className="yp-ince"> · {oz.ogrenci.gonderilmis} gönderilmiş · {oz.ogrenci.gecici_sifreli} geçici şifrede</span></div>
            {oz.yetkili_gonderebilir && <div><b>{oz.yetkili.toplam}</b> okul yetkilisi<span className="yp-ince"> · {oz.yetkili.gonderilmis} gönderilmiş · {oz.yetkili.gecici_sifreli} geçici şifrede</span></div>}
          </div>
          {oz.yetkili_gonderebilir && (
            <div className="hg-secenek" role="radiogroup" aria-label="Kime">
              {[['hepsi', 'Herkese'], ['ogrenci', 'Yalnız öğrencilere'], ['yetkili', 'Yalnız okul yetkililerine']].map(([k, ad]) => (
                <label key={k}><input type="radio" name={`kime-${okulId}`} checked={kime === k} onChange={() => { setKime(k); setOnay(false) }} /> {ad}</label>
              ))}
            </div>
          )}
          <label className="hg-secenek" style={{ display: 'flex' }}>
            <input type="checkbox" checked={yalnizYeni} onChange={(e) => { setYalnizYeni(e.target.checked); setOnay(false) }} />
            &nbsp;Yalnız daha önce gönderilmemiş olanlara
          </label>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginTop: 10 }}>
            <button className="btn sec" onClick={() => setOnizleme('ogrenci')}>👁 Öğrenci e-postası</button>
            {oz.yetkili_gonderebilir && <button className="btn sec" onClick={() => setOnizleme('yetkili')}>👁 Yetkili e-postası</button>}
            <div style={{ flex: 1 }} />
            {onay ? (
              <>
                <span style={{ fontSize: 12.5 }}><b>{oz.okul}</b>: {hedef} kişiye e-posta gidecek. Emin misiniz?</span>
                <button className="btn" disabled={bekle} onClick={gonder}>{bekle ? <span className="spin" /> : 'Evet, gönder'}</button>
                <button className="btn sec" onClick={() => setOnay(false)}>Vazgeç</button>
              </>
            ) : (
              <button className="btn" disabled={!hedef || !oz.eposta_hazir || (isId && !isBitti)} onClick={() => setOnay(true)}>
                ✉ {hedef ? `${hedef} kişiye gönder` : 'Gönderilecek kişi yok'}
              </button>
            )}
          </div>
          {hedef > 400 && <div className="yp-ince" style={{ marginTop: 6, color: 'var(--am)' }}>
            Çok sayıda e-posta: e-posta sağlayıcısının günlük gönderim sınırı aşılırsa bir kısmı gönderilemez; “yalnız gönderilmemiş” seçeneğiyle ertesi gün kalanlar gönderilebilir.
          </div>}
        </>
      )}
      {isId && <div style={{ marginTop: 12 }}><GonderimIlerlemesi isId={isId} onBitti={bittiginde} /></div>}
      {onizleme && <EpostaOnizleme tur={onizleme} okulId={okulId} onKapat={() => setOnizleme(null)} />}
    </div>
  )
}
