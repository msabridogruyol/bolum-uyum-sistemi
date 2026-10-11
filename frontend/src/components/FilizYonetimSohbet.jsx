import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { okulBolumleri } from './yonetim/okulBolumleri'
import { FILIZ_CSS, FilizAcDugmesi, FilizCerceve, durumYayinla } from './FilizSohbet'

// [2026-10-11] Filiz — yönetim paneli asistanı sohbeti ("Bana sor"). Öğrenci sohbetinin görsel parçalarını kullanır.
// POST /yonetim/filiz/sor → { mod: 'ai' | 'rehber', ... }. Yapay zekâ modu (okulda 'filiz_ai' + anahtar) yoksa ya da hata
// verirse kural tabanlı rehber cevap verir. Belirli öğrenci / öğrenci listesi soruları sunucuda YEREL cevaplanır (yapay
// zekâya gitmez). Sohbet yalnızca bu sekmede (bellekte) durur; son birkaç mesaj bağlam için gönderilir, sunucuda saklanmaz.
// Açma: maskottaki "💬 Bana sor" (masaüstü), sağ alttaki "Filiz'e sor" (telefon) ya da window 'filiz-ac' olayı.

/** Okul yetkilisi: paketinde kapalı bölüme giden bağlantıyı gösterme (tek kaynak: okulBolumleri.js). */
export function baglantiAcikMi(yol, okulId, moduller) {
  const m = /^\/admin\/okul\/(\d+)(?:\?sekme=([a-z_]+))?/.exec(yol || '')
  if (!m || !okulId || Number(m[1]) !== Number(okulId)) return true
  const sekme = m[2] || 'ozet'
  return okulBolumleri(Number(okulId), moduller).some((b) => b.k === sekme)
}

