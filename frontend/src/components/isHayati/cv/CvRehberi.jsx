// [2026-10-11] CV Atölyesi → "CV Rehberi" (ilk alt sekme): CV nedir, türleri, bölümler, eylem fiilleri, yapılmaması gerekenler, ATS,
// başvuru. İçerik: GET /ogrenci/is-hayati/cv/rehber (backend/app/data/cv_rehberi.json). Mini sınav istemcide puanlanır (not tutulmaz);
// hangi konunun okunduğu yalnızca bu tarayıcıda (localStorage) hatırlanır.
import { useEffect, useRef, useState } from 'react'
import { api } from '../../../api/client'

const ANAHTAR = 'fz-cv-rehber'
function oku() { try { return JSON.parse(localStorage.getItem(ANAHTAR) || 'null') || {} } catch { return {} } }
function yaz(v) { try { localStorage.setItem(ANAHTAR, JSON.stringify(v)) } catch { /* depolama kapalı */ } }

function MiniSinav({ sorular, onBitti }) {
  const [cevap, setCevap] = useState(() => sorular.map(() => null))
  const [bitti, setBitti] = useState(false)
  const dogru = sorular.filter((s, i) => cevap[i] === s.dogru).length
  return (
    <div className="ihd-sinav cvr-sinav">
      <div className="ihz-ara-baslik">📝 Kendini kontrol et</div>
      {sorular.map((s, i) => (
        <fieldset key={i} className="ihd-soru">
          <legend>{i + 1}. {s.soru}</legend>
          {s.secenekler.map((x, j) => {
            const sinif = bitti ? (j === s.dogru ? ' dogru' : j === cevap[i] ? ' yanlis' : '') : ''
            return (
              <label key={j} className={`ihd-secenek${cevap[i] === j ? ' secili' : ''}${sinif}`}>
                <input type="radio" name={`cvr-${s.soru.slice(0, 20)}-${i}`} checked={cevap[i] === j} disabled={bitti}
                  onChange={() => setCevap(cevap.map((c, k) => (k === i ? j : c)))} />
                <span>{x}</span>
              </label>
            )
          })}
          {bitti && <div className={`ms-geri ${cevap[i] === s.dogru ? 'iyi' : ''}`} style={{ marginTop: 6 }}>{cevap[i] === s.dogru ? '✓ ' : ''}{s.aciklama}</div>}
        </fieldset>
      ))}
      {bitti
        ? <div className="ms-kutu iyi"><b>{sorular.length} sorudan {dogru} doğru.</b> {dogru === sorular.length ? 'Harika! 🎉' : 'Açıklamaları oku; istediğin zaman yeniden deneyebilirsin.'}
            <button type="button" className="yp-mini" style={{ marginLeft: 8 }} onClick={() => { setBitti(false); setCevap(sorular.map(() => null)) }}>↻ Yeniden dene</button></div>
        : <button type="button" className="btn" disabled={cevap.some((c) => c == null)} onClick={() => { setBitti(true); onBitti(dogru) }}>Cevaplarımı kontrol et</button>}
    </div>
  )
}

function Blok({ b }) {
  if (b.tur === 'metin') return <p className="cvr-metin">{b.metin}</p>
  if (b.tur === 'not') return <div className={`cvr-not ${b.renk || 'bilgi'}`}>{b.metin}</div>
  if (b.tur === 'liste') return (
    <div>
      {b.baslik && <div className="cvr-alt-baslik">{b.baslik}</div>}
      <ul className="cvr-liste">{b.maddeler.map((m) => <li key={m}>{m}</li>)}</ul>
    </div>
  )
  if (b.tur === 'kartlar') return (
    <div>
      {b.baslik && <div className="cvr-alt-baslik">{b.baslik}</div>}
      <div className="cvr-kartlar">
        {b.kartlar.map((k) => (
          <div key={k.baslik} className="cvr-kart">
            <div className="cvr-kart-ust"><span aria-hidden="true">{k.ikon}</span><b>{k.baslik}</b></div>
            <div>{k.metin}</div>
          </div>
        ))}
      </div>
    </div>
  )
  if (b.tur === 'cift') return (
    <div>
      {b.baslik && <div className="cvr-alt-baslik">{b.baslik}</div>}
      {b.ciftler.map((c) => (
        <div key={c.kotu} className="cvr-cift">
          <div className="cvr-kotu"><span className="cvr-etiket">✕ Yerine</span>{c.kotu}</div>
          <div className="cvr-iyi"><span className="cvr-etiket">✓ Şöyle</span>{c.iyi}</div>
          {c.neden && <div className="yp-ince cvr-neden">{c.neden}</div>}
        </div>
      ))}
    </div>
  )
  if (b.tur === 'fiiller') return (
    <div className="cvr-fiiller">
      {b.gruplar.map((g) => (
        <div key={g.ad} className="cvr-fiil-grup">
          <div className="cvr-alt-baslik" style={{ marginTop: 0 }}>{g.ad}</div>
          <div className="cvr-ciplar">{g.fiiller.map((f) => <span key={f} className="cvr-cip">{f}</span>)}</div>
        </div>
      ))}
    </div>
  )
  if (b.tur === 'ornek') return (
    <div>
      {b.baslik && <div className="cvr-alt-baslik">{b.baslik}</div>}
      <div className="cva-ornek-etiket" style={{ marginBottom: 6 }}>Örnek — kurgusal</div>
      <div className="cva-mektup">{b.metin}</div>
    </div>
  )
  return null
}

