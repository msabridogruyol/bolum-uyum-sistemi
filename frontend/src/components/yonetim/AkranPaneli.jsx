// [2026-10-10] Akran eşleştirme, şube dağılımı önerisi ve aday öğrenci şube uyumu (yalnızca rehber / yönetim görür).
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { DurumRozeti } from './ortak'

const SINIFLAR = ['9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf']

function BenzerlikCubugu({ deger }) {
  if (deger == null) return <span className="yp-ince">—</span>
  const renk = deger >= 70 ? 'var(--gr)' : deger >= 55 ? 'var(--okul-c, var(--pu))' : 'var(--tx3)'
  return <div className="yp-cubuk"><div style={{ width: `${Math.max(4, deger)}%`, background: renk }} /><span>%{deger}</span></div>
}

function EtikNot() {
  return (
    <div className="ak-not">
      Benzerlik, K1–K4 sonuçlarının okul ortalamasına göre <b>aynı yönde ayrışmasıdır</b> (%50 = ilişkisiz, %100 = çok benzer).
      Yalnızca rehberlik amaçlıdır: öğrenciye "şuna benziyorsun" şeklinde paylaşılmamalı, şube kararında tek ölçüt olmamalıdır.
    </div>
  )
}

function AkranSatiri({ a, onSec }) {
  return (
    <tr>
      <td><b>{onSec ? <button className="ak-link" onClick={() => onSec(a.id)}>{a.ad_soyad}</button> : a.ad_soyad}</b>
        {a.dusuk_guven && <span className="ak-uyari-cip" title="Bu öğrencinin güven puanı düşük">güven düşük</span>}
        <div className="yp-ince">{a.sinif || '—'}</div></td>
      <td style={{ width: '28%' }}><BenzerlikCubugu deger={a.benzerlik} /></td>
      <td>
        {a.ortak_guclu.length > 0 ? a.ortak_guclu.map((x) => <span key={x} className="ak-cip ak-cip-ortak">{x}</span>) : <span className="yp-ince">Ortak belirgin güçlü yön yok</span>}
        {a.farkli.length > 0 && <div className="yp-ince" style={{ marginTop: 4 }}>Ayrıştıkları: {a.farkli.join(', ')}</div>}
      </td>
    </tr>
  )
}

// ----------------------------------------------------------------------------- öğrenci detayı: benzer akranlar
export function AkranListesi({ ogrenciId }) {
  const [kapsam, setKapsam] = useState('okul')
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => {
    setV(null); setHata(null)
    api.ogrenciAkranlari(ogrenciId, kapsam).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  }, [ogrenciId, kapsam])
  return (
    <div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10, flexWrap: 'wrap' }}>
        <span className="yp-ince">Karşılaştırılan grup:</span>
        <select className="yp-sec" value={kapsam} onChange={(e) => setKapsam(e.target.value)}>
          <option value="okul">Tüm okul</option><option value="sinif">Yalnızca aynı sınıf düzeyi</option>
        </select>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v && !hata && <div className="bos-durum">Hesaplanıyor…</div>}
      {v?.durum === 'profil_yok' && <div className="bos-durum">Öğrenci henüz yeterli sayıda soru cevaplamadı; benzerlik hesaplanamıyor.</div>}
      {v?.durum === 'tamam' && (
        <>
          {(v.tamamlanmamis || v.dusuk_guven) && (
            <div className="yp-uyari">{v.tamamlanmamis ? 'Öğrenci testi tamamlamadı; sonuçlar ön bilgidir. ' : ''}{v.dusuk_guven ? 'Güven puanı düşük; dikkatle yorumlayın.' : ''}</div>
          )}
          {v.akranlar.length === 0 ? <div className="bos-durum">Karşılaştırılabilecek öğrenci yok ({v.havuz} profil).</div> : (
            <table className="yp-tablo">
              <thead><tr><th>Akran</th><th>Benzerlik</th><th>Ortak güçlü yönler</th></tr></thead>
              <tbody>{v.akranlar.map((a) => <AkranSatiri key={a.id} a={a} />)}</tbody>
            </table>
          )}
          <div className="yp-ince" style={{ marginTop: 8 }}>Kullanım önerisi: çalışma / proje grubu, akran mentorluğu, kulüp ekibi. {v.havuz} öğrenci arasından seçildi.</div>
          <EtikNot />
        </>
      )}
    </div>
  )
}

