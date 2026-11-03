import { useEffect, useState, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import Sayac from '../components/Sayac'
import { useBolumBilgi } from '../context/BolumBilgiContext'
import { AlanTuruRozeti, GeriBildirimOzeti, OlcumKarti, OlcumPenceresi, TamamlaFormu } from '../components/kocluk/KoclukMotoru'
import { useModuller } from '../yardimci/moduller'
import { BirGunumSekmesi, BolumunuTani } from '../components/kocluk/BirGunum'
import { puanTuruMetni } from '../yardimci/puanTuru'

// ============================================================
// Ana sayfa
// ============================================================
// [2026-10-17] Sen ve bölüm karşılaştırması YAKINLIK dilinde: uyum puanı farkın yönüne bakmaz (fazlalık da eksiklik de
// uyumu düşürür). Uyumlu = yeşil; fazla / az = turuncu; belirgin fazla / az = kırmızı. Fazlalık "güçlü yön" değildir.
// Değerlerde (K1) fark "senin için daha önemli / daha az önemli" diye anlatılır (bir üstünlük ya da eksik değildir).
const FARK = {
  uyumlu: { etiket: 'Uyumlu', renk: 'var(--gr)', zemin: 'var(--grl)' },
  fazla: { etiket: 'Beklenenden fazla', renk: 'var(--am)', zemin: 'var(--aml)' },
  belirgin_fazla: { etiket: 'Belirgin fazla', renk: 'var(--re)', zemin: 'var(--rel)' },
  eksik: { etiket: 'Beklenenden az', renk: 'var(--am)', zemin: 'var(--aml)' },
  belirgin_eksik: { etiket: 'Belirgin az', renk: 'var(--re)', zemin: 'var(--rel)' },
}
const DEGER_ETIKET = {
  fazla: 'Senin için daha önemli', belirgin_fazla: 'Senin için çok daha önemli',
  eksik: 'Senin için daha az önemli', belirgin_eksik: 'Senin için çok daha az önemli',
}
// eski kayıtlar (fark_sinifi yok) için kategoriden türetme
const KATEGORIDEN = { belirgin_ustun: 'belirgin_fazla', ustun: 'fazla', beklenti: 'uyumlu', altinda: 'eksik', belirgin_altinda: 'belirgin_eksik' }
const farkSinifi = (g) => g?.fark_sinifi || KATEGORIDEN[g?.kategori] || 'uyumlu'
function farkBilgisi(g) {
  const sinif = farkSinifi(g)
  const f = FARK[sinif] || FARK.uyumlu
  const deger = String(g?.degisken_kod || '').startsWith('D') && DEGER_ETIKET[sinif]
  return { ...f, sinif, etiket: deger || f.etiket }
}
// [2026-10-10] Özet kutularındaki üç grubun ne anlama geldiği (öğrenci dilinde)
const GRUP_ACIKLAMA = {
  uyumlu: { ad: 'bölümle uyumlu', metin: 'Bu özelliklerde bölümün beklediği düzeydesin. Uyumunu en çok bunlar destekler. Güçlü yönlerin de bu gruptan, senin en yüksek olduğun özelliklerden seçilir.' },
  fazla: { ad: 'beklenenden fazla', metin: 'Bu özelliklerde bölümün beklediğinden fazlasın. Bu bir eksiklik de avantaj da değil, bölümle aranda bir fark: bu yönünü bu bölümde daha az kullanabilirsin; sana uyup uymadığını sına. Değerlerde ise bu değer senin için, bölümün öne çıkardığından daha önemli demek; bölümün bu yönü sana uyar mı, karar verirken dikkate al.' },
  eksik: { ad: 'beklenenden az', metin: 'Bu özelliklerde bölümün beklediği düzeyin altındasın. Yol haritan bunların içinden bölüm için en ayırt edici en fazla 3 alana odaklanır: beceriler çalıştıkça gelişir, kişilik yönlerin küçük alışkanlıklarla esneyebilir, ilgileri deneyerek keşfedersin. Değerlerde ise bu değer senin için, bölümün öne çıkardığından daha az önemli demek; geliştirilecek bir eksik değil, karar verirken dikkate alacağın bir fark.' },
}
// [2026-10-09] Sadeleştirildi: yalnızca "Başladım" ve "Yaptım"
const DURUMLAR = [
  { kod: 'devam_ediyor', etiket: '▶ Başladım' },
  { kod: 'tamamlandi', etiket: '✓ Yaptım' },
]

function FarkRozeti({ g }) {
  const k = farkBilgisi(g)
  return (
    <span style={{ fontSize: 10.5, fontWeight: 700, color: k.renk, background: k.zemin, padding: '2px 8px', borderRadius: 20, whiteSpace: 'nowrap' }}>
      {k.etiket}
    </span>
  )
}

function Cip({ children, renk = 'var(--tx2)', zemin = 'var(--sur2)' }) {
  return <span style={{ fontSize: 10.5, fontWeight: 600, color: renk, background: zemin, padding: '2px 8px', borderRadius: 20, whiteSpace: 'nowrap' }}>{children}</span>
}

function KarsilastirmaSatiri({ g }) {
  const [acik, setAcik] = useState(false)
  return (
    <div style={{ marginBottom: 12 }}>
      <div onClick={() => setAcik(!acik)} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, marginBottom: 5, cursor: 'pointer' }}>
        <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--tx2)' }}>{g.degisken_adi} <span style={{ color: 'var(--tx3)', fontWeight: 400 }}>{acik ? '▴' : 'ⓘ'}</span></div>
        <FarkRozeti g={g} />
      </div>
      {acik && (
        <div style={{ fontSize: 11.5, color: 'var(--tx3)', margin: '0 0 6px', lineHeight: 1.45 }}>
          {g.nedir}{(g.aciklama || g.durum_tespiti) ? <><br /><span style={{ color: 'var(--tx2)' }}>{g.aciklama || g.durum_tespiti}</span></> : null}
        </div>
      )}
      {/* [2026-10-17] Senin çubuğun fark rengiyle (yeşil uyumlu · turuncu / kırmızı fark), bölümünki nötr */}
      <div className="mini-cubuk-track" style={{ width: '100%', marginBottom: 3 }}>
        <div className="mini-cubuk-fill" style={{ width: `${g.ogrenci_goreli ?? g.ogrenci_puan}%`, background: farkBilgisi(g).renk }} />
      </div>
      <div className="mini-cubuk-track" style={{ width: '100%' }}>
        <div className="mini-cubuk-fill" style={{ width: `${g.bolum_goreli ?? g.bolum_beklenen}%`, background: 'var(--tx3)' }} />
      </div>
    </div>
  )
}

