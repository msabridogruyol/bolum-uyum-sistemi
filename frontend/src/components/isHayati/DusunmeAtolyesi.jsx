// [2026-10-13] İş Hayatı → 'dusunme' sekmesi: Düşünme Atölyesi.
// Okulda doğrudan öğretilmeyen düşünme araçları, yaparak: kök neden (5 Neden), korelasyon ≠ nedensellik, algoritmik düşünme,
// ikiye bölerek arama. Modül akışı: giriş → ilk deneme (alıştırma) → araç → okulda → iş hayatında → bu hafta dene → özet.
// Zekâ testi değil: özet "ilk denemen → aracı kullanınca" karşılaştırmasıdır; sonuçlar yalnızca öğrenciye görünür.
// ?arac=<kod> ile doğrudan bir modül açılır (Mülakat Simülasyonu'ndaki "Atölyede dene" bağlantısı).
// Uçlar: GET /ogrenci/is-hayati/dusunme?bolum_id=, POST /ogrenci/is-hayati/dusunme/{kod} (backend/app/api/is_hayati_dusunme.py)
import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../../api/client'

const ADIMLAR = [['giris', 'Durum'], ['alistirma', 'İlk deneme'], ['arac', 'Araç'], ['okulda', 'Okulda'], ['iste', 'İş hayatında'], ['dene', 'Bu hafta dene']]
const karistir = (l, tohum) => {
  const a = [...l]
  let s = tohum
  for (let i = a.length - 1; i > 0; i--) { s = (s * 9301 + 49297) % 233280; const j = Math.floor((s / 233280) * (i + 1)); [a[i], a[j]] = [a[j], a[i]] }
  return a
}

