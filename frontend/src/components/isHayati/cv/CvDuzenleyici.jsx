// [2026-10-10] CV Atölyesi → CV oluşturucu: kişisel bilgiler (yalnızca gerekenler), profil, bölümler (sırala / gizle / düzenle).
import { useState } from 'react'

export const yeniId = () => Math.random().toString(36).slice(2, 12)

const IPUCU = {
  egitim: 'Okulunu ve sınıfını yazman yeter. İstersen öne çıkan bir dersi, proje ödevini ya da başarını tek maddeyle ekle.',
  deneyim: 'Staj, kulüp görevi, takım kaptanlığı, aile işinde yardım… Hepsi deneyimdir.',
  projeler: 'Okul projeleri, kendi yaptığın uygulama, oyun, video, maket…',
  gonulluluk: 'Kaç saat, kaç kişiye ulaştın? Sayı ekle.',
  oduller: 'Dereceni ve hangi düzeyde aldığını yaz (okul / il / bölge / ulusal).',
  sertifikalar: 'Kursun adını, veren kurumu ve tarihi yaz. Belgeyi doğrulayan bağlantı portfolyonda kalsın.',
  beceriler: 'Somut beceriler yaz: kullandığın araçlar (Excel, Canva, Python) ve dil dışındaki yetkinlikler (sunum yapma, tablo hazırlama).',
  diller: 'A1–C2 seviyesiyle yaz. "İyi derecede" demek net değildir.',
  ilgi: 'Kısa tut (3–5 tane). Mülakatta sohbet konusu olur: "satranç (okul takımı)", "belgesel fotoğrafçılığı".',
}
const ORNEK_MADDE = 'ör.\nOkul gazetesinin 4 sayısının sayfa düzenini hazırladım.\n6 kişilik ekibe Canva kullanmayı öğrettim.'

function Oge({ o, onDegis, onSil, onYukari, onAsagi }) {
  const [acik, setAcik] = useState(!o.baslik)
  const s = (alan) => (e) => onDegis({ ...o, [alan]: e.target.value, ...(alan === 'baslik' || alan === 'kurum' ? { onayli: false } : {}) })
  return (
    <div className={`cva-oge${o.gizli ? ' gizli' : ''}`}>
      <div className="cva-oge-ust">
        <button type="button" className="cva-oge-ad" onClick={() => setAcik(!acik)} aria-expanded={acik}>
          <b>{o.baslik || 'Yeni öğe'}</b>
          <span className="yp-ince">{[o.kurum, o.donem].filter(Boolean).join(' · ')}</span>
        </button>
        {o.onayli && <span className="pf-rozet onay" title={o.onaylayan ? `Onaylayan: ${o.onaylayan}` : undefined}>✓ Okul onaylı</span>}
        <div className="cva-oge-islem">
          <button type="button" className="yp-mini" onClick={onYukari} aria-label="Yukarı taşı">↑</button>
          <button type="button" className="yp-mini" onClick={onAsagi} aria-label="Aşağı taşı">↓</button>
          <button type="button" className="yp-mini" onClick={() => onDegis({ ...o, gizli: !o.gizli })} title={o.gizli ? 'CV\'de göster' : 'CV\'de gizle'}>{o.gizli ? 'Göster' : 'Gizle'}</button>
          <button type="button" className="yp-mini" onClick={() => setAcik(!acik)}>{acik ? 'Kapat' : '✎'}</button>
        </div>
      </div>
      {acik && (
        <div className="pf-alanlar" style={{ marginTop: 10 }}>
          <label className="genis"><span>Başlık</span><input className="auth-input" maxLength={140} value={o.baslik} onChange={s('baslik')} placeholder="ör. Robotik takımı yazılım sorumlusu" /></label>
          <label><span>Kurum / yer</span><input className="auth-input" maxLength={120} value={o.kurum} onChange={s('kurum')} /></label>
          <label><span>Dönem <small>(ör. Eylül 2024 – Haziran 2025)</small></span><input className="auth-input" maxLength={60} value={o.donem} onChange={s('donem')} /></label>
          <label className="genis"><span>Ne yaptın? <small>Her satıra bir madde yaz · cümleyi bir eylemle bitir · mümkünse sayı ver</small></span>
            <textarea className="auth-input" rows={3} maxLength={900} value={o.aciklama} onChange={s('aciklama')} placeholder={ORNEK_MADDE} />
          </label>
          {o.portfolyo_id && <div className="genis yp-ince">Portfolyondan geldi. {o.onayli ? 'Başlığı ya da kurumu değiştirirsen "Okul onaylı" işareti kalkar.' : 'Rehber öğretmenin bunu portfolyoda onaylarsa CV\'de "Okul onaylı" yazar.'}</div>}
          <div className="genis"><button type="button" className="hg-link" style={{ color: 'var(--re)' }} onClick={onSil}>Bu öğeyi sil</button></div>
        </div>
      )}
    </div>
  )
}

