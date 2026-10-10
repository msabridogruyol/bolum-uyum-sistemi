// [2026-10-10] İş Hayatı → 'gercek' sekmesi: Beklenti ve Gerçek.
// Öğrenci önce tahminini girer (yalnızca resmî verisi olan göstergeler sorulur), sonra gerçek veriyle yan yana görür.
// Uydurma sayı yok: veri yoksa "veri yok"; "çoğu öğrenci …" cümlesi yalnızca en az 5 öğrencinin gerçek tahmini varsa kurulur.
// Uçlar: GET/POST /ogrenci/is-hayati/gercek/{bolum_id} (backend/app/api/is_hayati_gercek.py)
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import { tl, TahminEtiketi } from './ortak'

const SAYI = (v, k = 1) => Number(v).toLocaleString('tr-TR', { maximumFractionDigits: k })

// Gösterge tanımları: kaydırıcı aralığı ve gerçekle fark yorumları (yargılamayan, umut veren dil)
const TANIM = {
  istihdam_orani: {
    soru: 'Mezunların yüzde kaçı kayıtlı (sigortalı) bir işte çalışıyor?', birim: '%', min: 0, max: 100, adim: 1,
    yakin: 5,
    yuksek: 'Gerçek oran tahmininden düşük: mezunların bir kısmı ilk yıllarda kayıtlı bir işte değil. Staj, yabancı dil ve gerçek proje deneyimi seni bu oranın iyi tarafına taşıyan şeyler.',
    dusuk: 'İyi haber: mezunların tahmin ettiğinden daha büyük bir kısmı kayıtlı çalışıyor.',
  },
  is_bulma_suresi_ay: {
    soru: 'Mezunlar ilk işlerini ortalama kaç ayda buluyor?', birim: 'ay', min: 0, max: 36, adim: 1,
    yakin: 1.5,
    yuksek: 'İş bulma süresi tahmin ettiğinden kısa. Yine de son sınıfta başvurmaya başlamak bu süreyi daha da kısaltır.',
    dusuk: 'İş aramak tahmin ettiğinden uzun sürebiliyor. Son sınıfta başvurmaya başlamak, staj yaptığın yerle bağı korumak ve bu süre için küçük bir birikim planlamak işini kolaylaştırır.',
  },
  alan_uyum_orani: {
    soru: 'Çalışan mezunların yüzde kaçı kendi alanında çalışıyor?', birim: '%', min: 0, max: 100, adim: 1,
    yakin: 5,
    yuksek: 'Mezunların bir bölümü başka alanlarda çalışıyor. Bu bir başarısızlık sayılmaz: bölümde kazandığın beceriler başka işlere de taşınır. Alanında çalışmak istiyorsan stajını alanında yapmak en güçlü adım.',
    dusuk: 'Mezunların tahmin ettiğinden daha büyük bir kısmı kendi alanında çalışıyor.',
  },
}

function Cubuk({ etiket, deger, maks, renk, metin, soluk }) {
  const oran = deger == null || !maks ? 0 : Math.max(2, Math.min(100, (deger / maks) * 100))
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(84px, 110px) 1fr', gap: 8, alignItems: 'center', margin: '4px 0' }}>
      <div style={{ fontSize: 12, color: 'var(--tx2)', fontWeight: 600 }}>{etiket}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
        <div style={{ flex: 1, height: 14, background: 'var(--sur2)', borderRadius: 7, overflow: 'hidden' }}>
          <div style={{ width: `${oran}%`, height: '100%', background: renk, opacity: soluk ? 0.55 : 1, borderRadius: 7, transition: 'width .4s' }} />
        </div>
        <div style={{ fontSize: 13, fontWeight: 800, minWidth: 64, textAlign: 'right', whiteSpace: 'nowrap' }}>{metin}</div>
      </div>
    </div>
  )
}

function Kaynak({ g }) {
  if (!g?.kaynak) return null
  return <div className="yp-ince" style={{ marginTop: 6 }}>Kaynak: {g.kaynak}{g.yil ? ` · veri yılı ${g.yil}` : ''}{g.program ? ` · ${g.program}` : ''}</div>
}

