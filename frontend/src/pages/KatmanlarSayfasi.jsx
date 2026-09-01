import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const DURUM_ETIKET = { baslamadi: null, devam_ediyor: 'Devam Ediyor', tamamlandi: 'Tamamlandı' }
const DURUM_RENK = { devam_ediyor: 'bdg-prog', tamamlandi: 'bdg-done' }
const KATMAN_IKON = { K1: '🌱', K2: '🌿', K3: '🍃', K4: '🌸', K5: '🌻' }

// [DÜZELTME] Önceden "boyut sayısı" (K1:7, K2:8 vb.) öğrenciye gösteriliyordu
// — bu teknik bir detay, öğrencinin bilmesine gerek yok, kaldırıldı.
// Süre artık backend'den gelen GERÇEK aktif soru sayısına göre hesaplanıyor
// (sabit/tahmini bir tablo değil).
const SANIYE_BASINA_SORU_TAHMINI = 20 // Likert+SJT karışık ortalama kaba tahmin
function tahminiSureDk(soruSayisi) {
  if (!soruSayisi) return null
  return Math.max(1, Math.round((soruSayisi * SANIYE_BASINA_SORU_TAHMINI) / 60))
}

const KATMAN_ACIKLAMA = {
  K1: 'Kariyerinde neye değer verdiğini keşfeder',
  K2: 'Kişilik yapını ve çalışma tarzını ölçer',
  K3: 'İş ortamındaki profesyonel yetkinliklerini değerlendirir',
  K4: 'Hangi alanlara doğal bir eğilimin olduğunu belirler',
}

const DURUM_YUZDE = { tamamlandi: 100, devam_ediyor: 50, baslamadi: 0 }
const DURUM_RENK_HEX = { tamamlandi: 'var(--gr)', devam_ediyor: 'var(--pu)', baslamadi: 'var(--tx3)' }