function Etiketler({ ogeler, onDegis, oneriler }) {
  const [yeni, setYeni] = useState('')
  const ekle = (x) => { const v = (x || '').trim(); if (v && !ogeler.some((y) => y.toLocaleLowerCase('tr') === v.toLocaleLowerCase('tr'))) onDegis([...ogeler, v.slice(0, 40)]) }
  return (
    <>
      <div className="pf-cipler" style={{ marginTop: 0 }}>
        {ogeler.map((y, i) => (
          <span key={y} className="pf-cip">
            {i > 0 && <button type="button" aria-label={`${y} sola taşı`} onClick={() => { const a = [...ogeler];[a[i - 1], a[i]] = [a[i], a[i - 1]]; onDegis(a) }}>‹</button>}
            {y}<button type="button" aria-label={`${y} sil`} onClick={() => onDegis(ogeler.filter((x) => x !== y))}>×</button>
          </span>
        ))}
        <form onSubmit={(e) => { e.preventDefault(); ekle(yeni); setYeni('') }}>
          <input className="auth-input pf-cip-giris" maxLength={40} placeholder="+ ekle (Enter)" value={yeni} onChange={(e) => setYeni(e.target.value)} />
        </form>
      </div>
      {oneriler?.map((g) => {
        const kalan = g.liste.filter((x) => !ogeler.some((y) => y.toLocaleLowerCase('tr') === x.ad.toLocaleLowerCase('tr')))
        if (!kalan.length) return null
        return (
          <div key={g.baslik} style={{ marginTop: 10 }}>
            <div className="yp-ince" style={{ marginBottom: 4 }}>{g.baslik}</div>
            <div className="pf-cipler" style={{ marginTop: 0 }}>
              {kalan.map((x) => <button key={x.ad} type="button" className="cva-oneri" title={x.kaynak && x.kaynak !== x.ad ? `Değerlendirmedeki adı: ${x.kaynak}` : undefined} onClick={() => ekle(x.ad)}>+ {x.ad}</button>)}
            </div>
          </div>
        )
      })}
    </>
  )
}

function Diller({ ogeler, onDegis, seviyeler }) {
  return (
    <>
      {ogeler.map((d, i) => (
        <div key={i} className="pf-dil">
          <input className="auth-input" maxLength={30} value={d.dil} placeholder="Dil" onChange={(e) => onDegis(ogeler.map((x, j) => (j === i ? { ...x, dil: e.target.value } : x)))} />
          <select className="auth-input" value={d.seviye} onChange={(e) => onDegis(ogeler.map((x, j) => (j === i ? { ...x, seviye: e.target.value } : x)))}>{seviyeler.map((s) => <option key={s}>{s}</option>)}</select>
          <button type="button" className="hg-link" onClick={() => onDegis(ogeler.filter((_, j) => j !== i))}>Sil</button>
        </div>
      ))}
      <button type="button" className="hg-link" onClick={() => onDegis([...ogeler, { dil: '', seviye: 'B1' }])}>+ Dil ekle</button>
    </>
  )
}

