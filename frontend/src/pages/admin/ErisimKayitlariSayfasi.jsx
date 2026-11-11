// [2026-11-05] Süper admin › Erişim Kayıtları: kim, ne zaman giriş yaptı; kimin verisine, hangi bölümde eriştiyse.
// Öğrenci, okul yetkilisi ve süper admin dahil herkes. Kişiye tıklayınca o kişinin, öğrenciye tıklayınca o öğrencinin
// verisine kimlerin baktığı süzülür.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { KpiKarti } from '../../components/istatistik/KpiKarti'
import Secim from '../../components/Secim'   // [2026-11-11] uzun açılır listeler yazarak aranır

const gun = (fark = 0) => {
  const d = new Date(); d.setDate(d.getDate() - fark)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const BOS = { bas: gun(6), bit: gun(0), kullanici_tipi: '', olay: '', okul_id: '', kisi: '', hedef: '', yalniz_hata: false }
const OLAYLAR = [
  ['', 'Tüm olaylar'], ['giris_hepsi', 'Tüm giriş denemeleri'], ['giris', 'Giriş'], ['giris_hatali', 'Hatalı giriş'],
  ['giris_engellendi', 'Engellenen giriş'], ['iki_adim_hatali', 'Hatalı doğrulama kodu'],
  ['goruntuleme', 'Görüntüleme'], ['indirme', 'İndirme'], ['islem', 'İşlem'],
]
const TIPLER = [['', 'Herkes'], ['ogrenci', 'Öğrenci'], ['okul_yetkilisi', 'Okul yetkilisi'], ['super_admin', 'Süper admin'], ['bilinmiyor', 'Bilinmeyen hesap']]
const zamanYaz = (z) => new Date(z).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })

