// [2026-10-10] Tercih dönemi (rehber incelemesi) ve mezun takibi.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere } from './ortak'
import { RiskOzeti, TercihTablosu } from '../../pages/TercihSayfasi'

const DURUM_RENK = { taslak: 'var(--tx3)', incelemede: 'var(--am)', onaylandi: 'var(--gr)', duzeltme: 'var(--re)' }

// ----------------------------------------------------------------------------- öğrencinin listesi + karar
export function OgrenciTercih({ ogrenciId, onKarar }) {
  const [v, setV] = useState(null)
  const [notu, setNotu] = useState('')
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const yukle = useCallback(() => api.ogrenciTercihi(ogrenciId).then((x) => { setV(x); setNotu(x.liste.rehber_notu || '') }).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [ogrenciId])
  useEffect(() => { yukle() }, [yukle])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  async function karar(k) { setBekle(true); setHata(null); try { await api.tercihKarar(ogrenciId, k, notu); await yukle(); onKarar?.() } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) } }
  if (!v.tercihler.length) return <div className="bos-durum">Öğrenci henüz tercih listesi hazırlamadı.</div>
  return (
    <div>
      <div className="yp-ince" style={{ marginBottom: 8 }}>
        Durum: <b style={{ color: DURUM_RENK[v.liste.durum] }}>{v.liste.durum_adi}</b>
        {v.liste.puan_turu && ` · ${v.liste.puan_turu}`}{v.liste.siralama && ` · başarı sırası ${Number(v.liste.siralama).toLocaleString('tr-TR')}`}
        {v.hedef && ` · hedef: ${v.hedef.ad}`}
      </div>
      <RiskOzeti s={v.sayilar} />
      {v.uyarilar.length > 0 && <div className="tr-uyarilar">{v.uyarilar.map((u) => <div key={u}>⚠️ {u}</div>)}</div>}
      <TercihTablosu v={v} />
      <div className="tr-karar">
        <textarea className="auth-input" rows={3} maxLength={1500} value={notu} onChange={(e) => setNotu(e.target.value)} placeholder="Öğrenciye notunuz (ör. 3. sıradaki programı 1. sıraya alabilirsin; sona 2 güvenli tercih ekle)" />
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn" disabled={bekle} onClick={() => karar('onayla')}>✓ Onayla</button>
          <button className="btn sec" disabled={bekle} onClick={() => karar('duzeltme')}>Düzeltme iste</button>
        </div>
        <div className="yp-ince">Öğrenciye bildirim ve e-posta gider.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
    </div>
  )
}

