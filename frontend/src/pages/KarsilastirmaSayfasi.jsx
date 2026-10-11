// [2026-10-11] Bölüm karşılaştırma — /karsilastir (ve Bölümler → Karşılaştır sekmesi, gomulu).
// 2–3 bölüm yan yana; seçim URL'de (?b=1,2,3 — eski ?ids= de okunur). URL boşsa önce karşılaştırma sepeti,
// o da boşsa hedef bölüm + ilk 2 öneri. Tüm veriler tek istekte: GET /ogrenci/karsilastir (app/api/karsilastir.py).
// YÖK Atlas önbelleği olmayan bölümler için /bolumler/{id}/universiteler ayrıca çekilir (sayfayı bekletmez).
// Satır bazında en iyi değer vurgulanır; veri olmayan hücrede "—" ve kısa açıklama (uydurma yok).
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import FavoriYildiz, { useListem } from '../components/FavoriYildiz'
import { useBolumBilgi } from '../context/BolumBilgiContext'
import { sepetAyarla, useSepet, SEPET_SINIRI } from '../components/KarsilastirSepeti'
import { simulasyonAc } from '../components/MeslekSimulasyonu'

const liste = (v) => (Array.isArray(v) ? v : [])
const sayi = (v, k = 0) => (v == null ? '—' : Number(v).toLocaleString('tr-TR', { maximumFractionDigits: k }))
const idOku = (p) => (p.get('b') || p.get('ids') || '').split(',').map(Number).filter((x) => Number.isInteger(x) && x > 0)
  .filter((x, i, a) => a.indexOf(x) === i).slice(0, SEPET_SINIRI)

function uniOzeti(u) {   // /bolumler/{id}/universiteler → backend'in önbellek özetiyle aynı biçim
  if (!u) return null
  const p = liste(u.programlar)
  if (!p.length) return { durum: u.durum || 'veri_yok', mesaj: u.mesaj }
  const puan = p.map((x) => x.taban_puan).filter((x) => x != null)
  const sira = p.map((x) => x.basari_sirasi).filter((x) => x != null)
  return {
    durum: 'tamam', yil: u.yil, program: p.length, devlet: p.filter((x) => String(x.universite_turu || '').toUpperCase().startsWith('DEV')).length,
    puan_min: puan.length ? Math.min(...puan) : null, puan_max: puan.length ? Math.max(...puan) : null,
    sira_en: sira.length ? Math.min(...sira) : null, sira_son: sira.length ? Math.max(...sira) : null,
  }
}

const Yok = ({ neden }) => <span className="ks-yok">—{neden && <small>{neden}</small>}</span>

