import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { BolumBilgiIcerik } from '../components/BolumBilgiPenceresi'
import FavoriYildiz from '../components/FavoriYildiz'
import { KarsilastirDugmesi } from '../components/KarsilastirSepeti'

const ORNEK_ARAMALAR = ['Tıp', 'Bilgisayar Mühendisliği', 'Psikoloji', 'Hukuk', 'İşletme', 'Mimarlık']

export default function KesfetSayfasi({ gomulu = false }) {
  const [sorgu, setSorgu] = useState('')
  const [sonuclar, setSonuclar] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [secili, setSecili] = useState(null)
  const navigate = useNavigate()
  const [parametreler] = useSearchParams()
  const hedefBolumId = Number(parametreler.get('bolum')) || null

  // [2026-10-04] Haftalık keşif görevinden gelindiyse: bölümü ara ve doğrudan aç
  useEffect(() => {
    const ara = parametreler.get('ara')
    if (ara) aramaYap(ara)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!hedefBolumId || !sonuclar || secili) return
    const bulunan = sonuclar.find((s) => s.bolum_id === hedefBolumId)
    if (bulunan) setSecili(bulunan)
  }, [sonuclar]) // eslint-disable-line react-hooks/exhaustive-deps

  async function aramaYap(terim) {
    const t = (terim ?? sorgu).trim()
    if (t.length < 2) {
      setHata('Arama terimi en az 2 karakter olmalı.')
      return
    }
    setHata(null)
    setYukleniyor(true)
    setSorgu(t)
    setSecili(null)
    try {
      setSonuclar(await api.kesfetAra(t))
    } catch (err) {
      setHata(err.detail || 'Arama yapılamadı.')
    } finally {
      setYukleniyor(false)
    }
  }

  function ara(e) {
    e.preventDefault()
    aramaYap()
  }

  return (
    <div className={`pg${secili ? ' pg-genis' : ''}`}>
      {!gomulu && <div className="ph">
        <div className="pt">Tüm Bölümleri Keşfet</div>
        <div className="ps">301 bölümün tamamı elinin altında — bir bölüme tıkla; tanıtımını, mesleklerini, yetkinlik profilini ve üniversitelerini incele.</div>
      </div>}

      <form onSubmit={ara} style={{ display: 'flex', gap: 8, marginBottom: sonuclar ? 20 : 14 }}>
        <input
          className="auth-input"
          style={{ flex: 1 }}
          value={sorgu}
          onChange={(e) => setSorgu(e.target.value)}
          placeholder="örn. Tıp, Ekonometri, Hukuk..."
          autoFocus={!gomulu}
        />
        <button className="btn" type="submit" disabled={yukleniyor}>
          {yukleniyor ? <span className="spin" /> : '🔍 Ara'}
        </button>
      </form>

      {hata && <div className="auth-error">{hata}</div>}

      {!sonuclar && !yukleniyor && (
        <div>
          <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--tx3)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.04em' }}>
            Popüler Aramalar
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 24 }}>
            {ORNEK_ARAMALAR.map((ornek) => (
              <button
                key={ornek}
                type="button"
                className="bdg bdg-prog"
                style={{ fontSize: 13, padding: '8px 16px', cursor: 'pointer', border: 'none' }}
                onClick={() => aramaYap(ornek)}
              >
                {ornek}
              </button>
            ))}
          </div>
          <div className="veri-yok-grafik">
            <div className="vg-ikon">🔍</div>
            <div className="vg-metin">Yukarıdan bir örneğe tıkla ya da yukarıya kendi aramanı yaz.</div>
          </div>
        </div>
      )}

      {sonuclar && sonuclar.length === 0 && (
        <div className="veri-yok-grafik">
          <div className="vg-ikon">🌱</div>
          <div className="vg-metin">"{sorgu}" için sonuç bulunamadı — farklı bir kelimeyle dene.</div>
        </div>
      )}

      {sonuclar && sonuclar.length > 0 && (
        <>
          <div className="ps" style={{ marginBottom: 12, fontSize: 12 }}>{sonuclar.length} sonuç bulundu — birine tıkla</div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginBottom: secili ? 20 : 0 }}>
            {sonuclar.map((s) => (
              <div
                key={s.bolum_id}
                className="ob-card"
                onClick={() => setSecili(s)}
                style={{ borderColor: secili?.bolum_id === s.bolum_id ? 'var(--pu)' : undefined, background: secili?.bolum_id === s.bolum_id ? 'var(--pul)' : undefined }}
              >
                <div className="ob-top">
                  <div className="ob-body"><div className="ob-name">{s.bolum_adi}</div></div>
                  <div className="ob-score">{s.toplam_uyum !== null ? `%${Math.round(s.toplam_uyum)}` : '—'}</div>
                  <FavoriYildiz id={s.bolum_id} ad={s.bolum_adi} />
                  <KarsilastirDugmesi id={s.bolum_id} ad={s.bolum_adi} />
                </div>
              </div>
            ))}
          </div>

          {secili && (
            <>
              <div style={{ height: 1, background: 'var(--bor)', margin: '20px 0' }} />
              <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 14, flexWrap: 'wrap', marginBottom: 14 }}>
                <div>
                  <div style={{ fontSize: 11, color: 'var(--tx3)', fontWeight: 700, textTransform: 'uppercase' }}>Seçilen Bölüm</div>
                  <div style={{ fontSize: 13, color: 'var(--tx2)', marginTop: 2 }}>
                    {secili.toplam_uyum !== null ? 'Testine göre bu bölümle uyumun:' : 'Uyumunu görmek için katmanları tamamla.'}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  {secili.toplam_uyum !== null && (
                    <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--pu)', fontFamily: 'var(--fd)' }}>%{Math.round(secili.toplam_uyum)}</div>
                  )}
                  <button className="btn" style={{ fontSize: 13 }} onClick={() => navigate(`/profil?hedef=${secili.bolum_id}#hedef`)}>Hedef Olarak Seç →</button>
                </div>
              </div>
              <BolumBilgiIcerik gomulu bolumId={secili.bolum_id} ad={secili.bolum_adi} />
            </>
          )}
        </>
      )}
    </div>
  )
}
