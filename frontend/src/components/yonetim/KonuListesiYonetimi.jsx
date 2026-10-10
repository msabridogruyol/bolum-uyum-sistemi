// [2026-10-10] Net Takibi konu listesinin yönetimi.
// okulId yok → GENEL liste (yalnızca süper admin): ekle / adlandır / sırala / sil — tüm okullarda geçerli.
// okulId var → OKUL görünümü: genel konuları okulda gizle / göster, okula özel konu ekle / adlandır / sırala / sil.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'

function KonuSatiri({ k, okulId, yenile, hata }) {
  const [duzen, setDuzen] = useState(null)
  const [silOnay, setSilOnay] = useState(false)
  const [bekle, setBekle] = useState(false)
  const genelOkulda = okulId && k.kaynak === 'genel'   // okul görünümünde genel konu: yalnızca gizle / göster
  async function islem(f) { setBekle(true); hata(null); try { await f(); await yenile() } catch (e) { hata(e.detail || 'İşlem yapılamadı.') } finally { setBekle(false) } }
  if (duzen !== null) {
    return (
      <form className="kl-satir duzen" onSubmit={(e) => { e.preventDefault(); islem(async () => { await api.konuDuzenle(k.id, duzen); setDuzen(null) }) }}>
        <input className="auth-input" autoFocus maxLength={120} value={duzen} onChange={(e) => setDuzen(e.target.value)} />
        <button className="btn" disabled={bekle || !duzen.trim()}>Kaydet</button>
        <button type="button" className="btn sec" onClick={() => setDuzen(null)}>Vazgeç</button>
      </form>
    )
  }
  return (
    <div className={`kl-satir${k.gizli ? ' gizli' : ''}`}>
      <span className="kl-ad">{k.ad}</span>
      <span className={`kl-rozet ${k.kaynak}`}>{k.kaynak === 'okul' ? 'Okula özel' : 'Genel'}</span>
      {k.gizli && <span className="kl-rozet gizli">Okulda gizli</span>}
      <span className="kl-islemler">
        {genelOkulda ? (
          <button className="yp-mini" disabled={bekle} onClick={() => islem(() => api.konuGizle(k.id, okulId, !k.gizli))}>{k.gizli ? '👁 Göster' : '🚫 Okulumuzda gizle'}</button>
        ) : silOnay ? (
          <>
            <span className="yp-ince">Silinsin mi? Öğrencilerin bu konudaki işaretleri de silinir.</span>
            <button className="yp-mini kirmizi" disabled={bekle} onClick={() => islem(() => api.konuSil(k.id))}>Evet, sil</button>
            <button className="yp-mini" onClick={() => setSilOnay(false)}>Vazgeç</button>
          </>
        ) : (
          <>
            <button className="yp-mini" title="Yukarı taşı" disabled={bekle} onClick={() => islem(() => api.konuTasi(k.id, 'yukari'))}>↑</button>
            <button className="yp-mini" title="Aşağı taşı" disabled={bekle} onClick={() => islem(() => api.konuTasi(k.id, 'asagi'))}>↓</button>
            <button className="yp-mini" disabled={bekle} onClick={() => setDuzen(k.ad)}>✎ Düzenle</button>
            <button className="yp-mini" disabled={bekle} onClick={() => setSilOnay(true)}>Sil</button>
          </>
        )}
      </span>
    </div>
  )
}

export default function KonuListesiYonetimi({ okulId = null }) {
  const [veri, setVeri] = useState(null)
  const [ders, setDers] = useState('tyt_turkce')
  const [yeni, setYeni] = useState('')
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const yenile = useCallback(() => api.konuListesi(okulId).then(setVeri).catch((e) => setHata(e.detail || 'Liste yüklenemedi.')), [okulId])
  useEffect(() => { yenile() }, [yenile])
  if (!veri) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const aktif = veri.dersler.find((d) => d.kod === ders) || veri.dersler[0]
  const okulGorunumu = !!veri.okul_id && !!okulId
  async function ekle(e) {
    e.preventDefault(); setHata(null); setBekle(true)
    try { await api.konuEkle(aktif.kod, yeni, okulGorunumu ? okulId : null); setYeni(''); await yenile() } catch (er) { setHata(er.detail || 'Eklenemedi.') } finally { setBekle(false) }
  }
  const say = (d) => d.konular.filter((k) => !k.gizli).length
  return (
    <>
      <div className="yp-ince" style={{ marginBottom: 12, lineHeight: 1.6 }}>
        {okulGorunumu
          ? <>Öğrencilerinizin <b>Net Takibi → Konu Takibi</b> ekranında gördüğü liste. <b>Genel</b> konular tüm okullar için Filizyol tarafından hazırlanır; okulunuzda gerekmeyenleri gizleyebilirsiniz. <b>Okula özel</b> konu ekleyebilir, adlandırabilir, sıralayabilir ve silebilirsiniz.</>
          : <>Tüm okullarda geçerli <b>genel</b> konu listesi. Okullar bu listeye kendi konularını ekleyebilir ve istemedikleri genel konuları kendi öğrencileri için gizleyebilir. Bir konunun adını değiştirdiğinizde öğrencilerin o konudaki işaretleri korunur.</>}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="kt-duzen">
        <div className="kt-dersler">
          {['TYT', 'AYT'].map((o) => (
            <div key={o}>
              <div className="ns" style={{ padding: '8px 4px 4px' }}>{o}</div>
              {veri.dersler.filter((d) => d.oturum === o).map((d) => (
                <button key={d.kod} className={`kt-ders${d.kod === aktif.kod ? ' secili' : ''}`} onClick={() => setDers(d.kod)}>
                  <span>{d.ad}</span><small>{say(d)} konu</small>
                </button>
              ))}
            </div>
          ))}
        </div>
        <div className="card" style={{ margin: 0 }}>
          <div className="ct">{aktif.oturum} · {aktif.ad}</div>
          <form className="kl-ekle" onSubmit={ekle}>
            <input className="auth-input" maxLength={120} placeholder={okulGorunumu ? 'Okulunuza özel yeni konu…' : 'Genel listeye yeni konu…'} value={yeni} onChange={(e) => setYeni(e.target.value)} />
            <button className="btn" disabled={bekle || !yeni.trim()}>+ Konu ekle</button>
          </form>
          <div className="kl-liste">
            {aktif.konular.length === 0 && <div className="bos-durum">Bu derste konu yok.</div>}
            {aktif.konular.map((k) => <KonuSatiri key={k.id} k={k} okulId={okulGorunumu ? okulId : null} yenile={yenile} hata={setHata} />)}
          </div>
        </div>
      </div>
    </>
  )
}
