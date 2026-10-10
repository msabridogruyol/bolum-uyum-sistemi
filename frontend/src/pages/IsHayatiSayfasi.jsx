// [2026-10-10] İş Hayatı (modül: is_hayati) — "pembe rüyadan uyan, ama umudunu kaybetme".
// Üstte bölüm seçici (varsayılan: hedef bölüm, yoksa 1. öneri; tüm bölümlerden aranabilir), kısa veri şeridi, altta sekmeler.
// Sekmeler components/isHayati/sekmeler.js'de tanımlıdır; her biri { bolum, veri, ogrenci } alır. Seçili bölüm ve sekme URL'de
// (?bolum=ID&sekme=kod) tutulur.
import { Suspense, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { SEKMELER, VARSAYILAN_SEKME } from '../components/isHayati/sekmeler'
import VerilerHakkinda from '../components/isHayati/VerilerHakkinda'
import { KAZANC_GRUBU_RENK, ay, yuzde } from '../components/isHayati/ortak'

function BolumSecici({ ozet, secili, onSec }) {
  const [ara, setAra] = useState('')
  const [acik, setAcik] = useState(false)
  const kucuk = (s) => (s || '').toLocaleLowerCase('tr-TR')
  const sonuclar = useMemo(() => (ara.trim().length < 2 ? [] : ozet.bolumler.filter((b) => kucuk(b.ad).includes(kucuk(ara.trim()))).slice(0, 12)), [ara, ozet])
  const hizli = [...(ozet.hedef ? [{ ...ozet.hedef, etiket: '🎯 Hedefin' }] : []),
    ...ozet.oneriler.filter((o) => o.id !== ozet.hedef?.id).map((o) => ({ ...o, etiket: `${o.sira}. öneri` }))]
  return (
    <div className="card" style={{ padding: '14px 16px' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
        {hizli.map((b) => (
          <button key={b.id} onClick={() => onSec(b.id)} className="yp-mini"
            style={secili === b.id ? { background: 'var(--pu)', borderColor: 'var(--pu)', color: '#fff' } : undefined}>
            {b.ad} <span style={{ opacity: 0.75, fontWeight: 600 }}>· {b.etiket}</span>
          </button>
        ))}
        <div style={{ position: 'relative', marginLeft: hizli.length ? 'auto' : 0, minWidth: 220, flex: hizli.length ? '0 1 280px' : 1 }}>
          <input className="yp-sec" style={{ width: '100%' }} value={ara} placeholder="🔎 Başka bir bölüm ara…"
            onChange={(e) => { setAra(e.target.value); setAcik(true) }} onFocus={() => setAcik(true)}
            onBlur={() => setTimeout(() => setAcik(false), 150)} aria-label="Bölüm ara" />
          {acik && sonuclar.length > 0 && (
            <div role="listbox" style={{ position: 'absolute', zIndex: 20, top: '100%', left: 0, right: 0, marginTop: 4, background: 'var(--sur)', border: '1.5px solid var(--bor)', borderRadius: 10, maxHeight: 280, overflow: 'auto', boxShadow: '0 8px 24px rgba(0,0,0,.12)' }}>
              {sonuclar.map((b) => (
                <div key={b.id} role="option" aria-selected={secili === b.id} tabIndex={0}
                  onMouseDown={() => { onSec(b.id); setAra(''); setAcik(false) }}
                  onKeyDown={(e) => { if (e.key === 'Enter') { onSec(b.id); setAra(''); setAcik(false) } }}
                  style={{ padding: '8px 12px', fontSize: 13, cursor: 'pointer', borderBottom: '1px solid var(--bor)' }}>{b.ad}</div>
              ))}
            </div>
          )}
        </div>
      </div>
      {!hizli.length && <div className="yp-ince" style={{ marginTop: 8 }}>Hedef bölüm seçtiğinde ya da değerlendirmeni tamamladığında önerilerin burada hazır gelir.</div>}
    </div>
  )
}

function Seritte({ etiket, deger, renk, alt }) {
  return (
    <div className="yp-kpi" style={{ padding: '10px 12px' }}>
      <div className="yp-kpi-e">{etiket}</div>
      <div className="yp-kpi-d" style={{ fontSize: 20, color: renk || 'var(--tx)' }}>{deger}</div>
      {alt && <div className="yp-kpi-a">{alt}</div>}
    </div>
  )
}

function KisaSerit({ veri }) {
  const i = veri.istihdam
  if (!i) {
    return (
      <div className="card" style={{ padding: '12px 16px', fontSize: 12.5, color: 'var(--tx2)' }}>
        📭 Bu bölüm için henüz resmî istihdam verisi yüklenmedi. Sekmelerdeki genel bilgiler yine de işine yarar.
      </div>
    )
  }
  return (
    <div className="yp-kpi-grid" style={{ marginBottom: 0 }}>
      <Seritte etiket="Mezun istihdamı" deger={yuzde(i.istihdam_orani)} alt={`TÜİK · ${i.veri_yili}`} />
      <Seritte etiket="İş bulma süresi" deger={ay(i.is_bulma_suresi_ay)} alt="ortalama" />
      <Seritte etiket="Alanında çalışan" deger={yuzde(i.alan_uyum_orani)} alt="mezunlar içinde" />
      <Seritte etiket="Kazanç düzeyi" deger={i.kazanc_grubu_ad || '—'} renk={KAZANC_GRUBU_RENK[i.kazanc_grubu]} alt="diğer programlara göre" />
    </div>
  )
}

export default function IsHayatiSayfasi() {
  const [params, setParams] = useSearchParams()
  const [ozet, setOzet] = useState(null)
  const [ogrenci, setOgrenci] = useState(null)
  const [veri, setVeri] = useState(null)
  const [hata, setHata] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)

  const sekme = SEKMELER.some((s) => s.kod === params.get('sekme')) ? params.get('sekme') : VARSAYILAN_SEKME
  const bolumId = Number(params.get('bolum')) || ozet?.varsayilan_bolum_id || null

  function paramDegistir(degisim) {
    const p = new URLSearchParams(params)
    Object.entries(degisim).forEach(([k, v]) => (v == null ? p.delete(k) : p.set(k, String(v))))
    setParams(p, { replace: true })
  }

  useEffect(() => {
    api.isHayatiOzet().then(setOzet).catch((e) => setHata(e.detail || 'İş Hayatı verileri yüklenemedi.'))
    api.profilGetir().then(setOgrenci).catch(() => {})
  }, [])

  useEffect(() => {
    if (!bolumId) return
    let iptal = false
    setYukleniyor(true); setHata(null)
    api.isHayatiBolum(bolumId)
      .then((v) => { if (!iptal) setVeri(v) })
      .catch((e) => { if (!iptal) { setVeri(null); setHata(e.detail || 'Bölüm verisi yüklenemedi.') } })
      .finally(() => { if (!iptal) setYukleniyor(false) })
    return () => { iptal = true }
  }, [bolumId])

  const aktif = SEKMELER.find((s) => s.kod === sekme)
  const Bilesen = aktif.bilesen

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">İş Hayatı</div>
        <div className="ps">Bir mesleğin vitrininin arkasını gör: mezunlar ne kadar sürede iş buluyor, ne kazanıyor, ilk maaş neye yetiyor?
          Gerçekleri bilmek seni korkutmak için değil, yolunu bilerek seçmen için.</div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}
      {!ozet && !hata && <div className="bos-durum">Yükleniyor…</div>}

      {ozet && (
        <div className="koc-kap">
          <BolumSecici ozet={ozet} secili={bolumId} onSec={(id) => paramDegistir({ bolum: id })} />

          {!bolumId && (
            <div className="card bos-durum" style={{ marginTop: 14 }}>Başlamak için yukarıdan bir bölüm ara.</div>
          )}

          {bolumId && veri && veri.bolum.id === bolumId && (
            <>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, flexWrap: 'wrap', margin: '16px 0 10px' }}>
                <div style={{ fontSize: 20, fontWeight: 800 }}>💼 {veri.bolum.ad}</div>
                {veri.bolum.ogrenim_suresi && <span className="yp-ince">{veri.bolum.ogrenim_suresi} · {veri.bolum.meslek_sayisi} meslek</span>}
                {yukleniyor && <span className="yp-ince">güncelleniyor…</span>}
              </div>
              <KisaSerit veri={veri} />

              <div className="koc-sekmeler" role="tablist">
                {SEKMELER.map((s) => (
                  <button key={s.kod} role="tab" aria-selected={sekme === s.kod} className={sekme === s.kod ? 'aktif' : ''}
                    onClick={() => paramDegistir({ sekme: s.kod })}>
                    <span aria-hidden="true">{s.ikon}</span> {s.ad}
                  </button>
                ))}
              </div>
              <Suspense fallback={<div className="bos-durum">Yükleniyor…</div>}>
                <Bilesen key={`${sekme}-${bolumId}`} bolum={veri.bolum} veri={veri} ogrenci={ogrenci} />
              </Suspense>
              <VerilerHakkinda kaynaklar={veri.veri_kaynaklari} />
            </>
          )}
          {bolumId && (!veri || veri.bolum.id !== bolumId) && !hata && <div className="bos-durum">Bölüm verisi yükleniyor…</div>}
        </div>
      )}
    </div>
  )
}
