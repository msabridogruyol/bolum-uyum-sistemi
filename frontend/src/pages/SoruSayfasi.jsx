import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { KATMAN_BILGI } from '../yardimci/katmanAdlari'

function renkSec(puan) {
  if (puan >= 70) return 'var(--gr)'
  if (puan >= 40) return 'var(--pu)'
  return 'var(--tx3)'
}

function DegiskenKarti({ s }) {
  return (
    <div style={{ padding: '14px 0', borderBottom: '1px solid var(--bor)' }}>
      <div className="dr" style={{ marginBottom: s.durum_tespiti ? 8 : 0 }}>
        <div className="dl">{s.degisken_adi}</div>
        <div className="db"><div className="df" style={{ width: `${s.puan}%`, background: renkSec(s.puan) }} /></div>
        <div className="ds" style={{ color: renkSec(s.puan) }}>{s.puan}</div>
      </div>
      {s.durum_tespiti && (
        <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.6, marginTop: 4 }}>{s.durum_tespiti}</div>
      )}
      {s.aksiyon_onerisi && (
        <div style={{
          marginTop: 8, fontSize: 12, color: 'var(--am)', background: 'var(--aml)',
          padding: '8px 12px', borderRadius: 10, display: 'flex', gap: 8, alignItems: 'flex-start',
        }}>
          <span>💡</span>
          <span>{s.aksiyon_onerisi}</span>
        </div>
      )}
    </div>
  )
}

// ============================================================
// Güvenlik altyapısı — tam ekran zorlama, sekme/odak takibi, periyodik fotoğraf
// ============================================================
const FOTOGRAF_ARALIGI_SORU = 4  // her 4 soruda bir fotoğraf çek
// [2026-10-10] Öğrenciye anında gösterilen ihlal bildirimleri (cezalı olaylar)
const IHLAL_METNI = {
  tam_ekrandan_cikti: 'Tam ekrandan çıktın.',
  sekme_degisti: 'Başka bir sekmeye geçtin.',
  pencere_odagi_kaybedildi: 'Başka bir pencereye geçtin.',
  coklu_ekran: 'İkinci bir ekran algılandı.',
  ekran_goruntusu_tusu: 'Ekran görüntüsü tuşuna bastın.',
  kopyalama: 'Kopyalama yapılamaz.',
  kamera_kapandi: 'Kamera kapandı.',
}
// [2026-10-10] Soru tipleri ve nasıl cevaplanacakları (tanıtım ekranında ve her sorunun üstünde)
const SORU_TIPI = {
  likert: { ad: 'Katılım sorusu', ikon: '📏', kisa: 'Bu ifade seni ne kadar anlatıyor?', uzun: 'Bir ifade okursun ve sana ne kadar uyduğunu seçersin: “Kesinlikle katılmıyorum”dan “Kesinlikle katılıyorum”a kadar. Ortadaki şık “kararsızım” demektir; mümkün olduğunca net olmaya çalış.' },
  kutup: { ad: 'Tercih sorusu', ikon: '⚖️', kisa: 'İki uçtan hangisine daha yakınsın?', uzun: 'İki farklı tercih verilir. Hangisine ne kadar yakın olduğunu seçersin: “Kesinlikle A” · “Daha çok A” · “Daha çok B” · “Kesinlikle B”. İkisi de iyi olabilir; sana daha yakın olanı seç.' },
  sjt: { ad: 'Durum sorusu', ikon: '🎬', kisa: 'Sen olsan ne yapardın?', uzun: 'Gerçek hayattan bir durum anlatılır. Sen o durumda olsan en çok ne yapacağını seçersin. “En çok / en az” sorularında önce sana EN ÇOK uyan, sonra EN AZ uyan şıkkı seçersin.' },
  kontrol: { ad: 'Dikkat sorusu', ikon: '👀', kisa: 'Soruda ne isteniyorsa onu seç.', uzun: 'Arada dikkatli okuduğunu gösteren kısa sorular vardır; soruda istenen şıkkı seçmen yeterli. Bu sorular puanına değil güven puanına etki eder.' },
}

function GuvenlikUyariKatmani({ tamEkranaGeriDon, onErkenBitir }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(20,16,10,0.92)', zIndex: 9999,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      color: '#fff', textAlign: 'center', padding: 24,
    }}>
      <div style={{ fontSize: 40, marginBottom: 12 }}>⚠️</div>
      <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Tam ekrandan çıktınız</div>
      <div style={{ fontSize: 13.5, opacity: 0.85, marginBottom: 20, maxWidth: 380 }}>
        Bu değerlendirme tam ekran modunda yapılmalı. Devam etmek için tam ekrana geri dönün.
      </div>
      <button className="btn" onClick={tamEkranaGeriDon}>Tam Ekrana Geri Dön</button>
      <button
        onClick={onErkenBitir}
        style={{ marginTop: 16, background: 'none', border: 'none', color: 'rgba(255,255,255,0.65)', fontSize: 12.5, fontWeight: 600, cursor: 'pointer', textDecoration: 'underline' }}
      >
        Sınavı erken bitir
      </button>
    </div>
  )
}

