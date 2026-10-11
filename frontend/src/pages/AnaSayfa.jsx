import { useEffect, useState } from 'react'
import GecersizTurUyarisi from '../components/GecersizTurUyarisi'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import HaftalikGorevler from '../components/HaftalikGorevler'
import { useBolumBilgi } from '../context/BolumBilgiContext'
import AnaSayfaGrafikleri from '../components/AnaSayfaGrafikleri'
import BugunPaneli from '../components/BugunPaneli'
import { modulAcikMi, modulleriYukle, useModuller } from '../yardimci/moduller'

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
  const [motivasyon, setMotivasyon] = useState(null)   // [2026-10-10] YKS sayacı, haftalık mesaj
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()
  const { ac: bolumBilgisiAc } = useBolumBilgi()
  const acik = useModuller()
  const kocluk = acik('kocluk')

  useEffect(() => {
    api.durumOzetiGetir().then(setOzet).catch(() => {})
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail))
    api.profilGetir().then(setProfil).catch(() => {})
    api.motivasyonGetir().then(setMotivasyon).catch(() => {})
    api.k5Durumu().then(setK5Durum).catch(() => setK5Durum({ acilan: [], ilgi_gosterilen: [] }))
    api.aktifHedefGetir().then((h) => {
      setHedef(h)
      // [2026-10-10] Koçluk okulun paketinde yoksa plan istenmez
      if (h) modulleriYukle().then(() => { if (modulAcikMi('kocluk')) api.gelisimPlaniGetir().then(setPlan).catch(() => setPlan(false)) })   // false = alınamadı (yükleniyor değil)
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

  const tumSonuclar = ANA_KATMANLAR.flatMap((kod) => katmanSonuclari[kod]?.sonuclar || [])

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
              ? 'Tüm katmanları bitirdin. İşte bölüm uyum profilin.'
              : `Yolculuğunun %${tamamlananYuzde}'ini tamamladın.`}
          </div>
          <div className="as-kimlik" onClick={() => navigate('/profilim')} title="Profilime git">
            <span className="as-kimlik-av">
              {profil?.profil_foto_base64 ? <img src={profil.profil_foto_base64} alt="" /> : '🎓'}
            </span>
            <b>{profil?.ad_soyad || 'Öğrenci'}</b>
            <span className="as-kimlik-ayrac">·</span>
            <span>{[profil?.okul, profil?.sinif].filter(Boolean).join(' · ') || 'Okul bilgisi eklenmedi'}</span>
            {profilSkoru !== null && <><span className="as-kimlik-ayrac">·</span><span>En yüksek uyum <b className="as-kimlik-skor">{profilSkoru}</b>/100</span></>}
            <span className="as-kimlik-git">Profilim →</span>
          </div>
        </div>

        {hedefBolumAdi && (
          <div className="hedef-kart" onClick={() => navigate(kocluk ? '/koclugu' : '/bolumler')} title={kocluk ? 'Hedef bölüm koçluğuna git' : 'Bölümlerime git'}>
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

      <GecersizTurUyarisi ozet={ozet} />

      <BugunPaneli ozet={ozet} katmanlar={katmanlar} hedef={hedef} plan={plan} motivasyon={motivasyon} kocluk={kocluk} />

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
              Yeni değerlendirme turun açıldı. Profilini güncellemek için değerlendirmeyi yeniden yapabilirsin.
            </div>
          </div>
          <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--gr)' }}>Başla →</span>
        </div>
      )}

      {/* [2026-10-04] Her hafta 3 görev — sistemi düzenli kullanımın merkezi */}
      {kocluk && <HaftalikGorevler />}

      {/* [2026-10-11] Güç Dağılımın ve Rozetler kaldırıldı; öğrenci bilgisi başlığın altında küçük şeritte */}

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
