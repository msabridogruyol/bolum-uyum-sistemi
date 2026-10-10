// [2026-10-09] Okul paneli — okul bazlı yönetim: özet istatistik, öğrenci hesapları (toplu açma / şifre / silme),
// okul yetkilileri ve işlem kayıtları. Süper admin her okulu (ve okulId=0: okul harici) görür; okul yetkilisi yalnızca kendi okulunu.
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import RaporDugmeleri from '../../components/RaporDugmeleri'
import { api } from '../../api/client'
import { useAdminAuth } from '../../context/AdminAuthContext'
import TopluYuklemePenceresi from '../../components/yonetim/TopluYuklemePenceresi'
import OgrenciDetayPenceresi from '../../components/yonetim/OgrenciDetayPenceresi'
import { DurumRozeti, Pencere, SifreHucresi, SifreListesi, base64Indir, onceSure, tarih } from '../../components/yonetim/ortak'
import OkulBilgiKarti from '../../components/OkulBilgiKarti'
import MeslekDiliDuzenleyici from '../../components/yonetim/MeslekDiliDuzenleyici'
import OkulTemaKarti from '../../components/yonetim/OkulTemaKarti'
import AkranSekmesi from '../../components/yonetim/AkranPaneli'

function Cubuk({ deger, toplam, renk = 'var(--pu)' }) {
  const y = toplam ? Math.round((100 * deger) / toplam) : 0
  return <div className="yp-cubuk"><div style={{ width: `${Math.max(y ? 3 : 0, y)}%`, background: renk }} /><span>{deger} · %{y}</span></div>
}

