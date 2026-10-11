// [2026-10-10] Okul paneli → Mezunlar → "Mezun hikâyeleri": okulun gerçek mezunlarının anlatıları (İş Hayatı → Mezunlardan sekmesinde görünür).
// Yalnızca okul yetkilisi ekler/düzenler; mezunun açık rızası ve rıza tarihi zorunlu. Uçlar: app/api/is_hayati_mezun.py.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere } from './ortak'

const basHarf = (ad) => (ad || '').replace(/\./g, ' ').split(/\s+/).filter(Boolean).map((p) => `${p[0].toLocaleUpperCase('tr-TR')}.`).join(' ') || 'Mezun'
const bugun = () => new Date().toISOString().slice(0, 10)

function HikayeFormu({ v, okulId, mevcut, onKapat }) {
  const [f, setF] = useState(() => (mevcut
    ? { ...mevcut, bolum_id: mevcut.bolum_id || '', bolum_ad: mevcut.bolum_ad || '', universite: mevcut.universite || '', su_anki_is: mevcut.su_anki_is || '' }
    : { mezun_ad: '', ad_bicimi: 'bas_harf', mezuniyet_yili: new Date().getFullYear() - 5, bolum_id: '', bolum_ad: '', universite: '', su_anki_is: '', cevaplar: {}, riza_alindi: false, riza_tarihi: bugun(), durum: 'taslak' }))
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const s = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const doluSoru = v.sorular.filter((q) => (f.cevaplar[q.kod] || '').trim()).length
  async function kaydet() {
    setHata(null); setBekle(true)
    const govde = { mezun_ad: f.mezun_ad, ad_bicimi: f.ad_bicimi, mezuniyet_yili: Number(f.mezuniyet_yili), bolum_id: f.bolum_id ? Number(f.bolum_id) : null,
      bolum_ad: f.bolum_ad || null, universite: f.universite || null, su_anki_is: f.su_anki_is || null, cevaplar: f.cevaplar,
      riza_alindi: f.riza_alindi, riza_tarihi: f.riza_tarihi, durum: f.durum }
    try {
      if (mevcut) await api.isHayatiMezunHikayesiDuzenle(okulId, mevcut.id, govde); else await api.isHayatiMezunHikayesiEkle(okulId, govde)
      onKapat(true)
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  return (
    <Pencere genis baslik={mevcut ? 'Mezun hikâyesini düzenle' : 'Mezun hikâyesi ekle'} altBaslik="Öğrenciler bu metni İş Hayatı → Mezunlardan sekmesinde okur." onKapat={() => onKapat(false)}
      alt={<><button className="btn sec" onClick={() => onKapat(false)}>Vazgeç</button>
        <button className="btn" disabled={bekle || !f.riza_alindi || f.mezun_ad.trim().length < 2 || !f.riza_tarihi} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Kaydet'}</button></>}>
      <div className="pf-alanlar">
        <label><span>Mezunun adı soyadı</span><input className="auth-input" maxLength={120} value={f.mezun_ad} onChange={s('mezun_ad')} /></label>
        <label><span>Öğrencilere nasıl görünsün? <small>(mezunun tercihi)</small></span>
          <select className="auth-input" value={f.ad_bicimi} onChange={s('ad_bicimi')}>
            <option value="bas_harf">Yalnızca baş harfler ({basHarf(f.mezun_ad)})</option>
            <option value="tam">Tam adı ({f.mezun_ad || 'Ad Soyad'})</option>
          </select>
        </label>
        <label><span>Mezuniyet yılı</span><input className="auth-input" type="number" min="1950" max={new Date().getFullYear()} value={f.mezuniyet_yili} onChange={s('mezuniyet_yili')} /></label>
        <label><span>Okuduğu bölüm</span>
          <select className="auth-input" value={f.bolum_id} onChange={s('bolum_id')}><option value="">— seç (eşleştirme için önerilir) —</option>{v.bolumler.map((b) => <option key={b.id} value={b.id}>{b.ad}</option>)}</select>
        </label>
        <label><span>Bölüm adı <small>(listede yoksa ya da farklı yazılsın istiyorsanız)</small></span><input className="auth-input" maxLength={160} value={f.bolum_ad} onChange={s('bolum_ad')} /></label>
        <label><span>Üniversite</span><input className="auth-input" maxLength={160} value={f.universite} onChange={s('universite')} /></label>
        <label className="genis"><span>Şu anki işi</span><input className="auth-input" maxLength={160} value={f.su_anki_is} onChange={s('su_anki_is')} placeholder="ör. Bir hastanede acil servis hemşiresi" /></label>
        {v.sorular.map((q) => (
          <label key={q.kod} className="genis"><span>{q.soru} <small>{q.ipucu}</small></span>
            <textarea className="auth-input" rows={3} maxLength={2500} value={f.cevaplar[q.kod] || ''} onChange={(e) => setF({ ...f, cevaplar: { ...f.cevaplar, [q.kod]: e.target.value } })} />
          </label>
        ))}
        <div className="genis yp-ince">Metni mezunun kendi sözleriyle yazın; düzeltme yaptıysanız son hâlini mezuna gösterin. Kişisel iletişim bilgisi (telefon, adres, sosyal medya) eklemeyin.</div>
        <div className="genis mh-riza">
          <label className="pf-onay" style={{ marginTop: 0 }}>
            <input type="checkbox" checked={f.riza_alindi} onChange={(e) => setF({ ...f, riza_alindi: e.target.checked })} />
            <span><b>Mezunun bu metnin okul öğrencilerine gösterilmesine açık rızası alınmıştır.</b> (zorunlu)</span>
          </label>
          <label style={{ maxWidth: 220, marginTop: 8 }}><span>Rıza tarihi</span><input className="auth-input" type="date" max={bugun()} value={f.riza_tarihi} onChange={s('riza_tarihi')} /></label>
          <div className="yp-ince" style={{ marginTop: 6 }}>Rıza, mezunun adı ve tarihiyle birlikte kaydedilir; işlem denetim kaydına yazılır. Mezun rızasını geri çekerse hikâyeyi kaldırın.</div>
        </div>
        <div className="genis eu-filtre" role="radiogroup" aria-label="Durum" style={{ marginBottom: 0 }}>
          <button type="button" className={f.durum === 'taslak' ? 'secili' : ''} onClick={() => setF({ ...f, durum: 'taslak' })}>Taslak (öğrenciler görmez)</button>
          <button type="button" className={f.durum === 'yayinda' ? 'secili' : ''} onClick={() => setF({ ...f, durum: 'yayinda' })}>Yayında</button>
          {f.durum === 'yayinda' && doluSoru < 2 && <span className="yp-ince">Yayınlamak için en az iki soruyu cevaplayın.</span>}
        </div>
      </div>
      {hata && <div className="auth-error" style={{ marginTop: 12 }}>{hata}</div>}
    </Pencere>
  )
}

export default function MezunHikayeleriYonetim({ okulId }) {
  const [v, setV] = useState(null)
  const [form, setForm] = useState(null)
  const [silOnay, setSilOnay] = useState(null)
  const [hata, setHata] = useState(null)
  const yukle = useCallback(() => api.isHayatiMezunHikayeleriOkul(okulId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [okulId])
  useEffect(() => { yukle() }, [yukle])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  async function durumDegistir(h) {
    setHata(null)
    try { await api.isHayatiMezunHikayesiDuzenle(okulId, h.id, { ...h, durum: h.durum === 'yayinda' ? 'taslak' : 'yayinda' }); yukle() } catch (e) { setHata(e.detail || 'Değiştirilemedi.') }
  }
  const yayinda = v.hikayeler.filter((h) => h.durum === 'yayinda').length
  return (
    <>
      <div className="rh-ust">
        <div className="yp-ince" style={{ maxWidth: 760, lineHeight: 1.6 }}>
          Mezunlarınızın meslek hayatını kendi sözleriyle anlattığı hikâyeler, öğrencilerinizin İş Hayatı sayfasında (<b>Mezunlardan</b> sekmesi) görünür;
          öğrencinin seçtiği bölümle eşleşenler önce gelir. Yalnızca okulunuzun <b>gerçek mezunları</b> ve <b>açık rızaları</b> alınarak eklenmelidir.
        </div>
        {v.yazabilir && <button className="btn" onClick={() => setForm({})}>+ Hikâye ekle</button>}
      </div>
      {!v.yazabilir && <div className="yp-uyari">Mezun hikâyelerini yalnızca okulun kendi yetkilileri ekleyip düzenleyebilir (sahte tanıklık önlemi). Bu ekranda yalnızca görüntüleme ve uygunsuz içeriği kaldırma yapılabilir.</div>}
      {hata && <div className="auth-error">{hata}</div>}
      <div className="card">
        <div className="ct">Mezun hikâyeleri · {yayinda} yayında / {v.hikayeler.length}</div>
        {v.hikayeler.length === 0 ? <div className="bos-durum">Henüz hikâye yok. Mezunlarınızdan birine "İşinde gerçekte ne yapıyorsun?" diye sorarak başlayabilirsiniz.</div> : (
          <table className="yp-tablo">
            <thead><tr><th>Mezun</th><th>Yıl</th><th>Bölüm / üniversite</th><th>Şu anki işi</th><th>Rıza</th><th>Durum</th><th /></tr></thead>
            <tbody>
              {v.hikayeler.map((h) => (
                <tr key={h.id}>
                  <td>{h.mezun_ad}<div className="yp-ince">Görünen: {h.gorunen_ad}</div></td>
                  <td>{h.mezuniyet_yili}</td>
                  <td>{[h.bolum_ad, h.universite].filter(Boolean).join(' — ') || '—'}</td>
                  <td>{h.su_anki_is || '—'}</td>
                  <td className="yp-ince">{h.riza_tarihi ? new Date(h.riza_tarihi).toLocaleDateString('tr-TR') : '—'}{h.riza_kaydeden && <div>{h.riza_kaydeden}</div>}</td>
                  <td>{h.durum === 'yayinda' ? <b style={{ color: 'var(--gr)' }}>Yayında</b> : <span className="yp-ince">Taslak</span>}</td>
                  <td className="tr-islem">
                    {v.yazabilir && <button className="yp-mini" onClick={() => durumDegistir(h)}>{h.durum === 'yayinda' ? 'Yayından al' : 'Yayınla'}</button>}
                    {v.yazabilir && <button className="yp-mini" onClick={() => setForm({ mevcut: h })} aria-label="Düzenle">✎</button>}
                    {silOnay === h.id
                      ? <button className="yp-mini yp-tehlike" onClick={async () => { setSilOnay(null); try { await api.isHayatiMezunHikayesiSil(okulId, h.id); yukle() } catch (e) { setHata(e.detail || 'Kaldırılamadı.') } }}>Kaldır</button>
                      : <button className="yp-mini" onClick={() => setSilOnay(h.id)} aria-label="Kaldır">🗑</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {form && <HikayeFormu v={v} okulId={okulId} mevcut={form.mevcut} onKapat={(d) => { setForm(null); if (d) yukle() }} />}
    </>
  )
}
