import { useEffect, useState, useCallback } from 'react'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { api } from '../../api/client'

export default function ParametrelerSayfasi() {
  const [parametreler, setParametreler] = useState(null)
  const [duzenleme, setDuzenleme] = useState({})
  const [hata, setHata] = useState(null)
  const { rol } = useAdminAuth()
  const suAdminMi = rol === 'super_admin'

  const yukle = useCallback(() => {
    api.parametreleriListele().then(setParametreler).catch((e) => setHata(e.detail || 'Parametreler yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  async function kaydet(anahtar) {
    try {
      await api.parametreGuncelle(anahtar, duzenleme[anahtar])
      yukle()
    } catch (err) {
      setHata(err.detail || 'Güncellenemedi.')
    }
  }

  if (!parametreler) return <div className="pg"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Sistem Parametreleri</div>
        <div className="ps">
          {suAdminMi ? 'Koda gömülmeyen, çalışma zamanında değiştirilebilir değerler.' : 'Yalnızca süper admin bu değerleri değiştirebilir — sen görüntüleyebilirsin.'}
        </div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <KatmanAgirliklariKarti duzenlenebilir={suAdminMi} />
      <div className="ll">
        {parametreler.map((p) => (
          <div key={p.anahtar} className="lc" style={{ cursor: 'default' }}>
            <div className="lb-wrap">
              <div className="lt">{p.anahtar}</div>
              <div className="ld">{p.aciklama}</div>
            </div>
            <input
              className="auth-input"
              style={{ width: 100 }}
              defaultValue={p.deger}
              disabled={!suAdminMi}
              onChange={(e) => setDuzenleme((d) => ({ ...d, [p.anahtar]: e.target.value }))}
            />
            {suAdminMi && (
              <button className="btn sec" onClick={() => kaydet(p.anahtar)} disabled={duzenleme[p.anahtar] === undefined}>
                Kaydet
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}


// [2026-10-10] K1–K4 katman ağırlıkları — skor motorunun okuduğu katmanlar.normalizasyon_agirligi.
// Kaydetmeden önce sayfa içi onay ister (değişiklik tüm öğrencilerin bölüm sıralamasını etkiler).
function KatmanAgirliklariKarti({ duzenlenebilir }) {
  const [katmanlar, setKatmanlar] = useState(null)
  const [degerler, setDegerler] = useState({})
  const [onayAdimi, setOnayAdimi] = useState(false)
  const [kaydediliyor, setKaydediliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [mesaj, setMesaj] = useState(null)

  const yukle = useCallback(() => {
    api.katmanAgirliklariGetir()
      .then((liste) => {
        setKatmanlar(liste)
        setDegerler(Object.fromEntries(liste.map((k) => [k.katman_kod, String(k.agirlik)])))
      })
      .catch((e) => setHata(e.detail || 'Katman ağırlıkları yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  if (!katmanlar) {
    return <div className="card" style={{ marginBottom: 20 }}><div className="ct">Katman ağırlıkları</div><div className="ps">{hata || 'Yükleniyor…'}</div></div>
  }

  const sayilar = Object.fromEntries(katmanlar.map((k) => [k.katman_kod, Number(String(degerler[k.katman_kod] ?? '').replace(',', '.'))]))
  const gecersiz = katmanlar.filter((k) => {
    const v = sayilar[k.katman_kod]
    return String(degerler[k.katman_kod] ?? '').trim() === '' || !Number.isFinite(v) || v < 0 || v > 100
  })
  const toplam = Math.round(Object.values(sayilar).reduce((a, b) => a + (Number.isFinite(b) ? b : 0), 0) * 100) / 100
  const toplamDogru = Math.abs(toplam - 100) <= 0.01
  const degisti = katmanlar.some((k) => sayilar[k.katman_kod] !== Number(k.agirlik))
  const kaydedilebilir = duzenlenebilir && degisti && toplamDogru && gecersiz.length === 0 && !kaydediliyor

  async function kaydet() {
    setKaydediliyor(true); setHata(null); setMesaj(null)
    try {
      const liste = await api.katmanAgirliklariniGuncelle(sayilar)
      setKatmanlar(liste)
      setDegerler(Object.fromEntries(liste.map((k) => [k.katman_kod, String(k.agirlik)])))
      setOnayAdimi(false)
      setMesaj('Katman ağırlıkları kaydedildi. Yeni ağırlıklar bundan sonraki uyum hesaplamalarında kullanılır.')
    } catch (err) {
      setHata(err.detail || 'Kaydedilemedi.')
    } finally {
      setKaydediliyor(false)
    }
  }

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div className="ct">Katman ağırlıkları</div>
      <div className="ps" style={{ margin: '0 0 12px' }}>
        Bölüm uyum skorunda her ana katmanın payı (%). Dört değerin toplamı 100 olmalı. Skor motoru bu değerleri doğrudan kullanır.
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {mesaj && <div style={{ marginBottom: 10, fontSize: 13, color: 'var(--gr, #15803d)', fontWeight: 600 }}>{mesaj}</div>}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'flex-end' }}>
        {katmanlar.map((k) => (
          <label key={k.katman_kod} style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12, fontWeight: 600 }}>
            <span title={k.ad}>{k.katman_kod} · {k.ad}</span>
            <input
              className="auth-input"
              style={{ width: 110, borderColor: gecersiz.includes(k) ? 'var(--re)' : undefined }}
              type="number" min="0" max="100" step="0.5" inputMode="decimal"
              value={degerler[k.katman_kod] ?? ''}
              disabled={!duzenlenebilir || kaydediliyor}
              onChange={(e) => { setDegerler((d) => ({ ...d, [k.katman_kod]: e.target.value })); setOnayAdimi(false); setMesaj(null) }}
            />
          </label>
        ))}
        <div style={{ fontSize: 13, fontWeight: 700, padding: '8px 0', color: toplamDogru ? 'var(--gr, #15803d)' : 'var(--re)' }}>
          Toplam: {toplam} / 100{!toplamDogru && ` (fark ${Math.round((100 - toplam) * 100) / 100 > 0 ? '+' : ''}${Math.round((100 - toplam) * 100) / 100})`}
        </div>
      </div>
      {gecersiz.length > 0 && <div style={{ marginTop: 8, fontSize: 12, color: 'var(--re)' }}>Her ağırlık 0 ile 100 arasında bir sayı olmalı.</div>}
      {duzenlenebilir && !onayAdimi && (
        <div style={{ marginTop: 12, display: 'flex', gap: 10 }}>
          <button className="btn" disabled={!kaydedilebilir} onClick={() => setOnayAdimi(true)}>Kaydet</button>
          {degisti && <button className="btn sec" disabled={kaydediliyor} onClick={() => { yukle(); setOnayAdimi(false) }}>Vazgeç</button>}
        </div>
      )}
      {duzenlenebilir && onayAdimi && (
        <div style={{ marginTop: 12, padding: '10px 12px', borderRadius: 8, border: '1px solid var(--re)', background: 'var(--rel)' }}>
          <div style={{ fontSize: 13, marginBottom: 10 }}>
            <b>Bu değişiklik tüm öğrencilerin bölüm sıralamasını etkiler.</b> Yeni değerler:{' '}
            {katmanlar.map((k) => `${k.katman_kod} %${sayilar[k.katman_kod]}`).join(', ')}. Emin misiniz?
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn" style={{ background: 'var(--re)', borderColor: 'var(--re)' }} disabled={!kaydedilebilir} onClick={kaydet}>
              {kaydediliyor ? <span className="spin" /> : 'Evet, kaydet'}
            </button>
            <button className="btn sec" disabled={kaydediliyor} onClick={() => setOnayAdimi(false)}>Vazgeç</button>
          </div>
        </div>
      )}
    </div>
  )
}
