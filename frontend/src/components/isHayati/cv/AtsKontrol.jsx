// [2026-10-11] CV Atölyesi → "ATS kontrolü". POST /ogrenci/is-hayati/cv/ats (algoritma: backend/app/core/ats.py):
// a) biçim: sistemin ürettiği PDF sunucuda pypdf ile ayrıştırılır, "ATS'nin gördüğü" düz metin + 6 madde (/100);
// b) ilana uyum: örnek ilan ya da yapıştırılan ilan → anahtar kelime eşleştirmesi. Gönderilen CV düzenleyicideki (kaydedilmemiş olabilir)
// hâlidir. İlan metni ve sonuçlar HİÇBİR YERDE saklanmaz (sunucu da kaydetmez); sayfadan çıkınca kaybolur.
// Kontrol listesiyle çakışma: tarih / tek sayfa / iletişim maddeleri iki yerde de var ama birbirine bağlantı verir (ayrı bakış açısı:
// kontrol listesi CV içeriğine, ATS kontrolü PDF'ten çıkan metne bakar).
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../../api/client'
import { DURUM, puanRengi } from './CvKontrol'

const LISTEDE_DE = { tarih: 'Tarih biçimi tutarlı', tek_sayfa: 'Tek sayfa', iletisim: 'İletişim bilgisi tam' }
const TUR = { zorunlu: { ad: 'Zorunlu', renk: 'var(--re)' }, tercih: { ad: 'Tercih', renk: 'var(--gr)' }, genel: { ad: 'İlanda geçiyor', renk: 'var(--tx3)' }, gizli: { ad: 'Satır arası', renk: 'var(--am)' } }
const BOLUM = { diller: 'Diller', beceriler: 'Beceriler', sertifikalar: 'Sertifikalar ve kurslar', deneyim: 'Deneyim / proje açıklaması' }

function Madde({ m, acik, onAc, onGit }) {
  const d = DURUM[m.durum]
  return (
    <div className="cva-madde">
      <button type="button" className="cva-madde-ust" onClick={onAc} aria-expanded={acik}>
        <span className="cva-madde-ikon" style={{ color: d.renk, background: d.zemin }} aria-label={d.ad}>{d.ikon}</span>
        <span style={{ flex: 1, textAlign: 'left' }}>{m.ad}</span>
        <span className="yp-ince" style={{ whiteSpace: 'nowrap' }}>{Math.round(m.puan * 10) / 10} / {m.agirlik}</span>
      </button>
      {acik && (
        <div className="cva-madde-govde">
          <div>{m.aciklama}</div>
          <div className="cva-oneri-metni" style={{ borderColor: d.renk }}><b>{m.durum === 'tamam' ? 'Sonuç' : 'Ne yapabilirsin'}:</b> {m.oneri}</div>
          {m.ayrinti?.length > 0 && <div className="yp-ince" style={{ marginTop: 6 }}>{m.ayrinti.join(' · ')}</div>}
          {LISTEDE_DE[m.kod] && (
            <div className="yp-ince" style={{ marginTop: 6 }}>Kontrol listesinde de var (“{LISTEDE_DE[m.kod]}”) — orada CV içeriğine, burada PDF'ten çıkan metne bakılır.{' '}
              <button type="button" className="hg-link" style={{ fontSize: 11.5, color: 'var(--okul-c)' }} onClick={() => onGit('kontrol')}>Kontrol listesine git →</button></div>
          )}
        </div>
      )}
    </div>
  )
}

function Cip({ x, ek }) {
  const t = TUR[x.tur] || TUR.genel
  return (
    <span className="ats-cip" title={t.ad}>
      <span className="ats-nokta" style={{ background: t.renk }} aria-hidden="true" />{x.ifade}{ek && <small> · {ek}</small>}
    </span>
  )
}

