// [2026-10-10] Kulüp katılma talepleri (onay / red), üye listesi ve kulüp duyuruları / etkinlikleri — okul yetkilisi.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere, tarih } from './ortak'

export function KatilmaTalepleri({ okulId, onDegisti }) {
  const [v, setV] = useState(null)
  const [gecmis, setGecmis] = useState(false)
  const [yanit, setYanit] = useState({})
  const [bekle, setBekle] = useState(null)
  const [hata, setHata] = useState(null)
  const yukle = useCallback(() => api.kulupTalepleri(okulId, gecmis ? 'hepsi' : 'bekliyor').then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [okulId, gecmis])
  useEffect(() => { yukle() }, [yukle])
  async function karar(t, k) {
    setBekle(t.id); setHata(null)
    try { await api.kulupKarar(t.id, k, yanit[t.id] || null); await yukle(); onDegisti?.() } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(null) }
  }
  if (!v) return null
  const DURUM = { bekliyor: '⏳ Bekliyor', onaylandi: '✅ Onaylandı', reddedildi: '✖ Reddedildi', ayrildi: '↩ Ayrıldı' }
  return (
    <div className={`card kt-talepler${v.bekleyen ? ' var' : ''}`} style={{ margin: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <div className="ct" style={{ margin: 0, marginRight: 'auto' }}>🙋 Katılma talepleri {v.bekleyen > 0 && <span className="kt-sayi">{v.bekleyen} bekliyor</span>}</div>
        <label className="yp-ince" style={{ display: 'flex', gap: 6, alignItems: 'center' }}><input type="checkbox" checked={gecmis} onChange={(e) => setGecmis(e.target.checked)} /> Sonuçlananları da göster</label>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {v.talepler.length === 0 ? <div className="bos-durum" style={{ padding: 12 }}>{gecmis ? 'Henüz talep yok.' : 'Bekleyen talep yok.'}</div> : (
        <table className="yp-tablo">
          <thead><tr><th>Öğrenci</th><th>Kulüp</th><th>Öğrencinin notu</th><th>Tarih</th><th style={{ width: '34%' }}>Yanıt / karar</th></tr></thead>
          <tbody>
            {v.talepler.map((t) => (
              <tr key={t.id}>
                <td><b>{t.ogrenci?.ad_soyad}</b><div className="yp-ince">{t.ogrenci?.sinif || '—'}</div></td>
                <td>{t.kulup}</td>
                <td className="yp-ince">{t.mesaj || '—'}</td>
                <td className="yp-ince">{tarih(t.talep_zamani)}</td>
                <td>
                  {t.durum === 'bekliyor' ? (
                    <div className="kt-karar">
                      <input className="auth-input" maxLength={300} placeholder="Öğrenciye not (isteğe bağlı): buluşma yeri, saat…" value={yanit[t.id] || ''} onChange={(e) => setYanit({ ...yanit, [t.id]: e.target.value })} />
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button className="yp-mini yesil" disabled={bekle === t.id} onClick={() => karar(t, 'onayla')}>✓ Onayla</button>
                        <button className="yp-mini kirmizi" disabled={bekle === t.id} onClick={() => karar(t, 'reddet')}>✖ Reddet</button>
                      </div>
                    </div>
                  ) : <span className="yp-ince">{DURUM[t.durum]}{t.karar_veren ? ` · ${t.karar_veren}` : ''}{t.yanit ? ` — “${t.yanit}”` : ''}</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export function UyelerPenceresi({ kulup, onKapat, onDegisti }) {
  const [v, setV] = useState(null)
  const [cikar, setCikar] = useState(null)
  const yukle = useCallback(() => api.kulupUyeleri(kulup.id).then(setV), [kulup.id])
  useEffect(() => { yukle() }, [yukle])
  return (
    <Pencere baslik={`👥 ${kulup.ad}`} altBaslik="Onaylı üyeler" onKapat={onKapat}>
      {!v ? <div className="bos-durum">Yükleniyor…</div> : v.uyeler.length === 0 ? <div className="bos-durum">Henüz üye yok.</div> : (
        <table className="yp-tablo">
          <thead><tr><th>Öğrenci</th><th>Sınıf</th><th>Üyelik</th><th /></tr></thead>
          <tbody>{v.uyeler.map((u) => (
            <tr key={u.id}><td><b>{u.ogrenci?.ad_soyad}</b></td><td>{u.ogrenci?.sinif || '—'}</td><td className="yp-ince">{tarih(u.karar_zamani)}</td>
              <td>{cikar === u.id ? (
                <><button className="yp-mini kirmizi" onClick={async () => { await api.kulupKarar(u.id, 'cikar'); setCikar(null); yukle(); onDegisti?.() }}>Evet, çıkar</button>{' '}
                  <button className="yp-mini" onClick={() => setCikar(null)}>Vazgeç</button></>
              ) : <button className="yp-mini" onClick={() => setCikar(u.id)}>Kulüpten çıkar</button>}</td></tr>
          ))}</tbody>
        </table>
      )}
    </Pencere>
  )
}

const BOS_DUYURU = { tur: 'duyuru', baslik: '', metin: '', tarih: '', saat: '', yer: '', herkese: false }

export function DuyurularPenceresi({ kulup, onKapat }) {
  const [v, setV] = useState(null)
  const [f, setF] = useState(BOS_DUYURU)
  const [duzenId, setDuzenId] = useState(null)
  const [silId, setSilId] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const yukle = useCallback(() => api.kulupDuyurulari(kulup.id).then(setV), [kulup.id])
  useEffect(() => { yukle() }, [yukle])
  async function kaydet(e) {
    e.preventDefault(); setHata(null); setBekle(true)
    const veri = { ...f, tarih: f.tarih || null, saat: f.saat || null, yer: f.yer || null, metin: f.metin || null }
    try {
      if (duzenId) await api.kulupDuyuruDuzenle(duzenId, veri); else await api.kulupDuyuruEkle(kulup.id, veri)
      setF(BOS_DUYURU); setDuzenId(null); await yukle()
    } catch (er) { setHata(Array.isArray(er.detail) ? 'Başlık en az 2 karakter olmalı.' : (er.detail || 'Kaydedilemedi.')) } finally { setBekle(false) }
  }
  return (
    <Pencere baslik={`📣 ${kulup.ad}`} altBaslik="Duyurular ve etkinlikler — üyeler görür; “Okula açık” işaretlenirse okuldaki tüm öğrenciler görür" onKapat={onKapat} genis>
      <form className="kd-form" onSubmit={kaydet}>
        <div className="nt-secim">
          {[['duyuru', '📣 Duyuru'], ['etkinlik', '📅 Etkinlik']].map(([k, a]) => <button type="button" key={k} className={f.tur === k ? 'secili' : ''} onClick={() => setF({ ...f, tur: k })}>{a}</button>)}
        </div>
        <input className="auth-input" maxLength={120} placeholder={f.tur === 'etkinlik' ? 'Etkinlik adı (ör. Robot yarışması hazırlığı)' : 'Duyuru başlığı'} value={f.baslik} onChange={(e) => setF({ ...f, baslik: e.target.value })} />
        {f.tur === 'etkinlik' && (
          <div className="kd-form-satir">
            <label>Tarih<input type="date" className="auth-input" value={f.tarih || ''} onChange={(e) => setF({ ...f, tarih: e.target.value })} /></label>
            <label>Saat<input className="auth-input" maxLength={20} placeholder="15:30" value={f.saat || ''} onChange={(e) => setF({ ...f, saat: e.target.value })} /></label>
            <label style={{ flex: 1 }}>Yer<input className="auth-input" maxLength={80} placeholder="Fizik laboratuvarı" value={f.yer || ''} onChange={(e) => setF({ ...f, yer: e.target.value })} /></label>
          </div>
        )}
        <textarea className="auth-input" rows={3} maxLength={1000} placeholder="Ayrıntı (isteğe bağlı)" value={f.metin || ''} onChange={(e) => setF({ ...f, metin: e.target.value })} />
        <label className="yp-ince" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <input type="checkbox" checked={f.herkese} onChange={(e) => setF({ ...f, herkese: e.target.checked })} /> Okula açık (üye olmayan öğrenciler de görsün — ör. yeni üye alımı)
        </label>
        {hata && <div className="auth-error" style={{ margin: 0 }}>{hata}</div>}
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn" disabled={bekle || f.baslik.trim().length < 2 || (f.tur === 'etkinlik' && !f.tarih)}>{duzenId ? 'Değişiklikleri kaydet' : 'Yayınla'}</button>
          {duzenId && <button type="button" className="btn sec" onClick={() => { setDuzenId(null); setF(BOS_DUYURU) }}>Vazgeç</button>}
        </div>
      </form>
      <div className="ct" style={{ marginTop: 16 }}>Yayınlananlar</div>
      {!v ? <div className="bos-durum">Yükleniyor…</div> : v.duyurular.length === 0 ? <div className="bos-durum">Henüz duyuru yok.</div> : (
        <div className="kd-liste">
          {v.duyurular.map((d) => (
            <div key={d.id} className={`kd-satir ${d.tur}`}>
              <div className="kd-tarih">{d.tur === 'etkinlik' ? <><b>{new Date(d.tarih).getDate()}</b><span>{new Date(d.tarih).toLocaleDateString('tr-TR', { month: 'short' })}</span></> : '📣'}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="kd-baslik">{d.baslik} {d.herkese && <span className="kd-herkese">Okula açık</span>}</div>
                {d.tur === 'etkinlik' && <div className="yp-ince">{[d.saat && `⏰ ${d.saat}`, d.yer && `📍 ${d.yer}`].filter(Boolean).join(' · ')}</div>}
                {d.metin && <div className="kd-metin">{d.metin}</div>}
                <div className="yp-ince">{tarih(d.olusturulma_zamani)} · {d.olusturan}</div>
              </div>
              <div style={{ display: 'flex', gap: 4, alignItems: 'flex-start' }}>
                {silId === d.id ? (
                  <><button className="yp-mini kirmizi" onClick={async () => { await api.kulupDuyuruSil(d.id); setSilId(null); yukle() }}>Sil</button><button className="yp-mini" onClick={() => setSilId(null)}>Vazgeç</button></>
                ) : (
                  <><button className="yp-mini" onClick={() => { setDuzenId(d.id); setF({ ...BOS_DUYURU, ...d, tarih: d.tarih || '', saat: d.saat || '', yer: d.yer || '', metin: d.metin || '' }) }}>Düzenle</button>
                    <button className="yp-mini" onClick={() => setSilId(d.id)}>Sil</button></>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Pencere>
  )
}
