// [2026-10-10] Test Hesapları (yalnızca süper admin)
// Deneme / tanıtım için öğrenci ve okul yetkilisi hesapları: 2 adımlı doğrulama istemez, süreli giriş bağlantısıyla açılır.
// Öğrenci ilerlemesi senaryoyla kurulur — sistem soruları gerçek akışla cevaplar, sonuçlar gerçek hesaplamayla oluşur.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { Pencere, onceSure, tarih } from '../../components/yonetim/ortak'

const SURELER = [[1, '1 saat'], [24, '1 gün'], [168, '1 hafta'], [720, '30 gün']]
const BOS_SENARYO = {
  asama: 'tamamlandi', yarim: false, egilim: 'rastgele', egilim_bolum_id: '', gun_once: 3, yeni_tur_hazir: false,
  onceki_tur: false, hedef: 'otomatik', hedef_bolum_id: '', tamamlanan_adim: 3, listem_otomatik: true,
}

function BolumSec({ bolumler, deger, onChange, yerTutucu = 'Bölüm seçin…' }) {
  const [q, setQ] = useState('')
  const liste = useMemo(() => {
    const k = q.trim().toLocaleLowerCase('tr')
    return (bolumler || []).filter((b) => !k || b.ad.toLocaleLowerCase('tr').includes(k)).slice(0, 200)
  }, [bolumler, q])
  return (
    <div style={{ display: 'flex', gap: 6, flex: 1, minWidth: 220 }}>
      <input className="auth-input" style={{ margin: 0, width: 110 }} placeholder="süz…" value={q} onChange={(e) => setQ(e.target.value)} />
      <select className="yp-sec" style={{ flex: 1, minWidth: 0 }} value={deger} onChange={(e) => onChange(e.target.value)}>
        <option value="">{yerTutucu}</option>
        {liste.map((b) => <option key={b.id} value={b.id}>{b.ad}</option>)}
      </select>
    </div>
  )
}

