import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'

// [2026-10-18] Yeni K5 soru bankası: K5 soruları öğrenciye özel, bu cümle ve köklerden üretilir (soru bankası listesinde
// görünmez). Metin değişikliği yalnızca bundan sonra üretilecek soruları etkiler.
const TIP_AD = { encok: 'En çok / en az', tek: 'Tek seçim', kutup: 'Uçlar' }

function Metin({ deger, onKaydet }) {
  const [taslak, setTaslak] = useState(deger)
  const [kayit, setKayit] = useState(false)
  useEffect(() => setTaslak(deger), [deger])
  async function kaydet() {
    if (taslak.trim() === deger || !taslak.trim()) { setTaslak(deger); return }
    setKayit(true)
    try { await onKaydet(taslak.trim()) } finally { setKayit(false) }
  }
  return (
    <input type="text" className="auth-input" value={taslak} disabled={kayit} onChange={(e) => setTaslak(e.target.value)}
      onBlur={kaydet} onKeyDown={(e) => { if (e.key === 'Enter') e.currentTarget.blur(); if (e.key === 'Escape') setTaslak(deger) }}
      style={{ width: '100%', fontSize: 13, padding: '5px 8px' }} />
  )
}

export default function K5BankasiPaneli() {
  const [veri, setVeri] = useState(null)
  const [hata, setHata] = useState(null)
  const [arama, setArama] = useState('')
  const yukle = () => api.k5BankasiGetir().then(setVeri).catch((e) => setHata(e.detail || 'K5 bankası yüklenemedi.'))
  useEffect(() => { yukle() }, [])

  const isTurleri = useMemo(() => {
    const q = arama.trim().toLocaleLowerCase('tr')
    return (veri?.is_turleri || []).filter((x) => !q || `${x.ad} ${x.kod} ${x.alan || ''} ${x.cumleler.map((c) => c.metin).join(' ')}`
      .toLocaleLowerCase('tr').includes(q))
  }, [veri, arama])

  if (hata) return <div className="bos-durum">{hata}</div>
  if (!veri) return <div className="bos-durum yukleniyor">Yükleniyor…</div>
  const cumleSayisi = veri.is_turleri.reduce((t, x) => t + x.cumleler.filter((c) => c.aktif_mi).length, 0)

  return (
    <div>
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="ct">K5 — iş türü soru bankası</div>
        <div className="ps" style={{ margin: 0 }}>
          K5 soruları her öğrenciye özel üretilir: K1-K4 uyumu ≥ 70 olan bölümlerin (en fazla 20) bağlı iş türlerinin
          cümleleri aşağıdaki köklerle birleştirilir. {veri.is_turleri.length} iş türü · {cumleSayisi} aktif cümle ·
          {' '}{veri.kokler.filter((k) => k.aktif_mi).length} aktif kök. Metin değişikliği yalnızca bundan sonra üretilecek
          soruları etkiler; öğrencinin başlamış turundaki sorular değişmez.
        </div>
      </div>

      <div className="card" style={{ marginBottom: 14 }}>
        <div className="ct" style={{ fontSize: 14 }}>Soru kökleri</div>
        {['encok', 'tek', 'kutup'].map((t) => (
          <div key={t} style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--tx2)', margin: '6px 0' }}>{TIP_AD[t]}</div>
            {veri.kokler.filter((k) => k.tip === t).map((k) => (
              <div key={k.id} style={{ marginBottom: 5, opacity: k.aktif_mi ? 1 : 0.5 }}>
                <Metin deger={k.metin} onKaydet={async (m) => { await api.k5KokGuncelle(k.id, m); await yukle() }} />
              </div>
            ))}
          </div>
        ))}
      </div>

      <input className="auth-input" style={{ width: 280, marginBottom: 12 }} placeholder="🔍 İş türü ya da cümle ara…"
        value={arama} onChange={(e) => setArama(e.target.value)} />
      {isTurleri.map((x) => (
        <div key={x.degisken_id} className="card" style={{ marginBottom: 10 }}>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginBottom: 8 }}>
            <b style={{ fontSize: 14 }}>{x.ad}</b>
            <span className="bdg bdg-lock">{x.kod}</span>
            {x.alan && <span className="bdg" style={{ background: 'var(--tll)', color: 'var(--tl)' }}>{x.alan}</span>}
            <span className="bdg bdg-lock">{x.bagli_bolum_sayisi} bölüme bağlı</span>
          </div>
          {x.cumleler.length === 0 ? <div className="yp-ince">Cümle yok — bu iş türü sorulamaz.</div> : x.cumleler.map((c) => (
            <div key={c.id} style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 5, opacity: c.aktif_mi ? 1 : 0.5 }}>
              <span style={{ width: 16, color: 'var(--tx3)', fontWeight: 700, fontSize: 12 }}>{c.sira}.</span>
              <div style={{ flex: 1 }}>
                <Metin deger={c.metin} onKaydet={async (m) => { await api.k5CumleGuncelle(c.id, m); await yukle() }} />
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
