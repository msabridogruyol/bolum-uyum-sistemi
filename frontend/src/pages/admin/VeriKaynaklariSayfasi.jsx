// [2026-11-01] Veri Kaynakları (süper admin): sistemdeki dış veriler (TÜİK, YÖK Atlas, asgari ücret, kamu maaşları, bölüm
// profilleri, YKS tarihi…) sistemde var mı, hangi döneme ait, en son ne zaman güncellendi, en son kim ne zaman kontrol etti.
// "Kontrol ettim / Güncelledim / Sorun var" kaydı bırakılır; kayıtlar Audit Log'a da yazılır. Hesap: backend/app/core/veri_kaynaklari.py
import { Fragment, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'

const DURUM = {
  yok: ['✗ Sistemde yok', 're'],
  sorun: ['⚠ Sorun var', 're'],
  bekleniyor: ['⏳ Yeni dönem bekleniyor', 'am'],
  kontrol_zamani: ['🔎 Kontrol zamanı', 'am'],
  guncel: ['✓ Güncel', 'gr'],
}
const RENK = { re: { background: 'var(--rel)', color: 'var(--re)' } }

const tarih = (iso) => (iso ? new Date(iso).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—')
const gunOnce = (iso) => {
  if (!iso) return null
  const g = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000)
  return g <= 0 ? 'bugün' : `${g} gün önce`
}

function Durum({ d }) {
  const [ad, renk] = DURUM[d] || [d, 'am']
  return <span className={`kc-durum kc-durum-${renk}`} style={RENK[renk]}>{ad}</span>
}

function KontrolFormu({ k, onKaydet }) {
  const [sonuc, setSonuc] = useState('guncel')
  const [notlar, setNotlar] = useState('')
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const kaydet = async () => {
    setBekle(true); setHata(null)
    try { await onKaydet(k.kod, sonuc, notlar); setNotlar('') } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
    setBekle(false)
  }
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
      <select className="yp-sec" value={sonuc} onChange={(e) => setSonuc(e.target.value)}>
        <option value="guncel">Kontrol ettim, güncel</option>
        <option value="guncellendi">Güncelledim</option>
        <option value="sorun">Sorun var</option>
      </select>
      <input className="yp-sec" style={{ flex: 1, minWidth: 160 }} value={notlar} maxLength={1000} onChange={(e) => setNotlar(e.target.value)}
        placeholder={sonuc === 'sorun' ? 'Sorunu kısaca yazın (zorunlu)' : 'Not (isteğe bağlı): kaynak, dönem…'} />
      <button className="yp-mini" disabled={bekle || (sonuc === 'sorun' && !notlar.trim())} onClick={kaydet}>Kaydet</button>
      {hata && <div className="auth-error" style={{ width: '100%' }}>{hata}</div>}
    </div>
  )
}

