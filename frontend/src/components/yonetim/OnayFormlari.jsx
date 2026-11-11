// [2026-11-05] Onay formları — KVKK onayı ve 18 yaş altı veli onay formu tamamlanma durumu.
// Kural (backend app/core/veli_onayi.py): imzalı veli onay formu okula ulaşıp burada işaretlenene kadar öğrenci değerlendirmeye
// ve yapay zekâ destekli bölümlere başlayamaz. 18 yaşını doldurmuş öğrenci kimlikten doğrulanıp "reşit" işaretlenir.
// Okul yetkilisi kendi okulunu, süper admin her okulu ve okul harici (okulId = 0) öğrencileri görür.
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { KpiKarti } from '../istatistik/KpiKarti'
import { Pencere, tarih } from './ortak'
import Secim from '../Secim'   // [2026-11-11] uzun açılır listeler yazarak aranır

const bugunISO = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function VeliHucresi({ v, test }) {
  if (test) return <span className="yp-durum yp-d-gri">Test hesabı (muaf)</span>
  if (v?.islem === 'alindi') {
    return (
      <span>
        <span className="yp-durum yp-d-yesil">✓ Form alındı</span>
        <span className="yp-ince"> {tarih(v.form_tarihi, false)}{v.veli_ad_soyad ? ` · ${v.veli_ad_soyad}` : ''}{v.kamera ? ' · kamera onaylı' : ' · kamera yok'}</span>
      </span>
    )
  }
  if (v?.islem === 'resit') return <span className="yp-durum yp-d-mor">18 yaşını doldurmuş</span>
  return <span className="yp-durum yp-d-amber">Bekliyor{v?.islem === 'geri_alindi' ? ' (geri alındı)' : ''}</span>
}

function IsaretPenceresi({ okulId, secili, islem, onKapat, onBitti }) {
  const [formTarihi, setFormTarihi] = useState(bugunISO())
  const [veliAd, setVeliAd] = useState('')
  const [kamera, setKamera] = useState(false)
  const [teyit, setTeyit] = useState(false)
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const tek = secili.length === 1
  const alindi = islem === 'alindi'

  async function kaydet() {
    setBekle(true); setHata(null)
    try {
      const v = await api.veliOnayiIsaretle(okulId, {
        ogrenci_idler: secili.map((s) => s.id), islem,
        form_tarihi: alindi ? formTarihi : null, veli_ad_soyad: alindi && tek ? veliAd || null : null, kamera: alindi && kamera,
      })
      onBitti(v)
    } catch (e) {
      setHata(e.detail || 'Kaydedilemedi.')
    } finally {
      setBekle(false)
    }
  }

  return (
    <Pencere baslik={alindi ? 'Veli onay formu alındı' : '18 yaşını doldurmuş olarak işaretle'} onKapat={onKapat}
      altBaslik={tek ? secili[0].ad_soyad : `${secili.length} öğrenci`}
      alt={(
        <>
          <button className="btn sec" onClick={onKapat} disabled={bekle}>Vazgeç</button>
          <button className="btn" onClick={kaydet} disabled={bekle || !teyit || (alindi && !formTarihi)}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
        </>
      )}>
      {alindi ? (
        <>
          <label className="yp-ince" style={{ display: 'block', marginBottom: 10 }}>
            Formun imza tarihi
            <input type="date" className="yp-sec" style={{ display: 'block', marginTop: 4 }} value={formTarihi} max={bugunISO()} onChange={(e) => setFormTarihi(e.target.value)} />
          </label>
          {tek && (
            <label className="yp-ince" style={{ display: 'block', marginBottom: 10 }}>
              Velinin adı soyadı (isteğe bağlı)
              <input className="auth-input" style={{ display: 'block', marginTop: 4, width: '100%' }} maxLength={120} value={veliAd} onChange={(e) => setVeliAd(e.target.value)} />
            </label>
          )}
          <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 13, marginBottom: 10 }}>
            <input type="checkbox" checked={kamera} onChange={(e) => setKamera(e.target.checked)} />
            <span>Veli isteğe bağlı kamera maddesini <b>onayladı</b>{tek ? '' : ' (seçilen tüm formlarda)'}. İşaretlenmezse değerlendirme kamerasız yapılır.</span>
          </label>
          <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 13 }}>
            <input type="checkbox" checked={teyit} onChange={(e) => setTeyit(e.target.checked)} />
            <span>İmzalı formu teslim aldım; ilk üç zorunlu maddenin hepsi “Onaylıyorum” olarak işaretli. Formun aslını okulda saklayacağım.</span>
          </label>
        </>
      ) : (
        <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 13 }}>
          <input type="checkbox" checked={teyit} onChange={(e) => setTeyit(e.target.checked)} />
          <span>Öğrencinin 18 yaşını doldurduğunu resmî bir belgeden doğruladım. Bu öğrenci için veli onayı gerekmez.</span>
        </label>
      )}
      {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}
    </Pencere>
  )
}