export default function KatmanlarSayfasi() {
  const [katmanlar, setKatmanlar] = useState(null)
  const [k5Durum, setK5Durum] = useState(null)
  const [hedef, setHedef] = useState(undefined) // undefined=yükleniyor, null=yok
  const [profil, setProfil] = useState(null)
  const [k1Sonuc, setK1Sonuc] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail || 'Katmanlar yüklenemedi.'))
    api.k5Durumu().then(setK5Durum).catch(() => setK5Durum(null))
    api.aktifHedefGetir().then(setHedef).catch(() => setHedef(null))
    api.profilGetir().then(setProfil).catch(() => {})
    api.katmanSonucuGetir('K1').then(setK1Sonuc).catch(() => setK1Sonuc(null))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar || hedef === undefined) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const tamamlanan = katmanlar.filter((k) => k.durum === 'tamamlandi').length
  const devamEden = katmanlar.filter((k) => k.durum === 'devam_ediyor').length
  const profilYuzde = Math.round((tamamlanan / katmanlar.length) * 100)
  const k5AcikMi = k5Durum && (k5Durum.acilan?.length > 0 || k5Durum.ilgi_gosterilen?.length > 0)

  const enGucluDeger = k1Sonuc?.tamamlandi_mi && k1Sonuc.sonuclar.length
    ? [...k1Sonuc.sonuclar].sort((a, b) => b.puan - a.puan)[0]
    : null

  const hedefVarMi = hedef || profil?.hedef_universite || profil?.hedef_meslek_adi

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Yol Haritan</div>
        <div className="ps">
          Katmanları sırayla tamamla; son katman (Alan Eğilimi) sonucuna göre sana özel derinleşme dalları burada, aynı listede açılır.
        </div>
      </div>

      <div className="yol-duzen">
        <div>
          <div className="sg">
            <div className="sc"><div className="sl">Toplam Katman</div><div className="sv">{katmanlar.length}</div></div>
            <div className="sc"><div className="sl">Tamamlanan</div><div className="sv gr">{tamamlanan}</div></div>
            <div className="sc"><div className="sl">Devam Eden</div><div className="sv pu">{devamEden}</div></div>
            <div className="sc"><div className="sl">Profil Tamamlama</div><div className="sv">%{profilYuzde}</div></div>
          </div>

          <div className="ll">
            {katmanlar.map((k) => (
              <div
                key={k.id}
                className={`lc${k.durum === 'tamamlandi' ? ' done' : k.durum === 'devam_ediyor' ? ' cur' : ''}`}
                onClick={() => navigate(`/katmanlar/${k.kod}`)}
              >
                <div className="ln" style={{ fontSize: 18 }}>
                  {k.durum === 'tamamlandi' ? '✓' : KATMAN_IKON[k.kod] || k.sira}
                </div>
                <div className="lb-wrap">
                  <div className="lt">{k.ad}</div>
                  <div className="ld">
                    {k.kosullu_mu ? 'Koşullu / Dinamik — önceki katmana bağlı' : (KATMAN_ACIKLAMA[k.kod] || `Ağırlık: %${k.normalizasyon_agirligi}`)}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
                    {DURUM_ETIKET[k.durum] && <span className={`bdg ${DURUM_RENK[k.durum]}`}>{DURUM_ETIKET[k.durum]}</span>}
                    {k.soru_sayisi > 0 && (
                      <span style={{ fontSize: 10.5, color: 'var(--tx3)' }}>
                        {k.soru_sayisi} soru · ~{tahminiSureDk(k.soru_sayisi)} dk
                      </span>
                    )}
                  </div>
                </div>
                <div className="mini-ilerleme-wrap">
                  <div className="mini-ilerleme-track">
                    <div className="mini-ilerleme-fill" style={{ width: `${DURUM_YUZDE[k.durum]}%`, background: DURUM_RENK_HEX[k.durum] }} />
                  </div>
                  <div className="mini-ilerleme-yuzde" style={{ color: DURUM_RENK_HEX[k.durum] }}>%{DURUM_YUZDE[k.durum]}</div>
                </div>
              </div>
            ))}

            {k5Durum?.acilan?.map((d) => (
              <div key={d.dal_kodu} className="lc" onClick={() => navigate(`/k5/${d.dal_kodu}`)}>
                <div className="ln" style={{ background: 'var(--pul)', color: 'var(--pu)', fontSize: 18 }}>🌟</div>
                <div className="lb-wrap">
                  <div className="lt">{d.dal_adi}</div>
                  <div className="ld">Derinleşme dalı — Puanın: {d.puan}</div>
                  <span className="bdg bdg-prog">Açık — sorularını cevapla</span>
                </div>
              </div>
            ))}
          </div>

          {k5Durum?.ilgi_gosterilen?.length > 0 && (
            <div className="card" style={{ marginTop: 14 }}>
              <div className="ct">Ayrıca İlgi Gösterdiğin Alanlar</div>
              <div className="ps" style={{ margin: 0 }}>
                {k5Durum.ilgi_gosterilen.map((d) => `${d.dal_adi} (${d.puan} puan)`).join(', ')} —
                bu alanlar için ek soru sorulmadı ama eşiğe yakınsın.
              </div>
            </div>
          )}

          {!k5AcikMi && tamamlanan === katmanlar.length && (
            <div className="bos-durum" style={{ marginTop: 14 }}>
              Şu an için açılmış bir derinleşme dalın yok — bu, profiline uygun dal olmadığı anlamına gelebilir.
            </div>
          )}
        </div>

        <div className="yan-panel">
          <div className="card" style={{ marginBottom: 0, background: hedefVarMi ? 'linear-gradient(135deg,var(--pul),var(--sur))' : undefined, borderColor: hedefVarMi ? 'var(--pu)' : undefined }}>
            <div className="ct">🎯 Hedefin</div>
            {hedefVarMi ? (
              <div>
                {hedef && (
                  <div style={{ marginBottom: profil?.hedef_universite || profil?.hedef_meslek_adi ? 10 : 0 }}>
                    <div style={{ fontSize: 10.5, color: 'var(--tx3)', fontWeight: 600 }}>Hedef Bölüm</div>
                    <div style={{ fontSize: 15, fontWeight: 700 }}>{hedef.bolum_adi}</div>
                  </div>
                )}
                {profil?.hedef_universite && (
                  <div style={{ marginBottom: profil?.hedef_meslek_adi ? 10 : 0 }}>
                    <div style={{ fontSize: 10.5, color: 'var(--tx3)', fontWeight: 600 }}>Hedef Üniversite</div>
                    <div style={{ fontSize: 13.5, fontWeight: 600 }}>{profil.hedef_universite}</div>
                  </div>
                )}
                {profil?.hedef_meslek_adi && (
                  <div>
                    <div style={{ fontSize: 10.5, color: 'var(--tx3)', fontWeight: 600 }}>Hedef Meslek</div>
                    <div style={{ fontSize: 13.5, fontWeight: 600 }}>{profil.hedef_meslek_adi}</div>
                  </div>
                )}
                <button className="btn sec" style={{ marginTop: 12, width: '100%' }} onClick={() => navigate(hedef ? '/koclugu' : '/profil')}>
                  {hedef ? 'Koçluğa Git' : 'Profilden Düzenle'}
                </button>
              </div>
            ) : (
              <div>
                <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.6, marginBottom: 12 }}>
                  Henüz bir hedef belirlemedin. Bir bölüm, üniversite veya meslek hedeflemek yolculuğunu daha anlamlı kılabilir.
                </div>
                <button className="btn" style={{ width: '100%' }} onClick={() => navigate('/koclugu')}>Hedef Belirle</button>
              </div>
            )}
          </div>

          <div className="card" style={{ marginBottom: 0 }}>
            <div className="ct">💛 Seni Motive Eden</div>
            {enGucluDeger ? (
              <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.65 }}>
                Değerler katmanına göre senin için en önemli şey: <b style={{ color: 'var(--tx)' }}>{enGucluDeger.degisken_adi}</b>.
                {' '}Bu yolculuğu tamamlamak, sana bunu sağlayacak bölümleri bulman için.
              </div>
            ) : (
              <div className="taslak-onizleme">
                <div className="taslak-onizleme-icerik">
                  <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.65 }}>
                    Değerler katmanına göre senin için en önemli şey: <b>Anlam / yaşam amacı</b>.
                    {' '}Bu yolculuğu tamamlamak, sana bunu sağlayacak bölümleri bulman için.
                  </div>
                </div>
                <div className="taslak-onizleme-overlay">
                  <div className="to-metin" style={{ fontSize: 11.5 }}>K1'i tamamlayınca gerçek motivasyonun burada görünecek</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