function Satir({ k, acik, onAc, onKaydet }) {
  return (
    <>
      <tr className={acik ? 'secili' : ''}>
        <td style={{ minWidth: 230 }}>
          <b>{k.ad}</b>
          <div className="yp-ince">{k.grup} · {k.kullanim}</div>
        </td>
        <td><Durum d={k.durum} /><div className="yp-ince" style={{ marginTop: 4, maxWidth: 260 }}>{k.aciklama}</div></td>
        <td>{k.kayit ? k.kayit.toLocaleString('tr-TR') : '—'}{k.donem && <div className="yp-ince">{k.donem}</div>}</td>
        <td>{tarih(k.son_guncelleme)}{k.son_guncelleme && <div className="yp-ince">{gunOnce(k.son_guncelleme)}</div>}</td>
        <td>
          {k.son_kontrol ? <>{tarih(k.son_kontrol.zaman)}<div className="yp-ince">{k.son_kontrol.sonuc_ad} · {k.son_kontrol.kontrol_eden || '—'}</div></> : <span className="yp-ince">Kayıt yok</span>}
        </td>
        <td style={{ whiteSpace: 'nowrap' }}>
          <button className="yp-mini" onClick={onAc}>{acik ? 'Kapat' : 'Ayrıntı / kontrol'}</button>
          {k.ekran && <Link className="yp-mini" style={{ marginLeft: 6, textDecoration: 'none' }} to={k.ekran}>Güncelle →</Link>}
        </td>
      </tr>
      {acik && (
        <tr>
          <td colSpan={6} style={{ background: 'var(--sur2)' }}>
            <div style={{ display: 'grid', gap: 10 }}>
              <div className="yp-ince" style={{ fontSize: 12.5 }}>
                {k.kaynak && <div><b>Kaynak:</b> {k.kaynak}</div>}
                {k.ayrinti && <div>{k.ayrinti}</div>}
                <div><b>Kontrol aralığı:</b> {k.kontrol_araligi_gun} gün. Bu, kaynağın ne sıklıkla gözden geçirilmesi gerektiğidir; resmî yayın takvimi değildir.</div>
                {!k.ekran && <div>Bu veri kodla birlikte gelir; güncellemesi kod değişikliğiyle yapılır.</div>}
              </div>
              <KontrolFormu k={k} onKaydet={onKaydet} />
              {k.kontroller.length > 0 && (
                <div>
                  <div className="yp-ince" style={{ fontWeight: 700, marginBottom: 4 }}>Son kontroller</div>
                  {k.kontroller.map((c) => (
                    <div key={c.id} className="yp-ince" style={{ fontSize: 12 }}>
                      {tarih(c.zaman)} · <b>{c.sonuc_ad}</b> · {c.kontrol_eden || '—'}{c.notlar ? ` — ${c.notlar}` : ''}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function VeriKaynaklariSayfasi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [acik, setAcik] = useState(null)
  const [filtre, setFiltre] = useState('hepsi')
  const yukle = () => api.veriKaynaklari().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [])
  const kaydet = async (kod, sonuc, notlar) => { await api.veriKaynagiKontrol(kod, sonuc, notlar); await yukle() }
  const dikkat = v ? v.ozet.yok + v.ozet.sorun + v.ozet.bekleniyor + v.ozet.kontrol_zamani : 0
  const liste = useMemo(() => (v?.kaynaklar || []).filter((k) => filtre === 'hepsi' || (filtre === 'dikkat' ? k.durum !== 'guncel' : k.durum === 'guncel')), [v, filtre])

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Veri Kaynakları</div>
        <div className="ps">Sistemin kullandığı dış veriler: sistemde var mı, hangi döneme ait, en son ne zaman güncellendi ve en son ne zaman kontrol edildi. "Son güncelleme" verinin kendi kaydından okunur; "Son kontrol" burada bıraktığınız kayıttır (Audit Log'a da yazılır). Eksik ya da kontrol zamanı geçen kaynaklar için ayda bir bildirim gelir.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v && !hata && <div className="bos-durum">Yükleniyor…</div>}
      {v && (
        <>
          <div className="yp-kpi-sira" style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
            {[['Toplam kaynak', v.kaynaklar.length], ['Güncel', v.ozet.guncel], ['Kontrol zamanı', v.ozet.kontrol_zamani],
              ['Yeni dönem bekleniyor', v.ozet.bekleniyor], ['Sistemde yok', v.ozet.yok], ['Sorun', v.ozet.sorun]].map(([e, d]) => (
              <div key={e} className="yp-kpi"><div className="yp-kpi-e">{e}</div><div className="yp-kpi-d">{d}</div></div>
            ))}
          </div>
          <div className="kc-filtre">
            {[['hepsi', 'Tümü'], ['dikkat', `Dikkat gerekenler (${dikkat})`], ['guncel', `Güncel (${v.ozet.guncel})`]].map(([kod, ad]) =>
              <button key={kod} className={filtre === kod ? 'aktif' : ''} onClick={() => setFiltre(kod)}>{ad}</button>)}
            <span className="yp-ince" style={{ marginLeft: 'auto' }}>Hesaplandı: {new Date(v.zaman).toLocaleString('tr-TR')}</span>
          </div>
          <div className="card" style={{ padding: 0, overflow: 'auto' }}>
            <table className="yp-tablo">
              <thead><tr><th>Veri</th><th>Durum</th><th>Kayıt / dönem</th><th>Son güncelleme</th><th>Son kontrol</th><th></th></tr></thead>
              <tbody>
                {liste.map((k) => (
                  <Fragment key={k.kod}>
                    <Satir k={k} acik={acik === k.kod} onAc={() => setAcik(acik === k.kod ? null : k.kod)} onKaydet={kaydet} />
                  </Fragment>
                ))}
              </tbody>
            </table>
            {liste.length === 0 && <div className="bos-durum">Bu filtrede kaynak yok.</div>}
          </div>
        </>
      )}
    </div>
  )
}