// Sınav ekranının üstündeki sabit logo/marka satırı
function SinavBasligi() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '14px 0 2px' }}>
      <span style={{ fontSize: 20 }}>🌱</span>
      <span style={{ fontFamily: 'var(--fd)', fontSize: 16, fontWeight: 700, color: 'var(--tx)' }}>
        Filizyol
      </span>
    </div>
  )
}

// Sağ üstte, öğrencinin kendini görebildiği canlı kamera önizlemesi
function KameraOnizleme({ videoRef }) {
  return (
    <div className="sn-kamera-onizleme" title="Kamera doğrulaması açık">
      <video ref={videoRef} muted playsInline />
    </div>
  )
}

// ============================================================
// Katman Tanıtım / Onay Ekranı — her katman başında bir kez gösterilir
// ============================================================
const ONAY_METNI = 'ONAYLIYORUM'

function KatmanTanitimEkrani({ kod, sorular, onBasla, cikisYapiliyor, baslik, altBaslik, kameraRizasi, onKameraIzni, devamBilgisi }) {
  const [yaziliOnay, setYaziliOnay] = useState('')
  const [kurallarOk, setKurallarOk] = useState(false)
  const [kameraBekle, setKameraBekle] = useState(false)
  const katman = KATMAN_BILGI[kod] || { ikon: '🌻', ad: baslik || kod }

  const tipler = ['kutup', 'likert', 'sjt', 'kontrol'].map((t) => ({ t, n: sorular.filter((s) => s.soru_tipi === t).length })).filter((x) => x.n > 0)
  const say = (t) => sorular.filter((s) => s.soru_tipi === t).length
  const tahminiDakika = Math.max(1, Math.ceil((say('likert') * 15 + say('kutup') * 20 + say('sjt') * 30 + say('kontrol') * 10) / 60))
  const onayGecerli = yaziliOnay.trim() === ONAY_METNI && kurallarOk

  return (
    <div className="qwrap sn-tanitim">
      <div style={{ textAlign: 'center', marginBottom: 22 }}>
        <div style={{ fontSize: 44, marginBottom: 8 }}>{katman.ikon}</div>
        <div style={{ fontFamily: 'var(--fd)', fontSize: 26, fontWeight: 700 }}>{katman.ad}</div>
        <div style={{ fontSize: 14, color: 'var(--tx3)', fontWeight: 600, marginTop: 4 }}>{altBaslik || `${kod} katmanına başlıyorsun`} · {sorular.length} soru · ~{tahminiDakika} dk</div>
      </div>

      <div className="sn-bolum">
        <div className="sn-bolum-bas">🧩 Soru tipleri ve nasıl cevaplanır</div>
        <div className="sn-tipler">
          {tipler.map(({ t, n }) => (
            <div key={t} className="sn-tip">
              <div className="sn-tip-bas"><span>{SORU_TIPI[t].ikon}</span><b>{SORU_TIPI[t].ad}</b><em>{n} soru</em></div>
              <div>{SORU_TIPI[t].uzun}</div>
            </div>
          ))}
        </div>
        <div className="sn-not">Doğru ya da yanlış cevap yok. Uzun düşünme; sana ilk “evet, bu benim” dedirten şıkkı seç. İstersen <b>önceki soruya dönüp</b> cevabını değiştirebilirsin.</div>
      </div>

      <div className="sn-bolum sn-kurallar">
        <div className="sn-bolum-bas">🛡️ Sınav kuralları — lütfen dikkatle oku</div>
        <ul>
          <li>Değerlendirme <b>tam ekranda</b> yapılır. Tam ekrandan çıkmak, <b>başka sekme ya da pencereye geçmek</b>, <b>ikinci ekran</b> kullanmak, <b>ekran görüntüsü tuşu</b> ve <b>kopyalama</b> denemeleri kayda geçer.</li>
          <li>Her ihlal <b>güven puanını</b> düşürür; puanını ekranın üstünde canlı görürsün. Güven puanın <b>50'nin altına düşerse değerlendirmen geçersiz sayılır</b> ve rehber öğretmenin yeniden yapmanı isteyebilir.</li>
          <li>Ekran kaydı ya da başkasından yardım almak da kurallara aykırıdır; sonuçların <b>yalnızca seni</b> anlatırsa işe yarar.</li>
          <li>Ara vermen gerekirse çıkabilirsin: verdiğin cevaplar kaydedilir, döndüğünde <b>kaldığın sorudan</b> devam edersin.</li>
        </ul>
        <div className={`sn-kamera${kameraRizasi ? ' acik' : ''}`}>
          {kameraRizasi ? (
            <span>📷 <b>Kamera doğrulaması açık.</b> Kimlik doğrulama için aralıklarla fotoğraf çekilir; fotoğraflar 6 ay sonra silinir.</span>
          ) : (
            <>
              <span>📷 <b>Kamera doğrulaması kapalı.</b> Açarsan sonucun “kimliği doğrulanmış” olarak işaretlenir. Açmak zorunlu değil; açmasan da puanın düşmez.</span>
              <button className="btn sec" disabled={kameraBekle || kameraRizasi === null} onClick={async () => { setKameraBekle(true); await onKameraIzni(); setKameraBekle(false) }}>
                {kameraBekle ? <span className="spin" /> : 'Kamerayı aç'}
              </button>
            </>
          )}
        </div>
        <label className="sn-onay"><input type="checkbox" checked={kurallarOk} onChange={(e) => setKurallarOk(e.target.checked)} /> Kuralları okudum; ihlal durumunda değerlendirmemin geçersiz sayılabileceğini biliyorum.</label>
      </div>

      <div className="auth-field">
        <label className="auth-label">Başlamak için aşağıya büyük harflerle <b>{ONAY_METNI}</b> yaz:</label>
        <input className="auth-input" value={yaziliOnay} onChange={(e) => setYaziliOnay(e.target.value)} placeholder={ONAY_METNI} autoComplete="off" />
      </div>
      {devamBilgisi && (
        <div className="yp-basari" style={{ marginBottom: 10 }}>
          ✓ Bu bölüme daha önce başlamıştın: <b>{devamBilgisi.cevaplanan}/{devamBilgisi.toplam}</b> sorunun cevabı kayıtlı. Kaldığın yerden devam edeceksin; önceki cevaplarını "← Önceki soru" ile görebilir ve değiştirebilirsin.
        </div>
      )}
      <button className="btn full" disabled={!onayGecerli || cikisYapiliyor} onClick={onBasla} style={{ marginTop: 4, fontSize: 16, padding: 15 }}>
        {cikisYapiliyor ? <span className="spin" /> : devamBilgisi ? `Kaldığın yerden devam et (${devamBilgisi.sira}. soru) →` : 'Değerlendirmeye Başla →'}
      </button>
    </div>
  )
}