export default function ErisimKayitlariSayfasi() {
  const [s, setS] = useState(BOS)            // ekrandaki süzgeç
  const [uygulanan, setUygulanan] = useState(BOS)
  const [kisiSecimi, setKisiSecimi] = useState(null)     // {id, ad}
  const [hedefSecimi, setHedefSecimi] = useState(null)   // {id, ad}
  const [sayfa, setSayfa] = useState(1)
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [okullar, setOkullar] = useState([])

  useEffect(() => { api.okullariListele().then((l) => setOkullar(l || [])).catch(() => setOkullar([])) }, [])

  const sorgu = useCallback(() => {
    const p = new URLSearchParams()
    Object.entries(uygulanan).forEach(([k, d]) => { if (d !== '' && d !== false && d != null) p.set(k, d) })
    if (kisiSecimi) p.set('kullanici_id', kisiSecimi.id)
    if (hedefSecimi) p.set('hedef_ogrenci_id', hedefSecimi.id)
    return p
  }, [uygulanan, kisiSecimi, hedefSecimi])

  useEffect(() => {
    const p = sorgu(); p.set('sayfa', sayfa); p.set('adet', 50)
    setYukleniyor(true); setHata(null)
    api.erisimKayitlari(p.toString()).then(setV).catch((e) => setHata(e.detail || 'Kayıtlar yüklenemedi.')).finally(() => setYukleniyor(false))
  }, [sorgu, sayfa])

  const uygula = (yeni) => { const d = { ...s, ...yeni }; setS(d); setUygulanan(d); setSayfa(1) }
  const sifirla = () => { setS(BOS); setUygulanan(BOS); setKisiSecimi(null); setHedefSecimi(null); setSayfa(1) }
  const csv = () => api.erisimKayitlariCsv(sorgu().toString()).catch((e) => setHata(e.detail || 'Dışa aktarılamadı.'))

  const o = v?.ozet || {}
  const sayfaSayisi = v ? Math.max(1, Math.ceil(v.toplam / v.adet)) : 1
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Erişim Kayıtları</div>
        <div className="ps">
          Kim, ne zaman giriş yaptı; kimin verisine, hangi bölümde eriştiyse. Öğrenciler, okul yetkilileri ve süper adminler dahil herkes
          kayıt altındadır; bu ekranı yalnızca süper admin görür. Bir kişiye tıklayınca o kişinin, bir öğrenciye tıklayınca o öğrencinin
          verisine kimlerin baktığı listelenir.
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
          <input className="auth-input" type="date" style={{ width: 150 }} value={s.bas} max={s.bit || undefined} onChange={(e) => setS({ ...s, bas: e.target.value })} aria-label="Başlangıç" />
          <span className="yp-ince">–</span>
          <input className="auth-input" type="date" style={{ width: 150 }} value={s.bit} min={s.bas || undefined} onChange={(e) => setS({ ...s, bit: e.target.value })} aria-label="Bitiş" />
          {[[0, 'Bugün'], [6, '7 gün'], [29, '30 gün']].map(([f, ad]) => (
            <button key={ad} type="button" className="btn sec" onClick={() => uygula({ bas: gun(f), bit: gun(0) })}>{ad}</button>
          ))}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
          <Secim className="auth-input" style={{ flex: '1 1 150px' }} value={s.kullanici_tipi} onChange={(e) => setS({ ...s, kullanici_tipi: e.target.value })} aria-label="Kişi türü">
            {TIPLER.map(([k, ad]) => <option key={k} value={k}>{ad}</option>)}
          </Secim>
          <Secim className="auth-input" style={{ flex: '1 1 170px' }} value={s.olay} onChange={(e) => setS({ ...s, olay: e.target.value })} aria-label="Olay">
            {OLAYLAR.map(([k, ad]) => <option key={k} value={k}>{ad}</option>)}
          </Secim>
          <Secim className="auth-input" style={{ flex: '1 1 190px' }} value={s.okul_id} onChange={(e) => setS({ ...s, okul_id: e.target.value })} aria-label="Okul">
            <option value="">Tüm okullar</option>
            {okullar.map((x) => <option key={x.id} value={x.id}>{x.ad}</option>)}
          </Secim>
          <input className="auth-input" style={{ flex: '1 1 170px' }} placeholder="Kişi (ad veya e-posta)" value={s.kisi} onChange={(e) => setS({ ...s, kisi: e.target.value })}
                 onKeyDown={(e) => e.key === 'Enter' && uygula({})} />
          <input className="auth-input" style={{ flex: '1 1 170px' }} placeholder="Verisine bakılan öğrenci" value={s.hedef} onChange={(e) => setS({ ...s, hedef: e.target.value })}
                 onKeyDown={(e) => e.key === 'Enter' && uygula({})} />
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 10, alignItems: 'center' }}>
          <label className="yp-ince" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" checked={s.yalniz_hata} onChange={(e) => setS({ ...s, yalniz_hata: e.target.checked })} /> Yalnızca başarısız denemeler
          </label>
          {kisiSecimi && <button type="button" className="btn sec" onClick={() => { setKisiSecimi(null); setSayfa(1) }}>Kişi: {kisiSecimi.ad} ✕</button>}
          {hedefSecimi && <button type="button" className="btn sec" onClick={() => { setHedefSecimi(null); setSayfa(1) }}>Öğrenci: {hedefSecimi.ad} ✕</button>}
          <div style={{ flex: 1 }} />
          <button type="button" className="btn sec" onClick={sifirla}>Sıfırla</button>
          <button type="button" className="btn sec" onClick={csv}>CSV indir</button>
          <button type="button" className="btn" onClick={() => uygula({})}>Listele</button>
        </div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}

      {v && (
        <div className="card">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12 }}>
            <KpiKarti etiket="Kayıt" deger={v.toplam} ikon="📜" alt={`saklama ${v.saklama_gun === '0' ? 'süresiz' : `${v.saklama_gun} gün`}`} />
            <KpiKarti etiket="Giriş" deger={o.giris} ikon="🔑" />
            <KpiKarti etiket="Başarısız giriş" deger={o.hatali_giris} ikon="⛔" ton={o.hatali_giris ? 'uyari' : undefined}
                      onClick={o.hatali_giris ? () => uygula({ olay: 'giris_hepsi', yalniz_hata: true }) : undefined} />
            <KpiKarti etiket="Reddedilen erişim" deger={o.reddedilen} ikon="🚫" ton={o.reddedilen ? 'kotu' : undefined} alt="yetkisi olmayan veriye deneme"
                      onClick={o.reddedilen ? () => uygula({ olay: '', yalniz_hata: true }) : undefined} />
            <KpiKarti etiket="İndirme" deger={o.indirme} ikon="⬇️" onClick={o.indirme ? () => uygula({ olay: 'indirme' }) : undefined} />
            <KpiKarti etiket="Kişi" deger={o.kisi} ikon="👤" alt={`${o.bakilan_ogrenci || 0} öğrencinin verisine bakıldı`} />
          </div>
        </div>
      )}

      <div className="card">
        {!v ? <div className="bos-durum yukleniyor">Yükleniyor…</div> : v.kayitlar.length === 0 ? <div className="bos-durum">Bu süzgeçle kayıt yok.</div> : (
          <>
            <div className="yp-tablo-kap" style={{ opacity: yukleniyor ? 0.6 : 1 }}>
              <table className="yp-tablo">
                <thead><tr><th>Zaman</th><th>Kişi</th><th>Olay</th><th>Bölüm</th><th>Verisine bakılan öğrenci</th><th>Sonuç</th><th>IP</th></tr></thead>
                <tbody>
                  {v.kayitlar.map((k) => (
                    <tr key={k.id}>
                      <td style={{ whiteSpace: 'nowrap' }}>{zamanYaz(k.zaman)}</td>
                      <td>
                        {k.kullanici_id
                          ? <button type="button" className="hg-link" style={{ fontSize: 12.5, color: 'var(--tx)' }} title="Bu kişinin tüm kayıtları"
                                    onClick={() => { setKisiSecimi({ id: k.kullanici_id, ad: k.kullanici_ad || k.kullanici_eposta }); setSayfa(1) }}>{k.kullanici_ad || k.kullanici_eposta || '—'}</button>
                          : <span>{k.kullanici_eposta || '—'}</span>}
                        <div className="yp-ince">{k.kullanici_tipi_etiket}{k.okul_ad ? ` · ${k.okul_ad}` : ''}</div>
                      </td>
                      <td>{k.olay_etiket}</td>
                      <td>{k.bolum}{k.yol && <div className="yp-ince" title={k.yol} style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{k.yontem} {k.yol}</div>}</td>
                      <td>
                        {k.hedef_ogrenci_id && k.kullanici_tipi !== 'ogrenci'
                          ? <button type="button" className="hg-link" style={{ fontSize: 12.5, color: 'var(--tx)' }} title="Bu öğrencinin verisine kimler baktı"
                                    onClick={() => { setHedefSecimi({ id: k.hedef_ogrenci_id, ad: k.hedef_ad || 'öğrenci' }); setSayfa(1) }}>{k.hedef_ad || 'Silinmiş öğrenci'}</button>
                          : k.kullanici_tipi === 'ogrenci' && k.hedef_ogrenci_id ? <span className="yp-ince">kendi verisi</span>
                            : k.hedef_okul_ad ? <span className="yp-ince">{k.hedef_okul_ad}</span> : <span className="yp-ince">—</span>}
                      </td>
                      <td>{k.basarili ? 'Başarılı' : <b style={{ color: 'var(--re)' }}>Başarısız{k.durum_kodu ? ` (${k.durum_kodu})` : ''}</b>}</td>
                      <td className="yp-ince">{k.ip || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'flex-end', marginTop: 10 }}>
              <span className="yp-ince">{v.toplam} kayıt · sayfa {sayfa} / {sayfaSayisi}</span>
              <button type="button" className="btn sec" disabled={sayfa <= 1} onClick={() => setSayfa(sayfa - 1)}>‹ Önceki</button>
              <button type="button" className="btn sec" disabled={sayfa >= sayfaSayisi} onClick={() => setSayfa(sayfa + 1)}>Sonraki ›</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