export default function OnayFormlari({ okulId }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [filtre, setFiltre] = useState('eksik')
  const [sinif, setSinif] = useState('')
  const [ara, setAra] = useState('')
  const [secim, setSecim] = useState(new Set())
  const [pencere, setPencere] = useState(null)   // 'alindi' | 'resit'
  const [indiriliyor, setIndiriliyor] = useState(false)
  const [mesaj, setMesaj] = useState(null)

  const yukle = useCallback(() => { api.okulOnaylari(okulId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [okulId])
  useEffect(() => { yukle() }, [yukle])

  const liste = useMemo(() => {
    if (!v) return []
    const a = ara.trim().toLocaleLowerCase('tr')
    return v.ogrenciler.filter((o) => {
      const tamam = o.test_hesabi || (o.kvkk && o.veli.tamam)
      if (filtre === 'eksik' && tamam) return false
      if (filtre === 'tamam' && !tamam) return false
      if (sinif && (o.sinif || 'Sınıfı yok') !== sinif) return false
      return !a || o.ad_soyad.toLocaleLowerCase('tr').includes(a)
    })
  }, [v, filtre, sinif, ara])

  async function indir(secenek) {
    setIndiriliyor(true); setMesaj(null)
    try { await api.veliFormlariIndir(okulId, secenek) } catch (e) { setMesaj(e.detail || 'Form hazırlanamadı.') } finally { setIndiriliyor(false) }
  }
  async function geriAl(o) {
    const neden = window.prompt(`${o.ad_soyad} için veli onayı geri alınsın mı? Kısa bir neden yazın (ör. veli rızasını geri aldı):`)
    if (neden === null) return
    try { await api.veliOnayiGeriAl(o.id, neden || null); yukle() } catch (e) { setMesaj(e.detail || 'Geri alınamadı.') }
  }

  if (hata) return <div className="card"><div className="auth-error" style={{ margin: 0 }}>{hata}</div></div>
  if (!v) return <div className="bos-durum yukleniyor">Onaylar yükleniyor…</div>
  const oz = v.ozet
  const seciliOgr = v.ogrenciler.filter((o) => secim.has(o.id))
  const tumSecili = liste.length > 0 && liste.every((o) => o.test_hesabi || secim.has(o.id))

  return (
    <>
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
          <KpiKarti etiket="Tamamlanma" deger={oz.yuzde} birim="%" ikon="✍️" ton={oz.yuzde === 100 ? 'iyi' : 'okul'} alt={`${oz.tamam} / ${oz.ogrenci} öğrenci iki onayı da tamamladı`} />
          <KpiKarti etiket="KVKK onayı" deger={oz.kvkk} ikon="🔒" alt={`${oz.ogrenci - oz.kvkk} öğrenci henüz onaylamadı`} />
          <KpiKarti etiket="Veli formu alındı" deger={oz.veli_alindi} ikon="📄" alt={`${oz.resit} öğrenci 18 yaşını doldurmuş`} />
          <KpiKarti etiket="Veli formu bekleyen" deger={oz.veli_bekleyen} ikon="⏳" ton={oz.veli_bekleyen ? 'uyari' : undefined} alt="Bu öğrenciler değerlendirmeye başlayamaz" />
        </div>
        <div className="yp-ince" style={{ marginTop: 12, lineHeight: 1.5 }}>
          Öğrenci, burada işaretlenene kadar değerlendirmeye ve yapay zekâ destekli bölümlere başlayamaz: 18 yaşından küçükse imzalı veli onay formu okula ulaşınca "Veli formu alındı", 18 yaşını doldurmuşsa resmî belgeden doğrulandıktan sonra "18 yaşını doldurmuş" olarak işaretleyin.
          Formu öğrenci de kendi hesabından indirebilir. Test hesapları bu kuraldan muaftır ve sayılara katılmaz.
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
          <button className="btn" disabled={indiriliyor || !oz.veli_bekleyen} onClick={() => indir({ bekleyenler: true })}>
            {indiriliyor ? <span className="spin" /> : `📄 Bekleyenlerin formlarını indir (${oz.veli_bekleyen})`}
          </button>
        </div>
        {mesaj && <div className="auth-error" style={{ marginTop: 8 }}>{mesaj}</div>}
      </div>

      {v.siniflar.length > 1 && (
        <div className="card">
          <div className="ct">Sınıflara göre</div>
          <div className="tablo-kap">
            <table className="yp-tablo">
              <thead><tr><th>Sınıf</th><th>Öğrenci</th><th>KVKK onayı</th><th>Veli formu</th><th>18 yaş üstü</th><th>Bekleyen</th><th>Tamamlanma</th><th /></tr></thead>
              <tbody>
                {v.siniflar.map((s) => (
                  <tr key={s.sinif}>
                    <td><b>{s.sinif}</b></td><td>{s.ogrenci}</td><td>{s.kvkk}</td><td>{s.veli_alindi}</td><td>{s.resit}</td>
                    <td>{s.veli_bekleyen ? <b style={{ color: 'var(--am)' }}>{s.veli_bekleyen}</b> : 0}</td><td>%{s.yuzde}</td>
                    <td>{s.veli_bekleyen > 0 && <button className="hg-link" onClick={() => indir({ sinif: s.sinif, bekleyenler: true })}>Formları indir</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="card">
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
          <div className="ct" style={{ margin: 0, flex: 1 }}>Öğrenciler</div>
          <Secim className="yp-sec" value={filtre} onChange={(e) => setFiltre(e.target.value)} aria-label="Durum">
            <option value="eksik">Eksik olanlar</option><option value="tamam">Tamamlananlar</option><option value="hepsi">Tümü</option>
          </Secim>
          {v.siniflar.length > 1 && (
            <Secim className="yp-sec" value={sinif} onChange={(e) => setSinif(e.target.value)} aria-label="Sınıf">
              <option value="">Tüm sınıflar</option>{v.siniflar.map((s) => <option key={s.sinif} value={s.sinif}>{s.sinif}</option>)}
            </Secim>
          )}
          <input className="auth-input" style={{ width: 200 }} placeholder="Ad ile ara" value={ara} onChange={(e) => setAra(e.target.value)} />
        </div>
        {secim.size > 0 && (
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', padding: '8px 10px', background: 'var(--sur2)', borderRadius: 10, marginBottom: 10 }}>
            <b style={{ fontSize: 13 }}>{secim.size} öğrenci seçili</b>
            <button className="btn" onClick={() => setPencere('alindi')}>Veli formu alındı</button>
            <button className="btn sec" onClick={() => setPencere('resit')}>18 yaşını doldurmuş</button>
            <button className="btn sec" disabled={indiriliyor} onClick={() => indir({ idler: [...secim] })}>Formlarını indir</button>
            <button className="hg-link" onClick={() => setSecim(new Set())}>Seçimi kaldır</button>
          </div>
        )}
        {liste.length === 0 ? (
          <div className="bos-durum">{filtre === 'eksik' ? 'Eksik onayı olan öğrenci yok.' : 'Öğrenci yok.'}</div>
        ) : (
          <div className="tablo-kap">
            <table className="yp-tablo">
              <thead>
                <tr>
                  <th style={{ width: 32 }}><input type="checkbox" aria-label="Tümünü seç" checked={tumSecili}
                    onChange={(e) => setSecim(e.target.checked ? new Set(liste.filter((o) => !o.test_hesabi).map((o) => o.id)) : new Set())} /></th>
                  <th>Öğrenci</th><th>Sınıf</th><th>KVKK onayı</th><th>Veli onayı</th><th />
                </tr>
              </thead>
              <tbody>
                {liste.map((o) => (
                  <tr key={o.id}>
                    <td>{!o.test_hesabi && <input type="checkbox" aria-label={`${o.ad_soyad} seç`} checked={secim.has(o.id)}
                      onChange={(e) => { const s = new Set(secim); if (e.target.checked) s.add(o.id); else s.delete(o.id); setSecim(s) }} />}</td>
                    <td><b>{o.ad_soyad}</b></td>
                    <td>{[o.sinif, o.sube].filter(Boolean).join(' / ') || '—'}</td>
                    <td>{o.kvkk ? <span className="yp-durum yp-d-yesil">✓ {tarih(o.kvkk_zaman, false)}</span> : <span className="yp-durum yp-d-amber">Onaylamadı</span>}</td>
                    <td><VeliHucresi v={o.veli} test={o.test_hesabi} /></td>
                    <td>{['alindi', 'resit'].includes(o.veli?.islem) && !o.test_hesabi && <button className="hg-link" onClick={() => geriAl(o)}>Geri al</button>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="yp-ince" style={{ marginTop: 8 }}>KVKK onayını öğrenci ilk girişinde kendisi verir; okul bu onayı veremez. Her işaretleme Kayıtlar bölümüne yazılır.</div>
      </div>

      {pencere && (
        <IsaretPenceresi okulId={okulId} secili={seciliOgr} islem={pencere} onKapat={() => setPencere(null)}
          onBitti={(yeni) => { setV(yeni); setSecim(new Set()); setPencere(null) }} />
      )}
    </>
  )
}