// [2026-10-03] mod='dal' → K5 dal soruları da K1-K4 ile birebir aynı akışta
// (tanıtım/onay ekranı, tam ekran, kamera, sonuç ekranı) çalışır; yalnızca API uç noktaları farklıdır.
export default function SoruSayfasi({ mod = 'katman' }) {
  const { kod } = useParams()
  const navigate = useNavigate()
  const dalMi = mod === 'dal'
  const [dalAdi, setDalAdi] = useState(null)
  const [k5Bekliyor, setK5Bekliyor] = useState(false)

  const [sorular, setSorular] = useState(null)
  const [turId, setTurId] = useState(null)
  const [aktifIndex, setAktifIndex] = useState(0)
  const [cevaplar, setCevaplar] = useState({})
  const [devamBilgisi, setDevamBilgisi] = useState(null)   // [2026-10-10] { cevaplanan, toplam }
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [tamamlandi, setTamamlandi] = useState(null)
  const [tamEkranDisinda, setTamEkranDisinda] = useState(false)
  const [basladiMi, setBasladiMi] = useState(false)  // tanıtım/onay ekranı geçildi mi
  const [guven, setGuven] = useState(null)           // [2026-10-10] canlı güven puanı {guven_puani, esik, ihlaller}
  const [uyari, setUyari] = useState(null)           // ihlal bildirimi (6 sn)
  const [ikinciEkran, setIkinciEkran] = useState(false)
  const [kameraDurumu, setKameraDurumu] = useState('kapali')  // acik | kapali | reddedildi | yok

  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const kameraAktifRef = useRef(false)
  const turIdRef = useRef(null)  // olay/fotoğraf gönderirken en güncel tur_id'yi kullanmak için
  // [2026-10-04] KVKK: kamera yalnızca öğrenci "kamera" iznini verdiyse açılır (Ayarlar > Gizlilik ve İzinler)
  const [kameraRizasi, setKameraRizasi] = useState(null)
  useEffect(() => {
    api.kvkkDurumu().then((d) => setKameraRizasi(!!d.onaylar?.kamera)).catch(() => setKameraRizasi(false))
  }, [])

  useEffect(() => { turIdRef.current = turId }, [turId])

  // ------------------------------------------------------------------
  // Katman başlatma
  // ------------------------------------------------------------------
  useEffect(() => {
    setSorular(null)
    setAktifIndex(0)
    setCevaplar({})
    setTamamlandi(null)
    setBasladiMi(false)
    ;(dalMi ? api.daliBaslat(kod) : api.katmaniBaslat(kod))
      .then((veri) => {
        // [2026-10-10] Yarıda bırakılan katman: önceki cevaplar geri yüklenir, ilk cevapsız sorudan devam edilir
        const onceki = {}
        const bicim = Object.fromEntries(veri.sorular.map((x) => [x.id, x.cevap_bicimi]))
        ;(veri.mevcut_cevaplar || []).forEach((c) => {
          onceki[c.soru_id] = bicim[c.soru_id] === 'encok_enaz' ? { enCok: c.secenek_id, enAz: c.en_az_secenek_id } : c.secenek_id
        })
        const ilkBos = veri.sorular.findIndex((x) => !onceki[x.id])
        setCevaplar(onceki)
        setDevamBilgisi(Object.keys(onceki).length ? { cevaplanan: Object.keys(onceki).length, toplam: veri.sorular.length, sira: (ilkBos === -1 ? veri.sorular.length : ilkBos + 1) } : null)
        setAktifIndex(ilkBos === -1 ? Math.max(0, veri.sorular.length - 1) : ilkBos)
        setSorular(veri.sorular)
        setTurId(veri.tur_id ?? null)
        if (dalMi) setDalAdi(veri.dal_adi || null)
      })
      .catch((e) => setHata(e.detail || (dalMi ? 'Alan soruları başlatılamadı.' : 'Katman başlatılamadı.')))
  }, [kod, dalMi])

  // ------------------------------------------------------------------
  // Tam ekrana geçiş + çıkış/geri dönüş yönetimi
  // ------------------------------------------------------------------
  const tamEkranaGec = useCallback(() => {
    const el = document.documentElement
    if (el.requestFullscreen) el.requestFullscreen().catch(() => {})
  }, [])

  useEffect(() => {
    if (sorular && basladiMi && !tamamlandi) tamEkranaGec()
  }, [sorular, basladiMi, tamamlandi, tamEkranaGec])

  // [2026-10-10] Güvenlik olayı: kaydet + canlı güven puanını tazele + cezalı olaylarda öğrenciye anında bildir
  const olayKaydet = useCallback((tip, bildir = true) => {
    if (!turIdRef.current) return
    api.guvenlikOlayiKaydet(turIdRef.current, tip, kod)
      .then(() => api.guvenlikDurumu(turIdRef.current))
      .then((d) => {
        setGuven(d)
        if (bildir && IHLAL_METNI[tip]) setUyari({ metin: IHLAL_METNI[tip], puan: d.guven_puani, esik: d.esik, zaman: Date.now() })
      })
      .catch(() => {})
  }, [kod])

  useEffect(() => {
    if (!sorular || !basladiMi || tamamlandi) return
    let odakZamanlayici = null
    let sonKopya = 0
    function tamEkranDegisti() {
      const disinda = !document.fullscreenElement
      setTamEkranDisinda(disinda)
      olayKaydet(disinda ? 'tam_ekrandan_cikti' : 'tam_ekrana_geri_donuldu')
    }
    function gorunurlukDegisti() {
      olayKaydet(document.hidden ? 'sekme_degisti' : 'sekmeye_geri_donuldu')
    }
    function odakKaybedildi() {
      // sekme değişince hem blur hem visibilitychange gelir: çift ceza olmasın diye kısa bekleyip kontrol et
      clearTimeout(odakZamanlayici)
      odakZamanlayici = setTimeout(() => { if (!document.hidden) olayKaydet('pencere_odagi_kaybedildi') }, 400)
    }
    function odakKazanildi() {
      clearTimeout(odakZamanlayici)
      olayKaydet('pencere_odagi_geri_kazanildi', false)
    }
    function tusBirakildi(e) {
      if (e.key === 'PrintScreen') olayKaydet('ekran_goruntusu_tusu')
    }
    function kopyalama(e) {
      e.preventDefault()
      if (Date.now() - sonKopya > 8000) { sonKopya = Date.now(); olayKaydet('kopyalama') }
    }
    function sagTik(e) { e.preventDefault() }
    // İkinci ekran (Chrome/Edge: screen.isExtended). Desteklenmeyen tarayıcıda sessizce atlanır.
    function ekranKontrol() {
      if (window.screen?.isExtended) { setIkinciEkran(true); olayKaydet('coklu_ekran') } else setIkinciEkran(false)
    }
    ekranKontrol()
    window.screen?.addEventListener?.('change', ekranKontrol)
    document.addEventListener('fullscreenchange', tamEkranDegisti)
    document.addEventListener('visibilitychange', gorunurlukDegisti)
    window.addEventListener('blur', odakKaybedildi)
    window.addEventListener('focus', odakKazanildi)
    window.addEventListener('keyup', tusBirakildi)
    document.addEventListener('copy', kopyalama)
    document.addEventListener('cut', kopyalama)
    document.addEventListener('contextmenu', sagTik)
    if (turIdRef.current) api.guvenlikDurumu(turIdRef.current).then(setGuven).catch(() => {})
    return () => {
      clearTimeout(odakZamanlayici)
      window.screen?.removeEventListener?.('change', ekranKontrol)
      document.removeEventListener('fullscreenchange', tamEkranDegisti)
      document.removeEventListener('visibilitychange', gorunurlukDegisti)
      window.removeEventListener('blur', odakKaybedildi)
      window.removeEventListener('focus', odakKazanildi)
      window.removeEventListener('keyup', tusBirakildi)
      document.removeEventListener('copy', kopyalama)
      document.removeEventListener('cut', kopyalama)
      document.removeEventListener('contextmenu', sagTik)
    }
  }, [sorular, basladiMi, tamamlandi, olayKaydet])

  useEffect(() => {
    if (!uyari) return
    const z = setTimeout(() => setUyari(null), 6000)
    return () => clearTimeout(z)
  }, [uyari])

  // ------------------------------------------------------------------
  // Kamera kurulumu — izin verilmezse sessizce atlanır, testi bloklamaz
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!sorular || !basladiMi || tamamlandi || kameraRizasi === null) return
    let akis = null

    if (!kameraRizasi) {
      const gonder = () => api.guvenlikOlayiKaydet(turIdRef.current, 'kamera_rizasi_verilmedi', kod).catch(() => {})
      if (turIdRef.current) gonder()
      else setTimeout(gonder, 500)
      return
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      const gonder = () => api.guvenlikOlayiKaydet(turIdRef.current, 'kamera_desteklenmiyor', kod).catch(() => {})
      if (turIdRef.current) gonder()
      else setTimeout(gonder, 500)
      return
    }

    navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } })
      .then((s) => {
        akis = s
        if (videoRef.current) {
          videoRef.current.srcObject = s
          videoRef.current.play().catch(() => {})
          kameraAktifRef.current = true
          setKameraDurumu('acik')
          s.getVideoTracks().forEach((t) => { t.onended = () => { kameraAktifRef.current = false; setKameraDurumu('kapali'); olayKaydet('kamera_kapandi') } })
        }
      })
      .catch(() => {
        kameraAktifRef.current = false
        setKameraDurumu('reddedildi')
        const gonder = () => api.guvenlikOlayiKaydet(turIdRef.current, 'kamera_izni_reddedildi', kod).catch(() => {})
        if (turIdRef.current) gonder()
        else setTimeout(gonder, 500)
      })

    return () => {
      akis?.getTracks().forEach((t) => t.stop())
      kameraAktifRef.current = false
    }
  }, [sorular, basladiMi, tamamlandi, kod, kameraRizasi, olayKaydet])

  const fotografCek = useCallback(() => {
    if (!kameraAktifRef.current || !videoRef.current || !canvasRef.current || !turIdRef.current) return
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video.videoWidth) return
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const base64 = canvas.toDataURL('image/jpeg', 0.7)
    api.guvenlikFotografiKaydet(turIdRef.current, base64, kod).catch(() => {})
  }, [kod])

  useEffect(() => {
    if (!sorular || !basladiMi || tamamlandi || !turId) return
    const zamanlayici = setTimeout(fotografCek, 1500)
    return () => clearTimeout(zamanlayici)
  }, [turId, sorular, basladiMi, tamamlandi, fotografCek])

  useEffect(() => {
    if (aktifIndex > 0 && aktifIndex % FOTOGRAF_ARALIGI_SORU === 0) fotografCek()
  }, [aktifIndex, fotografCek])

  useEffect(() => {
    if (!sorular || !basladiMi || tamamlandi) return
    function kapatmaUyarisi(e) {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', kapatmaUyarisi)
    return () => window.removeEventListener('beforeunload', kapatmaUyarisi)
  }, [sorular, basladiMi, tamamlandi])

  // ------------------------------------------------------------------
  // Kullanıcı aksiyonları
  // ------------------------------------------------------------------
  function sinavdanCik() {
    const uyari = tamamlandi
      ? null
      : 'Değerlendirmeden çıkmak istiyor musun? Verdiğin cevaplar kayıtlı; döndüğünde kaldığın sorudan devam edersin.'
    if (uyari && !window.confirm(uyari)) return
    if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {})
    navigate('/katmanlar')
  }

  async function cevabiGonder(soruId, secenekId, enAzSecenekId = null) {
    setGonderiliyor(true)
    try {
      await (dalMi
        ? api.dalSoruyuCevapla(kod, soruId, secenekId, enAzSecenekId)
        : api.soruyuCevapla(kod, soruId, secenekId, enAzSecenekId))
    } catch (e) {
      setHata(e.detail || 'Cevap kaydedilemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  // cevaplar[soruId]: tek seçimli soruda secenek_id;
  // "en çok / en az" sorusunda { enCok, enAz } nesnesi.
  async function secenekSec(secenekId, soruId) {
    const soru = sorular.find((s) => s.id === soruId)
    if (soru?.cevap_bicimi !== 'encok_enaz') {
      setCevaplar((onceki) => ({ ...onceki, [soruId]: secenekId }))
      await cevabiGonder(soruId, secenekId)
      return
    }
    const mevcut = cevaplar[soruId] || {}
    let yeni
    if (!mevcut.enCok) yeni = { enCok: secenekId, enAz: null }                       // 1. adım: en çok
    else if (secenekId === mevcut.enCok) yeni = { enCok: null, enAz: null }          // en çoka tekrar dokunma: sıfırla
    else if (secenekId === mevcut.enAz) yeni = { enCok: mevcut.enCok, enAz: null }   // en aza tekrar dokunma: geri al
    else yeni = { enCok: mevcut.enCok, enAz: secenekId }                              // 2. adım: en az (değiştirilebilir)
    setCevaplar((onceki) => ({ ...onceki, [soruId]: yeni }))
    if (yeni.enCok && yeni.enAz) await cevabiGonder(soruId, yeni.enCok, yeni.enAz)
  }

  function geriGit() {
    if (aktifIndex > 0) setAktifIndex((i) => i - 1)
  }

  async function ileriGit() {
    if (aktifIndex < sorular.length - 1) {
      setAktifIndex((i) => i + 1)
    } else {
      setGonderiliyor(true)
      try {
        const sonuc = await (dalMi ? api.daliTamamla(kod) : api.katmaniTamamla(kod))
        if (dalMi) {
          // Başka açık dal kaldı mı? Kalmadıysa öğrenci doğrudan bölüm sonuçlarına gider.
          const ozet = await api.durumOzetiGetir().catch(() => null)
          setK5Bekliyor(!!ozet && ozet.k5_acilan_dal_sayisi > ozet.k5_tamamlanan_dal_sayisi)
        }
        setTamamlandi(sonuc)
        if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {})
      } catch (e) {
        setHata(e.detail || 'Katman tamamlanamadı.')
      } finally {
        setGonderiliyor(false)
      }
    }
  }

  // ------------------------------------------------------------------
  // Render — her durumda aynı ortalanmış/logolu dış çerçeve
  // ------------------------------------------------------------------
  return (
    <div style={{
      minHeight: '100vh', width: '100%', display: 'flex', flexDirection: 'column',
      alignItems: 'center', background: 'var(--bg)',
    }}>
      {tamEkranDisinda && <GuvenlikUyariKatmani tamEkranaGeriDon={tamEkranaGec} onErkenBitir={sinavdanCik} />}
      {!tamEkranDisinda && ikinciEkran && basladiMi && !tamamlandi && (
        <div className="sn-ikinci-ekran">🖥️ İkinci bir ekran bağlı görünüyor. Değerlendirme süresince ikinci ekranı çıkar ya da kapat; bu durum kayda geçiyor.</div>
      )}
      {uyari && (
        <div className="sn-uyari" role="alert" key={uyari.zaman}>
          <b>⚠️ {uyari.metin}</b>
          <span>Bu durum kayda geçti. Güven puanın: <b>{uyari.puan}</b>/100 · {uyari.esik}'nin altına düşerse değerlendirmen geçersiz sayılabilir.</span>
        </div>
      )}
      {kameraRizasi && basladiMi && !tamamlandi && <KameraOnizleme videoRef={videoRef} />}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      <SinavBasligi />

      <div className="sn-sayfa">
        {hata ? (
          <div className="bos-durum">{hata}</div>
        ) : !sorular ? (
          <div className="bos-durum">Yükleniyor…</div>
        ) : tamamlandi ? (
          <div className="qwrap" style={{ maxWidth: 640 }}>
            <div className="ph" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 46 }}>{dalMi ? '🌻' : (KATMAN_BILGI[kod]?.ikon || '🎉')}</div>
              <div className="pt">{dalMi ? (dalAdi || kod) : (KATMAN_BILGI[kod]?.ad || kod)} tamamlandı 🎉</div>
              {!dalMi && (() => {
                const n = Number(String(kod).replace(/\D/g, '')) || 0
                return (
                  <div className="bitis-yol">
                    {[1, 2, 3, 4].map((i) => <span key={i} className={i <= n ? 'dolu' : ''}>{i <= n ? '✓' : i}</span>)}
                    <em>{n >= 4 ? 'Dört bölümü de bitirdin!' : n === 2 ? 'Yarıladın, harika gidiyorsun 💪' : `${4 - n} bölüm kaldı`}</em>
                  </div>
                )
              })()}
            </div>
            {tamamlandi.sonuclar.length > 0 && (
              <div className="bitis-one-cikan">
                <div className="bitis-etiket">✨ Bu bölüm senin hakkında ne söyledi?</div>
                <div className="bitis-cipler">
                  {[...tamamlandi.sonuclar].sort((a, b) => b.puan - a.puan).slice(0, 3).map((x) => <span key={x.degisken_id}>{x.degisken_adi}</span>)}
                </div>
                <div className="bitis-alt">Bu üç özellik bu bölümde en çok öne çıkanların. Bölüm önerilerin hepsi bitince bunlara göre hesaplanır.</div>
              </div>
            )}

            {guven && (
              <div className={`sn-sonuc-guven ${guven.guven_puani < guven.esik ? 'kotu' : ''}`}>
                🛡️ Güven puanın: <b>{guven.guven_puani}</b>/100
                {guven.ihlaller.length ? <> · {guven.ihlaller.map((i) => `${i.ad} (${i.sayi})`).join(', ')}</> : ' · ihlal yok, teşekkürler!'}
              </div>
            )}
            {tamamlandi.sonuclar.length === 0 ? (
              <div className="veri-yok-grafik">
                <div className="vg-ikon">📊</div>
                <div className="vg-metin">Bu katman için henüz sonuç hesaplanmadı.</div>
              </div>
            ) : (
              <details className="card bitis-detay">
                <summary>Tüm puanlarını ve ne anlama geldiklerini gör</summary>
                {[...tamamlandi.sonuclar].sort((a, b) => b.puan - a.puan).map((s) => (
                  <DegiskenKarti key={s.degisken_id} s={s} />
                ))}
              </details>
            )}

            {/* [2026-10-03] K5 zorunlu: K4 bitince öğrenci önce açılan dallara (Katmanlar sayfasında listelenir) yönlendirilir */}
            {dalMi ? (
              <button className="btn full" onClick={() => navigate(k5Bekliyor ? '/katmanlar' : '/bolumler')}>
                {k5Bekliyor ? 'Sıradaki Alan Sorularına Geç →' : 'Bölüm Sonuçlarımı Gör →'}
              </button>
            ) : (
              (() => {
                // [2026-10-03] Katmanlar sırayla ilerler: K1 → K2 → K3 → K4 → (K5 alan soruları)
                const n = Number(String(kod).replace(/\D/g, ''))
                const sonraki = !tamamlandi.tum_katmanlar_tamamlandi_mi && n >= 1 && n < 4 ? `K${n + 1}` : null
                return sonraki ? (
                  <>
                    <button className="btn full" onClick={() => navigate(`/katmanlar/${sonraki}`)}>Sıradaki bölüme geç: {KATMAN_BILGI[sonraki]?.ad || sonraki} →</button>
                    <button className="btn sec full" style={{ marginTop: 8 }} onClick={() => navigate('/')}>Şimdilik ara ver — kaldığın yer kayıtlı</button>
                  </>
                ) : (
                  <button className="btn full" onClick={() => navigate('/katmanlar')}>
                    {tamamlandi.tum_katmanlar_tamamlandi_mi ? 'Sana özel derinleşme sorularına geç →' : 'Değerlendirmeye dön'}
                  </button>
                )
              })()
            )}
          </div>
        ) : !basladiMi ? (
          <KatmanTanitimEkrani
            kod={kod} sorular={sorular} onBasla={() => setBasladiMi(true)} cikisYapiliyor={false} devamBilgisi={devamBilgisi}
            kameraRizasi={kameraRizasi} onKameraIzni={async () => {
              try { await api.kvkkGuncelle({ kamera: true }); setKameraRizasi(true) } catch { /* izin kaydedilemedi */ }
            }}
            baslik={dalMi ? (dalAdi || 'Alan Soruları') : undefined}
            altBaslik={dalMi ? 'K5 — sana özel alan sorularına başlıyorsun' : undefined}
          />
        ) : (
          <SoruIcerigiDuzeni
            sorular={sorular}
            aktifIndex={aktifIndex}
            cevaplar={cevaplar}
            gonderiliyor={gonderiliyor}
            kod={kod}
            baslik={dalMi ? (dalAdi || 'Alan Soruları') : undefined}
            onSecenekSec={secenekSec}
            onIleriGit={ileriGit}
            onGeriGit={geriGit}
            onCik={sinavdanCik}
            guven={guven}
            kameraDurumu={kameraRizasi ? kameraDurumu : 'yok'}
          />
        )}
      </div>
    </div>
  )
}


