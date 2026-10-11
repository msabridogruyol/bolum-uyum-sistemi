// [2026-10-10] İş Hayatı → 'dersler' sekmesi: Okulda Öğretilmeyenler.
// Kısa dersler (kartlar + mini sınav + kaynaklar). Bordro dersindeki örnek, asgari_ucret tablosundaki güncel dönemden gelir (uydurma tutar yok).
// Uçlar: GET /ogrenci/is-hayati/dersler, POST /ogrenci/is-hayati/dersler/{kod}/sinav (backend/app/api/is_hayati_dersler.py;
// içerik backend/app/data/is_hayati_dersler.json)
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { tl } from './ortak'

function BordroOrnegi({ b }) {
  if (!b) return <div className="yp-ince">Asgari ücret verisi henüz yüklenmediği için örnek gösterilemiyor.</div>
  const satir = (ad, deger, eksi) => (
    <tr><td>{ad}</td><td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>{deger == null ? '—' : `${eksi && deger ? '− ' : ''}${tl(deger)}`}</td></tr>
  )
  return (
    <div className="ihd-bordro">
      <table>
        <tbody>
          {satir('Brüt asgari ücret', b.brut)}
          {b.hesap_tutarli && satir('SGK primi işçi payı (%14)', b.sgk_isci, true)}
          {b.hesap_tutarli && satir('İşsizlik sigortası işçi payı (%1)', b.issizlik_isci, true)}
          {b.hesap_tutarli && satir('Gelir vergisi (asgari ücret istisnası)', 0)}
          {b.hesap_tutarli && satir('Damga vergisi (asgari ücret istisnası)', 0)}
          <tr className="toplam"><td>Net (hesabına yatan)</td><td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>{tl(b.net)}</td></tr>
        </tbody>
      </table>
      <div className="yp-ince">Dönem: {b.donem} · Kaynak: {b.kaynak}. Tutarlar küsuratsız gösterilmiştir.</div>
    </div>
  )
}

function Sinav({ ders, onBitti }) {
  const [cevap, setCevap] = useState(() => ders.sinav.map(() => null))
  const [sonuc, setSonuc] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  async function gonder() {
    setBekle(true); setHata(null)
    try { const r = await api.isHayatiDersSinav(ders.kod, cevap); setSonuc(r); onBitti(r) } catch (e) { setHata(e.detail || 'Gönderilemedi.') } finally { setBekle(false) }
  }
  return (
    <div className="ihd-sinav">
      <div className="ihz-ara-baslik">📝 Mini sınav</div>
      {ders.sinav.map((s, i) => (
        <fieldset key={i} className="ihd-soru">
          <legend>{i + 1}. {s.soru}</legend>
          {s.secenekler.map((x, j) => {
            const r = sonuc?.sonuc[i]
            const sinif = r ? (j === r.dogru ? ' dogru' : j === cevap[i] ? ' yanlis' : '') : ''
            return (
              <label key={j} className={`ihd-secenek${cevap[i] === j ? ' secili' : ''}${sinif}`}>
                <input type="radio" name={`s${i}`} checked={cevap[i] === j} disabled={!!sonuc}
                  onChange={() => setCevap(cevap.map((c, k) => (k === i ? j : c)))} />
                <span>{x}</span>
              </label>
            )
          })}
          {sonuc && <div className={`ms-geri ${sonuc.sonuc[i].dogru_mu ? 'iyi' : ''}`} style={{ marginTop: 6 }}>{sonuc.sonuc[i].dogru_mu ? '✓ ' : ''}{sonuc.sonuc[i].aciklama}</div>}
        </fieldset>
      ))}
      {hata && <div className="auth-error">{hata}</div>}
      {sonuc
        ? <div className="ms-kutu iyi"><b>{sonuc.toplam} sorudan {sonuc.puan} doğru.</b> {sonuc.puan === sonuc.toplam ? 'Harika! 🎉' : 'Açıklamaları okuyup istediğin zaman yeniden deneyebilirsin.'}
            <button className="yp-mini" style={{ marginLeft: 8 }} onClick={() => { setSonuc(null); setCevap(ders.sinav.map(() => null)) }}>↻ Yeniden dene</button></div>
        : <button className="btn" disabled={bekle || cevap.some((c) => c == null)} onClick={gonder}>{bekle ? <span className="spin" /> : 'Cevaplarımı kontrol et'}</button>}
    </div>
  )
}

