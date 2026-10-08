// [2026-10-08] Bölüm bilgi kartı — açılır pencere. Sekmeler: Genel Bakış · Meslekler · Üniversiteler (YÖK Atlas)
import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'

const SEKMELER = [
  { kod: 'genel', ad: 'Genel Bakış' },
  { kod: 'meslek', ad: 'Meslekler' },
  { kod: 'uni', ad: 'Üniversiteler' },
]

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
    return <div style={{ fontSize: 13.5, color: 'var(--tx2)', lineHeight: 1.6 }}>{bilgi.kisa_aciklama || 'Bu bölüm için henüz açıklama eklenmedi.'}</div>
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

function Meslekler({ detay }) {
  const [acik, setAcik] = useState(0)
  const liste = detay?.meslekler || []
  if (!liste.length) return <div className="ps" style={{ margin: 0 }}>Bu bölüm için henüz meslek bilgisi eklenmedi.</div>
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

export default function BolumBilgiPenceresi({ secim, onKapat }) {
  const [bilgi, setBilgi] = useState(null)
  const [hata, setHata] = useState(null)
  const [sekme, setSekme] = useState(secim.sekme || 'genel')

  useEffect(() => {
    let iptal = false
    setBilgi(null); setHata(null); setSekme(secim.sekme || 'genel')
    const yukle = async () => {
      try {
        let id = secim.id
        if (!id && secim.ad) id = (await api.bolumAdaGore(secim.ad)).bolum_id
        const b = await api.bolumBilgi(id)
        if (!iptal) setBilgi(b)
      } catch (e) {
        if (!iptal) setHata(e.detail || 'Bölüm bilgisi alınamadı.')
      }
    }
    yukle()
    return () => { iptal = true }
  }, [secim])

  useEffect(() => {
    const tus = (e) => { if (e.key === 'Escape') onKapat() }
    window.addEventListener('keydown', tus)
    const eski = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { window.removeEventListener('keydown', tus); document.body.style.overflow = eski }
  }, [onKapat])

  const d = bilgi?.detay
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
        <div style={{ padding: '16px 18px 0', borderBottom: '1px solid var(--bor)', background: 'var(--sur)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
            <div style={{ minWidth: 0 }}>
              {bilgi?.ust_alan && (
                <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--tx3)', textTransform: 'uppercase', letterSpacing: 0.3 }}>
                  {bilgi.ust_alan}{bilgi.alt_alan ? ` · ${bilgi.alt_alan}` : ''}
                </div>
              )}
              <div style={{ fontFamily: 'var(--fd)', fontSize: 21, fontWeight: 700, color: 'var(--tx)', lineHeight: 1.25 }}>
                {bilgi?.ad || secim.ad || 'Bölüm'}
              </div>
              {d && (
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                  {d.ogrenim_suresi && <span style={{ fontSize: 11.5, fontWeight: 700, padding: '3px 9px', borderRadius: 999, background: 'var(--sur2)', color: 'var(--tx2)' }}>⏱ {d.ogrenim_suresi}</span>}
                  {d.puan_turu && <span style={{ fontSize: 11.5, fontWeight: 700, padding: '3px 9px', borderRadius: 999, background: 'var(--sur2)', color: 'var(--tx2)' }}>📝 {d.puan_turu}</span>}
                </div>
              )}
            </div>
            <button onClick={onKapat} aria-label="Kapat" style={{ border: 'none', background: 'var(--sur2)', borderRadius: 10, width: 34, height: 34, fontSize: 18, cursor: 'pointer', color: 'var(--tx)', flexShrink: 0 }}>×</button>
          </div>
          <div style={{ display: 'flex', gap: 4, marginTop: 12 }}>
            {SEKMELER.map((s) => (
              <button
                key={s.kod}
                onClick={() => setSekme(s.kod)}
                style={{
                  border: 'none', background: 'none', cursor: 'pointer', padding: '9px 12px', fontSize: 13, fontWeight: 800,
                  color: sekme === s.kod ? 'var(--pu)' : 'var(--tx2)', borderBottom: `3px solid ${sekme === s.kod ? 'var(--pu)' : 'transparent'}`,
                }}
              >{s.ad}</button>
            ))}
          </div>
        </div>
        <div style={{ padding: 16, overflowY: 'auto' }}>
          {hata ? <div className="ps" style={{ margin: 0 }}>{hata}</div>
            : !bilgi ? <div className="ps" style={{ margin: 0 }}>Yükleniyor…</div>
              : sekme === 'genel' ? <GenelBakis bilgi={bilgi} />
                : sekme === 'meslek' ? <Meslekler detay={d} />
                  : <Universiteler bolumId={bilgi.bolum_id} />}
        </div>
      </div>
    </div>
  )
}