// ---------------------------------------------------------------- ortak: tek seçimli soru
function Secmeli({ secenekler, onSonuc, kilit = true }) {
  const [secim, setSecim] = useState(null)
  const bitti = kilit && secim != null && secenekler[secim]?.dogru
  return (
    <div className="da-secenekler">
      {secenekler.map((x, i) => {
        const goster = secim != null && (i === secim || (kilit ? false : x.dogru))
        return (
          <div key={i} className="da-secenek-kap">
            <button type="button" disabled={bitti || (!kilit && secim != null)}
              className={`da-secenek${secim === i ? (x.dogru ? ' dogru' : ' yanlis') : ''}`}
              onClick={() => { setSecim(i); onSonuc?.(x.dogru, i) }}>
              <span className="da-isaret" aria-hidden="true">{secim === i ? (x.dogru ? '✓' : '✗') : ''}</span>{x.metin}
            </button>
            {goster && <div className={`da-aciklama ${x.dogru ? 'dogru' : 'yanlis'}`}>{x.aciklama}</div>}
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------- 1. kök neden: neden zinciri
function Zincir({ a, onBitti }) {
  const [adim, setAdim] = useState(0)
  const [zincir, setZincir] = useState([])
  const [ilk, setIlk] = useState(0)          // ilk seferde doğru seçilen adım sayısı
  const [yanlis, setYanlis] = useState(null)
  const [hataVar, setHataVar] = useState(false)
  const [cozum, setCozum] = useState(null)
  const cozumler = useMemo(() => karistir(a.cozumler, 7), [a])
  const s = a.adimlar[adim]
  const sec = (x) => {
    if (x.dogru) {
      if (!hataVar) setIlk((n) => n + 1)
      setZincir((z) => [...z, x.metin]); setYanlis(null); setHataVar(false); setAdim(adim + 1)
    } else { setYanlis(x); setHataVar(true) }
  }
  const zincirBitti = adim >= a.adimlar.length
  return (
    <div className="da-zincir">
      <ol className="da-halkalar">
        <li className="sorun"><span className="da-halka-etiket">Sorun</span>{a.sorun}</li>
        {zincir.map((m, i) => <li key={i}><span className="da-halka-etiket">Neden {i + 1}</span>{m}</li>)}
        {zincirBitti && <li className="kok"><span className="da-halka-etiket">Kök neden</span>{a.kok}</li>}
      </ol>
      {!zincirBitti && (
        <div className="da-soru-kutu">
          <div className="da-soru">{s.soru} <span className="yp-ince">({adim + 1} / {a.adimlar.length})</span></div>
          <div className="da-secenekler">
            {s.secenekler.map((x, i) => (
              <button key={`${adim}-${i}`} type="button" className={`da-secenek${yanlis === x ? ' yanlis' : ''}`} onClick={() => sec(x)}>
                <span className="da-isaret" aria-hidden="true">{yanlis === x ? '✗' : ''}</span>{x.metin}
              </button>
            ))}
          </div>
          {yanlis && <div className="da-aciklama yanlis">{yanlis.aciklama} Başka bir seçenek dene.</div>}
        </div>
      )}
      {zincirBitti && (
        <div className="da-soru-kutu">
          <div className="da-soru">Kök nedene ulaştın. Şimdi iki çözümden hangisi sorunu kökünden çözer?</div>
          <div className="da-secenekler">
            {cozumler.map((c, i) => (
              <div key={i} className="da-secenek-kap">
                <button type="button" disabled={cozum != null}
                  className={`da-secenek${cozum === i ? (c.tur === 'kok' ? ' dogru' : ' yanlis') : ''}`}
                  onClick={() => setCozum(i)}>
                  <span className="da-isaret" aria-hidden="true">{cozum === i ? (c.tur === 'kok' ? '✓' : '✗') : ''}</span>{c.metin}
                </button>
                {cozum != null && <div className={`da-aciklama ${c.tur === 'kok' ? 'dogru' : 'yanlis'}`}><b>{c.tur === 'kok' ? 'Köke yönelik' : 'Belirtiye yönelik'}:</b> {c.aciklama}</div>}
              </div>
            ))}
          </div>
          {cozum != null && (
            <button type="button" className="btn" onClick={() => onBitti(ilk + (cozumler[cozum].tur === 'kok' ? 1 : 0), a.adimlar.length + 1)}>Tamam</button>
          )}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------- 2. korelasyon: ilişki vakaları + küçük saçılım grafiği
function Sacilim({ v }) {
  const G = 300, Y = 170, sol = 34, alt = 26, ust = 10, sag = 10
  const xs = v.noktalar.map((p) => p[0]), ys = v.noktalar.map((p) => p[1])
  const [x0, x1] = [Math.min(0, ...xs), Math.max(...xs)], [y0, y1] = [Math.min(0, ...ys), Math.max(...ys)]
  const px = (x) => sol + ((x - x0) / (x1 - x0 || 1)) * (G - sol - sag)
  const py = (y) => Y - alt - ((y - y0) / (y1 - y0 || 1)) * (Y - alt - ust)
  return (
    <figure className="da-grafik">
      <svg viewBox={`0 0 ${G} ${Y}`} role="img" aria-label={`${v.x_ad} ile ${v.y_ad} arasındaki ilişki`}>
        <line x1={sol} y1={Y - alt} x2={G - sag} y2={Y - alt} className="da-eksen" />
        <line x1={sol} y1={ust} x2={sol} y2={Y - alt} className="da-eksen" />
        <text x={sol - 6} y={py(y1) + 4} textAnchor="end" className="da-eksen-yazi">{y1}</text>
        <text x={sol - 6} y={Y - alt + 4} textAnchor="end" className="da-eksen-yazi">{y0}</text>
        <text x={G - sag} y={Y - 8} textAnchor="end" className="da-eksen-yazi">{x1}</text>
        {v.noktalar.map((p, i) => <circle key={i} cx={px(p[0])} cy={py(p[1])} r="5" className="da-nokta"><title>{`${p[0]} · ${p[1]}`}</title></circle>)}
      </svg>
      <figcaption><span>↔ {v.x_ad}</span><span>↕ {v.y_ad}</span></figcaption>
    </figure>
  )
}

function Iliski({ a, onBitti }) {
  const [i, setI] = useState(0)
  const [ilk, setIlk] = useState(0)
  const [cevap, setCevap] = useState(null)
  const v = a.vakalar[i]
  const son = i + 1 >= a.vakalar.length
  return (
    <div className="da-iliski">
      <div className="da-soru">Vaka {i + 1} / {a.vakalar.length}</div>
      <blockquote className="da-iddia">“{v.iddia}”</blockquote>
      <Sacilim v={v} />
      <div className="da-soru">Bu ilişkiye en iyi açıklama hangisi?</div>
      <Secmeli key={i} secenekler={v.secenekler} kilit={false} onSonuc={(d) => { setCevap(d); if (d) setIlk((n) => n + 1) }} />
      {cevap != null && (
        <>
          <div className="da-ders">💡 {v.ders}</div>
          <button type="button" className="btn" onClick={() => {
            if (son) onBitti(ilk, a.vakalar.length)
            else { setI(i + 1); setCevap(null) }
          }}>{son ? 'Tamam' : 'Sonraki vaka'}</button>
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------- 3. algoritma: adımları sırala, robotu çalıştır
function Siralama({ a, onBitti }) {
  const karisik = useMemo(() => karistir(a.adimlar.map((m, i) => ({ m, i })), 11), [a])
  const [sira, setSira] = useState([])
  const [calisma, setCalisma] = useState(null)   // {adim, hata: index|null}
  const [ilkDogru, setIlkDogru] = useState(null)
  const [eksikSonuc, setEksikSonuc] = useState(null)
  const zaman = useRef(null)
  useEffect(() => () => clearTimeout(zaman.current), [])
  const kalan = karisik.filter((x) => !sira.includes(x))
  const calistir = () => {
    const hata = sira.findIndex((x, k) => x.i !== k)
    const azHareket = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    let k = 0
    const ilerle = () => {
      setCalisma({ adim: k, hata: null })
      if (hata >= 0 && k === hata) { setCalisma({ adim: k, hata }); if (ilkDogru == null) setIlkDogru(false); return }
      if (k >= sira.length - 1) { setCalisma({ adim: k, hata: null, bitti: true }); if (ilkDogru == null) setIlkDogru(true); return }
      k += 1
      zaman.current = setTimeout(ilerle, azHareket ? 0 : 550)
    }
    ilerle()
  }
  const tamam = calisma?.bitti
  return (
    <div className="da-siralama">
      <div className="da-soru">{a.gorev}</div>
      <div className="da-iki-sutun">
        <div>
          <div className="da-alt-baslik">Adımlar (dokunarak sıraya ekle)</div>
          <div className="da-kartlar">
            {kalan.map((x) => <button key={x.i} type="button" className="da-kart" disabled={tamam} onClick={() => { setSira([...sira, x]); setCalisma(null) }}>{x.m}</button>)}
            {kalan.length === 0 && <div className="yp-ince">Tüm adımlar sırada.</div>}
          </div>
        </div>
        <div>
          <div className="da-alt-baslik">Robotun algoritması</div>
          <ol className="da-algoritma">
            {sira.map((x, k) => (
              <li key={x.i} className={calisma && k <= calisma.adim ? (calisma.hata === k ? 'hata' : 'calisti') : ''}>
                <span className="da-satir-no">{k + 1}</span>
                <span className="da-satir-metin">{x.m}</span>
                {calisma?.adim === k && calisma.hata == null && !tamam && <span className="da-robot" aria-hidden="true">🤖</span>}
                {!tamam && <button type="button" className="da-cikar" aria-label="Adımı çıkar" onClick={() => { setSira(sira.filter((y) => y !== x)); setCalisma(null) }}>×</button>}
              </li>
            ))}
            {sira.length === 0 && <li className="bos">Soldaki adımlara dokun.</li>}
          </ol>
          <button type="button" className="btn" disabled={sira.length !== a.adimlar.length || tamam} onClick={calistir}>▶ Robotu çalıştır</button>
        </div>
      </div>
      {calisma?.hata != null && (
        <div className="da-aciklama yanlis">
          🤖 Robot {calisma.hata + 1}. satırda takıldı: “{sira[calisma.hata].m}” adımına geldi ama önce “{a.adimlar[calisma.hata]}” yapılmalıydı.
          Satırı çıkarıp düzelt ve yeniden çalıştır.
        </div>
      )}
      {tamam && (
        <>
          <div className="da-aciklama dogru">🤖 Robot tüm adımları sorunsuz uyguladı.</div>
          <div className="da-soru-kutu">
            <div className="da-durum">{a.eksik.durum}</div>
            <div className="da-soru">{a.eksik.soru}</div>
            <Secmeli secenekler={a.eksik.secenekler} kilit={false} onSonuc={(d) => setEksikSonuc(d)} />
            {eksikSonuc != null && (
              <button type="button" className="btn" onClick={() => onBitti((ilkDogru ? 1 : 0) + (eksikSonuc ? 1 : 0), 2)}>Tamam</button>
            )}
          </div>
        </>
      )}
    </div>
  )
}

// ---------------------------------------------------------------- 4. ikiye bölerek arama: sayı bulma oyunu
function SayiBul({ a, onBitti }) {
  const { alt, ust } = a
  const [hedef] = useState(() => alt + Math.floor(Math.random() * (ust - alt + 1)))
  const [aralik, setAralik] = useState([alt, ust])
  const [tahminler, setTahminler] = useState([])
  const [deger, setDeger] = useState('')
  const [demo, setDemo] = useState(null)
  const bulundu = tahminler.at(-1)?.t === hedef
  const tahmin = (e) => {
    e?.preventDefault()
    const t = Number(deger)
    if (!Number.isInteger(t) || t < alt || t > ust || bulundu) return
    const yon = t === hedef ? 'tamam' : t < hedef ? 'buyuk' : 'kucuk'
    setTahminler([...tahminler, { t, yon }])
    if (yon === 'buyuk') setAralik([Math.max(aralik[0], t + 1), aralik[1]])
    if (yon === 'kucuk') setAralik([aralik[0], Math.min(aralik[1], t - 1)])
    setDeger('')
  }
  const demoCalistir = () => {
    let [d0, d1] = [alt, ust]
    const adimlar = []
    while (d0 <= d1) {
      const o = Math.floor((d0 + d1) / 2)
      adimlar.push({ o, d0, d1 })
      if (o === hedef) break
      if (o < hedef) d0 = o + 1; else d1 = o - 1
    }
    setDemo(adimlar)
  }
  const genislik = ust - alt + 1
  return (
    <div className="da-sayi">
      <div className="da-soru">{alt} ile {ust} arasında bir sayı tuttum. En az tahminle bul; her tahminde “daha büyük” ya da “daha küçük” diyeceğim.</div>
      <div className="da-cizgi" aria-hidden="true">
        <span className="da-cizgi-acik" style={{ left: `${((aralik[0] - alt) / genislik) * 100}%`, width: `${((aralik[1] - aralik[0] + 1) / genislik) * 100}%` }} />
        {tahminler.map((x, i) => <span key={i} className={`da-cizgi-tahmin ${x.yon}`} style={{ left: `${((x.t - alt + 0.5) / genislik) * 100}%` }} />)}
      </div>
      <div className="da-cizgi-etiket"><span>{alt}</span><span>Kalan aralık: {aralik[0]}–{aralik[1]}</span><span>{ust}</span></div>
      {!bulundu && (
        <form className="da-tahmin" onSubmit={tahmin}>
          <label htmlFor="da-tahmin-g" className="yp-ince">Tahminin</label>
          <input id="da-tahmin-g" type="number" inputMode="numeric" min={alt} max={ust} value={deger} onChange={(e) => setDeger(e.target.value)} />
          <button className="btn" type="submit" disabled={deger === ''}>Tahmin et</button>
        </form>
      )}
      <div className="da-tahminler" aria-live="polite">
        {tahminler.map((x, i) => (
          <span key={i} className={`da-tahmin-cip ${x.yon}`}>{x.t} {x.yon === 'tamam' ? '🎯' : x.yon === 'buyuk' ? '↑ daha büyük' : '↓ daha küçük'}</span>
        ))}
      </div>
      {bulundu && (
        <>
          <div className="da-aciklama dogru">{tahminler.length} tahminde buldun. {a.aciklama}</div>
          {!demo && <button type="button" className="btn sec" onClick={demoCalistir}>Ortadan bölerek nasıl bulunurdu? Göster</button>}
          {demo && (
            <ol className="da-demo">
              {demo.map((d, i) => (
                <li key={i}><b>{i + 1}.</b> Aralık {d.d0}–{d.d1}, ortası <b>{d.o}</b>{d.o === hedef ? ' 🎯' : d.o < hedef ? ' → daha büyük, alt yarı elendi' : ' → daha küçük, üst yarı elendi'}</li>
              ))}
            </ol>
          )}
          <button type="button" className="btn" onClick={() => onBitti(tahminler.length <= 7 ? 1 : 0, 1, tahminler.length)}>Tamam</button>
        </>
      )}
    </div>
  )
}

const ALISTIRMA = { zincir: Zincir, iliski: Iliski, siralama: Siralama, sayi_bul: SayiBul }

// ---------------------------------------------------------------- modül
function Modul({ a, onKapat, onKaydedildi }) {
  const [adim, setAdim] = useState(0)
  const [ilk, setIlk] = useState(null)        // {dogru, toplam, tahmin?}
  const [okulda, setOkulda] = useState(null)
  const [iste, setIste] = useState(null)
  const [kayit, setKayit] = useState(null)
  const [, setParams] = useSearchParams()
  const ust = useRef(null)
  const kod = ADIMLAR[adim]?.[0] || 'ozet'
  useEffect(() => { ust.current?.scrollIntoView({ block: 'start', behavior: 'auto' }) }, [adim])
  const ileri = () => setAdim((x) => x + 1)
  const Alistirma = ALISTIRMA[a.alistirma.tur]
  const bitir = () => {
    api.isHayatiDusunmeBitir(a.kod, { ilk_dogru: ilk?.dogru || 0, ilk_toplam: ilk?.toplam || 0, okulda, iste })
      .then((r) => { setKayit(r); onKaydedildi() }).catch(() => setKayit({ hata: true }))
    ileri()
  }
  return (
    <div className="card da-modul" ref={ust}>
      <div className="da-modul-ust">
        <button type="button" className="da-geri" onClick={onKapat}>← Araçlar</button>
        <span className="da-modul-ad"><span aria-hidden="true">{a.ikon}</span> {a.ad}</span>
      </div>
      <ol className="da-adimlar" aria-label="Modül adımları">
        {ADIMLAR.map(([k, ad], i) => <li key={k} className={i < adim ? 'bitti' : i === adim ? 'simdi' : ''} aria-current={i === adim ? 'step' : undefined}>{ad}</li>)}
      </ol>

      {kod === 'giris' && (
        <div className="da-bolum">
          <h3 className="da-baslik">{a.giris.baslik}</h3>
          <p className="da-metin">{a.giris.durum}</p>
          <p className="da-not">Önce aracı bilmeden kendi bildiğin gibi dene. Yanılman çok normal; asıl öğrenme oradan başlıyor.</p>
          <button type="button" className="btn" onClick={ileri}>Denemeye başla</button>
        </div>
      )}
      {kod === 'alistirma' && (
        <div className="da-bolum">
          <Alistirma a={a.alistirma} onBitti={(dogru, toplam, tahmin) => { setIlk({ dogru, toplam, tahmin }); ileri() }} />
        </div>
      )}
      {kod === 'arac' && (
        <div className="da-bolum">
          <h3 className="da-baslik">{a.arac.baslik}</h3>
          <p className="da-metin">{a.arac.metin}</p>
          <ol className="da-arac-adimlar">{a.arac.adimlar.map((m, i) => <li key={i}>{m}</li>)}</ol>
          {a.arac.ipucu && <div className="da-ders">💡 {a.arac.ipucu}</div>}
          <button type="button" className="btn" onClick={ileri}>Okulda nasıl kullanılır?</button>
        </div>
      )}
      {(kod === 'okulda' || kod === 'iste') && (() => {
        const s = a[kod]
        const sonuc = kod === 'okulda' ? okulda : iste
        return (
          <div className="da-bolum" key={kod}>
            <div className="da-etiket">{kod === 'okulda' ? '🏫 Okulda' : `💼 İş hayatında · ${s.meslek}`}</div>
            <p className="da-metin">{s.durum}</p>
            <div className="da-soru">{s.soru}</div>
            <Secmeli secenekler={s.secenekler} kilit={false} onSonuc={(d) => (kod === 'okulda' ? setOkulda(d) : setIste(d))} />
            {sonuc != null && <button type="button" className="btn" onClick={ileri}>{kod === 'okulda' ? 'İş hayatında nasıl kullanılır?' : 'Devam'}</button>}
          </div>
        )
      })()}
      {kod === 'dene' && (
        <div className="da-bolum">
          <h3 className="da-baslik">Bu hafta dene</h3>
          <div className="da-dene">{a.dene}</div>
          <button type="button" className="btn" onClick={bitir}>Modülü bitir</button>
        </div>
      )}
      {kod === 'ozet' && (
        <div className="da-bolum">
          <h3 className="da-baslik">{a.ad}: tamamlandı</h3>
          <div className="da-karsilastir">
            <div className="da-k-kutu">
              <div className="da-k-baslik">İlk denemen (aracı bilmeden)</div>
              <div className="da-k-deger">{ilk?.tahmin ? `${ilk.tahmin} tahmin` : `${ilk?.dogru ?? 0} / ${ilk?.toplam ?? 0} ilk seferde`}</div>
            </div>
            <span className="da-k-ok" aria-hidden="true">→</span>
            <div className="da-k-kutu">
              <div className="da-k-baslik">Aracı kullanınca</div>
              <div className="da-k-deger">Okulda {okulda ? '✓' : '↺'} · İş hayatında {iste ? '✓' : '↺'}</div>
            </div>
          </div>
          <p className="da-not">Bu bir puan değil. Aynı aracı farklı yerlerde kullandıkça alışkanlığa dönüşür; ↺ olan durumların açıklamalarına bir kez daha bakabilirsin.</p>
          {a.mulakat?.length > 0 && (
            <div className="da-mulakat">
              <div className="da-alt-baslik">Bu bölümün mülakatında bu araç</div>
              <ul>{a.mulakat.map((m, i) => <li key={i}><b>{m.konu}:</b> {m.soru}</li>)}</ul>
              <button type="button" className="btn sec" onClick={() => setParams((p) => { const n = new URLSearchParams(p); n.set('sekme', 'mulakatsim'); n.delete('arac'); return n })}>Mülakat Simülasyonu'nu aç</button>
            </div>
          )}
          {kayit?.hata && <div className="yp-ince">Sonuç kaydedilemedi; modülü yeniden açtığında tekrar deneyebilirsin.</div>}
          <button type="button" className="btn" onClick={onKapat}>Diğer araçlara dön</button>
        </div>
      )}
    </div>
  )
}

export default function DusunmeAtolyesi({ bolum }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [params, setParams] = useSearchParams()
  const acik = params.get('arac')
  const yukle = () => api.isHayatiDusunme(bolum?.id).then(setV).catch((e) => setHata(e.message || 'Atölye yüklenemedi.'))
  useEffect(() => { yukle() }, [bolum?.id]) // eslint-disable-line react-hooks/exhaustive-deps
  const ac = (kod) => setParams((p) => { const n = new URLSearchParams(p); if (kod) n.set('arac', kod); else n.delete('arac'); return n })

  if (hata) return <div className="card bos-durum">{hata}</div>
  if (!v) return <div className="card bos-durum yukleniyor">Yükleniyor…</div>
  const secili = v.araclar.find((a) => a.kod === acik)
  if (secili) return <Modul key={secili.kod} a={secili} onKapat={() => ac(null)} onKaydedildi={yukle} />
  return (
    <div className="da">
      <div className="card da-giris">
        <h3 className="da-baslik">Okulda pek öğretilmeyen düşünme araçları</h3>
        <p className="da-metin">Neden–sonuç bağı kurmak, bir sorunun kökünü bulmak, bir işi adım adım tarif etmek… Bunlar her derste, her
          meslekte ve günlük hayatta işine yarar. Her araç 5–7 dakika: önce kendi bildiğin gibi dene, sonra aracı öğren, okulda ve iş
          hayatında nasıl kullanıldığını gör.</p>
      </div>
      <div className="da-araclar">
        {v.araclar.map((a) => {
          const il = v.ilerleme[a.kod]
          return (
            <button key={a.kod} type="button" className={`da-arac-kart${il ? ' bitti' : ''}`} onClick={() => ac(a.kod)}>
              <span className="da-arac-ikon" aria-hidden="true">{a.ikon}</span>
              <span className="da-arac-govde">
                <span className="da-arac-ad">{a.ad}</span>
                <span className="da-arac-ozet">{a.ozet}</span>
                <span className="da-arac-alt">
                  {a.sure_dk} dk{il ? ' · ✓ tamamlandı' : ''}{a.mulakat?.length ? ` · Bu bölümün mülakatında ${a.mulakat.length} soruda` : ''}
                </span>
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
