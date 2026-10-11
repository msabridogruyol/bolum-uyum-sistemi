// [2026-10-08] Bölüm bilgi kartı — açılır pencere. Sekmeler: Genel Bakış · Meslekler · Meslek Dili · Yetkinlikler · Üniversiteler (YÖK Atlas)
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import FavoriYildiz from './FavoriYildiz'
import { KarsilastirDugmesi } from './KarsilastirSepeti'

const SEKMELER = [
  { kod: 'genel', ad: 'Genel Bakış' },
  { kod: 'meslek', ad: 'Meslekler' },
  { kod: 'jargon', ad: 'Meslek Dili' },
  { kod: 'yetkinlik', ad: 'Yetkinlikler' },
  { kod: 'uni', ad: 'Üniversiteler' },
]

const KATMAN_IKON = { K1: '🌱', K2: '🌿', K3: '🍃', K4: '🌸' }
const ONEM_RENK = { 'Çok önemli': 'var(--pu)', 'Önemli': 'var(--pum)' }

// [2026-10-09] Yalnızca bu bölümde ÖNE ÇIKAN özellikler gösterilir. "Düşük" etiketi kullanılmaz:
// listede olmayan bir özellik "önemsiz" değil, bu bölümü diğerlerinden ayıran bir özellik değil demektir.
// İki uçlu özelliklerde (ör. rutin ↔ dinamik) hangi uç öne çıkıyorsa o yazılır.
function YetkinlikProfili({ bolumId }) {
  const [veri, setVeri] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => {
    let iptal = false
    setVeri(null); setHata(null)
    api.bolumYetkinlik(bolumId).then((v) => { if (!iptal) setVeri(v) }).catch((e) => { if (!iptal) setHata(e.detail || 'Yetkinlik profili alınamadı.') })
    return () => { iptal = true }
  }, [bolumId])
  if (hata) return <div className="ps" style={{ margin: 0 }}>{hata}</div>
  if (!veri) return <div className="ps" style={{ margin: 0 }}>Yükleniyor…</div>
  if (!veri.katmanlar.length) return <div className="ps" style={{ margin: 0 }}>Bu bölümün yetkinlik profili şu an gösterilemiyor. Genel Bakış ve Meslekler sekmelerine göz atabilirsin.</div>
  const katmanlar = veri.katmanlar.map((k) => ({ ...k, liste: k.one_cikanlar || k.degiskenler.filter((d) => d.one_cikan) }))
  const toplam = katmanlar.reduce((t, k) => t + k.liste.length, 0)
  return (
    <>
      <div className="ps" style={{ margin: '0 0 12px', fontSize: 12.5, lineHeight: 1.55 }}>
        Bu bölümü {veri.bolum_sayisi} bölüm arasında <b>en çok öne çıkaran {toplam} özellik</b>. Listede olmayan özellikler de değerlidir;
        yalnızca bu bölümü diğerlerinden belirgin biçimde ayırmazlar.
      </div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
        {Object.entries(ONEM_RENK).map(([ad, renk]) => (
          <span key={ad} style={{ display: 'inline-flex', alignItems: 'center', gap: 5, fontSize: 11.5, color: 'var(--tx2)', fontWeight: 700 }}>
            <span style={{ width: 10, height: 10, borderRadius: 3, background: renk, display: 'inline-block' }} />{ad}
          </span>
        ))}
      </div>
      {katmanlar.filter((k) => k.liste.length).map((k) => (
        <Bolum key={k.kod} baslik={`${KATMAN_IKON[k.kod] || ''} ${k.ad}`}>
          {k.liste.map((d) => (
            <div key={d.kod} title={d.aciklama || ''} style={{ display: 'grid', gridTemplateColumns: 'minmax(140px, 44%) 1fr auto', gap: 10, alignItems: 'center', padding: '5px 0' }}>
              <div style={{ fontSize: 13, color: 'var(--tx)', fontWeight: 600, lineHeight: 1.3 }}>{d.etiket}</div>
              <div style={{ height: 9, borderRadius: 99, background: 'var(--sur2)', overflow: 'hidden' }}>
                <div style={{ width: `${Math.max(8, d.guc)}%`, height: '100%', borderRadius: 99, background: ONEM_RENK[d.onem] }} />
              </div>
              <div style={{ fontSize: 11.5, fontWeight: 800, color: ONEM_RENK[d.onem], minWidth: 74, textAlign: 'right' }}>{d.onem}</div>
            </div>
          ))}
        </Bolum>
      ))}
      {toplam === 0 && <div className="ps" style={{ margin: 0 }}>Bu bölüm özellik bakımından dengeli; belirgin biçimde öne çıkan bir özellik yok.</div>}
    </>
  )
}

