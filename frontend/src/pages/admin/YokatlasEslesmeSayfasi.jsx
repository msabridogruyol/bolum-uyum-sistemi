// [2026-10-10] YÖK Atlas eşleştirme: sistemdeki bölüm adı ↔ YÖK Atlas program grubu.
// Otomatik eşleşmeyen bölümler için benzer adaylar önerilir; tek tıkla ya da listeden seçilerek elle eşleştirilir.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'

const DURUM = { otomatik: ['✓ Otomatik', 'gr'], elle: ['✎ Elle', 'pu'], yok: ['✗ Eşleşmedi', 'am'] }

function Satir({ b, grupAdlari, onKaydet }) {
  const [ara, setAra] = useState('')
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const kaydet = async (gruplar) => {
    setBekle(true); setHata(null)
    try { await onKaydet(b.id, gruplar) } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  const ekle = () => { if (ara.trim()) { kaydet([...(b.durum === 'elle' ? b.gruplar : []), ara.trim()]); setAra('') } }
  const [ad, renk] = DURUM[b.durum]
  return (
    <tr>
      <td><b>{b.ad}</b><div className="yp-ince">{b.alan || '—'}{b.ozel_yetenek_alani && ' · çoğunlukla özel yetenek'}</div></td>
      <td><span className={`kc-durum kc-durum-${renk}`}>{ad}</span>{b.program_sayisi != null && <div className="yp-ince" style={{ marginTop: 4 }}>{b.program_sayisi} program (önbellek)</div>}</td>
      <td>
        {b.gruplar.map((g) => <span key={g} className="ak-cip ak-cip-ortak">{g}</span>)}
        {b.durum === 'yok' && b.adaylar.length > 0 && (
          <div><span className="yp-ince">Öneriler: </span>
            {b.adaylar.map((a) => <button key={a.ad} className="kl-ilgi" disabled={bekle} onClick={() => kaydet([a.ad])} title="Bu programla eşleştir">{a.ad} <small>%{a.puan}</small></button>)}
          </div>
        )}
        {b.durum === 'yok' && b.adaylar.length === 0 && <div className="yp-ince">Benzer ad bulunamadı{b.ozel_yetenek_alani ? ' — öğrenciye "özel yetenek" açıklaması gösterilir' : ''}.</div>}
        {hata && <div className="auth-error" style={{ marginTop: 4 }}>{hata}</div>}
      </td>
      <td style={{ minWidth: 260 }}>
        <div style={{ display: 'flex', gap: 6 }}>
          <input className="yp-sec" list="yok-gruplar" value={ara} onChange={(e) => setAra(e.target.value)} placeholder="YÖK Atlas program adı ara…" style={{ flex: 1, minWidth: 0 }} />
          <button className="yp-mini" disabled={bekle || !ara.trim()} onClick={ekle}>{b.durum === 'elle' ? 'Ekle' : 'Eşle'}</button>
        </div>
        {b.durum === 'elle' && <button className="yp-mini" style={{ marginTop: 6 }} disabled={bekle} onClick={() => kaydet([])}>Otomatiğe dön</button>}
      </td>
    </tr>
  )
}

export default function YokatlasEslesmeSayfasi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [filtre, setFiltre] = useState('yok')
  const [arama, setArama] = useState('')
  const yukle = () => api.yokatlasEslesme().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [])
  const kaydet = async (id, gruplar) => { await api.yokatlasEslestir(id, gruplar); await yukle() }
  const liste = useMemo(() => (v?.bolumler || []).filter((b) => (filtre === 'hepsi' || b.durum === filtre)
    && (!arama || b.ad.toLocaleLowerCase('tr-TR').includes(arama.toLocaleLowerCase('tr-TR')))), [v, filtre, arama])

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">YÖK Atlas Eşleştirme</div>
        <div className="ps">Bölüm penceresindeki üniversite / taban puan listesi, bölüm adının YÖK Atlas'taki program adıyla eşleşmesine bağlıdır. Ad birebir aynı değilse burada önerilerden seçin ya da YÖK Atlas adını arayıp eşleyin. Bir bölüm birden fazla YÖK programıyla eşleşebilir (ör. "Grafik Tasarım" + "Grafik Tasarımı").</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v && !hata && <div className="bos-durum">YÖK Atlas program listesi alınıyor… (ilk açılışta 10-20 sn sürebilir)</div>}
      {v && (
        <>
          <div className="yp-kpi-grid" style={{ marginBottom: 14 }}>
            <div className="yp-kpi"><div className="yp-kpi-e">Bölüm</div><div className="yp-kpi-d">{v.ozet.toplam}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Otomatik eşleşen</div><div className="yp-kpi-d" style={{ color: 'var(--gr)' }}>{v.ozet.otomatik}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Elle eşlenen</div><div className="yp-kpi-d">{v.ozet.elle}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Eşleşmeyen</div><div className="yp-kpi-d" style={{ color: 'var(--am)' }}>{v.ozet.yok}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">YÖK Atlas programı</div><div className="yp-kpi-d">{v.grup_adlari.length}</div></div>
          </div>
          <div className="kc-filtre">
            {[['yok', `Eşleşmeyen (${v.ozet.yok})`], ['elle', `Elle (${v.ozet.elle})`], ['otomatik', `Otomatik (${v.ozet.otomatik})`], ['hepsi', 'Tümü']].map(([k, ad]) =>
              <button key={k} className={filtre === k ? 'aktif' : ''} onClick={() => setFiltre(k)}>{ad}</button>)}
            <input className="yp-sec" value={arama} onChange={(e) => setArama(e.target.value)} placeholder="Bölüm ara…" style={{ marginLeft: 'auto' }} />
          </div>
          <datalist id="yok-gruplar">{v.grup_adlari.map((g) => <option key={g} value={g} />)}</datalist>
          <div className="card" style={{ padding: 0, overflow: 'auto' }}>
            <table className="yp-tablo">
              <thead><tr><th>Bölüm</th><th>Durum</th><th>YÖK Atlas programı</th><th>Elle eşle</th></tr></thead>
              <tbody>{liste.map((b) => <Satir key={`${b.id}-${b.durum}-${b.gruplar.join()}`} b={b} grupAdlari={v.grup_adlari} onKaydet={kaydet} />)}</tbody>
            </table>
            {liste.length === 0 && <div className="bos-durum">Bu filtrede bölüm yok.</div>}
          </div>
        </>
      )}
    </div>
  )
}
