// [2026-10-13] İş Hayatı → 'mulakatsim' sekmesi: Mülakat Simülasyonu.
// Görüntülü görüşme düzeni: üstte mülakatçı soruyu sorar, altta iki aday (Aday 1 / Aday 2) düşünür ve cevap verir.
// Öğrenci daha iyi cevap verdiğini düşündüğü adayı seçer; ardından iki cevabın neden güçlü / zayıf olduğu, mülakatçının tercihi
// (ya da 'ikisi_de' sorularda iki yaklaşımın sonucu) ve "Alandan bir bilgi" gösterilir. Sonda kısa özet + öğrenilenler.
// Amaç bilgi sınavı değil, mesleğe ön bakış: doğru cevap adayların gerekçesinden mantıkla bulunabilir.
// Uçlar: GET /ogrenci/is-hayati/mulakat-sim/{bolum_id}, POST /ogrenci/is-hayati/mulakat-sim (backend/app/api/is_hayati_mulakat_sim.py)
import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'

const ADAYLAR = [{ ad: 'Aday 1', yuz: '🧑🏽' }, { ad: 'Aday 2', yuz: '🧑🏼‍🦱' }]
const azHareket = () => typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function Baslangic({ v, onBasla }) {
  return (
    <div className="card msim-giris">
      <div className="msim-giris-ust">
        <span className="msim-giris-yuz" aria-hidden="true">🧑🏻‍💼</span>
        <div>
          <h3 className="msim-giris-baslik">{v.pozisyon} görüşmesi</h3>
          <div className="msim-giris-rol">Mülakatı yapan: {v.mulakatci}</div>
        </div>
      </div>
      <p className="msim-giris-metin">
        Mülakatçı bu meslekte gerçekten karşılaşılan {v.sorular.length} durum soracak; iki aday farklı yollarla cevap verecek.
        Sen de hangisinin daha iyi cevap verdiğini seç. Alanı bilmen gerekmiyor: adayların gerekçelerini dinle, mantığına güven.
        Her sorudan sonra bu meslekte işin nasıl yapıldığını göreceksin.
      </p>
      <div className="msim-konular">
        {v.sorular.map((q) => <span key={q.no} className="msim-konu">{q.konu}</span>)}
      </div>
      <button className="btn msim-basla" onClick={onBasla}>Mülakatı başlat</button>
      {v.son.length > 0 && (
        <div className="msim-son">
          Son denemelerin:{' '}
          {v.son.map((s, i) => (
            <span key={s.zaman}>{i > 0 && ', '}{s.toplam ? `${s.dogru} / ${s.toplam}` : 'tamamlandı'} ({new Date(s.zaman).toLocaleDateString('tr-TR')})</span>
          ))}
        </div>
      )}
    </div>
  )
}

function Karo({ i, durum, secili, iyi, acik, onSec }) {
  // durum: 'dusunuyor' | 'cevapladi' | 'sonuc'
  const a = ADAYLAR[i]
  const tepki = durum === 'dusunuyor' ? '🤔' : durum === 'cevapladi' ? '💬' : iyi ? '😊' : '🤔'
  const ic = (
    <>
      <span className={`msim-tepki${durum === 'dusunuyor' ? ' dusunuyor' : ''}`} aria-hidden="true">{tepki}</span>
      <span className="msim-yuz" aria-hidden="true">{a.yuz}</span>
      <span className="msim-dizustu" aria-hidden="true" />
      <span className="msim-ad">{a.ad}</span>
      {durum === 'sonuc' && secili && <span className="msim-rozet sen">Senin seçimin</span>}
      {durum === 'sonuc' && iyi && <span className="msim-rozet iyi">{acik ? 'Savunulabilir' : 'Mülakatçının tercihi'}</span>}
    </>
  )
  const sinif = `msim-karo${secili ? ' secili' : ''}${durum === 'sonuc' && iyi ? ' iyi' : ''}`
  if (durum === 'cevapladi') {
    return <button type="button" className={sinif} onClick={onSec} aria-label={`${a.ad} daha iyi cevap verdi`}>{ic}</button>
  }
  return <div className={sinif}>{ic}</div>
}

