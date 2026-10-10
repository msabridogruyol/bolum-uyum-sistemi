// [2026-10-09] Öğrenci detayı: hesap, ilerleme, sonuç, istatistik, kayıtlar + şifre sıfırla / düzenle / sil
import { useEffect, useState } from 'react'
import { AkranListesi } from './AkranPaneli'
import { OgrenciIlgi } from './KulupYonetimi'
import { api } from '../../api/client'
import { DurumRozeti, Pencere, SifreHucresi, SifreListesi, onceSure, tarih } from './ortak'
import RaporDugmeleri from '../RaporDugmeleri'
import CevapAnaliziSekmesi from './CevapAnaliziSekmesi'

// [2026-10-09] Hedef bölüm: öğrenci en fazla 3 kez değiştirebilir; okul yetkilisi / süper admin hedefi değiştirebilir
// (öğrencinin hakkından düşmez) ya da ek hak verebilir.
function HedefYonetimi({ d, ogrenciId, bekle, islem, yenile }) {
  const [secim, setSecim] = useState(null)   // null = kapalı, '' = açık
  const [bolumler, setBolumler] = useState(null)
  const hak = d.hedef_hak || { degisim_sayisi: 0, degisim_hakki: 3, kalan_hak: 3 }
  function ac() { setSecim(''); if (!bolumler) api.yonetimBolumler().then(setBolumler).catch(() => setBolumler([])) }
  return (
    <div>
      <b>{d.hedef ? `${d.hedef.bolum}${d.hedef.uyum != null ? ` · uyum %${d.hedef.uyum}` : ''}` : 'Seçmedi'}</b>
      <div className="yp-ince" style={{ marginTop: 3 }}>
        Değiştirme hakkı: {hak.degisim_sayisi}/{hak.degisim_hakki} kullanıldı{hak.kalan_hak === 0 ? ' — hakkı doldu' : ` · ${hak.kalan_hak} kaldı`}
      </div>
      <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap', alignItems: 'center' }}>
        <button className="yp-mini" disabled={bekle} onClick={() => islem(async () => { await api.yonetimHedefHakki(ogrenciId, 1); yenile() })}>+1 değiştirme hakkı ver</button>
        {secim === null ? (
          <button className="yp-mini" disabled={bekle} onClick={ac}>Hedefini ben değiştireyim</button>
        ) : (
          <>
            <select className="yp-sec" value={secim} onChange={(e) => setSecim(e.target.value)} disabled={!bolumler}>
              <option value="">{bolumler ? 'Bölüm seç…' : 'Yükleniyor…'}</option>
              {(bolumler || []).map((b) => <option key={b.id} value={b.id}>{b.ad}</option>)}
            </select>
            <button className="yp-mini" disabled={bekle || !secim} onClick={() => islem(async () => { await api.yonetimOgrenciHedef(ogrenciId, Number(secim)); setSecim(null); yenile() })}>Kaydet</button>
            <button className="yp-mini" onClick={() => setSecim(null)}>Vazgeç</button>
          </>
        )}
      </div>
    </div>
  )
}

const SEKMELER = [['genel', 'Genel'], ['ilerleme', 'Test ilerlemesi'], ['sonuc', 'Sonuçlar'], ['akran', 'Benzer akranlar'], ['ilgi', 'İlgi & kulüp'], ['kayit', 'Kayıtlar']]
const KATMAN_DURUM = { tamamlandi: '✓ Tamamlandı', devam_ediyor: '… Devam ediyor', yarida_birakildi: '⏸ Yarıda bıraktı', baslamadi: '— Başlamadı' }