function GirisSatiri({ tanim, deger, onDeger }) {
  const secili = deger !== '' && deger != null
  return (
    <div style={{ padding: '12px 0', borderBottom: '1px solid var(--bor)' }}>
      <label style={{ fontSize: 13.5, fontWeight: 700, display: 'block', marginBottom: 8 }}>{tanim.soru}</label>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <input type="range" min={tanim.min} max={tanim.max} step={tanim.adim} aria-label={tanim.soru}
          value={secili ? deger : (tanim.min + tanim.max) / 2} onChange={(e) => onDeger(Number(e.target.value))}
          style={{ flex: '1 1 180px', accentColor: 'var(--okul-c)', opacity: secili ? 1 : 0.45 }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <input className="yp-sec" type="number" inputMode="decimal" min={tanim.min} max={tanim.max} step={tanim.adim} value={secili ? deger : ''}
            placeholder="?" onChange={(e) => onDeger(e.target.value === '' ? '' : Math.max(tanim.min, Math.min(tanim.max, Number(e.target.value))))}
            style={{ width: 72 }} aria-label={`${tanim.soru} (sayı)`} />
          <span style={{ fontSize: 12.5, color: 'var(--tx2)' }}>{tanim.birim}</span>
        </div>
      </div>
      {!secili && <div className="yp-ince" style={{ marginTop: 4 }}>Kaydırıcıyı oynat ya da bir sayı yaz. Bilmiyorsan boş bırakabilirsin.</div>}
    </div>
  )
}

function yorumla(kod, tahmin, gercek, topluluk) {
  const t = TANIM[kod]
  const fark = tahmin - gercek
  const toplulukCumlesi = topluluk
    ? (topluluk.ortanca > gercek + t.yakin
      ? ` Bu bölüm için tahmin yapan ${topluluk.n} öğrencinin çoğu da bu değeri gerçekte olduğundan yüksek tahmin etti (ortanca ${SAYI(topluluk.ortanca)} ${t.birim}).`
      : topluluk.ortanca < gercek - t.yakin
        ? ` Bu bölüm için tahmin yapan ${topluluk.n} öğrencinin çoğu bu değeri gerçekte olduğundan düşük tahmin etti (ortanca ${SAYI(topluluk.ortanca)} ${t.birim}).`
        : ` Bu bölüm için tahmin yapan ${topluluk.n} öğrencinin ortancası (${SAYI(topluluk.ortanca)} ${t.birim}) gerçeğe yakın.`)
    : ''
  if (Math.abs(fark) <= t.yakin) return { ton: 'iyi', metin: `Gerçeğe çok yakın tahmin etmişsin.${toplulukCumlesi}` }
  return { ton: 'bilgi', metin: (fark > 0 ? t.yuksek : t.dusuk) + toplulukCumlesi }
}

function GostergeSonuc({ g, tahmin, topluluk }) {
  const t = TANIM[g.kod]
  const maks = t.birim === '%' ? 100 : Math.max(tahmin ?? 0, g.deger ?? 0, 6) * 1.15
  const y = tahmin != null && g.deger != null ? yorumla(g.kod, tahmin, g.deger, topluluk) : null
  return (
    <div className="card" style={{ padding: '14px 16px' }}>
      <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 6 }}>{g.ad}</div>
      {g.veri_yok ? (
        <div style={{ fontSize: 12.5, color: 'var(--tx2)' }}>📭 Bu gösterge için resmî veri yok. Yüklendiğinde burada karşılaştırma görünecek.</div>
      ) : (
        <>
          {tahmin != null
            ? <Cubuk etiket="Senin tahminin" deger={tahmin} maks={maks} renk="var(--tx3)" soluk metin={`${SAYI(tahmin)} ${t.birim}`} />
            : <div className="yp-ince" style={{ margin: '4px 0' }}>Bu soruyu boş bıraktın.</div>}
          <Cubuk etiket="Gerçek" deger={g.deger} maks={maks} renk="var(--okul-c)" metin={`${SAYI(g.deger)} ${t.birim}`} />
          {y && <div style={{ marginTop: 8, fontSize: 12.5, lineHeight: 1.55, color: 'var(--tx2)', background: y.ton === 'iyi' ? 'var(--grl)' : 'var(--sur2)', padding: '8px 10px', borderRadius: 10 }}>{y.metin}</div>}
          <Kaynak g={g} />
        </>
      )}
    </div>
  )
}

