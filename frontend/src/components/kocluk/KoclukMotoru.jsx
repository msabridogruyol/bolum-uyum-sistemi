// [2026-10-10] Koçluk motoru arayüzü: adım bitirirken kısa geri bildirim, alan türü rozeti, tekrar ölçüm kartı ve penceresi.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere } from '../yonetim/ortak'

export const ALAN_TURU_RENK = {
  deger: { renk: 'var(--am)', zemin: 'var(--aml)', ikon: '🧭' },
  aliskanlik: { renk: 'var(--pu)', zemin: 'var(--pul)', ikon: '🌀' },
  beceri: { renk: 'var(--gr)', zemin: 'var(--grl)', ikon: '🛠️' },
  egilim: { renk: 'var(--tl)', zemin: 'var(--tll)', ikon: '🔭' },
}

export function AlanTuruRozeti({ odak }) {
  if (!odak?.alan_turu_etiket) return null
  const r = ALAN_TURU_RENK[odak.alan_turu] || ALAN_TURU_RENK.beceri
  return (
    <span className="alan-turu-rozet" style={{ color: r.renk, background: r.zemin }} title={odak.alan_turu_aciklama || ''}>
      {r.ikon} {odak.alan_turu_etiket}
    </span>
  )
}

// ---------------------------------------------------------------- "Yaptım" sonrası kısa geri bildirim
const FAYDA = [
  { d: 1, e: '😕', a: 'Hiç' }, { d: 2, e: '🙁', a: 'Az' }, { d: 3, e: '😐', a: 'Orta' }, { d: 4, e: '🙂', a: 'Faydalı' }, { d: 5, e: '🤩', a: 'Çok' },
]
const ZORLUK = [{ k: 'kolay', a: 'Kolaydı' }, { k: 'uygun', a: 'Tam kararında' }, { k: 'zor', a: 'Zorladı' }]

export function TamamlaFormu({ adim, onKaydet, onVazgec }) {
  const [f, setF] = useState({ fayda: null, zorluk: null, ne_yaptim: '', ne_ogrendim: '' })
  const [bekle, setBekle] = useState(false)
  async function gonder(bos) {
    setBekle(true)
    await onKaydet(bos ? {} : f)
    setBekle(false)
  }
  return (
    <div className="tamamla-form">
      <div className="tamamla-baslik">🎉 Harika! Bitirmeden önce 20 saniye: nasıl geçti?</div>
      <div className="tamamla-soru">Bu adım sana ne kadar faydalı oldu?</div>
      <div className="tamamla-fayda">
        {FAYDA.map((x) => (
          <button key={x.d} type="button" className={f.fayda === x.d ? 'secili' : ''} onClick={() => setF({ ...f, fayda: x.d })}>
            <span>{x.e}</span><small>{x.a}</small>
          </button>
        ))}
      </div>
      <div className="tamamla-soru">Zorluğu nasıldı?</div>
      <div className="tamamla-zorluk">
        {ZORLUK.map((x) => (
          <button key={x.k} type="button" className={f.zorluk === x.k ? 'secili' : ''} onClick={() => setF({ ...f, zorluk: x.k })}>{x.a}</button>
        ))}
      </div>
      <div className="tamamla-metinler">
        <label><div>Ne yaptın? <span>(isteğe bağlı)</span></div>
          <input maxLength={300} value={f.ne_yaptim} placeholder={`ör. ${adim.olcut || 'kısaca yaz'}`} onChange={(e) => setF({ ...f, ne_yaptim: e.target.value })} />
        </label>
        <label><div>Ne öğrendin? <span>(isteğe bağlı)</span></div>
          <input maxLength={300} value={f.ne_ogrendim} placeholder="Tek cümle yeter" onChange={(e) => setF({ ...f, ne_ogrendim: e.target.value })} />
        </label>
      </div>
      <div className="tamamla-dugmeler">
        <button className="btn" disabled={bekle} onClick={() => gonder(false)}>{bekle ? <span className="spin" /> : '✓ Kaydet ve bitir'}</button>
        <button className="btn sec" disabled={bekle} onClick={() => gonder(true)}>Atla, sadece bitir</button>
        <button className="hg-link" disabled={bekle} onClick={onVazgec}>Vazgeç</button>
      </div>
      <div className="tamamla-not">Cevapların bir sonraki adımı sana göre ayarlamamıza yardım eder. Rehber öğretmenin de gelişimini buradan takip edebilir.</div>
    </div>
  )
}

export function GeriBildirimOzeti({ gb }) {
  if (!gb) return null
  const f = FAYDA.find((x) => x.d === gb.fayda)
  const z = ZORLUK.find((x) => x.k === gb.zorluk)
  return (
    <div className="gb-ozet">
      {f && <span>{f.e} {f.a}</span>}{z && <span>{z.a}</span>}
      {gb.ne_ogrendim && <span className="gb-ogrendim">“{gb.ne_ogrendim}”</span>}
    </div>
  )
}