// Tek bir yol haritası adımı: ne yapacağın, ne kadar sürer + [2026-10-09] adım adım "Nasıl yaparsın?",
// kontrol listesi olarak "Nasıl anlarsın?" ve ipucu (açılır-kapanır; sıradaki adımda açık gelir) + durum düğmeleri
function kontrolOku(kod) {
  try { return JSON.parse(localStorage.getItem(`adim_kontrol_${kod}`) || '[]') } catch { return [] }
}
function kontrolYaz(kod, liste) {
  try { localStorage.setItem(`adim_kontrol_${kod}`, JSON.stringify(liste)) } catch { /* gizli sekme */ }
}

function AdimKarti({ adim, onDurum, vurgulu = false, alanGoster = true }) {
  const bitti = adim.durum === 'tamamlandi'
  const basladi = adim.durum === 'devam_ediyor'
  const detayVar = (adim.nasil && adim.nasil.length > 0) || (adim.kontrol && adim.kontrol.length > 0)
  const [acik, setAcik] = useState(vurgulu)
  const [isaretli, setIsaretli] = useState(() => kontrolOku(adim.kod))
  const [bekle, setBekle] = useState(null)
  const [hata, setHata] = useState(null)
  const [formAcik, setFormAcik] = useState(false)   // [2026-10-10] "Yaptım" → kısa geri bildirim
  const kontrolSayisi = adim.kontrol?.length || 0
  const hepsiIsaretli = kontrolSayisi > 0 && isaretli.length >= kontrolSayisi

  function tikla(i) {
    const yeni = isaretli.includes(i) ? isaretli.filter((x) => x !== i) : [...isaretli, i]
    setIsaretli(yeni); kontrolYaz(adim.kod, yeni)
    // ilk işaretle adım otomatik "başladım" olur
    if (!basladi && !bitti && yeni.length === 1 && !isaretli.length) durumGonder('devam_ediyor')
  }
  async function durumGonder(kod, gb) {
    if (kod === 'tamamlandi' && gb === undefined) { setFormAcik(true); return }
    setBekle(kod); setHata(null)
    const h = await onDurum(adim.kod, kod, gb)
    if (h) setHata(h)
    else setFormAcik(false)
    setBekle(null)
  }

  return (
    <div className={`adim-kart${vurgulu ? ' vurgulu' : ''}${bitti && !vurgulu ? ' bitti' : ''}`}>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
        {alanGoster && <Cip renk="var(--pu)" zemin="var(--pul)">{adim.degisken_adi}</Cip>}
        <Cip>{adim.tur_etiket}</Cip>
        <Cip>⏱ {adim.sure}</Cip>
        {basladi && <Cip renk="var(--am)" zemin="var(--aml)">▶ Devam ediyor</Cip>}
      </div>
      <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 4, textDecoration: bitti ? 'line-through' : 'none' }}>{bitti ? '✓ ' : ''}{adim.baslik}</div>
      <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5, marginBottom: 8 }}>{adim.aciklama}</div>
      {adim.kazanim && !bitti && (
        <div className="adim-kazanim"><span>🎁 Sana ne katar?</span> {adim.kazanim}</div>
      )}
      {vurgulu && adim.uyarlama && !bitti && <div className="adim-uyarlama">🧭 {adim.uyarlama}</div>}
      {bitti && <GeriBildirimOzeti gb={adim.geri_bildirim} />}

      {detayVar ? (
        <>
          <button type="button" className="adim-ac" aria-expanded={acik} onClick={() => setAcik(!acik)}>
            <span>{acik ? '▾' : '▸'}</span> {acik ? 'Ayrıntıları gizle' : `Nasıl yaparsın? · ${adim.nasil.length} adım`}
          </button>
          {acik ? (
            <div className="adim-detay">
              <div className="adim-detay-baslik">🛠️ Nasıl yaparsın?</div>
              <ol className="adim-nasil">
                {adim.nasil.map((m, i) => <li key={i}>{m}</li>)}
              </ol>
              {kontrolSayisi > 0 && (
                <>
                  <div className="adim-detay-baslik">✅ Nasıl anlarsın? <span>Yaptıklarını işaretle. Hepsi tamamsa bu adım bitti:</span></div>
                  <ul className="adim-kontrol tiklanir">
                    {adim.kontrol.map((m, i) => (
                      <li key={i}>
                        <label className={isaretli.includes(i) || bitti ? 'isaretli' : ''}>
                          <input type="checkbox" checked={isaretli.includes(i) || bitti} disabled={bitti} onChange={() => tikla(i)} />
                          <span>{m}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                  {!bitti && <div className="adim-kontrol-durum">{hepsiIsaretli ? '🎉 Hepsini işaretledin. Şimdi aşağıdaki “Yaptım” düğmesine bas.' : `${Math.min(isaretli.length, kontrolSayisi)} / ${kontrolSayisi} işaretlendi`}</div>}
                </>
              )}
              {adim.ipucu && <div className="adim-ipucu">💡 {adim.ipucu}</div>}
            </div>
          ) : (
            <div style={{ fontSize: 11.5, color: 'var(--tx3)', margin: '6px 0 8px' }}><b>Nasıl anlarsın?</b> {adim.olcut}</div>
          )}
        </>
      ) : (
        <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginBottom: 8 }}><b>Nasıl anlarsın?</b> {adim.olcut}</div>
      )}

      {formAcik && !bitti ? (
        <>
          <TamamlaFormu adim={adim} onKaydet={(gb) => durumGonder('tamamlandi', gb)} onVazgec={() => setFormAcik(false)} />
          {hata && <div className="auth-error" style={{ marginTop: 6, fontSize: 12 }}>{hata}</div>}
        </>
      ) : (
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        {bitti ? (
          <button className="btn sec" style={vurgulu ? { fontSize: 13.5, padding: '9px 18px' } : { fontSize: 11.5, padding: '5px 10px' }}
            disabled={!!bekle} onClick={() => durumGonder(null)}>{bekle ? <span className="spin" /> : '↩ Geri al'}</button>
        ) : DURUMLAR.map((d) => {
          const aktif = adim.durum === d.kod
          const birincil = d.kod === 'tamamlandi' ? (vurgulu || hepsiIsaretli) : aktif
          return (
            <button key={d.kod} className={birincil ? 'btn' : 'btn sec'} aria-pressed={aktif}
              style={vurgulu ? { fontSize: 13.5, padding: '9px 18px' } : { fontSize: 11.5, padding: '5px 10px' }}
              disabled={!!bekle} onClick={() => durumGonder(aktif ? null : d.kod)}>
              {bekle === d.kod ? <span className="spin" /> : d.kod === 'devam_ediyor' && aktif ? '▶ Başladın (geri al)' : d.etiket}
            </button>
          )
        })}
        {hata && <span className="auth-error" style={{ margin: 0, padding: '4px 10px', fontSize: 12 }}>{hata}</span>}
      </div>
      )}
    </div>
  )
}

