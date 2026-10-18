import { useEffect, useState } from 'react'
import GecersizTurUyarisi from '../components/GecersizTurUyarisi'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import HaftalikGorevler from '../components/HaftalikGorevler'
import { useBolumBilgi } from '../context/BolumBilgiContext'
import { gucluMu } from '../yardimci/seviye'
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
  if (!katmanlar || !ozet || !katmanSonuclari || !k5Durum) return <div className="pg"><div className="bos-durum yukleniyor">Yükleniyor…</div></div>

  const ilkAd = (profil?.ad_soyad || 'Öğrenci').split(' ')[0]
  const tamamlananYuzde = katmanlar.length ? Math.round((ozet.tamamlanan_katman_sayisi / ozet.toplam_ana_katman_sayisi) * 100) : 0


  // [2026-10-18] Profil özeti: güçlü yönler (62+, değerler ve P4 hariç) ve en önem verilen değerler.
  // Katman ortalaması gösterilmez (katman içi puanlar göreli, ortalama hep ≈50).
  const tumSonuclar = ANA_KATMANLAR.flatMap((kod) => (katmanSonuclari[kod]?.sonuclar || []).map((s) => ({ ...s, katmanKod: kod })))
  const degerMi = (s) => s.katmanKod === 'K1' || String(s.degisken_kod || '').startsWith('D')
  const gucluYonler = tumSonuclar.filter((s) => !degerMi(s) && s.degisken_kod !== 'P4' && gucluMu(s.puan)).sort((a, b) => b.puan - a.puan).slice(0, 3)
  const onemliDegerler = tumSonuclar.filter(degerMi).sort((a, b) => b.puan - a.puan).slice(0, 3)

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
            <span className="as-kimlik-git">Profilim →</span>
          </div>
          {/* [2026-10-11] Kendi aktiflik serin: son 14 gün (sistemi açtığın günler) */}
          {motivasyon?.aktiflik && (
            <div className="as-aktif" title="Sistemi açtığın günler (her gün bir kez sayılır)">
              <span className="as-aktif-noktalar" aria-hidden="true">
                {motivasyon.aktiflik.takvim.map((g) => <i key={g.gun} className={g.aktif ? 'aktif' : ''} />)}
              </span>
              <span>
                Son 2 haftada <b>{motivasyon.aktiflik.aktif_gun} gün</b> buradaydın
                {motivasyon.aktiflik.seri > 1 ? <> · <b>{motivasyon.aktiflik.seri} gündür</b> üst üste 🔥</> : ''}
              </span>
            </div>
          )}
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

      {/* [2026-10-17] Sistemin ana işi: bölüm uyumu + hedef bölümle karşılaştırma / koçluk. Diğer araçlardan önce ve belirgin. */}
      {ozet.tur_tamamlandi_mi && siralama && siralama.length > 0 && (
        <section className="as-cekirdek" aria-label="Bölüm uyumun ve koçluğun">
          <div className="as-cekirdek-kutu">
            <div className="as-cekirdek-ust">🌟 Sana en uygun bölümler</div>
            <ol className="as-cekirdek-liste">
              {siralama.slice(0, 3).map((s) => (
                <li key={s.bolum_id}>
                  <button type="button" onClick={() => bolumBilgisiAc(s.bolum_id, s.bolum_adi)}>{s.bolum_adi}</button>
                  <b>%{Math.round(s.toplam_uyum)}</b>
                </li>
              ))}
            </ol>
            <div className="as-cekirdek-not">Puan, bölümün tüm bölümler içinde sana ne kadar yakın olduğunu gösterir (100 = en yakın).</div>
            <div className="as-cekirdek-dugmeler">
              <button type="button" className="btn" onClick={() => navigate('/bolumler')}>Öneriler ve nedenleri →</button>
              <button type="button" className="btn sec" onClick={() => navigate('/bolumler/karsilastir')}>Karşılaştır</button>
              <button type="button" className="btn sec" onClick={() => navigate('/bolumler/tum')}>Tüm bölümler</button>
            </div>
          </div>
          {kocluk && (
            <div className="as-cekirdek-kutu">
              <div className="as-cekirdek-ust">📊 Sen ve hedef bölümün</div>
              {hedefBolumAdi ? (
                <>
                  <div className="as-cekirdek-hedef">{hedefBolumAdi}</div>
                  <div className="as-cekirdek-not">Bu bölümün beklediği özelliklerle seni tek tek karşılaştırdık: nerede uyumlusun, nerede farkın var ve ne yapabilirsin.</div>
                  <div className="as-cekirdek-dugmeler">
                    <button type="button" className="btn" onClick={() => navigate('/koclugu?sekme=karsilastirma')}>Karşılaştırmayı gör →</button>
                    <button type="button" className="btn sec" onClick={() => navigate('/koclugu?sekme=yol')}>Yol haritam</button>
                  </div>
                </>
              ) : (
                <>
                  <div className="as-cekirdek-not">Bir hedef bölüm seç; seni o bölümle özellik özellik karşılaştıralım ve sana adım adım bir gelişim planı hazırlayalım.</div>
                  <div className="as-cekirdek-dugmeler">
                    <button type="button" className="btn" onClick={() => navigate('/profil#hedef')}>Hedef bölümümü seç →</button>
                  </div>
                </>
              )}
            </div>
          )}
        </section>
      )}

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

      {/* [2026-10-18] Grafik satırı ve kısayol kutuları kaldırıldı (katman ortalaması anlamsızdı; kısayollar menüyü tekrar ediyordu).
          Yerine kısa profil özeti; ayrıntı Profilim'de. */}
      {(gucluYonler.length > 0 || onemliDegerler.length > 0) && (
        <section className="card as-profil-ozet" aria-label="Profil özetin">
          <div className="as-profil-ust">
            <div className="ct" style={{ margin: 0 }}>🧭 Profil özetin</div>
            <button type="button" className="hg-link" onClick={() => navigate('/profilim')}>Profilimin tamamı →</button>
          </div>
          <div className="as-profil-sutunlar">
            <div>
              <div className="as-profil-baslik">Güçlü yönlerin</div>
              {gucluYonler.length
                ? gucluYonler.map((s) => <div key={s.degisken_id} className="as-profil-satir"><span>{s.degisken_adi}</span><b style={{ color: 'var(--gr)' }}>{Math.round(s.puan)}</b></div>)
                : <div className="as-cekirdek-not">Henüz belirgin biçimde öne çıkan bir özelliğin yok.</div>}
            </div>
            <div>
              <div className="as-profil-baslik">En önem verdiğin değerler</div>
              {onemliDegerler.map((s) => <div key={s.degisken_id} className="as-profil-satir"><span>{s.degisken_adi}</span><b style={{ color: 'var(--pu)' }}>{Math.round(s.puan)}</b></div>)}
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