// ----------------------------------------------------------------------------- şube dağılımı aracı
function SubeDagilimi({ okulId, ogrenciler, yenile }) {
  const [sinif, setSinif] = useState('9. Sınıf')
  const mevcutSubeler = useMemo(() => [...new Set(ogrenciler.filter((o) => o.sinif === sinif && o.sube).map((o) => o.sube))].sort(), [ogrenciler, sinif])
  const [subeMetni, setSubeMetni] = useState('')
  const [mod, setMod] = useState('dengeli')
  const [adaylar, setAdaylar] = useState(false)
  const [cinsiyet, setCinsiyet] = useState(true)
  const [oneri, setOneri] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [mesaj, setMesaj] = useState(null)
  const adaySayisi = ogrenciler.filter((o) => o.sinif === 'Aday').length
  const sinifSayisi = ogrenciler.filter((o) => o.sinif === sinif).length

  useEffect(() => { setSubeMetni(mevcutSubeler.join(', ') || 'A, B'); setOneri(null) }, [sinif, mevcutSubeler.join()])

  const olustur = async () => {
    setBekle(true); setMesaj(null)
    try {
      setOneri(await api.subeDagilimiOner(okulId, { sinif, subeler: subeMetni.split(/[,\s;]+/).filter(Boolean), mod, adaylar_dahil: adaylar, cinsiyet_dengele: cinsiyet }))
    } catch (e) { setMesaj({ hata: true, metin: e.detail || 'Öneri oluşturulamadı.' }) }
    setBekle(false)
  }
  const uygula = async () => {
    setBekle(true); setMesaj(null)
    try {
      const atamalar = oneri.subeler.flatMap((g) => g.ogrenciler.map((o) => ({ id: o.id, sube: g.sube })))
      const r = await api.subeDagilimiUygula(okulId, { sinif, atamalar })
      setMesaj({ metin: `${r.guncellenen} öğrencinin sınıf/şubesi güncellendi.` }); setOneri(null); yenile?.()
    } catch (e) { setMesaj({ hata: true, metin: e.detail || 'Uygulanamadı.' }) }
    setBekle(false)
  }
  // Önizlemede elle taşıma: öğrenciyi başka şubeye al
  const tasi = (id, hedef) => setOneri((o) => {
    const ogr = o.subeler.flatMap((g) => g.ogrenciler).find((x) => x.id === id)
    return { ...o, elle: true, subeler: o.subeler.map((g) => ({ ...g,
      ogrenciler: g.sube === hedef ? [...g.ogrenciler.filter((x) => x.id !== id), ogr] : g.ogrenciler.filter((x) => x.id !== id),
    })).map((g) => ({ ...g, sayi: g.ogrenciler.length })) }
  })

  return (
    <div className="card" style={{ margin: 0 }}>
      <div className="ct">Şube dağılımı önerisi</div>
      <div className="ak-form">
        <label>Sınıf düzeyi
          <select className="yp-sec" value={sinif} onChange={(e) => setSinif(e.target.value)}>{SINIFLAR.map((s) => <option key={s}>{s}</option>)}</select>
        </label>
        <label>Şubeler (virgülle)
          <input className="yp-sec" value={subeMetni} onChange={(e) => setSubeMetni(e.target.value.toUpperCase())} placeholder="A, B, C" />
        </label>
        <div className="ak-mod">
          <button className={mod === 'dengeli' ? 'aktif' : ''} onClick={() => setMod('dengeli')}><b>Dengeli dağıt</b><span>Her şubede farklı profiller; şubeler birbirine benzer (önerilen)</span></button>
          <button className={mod === 'benzer' ? 'aktif' : ''} onClick={() => setMod('benzer')}><b>Benzerleri grupla</b><span>Benzer profiller aynı grupta; etüt / proje grupları için</span></button>
        </div>
        <label className="ak-kutu"><input type="checkbox" checked={cinsiyet} onChange={(e) => setCinsiyet(e.target.checked)} /> Cinsiyet dağılımını da dengele</label>
        {adaySayisi > 0 && <label className="ak-kutu"><input type="checkbox" checked={adaylar} onChange={(e) => setAdaylar(e.target.checked)} /> {adaySayisi} aday öğrenciyi de bu sınıfa dağıt</label>}
      </div>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 12 }}>
        <button className="btn" disabled={bekle || (!sinifSayisi && !adaylar)} onClick={olustur}>{bekle && !oneri ? <span className="spin" /> : 'Öneri oluştur'}</button>
        <span className="yp-ince">{sinif}: {sinifSayisi} öğrenci{adaylar ? ` + ${adaySayisi} aday` : ''}</span>
      </div>
      {mesaj && <div className={mesaj.hata ? 'auth-error' : 'yp-basari'} style={{ marginTop: 10 }}>{mesaj.metin}</div>}

      {oneri && (
        <div style={{ marginTop: 14 }}>
          <div className="ak-ozet">
            <span>Profili olan: <b>{oneri.profilli}</b></span>
            {oneri.profilsiz > 0 && <span title="Testi henüz çözmedikleri için yalnızca sayıya göre yerleştirildi">Profili olmayan: <b>{oneri.profilsiz}</b></span>}
            {oneri.subeler_arasi_fark != null && <span title="Şube profil ortalamalarının okul ortalamasından uzaklığı. Dengeli dağıtımda düşük olması beklenir.">Şubeler arası fark: <b>{oneri.subeler_arasi_fark}</b></span>}
            <span>Şubesi değişecek: <b>{oneri.degisecek}</b></span>
          </div>
          <div className="ak-subeler">
            {oneri.subeler.map((g) => (
              <div key={g.sube} className="ak-sube">
                <div className="ak-sube-b"><b>{sinif.replace('. Sınıf', '')}-{g.sube}</b><span>{g.sayi} öğrenci</span></div>
                <div className="yp-ince">
                  {g.ic_benzerlik != null && <>İç benzerlik %{g.ic_benzerlik} · </>}
                  {Object.entries(g.cinsiyet).filter(([k]) => k !== 'belirtilmemis').map(([k, n]) => `${n} ${k === 'kadin' ? 'K' : k === 'erkek' ? 'E' : k}`).join(' / ') || '—'}
                </div>
                {g.belirgin.length > 0 && <div style={{ margin: '6px 0' }}>{g.belirgin.map((x) => <span key={x} className="ak-cip">{x}</span>)}</div>}
                <ul>
                  {g.ogrenciler.map((o) => (
                    <li key={o.id} className={o.profil ? '' : 'ak-profilsiz'}>
                      <span>{o.ad_soyad}{o.eski_sube && o.eski_sube !== g.sube && <em> ({o.eski_sube === 'Aday' ? 'aday' : `eski: ${o.eski_sube}`})</em>}</span>
                      <select aria-label="Şubeyi değiştir" value={g.sube} onChange={(e) => tasi(o.id, e.target.value)}>
                        {oneri.subeler.map((x) => <option key={x.sube}>{x.sube}</option>)}
                      </select>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
            <button className="btn" disabled={bekle} onClick={uygula}>{bekle ? <span className="spin" /> : 'Bu dağılımı uygula'}</button>
            <button className="btn sec" disabled={bekle} onClick={() => setOneri(null)}>Vazgeç</button>
            <span className="yp-ince" style={{ alignSelf: 'center' }}>Uygulamadan önce listeden elle taşıma yapabilirsiniz. İşlem kayıtlara yazılır.</span>
          </div>
        </div>
      )}
      <EtikNot />
    </div>
  )
}

// ----------------------------------------------------------------------------- aday öğrenciler
function AdayDetay({ aday, okulId, onAtandi }) {
  const [sinif, setSinif] = useState('9. Sınıf')
  const [v, setV] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  useEffect(() => { setV(null); api.adayUyumu(aday.id, sinif).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [aday.id, sinif])
  const ata = async (sube) => {
    setBekle(true); setHata(null)
    try { await api.subeDagilimiUygula(okulId, { sinif, atamalar: [{ id: aday.id, sube }] }); onAtandi?.() } catch (e) { setHata(e.detail || 'Atanamadı.') }
    setBekle(false)
  }
  return (
    <div className="yp-kutu" style={{ marginTop: 10 }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 8 }}>
        <div className="yp-kb" style={{ margin: 0 }}>{aday.ad_soyad}</div>
        <span className="yp-ince">karşılaştırılan sınıf:</span>
        <select className="yp-sec" value={sinif} onChange={(e) => setSinif(e.target.value)}>{SINIFLAR.map((s) => <option key={s}>{s}</option>)}</select>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v && !hata && <div className="bos-durum">Hesaplanıyor…</div>}
      {v?.durum === 'profil_yok' && <div className="bos-durum">Aday henüz testi çözmedi. K1 ve K2 tamamlanınca şube uyumu görünür.</div>}
      {v?.durum === 'tamam' && (
        <>
          {(v.tamamlanmamis || v.dusuk_guven) && <div className="yp-uyari">{v.tamamlanmamis ? 'Test tamamlanmadı; sonuç ön bilgidir. ' : ''}{v.dusuk_guven ? 'Güven puanı düşük.' : ''}</div>}
          <div className="yp-ince" style={{ marginBottom: 6 }}>Öne çıkan yönleri: {v.gucluler.map((g) => `${g.ad} (${g.puan})`).join(', ')}</div>
          {v.subeler.length === 0 ? <div className="bos-durum">{sinif} için profili olan şube yok ({v.sinif_ogrenci} öğrenci).</div> : (
            <table className="yp-tablo">
              <thead><tr><th>Şube</th><th>Profil uyumu</th><th>Yakın akran</th><th>Şubenin belirgin yönleri</th><th /></tr></thead>
              <tbody>
                {v.subeler.map((s, i) => (
                  <tr key={s.sube}>
                    <td><b>{sinif.replace('. Sınıf', '')}-{s.sube}</b>{i === 0 && <span className="ak-cip ak-cip-ortak" style={{ marginLeft: 6 }}>en yakın</span>}<div className="yp-ince">{s.profilli} profil</div></td>
                    <td style={{ width: '24%' }}><BenzerlikCubugu deger={s.uyum} /></td>
                    <td>{s.yakin_akran}</td>
                    <td>{s.belirgin.map((x) => <span key={x} className="ak-cip">{x}</span>)}</td>
                    <td><button className="btn sec" disabled={bekle} onClick={() => ata(s.sube)}>Bu şubeye ata</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {v.akranlar.length > 0 && (
            <>
              <div className="yp-kb" style={{ marginTop: 12 }}>En benzer 3 öğrenci ({sinif})</div>
              <table className="yp-tablo"><tbody>{v.akranlar.map((a) => <AkranSatiri key={a.id} a={a} />)}</tbody></table>
            </>
          )}
          <div className="yp-ince" style={{ marginTop: 8 }}>Not: "Profil uyumu" şubenin ortalama profiline benzerliktir. Uyum ve çeşitlilik dengesi için rehber değerlendirmesi esastır; yalnızca en yüksek uyuma göre yerleştirme, şubeleri zamanla tek tipleştirebilir.</div>
        </>
      )}
    </div>
  )
}

function Adaylar({ okulId, yenile }) {
  const [liste, setListe] = useState(null)
  const [acik, setAcik] = useState(null)
  const yukle = () => api.okulAdaylari(okulId).then(setListe).catch(() => setListe([]))
  useEffect(() => { yukle() }, [okulId])
  return (
    <div className="card" style={{ margin: 0 }}>
      <div className="ct">Aday öğrenciler</div>
      <div className="yp-ince" style={{ marginBottom: 10 }}>
        Okula kayıt için gelen öğrencileri, Öğrenciler sekmesinden sınıfı <b>"Aday"</b> olarak ekleyin (toplu yüklemede sınıf sütununa "Aday" yazmanız yeterli).
        Aday testi çözdükten sonra hangi şubenin profiline daha yakın olduğunu ve en benzer öğrencileri burada görürsünüz. Aday kendi sonucunu görür; şube karşılaştırmasını görmez.
      </div>
      {!liste ? <div className="bos-durum">Yükleniyor…</div> : liste.length === 0 ? <div className="bos-durum">Aday öğrenci yok.</div> : (
        <table className="yp-tablo">
          <thead><tr><th>Ad soyad</th><th>No</th><th>Durum</th><th /></tr></thead>
          <tbody>
            {liste.map((a) => (
              <tr key={a.id} className={acik?.id === a.id ? 'secili' : ''}>
                <td><b>{a.ad_soyad}</b><div className="yp-ince">{a.email}</div></td>
                <td>{a.ogrenci_no || '—'}</td>
                <td><DurumRozeti kod={a.durum} etiket={a.durum_etiket} /></td>
                <td><button className="btn sec" onClick={() => setAcik(acik?.id === a.id ? null : a)}>{acik?.id === a.id ? 'Kapat' : 'Şube uyumu'}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {acik && <AdayDetay key={acik.id} aday={acik} okulId={okulId} onAtandi={() => { setAcik(null); yukle(); yenile?.() }} />}
    </div>
  )
}

export default function AkranSekmesi({ okulId, ogrenciler, yenile }) {
  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <Adaylar okulId={okulId} yenile={yenile} />
      <SubeDagilimi okulId={okulId} ogrenciler={ogrenciler} yenile={yenile} />
    </div>
  )
}
