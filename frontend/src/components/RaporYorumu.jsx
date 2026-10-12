// [2026-10-12] Rapor yorumu: sayıların yanında "ne anlama geliyor, ne yapmalı, neden kaçınmalı".
// PDF raporlarındaki bölümün ekran karşılığı; içerik backend'de kural tabanlı üretilir (app/core/rapor/yorum.py).
//  - OgrenciRaporYorumu: öğrencinin kendisi (Profilim → Genel bakış, Raporlarım)
//  - YonetimOgrenciYorumu: öğrenci detayı — rehber / veli / sınıf öğretmeni / öğrenci gözüyle
//  - OkulRaporYorumu: Rapor Merkezi → Tek Bakışta (okul, sınıf düzeyi, şube)
import { useEffect, useState } from 'react'
import { api } from '../api/client'

const BASLIKLAR = {
  ogrenci: ['Bunu yap', 'Bundan kaçın', 'Güçlü yönlerini nasıl kullanırsın?', 'Gelişmek için küçük adımlar', 'Rehber öğretmeninle konuşabileceklerin'],
  veli: ['Yapabilecekleriniz', 'Kaçınmanız gerekenler', 'Güçlü yönlerini nasıl destekleyebilirsiniz?', 'Gelişebileceği alanlarda evde destek', 'Rehber öğretmenle görüşmede sorabilecekleriniz'],
  ogretmen: ['Önerilenler', 'Kaçınılması gerekenler', 'Güçlü yönlerini sınıfta değerlendirme', 'Gelişim için sınıf içi destek', ''],
  rehber: ['Yapılması gerekenler', 'Yapılmaması gerekenler', 'Güçlü yönlerin değerlendirilmesi', 'Gelişim için destek', 'Görüşme gündemi'],
  okul: ['Yapılması gerekenler', 'Yapılmaması gerekenler', 'Ortak güçlü yönlerden yararlanmak için', 'Ortak gelişim alanları için etkinlik önerisi', ''],
}

function Liste({ baslik, l }) {
  if (!l?.length || !baslik) return null
  return (
    <div className="ry-blok">
      <div className="ry-bb">{baslik}</div>
      <ul className="ry-liste">
        {l.map((x, i) => <li key={i}><b>{x.ad}:</b> {x.metin}</li>)}
      </ul>
    </div>
  )
}

