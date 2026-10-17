// [2026-10-09] Öğrenci detayı → "Cevap analizi". [2026-10-17] Süper admin VE okul yetkilisi (kendi okulu); öğrenci görmez.
// Cevaptan bölüm sonucuna kadar izlenebilir üç matris:
//   Uyum matrisi (özellik × bölüm) — fark (öğrenci − bölüm beklentisi) ya da katkı ("bu özellik olmasaydı")
//   Neden yüksek / düşük — her bölümde puanı en çok yükselten ve düşüren özellikler
//   Cevap matrisi (soru × özellik) — her cevabın her özelliğe katkısı; matristeki bir hücreye tıklayınca o cevaplar açılır
//   Yöntem matrisi (bölüm × 10 ÇKKV yöntemi + Kendall W) — yalnızca süper admin
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { tarih } from './ortak'
import { gelisimeAcikMi, gucluMu } from '../../yardimci/seviye'

// [2026-10-10] Özellik puanı bantları (Güçlü 62+, Gelişime açık 40 altı)
const renk = (p) => (p == null ? 'var(--tx3)' : gucluMu(p) ? 'var(--gr)' : gelisimeAcikMi(p) ? 'var(--re)' : 'var(--tx2)')
const zemin = (p) => (p == null ? 'var(--sur2)' : gucluMu(p) ? 'var(--grl)' : gelisimeAcikMi(p) ? 'var(--rel)' : 'var(--sur2)')
const sayi = (v, o = 1) => (v == null ? '—' : Number(v).toLocaleString('tr-TR', { maximumFractionDigits: o }))
const isaretli = (v, o = 1) => {
  if (v == null) return '—'
  const r = Math.round(v * 10 ** o) / 10 ** o
  return r === 0 ? '0' : `${r > 0 ? '+' : ''}${sayi(r, o)}`
}
// [2026-10-17] Fark renkleri (öğrencinin "Sen ve Bölümün" ekranıyla aynı): uyumlu yeşil · fazla / az turuncu · belirgin kırmızı
const FARK_ZEMIN = { yesil: 'var(--grl)', turuncu: 'var(--aml)', kirmizi: 'var(--rel)' }
const FARK_RENK = { yesil: 'var(--gr)', turuncu: 'var(--am)', kirmizi: 'var(--re)' }
const SINIF_AD = { uyumlu: 'uyumlu', fazla: 'beklenenden fazla', belirgin_fazla: 'belirgin fazla', eksik: 'beklenenden az', belirgin_eksik: 'belirgin az' }
const katkiZemin = (k) => (k >= 0.5 ? 'var(--grl)' : k <= -0.5 ? 'var(--rel)' : 'transparent')
const katkiRenk = (k) => (k >= 0.5 ? 'var(--gr)' : k <= -0.5 ? 'var(--re)' : 'var(--tx3)')
const kisaAd = (ad) => {
  const s = String(ad || '').toLocaleLowerCase('tr').replace(/(^|\s)\S/g, (h) => h.toLocaleUpperCase('tr'))
  return s.length > 26 ? `${s.slice(0, 24)}…` : s
}

function KatkiCip({ k, onTik }) {
  return (
    <button className="ca-katki" style={{ background: zemin(k.puan), color: renk(k.puan) }} onClick={() => onTik?.(k.id)}
      title={`${k.ad} (${k.katman}) — bu cevabın katkısı: ${sayi(k.puan)} / 100`}>
      <b>{k.kod}</b> {k.ad} <span>{sayi(k.puan, 0)}</span>
    </button>
  )
}

