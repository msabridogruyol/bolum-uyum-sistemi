import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const KATMAN_IKON = { K1: '🌱', K2: '🌿', K3: '🍃', K4: '🌸' }
const ANA_KATMANLAR = ['K1', 'K2', 'K3', 'K4']

export default function AnaSayfa() {
  const [ozet, setOzet] = useState(null)
  const [katmanlar, setKatmanlar] = useState(null)
  const [siralama, setSiralama] = useState(null)
  const [profil, setProfil] = useState(null)
  const [katmanSonuclari, setKatmanSonuclari] = useState(null)
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
    // Katman sonuçlarını her durumda tek tek çek — tur tamamlanmamış olsa bile
    // bireysel katmanlar bitmiş olabilir.
    Promise.all(ANA_KATMANLAR.map((kod) => api.katmanSonucuGetir(kod).then((r) => [kod, r]).catch(() => [kod, null])))
      .then((liste) => {
        const harita = {}
        liste.forEach(([kod, r]) => {
          harita[kod] = (r && r.tamamlandi_mi && r.sonuclar.length)
            ? { puanOrtalama: Math.round(r.sonuclar.reduce((a, s) => a + s.puan, 0) / r.sonuclar.length), sonuclar: r.sonuclar }
            : null
        })
        setKatmanSonuclari(harita)
      })
  }, [ozet])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar || !ozet || !katmanSonuclari) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const ilkAd = (profil?.ad_soyad || 'Öğrenci').split(' ')[0]
  const tamamlananYuzde = katmanlar.length ? Math.round((ozet.tamamlanan_katman_sayisi / ozet.toplam_ana_katman_sayisi) * 100) : 0

  // Gerçek "profil skoru" — en yüksek bölüm uyum puanı
  const profilSkoru = siralama && siralama.length > 0 ? Math.round(siralama[0].toplam_uyum) : null

  // Gerçek "etiketler" — tüm katmanlardaki en yüksek puanlı 3 değişken (uydurma tip adı değil)
  const tumSonuclar = ANA_KATMANLAR.flatMap((kod) => katmanSonuclari[kod]?.sonuclar || [])
  const enYuksek3 = [...tumSonuclar].sort((a, b) => b.puan - a.puan).slice(0, 3)

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

      {/* --- Profil kartı: avatar + isim + etiketler + skor + katman satırı, hepsi bir arada --- */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
          <div className="av" style={{ width: 56, height: 56, fontSize: 24, overflow: 'hidden' }}>
            {profil?.profil_foto_base64
              ? <img src={profil.profil_foto_base64} alt="Profil" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              : '🎓'}
          </div>
          <div style={{ flex: 1, minWidth: 160 }}>
            <div style={{ fontSize: 17, fontWeight: 700 }}>{profil?.ad_soyad || 'Öğrenci'}</div>
            <div style={{ fontSize: 12, color: 'var(--tx3)', marginBottom: 8 }}>
              {[profil?.okul, profil?.sinif].filter(Boolean).join(' · ') || 'Okul bilgisi eklenmedi'}
            </div>
            {enYuksek3.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {enYuksek3.map((s) => (
                  <span key={s.degisken_id} className="bdg bdg-prog">{s.degisken_adi}</span>
                ))}
              </div>
            )}
          </div>
          {profilSkoru !== null && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10.5, color: 'var(--tx3)', marginBottom: 2 }}>En yüksek uyum</div>
              <div style={{ fontFamily: 'var(--fd)', fontSize: 32, fontWeight: 700, color: 'var(--pu)', lineHeight: 1 }}>{profilSkoru}</div>
              <div style={{ fontSize: 10, color: 'var(--tx3)' }}>/ 100</div>
            </div>
          )}
          <button className="btn sec" onClick={() => navigate('/profil')}>Profili Düzenle</button>
        </div>

        {/* --- Katman özet satırı, aynı kartın içinde --- */}
        <div style={{ display: 'flex', gap: 8, marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--bor)', flexWrap: 'wrap' }}>
          {ANA_KATMANLAR.map((kod) => {
            const k = katmanlar.find((x) => x.kod === kod)
            const sonuc = katmanSonuclari[kod]
            return (
              <div
                key={kod}
                onClick={() => navigate(`/sonuc/${kod}`)}
                style={{ flex: '1 1 90px', textAlign: 'center', cursor: 'pointer' }}
              >
                <div style={{ fontSize: 18 }}>{KATMAN_IKON[kod]}</div>
                <div style={{ fontSize: 9.5, color: 'var(--tx3)', marginTop: 3, fontWeight: 600 }}>{k?.ad?.split('/')[0]?.split('&')[0]?.trim() || kod}</div>
                <div style={{ fontSize: 13, fontWeight: 700, marginTop: 1, color: sonuc ? 'var(--gr)' : k?.durum === 'devam_ediyor' ? 'var(--pu)' : 'var(--tx3)' }}>
                  {sonuc ? `${sonuc.puanOrtalama}%` : k?.durum === 'devam_ediyor' ? 'Devam ediyor' : 'Henüz başlanmadı'}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* --- Önerilen bölümler — başlık her zaman görünür --- */}
      <div className="ct" style={{ marginTop: 20 }}>Sana Önerilen Bölümler</div>
      {!ozet.tur_tamamlandi_mi ? (
        <div className="card" style={{ background: 'linear-gradient(135deg,var(--pul),var(--sur))', borderColor: 'var(--pu)' }}>
          <div className="veri-yok-grafik" style={{ padding: '18px 10px' }}>
            <div className="vg-ikon">🌱</div>
            <div className="vg-metin">
              Bölüm önerilerin, K1-K4 katmanlarının **tamamı** bitince burada görünecek.
              {' '}Şu an {ozet.tamamlanan_katman_sayisi}/{ozet.toplam_ana_katman_sayisi} katman tamamlandı.
            </div>
            <button className="btn" style={{ marginTop: 14 }} onClick={() => navigate('/katmanlar')}>
              {ozet.tamamlanan_katman_sayisi === 0 ? 'Yolculuğuna Başla' : 'Kaldığın Yerden Devam Et'} →
            </button>
          </div>
        </div>
      ) : siralama === null ? (
        <div className="bos-durum">Yükleniyor…</div>
      ) : siralama.length === 0 ? (
        <div className="veri-yok-grafik">
          <div className="vg-ikon">🌱</div>
          <div className="vg-metin">Henüz önerilecek bölüm hesaplanmadı.</div>
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
            {siralama.map((s, i) => (
              <div key={s.bolum_id} className="ob-card" style={{ cursor: 'default' }}>
                <div className="ob-top">
                  <div className={`ob-rank${i < 3 ? ' top' : ''}`}>{i + 1}</div>
                  <div className="ob-body">
                    <div className="ob-name">{s.bolum_adi}</div>
                    <div className="mini-ilerleme-track" style={{ width: '100%', marginTop: 6 }}>
                      <div className="mini-ilerleme-fill" style={{ width: `${s.toplam_uyum}%`, background: 'var(--pu)' }} />
                    </div>
                  </div>
                  <div className="ob-score">%{Math.round(s.toplam_uyum)}</div>
                </div>
              </div>
            ))}
          </div>
          <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/koclugu')}>
            Bölüm Karşılaştırmasına Git →
          </button>
        </>
      )}
    </div>
  )
}