function Ders({ d, bordro, genelNot, onKapat, onIlerleme }) {
  const [k, setK] = useState(0)
  const n = d.kartlar.length
  const sinavda = k >= n
  const kart = d.kartlar[Math.min(k, n - 1)]
  return (
    <div className="card ihd-ders">
      <div className="ihz-tur-ust">
        <button className="yp-mini" onClick={onKapat}>← Dersler</button>
        <b className="ihz-tur-ad">{d.ikon} {d.baslik}</b>
        <span className="yp-ince">{sinavda ? 'Sınav' : `${k + 1} / ${n}`}</span>
      </div>
      <div className="ihd-noktalar" aria-hidden="true">
        {[...d.kartlar, null].map((_, j) => <i key={j} className={j === k ? 'simdi' : j < k ? 'gecti' : ''} />)}
      </div>
      {!sinavda && (
        <div key={k} className="ihd-kart">
          <div className="ihd-kart-baslik">{kart.baslik}</div>
          <div className="ihd-kart-metin">{kart.metin}</div>
          {kart.tip === 'bordro' && <BordroOrnegi b={bordro} />}
        </div>
      )}
      {sinavda && <Sinav ders={d} onBitti={onIlerleme} />}
      <div className="ms-alt">
        {k > 0 && <button className="btn sec" onClick={() => setK(k - 1)}>← Önceki</button>}
        <span style={{ marginRight: 'auto' }} />
        {!sinavda && <button className="btn" onClick={() => setK(k + 1)}>{k === n - 1 ? 'Mini sınava geç →' : 'Sonraki →'}</button>}
      </div>
      <div className="ihd-kaynak">
        <div className="ihd-onemli">⚠️ {genelNot}</div>
        <b>Kaynaklar</b>
        <ul>
          {d.kaynaklar.map((x) => <li key={x.ad}>{x.url ? <a href={x.url} target="_blank" rel="noreferrer">{x.ad}</a> : x.ad}</li>)}
        </ul>
        <div className="yp-ince">Son kontrol: {d.son_kontrol}</div>
      </div>
    </div>
  )
}

export default function OkuldaOgretilmeyenler() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [acik, setAcik] = useState(null)
  useEffect(() => { api.isHayatiDersler().then(setV).catch((e) => setHata(e.detail || 'Dersler yüklenemedi.')) }, [])
  if (hata) return <div className="auth-error">{hata}</div>
  if (!v) return <div className="bos-durum">Yükleniyor…</div>

  const ders = v.dersler.find((d) => d.kod === acik)
  if (ders) {
    return <Ders d={ders} bordro={v.bordro} genelNot={v.not} onKapat={() => setAcik(null)}
      onIlerleme={(r) => setV({ ...v, dersler: v.dersler.map((d) => (d.kod === ders.kod
        ? { ...d, ilerleme: { puan: Math.max(r.puan, d.ilerleme?.puan || 0), toplam: r.toplam } } : d)) })} />
  }
  const tamam = v.dersler.filter((d) => d.ilerleme).length
  return (
    <div>
      <div className="card ihz-giris">
        <div className="ihz-giris-ust">
          <span className="ihz-buyuk-ikon" aria-hidden="true">🧰</span>
          <div style={{ flex: 1 }}>
            <div className="ihz-baslik">Okulda öğretilmeyenler</div>
            <div className="ihz-metin">Maaş bordrosu, sözleşme, izin hakları, profesyonel e-posta… İş hayatına başlamadan bilmen gereken pratik bilgiler,
              birkaç dakikalık kısa derslerle.</div>
            <div className="ihd-ilerleme"><span style={{ width: `${(100 * tamam) / v.dersler.length}%` }} /></div>
            <div className="yp-ince">{tamam} / {v.dersler.length} ders tamamlandı</div>
          </div>
        </div>
      </div>
      <div className="ihd-liste">
        {v.dersler.map((d) => (
          <button key={d.kod} className={`ihd-kutu${d.ilerleme ? ' bitti' : ''}`} onClick={() => setAcik(d.kod)}>
            <span className="ihd-kutu-ikon" aria-hidden="true">{d.ikon}</span>
            <span className="ihd-kutu-govde">
              <b>{d.baslik}</b>
              <span>{d.ozet}</span>
              <span className="ihd-kutu-alt">{d.kartlar.length} kart · {d.sinav.length} soru
                {d.ilerleme && <em> · ✓ en iyi: {d.ilerleme.puan}/{d.ilerleme.toplam}</em>}</span>
            </span>
          </button>
        ))}
      </div>
      <div className="yp-ince" style={{ marginTop: 8 }}>{v.not}</div>
    </div>
  )
}
