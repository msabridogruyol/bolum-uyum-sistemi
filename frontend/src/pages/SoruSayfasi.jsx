import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

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

function GuvenlikUyariKatmani({ tamEkranaGeriDon }) {
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
    </div>
  )
}

export default function SoruSayfasi() {
  const { kod } = useParams()
  const navigate = useNavigate()

  const [sorular, setSorular] = useState(null)
  const [turId, setTurId] = useState(null)
  const [aktifIndex, setAktifIndex] = useState(0)
  const [cevaplar, setCevaplar] = useState({})
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [tamamlandi, setTamamlandi] = useState(null)
  const [tamEkranDisinda, setTamEkranDisinda] = useState(false)

  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const kameraAktifRef = useRef(false)
  const turIdRef = useRef(null)  // olay/fotoğraf gönderirken en güncel tur_id'yi kullanmak için

  useEffect(() => { turIdRef.current = turId }, [turId])

  // ------------------------------------------------------------------
  // Katman başlatma
  // ------------------------------------------------------------------
  useEffect(() => {
    setSorular(null)
    setAktifIndex(0)
    setCevaplar({})
    setTamamlandi(null)
    api.katmaniBaslat(kod)
      .then((veri) => {
        setSorular(veri.sorular)
        setTurId(veri.tur_id)
      })
      .catch((e) => setHata(e.detail || 'Katman başlatılamadı.'))
  }, [kod])

  // ------------------------------------------------------------------
  // Tam ekrana geçiş + çıkış/geri dönüş yönetimi
  // ------------------------------------------------------------------
  const tamEkranaGec = useCallback(() => {
    const el = document.documentElement
    if (el.requestFullscreen) el.requestFullscreen().catch(() => {})
  }, [])

  useEffect(() => {
    if (sorular && !tamamlandi) tamEkranaGec()
  }, [sorular, tamamlandi, tamEkranaGec])

  useEffect(() => {
    function tamEkranDegisti() {
      const disinda = !document.fullscreenElement
      setTamEkranDisinda(disinda)
      if (turIdRef.current) {
        api.guvenlikOlayiKaydet(
          turIdRef.current,
          disinda ? 'tam_ekrandan_cikti' : 'tam_ekrana_geri_donuldu',
          kod,
        ).catch(() => {})
      }
    }
    function gorunurlukDegisti() {
      if (!turIdRef.current) return
      api.guvenlikOlayiKaydet(
        turIdRef.current,
        document.hidden ? 'sekme_degisti' : 'sekmeye_geri_donuldu',
        kod,
      ).catch(() => {})
    }
    function odakKaybedildi() {
      if (!turIdRef.current) return
      api.guvenlikOlayiKaydet(turIdRef.current, 'pencere_odagi_kaybedildi', kod).catch(() => {})
    }
    function odakKazanildi() {
      if (!turIdRef.current) return
      api.guvenlikOlayiKaydet(turIdRef.current, 'pencere_odagi_geri_kazanildi', kod).catch(() => {})
    }

    document.addEventListener('fullscreenchange', tamEkranDegisti)
    document.addEventListener('visibilitychange', gorunurlukDegisti)
    window.addEventListener('blur', odakKaybedildi)
    window.addEventListener('focus', odakKazanildi)
    return () => {
      document.removeEventListener('fullscreenchange', tamEkranDegisti)
      document.removeEventListener('visibilitychange', gorunurlukDegisti)
      window.removeEventListener('blur', odakKaybedildi)
      window.removeEventListener('focus', odakKazanildi)
    }
  }, [kod])

  // ------------------------------------------------------------------
  // Kamera kurulumu — izin verilmezse sessizce atlanır, testi bloklamaz
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!sorular || tamamlandi) return
    let akis = null

    if (!navigator.mediaDevices?.getUserMedia) {
      // Tarayıcı hiç desteklemiyor — test bloklanmaz, yalnızca loglanır
      if (turIdRef.current) api.guvenlikOlayiKaydet(turIdRef.current, 'kamera_desteklenmiyor', kod).catch(() => {})
      else setTimeout(() => api.guvenlikOlayiKaydet(turIdRef.current, 'kamera_desteklenmiyor', kod).catch(() => {}), 500)
      return
    }

    navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } })
      .then((s) => {
        akis = s
        if (videoRef.current) {
          videoRef.current.srcObject = s
          videoRef.current.play().catch(() => {})
          kameraAktifRef.current = true
        }
      })
      .catch(() => {
        // İzin reddedildi ya da cihaz hatası — test bloklanmaz, yalnızca loglanır
        kameraAktifRef.current = false
        const gonder = () => api.guvenlikOlayiKaydet(turIdRef.current, 'kamera_izni_reddedildi', kod).catch(() => {})
        if (turIdRef.current) gonder()
        else setTimeout(gonder, 500)
      })

    return () => {
      akis?.getTracks().forEach((t) => t.stop())
      kameraAktifRef.current = false
    }
  }, [sorular, tamamlandi, kod])

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

  // Katman başında bir kare + her FOTOGRAF_ARALIGI_SORU soruda bir kare
  useEffect(() => {
    if (!sorular || tamamlandi || !turId) return
    const zamanlayici = setTimeout(fotografCek, 1500)  // kameranın açılmasına küçük bir pay
    return () => clearTimeout(zamanlayici)
  }, [turId, sorular, tamamlandi, fotografCek])

  useEffect(() => {
    if (aktifIndex > 0 && aktifIndex % FOTOGRAF_ARALIGI_SORU === 0) fotografCek()
  }, [aktifIndex, fotografCek])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!sorular) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  if (tamamlandi) {
    const siraliSonuclar = [...tamamlandi.sonuclar].sort((a, b) => b.puan - a.puan)

    return (
      <div className="pg">
        <div className="qwrap" style={{ maxWidth: 640 }}>
          <div className="ph">
            <div className="pt">{kod} tamamlandı 🎉</div>
            <div className="ps">Bu katmandaki değişken puanların ve ne anlama geldikleri:</div>
          </div>

          {siraliSonuclar.length === 0 ? (
            <div className="veri-yok-grafik">
              <div className="vg-ikon">📊</div>
              <div className="vg-metin">Bu katman için henüz sonuç hesaplanmadı.</div>
            </div>
          ) : (
            <div className="card">
              {siraliSonuclar.map((s) => <DegiskenKarti key={s.degisken_id} s={s} />)}
            </div>
          )}

          <button className="btn full" onClick={() => navigate(tamamlandi.tum_katmanlar_tamamlandi_mi ? '/sonuc/genel' : '/katmanlar')}>
            {tamamlandi.tum_katmanlar_tamamlandi_mi ? 'Sonuçlarımı Gör →' : 'Katmanlara Dön'}
          </button>
        </div>
      </div>
    )
  }

  const aktifSoru = sorular[aktifIndex]
  const secilenSecenek = cevaplar[aktifSoru.id]
  const ilerlemeYuzde = Math.round((aktifIndex / sorular.length) * 100)

  async function secenekSec(secenekId) {
    setCevaplar((onceki) => ({ ...onceki, [aktifSoru.id]: secenekId }))
    setGonderiliyor(true)
    try {
      await api.soruyuCevapla(kod, aktifSoru.id, secenekId)
    } catch (e) {
      setHata(e.detail || 'Cevap kaydedilemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  async function ileriGit() {
    if (aktifIndex < sorular.length - 1) {
      setAktifIndex((i) => i + 1)
    } else {
      setGonderiliyor(true)
      try {
        const sonuc = await api.katmaniTamamla(kod)
        setTamamlandi(sonuc)
        if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {})
      } catch (e) {
        setHata(e.detail || 'Katman tamamlanamadı.')
      } finally {
        setGonderiliyor(false)
      }
    }
  }

  return (
    <div className="pg">
      {tamEkranDisinda && <GuvenlikUyariKatmani tamEkranaGeriDon={tamEkranaGec} />}

      {/* Kamera önizlemesi görünmez tutulur — yalnızca kare yakalamak için */}
      <video ref={videoRef} muted playsInline style={{ position: 'fixed', width: 1, height: 1, opacity: 0, pointerEvents: 'none' }} />
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      <div className="qwrap">
        <div className="qmeta">
          <span>Soru {aktifIndex + 1} / {sorular.length}</span>
          <span>{kod}</span>
        </div>
        <div className="qtrack"><div className="qfill" style={{ width: `${ilerlemeYuzde}%` }} /></div>
        <div className="qtext">{aktifSoru.soru_metni}</div>
        <div className="qopts">
          {aktifSoru.secenekler.map((sec) => (
            <button
              key={sec.id}
              className={`qopt${secilenSecenek === sec.id ? ' sel' : ''}`}
              onClick={() => secenekSec(sec.id)}
              disabled={gonderiliyor}
            >
              {sec.secenek_metni}
            </button>
          ))}
        </div>
        <div className="qnav">
          <button className="btn sec" onClick={() => navigate('/katmanlar')}>← Katmanlara dön</button>
          <button className="btn" onClick={ileriGit} disabled={!secilenSecenek || gonderiliyor}>
            {gonderiliyor ? <span className="spin" /> : aktifIndex < sorular.length - 1 ? 'Sonraki soru →' : 'Katmanı tamamla'}
          </button>
        </div>
      </div>
    </div>
  )
}
