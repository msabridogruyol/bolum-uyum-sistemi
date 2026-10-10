// [2026-10-10] Bölümler → Karşılaştır: 2-3 bölüm yan yana.
// Satırlar: uyum · alan · puan türü · süre · taban puan / başarı sırası (YÖK Atlas) · öne çıkan özellikler
// (sende de güçlü olanlar ✓) · örnek meslekler · meslek dilinden örnek. Seçim URL'de tutulur (?ids=1,2,3).
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useListem } from './FavoriYildiz'
import FavoriYildiz from './FavoriYildiz'
import { useBolumBilgi } from '../context/BolumBilgiContext'

const sayi = (v) => (v == null ? '—' : Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 2 }))
const liste = (v) => (Array.isArray(v) ? v : [])

function uniOzeti(u) {
  if (!u) return null
  const p = liste(u.programlar)
  const puan = p.map((x) => x.taban_puan).filter((x) => x != null)
  const sira = p.map((x) => x.basari_sirasi).filter((x) => x != null)
  return {
    durum: u.durum, mesaj: u.mesaj, yil: u.yil, program: p.length,
    devlet: p.filter((x) => (x.universite_turu || '').startsWith('DEV')).length,
    puanMin: puan.length ? Math.min(...puan) : null, puanMax: puan.length ? Math.max(...puan) : null,
    siraEn: sira.length ? Math.min(...sira) : null, siraSon: sira.length ? Math.max(...sira) : null,
  }
}

function Secici({ secili, setSecili }) {
  const fav = useListem()
  const [acik, setAcik] = useState(secili.length < 2)
  const [oneri, setOneri] = useState([])
  const [q, setQ] = useState('')
  const [sonuc, setSonuc] = useState(null)
  useEffect(() => { api.siralamaGetir(10).then((l) => setOneri(liste(l))).catch(() => setOneri([])) }, [])

  const adlar = useMemo(() => {
    const m = {}
    ;[...(fav || []), ...oneri, ...(sonuc || [])].forEach((b) => { m[b.bolum_id] = b.bolum_adi })
    return m
  }, [fav, oneri, sonuc])
  const ekle = (b) => setSecili((s) => (s.some((x) => x.id === b.bolum_id) || s.length >= 3 ? s : [...s, { id: b.bolum_id, ad: b.bolum_adi }]))
  const cip = (b) => {
    const var_ = secili.some((x) => x.id === b.bolum_id)
    return (
      <button key={b.bolum_id} type="button" className={`kr-cip${var_ ? ' secili' : ''}`} disabled={!var_ && secili.length >= 3}
        onClick={() => (var_ ? setSecili((s) => s.filter((x) => x.id !== b.bolum_id)) : ekle(b))}>
        {var_ ? '✓ ' : '+ '}{b.bolum_adi}{b.toplam_uyum != null && <span>%{Math.round(b.toplam_uyum)}</span>}
      </button>
    )
  }
  async function ara(e) {
    e.preventDefault()
    if (q.trim().length < 2) return
    try { setSonuc(liste(await api.kesfetAra(q.trim(), 8))) } catch { setSonuc([]) }
  }

  return (
    <div className="card kr-secici">
      <div className="kr-secili">
        {[0, 1, 2].map((i) => (
          <div key={i} className={`kr-yuva${secili[i] ? ' dolu' : ''}`}>
            {secili[i] ? (
              <>
                <span>{secili[i].ad || adlar[secili[i].id] || '…'}</span>
                <button type="button" aria-label="Çıkar" onClick={() => setSecili((s) => s.filter((_, j) => j !== i))}>×</button>
              </>
            ) : <span className="yp-ince">{i < 2 ? `${i + 1}. bölümü seç` : '3. bölüm (isteğe bağlı)'}</span>}
          </div>
        ))}
      </div>
      {!acik ? (
        <button type="button" className="hg-link" onClick={() => setAcik(true)}>{secili.length < 3 ? '+ Bölüm ekle / değiştir' : 'Seçimi değiştir'}</button>
      ) : (<>
      {fav?.length > 0 && (<><div className="kr-baslik">⭐ Listemden</div><div className="kr-cipler">{fav.map(cip)}</div></>)}
      {oneri.length > 0 && (<><div className="kr-baslik">🌟 Sana uygun</div><div className="kr-cipler">{oneri.map(cip)}</div></>)}
      <form onSubmit={ara} style={{ display: 'flex', gap: 8, marginTop: 12 }}>
        <input className="auth-input" style={{ flex: 1, margin: 0 }} value={q} onChange={(e) => setQ(e.target.value)} placeholder="ya da bölüm ara… (örn. Psikoloji)" />
        <button className="btn sec" type="submit">Ara</button>
      </form>
      {sonuc && <div className="kr-cipler" style={{ marginTop: 10 }}>{sonuc.length ? sonuc.map(cip) : <span className="yp-ince">Sonuç yok.</span>}</div>}
      {secili.length >= 2 && <button type="button" className="hg-link" style={{ marginTop: 10 }} onClick={() => setAcik(false)}>Seçimi kapat ↑</button>}
      </>)}
    </div>
  )
}