function Uyum({ u }) {
  const renk = puanRengi(u.uyum)
  const zorunluEksik = u.eksik.filter((x) => x.tur === 'zorunlu')
  return (
    <div className="ats-uyum">
      <div className="cva-puan-kart" style={{ marginBottom: 10 }}>
        <div className="cva-puan" style={{ color: renk }}>%{u.uyum}</div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>İlanla tahmini uyum · {u.bulunan.length}/{u.anahtar_sayisi} anahtar kelime CV'nde var</div>
          <div className="qtrack" style={{ marginBottom: 6 }}><div className="qfill" style={{ width: `${u.uyum}%`, background: renk }} /></div>
          <div className="yp-ince">Zorunlu niteliklerdeki kelimeler 3, tercih edilenler 2, diğerleri 1 puan sayılır. %100 hedef değildir; ilanın tamamı herkese uymaz.</div>
        </div>
      </div>
      <div className="ats-lejant yp-ince">
        {['zorunlu', 'tercih', 'genel'].map((k) => <span key={k}><span className="ats-nokta" style={{ background: TUR[k].renk }} />{TUR[k].ad}</span>)}
      </div>

      {u.bulunan.length > 0 && (
        <div className="ats-grup">
          <div className="cvr-alt-baslik">✓ CV'nde bulunanlar</div>
          <div className="cvr-ciplar">{u.bulunan.map((x) => <Cip key={x.ifade} x={x} ek={x.bolum_ad} />)}</div>
        </div>
      )}
      {u.kismen.length > 0 && (
        <div className="ats-grup">
          <div className="cvr-alt-baslik">◐ Kısmen</div>
          <div className="cvr-ciplar">{u.kismen.map((x) => <Cip key={x.ifade} x={x} />)}</div>
          <div className="yp-ince" style={{ marginTop: 4 }}>Kelimeler CV'nde var ama yan yana değil. Gerçekten bu beceriye sahipsen ilandaki ifadeyi aynen kullanabilirsin.</div>
        </div>
      )}
      {u.eksik.length > 0 && (
        <div className="ats-grup">
          <div className="cvr-alt-baslik">CV'nde bulunamayanlar</div>
          <div className="cvr-not uyari" style={{ marginBottom: 8 }}>
            <b>Bunu CV'ne dürüstçe ekleyebilir misin?</b> Yalnızca gerçekten sahip olduğun becerileri ve yaptığın şeyleri ekle. Sahip olmadığın bir beceriyi
            yazmak görüşmede ortaya çıkar. Eksik bir şey varsa sorun değil: tercih edilenler zaten herkeste olmaz; zorunlu olanlar için de bir kurs ya da proje hedefi koyabilirsin.
          </div>
          <div className="ats-eksik-liste">
            {u.eksik.map((x) => (
              <div key={x.ifade} className="ats-eksik">
                <Cip x={x} />
                <div className="yp-ince"><b>{BOLUM[x.bolum] || 'Deneyim'}:</b> {x.oneri}</div>
              </div>
            ))}
          </div>
          {zorunluEksik.length > 0 && <div className="yp-ince" style={{ marginTop: 6 }}>Not: Bazı kelimeler (ör. yaş, gün, şehir) bir beceri değil, ilanın koşuludur; bunları CV'ye eklemen gerekmez.</div>}
        </div>
      )}
      <details className="cvr-kaynak" style={{ marginTop: 10 }}>
        <summary>Bu yüzde nasıl hesaplanıyor?</summary>
        <ul>
          <li>İlan satırlara bölünür; “zorunlu, şart, en az, aranır” → zorunlu, “tercih, tercihen, avantaj, artı” → tercih edilen sayılır (örnek ilanlarda tür hazırdır).</li>
          <li>Kelimeler küçük harfe çevrilir (İ→i, I→ı); “ve, ile, için” gibi durak sözcükleri ve “deneyim, bilgi, aday” gibi ilan kalıpları atılır.</li>
          <li>Yaygın ekler basitçe budanır (projelerinde → proje, ekibimize → ekip): mükemmel değildir, bazen iki farklı kelimeyi aynı sanabilir ya da bir eşleşmeyi kaçırabilir.</li>
          <li>“Ekip çalışması”, “sosyal medya” gibi öbekler birlikte aranır; “takım” ile “ekip” aynı sayılır.</li>
          <li>Arama, PDF'inden çıkan metinde (yukarıdaki “ATS'nin gördüğü”) yapılır.</li>
        </ul>
      </details>
    </div>
  )
}