const FILIZLENME_MESAJLARI = [
  'Her cevap, profilini biraz daha netleştiriyor.',
  'Doğru ya da yanlış cevap yok — yalnızca sana en uygun olanı seç.',
  'Az kaldı, kendi yolunu filizlendirmeye devam ediyorsun.',
  'İçtenlikle cevapladığın her soru, daha isabetli bir sonuç demek.',
]

function SoruIcerigiDuzeni({ sorular, aktifIndex, cevaplar, gonderiliyor, kod, baslik, onSecenekSec, onIleriGit, onGeriGit, onCik, guven, kameraDurumu }) {
  const katman = KATMAN_BILGI[kod] || { ikon: '🌻', ad: baslik || kod }
  // [2026-10-10] Mola: uzun bölümlerde (8+ soru) yarıya gelince bir kez kısa nefes molası önerilir
  const yari = Math.floor(sorular.length / 2)
  const [molaGoruldu, setMolaGoruldu] = useState(sorular.length < 8 || aktifIndex > yari)
  if (!molaGoruldu && aktifIndex === yari) {
    return (
      <div className="sn-duzen">
        <div className="mola-kart">
          <div style={{ fontSize: 44 }}>🌿</div>
          <div className="mola-baslik">Yarıyı geçtin!</div>
          <div className="mola-metin">{yari} soruyu cevapladın, {sorular.length - yari} soru kaldı. İstersen gözlerini birkaç saniye dinlendir, omuzlarını gevşet, derin bir nefes al.</div>
          <div className="mola-not">Tam ekrandasın; bu ekranda beklemek kayda geçmez.</div>
          <button className="btn" onClick={() => setMolaGoruldu(true)}>Hazırım, devam →</button>
        </div>
      </div>
    )
  }
  const mesaj = FILIZLENME_MESAJLARI[aktifIndex % FILIZLENME_MESAJLARI.length]
  const puan = guven?.guven_puani ?? 100
  const esik = guven?.esik ?? 50
  const puanSinif = puan < esik ? 'kotu' : puan < esik + 20 ? 'orta' : 'iyi'
  return (
    <div className="sn-duzen">
      <div className="sn-ust">
        <div className="sn-katman"><span>{katman.ikon}</span><b>{katman.ad}</b></div>
        <div className="sn-rozetler">
          <span className={`sn-guven ${puanSinif}`} title={guven?.ihlaller?.length ? guven.ihlaller.map((i) => `${i.ad}: ${i.sayi}`).join(' · ') : 'İhlal yok'}>
            🛡️ Güven puanı <b>{puan}</b>
          </span>
          <span className={`sn-kamera-rozet ${kameraDurumu}`}>{kameraDurumu === 'acik' ? '📷 Kamera açık' : kameraDurumu === 'yok' ? '📷 Kamera kapalı' : '📷 Kamera kapalı'}</span>
          <button className="sn-cik" onClick={onCik}>Çık ✕</button>
        </div>
      </div>
      <SoruIcerigi
        sorular={sorular} aktifIndex={aktifIndex} cevaplar={cevaplar} gonderiliyor={gonderiliyor}
        kod={kod} onSecenekSec={onSecenekSec} onIleriGit={onIleriGit} onGeriGit={onGeriGit}
      />
      <div className="sn-mesaj">🌱 {mesaj}</div>
    </div>
  )
}