// ---------------------------------------------------------------- Tekrar ölçüm
export function OlcumKarti({ odak, onOlc }) {
  const o = odak.olcum
  if (!o) return null
  const kalan = Math.max(0, o.gereken - o.tamamlanan_adim)
  const son = o.son
  return (
    <div className={`olcum-kart${o.acik ? ' acik' : ''}`}>
      <div className="olcum-ust">
        <span className="olcum-ikon">📏</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="olcum-ad">{odak.degisken_adi}</div>
          {son ? (
            <div className="olcum-sonuc">
              <span>{Math.round(son.onceki)}</span><span className="olcum-ok">→</span><b>{Math.round(son.yeni)}</b>
              <span className={`olcum-fark ${son.gelisim >= 0 ? 'arti' : 'eksi'}`}>{son.gelisim >= 0 ? '▲' : '▼'} {Math.abs(Math.round(son.gelisim))}</span>
            </div>
          ) : <div className="olcum-alt">Henüz ölçülmedi</div>}
        </div>
      </div>
      {o.acik ? (
        <button className="btn" style={{ width: '100%' }} onClick={() => onOlc(odak)}>Gelişimini ölç · 5 soru, 2 dk</button>
      ) : (
        <>
          <div className="olcum-ilerleme"><div style={{ width: `${Math.max(0, Math.min(100, (100 * (o.tamamlanan_adim - (o.gereken - 3))) / 3))}%` }} /></div>
          <div className="olcum-alt">{kalan} adım sonra yeni ölçüm açılır</div>
        </>
      )}
    </div>
  )
}

export function OlcumPenceresi({ odak, onKapat, onBitti }) {
  const [veri, setVeri] = useState(null)
  const [i, setI] = useState(0)
  const [cevap, setCevap] = useState({})
  const [sonuc, setSonuc] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  useEffect(() => { api.alanOlcumSorulari(odak.degisken_id).then(setVeri).catch((e) => setHata(e.detail || 'Sorular yüklenemedi.')) }, [odak.degisken_id])

  const soru = veri?.sorular[i]
  const ikili = soru?.cevap_bicimi === 'encok_enaz'
  const c = soru ? cevap[soru.id] || {} : {}
  const tamam = ikili ? c.enCok && c.enAz : c.enCok

  function sec(id) {
    const x = { ...c }
    if (!ikili) x.enCok = id
    else if (x.enCok === id) x.enCok = null
    else if (x.enAz === id) x.enAz = null
    else if (!x.enCok) x.enCok = id
    else x.enAz = id
    setCevap({ ...cevap, [soru.id]: x })
  }
  async function bitir() {
    setBekle(true); setHata(null)
    try {
      const r = await api.alanOlcumKaydet(odak.degisken_id, veri.sorular.map((s) => ({ soru_id: s.id, secenek_id: cevap[s.id].enCok, en_az_secenek_id: cevap[s.id].enAz || null })))
      setSonuc(r); onBitti?.()
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }

  return (
    <Pencere baslik={`📏 ${odak.degisken_adi} · gelişimini ölç`} altBaslik="İlk değerlendirmedeki sorulardan birkaçı. Düşünmeden, şu anki hâline göre cevapla." onKapat={onKapat}>
      {hata && <div className="auth-error">{hata}</div>}
      {!veri && !hata && <div className="bos-durum">Yükleniyor…</div>}
      {veri && veri.sorular.length === 0 && <div className="bos-durum">Bu alan için ölçüm sorusu bulunamadı.</div>}
      {sonuc ? (
        <div className="olcum-bitti">
          <div className="olcum-bitti-sayilar">
            <div><small>Önce</small><b>{Math.round(sonuc.onceki)}</b></div>
            <div className="olcum-ok">→</div>
            <div><small>Şimdi</small><b style={{ color: sonuc.gelisim >= 0 ? 'var(--gr)' : 'var(--am)' }}>{Math.round(sonuc.yeni)}</b></div>
          </div>
          <p>{sonuc.yorum}</p>
          <p className="olcum-not">Bu kısa ölçüm bir eğilim göstergesidir; kesin bir puan değildir. Bir sonraki tam değerlendirmede daha net göreceğiz.</p>
          <button className="btn" onClick={onKapat}>Tamam</button>
        </div>
      ) : soru && (
        <div className="olcum-soru">
          <div className="olcum-sayac">Soru {i + 1} / {veri.sorular.length}</div>
          <div className="olcum-metin">{soru.metin}</div>
          {ikili && <div className={`sn-adim ${!c.enCok ? 'bir' : !c.enAz ? 'iki' : 'tamam'}`}>{!c.enCok ? '1. Sana EN ÇOK uyan şıkkı seç.' : !c.enAz ? '2. Şimdi EN AZ uyan şıkkı seç.' : '✓ Tamam.'}</div>}
          <div className="qopts sn-secenekler">
            {soru.secenekler.map((s) => {
              const cok = c.enCok === s.id; const az = ikili && c.enAz === s.id
              return (
                <button key={s.id} className={`qopt sn-secenek${cok ? ' sel' : ''}${az ? ' az' : ''}`} onClick={() => sec(s.id)}>
                  {ikili && (cok || az) && <span className={`sn-isaret ${cok ? 'cok' : 'az'}`}>{cok ? 'EN ÇOK' : 'EN AZ'}</span>}
                  <span>{s.metin}</span>
                </button>
              )
            })}
          </div>
          <div className="qnav sn-nav">
            <button className="btn sec" disabled={i === 0} onClick={() => setI(i - 1)}>← Önceki</button>
            {i < veri.sorular.length - 1
              ? <button className="btn" disabled={!tamam} onClick={() => setI(i + 1)}>Sonraki →</button>
              : <button className="btn" disabled={!tamam || bekle} onClick={bitir}>{bekle ? <span className="spin" /> : 'Sonucu gör ✓'}</button>}
          </div>
        </div>
      )}
    </Pencere>
  )
}