// ============================================================
// [2026-10-09] Sayfa başlık başlık sekmelere bölündü:
//   Özet · Yol Haritası · Güçlü Yönlerin · Bölümle Karşılaştırma · Gelişimin
// [2026-10-09] Hedef seçimi/değiştirme yalnızca Ayarlar sayfasında (en fazla 3 değişiklik).
// ============================================================
// [2026-10-18] 8 sekme 3 gruba toplandı (içerik aynı; alt sekmeler grubun içinde). Sekme kodları değişmedi,
// eski bağlantılar (?sekme=…) doğru grubu ve alt sekmeyi açar.
const GRUPLAR = [
  { kod: 'durum', ad: 'Durumum', ikon: '🧭', alt: [
    { kod: 'ozet', ad: 'Özet' },
    { kod: 'karsilastirma', ad: 'Sen ve Bölümün' },
    { kod: 'gelisim', ad: 'Gelişimin' },
  ] },
  { kod: 'adimlar', ad: 'Adımlarım', ikon: '🗺️', alt: [
    { kod: 'yol', ad: 'Yol Haritam' },
    { kod: 'guclu', ad: 'Güçlü Yönlerin' },
    { kod: 'ilham', ad: 'İlham Kaynakları' },
  ] },
  { kod: 'tani', ad: 'Bölümünü Tanı', ikon: '📘', alt: [
    { kod: 'bolum', ad: 'Bölüm Rehberi' },
    { kod: 'gun', ad: 'Bir Günümü Yaşa' },
  ] },
]
const SEKMELER = GRUPLAR.flatMap((g) => g.alt.map((s) => ({ ...s, grup: g.kod })))

// [2026-10-09] İlham kaynakları — yönetimdeki "Gelişim Kaynak Havuzu" öğrencinin odak ve güçlü alanlarına göre
const KAYNAK_TIP = {
  kitap: { ad: 'Kitap', ikon: '📖', renk: 'var(--pu)', zemin: 'var(--pul)' },
  film: { ad: 'Film / Belgesel', ikon: '🎬', renk: 'var(--am)', zemin: 'var(--aml)' },
  rol_model: { ad: 'İlham veren kişi', ikon: '🌟', renk: 'var(--gr)', zemin: 'var(--grl)' },
  olay: { ad: 'Önemli olay', ikon: '🗓️', renk: 'var(--tl)', zemin: 'var(--tll)' },
  psikolojik_yaklasim: { ad: 'Yaklaşım', ikon: '🧠', renk: 'var(--tl)', zemin: 'var(--tll)' },
  aktivite: { ad: 'Aktivite', ikon: '🎯', renk: 'var(--re)', zemin: 'var(--rel)' },
}

function filizeSor(k, alan) {
  window.dispatchEvent(new CustomEvent('filiz-ac', { detail: { mesaj: `"${k.baslik}" (${KAYNAK_TIP[k.tip]?.ad || k.tip}) bana ${alan} konusunda nasıl yardımcı olabilir? Nereden başlamalıyım?` } }))
}

// [2026-10-10] Kaynaklar türe göre (Kitaplar, Filmler, Kişiler, Olaylar…) geniş ızgarada; istenirse alana göre.
// Kitap ve filmler tek tıkla Kütüphanem'e "okumak / izlemek istiyorum" olarak eklenir.
const KUTUPHANE_KATEGORI = { kitap: 'kitap', film: 'izleme' }