// ----------------------------------------------------------------------------- okul: tercih dönemi
export function TercihDonemi({ okulId }) {
  const [v, setV] = useState(null)
  const [secili, setSecili] = useState(null)
  const [filtre, setFiltre] = useState('')
  const [hata, setHata] = useState(null)
  const yukle = useCallback(() => api.okulTercihleri(okulId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [okulId])
  useEffect(() => { yukle() }, [yukle])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const liste = v.ogrenciler.filter((o) => !filtre || (filtre === 'yok' ? !o.durum : o.durum === filtre))
  return (
    <>
      <div className="yp-kpi-grid" style={{ marginBottom: 14 }}>
        <div className="yp-kpi"><div className="yp-kpi-e">12. sınıf + mezun</div><div className="yp-kpi-d">{v.ozet.toplam}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Liste hazırlayan</div><div className="yp-kpi-d">{v.ozet.liste_var}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">İnceleme bekleyen</div><div className="yp-kpi-d" style={{ color: v.ozet.incelemede ? 'var(--am)' : undefined }}>{v.ozet.incelemede}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Onaylanan</div><div className="yp-kpi-d" style={{ color: 'var(--gr)' }}>{v.ozet.onaylandi}</div></div>
      </div>
      <div className="eu-filtre">
        {[['', 'Tümü'], ['incelemede', 'İnceleme bekleyen'], ['duzeltme', 'Düzeltme istenen'], ['onaylandi', 'Onaylanan'], ['taslak', 'Hazırlanıyor'], ['yok', 'Liste yok']].map(([k, ad]) => (
          <button key={k} className={filtre === k ? 'secili' : ''} onClick={() => setFiltre(k)}>{ad}</button>
        ))}
      </div>
      <div className="card">
        {liste.length === 0 ? <div className="bos-durum">Bu filtrede öğrenci yok.</div> : (
          <table className="yp-tablo">
            <thead><tr><th>Öğrenci</th><th>Sınıf</th><th>Durum</th><th>Tercih</th><th>Güvenli / dengeli / riskli</th><th>Uyarı</th><th>Sonuç</th><th /></tr></thead>
            <tbody>
              {liste.map((o) => (
                <tr key={o.ogrenci_id}>
                  <td>{o.ad_soyad}</td><td>{o.sinif_metni}</td>
                  <td><b style={{ color: DURUM_RENK[o.durum] || 'var(--tx3)' }}>{o.durum_adi}</b></td>
                  <td>{o.sayilar.toplam || '—'}</td>
                  <td>{o.sayilar.toplam ? `${o.sayilar.guvenli} / ${o.sayilar.dengeli} / ${o.sayilar.riskli}` : '—'}</td>
                  <td>{o.uyari ? <span className="eu-cip orta">⚠️ {o.uyari}</span> : '—'}</td>
                  <td className="yp-ince">{o.yerlesme ? { yerlesti: 'Yerleşti', yerlesemedi: 'Yerleşemedi', tekrar: 'Tekrar', yurtdisi: 'Yurt dışı', calisiyor: 'Çalışıyor', diger: 'Diğer' }[o.yerlesme] : '—'}</td>
                  <td>{o.durum && <button className="yp-mini" onClick={() => setSecili(o)}>İncele →</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {secili && (
        <Pencere genis baslik={`${secili.ad_soyad} · tercih listesi`} altBaslik={secili.sinif_metni} onKapat={() => setSecili(null)}>
          <OgrenciTercih ogrenciId={secili.ogrenci_id} onKarar={() => { yukle(); setSecili(null) }} />
        </Pencere>
      )}
    </>
  )
}

// ----------------------------------------------------------------------------- okul: mezunlar
function MezunFormu({ v, mevcut, onKapat, onKaydet }) {
  const [f, setF] = useState(mevcut ? { ...mevcut, siralama: mevcut.siralama ?? '', burs: mevcut.burs || '', universite: mevcut.universite || '', bolum_ad: mevcut.bolum_ad || '' }
    : { ad_soyad: '', yil: new Date().getFullYear(), durum: 'yerlesti', universite: '', bolum_ad: '', bolum_id: null, burs: '', siralama: '' })
  const [hata, setHata] = useState(null)
  const s = (k) => (e) => setF({ ...f, [k]: e.target.value })
  async function kaydet() {
    setHata(null)
    const veri = { ad_soyad: f.ad_soyad, yil: Number(f.yil), durum: f.durum, universite: f.universite || null, bolum_ad: f.bolum_ad || null, bolum_id: f.bolum_id || null,
      burs: f.burs || null, siralama: f.siralama === '' ? null : Number(f.siralama) }
    try { if (mevcut) await api.mezunDuzenle(mevcut.id, veri); else await onKaydet(veri); onKapat(true) } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
  }
  return (
    <Pencere baslik={mevcut ? 'Mezun kaydını düzenle' : 'Mezun kaydı ekle'} onKapat={() => onKapat(false)}
      alt={<><button className="btn sec" onClick={() => onKapat(false)}>Vazgeç</button><button className="btn" disabled={f.ad_soyad.trim().length < 3} onClick={kaydet}>Kaydet</button></>}>
      <div className="pf-alanlar">
        <label className="genis"><span>Ad soyad</span><input className="auth-input" disabled={!!mevcut?.ogrenci_id} maxLength={120} value={f.ad_soyad} onChange={s('ad_soyad')} /></label>
        <label><span>Mezuniyet / yerleşme yılı</span><input className="auth-input" type="number" min="2000" max="2100" value={f.yil} onChange={s('yil')} /></label>
        <label><span>Durum</span><select className="auth-input" value={f.durum} onChange={s('durum')}>{Object.entries(v.secenekler.durumlar).map(([k, a]) => <option key={k} value={k}>{a}</option>)}</select></label>
        <label className="genis"><span>Üniversite</span><input className="auth-input" maxLength={140} value={f.universite} onChange={s('universite')} /></label>
        <label><span>Bölüm</span>
          <select className="auth-input" value={f.bolum_id || ''} onChange={(e) => { const id = Number(e.target.value) || null; const b = v.bolumler.find((x) => x.id === id); setF({ ...f, bolum_id: id, bolum_ad: b ? b.ad : f.bolum_ad }) }}>
            <option value="">— seç —</option>{v.bolumler.map((b) => <option key={b.id} value={b.id}>{b.ad}</option>)}
          </select>
        </label>
        <label><span>Burs</span><select className="auth-input" value={f.burs} onChange={s('burs')}><option value="">—</option>{v.secenekler.burslar.map((b) => <option key={b}>{b}</option>)}</select></label>
        <label><span>Başarı sırası</span><input className="auth-input" type="number" min="1" value={f.siralama} onChange={s('siralama')} /></label>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
    </Pencere>
  )
}

const yuzde = (a, b) => (b ? `%${Math.round((100 * a) / b)}` : '—')

export function Mezunlar({ okulId }) {
  const [v, setV] = useState(null)
  const [form, setForm] = useState(null)
  const [yil, setYil] = useState('')
  const [silOnay, setSilOnay] = useState(null)
  const [hata, setHata] = useState(null)
  const yukle = useCallback(() => api.mezunlar(okulId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [okulId])
  useEffect(() => { yukle() }, [yukle])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const kayit = v.kayitlar.filter((k) => !yil || k.yil === Number(yil))
  const son = v.yillar[0]
  return (
    <>
      <div className="rh-ust">
        <div className="yp-ince" style={{ maxWidth: 760, lineHeight: 1.6 }}>Öğrenciler Tercihlerim sayfasından sonuçlarını bildirir; diğer mezunları siz ekleyebilirsiniz. Filizyol'u kullanan mezunlarda yerleşilen bölüm, öğrencinin hedefi ve Filizyol önerileriyle karşılaştırılır.</div>
        <button className="btn" onClick={() => setForm({})}>+ Mezun ekle</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {son && (
        <div className="yp-kpi-grid" style={{ marginBottom: 14 }}>
          <div className="yp-kpi"><div className="yp-kpi-e">{son.yil} kaydı</div><div className="yp-kpi-d">{son.kayit}</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Yerleşen</div><div className="yp-kpi-d">{yuzde(son.yerlesti, son.kayit)}</div><div className="yp-kpi-a">{son.yerlesti} mezun</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Hedef bölümüne yerleşen</div><div className="yp-kpi-d">{yuzde(son.hedefle_ayni, son.hedef_bilinen)}</div><div className="yp-kpi-a">hedefi bilinen {son.hedef_bilinen} kişide</div></div>
          <div className="yp-kpi"><div className="yp-kpi-e">Önerilen ilk 10 bölüme yerleşen</div><div className="yp-kpi-d">{yuzde(son.ilk10, son.oneri_bilinen)}</div><div className="yp-kpi-a">Filizyol kullanan {son.oneri_bilinen} kişide</div></div>
        </div>
      )}
      {v.yillar.length > 1 && (
        <div className="card">
          <div className="ct">Yıllara göre</div>
          <table className="yp-tablo">
            <thead><tr><th>Yıl</th><th>Kayıt</th><th>Yerleşme</th><th>Hedefine yerleşen</th><th>Önerilen ilk 10'a yerleşen</th></tr></thead>
            <tbody>{v.yillar.map((y) => <tr key={y.yil}><td><b>{y.yil}</b></td><td>{y.kayit}</td><td>{yuzde(y.yerlesti, y.kayit)}</td><td>{yuzde(y.hedefle_ayni, y.hedef_bilinen)}</td><td>{yuzde(y.ilk10, y.oneri_bilinen)}</td></tr>)}</tbody>
          </table>
        </div>
      )}
      <div className="card">
        <div className="ct" style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
          <span>Mezun kayıtları</span>
          <select className="auth-input" style={{ width: 'auto', padding: '4px 8px' }} value={yil} onChange={(e) => setYil(e.target.value)}><option value="">Tüm yıllar</option>{v.yillar.map((y) => <option key={y.yil}>{y.yil}</option>)}</select>
        </div>
        {kayit.length === 0 ? <div className="bos-durum">Henüz mezun kaydı yok.</div> : (
          <table className="yp-tablo">
            <thead><tr><th>Yıl</th><th>Mezun</th><th>Durum</th><th>Üniversite / bölüm</th><th>Hedefi</th><th>Öneri sırası</th><th>Kaynak</th><th /></tr></thead>
            <tbody>
              {kayit.map((k) => (
                <tr key={k.id}>
                  <td>{k.yil}</td><td>{k.ad_soyad}</td><td>{k.durum_adi}</td>
                  <td>{[k.universite, k.bolum_ad].filter(Boolean).join(' — ') || '—'}{k.burs && <div className="yp-ince">{k.burs}</div>}</td>
                  <td>{k.hedef_bolum_ad ? <>{k.hedef_bolum_ad}{k.hedefle_ayni != null && <span className={k.hedefle_ayni ? 'arti' : 'yp-ince'}> {k.hedefle_ayni ? '✓ aynı' : '· farklı'}</span>}</> : '—'}</td>
                  <td>{k.oneri_sirasi ? `#${k.oneri_sirasi}` : '—'}</td>
                  <td className="yp-ince">{k.kaynak === 'ogrenci' ? 'Öğrenci bildirdi' : 'Okul ekledi'}</td>
                  <td className="tr-islem">
                    <button className="yp-mini" onClick={() => setForm({ mevcut: k })}>✎</button>
                    {silOnay === k.id ? <button className="yp-mini yp-tehlike" onClick={async () => { setSilOnay(null); try { await api.mezunSil(k.id); yukle() } catch (e) { setHata(e.detail || 'Silinemedi.') } }}>Sil</button>
                      : <button className="yp-mini" onClick={() => setSilOnay(k.id)}>🗑</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {form && <MezunFormu v={v} mevcut={form.mevcut} onKaydet={(x) => api.mezunEkle(okulId, x)} onKapat={(degisti) => { setForm(null); if (degisti) yukle() }} />}
    </>
  )
}