function SoruIcerigi({ sorular, aktifIndex, cevaplar, gonderiliyor, onSecenekSec, onIleriGit, onGeriGit }) {
  const aktifSoru = sorular[aktifIndex]
  const ikiliMi = aktifSoru.cevap_bicimi === 'encok_enaz'
  const cevap = cevaplar[aktifSoru.id]
  const secilenSecenek = ikiliMi ? null : cevap
  const enCok = ikiliMi ? cevap?.enCok : null
  const enAz = ikiliMi ? cevap?.enAz : null
  const cevapTamam = ikiliMi ? !!(enCok && enAz) : !!secilenSecenek
  const cevaplanan = sorular.filter((s) => { const c = cevaplar[s.id]; return c && (typeof c !== 'object' || (c.enCok && c.enAz)) }).length
  const ilerlemeYuzde = Math.round((cevaplanan / sorular.length) * 100)
  const tip = SORU_TIPI[aktifSoru.soru_tipi]
  const kutupMu = aktifSoru.soru_tipi === 'kutup' || aktifSoru.soru_tipi === 'likert'

  return (
    <div className="qwrap sn-soru">
      <div className="qmeta sn-meta">
        <span>Soru <b>{aktifIndex + 1}</b> / {sorular.length}</span>
        <span>%{ilerlemeYuzde} tamamlandı</span>
      </div>
      <div className="qtrack sn-track"><div className="qfill" style={{ width: `${ilerlemeYuzde}%` }} /></div>
      {tip && <div className="sn-tip-etiket" title={tip.uzun}>{tip.ikon} {tip.ad} · <span>{ikiliMi ? 'Önce EN ÇOK, sonra EN AZ uyan şıkkı seç.' : tip.kisa}</span></div>}
      <div className="qtext sn-metin" key={aktifSoru.id}>{aktifSoru.soru_metni}</div>
      {ikiliMi && (
        <div className={`sn-adim ${!enCok ? 'bir' : !enAz ? 'iki' : 'tamam'}`}>
          {!enCok ? '1. adım: Sana EN ÇOK uyan şıkkı seç.' : !enAz ? '2. adım: Şimdi sana EN AZ uyan şıkkı seç.' : '✓ Tamam. Değiştirmek için şıklara tekrar dokunabilirsin.'}
        </div>
      )}
      <div className={`qopts sn-secenekler${kutupMu && aktifSoru.secenekler.length <= 5 ? ' olcek' : ''}`}>
        {aktifSoru.secenekler.map((sec) => {
          const cokMu = ikiliMi && enCok === sec.id
          const azMi = ikiliMi && enAz === sec.id
          return (
            <button key={sec.id} className={`qopt sn-secenek${secilenSecenek === sec.id || cokMu ? ' sel' : ''}${azMi ? ' az' : ''}`}
              onClick={() => onSecenekSec(sec.id, aktifSoru.id)} disabled={gonderiliyor}>
              {ikiliMi && (cokMu || azMi) && <span className={`sn-isaret ${cokMu ? 'cok' : 'az'}`}>{cokMu ? 'EN ÇOK' : 'EN AZ'}</span>}
              <span>{sec.secenek_metni}</span>
            </button>
          )
        })}
      </div>
      <div className="qnav sn-nav">
        <button className="btn sec" onClick={onGeriGit} disabled={aktifIndex === 0 || gonderiliyor}>← Önceki soru</button>
        <button className="btn" onClick={onIleriGit} disabled={!cevapTamam || gonderiliyor}>
          {gonderiliyor ? <span className="spin" /> : aktifIndex < sorular.length - 1 ? 'Sonraki soru →' : 'Katmanı tamamla ✓'}
        </button>
      </div>
    </div>
  )
}