const turGrubu = (t) => (t === 'DEVLET' ? 'DEVLET' : (t || '').startsWith('VAKIF') ? 'VAKIF' : 'DIGER')
const turAdi = (t) => ({ DEVLET: 'Devlet', VAKIF: 'Vakıf', DIGER: t ? t.charAt(0) + t.slice(1).toLocaleLowerCase('tr') : null })[turGrubu(t)]

const sayi = (v, ondalik = 0) =>
  v === null || v === undefined ? '—' : Number(v).toLocaleString('tr-TR', { minimumFractionDigits: ondalik, maximumFractionDigits: ondalik })

function Liste({ maddeler }) {
  return (
    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13.5, color: 'var(--tx2)', lineHeight: 1.65 }}>
      {maddeler.map((m, i) => <li key={i} style={{ marginBottom: 4 }}>{m}</li>)}
    </ul>
  )
}

function Bolum({ baslik, children, vurgu }) {
  return (
    <div style={{
      marginBottom: 14, padding: '14px 16px', borderRadius: 14,
      border: `1.5px solid ${vurgu ? 'var(--am)' : 'var(--bor)'}`, background: vurgu ? 'var(--aml)' : 'var(--sur)',
    }}>
      <div style={{ fontSize: 13, fontWeight: 800, marginBottom: 8, color: vurgu ? 'var(--am)' : 'var(--tx)' }}>{baslik}</div>
      {children}
    </div>
  )
}

function GenelBakis({ bilgi }) {
  const d = bilgi.detay
  if (!d) {
    return <div style={{ fontSize: 13.5, color: 'var(--tx2)', lineHeight: 1.6 }}>{bilgi.kisa_aciklama || 'Bu bölümün ayrıntılarını Meslekler ve Üniversiteler sekmelerinde inceleyebilirsin.'}</div>
  }
  return (
    <>
      <Bolum baslik="Bölüm Hakkında">
        <div style={{ fontSize: 13.5, color: 'var(--tx2)', lineHeight: 1.65 }}>{d.ozet}</div>
      </Bolum>
      {d.neler_ogrenilir?.length > 0 && <Bolum baslik="Neler Öğrenilir?"><Liste maddeler={d.neler_ogrenilir} /></Bolum>}
      {d.ornek_dersler?.length > 0 && (
        <Bolum baslik="Örnek Dersler">
          <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
            {d.ornek_dersler.map((x, i) => (
              <span key={i} style={{ fontSize: 12.5, fontWeight: 600, padding: '5px 11px', borderRadius: 10, background: 'var(--pul)', color: 'var(--tx)' }}>{x}</span>
            ))}
          </div>
        </Bolum>
      )}
      {d.kimler_icin_uygun?.length > 0 && <Bolum baslik="Kimler İçin Uygun?"><Liste maddeler={d.kimler_icin_uygun} /></Bolum>}
      {d.calisma_alanlari?.length > 0 && <Bolum baslik="Nerelerde Çalışılır?"><Liste maddeler={d.calisma_alanlari} /></Bolum>}
      {d.bilmen_gerekenler?.length > 0 && <Bolum baslik="Bilmen Gerekenler" vurgu><Liste maddeler={d.bilmen_gerekenler} /></Bolum>}
    </>
  )
}

