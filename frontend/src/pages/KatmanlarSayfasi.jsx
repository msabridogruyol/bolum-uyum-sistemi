import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

const DURUM_ETIKET = { baslamadi: null, devam_ediyor: 'Devam Ediyor', tamamlandi: 'Tamamlandı' }
const DURUM_RENK = { devam_ediyor: 'bdg-prog', tamamlandi: 'bdg-done' }
const KATMAN_IKON = { K1: '🌱', K2: '🌿', K3: '🍃', K4: '🌸', K5: '🌻' }

// Gerçek veri: her katmandaki değişken (boyut) sayısı — schema'daki sabit dağılım
const KATMAN_BOYUT_SAYISI = { K1: 7, K2: 8, K3: 7, K4: 9 }

// Süre TAHMİNİ — ölçülmüş bir veri değil, hesaplanmış bir tahmin:
// varsayım: soru başına ortalama ~25 saniye (Likert tipi bir soruyu okuyup
// cevaplamak için makul bir süre) × o katmandaki boyut sayısı
const SANIYE_BASINA_SORU_TAHMINI = 25
function tahminiSureDk(kod) {
  const boyut = KATMAN_BOYUT_SAYISI[kod]
  if (!boyut) return null
  return Math.max(1, Math.round((boyut * SANIYE_BASINA_SORU_TAHMINI) / 60))
}

// Kısa açıklamalar — sistem_genel_anlatim.md'deki katman tanımlarından
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
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.katmanlariListele().then(setKatmanlar).catch((e) => setHata(e.detail || 'Katmanlar yüklenemedi.'))
    api.k5Durumu().then(setK5Durum).catch(() => setK5Durum(null))
  }, [])

  if (hata) return <div className="pg"><div className="bos-durum">{hata}</div></div>
  if (!katmanlar) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const tamamlanan = katmanlar.filter((k) => k.durum === 'tamamlandi').length
  const devamEden = katmanlar.filter((k) => k.durum === 'devam_ediyor').length
  const profilYuzde = Math.round((tamamlanan / katmanlar.length) * 100)
  const k5AcikMi = k5Durum && (k5Durum.acilan?.length > 0 || k5Durum.ilgi_gosterilen?.length > 0)

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Yol Haritan</div>
        <div className="ps">
          Katmanları sırayla tamamla; son katman (Alan Eğilimi) sonucuna göre sana özel derinleşme dalları burada, aynı listede açılır.
        </div>
      </div>

      {/* --- İstatistik kartları --- */}
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
                {KATMAN_BOYUT_SAYISI[k.kod] && (
                  <span style={{ fontSize: 10.5, color: 'var(--tx3)' }}>
                    {KATMAN_BOYUT_SAYISI[k.kod]} boyut · ~{tahminiSureDk(k.kod)} dk
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

        {/* K5 dalları — ayrı bir sayfa değil, aynı listenin devamı */}
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
  )
}