function Soru({ q, v, sira, toplam, secim, onSec, onIleri }) {
  const [durum, setDurum] = useState(secim != null ? 'sonuc' : 'dusunuyor')
  const geriRef = useRef(null)
  useEffect(() => {
    if (secim != null) return undefined
    setDurum('dusunuyor')
    const t = setTimeout(() => setDurum('cevapladi'), azHareket() ? 0 : 1400)
    return () => clearTimeout(t)
  }, [q.no]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (secim != null) { setDurum('sonuc'); setTimeout(() => geriRef.current?.scrollIntoView({ behavior: azHareket() ? 'auto' : 'smooth', block: 'nearest' }), 60) }
  }, [secim])
  const ikisi = q.tur === 'ikisi_de'
  const sec = secim != null ? q.adaylar[secim] : null
  const diger = secim != null ? q.adaylar[1 - secim] : null
  const ayni = sec?.iyi
  return (
    <div className="msim">
      <div className="msim-ilerleme" aria-label={`Soru ${sira + 1} / ${toplam}`}>
        {Array.from({ length: toplam }, (_, i) => <span key={i} className={i < sira ? 'bitti' : i === sira ? 'simdi' : ''} />)}
        <span className="msim-ilerleme-metin">Soru {sira + 1} / {toplam} · {q.konu}</span>
      </div>
      <section className="msim-sahne" aria-label="Görüşme">
        <div className="msim-mulakatci">
          <span className="msim-m-yuz" aria-hidden="true">🧑🏻‍💼</span>
          <div className="msim-m-govde">
            <div className="msim-m-rol">Mülakatçı · {v.mulakatci}</div>
            <p className="msim-m-soru">{q.soru}</p>
            {q.terimler.length > 0 && (
              <dl className="msim-terimler">
                {q.terimler.map((t) => <div key={t.terim}><dt>{t.terim}</dt><dd>{t.aciklama}</dd></div>)}
              </dl>
            )}
          </div>
        </div>
        <div className="msim-adaylar">
          {q.adaylar.map((a, i) => (
            <div key={i} className="msim-aday">
              <Karo i={i} durum={durum} secili={secim === i} iyi={a.iyi} acik={ikisi} onSec={() => onSec(i)} />
              <div className={`msim-balon${durum === 'dusunuyor' ? ' bekliyor' : ''}`} aria-live="polite">
                {durum === 'dusunuyor' ? <span className="msim-yaziyor" aria-label={`${ADAYLAR[i].ad} düşünüyor`}><i /><i /><i /></span> : a.cevap}
              </div>
            </div>
          ))}
        </div>
        {durum === 'cevapladi' && (
          <div className="msim-sor">
            <span>Sence hangi aday daha iyi cevap verdi?</span>
            <div className="msim-sor-dugmeler">
              {ADAYLAR.map((a, i) => <button key={a.ad} className="btn" onClick={() => onSec(i)}>{a.ad}</button>)}
            </div>
          </div>
        )}
      </section>

      {secim != null && (
        <div ref={geriRef} className={`msim-geri ${ikisi ? 'iki' : ayni ? 'ayni' : 'farkli'}`}>
          <div className="msim-geri-baslik">
            {ikisi ? 'İki yaklaşım da savunulabilir' : ayni ? 'Mülakatçıyla aynı adayı seçtin' : 'Mülakatçı diğer adayı tercih etti'}
          </div>
          {ikisi && <p className="msim-geri-alt">Bu soruda tek bir doğru yok; iki aday farklı bir şeye öncelik veriyor. Önemli olan sonuçlarını bilerek seçmek.</p>}
          <div className="msim-gerekce">
            <div className={`msim-g ${sec.iyi ? 'guclu' : 'zayif'}`}>
              <div className="msim-g-ad">Senin seçtiğin: {ADAYLAR[secim].ad}</div>
              <p>{sec.neden}</p>
              {ikisi && sec.sonuc && <p className="msim-g-sonuc"><b>Sonucu:</b> {sec.sonuc}</p>}
            </div>
            <div className={`msim-g ${diger.iyi ? 'guclu' : 'zayif'}`}>
              <div className="msim-g-ad">{ikisi ? 'Diğer aday' : ayni ? 'Diğer aday' : 'Mülakatçının tercihi'}: {ADAYLAR[1 - secim].ad}</div>
              <p>{diger.neden}</p>
              {ikisi && diger.sonuc && <p className="msim-g-sonuc"><b>Sonucu:</b> {diger.sonuc}</p>}
            </div>
          </div>
          <div className="msim-ders">
            <div className="msim-ders-baslik">💡 Alandan bir bilgi</div>
            <p>{q.ders}</p>
            {q.beceri && <div className="msim-beceri">Bu soruda aranan: <b>{q.beceri}</b></div>}
          </div>
          <button className="btn msim-ileri" onClick={onIleri}>{sira + 1 < toplam ? 'Sonraki soru' : 'Sonucu gör'}</button>
        </div>
      )}
    </div>
  )
}

