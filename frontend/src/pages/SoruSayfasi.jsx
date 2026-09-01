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
        Bölüm Uyum Sistemi
      </span>
    </div>
  )
}

// Sağ üstte, öğrencinin kendini görebildiği canlı kamera önizlemesi
function KameraOnizleme({ videoRef }) {
  return (
    <div style={{
      position: 'fixed', top: 16, right: 16, zIndex: 500,
      width: 120, height: 90, borderRadius: 12, overflow: 'hidden',
      border: '2px solid var(--bor2)', boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
      background: 'var(--sur2)',
    }}>
      <video ref={videoRef} muted playsInline style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)' }} />
    </div>
  )
}

// ============================================================
// Katman Tanıtım / Onay Ekranı — her katman başında bir kez gösterilir
// ============================================================
const ONAY_METNI = 'ONAYLIYORUM'

function KatmanTanitimEkrani({ kod, sorular, onBasla, cikisYapiliyor }) {
  const [yaziliOnay, setYaziliOnay] = useState('')
  const katman = KATMAN_BILGI[kod] || { ikon: '🌱', ad: kod }

  const likertSayisi = sorular.filter((s) => s.soru_tipi === 'likert').length
  const sjtSayisi = sorular.filter((s) => s.soru_tipi === 'sjt').length
  const tahminiDakika = Math.max(1, Math.ceil((likertSayisi * 15 + sjtSayisi * 30) / 60))
  const onayGecerli = yaziliOnay.trim() === ONAY_METNI

  return (
    <div className="qwrap" style={{ maxWidth: 620, width: '100%', minHeight: 620 }}>
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{ fontSize: 42, marginBottom: 10 }}>{katman.ikon}</div>
        <div style={{ fontFamily: 'var(--fd)', fontSize: 22, fontWeight: 700 }}>{katman.ad}</div>
        <div style={{ fontSize: 12.5, color: 'var(--tx3)', fontWeight: 600, marginTop: 3 }}>{kod} katmanına başlıyorsun</div>
      </div>

      <div className="sg" style={{ marginBottom: 18 }}>
        <div className="sc">
          <div className="sl">Toplam Soru</div>
          <div className="sv pu">{sorular.length}</div>
        </div>
        <div className="sc">
          <div className="sl">Tahmini Süre</div>
          <div className="sv pu">~{tahminiDakika} dk</div>
        </div>
        <div className="sc">
          <div className="sl">Soru Tipleri</div>
          <div className="sv" style={{ fontSize: 14, lineHeight: 1.5 }}>
            {likertSayisi > 0 && <div>{likertSayisi} Likert</div>}
            {sjtSayisi > 0 && <div>{sjtSayisi} Durum Sorusu</div>}
          </div>
        </div>
      </div>

      <div style={{
        background: 'var(--tll)', border: '1.5px solid var(--tl)', borderRadius: 16,
        padding: '16px 18px', marginBottom: 20, fontSize: 12.5, color: 'var(--tx)', lineHeight: 1.7,
      }}>
        <div style={{ fontWeight: 700, marginBottom: 6, color: 'var(--tl)' }}>📋 Bilmen Gerekenler</div>
        <div>• Bu değerlendirme <b>tam ekran</b> modunda yapılacak — tam ekrandan çıkarsan uyarı alırsın.</div>
        <div>• <b>Kameran</b>, kimlik doğrulama amacıyla aralıklarla fotoğraf çekecek (izin verirsen).</div>
        <div>• Sekme değiştirme ve pencere odağı kaybı gibi olaylar kayıt altına alınır.</div>
        <div>• Katmandan erken çıkarsan, o ana kadarki ilerlemen kaybolur — baştan başlaman gerekir.</div>
        <div>• Doğru/yanlış cevap yok — içtenlikle, düşünmeden hızlıca cevapla.</div>
      </div>

      <div className="auth-field">
        <label className="auth-label">
          Devam etmek için aşağıya <b>büyük harflerle tam olarak</b> "{ONAY_METNI}" yazın:
        </label>
        <input
          className="auth-input"
          value={yaziliOnay}
          onChange={(e) => setYaziliOnay(e.target.value)}
          placeholder={ONAY_METNI}
          autoComplete="off"
        />
      </div>

      <button className="btn full" disabled={!onayGecerli || cikisYapiliyor} onClick={onBasla} style={{ marginTop: 4 }}>
        {cikisYapiliyor ? <span className="spin" /> : 'Değerlendirmeye Başla →'}
      </button>
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
  const [basladiMi, setBasladiMi] = useState(false)  // tanıtım/onay ekranı geçildi mi

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
    setBasladiMi(false)
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
    if (sorular && basladiMi && !tamamlandi) tamEkranaGec()
  }, [sorular, basladiMi, tamamlandi, tamEkranaGec])

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
    if (!sorular || !basladiMi || tamamlandi) return
    let akis = null

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
        }
      })
      .catch(() => {
        kameraAktifRef.current = false
        const gonder = () => api.guvenlikOlayiKaydet(turIdRef.current, 'kamera_izni_reddedildi', kod).catch(() => {})
        if (turIdRef.current) gonder()
        else setTimeout(gonder, 500)
      })

    return () => {
      akis?.getTracks().forEach((t) => t.stop())
      kameraAktifRef.current = false
    }
  }, [sorular, basladiMi, tamamlandi, kod])

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
      : 'Şu anki katmandan çıkarsan bu oturumdaki ilerlemen kaybolur — kaldığın soruya değil, katmanın başına dönmen gerekir. Yine de çıkmak istiyor musun?'
    if (uyari && !window.confirm(uyari)) return
    if (document.fullscreenElement) document.exitFullscreen?.().catch(() => {})
    navigate('/katmanlar')
  }

  async function secenekSec(secenekId, soruId) {
    setCevaplar((onceki) => ({ ...onceki, [soruId]: secenekId }))
    setGonderiliyor(true)
    try {
      await api.soruyuCevapla(kod, soruId, secenekId)
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

  // ------------------------------------------------------------------
  // Render — her durumda aynı ortalanmış/logolu dış çerçeve
  // ------------------------------------------------------------------
  return (
    <div style={{
      minHeight: '100vh', width: '100%', display: 'flex', flexDirection: 'column',
      alignItems: 'center', background: 'var(--bg)',
    }}>
      {tamEkranDisinda && <GuvenlikUyariKatmani tamEkranaGeriDon={tamEkranaGec} onErkenBitir={sinavdanCik} />}
      <KameraOnizleme videoRef={videoRef} />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      <SinavBasligi />

      <div className="pg" style={{ width: '100%', display: 'flex', justifyContent: 'center' }}>
        {hata ? (
          <div className="bos-durum">{hata}</div>
        ) : !sorular ? (
          <div className="bos-durum">Yükleniyor…</div>
        ) : tamamlandi ? (
          <div className="qwrap" style={{ maxWidth: 640 }}>
            <div className="ph">
              <div className="pt">{kod} tamamlandı 🎉</div>
              <div className="ps">Bu katmandaki değişken puanların ve ne anlama geldikleri:</div>
            </div>

            {tamamlandi.sonuclar.length === 0 ? (
              <div className="veri-yok-grafik">
                <div className="vg-ikon">📊</div>
                <div className="vg-metin">Bu katman için henüz sonuç hesaplanmadı.</div>
              </div>
            ) : (
              <div className="card">
                {[...tamamlandi.sonuclar].sort((a, b) => b.puan - a.puan).map((s) => (
                  <DegiskenKarti key={s.degisken_id} s={s} />
                ))}
              </div>
            )}

            <button className="btn full" onClick={() => navigate(tamamlandi.tum_katmanlar_tamamlandi_mi ? '/sonuc/genel' : '/katmanlar')}>
              {tamamlandi.tum_katmanlar_tamamlandi_mi ? 'Sonuçlarımı Gör →' : 'Katmanlara Dön'}
            </button>
          </div>
        ) : !basladiMi ? (
          <KatmanTanitimEkrani kod={kod} sorular={sorular} onBasla={() => setBasladiMi(true)} cikisYapiliyor={false} />
        ) : (
          <SoruIcerigiDuzeni
            sorular={sorular}
            aktifIndex={aktifIndex}
            cevaplar={cevaplar}
            gonderiliyor={gonderiliyor}
            kod={kod}
            onSecenekSec={secenekSec}
            onIleriGit={ileriGit}
            onCik={sinavdanCik}
          />
        )}
      </div>
    </div>
  )
}

const KATMAN_BILGI = {
  K1: { ikon: '🌱', ad: 'Değerler / Motivasyon' },
  K2: { ikon: '🌿', ad: 'Kişilik & Çalışma Tarzı' },
  K3: { ikon: '🍃', ad: 'İş Ortamı & Profesyonel Yetkinlik' },
  K4: { ikon: '🌸', ad: 'Alan Eğilimi & Bilişsel Stil' },
  K5: { ikon: '🌻', ad: 'Derinleşme' },
}

const FILIZLENME_MESAJLARI = [
  'Her cevap, profilini biraz daha netleştiriyor.',
  'Doğru ya da yanlış cevap yok — yalnızca sana en uygun olanı seç.',
  'Az kaldı, kendi yolunu filizlendirmeye devam ediyorsun.',
  'İçtenlikle cevapladığın her soru, daha isabetli bir sonuç demek.',
]

function SoruIcerigiDuzeni({ sorular, aktifIndex, cevaplar, gonderiliyor, kod, onSecenekSec, onIleriGit, onCik }) {
  const katman = KATMAN_BILGI[kod] || { ikon: '🌱', ad: kod }
  const kalanSoru = sorular.length - aktifIndex - 1
  const mesaj = FILIZLENME_MESAJLARI[aktifIndex % FILIZLENME_MESAJLARI.length]

  return (
    <div style={{ display: 'flex', gap: 18, alignItems: 'flex-start', flexWrap: 'wrap', justifyContent: 'center', width: '100%' }}>
      <SoruIcerigi
        sorular={sorular} aktifIndex={aktifIndex} cevaplar={cevaplar} gonderiliyor={gonderiliyor}
        kod={kod} onSecenekSec={onSecenekSec} onIleriGit={onIleriGit} onCik={onCik}
      />

      {/* Sağ panel — katman bilgisi + ilerleme, tek kompakt kart halinde */}
      <div style={{ width: 220, flexShrink: 0 }}>
        <div className="card" style={{ textAlign: 'center', padding: '16px 14px', marginBottom: 10 }}>
          <div style={{ fontSize: 22, marginBottom: 2 }}>{katman.ikon}</div>
          <div style={{ fontFamily: 'var(--fd)', fontSize: 12.5, fontWeight: 700, lineHeight: 1.3 }}>{katman.ad}</div>
          <div style={{ fontSize: 10, color: 'var(--tx3)', fontWeight: 600, marginTop: 6, paddingTop: 8, borderTop: '1px solid var(--bor)' }}>
            <span style={{ fontFamily: 'var(--fd)', fontSize: 20, fontWeight: 700, color: 'var(--pu)' }}>{aktifIndex + 1}</span>
            {' '}/ {sorular.length} soru · {kalanSoru > 0 ? `${kalanSoru} kaldı` : 'son soru 🎉'}
          </div>
        </div>

        <div style={{
          background: 'var(--grl)', borderRadius: 14, padding: '10px 13px',
          fontSize: 11.5, color: 'var(--gr)', fontWeight: 600, lineHeight: 1.4,
          display: 'flex', gap: 6, alignItems: 'flex-start',
        }}>
          <span>🌱</span>
          <span>{mesaj}</span>
        </div>
      </div>
    </div>
  )
}

function SoruIcerigi({ sorular, aktifIndex, cevaplar, gonderiliyor, kod, onSecenekSec, onIleriGit, onCik }) {
  const aktifSoru = sorular[aktifIndex]
  const secilenSecenek = cevaplar[aktifSoru.id]
  const ilerlemeYuzde = Math.round((aktifIndex / sorular.length) * 100)

  return (
    <div className="qwrap" style={{ maxWidth: 700, width: '100%', paddingTop: 24, minHeight: 560 }}>
      <div className="qmeta" style={{ fontSize: 13 }}>
        <span>Soru {aktifIndex + 1} / {sorular.length}</span>
        <span>{kod}</span>
      </div>
      <div className="qtrack" style={{ height: 8 }}><div className="qfill" style={{ width: `${ilerlemeYuzde}%` }} /></div>
      <div className="qtext" style={{ fontSize: 23, minHeight: 100, display: 'flex', alignItems: 'center' }}>{aktifSoru.soru_metni}</div>
      <div className="qopts" style={{ gap: 10 }}>
        {aktifSoru.secenekler.map((sec) => (
          <button
            key={sec.id}
            className={`qopt${secilenSecenek === sec.id ? ' sel' : ''}`}
            onClick={() => onSecenekSec(sec.id, aktifSoru.id)}
            disabled={gonderiliyor}
            style={{ padding: '14px 18px', fontSize: 14.5 }}
          >
            {sec.secenek_metni}
          </button>
        ))}
      </div>
      <div className="qnav">
        <button className="btn sec" onClick={onCik} style={{ padding: '13px 22px', fontSize: 15 }}>← Katmanlara dön</button>
        <button className="btn" onClick={onIleriGit} disabled={!secilenSecenek || gonderiliyor} style={{ padding: '13px 26px', fontSize: 15 }}>
          {gonderiliyor ? <span className="spin" /> : aktifIndex < sorular.length - 1 ? 'Sonraki soru →' : 'Katmanı tamamla'}
        </button>
      </div>
    </div>
  )
}
