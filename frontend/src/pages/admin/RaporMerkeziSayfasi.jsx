// [2026-10-10] Süper admin — Rapor Merkezi: indirilebilir tüm raporlar tek yerde.
// Okul raporları: GET /yonetim/okul/{id}/rapor (app/api/raporlar.py), giriş listesi ve görüşmeler (okul_yonetimi / rehberlik);
// sistem geneli: istatistik Excel'i, okul karşılaştırması, anket psikometrisi, audit log (app/api/sistem_istatistik.py).
// Öğrenci bazlı raporlar okul panelinde öğrencinin detayından alınır.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import RaporDugmeleri from '../../components/RaporDugmeleri'
import { base64Indir } from '../../components/yonetim/ortak'

const TOPLU = [
  ['toplu_veli', '👪 Veli raporları'],
  ['toplu_ogrenci', '📘 Öğrenci raporları'],
  ['toplu_yonetici', '🗂️ Yönetim (ayrıntılı) raporları'],
  ['toplu_sinif_ogretmeni', '🧑‍🏫 Sınıf öğretmeni raporları'],
]
const subeAdi = (s) => s.etiket || [s.sinif, s.sube].filter(Boolean).join('-')

function RaporKarti({ ikon, baslik, aciklama, children, secenekler }) {
  return (
    <section className="card rm-kart">
      <div className="rm-ust">
        <span className="rm-ikon" aria-hidden="true">{ikon}</span>
        <div>
          <h3 className="rm-baslik">{baslik}</h3>
          <p className="rm-aciklama">{aciklama}</p>
        </div>
      </div>
      {children && <div className="rm-ayar">{children}</div>}
      <RaporDugmeleri baslik={null} secenekler={secenekler} />
    </section>
  )
}