function Ozet({ o, v, onTekrar }) {
  const [, setParams] = useSearchParams()
  return (
    <div className="card msim-ozet">
      <div className="msim-ozet-ust">
        <span className="msim-giris-yuz" aria-hidden="true">🤝</span>
        <div>
          <h3 className="msim-giris-baslik">Görüşme bitti</h3>
          <div className="msim-ozet-skor">
            {o.toplam > 0
              ? <><span>{`${o.toplam} sorunun ${o.dogru} tanesinde mülakatçıyla aynı adayı seçtin.`}</span>
                {o.ikisi_de > 0 && <span>{` ${o.ikisi_de} soruda iki yaklaşım da savunulabilirdi.`}</span>}</>
              : 'İki yaklaşımın da savunulabildiği durumları inceledin.'}
          </div>
        </div>
      </div>
      <p className="msim-giris-metin">{o.yorum}</p>
      <h4 className="msim-ozet-ara">Bu görüşmede öğrendiklerin</h4>
      <ul className="msim-ogrenilen">
        {o.sorular.map((s) => (
          <li key={s.no} className={s.ayni === false ? 'farkli' : s.ayni ? 'ayni' : 'iki'}>
            <span className="msim-o-isaret" aria-hidden="true">{s.ayni === false ? '↺' : s.ayni ? '✓' : '⚖'}</span>
            <div><b>{s.konu}</b><p>{s.ders}</p></div>
          </li>
        ))}
      </ul>
      {o.beceriler.length > 0 && (
        <div className="msim-beceriler">
          <span>Bu meslekte aranan beceriler:</span>
          {o.beceriler.map((b) => <span key={b} className="msim-konu">{b}</span>)}
        </div>
      )}
      <div className="msim-ozet-dugmeler">
        <button className="btn" onClick={onTekrar}>Yeniden dene</button>
        <button className="btn sec" onClick={() => setParams((p) => { const n = new URLSearchParams(p); n.set('sekme', 'mulakat'); return n })}>
          Kendi cevabını yaz: Mülakat Pratiği
        </button>
      </div>
      <div className="yp-ince msim-not">{v.kaynak_notu}</div>
    </div>
  )
}

export default function MulakatSimulasyonu({ bolum }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [adim, setAdim] = useState('giris')   // giris → soru → ozet
  const [sira, setSira] = useState(0)
  const [secimler, setSecimler] = useState({})
  const [ozet, setOzet] = useState(null)
  const [bekle, setBekle] = useState(false)

  const yukle = () => {
    setHata(null)
    api.isHayatiMulakatSim(bolum.id).then(setV).catch((e) => setHata(e.message || 'Mülakat yüklenemedi.'))
  }
  useEffect(yukle, [bolum.id]) // eslint-disable-line react-hooks/exhaustive-deps

  if (hata) return <div className="card bos-durum">{hata}</div>
  if (!v) return <div className="card bos-durum yukleniyor">Yükleniyor…</div>

  const basla = () => { setSecimler({}); setSira(0); setOzet(null); setAdim('soru') }
  const ileri = () => {
    if (sira + 1 < v.sorular.length) { setSira(sira + 1); window.scrollTo?.({ top: 0, behavior: azHareket() ? 'auto' : 'smooth' }); return }
    setBekle(true)
    api.isHayatiMulakatSimKaydet({ bolum_id: bolum.id, secimler })
      .then((o) => { setOzet(o); setAdim('ozet'); yukle() })
      .catch((e) => setHata(e.message || 'Sonuç kaydedilemedi.'))
      .finally(() => setBekle(false))
  }

  if (adim === 'giris') return <Baslangic v={v} onBasla={basla} />
  if (adim === 'ozet' && ozet) return <Ozet o={ozet} v={v} onTekrar={basla} />
  const q = v.sorular[sira]
  return (
    <div aria-busy={bekle}>
      <Soru key={q.no} q={q} v={v} sira={sira} toplam={v.sorular.length} secim={secimler[q.no]}
        onSec={(i) => setSecimler((s) => (s[q.no] != null ? s : { ...s, [q.no]: i }))} onIleri={ileri} />
    </div>
  )
}
