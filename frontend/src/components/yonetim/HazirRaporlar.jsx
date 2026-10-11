// [2026-10-11] Okul yetkilisi — hazır raporlar: indirmeye gerek kalmadan ekranda görülen öğrenci listeleri.
// En çok / en az giriş yapanlar, en yüksek TYT neti, netini en çok artıranlar, en çok çalışma kaydedenler,
// koçluk ve görevlerde en aktifler. Veri: GET /yonetim/okul/{id}/hazir-raporlar (app/api/hazir_raporlar.py).
// kompakt: okul ana sayfası (Özet) için ilk 5 satır, dönem seçimi; tam: Raporlar sayfası (10 satır + sınıf filtresi + CSV).
// İsme tıklayınca öğrencinin detay penceresi açılır (Öğrenciler sekmesi derin bağlantısı).
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { csvIndir } from '../istatistik'

const DONEM_AD = { 7: 'Son 7 gün', 30: 'Son 30 gün', 90: 'Son 3 ay', 365: 'Son 1 yıl' }

function Liste({ l, kompakt, onAc }) {
  const satirlar = kompakt ? l.satirlar.slice(0, 5) : l.satirlar
  return (
    <div className="card hr-kart">
      <div className="hr-bas">
        <span className="hr-ikon" aria-hidden="true">{l.ikon}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="hr-baslik">{l.baslik}</div>
          <div className="hr-aciklama">{l.aciklama}</div>
        </div>
        {!kompakt && l.satirlar.length > 0 && (
          <button type="button" className="hr-csv" title="Excel'de açılabilir CSV olarak indir"
            onClick={() => csvIndir({ sutunlar: ['Sıra', 'Öğrenci', 'Sınıf', l.birim, 'Not'], satirlar: l.satirlar.map((s, i) => [i + 1, s.ad, s.sinif, s.deger, s.ek || '']) }, l.baslik)}>⬇ CSV</button>
        )}
      </div>
      {satirlar.length === 0 ? <div className="hr-bos">{l.bos}</div> : (
        <ol className="hr-liste">
          {satirlar.map((s, i) => (
            <li key={s.id}>
              <span className="hr-sira">{i + 1}</span>
              <button type="button" className="hr-ad" onClick={() => onAc(s.id)} title="Öğrenci detayını aç">{s.ad}</button>
              <span className="hr-sinif">{s.sinif}</span>
              <span className="hr-deger"><b>{s.deger}</b> {l.birim}</span>
              {s.ek && !kompakt && <span className="hr-ek">{s.ek}</span>}
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}

export default function HazirRaporlar({ okulId, kompakt = false, onTumu }) {
  const navigate = useNavigate()
  const [gun, setGun] = useState(30)
  const [filtre, setFiltre] = useState({ sinif: '', sube: '' })
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    setHata(null)
    api.hazirRaporlar(okulId, { gun, ...filtre, adet: kompakt ? 5 : 10 })
      .then(setV).catch((e) => setHata(e.detail || 'Raporlar yüklenemedi.'))
  }, [okulId, gun, filtre, kompakt])

  const ac = (id) => navigate(`/admin/okul/${okulId}?sekme=ogrenciler&ogrenci=${id}`)
  const subeler = v?.secenekler?.find((s) => s.sinif === filtre.sinif)?.subeler || []

  return (
    <section className="hr">
      <div className="hr-ust">
        <div style={{ flex: 1, minWidth: 220 }}>
          <div className="ct" style={{ margin: 0 }}>📋 Hazır raporlar</div>
          {v && (
            <div className="hr-ozet">
              {v.kapsam} · {v.ogrenci_sayisi} öğrenci · {DONEM_AD[v.gun]} içinde <b>{v.donemde_giris_yapan}</b> öğrenci giriş yaptı
              {v.hic_girmeyen > 0 && <> · <b className="hr-uyari">{v.hic_girmeyen}</b> öğrenci hiç giriş yapmadı</>}
              {v.girmeyen_14_gun > 0 && <> · <b>{v.girmeyen_14_gun}</b> öğrenci 14 günden uzun süredir girmiyor</>}
            </div>
          )}
        </div>
        <div className="hr-filtre">
          {!kompakt && v?.secenekler?.length > 0 && (
            <>
              <select value={filtre.sinif} onChange={(e) => setFiltre({ sinif: e.target.value, sube: '' })} aria-label="Sınıf">
                <option value="">Tüm sınıflar</option>
                {v.secenekler.map((s) => <option key={s.sinif} value={s.sinif}>{s.sinif}</option>)}
              </select>
              {subeler.length > 0 && (
                <select value={filtre.sube} onChange={(e) => setFiltre((f) => ({ ...f, sube: e.target.value }))} aria-label="Şube">
                  <option value="">Tüm şubeler</option>
                  {subeler.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              )}
            </>
          )}
          <select value={gun} onChange={(e) => setGun(Number(e.target.value))} aria-label="Dönem">
            {(v?.donemler || [7, 30, 90, 365]).map((d) => <option key={d} value={d}>{DONEM_AD[d]}</option>)}
          </select>
          {kompakt && onTumu && <button type="button" className="ak-link" onClick={onTumu}>Tüm raporlar →</button>}
        </div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v && !hata && <div className="bos-durum">Yükleniyor…</div>}
      {v && (
        <div className={`hr-izgara${kompakt ? ' kompakt' : ''}`}>
          {v.listeler.map((l) => <Liste key={l.kod} l={l} kompakt={kompakt} onAc={ac} />)}
        </div>
      )}
      {v && !kompakt && (
        <div className="yp-ince" style={{ marginTop: 10, lineHeight: 1.6 }}>
          Giriş sayısı, sisteme şifreyle yapılan başarılı girişlerdir; "beni hatırla" ile açık kalan oturumlar ayrıca sayılmaz.
          Sıralamalar yalnızca katılım ve deneme netine göre yapılır; kişilik, değer ve ilgi sonuçları sıralamada kullanılmaz.
          Test hesapları hariçtir.
        </div>
      )}
    </section>
  )
}