function Meslekler({ detay, bolumId }) {
  const [acik, setAcik] = useState(0)
  const liste = detay?.meslekler || []
  if (!liste.length) return <div className="ps" style={{ margin: 0 }}>Bu bölümün mezunlarının çalıştığı alanları Genel Bakış sekmesinde bulabilirsin.</div>
  return (
    <>
      <div className="ps" style={{ margin: '0 0 12px', fontSize: 12.5 }}>Mezunların sık yöneldiği meslekler. Ayrıntı için bir mesleğe dokun.</div>
      {liste.map((m, i) => {
        const a = acik === i
        return (
          <div key={i} style={{ border: `1.5px solid ${a ? 'var(--pu)' : 'var(--bor)'}`, borderRadius: 14, marginBottom: 10, background: 'var(--sur)', overflow: 'hidden' }}>
            <button
              onClick={() => setAcik(a ? -1 : i)}
              style={{ width: '100%', textAlign: 'left', background: 'none', border: 'none', padding: '12px 14px', cursor: 'pointer', color: 'var(--tx)' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                <div style={{ fontSize: 14, fontWeight: 800 }}>{m.ad}</div>
                <div style={{ color: 'var(--pu)', fontWeight: 800 }}>{a ? '−' : '+'}</div>
              </div>
              <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.55, marginTop: 4 }}>{m.aciklama}</div>
            </button>
            {a && (
              <div style={{ padding: '0 14px 14px', fontSize: 13, color: 'var(--tx2)', lineHeight: 1.6 }}>
                {m.gunluk_isler?.length >= 3 && bolumId && window.__filizSimulasyon && (
                  <button className="btn" style={{ margin: '4px 0 8px' }} onClick={() => window.dispatchEvent(new CustomEvent('simulasyon-ac', { detail: { bolumId, meslek: i, ad: m.ad } }))}>🎬 Bir gününü yaşa</button>
                )}
                {m.gunluk_isler?.length > 0 && (
                  <>
                    <div style={{ fontWeight: 800, color: 'var(--tx)', margin: '6px 0 4px', fontSize: 12.5 }}>Bir iş gününde neler yapar?</div>
                    <Liste maddeler={m.gunluk_isler} />
                  </>
                )}
                {m.calisma_ortami && (
                  <>
                    <div style={{ fontWeight: 800, color: 'var(--tx)', margin: '10px 0 4px', fontSize: 12.5 }}>Çalışma ortamı</div>
                    <div>{m.calisma_ortami}</div>
                  </>
                )}
                {m.gerekli_beceriler?.length > 0 && (
                  <>
                    <div style={{ fontWeight: 800, color: 'var(--tx)', margin: '10px 0 6px', fontSize: 12.5 }}>Gerekli beceriler</div>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      {m.gerekli_beceriler.map((b, j) => (
                        <span key={j} style={{ fontSize: 12, fontWeight: 700, padding: '4px 10px', borderRadius: 999, background: 'var(--grl)', color: 'var(--gr)' }}>{b}</span>
                      ))}
                    </div>
                  </>
                )}
                {m.nasil_olunur && (
                  <>
                    <div style={{ fontWeight: 800, color: 'var(--tx)', margin: '10px 0 4px', fontSize: 12.5 }}>Bu mesleğe nasıl ulaşılır?</div>
                    <div>{m.nasil_olunur}</div>
                  </>
                )}
              </div>
            )}
          </div>
        )
      })}
    </>
  )
}

// [2026-10-09] Meslek dili: sahada kullanılan terimler, anlamları ve gerçek bir cümle içinde kullanımı.
// "Kendini dene" modunda anlam gizlenir; öğrenci önce tahmin eder, sonra karta dokunup açar.
function MeslekDili({ terimler }) {
  const [arama, setArama] = useState('')
  const [dene, setDene] = useState(false)
  const [acik, setAcik] = useState({})
  if (!terimler?.length) return <div className="ps" style={{ margin: 0 }}>Bu bölümün meslek dili şu an gösterilemiyor.</div>
  const q = arama.trim().toLocaleLowerCase('tr')
  const liste = terimler.filter((t) => !q || `${t.terim} ${t.anlam}`.toLocaleLowerCase('tr').includes(q))
  const secim = { fontSize: 12.5, padding: '7px 10px', borderRadius: 10, border: '1.5px solid var(--bor2)', background: 'var(--sur)', color: 'var(--tx)' }
  return (
    <>
      <div className="ps" style={{ margin: '0 0 12px', fontSize: 12.5, lineHeight: 1.55 }}>
        Bu alanda çalışanların her gün kullandığı kelimeler. Bir mezunla konuşurken ya da staj yaparken bu terimleri tanımak işini kolaylaştırır.
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
        <input placeholder="Terim ara…" value={arama} onChange={(e) => setArama(e.target.value)} style={{ ...secim, flex: '1 1 160px' }} />
        <button
          onClick={() => { setDene(!dene); setAcik({}) }}
          style={{ ...secim, cursor: 'pointer', fontWeight: 800, borderColor: dene ? 'var(--pu)' : 'var(--bor2)', color: dene ? 'var(--pu)' : 'var(--tx)' }}
        >{dene ? '✓ Kendini dene açık' : '🧠 Kendini dene'}</button>
      </div>
      {dene && <div className="ps" style={{ margin: '0 0 10px', fontSize: 12 }}>Anlamı tahmin et, sonra görmek için karta dokun.</div>}
      {liste.map((t, i) => {
        const gizli = dene && !acik[t.terim]
        return (
          <div
            key={t.terim}
            onClick={dene ? () => setAcik({ ...acik, [t.terim]: !acik[t.terim] }) : undefined}
            style={{ border: '1.5px solid var(--bor)', borderRadius: 14, padding: '11px 14px', marginBottom: 8, background: 'var(--sur)', cursor: dene ? 'pointer' : 'default' }}
          >
            <div style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
              <span style={{ fontSize: 11, fontWeight: 800, color: 'var(--tx3)', minWidth: 18 }}>{i + 1}</span>
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--tx)' }}>{t.terim}</div>
                {gizli ? (
                  <div style={{ fontSize: 12.5, color: 'var(--tx3)', marginTop: 4 }}>Anlamı görmek için dokun</div>
                ) : (
                  <>
                    <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.55, marginTop: 3 }}>{t.anlam}</div>
                    {t.ornek && (
                      <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5, marginTop: 6, padding: '6px 10px', borderLeft: '3px solid var(--pum)', background: 'var(--pul)', borderRadius: '0 8px 8px 0', fontStyle: 'italic' }}>
                        “{t.ornek}”
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )
      })}
      {liste.length === 0 && <div className="ps" style={{ margin: 0 }}>Aramana uyan terim yok.</div>}
    </>
  )
}

