// [2026-10-12] Yeni eğitim yılı — toplu sınıf atlatma (okul yetkilisi / süper admin).
// 9 → 10, 10 → 11, 11 → 12, 12 → Mezun; şube harfi korunur. Seçili öğrenciler (sınıf tekrarı) sınıfında kalır.
// İşlem 30 gün içinde "Geri al" ile geri alınabilir (sonradan sınıfı elle değiştirilen öğrenciler hariç).
// Veri: GET/POST /yonetim/okul/{id}/sinif-atlat, POST /yonetim/toplu-islem/{id}/geri-al (app/api/toplu_ogrenci.py)
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere, tarih } from './ortak'

export default function SinifAtlatPenceresi({ okulId, haric = [], haricAdlar = [], onKapat, onBitti }) {
  const [v, setV] = useState(null)
  const [secili, setSecili] = useState(new Set(['9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf']))
  const [onay, setOnay] = useState(false)
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const [sonuc, setSonuc] = useState(null)

  const yukle = () => api.sinifAtlatOnizle(okulId, haric).then(setV).catch((e) => setHata(e.detail || 'Önizleme yüklenemedi.'))
  useEffect(() => { yukle() }, [okulId]) // eslint-disable-line react-hooks/exhaustive-deps

  const toplam = v ? v.gecisler.filter((g) => secili.has(g.eski)).reduce((a, g) => a + g.sayi, 0) : 0
  const degistir = (s) => setSecili((x) => { const y = new Set(x); y.has(s) ? y.delete(s) : y.add(s); return y })

  async function uygula() {
    setBekle(true); setHata(null)
    try {
      const r = await api.sinifAtlat(okulId, { siniflar: [...secili], haric, onay: true })
      setSonuc(r); onBitti?.()
    } catch (e) { setHata(e.detail || 'İşlem yapılamadı.') } finally { setBekle(false) }
  }
  async function geriAl(id) {
    setBekle(true); setHata(null)
    try {
      const r = await api.topluIslemGeriAl(id)
      setSonuc({ geriAlindi: r }); onBitti?.(); yukle()
    } catch (e) { setHata(e.detail || 'Geri alınamadı.') } finally { setBekle(false) }
  }

  if (sonuc) {
    return (
      <Pencere baslik="Sınıf atlatma" onKapat={onKapat} alt={<button className="btn" onClick={onKapat}>Kapat</button>}>
        {sonuc.geriAlindi ? (
          <div className="yp-uyari-yesil">
            {`Sınıf atlatma geri alındı: ${sonuc.geriAlindi.donen} öğrenci eski sınıfına döndü.`}
            {sonuc.geriAlindi.atlanan > 0 && <div className="yp-ince">{`${sonuc.geriAlindi.atlanan} öğrencinin sınıfı sonradan değiştirildiği için dokunulmadı.`}</div>}
          </div>
        ) : (
          <>
            <div className="yp-uyari-yesil">{`${sonuc.sayi} öğrencinin sınıfı bir üst sınıfa geçirildi.`}</div>
            <div className="yp-ince" style={{ marginTop: 10 }}>{`Bir hata olduysa ${sonuc.geri_alma_gun} gün içinde bu pencereden geri alabilirsiniz.`}</div>
            <button className="btn sec" style={{ marginTop: 10 }} disabled={bekle} onClick={() => geriAl(sonuc.islem_id)}>↩ Geri al</button>
          </>
        )}
        {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}
      </Pencere>
    )
  }

  return (
    <Pencere genis baslik="🎓 Yeni eğitim yılı: sınıf atlat" altBaslik="Okuldaki bütün öğrenciler bir üst sınıfa geçer; şube harfleri korunur."
      onKapat={onKapat}
      alt={<>
        <button className="btn sec" onClick={onKapat}>Vazgeç</button>
        <button className="btn" disabled={bekle || !onay || toplam === 0} onClick={uygula}>{`${toplam} öğrencinin sınıfını atlat`}</button>
      </>}>
      {hata && <div className="auth-error">{hata}</div>}
      {!v ? <div className="bos-durum yukleniyor">Yükleniyor…</div> : (
        <>
          {v.uyari && <div className="yp-uyari">⚠️ {v.uyari}</div>}
          <table className="yp-tablo sa-tablo">
            <thead><tr><th style={{ width: 30 }} /><th>Şu anki sınıf</th><th>Geçeceği sınıf</th><th style={{ textAlign: 'right' }}>Öğrenci</th><th style={{ textAlign: 'right' }}>Sınıfında kalan</th></tr></thead>
            <tbody>
              {v.gecisler.map((g) => (
                <tr key={g.eski} className={secili.has(g.eski) ? '' : 'sa-pasif'}>
                  <td><input type="checkbox" checked={secili.has(g.eski)} onChange={() => degistir(g.eski)} aria-label={g.eski} /></td>
                  <td>{g.eski}</td>
                  <td>→ <b>{g.yeni}</b></td>
                  <td style={{ textAlign: 'right' }}><b>{g.sayi}</b></td>
                  <td style={{ textAlign: 'right' }} className="yp-ince">{g.kalan || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {v.degismeyen.length > 0 && (
            <div className="yp-ince" style={{ marginTop: 8 }}>
              Değişmeyenler: {v.degismeyen.map((d) => `${d.sinif} (${d.sayi})`).join(', ')}
            </div>
          )}
          <div className="sa-bilgi">
            <div className="sa-baslik">Sınıf tekrarı yapacak öğrenciler</div>
            {haric.length > 0 ? (
              <>
                <div className="yp-ince">{`Öğrenci listesinde seçtiğiniz ${haric.length} öğrenci sınıfında kalacak:`}</div>
                <div className="sa-adlar">{haricAdlar.slice(0, 30).join(', ')}{haricAdlar.length > 30 ? '…' : ''}</div>
              </>
            ) : (
              <div className="yp-ince">Sınıfta kalacak öğrenci varsa bu pencereyi kapatın, öğrenci listesinde onları seçin ve sınıf atlatmayı yeniden açın.</div>
            )}
          </div>
          <ul className="sa-liste">
            <li>12. sınıflar “Mezun” olur; hesapları açık kalır. İsterseniz sonra “Mezun” filtresiyle seçip silebilirsiniz.</li>
            <li>Değerlendirme sonuçları, denemeler ve diğer kayıtlar değişmez.</li>
            <li>Test hesapları ve “Aday” öğrenciler bu işleme dahil değildir.</li>
            <li>{`İşlem ${v.geri_alma_gun} gün içinde geri alınabilir.`}</li>
          </ul>
          {v.son_islem && (
            <div className="sa-son">
              {`Son sınıf atlatma: ${tarih(v.son_islem.zaman)} · ${v.son_islem.sayi} öğrenci · ${v.son_islem.yapan || ''}`}
              {v.son_islem.geri_alindi && <span className="yp-ince"> · geri alındı</span>}
              {v.son_islem.geri_alinabilir && <button className="yp-mini" style={{ marginLeft: 8 }} disabled={bekle} onClick={() => geriAl(v.son_islem.id)}>↩ Geri al</button>}
            </div>
          )}
          <label className="sa-onay">
            <input type="checkbox" checked={onay} onChange={(e) => setOnay(e.target.checked)} />
            <span>Öğrencilerin yeni eğitim yılına geçtiğini ve sınıf atlatmanın yapılacağını onaylıyorum.</span>
          </label>
        </>
      )}
    </Pencere>
  )
}
