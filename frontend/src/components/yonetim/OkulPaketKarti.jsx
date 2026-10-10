// [2026-10-10] Okulun paketi ve açık modülleri.
// Süper admin: paket seçer, okula özel modül ekler / çıkarır. Okul yetkilisi: yalnızca görür.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

export default function OkulPaketKarti({ okulId, superAdmin, onDegisti }) {
  const [v, setV] = useState(null)
  const [paketler, setPaketler] = useState([])
  const [secim, setSecim] = useState(null)   // { paket, etkin: Set }
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [kaydedildi, setKaydedildi] = useState(false)

  function yukle() {
    api.okulPaketi(okulId).then((d) => { setV(d); setSecim({ paket: d.paket, etkin: new Set(d.moduller) }) }).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  }
  useEffect(() => {
    yukle()
    if (superAdmin) api.paketler().then((d) => setPaketler(d.paketler)).catch(() => {})
  }, [okulId, superAdmin])   // eslint-disable-line react-hooks/exhaustive-deps

  if (!v || !secim) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const paketMod = new Set((paketler.find((p) => p.kod === secim.paket) || (secim.paket === v.paket ? { moduller: v.paket_modulleri } : { moduller: [] })).moduller)

  function paketSec(kod) {
    const p = paketler.find((x) => x.kod === kod)
    setSecim({ paket: kod, etkin: new Set(p?.moduller || []) }); setKaydedildi(false)
  }
  function degistir(kod) {
    const e = new Set(secim.etkin); e.has(kod) ? e.delete(kod) : e.add(kod)
    setSecim({ ...secim, etkin: e }); setKaydedildi(false)
  }
  async function kaydet() {
    setBekle(true); setHata(null)
    const ekle = [...secim.etkin].filter((m) => !paketMod.has(m))
    const cikar = [...paketMod].filter((m) => !secim.etkin.has(m))
    try { await api.okulPaketiKaydet(okulId, { paket: secim.paket, ekle, cikar }); yukle(); setKaydedildi(true); onDegisti?.() }
    catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }

  return (
    <div className="card">
      <div className="ct">📦 Paket: {superAdmin ? (paketler.find((p) => p.kod === secim.paket)?.ad || v.paket_ad) : v.paket_ad}</div>
      {superAdmin ? (
        <>
          <div className="pk-paketler">
            {paketler.map((p) => (
              <button key={p.kod} type="button" className={`pk-paket${secim.paket === p.kod ? ' secili' : ''}`} onClick={() => paketSec(p.kod)}>
                <b>{p.ad}</b><small>{p.moduller.length} modül</small>
              </button>
            ))}
          </div>
          <div className="yp-ince" style={{ margin: '10px 0' }}>Paketi seçin; gerekirse bu okula özel modül ekleyip çıkarın. <b>Değerlendirme, bölüm önerileri, profil, okul paneli ve temel raporlar</b> her pakette vardır.</div>
        </>
      ) : (
        <div className="yp-ince" style={{ marginBottom: 10 }}>Okulunuzda açık olan Filizyol modülleri. Paket değişikliği için Filizyol ile iletişime geçebilirsiniz.</div>
      )}
      <div className="pk-moduller">
        {v.modul_tanimlari.map((m) => {
          const acik = secim.etkin.has(m.kod)
          const fark = superAdmin && acik !== paketMod.has(m.kod)
          return (
            <label key={m.kod} className={`pk-modul${acik ? ' acik' : ''}${superAdmin ? '' : ' salt'}`}>
              {superAdmin ? <input type="checkbox" checked={acik} onChange={() => degistir(m.kod)} /> : <span className="pk-isaret">{acik ? '✓' : '—'}</span>}
              <span style={{ minWidth: 0 }}>
                <b>{m.ikon} {m.ad}</b>{fark && <span className="pk-fark">{acik ? 'okula eklendi' : 'okuldan çıkarıldı'}</span>}
                <small>{m.aciklama}</small>
              </span>
            </label>
          )
        })}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {superAdmin && (
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 12 }}>
          <button className="btn" disabled={bekle} onClick={kaydet}>Kaydet</button>
          {kaydedildi && <span className="yp-ince" style={{ color: 'var(--gr)' }}>✓ Kaydedildi — öğrenciler bir sonraki girişlerinde yeni menüyü görür.</span>}
        </div>
      )}
    </div>
  )
}