export function RaporYorumuIcerik({ y, kitle = 'ogrenci', ozetBaslik = 'Kısaca' }) {
  if (!y) return null
  const [bYap, bKacin, bGuclu, bDestek, bGorusme] = BASLIKLAR[kitle] || BASLIKLAR.rehber
  const isler = y.isler?.length ? y.isler : null
  return (
    <div className="ry">
      {y.ozet?.length > 0 && (
        <div className="ry-ozet"><div className="ry-ozet-b">{ozetBaslik}</div><p>{y.ozet.map((c, i) => <span key={i}>{c}{i < y.ozet.length - 1 ? ' ' : ''}</span>)}</p></div>
      )}
      {isler && (
        <div className="ry-blok">
          <div className="ry-bb">Öncelikli işler</div>
          <div className="yp-tablo-kap">
            <table className="yp-tablo ry-isler">
              <thead><tr><th style={{ width: 28 }}>#</th><th>Ne yapılmalı?</th><th>Kim?</th><th>Ne zaman?</th></tr></thead>
              <tbody>
                {isler.map((x, i) => (
                  <tr key={i}>
                    <td>{i + 1}</td><td>{x.metin}</td><td className="yp-ince">{x.kim}</td>
                    <td><span className={`ry-zaman ry-z${x.oncelik}`}>{x.ne_zaman}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {(y.yap?.length > 0 && !isler) || y.kacin?.length > 0 ? (
        <div className={`ry-iki${isler || !y.yap?.length || !y.kacin?.length ? ' tek' : ''}`}>
          {!isler && y.yap?.length > 0 && (
            <div className="ry-yap">
              <div className="ry-bb">{bYap}</div>
              <ul>{y.yap.map((m, i) => <li key={i}>{m}</li>)}</ul>
            </div>
          )}
          {y.kacin?.length > 0 && (
            <div className="ry-kacin">
              <div className="ry-bb">{bKacin}</div>
              <ul>{y.kacin.map((m, i) => <li key={i}>{m}</li>)}</ul>
            </div>
          )}
        </div>
      ) : null}
      <Liste baslik={bGuclu} l={y.guclu} />
      <Liste baslik={bDestek} l={y.destek} />
      {y.gorusme?.length > 0 && bGorusme && (
        <div className="ry-blok">
          <div className="ry-bb">{bGorusme}</div>
          <ul className="ry-liste ry-gorusme">{y.gorusme.map((m, i) => <li key={i}>{m}</li>)}</ul>
        </div>
      )}
      {y.notlar?.map((n, i) => <div key={i} className="yp-ince ry-not">{n}</div>)}
    </div>
  )
}

function Kart({ baslik, altBaslik, sag, children, acik, onAc }) {
  return (
    <section className="card ry-kart">
      <button type="button" className="ry-ust" onClick={onAc} aria-expanded={acik}>
        <span className="ry-ikon" aria-hidden="true">🧭</span>
        <span className="ry-ust-metin"><b>{baslik}</b>{altBaslik && <small>{altBaslik}</small>}</span>
        <span className="ry-ok" aria-hidden="true">{acik ? '▾' : '▸'}</span>
      </button>
      {acik && <>{sag}{children}</>}
    </section>
  )
}

// Öğrencinin kendi yorumu
export function OgrenciRaporYorumu({ baslangicAcik = true }) {
  const [y, setY] = useState(null)
  const [acik, setAcik] = useState(baslangicAcik)
  useEffect(() => { api.raporYorumum().then(setY).catch(() => setY(false)) }, [])
  if (y === false || (y && !y.ozet?.length && !y.yap?.length)) return null
  return (
    <Kart baslik={y?.baslik || 'Sonuçların ne anlatıyor, şimdi ne yapmalısın?'} altBaslik="Sonuçlarının kısa yorumu ve bu dönem için öneriler"
      acik={acik} onAc={() => setAcik(!acik)}>
      {!y ? <div className="bos-durum yukleniyor">Yükleniyor…</div> : <RaporYorumuIcerik y={y} kitle="ogrenci" />}
    </Kart>
  )
}

// Öğrenci detayı (rehber öğretmen / okul yetkilisi): aynı sonuçlar farklı okuyucunun gözüyle
const KITLE_SEC = [['rehber', 'Rehber öğretmen'], ['veli', 'Veli için'], ['ogretmen', 'Sınıf öğretmeni için'], ['ogrenci', 'Öğrenci için']]
export function YonetimOgrenciYorumu({ ogrenciId }) {
  const [kitle, setKitle] = useState('rehber')
  const [v, setV] = useState({})
  const [acik, setAcik] = useState(true)
  useEffect(() => {
    if (v[kitle] !== undefined) return
    api.ogrenciRaporYorumu(ogrenciId, kitle).then((y) => setV((o) => ({ ...o, [kitle]: y }))).catch(() => setV((o) => ({ ...o, [kitle]: false })))
  }, [ogrenciId, kitle]) // eslint-disable-line react-hooks/exhaustive-deps
  const y = v[kitle]
  return (
    <Kart baslik="Değerlendirme ve öneriler" altBaslik="Sonuçların yorumu, yapılması ve kaçınılması gerekenler; veli ve sınıf öğretmeni raporlarında yazanlar"
      acik={acik} onAc={() => setAcik(!acik)}
      sag={(
        <div className="ry-kitle" role="tablist" aria-label="Kimin gözüyle">
          {KITLE_SEC.map(([k, ad]) => <button key={k} role="tab" aria-selected={kitle === k} className={kitle === k ? 'aktif' : ''} onClick={() => setKitle(k)}>{ad}</button>)}
        </div>
      )}>
      {y === undefined ? <div className="bos-durum yukleniyor">Yükleniyor…</div>
        : y === false ? <div className="bos-durum">Yorum yüklenemedi.</div>
          : <RaporYorumuIcerik y={y} kitle={kitle} />}
    </Kart>
  )
}

// Okul / sınıf düzeyi / şube
export function OkulRaporYorumu({ okulId, sinif = '', sube = '' }) {
  const [y, setY] = useState(null)
  const [acik, setAcik] = useState(true)
  useEffect(() => {
    let iptal = false
    setY(null)
    api.okulRaporYorumu(okulId, { sinif, sube }).then((d) => { if (!iptal) setY(d) }).catch(() => { if (!iptal) setY(false) })
    return () => { iptal = true }
  }, [okulId, sinif, sube])
  if (y === false) return null
  return (
    <Kart baslik="Ne yapılmalı?" altBaslik="Yönetici özeti, öncelikli işler (kim / ne zaman) ve yapılmaması gerekenler"
      acik={acik} onAc={() => setAcik(!acik)}>
      {!y ? <div className="bos-durum yukleniyor">Yükleniyor…</div> : <RaporYorumuIcerik y={y} kitle="okul" ozetBaslik="Yönetici özeti" />}
    </Kart>
  )
}