function Bolum({ b, tip, onDegis, onYukari, onAsagi, oneriler, seviyeler }) {
  const [adDuzen, setAdDuzen] = useState(false)
  const tasi = (i, yon) => { const a = [...b.ogeler]; const j = i + yon; if (j < 0 || j >= a.length) return; [a[i], a[j]] = [a[j], a[i]]; onDegis({ ...b, ogeler: a }) }
  return (
    <div className={`card cva-bolum${b.gizli ? ' gizli' : ''}`}>
      <div className="cva-bolum-ust">
        {adDuzen
          ? <input className="auth-input" style={{ maxWidth: 260, padding: '5px 10px' }} autoFocus maxLength={50} value={b.baslik} onChange={(e) => onDegis({ ...b, baslik: e.target.value })} onBlur={() => setAdDuzen(false)} onKeyDown={(e) => e.key === 'Enter' && setAdDuzen(false)} />
          : <button type="button" className="cva-bolum-ad" onClick={() => setAdDuzen(true)} title="Başlığı değiştir">{b.baslik} <span aria-hidden="true">✎</span></button>}
        {b.gizli && <span className="pf-rozet">CV'de gizli</span>}
        <div className="cva-oge-islem">
          <button type="button" className="yp-mini" onClick={onYukari} aria-label={`${b.baslik} bölümünü yukarı taşı`}>↑</button>
          <button type="button" className="yp-mini" onClick={onAsagi} aria-label={`${b.baslik} bölümünü aşağı taşı`}>↓</button>
          <button type="button" className="yp-mini" onClick={() => onDegis({ ...b, gizli: !b.gizli })}>{b.gizli ? 'Göster' : 'Gizle'}</button>
        </div>
      </div>
      <div className="yp-ince" style={{ margin: '2px 0 10px' }}>{IPUCU[b.kod]}</div>
      {tip === 'liste' && (
        <>
          {b.ogeler.length === 0 && <div className="yp-ince" style={{ fontStyle: 'italic', marginBottom: 6 }}>Henüz öğe yok. Boş bölüm CV'de görünmez.</div>}
          {b.ogeler.map((o, i) => (
            <Oge key={o.id} o={o} onDegis={(x) => onDegis({ ...b, ogeler: b.ogeler.map((y) => (y.id === o.id ? x : y)) })}
              onSil={() => onDegis({ ...b, ogeler: b.ogeler.filter((y) => y.id !== o.id) })} onYukari={() => tasi(i, -1)} onAsagi={() => tasi(i, 1)} />
          ))}
          <button type="button" className="hg-link" style={{ marginTop: 8 }} onClick={() => onDegis({ ...b, ogeler: [...b.ogeler, { id: yeniId(), baslik: '', kurum: '', donem: '', aciklama: '', gizli: false, portfolyo_id: null, kulup: false }] })}>+ Öğe ekle</button>
        </>
      )}
      {tip === 'etiket' && <Etiketler ogeler={b.ogeler} onDegis={(x) => onDegis({ ...b, ogeler: x })} oneriler={oneriler} />}
      {tip === 'dil' && <Diller ogeler={b.ogeler} onDegis={(x) => onDegis({ ...b, ogeler: x })} seviyeler={seviyeler} />}
    </div>
  )
}

export default function CvDuzenleyici({ icerik, setIcerik, sabitler, oneriler }) {
  const [neden, setNeden] = useState(false)
  const k = icerik.kisisel
  const tipi = Object.fromEntries(sabitler.bolumler.map((b) => [b.kod, b.tip]))
  const kisisel = (alan) => (e) => setIcerik({ ...icerik, kisisel: { ...k, [alan]: e.target.value } })
  const bolumTasi = (i, yon) => { const a = [...icerik.bolumler]; const j = i + yon; if (j < 0 || j >= a.length) return; [a[i], a[j]] = [a[j], a[i]]; setIcerik({ ...icerik, bolumler: a }) }
  const beceriOneri = [
    { baslik: '💪 Güçlü yönlerin (Filizyol değerlendirmenden) — eklemeden önce bunu bir deneyiminle gösterebileceğinden emin ol', liste: oneriler.gucluler || [] },
    { baslik: '🗂️ Portfolyondaki yeteneklerin', liste: (oneriler.yetenekler || []).map((ad) => ({ ad })) },
  ]
  return (
    <div>
      <div className="card">
        <div className="ct">👤 Kişisel bilgiler</div>
        <div className="pf-alanlar">
          <label className="genis"><span>Ad soyad</span><input className="auth-input" maxLength={80} value={k.ad} onChange={kisisel('ad')} /></label>
          <label><span>E-posta</span><input className="auth-input" type="email" maxLength={120} value={k.eposta} onChange={kisisel('eposta')} placeholder="ad.soyad@…" /></label>
          <label><span>Şehir</span><input className="auth-input" maxLength={60} value={k.sehir} onChange={kisisel('sehir')} placeholder="ör. Kayseri" /></label>
        </div>
        <div className="cva-bilgi">
          <button type="button" className="hg-link" onClick={() => setNeden(!neden)} aria-expanded={neden}>ℹ️ TC kimlik no, doğum tarihi, fotoğraf neden yok? {neden ? '▴' : '▾'}</button>
          {neden && (
            <div className="yp-ince" style={{ lineHeight: 1.6, marginTop: 6 }}>
              CV'ni pek çok kişi görür ve kolayca kopyalanır. <b>TC kimlik numaran</b> kimlik hırsızlığında kullanılabilir. <b>Doğum tarihi, fotoğraf, medeni durum,
              din ve sağlık bilgisi</b> ise işle ilgili değildir. Bu bilgiler, bilerek ya da bilmeden ayrımcılık yapılmasına yol açabilir. İşveren bunlara gerçekten
              ihtiyaç duyarsa (ör. işe girişte sigorta kaydı) ayrıca ister. <b>Telefon numaranı</b> da yalnızca güvendiğin başvurularda paylaş: başvuru formunda ya da
              ön yazında. 18 yaşından küçüksen bu kararı velinle konuşarak ver.
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="ct">✍️ Kısa profil</div>
        <textarea className="auth-input" rows={3} maxLength={700} value={icerik.profil} onChange={(e) => setIcerik({ ...icerik, profil: e.target.value })}
          placeholder="ör. 11. sınıf öğrencisiyim; okul robotik takımında 2 yıldır yazılım sorumlusuyum. Yaz döneminde yazılım alanında gözlem stajı arıyorum." />
        <div className="cva-sayac"><span className="yp-ince">2–3 cümle yaz: Kimsin? Ne yaptın? Ne arıyorsun? "Çalışkan, dürüst" gibi sıfatlar yerine yaptığın bir şeyi anlat.</span>
          <span className="yp-ince" style={{ color: (icerik.profil || '').length > 450 ? 'var(--re)' : undefined }}>{(icerik.profil || '').length}/450</span></div>
      </div>

      {icerik.bolumler.map((b, i) => (
        <Bolum key={b.kod} b={b} tip={tipi[b.kod]} seviyeler={sabitler.dil_seviyeleri}
          oneriler={b.kod === 'beceriler' ? beceriOneri : null}
          onDegis={(x) => setIcerik({ ...icerik, bolumler: icerik.bolumler.map((y) => (y.kod === b.kod ? x : y)) })}
          onYukari={() => bolumTasi(i, -1)} onAsagi={() => bolumTasi(i, 1)} />
      ))}
    </div>
  )
}