function MaasSonuc({ k, tahmin, asgari }) {
  const katT = tahmin != null && asgari?.net ? tahmin / asgari.net : null
  return (
    <div className="card" style={{ padding: '14px 16px' }}>
      <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 6 }}>İlk net maaş</div>
      {tahmin != null
        ? <div style={{ fontSize: 13, marginBottom: 6 }}>Senin tahminin: <b>{tl(tahmin)}</b>{katT != null && <> · güncel net asgari ücretin (<b>{tl(asgari.net)}</b>, {asgari.donem}) <b>{SAYI(katT, 2)} katı</b></>}</div>
        : <div className="yp-ince">Bu soruyu boş bıraktın.</div>}

      {k.deger != null && (
        <>
          {k.asgari_kat != null && katT != null ? (
            <>
              <div className="yp-ince" style={{ margin: '6px 0 2px' }}>Farklı yılların TL'si doğrudan karşılaştırılamaz; bu yüzden ikisini de <b>asgari ücretin katı</b> olarak gösteriyoruz.</div>
              <Cubuk etiket="Senin tahminin" deger={katT} maks={Math.max(katT, k.asgari_kat, 1) * 1.15} renk="var(--tx3)" soluk metin={`${SAYI(katT, 2)}×`} />
              <Cubuk etiket="Gerçek" deger={k.asgari_kat} maks={Math.max(katT, k.asgari_kat, 1) * 1.15} renk="var(--okul-c)" metin={`${SAYI(k.asgari_kat, 2)}×`} />
            </>
          ) : null}
          <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 6 }}>
            Resmî veri: mezunların kazancı <b>{tl(k.deger)}</b> ({k.yil} yılı TL'si)
            {k.yil_asgari && <> · o yıl net asgari ücret ortalaması {tl(k.yil_asgari.net_ortalama)}</>}.
            {k.asgari_kat == null && ' O yılın asgari ücreti tabloda olmadığı için oran hesaplanamadı.'}
          </div>
        </>
      )}

      {k.deger == null && k.kazanc_grubu_ad && (
        <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 6, lineHeight: 1.55 }}>
          Resmî veri bu bölüm için TL vermiyor; mezunların kazancını diğer programlara göre <b>“{k.kazanc_grubu_ad}”</b> grubunda gösteriyor.
          {katT != null && <> Senin tahminin asgari ücretin {SAYI(katT, 2)} katı; bunu grubun düzeyiyle karşılaştırırken ilk maaşların genellikle ortalamanın altında olduğunu unutma.</>}
        </div>
      )}

      {k.meslek_tahmini && (
        <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 8, lineHeight: 1.55 }}>
          Bu bölümün mesleklerinde <b>ortalama</b> (ilk maaş değil) net kazanç: <b>{tl(k.meslek_tahmini.min)}{k.meslek_tahmini.max !== k.meslek_tahmini.min ? ` – ${tl(k.meslek_tahmini.max)}` : ''}</b>
          <TahminEtiketi /> <span className="yp-ince">({k.meslek_tahmini.meslek_sayisi} meslek · TÜİK {k.meslek_tahmini.veri_yili} · {k.meslek_tahmini.donem} asgari ücretiyle güncellendi)</span>
        </div>
      )}
      {k.veri_yok && <div style={{ fontSize: 12.5, color: 'var(--tx2)' }}>📭 Bu bölüm için kazanç verisi yok.</div>}
      <div style={{ marginTop: 8, fontSize: 12.5, lineHeight: 1.55, color: 'var(--tx2)', background: 'var(--sur2)', padding: '8px 10px', borderRadius: 10 }}>
        İlk maaş şehir, şirket ve deneyime göre çok değişir; çoğu meslekte ilk yıllardaki artış en hızlı dönemdir. “İlk Maaşla Bir Ay” sekmesinde bu maaşın neye yettiğini hesaplayabilirsin.
      </div>
      <Kaynak g={k} />
    </div>
  )
}

