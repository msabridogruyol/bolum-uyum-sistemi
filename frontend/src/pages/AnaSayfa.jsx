import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const KATMAN_IKON = { K1: '🌱', K2: '🌿', K3: '🍃', K4: '🌸', K5: '🌻' }

export default function AnaSayfa() {
  const [ozet, setOzet] = useState(null)
  const [katmanlar, setKatmanlar] = useState(null)
  const [siralama, setSiralama] = useState(null)
  const [profil, setProfil] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.durumOzetiGetir().then(setOzet).catch(() => {})
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail))
    api.profilGetir().then(setProfil).catch(() => {})
  }, [])

  useEffect(() => {
    if (!ozet) return
    if (ozet.tur_tamamlandi_mi) {
      api.siralamaGetir(10).then(setSiralama).catch(() => setSiralama([]))
    } else {
      setSiralama([])
    }
  }, [ozet])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar || !ozet) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const ilkAd = (profil?.ad_soyad || 'Öğrenci').split(' ')[0]
  const tamamlananYuzde = katmanlar.length ? Math.round((ozet.tamamlanan_katman_sayisi / ozet.toplam_ana_katman_sayisi) * 100) : 0

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Merhaba, {ilkAd} 👋</div>
        <div className="ps">
          {ozet.tur_tamamlandi_mi
            ? 'Tüm katmanlar tamamlandı — işte senin bölüm uyum profilin.'
            : `Yolculuğunun %${tamamlananYuzde}'ini tamamladın.`}
        </div>
      </div>

      {/* --- Profil kartı --- */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
        <div className="av" style={{ width: 56, height: 56, fontSize: 24, overflow: 'hidden' }}>
          {profil?.profil_foto_base64
            ? <img src={profil.profil_foto_base64} alt="Profil" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            : '🎓'}
        </div>
        <div style={{ flex: 1, minWidth: 160 }}>
          <div style={{ fontSize: 17, fontWeight: 700 }}>{profil?.ad_soyad || 'Öğrenci'}</div>
          <div style={{ fontSize: 12, color: 'var(--tx3)' }}>
            {[profil?.okul, profil?.sinif].filter(Boolean).join(' · ') || 'Okul bilgisi eklenmedi'}
          </div>
        </div>
        <button className="btn sec" onClick={() => navigate('/profil')}>Profili Düzenle</button>
      </div>

      {/* --- Katman durumu satırı --- */}
      <div className="card">
        <div className="ct">Yolculuk Durumun</div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {katmanlar.map((k) => (
            <div
              key={k.id}
              onClick={() => navigate(k.durum === 'baslamadi' && k.sira > 1 ? '/katmanlar' : `/katmanlar/${k.kod}`)}
              style={{
                flex: '1 1 100px', textAlign: 'center', padding: '14px 10px', borderRadius: 14, cursor: 'pointer',
                background: k.durum === 'tamamlandi' ? 'var(--grl)' : k.durum === 'devam_ediyor' ? 'var(--pul)' : 'var(--sur2)',
              }}
            >
              <div style={{ fontSize: 20 }}>{KATMAN_IKON[k.kod] || '•'}</div>
              <div style={{ fontSize: 10.5, color: 'var(--tx2)', marginTop: 4, fontWeight: 600 }}>{k.kod}</div>
              <div style={{ fontSize: 12, fontWeight: 700, marginTop: 2, color: k.durum === 'tamamlandi' ? 'var(--gr)' : k.durum === 'devam_ediyor' ? 'var(--pu)' : 'var(--tx3)' }}>
                {k.durum === 'tamamlandi' ? 'Tamamlandı' : k.durum === 'devam_ediyor' ? 'Devam Ediyor' : 'Başlamadı'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* --- Önerilen bölümler --- */}
      {ozet.tur_tamamlandi_mi ? (
        <>
          <div className="ct" style={{ marginTop: 20 }}>Sana Önerilen Bölümler</div>
          {siralama === null ? (
            <div className="bos-durum">Yükleniyor…</div>
          ) : siralama.length === 0 ? (
            <div className="veri-yok-grafik">
              <div className="vg-ikon">🌱</div>
              <div className="vg-metin">Henüz önerilecek bölüm hesaplanmadı.</div>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
              {siralama.map((s, i) => (
                <div key={s.bolum_id} className={`ob-card${i < 3 ? '' : ''}`} style={{ cursor: 'default' }}>
                  <div className="ob-top">
                    <div className={`ob-rank${i < 3 ? ' top' : ''}`}>{i + 1}</div>
                    <div className="ob-body"><div className="ob-name">{s.bolum_adi}</div></div>
                    <div className="ob-score">%{Math.round(s.toplam_uyum)}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
          <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/sonuc')}>
            Tüm Sonuçlarımı Gör →
          </button>
        </>
      ) : (
        <div className="card" style={{ background: 'linear-gradient(135deg,var(--pul),var(--sur))', borderColor: 'var(--pu)' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--pu)', marginBottom: 6 }}>SIRADAKİ ADIM</div>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 14 }}>
            {ozet.tamamlanan_katman_sayisi === 0
              ? 'Yolculuğuna ilk katmanla başla'
              : 'Kaldığın yerden devam et'}
          </div>
          <button className="btn" onClick={() => navigate('/katmanlar')}>Yol Haritama Git →</button>
        </div>
      )}
    </div>
  )
}