export default function RaporMerkeziSayfasi() {
  const [okullar, setOkullar] = useState([])
  const [okulId, setOkulId] = useState('')
  const [ozet, setOzet] = useState(null)
  const [ozetHata, setOzetHata] = useState(null)
  const [netler, setNetler] = useState(true)
  const [sinif, setSinif] = useState('')
  const [sube, setSube] = useState('')
  const [topluKapsam, setTopluKapsam] = useState('')
  const [topluTur, setTopluTur] = useState('toplu_veli')
  const [donem, setDonem] = useState('tum')
  const [auditGun, setAuditGun] = useState(90)

  useEffect(() => { api.okullariListele().then((l) => setOkullar(l || [])).catch(() => setOkullar([])) }, [])
  useEffect(() => {
    setOzet(null); setOzetHata(null); setSinif(''); setSube(''); setTopluKapsam('')
    if (okulId === '') return
    api.okulOzeti(okulId).then(setOzet).catch((e) => setOzetHata(e.detail || 'Okul bilgisi alınamadı.'))
  }, [okulId])

  const okulAdi = okulId === '0' ? 'Okul harici öğrenciler' : okullar.find((o) => String(o.id) === okulId)?.ad
  const moduller = ozet?.moduller || []
  const netVar = moduller.includes('net_takibi')
  const net = netler && netVar
  const siniflar = (ozet?.siniflar || []).filter((s) => s.sinif && s.sinif !== 'Belirtilmedi')
  const subeler = (ozet?.subeler || []).filter((s) => s.sinif && s.sinif !== 'Belirtilmedi')
  const secSube = subeler.find((s) => `${s.sinif}|${s.sube}` === sube)
  const topluSec = topluKapsam ? (() => { const [sf, sb] = topluKapsam.split('|'); return { sinif: sf, sube: sb || null } })() : null
  const topluSayi = topluSec ? (topluSec.sube ? subeler.find((s) => s.sinif === topluSec.sinif && s.sube === topluSec.sube)?.ogrenci
    : siniflar.find((s) => s.sinif === topluSec.sinif)?.ogrenci) : null
  // Seçim yapılmadan basılırsa düğmenin yanında uyarı (RaporDugmeleri hata olarak gösterir)
  const sart = (kosul, metin, fn) => () => (kosul ? fn() : Promise.reject({ detail: metin }))

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Rapor Merkezi</div>
        <div className="ps">Sistemdeki tüm indirilebilir raporlar. Her indirme Audit Log’a yazılır. Toplu raporlarda 5’ten az öğrenciye dayanan toplu değerler gizlenir.</div>
      </div>

      <div className="sis-bolum-baslik"><h2>Okul raporları</h2><p>Önce okulu seçin; sınıf ve şube listesi okulun kayıtlarından gelir.</p></div>
      <div className="sis-filtreler">
        <select className="yp-sec" aria-label="Okul" value={okulId} onChange={(e) => setOkulId(e.target.value)} style={{ minWidth: 240 }}>
          <option value="">Okul seçin…</option>
          {okullar.map((o) => <option key={o.id} value={String(o.id)}>{o.ad}{o.aktif_mi === false ? ' (pasif)' : ''}</option>)}
          <option value="0">Okul harici öğrenciler</option>
        </select>
        {ozet && <span className="yp-ince">{ozet.toplam} öğrenci · {ozet.tamamlayan} testi tamamladı</span>}
        {netVar && (
          <label className="sis-onay"><input type="checkbox" checked={netler} onChange={(e) => setNetler(e.target.checked)} /> Deneme ve net bilgilerini ekle</label>
        )}
        {okulId !== '' && <Link to={`/admin/okul/${okulId}`} className="ak-link" style={{ marginLeft: 'auto' }}>Okul paneline git →</Link>}
      </div>
      {ozetHata && <div className="auth-error">{ozetHata}</div>}
      {okulId === '' ? (
        <div className="bos-durum">Okul raporları için yukarıdan bir okul seçin.</div>
      ) : !ozet ? (
        !ozetHata && <div className="bos-durum">Yükleniyor…</div>
      ) : (
        <div className="ist-kartlar">
          <RaporKarti ikon="🏫" baslik="Okul genel raporu" aciklama={`${okulAdi}: katılım durumu, sınıf ve şube kırılımları, alan dağılımı, katman ortalamaları, öğrenci listesi.`}
            secenekler={[
              { anahtar: 'pdf', ad: 'PDF', ikon: '📄', indir: () => api.okulRaporuIndir(okulId, 'pdf', net) },
              { anahtar: 'xlsx', ad: 'Excel', ikon: '📊', indir: () => api.okulRaporuIndir(okulId, 'xlsx', net) },
            ]} />
          <RaporKarti ikon="🏷️" baslik="Sınıf düzeyi raporu" aciklama="Seçilen sınıf düzeyindeki şubelerin karşılaştırması, ortak güçlü yönler, okul ortalamasıyla kıyas."
            secenekler={[
              { anahtar: 'pdf', ad: 'PDF', ikon: '📄', indir: sart(sinif, 'Önce sınıf düzeyi seçin.', () => api.sinifRaporuIndir(okulId, sinif, null, 'ozet', 'pdf', net)) },
              { anahtar: 'xlsx', ad: 'Excel', ikon: '📊', indir: sart(sinif, 'Önce sınıf düzeyi seçin.', () => api.sinifRaporuIndir(okulId, sinif, null, 'ozet', 'xlsx', net)) },
            ]}>
            <select className="yp-sec" aria-label="Sınıf düzeyi" value={sinif} onChange={(e) => setSinif(e.target.value)}>
              <option value="">Sınıf düzeyi seçin…</option>
              {siniflar.map((s) => <option key={s.sinif} value={s.sinif}>{s.sinif} ({s.ogrenci} öğrenci)</option>)}
            </select>
          </RaporKarti>
          <RaporKarti ikon="🚪" baslik="Şube raporu" aciklama="Şubenin durumu, alanları, okul ortalamasıyla karşılaştırma ve öğrenci listesi (sınıf öğretmeni için)."
            secenekler={[
              { anahtar: 'pdf', ad: 'PDF', ikon: '📄', indir: sart(secSube, 'Önce şube seçin.', () => api.sinifRaporuIndir(okulId, secSube.sinif, secSube.sube || null, 'ozet', 'pdf', net)) },
              { anahtar: 'xlsx', ad: 'Excel', ikon: '📊', indir: sart(secSube, 'Önce şube seçin.', () => api.sinifRaporuIndir(okulId, secSube.sinif, secSube.sube || null, 'ozet', 'xlsx', net)) },
            ]}>
            <select className="yp-sec" aria-label="Şube" value={sube} onChange={(e) => setSube(e.target.value)}>
              <option value="">Şube seçin…</option>
              {subeler.map((s) => <option key={`${s.sinif}|${s.sube}`} value={`${s.sinif}|${s.sube}`}>{subeAdi(s)} ({s.ogrenci} öğrenci)</option>)}
            </select>
          </RaporKarti>
          <RaporKarti ikon="📚" baslik="Toplu bireysel raporlar" aciklama="Seçilen sınıf düzeyindeki ya da şubedeki her öğrencinin bireysel raporu tek PDF’te (veli toplantısı, sınıf öğretmeni). En çok 80 öğrenci."
            secenekler={[
              { anahtar: 'pdf', ad: 'Toplu PDF', ikon: '📄', indir: sart(topluSec, 'Önce sınıf ya da şube seçin.', () => api.sinifRaporuIndir(okulId, topluSec.sinif, topluSec.sube, topluTur, 'pdf', net)) },
            ]}>
            <select className="yp-sec" aria-label="Rapor türü" value={topluTur} onChange={(e) => setTopluTur(e.target.value)}>
              {TOPLU.map(([k, ad]) => <option key={k} value={k}>{ad}</option>)}
            </select>
            <select className="yp-sec" aria-label="Sınıf ya da şube" value={topluKapsam} onChange={(e) => setTopluKapsam(e.target.value)}>
              <option value="">Sınıf / şube seçin…</option>
              {siniflar.map((s) => (
                <optgroup key={s.sinif} label={s.sinif}>
                  <option value={`${s.sinif}|`}>{s.sinif} — tüm şubeler ({s.ogrenci})</option>
                  {subeler.filter((x) => x.sinif === s.sinif && x.sube).map((x) => <option key={x.sube} value={`${x.sinif}|${x.sube}`}>{subeAdi(x)} ({x.ogrenci})</option>)}
                </optgroup>
              ))}
            </select>
            {topluSayi > 80 && <span className="yp-ince" style={{ color: 'var(--re)' }}>{topluSayi} öğrenci: şube seçin.</span>}
          </RaporKarti>
          <RaporKarti ikon="🔑" baslik="Giriş listesi" aciklama="Okulun tüm öğrencileri: ad soyad, no, sınıf, e-posta ve geçici şifre (kendi şifresini belirleyenlerde “kendi şifresi”). Gizli bilgi içerir."
            secenekler={[
              { anahtar: 'xlsx', ad: 'Excel', ikon: '📊', indir: async () => { const r = await api.girisListesi(okulId); base64Indir(r.dosya_adi, r.icerik_base64) } },
            ]} />
          {moduller.includes('rehberlik') && (
            <RaporKarti ikon="🧭" baslik="Rehberlik görüşmeleri" aciklama="Okulun görüşme kayıtları, randevular ve takipler."
              secenekler={[{ anahtar: 'xlsx', ad: 'Excel', ikon: '📊', indir: () => api.gorusmeExcel(okulId) }]} />
          )}
        </div>
      )}

      <div className="sis-bolum-baslik"><h2>Sistem geneli raporlar</h2><p>Tüm okulları kapsayan raporlar; kurumlara iletilebilir.</p></div>
      <div className="ist-kartlar">
        <RaporKarti ikon="📊" baslik="İstatistikler" aciklama="İstatistikler sayfasının tamamı: özet göstergeler, zaman serisi, huni, katman puanları, bölümler, alanlar, modül kullanımı, okul tablosu, paketler (test hesapları hariç)."
          secenekler={[{ anahtar: 'xlsx', ad: 'Excel', ikon: '📊', indir: () => api.sistemIstatistikExcel({ donem }) }]}>
          <select className="yp-sec" aria-label="Dönem" value={donem} onChange={(e) => setDonem(e.target.value)}>
            <option value="30">Son 30 gün</option><option value="90">Son 90 gün</option><option value="yil">Bu eğitim yılı</option><option value="tum">Tümü</option>
          </select>
          <Link to="/admin/istatistikler" className="ak-link">Filtreli görünüm →</Link>
        </RaporKarti>
        <RaporKarti ikon="⚖️" baslik="Okul karşılaştırması" aciklama="Tüm okulların katılım ve sonuç göstergeleri yan yana. Belirli okullar için Okul Karşılaştırması sayfasında seçim yapın."
          secenekler={[{ anahtar: 'xlsx', ad: 'Excel (tüm okullar)', ikon: '📊', indir: () => api.okulKarsilastirmaExcel([]) }]}>
          <Link to="/admin/karsilastirma" className="ak-link">Okul seçerek al →</Link>
        </RaporKarti>
        <RaporKarti ikon="📐" baslik="Anket psikometrisi" aciklama="Hazır tarama formlarının güvenirlik ve madde istatistikleri (tüm okulların yanıtları)."
          secenekler={[{ anahtar: 'xlsx', ad: 'Excel', ikon: '📊', indir: () => api.anketPsikometriExcel() }]} />
        <RaporKarti ikon="📜" baslik="Audit Log" aciklama="Yönetim işlemlerinin kaydı: zaman, yapan, işlem, hedef, gerekçe ve okul."
          secenekler={[{ anahtar: 'xlsx', ad: 'Excel', ikon: '📊', indir: () => api.auditLogExcel(auditGun) }]}>
          <select className="yp-sec" aria-label="Süre" value={auditGun} onChange={(e) => setAuditGun(Number(e.target.value))}>
            <option value={30}>Son 30 gün</option><option value={90}>Son 90 gün</option><option value={365}>Son 1 yıl</option><option value={0}>Tümü</option>
          </select>
        </RaporKarti>
      </div>
      <div className="yp-ince" style={{ marginTop: 6 }}>
        Öğrenci bazlı raporlar (öğrenci, veli, yönetim, sınıf öğretmeni; PDF / Excel) okul panelinde öğrencinin detayından alınır. Okulun kendi anketlerinin Excel’i okul panelindeki Anketler bölümündedir.
      </div>
    </div>
  )
}
