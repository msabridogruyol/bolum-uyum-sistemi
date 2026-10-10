// [2026-10-10] Profilim → İlgi & Kulüpler: 20 soruluk kısa ilgi testi ve okul kulübü önerileri.
// Bu test bölüm önerilerini etkilemez; sosyal etkinlik / kulüp seçimi için.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

const OLCEK = [
  [1, 'Hiç hoşlanmam'], [2, 'Pek hoşlanmam'], [3, 'Kararsızım'], [4, 'Hoşlanırım'], [5, 'Çok hoşlanırım'],
]

function Test({ sorular, onceki, onBitti, onIptal }) {
  const [c, setC] = useState(onceki || {})
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const sayi = Object.keys(c).length
  const gonder = async () => {
    setBekle(true); setHata(null)
    try { onBitti(await api.ilgiTestiGonder(c)) } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  return (
    <div className="card">
      <div className="ik-baslik">
        <div>
          <div className="ik-bt">Kısa ilgi testi</div>
          <div className="ps" style={{ margin: 0 }}>Her etkinlik için ne kadar hoşlanacağını seç. Doğru ya da yanlış cevap yok; yaklaşık 3 dakika.</div>
        </div>
        <div className="ik-sayac">{sayi}/{sorular.length}</div>
      </div>
      <div className="qtrack" style={{ margin: "10px 0 16px" }}><div className="qfill" style={{ width: `${(100 * sayi) / sorular.length}%` }} /></div>
      <ol className="ik-sorular">
        {sorular.map((s, i) => (
          <li key={s.kod} className={c[s.kod] ? 'cevapli' : ''}>
            <div className="ik-soru"><span>{i + 1}.</span> {s.metin}</div>
            <div className="ik-olcek" role="radiogroup" aria-label={s.metin}>
              {OLCEK.map(([v, ad]) => (
                <button key={v} type="button" role="radio" aria-checked={c[s.kod] === v} className={c[s.kod] === v ? 'secili' : ''}
                  onClick={() => setC({ ...c, [s.kod]: v })} title={ad}>
                  <b>{v}</b><small>{ad}</small>
                </button>
              ))}
            </div>
          </li>
        ))}
      </ol>
      {hata && <div className="auth-error">{hata}</div>}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <button className="btn" disabled={bekle || sayi < sorular.length} onClick={gonder}>{bekle ? <span className="spin" /> : 'Sonucumu gör'}</button>
        {onIptal && <button className="btn sec" onClick={onIptal}>Vazgeç</button>}
        {sayi < sorular.length && <span className="yp-ince">{sorular.length - sayi} soru kaldı</span>}
      </div>
    </div>
  )
}

function Sonuc({ v, onYeniden }) {
  const sirali = useMemo(() => v.boyutlar.map((b) => ({ ...b, puan: v.sonuc.puanlar[b.kod] ?? 0 })).sort((a, b) => b.puan - a.puan), [v])
  return (
    <>
      <div className="card">
        <div className="ik-baslik">
          <div className="ct" style={{ margin: 0 }}>İlgi profilin</div>
          <button className="btn sec" onClick={onYeniden}>Testi yeniden çöz</button>
        </div>
        <div className="ik-boyutlar">
          {sirali.map((b, i) => (
            <div key={b.kod} className={`ik-boyut${i < 3 ? ' ust' : ''}`}>
              <span className="ik-ikon" aria-hidden="true">{b.ikon}</span>
              <span className="ik-ad">{b.ad}</span>
              <div className="ik-cubuk"><div style={{ width: `${Math.max(3, b.puan)}%` }} /></div>
              <b>%{b.puan}</b>
            </div>
          ))}
        </div>
        <div className="yp-ince" style={{ marginTop: 10 }}>Bu test bölüm önerilerini değiştirmez. Okulda hangi topluluklarda kendini daha iyi ifade edebileceğini bulmana yardımcı olur.</div>
      </div>
      <div className="card">
        <div className="ct">{v.okul_kulubu_var ? 'Okulundaki kulüplerden sana önerilenler' : 'Sana uygun kulüp türleri'}</div>
        {!v.okul_kulubu_var && <div className="yp-uyari" style={{ marginBottom: 12 }}>Okulun kulüp listesini henüz girmedi. Aşağıdakiler lise kulüplerinde yaygın olanlardır; okulunda yoksa rehber öğretmenine kurulmasını önerebilirsin.</div>}
        <div className="ik-kulupler">
          {v.oneriler.map((k, i) => (
            <div key={k.id ?? k.ad} className="ik-kulup">
              <div className="ik-kulup-ust"><span className="ik-sira">{i + 1}</span><b>{k.ad}</b><span className="ik-uyum">%{k.uyum}</span></div>
              {k.aciklama && <div className="ik-ac">{k.aciklama}</div>}
              <div className="ik-neden">{k.neden}</div>
              {(k.sorumlu || k.bulusma) && <div className="yp-ince">{k.sorumlu && <>👤 {k.sorumlu}</>}{k.sorumlu && k.bulusma && ' · '}{k.bulusma && <>🗓 {k.bulusma}</>}</div>}
            </div>
          ))}
        </div>
      </div>
    </>
  )
}

export default function IlgiKulupSekmesi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [testte, setTestte] = useState(false)
  useEffect(() => { api.ilgiTesti().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [])
  if (hata) return <div className="auth-error">{hata}</div>
  if (!v) return <div className="bos-durum">Yükleniyor…</div>
  if (!v.sonuc || testte) {
    return (
      <>
        {!v.sonuc && (
          <div className="ik-giris">
            <span aria-hidden="true">🎯</span>
            <div><b>Hangi kulüp sana göre?</b><div>20 kısa soruyla ilgi alanlarını belirleyelim ve okulundaki kulüplerden sana uygun olanları önerelim.</div></div>
          </div>
        )}
        <Test sorular={v.sorular} onceki={testte ? v.sonuc?.cevaplar : null} onIptal={v.sonuc ? () => setTestte(false) : null}
          onBitti={(yeni) => { setV(yeni); setTestte(false); window.scrollTo({ top: 0, behavior: 'smooth' }) }} />
      </>
    )
  }
  return <Sonuc v={v} onYeniden={() => setTestte(true)} />
}