function NeOgrendin({ denemeler }) {
  if (denemeler.length < 2) return null
  const [son, onceki] = denemeler
  const satirlar = Object.keys(TANIM).map((kod) => {
    const g = son.gercek?.gostergeler?.[kod]
    const a = onceki.tahminler?.[kod], b = son.tahminler?.[kod]
    if (g == null || a == null || b == null) return null
    const once = Math.abs(a - g), simdi = Math.abs(b - g)
    const fark = once - simdi
    return { kod, metin: Math.abs(fark) < 0.5 ? 'aynı uzaklıkta' : fark > 0 ? `${SAYI(fark)} ${TANIM[kod].birim} daha yakın` : `${SAYI(-fark)} ${TANIM[kod].birim} daha uzak`, iyi: fark > 0 }
  }).filter(Boolean)
  if (!satirlar.length) return null
  return (
    <div className="card" style={{ padding: '14px 16px', borderLeft: '4px solid var(--okul-c)' }}>
      <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 6 }}>🧠 Ne öğrendin?</div>
      <div className="yp-ince" style={{ marginBottom: 6 }}>Bir önceki denemene göre gerçeğe uzaklığın:</div>
      {satirlar.map((s) => (
        <div key={s.kod} style={{ fontSize: 13, margin: '3px 0' }}>{s.iyi ? '✅' : '•'} {TANIM[s.kod].soru.replace('?', '')}: <b>{s.metin}</b></div>
      ))}
    </div>
  )
}

