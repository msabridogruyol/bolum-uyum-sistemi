// [2026-11-11] Süper admin › Kullanım Analizi: kim, hangi menüde, ne kadar süre geçiriyor.
// Öğrenciler, okul yetkilileri ve süper adminler ayrı; okul okul ve toplam. Kişiye tıklayınca o kişinin ayrıntısı açılır.
// Ölçü "aktif süre": sekme ekranda ve kişi son 2 dakikada etkin (bkz. components/KullanimIzleyici.jsx).
import { Fragment, useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { Pencere } from '../../components/yonetim/ortak'
import {
  CizgiGrafik, GrafikKarti, Halka, IsiHaritasi, KpiKarti, KpiSatiri, SutunGrafik, YatayCubuk,
} from '../../components/istatistik'
import Secim from '../../components/Secim'   // [2026-11-11] uzun açılır listeler yazarak aranır

const gun = (fark = 0) => {
  const d = new Date(); d.setDate(d.getDate() - fark)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const TIP_AD = { ogrenci: 'Öğrenciler', okul_yetkilisi: 'Okul yetkilileri', super_admin: 'Süper adminler' }
const TIP_TEKIL = { ogrenci: 'Öğrenci', okul_yetkilisi: 'Okul yetkilisi', super_admin: 'Süper admin' }
const SEKMELER = [['genel', 'Genel bakış'], ['ogrenci', 'Öğrenciler'], ['okul_yetkilisi', 'Okul yetkilileri'],
  ['super_admin', 'Süper adminler'], ['okullar', 'Okullar'], ['kisiler', 'Kişiler']]
const GUNLER = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
const SAATLER = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))

/** 45 sn · 12 dk · 3 sa 05 dk */
function sureYaz(sn) {
  const s = Math.round(Number(sn) || 0)
  if (s < 60) return `${s} sn`
  if (s < 3600) return `${Math.round(s / 60)} dk`
  const dakika = Math.round(s / 60)   // önce dakikaya yuvarlanır: "6 sa 60 dk" olmaz
  const sa = Math.floor(dakika / 60), dk = dakika % 60
  return dk ? `${sa.toLocaleString('tr-TR')} sa ${String(dk).padStart(2, '0')} dk` : `${sa.toLocaleString('tr-TR')} sa`
}
const dk = (sn) => Math.round(((Number(sn) || 0) / 60) * 10) / 10
const yuzde = (v) => (v == null ? '—' : `%${Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`)
const tarihYaz = (z) => (z ? new Date(z).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '—')
const gunYaz = (g) => { const [, a, d] = g.split('-'); return `${d}.${a}` }
function degisim(simdi, once) {
  if (!once) return undefined
  return { deger: Math.round(((simdi - once) / once) * 1000) / 10, birim: '%', donem: 'önceki döneme göre' }
}

// ============================================================================ sayfa
export default function KullanimAnaliziSayfasi() {
  const [s, setS] = useState({ bas: gun(29), bit: gun(0), okul_id: '', test_dahil: false })
  const [uygulanan, setUygulanan] = useState(s)
  const [sekme, setSekme] = useState('genel')
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [yukleniyor, setYukleniyor] = useState(false)
  const [okullar, setOkullar] = useState([])
  const [kisi, setKisi] = useState(null)   // {tip, id}

  useEffect(() => { api.okullariListele().then((l) => setOkullar(l || [])).catch(() => setOkullar([])) }, [])
  const sorgu = useMemo(() => {
    const p = new URLSearchParams({ bas: uygulanan.bas, bit: uygulanan.bit })
    if (uygulanan.okul_id !== '') p.set('okul_id', uygulanan.okul_id)
    if (uygulanan.test_dahil) p.set('test_dahil', 'true')
    return p.toString()
  }, [uygulanan])
  useEffect(() => {
    setYukleniyor(true); setHata(null)
    api.kullanimAnalizi(sorgu).then(setV).catch((e) => setHata(e.detail || 'Analiz yüklenemedi.')).finally(() => setYukleniyor(false))
  }, [sorgu])

  const uygula = (yeni = {}) => { const d = { ...s, ...yeni }; setS(d); setUygulanan(d) }
  const csv = (tur, tip) => api.kullanimAnaliziCsv(`${sorgu}&tur=${tur}${tip ? `&tip=${tip}` : ''}`).catch((e) => setHata(e.detail || 'Dışa aktarılamadı.'))
  const kisiAc = useCallback((tip, id) => setKisi({ tip, id }), [])
  const okulSec = useCallback((id) => { uygula({ okul_id: String(id) }); setSekme('genel') }, [s])   // eslint-disable-line

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Kullanım Analizi</div>
        <div className="ps">
          Kim, hangi menüde ne kadar süre geçiriyor: öğrenciler, okul yetkilileri ve süper adminler ayrı; okul okul ve toplam.
          Süre <b>aktif süredir</b>: sekme ekranda açık ve kişi son 2 dakika içinde dokunmuş, tıklamış, yazmış ya da kaydırmışsa sayılır.
          Başka sekmede, arka planda ya da başında kimse yokken geçen süre sayılmaz. Test hesapları ve demo okullar varsayılan olarak hariçtir.
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center' }}>
          <input className="auth-input" type="date" style={{ width: 150 }} value={s.bas} max={s.bit || undefined} onChange={(e) => setS({ ...s, bas: e.target.value })} aria-label="Başlangıç" />
          <span className="yp-ince">–</span>
          <input className="auth-input" type="date" style={{ width: 150 }} value={s.bit} min={s.bas || undefined} onChange={(e) => setS({ ...s, bit: e.target.value })} aria-label="Bitiş" />
          {[[0, 'Bugün'], [6, '7 gün'], [29, '30 gün'], [89, '90 gün'], [364, '1 yıl']].map(([f, ad]) => (
            <button key={ad} type="button" className="btn sec" onClick={() => uygula({ bas: gun(f), bit: gun(0) })}>{ad}</button>
          ))}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 10, alignItems: 'center' }}>
          <Secim className="auth-input" style={{ flex: '1 1 220px', maxWidth: 360 }} value={s.okul_id} onChange={(e) => uygula({ okul_id: e.target.value })} aria-label="Okul">
            <option value="">Tüm okullar (toplam)</option>
            <option value="0">Okul harici öğrenciler</option>
            {okullar.map((x) => <option key={x.id} value={x.id}>{x.ad}{x.demo ? ' (demo)' : ''}</option>)}
          </Secim>
          <label className="yp-ince" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" checked={s.test_dahil} onChange={(e) => uygula({ test_dahil: e.target.checked })} /> Test hesapları ve demo okullar dahil
          </label>
          <div style={{ flex: 1 }} />
          <button type="button" className="btn" onClick={() => uygula({})}>Uygula</button>
        </div>
        {v && (
          <div className="yp-ince" style={{ marginTop: 8 }}>
            Dönem: {gunYaz(v.donem.bas)} – {gunYaz(v.donem.bit)} ({v.donem.gun} gün) · karşılaştırma: {gunYaz(v.donem.onceki_bas)} – {gunYaz(v.donem.onceki_bit)}
            {v.olcum_baslangici ? ` · ölçüm başlangıcı: ${tarihYaz(v.olcum_baslangici)}` : ' · henüz ölçüm yok: kayıtlar kullanıcılar sisteme girdikçe oluşur'}
          </div>
        )}
      </div>

      <div className="koc-sekmeler" role="tablist">
        {SEKMELER.map(([k, ad]) => <button key={k} role="tab" aria-selected={sekme === k} className={sekme === k ? 'aktif' : ''} onClick={() => setSekme(k)}>{ad}</button>)}
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v ? !hata && <div className="bos-durum yukleniyor">Yükleniyor…</div> : (
        <div style={{ opacity: yukleniyor ? 0.6 : 1 }}>
          {sekme === 'genel' && <GenelBakis v={v} csv={csv} kisiAc={kisiAc} okulSec={okulSec} />}
          {['ogrenci', 'okul_yetkilisi', 'super_admin'].includes(sekme) && <TipPaneli v={v} tip={sekme} csv={csv} kisiAc={kisiAc} />}
          {sekme === 'okullar' && <OkullarPaneli v={v} csv={csv} okulSec={okulSec} />}
          {sekme === 'kisiler' && <KisilerPaneli sorgu={sorgu} csv={csv} kisiAc={kisiAc} siniflar={v.siniflar} />}
        </div>
      )}
      {kisi && <KisiAyrintisi tip={kisi.tip} id={kisi.id} bas={uygulanan.bas} bit={uygulanan.bit} onKapat={() => setKisi(null)} />}
    </div>
  )
}