// ----------------------------------------------------------------------------- Özet
function OzetSekmesi({ oz }) {
  const enCokGiris = Math.max(1, ...oz.gunluk_giris.map((g) => g.sayi))
  return (
    <>
      <div className="yp-kpi-grid">
        <div className="yp-kpi"><div className="yp-kpi-e">Öğrenci</div><div className="yp-kpi-d">{oz.toplam}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Giriş yapan</div><div className="yp-kpi-d">{oz.giris_yapan}</div><div className="yp-kpi-a">%{oz.toplam ? Math.round((100 * oz.giris_yapan) / oz.toplam) : 0}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Teste başlayan</div><div className="yp-kpi-d">{oz.teste_baslayan}</div><div className="yp-kpi-a">%{oz.toplam ? Math.round((100 * oz.teste_baslayan) / oz.toplam) : 0}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Testi tamamlayan</div><div className="yp-kpi-d" style={{ color: 'var(--gr)' }}>{oz.tamamlayan}</div><div className="yp-kpi-a">%{oz.toplam ? Math.round((100 * oz.tamamlayan) / oz.toplam) : 0}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Hedef bölüm seçen</div><div className="yp-kpi-d">{oz.hedef_secen}</div></div>
      </div>

      <div className="yp-iki">
        <div className="card" style={{ margin: 0 }}>
          <div className="ct">Öğrenci durumu</div>
          {oz.durumlar.map((d) => (
            <div key={d.kod} className="yp-cubuk-satir"><span><DurumRozeti kod={d.kod} etiket={d.etiket} /></span><Cubuk deger={d.sayi} toplam={oz.toplam}
              renk={{ tamamlandi: 'var(--gr)', devam: 'var(--pu)', giris_yok: 'var(--am)' }[d.kod] || 'var(--tx3)'} /></div>
          ))}
        </div>
        <div className="card" style={{ margin: 0 }}>
          <div className="ct">Son 14 gün — giriş yapan öğrenci</div>
          <div className="yp-gunluk">
            {oz.gunluk_giris.map((g) => (
              <div key={g.gun} title={`${new Date(g.gun).toLocaleDateString('tr-TR')}: ${g.sayi} öğrenci`}>
                <div className="yp-gunluk-cubuk" style={{ height: `${(100 * g.sayi) / enCokGiris}%` }}>{g.sayi > 0 && <span>{g.sayi}</span>}</div>
                <div className="yp-gunluk-gun">{new Date(g.gun).getDate()}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <div className="ct">Sınıflara göre</div>
        {oz.siniflar.length === 0 ? <div className="bos-durum">Henüz öğrenci yok.</div> : (
          <table className="yp-tablo">
            <thead><tr><th>Sınıf</th><th>Öğrenci</th><th style={{ width: '24%' }}>Giriş yapan</th><th style={{ width: '24%' }}>Devam eden</th><th style={{ width: '24%' }}>Tamamlayan</th></tr></thead>
            <tbody>
              {oz.siniflar.map((s) => (
                <tr key={s.sinif}><td><b>{s.sinif}</b></td><td>{s.ogrenci}</td>
                  <td><Cubuk deger={s.giris_yapan} toplam={s.ogrenci} renk="var(--am)" /></td>
                  <td><Cubuk deger={s.devam} toplam={s.ogrenci} /></td>
                  <td><Cubuk deger={s.tamamlayan} toplam={s.ogrenci} renk="var(--gr)" /></td></tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="yp-iki" style={{ marginTop: 14 }}>
        {[['En çok 1. sırada önerilen bölümler', oz.en_cok_onerilen], ['En çok hedeflenen bölümler', oz.en_cok_hedeflenen]].map(([baslik, liste]) => (
          <div key={baslik} className="card" style={{ margin: 0 }}>
            <div className="ct">{baslik}</div>
            {liste.length === 0 ? <div className="yp-ince">Henüz veri yok.</div> : liste.map((b) => (
              <div key={b.bolum} className="yp-cubuk-satir"><span className="yp-bolum-adi">{b.bolum}</span><Cubuk deger={b.sayi} toplam={liste[0].sayi} /></div>
            ))}
          </div>
        ))}
      </div>
    </>
  )
}

// ----------------------------------------------------------------------------- Öğrenciler
function OgrencilerSekmesi({ okulId, okulAd, superAdmin, okullar, ogrenciler, yenile }) {
  const [arama, setArama] = useState('')
  const [sinif, setSinif] = useState('')
  const [durum, setDurum] = useState('')
  const [secili, setSecili] = useState(new Set())
  const [yukleme, setYukleme] = useState(false)
  const [detay, setDetay] = useState(null)
  const [sifreler, setSifreler] = useState(null)
  const [silOnay, setSilOnay] = useState(false)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [sinifAta, setSinifAta] = useState({ sinif: '', sube: '' })

  const siniflar = useMemo(() => [...new Set(ogrenciler.map((o) => o.sinif).filter(Boolean))], [ogrenciler])
  const liste = ogrenciler.filter((o) => {
    const a = arama.toLocaleLowerCase('tr')
    return (!a || o.ad_soyad.toLocaleLowerCase('tr').includes(a) || o.email.toLowerCase().includes(a) || (o.ogrenci_no || '').includes(a))
      && (!sinif || o.sinif === sinif) && (!durum || o.durum === durum)
  })
  const hepsiSecili = liste.length > 0 && liste.every((o) => secili.has(o.id))

  function sec(id) { setSecili((s) => { const y = new Set(s); y.has(id) ? y.delete(id) : y.add(id); return y }) }
  function hepsiniSec() { setSecili(hepsiSecili ? new Set() : new Set(liste.map((o) => o.id))) }

  async function topluIslem(fn) {
    setBekle(true); setHata(null)
    try { await fn() } catch (e) { setHata(e.detail || 'İşlem başarısız.') } finally { setBekle(false) }
  }
  const sifreSifirla = () => topluIslem(async () => { setSifreler(await api.ogrenciSifreleriniSifirla([...secili])); setSecili(new Set()); yenile() })
  const sil = () => topluIslem(async () => { await api.ogrencileriSil([...secili]); setSecili(new Set()); setSilOnay(false); yenile() })
  // [2026-10-10] Seçili öğrencilere sınıf / şube ver (rehber öğretmen)
  const sinifVer = () => topluIslem(async () => {
    for (const id of secili) await api.ogrenciDuzenle(id, { sinif: sinifAta.sinif || undefined, sube: sinifAta.sube })
    setSecili(new Set()); yenile()
  })

  return (
    <>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="yp-arac">
        <input className="auth-input" style={{ maxWidth: 260 }} placeholder="İsim veya e-posta ara…" value={arama} onChange={(e) => setArama(e.target.value)} />
        <select className="yp-sec" value={sinif} onChange={(e) => setSinif(e.target.value)}>
          <option value="">Tüm sınıflar</option>{siniflar.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select className="yp-sec" value={durum} onChange={(e) => setDurum(e.target.value)}>
          <option value="">Tüm durumlar</option>
          <option value="giris_yok">Henüz giriş yapmadı</option><option value="baslamadi">Teste başlamadı</option>
          <option value="devam">Devam ediyor</option><option value="tamamlandi">Testi tamamladı</option>
        </select>
        <div style={{ flex: 1 }} />
        <button className="btn sec" disabled={bekle} title="Tüm öğrenciler: ad soyad, no, sınıf, e-posta, şifre (geçiciyse). Düzenleyip geri yükleyebilirsiniz."
          onClick={() => topluIslem(async () => { const r = await api.girisListesi(okulId); base64Indir(r.dosya_adi, r.icerik_base64) })}>⬇ Giriş listesi (Excel)</button>
        <button className="btn" onClick={() => setYukleme(true)}>+ Öğrenci ekle / Excel yükle</button>
      </div>

      {secili.size > 0 && (
        <div className="yp-secim-cubugu">
          <b>{secili.size} öğrenci seçili</b>
          <button className="btn sec" disabled={bekle} onClick={sifreSifirla}>🔑 Şifrelerini sıfırla</button>
          <span className="yp-sinif-ata">
            <select className="yp-sec" value={sinifAta.sinif} onChange={(e) => setSinifAta({ ...sinifAta, sinif: e.target.value })}>
              <option value="">Sınıf…</option>{['Aday', '9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf', 'Mezun'].map((s) => <option key={s}>{s}</option>)}
            </select>
            <input className="auth-input" style={{ width: 64, margin: 0 }} maxLength={2} placeholder="Şube" value={sinifAta.sube} onChange={(e) => setSinifAta({ ...sinifAta, sube: e.target.value.toUpperCase() })} />
            <button className="btn sec" disabled={bekle || (!sinifAta.sinif && !sinifAta.sube)} onClick={sinifVer}>Sınıfı ata</button>
          </span>
          {silOnay ? (
            <>
              <span style={{ fontSize: 12, color: 'var(--re)' }}>{secili.size} öğrenci tüm verileriyle kalıcı olarak silinecek.</span>
              <button className="btn yp-tehlike" disabled={bekle} onClick={sil}>Evet, sil</button>
              <button className="btn sec" onClick={() => setSilOnay(false)}>Vazgeç</button>
            </>
          ) : <button className="btn sec yp-tehlike-ince" onClick={() => setSilOnay(true)}>🗑 Sil</button>}
          <div style={{ flex: 1 }} />
          <button className="yp-mini" onClick={() => setSecili(new Set())}>Seçimi kaldır</button>
        </div>
      )}

      <div className="yp-ince" style={{ margin: '4px 0 8px' }}>{liste.length} / {ogrenciler.length} öğrenci</div>
      {ogrenciler.length === 0 ? (
        <div className="yp-bos">
          <div style={{ fontSize: 34 }}>🎒</div>
          <b>Bu okulda henüz öğrenci hesabı yok.</b>
          <div className="yp-ince">Excel şablonuyla tüm sınıfı tek seferde ekleyebilirsiniz.</div>
          <button className="btn" style={{ marginTop: 10 }} onClick={() => setYukleme(true)}>+ Öğrenci hesabı aç</button>
        </div>
      ) : (
        <div className="yp-tablo-kap">
          <table className="yp-tablo yp-tiklanir">
            <thead>
              <tr>
                <th style={{ width: 30 }}><input type="checkbox" checked={hepsiSecili} onChange={hepsiniSec} aria-label="Tümünü seç" /></th>
                <th>Ad Soyad</th><th>No</th><th>Sınıf</th><th>Şifre</th><th>Durum</th><th>Son giriş</th><th>Öneri / hedef</th>
              </tr>
            </thead>
            <tbody>
              {liste.map((o) => (
                <tr key={o.id} onClick={() => setDetay(o.id)} className={secili.has(o.id) ? 'secili' : ''}>
                  <td onClick={(e) => e.stopPropagation()}><input type="checkbox" checked={secili.has(o.id)} onChange={() => sec(o.id)} aria-label={`${o.ad_soyad} seç`} /></td>
                  <td><b>{o.ad_soyad}</b>{o.test_hesabi && <span className="test-rozet">TEST</span>}<div className="yp-ince">{o.email}</div></td>
                  <td className="yp-ince">{o.ogrenci_no || '—'}</td>
                  <td>{o.sinif_metni || '—'}</td>
                  <td><SifreHucresi gecici={o.gecici_sifre} degistirmeli={o.sifre_degistirmeli} /></td>
                  <td><DurumRozeti kod={o.durum} etiket={o.durum_etiket} /></td>
                  <td className="yp-ince">{onceSure(o.son_giris_zamani)}</td>
                  <td style={{ fontSize: 12 }}>
                    {o.ilk_bolum ? <div>⭐ {o.ilk_bolum}</div> : <span className="yp-ince">—</span>}
                    {o.hedef_bolum && <div className="yp-ince">🎯 {o.hedef_bolum}</div>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {yukleme && <TopluYuklemePenceresi okulId={okulId} okulAd={okulAd} onKapat={() => setYukleme(false)} onBitti={yenile} />}
      {detay && <OgrenciDetayPenceresi ogrenciId={detay} superAdmin={superAdmin} okullar={okullar} onKapat={() => setDetay(null)} onDegisti={yenile} />}
      {sifreler && (
        <Pencere genis baslik={`${sifreler.kayitlar.length} öğrencinin şifresi sıfırlandı`} onKapat={() => setSifreler(null)}
          alt={<button className="btn" onClick={() => setSifreler(null)}>Kapat</button>}>
          <SifreListesi kayitlar={sifreler.kayitlar} dosya={sifreler} aciklama="Eski şifreler artık geçmez; öğrenciler yeni geçici şifreyle girip kendi şifrelerini belirler." />
        </Pencere>
      )}
    </>
  )
}

// ----------------------------------------------------------------------------- Okul yetkilileri
function YetkililerSekmesi({ okulId, superAdmin }) {
  const [liste, setListe] = useState(null)
  const [form, setForm] = useState({ ad_soyad: '', email: '' })
  const [sifre, setSifre] = useState(null)
  const [silinecek, setSilinecek] = useState(null)
  const [hata, setHata] = useState(null)
  const yukle = useCallback(() => { api.okulYetkilileri(okulId).then(setListe).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [okulId])
  useEffect(yukle, [yukle])

  async function islem(fn) { setHata(null); try { await fn() } catch (e) { setHata(e.detail || 'İşlem başarısız.') } }
  const ekle = (e) => { e.preventDefault(); islem(async () => { const r = await api.okulYetkilisiEkle(okulId, form); setSifre(r); setForm({ ad_soyad: '', email: '' }); yukle() }) }

  return (
    <>
      <div className="yp-ince" style={{ marginBottom: 12 }}>
        Okul yetkilileri (rehber öğretmen, müdür yardımcısı vb.) yönetim girişinden (<code>/admin/giris</code>) girer ve yalnızca bu okulun
        öğrencilerini görür: hesap açar, şifre sıfırlar, siler, istatistik ve kayıtları inceler.
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {superAdmin && (
        <form className="yp-kutu yp-form-satir" style={{ marginBottom: 14 }} onSubmit={ekle}>
          <input className="auth-input" placeholder="Ad Soyad" value={form.ad_soyad} onChange={(e) => setForm({ ...form, ad_soyad: e.target.value })} required minLength={3} />
          <input className="auth-input" type="email" placeholder="E-posta" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <button className="btn" type="submit">+ Okul yetkilisi ekle</button>
        </form>
      )}
      {sifre && (
        <div className="yp-uyari" style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <span><b>{sifre.ad_soyad}</b> için geçici şifre (tabloda da “geçici” olarak görünür; kendi şifresini belirleyince kaybolur):</span>
          <code className="yp-sifre">{sifre.gecici_sifre}</code>
          <span className="yp-ince">Giriş: {sifre.email} · ilk girişte kendi şifresini belirler.</span>
          <button className="yp-mini" onClick={() => setSifre(null)}>Tamam</button>
        </div>
      )}
      {!liste ? <div className="bos-durum">Yükleniyor…</div> : liste.length === 0 ? <div className="bos-durum">Bu okulun henüz yetkilisi yok.</div> : (
        <table className="yp-tablo">
          <thead><tr><th>Ad Soyad</th><th>E-posta</th><th>Son giriş</th><th>Şifre</th>{superAdmin && <th />}</tr></thead>
          <tbody>
            {liste.map((y) => (
              <tr key={y.id}>
                <td><b>{y.ad_soyad}</b>{y.test_hesabi && <span className="test-rozet">TEST</span>}</td><td className="yp-ince">{y.email}</td><td className="yp-ince">{onceSure(y.son_giris_zamani)}</td>
                <td><SifreHucresi gecici={y.gecici_sifre} degistirmeli={y.sifre_degistirmeli} /></td>
                {superAdmin && (
                  <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <button className="yp-mini" onClick={() => islem(async () => setSifre({ ...y, ...(await api.okulYetkilisiSifreSifirla(y.id)) }))}>🔑 Şifre sıfırla</button>{' '}
                    {silinecek === y.id
                      ? <><button className="yp-mini yp-tehlike" onClick={() => islem(async () => { await api.okulYetkilisiSil(y.id); setSilinecek(null); yukle() })}>Evet, sil</button> <button className="yp-mini" onClick={() => setSilinecek(null)}>Vazgeç</button></>
                      : <button className="yp-mini" onClick={() => setSilinecek(y.id)}>🗑</button>}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  )
}

// ----------------------------------------------------------------------------- Kayıtlar
function KayitlarSekmesi({ okulId }) {
  const [gun, setGun] = useState(30)
  const [tur, setTur] = useState('')
  const [liste, setListe] = useState(null)
  useEffect(() => { setListe(null); api.okulKayitlari(okulId, gun).then(setListe).catch(() => setListe([])) }, [okulId, gun])
  const gosterilen = (liste || []).filter((k) => !tur || k.tur === tur)
  return (
    <>
      <div className="yp-arac">
        <select className="yp-sec" value={gun} onChange={(e) => setGun(Number(e.target.value))}>
          {[7, 30, 90, 365].map((g) => <option key={g} value={g}>Son {g} gün</option>)}
        </select>
        <select className="yp-sec" value={tur} onChange={(e) => setTur(e.target.value)}>
          <option value="">Tüm kayıtlar</option><option value="yonetim">Yönetim işlemleri</option><option value="ogrenci">Öğrenci girişleri</option>
        </select>
        <span className="yp-ince">{gosterilen.length} kayıt</span>
      </div>
      {!liste ? <div className="bos-durum">Yükleniyor…</div> : gosterilen.length === 0 ? <div className="bos-durum">Bu aralıkta kayıt yok.</div> : (
        <div className="yp-tablo-kap">
          <table className="yp-tablo">
            <thead><tr><th style={{ width: 150 }}>Zaman</th><th>İşlem</th><th>Kim</th><th>Ayrıntı</th></tr></thead>
            <tbody>
              {gosterilen.map((k, i) => (
                <tr key={i}>
                  <td className="yp-ince">{tarih(k.zaman)}</td>
                  <td><span className={`yp-durum ${k.tur === 'yonetim' ? 'yp-d-mor' : k.etiket.startsWith('Hatalı') ? 'yp-d-kirmizi' : 'yp-d-gri'}`}>{k.etiket}</span></td>
                  <td>{k.yapan}</td>
                  <td className="yp-ince" style={{ maxWidth: 420 }}>{k.aciklama || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}

// ----------------------------------------------------------------------------- Okul tanıtım bilgileri
const BOS_KISI = { gorev: 'Rehber Öğretmen / Psikolojik Danışman', ad: '', eposta: '', telefon: '' }

function OkulBilgileriSekmesi({ okulId }) {
  const [f, setF] = useState(null)
  const [gorevler, setGorevler] = useState([])
  const [hata, setHata] = useState(null)
  const [bilgi, setBilgi] = useState(null)
  const [bekle, setBekle] = useState(false)

  useEffect(() => {
    api.okulBilgi(okulId).then((d) => {
      setGorevler(d.gorevler || [])
      setF({ ...d, kurulus_yili: d.kurulus_yili ?? '', ogrenci_sayisi: d.ogrenci_sayisi ?? '', kadro: d.kadro?.length ? d.kadro : [{ ...BOS_KISI, gorev: 'Okul Müdürü' }] })
    }).catch((e) => setHata(e.detail || 'Bilgiler yüklenemedi.'))
  }, [okulId])

  if (!f) return hata ? <div className="auth-error">{hata}</div> : <div className="bos-durum">Yükleniyor…</div>
  const alan = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const kisi = (i, k) => (e) => setF({ ...f, kadro: f.kadro.map((x, j) => (j === i ? { ...x, [k]: e.target.value } : x)) })
  const kisiSil = (i) => setF({ ...f, kadro: f.kadro.filter((_, j) => j !== i) })
  const kisiTasi = (i, y) => { const k = [...f.kadro]; [k[i], k[i + y]] = [k[i + y], k[i]]; setF({ ...f, kadro: k }) }

  async function kaydet(e) {
    e.preventDefault()
    setBekle(true); setHata(null)
    try {
      const d = await api.okulBilgiGuncelle(okulId, {
        ...f,
        kurulus_yili: f.kurulus_yili === '' ? null : Number(f.kurulus_yili),
        ogrenci_sayisi: f.ogrenci_sayisi === '' ? null : Number(f.ogrenci_sayisi),
      })
      setF({ ...d, kurulus_yili: d.kurulus_yili ?? '', ogrenci_sayisi: d.ogrenci_sayisi ?? '', kadro: d.kadro?.length ? d.kadro : [] })
      setBilgi('Kaydedildi. Öğrenciler okul rozetine tıklayınca bu bilgileri görür.'); setTimeout(() => setBilgi(null), 4000)
    } catch (err) {
      setHata(err.detail || 'Kaydedilemedi.')
    } finally { setBekle(false) }
  }

  return (
    <div className="okb-duzen">
      <form onSubmit={kaydet} className="okb-form">
        {hata && <div className="auth-error">{hata}</div>}
        {bilgi && <div className="card" style={{ background: 'var(--grl)', borderColor: 'var(--gr)', padding: '10px 14px', fontSize: 12.5 }}>{bilgi}</div>}
        <div className="card" style={{ margin: 0 }}>
          <div className="ct">Genel bilgiler</div>
          <div className="okb-form-iki">
            <div><label className="auth-label">Kuruluş yılı</label><input className="auth-input" type="number" min={1800} max={new Date().getFullYear()} value={f.kurulus_yili} onChange={alan('kurulus_yili')} placeholder="Örn. 1987" /></div>
            <div><label className="auth-label">Öğrenci sayısı</label><input className="auth-input" type="number" min={0} value={f.ogrenci_sayisi} onChange={alan('ogrenci_sayisi')} placeholder="Örn. 640" /></div>
          </div>
          <label className="auth-label">Kısa tanıtım <span className="yp-ince">({(f.tanitim || '').length}/3000)</span></label>
          <textarea className="auth-input" rows={5} maxLength={3000} style={{ resize: 'vertical', fontFamily: 'var(--fn)' }} value={f.tanitim || ''} onChange={alan('tanitim')}
            placeholder="Okulun vizyonu, öne çıkan programları, kulüpleri, başarıları…" />
        </div>

        <div className="card" style={{ margin: 0 }}>
          <div className="ct">Kadro (müdür, müdür yardımcıları, rehber öğretmen / psikolojik danışman…)</div>
          {f.kadro.map((k, i) => (
            <div key={i} className="okb-kadro-satir">
              <select className="auth-input" value={gorevler.includes(k.gorev) ? k.gorev : 'Diğer'} onChange={kisi(i, 'gorev')}>
                {gorevler.map((g) => <option key={g}>{g}</option>)}
              </select>
              <input className="auth-input" value={k.ad} onChange={kisi(i, 'ad')} placeholder="Ad Soyad" />
              <div className="okb-kadro-tus">
                <button type="button" className="yp-mini" disabled={i === 0} onClick={() => kisiTasi(i, -1)} title="Yukarı">↑</button>
                <button type="button" className="yp-mini" disabled={i === f.kadro.length - 1} onClick={() => kisiTasi(i, 1)} title="Aşağı">↓</button>
                <button type="button" className="yp-mini" onClick={() => kisiSil(i)} title="Kaldır">✕</button>
              </div>
              <input className="auth-input" type="email" value={k.eposta || ''} onChange={kisi(i, 'eposta')} placeholder="E-posta" />
              <input className="auth-input" value={k.telefon || ''} onChange={kisi(i, 'telefon')} placeholder="Telefon (isteğe bağlı)" />
            </div>
          ))}
          <button type="button" className="btn sec" onClick={() => setF({ ...f, kadro: [...f.kadro, { ...BOS_KISI }] })}>+ Kişi ekle</button>
        </div>

        <div className="card" style={{ margin: 0 }}>
          <div className="ct">İletişim</div>
          <label className="auth-label">Adres</label>
          <input className="auth-input" value={f.adres || ''} onChange={alan('adres')} placeholder="Mahalle, cadde, ilçe / il" />
          <div className="okb-form-iki">
            <div><label className="auth-label">Telefon</label><input className="auth-input" value={f.telefon || ''} onChange={alan('telefon')} placeholder="0 (212) 000 00 00" /></div>
            <div><label className="auth-label">E-posta</label><input className="auth-input" type="email" value={f.eposta || ''} onChange={alan('eposta')} placeholder="bilgi@okul.k12.tr" /></div>
          </div>
          <label className="auth-label">Web sitesi</label>
          <input className="auth-input" value={f.web || ''} onChange={alan('web')} placeholder="www.okul.k12.tr" />
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button className="btn" type="submit" disabled={bekle}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
          {f.bilgi_guncelleme_zamani && <span className="yp-ince">Son güncelleme: {tarih(f.bilgi_guncelleme_zamani)}</span>}
        </div>
      </form>
      <div className="okb-onizleme">
        <div className="yp-ince" style={{ marginBottom: 6, fontWeight: 700 }}>ÖĞRENCİ BÖYLE GÖRÜR (okul rozetine tıklayınca)</div>
        <div className="card" style={{ margin: 0 }}><OkulBilgiKarti okul={{ ...f, kurulus_yili: Number(f.kurulus_yili) || null, ogrenci_sayisi: Number(f.ogrenci_sayisi) || null }} /></div>
      </div>
    </div>
  )
}

// ----------------------------------------------------------------------------- Sayfa
export default function OkulPaneliSayfasi() {
  const { okulId: ham } = useParams()
  const okulId = Number(ham)
  const { rol } = useAdminAuth()
  const superAdmin = rol === 'super_admin'
  // ?sekme=bilgiler | yetkililer | ogrenciler | meslekdili | gorunum | kayitlar — Okullar sayfasındaki kısayollar doğrudan ilgili sekmeyi açar
  const [params] = useSearchParams()
  const [sekme, setSekme] = useState(params.get('sekme') || 'ozet')
  const [oz, setOz] = useState(null)
  const [ogrenciler, setOgrenciler] = useState([])
  const [okullar, setOkullar] = useState([])
  const [hata, setHata] = useState(null)

  const yenile = useCallback(() => {
    api.okulOzeti(okulId).then(setOz).catch((e) => setHata(e.detail || 'Okul yüklenemedi.'))
    api.okulOgrencileri(okulId).then(setOgrenciler).catch(() => {})
  }, [okulId])
  useEffect(() => { setOz(null); setHata(null); yenile() }, [yenile])
  useEffect(() => { if (superAdmin) api.yonetimOkullar().then(setOkullar).catch(() => {}) }, [superAdmin])

  if (hata) return <div className="pg pg-genis"><div className="auth-error">{hata}</div></div>
  if (!oz) return <div className="pg pg-genis"><div className="bos-durum">Yükleniyor…</div></div>

  const sekmeler = [['ozet', 'Özet'], ['ogrenciler', `Öğrenciler (${oz.toplam})`], ['akran', 'Şube & Akran'],
    ...(okulId ? [['bilgiler', 'Okul Bilgileri'], ['yetkililer', `Okul Yetkilileri (${oz.yetkili_sayisi})`], ['meslekdili', 'Meslek Dili'], ['gorunum', 'Görünüm']] : []), ['kayitlar', 'Kayıtlar']]
  return (
    <div className="pg pg-genis">
      {superAdmin && <Link to="/admin/okullar" className="yp-geri">← Okullar</Link>}
      <div className="yp-okul-baslik">
        {oz.okul.logo ? <img src={oz.okul.logo} alt="" className="yp-okul-logo" /> : <div className="yp-okul-logo yp-okul-logo-bos">{okulId ? '🏫' : '👤'}</div>}
        <div>
          <div className="pt" style={{ margin: 0 }}>{oz.okul.ad}</div>
          <div className="ps" style={{ margin: 0 }}>{oz.okul.alt_baslik || 'Okul paneli'}</div>
        </div>
      </div>
      <RaporDugmeleri baslik="Okul raporu" secenekler={[
        { anahtar: 'p', ad: 'PDF', ikon: '📄', aciklama: 'Tamamlama oranları, sınıflar, alan dağılımı, ortak güçlü yönler ve öğrenci listesi', indir: () => api.okulRaporuIndir(okulId, 'pdf') },
        { anahtar: 'x', ad: 'Excel', ikon: '📊', aciklama: 'Özet, sınıflar ve tüm öğrenciler tablo halinde', indir: () => api.okulRaporuIndir(okulId, 'xlsx') },
      ]} />
      <div className="yp-sekmeler yp-sekmeler-buyuk">
        {sekmeler.map(([k, ad]) => <button key={k} className={sekme === k ? 'aktif' : ''} onClick={() => setSekme(k)}>{ad}</button>)}
      </div>
      {sekme === 'ozet' && <OzetSekmesi oz={oz} />}
      {sekme === 'ogrenciler' && <OgrencilerSekmesi okulId={okulId} okulAd={oz.okul.ad} superAdmin={superAdmin} okullar={okullar} ogrenciler={ogrenciler} yenile={yenile} />}
      {sekme === 'akran' && <AkranSekmesi okulId={okulId} ogrenciler={ogrenciler} yenile={yenile} />}
      {sekme === 'bilgiler' && <OkulBilgileriSekmesi okulId={okulId} />}
      {sekme === 'yetkililer' && <YetkililerSekmesi okulId={okulId} superAdmin={superAdmin} />}
      {sekme === 'meslekdili' && okulId > 0 && <MeslekDiliDuzenleyici okulId={okulId} />}
      {sekme === 'gorunum' && okulId > 0 && <OkulTemaKarti okulId={okulId} />}
      {sekme === 'kayitlar' && <KayitlarSekmesi okulId={okulId} />}
    </div>
  )
}