function Secici({ secili, setSecili, adlar }) {
  const fav = useListem()
  const [acik, setAcik] = useState(secili.length < 2)
  const [oneri, setOneri] = useState([])
  const [q, setQ] = useState('')
  const [sonuc, setSonuc] = useState(null)
  useEffect(() => { api.siralamaGetir(10).then((l) => setOneri(liste(l))).catch(() => setOneri([])) }, [])
  const [elle, setElle] = useState(false)   // kullanıcı seçiciyi kendisi açtıysa otomatik kapatma
  useEffect(() => {
    if (secili.length < 2) setAcik(true)
    else if (!elle) setAcik(false)
  }, [secili.length]) // eslint-disable-line react-hooks/exhaustive-deps

  const ekle = (b) => setSecili((s) => (s.some((x) => x.id === b.bolum_id) || s.length >= SEPET_SINIRI ? s : [...s, { id: b.bolum_id, ad: b.bolum_adi }]))
  const cip = (b) => {
    const var_ = secili.some((x) => x.id === b.bolum_id)
    return (
      <button key={b.bolum_id} type="button" className={`kr-cip${var_ ? ' secili' : ''}`} disabled={!var_ && secili.length >= SEPET_SINIRI}
        onClick={() => (var_ ? setSecili((s) => s.filter((x) => x.id !== b.bolum_id)) : ekle(b))}>
        {var_ ? '✓ ' : '+ '}{b.bolum_adi}{b.toplam_uyum != null && <span>%{Math.round(b.toplam_uyum)}</span>}
      </button>
    )
  }
  async function ara(e) {
    e.preventDefault()
    if (q.trim().length < 2) return
    try { setSonuc(liste(await api.kesfetAra(q.trim(), 10))) } catch { setSonuc([]) }
  }
  return (
    <div className="card kr-secici">
      <div className="kr-secili">
        {[0, 1, 2].map((i) => (
          <div key={i} className={`kr-yuva${secili[i] ? ' dolu' : ''}`}>
            {secili[i] ? (
              <>
                <span>{secili[i].ad || adlar[secili[i].id] || '…'}</span>
                <button type="button" aria-label="Çıkar" onClick={() => setSecili((s) => s.filter((_, j) => j !== i))}>×</button>
              </>
            ) : <span className="yp-ince">{i < 2 ? `${i + 1}. bölümü seç` : '3. bölüm (isteğe bağlı)'}</span>}
          </div>
        ))}
      </div>
      {!acik ? (
        <button type="button" className="hg-link" onClick={() => { setElle(true); setAcik(true) }}>{secili.length < SEPET_SINIRI ? '+ Bölüm ekle / değiştir' : 'Seçimi değiştir'}</button>
      ) : (<>
        {oneri.length > 0 && (<><div className="kr-baslik">🌟 Sana en uygun</div><div className="kr-cipler">{oneri.map(cip)}</div></>)}
        {fav?.length > 0 && (<><div className="kr-baslik">⭐ Listemden</div><div className="kr-cipler">{fav.map(cip)}</div></>)}
        <form onSubmit={ara} className="ks-ara">
          <input className="auth-input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tüm bölümlerde ara… (örn. Psikoloji)" aria-label="Bölüm ara" />
          <button className="btn sec" type="submit">Ara</button>
        </form>
        {sonuc && <div className="kr-cipler" style={{ marginTop: 10 }}>{sonuc.length ? sonuc.map(cip) : <span className="yp-ince">Sonuç yok.</span>}</div>}
        {secili.length >= 2 && <button type="button" className="hg-link" style={{ marginTop: 10 }} onClick={() => setAcik(false)}>Seçimi kapat ↑</button>}
      </>)}
    </div>
  )
}