// ============================================================================ ortak parçalar
function OzetKpileri({ o, tip }) {
  return (
    <KpiSatiri min={165}>
      <KpiKarti etiket="Toplam aktif süre" deger={sureYaz(o.toplam_aktif_sn)} ikon="⏱️"
                degisim={degisim(o.toplam_aktif_sn, o.onceki.toplam_aktif_sn)} alt={`açık kalma: ${sureYaz(o.toplam_acik_sn)}`} />
      <KpiKarti etiket="Kullanan kişi" deger={o.aktif_kullanici} ikon="👥" degisim={degisim(o.aktif_kullanici, o.onceki.aktif_kullanici)}
                alt={`${o.kayitli.toLocaleString('tr-TR')} kayıtlı ${tip ? TIP_TEKIL[tip].toLocaleLowerCase('tr-TR') : 'hesap'}`} />
      <KpiKarti etiket="Katılım" deger={yuzde(o.katilim_orani)} ikon="📈" ton={o.katilim_orani != null && o.katilim_orani < 50 ? 'uyari' : 'notr'}
                alt={`${o.hic_kullanmayan.toLocaleString('tr-TR')} kişi hiç kullanmadı`} />
      <KpiKarti etiket="Kişi başı süre" deger={sureYaz(o.kisi_basi_sn)} ikon="👤" alt={`medyan ${sureYaz(o.medyan_kisi_sn)}`} />
      <KpiKarti etiket="Oturum" deger={o.oturum} ikon="🔁" alt={`kişi başı ${o.kisi_basi_oturum.toLocaleString('tr-TR')} · ${o.kisi_basi_aktif_gun.toLocaleString('tr-TR')} aktif gün`} />
      <KpiKarti etiket="Ortalama oturum" deger={sureYaz(o.ort_oturum_sn)} ikon="⌛" alt={`medyan ${sureYaz(o.medyan_oturum_sn)} · 1 dk'dan kısa ${yuzde(o.kisa_oturum_orani)}`} />
      <KpiKarti etiket="Günlük ortalama aktif kişi" deger={o.ort_gunluk_aktif_kisi.toLocaleString('tr-TR')} ikon="📅" />
    </KpiSatiri>
  )
}