export default function BolumKarsilastir() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const { ac } = useBolumBilgi()
  const [veri, setVeri] = useState(null)
  const [bilgi, setBilgi] = useState({})
  const [uni, setUni] = useState({})
  const [hata, setHata] = useState(null)

  const secili = useMemo(() => (params.get('ids') || '').split(',').map(Number).filter(Boolean).slice(0, 3)
    .map((id) => ({ id, ad: veri?.bolumler.find((b) => b.bolum_id === id)?.bolum_adi })), [params, veri])
  const setSecili = (f) => {
    const yeni = typeof f === 'function' ? f(secili) : f
    const p = new URLSearchParams(params)
    if (yeni.length) p.set('ids', yeni.map((x) => x.id).join(',')); else p.delete('ids')
    setParams(p, { replace: true })
  }
  const anahtar = secili.map((x) => x.id).join(',')

  useEffect(() => {
    const idler = anahtar ? anahtar.split(',').map(Number) : []
    setHata(null)
    if (idler.length < 2) { setVeri(null); return }
    let iptal = false
    api.bolumKarsilastir(idler).then((d) => { if (!iptal) setVeri(d) }).catch((e) => { if (!iptal) setHata(e.detail || 'Karşılaştırma yapılamadı.') })
    idler.forEach((id) => {
      if (!bilgi[id]) api.bolumBilgi(id).then((b) => !iptal && setBilgi((m) => ({ ...m, [id]: b }))).catch(() => {})
      if (!uni[id]) api.bolumUniversiteleri(id).then((u) => !iptal && setUni((m) => ({ ...m, [id]: u }))).catch(() => !iptal && setUni((m) => ({ ...m, [id]: { durum: 'hata', programlar: [] } })))
    })
    return () => { iptal = true }
  }, [anahtar]) // eslint-disable-line react-hooks/exhaustive-deps

  const kolonlar = veri ? secili.map((s) => veri.bolumler.find((b) => b.bolum_id === s.id)).filter(Boolean) : []
  const enIyiUyum = Math.max(...kolonlar.map((b) => b.toplam_uyum ?? -1))
  const ortusme = (b) => b.one_cikanlar.filter((x) => x.sende).length
  const enIyiOrtusme = Math.max(...kolonlar.map(ortusme))

  const satir = (etiket, hucre, ipucu) => (
    <div className="kr-satir">
      <div className="kr-etiket">{etiket}{ipucu && <small>{ipucu}</small>}</div>
      {kolonlar.map((b) => <div key={b.bolum_id} className="kr-hucre">{hucre(b)}</div>)}
    </div>
  )

  return (
    <>
      <Secici secili={secili} setSecili={setSecili} />
      {hata && <div className="auth-error">{hata}</div>}
      {secili.length < 2 && !hata && (
        <div className="veri-yok-grafik"><div className="vg-ikon">⚖️</div><div className="vg-metin">Yan yana görmek için en az 2 bölüm seç.</div></div>
      )}
      {secili.length >= 2 && !veri && !hata && <div className="bos-durum">Karşılaştırılıyor…</div>}
      {kolonlar.length >= 2 && (
        <>
          {/* Veri temelli kısa okuma: en yüksek uyum ve güçlü yönlerinle en çok örtüşen bölüm */}
          <div className="kr-ozet">
            {enIyiUyum >= 0 && <div>🎯 Uyumun en yüksek: <b>{kolonlar.find((b) => b.toplam_uyum === enIyiUyum)?.bolum_adi}</b> (%{Math.round(enIyiUyum)})</div>}
            {veri.profil_var && enIyiOrtusme > 0 && <div>💪 Güçlü yönlerinle en çok örtüşen: <b>{kolonlar.find((b) => ortusme(b) === enIyiOrtusme)?.bolum_adi}</b> ({enIyiOrtusme}/{kolonlar.find((b) => ortusme(b) === enIyiOrtusme)?.one_cikanlar.length} özellik)</div>}
            <div className="yp-ince">Karar verirken yalnızca yüzdeye değil, aşağıdaki meslekler ve ders içeriğine de bak.</div>
          </div>

          <div className="kr-tablo-kap">
            <div className="kr-tablo" style={{ '--kr-n': kolonlar.length }}>
              <div className="kr-satir kr-bas">
                <div className="kr-etiket" />
                {kolonlar.map((b) => (
                  <div key={b.bolum_id} className="kr-hucre">
                    <div className="kr-alan">{b.ust_alan || ''}</div>
                    <div className="kr-ad">{b.bolum_adi}</div>
                    <div className="kr-eylem">
                      <button className="hg-link" onClick={() => ac(b.bolum_id, b.bolum_adi)}>İncele</button>
                      <FavoriYildiz id={b.bolum_id} ad={b.bolum_adi} />
                    </div>
                  </div>
                ))}
              </div>
              {satir('Uyumun', (b) => b.toplam_uyum == null ? <span className="yp-ince">Değerlendirme bitince</span> : (
                <div className={`kr-uyum${b.toplam_uyum === enIyiUyum ? ' en' : ''}`}>
                  <b>%{Math.round(b.toplam_uyum)}</b>
                  <div className="mini-ilerleme-track"><div className="mini-ilerleme-fill" style={{ width: `${b.toplam_uyum}%`, background: 'var(--pu)' }} /></div>
                </div>
              ))}
              {satir('Alan', (b) => b.alt_alan || b.ust_alan || '—')}
              {satir('Puan türü', (b) => bilgi[b.bolum_id]?.detay?.puan_turu || uni[b.bolum_id]?.programlar?.[0]?.puan_turu || '—')}
              {satir('Öğrenim süresi', (b) => bilgi[b.bolum_id]?.detay?.ogrenim_suresi || '—')}
              {satir('Taban puan', (b) => {
                const o = uniOzeti(uni[b.bolum_id])
                if (!o) return <span className="spin" />
                if (o.puanMin == null) return <span className="yp-ince">{o.mesaj || 'Veri yok'}</span>
                return <>{sayi(o.puanMin)} – {sayi(o.puanMax)}</>
              }, 'YÖK Atlas, en düşük – en yüksek')}
              {satir('Başarı sırası', (b) => {
                const o = uniOzeti(uni[b.bolum_id])
                if (!o) return <span className="spin" />
                if (o.siraEn == null) return '—'
                return <>{sayi(o.siraEn)} – {sayi(o.siraSon)}</>
              }, 'en iyi – en son yerleşen')}
              {satir('Program sayısı', (b) => {
                const o = uniOzeti(uni[b.bolum_id])
                if (!o) return <span className="spin" />
                return o.program ? <>{o.program} program{o.devlet ? <span className="yp-ince"> · {o.devlet} devlet</span> : null}{o.yil ? <span className="yp-ince"> · {o.yil}</span> : null}</> : '—'
              })}
              {satir('Öne çıkan özellikler', (b) => (
                <ul className="kr-liste">
                  {b.one_cikanlar.map((x) => (
                    <li key={x.kod} className={x.sende ? 'sende' : ''} title={x.sende ? 'Bu özellik sende de güçlü' : ''}>
                      <span>{x.sende ? '✓' : '·'}</span>{x.etiket}
                    </li>
                  ))}
                  {!b.one_cikanlar.length && <li>—</li>}
                </ul>
              ), veri.profil_var ? '✓ sende de güçlü' : null)}
              {satir('Örnek meslekler', (b) => {
                const m = liste(bilgi[b.bolum_id]?.detay?.meslekler).map((x) => (typeof x === 'string' ? x : x.ad)).filter(Boolean)
                const l = (m.length ? m : b.meslekler).slice(0, 4)
                return l.length ? <ul className="kr-liste duz">{l.map((x) => <li key={x}>{x}</li>)}</ul> : '—'
              })}
              {satir('Meslek dilinden', (b) => (b.jargon.length ? (
                <ul className="kr-liste kr-jargon">{b.jargon.map((j) => (
                  <li key={j.terim}><b>{j.terim}</b>{j.anlam && <small>{j.anlam.length > 90 ? j.anlam.slice(0, 88) + '…' : j.anlam}</small>}</li>
                ))}</ul>
              ) : '—'))}
              <div className="kr-satir">
                <div className="kr-etiket" />
                {kolonlar.map((b) => (
                  <div key={b.bolum_id} className="kr-hucre">
                    <button className="btn sec" style={{ width: '100%', fontSize: 12.5 }} onClick={() => navigate(`/profil?hedef=${b.bolum_id}#hedef`)}>Hedefim yap</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </>
  )
}