function KaynakKarti({ k, alan, grup, eklendi, onEkle, alanGoster = true }) {
  const t = KAYNAK_TIP[k.tip] || { ad: k.tip, ikon: '•', renk: 'var(--tx2)', zemin: 'var(--sur2)' }
  const modulAcik = useModuller()   // [2026-10-10] paket: Filiz / Kütüphane kapalıysa düğmeleri yok
  return (
    <div className="ilham-kart">
      <div className="ilham-ust">
        <span className="ilham-tip" style={{ color: t.renk, background: t.zemin }}>{t.ikon} {t.ad}</span>
        {alanGoster && <span className={`ilham-alan-cip ${grup}`} title={grup === 'guclu' ? 'Güçlü yönün' : 'Gelişim alanın'}>{grup === 'guclu' ? '💪' : '🌱'} {alan}</span>}
      </div>
      <div className="ilham-baslik">{k.baslik}</div>
      <div className="ilham-aciklama">{k.aciklama}</div>
      <div className="ilham-islem">
        {modulAcik('filiz') && <button className="hg-link ilham-sor" onClick={() => filizeSor(k, alan)}>💬 Filiz'e sor</button>}
        {KUTUPHANE_KATEGORI[k.tip] && modulAcik('kutuphane') && (eklendi
          ? <span className="ilham-eklendi">✓ Kütüphanende</span>
          : <button className="hg-link" onClick={() => onEkle(k, alan)}>＋ Kütüphaneme ekle</button>)}
      </div>
    </div>
  )
}

function IlhamSekmesi({ kaynaklar }) {
  const [tip, setTip] = useState('')
  const [gorunum, setGorunum] = useState('tur')
  const [eklenen, setEklenen] = useState(new Set())
  useEffect(() => {
    api.kutuphane().then((v) => setEklenen(new Set(v.kayitlar.map((x) => x.baslik.toLocaleLowerCase('tr-TR'))))).catch(() => {})
  }, [])
  if (!kaynaklar) return <div className="bos-durum">Kaynaklar hazırlanıyor…</div>
  if (!kaynaklar.alanlar.length) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 30 }}>
        <div style={{ fontSize: 30 }}>📚</div>
        <div style={{ fontWeight: 800, margin: '6px 0 4px' }}>İlham kaynaklarını birlikte keşfedelim</div>
        <div className="ps" style={{ margin: 0 }}>
          {kaynaklar.aranan_alanlar?.length ? <>Odak alanların: <b>{kaynaklar.aranan_alanlar.join(', ')}</b>. </> : null}Bu alanlarda ilgini çeken kitap, film ya da belgeselleri Kütüphanem'e ekle. Böylece kendi ilham listeni kurarsın.
        </div>
      </div>
    )
  }
  const ekle = async (k, alan) => {
    try {
      await api.kutuphaneEkle({ kategori: KUTUPHANE_KATEGORI[k.tip], baslik: k.baslik, durum: 'istek', notlar: `İlham kaynağı önerisi (${alan})` })
      setEklenen((s) => new Set([...s, k.baslik.toLocaleLowerCase('tr-TR')]))
    } catch { /* yoksay */ }
  }
  const hepsi = kaynaklar.alanlar.flatMap((a) => a.kaynaklar.map((k) => ({ k, alan: a.degisken_adi, grup: a.grup, kategori: a.kategori })))
  const tekil = []
  const gorulen = new Set()
  hepsi.forEach((x) => { if (!gorulen.has(x.k.id)) { gorulen.add(x.k.id); tekil.push(x) } })
  const tipler = Object.keys(KAYNAK_TIP).filter((t) => tekil.some((x) => x.k.tip === t))
  const kart = (x, alanGoster = true) => (
    <KaynakKarti key={`${x.k.id}-${x.alan}`} k={x.k} alan={x.alan} grup={x.grup} alanGoster={alanGoster}
      eklendi={eklenen.has(x.k.baslik.toLocaleLowerCase('tr-TR'))} onEkle={ekle} />
  )
  return (
    <>
      <div className="ilham-ust-bar">
        <div className="ps" style={{ margin: 0, flex: 1, minWidth: 260 }}>
          Burada gelişim alanlarına ve güçlü yönlerine göre seçilmiş kitaplar, filmler, ilham veren kişiler ve önemli olaylar var. Kitap ve filmleri Kütüphanem'e ekleyebilirsin. Merak ettiğini Filiz'e sor.
        </div>
        <div className="ilham-gorunum" role="tablist">
          <button className={gorunum === 'tur' ? 'aktif' : ''} onClick={() => setGorunum('tur')}>Türe göre</button>
          <button className={gorunum === 'alan' ? 'aktif' : ''} onClick={() => setGorunum('alan')}>Alana göre</button>
        </div>
      </div>
      <div className="ilham-ozet">
        <button className={!tip ? 'aktif' : ''} onClick={() => setTip('')}><b>{tekil.length}</b><span>Tümü</span></button>
        {tipler.map((t) => (
          <button key={t} className={tip === t ? 'aktif' : ''} onClick={() => setTip(tip === t ? '' : t)}>
            <b>{tekil.filter((x) => x.k.tip === t).length}</b><span>{KAYNAK_TIP[t].ikon} {KAYNAK_TIP[t].ad}</span>
          </button>
        ))}
      </div>
      {gorunum === 'tur' ? (
        tipler.filter((t) => !tip || t === tip).map((t) => (
          <section key={t} className="ilham-bolum">
            <h3>{KAYNAK_TIP[t].ikon} {KAYNAK_TIP[t].ad}<small>{tekil.filter((x) => x.k.tip === t).length}</small></h3>
            <div className="ilham-grid">{tekil.filter((x) => x.k.tip === t).map((x) => kart(x))}</div>
          </section>
        ))
      ) : (
        [['gelisim', '🌱 Gelişim alanların için'], ['guclu', '💪 Güçlü yönlerini kullanmak için']].map(([g, baslik]) => {
          const alanlar = kaynaklar.alanlar.filter((a) => a.grup === g)
            .map((a) => ({ ...a, liste: a.kaynaklar.filter((k) => !tip || k.tip === tip) })).filter((a) => a.liste.length)
          if (!alanlar.length) return null
          return (
            <section key={g} className="ilham-bolum">
              <h3>{baslik}</h3>
              {alanlar.map((a) => (
                <div key={a.degisken_kod} className="ilham-alan-satir">
                  <div className="ilham-alan-bas"><b>{a.degisken_adi}</b>{a.grup === 'guclu'
                    ? <span style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--gr)', background: 'var(--grl)', padding: '2px 8px', borderRadius: 20, whiteSpace: 'nowrap' }}>Güçlü yönün</span>
                    : <FarkRozeti g={a} />}</div>
                  <div className="ilham-grid">{a.liste.map((k) => kart({ k, alan: a.degisken_adi, grup: a.grup }, false))}</div>
                </div>
              ))}
            </section>
          )
        })
      )}
    </>
  )
}

function Bolum({ baslik, alt, children, sag }) {
  return (
    <section className="koc-bolum">
      <div className="koc-bolum-bas">
        <div>
          <h2 className="koc-bolum-baslik">{baslik}</h2>
          {alt && <div className="koc-bolum-alt">{alt}</div>}
        </div>
        {sag}
      </div>
      {children}
    </section>
  )
}