function KarsilastirmaTablosu({ ozet, tipler }) {
  const satirlar = [
    ['Kayıtlı hesap', (o) => o.kayitli.toLocaleString('tr-TR')],
    ['Kullanan kişi', (o) => o.aktif_kullanici.toLocaleString('tr-TR')],
    ['Katılım oranı', (o) => yuzde(o.katilim_orani)],
    ['Hiç kullanmayan', (o) => o.hic_kullanmayan.toLocaleString('tr-TR')],
    ['Toplam aktif süre', (o) => sureYaz(o.toplam_aktif_sn)],
    ['Önceki dönem toplam süre', (o) => sureYaz(o.onceki.toplam_aktif_sn)],
    ['Kişi başı süre (ortalama)', (o) => sureYaz(o.kisi_basi_sn)],
    ['Kişi başı süre (medyan)', (o) => sureYaz(o.medyan_kisi_sn)],
    ['Oturum sayısı', (o) => o.oturum.toLocaleString('tr-TR')],
    ['Ortalama oturum süresi', (o) => sureYaz(o.ort_oturum_sn)],
    ['Medyan oturum süresi', (o) => sureYaz(o.medyan_oturum_sn)],
    ["1 dk'dan kısa oturum", (o) => yuzde(o.kisa_oturum_orani)],
    ['Kişi başı oturum', (o) => o.kisi_basi_oturum.toLocaleString('tr-TR')],
    ['Kişi başı aktif gün', (o) => o.kisi_basi_aktif_gun.toLocaleString('tr-TR')],
    ['Günlük ortalama aktif kişi', (o) => o.ort_gunluk_aktif_kisi.toLocaleString('tr-TR')],
    ['Menü ziyareti', (o) => o.ziyaret.toLocaleString('tr-TR')],
  ]
  return (
    <div className="yp-tablo-kap">
      <table className="yp-tablo">
        <thead><tr><th>Ölçü</th>{tipler.map(([k, ad]) => <th key={k} style={{ textAlign: 'right' }}>{ad}</th>)}</tr></thead>
        <tbody>{satirlar.map(([ad, f]) => (
          <tr key={ad}><td>{ad}</td>{tipler.map(([k]) => <td key={k} style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{f(ozet[k])}</td>)}</tr>
        ))}</tbody>
      </table>
    </div>
  )
}

function seriler(gunluk, tipler, alan, donustur = (x) => x) {
  return tipler.map(([k, ad]) => ({ ad, degerler: gunluk.map((g) => donustur(g[`${k}_${alan}`])) }))
}

