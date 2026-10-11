import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

// [2026-10-10] Kaynakça — sistemde elle hazırlanan her bileşen ve dayandığı kaynaklar.
// Veri backend'den gelir; süper admin "nasıl hesaplanıyor" ve tasarım notu ayrıntılarını da görür.
const kucuk = (s) => (s || '').toLocaleLowerCase('tr-TR')

function KaynakSatiri({ k, destek, acik, onAc }) {
  return (
    <div className={`kc-ref${acik ? ' acik' : ''}`}>
      <button className="kc-ref-ust" onClick={onAc} aria-expanded={acik}>
        <span className="kc-no">[{k.id}]</span>
        <span className="kc-kisa">{k.kisa}</span>
        {destek && <span className="kc-destek">{destek}</span>}
      </button>
      {acik && (
        <div className="kc-tam">
          {k.a}
          {k.u && <> · <a href={k.u} target="_blank" rel="noreferrer noopener">Kaynağa git ↗</a></>}
        </div>
      )}
    </div>
  )
}

export default function Kaynakca() {
  const [v, setV] = useState(null)
  const [sekme, setSekme] = useState('bilesen')
  const [grup, setGrup] = useState('')
  const [ara, setAra] = useState('')
  const [acikRef, setAcikRef] = useState(null)
  const [hata, setHata] = useState('')
  useEffect(() => { api.kaynakca().then(setV).catch((e) => setHata(e.message || 'Kaynakça yüklenemedi')) }, [])
  const ayrinti = !!v?.ayrinti

  const kaynakMap = useMemo(() => new Map((v?.kaynaklar || []).map((k) => [k.id, k])), [v])
  const kullanim = useMemo(() => {
    const m = new Map()
    ;(v?.bilesenler || []).forEach((b) => b.k.forEach(({ id }) => { if (!m.has(id)) m.set(id, []); m.get(id).push(b.b) }))
    return m
  }, [v])

  const q = kucuk(ara.trim())
  const bilesenler = useMemo(() => (v?.bilesenler || []).filter((b) => {
    if (grup && b.g !== grup) return false
    if (!q) return true
    const metin = [b.b, b.ne, ayrinti ? b.nasil : '', b.not, ...b.k.map(({ id, destek }) => `${kaynakMap.get(id)?.a} ${destek}`)].join(' ')
    return kucuk(metin).includes(q)
  }), [v, grup, q, ayrinti, kaynakMap])
  const kaynaklar = useMemo(() => (v?.kaynaklar || []).filter((k) => !q || kucuk(`${k.a} ${(kullanim.get(k.id) || []).join(' ')}`).includes(q)), [v, q, kullanim])

  if (!v) return <div className="pg pg-genis"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>
  const gruplar = v.gruplar.filter((g) => v.bilesenler.some((b) => b.g === g))
  const kaynakli = v.bilesenler.filter((b) => b.k.length).length

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Kaynakça</div>
        <div className="ps">
          {ayrinti
            ? `Filizyol'da elle hazırlanan her bileşen ve dayandığı akademik ya da resmî kaynaklar. ${v.bilesenler.length} bileşen · ${v.kaynaklar.length} kaynak · ${kaynakli} bileşen en az bir kaynağa dayanıyor.`
            : `Filizyol'un değerlendirme, rehberlik ve koçluk bileşenlerinin dayandığı akademik ve resmî kaynaklar. ${v.bilesenler.length} bileşen · ${v.kaynaklar.length} kaynak.`}
        </div>
      </div>

      {ayrinti ? (
        <div className="card kc-uyari">
          <b>Nasıl okunmalı? (yalnızca süper admin)</b> Kaynaklar, ilgili bileşenin <i>kuramsal dayanağını</i> gösterir. Filizyol ölçekleri bu kaynaklardaki
          ölçeklerin birebir uyarlaması değildir; ayrı bir geçerlik-güvenirlik çalışması gerektirir. Eşik, ağırlık ve sayı gibi ürün kararları
          <span className="kc-rozet">Kurum içi</span> notuyla ayrıca belirtilmiştir. Okul yetkilisi bu notları, "Nasıl" ayrıntılarını ve iç süreç bileşenlerini görmez.
        </div>
      ) : (
        <div className="card kc-uyari">
          Her bileşenin altında, o bileşenin kuramsal çerçevesini oluşturan kaynaklar yer alır. Bir kaynağa tıklayarak tam künyesini ve bağlantısını görebilirsiniz.
        </div>
      )}

      <div className="kc-arac">
        <div className="kc-sekmeler" role="tablist">
          <button role="tab" aria-selected={sekme === 'bilesen'} className={sekme === 'bilesen' ? 'aktif' : ''} onClick={() => setSekme('bilesen')}>Bileşenlere göre</button>
          <button role="tab" aria-selected={sekme === 'liste'} className={sekme === 'liste' ? 'aktif' : ''} onClick={() => setSekme('liste')}>Kaynak listesi ({v.kaynaklar.length})</button>
        </div>
        <input className="yp-sec" style={{ minWidth: 240, marginLeft: 'auto' }} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Bileşen, yazar veya konu ara…" />
      </div>

      {sekme === 'bilesen' && (
        <>
          <div className="kc-cipler">
            <button className={!grup ? 'aktif' : ''} onClick={() => setGrup('')}>Tümü</button>
            {gruplar.map((g) => <button key={g} className={grup === g ? 'aktif' : ''} onClick={() => setGrup(g)}>{g}</button>)}
          </div>
          {bilesenler.length === 0 && <div className="bos-durum">Aramana uygun bileşen bulunamadı.</div>}
          {gruplar.filter((g) => bilesenler.some((b) => b.g === g)).map((g) => (
            <div key={g} className="kc-grup">
              <div className="kc-grup-ad">{g}</div>
              {bilesenler.filter((b) => b.g === g).map((b) => (
                <div key={b.b} className="card kc-bilesen">
                  <div className="kc-baslik">
                    <span>{b.b}</span>
                    {b.ic && <span className="kc-rozet" title="Ağırlıklı olarak ürün tasarımı kararı">Kurum içi</span>}
                  </div>
                  <div className="kc-ne">{b.ne}</div>
                  {ayrinti && b.nasil && <div className="kc-nasil"><b>Nasıl:</b> {b.nasil}</div>}
                  {b.k.length > 0 ? (
                    <div className="kc-refler">
                      <div className="kc-etiket">Dayanak</div>
                      {b.k.map(({ id, destek }) => {
                        const k = kaynakMap.get(id); const anahtar = `${b.b}|${id}`
                        return k && <KaynakSatiri key={id} k={k} destek={destek} acik={acikRef === anahtar} onAc={() => setAcikRef(acikRef === anahtar ? null : anahtar)} />
                      })}
                    </div>
                  ) : <div className="kc-etiket" style={{ marginTop: 8 }}>Akademik dayanak yok</div>}
                  {b.not && <div className="kc-not">ℹ️ {b.not}</div>}
                </div>
              ))}
            </div>
          ))}
        </>
      )}

      {sekme === 'liste' && (
        <div className="card">
          <div className="yp-ince" style={{ marginBottom: 10 }}>APA 7 biçiminde, alfabetik. Köşeli parantezdeki numaralar bileşen kartlarındaki numaralarla aynıdır.</div>
          {kaynaklar.length === 0 && <div className="bos-durum">Aramana uygun kaynak bulunamadı.</div>}
          <ol className="kc-liste">
            {kaynaklar.map((k) => (
              <li key={k.id}>
                <span className="kc-no">[{k.id}]</span>
                <div>
                  <div>{k.a}{k.u && <> · <a href={k.u} target="_blank" rel="noreferrer noopener">Kaynağa git ↗</a></>}</div>
                  <div className="kc-kullanim">Kullanıldığı yer: {(kullanim.get(k.id) || []).join(' · ')}</div>
                  {ayrinti && k.d && <div className="kc-kullanim">Doğrulama: {k.d}</div>}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}
