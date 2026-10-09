// [2026-10-09] Meslek dili (jargon) sözlüğü düzenleyici.
// okulId = 0 → genel sürüm (süper admin; tüm okullar). okulId > 0 → yalnızca o okulun öğrencilerine görünen özel sürüm.
import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { tarih } from './ortak'

const bosTerim = () => ({ terim: '', anlam: '', ornek: '' })
const KAYNAK = {
  okul: ['Okula özel', 'yp-d-yesil'],
  genel: ['Genel (düzenlendi)', 'yp-d-mor'],
  varsayilan: ['Varsayılan', 'yp-d-gri'],
}
const baslikYap = (s) => (s || '').toLocaleLowerCase('tr').replace(/(^|[\s(/-])(\p{L})/gu, (m, a, b) => a + b.toLocaleUpperCase('tr'))

export default function MeslekDiliDuzenleyici({ okulId }) {
  const genel = !okulId
  const [liste, setListe] = useState(null)
  const [hata, setHata] = useState(null)
  const [arama, setArama] = useState('')
  const [yalnizDuzenlenen, setYalnizDuzenlenen] = useState(false)
  const [secili, setSecili] = useState(null)       // bolum_id
  const [kayit, setKayit] = useState(null)         // sunucudaki hâli
  const [terimler, setTerimler] = useState([])     // düzenlenen hâli
  const [mesaj, setMesaj] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [sifirlaOnay, setSifirlaOnay] = useState(false)

  const listeYenile = useCallback(() => {
    api.meslekDiliListe(okulId).then((v) => setListe([...v.bolumler].sort((a, b) => a.ad.localeCompare(b.ad, 'tr')))).catch((e) => setHata(e.detail || 'Liste alınamadı.'))
  }, [okulId])
  useEffect(() => { setListe(null); setSecili(null); listeYenile() }, [listeYenile])

  const degisti = useMemo(() => kayit && JSON.stringify(terimler) !== JSON.stringify(kayit.terimler), [terimler, kayit])

  function sec(bolumId) {
    if (bolumId === secili) return
    if (degisti && !window.confirm('Kaydedilmemiş değişiklikler var. Kaydetmeden başka bölüme geçilsin mi?')) return
    setSecili(bolumId); setKayit(null); setMesaj(null); setSifirlaOnay(false)
    api.meslekDiliGetir(okulId, bolumId)
      .then((v) => { setKayit(v); setTerimler(v.terimler.map((t) => ({ terim: t.terim, anlam: t.anlam, ornek: t.ornek || '' }))) })
      .catch((e) => setMesaj({ tur: 'hata', metin: e.detail || 'Bölüm yüklenemedi.' }))
  }

  const guncelle = (i, alan, deger) => setTerimler((l) => l.map((t, j) => (j === i ? { ...t, [alan]: deger } : t)))
  const tasi = (i, yon) => setTerimler((l) => {
    const j = i + yon
    if (j < 0 || j >= l.length) return l
    const k = [...l]; [k[i], k[j]] = [k[j], k[i]]; return k
  })
  const sil = (i) => setTerimler((l) => l.filter((_, j) => j !== i))

  async function kaydet() {
    setBekle(true); setMesaj(null)
    try {
      const v = await api.meslekDiliKaydet(okulId, secili, terimler)
      setKayit(v); setTerimler(v.terimler.map((t) => ({ terim: t.terim, anlam: t.anlam, ornek: t.ornek || '' })))
      setMesaj({ tur: 'tamam', metin: genel ? 'Kaydedildi. Kendi sürümü olmayan tüm okullarda görünür.' : 'Kaydedildi. Okulunuzun öğrencileri artık bu sürümü görür.' })
      listeYenile()
    } catch (e) {
      setMesaj({ tur: 'hata', metin: e.detail || 'Kaydedilemedi.' })
    } finally { setBekle(false) }
  }

  async function sifirla() {
    setBekle(true); setMesaj(null)
    try {
      const v = await api.meslekDiliSifirla(okulId, secili)
      setKayit(v); setTerimler(v.terimler.map((t) => ({ terim: t.terim, anlam: t.anlam, ornek: t.ornek || '' })))
      setMesaj({ tur: 'tamam', metin: genel ? 'Varsayılan içeriğe dönüldü.' : 'Okula özel sürüm kaldırıldı; öğrenciler genel sözlüğü görür.' })
      setSifirlaOnay(false); listeYenile()
    } catch (e) {
      setMesaj({ tur: 'hata', metin: e.detail || 'İşlem yapılamadı.' })
    } finally { setBekle(false) }
  }

  const gorunen = useMemo(() => {
    const q = arama.trim().toLocaleLowerCase('tr')
    return (liste || []).filter((b) => (!q || b.ad.toLocaleLowerCase('tr').includes(q)) && (!yalnizDuzenlenen || b.duzenlendi))
  }, [liste, arama, yalnizDuzenlenen])

  if (hata) return <div className="auth-error">{hata}</div>
  if (!liste) return <div className="bos-durum">Yükleniyor…</div>
  const duzenlenenSayisi = liste.filter((b) => b.duzenlendi).length

  return (
    <div>
      <div className="yp-uyari" style={{ background: 'var(--pul)', borderColor: 'var(--pum)' }}>
        {genel
          ? <><b>Genel sözlük.</b> Burada yaptığın değişiklikler, o bölüm için kendi sürümünü oluşturmamış tüm okulların öğrencilerine görünür.</>
          : <><b>Okulunuza özel sözlük.</b> Buradaki değişiklikler yalnızca bu okulun öğrencilerine görünür. Düzenlemediğiniz bölümlerde genel sözlük gösterilir.</>}
        {' '}Öğrenciler bu terimleri bölüm penceresindeki <b>Meslek Dili</b> sekmesinde görür.
      </div>

      <div className="md-duzen">
        <div className="md-liste">
          <input className="auth-input" style={{ margin: 0 }} placeholder="Bölüm ara…" value={arama} onChange={(e) => setArama(e.target.value)} />
          <label className="md-filtre">
            <input type="checkbox" checked={yalnizDuzenlenen} onChange={(e) => setYalnizDuzenlenen(e.target.checked)} />
            Yalnızca düzenlenenler ({duzenlenenSayisi})
          </label>
          <div className="md-liste-kap">
            {gorunen.map((b) => {
              const [etiket, sinif] = KAYNAK[b.kaynak] || KAYNAK.varsayilan
              return (
                <button key={b.bolum_id} className={`md-bolum${secili === b.bolum_id ? ' aktif' : ''}`} onClick={() => sec(b.bolum_id)}>
                  <span className="md-bolum-ad">{baslikYap(b.ad)}</span>
                  <span className="md-bolum-alt">
                    <span className={`yp-durum ${sinif}`}>{etiket}</span>
                    <span className="yp-ince">{b.terim_sayisi} terim</span>
                  </span>
                </button>
              )
            })}
            {gorunen.length === 0 && <div className="yp-ince" style={{ padding: 12 }}>Eşleşen bölüm yok.</div>}
          </div>
        </div>

        <div className="md-editor">
          {!secili && <div className="yp-bos"><div style={{ fontSize: 28 }}>📖</div><b>Düzenlemek için soldan bir bölüm seç</b><span className="yp-ince">Her bölümde terim, anlamı ve sahadan bir örnek cümle bulunur.</span></div>}
          {secili && !kayit && !mesaj && <div className="bos-durum">Yükleniyor…</div>}
          {secili && kayit && (
            <>
              <div className="md-editor-baslik">
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 17, fontWeight: 800, color: 'var(--tx)' }}>{baslikYap(kayit.ad)}</div>
                  <div className="yp-ince">
                    {kayit.duzenlendi
                      ? `${genel ? 'Genel sürüm' : 'Okula özel sürüm'} · Son düzenleyen: ${kayit.guncelleyen_ad || '—'} · ${tarih(kayit.guncelleme_zamani)}`
                      : `Şu an ${kayit.ust_kaynak === 'genel' ? 'genel sözlük' : 'varsayılan içerik'} gösteriliyor. Kaydettiğinde ${genel ? 'genel sürüm' : 'okulunuza özel sürüm'} oluşur.`}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {kayit.duzenlendi && !sifirlaOnay && (
                    <button className="btn sec" disabled={bekle} onClick={() => setSifirlaOnay(true)}>{genel ? 'Varsayılana dön' : 'Genel sözlüğe dön'}</button>
                  )}
                  {sifirlaOnay && (
                    <>
                      <button className="btn sec" disabled={bekle} onClick={() => setSifirlaOnay(false)}>Vazgeç</button>
                      <button className="btn" style={{ background: 'var(--re)' }} disabled={bekle} onClick={sifirla}>Evet, düzenlemeyi kaldır</button>
                    </>
                  )}
                  <button className="btn" disabled={bekle || !degisti} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
                </div>
              </div>
              {sifirlaOnay && (
                <div className="yp-uyari">
                  {genel ? 'Genel sürümdeki değişiklikler silinir ve varsayılan içerik geri gelir.' : 'Okulunuza özel sürüm silinir; öğrencileriniz genel sözlüğü görür.'} Bu işlem geri alınamaz.
                </div>
              )}
              {mesaj && <div className={mesaj.tur === 'hata' ? 'auth-error' : 'yp-uyari'} style={mesaj.tur === 'tamam' ? { background: 'var(--grl)', borderColor: 'var(--gr)' } : undefined}>{mesaj.metin}</div>}

              {terimler.map((t, i) => (
                <div key={i} className="md-terim">
                  <div className="md-terim-ust">
                    <span className="md-sira">{i + 1}</span>
                    <input className="auth-input md-girdi" placeholder="Terim (ör. Triyaj)" value={t.terim} maxLength={80} onChange={(e) => guncelle(i, 'terim', e.target.value)} />
                    <div className="md-araclar">
                      <button className="yp-mini" title="Yukarı taşı" disabled={i === 0} onClick={() => tasi(i, -1)}>↑</button>
                      <button className="yp-mini" title="Aşağı taşı" disabled={i === terimler.length - 1} onClick={() => tasi(i, 1)}>↓</button>
                      <button className="yp-mini" title="Terimi sil" onClick={() => sil(i)}>Sil</button>
                    </div>
                  </div>
                  <textarea className="auth-input md-girdi" rows={2} placeholder="Anlamı — öğrencinin anlayacağı sade bir dille" value={t.anlam} maxLength={600} onChange={(e) => guncelle(i, 'anlam', e.target.value)} />
                  <textarea className="auth-input md-girdi md-ornek" rows={2} placeholder="Örnek cümle — sahada nasıl kullanılır? (isteğe bağlı)" value={t.ornek} maxLength={400} onChange={(e) => guncelle(i, 'ornek', e.target.value)} />
                </div>
              ))}
              <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', flexWrap: 'wrap', marginTop: 4 }}>
                <button className="btn sec" disabled={terimler.length >= 40} onClick={() => setTerimler((l) => [...l, bosTerim()])}>+ Terim ekle</button>
                <button className="btn" disabled={bekle || !degisti} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
              </div>
            </>
          )}
          {secili && !kayit && mesaj && <div className="auth-error">{mesaj.metin}</div>}
        </div>
      </div>
    </div>
  )
}
