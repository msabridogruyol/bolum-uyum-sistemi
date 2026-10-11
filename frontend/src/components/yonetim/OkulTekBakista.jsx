// [2026-10-10] Rapor Merkezi → "Tek Bakışta": okul yöneticisi için tek ekranlık özet (GET /yonetim/okul/{id}/tek-bakista).
// Yukarıdan aşağı: öne çıkan bulgular · KPI şeridi · kritik öğrenciler · akademik sıralama · şube karşılaştırma · grafikler · hedef–uyum.
// Filtre: sınıf düzeyi + şube (İstatistikler ile aynı). "Okul ortalaması" her zaman tüm okuldur.
// Etik: kişilik / değer / ilgi puanlarına göre sıralama yok — sıralamalar yalnızca net, net değişimi, katılım ve hedef uyumuyla.
// Okul kendi öğrencilerini isimle gördüğü için küçük grup gizleme bu ekranda uygulanmaz. Öğrenci adı → OgrenciDetayPenceresi.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { CizgiGrafik, DURUM, GrafikKarti, Halka, KATEGORIK, KpiKarti, KpiSatiri, YatayCubuk, bicim, sayi } from '../istatistik'
import OgrenciDetayPenceresi from './OgrenciDetayPenceresi'
import { onceSure } from './ortak'

const OKUL = 'var(--okul-c, var(--ist-k1))'
const yuzde = (v) => (v == null ? '—' : bicim(v, '%', 0))
const net = (v) => (v == null ? '—' : sayi(v, 2))
const isaretli = (v) => (v == null ? '—' : `${v > 0 ? '+' : v < 0 ? '−' : ''}${sayi(Math.abs(v), 2)}`)
const gunTR = (iso) => (iso ? new Date(String(iso).length <= 10 ? `${iso}T00:00:00` : iso).toLocaleDateString('tr-TR') : '')

// erken uyarı seviyesi → durum rengi (hepsi dikkat gerektirir; ağırlığa göre kırmızı → turuncu → sarı)
const SEVIYE = {
  yuksek: { d: DURUM.kritik, ad: 'Yüksek' },
  orta: { d: DURUM.ciddi, ad: 'Orta' },
  dusuk: { d: DURUM.uyari, ad: 'Düşük' },
}
const BULGU = {
  dikkat: { ikon: '!', ad: 'Dikkat' },
  olumlu: { ikon: '✓', ad: 'Olumlu' },
  bilgi: { ikon: 'i', ad: 'Bilgi' },
}
const SUBE_SUTUN = [
  ['tamamlama', 'Tamamlama', yuzde],
  ['aktif7', 'Son 7 gün aktif', yuzde],
  ['tyt', 'Ort. TYT neti', (v) => (v == null ? '—' : sayi(v, 1))],
  ['hedef', 'Hedef seçen', yuzde],
  ['kritik', 'Kritik öğrenci', (v) => (v == null ? '—' : String(v))],
]
const TON_ADI = { iyi: 'okul ortalamasının belirgin üstünde', iyi_hafif: 'okul ortalamasının üstünde', uyari: 'okul ortalamasının biraz altında', kotu: 'okul ortalamasının belirgin altında' }

function Bolum({ baslik, aciklama, sag, children }) {
  return (
    <section className="otb-bolum">
      <div className="otb-bolum-ust">
        <div style={{ minWidth: 0 }}>
          <h2 className="ois-bolum-baslik">{baslik}</h2>
          {aciklama && <p className="ois-bolum-aciklama">{aciklama}</p>}
        </div>
        {sag}
      </div>
      {children}
    </section>
  )
}

function SeviyeRozeti({ kod }) {
  const s = SEVIYE[kod]
  if (!s) return null
  return (
    <span className={`otb-seviye otb-s-${kod}`} style={{ '--d': s.d.renk }}>
      <span className="otb-seviye-ikon" aria-hidden="true">{s.d.ikon}</span>{s.ad}
    </span>
  )
}

function Ad({ x, onAc }) {
  return <button type="button" className="ak-link otb-ad" onClick={(e) => { e.stopPropagation(); onAc(x.ogrenci_id) }}>{x.ad_soyad}</button>
}