function EnCokKullananlar({ liste, tip, kisiAc }) {
  if (!liste?.length) return <div className="ist-bos">Henüz veri yok</div>
  return (
    <div className="yp-tablo-kap">
      <table className="yp-tablo">
        <thead><tr><th>#</th><th>Kişi</th><th style={{ textAlign: 'right' }}>Aktif süre</th><th style={{ textAlign: 'right' }}>Oturum</th></tr></thead>
        <tbody>{liste.map((k, i) => (
          <tr key={k.kullanici_id}>
            <td>{i + 1}</td>
            <td><button type="button" className="hg-link" style={{ fontSize: 12.5, color: 'var(--tx)' }} onClick={() => kisiAc(tip, k.kullanici_id)}>{k.ad}</button>
              {k.okul_ad && <div className="yp-ince">{k.okul_ad}</div>}</td>
            <td style={{ textAlign: 'right' }}>{sureYaz(k.aktif_sn)}</td>
            <td style={{ textAlign: 'right' }}>{k.oturum}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  )
}

// ============================================================================ genel bakış
function GenelBakis({ v, csv, kisiAc, okulSec }) {
  const tipler = v.suzgec.okul_id != null
    ? [['ogrenci', 'Öğrenciler'], ['okul_yetkilisi', 'Okul yetkilileri'], ['toplam', 'Toplam']]
    : [['ogrenci', 'Öğrenciler'], ['okul_yetkilisi', 'Okul yetkilileri'], ['super_admin', 'Süper adminler'], ['yetkili', 'Tüm yetkililer'], ['toplam', 'Toplam']]
  const ciz = tipler.filter(([k]) => !['toplam', 'yetkili'].includes(k))
  const x = v.gunluk.map((g) => gunYaz(g.gun))
  const okulTop = v.okullar.filter((o) => o.ogrenci.toplam_sn + o.okul_yetkilisi.toplam_sn > 0)
  return (
    <>
      <div className="card"><div className="ist-kart-baslik" style={{ marginBottom: 10 }}>Toplam (herkes)</div><OzetKpileri o={v.ozet.toplam} /></div>
      <div className="ist-kartlar">
        <GrafikKarti genis baslik="Öğrenci ve yetkili karşılaştırması" aciklama="Her kullanıcı tipinin kendi kayıtlı hesap sayısına göre ölçüleri. Kişi başı değerler yalnızca sistemi kullananlar üzerinden hesaplanır."
                     sag={<button type="button" className="btn sec" onClick={() => csv('gunluk')}>Günlük CSV</button>}>
          <KarsilastirmaTablosu ozet={v.ozet} tipler={tipler} />
        </GrafikKarti>
        <GrafikKarti genis baslik="Günlük toplam aktif süre" aciklama="Dakika; kullanıcı tipine göre"
                     tablo={{ sutunlar: ['Gün', ...ciz.map(([, a]) => `${a} (dk)`)], satirlar: v.gunluk.map((g) => [g.gun, ...ciz.map(([k]) => dk(g[`${k}_sn`]))]) }}>
          <CizgiGrafik x={x} seriler={seriler(v.gunluk, ciz, 'sn', dk)} birim="dk" alan={false} />
        </GrafikKarti>
        <GrafikKarti genis baslik="Günlük aktif kişi" aciklama="O gün sistemi en az bir kez etkin kullanan kişi sayısı"
                     tablo={{ sutunlar: ['Gün', ...ciz.map(([, a]) => a)], satirlar: v.gunluk.map((g) => [g.gun, ...ciz.map(([k]) => g[`${k}_kisi`])]) }}>
          <CizgiGrafik x={x} seriler={seriler(v.gunluk, ciz, 'kisi')} birim="kişi" kesir={0} alan={false} />
        </GrafikKarti>
        {['ogrenci', 'okul_yetkilisi'].map((t) => (
          <GrafikKarti key={t} baslik={`${TIP_AD[t]}: en çok zaman geçirilen menüler`} aciklama="Toplam aktif süre (dakika); ayrıntı ilgili sekmede"
                       tablo={{ sutunlar: ['Menü', 'Dakika', 'Pay (%)'], satirlar: v.menuler[t].map((m) => [m.menu_ad, dk(m.aktif_sn), m.pay]) }}>
            <YatayCubuk veri={v.menuler[t].map((m) => ({ ad: m.menu_ad, deger: dk(m.aktif_sn), alt: `%${(m.pay ?? 0).toLocaleString('tr-TR')} · ${m.kullanici} kişi` }))} birim="dk" enFazla={10} />
          </GrafikKarti>
        ))}
        {v.suzgec.okul_id == null && (
          <GrafikKarti genis baslik="Okullara göre toplam aktif süre" aciklama="Öğrenci + okul yetkilisi, dakika. Okula tıklayınca rapor o okula süzülür."
                       tablo={{ sutunlar: ['Okul', 'Öğrenci (dk)', 'Yetkili (dk)'], satirlar: okulTop.map((o) => [o.okul_ad, dk(o.ogrenci.toplam_sn), dk(o.okul_yetkilisi.toplam_sn)]) }}>
            <YatayCubuk veri={okulTop.map((o) => ({ ad: o.okul_ad, deger: dk(o.ogrenci.toplam_sn + o.okul_yetkilisi.toplam_sn), alt: `${o.ogrenci.aktif} öğrenci · ${o.okul_yetkilisi.aktif} yetkili`, id: o.okul_id }))}
                        birim="dk" enFazla={15} onTik={(o) => okulSec(o.id)} />
          </GrafikKarti>
        )}
        {['ogrenci', 'okul_yetkilisi'].map((t) => (
          <GrafikKarti key={`e${t}`} baslik={`${TIP_AD[t]}: en çok kullananlar`} aciklama="İlk 10 kişi; ada tıklayınca ayrıntı açılır">
            <EnCokKullananlar liste={v.en_cok[t]} tip={t} kisiAc={kisiAc} />
          </GrafikKarti>
        ))}
      </div>
    </>
  )
}

// ============================================================================ tip paneli (öğrenci / okul yetkilisi / süper admin)
// Menü › alt sekme › içerik: her düzey tıklanınca bir alttakini açar. Pay, bir üst düzey içindeki paydır.
const sag = { textAlign: 'right' }
function MenuSatiri({ duzey, ad, o, pay, payBaslik, yayginlik, acilir, acik, onAc, altSayisi, altEtiket }) {
  const girinti = [0, 22, 44][duzey]
  return (
    <tr style={duzey ? { background: duzey === 1 ? 'var(--bg2, transparent)' : 'var(--bg3, var(--bg2, transparent))' } : undefined}>
      <td style={{ paddingLeft: 12 + girinti }}>
        {acilir
          ? <button type="button" className="hg-link" style={{ fontSize: duzey ? 12.5 : 13, color: 'var(--tx)', fontWeight: duzey ? 500 : 600, textAlign: 'left' }}
                    aria-expanded={acik} onClick={onAc}>{acik ? '▾' : '▸'} {ad}</button>
          : duzey ? <span>{ad}</span> : <b>{ad}</b>}
        {acilir && <span className="yp-ince"> · {altSayisi} {altEtiket}</span>}
      </td>
      <td style={sag}>{sureYaz(o.aktif_sn)}</td>
      <td style={sag} title={payBaslik}>{yuzde(pay)}</td>
      <td style={sag}>{o.kullanici}</td>
      <td style={sag}>{duzey ? '' : yuzde(yayginlik)}</td>
      <td style={sag}>{sureYaz(o.kisi_basi_sn)}</td>
      <td style={sag}>{o.ziyaret || '—'}</td>
      <td style={sag}>{o.ziyaret ? sureYaz(o.ort_ziyaret_sn) : '—'}</td>
    </tr>
  )
}

function MenuTablosu({ menuler, kisiSayisi }) {
  const [acik, setAcik] = useState({})
  const ac = (k) => setAcik((a) => ({ ...a, [k]: !a[k] }))
  if (!menuler.length) return <div className="ist-bos">Henüz veri yok</div>
  return (
    <div className="yp-tablo-kap">
      <table className="yp-tablo">
        <thead><tr>
          <th>Menü › alt sekme › içerik</th><th style={sag}>Aktif süre</th><th style={sag} title="Bir üst düzey içindeki pay">Pay</th>
          <th style={sag} title="Kullanan kişi">Kişi</th>
          <th style={sag} title={`Menüyü kullanan kişinin dönemde sistemi kullanan ${kisiSayisi} kişiye oranı`}>Yaygınlık</th>
          <th style={sag}>Kişi başı</th><th style={sag}>Ziyaret</th>
          <th style={sag} title="Her girişte ortalama kalma süresi">Ziyaret başı</th>
        </tr></thead>
        <tbody>{menuler.map((m) => (
          <Fragment key={m.menu_kod}>
            <MenuSatiri duzey={0} ad={m.menu_ad} o={m} pay={m.pay} payBaslik="Toplam süredeki payı" yayginlik={m.yayginlik}
                        acilir={m.altlar.length > 0} acik={!!acik[m.menu_kod]} onAc={() => ac(m.menu_kod)} altSayisi={m.altlar.length} altEtiket="alt sekme" />
            {acik[m.menu_kod] && m.altlar.map((a) => {
              const ak = `${m.menu_kod}|${a.alt_kod}`
              return (
                <Fragment key={ak}>
                  <MenuSatiri duzey={1} ad={a.alt_ad} o={a} pay={a.pay_menude} payBaslik={`${m.menu_ad} içindeki payı`}
                              acilir={a.detaylar?.length > 0} acik={!!acik[ak]} onAc={() => ac(ak)} altSayisi={a.detaylar?.length} altEtiket="içerik" />
                  {acik[ak] && a.detaylar.map((d) => (
                    <MenuSatiri key={d.detay_kod} duzey={2} ad={d.detay_ad} o={d} pay={d.pay_altta} payBaslik={`${a.alt_ad} içindeki payı`} />
                  ))}
                </Fragment>
              )
            })}
          </Fragment>
        ))}</tbody>
      </table>
    </div>
  )
}

function TipPaneli({ v, tip, csv, kisiAc }) {
  const o = v.ozet[tip]
  const menuler = v.menuler[tip]
  const isi = v.isi[tip].map((sat) => sat.map((s) => (s ? dk(s) : null)))
  if (tip === 'super_admin' && v.suzgec.okul_id != null) return <div className="card bos-durum">Okul süzgeci seçiliyken süper admin kullanımı gösterilmez.</div>
  return (
    <>
      <div className="card"><OzetKpileri o={o} tip={tip} /></div>
      <div className="ist-kartlar">
        <GrafikKarti genis baslik="Menü, alt sekme ve içerik ayrıntısı" aciklama="Üç düzey: menü › alt sekme › içerik (ör. İş Hayatı › Okulda Öğretilmeyenler › tek tek dersler). Ada tıklayınca bir alt düzey açılır. Pay: bir üst düzey içindeki pay."
                     sag={<button type="button" className="btn sec" onClick={() => csv('menuler')}>Menüler CSV</button>}>
          <MenuTablosu menuler={menuler} kisiSayisi={o.aktif_kullanici} />
        </GrafikKarti>
        <GrafikKarti baslik="Menülere göre aktif süre" aciklama="Dakika"
                     tablo={{ sutunlar: ['Menü', 'Dakika'], satirlar: menuler.map((m) => [m.menu_ad, dk(m.aktif_sn)]) }}>
          <YatayCubuk veri={menuler.map((m) => ({ ad: m.menu_ad, deger: dk(m.aktif_sn), alt: `${m.kullanici} kişi · ${sureYaz(m.kisi_basi_sn)} kişi başı` }))} birim="dk" enFazla={12} />
        </GrafikKarti>
        <GrafikKarti baslik="Menülerin yaygınlığı" aciklama="Menüyü kullanan kişinin, dönemde sistemi kullanan kişilere oranı"
                     tablo={{ sutunlar: ['Menü', 'Yaygınlık (%)', 'Kişi'], satirlar: menuler.map((m) => [m.menu_ad, m.yayginlik, m.kullanici]) }}>
          <YatayCubuk veri={menuler.map((m) => ({ ad: m.menu_ad, deger: m.yayginlik ?? 0, alt: `${m.kullanici} / ${o.aktif_kullanici} kişi` }))} birim="%" maks={100} enFazla={12} />
        </GrafikKarti>
        <GrafikKarti genis baslik="Gün ve saate göre kullanım" aciklama="Aktif süre, dakika (Türkiye saati)"
                     tablo={{ sutunlar: ['Gün', ...SAATLER], satirlar: GUNLER.map((g, i) => [g, ...v.isi[tip][i].map(dk)]) }}>
          <IsiHaritasi satirlar={GUNLER} sutunlar={SAATLER} degerler={isi} bicim={(x) => Math.round(x).toLocaleString('tr-TR')} satirBasligi="Gün" />
        </GrafikKarti>
        <GrafikKarti baslik="Kişi başı süre dağılımı" aciklama="Dönemdeki toplam aktif süresine göre kişi sayısı"
                     tablo={{ sutunlar: ['Süre', 'Kişi'], satirlar: o.kisi_dagilimi.map((k) => [k.ad, k.sayi]) }}>
          <SutunGrafik veri={o.kisi_dagilimi.map((k) => ({ ad: k.ad, deger: k.sayi }))} birim="kişi" kesir={0} />
        </GrafikKarti>
        <GrafikKarti baslik="Oturum süresi dağılımı" aciklama="Bir oturumda (30 dk'dan uzun ara vermeden) geçirilen aktif süre"
                     tablo={{ sutunlar: ['Süre', 'Oturum'], satirlar: o.oturum_dagilimi.map((k) => [k.ad, k.sayi]) }}>
          <SutunGrafik veri={o.oturum_dagilimi.map((k) => ({ ad: k.ad, deger: k.sayi }))} birim="oturum" kesir={0} />
        </GrafikKarti>
        <GrafikKarti baslik="Günlük seyir" aciklama="Toplam aktif süre, dakika"
                     tablo={{ sutunlar: ['Gün', 'Dakika', 'Aktif kişi'], satirlar: v.gunluk.map((g) => [g.gun, dk(g[`${tip}_sn`]), g[`${tip}_kisi`]]) }}>
          <CizgiGrafik x={v.gunluk.map((g) => gunYaz(g.gun))} seriler={[{ ad: 'Aktif süre', degerler: v.gunluk.map((g) => dk(g[`${tip}_sn`])) }]} birim="dk" />
        </GrafikKarti>
        <GrafikKarti baslik="Cihaz" aciklama="Aktif sürenin cihaz türüne göre dağılımı"
                     tablo={{ sutunlar: ['Cihaz', 'Dakika', 'Kişi'], satirlar: v.cihaz[tip].map((c) => [c.ad, dk(c.aktif_sn), c.kullanici]) }}>
          <Halka veri={v.cihaz[tip].map((c) => ({ ad: c.ad, deger: dk(c.aktif_sn) }))} birim="dk" merkezEtiket="dakika" />
        </GrafikKarti>
        {tip === 'ogrenci' && (
          <GrafikKarti genis baslik="Sınıflara göre" aciklama="Öğrencinin bugünkü sınıfına göre; katılım = kullanan / kayıtlı"
                       tablo={{ sutunlar: ['Sınıf', 'Kayıtlı', 'Kullanan', 'Katılım (%)', 'Toplam (dk)', 'Kişi başı (dk)'],
                                satirlar: v.siniflar.map((s) => [s.sinif, s.kayitli, s.aktif, s.katilim_orani, dk(s.toplam_sn), dk(s.kisi_basi_sn)]) }}>
            <YatayCubuk veri={v.siniflar.map((s) => ({ ad: s.sinif, deger: s.katilim_orani ?? 0, alt: `${s.aktif} / ${s.kayitli} öğrenci · kişi başı ${sureYaz(s.kisi_basi_sn)}` }))}
                        birim="%" maks={100} sirala={false} />
          </GrafikKarti>
        )}
        <GrafikKarti genis baslik="En çok kullananlar" aciklama="İlk 10 kişi; tüm liste Kişiler sekmesinde"
                     sag={<button type="button" className="btn sec" onClick={() => csv('kullanicilar', tip)}>Tüm kişiler CSV</button>}>
          <EnCokKullananlar liste={v.en_cok[tip]} tip={tip} kisiAc={kisiAc} />
        </GrafikKarti>
      </div>
    </>
  )
}

// ============================================================================ okullar
const OKUL_SIRALARI = {
  toplam: (o) => -(o.ogrenci.toplam_sn + o.okul_yetkilisi.toplam_sn),
  ogr_katilim: (o) => -(o.ogrenci.katilim_orani ?? -1),
  ogr_kisi: (o) => -o.ogrenci.kisi_basi_sn,
  yet_toplam: (o) => -o.okul_yetkilisi.toplam_sn,
  ad: (o) => o.okul_ad,
}
function OkullarPaneli({ v, csv, okulSec }) {
  const [sira, setSira] = useState('toplam')
  const l = [...v.okullar].sort((a, b) => { const x = OKUL_SIRALARI[sira](a), y = OKUL_SIRALARI[sira](b); return typeof x === 'string' ? x.localeCompare(y, 'tr') : x - y })
  const katilim = v.okullar.filter((o) => o.ogrenci.kayitli > 0)
  return (
    <div className="ist-kartlar">
      <GrafikKarti genis baslik="Okul okul kullanım" aciklama="Öğrenci ve okul yetkilisi ayrı. Okula tıklayınca bütün rapor o okula süzülür."
                   sag={<>
                     <Secim className="auth-input" style={{ width: 210 }} value={sira} onChange={(e) => setSira(e.target.value)} aria-label="Sıralama">
                       <option value="toplam">Toplam süreye göre</option><option value="ogr_katilim">Öğrenci katılımına göre</option>
                       <option value="ogr_kisi">Öğrenci kişi başı süreye göre</option><option value="yet_toplam">Yetkili süresine göre</option><option value="ad">Ada göre</option>
                     </Secim>
                     <button type="button" className="btn sec" onClick={() => csv('okullar')}>Okullar CSV</button>
                   </>}>
        {!l.length ? <div className="ist-bos">Henüz veri yok</div> : (
          <div className="yp-tablo-kap">
            <table className="yp-tablo">
              <thead>
                <tr><th rowSpan={2}>Okul</th><th colSpan={6} style={{ textAlign: 'center' }}>Öğrenciler</th><th colSpan={5} style={{ textAlign: 'center' }}>Okul yetkilileri</th></tr>
                <tr>
                  {['Kayıtlı', 'Kullanan', 'Katılım', 'Toplam', 'Kişi başı', 'En çok menü', 'Kayıtlı', 'Kullanan', 'Toplam', 'Kişi başı', 'En çok menü'].map((b, i) =>
                    <th key={i} style={{ textAlign: b === 'En çok menü' ? 'left' : 'right' }}>{b}</th>)}
                </tr>
              </thead>
              <tbody>{l.map((o) => (
                <tr key={o.okul_id}>
                  <td><button type="button" className="hg-link" style={{ fontSize: 12.5, color: 'var(--tx)', textAlign: 'left' }} onClick={() => okulSec(o.okul_id)}>{o.okul_ad}</button>
                    {o.demo && <span className="yp-ince"> · demo</span>}
                    {(o.ogrenci.son || o.okul_yetkilisi.son) && <div className="yp-ince">son kullanım {tarihYaz([o.ogrenci.son, o.okul_yetkilisi.son].filter(Boolean).sort().pop())}</div>}</td>
                  <td style={{ textAlign: 'right' }}>{o.ogrenci.kayitli}</td>
                  <td style={{ textAlign: 'right' }}>{o.ogrenci.aktif}</td>
                  <td style={{ textAlign: 'right' }}>{yuzde(o.ogrenci.katilim_orani)}</td>
                  <td style={{ textAlign: 'right' }}>{sureYaz(o.ogrenci.toplam_sn)}</td>
                  <td style={{ textAlign: 'right' }}>{sureYaz(o.ogrenci.kisi_basi_sn)}</td>
                  <td>{o.ogrenci.en_cok_menu || '—'}</td>
                  <td style={{ textAlign: 'right' }}>{o.okul_yetkilisi.kayitli}</td>
                  <td style={{ textAlign: 'right' }}>{o.okul_yetkilisi.aktif}</td>
                  <td style={{ textAlign: 'right' }}>{sureYaz(o.okul_yetkilisi.toplam_sn)}</td>
                  <td style={{ textAlign: 'right' }}>{sureYaz(o.okul_yetkilisi.kisi_basi_sn)}</td>
                  <td>{o.okul_yetkilisi.en_cok_menu || '—'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </GrafikKarti>
      <GrafikKarti baslik="Öğrenci katılımı" aciklama="Dönemde sistemi kullanan öğrencinin kayıtlı öğrenciye oranı"
                   tablo={{ sutunlar: ['Okul', 'Katılım (%)', 'Kullanan', 'Kayıtlı'], satirlar: katilim.map((o) => [o.okul_ad, o.ogrenci.katilim_orani, o.ogrenci.aktif, o.ogrenci.kayitli]) }}>
        <YatayCubuk veri={katilim.map((o) => ({ ad: o.okul_ad, deger: o.ogrenci.katilim_orani ?? 0, alt: `${o.ogrenci.aktif} / ${o.ogrenci.kayitli}`, id: o.okul_id }))}
                    birim="%" maks={100} enFazla={15} onTik={(o) => okulSec(o.id)} />
      </GrafikKarti>
      <GrafikKarti baslik="Öğrenci başına süre" aciklama="Sistemi kullanan öğrenci başına ortalama aktif süre, dakika"
                   tablo={{ sutunlar: ['Okul', 'Kişi başı (dk)'], satirlar: katilim.map((o) => [o.okul_ad, dk(o.ogrenci.kisi_basi_sn)]) }}>
        <YatayCubuk veri={katilim.filter((o) => o.ogrenci.aktif).map((o) => ({ ad: o.okul_ad, deger: dk(o.ogrenci.kisi_basi_sn), id: o.okul_id }))}
                    birim="dk" enFazla={15} onTik={(o) => okulSec(o.id)} />
      </GrafikKarti>
    </div>
  )
}

// ============================================================================ kişiler
function KisilerPaneli({ sorgu, csv, kisiAc, siniflar }) {
  const [f, setF] = useState({ tip: 'ogrenci', ara: '', sinif: '', yalniz: 'hepsi', siralama: 'aktif_cok' })
  const [ara, setAra] = useState('')
  const [sayfa, setSayfa] = useState(1)
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => { setSayfa(1) }, [sorgu, f])
  useEffect(() => {
    const p = new URLSearchParams(sorgu)
    Object.entries(f).forEach(([k, d]) => { if (d) p.set(k, d) })
    p.set('sayfa', sayfa); p.set('adet', 50)
    setHata(null)
    api.kullanimKisileri(p.toString()).then(setV).catch((e) => setHata(e.detail || 'Liste yüklenemedi.'))
  }, [sorgu, f, sayfa])
  const sayfaSayisi = v ? Math.max(1, Math.ceil(v.toplam / v.adet)) : 1
  return (
    <div className="card">
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
        <Secim className="auth-input" style={{ flex: '1 1 150px' }} value={f.tip} onChange={(e) => setF({ ...f, tip: e.target.value, sinif: '' })} aria-label="Kullanıcı tipi">
          {Object.entries(TIP_TEKIL).map(([k, a]) => <option key={k} value={k}>{a}</option>)}
        </Secim>
        {f.tip === 'ogrenci' && (
          <Secim className="auth-input" style={{ flex: '1 1 130px' }} value={f.sinif} onChange={(e) => setF({ ...f, sinif: e.target.value })} aria-label="Sınıf">
            <option value="">Tüm sınıflar</option>
            {siniflar.filter((s) => s.sinif !== 'Belirtilmemiş').map((s) => <option key={s.sinif} value={s.sinif}>{s.sinif}</option>)}
          </Secim>
        )}
        <Secim className="auth-input" style={{ flex: '1 1 150px' }} value={f.yalniz} onChange={(e) => setF({ ...f, yalniz: e.target.value })} aria-label="Kullanım">
          <option value="hepsi">Herkes</option><option value="kullanan">Yalnızca kullananlar</option><option value="kullanmayan">Hiç kullanmayanlar</option>
        </Secim>
        <Secim className="auth-input" style={{ flex: '1 1 170px' }} value={f.siralama} onChange={(e) => setF({ ...f, siralama: e.target.value })} aria-label="Sıralama">
          <option value="aktif_cok">En çok süre</option><option value="aktif_az">En az süre</option><option value="son">Son kullanım</option>
          <option value="oturum">Oturum sayısı</option><option value="gun">Aktif gün</option><option value="ad">Ad</option>
        </Secim>
        <input className="auth-input" style={{ flex: '2 1 200px' }} placeholder="Ad veya e-posta" value={ara} onChange={(e) => setAra(e.target.value)}
               onKeyDown={(e) => e.key === 'Enter' && setF({ ...f, ara })} />
        <button type="button" className="btn sec" onClick={() => setF({ ...f, ara })}>Ara</button>
        <button type="button" className="btn sec" onClick={() => csv('kullanicilar', f.tip)}>CSV</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v ? <div className="bos-durum yukleniyor">Yükleniyor…</div> : !v.kullanicilar.length ? <div className="bos-durum">Bu süzgeçle kişi yok.</div> : (
        <>
          <div className="yp-ince" style={{ marginBottom: 6 }}>{v.toplam.toLocaleString('tr-TR')} kişi</div>
          <div className="yp-tablo-kap">
            <table className="yp-tablo">
              <thead><tr>
                <th>Kişi</th><th style={{ textAlign: 'right' }}>Aktif süre</th><th style={{ textAlign: 'right' }}>Oturum</th>
                <th style={{ textAlign: 'right' }}>Ort. oturum</th><th style={{ textAlign: 'right' }}>Aktif gün</th>
                <th>En çok menü</th><th>Son kullanım</th><th>Son giriş</th>
              </tr></thead>
              <tbody>{v.kullanicilar.map((k) => (
                <tr key={k.kullanici_id}>
                  <td><button type="button" className="hg-link" style={{ fontSize: 12.5, color: 'var(--tx)' }} onClick={() => kisiAc(v.tip, k.kullanici_id)}>{k.ad}</button>
                    <div className="yp-ince">{[k.okul_ad, k.sinif && `${k.sinif}${k.sube ? ` / ${k.sube}` : ''}`, k.test_hesabi && 'test hesabı'].filter(Boolean).join(' · ') || k.eposta}</div></td>
                  <td style={{ textAlign: 'right' }}>{k.aktif_sn ? sureYaz(k.aktif_sn) : '—'}</td>
                  <td style={{ textAlign: 'right' }}>{k.oturum || '—'}</td>
                  <td style={{ textAlign: 'right' }}>{k.oturum ? sureYaz(k.ort_oturum_sn) : '—'}</td>
                  <td style={{ textAlign: 'right' }}>{k.aktif_gun || '—'}</td>
                  <td>{k.en_cok_menu || '—'}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>{tarihYaz(k.son_kullanim)}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>{tarihYaz(k.son_giris)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
          {sayfaSayisi > 1 && (
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', alignItems: 'center', marginTop: 10 }}>
              <button type="button" className="btn sec" disabled={sayfa <= 1} onClick={() => setSayfa(sayfa - 1)}>‹ Önceki</button>
              <span className="yp-ince">{sayfa} / {sayfaSayisi}</span>
              <button type="button" className="btn sec" disabled={sayfa >= sayfaSayisi} onClick={() => setSayfa(sayfa + 1)}>Sonraki ›</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// ============================================================================ kişi ayrıntısı
function KisiAyrintisi({ tip, id, bas, bit, onKapat }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => {
    api.kullanimKisisi(new URLSearchParams({ tip, kullanici_id: id, bas, bit }).toString()).then(setV).catch((e) => setHata(e.detail || 'Ayrıntı yüklenemedi.'))
  }, [tip, id, bas, bit])
  const k = v?.kisi
  return (
    <Pencere genis onKapat={onKapat} baslik={k ? k.ad : 'Kişi ayrıntısı'}
             altBaslik={k ? [k.tip_etiket, k.okul_ad, k.sinif && `${k.sinif}${k.sube ? ` / ${k.sube}` : ''}`, `${gunYaz(v.donem.bas)} – ${gunYaz(v.donem.bit)}`].filter(Boolean).join(' · ') : null}>
      {hata && <div className="auth-error">{hata}</div>}
      {!v ? !hata && <div className="bos-durum yukleniyor">Yükleniyor…</div> : (
        <>
          <KpiSatiri min={140}>
            <KpiKarti etiket="Aktif süre" deger={sureYaz(v.ozet.toplam_aktif_sn)} ikon="⏱️" />
            <KpiKarti etiket="Oturum" deger={v.ozet.oturum} ikon="🔁" alt={`ortalama ${sureYaz(v.ozet.ort_oturum_sn)}`} />
            <KpiKarti etiket="Aktif gün" deger={v.ozet.aktif_gun} ikon="📅" alt={`günde ortalama ${sureYaz(v.ozet.gunluk_ort_sn)}`} />
            <KpiKarti etiket="Menü ziyareti" deger={v.ozet.ziyaret} ikon="🧭" alt={`son giriş ${tarihYaz(k.son_giris)}`} />
          </KpiSatiri>
          <div className="ist-kartlar" style={{ marginTop: 14 }}>
            <GrafikKarti genis baslik="Menüler" aciklama="Menü › alt sekme › içerik; ada tıklayınca bir alt düzey açılır">
              <MenuTablosu menuler={v.menuler.map((m) => ({ ...m, yayginlik: null }))} kisiSayisi={1} />
            </GrafikKarti>
            <GrafikKarti baslik="Günlere göre" aciklama="Aktif süre, dakika"
                         tablo={{ sutunlar: ['Gün', 'Dakika'], satirlar: v.gunluk.map((g) => [g.gun, dk(g.aktif_sn)]) }}>
              <SutunGrafik veri={v.gunluk.map((g) => ({ ad: gunYaz(g.gun), deger: dk(g.aktif_sn) }))} birim="dk" degerEtiketi={false} />
            </GrafikKarti>
            <GrafikKarti baslik="Saatlere göre" aciklama="Aktif süre, dakika (Türkiye saati)"
                         tablo={{ sutunlar: ['Saat', 'Dakika'], satirlar: v.saatler.map((s, i) => [SAATLER[i], dk(s)]) }}>
              <SutunGrafik veri={v.saatler.map((s, i) => ({ ad: SAATLER[i], deger: dk(s) }))} birim="dk" degerEtiketi={false} />
            </GrafikKarti>
            <GrafikKarti genis baslik="Oturumlar" aciklama="Son 100 oturum; menüler en çok zaman geçirilenden başlayarak">
              {!v.oturumlar.length ? <div className="ist-bos">Henüz veri yok</div> : (
                <div className="yp-tablo-kap">
                  <table className="yp-tablo">
                    <thead><tr><th>Başlangıç</th><th>Bitiş</th><th style={{ textAlign: 'right' }}>Aktif süre</th><th>Cihaz</th><th>Menüler</th></tr></thead>
                    <tbody>{v.oturumlar.map((o, i) => (
                      <tr key={i}>
                        <td style={{ whiteSpace: 'nowrap' }}>{tarihYaz(o.bas)}</td>
                        <td style={{ whiteSpace: 'nowrap' }}>{tarihYaz(o.bit)}</td>
                        <td style={{ textAlign: 'right' }}>{sureYaz(o.aktif_sn)}</td>
                        <td>{o.cihaz}</td>
                        <td>{o.menuler.join(', ')}{o.menu_sayisi > o.menuler.length ? ` +${o.menu_sayisi - o.menuler.length}` : ''}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </GrafikKarti>
          </div>
        </>
      )}
    </Pencere>
  )
}
