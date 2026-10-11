// [2026-10-10] Anketler (öğrenci) — okulun gönderdiği anketleri yanıtla; isimli tarama formlarında kendi sonucunu gör.
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

function SonucKarti({ s }) {
  if (!s) return null
  return (
    <div className={`an-sonucum ${s.kod}`}>
      <div className="an-sonucum-ad">Sonucun: <b>{s.ad}</b></div>
      <div>{s.metin}</div>
    </div>
  )
}

function Yanitla({ id, onBitti, onGeri }) {
  const [a, setA] = useState(null)
  const [c, setC] = useState({})
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [bitti, setBitti] = useState(null)
  useEffect(() => { api.anketAc(id).then(setA).catch((e) => setHata(e.detail || 'Anket açılamadı.')) }, [id])
  if (!a) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const zorunlu = a.sorular.filter((s) => s.zorunlu)
  const tamam = zorunlu.filter((s) => c[s.id] != null && c[s.id] !== '' && !(Array.isArray(c[s.id]) && !c[s.id].length)).length
  async function gonder() {
    setBekle(true); setHata(null)
    try { const r = await api.anketYanitla(id, c); setBitti(r); onBitti() } catch (e) { setHata(e.detail || 'Gönderilemedi.') } finally { setBekle(false) }
  }
  if (bitti || a.yanitladim) {
    return (
      <div className="card" style={{ maxWidth: 720 }}>
        <div className="ct">{a.baslik}</div>
        <div style={{ fontSize: 15, fontWeight: 700, margin: '6px 0 10px' }}>🙏 Teşekkürler, yanıtların kaydedildi.</div>
        <SonucKarti s={bitti?.sonucum} />
        <button className="btn sec" style={{ marginTop: 12 }} onClick={onGeri}>← Anketlere dön</button>
      </div>
    )
  }
  return (
    <div style={{ maxWidth: 760 }}>
      <button className="hg-link" onClick={onGeri}>← Anketler</button>
      <div className="card" style={{ marginTop: 8 }}>
        <div className="pt" style={{ fontSize: 20 }}>{a.baslik}</div>
        {a.aciklama && <div className="ps" style={{ marginTop: 6 }}>{a.aciklama}</div>}
        <div className="yp-ince" style={{ marginTop: 8 }}>{a.anonim ? '🔒 Bu anket anonim: cevapların adınla eşleştirilmez.' : '👤 Bu form isimli: cevaplarını rehber öğretmenin görür ve sana daha iyi destek olmak için kullanır.'}</div>
      </div>
      {a.sorular.map((s, i) => (
        <div key={s.id} className="card an-yanit-soru">
          <div className="an-yanit-metin"><span>{i + 1}.</span> {s.metin}{!s.zorunlu && <small className="yp-ince"> (isteğe bağlı)</small>}</div>
          {s.tur === 'likert' && (
            <div className="an-likert" role="radiogroup">
              {a.likert.map((e, k) => (
                <button key={k} type="button" role="radio" aria-checked={c[s.id] === k + 1} className={c[s.id] === k + 1 ? 'secili' : ''} onClick={() => setC({ ...c, [s.id]: k + 1 })}>
                  <b>{k + 1}</b><span>{e}</span>
                </button>
              ))}
            </div>
          )}
          {s.tur === 'puan' && (
            <div className="an-puan" role="radiogroup">
              {Array.from({ length: 10 }, (_, k) => <button key={k} type="button" role="radio" aria-checked={c[s.id] === k + 1} className={c[s.id] === k + 1 ? 'secili' : ''} onClick={() => setC({ ...c, [s.id]: k + 1 })}>{k + 1}</button>)}
            </div>
          )}
          {s.tur === 'tek' && s.secenekler.map((e) => (
            <label key={e} className={`an-secenek${c[s.id] === e ? ' secili' : ''}`}><input type="radio" name={s.id} checked={c[s.id] === e} onChange={() => setC({ ...c, [s.id]: e })} />{e}</label>
          ))}
          {s.tur === 'coklu' && s.secenekler.map((e) => {
            const l = c[s.id] || []
            return <label key={e} className={`an-secenek${l.includes(e) ? ' secili' : ''}`}><input type="checkbox" checked={l.includes(e)} onChange={() => setC({ ...c, [s.id]: l.includes(e) ? l.filter((x) => x !== e) : [...l, e] })} />{e}</label>
          })}
          {s.tur === 'acik' && <textarea className="auth-input" rows={3} maxLength={1000} value={c[s.id] || ''} onChange={(e) => setC({ ...c, [s.id]: e.target.value })} />}
        </div>
      ))}
      {hata && <div className="auth-error">{hata}</div>}
      <div className="an-gonder">
        <span className="yp-ince">{tamam} / {zorunlu.length} zorunlu soru yanıtlandı</span>
        <button className="btn" disabled={bekle || tamam < zorunlu.length} onClick={gonder}>{bekle ? <span className="spin" /> : 'Gönder'}</button>
      </div>
    </div>
  )
}

export default function AnketlerSayfasi() {
  const [params, setParams] = useSearchParams()
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const acik = params.get('anket')
  const yukle = () => api.anketlerim().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [])
  const ac = (id) => setParams(id ? { anket: id } : {})
  if (acik) return <div className="pg"><Yanitla id={Number(acik)} onBitti={yukle} onGeri={() => ac(null)} /></div>
  if (!v) return <div className="pg"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>
  const bekleyen = v.anketler.filter((a) => a.acik && !a.yanitladim)
  const biten = v.anketler.filter((a) => a.yanitladim)
  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Anketler</div>
        <div className="ps">Okulunun ve rehber öğretmeninin senin görüşünü almak için gönderdiği anketler.</div>
      </div>
      {bekleyen.length === 0 && biten.length === 0 && <div className="card bos-durum">Şu an yanıtlaman gereken bir anket yok. 🎉</div>}
      {bekleyen.length > 0 && (
        <div className="card">
          <div className="ct">📋 Yanıt bekleyenler</div>
          {bekleyen.map((a) => (
            <div key={a.id} className="an-ogr-satir">
              <div style={{ flex: 1, minWidth: 0 }}>
                <b>{a.baslik}</b>
                <div className="yp-ince">{a.soru_sayisi} soru · yaklaşık {Math.max(2, Math.round(a.soru_sayisi / 3))} dk{a.anonim ? ' · anonim' : ''}{a.bitis ? ` · son gün ${new Date(`${a.bitis}T12:00`).toLocaleDateString('tr-TR')}` : ''}</div>
              </div>
              <button className="btn" onClick={() => ac(a.id)}>Yanıtla →</button>
            </div>
          ))}
        </div>
      )}
      {biten.length > 0 && (
        <div className="card">
          <div className="ct">✓ Yanıtladıkların</div>
          {biten.map((a) => (
            <div key={a.id} className="an-ogr-satir" style={{ alignItems: 'flex-start' }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <b>{a.baslik}</b>
                {a.sonucum && <SonucKarti s={a.sonucum} />}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
