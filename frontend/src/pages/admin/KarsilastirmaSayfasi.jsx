// [2026-10-10] Okul karşılaştırması (süper admin) — kurumlara rapor: metrik seç, okulları kıyasla, Excel al.
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'

const bicim = (m, v) => (v == null ? '—' : m.tur === 'yuzde' ? `%${v}` : m.tur === 'net' ? Number(v).toLocaleString('tr-TR') : Number(v).toLocaleString('tr-TR'))

export default function KarsilastirmaSayfasi() {
  const [v, setV] = useState(null)
  const [metrik, setMetrik] = useState('tamamlama')
  const [secili, setSecili] = useState(new Set())
  const [hata, setHata] = useState(null)
  useEffect(() => { api.okulKarsilastirma().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [])
  const m = v?.metrikler.find((x) => x.k === metrik)
  const sirali = useMemo(() => (v ? [...v.okullar].filter((o) => o[metrik] != null).sort((a, b) => b[metrik] - a[metrik]) : []), [v, metrik])
  if (!v) return <div className="pg pg-genis"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>
  const enCok = m.tur === 'yuzde' ? 100 : Math.max(1, ...sirali.map((o) => o[metrik]))
  const eksik = v.okullar.length - sirali.length
  const ort = sirali.length ? sirali.reduce((a, o) => a + o[metrik], 0) / sirali.length : null
  const degis = (id) => { const s = new Set(secili); s.has(id) ? s.delete(id) : s.add(id); setSecili(s) }
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Okul Karşılaştırması</div>
        <div className="ps">Okulların katılım ve sonuç göstergelerini yan yana görün. Birden çok okulu olan kurumlara seçtiğiniz okulların tablosunu Excel olarak iletebilirsiniz.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="eu-filtre">
        {v.metrikler.map((x) => <button key={x.k} className={metrik === x.k ? 'secili' : ''} onClick={() => setMetrik(x.k)}>{x.ad}</button>)}
      </div>
      <div className="card">
        <div className="ct">{m.ad}{ort != null && <span className="yp-ince" style={{ marginLeft: 8, textTransform: 'none', letterSpacing: 0 }}>· ortalama {bicim(m, m.tur === 'yuzde' ? Math.round(ort) : Math.round(ort * 10) / 10)}</span>}</div>
        {sirali.length === 0 ? <div className="bos-durum">Bu gösterge için veri yok.</div> : (
          <div className="ks-cubuklar">
            {sirali.map((o) => (
              <div key={o.id} className="ks-satir" title={`${o.ad}: ${bicim(m, o[metrik])}`}>
                <Link to={`/admin/okul/${o.id}`} className="ks-ad">{o.ad}</Link>
                <div className="ks-iz"><div style={{ width: `${Math.max(1.5, (100 * o[metrik]) / enCok)}%` }} /></div>
                <b>{bicim(m, o[metrik])}</b>
              </div>
            ))}
          </div>
        )}
        {eksik > 0 && <div className="yp-ince" style={{ marginTop: 8 }}>{eksik} okulda bu gösterge yok (modül paketinde değil ya da henüz veri yok).</div>}
      </div>
      <div className="card" style={{ overflowX: 'auto' }}>
        <div className="ct" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span>Tüm göstergeler</span>
          <button className="rd-dugme" onClick={() => api.okulKarsilastirmaExcel([...secili]).catch((e) => setHata(e.detail || 'İndirilemedi.'))}>📊 Excel{secili.size ? ` (${secili.size} okul)` : ' (tümü)'}</button>
        </div>
        <table className="yp-tablo">
          <thead><tr><th /><th>Okul</th><th>Paket</th>{v.metrikler.map((x) => <th key={x.k} className={x.k === metrik ? 'ks-secili' : ''}>{x.ad}</th>)}</tr></thead>
          <tbody>
            {v.okullar.map((o) => (
              <tr key={o.id}>
                <td><input type="checkbox" aria-label={`${o.ad} seç`} checked={secili.has(o.id)} onChange={() => degis(o.id)} /></td>
                <td><Link to={`/admin/okul/${o.id}`} className="ak-link">{o.ad}</Link></td>
                <td className="yp-ince">{o.paket}</td>
                {v.metrikler.map((x) => <td key={x.k} className={x.k === metrik ? 'ks-secili' : ''}>{bicim(x, o[x.k])}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="yp-ince" style={{ marginTop: 8 }}>Excel için okulları işaretleyin; işaret yoksa tüm okullar alınır. “—”: modül okulun paketinde yok ya da veri yok.</div>
      </div>
    </div>
  )
}
