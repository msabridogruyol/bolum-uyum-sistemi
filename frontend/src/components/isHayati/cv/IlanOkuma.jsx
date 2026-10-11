// [2026-10-10] CV Atölyesi → "İlan okuma" egzersizi. İlanlar KURGUSALDIR (backend/app/data/ornek_ilanlar.json); seçili bölümle ilgili olanlar önce.
// Öğrenci her satırı işaretler (zorunlu / tercih edilen / satır arası beklenti / genel bilgi), sonra açıklamalı çözümü görür.
import { useEffect, useState } from 'react'
import { api } from '../../../api/client'

const SIRA = ['zorunlu', 'tercih', 'gizli', 'bilgi']
const RENK = { zorunlu: 'var(--re)', tercih: 'var(--gr)', gizli: 'var(--am)', bilgi: 'var(--tx3)' }
const KISA = { zorunlu: 'Zorunlu', tercih: 'Tercih', gizli: 'Satır arası', bilgi: 'Bilgi' }

function oku(anahtar) { try { return JSON.parse(localStorage.getItem(anahtar) || 'null') } catch { return null } }
function yaz(anahtar, v) { try { localStorage.setItem(anahtar, JSON.stringify(v)) } catch { /* depolama kapalı */ } }

function Ilan({ ilan, kategoriler, onGeri }) {
  const ANAHTAR = `fz-ilan-${ilan.id}`
  const [isaret, setIsaret] = useState(() => oku(ANAHTAR)?.isaret || {})
  const [cozum, setCozum] = useState(() => !!oku(ANAHTAR)?.cozum)
  useEffect(() => { yaz(ANAHTAR, { isaret, cozum }) }, [ANAHTAR, isaret, cozum])
  const isaretli = Object.keys(isaret).length
  const dogru = ilan.satirlar.filter((s, i) => isaret[i] === s.dogru).length
  return (
    <div>
      <button className="back" onClick={onGeri}>← Tüm örnek ilanlar</button>
      <div className="card cva-ilan">
        <div className="cva-ornek-etiket">ÖRNEK İLAN — gerçek bir şirkete ait değil</div>
        <div style={{ fontSize: 17, fontWeight: 800, marginTop: 8 }}>{ilan.baslik}</div>
        <div className="yp-ince">{ilan.isveren} · {ilan.tur}</div>
        <div className="yp-ince" style={{ margin: '12px 0 8px', lineHeight: 1.55 }}>
          Her satır için seç: <b style={{ color: RENK.zorunlu }}>Zorunlu</b> (yoksa elenirsin) · <b style={{ color: RENK.tercih }}>Tercih</b> (artı puan) ·
          {' '}<b style={{ color: RENK.gizli }}>Satır arası</b> (açıkça yazmasa da işin temposu, saatleri, sorumluluğu hakkında ipucu) · <b>Bilgi</b> (nitelik değil).
        </div>
        {ilan.satirlar.map((s, i) => {
          const sec = isaret[i]
          const dogruMu = cozum && sec === s.dogru
          return (
            <div key={i} className={`cva-ilan-satir${cozum ? (dogruMu ? ' dogru' : ' yanlis') : ''}`}>
              <div className="cva-ilan-metin">{s.metin}</div>
              <div className="cva-ilan-secim" role="radiogroup" aria-label={`Satır ${i + 1}`}>
                {SIRA.map((k) => (
                  <button key={k} type="button" role="radio" aria-checked={sec === k} disabled={cozum}
                    className={sec === k ? 'secili' : ''} style={sec === k ? { borderColor: RENK[k], color: RENK[k] } : undefined}
                    onClick={() => setIsaret({ ...isaret, [i]: k })}>{KISA[k]}</button>
                ))}
              </div>
              {cozum && (
                <div className="cva-ilan-cozum">
                  <b style={{ color: RENK[s.dogru] }}>{dogruMu ? '✓ ' : sec ? '✕ ' : ''}{kategoriler[s.dogru]?.ad || s.dogru}</b>{' — '}{s.aciklama}
                </div>
              )}
            </div>
          )
        })}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginTop: 14 }}>
          {!cozum
            ? <><button className="btn" onClick={() => setCozum(true)}>Çözümü göster</button><span className="yp-ince">{isaretli}/{ilan.satirlar.length} satır işaretlendi</span></>
            : <><div style={{ fontWeight: 800 }}>{dogru}/{ilan.satirlar.length} doğru</div><button className="btn sec" onClick={() => { setIsaret({}); setCozum(false) }}>Yeniden dene</button></>}
        </div>
        {cozum && ilan.notlar?.length > 0 && (
          <div className="yp-kutu" style={{ marginTop: 14 }}>
            <div className="ct" style={{ marginBottom: 6 }}>Bu ilandan çıkarılacak dersler</div>
            {ilan.notlar.map((n) => <div key={n} style={{ fontSize: 12.5, lineHeight: 1.55, marginBottom: 4 }}>• {n}</div>)}
          </div>
        )}
      </div>
    </div>
  )
}

export default function IlanOkuma({ bolum }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [secili, setSecili] = useState(null)
  useEffect(() => { api.isHayatiCvIlanlar(bolum?.id).then(setV).catch((e) => setHata(e.detail || 'İlanlar yüklenemedi.')) }, [bolum?.id])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const ilan = v.ilanlar.find((x) => x.id === secili)
  if (ilan) return <Ilan ilan={ilan} kategoriler={v.kategoriler} onGeri={() => setSecili(null)} />
  return (
    <div>
      <div className="card">
        <div className="ct">🔎 İlan okumayı öğren</div>
        <div className="yp-ince" style={{ lineHeight: 1.6, fontSize: 12.5 }}>
          Bir ilanı doğru okumak, hem doğru yere başvurmanı hem de CV'ni ilana göre uyarlamanı sağlar. "Zorunlu" nitelikleri karşılamıyorsan başvurma;
          "tercih edilen"ler eksikse yine de başvurabilirsin. Satır aralarındaki ifadeler ("dinamik ekip", "esnek saatler") kötü bir şey anlatmaz, işin
          gerçek temposunu anlatır: sana uyup uymadığını düşün.
        </div>
        <div className="cva-ornek-etiket" style={{ marginTop: 10 }}>{v.not}</div>
      </div>
      <div className="cva-ilan-liste">
        {v.ilanlar.map((x) => {
          const kayit = oku(`fz-ilan-${x.id}`)
          const sonuc = kayit?.cozum ? x.satirlar.filter((s, i) => kayit.isaret?.[i] === s.dogru).length : null
          return (
            <button key={x.id} type="button" className="card cva-ilan-kart" onClick={() => setSecili(x.id)}>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
                <span className="pf-rozet">{x.tur}</span>
                {x.ilgili && <span className="pf-rozet onay">{bolum?.ad ? 'Bölümünle ilgili' : 'İlgili'}</span>}
                {sonuc != null && <span className="pf-rozet">{sonuc}/{x.satirlar.length} doğru</span>}
              </div>
              <div style={{ fontWeight: 800, fontSize: 14 }}>{x.baslik}</div>
              <div className="yp-ince" style={{ marginTop: 2 }}>{x.isveren}</div>
            </button>
          )
        })}
      </div>
    </div>
  )
}
