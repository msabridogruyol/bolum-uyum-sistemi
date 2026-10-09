// [2026-10-09] Öğrenci detayı → "Cevap analizi" (YALNIZCA süper admin).
// Her soruya verilen cevap, bu cevabın hangi özelliğe kaç puan kattığı, özellik puanlarının nasıl oluştuğu
// ve özelliklerin bölüm önerilerini nasıl etkilediği.
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { tarih } from './ortak'

const renk = (p) => (p == null ? 'var(--tx3)' : p >= 60 ? 'var(--gr)' : p <= 40 ? 'var(--re)' : 'var(--tx2)')
const zemin = (p) => (p == null ? 'var(--sur2)' : p >= 60 ? 'var(--grl)' : p <= 40 ? 'var(--rel)' : 'var(--sur2)')
const sayi = (v, o = 1) => (v == null ? '—' : Number(v).toLocaleString('tr-TR', { maximumFractionDigits: o }))

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

export default function CevapAnaliziSekmesi({ ogrenciId }) {
  const [d, setD] = useState(null)
  const [hata, setHata] = useState(null)
  const [turNo, setTurNo] = useState(null)
  const [gorunum, setGorunum] = useState('cevap')
  const [katman, setKatman] = useState('')
  const [ozellikId, setOzellikId] = useState(null)
  const [arama, setArama] = useState('')

  useEffect(() => {
    setD(null); setHata(null)
    api.cevapAnalizi(ogrenciId, turNo).then(setD).catch((e) => setHata(e.detail || 'Cevap analizi alınamadı.'))
  }, [ogrenciId, turNo])

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

  const katmanlar = [...new Set(d.cevaplar.map((c) => c.katman))]
  const kontroller = d.cevaplar.filter((c) => c.kontrol)
  const ozellikGoster = (id) => { setOzellikId(id); setKatman(''); setArama(''); setGorunum('cevap') }
  const maxEtki = Math.max(0.0001, ...d.etki.flatMap((e) => [...e.yukari, ...e.asagi].map((k) => Math.abs(k.etki))))

  return (
    <div>
      <div className="ca-bilgi">
        🔒 Bu bölümü yalnızca süper admin görür; her görüntüleme Audit Log'a yazılır.
      </div>
      <div className="ca-ust">
        {d.turlar.length > 1 && (
          <select className="yp-sec" value={d.tur.tur_no} onChange={(e) => setTurNo(Number(e.target.value))}>
            {d.turlar.map((t) => <option key={t.tur_no} value={t.tur_no}>{t.tur_no}. değerlendirme{t.durum !== 'tamamlandi' ? ' (devam ediyor)' : ''}</option>)}
          </select>
        )}
        <span className="yp-ince">
          {d.cevaplar.length} cevap · {d.ozellikler.length} özellik
          {kontroller.length > 0 && ` · dikkat kontrolü ${kontroller.filter((c) => c.kontrol.dogru).length}/${kontroller.length} doğru`}
        </span>
      </div>
      <div className="yp-sekmeler" style={{ marginTop: 6 }}>
        {[['cevap', `Cevaplar (${d.cevaplar.length})`], ['ozellik', 'Özellik puanları'], ['etki', 'Sonuca etkisi']].map(([k, ad]) => (
          <button key={k} className={gorunum === k ? 'aktif' : ''} onClick={() => setGorunum(k)}>{ad}</button>
        ))}
      </div>

      {gorunum === 'cevap' && (
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
            </div>
          )}
          {liste.length === 0 && <div className="bos-durum">Bu filtreye uyan cevap yok.</div>}
          {liste.map((c) => <CevapKarti key={c.sira} c={c} onOzellik={ozellikGoster} />)}
        </>
      )}

      {gorunum === 'ozellik' && (
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

      {gorunum === 'etki' && (
        <>
          <div className="yp-ince" style={{ margin: '0 0 12px', lineHeight: 1.55 }}>
            İlk 5 öneri ve her birinde bölümü <b>diğer bölümlere göre</b> öne çıkaran ya da geri çeken özellikler.
            Değer = özellik ağırlığı × (öğrencinin bu bölümle uyumu − tüm bölümlerle ortalama uyumu), uyum puanı cinsinden.
            Öğrenci profili K1–K4 içinde göreli ölçeklendiği için "öğrenci" sütunu ham puanı gösterir. Özelliğe tıklayınca o cevaplar açılır.
          </div>
          {d.not && <div className="yp-uyari">{d.not}</div>}
          {d.etki.map((e, i) => (
            <div key={e.bolum_id} className="ca-etki">
              <div className="ca-etki-bas"><span className="ca-no">{i + 1}</span><b>{e.bolum}</b><span className="ca-etki-uyum">%{sayi(e.uyum, 0)}</span></div>
              <div className="ca-etki-iki">
                {[['Öne çıkaran', e.yukari, 'var(--gr)'], ['Geri çeken', e.asagi, 'var(--re)']].map(([baslik, l, r]) => (
                  <div key={baslik}>
                    <div className="ca-etki-baslik" style={{ color: r }}>{baslik}</div>
                    {l.length === 0 && <div className="yp-ince">—</div>}
                    {l.map((k) => (
                      <button key={k.id} className="ca-etki-satir" onClick={() => ozellikGoster(k.id)}
                        title={`Öğrenci: ${sayi(k.ogrenci_puan, 0)} · Bölüm beklentisi (ölçekli): ${sayi(k.bolum_beklenti, 0)} · Uyum: ${sayi(k.uyum, 0)}`}>
                        <span className="ca-etki-ad"><b>{k.kod}</b> {k.ad}</span>
                        <span className="ca-etki-bar"><span style={{ width: `${(Math.abs(k.etki) / maxEtki) * 100}%`, background: r }} /></span>
                        <span className="ca-etki-deger" style={{ color: r }}>{k.etki > 0 ? '+' : ''}{sayi(k.etki, 2)}</span>
                        <span className="yp-ince ca-etki-ogr">öğrenci {sayi(k.ogrenci_puan, 0)}</span>
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  )
}