function OdakSatirlari({ plan }) {
  return (
    <div className="koc-odak-liste">
      {plan.odak_alanlari.map((o) => (
        <div key={o.degisken_kod} className="koc-odak-satir">
          <span className="koc-odak-no">{o.oncelik_sirasi}</span>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div style={{ fontSize: 13.5, fontWeight: 700 }}>{o.degisken_adi}</div>
            <div style={{ fontSize: 12, color: 'var(--tx2)', lineHeight: 1.5 }}>{o.neden_onemli}</div>
            {o.alan_turu_aciklama && <div className="koc-alan-turu-not">{o.alan_turu_aciklama}</div>}
            {o.maarif?.length > 0 && <div className="maarif-satir">Maarif Modeli'nde ilişkili: <span translate="no">{o.maarif.join(' · ')}</span></div>}
          </div>
          <div className="koc-odak-rozetler">
            <AlanTuruRozeti odak={o} />
            <FarkRozeti g={o} />
          </div>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------- 1) Özet
// [2026-10-10] Önce "ne demek?" (üç grup + hangi özellikler), sonra "neden bu adımlar?", en son şimdiki adım.
function OzetSekmesi({ plan, gelisim, sekmeyeGit }) {
  const [acikGrup, setAcikGrup] = useState(null)
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  const s = plan.siradaki_adim
  const gruplar = { uyumlu: [], fazla: [], eksik: [] }
  ;(gelisim || []).forEach((g) => gruplar[farkSinifi(g).replace('belirgin_', '')].push(g))
  const renk = { uyumlu: 'var(--gr)', fazla: 'var(--am)', eksik: 'var(--am)' }
  return (
    <>
      <div className="koc-ozet-kutular">
        {['uyumlu', 'fazla', 'eksik'].map((k) => (
          <button key={k} className={`koc-ozet-kutu${acikGrup === k ? ' acik' : ''}`} onClick={() => setAcikGrup(acikGrup === k ? null : k)} aria-expanded={acikGrup === k}>
            <b style={{ color: renk[k] }}><Sayac deger={gruplar[k].length} /></b><span>{GRUP_ACIKLAMA[k].ad}</span>
            <small>{acikGrup === k ? 'gizle ▴' : 'ne demek? ▾'}</small>
          </button>
        ))}
      </div>
      {acikGrup && (
        <div className="koc-grup-aciklama" style={{ borderColor: renk[acikGrup] }}>
          <div>{GRUP_ACIKLAMA[acikGrup].metin}</div>
          {gruplar[acikGrup].length > 0 && (
            <div className="koc-grup-cipler">
              {gruplar[acikGrup].map((g) => <span key={g.degisken_id}>{g.degisken_adi}</span>)}
            </div>
          )}
          <button className="hg-link" onClick={() => sekmeyeGit(acikGrup === 'uyumlu' ? 'guclu' : acikGrup === 'eksik' ? 'yol' : 'karsilastirma')}>
            {acikGrup === 'uyumlu' ? 'Güçlü yönlerini gör →' : acikGrup === 'eksik' ? 'Yol haritanı gör →' : 'Bölümle tek tek karşılaştır →'}
          </button>
        </div>
      )}
      <div className="koc-ozet-not">
        Bu sayılar, <b>senin</b> özelliklerini <b>{plan.hedef_bolum_adi}</b> bölümünün beklediği düzeyle karşılaştırır. Hangi özellikler olduğunu görmek için bir kutuya dokun.
      </div>

      {plan.odak_alanlari.length > 0 ? (
        <Bolum baslik="🎯 Neden bu adımlar?" alt={`Bu adımları, ${plan.hedef_bolum_adi} için seni en çok ileri taşıyacak ${plan.odak_alanlari.length} alana göre seçtik.`}
          sag={<button className="hg-link" onClick={() => sekmeyeGit('karsilastirma')}>Karşılaştırmayı gör →</button>}>
          <OdakSatirlari plan={plan} />
        </Bolum>
      ) : (
        <div className="card">
          <div className="ps" style={{ margin: 0 }}>
            {plan.hedef_bolum_adi} için belirgin bir gelişim alanın görünmüyor. Güçlü yönlerini kullanmak için “Güçlü Yönlerin” sekmesindeki adımlara bak; “Sen ve Bölümün” sekmesinde fazlalıklarını da gözden geçir.
          </div>
        </div>
      )}

      <Bolum baslik="👉 Şimdiki adımın">
        <button className="card koc-siradaki" onClick={() => sekmeyeGit('yol')}>
          {s ? (
            <>
              <div style={{ minWidth: 0 }}>
                <div className="koc-siradaki-ust">{s.degisken_adi} · {s.tur_etiket} · ⏱ {s.sure}</div>
                <div className="koc-siradaki-baslik">{s.baslik}</div>
              </div>
              <span className="koc-siradaki-git">Yol haritamda aç →</span>
            </>
          ) : <div style={{ fontWeight: 700 }}>🎉 Yol haritandaki tüm adımları tamamladın!</div>}
        </button>
      </Bolum>
    </>
  )
}

// ---------------------------------------------------------------- 2) Yol haritası — her seferinde TEK adım
// [2026-10-09] Lise öğrencisi için sade akış: ekranda yalnızca şimdiki adım var. "Yaptım" deyince sıradaki gelir.
// Üstte noktalı ilerleme yolu, altta sıradaki 2 adımın başlığı ve katlanmış "Tamamladıkların" listesi.
function YolHaritasiSekmesi({ plan, gelisim, hedefId, onDurum, kaynaklar, sekmeyeGit, onOlc }) {
  const [bitenAcik, setBitenAcik] = useState(false)
  const gorulduAnahtari = `kocluk_karsilastirma_goruldu_${hedefId}`
  const [karsilastirmaGoruldu] = useState(() => { try { return localStorage.getItem(gorulduAnahtari) === '1' } catch { return true } })
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  if (plan.odak_alanlari.length === 0) {
    return <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedef için belirgin bir gelişim alanın yok. “Güçlü Yönlerin” sekmesine göz at.</div></div>
  }
  const tum = plan.asamalar.flatMap((a) => a.adimlar.map((x) => ({ ...x, asama_baslik: a.baslik })))
  const simdiki = plan.siradaki_adim ? (tum.find((x) => x.kod === plan.siradaki_adim.kod) || plan.siradaki_adim) : null
  const biten = tum.filter((x) => x.durum === 'tamamlandi')
  const sirada = tum.filter((x) => x.durum !== 'tamamlandi' && x.kod !== simdiki?.kod).slice(0, 2)
  const yuzde = tum.length ? Math.round((100 * biten.length) / tum.length) : 0
  return (
    <>
      <div className="card yh-ust">
        <div className="yh-ust-satir">
          <div>
            <div className="yh-sayi"><Sayac deger={biten.length} /><span> / {tum.length} adım</span></div>
            <div className="yh-alt">Bir adımı bitirince sıradaki açılır. Acele etme, haftada 1-2 adım yeterli.</div>
          </div>
          <div className="yh-yuzde">%{yuzde}</div>
        </div>
        <div className="yh-yol" aria-hidden="true">
          {tum.map((x) => (
            <span key={x.kod} title={x.baslik}
              className={`yh-nokta${x.durum === 'tamamlandi' ? ' bitti' : ''}${x.kod === simdiki?.kod ? ' simdi' : ''}`} />
          ))}
        </div>
      </div>

      {!karsilastirmaGoruldu && (
        <div className="yh-once">
          <span>📊</span>
          <div><b>Önce neden bu adımları yaptığını gör.</b> Bu yol haritasını, seni {plan.hedef_bolum_adi} bölümünün beklentileriyle karşılaştırarak hazırladık.</div>
          <button className="btn sec" onClick={() => sekmeyeGit('karsilastirma')}>Sen ve Bölümün →</button>
        </div>
      )}
      {simdiki ? (
        <div key={simdiki.kod} className="yh-simdi">
          <div className="yh-etiket">Şimdiki adımın <span>{simdiki.asama_baslik?.replace(/^\d\. Aşama · /, '')}</span></div>
          {(() => {
            const odak = plan.odak_alanlari.find((o) => o.degisken_kod === simdiki.degisken_kod)
            const g = (gelisim || []).find((x) => x.degisken_adi === simdiki.degisken_adi)
            if (!odak && !g) return null
            return (
              <div className="yh-neden">
                <div className="yh-neden-bas">❓ Bu adım neden? <b>{simdiki.degisken_adi}</b>
                  {odak?.alan_turu ? <AlanTuruRozeti odak={odak} /> : g && <FarkRozeti g={g} />}</div>
                {odak?.neden_onemli && <div>{odak.neden_onemli}</div>}
                {odak?.alan_turu_aciklama && <div className="koc-alan-turu-not">{odak.alan_turu_aciklama}</div>}
                {g && (
                  <div className="yh-neden-cubuk">
                    <div><span>Sen</span><div className="mini-cubuk-track"><div className="mini-cubuk-fill" style={{ width: `${g.ogrenci_goreli ?? g.ogrenci_puan}%`, background: 'var(--pu)' }} /></div></div>
                    <div><span>Bölüm</span><div className="mini-cubuk-track"><div className="mini-cubuk-fill" style={{ width: `${g.bolum_goreli ?? g.bolum_beklenen}%`, background: 'var(--gr)' }} /></div></div>
                  </div>
                )}
              </div>
            )
          })()}
          <AdimKarti adim={simdiki} onDurum={onDurum} vurgulu />
          {(() => {
            const alan = kaynaklar?.alanlar.find((a) => a.degisken_kod === simdiki.degisken_kod)
            if (!alan) return null
            return (
              <div className="yh-ilham">
                <span className="yh-ilham-bas">📚 Bu alanda ilham al:</span>
                {alan.kaynaklar.slice(0, 2).map((k) => (
                  <span key={k.id} className="yh-ilham-oge">{KAYNAK_TIP[k.tip]?.ikon} <b>{k.baslik}</b></span>
                ))}
                <button className="hg-link" style={{ color: 'var(--pu)' }} onClick={() => sekmeyeGit('ilham')}>Tümünü gör →</button>
              </div>
            )
          })()}
        </div>
      ) : (
        <div className="card" style={{ textAlign: 'center', padding: 30 }}>
          <div style={{ fontSize: 34 }}>🎉</div>
          <div style={{ fontWeight: 800, marginTop: 6 }}>Yol haritanın tamamını bitirdin!</div>
          <div className="ps" style={{ margin: '4px 0 0' }}>Bir sonraki değerlendirme turunda gelişimini birlikte görelim.</div>
        </div>
      )}

      {sirada.length > 0 && (
        <div className="yh-sirada">
          <div className="yh-etiket">Sırada</div>
          {sirada.map((x, i) => (
            <div key={x.kod} className="yh-sirada-satir">
              <span className="yh-sirada-no">{biten.length + 2 + i}</span>
              <span className="yh-sirada-ad">{x.baslik}</span>
              <span className="yh-sirada-alan">{x.degisken_adi}</span>
            </div>
          ))}
        </div>
      )}

      {plan.odak_alanlari.some((o) => o.olcum) && (
        <div className="olcum-alan">
          <div className="yh-etiket">📏 Gelişimini ölç <span>Her 3 adımda bir aynı soruları cevapla, öncesiyle sonrasını gör</span></div>
          <div className="olcum-izgara">
            {plan.odak_alanlari.filter((o) => o.olcum).map((o) => <OlcumKarti key={o.degisken_id} odak={o} onOlc={onOlc} />)}
          </div>
        </div>
      )}

      {biten.length > 0 && (
        <div className="yh-biten">
          <button className="hg-link" onClick={() => setBitenAcik(!bitenAcik)}>{bitenAcik ? '▴' : '▾'} Tamamladıkların ({biten.length})</button>
          {bitenAcik && (
            <div className="yh-biten-liste">
              {biten.map((x) => (
                <div key={x.kod} className="yh-biten-satir">
                  <span className="yh-tik">✓</span>
                  <span style={{ flex: 1, minWidth: 0 }}>{x.baslik}<GeriBildirimOzeti gb={x.geri_bildirim} /></span>
                  <button className="hg-link" onClick={() => onDurum(x.kod, null)} title="Yanlışlıkla işaretlediysen geri al">Geri al</button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  )
}

// [2026-10-09] Hedef kartı: hedef bölüm + kısa bölüm bilgisi. Hedef değişikliği yalnızca Ayarlar'dan.
function HedefKarti({ hedef, plan }) {
  const [b, setB] = useState(null)
  const { ac } = useBolumBilgi()
  const navigate = useNavigate()
  useEffect(() => { api.bolumBilgi(hedef.bolum_id).then(setB).catch(() => setB(null)) }, [hedef.bolum_id])
  const d = b?.detay
  const ozet = d?.ozet || b?.kisa_aciklama
  const meslekler = (d?.meslekler || []).slice(0, 3).map((m) => m.ad)
  const ilerleme = plan && plan.ilerleme.toplam ? plan.ilerleme : null
  return (
    <div className="card koc-hedef">
      <div className="koc-hedef-ust">
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="ct" style={{ marginBottom: 4 }}>🎯 Hedefin</div>
          <div className="koc-hedef-ad">{hedef.bolum_adi}</div>
          <div className="koc-hedef-cipler">
            {b?.ust_alan && <span>{b.ust_alan}</span>}
            {d?.puan_turu && <span>📝 {puanTuruMetni(d.puan_turu)}</span>}
            {d?.ogrenim_suresi && <span>⏱ {d.ogrenim_suresi}</span>}
          </div>
        </div>
        {ilerleme && (
          <div className="koc-hedef-ilerleme">
            <b>{ilerleme.tamamlanan}/{ilerleme.toplam}</b><span>adım tamam</span>
          </div>
        )}
      </div>
      {ozet && <p className="koc-hedef-ozet">{ozet}</p>}
      {meslekler.length > 0 && <div className="koc-hedef-meslek"><b>Mezunlar ne iş yapar?</b> {meslekler.join(' · ')}</div>}
      <div className="koc-hedef-alt">
        <button className="hg-link" style={{ color: 'var(--pu)' }} onClick={() => ac(hedef.bolum_id, hedef.bolum_adi)}>Bölüm hakkında her şey →</button>
        <button className="hg-link" onClick={() => navigate('/profil#hedef')}>
          Hedefini Ayarlar'dan değiştirebilirsin{hedef.kalan_hak != null ? ` · ${hedef.kalan_hak} değiştirme hakkın kaldı` : ''}
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- 3) Güçlü yönler
function GucluSekmesi({ plan, onDurum }) {
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  if (!plan.guclu_yonler.length) return <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedefe göre henüz öne çıkan bir güçlü yönün yok. Güçlü yön, hem bölümün beklediği düzeyde olduğun hem de kendi profilinde yüksek olan özelliklerindir. Katmanları yeniden tamamladığında burası güncellenir.</div></div>
  return (
    <>
      <div className="ps" style={{ marginBottom: 14 }}>Bu özellikler kendi profilinde öne çıkıyor ve {plan.hedef_bolum_adi} de bu düzeyi bekliyor. Aşağıdaki adımlarla onları somut deneyimlere dönüştürebilirsin.</div>
      {plan.guclu_yonler.map((g) => (
        <section key={g.degisken_kod} className="koc-yatay">
          <div className="koc-yatay-sol">
            <FarkRozeti g={g} />
            <h2>✓ {g.degisken_adi}</h2>
            <p>{g.neden_onemli}</p>
            {g.maarif?.length > 0 && <div className="maarif-satir">Maarif Modeli'nde ilişkili: <span translate="no">{g.maarif.join(' · ')}</span></div>}
            <small>{g.adimlar.filter((a) => a.durum === 'tamamlandi').length}/{g.adimlar.length} adım tamamlandı</small>
          </div>
          <div className="koc-adim-grid koc-yatay-sag">
            {g.adimlar.map((adim) => <AdimKarti key={adim.kod} adim={adim} onDurum={onDurum} alanGoster={false} />)}
          </div>
        </section>
      ))}
    </>
  )
}

// ---------------------------------------------------------------- 4) Karşılaştırma
function KarsilastirmaSekmesi({ gelisim, hedef }) {
  useEffect(() => { try { localStorage.setItem(`kocluk_karsilastirma_goruldu_${hedef.bolum_id}`, '1') } catch { /* yoksay */ } }, [hedef.bolum_id])
  const gruplar = {}
  gelisim.forEach((g) => {
    const anahtar = g.katman_kod || '?'
    if (!gruplar[anahtar]) gruplar[anahtar] = { ad: g.katman_adi || anahtar, satirlar: [] }
    gruplar[anahtar].satirlar.push(g)
  })
  const sira = Object.keys(gruplar).sort()
  const [secili, setSecili] = useState(sira[0])
  const grup = gruplar[secili] || gruplar[sira[0]]
  return (
    <div className="card">
      <div className="drl" style={{ marginBottom: 6 }}>
        <div className="dli"><div className="ddt" style={{ background: 'linear-gradient(90deg, var(--gr) 0 33%, var(--am) 33% 66%, var(--re) 66%)' }} /> Sen (renk: farkın büyüklüğü)</div>
        <div className="dli"><div className="ddt" style={{ background: 'var(--tx3)' }} /> {hedef.bolum_adi}</div>
      </div>
      <div className="ps" style={{ margin: '0 0 14px', fontSize: 11.5 }}>
        Bu karşılaştırma bölüm önerisi değildir; hedef bölümüne hazırlanırken nelere odaklanacağını gösterir. Her katmanda bir özelliğinin, diğer özelliklerine göre ne kadar öne çıktığına bakıyor ve bunu bölümün beklentisiyle karşılaştırıyoruz. İki çubuk aynı ölçekte. Bölümün beklentisine yakın olmak uyumu artırır; fazlası da azı da bir farktır. Açıklama için özelliğin adına dokun.
      </div>
      <div className="koc-etiket-rehber">
        <span><b style={{ color: 'var(--gr)' }}>Uyumlu</b> bölümün beklediği düzeydesin</span>
        <span><b style={{ color: 'var(--am)' }}>Beklenenden fazla / az</b> bölümle aranda fark var</span>
        <span><b style={{ color: 'var(--re)' }}>Belirgin fazla / az</b> fark büyük</span>
        <span><b>Değerlerde</b> “senin için daha önemli / daha az önemli” yazar</span>
      </div>
      <div className="koc-katman-cipler">
        {sira.map((kod) => {
          const n = gruplar[kod].satirlar.filter((g) => farkSinifi(g) !== 'uyumlu').length
          return (
            <button key={kod} className={kod === secili ? 'aktif' : ''} onClick={() => setSecili(kod)}>
              {gruplar[kod].ad}{n > 0 && <span className="koc-cip-sayi">{n}</span>}
            </button>
          )
        })}
      </div>
      <div className="koc-karsilastirma-liste">
        {grup.satirlar.slice().sort((a, b) => a.degisken_adi.localeCompare(b.degisken_adi, 'tr')).map((g) => <KarsilastirmaSatiri key={g.degisken_id} g={g} />)}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- 5) Turlar arası gelişim
// [2026-10-10] Gelişimin: yaptıklarının zaman çizelgesi + son 8 hafta + (2. turdan sonra) özellik değişimi
const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const kisaTarih = (t) => { const d = new Date(t); return `${d.getDate()} ${AY[d.getMonth()]}` }

function GelisimSekmesi({ karsilastirma }) {
  const [g, setG] = useState(null)
  useEffect(() => { api.gelisimimGetir().then(setG).catch(() => setG({ adimlar: [], haftalar: [], ozet: null })) }, [])
  const maks = Math.max(1, ...(g?.haftalar || []).map((h) => h.gorev_tamam + h.adim))

  return (
    <>
      {g?.ozet && (
        <div className="gm-ozet">
          <div><b>{g.ozet.tamamlanan_adim}</b><span>tamamlanan adım</span></div>
          <div><b>{g.ozet.tamamlanan_gorev}</b><span>haftalık görev</span></div>
          <div><b>{g.ozet.ust_uste_hafta}</b><span>hafta üst üste aktif{g.ozet.ust_uste_hafta >= 3 ? ' 🔥' : ''}</span></div>
        </div>
      )}
      {g?.haftalar?.length > 0 && (
        <div className="card">
          <div className="ct">Son 8 hafta</div>
          <div className="gm-haftalar" role="img" aria-label="Son 8 haftada tamamlanan görev ve adım sayıları">
            {g.haftalar.map((h, i) => {
              const top = h.gorev_tamam + h.adim
              return (
                <div key={h.hafta} className="gm-hafta" title={`${kisaTarih(h.hafta)} haftası: ${h.gorev_tamam} görev, ${h.adim} adım`}>
                  <span className="gm-deger">{top || ''}</span>
                  <div className="gm-sutun"><div style={{ height: `${(top / maks) * 100}%`, animationDelay: `${i * 50}ms` }} /></div>
                  <span className="gm-etiket">{i === g.haftalar.length - 1 ? 'Bu hafta' : kisaTarih(h.hafta)}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
      <div className="card">
        <div className="ct">Yaptıkların</div>
        {!g ? <div className="bos-durum yukleniyor" style={{ padding: 12 }}>Yükleniyor…</div> : g.adimlar.length === 0 ? (
          <div className="ps" style={{ margin: 0 }}>Yol haritandaki bir adımı “Yaptım” diye işaretle. Yaptıkların tarihiyle birlikte burada listelenir.</div>
        ) : (
          <ol className="gm-zaman">
            {g.adimlar.slice(0, 20).map((a) => (
              <li key={a.kod + a.zaman}>
                <span className="gm-tarih">{a.zaman ? kisaTarih(a.zaman) : ''}</span>
                <span className={`gm-nokta${a.guclu_yon ? ' guclu' : ''}`} />
                <div><b>{a.baslik}</b><small>{a.ozellik}{a.bolum ? ` · ${a.bolum}` : ''}</small></div>
              </li>
            ))}
          </ol>
        )}
      </div>
      <div className="ct" style={{ marginTop: 18 }}>Değerlendirmeler arası değişim</div>
      {(!karsilastirma || karsilastirma.length === 0) ? (
        <div className="card" style={{ textAlign: 'center', padding: 24 }}>
          <div style={{ fontSize: 26 }}>📈</div>
          <div style={{ fontWeight: 700, margin: '6px 0 4px' }}>İkinci değerlendirme turunda burada görünecek</div>
          <div className="ps" style={{ margin: 0 }}>Bir sonraki turu tamamla. O zaman her özelliğindeki değişimi ilk turla karşılaştırıp burada gösteririz.</div>
        </div>
      ) : (
        <div className="ll">
          {karsilastirma.map((k) => (
            <div key={k.degisken_id} className="ob-card">
              <div className="ob-top">
                <div className="ob-body">
                  <div className="ob-name">{k.degisken_adi}</div>
                  <div className="ld">{k.eski_puan} → {k.yeni_puan} ({k.degisim > 0 ? '+' : ''}{k.degisim})</div>
                  {k.yorum_metni && <div className="ld" style={{ marginTop: 4 }}>{k.yorum_metni}</div>}
                </div>
                <span className="bdg bdg-prog">{k.trend.replaceAll('_', ' ')}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  )
}

export default function KoclukSayfasi() {
  const [hedef, setHedef] = useState(undefined) // undefined=yükleniyor, null=yok
  const [gelisim, setGelisim] = useState(null)
  const [plan, setPlan] = useState(null)
  const [karsilastirma, setKarsilastirma] = useState(null)
  const [hata, setHata] = useState(null)
  const [kilit, setKilit] = useState(null) // K5 bitmediyse backend 409 döner
  const [kaynaklar, setKaynaklar] = useState(null)
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()
  const sekme = SEKMELER.some((s) => s.kod === params.get('sekme')) ? params.get('sekme') : 'ozet'
  function sekmeyeGit(kod) {
    const p = new URLSearchParams(params); p.set('sekme', kod); setParams(p, { replace: true })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // [2026-10-09] Hedef seçimi artık yalnızca Ayarlar'da: eski "?hedef=ID" bağlantıları oraya yönlendirilir
  useEffect(() => {
    const id = Number(params.get('hedef'))
    if (id) navigate(`/profil?hedef=${id}#hedef`, { replace: true })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    api.aktifHedefGetir().then(setHedef).catch(() => setHedef(null))
  }, [])

  const analiziYukle = useCallback(() => {
    setGelisim(null); setPlan(null); setKilit(null); setHata(null)
    api.gelisimAnaliziGetir().then(setGelisim).catch((e) => (e.status === 409 ? setKilit(e.detail) : setHata(e.detail)))
    api.gelisimPlaniGetir().then(setPlan).catch(() => {})
    api.turKarsilastirmasiGetir().then(setKarsilastirma).catch(() => {})
    api.ilhamKaynaklariGetir().then(setKaynaklar).catch(() => setKaynaklar({ alanlar: [] }))
  }, [])

  useEffect(() => { if (hedef) analiziYukle() }, [hedef, analiziYukle])

  const [olcumAlani, setOlcumAlani] = useState(null)
  async function adimDurumu(kod, durum, geriBildirim) {
    try {
      await api.adimDurumuGuncelle(kod, durum, geriBildirim || {})
      setPlan(await api.gelisimPlaniGetir()) // ilerleme ve sıradaki adım sunucuda yeniden hesaplanır
      window.dispatchEvent(new CustomEvent('haftalik-guncellendi'))
      return null
    } catch (err) {
      return err.detail || 'Kaydedemedik. İnternet bağlantını kontrol et ve tekrar dene.'
    }
  }

  if (hedef === undefined) return <div className="pg"><div className="bos-durum yukleniyor">Yükleniyor…</div></div>

  const veriVar = hedef && gelisim && gelisim.length > 0

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Koçluğum</div>
        <div className="ps">Hedef bölümünle kendini karşılaştır ve adım adım ilerle. Her seferinde tek bir adıma odaklan.</div>
      </div>

      <div className="koc-kap">
        {hedef ? <HedefKarti hedef={hedef} plan={plan} /> : (
          <div className="card koc-hedef-yok">
            <div style={{ fontSize: 32 }}>🎯</div>
            <div>
              <div className="ct" style={{ marginBottom: 4 }}>Önce bir hedef bölüm seç</div>
              <div className="ps" style={{ margin: '0 0 12px', fontSize: 12.5 }}>Hedefini seçince seni o bölümle karşılaştırırız. Sonra sana adım adım bir gelişim planı hazırlarız. Hedefini Ayarlar sayfasından seçebilirsin.</div>
              <button className="btn" onClick={() => navigate('/profil#hedef')}>Hedef bölümümü seç →</button>
            </div>
          </div>
        )}

        {hata && <div className="auth-error">{hata}</div>}

        {hedef && kilit && (
          <div className="card" style={{ borderColor: 'var(--am)', background: 'var(--aml)' }}>
            <div style={{ fontSize: 13 }}>{kilit}</div>
          </div>
        )}

        {hedef && gelisim && gelisim.length === 0 && (
          <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedefle karşılaştırma yapmak için henüz veri yok. Önce katmanlarını tamamla.</div></div>
        )}

        {veriVar && (
          <>
            <div className="koc-sekmeler" role="tablist">
              {GRUPLAR.map((g) => {
                const aktif = SEKMELER.find((s) => s.kod === sekme)?.grup === g.kod
                return (
                  <button key={g.kod} role="tab" aria-selected={aktif} className={aktif ? 'aktif' : ''} onClick={() => !aktif && sekmeyeGit(g.alt[0].kod)}>
                    <span aria-hidden="true">{g.ikon}</span> {g.ad}
                    {g.kod === 'adimlar' && plan && plan.ilerleme.toplam > 0 && <span className="koc-cip-sayi">{plan.ilerleme.tamamlanan}/{plan.ilerleme.toplam}</span>}
                  </button>
                )
              })}
            </div>
            <div className="koc-alt-sekmeler" role="tablist">
              {GRUPLAR.find((g) => g.alt.some((s) => s.kod === sekme))?.alt.map((s) => (
                <button key={s.kod} role="tab" aria-selected={sekme === s.kod} className={sekme === s.kod ? 'aktif' : ''} onClick={() => sekmeyeGit(s.kod)}>{s.ad}</button>
              ))}
            </div>
            {sekme === 'ozet' && <OzetSekmesi plan={plan} gelisim={gelisim} sekmeyeGit={sekmeyeGit} />}
            {sekme === 'yol' && <YolHaritasiSekmesi plan={plan} gelisim={gelisim} hedefId={hedef.bolum_id} onDurum={adimDurumu} kaynaklar={kaynaklar} sekmeyeGit={sekmeyeGit} onOlc={setOlcumAlani} />}
            {sekme === 'ilham' && <IlhamSekmesi kaynaklar={kaynaklar} />}
            {sekme === 'bolum' && <BolumunuTani hedef={hedef} />}
            {sekme === 'gun' && <BirGunumSekmesi hedef={hedef} />}
            {sekme === 'guclu' && <GucluSekmesi plan={plan} onDurum={adimDurumu} />}
            {sekme === 'karsilastirma' && <KarsilastirmaSekmesi gelisim={gelisim} hedef={hedef} />}
            {sekme === 'gelisim' && <GelisimSekmesi karsilastirma={karsilastirma} />}
            {olcumAlani && <OlcumPenceresi odak={olcumAlani} onKapat={() => setOlcumAlani(null)}
              onBitti={() => api.gelisimPlaniGetir().then(setPlan).catch(() => {})} />}
          </>
        )}
      </div>
    </div>
  )
}
