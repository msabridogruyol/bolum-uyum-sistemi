import { useEffect, useState, useCallback } from 'react'
import { api } from '../../api/client'

const GECISLER = { taslak: ['test_ediliyor'], test_ediliyor: ['yayinda', 'taslak'], yayinda: [] }
const DURUM_ETIKET = { taslak: 'Taslak', test_ediliyor: 'Test Ediliyor', yayinda: 'Yayında' }
const DURUM_RENK = { taslak: 'bdg-lock', test_ediliyor: 'bdg-prog', yayinda: 'bdg-done' }

export default function BolumlerSayfasi() {
  const [bolumler, setBolumler] = useState(null)
  const [hata, setHata] = useState(null)
  const [gerekceModal, setGerekceModal] = useState(null) // { bolumId, yeniDurum }
  const [gerekceMetni, setGerekceMetni] = useState('')
  const [aramaMetni, setAramaMetni] = useState('')

  // açıklama düzenleme
  const [duzenlemeId, setDuzenlemeId] = useState(null)
  const [duzenlemeMetni, setDuzenlemeMetni] = useState('')
  const [kaydediliyor, setKaydediliyor] = useState(false)

  const yukle = useCallback(() => {
    api.bolumleriListele().then(setBolumler).catch((e) => setHata(e.detail || 'Bölümler yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  async function gecisiOnayla() {
    try {
      await api.bolumDurumDegistir(gerekceModal.bolumId, gerekceModal.yeniDurum, gerekceMetni)
      setGerekceModal(null)
      setGerekceMetni('')
      yukle()
    } catch (err) {
      setHata(err.detail || 'Durum değiştirilemedi.')
    }
  }

  function duzenlemeyeBasla(b) {
    setDuzenlemeId(b.id)
    setDuzenlemeMetni(b.kisa_aciklama || '')
  }

  async function aciklamayiKaydet(bolumId) {
    if (!duzenlemeMetni.trim()) {
      setHata('Açıklama boş olamaz.')
      return
    }
    setKaydediliyor(true)
    try {
      await api.bolumAciklamaGuncelle(bolumId, duzenlemeMetni.trim())
      setDuzenlemeId(null)
      yukle()
    } catch (err) {
      setHata(err.detail || 'Açıklama kaydedilemedi.')
    } finally {
      setKaydediliyor(false)
    }
  }

  if (hata && !bolumler) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!bolumler) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const filtrelenmis = bolumler.filter((b) => b.ad.toLowerCase().includes(aramaMetni.toLowerCase()))

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Bölümler</div>
        <div className="ps">Taslak → Test Ediliyor → Yayında akışı ve öğrenciye gösterilen kısa açıklamalar buradan yönetilir.</div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}

      <input
        className="auth-input"
        style={{ marginBottom: 14 }}
        value={aramaMetni}
        onChange={(e) => setAramaMetni(e.target.value)}
        placeholder="Bölüm ara..."
      />

      {gerekceModal && (
        <div className="card" style={{ borderColor: 'var(--pu)', background: 'var(--pul)' }}>
          <div className="ct">Gerekçe Gerekli</div>
          <textarea
            className="auth-input"
            style={{ width: '100%', minHeight: 70, marginBottom: 10 }}
            value={gerekceMetni}
            onChange={(e) => setGerekceMetni(e.target.value)}
            placeholder="Bu geçişin gerekçesini yaz..."
          />
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn" onClick={gecisiOnayla} disabled={!gerekceMetni.trim()}>Onayla</button>
            <button className="btn sec" onClick={() => setGerekceModal(null)}>Vazgeç</button>
          </div>
        </div>
      )}

      <div className="ll">
        {filtrelenmis.map((b) => (
          <div key={b.id} className="lc" style={{ cursor: 'default', alignItems: 'flex-start' }}>
            <div className="lb-wrap">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <div className="lt">{b.ad}</div>
                <span className={`bdg ${DURUM_RENK[b.durum]}`}>{DURUM_ETIKET[b.durum]}</span>
              </div>

              {duzenlemeId === b.id ? (
                <div style={{ marginTop: 4 }}>
                  <textarea
                    className="auth-input"
                    style={{ width: '100%', minHeight: 60, fontFamily: 'var(--fn)' }}
                    value={duzenlemeMetni}
                    onChange={(e) => setDuzenlemeMetni(e.target.value)}
                    placeholder="Öğrenciye Keşfet ekranında gösterilecek kısa açıklama..."
                  />
                  <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <button className="btn" onClick={() => aciklamayiKaydet(b.id)} disabled={kaydediliyor}>
                      {kaydediliyor ? <span className="spin" /> : 'Kaydet'}
                    </button>
                    <button className="btn sec" onClick={() => setDuzenlemeId(null)}>Vazgeç</button>
                  </div>
                </div>
              ) : (
                <div
                  onClick={() => duzenlemeyeBasla(b)}
                  style={{ fontSize: 12.5, color: b.kisa_aciklama ? 'var(--tx2)' : 'var(--tx3)', cursor: 'pointer', fontStyle: b.kisa_aciklama ? 'normal' : 'italic' }}
                >
                  {b.kisa_aciklama || 'Açıklama yok — eklemek için tıkla'} <span style={{ color: 'var(--pu)', fontSize: 11 }}>✏️ düzenle</span>
                </div>
              )}

              {b.test_notu && duzenlemeId !== b.id && (
                <div className="ld" style={{ marginTop: 6 }}>Not: {b.test_notu}</div>
              )}
            </div>

            {duzenlemeId !== b.id && (
              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                {GECISLER[b.durum].map((yeniDurum) => (
                  <button
                    key={yeniDurum}
                    className="btn sec"
                    onClick={() => { setGerekceModal({ bolumId: b.id, yeniDurum }); setGerekceMetni('') }}
                  >
                    → {DURUM_ETIKET[yeniDurum]}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {filtrelenmis.length === 0 && <div className="bos-durum">Sonuç bulunamadı.</div>}
      </div>
    </div>
  )
}
