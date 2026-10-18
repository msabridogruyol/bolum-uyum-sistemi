import { useEffect, useState } from 'react'
import GecersizTurUyarisi from '../components/GecersizTurUyarisi'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { katmanAdi } from '../yardimci/katmanAdlari'
import { gelisimeAcikMi, gucluMu } from '../yardimci/seviye'

const KATMAN_IKON = { K1: '🌱', K2: '🌿', K3: '🍃', K4: '🌸', K5: '🌻' }
const ANA_KATMANLAR = ['K1', 'K2', 'K3', 'K4']

export default function GenelSonuclarSayfasi({ gomulu = false }) {
  const [katmanlar, setKatmanlar] = useState(null)
  const [katmanSonuclari, setKatmanSonuclari] = useState(null)
  const [k5Durum, setK5Durum] = useState(null)
  const [ozet, setOzet] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail || 'Katmanlar yüklenemedi.'))
    api.k5Durumu().then(setK5Durum).catch(() => setK5Durum({ acilan: [], ilgi_gosterilen: [] }))
    api.durumOzetiGetir().then(setOzet).catch(() => setOzet(null))
  }, [])

  useEffect(() => {
    if (!katmanlar) return
    Promise.all(ANA_KATMANLAR.map((kod) => api.katmanSonucuGetir(kod).then((r) => [kod, r]).catch(() => [kod, null])))
      .then((sonuclarListesi) => {
        const harita = {}
        sonuclarListesi.forEach(([kod, r]) => {
          if (r && r.tamamlandi_mi && r.sonuclar.length) {
            const ortalama = r.sonuclar.reduce((a, s) => a + s.puan, 0) / r.sonuclar.length
            harita[kod] = {
              puanOrtalama: Math.round(ortalama),
              sonuclar: r.sonuclar.map((s) => ({ ...s, katmanKod: kod })),
            }
          } else {
            harita[kod] = null
          }
        })
        setKatmanSonuclari(harita)
      })
  }, [katmanlar])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar || !katmanSonuclari || !k5Durum) return <div className="pg"><div className="bos-durum yukleniyor">Yükleniyor…</div></div>

  const tamamlanan = katmanlar.filter((k) => k.durum === 'tamamlandi').length
  const tumTamam = ANA_KATMANLAR.every((kod) => katmanSonuclari[kod] !== null)

  // [2026-10-03] K5 zorunlu: açılan dal(lar) bitmediyse öğrenci K5'e yönlendirilir
  const k5Bekliyor = !!ozet && ozet.k5_acilan_dal_sayisi > ozet.k5_tamamlanan_dal_sayisi

  // [2026-10-18] Yeni K5'in tek bir "puanı" yoktur (iş türü tercihleri küme içi sırayı değiştirir): kartta durum gösterilir
  const k5Bitti = k5Durum.acilan.some((d) => d.durum === 'tamamlandi')

  // [2026-10-18] Sadeleştirme + sistem mantığı: puanlar katman içinde görelidir (ortalama hep ≈50, gösterilmez).
  // Güçlü yön = 62 ve üstü; değerler (K1/D) güçlü yön ya da gelişim alanı sayılmaz, "önem verdiklerin" olarak ayrı
  // listelenir; duygusal hassasiyet (P4) ters yönlüdür, iki listeye de girmez (Kişilik sekmesinde görünür).
  const tumSonuclar = ANA_KATMANLAR.flatMap((kod) => katmanSonuclari[kod]?.sonuclar || [])
  const degerMi = (s) => s.katmanKod === 'K1' || String(s.degisken_kod || '').startsWith('D')
  const p4Mu = (s) => s.degisken_kod === 'P4'
  const ozellikler = tumSonuclar.filter((s) => !degerMi(s) && !p4Mu(s)).sort((a, b) => b.puan - a.puan)
  const degerler = tumSonuclar.filter(degerMi).sort((a, b) => b.puan - a.puan)
  const gucluler = ozellikler.filter((s) => gucluMu(s.puan)).slice(0, 6)
  const gorece = gucluler.length ? [] : ozellikler.slice(0, 3)
  const gelisim = ozellikler.filter((s) => gelisimeAcikMi(s.puan)).reverse().slice(0, 5)
  const onemli = degerler.slice(0, 3)
  const azOnemli = degerler.length > 3 ? degerler.slice(-2).reverse() : []
  const enOne = (kod) => [...(katmanSonuclari[kod]?.sonuclar || [])].filter((s) => !p4Mu(s)).sort((a, b) => b.puan - a.puan)[0]

  return (
    <div className="pg pg-genis">
      <div className="ph" style={gomulu ? { display: 'none' } : undefined}>
        <div className="pt">Genel Sonuçlar</div>
        <div className="ps">
          Tüm katmanların özet profili · {tamamlanan}/{katmanlar.length} katman tamamlandı
        </div>
      </div>
      {!gomulu && <GecersizTurUyarisi ozet={ozet} />}

      {k5Bekliyor && (
        <div className="card" style={{ borderColor: 'var(--pu)', background: 'var(--pul)', marginBottom: 16 }}>
          <div className="ct">Bir adım kaldı: İş Türü Soruları (K5)</div>
          <div className="ps" style={{ margin: '0 0 12px' }}>
            Sana en uygun çıkan bölümleri karşılaştıran, sana özel iş türü soruları açıldı. Bu soruları bitirince bölüm önerilerin hazırlanacak.
          </div>
          <button className="btn" onClick={() => navigate('/katmanlar')}>K5'e Devam Et →</button>
        </div>
      )}

      {/* --- Katmanlar: her katmanda en öne çıkan özellik (ortalama değil — katman içi puanlar göreli) --- */}
      <div className="gp-katmanlar">
        {ANA_KATMANLAR.map((kod) => {
          const sonuc = katmanSonuclari[kod]
          const ust = enOne(kod)
          return (
            <button key={kod} type="button" className="gp-katman" onClick={() => navigate(`/profilim/${kod}`)}>
              <span className="gp-katman-ad">{KATMAN_IKON[kod]} {katmanAdi(kod)}</span>
              {sonuc && ust ? (
                <span className="gp-katman-ust"><small>{kod === 'K1' ? 'En önem verdiğin' : 'En öne çıkan'}</small>{ust.degisken_adi}</span>
              ) : <span className="gp-katman-ust bos">Henüz tamamlanmadı</span>}
            </button>
          )
        })}
        <button type="button" className="gp-katman" onClick={() => navigate(k5Durum.acilan.length > 0 && !k5Bekliyor ? '/profilim/K5' : '/katmanlar')}>
          <span className="gp-katman-ad">{KATMAN_IKON.K5} {katmanAdi('K5')}</span>
          <span className={'gp-katman-ust' + (k5Bitti ? '' : ' bos')}>{k5Bitti ? <><small>Durum</small>Tamamlandı ✓</> : k5Durum.acilan.length ? 'Sorular bekliyor' : 'Açılmadı'}</span>
        </button>
      </div>

      {!tumTamam ? (
        <>
          <div className="taslak-onizleme">
            <div className="taslak-onizleme-icerik">
              <div className="sw">
                <div className="swc">
                  <div className="swh"><div className="swi" style={{ background: 'var(--grl)' }}>✓</div><div className="swt">Güçlü yönlerin</div></div>
                  {['Entelektüel Merak', 'Sistemik Düşünce', 'Sosyal Etki', 'Özerklik', 'Yaratıcılık'].map((ad, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--tx2)', padding: '5px 0' }}>
                      <span>{ad}</span><b style={{ color: 'var(--gr)' }}>{90 - i * 6}</b>
                    </div>
                  ))}
                </div>
                <div className="swc">
                  <div className="swh"><div className="swi" style={{ background: 'var(--aml)' }}>↻</div><div className="swt">Gelişime açık yönlerin</div></div>
                  {['Dışadönüklük', 'Risk Toleransı', 'Rekabet', 'Statü'].map((ad, i) => (
                    <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--tx2)', padding: '5px 0' }}>
                      <span>{ad}</span><b style={{ color: 'var(--am)' }}>{35 - i * 4}</b>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="taslak-onizleme-overlay">
              <div className="to-ikon">📊</div>
              <div className="to-metin">
                K1–K4'ün hepsini bitirince güçlü yönlerin, önem verdiğin değerler ve gelişime açık yönlerin burada görünecek. Şu an {tamamlanan}/{katmanlar.length} katman tamamlandı.
              </div>
            </div>
          </div>
          <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/katmanlar')}>
            {tamamlanan === 0 ? 'Yolculuğuna Başla' : 'Kaldığın Yerden Devam Et'} →
          </button>
        </>
      ) : (
        <>
          <div className="gp-ozet">
            <div className="swc">
              <div className="swh">
                <div className="swi" style={{ background: 'var(--grl)' }}>✓</div>
                <div className="swt">Güçlü yönlerin</div>
              </div>
              <div className="gp-not">Kendi profilinde öne çıkan özelliklerin (62 ve üstü).</div>
              {gucluler.map((s) => <Satir key={s.degisken_id} s={s} renk="var(--gr)" alt={s.durum_tespiti} />)}
              {!gucluler.length && (
                <>
                  <div className="gp-not">Henüz belirgin biçimde öne çıkan bir özelliğin yok; görece en yüksek puanların:</div>
                  {gorece.map((s) => <Satir key={s.degisken_id} s={s} renk="var(--tx2)" />)}
                </>
              )}
            </div>
            <div className="swc">
              <div className="swh">
                <div className="swi" style={{ background: 'var(--pul)' }}>❤</div>
                <div className="swt">Önem verdiğin değerler</div>
              </div>
              <div className="gp-not">Bir işte senin için önemli olanlar. Değerler geliştirilecek bir yön değil; bölüm seçerken dikkate alacağın bir tercih.</div>
              {onemli.map((s) => <Satir key={s.degisken_id} s={s} renk="var(--pu)" katmansiz />)}
              {azOnemli.length > 0 && (
                <>
                  <div className="gp-alt-baslik">Senin için daha az belirleyici</div>
                  {azOnemli.map((s) => <Satir key={s.degisken_id} s={s} renk="var(--tx3)" katmansiz />)}
                </>
              )}
            </div>
            <div className="swc">
              <div className="swh">
                <div className="swi" style={{ background: 'var(--aml)' }}>↻</div>
                <div className="swt">Gelişime açık yönlerin</div>
              </div>
              <div className="gp-not">Kendi profilinde geride kalan özelliklerin (40'ın altı). Kötü olduğun anlamına gelmez.</div>
              {gelisim.map((s) => <Satir key={s.degisken_id} s={s} renk="var(--am)" alt={s.aksiyon_onerisi && `💡 ${s.aksiyon_onerisi}`} />)}
              {!gelisim.length && <div className="gp-not">40'ın altında kalan bir özelliğin yok.</div>}
            </div>
          </div>
        </>
      )}

      {k5Bekliyor ? (
        <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/katmanlar')}>İş Türü Sorularına (K5) Devam Et →</button>
      ) : !gomulu && (
        <button className="btn full" style={{ marginTop: 16 }} onClick={() => navigate('/')}>Ana Sayfaya Dön</button>
      )}
    </div>
  )
}

// Tek özellik satırı: ad + katman adı + tam sayı puan (+ isteğe bağlı kısa açıklama)
function Satir({ s, renk, alt, katmansiz = false }) {
  return (
    <div className="gp-satir">
      <div className="gp-satir-ust">
        <span>
          {s.degisken_adi}
          {!katmansiz && <small>{katmanAdi(s.katmanKod).split(/ [&/] /)[0]}</small>}
        </span>
        <b style={{ color: renk }}>{Math.round(s.puan)}</b>
      </div>
      {alt && <div className="gp-satir-alt">{alt}</div>}
    </div>
  )
}