export default function FilizYonetimSohbet({ rol, okulId, moduller }) {
  const git = useNavigate()
  const [acik, setAcik] = useState(false)
  const [oneriler, setOneriler] = useState([])
  const [mod, setMod] = useState(null)            // 'ai' | 'rehber'
  const [aydinlatma, setAydinlatma] = useState('')
  const [mesajlar, setMesajlar] = useState([])   // { rol: 'kullanici'|'filiz'|'not', metin, cevap? }
  const [girdi, setGirdi] = useState('')
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const sonRef = useRef(null)
  const girdiRef = useRef(null)
  const gec = (b) => b && baglantiAcikMi(b.yol, okulId, moduller)

  useEffect(() => {
    const ac = (e) => { setAcik(true); if (e.detail?.mesaj) gonder(e.detail.mesaj) }
    window.addEventListener('filiz-ac', ac)
    return () => window.removeEventListener('filiz-ac', ac)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!acik || mod) return
    api.filizYonetimOzet().then((v) => { setOneriler(v.oneriler || []); setMod(v.mod || 'rehber'); setAydinlatma(v.aydinlatma || '') }).catch(() => {})
  }, [acik, mod])

  useEffect(() => { durumYayinla({ acik, dusunuyor: gonderiliyor }) }, [acik, gonderiliyor])
  useEffect(() => { sonRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [mesajlar, gonderiliyor, acik])
  useEffect(() => { if (acik) window.setTimeout(() => girdiRef.current?.focus(), 50) }, [acik])
  useEffect(() => {
    if (!acik) return undefined
    const tus = (e) => { if (e.key === 'Escape') setAcik(false) }
    window.addEventListener('keydown', tus)
    return () => window.removeEventListener('keydown', tus)
  }, [acik])

  async function gonder(metinParam) {
    const metin = (metinParam ?? girdi).trim()
    if (!metin || gonderiliyor) return
    setGirdi('')
    const gecmis = mesajlar.filter((x) => x.rol === 'kullanici' || x.rol === 'filiz').slice(-6).map((x) => ({ rol: x.rol, metin: String(x.metin || '').slice(0, 2000) }))
    setMesajlar((l) => [...l, { rol: 'kullanici', metin }])
    setGonderiliyor(true)
    try {
      const c = await api.filizYonetimSor(metin, gecmis)
      if (c.mod) setMod(c.mod)
      setMesajlar((l) => [...l, { rol: 'filiz', metin: c.metin, cevap: c }])
      durumYayinla({ acik: true, dusunuyor: false, cevaplandi: true })
    } catch (e) {
      setMesajlar((l) => [...l, { rol: 'not', metin: e.status === 403 ? (e.detail || 'Filiz bu panelde açık değil.') : 'Cevap alınamadı, bağlantınızı kontrol edip tekrar deneyin.' }])
    } finally {
      setGonderiliyor(false)
    }
  }

  function ac(yol) {
    git(yol)
    if (window.matchMedia?.('(max-width: 768px)').matches) setAcik(false)   // telefonda panel sayfayı kapatıyor
  }
  const Bag = ({ b }) => <button className="fy-bag" onClick={() => ac(b.yol)}>{b.etiket} →</button>

  const sonCevap = [...mesajlar].reverse().find((x) => x.rol === 'filiz')?.cevap
  const cipler = (sonCevap?.oneriler?.length ? sonCevap.oneriler : oneriler).filter((o) => !mesajlar.some((x) => x.metin === o)).slice(0, 4)
  const baslik = rol === 'super_admin' ? 'Filiz · Panel Asistanı' : 'Filiz · Rehber Asistanı'

  return (
    <>
      {!acik && <FilizAcDugmesi onClick={() => setAcik(true)} aria="Filiz Panel Asistanı'na sor" />}
      {acik && (
        <FilizCerceve baslik={baslik} ariaLabel="Filiz Panel Asistanı" onKapat={() => setAcik(false)}
          durum={gonderiliyor ? 'düşünüyor…' : <span className={`fy-mod fy-mod-${mod || 'rehber'}`}>{mod === 'ai' ? '✨ Yapay zekâ asistanı' : '📘 Rehber modu'}</span>}
          araclar={mesajlar.length > 0 && <button className="filiz-ikon-btn" title="Temizle" onClick={() => setMesajlar([])}>↺</button>}>
          <div className="filiz-oto-serit">
            🔒 {aydinlatma || 'Sorularınız kaydedilmez. Belirli bir öğrenciyle ilgili sorular yalnızca yetkiniz dahilinde, sistem içinde cevaplanır.'}
          </div>
          <div className="filiz-mesajlar">
            {mesajlar.length === 0 && (
              <div className="filiz-bos">
                <div style={{ fontSize: 30 }}>👋</div>
                <div style={{ fontWeight: 700, marginTop: 6 }}>Merhaba! Panelde size yol göstereyim.</div>
                <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 4, lineHeight: 1.5 }}>
                  “Nasıl yaparım / nerede” sorularını, “bugün ne var?” gibi durum sorularını sorabilirsiniz.
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 14, width: '100%' }}>
                  {oneriler.slice(0, 6).map((o) => <button key={o} className="filiz-oneri" onClick={() => gonder(o)}>{o}</button>)}
                </div>
              </div>
            )}
            {mesajlar.map((x, i) => (
              x.rol === 'not' ? <div key={i} className="filiz-not">{x.metin}</div>
                : x.rol === 'kullanici' ? <div key={i} className="filiz-mesaj ogrenci">{x.metin}</div>
                  : (
                    <div key={i} className="filiz-mesaj asistan fy-cevap">
                      <div className={x.cevap?.tur === 'ai' ? 'fy-ai-metin' : undefined}>{x.metin}</div>
                      {x.cevap?.ogrenciler?.length > 0 && (
                        <ul className="fy-ogrenciler">
                          {x.cevap.ogrenciler.map((o) => (
                            <li key={o.id}>
                              <b>{o.ad_soyad}</b>
                              <span>{o.bilgi}</span>
                              <Bag b={o.baglanti} />
                            </li>
                          ))}
                        </ul>
                      )}
                      {x.cevap?.not && <div className="fy-not">{x.cevap.not}</div>}
                      {x.cevap?.bulgular?.length > 0 && (
                        <ul className="fy-bulgular">
                          {x.cevap.bulgular.filter((b) => !b.baglanti || gec(b.baglanti)).map((b) => (
                            <li key={b.k} className={`fy-b-${b.seviye}`}>
                              <span>{b.ikon} {b.metin}</span>
                              {b.baglanti && <Bag b={{ ...b.baglanti, etiket: 'Göster' }} />}
                            </li>
                          ))}
                        </ul>
                      )}
                      {x.cevap?.baglantilar?.filter(gec).length > 0 && (
                        <div className="fy-baglar">{x.cevap.baglantilar.filter(gec).map((b) => <Bag key={b.yol} b={b} />)}</div>
                      )}
                      {x.cevap?.cevaplar?.map((c) => (
                        <details key={c.soru} className="fy-sss" open={!x.cevap.baglantilar?.length && x.cevap.cevaplar.length === 1}>
                          <summary>{c.soru}</summary>
                          <div>{c.cevap}</div>
                          {gec(c.baglanti) && <Bag b={c.baglanti} />}
                        </details>
                      ))}
                    </div>
                  )
            ))}
            {gonderiliyor && <div className="filiz-mesaj asistan filiz-yaziyor"><span /><span /><span /></div>}
            {!gonderiliyor && mesajlar.length > 0 && cipler.length > 0 && (
              <div className="filiz-cipler">{cipler.map((o) => <button key={o} onClick={() => gonder(o)}>{o}</button>)}</div>
            )}
            <div ref={sonRef} />
          </div>
          <form className="filiz-girdi" onSubmit={(e) => { e.preventDefault(); gonder() }}>
            <textarea ref={girdiRef} rows={1} value={girdi} maxLength={500} placeholder={rol === 'super_admin' ? 'Ör. hata kayıtları nerede?' : 'Ör. veli raporu nasıl alınır?'}
              onChange={(e) => setGirdi(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); gonder() } }} />
            <button className="btn" type="submit" disabled={!girdi.trim() || gonderiliyor} aria-label="Gönder">➤</button>
          </form>
          <div className="filiz-alt">Filiz yalnızca yol gösterir; işlemleri ilgili sayfada siz yaparsınız.</div>
        </FilizCerceve>
      )}
      <style>{FILIZ_CSS + FY_CSS}</style>
    </>
  )
}