export default function CvRehberi({ onGit }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [acik, setAcik] = useState(null)
  const [durum, setDurumHam] = useState(oku)
  const kok = useRef(null)
  useEffect(() => { api.isHayatiCvRehber().then(setV).catch((e) => setHata(e.detail || 'Rehber yüklenemedi.')) }, [])
  const setDurum = (x) => { setDurumHam(x); yaz(x) }

  function ac(kod) {
    const yeni = acik === kod ? null : kod
    setAcik(yeni)
    if (yeni && !durum.okunan?.[yeni]) setDurum({ ...durum, okunan: { ...(durum.okunan || {}), [yeni]: true } })
    if (yeni) setTimeout(() => kok.current?.querySelector(`[data-konu="${yeni}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 30)
  }

  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const okunan = v.konular.filter((k) => durum.okunan?.[k.kod]).length
  const sira = v.konular.findIndex((k) => k.kod === acik)

  return (
    <div ref={kok}>
      <div className="card cvr-hero">
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ fontWeight: 800, fontSize: 16 }}>📚 CV'ye yeni misin? Buradan başla.</div>
          <div className="yp-ince" style={{ lineHeight: 1.6, marginTop: 4, fontSize: 12.5 }}>
            {v.konular.length} kısa konu: CV nedir, nasıl yazılır, başvuru sistemleri (ATS) onu nasıl okur. Her konunun sonunda 2–3 soruluk mini sınav var.
            Hazır olduğunda <button type="button" className="hg-link" style={{ color: 'var(--okul-c)', fontSize: 12.5 }} onClick={() => onGit('olustur')}>CV'ni oluştur →</button>
          </div>
        </div>
        <div className="cvr-ilerleme" aria-label={`${okunan} / ${v.konular.length} konu açıldı`}>
          <b>{okunan}</b><span>/{v.konular.length}</span>
          <div className="qtrack" style={{ margin: '6px 0 0', width: 90 }}><div className="qfill" style={{ width: `${(100 * okunan) / v.konular.length}%` }} /></div>
        </div>
      </div>

      <div className="cvr-konular">
        {v.konular.map((k, i) => {
          const ac_ = acik === k.kod
          const puan = durum.sinav?.[k.kod]
          return (
            <section key={k.kod} data-konu={k.kod} className={`card cvr-konu${ac_ ? ' acik' : ''}`}>
              <button type="button" className="cvr-konu-ust" aria-expanded={ac_} onClick={() => ac(k.kod)}>
                <span className="cvr-ikon" aria-hidden="true">{k.ikon}</span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span className="cvr-konu-ad">{i + 1}. {k.baslik}</span>
                  <span className="cvr-konu-ozet">{k.ozet}</span>
                </span>
                {puan != null
                  ? <span className={`pf-rozet${puan === k.sinav.length ? ' onay' : ''}`}>{puan}/{k.sinav.length}</span>
                  : durum.okunan?.[k.kod] && <span className="pf-rozet">✓ açıldı</span>}
                <span className="cvr-ok" aria-hidden="true">{ac_ ? '−' : '+'}</span>
              </button>
              {ac_ && (
                <div className="cvr-govde">
                  {k.bloklar.map((b, j) => <Blok key={j} b={b} />)}
                  {k.kod === 'ats' && <div className="cvr-not iyi">Kendi CV'nin bir ATS'ye nasıl göründüğünü görmek ister misin? <button type="button" className="hg-link" style={{ color: 'var(--okul-c)', fontSize: 12.5 }} onClick={() => onGit('ats')}>ATS kontrolünü dene →</button></div>}
                  <MiniSinav key={k.kod} sorular={k.sinav} onBitti={(n) => setDurum({ ...durum, okunan: { ...(durum.okunan || {}), [k.kod]: true }, sinav: { ...(durum.sinav || {}), [k.kod]: n } })} />
                  <details className="cvr-kaynak">
                    <summary>Kaynaklar · son kontrol: {v.son_kontrol}</summary>
                    <ul>
                      {k.kaynaklar.map((id) => v.kaynaklar[id]).filter(Boolean).map((x) => (
                        <li key={x.url}><a href={x.url} target="_blank" rel="noopener noreferrer">{x.ad}</a><div className="yp-ince">{x.not}</div></li>
                      ))}
                    </ul>
                  </details>
                  <div className="cvr-alt-gezinti">
                    {sira > 0 && <button type="button" className="btn sec" onClick={() => ac(v.konular[sira - 1].kod)}>← Önceki</button>}
                    {sira < v.konular.length - 1
                      ? <button type="button" className="btn" onClick={() => ac(v.konular[sira + 1].kod)}>Sonraki konu →</button>
                      : <button type="button" className="btn" onClick={() => onGit('olustur')}>CV'ni oluşturmaya geç →</button>}
                  </div>
                </div>
              )}
            </section>
          )
        })}
      </div>
      <div className="yp-ince" style={{ marginTop: 10, lineHeight: 1.5 }}>Örneklerdeki kişi, okul ve kurumlar kurgusaldır. İçerik son kontrol: {v.son_kontrol}.</div>
    </div>
  )
}