// ----------------------------------------------------------------------------- 1. Bulgular
function Bulgular({ l }) {
  if (!l?.length) return null
  return (
    <section className="card otb-bulgular" aria-labelledby="otb-bulgu-b">
      <h2 id="otb-bulgu-b" className="otb-kart-baslik">Öne çıkan bulgular</h2>
      <ul>
        {l.map((b, i) => (
          <li key={i} className={`otb-bulgu otb-b-${b.tur}`}>
            <span className="otb-bulgu-ikon" aria-hidden="true">{BULGU[b.tur].ikon}</span>
            <span><span className="ist-gizli">{BULGU[b.tur].ad}: </span>{b.metin}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

// ----------------------------------------------------------------------------- 3. Kritik öğrenciler
function Kritik({ v, onAc, onRehberlik }) {
  const k = v.kritik
  const tumu = v.rehberlik && onRehberlik && (
    <button type="button" className="ak-link" onClick={onRehberlik}>Tümünü gör{k.toplam > k.ogrenciler.length ? ` (${k.toplam})` : ''} →</button>
  )
  return (
    <Bolum baslik={k.baslik} sag={tumu}
      aciklama={v.rehberlik
        ? 'Erken uyarı motorunun bugünkü sonucu; önce yüksek seviye. Adına tıklayarak öğrencinin ayrıntısını açın.'
        : 'Katılım verisine göre: değerlendirmeyi yarıda bırakan, hiç giriş yapmayan ya da sonucu doğrulanamayan öğrenciler.'}>
      {!k.ogrenciler.length ? <div className="card bos-durum">Şu anda takip gerektiren öğrenci yok. 🎉</div> : (
        <div className="yp-tablo-kap otb-tablo-kap">
          <table className="yp-tablo yp-tiklanir">
            <thead>
              <tr><th>Ad soyad</th><th>Şube</th><th>Seviye</th><th>Nedenler</th><th>Son giriş</th>{v.rehberlik && <th>Son görüşme</th>}</tr>
            </thead>
            <tbody>
              {k.ogrenciler.map((s) => (
                <tr key={s.ogrenci_id} onClick={() => onAc(s.ogrenci_id)}>
                  <td><Ad x={s} onAc={onAc} /></td>
                  <td>{s.sube}</td>
                  <td><SeviyeRozeti kod={s.seviye} /></td>
                  <td className="otb-nedenler">{s.nedenler.map((n) => <span key={n.ad} title={n.metin}>{n.ad}</span>)}</td>
                  <td className="yp-ince" style={{ whiteSpace: 'nowrap' }}>{s.son_giris ? onceSure(s.son_giris) : '—'}</td>
                  {v.rehberlik && (
                    <td style={{ whiteSpace: 'nowrap' }}>
                      {s.yaklasan_gorusme ? <span className="otb-gorusme otb-g-plan">📅 {gunTR(s.yaklasan_gorusme)}</span>
                        : s.son_gorusme ? <span className="yp-ince">{gunTR(s.son_gorusme)}</span>
                          : <span className="otb-gorusme otb-g-yok">Görüşme yok</span>}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {k.toplam > k.ogrenciler.length && <div className="yp-ince" style={{ marginTop: 6 }}>İlk {k.ogrenciler.length} öğrenci gösteriliyor (toplam {k.toplam}).</div>}
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- 4. Akademik sıralama
function SiraTablosu({ baslik, l, onAc, bos }) {
  return (
    <div className="otb-sira">
      <h3 className="otb-alt-baslik">{baslik}</h3>
      {!l.length ? <div className="yp-ince otb-sira-bos">{bos}</div> : (
        <div className="yp-tablo-kap otb-tablo-kap">
          <table className="yp-tablo yp-tiklanir">
            <thead><tr><th>#</th><th>Ad soyad</th><th>Şube</th><th className="otb-sag">Net</th><th className="otb-sag">Okula fark</th></tr></thead>
            <tbody>
              {l.map((x, i) => (
                <tr key={x.ogrenci_id} onClick={() => onAc(x.ogrenci_id)}>
                  <td className="yp-ince">{i + 1}</td><td><Ad x={x} onAc={onAc} /></td><td>{x.sube}</td>
                  <td className="otb-sag otb-sayi"><b>{net(x.net)}</b></td>
                  <td className={`otb-sag otb-sayi ${x.fark > 0 ? 'ist-d-iyi' : x.fark < 0 ? 'ist-d-kotu' : ''}`}>{isaretli(x.fark)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function DegisimTablosu({ baslik, l, onAc, bos }) {
  return (
    <div className="otb-sira">
      <h3 className="otb-alt-baslik">{baslik}</h3>
      {!l.length ? <div className="yp-ince otb-sira-bos">{bos}</div> : (
        <div className="yp-tablo-kap otb-tablo-kap">
          <table className="yp-tablo yp-tiklanir">
            <thead><tr><th>Ad soyad</th><th>Şube</th><th className="otb-sag">Net</th><th className="otb-sag">Fark</th></tr></thead>
            <tbody>
              {l.map((x) => (
                <tr key={x.ogrenci_id} onClick={() => onAc(x.ogrenci_id)}>
                  <td><Ad x={x} onAc={onAc} /></td><td>{x.sube}</td>
                  <td className="otb-sag otb-sayi" style={{ whiteSpace: 'nowrap' }}>{net(x.onceki)} → <b>{net(x.son)}</b></td>
                  <td className={`otb-sag otb-sayi ${x.fark > 0 ? 'ist-d-iyi' : 'ist-d-kotu'}`}><span aria-hidden="true">{x.fark > 0 ? '▲' : '▼'}</span> {isaretli(x.fark)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function Akademik({ v, onAc }) {
  const a = v.akademik
  const oturumlar = Object.keys(a?.oturumlar || {})
  const [ot, setOt] = useState(oturumlar[0] || 'TYT')
  if (!a) return null
  const x = a.oturumlar[ot]
  const sekmeler = oturumlar.length > 1 && (
    <div className="otb-mini-sekme" role="tablist" aria-label="Oturum">
      {oturumlar.map((o) => <button key={o} type="button" role="tab" aria-selected={o === ot} className={o === ot ? 'aktif' : ''} onClick={() => setOt(o)}>{o}</button>)}
    </div>
  )
  return (
    <Bolum baslik="Akademik sıralama" sag={sekmeler}
      aciklama="Deneme netlerine göre; okul ortalamasına fark tüm okulun aynı kaynaktaki ortalamasıyla hesaplanır.">
      {!x ? (
        <div className="card bos-durum">
          {a.okul_denemeleri ? "Henüz deneme sonucu yüklenmedi — Okul Denemeleri'nden yükleyebilirsiniz." : "Öğrenciler Net Takibi'ne deneme girdikçe sıralama burada oluşur."}
        </div>
      ) : (
        <div className="card otb-akademik">
          <div className="otb-kaynak">
            <span>📝 {x.kaynak_metni}</span>
            <span>Okul ortalaması <b>{net(x.okul_ort)}</b> net{v.filtre.sinif && x.kapsam_ort != null ? <> · {v.filtre.etiket}: <b>{net(x.kapsam_ort)}</b> net</> : null}</span>
          </div>
          <div className="otb-ikili">
            <SiraTablosu baslik="En yüksek 10" l={x.en_yuksek} onAc={onAc} bos="Bu kapsamda sonuç yok." />
            <SiraTablosu baslik="En düşük 10" l={x.en_dusuk} onAc={onAc} bos={x.en_yuksek.length ? 'Katılımcıların tamamı soldaki listede.' : 'Bu kapsamda sonuç yok.'} />
          </div>
          <div className="otb-ikili">
            <DegisimTablosu baslik="En çok yükselen 5" l={x.yukselen} onAc={onAc} bos={x.degisim_metni ? 'Yükselen öğrenci yok.' : 'Değişim için en az iki deneme gerekir.'} />
            <DegisimTablosu baslik="En çok düşen 5" l={x.dusen} onAc={onAc} bos={x.degisim_metni ? 'Düşen öğrenci yok. 👏' : 'Değişim için en az iki deneme gerekir.'} />
          </div>
          {x.degisim_metni && <div className="yp-ince">Değişim: {x.degisim_metni}.</div>}
        </div>
      )}
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- 5. Şube karşılaştırma (ısı renkli)
function SubeTablosu({ v }) {
  const l = v.subeler || []
  const oo = v.okul_ort
  const tytVar = l.some((s) => s.tyt != null)
  const sutunlar = SUBE_SUTUN.filter(([k]) => k !== 'tyt' || tytVar)
  if (!l.length) return null
  return (
    <Bolum baslik="Şube karşılaştırması" aciklama="Her hücre okul ortalamasıyla kıyaslanır. Çerçeveli hücre, okul ortalamasından belirgin biçimde ayrışan en iyi (yeşil) ya da en geride kalan (kırmızı) şubedir.">
      <div className="yp-tablo-kap otb-tablo-kap">
        <table className="yp-tablo otb-isi">
          <thead><tr><th>Şube</th><th className="otb-sag">Öğrenci</th>{sutunlar.map(([k, ad]) => <th key={k} className="otb-sag">{ad}</th>)}</tr></thead>
          <tbody>
            {l.map((s) => (
              <tr key={s.etiket}>
                <td><b>{s.etiket}</b></td>
                <td className="otb-sag otb-sayi">{s.ogrenci}</td>
                {sutunlar.map(([k, , f]) => {
                  const ton = s.tonlar[k], vurgu = s.vurgu[k]
                  return (
                    <td key={k} className={`otb-sag otb-sayi otb-t-${ton}${vurgu ? ` otb-v-${vurgu}` : ''}`}
                      title={[TON_ADI[ton], vurgu === 'en_iyi' ? 'sütunun en iyisi' : vurgu === 'en_kotu' ? 'sütunda en geride' : null].filter(Boolean).join(' · ') || undefined}>
                      {vurgu && <span className="otb-v-ikon" aria-label={vurgu === 'en_iyi' ? 'en iyi' : 'en geride'}>{vurgu === 'en_iyi' ? '★' : '▼'}</span>}
                      {f(s[k])}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr><td>Okul ortalaması</td><td className="otb-sag otb-sayi">{oo.ogrenci}</td>{sutunlar.map(([k, , f]) => <td key={k} className="otb-sag otb-sayi">{f(oo[k])}</td>)}</tr>
          </tfoot>
        </table>
      </div>
      <div className="otb-lejant" aria-hidden="true">
        <span><i className="otb-t-iyi" /> belirgin üstünde (15+ puan)</span>
        <span><i className="otb-t-iyi_hafif" /> üstünde</span>
        <span><i className="otb-t-uyari" /> biraz altında</span>
        <span><i className="otb-t-kotu" /> belirgin altında (15+ puan)</span>
        <span>★ en iyi · ▼ en geride</span>
      </div>
      <div className="yp-ince">Kritik öğrencide az olan iyidir (şube büyüklüğüne oranla kıyaslanır). TYT netinde fark, okul ortalamasının yüzdesi olarak değerlendirilir.</div>
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- 6. Grafikler
function Grafikler({ v }) {
  const subeler = (v.subeler || []).filter((s) => s.tamamlama != null)
  const oo = v.okul_ort
  const tyt = v.akademik?.oturumlar?.TYT
  const trend = tyt?.trend || []
  const filtreli = !!v.filtre.sinif
  const seviyeler = v.kritik.seviyeler.map((s) => ({ ad: SEVIYE[s.kod].ad, deger: s.deger, renk: SEVIYE[s.kod].d.renk }))
  return (
    <Bolum baslik="Grafikler">
      <div className="ist-kartlar">
        <GrafikKarti baslik="Şubelere göre tamamlama" aciklama={`Değerlendirmeyi tamamlayan öğrenci oranı · okul ortalaması ${yuzde(oo.tamamlama)}`}
          tablo={{ sutunlar: ['Şube', 'Tamamlama %', 'Öğrenci'], satirlar: subeler.map((s) => [s.etiket, s.tamamlama, s.ogrenci]) }}>
          <YatayCubuk veri={subeler.map((s) => ({ ad: s.etiket, deger: s.tamamlama, alt: `${s.ogrenci} öğrenci${s.tamamlama < oo.tamamlama ? ' · ortalamanın altında' : ''}` }))}
            maks={100} birim="%" renk={OKUL} enFazla={12} kesir={0} />
        </GrafikKarti>
        {v.akademik && (
          <GrafikKarti baslik="TYT ortalama net eğilimi" aciklama={tyt ? tyt.trend_metni : 'Deneme sonucu yok'}
            tablo={trend.length ? { sutunlar: ['Dönem', 'Okul', ...(filtreli ? [v.filtre.etiket] : [])], satirlar: trend.map((t) => [t.ad, t.okul, ...(filtreli ? [t.kapsam] : [])]) } : undefined}>
            {trend.length < 2 ? <div className="ist-bos">{trend.length ? 'Eğilim için en az iki deneme dönemi gerekir.' : "Henüz deneme sonucu yok — Okul Denemeleri'nden yükleyebilirsiniz."}</div> : (
              <CizgiGrafik x={trend.map((t) => t.etiket)} birim="net" seriler={[
                { ad: 'Okul', degerler: trend.map((t) => t.okul), renk: KATEGORIK[0] },
                ...(filtreli ? [{ ad: v.filtre.etiket, degerler: trend.map((t) => t.kapsam), renk: KATEGORIK[1] }] : []),
              ]} />
            )}
          </GrafikKarti>
        )}
        <GrafikKarti baslik={v.rehberlik ? 'Erken uyarı seviyeleri' : 'Takip seviyeleri'} aciklama={`${v.kritik.toplam} öğrenci · kırmızı en acil`}
          tablo={{ sutunlar: ['Seviye', 'Öğrenci'], satirlar: seviyeler.map((s) => [s.ad, s.deger]) }}>
          {v.kritik.toplam ? <Halka veri={seviyeler} birim="öğrenci" merkezEtiket="öğrenci" /> : <div className="ist-bos">Uyarıda öğrenci yok.</div>}
        </GrafikKarti>
      </div>
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- 7. Hedef–uyum
function HedefUyum({ v, onAc }) {
  const h = v.hedef_uyum
  if (!h) return null
  return (
    <Bolum baslik="Hedefiyle uyumu düşük öğrenciler" aciklama={`Seçtiği hedef bölümle uyumu %${h.esik}'ın altında olan öğrenciler — koçlukta hedefin nedenlerini ve yakın alternatifleri birlikte konuşmak için bir fırsat.`}>
      {!h.ogrenciler.length ? (
        <div className="card bos-durum">{h.hedefli ? `Hedef seçen ${h.hedefli} öğrencinin tamamı hedefiyle yeterli uyumda. 👍` : 'Henüz hedef bölüm seçip değerlendirmeyi tamamlayan öğrenci yok.'}</div>
      ) : (
        <div className="yp-tablo-kap otb-tablo-kap">
          <table className="yp-tablo yp-tiklanir">
            <thead><tr><th>Ad soyad</th><th>Şube</th><th>Hedef bölüm</th><th className="otb-sag">Uyum</th></tr></thead>
            <tbody>
              {h.ogrenciler.map((x) => (
                <tr key={x.ogrenci_id} onClick={() => onAc(x.ogrenci_id)}>
                  <td><Ad x={x} onAc={onAc} /></td><td>{x.sube}</td><td>🎯 {x.bolum}</td><td className="otb-sag otb-sayi">%{x.uyum}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {h.sayi > h.ogrenciler.length && <div className="yp-ince" style={{ marginTop: 6 }}>İlk {h.ogrenciler.length} öğrenci (toplam {h.sayi}).</div>}
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- Sayfa
export default function OkulTekBakista({ okulId, superAdmin, okullar, onDegisti, onRehberlik }) {
  const [sinif, setSinif] = useState('')
  const [sube, setSube] = useState('')
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [pdf, setPdf] = useState(false)
  const [secenekler, setSecenekler] = useState([])
  const [detay, setDetay] = useState(null)
  const [yenileme, setYenileme] = useState(0)
  const filtre = useMemo(() => ({ sinif, sube }), [sinif, sube])

  useEffect(() => {
    let iptal = false
    setBekle(true); setHata(null)
    api.okulTekBakista(okulId, filtre)
      .then((d) => { if (!iptal) { setV(d); if (!sinif) setSecenekler(d.filtre.secenekler) } })
      .catch((e) => { if (!iptal) setHata(e.detail || 'Özet yüklenemedi.') })
      .finally(() => { if (!iptal) setBekle(false) })
    return () => { iptal = true }
  }, [okulId, filtre, yenileme])   // eslint-disable-line react-hooks/exhaustive-deps

  const subeler = secenekler.find((s) => s.sinif === sinif)?.subeler || []
  async function pdfIndir() {
    setPdf(true); setHata(null)
    try { await api.okulTekBakistaPdf(okulId, filtre) } catch (e) { setHata(e.detail || 'PDF indirilemedi.') } finally { setPdf(false) }
  }
  const k = v?.kpi
  const tytDeg = k && k.tyt != null && k.tyt_onceki != null ? Math.round((k.tyt - k.tyt_onceki) * 10) / 10 : null

  return (
    <>
    <div className="ois otb">
      <div className="yp-arac ois-filtre" role="group" aria-label="Filtreler">
        <select className="yp-sec" value={sinif} onChange={(e) => { setSinif(e.target.value); setSube('') }} aria-label="Sınıf düzeyi">
          <option value="">Tüm sınıf düzeyleri</option>
          {secenekler.map((s) => <option key={s.sinif} value={s.sinif}>{s.sinif}</option>)}
        </select>
        <select className="yp-sec" value={sube} onChange={(e) => setSube(e.target.value)} disabled={!sinif || !subeler.length} aria-label="Şube">
          <option value="">{sinif ? 'Tüm şubeler' : 'Şube (önce sınıf)'}</option>
          {subeler.map((s) => <option key={s} value={s}>{sinif.replace('. Sınıf', '')}-{s}</option>)}
        </select>
        {bekle && v && <span className="spin" aria-label="Yükleniyor" />}
        <div style={{ flex: 1 }} />
        <button type="button" className="rd-dugme" disabled={!v || pdf} onClick={pdfIndir}
          title="Bu ekrandaki bulgular, göstergeler, kritik öğrenciler, şube tablosu ve akademik sıralama — seçili filtreyle">📄 {pdf ? 'Hazırlanıyor…' : 'Yönetici özeti (PDF)'}</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v ? <div className="bos-durum">{hata ? '' : 'Yükleniyor…'}</div> : (
        <div style={{ opacity: bekle ? 0.6 : 1, transition: 'opacity .2s' }}>
          <div className="yp-ince ois-kapsam"><span><b>{v.filtre.etiket}</b> · bugünkü durum · test hesapları hariç · okul ortalaması tüm okuldur</span></div>
          <Bulgular l={v.bulgular} />
          <KpiSatiri min={150}>
            <KpiKarti etiket="Öğrenci" deger={k.ogrenci} ikon="🎓" ton="okul" alt={`${k.aktif7 == null ? '—' : yuzde(k.aktif7)} son 7 günde giriş yaptı`} />
            <KpiKarti etiket="Tamamlama" deger={k.tamamlama ?? '—'} birim={k.tamamlama == null ? undefined : '%'} ikon="✅"
              alt={v.filtre.sinif ? `${k.tamamlayan} öğrenci · okul ${yuzde(v.okul_ort.tamamlama)}` : `${k.tamamlayan} öğrenci testi bitirdi`} />
            {k.tyt_kaynak && (
              <KpiKarti etiket="Ort. son TYT neti" deger={k.tyt == null ? '—' : Math.round(k.tyt * 10) / 10} ikon="📝"
                degisim={tytDeg != null ? { deger: tytDeg, birim: 'net', donem: 'önceki denemeye göre' } : undefined}
                alt={k.tyt_kaynak === 'okul' ? `son okul denemesi · ${k.tyt_n} öğrenci` : `öğrencilerin son denemesi · ${k.tyt_n} öğrenci`} />
            )}
            {v.rehberlik
              ? <KpiKarti etiket="Kritik öğrenci" deger={k.kritik} ikon="🚨" ton={k.kritik ? 'kotu' : 'iyi'} alt={`yüksek seviye uyarı · toplam ${k.takip} öğrenci uyarıda`} />
              : <KpiKarti etiket="Takip gereken" deger={k.takip} ikon="🧭" ton={k.takip ? 'uyari' : 'iyi'} alt="yarıda kalan, giriş yok, doğrulanamayan" />}
            {k.kocluk_aktif != null && <KpiKarti etiket="Koçlukta aktif" deger={k.kocluk_aktif} ikon="🪜" alt={`son 30 günde adım / görev · ${yuzde(k.ogrenci ? (100 * k.kocluk_aktif) / k.ogrenci : null)}`} />}
            <KpiKarti etiket="Hedef seçen" deger={k.hedef ?? '—'} birim={k.hedef == null ? undefined : '%'} ikon="🎯" alt={`${k.hedef_secen} öğrenci hedef bölüm seçti`} />
          </KpiSatiri>
          <Kritik v={v} onAc={setDetay} onRehberlik={onRehberlik} />
          <Akademik key={Object.keys(v.akademik?.oturumlar || {}).join()} v={v} onAc={setDetay} />
          <SubeTablosu v={v} />
          <Grafikler v={v} />
          <HedefUyum v={v} onAc={setDetay} />
          <p className="yp-ince otb-dipnot">Sıralamalar yalnızca deneme netleri, net değişimi, katılım ve hedef uyumuna göredir. Kişilik, değer ve ilgi sonuçları bir başarı ölçüsü olmadığından sıralamada kullanılmaz.</p>
        </div>
      )}
    </div>
    {/* .ois giriş animasyonu transform taşıdığından pencere onun DIŞINDA çizilir (yoksa fixed konum kayar) */}
    {detay && <OgrenciDetayPenceresi ogrenciId={detay} superAdmin={superAdmin} okullar={okullar} onKapat={() => setDetay(null)}
        onDegisti={() => { setYenileme((x) => x + 1); onDegisti?.() }} />}
    </>
  )
}