export default function KarsilastirmaSayfasi({ gomulu = false }) {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const { ac } = useBolumBilgi()
  const sepet = useSepet()
  const [veri, setVeri] = useState(null)
  const [uni, setUni] = useState({})
  const [hata, setHata] = useState(null)
  const [pdf, setPdf] = useState(false)
  const [adlar, setAdlar] = useState(() => Object.fromEntries(sepet.map((x) => [x.id, x.ad])))

  const idler = useMemo(() => idOku(params), [params])
  const anahtar = idler.join(',')
  const secili = idler.map((id) => ({ id, ad: adlar[id] || veri?.bolumler.find((b) => b.bolum_id === id)?.bolum_adi }))

  const setSecili = (f) => {
    const yeni = typeof f === 'function' ? f(secili) : f
    setAdlar((m) => ({ ...m, ...Object.fromEntries(yeni.filter((x) => x.ad).map((x) => [x.id, x.ad])) }))
    const p = new URLSearchParams(params)
    p.delete('ids'); p.delete('b')
    const diger = p.toString()
    const b = yeni.length ? `b=${yeni.map((x) => x.id).join(',')}` : ''   // virgüller kodlanmasın: ?b=1,2,3
    navigate({ search: [b, diger].filter(Boolean).join('&') }, { replace: true })
  }

  // URL boşsa: sepet → yoksa hedef + ilk 2 öneri
  useEffect(() => {
    if (idler.length) return
    if (sepet.length) { setSecili(sepet); return }
    let iptal = false
    api.karsilastirVarsayilan().then((d) => {
      const l = liste(d?.bolumler).map((b) => ({ id: b.bolum_id, ad: b.bolum_adi }))
      if (!iptal && l.length) setSecili(l)
    }).catch(() => {})
    return () => { iptal = true }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setHata(null)
    const l = anahtar ? anahtar.split(',').map(Number) : []
    if (l.length < 2) { setVeri(null); return }
    let iptal = false
    setVeri(null)
    api.bolumKarsilastir(l).then((d) => {
      if (iptal) return
      setVeri(d)
      const ad = Object.fromEntries(d.bolumler.map((b) => [b.bolum_id, b.bolum_adi]))
      setAdlar((m) => ({ ...m, ...ad }))
      sepetAyarla(d.bolumler.map((b) => ({ id: b.bolum_id, ad: b.bolum_adi })))   // sepet = son karşılaştırma
      d.bolumler.filter((b) => b.yokatlas?.durum === 'onbellek_yok' && !uni[b.bolum_id]).forEach((b) => {
        api.bolumUniversiteleri(b.bolum_id).then((u) => !iptal && setUni((m) => ({ ...m, [b.bolum_id]: uniOzeti(u) })))
          .catch(() => !iptal && setUni((m) => ({ ...m, [b.bolum_id]: { durum: 'hata' } })))
      })
    }).catch((e) => { if (!iptal) setHata(e.detail || 'Karşılaştırma yapılamadı.') })
    return () => { iptal = true }
  }, [anahtar]) // eslint-disable-line react-hooks/exhaustive-deps

  const kol = veri ? idler.map((id) => veri.bolumler.find((b) => b.bolum_id === id)).filter(Boolean) : []
  const yok = (b) => (b.yokatlas?.durum === 'onbellek_yok' ? uni[b.bolum_id] : b.yokatlas)
  const ortusme = (b) => b.one_cikanlar.filter((x) => x.sende).length
  const simMax = (b) => (b.simulasyon?.length ? Math.max(...b.simulasyon.map((s) => s.keyif)) : null)

  // satır bazında en iyi: yön 1 → en yüksek, -1 → en düşük; yalnızca en az 2 değer varsa ve hepsi eşit değilse
  const enIyi = (f, yon = 1) => {
    const d = kol.map(f).filter((x) => x != null)
    if (d.length < 2 || d.every((x) => x === d[0])) return null
    return yon > 0 ? Math.max(...d) : Math.min(...d)
  }
  const vurgu = (deger, en) => (en != null && deger === en ? ' ks-en' : '')

  const ist = (b, k) => b.istihdam?.[k] ?? null
  const satirlar = []
  const satir = (anah, etiket, hucre, ipucu) => satirlar.push({ anah, etiket, hucre, ipucu })

  if (kol.length >= 2) {
    const uyEn = enIyi((b) => b.toplam_uyum)
    satir('uyum', 'Uyumun', (b) => (b.toplam_uyum == null
      ? <Yok neden={veri.sonuc_var ? 'Hesaplanmadı' : 'Değerlendirmeni bitirince görünür'} />
      : (
        <div className={`kr-uyum${vurgu(b.toplam_uyum, uyEn)}`}>
          <b>%{Math.round(b.toplam_uyum)}</b>
          <div className="mini-ilerleme-track"><div className="mini-ilerleme-fill" style={{ width: `${b.toplam_uyum}%`, background: 'var(--okul-c)' }} /></div>
          {b.sira && <small className="yp-ince">{b.sira}. sırada · {veri.toplam_bolum} bölüm içinde</small>}
        </div>
      )), 'nihai uyum ve öneri sıran')
    if (veri.sonuc_var) {
      satir('neden', 'Neden bu bölüm', (b) => (b.neden.length || b.dikkat ? (
        <ul className="kr-liste duz">
          {b.neden.map((x) => <li key={x}>{x}</li>)}
          {b.dikkat && <li className="ks-dikkat">⚠️ {b.dikkat}</li>}
        </ul>
      ) : <Yok neden="Açıklama üretilemedi" />))
    }
    const ortEn = enIyi(ortusme)
    satir('guclu', 'Güçlü yönlerinle örtüşen', (b) => (
      <div className={vurgu(ortusme(b), ortEn) ? 'ks-en-kutu' : ''}>
        {veri.profil_var && <div className="ks-mini">{ortusme(b)}/{b.one_cikanlar.length} özellik sende de güçlü</div>}
        <ul className="kr-liste">
          {b.one_cikanlar.map((x) => (
            <li key={x.kod} className={x.sende ? 'sende' : ''} title={x.sende ? 'Bu özellik sende de güçlü' : ''}><span>{x.sende ? '✓' : '·'}</span>{x.etiket}</li>
          ))}
          {!b.one_cikanlar.length && <li><Yok neden="Bu bölümün yetkinlik profili yok" /></li>}
        </ul>
      </div>
    ), veri.profil_var ? '✓ sende de güçlü' : 'bölümde öne çıkanlar')
    satir('alan', 'Alan', (b) => b.alt_alan || b.ust_alan || <Yok />)
    satir('puan', 'Puan türü', (b) => b.puan_turu || <Yok neden="Bilgi yok" />)
    satir('sure', 'Öğrenim süresi', (b) => b.ogrenim_suresi || <Yok neden="Bilgi yok" />)
    satir('taban', 'Taban puan', (b) => {
      const o = yok(b)
      if (!o) return <span className="spin" />
      if (o.puan_min == null) return <Yok neden={o.mesaj || 'YÖK Atlas verisi yok'} />
      return <>{sayi(o.puan_min, 2)} – {sayi(o.puan_max, 2)}{o.yil && <small className="yp-ince"> · {o.yil}</small>}</>
    }, 'YÖK Atlas · en düşük – en yüksek')
    const uniVar = kol.some((b) => yok(b)?.durum === 'tamam' || !yok(b))
    if (uniVar) satir('sira', 'Başarı sırası', (b) => {
      const o = yok(b)
      if (!o) return <span className="spin" />
      if (o.sira_en == null) return <Yok />
      return <>{sayi(o.sira_en)} – {sayi(o.sira_son)}</>
    }, 'en iyi – en son yerleşen')
    if (uniVar) satir('program', 'Program sayısı', (b) => {
      const o = yok(b)
      if (!o) return <span className="spin" />
      return o.program ? <>{o.program} program{o.devlet ? <span className="yp-ince"> · {o.devlet} devlet</span> : null}</> : <Yok />
    })
    if (veri.moduller?.is_hayati) {
      const iEn = enIyi((b) => ist(b, 'istihdam_orani'))
      const sEn = enIyi((b) => ist(b, 'is_bulma_suresi_ay'), -1)
      const aEn = enIyi((b) => ist(b, 'alan_uyum_orani'))
      const istYok = <Yok neden="Bu bölüm için istihdam verisi henüz yok" />
      satir('istihdam', 'Mezun istihdamı', (b) => (ist(b, 'istihdam_orani') == null ? istYok : (
        <span className={vurgu(ist(b, 'istihdam_orani'), iEn)}><b>%{sayi(ist(b, 'istihdam_orani'))}</b>
          <small className="yp-ince"> · {[b.istihdam.kaynak, b.istihdam.veri_yili].filter(Boolean).join(' ')}</small></span>
      )), 'İş Hayatı · mezunların çalışma oranı')
      const istVar = kol.some((b) => b.istihdam)   // hiçbir bölümde veri yoksa yalnızca ilk satır (açıklamalı)
      if (istVar) satir('isbulma', 'İş bulma süresi', (b) => (ist(b, 'is_bulma_suresi_ay') == null ? <Yok /> : (
        <span className={vurgu(ist(b, 'is_bulma_suresi_ay'), sEn)}><b>{sayi(ist(b, 'is_bulma_suresi_ay'), 1)} ay</b></span>
      )), 'ortalama; kısa olan vurgulanır')
      if (istVar) satir('alanuyum', 'Alanında çalışan', (b) => (ist(b, 'alan_uyum_orani') == null ? <Yok /> : (
        <span className={vurgu(ist(b, 'alan_uyum_orani'), aEn)}><b>%{sayi(ist(b, 'alan_uyum_orani'))}</b></span>
      )))
      if (istVar) satir('kazanc', 'Kazanç grubu', (b) => ist(b, 'kazanc_grubu_ad') || <Yok />, 'TÜİK gruplaması')
      satir('yol', 'Mesleğe giden yol', (b) => (b.yol ? (
        <>
          <ol className="ks-yol">{b.yol.adimlar.map((x) => <li key={x}>{x}</li>)}</ol>
          {(b.yol.regule || b.yol.oda_kaydi) && <div className="ks-mini">{b.yol.regule ? 'Düzenlenmiş meslek' : ''}{b.yol.regule && b.yol.oda_kaydi ? ' · ' : ''}{b.yol.oda_kaydi ? 'Oda kaydı gerekebilir' : ''}</div>}
          {b.yol.ozel && <small className="yp-ince">{b.yol.ozel}</small>}
        </>
      ) : <Yok neden="Yol bilgisi yok" />), 'zorunlu adımlar')
    }
    satir('meslek', 'Meslekler', (b) => (b.meslekler.length ? <ul className="kr-liste duz">{b.meslekler.slice(0, 5).map((x) => <li key={x}>{x}</li>)}</ul> : <Yok neden="Bilgi yok" />))
    satir('gunluk', 'Günlük işler ve ortam', (b) => (b.gunluk.length ? (
      <div className="ks-gunluk">{b.gunluk.map((g) => (
        <div key={g.meslek}>
          <b>{g.meslek}</b>
          {liste(g.isler).length > 0 && <ul className="kr-liste duz">{g.isler.map((x) => <li key={x}>{x}</li>)}</ul>}
          {g.ortam && <small>📍 {g.ortam}</small>}
        </div>
      ))}</div>
    ) : <Yok neden="Bilgi yok" />), 'ilk iki meslekten')
    satir('beceri', 'Gerekli beceriler', (b) => (b.beceriler.length ? <div className="ks-etiketler">{b.beceriler.map((x) => <span key={x}>{x}</span>)}</div> : <Yok neden="Bilgi yok" />))
    if (veri.moduller?.simulasyon) {
      const smEn = enIyi(simMax)
      satir('sim', 'Simülasyon keyfin', (b) => (b.simulasyon?.length ? (
        <ul className="kr-liste duz">{b.simulasyon.slice(0, 3).map((s) => (
          <li key={s.meslek} className={vurgu(s.keyif, smEn)}>{s.meslek}: <b>%{s.keyif}</b></li>
        ))}</ul>
      ) : (
        <span className="ks-yok">—<small>Henüz denemedin</small>
          <button type="button" className="hg-link" onClick={() => simulasyonAc(b.bolum_id, 0, b.bolum_adi)}>🎬 Bir günümü yaşa</button></span>
      )), '“Bir günümü yaşa”')
    }
    satir('jargon', 'Meslek dilinden', (b) => (b.jargon.length ? (
      <ul className="kr-liste kr-jargon">{b.jargon.map((j) => (
        <li key={j.terim}><b>{j.terim}</b>{j.anlam && <small>{j.anlam.length > 90 ? j.anlam.slice(0, 88) + '…' : j.anlam}</small>}</li>
      ))}</ul>
    ) : <Yok />))
  }

  const uyEn = kol.length >= 2 ? enIyi((b) => b.toplam_uyum) : null
  const ortEn = kol.length >= 2 ? enIyi(ortusme) : null
  const govde = (
    <>
      <Secici secili={secili} setSecili={setSecili} adlar={adlar} />
      {hata && <div className="auth-error">{hata}</div>}
      {idler.length < 2 && !hata && (
        <div className="veri-yok-grafik"><div className="vg-ikon">⚖️</div><div className="vg-metin">Yan yana görmek için en az 2 bölüm seç. Bölüm kartlarındaki ⚖️ düğmesiyle de ekleyebilirsin.</div></div>
      )}
      {idler.length >= 2 && !veri && !hata && <div className="bos-durum">Karşılaştırılıyor…</div>}
      {kol.length >= 2 && (
        <>
          <div className="kr-ozet ks-ozet">
            {uyEn != null && <div>🎯 Uyumun en yüksek: <b>{kol.find((b) => b.toplam_uyum === uyEn)?.bolum_adi}</b> (%{Math.round(uyEn)})</div>}
            {veri.profil_var && ortEn != null && ortEn > 0 && <div>💪 Güçlü yönlerinle en çok örtüşen: <b>{kol.find((b) => ortusme(b) === ortEn)?.bolum_adi}</b></div>}
            <div className="yp-ince">Vurgulu hücreler o satırdaki en yüksek (iş bulma süresinde en kısa) değerdir. Karar verirken yalnızca yüzdeye değil, meslekler ve günlük işlere de bak; sonuçlar karar desteğidir.</div>
            <div className="ks-ozet-eylem">
              <button type="button" className="btn sec" disabled={pdf} onClick={async () => { setPdf(true); try { await api.bolumKarsilastirPdf(idler) } catch (e) { setHata(e.detail || 'PDF hazırlanamadı.') } finally { setPdf(false) } }}>
                {pdf ? <span className="spin" /> : '📄 PDF indir'}
              </button>
            </div>
          </div>

          <div className="kr-tablo-kap ks-tablo-kap">
            <div className="kr-tablo ks-tablo" style={{ '--kr-n': kol.length }}>
              <div className="kr-satir kr-bas">
                <div className="kr-etiket" />
                {kol.map((b) => (
                  <div key={b.bolum_id} className="kr-hucre">
                    <div className="kr-alan">{b.hedef ? '🎯 Hedefin' : (b.ust_alan || '')}</div>
                    <div className="kr-ad">{b.bolum_adi}</div>
                    <div className="kr-eylem">
                      <button type="button" className="hg-link" onClick={() => ac(b.bolum_id, b.bolum_adi)}>İncele</button>
                      <FavoriYildiz id={b.bolum_id} ad={b.bolum_adi} />
                    </div>
                  </div>
                ))}
              </div>
              {satirlar.map((s) => (
                <div key={s.anah} className="kr-satir">
                  <div className="kr-etiket">{s.etiket}{s.ipucu && <small>{s.ipucu}</small>}</div>
                  {kol.map((b) => <div key={b.bolum_id} className="kr-hucre">{s.hucre(b)}</div>)}
                </div>
              ))}
              <div className="kr-satir">
                <div className="kr-etiket" />
                {kol.map((b) => (
                  <div key={b.bolum_id} className="kr-hucre">
                    {b.hedef ? <span className="yp-ince">🎯 Şu anki hedefin</span> : (
                      <button type="button" className="btn sec" style={{ width: '100%', fontSize: 12.5 }} onClick={() => navigate(`/profil?hedef=${b.bolum_id}#hedef`)}>Hedefim yap</button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          {kol.length > 1 && <div className="yp-ince ks-kaydir">← Telefonda tabloyu yana kaydırabilirsin →</div>}
        </>
      )}
    </>
  )

  if (gomulu) return govde
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">⚖️ Bölüm karşılaştır</div>
        <div className="ps">Aklındaki 2–3 bölümü yan yana koy: uyumun, neden uygun olduğu, puan ve sıralama, iş hayatı, meslekler ve günlük işler.</div>
      </div>
      {govde}
    </div>
  )
}
