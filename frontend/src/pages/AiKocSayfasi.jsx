import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'

export default function AiKocSayfasi() {
  const [oturumId, setOturumId] = useState(null)
  const [mesajlar, setMesajlar] = useState([])
  const [girdiMetni, setGirdiMetni] = useState('')
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [baslatiliyor, setBaslatiliyor] = useState(true)
  const sonaKaydirRef = useRef(null)

  useEffect(() => {
    api.aiKocOturumBaslat()
      .then((veri) => setOturumId(veri.oturum_id))
      .catch((e) => setHata(e.detail || 'Asistan şu anda kullanılamıyor.'))
      .finally(() => setBaslatiliyor(false))
  }, [])

  useEffect(() => {
    sonaKaydirRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mesajlar])

  async function mesajGonder(e) {
    e.preventDefault()
    const metin = girdiMetni.trim()
    if (!metin || gonderiliyor || !oturumId) return

    setMesajlar((m) => [...m, { rol: 'ogrenci', icerik: metin }])
    setGirdiMetni('')
    setGonderiliyor(true)
    setHata(null)

    try {
      const cevap = await api.aiKocMesajGonder(oturumId, metin)
      setMesajlar((m) => [...m, { rol: 'asistan', icerik: cevap.asistan_yaniti }])
      if (cevap.oturum_kapandi_mi) {
        setHata('Bu oturum tamamlandı — sayfayı yenileyip yeni bir sohbet başlatabilirsin.')
      }
    } catch (err) {
      setHata(err.detail || 'Mesaj gönderilemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  return (
    <div className="pg" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 80px)' }}>
      <div className="ph" style={{ marginBottom: 12 }}>
        <div className="pt">🧭 Kariyer Koçun</div>
        <div className="ps">Sonuçların, hedef bölümün ve gelişim alanların hakkında dilediğin gibi sohbet edebilirsin.</div>
      </div>

      {baslatiliyor ? (
        <div className="bos-durum">Hazırlanıyor…</div>
      ) : hata && mesajlar.length === 0 ? (
        <div className="bos-durum">{hata}</div>
      ) : (
        <>
          <div style={{ flex: 1, overflowY: 'auto', padding: '8px 4px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {mesajlar.length === 0 && (
              <div className="veri-yok-grafik">
                <div className="vg-ikon">💬</div>
                <div className="vg-metin">Merhaba! Sonuçların, hedef bölümün ya da nereden başlayacağını bilemediğin bir konu hakkında konuşmak ister misin?</div>
              </div>
            )}
            {mesajlar.map((m, i) => (
              <div
                key={i}
                style={{
                  alignSelf: m.rol === 'ogrenci' ? 'flex-end' : 'flex-start',
                  maxWidth: '75%',
                  background: m.rol === 'ogrenci' ? 'var(--pu)' : 'var(--sur2)',
                  color: m.rol === 'ogrenci' ? '#fff' : 'var(--tx)',
                  padding: '12px 16px',
                  borderRadius: 16,
                  borderBottomRightRadius: m.rol === 'ogrenci' ? 4 : 16,
                  borderBottomLeftRadius: m.rol === 'asistan' ? 4 : 16,
                  fontSize: 14,
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                }}
              >
                {m.icerik}
              </div>
            ))}
            {gonderiliyor && (
              <div style={{ alignSelf: 'flex-start', color: 'var(--tx3)', fontSize: 13, padding: '4px 16px' }}>
                <span className="spin" /> yazıyor…
              </div>
            )}
            <div ref={sonaKaydirRef} />
          </div>

          {hata && mesajlar.length > 0 && (
            <div className="auth-error" style={{ marginBottom: 8 }}>{hata}</div>
          )}

          <form onSubmit={mesajGonder} style={{ display: 'flex', gap: 8, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
            <input
              className="auth-input"
              style={{ flex: 1 }}
              value={girdiMetni}
              onChange={(e) => setGirdiMetni(e.target.value)}
              placeholder="Bir şey yaz..."
              disabled={gonderiliyor || !oturumId}
              autoFocus
            />
            <button className="btn" type="submit" disabled={gonderiliyor || !girdiMetni.trim() || !oturumId}>
              Gönder
            </button>
          </form>
        </>
      )}
    </div>
  )
}