function SenaryoPenceresi({ ogrenci, bolumler, onKapat, onTamam }) {
  const [f, setF] = useState(BOS_SENARYO)
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const [sonuc, setSonuc] = useState(null)
  const d = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const tamam = f.asama === 'tamamlandi'
  const dortBitti = f.asama === 'tamamlandi' || f.asama === 'k5_bekliyor'

  async function uygula() {
    setBekle(true); setHata(null); setSonuc(null)
    try {
      const ayar = {
        asama: f.asama, yarim: !dortBitti && f.yarim, egilim: f.egilim,
        egilim_bolum_id: f.egilim === 'bolum' ? Number(f.egilim_bolum_id) || null : null,
        gun_once: Number(f.gun_once) || 0, yeni_tur_hazir: dortBitti && f.yeni_tur_hazir, onceki_tur: dortBitti && f.onceki_tur,
        hedef: !tamam ? 'yok' : f.hedef === 'bolum' ? String(f.hedef_bolum_id || '') || 'yok' : f.hedef,
        tamamlanan_adim: tamam && f.hedef !== 'yok' ? Number(f.tamamlanan_adim) || 0 : 0,
        listem_otomatik: tamam && f.listem_otomatik,
      }
      const s = await api.testSenaryo(ogrenci.id, ayar)
      setSonuc(s); onTamam?.()
    } catch (e) { setHata(e.detail || 'Senaryo uygulanamadı.') } finally { setBekle(false) }
  }

  return (
    <Pencere baslik={`İlerlemeyi ayarla — ${ogrenci.ad_soyad}`} altBaslik="Mevcut ilerleme silinir; sistem soruları seçtiğin eğilime göre gerçek akışla cevaplar." onKapat={onKapat} genis
      alt={<>
        <button className="btn sec" onClick={onKapat} disabled={bekle}>Kapat</button>
        <button className="btn" onClick={uygula} disabled={bekle || (f.egilim === 'bolum' && !f.egilim_bolum_id) || (tamam && f.hedef === 'bolum' && !f.hedef_bolum_id)}>
          {bekle ? <><span className="spin" /> Uygulanıyor…</> : 'Uygula'}
        </button>
      </>}>
      <div className="th-form">
        <label>Aşama
          <select className="yp-sec" value={f.asama} onChange={d('asama')}>
            <option value="baslamadi">Hiç başlamadı</option>
            <option value="k1">K1 bitti</option>
            <option value="k2">K1–K2 bitti</option>
            <option value="k3">K1–K3 bitti</option>
            <option value="k5_bekliyor">K1–K4 bitti, alan soruları (K5) bekliyor</option>
            <option value="tamamlandi">Değerlendirme tamamlandı (sonuçlar hazır)</option>
          </select>
        </label>
        {!dortBitti && <label className="th-onay"><input type="checkbox" checked={f.yarim} onChange={d('yarim')} /> Sıradaki katman yarıda kalsın</label>}

        <label>Cevap eğilimi
          <select className="yp-sec" value={f.egilim} onChange={d('egilim')}>
            <option value="rastgele">Rastgele profil (her seferinde farklı)</option>
            <option value="dengeli">Dengeli / ortalama öğrenci</option>
            <option value="bolum">Belirli bir bölüme yatkın</option>
          </select>
        </label>
        {f.egilim === 'bolum' && (
          <label>Yatkın olduğu bölüm
            <BolumSec bolumler={bolumler} deger={f.egilim_bolum_id} onChange={(v) => setF({ ...f, egilim_bolum_id: v })} />
          </label>
        )}

        {f.asama !== 'baslamadi' && (
          <label>Son katmanı kaç gün önce bitirdi
            <input className="auth-input" type="number" min={0} max={400} value={f.gun_once} onChange={d('gun_once')} style={{ margin: 0, maxWidth: 120 }} />
          </label>
        )}
        {dortBitti && (
          <>
            <label className="th-onay"><input type="checkbox" checked={f.yeni_tur_hazir} onChange={d('yeni_tur_hazir')} /> Yeni değerlendirme zamanı gelmiş olsun (bekleme süresi dolmuş)</label>
            <label className="th-onay"><input type="checkbox" checked={f.onceki_tur} onChange={d('onceki_tur')} /> Önceki bir tur da olsun (Gelişim karşılaştırması görünsün)</label>
          </>
        )}

        {tamam && (
          <>
            <label>Hedef bölüm
              <select className="yp-sec" value={f.hedef} onChange={d('hedef')}>
                <option value="otomatik">1. sıradaki öneri</option>
                <option value="bolum">Belirli bir bölüm</option>
                <option value="yok">Hedef seçmemiş olsun</option>
              </select>
            </label>
            {f.hedef === 'bolum' && (
              <label>Hedef
                <BolumSec bolumler={bolumler} deger={f.hedef_bolum_id} onChange={(v) => setF({ ...f, hedef_bolum_id: v })} />
              </label>
            )}
            {f.hedef !== 'yok' && (
              <label>Yol haritasında tamamlanan adım
                <input className="auth-input" type="number" min={0} max={30} value={f.tamamlanan_adim} onChange={d('tamamlanan_adim')} style={{ margin: 0, maxWidth: 120 }} />
              </label>
            )}
            <label className="th-onay"><input type="checkbox" checked={f.listem_otomatik} onChange={d('listem_otomatik')} /> Listem'e ilk 3 öneri (ve hedef) eklensin</label>
          </>
        )}
      </div>

      {hata && <div className="auth-error" style={{ marginTop: 12 }}>{hata}</div>}
      {sonuc && (
        <div className="th-sonuc">
          <b>✓ {sonuc.asama}</b> · {sonuc.ilerleme}
          {sonuc.ilk_bolumler?.length > 0 && (
            <ol>{sonuc.ilk_bolumler.map((b) => <li key={b.bolum_id}>{b.bolum_adi} <span className="yp-ince">%{Math.round(b.uyum)}</span></li>)}</ol>
          )}
          {sonuc.hedef && <div>🎯 Hedef: <b>{sonuc.hedef}</b>{sonuc.tamamlanan_adim ? ` · ${sonuc.tamamlanan_adim} adım tamam` : ''}</div>}
          <div className="yp-ince" style={{ marginTop: 4 }}>Aynı sonucu tekrar üretmek için tohum: {sonuc.tohum}</div>
        </div>
      )}
    </Pencere>
  )
}