function CevapKarti({ c, onOzellik }) {
  const encok = c.cevap_bicimi === 'encok_enaz'
  return (
    <div className="ca-cevap">
      <div className="ca-cevap-ust">
        <span className="ca-no">#{c.sira}</span>
        <span className="ca-etiket">{c.katman}</span>
        <span className="ca-etiket">{c.tip_ad}{encok ? ' · en çok / en az' : ''}{c.ters ? ' · ters kodlu' : ''}</span>
        <span className="yp-ince" style={{ marginLeft: 'auto' }}>{tarih(c.zaman)}</span>
      </div>
      <div className="ca-soru">{c.soru}</div>
      <div className="ca-secenekler">
        {c.secenekler.map((s) => (
          <div key={s.id} className={`ca-secenek${s.secildi ? ' secildi' : ''}${s.en_az ? ' enaz' : ''}`}>
            <span className="ca-isaret">{s.secildi ? (encok ? 'EN ÇOK' : '✓') : s.en_az ? 'EN AZ' : s.sira}</span>
            <span>{s.metin}</span>
          </div>
        ))}
      </div>
      {c.kontrol ? (
        <div className={`ca-kontrol ${c.kontrol.dogru ? 'dogru' : 'yanlis'}`}>
          Dikkat kontrolü — beklenen: {c.kontrol.beklenen}. şık · verilen: {c.kontrol.verilen}. şık {c.kontrol.dogru ? '✓ doğru' : '✗ yanlış'} · puanlamaya girmez, güven skorunu etkiler
        </div>
      ) : (
        <div className="ca-katkilar">
          <span className="yp-ince" style={{ fontWeight: 700 }}>Katkı:</span>
          {c.katkilar.length ? c.katkilar.map((k) => <KatkiCip key={k.id} k={k} onTik={onOzellik} />) : <span className="yp-ince">puanlamaya katkısı yok</span>}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------- Uyum matrisi (özellik × bölüm)
function UyumMatrisi({ m, kip, setKip, onOzellik, bolumListesi, onBolumEkle, onVarsayilan, ozelSecim }) {
  const [ekle, setEkle] = useState('')
  const katmanlar = [...new Set(m.ozellikler.map((o) => o.katman))]
  const ekleGonder = (e) => {
    e.preventDefault()
    const b = bolumListesi.find((x) => x.ad.toLocaleLowerCase('tr') === ekle.trim().toLocaleLowerCase('tr'))
    if (b) { onBolumEkle(b.id); setEkle('') }
  }
  return (
    <>
      <div className="ca-matris-ust">
        <div className="ca-anahtar">
          {[['fark', 'Fark (öğrenci − bölüm)'], ['katki', 'Katkı (bu özellik olmasaydı)']].map(([k, ad]) => (
            <button key={k} className={`ca-cip${kip === k ? ' aktif' : ''}`} onClick={() => setKip(k)}>{ad}</button>
          ))}
        </div>
        <form className="ca-bolum-ekle" onSubmit={ekleGonder}>
          <input className="auth-input" list="ca-bolumler" placeholder="Bölüm ekle…" value={ekle} onChange={(e) => setEkle(e.target.value)} />
          <datalist id="ca-bolumler">{bolumListesi.map((b) => <option key={b.id} value={b.ad} />)}</datalist>
          <button className="yp-mini" type="submit">Ekle</button>
          {ozelSecim && <button className="yp-mini" type="button" onClick={onVarsayilan}>Varsayılana dön</button>}
        </form>
      </div>
      <div className="ca-lejant">
        {kip === 'fark' ? (
          <>
            <span><i style={{ background: FARK_ZEMIN.yesil }} /> uyumlu (|fark| &lt; 5)</span>
            <span><i style={{ background: FARK_ZEMIN.turuncu }} /> fazla / az (5–15)</span>
            <span><i style={{ background: FARK_ZEMIN.kirmizi }} /> belirgin fazla / az (15+)</span>
            <span>Artı: öğrenci bölümün beklediğinden yüksek · eksi: düşük</span>
          </>
        ) : (
          <>
            <span><i style={{ background: 'var(--grl)' }} /> puanı yükseltiyor</span>
            <span><i style={{ background: 'var(--rel)' }} /> puanı düşürüyor</span>
            <span>Değer: bu özellik hesaba katılmasaydı uyum puanı bu kadar değişirdi</span>
          </>
        )}
        <span>Hücreye tıklayınca o özelliği oluşturan cevaplar açılır.</span>
      </div>
      <div className="ca-matris-kap">
        <table className="ca-matris">
          <thead>
            <tr>
              <th className="ca-m-ozellik">Özellik</th>
              <th title="Öğrencinin bu özellikteki değeri (katman içi ölçek, 50 = profilinin ortası)">Öğrenci</th>
              {m.bolumler.map((b) => (
                <th key={b.bolum_id} className={b.hedef ? 'hedef' : ''} title={b.bolum}>
                  <span className="ca-m-sira">{b.sira}.</span> {kisaAd(b.bolum)}
                  <span className="ca-m-uyum">%{sayi(b.uyum, 0)}{b.hedef ? ' · 🎯' : ''}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {katmanlar.map((k) => (
              <FragmentKatman key={k} katman={k} m={m} kip={kip} onOzellik={onOzellik} />
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

function FragmentKatman({ katman, m, kip, onOzellik }) {
  const satirlar = m.ozellikler.map((o, j) => ({ o, j })).filter((x) => x.o.katman === katman)
  return (
    <>
      <tr className="ca-m-grup"><td colSpan={2 + m.bolumler.length}>{katman}</td></tr>
      {satirlar.map(({ o, j }) => (
        <tr key={o.id}>
          <td className="ca-m-ozellik"><button onClick={() => onOzellik(o.id)} title={`Ağırlık %${sayi(o.agirlik, 2)}`}><b>{o.kod}</b> {o.ad}</button></td>
          <td className="ca-m-ogr">{sayi(o.ogrenci, 0)}</td>
          {m.bolumler.map((b) => {
            const h = b.hucreler[j]
            const deger = kip === 'fark' ? isaretli(h.fark, 0) : isaretli(h.katki, 1)
            return (
              <td key={b.bolum_id} className="ca-m-hucre"
                style={kip === 'fark' ? { background: FARK_ZEMIN[h.renk], color: FARK_RENK[h.renk] } : { background: katkiZemin(h.katki), color: katkiRenk(h.katki) }}
                onClick={() => onOzellik(o.id)}
                title={`${b.bolum} · ${o.ad}\nÖğrenci ${sayi(o.ogrenci, 0)} · bölüm beklentisi ${sayi(h.bolum, 0)} · fark ${isaretli(h.fark, 0)} (${SINIF_AD[h.sinif]})\nKatkı: ${isaretli(h.katki, 2)} puan`}>
                {deger}
              </td>
            )
          })}
        </tr>
      ))}
    </>
  )
}

// ---------------------------------------------------------------- Neden yüksek / düşük
function NedenDokumu({ m, onOzellik }) {
  const maks = Math.max(0.0001, ...m.bolumler.flatMap((b) => [...b.yukselten, ...b.dusuren].map((x) => Math.abs(x.katki))))
  return m.bolumler.map((b) => (
    <div key={b.bolum_id} className="ca-etki">
      <div className="ca-etki-bas">
        <span className="ca-no">{b.sira}</span><b>{b.bolum}</b>{b.hedef && <span className="ca-etiket">🎯 hedef</span>}
        <span className="ca-etki-uyum">%{sayi(b.uyum, 0)}</span>
      </div>
      {b.k5_katkisi != null && (
        <div className="yp-ince" style={{ marginBottom: 8 }}>Alan derinleşme (K5) katkısı: <b>{isaretli(b.k5_katkisi, 1)}</b> puan (özellik katkılarına ek olarak)</div>
      )}
      <div className="ca-etki-iki">
        {[['Puanı yükselten', b.yukselten, 'var(--gr)'], ['Puanı düşüren', b.dusuren, 'var(--re)']].map(([baslik, l, r]) => (
          <div key={baslik}>
            <div className="ca-etki-baslik" style={{ color: r }}>{baslik}</div>
            {l.length === 0 && <div className="yp-ince">—</div>}
            {l.map((x) => {
              const o = m.ozellikler[x.j]
              const h = b.hucreler[x.j]
              return (
                <button key={o.id} className="ca-etki-satir" onClick={() => onOzellik(o.id)}
                  title={`Öğrenci ${sayi(o.ogrenci, 0)} · bölüm beklentisi ${sayi(h.bolum, 0)} · fark ${isaretli(h.fark, 0)}`}>
                  <span className="ca-etki-ad"><b>{o.kod}</b> {o.ad}</span>
                  <span className="ca-etki-bar"><span style={{ width: `${(Math.abs(x.katki) / maks) * 100}%`, background: r }} /></span>
                  <span className="ca-etki-deger" style={{ color: r }}>{isaretli(x.katki, 2)}</span>
                  <span className="ca-etki-ogr" style={{ color: FARK_RENK[h.renk] }}>{SINIF_AD[h.sinif]}</span>
                </button>
              )
            })}
          </div>
        ))}
      </div>
    </div>
  ))
}

// ---------------------------------------------------------------- [2026-10-17] Hedefle kıyas (raporlardaki bölümle aynı hesap)
const KIYAS_SINIF = { uyumlu: 'uyumlu', fazla: 'fazla', eksik: 'az', belirgin_fazla: 'belirgin fazla', belirgin_eksik: 'belirgin az' }
function KiyasOzellikleri({ xs, hedefli, onOzellik }) {
  if (!xs?.length) return <div className="yp-ince">—</div>
  return xs.map((x) => (
    <button key={x.kod} className="ca-etki-satir" style={{ gridTemplateColumns: '1fr auto' }} onClick={() => onOzellik?.(x.kod)}>
      <span className="ca-etki-ad"><b>{x.kod}</b> {x.ad}</span>
      <span className="yp-ince">{hedefli ? `hedefte ${KIYAS_SINIF[x.hedef_sinif]} · burada ${KIYAS_SINIF[x.bolum_sinif]}` : KIYAS_SINIF[x.bolum_sinif]}</span>
    </button>
  ))
}

function HedefKiyasi({ k, onOzellik }) {
  if (!k) return <div className="bos-durum">Kıyas hesaplanamadı.</div>
  const hd = k.hedef
  return (
    <>
      {hd ? (
        <div className="ca-kiyas-hedef">🎯 <b>Hedef: {hd.bolum}</b> · uyum %{sayi(hd.uyum, 0)} · {k.bolum_sayisi} bölüm içinde {hd.sira}. sırada</div>
      ) : (
        <div className="yp-uyari">⚠ Öğrenci hedef bölüm seçmemiş; kıyas yapılamıyor. Aşağıda seçili bölümlerde puanı en çok etkileyen özellikler var.</div>
      )}
      <div className="yp-ince" style={{ margin: '0 0 12px', lineHeight: 1.55 }}>
        {hd
          ? 'Puan farkı = hedefin uyumu − bölümün uyumu. Özellik etkisi = hedefteki katkı − bölümdeki katkı ("bu özellik olmasaydı"; gösterilen puanla aynı hesap). Raporlardaki "Hedef bölüm kıyası" bu hesaptır. Bölüm eklemek için Uyum matrisi sekmesini kullanın.'
          : 'Hedef seçildiğinde her bölüm hedefe göre kıyaslanır.'}
      </div>
      {k.satirlar.map((s) => {
        const f = s.fark ?? 0
        return (
          <div key={s.bolum_id} className="ca-etki">
            <div className="ca-etki-bas">
              <span className="ca-no">{s.sira}</span><b>{s.bolum}</b>
              <span className="ca-etki-uyum">%{sayi(s.uyum, 0)}</span>
              {hd && <span className="ca-kiyas-fark" style={{ color: Math.abs(f) < 0.5 ? 'var(--tx2)' : f < 0 ? 'var(--re)' : 'var(--gr)' }}>
                {Math.abs(f) < 0.5 ? 'hedefle eşit' : f < 0 ? `hedef ${sayi(-f, 0)} puan geride` : `hedef ${sayi(f, 0)} puan önde`}
              </span>}
            </div>
            <div className="ca-etki-iki">
              <div>
                <div className="ca-etki-baslik" style={{ color: 'var(--re)' }}>{hd ? 'Hedefi geride bırakan' : 'Puanı düşüren'}</div>
                <KiyasOzellikleri xs={hd ? s.geride_birakan : s.dusuren} hedefli={!!hd} onOzellik={onOzellik} />
              </div>
              <div>
                <div className="ca-etki-baslik" style={{ color: 'var(--gr)' }}>{hd ? 'Hedefi öne çıkaran' : 'Puanı yükselten'}</div>
                <KiyasOzellikleri xs={hd ? s.one_cikaran : s.yukselten} hedefli={!!hd} onOzellik={onOzellik} />
              </div>
            </div>
          </div>
        )
      })}
    </>
  )
}

// ---------------------------------------------------------------- Yöntem matrisi (yalnızca süper admin)
function YontemMatrisi({ m }) {
  return (
    <div className="ca-matris-kap">
      <table className="ca-matris ca-yontem">
        <thead>
          <tr><th className="ca-m-ozellik">Bölüm</th><th>Uyum</th>{m.yontem_adlari.map((a) => <th key={a}>{a}</th>)}<th title="10 yöntemin sıralamada ne kadar hemfikir olduğu (1 = tam)">Kendall W</th></tr>
        </thead>
        <tbody>
          {m.bolumler.map((b) => (
            <tr key={b.bolum_id}>
              <td className="ca-m-ozellik"><span className="ca-m-sira">{b.sira}.</span> {kisaAd(b.bolum)}{b.hedef ? ' 🎯' : ''}</td>
              <td className="ca-m-ogr">{sayi(b.toplam_uyum, 1)}</td>
              {m.yontem_adlari.map((a) => <td key={a} className="ca-m-hucre">{sayi(b.yontemler?.[a], 1)}</td>)}
              <td className="ca-m-hucre">{sayi(b.kendall_w, 3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function CevapAnaliziSekmesi({ ogrenciId }) {
  const [d, setD] = useState(null)
  const [hata, setHata] = useState(null)
  const [turNo, setTurNo] = useState(null)
  const [secim, setSecim] = useState(null)   // null = varsayılan (ilk 10 + hedef + son 3)
  const [eklenen, setEklenen] = useState([])  // sonradan eklenen bölümler raporda öncelikli
  const [gorunum, setGorunum] = useState('matris')
  const [kip, setKip] = useState('fark')
  const [katman, setKatman] = useState('')
  const [ozellikId, setOzellikId] = useState(null)
  const [arama, setArama] = useState('')
  const [bolumListesi, setBolumListesi] = useState([])
  const [indiriliyor, setIndiriliyor] = useState(false)

  useEffect(() => {
    setHata(null)
    api.cevapAnalizi(ogrenciId, turNo, secim).then(setD).catch((e) => setHata(e.detail || 'Cevap analizi alınamadı.'))
  }, [ogrenciId, turNo, secim])
  useEffect(() => { api.yonetimBolumler().then(setBolumListesi).catch(() => setBolumListesi([])) }, [])

  const ozellikAdi = useMemo(() => Object.fromEntries((d?.ozellikler || []).map((o) => [o.id, `${o.kod} ${o.ad}`])), [d])
  const liste = useMemo(() => {
    if (!d) return []
    const q = arama.trim().toLocaleLowerCase('tr')
    return d.cevaplar.filter((c) => (!katman || c.katman === katman)
      && (!ozellikId || c.katkilar.some((k) => k.id === ozellikId))
      && (!q || `${c.soru} ${c.secenekler.map((s) => s.metin).join(' ')}`.toLocaleLowerCase('tr').includes(q)))
  }, [d, katman, ozellikId, arama])

  if (hata) return <div className="auth-error">{hata}</div>
  if (!d) return <div className="bos-durum">Cevaplar yükleniyor…</div>
  if (!d.tur) return <div className="bos-durum">{d.not}</div>

  const m = d.matris
  const katmanlar = [...new Set(d.cevaplar.map((c) => c.katman))]
  const kontroller = d.cevaplar.filter((c) => c.kontrol)
  const ozellikGoster = (id) => { setOzellikId(id); setKatman(''); setArama(''); setGorunum('cevap') }
  const sekmeler = [
    ...(m ? [['matris', 'Uyum matrisi'], ['kiyas', '🎯 Hedefle kıyas'], ['neden', 'Neden yüksek / düşük']] : []),
    ['cevap', `Cevaplar (${d.cevaplar.length})`], ['ozellik', 'Özellik puanları'],
    ...(m?.yontem_adlari ? [['yontem', '🔒 Yöntemler']] : []),
  ]
  const aktif = sekmeler.some(([k]) => k === gorunum) ? gorunum : sekmeler[0][0]
  // [2026-10-17] Ekrandaki bölümlerle yönetici raporu: hedef + ilk 5 (sunucu en çok 6 bölüm alır)
  async function rapor() {
    setIndiriliyor(true)
    try {
      const idler = [...new Set([...eklenen, ...m.bolumler.map((b) => b.bolum_id)])]
      await api.ogrenciRaporuIndir(ogrenciId, 'yonetici', 'pdf', true, idler)
    } catch (e) { setHata(e.detail || 'Rapor indirilemedi.') } finally { setIndiriliyor(false) }
  }
  async function excel() {
    setIndiriliyor(true)
    try { await api.cevapAnaliziExcel(ogrenciId, d.tur.tur_no) } catch (e) { setHata(e.detail || 'Excel indirilemedi.') } finally { setIndiriliyor(false) }
  }

  return (
    <div>
      <div className="ca-bilgi">
        🔒 Öğrencinin değerlendirme cevapları kişisel veridir. Bu bölümü yalnızca okulunuzun yetkilisi ve sistem yöneticisi görür; öğrenci görmez. Her görüntüleme ve indirme işlem kaydına yazılır.
      </div>
      <div className="ca-ust">
        {d.turlar.length > 1 && (
          <select className="yp-sec" value={d.tur.tur_no} onChange={(e) => { setTurNo(Number(e.target.value)); setSecim(null); setEklenen([]) }}>
            {d.turlar.map((t) => <option key={t.tur_no} value={t.tur_no}>{t.tur_no}. değerlendirme{t.durum !== 'tamamlandi' ? ' (devam ediyor)' : ''}</option>)}
          </select>
        )}
        <span className="yp-ince">
          {d.cevaplar.length} cevap · {d.ozellikler.length} özellik
          {kontroller.length > 0 && ` · dikkat kontrolü ${kontroller.filter((c) => c.kontrol.dogru).length}/${kontroller.length} doğru`}
        </span>
        {m && <button className="yp-mini" style={{ marginLeft: 'auto' }} onClick={rapor} disabled={indiriliyor}
          title="Yönetim raporu: hedef + eklediğiniz bölümler + ekrandaki ilk bölümler (en çok 6, hedef dahil)">📄 Bu bölümlerle rapor</button>}
        <button className="yp-mini" style={m ? undefined : { marginLeft: 'auto' }} onClick={excel} disabled={indiriliyor}>{indiriliyor ? 'Hazırlanıyor…' : '📊 Excel (tüm matrisler)'}</button>
      </div>
      {d.okuma_notu && m && <div className="yp-ince ca-okuma">{d.okuma_notu}</div>}
      {d.not && <div className="yp-uyari">{d.not}</div>}
      <div className="yp-sekmeler" style={{ marginTop: 6 }}>
        {sekmeler.map(([k, ad]) => <button key={k} className={aktif === k ? 'aktif' : ''} onClick={() => setGorunum(k)}>{ad}</button>)}
      </div>

      {aktif === 'matris' && m && (
        <UyumMatrisi m={m} kip={kip} setKip={setKip} onOzellik={ozellikGoster} bolumListesi={bolumListesi} ozelSecim={secim !== null}
          onBolumEkle={(id) => { setEklenen([...eklenen.filter((x) => x !== id), id]); setSecim([...new Set([...m.bolumler.map((b) => b.bolum_id), id])]) }}
          onVarsayilan={() => { setSecim(null); setEklenen([]) }} />
      )}
      {aktif === 'kiyas' && m && (
        <HedefKiyasi k={m.kiyas} onOzellik={(kod) => { const o = m.ozellikler.find((x) => x.kod === kod); if (o) ozellikGoster(o.id) }} />
      )}
      {aktif === 'neden' && m && (
        <>
          <div className="yp-ince" style={{ margin: '0 0 12px', lineHeight: 1.55 }}>
            Her bölümde puanı en çok yükselten ve düşüren özellikler. Katkı = bu özellik hesaba katılmasaydı uyum puanı ne kadar değişirdi
            (gösterilen puanla aynı hesap). Puan ve katkı göreli: 301 bölüm içinde öğrenciye yakınlık. Farkı olan bir özellik, öğrenci o
            özellikte bu bölüme diğer bölümlerin çoğundan daha yakınsa puanı yine yükseltebilir. Özelliğe tıklayınca o cevaplar açılır.
          </div>
          <NedenDokumu m={m} onOzellik={ozellikGoster} />
        </>
      )}
      {aktif === 'yontem' && m?.yontem_adlari && (
        <>
          <div className="yp-ince" style={{ margin: '0 0 12px' }}>Her yöntemin 0–100'e ölçeklenmiş puanı; uyum = 10 yöntemin ortalaması. Yalnızca sistem yöneticisi görür.</div>
          <YontemMatrisi m={m} />
        </>
      )}

      {aktif === 'cevap' && (
        <>
          <div className="ca-filtre">
            <button className={`ca-cip${!katman ? ' aktif' : ''}`} onClick={() => setKatman('')}>Tümü</button>
            {katmanlar.map((k) => <button key={k} className={`ca-cip${katman === k ? ' aktif' : ''}`} onClick={() => setKatman(k)}>{k}</button>)}
            <input className="auth-input" style={{ margin: 0, flex: '1 1 160px', padding: '7px 10px', fontSize: 12.5 }} placeholder="Soru veya şıkta ara…" value={arama} onChange={(e) => setArama(e.target.value)} />
          </div>
          {ozellikId && (
            <div className="ca-aktif-filtre">
              Yalnızca <b>{ozellikAdi[ozellikId]}</b> özelliğine katkı veren cevaplar
              <button className="yp-mini" onClick={() => setOzellikId(null)}>Filtreyi kaldır ✕</button>
              {m && <button className="yp-mini" onClick={() => setGorunum('matris')}>← Matrise dön</button>}
            </div>
          )}
          {liste.length === 0 && <div className="bos-durum">Bu filtreye uyan cevap yok.</div>}
          {liste.map((c) => <CevapKarti key={c.sira} c={c} onOzellik={ozellikGoster} />)}
        </>
      )}

      {aktif === 'ozellik' && (
        <>
          <div className="yp-ince" style={{ margin: '0 0 10px', lineHeight: 1.5 }}>
            Özellik puanı = o özelliğe katkı veren cevapların ortalaması (0–100). Satıra tıklayınca o cevaplar listelenir.
          </div>
          <div className="ca-ozellikler">
            {d.ozellikler.map((o) => (
              <button key={o.id} className="ca-ozellik" onClick={() => o.cevap_sayisi && ozellikGoster(o.id)} disabled={!o.cevap_sayisi}>
                <span className="ca-oz-ad"><b>{o.kod}</b> {o.ad}{o.dal ? <span className="yp-ince"> · {o.dal}</span> : null}</span>
                <span className="ca-oz-bar"><span style={{ width: `${o.puan ?? 0}%`, background: renk(o.puan) }} /></span>
                <span className="ca-oz-puan" style={{ color: renk(o.puan) }}>{sayi(o.puan, 0)}</span>
                <span className="yp-ince ca-oz-sayi">{o.cevap_sayisi} cevap</span>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