export default function AtsKontrol({ icerik, degisti, bolum, onGit }) {
  const [sonuc, setSonuc] = useState(null)
  const [uyum, setUyum] = useState(null)
  const [bekle, setBekle] = useState(null)   // 'bicim' | 'uyum'
  const [hata, setHata] = useState(null)
  const [acik, setAcik] = useState(null)
  const [metinAcik, setMetinAcik] = useState(false)
  const [ilanlar, setIlanlar] = useState([])
  const [kaynak, setKaynak] = useState('ornek')
  const [ilanId, setIlanId] = useState('')
  const [ilanMetni, setIlanMetni] = useState('')
  const [sonGonderilen, setSonGonderilen] = useState(null)
  const imza = useMemo(() => JSON.stringify(icerik), [icerik])

  async function calistir(ilanla) {
    setBekle(ilanla ? 'uyum' : 'bicim'); setHata(null)
    const govde = { icerik }
    if (ilanla) { if (kaynak === 'ornek') govde.ilan_id = ilanId; else govde.ilan_metni = ilanMetni }
    try { const r = await api.isHayatiCvAts(govde); setSonuc(r); if (ilanla) setUyum(r.uyum); setSonGonderilen(imza) } catch (e) { setHata(e.detail || 'Kontrol yapılamadı.') } finally { setBekle(null) }
  }
  useEffect(() => { calistir(false) }, [])   // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    api.isHayatiCvIlanlar(bolum?.id).then((x) => { setIlanlar(x.ilanlar); setIlanId((o) => o || x.ilanlar[0]?.id || '') }).catch(() => {})
  }, [bolum?.id])

  const b = sonuc?.bicim
  const eskidi = sonuc && sonGonderilen !== imza
  const ilk = b?.maddeler.find((m) => m.durum !== 'tamam')?.kod
  const ilanHazir = kaynak === 'ornek' ? !!ilanId : ilanMetni.trim().length >= 30

  return (
    <div>
      <div className="card ats-bilgi">
        <div style={{ fontWeight: 800, fontSize: 15 }}>🤖 Başvuru sistemi CV'ni nasıl görür?</div>
        <div className="yp-ince" style={{ lineHeight: 1.6, fontSize: 12.5, marginTop: 4 }}>
          Birçok kurum başvuruları ATS denen bir yazılımla toplar: CV'ndeki metni çıkarır, bölümlere ayırır, anahtar kelimelere bakar.
          Burada CV'nin PDF'ini aynı şekilde okuyup sana gösteriyoruz.{' '}
          <button type="button" className="hg-link" style={{ fontSize: 12.5, color: 'var(--okul-c)' }} onClick={() => onGit('rehber')}>ATS nedir? →</button>
        </div>
        <div className="cvr-not bilgi" style={{ margin: '10px 0 0' }}>
          Gerçek ATS'ler şirketten şirkete farklıdır; bu kontrol yaygın ilkelere dayanan bir tahmindir. Amaç yüksek puan değil: CV'nin hem bir yazılım hem de bir insan için kolay okunması.
        </div>
        <div className="yp-ince" style={{ marginTop: 8 }}>🔒 Yapıştırdığın ilan ve sonuçlar kaydedilmez; yalnızca bu ekranda kalır.</div>
      </div>

      {hata && <div className="auth-error">{hata}</div>}
      {degisti && <div className="yp-uyari">Kaydedilmemiş değişikliklerin var; kontrol, düzenleyicideki güncel hâliyle yapılır.</div>}

      <div className="ihz-ara-baslik">1 · Biçim kontrolü</div>
      {!b ? <div className="card bos-durum">{bekle ? <><span className="spin" /> PDF hazırlanıp okunuyor…</> : 'Kontrol yapılamadı.'}</div> : (
        <>
          <div className="card cva-puan-kart">
            <div className="cva-puan" style={{ color: puanRengi(b.puan) }}>{b.puan}<small>/100</small></div>
            <div style={{ flex: 1, minWidth: 200 }}>
              <div style={{ fontWeight: 800, marginBottom: 6 }}>{b.tamam} / {b.toplam} madde tamam · {sonuc.sayfa} sayfa</div>
              <div className="qtrack" style={{ marginBottom: 8 }}><div className="qfill" style={{ width: `${b.puan}%`, background: puanRengi(b.puan) }} /></div>
              <div className="yp-ince">Önerilen dosya adı: <b className="ats-dosya">{sonuc.dosya_adi}</b></div>
            </div>
            <button type="button" className="btn sec" disabled={!!bekle} onClick={() => calistir(false)}>{bekle === 'bicim' ? <span className="spin" /> : eskidi ? '↻ Yeniden kontrol et' : '↻ Yenile'}</button>
          </div>
          {eskidi && <div className="yp-uyari">CV'yi bu kontrolden sonra değiştirdin; sonucu güncellemek için yeniden kontrol et.</div>}
          <div className="card" style={{ padding: '6px 16px' }}>
            {b.maddeler.map((m) => (
              <Madde key={m.kod} m={m} onGit={onGit} acik={acik === m.kod || (acik === null && m.kod === ilk)} onAc={() => setAcik(acik === m.kod || (acik === null && m.kod === ilk) ? '' : m.kod)} />
            ))}
          </div>
          <div className="card ats-metin-kart">
            <button type="button" className="cva-madde-ust" style={{ padding: 0 }} onClick={() => setMetinAcik(!metinAcik)} aria-expanded={metinAcik}>
              <span style={{ flex: 1, textAlign: 'left' }}>👁 ATS'nin gördüğü metin</span>
              <span className="yp-ince">{metinAcik ? 'Gizle' : 'Göster'}</span>
            </button>
            <div className="yp-ince" style={{ marginTop: 4, lineHeight: 1.5 }}>
              Renk, kalın yazı ve çizgiler gider; geriye bu düz metin kalır. Bulunan başlıklar (yeşil: tanındı):
            </div>
            <div className="cvr-ciplar" style={{ gap: 4, marginTop: 4 }}>{b.bolumler.map((x) => <span key={x.baslik} className={`pf-rozet${x.standart ? ' onay' : ''}`} style={{ whiteSpace: 'nowrap' }}>{x.baslik}</span>)}</div>
            {metinAcik && <pre className="ats-metin" aria-label="ATS'nin gördüğü düz metin">{sonuc.ats_metni}</pre>}
          </div>
        </>
      )}

      <div className="ihz-ara-baslik">2 · İlana uyum (anahtar kelimeler)</div>
      <div className="card">
        <div className="eu-filtre" role="tablist" style={{ marginBottom: 10 }}>
          <button type="button" role="tab" aria-selected={kaynak === 'ornek'} className={kaynak === 'ornek' ? 'secili' : ''} onClick={() => setKaynak('ornek')}>Örnek ilan seç</button>
          <button type="button" role="tab" aria-selected={kaynak === 'yapistir'} className={kaynak === 'yapistir' ? 'secili' : ''} onClick={() => setKaynak('yapistir')}>İlan metni yapıştır</button>
        </div>
        {kaynak === 'ornek' ? (
          <div>
            <select className="auth-input" value={ilanId} onChange={(e) => setIlanId(e.target.value)} aria-label="Örnek ilan">
              {ilanlar.map((x) => <option key={x.id} value={x.id}>{x.baslik} — {x.tur}{x.ilgili ? ' (bölümünle ilgili)' : ''}</option>)}
            </select>
            <div className="yp-ince" style={{ marginTop: 4 }}>Örnek ilanlar kurgusaldır; “İlan okuma” sekmesindekilerle aynıdır.</div>
          </div>
        ) : (
          <div>
            <textarea className="auth-input" rows={7} maxLength={8000} value={ilanMetni} onChange={(e) => setIlanMetni(e.target.value)}
              placeholder={'İlanın “Aranan nitelikler” ve “Tercih sebebi” kısımlarını buraya yapıştır.\nAd, telefon gibi kişisel bilgileri yapıştırmana gerek yok.'} />
            <div className="cva-sayac yp-ince"><span>İlan metni kaydedilmez.</span><span>{ilanMetni.length} / 8000</span></div>
          </div>
        )}
        <button type="button" className="btn" style={{ marginTop: 10 }} disabled={!!bekle || !ilanHazir} onClick={() => calistir(true)}>
          {bekle === 'uyum' ? <span className="spin" /> : 'Uyumu hesapla'}</button>
        {kaynak === 'yapistir' && !ilanHazir && ilanMetni && <span className="yp-ince" style={{ marginLeft: 8 }}>Biraz daha uzun bir metin yapıştır.</span>}
      </div>
      {uyum && <div className="card"><Uyum u={uyum} /></div>}
    </div>
  )
}