export default function BeklentiGercek({ bolum }) {
  const [g, setG] = useState(null)
  const [hata, setHata] = useState(null)
  const [mod, setMod] = useState('giris')
  const [form, setForm] = useState({})
  const [gonderiliyor, setGonderiliyor] = useState(false)

  useEffect(() => {
    api.isHayatiGercek(bolum.id).then((v) => { setG(v); if (v.denemeler?.length) setMod('sonuc') })
      .catch((e) => setHata(e.detail || 'Veriler yüklenemedi.'))
  }, [bolum.id])

  const sorulacak = useMemo(() => (g ? g.gostergeler.filter((x) => !x.veri_yok) : []), [g])
  const maasSor = g && !g.kazanc.veri_yok

  async function gonder() {
    const tahminler = Object.fromEntries(Object.entries(form).filter(([, v]) => v !== '' && v != null && !Number.isNaN(Number(v))).map(([k, v]) => [k, Number(v)]))
    if (!Object.keys(tahminler).length) { setHata('En az bir soruyu yanıtla.'); return }
    setGonderiliyor(true); setHata(null)
    try { const v = await api.isHayatiGercekKaydet(bolum.id, tahminler); setG(v); setMod('sonuc') } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setGonderiliyor(false) }
  }

  if (hata && !g) return <div className="auth-error">{hata}</div>
  if (!g) return <div className="bos-durum">Yükleniyor…</div>

  if (!sorulacak.length && !maasSor) {
    return (
      <div className="card" style={{ padding: '18px 20px' }}>
        <div style={{ fontWeight: 800, fontSize: 15, marginBottom: 6 }}>📭 {bolum.ad} için henüz karşılaştırılacak resmî veri yok</div>
        <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.6 }}>
          Tahmin oyununu oynayabilmek için TÜİK istihdam göstergelerinin bu bölüme yüklenmesi gerekiyor. Bu sırada şunları yapabilirsin:
          <ul style={{ margin: '6px 0 0', paddingLeft: 18 }}>
            <li>“Mesleğe Giden Yol” sekmesinde bu bölümden mesleğe nasıl gidildiğine bak.</li>
            <li>Rehber öğretmeninle, bu bölümden mezun tanıdıklarınla ilk iş ve maaş beklentilerini konuş.</li>
            <li>Benzer bir bölümü seçip verisi olan bir bölümde tahminlerini dene.</li>
          </ul>
        </div>
      </div>
    )
  }

  const son = g.denemeler?.[0]

  if (mod === 'giris') {
    return (
      <div className="card" style={{ padding: '16px 18px' }}>
        <div style={{ fontWeight: 800, fontSize: 15 }}>🔍 Önce sen tahmin et</div>
        <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 4, lineHeight: 1.55 }}>
          {bolum.ad} mezunları için aklındaki rakamları gir; sonra resmî verilerle yan yana göreceğiz. Doğru ya da yanlış cevap yok —
          amaç beklentini fark etmek. {son && 'Önceki tahminin aşağıdaki sonuçlarda duruyor; tekrar denediğinde ne kadar yaklaştığını göreceksin.'}
        </div>
        {sorulacak.map((x) => (
          <GirisSatiri key={x.kod} tanim={TANIM[x.kod]} deger={form[x.kod] ?? ''} onDeger={(v) => setForm((f) => ({ ...f, [x.kod]: v }))} />
        ))}
        {maasSor && (
          <div style={{ padding: '12px 0' }}>
            <label style={{ fontSize: 13.5, fontWeight: 700, display: 'block', marginBottom: 8 }} htmlFor="ihg-maas">Mezun olup ilk işe girdiğinde eline geçecek aylık net maaş kaç TL olur?</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
              <input id="ihg-maas" className="yp-sec" type="number" inputMode="numeric" min={0} step={500} placeholder="ör. bugünkü TL ile"
                value={form.ilk_net_maas ?? ''} onChange={(e) => setForm((f) => ({ ...f, ilk_net_maas: e.target.value === '' ? '' : Math.max(0, Number(e.target.value)) }))}
                style={{ width: 170 }} />
              <span style={{ fontSize: 12.5, color: 'var(--tx2)' }}>TL / ay</span>
              {g.asgari && form.ilk_net_maas > 0 && <span className="yp-ince">= net asgari ücretin {SAYI(form.ilk_net_maas / g.asgari.net, 2)} katı</span>}
            </div>
            {g.asgari && <div className="yp-ince" style={{ marginTop: 4 }}>Bugünkü TL ile düşün. Karşılaştırma için: {g.asgari.donem} net asgari ücret {tl(g.asgari.net)}.</div>}
          </div>
        )}
        {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}
        <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
          <button className="btn" onClick={gonder} disabled={gonderiliyor} style={{ background: 'var(--okul-c)' }}>{gonderiliyor ? 'Kaydediliyor…' : 'Gerçekle karşılaştır →'}</button>
          {son && <button className="btn sec" onClick={() => setMod('sonuc')}>Son sonucuma dön</button>}
        </div>
      </div>
    )
  }

  const tahmin = son?.tahminler || {}
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
        <div style={{ fontWeight: 800, fontSize: 15 }}>Tahminin ve gerçek</div>
        {son && <span className="yp-ince">{new Date(son.zaman).toLocaleDateString('tr-TR')} · {g.denemeler.length}. deneme</span>}
        <button className="btn sec" style={{ marginLeft: 'auto', padding: '7px 14px', fontSize: 13 }} onClick={() => { setForm({}); setMod('giris') }}>↻ Tekrar dene</button>
      </div>
      <NeOgrendin denemeler={g.denemeler} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: 12 }}>
        {g.gostergeler.filter((x) => !x.veri_yok || tahmin[x.kod] != null).map((x) => (
          <GostergeSonuc key={x.kod} g={x} tahmin={tahmin[x.kod] ?? null} topluluk={g.topluluk?.[x.kod]} />
        ))}
        {(maasSor || tahmin.ilk_net_maas != null) && <MaasSonuc k={g.kazanc} tahmin={tahmin.ilk_net_maas ?? null} asgari={g.asgari} />}
      </div>
      <div className="yp-ince" style={{ marginTop: 6, lineHeight: 1.55 }}>
        Bu rakamlar bir bölümün tüm mezunlarının ortalamasıdır; senin yolunu belirlemez. Staj, yabancı dil, proje ve ilk işi aramaya erken
        başlamak ortalamanın üstüne çıkmanın en bilinen yollarıdır.
      </div>
    </div>
  )
}