function Universiteler({ bolumId }) {
  const [veri, setVeri] = useState(null)
  const [hata, setHata] = useState(null)
  const [il, setIl] = useState('')
  const [tur, setTur] = useState('')
  const [arama, setArama] = useState('')
  const [siralama, setSiralama] = useState('basari')

  useEffect(() => {
    let iptal = false
    setVeri(null); setHata(null)
    api.bolumUniversiteleri(bolumId)
      .then((v) => { if (!iptal) setVeri(v) })
      .catch((e) => { if (!iptal) setHata(e.detail || 'Üniversite bilgileri alınamadı.') })
    return () => { iptal = true }
  }, [bolumId])

  const programlar = veri?.programlar || []
  const iller = useMemo(() => [...new Set(programlar.map((p) => p.il).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'tr')), [programlar])
  const liste = useMemo(() => {
    const q = arama.trim().toLocaleLowerCase('tr')
    const s = programlar.filter((p) =>
      (!il || p.il === il) &&
      (!tur || turGrubu(p.universite_turu) === tur) &&
      (!q || `${p.universite} ${p.program}`.toLocaleLowerCase('tr').includes(q)))
    const anahtar = { basari: (p) => p.basari_sirasi ?? 1e12, kontenjan: (p) => -(p.kontenjan ?? -1), ad: null }[siralama]
    return anahtar ? [...s].sort((a, b) => anahtar(a) - anahtar(b)) : [...s].sort((a, b) => a.universite.localeCompare(b.universite, 'tr'))
  }, [programlar, il, tur, arama, siralama])

  if (hata) return <div className="ps" style={{ margin: 0 }}>{hata}</div>
  if (!veri) return <div className="ps" style={{ margin: 0 }}>YÖK Atlas'tan bilgiler alınıyor… (ilk açılışta birkaç saniye sürebilir)</div>
  if (veri.durum === 'ozel_yetenek') return <div className="yp-uyari" style={{ margin: 0 }}><b>🎨 Özel yetenek sınavıyla öğrenci alan bölüm</b><div style={{ marginTop: 4 }}>{veri.mesaj}</div></div>
  if (veri.durum !== 'tamam') return <div className="ps" style={{ margin: 0 }}>{veri.mesaj}</div>

  const secim = { fontSize: 12.5, padding: '7px 9px', borderRadius: 10, border: '1.5px solid var(--bor2)', background: 'var(--sur)', color: 'var(--tx)' }
  return (
    <>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
        <input placeholder="Üniversite ara…" value={arama} onChange={(e) => setArama(e.target.value)} style={{ ...secim, flex: '1 1 150px' }} />
        <select value={il} onChange={(e) => setIl(e.target.value)} style={secim}>
          <option value="">Tüm şehirler</option>
          {iller.map((x) => <option key={x} value={x}>{x}</option>)}
        </select>
        <select value={tur} onChange={(e) => setTur(e.target.value)} style={secim}>
          <option value="">Tüm üniversiteler</option>
          <option value="DEVLET">Devlet</option>
          <option value="VAKIF">Vakıf</option>
          <option value="DIGER">KKTC / yurt dışı</option>
        </select>
        <select value={siralama} onChange={(e) => setSiralama(e.target.value)} style={secim}>
          <option value="basari">Başarı sırasına göre</option>
          <option value="kontenjan">Kontenjana göre</option>
          <option value="ad">Üniversite adına göre</option>
        </select>
      </div>
      <div className="ps" style={{ margin: '0 0 10px', fontSize: 12 }}>
        {liste.length} program · {veri.yil ? `${veri.yil} yerleştirme verileri` : 'son yerleştirme verileri'} · Kaynak: YÖK Atlas.
        {' '}Tercih yapmadan önce güncel bilgiyi ÖSYM kılavuzundan doğrula.
      </div>
      {liste.map((p) => (
        <div key={p.kilavuz_kodu} style={{ border: '1.5px solid var(--bor)', borderRadius: 14, padding: '11px 13px', marginBottom: 8, background: 'var(--sur)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 13.5, fontWeight: 800, color: 'var(--tx)' }}>{p.universite}</div>
              <div style={{ fontSize: 12, color: 'var(--tx2)', marginTop: 2 }}>
                {[p.il, turAdi(p.universite_turu), p.program].filter(Boolean).join(' · ')}
              </div>
            </div>
            <a
              href={`https://yokatlas.yok.gov.tr/${p.ogrenim_suresi && p.ogrenim_suresi <= 2 ? 'onlisans' : 'lisans'}.php?y=${p.kilavuz_kodu}`}
              target="_blank" rel="noopener noreferrer"
              style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--pu)', whiteSpace: 'nowrap' }}
            >YÖK Atlas ↗</a>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginTop: 9 }}>
            {[['Kontenjan', sayi(p.kontenjan)], ['Taban puan', sayi(p.taban_puan, 2)], ['Başarı sırası', sayi(p.basari_sirasi)]].map(([k, v]) => (
              <div key={k} style={{ background: 'var(--sur2)', borderRadius: 10, padding: '6px 8px' }}>
                <div style={{ fontSize: 10.5, color: 'var(--tx3)', fontWeight: 700 }}>{k}</div>
                <div style={{ fontSize: 13.5, fontWeight: 800, color: 'var(--tx)' }}>{v}</div>
              </div>
            ))}
          </div>
          {p.gecmis?.length > 0 && (
            <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginTop: 7 }}>
              Önceki yıllar (başarı sırası): {p.gecmis.map((g) => `${g.yil}: ${sayi(g.basari_sirasi)}`).join(' · ')}
            </div>
          )}
        </div>
      ))}
    </>
  )
}