export default function OgrenciDetayPenceresi({ ogrenciId, superAdmin, okullar, onKapat, onDegisti }) {
  const [d, setD] = useState(null)
  const [hata, setHata] = useState(null)
  const [sekme, setSekme] = useState('genel')
  const [duzen, setDuzen] = useState(null)
  const [yeniSifre, setYeniSifre] = useState(null)
  const [silOnay, setSilOnay] = useState(false)
  const [bekle, setBekle] = useState(false)

  function yukle() {
    api.ogrenciDetayi(ogrenciId).then(setD).catch((e) => setHata(e.detail || 'Öğrenci yüklenemedi.'))
  }
  useEffect(yukle, [ogrenciId])

  async function islem(fn) {
    setBekle(true); setHata(null)
    try { await fn() } catch (e) { setHata(e.detail || 'İşlem başarısız.') } finally { setBekle(false) }
  }

  const sifreSifirla = () => islem(async () => {
    const r = await api.ogrenciSifreleriniSifirla([ogrenciId])
    setYeniSifre(r)
    yukle(); onDegisti?.()
  })
  const kaydet = (e) => { e.preventDefault(); islem(async () => { await api.ogrenciDuzenle(ogrenciId, duzen); setDuzen(null); yukle(); onDegisti?.() }) }
  const sil = () => islem(async () => { await api.ogrencileriSil([ogrenciId]); onDegisti?.(); onKapat() })
  const okulDegistir = (okulId) => islem(async () => { await api.ogrenciOkulDegistir(ogrenciId, Number(okulId)); yukle(); onDegisti?.() })

  if (!d) {
    return <Pencere baslik="Öğrenci" onKapat={onKapat}>{hata ? <div className="auth-error">{hata}</div> : <div className="bos-durum">Yükleniyor…</div>}</Pencere>
  }
  const h = d.hesap
  const st = d.istatistik

  return (
    <Pencere
      genis
      baslik={h.ad_soyad}
      altBaslik={<>{h.email} · {h.sinif_metni || 'sınıf yok'} · {h.okul_ad} <DurumRozeti kod={h.durum} etiket={h.durum_etiket} /></>}
      onKapat={onKapat}
      alt={
        <>
          <button className="btn sec" disabled={bekle} onClick={sifreSifirla}>🔑 Şifre sıfırla</button>
          <button className="btn sec" disabled={bekle} onClick={() => setDuzen({ ad_soyad: h.ad_soyad, email: h.email, sinif: h.sinif || '', sube: h.sube || '', ogrenci_no: h.ogrenci_no || '' })}>✎ Düzenle</button>
          <div style={{ flex: 1 }} />
          {silOnay ? (
            <>
              <span style={{ fontSize: 12, color: 'var(--re)' }}>Tüm cevapları ve sonuçlarıyla kalıcı olarak silinsin mi?</span>
              <button className="btn yp-tehlike" disabled={bekle} onClick={sil}>Evet, sil</button>
              <button className="btn sec" onClick={() => setSilOnay(false)}>Vazgeç</button>
            </>
          ) : <button className="btn sec yp-tehlike-ince" onClick={() => setSilOnay(true)}>🗑 Sil</button>}
        </>
      }
    >
      {hata && <div className="auth-error">{hata}</div>}
      {yeniSifre && <div style={{ marginBottom: 14 }}><SifreListesi kayitlar={yeniSifre.kayitlar} dosya={yeniSifre} aciklama="Öğrenci bu şifreyle girip yeni şifresini belirler; eski şifresi artık geçmez." /></div>}

      {duzen && (
        <form className="yp-kutu" style={{ marginBottom: 14 }} onSubmit={kaydet}>
          <div className="yp-kb">Bilgileri düzelt</div>
          <div className="yp-form-satir">
            <input className="auth-input" value={duzen.ad_soyad} onChange={(e) => setDuzen({ ...duzen, ad_soyad: e.target.value })} placeholder="Ad Soyad" required />
            <input className="auth-input" type="email" value={duzen.email} onChange={(e) => setDuzen({ ...duzen, email: e.target.value })} placeholder="E-posta" required />
            <select className="auth-input" value={duzen.sinif} onChange={(e) => setDuzen({ ...duzen, sinif: e.target.value })}>
              <option value="">Sınıf…</option>
              {['Aday', '9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf', 'Mezun'].map((s) => <option key={s}>{s}</option>)}
            </select>
            <input className="auth-input" style={{ maxWidth: 80 }} value={duzen.sube} maxLength={2} onChange={(e) => setDuzen({ ...duzen, sube: e.target.value })} placeholder="Şube" />
            <input className="auth-input" style={{ maxWidth: 120 }} value={duzen.ogrenci_no} maxLength={20} onChange={(e) => setDuzen({ ...duzen, ogrenci_no: e.target.value })} placeholder="Öğrenci no" />
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <button className="btn" type="submit" disabled={bekle}>Kaydet</button>
            <button className="btn sec" type="button" onClick={() => setDuzen(null)}>İptal</button>
          </div>
        </form>
      )}

      {/* [2026-10-10] Rehber öğretmen için raporlar: yönetici · öğrenci · veli (PDF) ve Excel */}
      <RaporDugmeleri kucuk secenekler={[
        { anahtar: 'y', ad: 'Yönetici', ikon: '🗂️', aciklama: 'Tüm ayrıntılar: güven puanı, ihlaller, katman puanları, öneriler, hedef, SWOT', indir: () => api.ogrenciRaporuIndir(ogrenciId, 'yonetici') },
        { anahtar: 'o', ad: 'Öğrenci', ikon: '📘', aciklama: 'Öğrenciye verilecek rapor', indir: () => api.ogrenciRaporuIndir(ogrenciId, 'ogrenci') },
        { anahtar: 'v', ad: 'Veli', ikon: '👪', aciklama: 'Veliye verilecek sade rapor ve öneriler', indir: () => api.ogrenciRaporuIndir(ogrenciId, 'veli') },
        { anahtar: 'x', ad: 'Excel', ikon: '📊', aciklama: 'Tüm puanlar tablo halinde', indir: () => api.ogrenciRaporuIndir(ogrenciId, 'ogrenci', 'xlsx') },
      ]} />
      <div className="yp-sekmeler">
        {[...SEKMELER, ...(superAdmin ? [['cevaplar', '🔒 Cevap analizi']] : [])].map(([k, ad]) => <button key={k} className={sekme === k ? 'aktif' : ''} onClick={() => setSekme(k)}>{ad}</button>)}
      </div>

      {sekme === 'genel' && (
        <>
          <div className="yp-kpi-grid">
            <div className="yp-kpi"><div className="yp-kpi-e">Test ilerlemesi</div><div className="yp-kpi-d">{st.biten_katman}/{st.toplam_katman}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Cevaplanan soru</div><div className="yp-kpi-d">{st.cevap_sayisi}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Teste harcanan süre</div><div className="yp-kpi-d">{st.toplam_sure_dk ? `${Math.round(st.toplam_sure_dk)} dk` : '—'}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Giriş sayısı</div><div className="yp-kpi-d">{st.giris_sayisi}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Güven skoru</div><div className="yp-kpi-d">{st.guven_skoru != null ? `%${Math.round(st.guven_skoru)}` : '—'}</div></div>
            <div className="yp-kpi"><div className="yp-kpi-e">Dikkat dağılması</div><div className="yp-kpi-d">{st.dikkat_dagilmasi}</div></div>
          </div>
          <div className="yp-bilgi-grid">
            <div><span>Hesap açılışı</span><b>{tarih(h.olusturulma_zamani)}</b></div>
            <div><span>Son giriş</span><b>{h.son_giris_zamani ? `${tarih(h.son_giris_zamani)} (${onceSure(h.son_giris_zamani)})` : 'Hiç giriş yapmadı'}</b></div>
            <div><span>Şifre</span><b><SifreHucresi gecici={h.gecici_sifre} degistirmeli={h.sifre_degistirmeli} /></b></div>
            <div><span>Öğrenci no</span><b>{h.ogrenci_no || '—'}</b></div>
            <div style={{ gridColumn: '1 / -1' }}><span>Hedef bölüm</span>
              <HedefYonetimi d={d} ogrenciId={ogrenciId} bekle={bekle} islem={islem} yenile={() => { yukle(); onDegisti?.() }} />
            </div>
            {/* [2026-10-10] Öğrencinin ★ Listem'i — görüşmede konuşulacak bölümler */}
            <div style={{ gridColumn: '1 / -1' }}><span>Listesindeki bölümler (★)</span>
              {d.listem?.length ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
                  {d.listem.map((b) => (
                    <span key={b.bolum_id} className="yp-etiket-cip" title={b.alt_alan || b.ust_alan || ''}>
                      ★ {b.bolum_adi}{b.toplam_uyum != null && <b> %{Math.round(b.toplam_uyum)}</b>}
                    </span>
                  ))}
                </div>
              ) : <b style={{ fontWeight: 500 }} className="yp-ince">Henüz listesine bölüm eklemedi</b>}
            </div>
            {h.ilgi_alanlari && <div style={{ gridColumn: '1 / -1' }}><span>İlgi alanları</span><b style={{ fontWeight: 500 }}>{h.ilgi_alanlari}</b></div>}
            {superAdmin && (
              <div><span>Okulu</span>
                <select className="yp-sec" value={h.okul_id} disabled={bekle} onChange={(e) => okulDegistir(e.target.value)}>
                  {okullar.map((o) => <option key={o.id} value={o.id}>{o.ad}</option>)}
                </select>
              </div>
            )}
          </div>
        </>
      )}

      {sekme === 'ilerleme' && (
        d.turlar.length === 0 ? <div className="bos-durum">Öğrenci teste henüz başlamadı.</div> : d.turlar.map((t) => (
          <div key={t.tur_no} className="yp-kutu" style={{ marginBottom: 12 }}>
            <div className="yp-kb">
              {t.tur_no}. değerlendirme · {t.durum === 'tamamlandi' ? 'tamamlandı' : 'devam ediyor'}
              <span className="yp-ince" style={{ fontWeight: 500 }}> — başlangıç {tarih(t.baslama)}{t.tamamlanma ? `, bitiş ${tarih(t.tamamlanma)}` : ''}</span>
            </div>
            <table className="yp-tablo">
              <thead><tr><th>Bölüm</th><th>Durum</th><th>Cevap</th><th>Süre</th><th>Bitiş</th></tr></thead>
              <tbody>
                {t.katmanlar.map((k) => (
                  <tr key={k.kod}><td><b>{k.kod}</b> {k.ad}</td><td>{KATMAN_DURUM[k.durum] || k.durum}</td><td>{k.cevap}</td>
                    <td>{k.sure_dk != null ? `${Math.round(k.sure_dk)} dk` : '—'}</td><td className="yp-ince">{tarih(k.tamamlanma)}</td></tr>
                ))}
                {t.dallar.map((x) => (
                  <tr key={x.ad}><td><b>K5</b> {x.ad}</td><td>{KATMAN_DURUM[x.durum] || x.durum}</td><td>—</td><td>{x.sure_dk != null ? `${Math.round(x.sure_dk)} dk` : '—'}</td><td /></tr>
                ))}
              </tbody>
            </table>
            {t.sonuc_gecerli_mi === false && <div className="auth-error" style={{ marginTop: 8 }}>Bu değerlendirme güvenilirlik kontrolünden geçemedi.</div>}
          </div>
        ))
      )}

      {sekme === 'sonuc' && (
        <>
          {d.sonuc_notu && <div className="yp-uyari" style={{ background: 'var(--sur2)', borderColor: 'var(--bor)' }}>{d.sonuc_notu}</div>}
          {d.oneriler.length > 0 && (
            <table className="yp-tablo">
              <thead><tr><th>#</th><th>Önerilen bölüm</th><th>Alan</th><th style={{ width: '35%' }}>Uyum</th></tr></thead>
              <tbody>
                {d.oneriler.map((o) => (
                  <tr key={o.sira}><td>{o.sira}</td><td><b>{o.bolum}</b></td><td className="yp-ince">{o.alan || '—'}</td>
                    <td><div className="yp-cubuk"><div style={{ width: `${Math.max(4, Math.min(100, o.uyum))}%` }} /><span>%{o.uyum}</span></div></td></tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}

      {sekme === 'akran' && <AkranListesi ogrenciId={ogrenciId} />}
      {sekme === 'ilgi' && <OgrenciIlgi ogrenciId={ogrenciId} />}

      {sekme === 'cevaplar' && superAdmin && <CevapAnaliziSekmesi ogrenciId={ogrenciId} />}

      {sekme === 'kayit' && (
        <div className="yp-zaman-cizelgesi">
          {d.kayitlar.map((k, i) => (
            <div key={i} className={`yp-zc-satir yp-zc-${k.olay}`}>
              <div className="yp-zc-zaman">{tarih(k.zaman)}</div>
              <div><b>{k.etiket}</b>{k.aciklama && <span className="yp-ince"> — {k.aciklama}</span>}{k.yapan && k.yapan !== 'Öğrenci' && <div className="yp-ince">İşlemi yapan: {k.yapan}</div>}</div>
            </div>
          ))}
        </div>
      )}
    </Pencere>
  )
}