const FY_CSS = `
.fy-mod{font-weight:700}
.fy-mod-ai{color:var(--pu)}
.fy-ai-metin{white-space:pre-line}
.fy-not{font-size:11.5px;color:var(--tx3)}
.fy-ogrenciler{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.fy-ogrenciler li{display:flex;flex-direction:column;gap:4px;background:var(--sur);border:1px solid var(--bor);border-radius:10px;padding:7px 10px;font-size:12.5px;line-height:1.45}
.fy-ogrenciler li span{color:var(--tx2)}
.fy-cevap{max-width:92%;display:flex;flex-direction:column;gap:8px;white-space:normal}
.fy-baglar{display:flex;flex-wrap:wrap;gap:6px}
.fy-bag{border:1.5px solid var(--pu);background:var(--sur);color:var(--pu);border-radius:999px;padding:4px 11px;font:inherit;font-size:12px;font-weight:800;cursor:pointer;align-self:flex-start}
.fy-bag:hover{background:var(--pu);color:#fff}
.fy-bulgular{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:6px}
.fy-bulgular li{display:flex;flex-direction:column;gap:5px;background:var(--sur);border:1px solid var(--bor);border-left:3px solid var(--tx3);border-radius:10px;padding:7px 10px;font-size:12.5px;line-height:1.45}
.fy-bulgular li.fy-b-yuksek{border-left-color:var(--re,#d9534f)}
.fy-bulgular li.fy-b-uyari{border-left-color:var(--pu)}
.fy-bulgular li.fy-b-bilgi{border-left-color:var(--tl,#2A9D8F)}
.fy-sss{background:var(--sur);border:1px solid var(--bor);border-radius:10px;padding:6px 10px;font-size:12.5px;line-height:1.5}
.fy-sss summary{cursor:pointer;font-weight:700}
.fy-sss > div{margin:6px 0;color:var(--tx2)}
`
