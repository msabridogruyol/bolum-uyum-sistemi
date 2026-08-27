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

  if (hata && !bolumler) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!bolumler) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Bölümler</div>
        <div className="ps">Taslak → Test Ediliyor → Yayında akışı. Her geçiş gerekçe gerektirir ve audit log'a yazılır.</div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}

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
        {bolumler.map((b) => (
          <div key={b.id} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{b.ad}</div>
              <span className={`bdg ${DURUM_RENK[b.durum]}`}>{DURUM_ETIKET[b.durum]}</span>
              {b.test_notu && <div className="ld" style={{ marginTop: 6 }}>{b.test_notu}</div>}
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
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
          </div>
        ))}
      </div>
    </div>
  )
}
