// [2026-10-10] Rehberlik: erken uyarı listesi + görüşme kayıtları (randevu, not, takip).
// RehberlikSekmesi → okul panelindeki "Rehberlik" bölümü; OgrenciRehberlik → öğrenci detay penceresindeki sekme.
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { Pencere } from './ortak'
import OgrenciDetayPenceresi from './OgrenciDetayPenceresi'

const SEVIYE = {
  yuksek: { ad: 'Yüksek', ikon: '▲', sinif: 'yuksek' },
  orta: { ad: 'Orta', ikon: '●', sinif: 'orta' },
  dusuk: { ad: 'Düşük', ikon: '▽', sinif: 'dusuk' },
}
const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const kisaTarih = (t) => { if (!t) return '—'; const d = new Date(t.length <= 10 ? `${t}T12:00` : t); return `${d.getDate()} ${AY[d.getMonth()]}` }
const bugunISO = () => new Date().toISOString().slice(0, 10)
// datetime-local için yerel "YYYY-MM-DDTHH:mm"
const yerelZaman = (d = new Date()) => { const p = (n) => String(n).padStart(2, '0'); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}` }

export function UyariCipleri({ uyarilar }) {
  return (
    <div className="eu-cipler">
      {uyarilar.map((u) => (
        <span key={u.kural} className={`eu-cip ${u.seviye}`} title={u.metin}><span aria-hidden="true">{SEVIYE[u.seviye].ikon}</span> {u.ad}</span>
      ))}
    </div>
  )
}

// ----------------------------------------------------------------------------- görüşme formu
export function GorusmeFormu({ ogrenci, ogrenciler, mevcut, varsayilan = {}, secenekler, onKapat, onKaydet }) {
  const [f, setF] = useState(() => mevcut ? {
    ...mevcut, zaman: mevcut.zaman.slice(0, 16), takip_tarihi: mevcut.takip_tarihi || '', baslik: mevcut.baslik || '', notlar: mevcut.notlar || '',
  } : {
    zaman: yerelZaman(), durum: 'yapildi', tur: 'bireysel', konu: 'akademik', baslik: '', notlar: '', takip_tarihi: '', takip_tamam: false, ogrenciye_goster: true, ...varsayilan,
  })
  const [secili, setSecili] = useState(ogrenci || null)
  const [ara, setAra] = useState('')
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const s = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const adaylar = useMemo(() => {
    if (!ogrenciler || secili) return []
    const q = ara.trim().toLocaleLowerCase('tr')
    return q.length < 2 ? [] : ogrenciler.filter((o) => `${o.ad_soyad} ${o.sinif_metni || ''} ${o.ogrenci_no || ''}`.toLocaleLowerCase('tr').includes(q)).slice(0, 8)
  }, [ara, ogrenciler, secili])

  async function kaydet(e) {
    e.preventDefault()
    if (!secili) { setHata('Öğrenci seçin.'); return }
    setBekle(true); setHata(null)
    const veri = { ...f, takip_tarihi: f.takip_tarihi || null, baslik: f.baslik || null, notlar: f.notlar || null }
    try {
      if (mevcut) await api.gorusmeDuzenle(mevcut.id, veri)
      else await api.gorusmeEkle(secili.id, veri)
      onKaydet?.()
    } catch (er) { setHata(er.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  const planli = f.durum === 'planlandi'
  return (
    <Pencere baslik={mevcut ? 'Görüşmeyi düzenle' : planli ? 'Görüşme planla' : 'Görüşme kaydı'} altBaslik={secili ? `${secili.ad_soyad}${secili.sinif_metni ? ` · ${secili.sinif_metni}` : ''}` : null} onKapat={onKapat}
      alt={<>
        <button className="btn sec" type="button" onClick={onKapat}>Vazgeç</button>
        <button className="btn" form="gorusme-formu" disabled={bekle}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
      </>}>
      <form id="gorusme-formu" className="gf-form" onSubmit={kaydet}>
        {!secili && (
          <label className="gf-tam">
            <span>Öğrenci</span>
            <input className="auth-input" autoFocus placeholder="Ad, sınıf ya da öğrenci no ile ara…" value={ara} onChange={(e) => setAra(e.target.value)} />
            {adaylar.length > 0 && (
              <div className="gf-adaylar">
                {adaylar.map((o) => <button type="button" key={o.id} onClick={() => setSecili(o)}><b>{o.ad_soyad}</b> <span className="yp-ince">{o.sinif_metni}</span></button>)}
              </div>
            )}
          </label>
        )}
        <div className="gf-durum gf-tam" role="radiogroup" aria-label="Durum">
          {Object.entries(secenekler.durumlar).filter(([k]) => mevcut || k !== 'iptal').map(([k, ad]) => (
            <label key={k} className={f.durum === k ? 'secili' : ''}><input type="radio" name="durum" checked={f.durum === k} onChange={() => setF({ ...f, durum: k })} />{k === 'yapildi' ? '✓ ' : k === 'planlandi' ? '🗓 ' : '✕ '}{ad}</label>
          ))}
        </div>
        <label><span>{planli ? 'Randevu zamanı' : 'Görüşme zamanı'}</span><input className="auth-input" type="datetime-local" required value={f.zaman} onChange={s('zaman')} /></label>
        <label><span>Görüşme türü</span>
          <select className="auth-input" value={f.tur} onChange={s('tur')}>{Object.entries(secenekler.turler).map(([k, ad]) => <option key={k} value={k}>{ad}</option>)}</select>
        </label>
        <label><span>Konu</span>
          <select className="auth-input" value={f.konu} onChange={s('konu')}>{Object.entries(secenekler.konular).map(([k, ad]) => <option key={k} value={k}>{ad}</option>)}</select>
        </label>
        <label><span>Başlık <small>(isteğe bağlı)</small></span><input className="auth-input" maxLength={120} value={f.baslik} onChange={s('baslik')} placeholder="ör. Deneme sonuçları" /></label>
        {!planli && (
          <label className="gf-tam"><span>Notlar <small>— yalnızca okul yetkilileri görür; öğrenci görmez</small></span>
            <textarea className="auth-input" rows={5} maxLength={5000} value={f.notlar} onChange={s('notlar')} placeholder="Konuşulanlar, gözlemler, alınan kararlar…" />
          </label>
        )}
        {!planli && (
          <label><span>Takip tarihi <small>(isteğe bağlı)</small></span><input className="auth-input" type="date" min={mevcut ? undefined : bugunISO()} value={f.takip_tarihi} onChange={s('takip_tarihi')} /></label>
        )}
        {!planli && f.takip_tarihi && mevcut && (
          <label className="gf-onay"><input type="checkbox" checked={f.takip_tamam} onChange={s('takip_tamam')} /> Takip yapıldı</label>
        )}
        {planli && (
          <label className="gf-onay gf-tam"><input type="checkbox" checked={f.ogrenciye_goster} onChange={s('ogrenciye_goster')} /> Öğrencinin takviminde “Rehberlik görüşmesi” olarak görünsün (not ve konu gösterilmez)</label>
        )}
        {hata && <div className="auth-error gf-tam" style={{ margin: 0 }}>{hata}</div>}
      </form>
    </Pencere>
  )
}

// ----------------------------------------------------------------------------- görüşme satırı
function GorusmeSatiri({ g, ogrenciGoster = true, onDuzenle, onYenile, setHata }) {
  const [acik, setAcik] = useState(false)
  const [silOnay, setSilOnay] = useState(false)
  async function islem(f) { setHata?.(null); try { await f(); onYenile() } catch (e) { setHata?.(e.detail || 'İşlem yapılamadı.') } }
  const veri = (ek) => ({ zaman: g.zaman.slice(0, 16), durum: g.durum, tur: g.tur, konu: g.konu, baslik: g.baslik, notlar: g.notlar, takip_tarihi: g.takip_tarihi, takip_tamam: g.takip_tamam, ogrenciye_goster: g.ogrenciye_goster, ...ek })
  const gecikti = g.takip_tarihi && !g.takip_tamam && g.takip_tarihi < bugunISO()
  return (
    <div className={`gs-satir ${g.durum}`}>
      <div className="gs-tarih"><b>{new Date(g.zaman).getDate()}</b><span>{AY[new Date(g.zaman).getMonth()]}</span><small>{g.saat}</small></div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="gs-ust">
          {ogrenciGoster && <b>{g.ad_soyad}</b>}
          {ogrenciGoster && g.sinif_metni && <span className="yp-ince">{g.sinif_metni}</span>}
          <span className="gs-etiket">{g.tur_adi}</span>
          <span className="gs-etiket konu">{g.konu_adi}</span>
          {g.durum !== 'yapildi' && <span className={`gs-etiket durum-${g.durum}`}>{g.durum_adi}</span>}
        </div>
        {g.baslik && <div className="gs-baslik">{g.baslik}</div>}
        {g.notlar && (
          <div className={`gs-not${acik ? ' acik' : ''}`} onClick={() => setAcik(!acik)} title={acik ? '' : 'Tamamını göster'}>{g.notlar}</div>
        )}
        <div className="gs-alt">
          {g.takip_tarihi && <span className={`gs-takip${g.takip_tamam ? ' tamam' : gecikti ? ' gecikti' : ''}`}>{g.takip_tamam ? '✓ Takip yapıldı' : `↻ Takip: ${kisaTarih(g.takip_tarihi)}${gecikti ? ' (gecikti)' : ''}`}</span>}
          {g.olusturan && <span className="yp-ince">{g.olusturan}</span>}
        </div>
      </div>
      <div className="gs-islem">
        {g.durum === 'planlandi' && <button className="yp-mini" onClick={() => onDuzenle(g, { durum: 'yapildi' })}>✓ Yapıldı</button>}
        {g.takip_tarihi && !g.takip_tamam && g.durum === 'yapildi' && <button className="yp-mini" onClick={() => islem(() => api.gorusmeDuzenle(g.id, veri({ takip_tamam: true })))}>Takibi kapat</button>}
        <button className="yp-mini" onClick={() => onDuzenle(g)}>✎</button>
        {silOnay
          ? <><button className="yp-mini yp-tehlike" onClick={() => islem(() => api.gorusmeSil(g.id))}>Sil</button><button className="yp-mini" onClick={() => setSilOnay(false)}>×</button></>
          : <button className="yp-mini" title="Sil" onClick={() => setSilOnay(true)}>🗑</button>}
      </div>
    </div>
  )
}

// ----------------------------------------------------------------------------- erken uyarı
function ErkenUyari({ okulId, veri, yenile, ogrenciler, formAc, detayAc }) {
  const [kural, setKural] = useState('')
  const [seviye, setSeviye] = useState('')
  const [hata, setHata] = useState(null)
  if (!veri) return <div className="bos-durum">Yükleniyor…</div>
  const liste = veri.ogrenciler.filter((s) => (!kural || s.uyarilar.some((u) => u.kural === kural)) && (!seviye || s.seviye === seviye))
  async function ertele(s) {
    setHata(null)
    try { for (const u of s.uyarilar) await api.riskErtele(s.ogrenci_id, u.kural, 14); yenile() } catch (e) { setHata(e.detail || 'Ertelenemedi.') }
  }
  const ogr = (s) => ogrenciler.find((o) => o.id === s.ogrenci_id) || { id: s.ogrenci_id, ad_soyad: s.ad_soyad, sinif_metni: s.sinif_metni }
  return (
    <>
      <div className="yp-kpi-grid" style={{ marginBottom: 14 }}>
        <div className="yp-kpi"><div className="yp-kpi-e">Dikkat gerektiren</div><div className="yp-kpi-d">{veri.ozet.toplam}</div></div>
        <button className={`yp-kpi eu-kpi yuksek${seviye === 'yuksek' ? ' secili' : ''}`} onClick={() => setSeviye(seviye === 'yuksek' ? '' : 'yuksek')}><div className="yp-kpi-e">▲ Yüksek</div><div className="yp-kpi-d">{veri.ozet.yuksek}</div>{veri.ozet.gorusulmemis_yuksek > 0 && <div className="yp-kpi-a">{veri.ozet.gorusulmemis_yuksek} kişiyle henüz görüşülmedi</div>}</button>
        <button className={`yp-kpi eu-kpi orta${seviye === 'orta' ? ' secili' : ''}`} onClick={() => setSeviye(seviye === 'orta' ? '' : 'orta')}><div className="yp-kpi-e">● Orta</div><div className="yp-kpi-d">{veri.ozet.orta}</div></button>
        <button className={`yp-kpi eu-kpi dusuk${seviye === 'dusuk' ? ' secili' : ''}`} onClick={() => setSeviye(seviye === 'dusuk' ? '' : 'dusuk')}><div className="yp-kpi-e">▽ Düşük</div><div className="yp-kpi-d">{veri.ozet.dusuk}</div></button>
      </div>
      <div className="eu-filtre">
        <button className={!kural ? 'secili' : ''} onClick={() => setKural('')}>Tümü</button>
        {veri.kurallar.filter((k) => k.sayi > 0).map((k) => <button key={k.kod} className={kural === k.kod ? 'secili' : ''} onClick={() => setKural(kural === k.kod ? '' : k.kod)}>{k.ad} <b>{k.sayi}</b></button>)}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {liste.length === 0 ? (
        <div className="card bos-durum">{veri.ozet.toplam === 0 ? '🎉 Şu an dikkat gerektiren öğrenci yok.' : 'Bu filtrede öğrenci yok.'}</div>
      ) : (
        <div className="eu-liste">
          {liste.map((s) => (
            <div key={s.ogrenci_id} className={`eu-kart ${s.seviye}`}>
              <div className="eu-sol">
                <span className={`eu-seviye ${s.seviye}`}>{SEVIYE[s.seviye].ikon} {SEVIYE[s.seviye].ad}</span>
                <button className="ak-link" onClick={() => detayAc(s.ogrenci_id)}>{s.ad_soyad}</button>
                <span className="yp-ince">{s.sinif_metni || '—'}</span>
              </div>
              <div className="eu-orta">
                {s.uyarilar.map((u) => <div key={u.kural} className="eu-neden"><span className={`eu-nokta ${u.seviye}`} aria-hidden="true" /><b>{u.ad}:</b> {u.metin}</div>)}
                <div className="yp-ince" style={{ marginTop: 4 }}>
                  {s.yaklasan_gorusme ? `🗓 Randevu: ${kisaTarih(s.yaklasan_gorusme)} ${s.yaklasan_gorusme.slice(11, 16)}` : s.son_gorusme ? `Son görüşme: ${kisaTarih(s.son_gorusme)}` : 'Henüz görüşme kaydı yok'}
                </div>
              </div>
              <div className="eu-islem">
                <button className="yp-mini" onClick={() => formAc({ ogrenci: ogr(s), varsayilan: { durum: 'planlandi', zaman: yerelZaman(new Date(Date.now() + 86400000)) } })}>🗓 Planla</button>
                <button className="yp-mini" onClick={() => formAc({ ogrenci: ogr(s) })}>✎ Görüşme kaydet</button>
                <button className="yp-mini" title="Bu uyarıları 14 gün gösterme" onClick={() => ertele(s)}>14 gün gizle</button>
              </div>
            </div>
          ))}
        </div>
      )}
      <div className="yp-ince" style={{ marginTop: 12, lineHeight: 1.6 }}>
        Liste her açılışta yeniden hesaplanır. Kurallar: hiç giriş yapmama (7+ gün), uzun süre girmeme (14+ gün), yarım kalan test (7+ gün işlem yok), giriş yapıp teste başlamama (14+ gün),
        net düşüşü (son deneme önceki ortalamanın %15+ altında), görevleri bırakma (önceden yapıp son 3 haftada hiç yapmama), son sınıfta hedef seçmeme. “Gizle” yalnızca bu uyarıları 14 gün gizler; durum sürerse uyarı geri gelir.
      </div>
    </>
  )
}

// ----------------------------------------------------------------------------- görüşmeler
function Gorusmeler({ okulId, veri, yenile, formAc }) {
  const [konu, setKonu] = useState('')
  const [ara, setAra] = useState('')
  const [hata, setHata] = useState(null)
  const [indir, setIndir] = useState(false)
  if (!veri) return <div className="bos-durum">Yükleniyor…</div>
  const duzenle = (g, ek) => formAc({ mevcut: ek ? { ...g, ...ek } : g })
  const q = ara.trim().toLocaleLowerCase('tr')
  const gecmis = veri.gecmis.filter((g) => (!konu || g.konu === konu) && (!q || `${g.ad_soyad} ${g.baslik || ''} ${g.notlar || ''}`.toLocaleLowerCase('tr').includes(q)))
  async function excel() { setIndir(true); setHata(null); try { await api.gorusmeExcel(okulId) } catch (e) { setHata(e.detail || 'İndirilemedi.') } finally { setIndir(false) } }
  return (
    <>
      <div className="yp-kpi-grid" style={{ marginBottom: 14 }}>
        <div className="yp-kpi"><div className="yp-kpi-e">Bu ay görüşme</div><div className="yp-kpi-d">{veri.ozet.bu_ay}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Son 90 gün</div><div className="yp-kpi-d">{veri.ozet.donem}</div><div className="yp-kpi-a">{veri.ozet.ogrenci} öğrenci</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Yaklaşan randevu</div><div className="yp-kpi-d">{veri.yaklasan.length}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Bekleyen takip</div><div className="yp-kpi-d" style={veri.ozet.geciken_takip ? { color: 'var(--re)' } : undefined}>{veri.takipler.length}</div>{veri.ozet.geciken_takip > 0 && <div className="yp-kpi-a">{veri.ozet.geciken_takip} gecikti</div>}</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="yp-iki" style={{ marginBottom: 14 }}>
        <div className="card" style={{ margin: 0 }}>
          <div className="ct">🗓 Yaklaşan randevular</div>
          {veri.yaklasan.length === 0 ? <div className="yp-ince">Planlanmış görüşme yok.</div>
            : veri.yaklasan.map((g) => <GorusmeSatiri key={g.id} g={g} onDuzenle={duzenle} onYenile={yenile} setHata={setHata} />)}
        </div>
        <div className="card" style={{ margin: 0 }}>
          <div className="ct">↻ Bekleyen takipler</div>
          {veri.takipler.length === 0 ? <div className="yp-ince">Bekleyen takip yok.</div>
            : veri.takipler.map((g) => <GorusmeSatiri key={g.id} g={g} onDuzenle={duzenle} onYenile={yenile} setHata={setHata} />)}
        </div>
      </div>
      <div className="card">
        <div className="ct" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span>Görüşme kayıtları · son 90 gün</span>
          <button className="rd-dugme" disabled={indir} onClick={excel}>📊 {indir ? 'Hazırlanıyor…' : 'Excel (son 1 yıl)'}</button>
        </div>
        <div className="eu-filtre" style={{ marginBottom: 10 }}>
          <input className="auth-input" style={{ maxWidth: 240, padding: '6px 10px' }} placeholder="Öğrenci, başlık ya da notta ara…" value={ara} onChange={(e) => setAra(e.target.value)} />
          <button className={!konu ? 'secili' : ''} onClick={() => setKonu('')}>Tüm konular</button>
          {veri.ozet.konular.map((k) => <button key={k.kod} className={konu === k.kod ? 'secili' : ''} onClick={() => setKonu(konu === k.kod ? '' : k.kod)}>{k.ad} <b>{k.sayi}</b></button>)}
        </div>
        {gecmis.length === 0 ? <div className="bos-durum">{veri.gecmis.length ? 'Bu filtrede kayıt yok.' : 'Henüz görüşme kaydı yok. “+ Yeni görüşme” ile ekleyebilir ya da Erken uyarı listesinden başlayabilirsiniz.'}</div>
          : gecmis.map((g) => <GorusmeSatiri key={g.id} g={g} onDuzenle={duzenle} onYenile={yenile} setHata={setHata} />)}
      </div>
    </>
  )
}

// ----------------------------------------------------------------------------- okul paneli bölümü
export default function RehberlikSekmesi({ okulId, ogrenciler = [], superAdmin, okullar, yenileOkul }) {
  const [alt, setAlt] = useState('uyari')
  const [uyari, setUyari] = useState(null)
  const [gorusme, setGorusme] = useState(null)
  const [form, setForm] = useState(null)
  const [detay, setDetay] = useState(null)
  const [hata, setHata] = useState(null)
  const yenile = useCallback(() => {
    api.erkenUyari(okulId).then(setUyari).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
    api.okulGorusmeleri(okulId).then(setGorusme).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  }, [okulId])
  useEffect(() => { yenile() }, [yenile])
  return (
    <>
      <div className="rh-ust">
        <div className="koc-sekmeler" role="tablist" style={{ marginBottom: 0 }}>
          <button role="tab" aria-selected={alt === 'uyari'} className={alt === 'uyari' ? 'aktif' : ''} onClick={() => setAlt('uyari')}>⚠️ Erken uyarı{uyari?.ozet.toplam ? <span className="koc-cip-sayi">{uyari.ozet.toplam}</span> : null}</button>
          <button role="tab" aria-selected={alt === 'gorusme'} className={alt === 'gorusme' ? 'aktif' : ''} onClick={() => setAlt('gorusme')}>🗂 Görüşmeler{gorusme?.yaklasan.length ? <span className="koc-cip-sayi">{gorusme.yaklasan.length} randevu</span> : null}</button>
        </div>
        {gorusme && <button className="btn" onClick={() => setForm({})}>+ Yeni görüşme</button>}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {alt === 'uyari' && <ErkenUyari okulId={okulId} veri={uyari} yenile={yenile} ogrenciler={ogrenciler} formAc={setForm} detayAc={setDetay} />}
      {alt === 'gorusme' && <Gorusmeler okulId={okulId} veri={gorusme} yenile={yenile} formAc={setForm} />}
      {form && gorusme && (
        <GorusmeFormu {...form} ogrenciler={ogrenciler} secenekler={gorusme.secenekler} onKapat={() => setForm(null)}
          onKaydet={() => { setForm(null); yenile() }} />
      )}
      {detay && <OgrenciDetayPenceresi ogrenciId={detay} superAdmin={superAdmin} okullar={okullar} baslangicSekme="rehberlik"
        onKapat={() => { setDetay(null); yenile() }} onDegisti={yenileOkul} />}
    </>
  )
}

// ----------------------------------------------------------------------------- öğrenci detay sekmesi
export function OgrenciRehberlik({ ogrenciId, ogrenci }) {
  const [v, setV] = useState(null)
  const [form, setForm] = useState(null)
  const [hata, setHata] = useState(null)
  const yenile = useCallback(() => api.ogrenciGorusmeleri(ogrenciId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [ogrenciId])
  useEffect(() => { yenile() }, [yenile])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const kim = { id: ogrenciId, ad_soyad: ogrenci?.ad_soyad, sinif_metni: ogrenci?.sinif_metni }
  return (
    <div>
      {v.uyarilar.length > 0 && (
        <div className="eu-kutu">
          <div className="yp-ince" style={{ fontWeight: 700, marginBottom: 6 }}>⚠️ ŞU AN DİKKAT GEREKTİREN</div>
          {v.uyarilar.map((u) => <div key={u.kural} className="eu-neden"><span className={`eu-nokta ${u.seviye}`} aria-hidden="true" /><b>{u.ad}:</b> {u.metin}</div>)}
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, margin: '12px 0' }}>
        <button className="btn" onClick={() => setForm({ ogrenci: kim })}>+ Görüşme kaydet</button>
        <button className="btn sec" onClick={() => setForm({ ogrenci: kim, varsayilan: { durum: 'planlandi', zaman: yerelZaman(new Date(Date.now() + 86400000)) } })}>🗓 Görüşme planla</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {v.gorusmeler.length === 0 ? <div className="bos-durum">Bu öğrenciyle henüz görüşme kaydı yok.</div>
        : v.gorusmeler.map((g) => <GorusmeSatiri key={g.id} g={g} ogrenciGoster={false} onDuzenle={(x, ek) => setForm({ mevcut: ek ? { ...x, ...ek } : x, ogrenci: kim })} onYenile={yenile} setHata={setHata} />)}
      {form && <GorusmeFormu {...form} secenekler={v.secenekler} onKapat={() => setForm(null)} onKaydet={() => { setForm(null); yenile() }} />}
    </div>
  )
}
