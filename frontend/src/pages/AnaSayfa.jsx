import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import HaftalikGorevler from '../components/HaftalikGorevler'
import { useBolumBilgi } from '../context/BolumBilgiContext'
import Sayac from '../components/Sayac'
import AnaSayfaGrafikleri from '../components/AnaSayfaGrafikleri'
import BugunPaneli, { Rozetler } from '../components/BugunPaneli'

const ANA_KATMANLAR = ['K1', 'K2', 'K3', 'K4']

export default function AnaSayfa() {
  const [ozet, setOzet] = useState(null)
  const [katmanlar, setKatmanlar] = useState(null)
  const [siralama, setSiralama] = useState(null)
  const [profil, setProfil] = useState(null)
  const [katmanSonuclari, setKatmanSonuclari] = useState(null)
  const [k5Durum, setK5Durum] = useState(null)
  const [hedef, setHedef] = useState(null)
  const [plan, setPlan] = useState(null)
  const [motivasyon, setMotivasyon] = useState(null)   // [2026-10-10] YKS sayacı, haftalık mesaj, rozetler
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()
  const { ac: bolumBilgisiAc } = useBolumBilgi()

  useEffect(() => {
    api.durumOzetiGetir().then(setOzet).catch(() => {})
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail))
    api.profilGetir().then(setProfil).catch(() => {})
    api.motivasyonGetir().then(setMotivasyon).catch(() => {})
    api.k5Durumu().then(setK5Durum).catch(() => setK5Durum({ acilan: [], ilgi_gosterilen: [] }))
    api.aktifHedefGetir().then((h) => {
      setHedef(h)
      if (h) api.gelisimPlaniGetir().then(setPlan).catch(() => setPlan(false))   // false = alınamadı (yükleniyor değil)
    }).catch(() => setHedef(null))
  }, [])

  useEffect(() => {
    if (!ozet) return
    if (ozet.tur_tamamlandi_mi) {
      api.siralamaGetir(8).then(setSiralama).catch(() => setSiralama([]))
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
  if (!katmanlar || !ozet || !katmanSonuclari || !k5Durum) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const ilkAd = (profil?.ad_soyad || 'Öğrenci').split(' ')[0]
  const tamamlananYuzde = katmanlar.length ? Math.round((ozet.tamamlanan_katman_sayisi / ozet.toplam_ana_katman_sayisi) * 100) : 0

  // K5 — dal bazlı, açılan dalların ortalama puanı (varsa)
  const k5OrtalamaPuan = k5Durum.acilan.length > 0
    ? Math.round(k5Durum.acilan.reduce((a, d) => a + d.puan, 0) / k5Durum.acilan.length)
    : null

  // Gerçek "profil skoru" — en yüksek bölüm uyum puanı
  const profilSkoru = siralama && siralama.length > 0 ? Math.round(siralama[0].toplam_uyum) : null

  // Gerçek "etiketler" — tüm katmanlardaki en yüksek puanlı 3 değişken (uydurma tip adı değil)
  const tumSonuclar = ANA_KATMANLAR.flatMap((kod) => katmanSonuclari[kod]?.sonuclar || [])
  const enYuksek3 = [...tumSonuclar].sort((a, b) => b.puan - a.puan).slice(0, 3)

  // Güç dağılımı — güçlü/orta/gelişim sayıları (gerçek puanlardan)
  const guclu = tumSonuclar.filter((s) => s.puan >= 70).length
  const gelisimSayisi = tumSonuclar.filter((s) => s.puan < 40).length
  const orta = tumSonuclar.length - guclu - gelisimSayisi
  const toplamBoyut = tumSonuclar.length || 1 // 0'a bölünmeyi önle

  const hedefBolumAdi = hedef?.bolum_adi || null
  const hedefUniversite = profil?.hedef_universite || null

  // Yeniden değerlendirme zamanı geldi mi? (sonraki_tur_tarihi geçmişse)
  const yenidenDegerlendirmeHazir = Boolean(
    ozet.sonraki_tur_tarihi && new Date(ozet.sonraki_tur_tarihi) <= new Date()
  )

  return (
    <div className="pg pg-genis">
      <div className="ph anasayfa-baslik">
        <div className="ab-metin">
          <div className="pt">Merhaba, {ilkAd} 👋</div>
          <div className="ps">
            {ozet.tur_tamamlandi_mi
              ? 'Tüm katmanlar tamamlandı — işte senin bölüm uyum profilin.'
              : `Yolculuğunun %${tamamlananYuzde}'ini tamamladın.`}
          </div>
        </div>

        {hedefBolumAdi && (
          <div className="hedef-kart" onClick={() => navigate('/koclugu')} title="Hedef bölüm koçluğuna git">
            <div style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.85)', letterSpacing: 0.6, textTransform: 'uppercase' }}>
              🎯 Hedef
            </div>
            <div style={{ fontSize: 19, fontWeight: 800, color: '#fff', marginTop: 3, lineHeight: 1.25 }}>
              {hedefBolumAdi}
            </div>
            {hedefUniversite && (
              <div style={{ fontSize: 14, fontWeight: 700, color: 'rgba(255,255,255,0.92)', marginTop: 3 }}>
                {hedefUniversite}
              </div>
            )}
          </div>
        )}
      </div>

      <BugunPaneli ozet={ozet} katmanlar={katmanlar} hedef={hedef} plan={plan} motivasyon={motivasyon} />

      {yenidenDegerlendirmeHazir && (
        <div
          onClick={() => navigate('/katmanlar')}
          style={{
            display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer',
            background: 'var(--grl)', border: '1.5px solid var(--gr)', borderRadius: 16,
            padding: '14px 20px', marginBottom: 20,
          }}
        >
          <span style={{ fontSize: 22 }}>🔔</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--gr)' }}>
              Yeniden değerlendirme zamanın geldi!
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 2 }}>
              90 günlük bekleme süresi doldu — profilini tazelemek için tekrar değerlendirilebilirsin.
            </div>
          </div>
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--gr)' }}>Başla →</span>
        </div>
      )}

      {/* [2026-10-04] Her hafta 3 görev — sistemi düzenli kullanımın merkezi */}
      <HaftalikGorevler />

      {/* [2026-10-09] Üst sıra: profil + güç dağılımı + katman ortalamaları; öneriler altta tam genişlikte */}
      <div className="anasayfa-ust">
          {/* --- Profil kartı --- */}
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
                  <div style={{ fontFamily: 'var(--fd)', fontSize: 32, fontWeight: 700, color: 'var(--pu)', lineHeight: 1 }}><Sayac deger={profilSkoru} /></div>
                  <div style={{ fontSize: 10, color: 'var(--tx3)' }}>/ 100</div>
                </div>
              )}
              <button className="btn sec" onClick={() => navigate('/profilim')}>Profilim →</button>
            </div>

          </div>

          <div className="card" style={{ marginBottom: 0 }}>
            <div className="ct">Güç Dağılımın</div>
            {tumSonuclar.length === 0 ? (
              <div className="taslak-onizleme">
                <div className="taslak-onizleme-icerik">
                  <div className="donut-wrap">
                    <div className="donut" style={{ background: 'conic-gradient(var(--sur2) 0deg 360deg)' }} />
                    <div className="donut-legend">
                      <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--sur2)' }} /><span className="donut-legend-etiket">Güçlü</span></div>
                      <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--sur2)' }} /><span className="donut-legend-etiket">Orta</span></div>
                      <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--sur2)' }} /><span className="donut-legend-etiket">Gelişim</span></div>
                    </div>
                  </div>
                </div>
                <div className="taslak-onizleme-overlay">
                  <div className="to-metin" style={{ fontSize: 11.5 }}>Katmanlar tamamlandıkça burada dolacak</div>
                </div>
              </div>
            ) : (
              <div className="donut-wrap">
                <div
                  className="donut"
                  style={{
                    background: `conic-gradient(var(--gr) 0deg ${(guclu / toplamBoyut) * 360}deg, var(--pu) ${(guclu / toplamBoyut) * 360}deg ${((guclu + orta) / toplamBoyut) * 360}deg, var(--am) ${((guclu + orta) / toplamBoyut) * 360}deg 360deg)`,
                  }}
                >
                  <div className="donut-ortasi">
                    <div className="sayi"><Sayac deger={toplamBoyut} /></div>
                    <div className="etiket">BOYUT</div>
                  </div>
                </div>
                <div className="donut-legend">
                  <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--gr)' }} /><span className="donut-legend-etiket">Güçlü (70+)</span><span className="donut-legend-sayi" style={{ color: 'var(--gr)' }}>{guclu}</span></div>
                  <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--pu)' }} /><span className="donut-legend-etiket">Orta (40-69)</span><span className="donut-legend-sayi" style={{ color: 'var(--pu)' }}>{orta}</span></div>
                  <div className="donut-legend-satir"><div className="donut-legend-nokta" style={{ background: 'var(--am)' }} /><span className="donut-legend-etiket">Gelişim (&lt;40)</span><span className="donut-legend-sayi" style={{ color: 'var(--am)' }}>{gelisimSayisi}</span></div>
                </div>
              </div>
            )}
          </div>

          {/* [2026-10-10] Koçluk kartı yerine rozetler: sıradaki adım artık en üstte "Bugün" panelinde */}
          <Rozetler motivasyon={motivasyon} />
      </div>

      {/* [2026-10-09] Tam genişlikte grafik satırı: katman profili · en güçlü yönler · bölüm uyum sıralaması */}
      {tumSonuclar.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <AnaSayfaGrafikleri
            katmanVerisi={[...ANA_KATMANLAR.map((kod) => ({ kod, deger: katmanSonuclari[kod]?.puanOrtalama ?? null })),
              ...(k5OrtalamaPuan !== null ? [{ kod: 'K5', deger: k5OrtalamaPuan }] : [])]}
            gucluYonler={[...tumSonuclar].sort((a, b) => b.puan - a.puan).slice(0, 6).map((s) => ({ ad: s.degisken_adi, deger: Math.round(s.puan) }))}
            siralama={siralama}
            onBolumAc={bolumBilgisiAc}
          />
        </div>
      )}

      {/* [2026-10-10] 10'lu öneri kartları kaldırıldı (grafikteki uyum sıralaması + Bölümler sayfası ile tekrar ediyordu) */}
      {ozet.tur_tamamlandi_mi && (
        <div className="as-baglantilar">
          <button type="button" onClick={() => navigate('/bolumler')}><span>🌟</span><b>Sana uygun bölümler</b><small>Nedenleriyle birlikte</small></button>
          <button type="button" onClick={() => navigate('/bolumler/karsilastir')}><span>⚖️</span><b>Karşılaştır</b><small>2-3 bölümü yan yana koy</small></button>
          <button type="button" onClick={() => navigate('/bolumler/tum')}><span>🔍</span><b>Tüm bölümler</b><small>301 bölümü keşfet</small></button>
          <button type="button" onClick={() => navigate('/profilim')}><span>🧭</span><b>Profilim</b><small>Güçlü yönlerin, katmanların</small></button>
        </div>
      )}
    </div>
  )
}