function BaglantiHucresi({ tip, h, yenile }) {
  const [saat, setSaat] = useState(24)
  const [baglanti, setBaglanti] = useState(null)
  const [kopyalandi, setKopyalandi] = useState(false)
  const [bekle, setBekle] = useState(false)
  const tam = baglanti ? `${window.location.origin}${baglanti.yol}` : null

  const [hata, setHata] = useState(null)
  async function uret() {
    setBekle(true); setHata(null)
    try { setBaglanti(await api.testBaglantiUret(tip, h.id, saat)); yenile() }
    catch (e) { setHata(e.detail || 'Bağlantı üretilemedi.') } finally { setBekle(false) }
  }
  async function iptal() {
    setHata(null)
    try { await api.testBaglantiIptal(tip, h.id); setBaglanti(null); yenile() } catch (e) { setHata(e.detail || 'İptal edilemedi.') }
  }
  async function kopyala() {
    try { await navigator.clipboard.writeText(tam); setKopyalandi(true); setTimeout(() => setKopyalandi(false), 1800) } catch { /* izin yok */ }
  }

  if (tam) {
    return (
      <div className="th-baglanti">
        <input className="auth-input" readOnly value={tam} onFocus={(e) => e.target.select()} />
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <button className="yp-mini" onClick={kopyala}>{kopyalandi ? '✓ Kopyalandı' : 'Kopyala'}</button>
          <a className="yp-mini" href={tam} target="_blank" rel="noreferrer">Yeni sekmede aç ↗</a>
          <button className="yp-mini" onClick={iptal}>İptal et</button>
        </div>
        <div className="yp-ince">Geçerlilik: {tarih(baglanti.bitis)} · Bu bağlantıyı bilen herkes hesabı açabilir.</div>
      </div>
    )
  }
  return (
    <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
      <select className="yp-sec" value={saat} onChange={(e) => setSaat(Number(e.target.value))} style={{ width: 96 }}>
        {SURELER.map(([s, ad]) => <option key={s} value={s}>{ad}</option>)}
      </select>
      <button className="yp-mini" onClick={uret} disabled={bekle}>{h.baglanti_var ? 'Yeni bağlantı' : 'Bağlantı üret'}</button>
      {h.baglanti_var && <span className="yp-ince">aktif · {tarih(h.baglanti_bitis)}'e kadar <button className="hg-link" onClick={iptal}>iptal</button></span>}
      {hata && <span className="auth-error" style={{ margin: 0, padding: '4px 8px', fontSize: 12 }}>{hata}</span>}
    </div>
  )
}

export default function TestHesaplariSayfasi() {
  const [d, setD] = useState(null)
  const [hata, setHata] = useState(null)
  const [bolumler, setBolumler] = useState([])
  const [form, setForm] = useState({ tip: 'ogrenci', ad_soyad: '', okul_id: '', sinif: '11' })
  const [yeni, setYeni] = useState(null)          // {email, sifre, ad_soyad}
  const [senaryo, setSenaryo] = useState(null)    // öğrenci
  const [bekle, setBekle] = useState(false)

  const yenile = () => api.testHesaplari().then(setD).catch((e) => setHata(e.detail || 'Liste alınamadı.'))
  useEffect(() => {
    yenile()
    api.yonetimBolumler().then((l) => setBolumler(Array.isArray(l) ? l.map((b) => ({ id: b.id ?? b.bolum_id, ad: b.ad ?? b.bolum_adi })) : [])).catch(() => {})
  }, [])

  async function ac(e) {
    e.preventDefault()
    setBekle(true); setHata(null)
    try {
      const h = await api.testHesabiAc({ ...form, okul_id: form.okul_id ? Number(form.okul_id) : null })
      setYeni(h); setForm({ ...form, ad_soyad: '' }); yenile()
    } catch (err) { setHata(err.detail || 'Hesap açılamadı.') } finally { setBekle(false) }
  }
  async function sifre(tip, h) {
    setHata(null)
    try {
      const s = await api.testSifreYenile(tip, h.id)
      setYeni({ ...s, ad_soyad: h.ad_soyad })
    } catch (e) { setHata(e.detail || 'Şifre yenilenemedi.') }
  }
  async function sil(tip, h) {
    if (!window.confirm(`${h.ad_soyad} test hesabı ve tüm verisi silinsin mi?`)) return
    setHata(null)
    try { await api.testHesabiSil(tip, h.id); yenile() } catch (e) { setHata(e.detail || 'Test hesabı silinemedi.') }
  }

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">🧪 Test Hesapları</div>
        <div className="ps">Deneme ve tanıtım için öğrenci / rehber öğretmen hesapları. 2 adımlı doğrulama istenmez; süreli giriş bağlantısıyla tek tıkla açılır. Öğrencinin ilerlemesini istediğin aşamaya getirebilirsin.</div>
      </div>

      <form className="yp-kutu yp-form-satir" style={{ marginBottom: 14 }} onSubmit={ac}>
        <select className="yp-sec" value={form.tip} onChange={(e) => setForm({ ...form, tip: e.target.value })}>
          <option value="ogrenci">Öğrenci</option>
          <option value="okul_yetkilisi">Rehber öğretmen</option>
        </select>
        <input className="auth-input" placeholder="Ad Soyad (örn. Deneme Öğrenci)" value={form.ad_soyad} onChange={(e) => setForm({ ...form, ad_soyad: e.target.value })} required minLength={3} />
        <select className="yp-sec" value={form.okul_id} onChange={(e) => setForm({ ...form, okul_id: e.target.value })} required={form.tip === 'okul_yetkilisi'}>
          <option value="">{form.tip === 'ogrenci' ? 'Okul harici' : 'Okul seçin…'}</option>
          {(d?.okullar || []).map((o) => <option key={o.id} value={o.id}>{o.ad}</option>)}
        </select>
        {form.tip === 'ogrenci' && (
          <select className="yp-sec" value={form.sinif} onChange={(e) => setForm({ ...form, sinif: e.target.value })}>
            {['9', '10', '11', '12', 'Mezun'].map((s) => <option key={s} value={s}>{s}{s !== 'Mezun' ? '. Sınıf' : ''}</option>)}
          </select>
        )}
        <button className="btn" type="submit" disabled={bekle}>+ Test hesabı aç</button>
      </form>
      {form.tip === 'okul_yetkilisi' && (
        <div className="yp-uyari">Rehber öğretmen test hesabı, seçtiğin okulun <b>gerçek öğrencilerini</b> de görür. Tanıtım için ayrı bir “Demo Okulu” açıp test öğrencilerini oraya koyman önerilir.</div>
      )}
      {yeni && (
        <div className="yp-uyari" style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span><b>{yeni.ad_soyad}</b> — şifreyle giriş (2 adımsız):</span>
          <code className="yp-sifre">{yeni.email}</code><code className="yp-sifre">{yeni.sifre}</code>
          <span className="yp-ince">Şifre yalnızca şimdi gösteriliyor.</span>
          <button className="yp-mini" onClick={() => setYeni(null)}>Tamam</button>
        </div>
      )}
      {hata && <div className="auth-error" role="alert">{hata}</div>}
      {!d ? <div className="bos-durum">Yükleniyor…</div> : (
        <>
          <div className="ct" style={{ marginTop: 18 }}>Öğrenci test hesapları ({d.ogrenciler.length})</div>
          {d.ogrenciler.length === 0 ? <div className="bos-durum">Henüz yok. Yukarıdan bir öğrenci test hesabı aç.</div> : (
            <div className="yp-kutu" style={{ padding: 0, overflowX: 'auto' }}>
              <table className="yp-tablo">
                <thead><tr><th>Hesap</th><th>Okul</th><th>İlerleme</th><th>Son giriş</th><th style={{ minWidth: 300 }}>Giriş bağlantısı</th><th /></tr></thead>
                <tbody>
                  {d.ogrenciler.map((o) => (
                    <tr key={o.id}>
                      <td><b>{o.ad_soyad}</b><div className="yp-ince">{o.email}</div></td>
                      <td className="yp-ince">{o.okul_ad}{o.sinif ? ` · ${o.sinif}` : ''}</td>
                      <td><span className="th-ilerleme">{o.ilerleme}</span><div><button className="hg-link" onClick={() => setSenaryo(o)}>İlerlemeyi ayarla →</button></div></td>
                      <td className="yp-ince">{onceSure(o.son_giris_zamani)}</td>
                      <td><BaglantiHucresi tip="ogrenci" h={o} yenile={yenile} /></td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <button className="yp-mini" onClick={() => sifre('ogrenci', o)}>Şifre</button>{' '}
                        <button className="yp-mini" onClick={() => sil('ogrenci', o)}>Sil</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="ct" style={{ marginTop: 22 }}>Rehber öğretmen test hesapları ({d.yetkililer.length})</div>
          {d.yetkililer.length === 0 ? <div className="bos-durum">Henüz yok.</div> : (
            <div className="yp-kutu" style={{ padding: 0, overflowX: 'auto' }}>
              <table className="yp-tablo">
                <thead><tr><th>Hesap</th><th>Okul</th><th>Son giriş</th><th style={{ minWidth: 300 }}>Giriş bağlantısı</th><th /></tr></thead>
                <tbody>
                  {d.yetkililer.map((y) => (
                    <tr key={y.id}>
                      <td><b>{y.ad_soyad}</b><div className="yp-ince">{y.email}</div></td>
                      <td className="yp-ince">{y.okul_ad}</td>
                      <td className="yp-ince">{onceSure(y.son_giris_zamani)}</td>
                      <td><BaglantiHucresi tip="okul_yetkilisi" h={y} yenile={yenile} /></td>
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <button className="yp-mini" onClick={() => sifre('okul_yetkilisi', y)}>Şifre</button>{' '}
                        <button className="yp-mini" onClick={() => sil('okul_yetkilisi', y)}>Sil</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="yp-ince" style={{ marginTop: 14, lineHeight: 1.6 }}>
            💡 Rehber öğretmen bağlantısını kendi tarayıcında açarsan süper admin oturumun kapanır — <b>gizli pencerede</b> açman önerilir.
            Öğrenci bağlantısı yönetim oturumunu etkilemez. Bağlantı üretmek, iptal etmek ve senaryo uygulamak Audit Log'a yazılır.
          </div>
        </>
      )}
      {senaryo && <SenaryoPenceresi ogrenci={senaryo} bolumler={bolumler} onKapat={() => setSenaryo(null)} onTamam={yenile} />}
    </div>
  )
}