// Bölüm içeriği: başlık + sekmeler + içerik. Hem açılır pencerede hem Keşfet sayfasında (gömülü) kullanılır.
export function BolumBilgiIcerik({ bolumId, ad, baslangicSekme = 'genel', onKapat, gomulu = false, ustEk = null }) {
  const [bilgi, setBilgi] = useState(null)
  const [hata, setHata] = useState(null)
  const [sekme, setSekme] = useState(baslangicSekme)

  useEffect(() => { setSekme(baslangicSekme) }, [baslangicSekme, bolumId])
  useEffect(() => {
    let iptal = false
    setBilgi(null); setHata(null)
    const yukle = async () => {
      try {
        let id = bolumId
        if (!id && ad) id = (await api.bolumAdaGore(ad)).bolum_id
        const b = await api.bolumBilgi(id)
        if (!iptal) setBilgi(b)
      } catch (e) {
        if (!iptal) setHata(e.detail || 'Bölüm bilgisi alınamadı.')
      }
    }
    yukle()
    return () => { iptal = true }
  }, [bolumId, ad])

  const d = bilgi?.detay
  const etiket = { fontSize: 11.5, fontWeight: 700, padding: '3px 9px', borderRadius: 999, background: 'var(--sur2)', color: 'var(--tx2)' }
  return (
    <>
      <div style={{ padding: gomulu ? '16px 18px 0' : '16px 18px 0', borderBottom: '1px solid var(--bor)', background: 'var(--sur)', ...(gomulu ? { borderRadius: '16px 16px 0 0', border: '1.5px solid var(--bor)' } : {}) }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
          <div style={{ minWidth: 0 }}>
            {bilgi?.ust_alan && (
              <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--tx3)', textTransform: 'uppercase', letterSpacing: 0.3 }}>
                {bilgi.ust_alan}{bilgi.alt_alan ? ` · ${bilgi.alt_alan}` : ''}
              </div>
            )}
            <div style={{ fontFamily: 'var(--fd)', fontSize: 21, fontWeight: 700, color: 'var(--tx)', lineHeight: 1.25 }}>
              {bilgi?.ad || ad || 'Bölüm'}
            </div>
            {d && (
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                {d.ogrenim_suresi && <span style={etiket}>⏱ {d.ogrenim_suresi}</span>}
                {d.puan_turu && <span style={etiket}>📝 {d.puan_turu}</span>}
              </div>
            )}
          </div>
          {/* [2026-10-10] Öğrenci tarafında ★ Listeme ekle (yönetim ekranlarında gösterilmez) */}
          {bilgi?.bolum_id && !window.location.pathname.startsWith('/admin') && (
            <div className="ks-pencere-eylem">
              <FavoriYildiz id={bilgi.bolum_id} ad={bilgi.ad} etiketli />
              <KarsilastirDugmesi id={bilgi.bolum_id} ad={bilgi.ad} etiketli />   {/* [2026-10-11] */}
            </div>
          )}
          {ustEk}
          {onKapat && (
            <button onClick={onKapat} aria-label="Kapat" style={{ border: 'none', background: 'var(--sur2)', borderRadius: 10, width: 34, height: 34, fontSize: 18, cursor: 'pointer', color: 'var(--tx)', flexShrink: 0 }}>×</button>
          )}
        </div>
        <div style={{ display: 'flex', gap: 2, marginTop: 12, overflowX: 'auto' }}>
          {SEKMELER.map((s) => (
            <button
              key={s.kod}
              onClick={() => setSekme(s.kod)}
              style={{
                border: 'none', background: 'none', cursor: 'pointer', padding: '9px 12px', fontSize: 13, fontWeight: 800, whiteSpace: 'nowrap',
                color: sekme === s.kod ? 'var(--pu)' : 'var(--tx2)', borderBottom: `3px solid ${sekme === s.kod ? 'var(--pu)' : 'transparent'}`,
              }}
            >{s.ad}</button>
          ))}
        </div>
      </div>
      <div style={{ padding: 16, ...(gomulu ? { border: '1.5px solid var(--bor)', borderTop: 'none', borderRadius: '0 0 16px 16px', background: 'var(--bg)' } : { overflowY: 'auto', flex: 1, minHeight: 0 }) }}>
        {hata ? <div className="ps" style={{ margin: 0 }}>{hata}</div>
          : !bilgi ? <div className="ps" style={{ margin: 0 }}>Yükleniyor…</div>
            : sekme === 'genel' ? <GenelBakis bilgi={bilgi} />
              : sekme === 'meslek' ? <Meslekler detay={d} bolumId={bilgi?.bolum_id || bilgi?.id || bolumId} />
                : sekme === 'jargon' ? <MeslekDili terimler={bilgi.jargon} />
                : sekme === 'yetkinlik' ? <YetkinlikProfili bolumId={bilgi.bolum_id} />
                  : <Universiteler bolumId={bilgi.bolum_id} />}
      </div>
    </>
  )
}

export default function BolumBilgiPenceresi({ secim, onKapat }) {
  useEffect(() => {
    const tus = (e) => { if (e.key === 'Escape') onKapat() }
    window.addEventListener('keydown', tus)
    const eski = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { window.removeEventListener('keydown', tus); document.body.style.overflow = eski }
  }, [onKapat])

  return (
    <div
      onClick={onKapat}
      style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(20,16,8,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 12 }}
    >
      <div
        role="dialog" aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 760, maxHeight: '92vh', display: 'flex', flexDirection: 'column',
          background: 'var(--bg)', borderRadius: 20, boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden',
        }}
      >
        <BolumBilgiIcerik bolumId={secim.id} ad={secim.ad} baslangicSekme={secim.sekme || 'genel'} onKapat={onKapat} />
      </div>
    </div>
  )
}
