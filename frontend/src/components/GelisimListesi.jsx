import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api/client'

// [2026-11-05] Gelişim listesi — haftalık 3 görevin yerine (kullanıcı kararı: süre / hafta / seri yok).
// Hedef bölüm için geliştirilecek her alan bir başlık; altında yapılacak maddeler. Her madde: yapmadım / yapıyorum / yaptım
// ve öğrencinin girdiği tarihli "ne yaptım" kayıtları ("12 Kasım — şunu yaptım"). "Yaptım" için en az bir kayıt gerekir.
// Bölüm keşfi ve 3 soruluk öz değerlendirme isteğe bağlıdır. Değişince 'gelisim-guncellendi' olayı yayınlanır (Filiz maskotu).

const DURUM = [
  { kod: 'bekliyor', ad: 'Yapmadım' },
  { kod: 'devam_ediyor', ad: 'Yapıyorum' },
  { kod: 'tamamlandi', ad: 'Yaptım' },
]
const DURUM_IKON = { bekliyor: '○', devam_ediyor: '◐', tamamlandi: '✓' }

export function yayinla(v) {
  window.dispatchEvent(new CustomEvent('gelisim-guncellendi', { detail: v }))
}

const bugunISO = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
export const tarihMetni = (iso) => (iso ? new Date(`${iso.slice(0, 10)}T12:00:00`).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long', year: 'numeric' }) : '')

function Cubuk({ yuzde, renk = 'var(--okul-c)' }) {
  return (
    <div className="mini-ilerleme-track" style={{ width: '100%' }} role="progressbar" aria-valuenow={yuzde} aria-valuemin={0} aria-valuemax={100}>
      <div className="mini-ilerleme-fill" style={{ width: `${yuzde}%`, background: renk }} />
    </div>
  )
}

function KayitFormu({ madde, onKaydet, onVazgec, zorunluMetin }) {
  const [tarih, setTarih] = useState(bugunISO())
  const [metin, setMetin] = useState('')
  const [bekle, setBekle] = useState(false)
  const yeterli = metin.trim().length >= 10
  return (
    <div className="gl-form">
      <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 6 }}>{zorunluMetin || 'Ne yaptın? Tarihiyle yaz:'}</div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <label style={{ fontSize: 12 }}>
          <div className="yp-ince">Tarih</div>
          <input type="date" className="yp-sec" value={tarih} max={bugunISO()} onChange={(e) => setTarih(e.target.value)} aria-label="Yaptığın gün" />
        </label>
        <label style={{ flex: '1 1 260px', fontSize: 12 }}>
          <div className="yp-ince">Ne yaptın?</div>
          <textarea className="auth-input" rows={2} maxLength={1000} value={metin} onChange={(e) => setMetin(e.target.value)}
            placeholder={madde.olcut ? `ör. ${madde.olcut}` : 'ör. Bir otobiyografi okudum; yazarın en zorlandığı anı not ettim.'}
            style={{ width: '100%', resize: 'vertical', fontFamily: 'inherit', fontSize: 13 }} />
        </label>
      </div>
      <div style={{ display: 'flex', gap: 6, marginTop: 6, alignItems: 'center', flexWrap: 'wrap' }}>
        <button className="btn" disabled={!yeterli || bekle || !tarih} onClick={async () => { setBekle(true); const ok = await onKaydet(tarih, metin); setBekle(false); if (ok) setMetin('') }}>
          {bekle ? <span className="spin" /> : 'Kaydet'}
        </button>
        <button className="btn sec" disabled={bekle} onClick={onVazgec}>Vazgeç</button>
        {!yeterli && metin.length > 0 && <span className="yp-ince">En az bir cümle yaz.</span>}
      </div>
    </div>
  )
}

function Madde({ m, onIslem }) {
  const [form, setForm] = useState(null)   // null | 'kayit' | 'yaptim'
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(null)
  const kayitVar = (m.kayitlar || []).length > 0

  async function durum(kod) {
    if (kod === m.durum) return
    if (kod === 'tamamlandi' && !kayitVar) { setForm('yaptim'); return }
    setBekle(kod); setHata(null)
    const h = await onIslem(() => api.gelisimDurum(m.kod, kod))
    setBekle(null)
    if (h) setHata(h)
  }
  async function kaydet(tarih, metin) {
    setHata(null)
    const h = await onIslem(async () => {
      await api.gelisimKayitEkle(m.kod, tarih, metin)
      if (form === 'yaptim') return api.gelisimDurum(m.kod, 'tamamlandi')
      return null
    })
    if (h) { setHata(h); return false }
    setForm(null)
    return true
  }

  return (
    <li className={`gl-madde gl-${m.durum}`}>
      <div className="gl-madde-ust">
        <span className="gl-ikon" aria-hidden="true">{DURUM_IKON[m.durum]}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="gl-baslik">{m.baslik}</div>
          <div className="yp-ince">{[m.tur_etiket, m.asama_ad].filter(Boolean).join(' · ')}</div>
          {m.aciklama && <div className="gl-aciklama">{m.aciklama}</div>}
          {m.olcut && <div className="yp-ince" style={{ marginTop: 2 }}><b>Ne zaman “yaptım” diyebilirsin?</b> {m.olcut}</div>}
        </div>
      </div>
      <div className="gl-durumlar" role="group" aria-label={`${m.baslik} durumu`}>
        {DURUM.map((d) => (
          <button key={d.kod} className={m.durum === d.kod ? 'btn' : 'btn sec'} aria-pressed={m.durum === d.kod}
            style={{ fontSize: 12, padding: '5px 10px' }} disabled={!!bekle} onClick={() => durum(d.kod)}>
            {bekle === d.kod ? <span className="spin" /> : d.ad}
          </button>
        ))}
        <button className="hg-link" onClick={() => setForm(form ? null : 'kayit')}>{form ? 'Kapat' : '＋ Kayıt ekle'}</button>
        <Link className="hg-link" to="/koclugu?sekme=yol">Nasıl yaparım?</Link>
      </div>
      {form && (
        <KayitFormu madde={m} onKaydet={kaydet} onVazgec={() => setForm(null)}
          zorunluMetin={form === 'yaptim' ? '“Yaptım” demeden önce ne yaptığını tarihiyle yaz:' : null} />
      )}
      {hata && <div className="auth-error" style={{ margin: '6px 0 0', fontSize: 12 }}>{hata}</div>}
      {kayitVar && (
        <ul className="gl-kayitlar">
          {m.kayitlar.map((k, i) => (
            <li key={k.id ?? `e${i}`}>
              <span className="gl-tarih">{tarihMetni(k.tarih)}</span>
              <span style={{ flex: 1 }}>{k.aciklama}</span>
              {k.id && (
                <button className="hg-link" aria-label="Kaydı sil" title="Kaydı sil"
                  onClick={() => { if (window.confirm('Bu kayıt silinsin mi?')) onIslem(() => api.gelisimKayitSil(k.id)) }}>Sil</button>
              )}
            </li>
          ))}
        </ul>
      )}
    </li>
  )
}

function Alan({ a, onIslem, acikBaslar, guclu = false }) {
  const [acik, setAcik] = useState(acikBaslar)
  return (
    <section className="card gl-alan" aria-label={a.ad}>
      <button className="gl-alan-bas" aria-expanded={acik} onClick={() => setAcik(!acik)}>
        <div style={{ flex: 1, minWidth: 0, textAlign: 'left' }}>
          <div className="ct" style={{ margin: 0 }}>{guclu ? '💪 ' : ''}{a.ad}{a.tur_etiket ? <span className="yp-ince" style={{ fontWeight: 500 }}> · {a.tur_etiket}</span> : null}</div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 6 }}>
            <div style={{ flex: 1 }}><Cubuk yuzde={a.yuzde} renk={guclu ? 'var(--gr)' : 'var(--okul-c)'} /></div>
            <span style={{ fontSize: 12.5, fontWeight: 700, whiteSpace: 'nowrap' }}>{a.tamamlanan}/{a.toplam} · %{a.yuzde}</span>
          </div>
        </div>
        <span className="yp-ince" aria-hidden="true">{acik ? '▲' : '▼'}</span>
      </button>
      {acik && (
        <>
          {a.neden && <div className="gl-neden">{guclu ? 'Bu güçlü yönünü hedefinde nasıl kullanırsın? ' : 'Neden önemli? '}{a.neden}</div>}
          {a.olcum?.acik && (
            <div className="gl-olcum">📏 Bu alanda yeterince madde tamamladın. <Link to="/koclugu?sekme=yol">Kısa ara ölçümü yap →</Link></div>
          )}
          <ol className="gl-maddeler">
            {a.adimlar.map((m) => <Madde key={m.kod} m={m} onIslem={onIslem} />)}
          </ol>
        </>
      )}
    </section>
  )
}

function OzDegerlendirme({ v, onIslem }) {
  const [acik, setAcik] = useState(false)
  const [yanit, setYanit] = useState({})
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const od = v.istege_bagli.oz_degerlendirme
  const tamam = od.sorular.every((s) => (yanit[s.anahtar] || '').trim().length >= 3)
  return (
    <div className="gl-istege">
      <div style={{ flex: 1, minWidth: 0 }}>
        <b>✍️ Öz değerlendirme</b> <span className="yp-ince">· isteğe bağlı, istediğin zaman</span>
        <div className="yp-ince">3 kısa soru: neyi iyi yaptın, nerede zorlandın, sıradaki küçük hedefin ne? Cevaplarını yalnızca sen görürsün.
          {od.son ? ` Son öz değerlendirmen: ${tarihMetni(od.son)}.` : ''}</div>
      </div>
      <button className="btn sec" style={{ fontSize: 12 }} onClick={() => setAcik(!acik)}>{acik ? 'Kapat' : 'Cevapla'}</button>
      {acik && (
        <div style={{ flexBasis: '100%' }}>
          {od.sorular.map((s) => (
            <div key={s.anahtar} style={{ marginTop: 8 }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 4 }}>{s.soru}</div>
              <textarea className="auth-input" rows={2} maxLength={600} value={yanit[s.anahtar] || ''} placeholder="Kısaca yaz…"
                onChange={(e) => setYanit({ ...yanit, [s.anahtar]: e.target.value })}
                style={{ width: '100%', resize: 'vertical', fontFamily: 'inherit', fontSize: 13 }} />
            </div>
          ))}
          <button className="btn" style={{ marginTop: 8 }} disabled={!tamam || bekle} onClick={async () => {
            setBekle(true); setHata(null)
            const h = await onIslem(() => api.ozDegerlendirmeKaydet(yanit))
            setBekle(false)
            if (h) setHata(h); else { setYanit({}); setAcik(false) }
          }}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
          {hata && <div className="auth-error" style={{ marginTop: 6, fontSize: 12 }}>{hata}</div>}
        </div>
      )}
    </div>
  )
}

// Ana sayfa için kısa özet kartı
export function GelisimOzetKarti() {
  const [v, setV] = useState(null)
  const navigate = useNavigate()
  useEffect(() => { api.gelisimListesi().then((x) => { setV(x); yayinla(x) }).catch(() => setV(false)) }, [])
  if (v === false) return null
  if (!v) return <div className="card"><div className="bos-durum" style={{ padding: 12 }}>Gelişim listen hazırlanıyor…</div></div>
  const siradaki = v.alanlar.flatMap((a) => a.adimlar.filter((m) => m.durum !== 'tamamlandi').slice(0, 1).map((m) => ({ ...m, alan: a.ad }))).slice(0, 3)
  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <div className="ct" style={{ margin: 0, flex: 1 }}>Gelişim listen</div>
        <span className="hg-rozet hg-filiz" title={`${v.seviye.puan} puan`}>{v.seviye.ikon} {v.seviye.ad}</span>
      </div>
      {v.on_adim ? (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontWeight: 700 }}>Önce: {v.on_adim.baslik}</div>
          <div className="yp-ince">{v.on_adim.aciklama}</div>
          <button className="btn" style={{ marginTop: 8 }} onClick={() => navigate(v.on_adim.link)}>Başla →</button>
        </div>
      ) : v.alanlar.length === 0 ? (
        <div className="yp-ince" style={{ marginTop: 6 }}>Hedef bölümünde geliştirmen gereken bir alan görünmüyor. Güçlü yönlerini kullanma maddelerine göz atabilirsin.</div>
      ) : (
        <>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', margin: '8px 0' }}>
            <div style={{ flex: 1 }}><Cubuk yuzde={v.ozet.yuzde} /></div>
            <span style={{ fontSize: 12.5, fontWeight: 700 }}>{v.ozet.tamamlanan}/{v.ozet.toplam} madde</span>
          </div>
          <ul className="gl-ozet-liste">
            {siradaki.map((m) => <li key={m.kod}><span className="yp-ince">{m.alan}:</span> {m.baslik}</li>)}
          </ul>
        </>
      )}
      <Link className="hg-link" to="/gelisim">Gelişim listemi aç →</Link>
    </div>
  )
}

export default function GelisimListesi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.gelisimListesi().then((x) => { setV(x); yayinla(x) }).catch((e) => setHata(e.detail || 'Gelişim listesi yüklenemedi.'))
  }, [])

  // Her işlem güncel listeyi döner; hata metni döner ya da null
  async function islem(fn) {
    try {
      const x = await fn()
      const yeni = x && x.alanlar ? x : await api.gelisimListesi()
      setV(yeni); yayinla(yeni)
      return null
    } catch (e) {
      return e.detail || 'Kaydedilemedi.'
    }
  }

  if (!v) return hata ? <div className="card"><div className="auth-error" style={{ margin: 0 }}>{hata}</div></div>
    : <div className="card"><div className="bos-durum yukleniyor" style={{ padding: 12 }}>Yükleniyor…</div></div>

  return (
    <>
      {v.on_adim && (
        <div className="card" style={{ borderLeft: '4px solid var(--okul-c)' }}>
          <div className="ct" style={{ marginBottom: 4 }}>Önce bunu yap</div>
          <div style={{ fontWeight: 700 }}>{v.on_adim.baslik}</div>
          <div className="yp-ince" style={{ margin: '4px 0 8px' }}>{v.on_adim.aciklama}</div>
          <button className="btn" onClick={() => navigate(v.on_adim.link)}>Başla →</button>
        </div>
      )}

      {v.hedef && (
        <div className="card">
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="yp-ince">Hedef bölümün</div>
              <div style={{ fontSize: 16, fontWeight: 800 }}>{v.hedef.ad}</div>
            </div>
            <span className="hg-rozet hg-filiz" title={v.seviye.kural}>{v.seviye.ikon} {v.seviye.ad} · {v.seviye.puan} puan</span>
          </div>
          {v.alanlar.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <div style={{ flex: 1 }}><Cubuk yuzde={v.ozet.yuzde} /></div>
                <span style={{ fontSize: 13, fontWeight: 700 }}>{v.ozet.tamamlanan}/{v.ozet.toplam} madde · %{v.ozet.yuzde}</span>
              </div>
              <div className="yp-ince" style={{ marginTop: 4 }}>
                {v.ozet.alan_sayisi} gelişim alanı{v.ozet.son_ilerleme ? ` · son ilerlemen ${tarihMetni(v.ozet.son_ilerleme)}` : ''}. Süre yok; kendi hızında ilerle.
                Yaptığın her şeyi tarihiyle yaz: hem sen hem rehber öğretmenin gelişimini görür.
              </div>
            </div>
          )}
          {v.seviye.sonraki_ad && <div className="yp-ince" style={{ marginTop: 6 }}>{v.seviye.sonraki_ad} olmana {v.seviye.sonraki_esik - v.seviye.puan} puan kaldı · {v.seviye.kural}</div>}
        </div>
      )}

      {v.alanlar.map((a, i) => <Alan key={a.degisken_kod} a={a} onIslem={islem} acikBaslar={i === 0} />)}

      {v.hedef && v.alanlar.length === 0 && (
        <div className="card"><div className="yp-ince">Hedef bölümünde geliştirmen gereken belirgin bir alan görünmüyor. Aşağıda güçlü yönlerini kullanma maddeleri var.</div></div>
      )}

      {v.guclu_yonler.length > 0 && (
        <>
          <div className="ct" style={{ margin: '18px 0 8px' }}>Güçlü yönlerini kullan <span className="yp-ince" style={{ fontWeight: 500 }}>· isteğe bağlı</span></div>
          {v.guclu_yonler.map((a) => <Alan key={a.degisken_kod} a={a} onIslem={islem} acikBaslar={false} guclu />)}
        </>
      )}

      <div className="card">
        <div className="ct">İsteğe bağlı</div>
        {v.istege_bagli.kesif ? (
          <div className="gl-istege">
            <div style={{ flex: 1, minWidth: 0 }}>
              <b>🔍 Keşfet: {v.istege_bagli.kesif.ad}</b>
              <div className="yp-ince">{v.istege_bagli.kesif.aciklama} Şu ana kadar {v.istege_bagli.kesif.kesfedilen} bölüm keşfettin.</div>
            </div>
            <button className="btn sec" style={{ fontSize: 12 }} onClick={() => navigate(v.istege_bagli.kesif.link)}>Keşfet →</button>
          </div>
        ) : (
          <div className="yp-ince">Bölüm keşfi önerisi değerlendirmen tamamlanınca burada görünür.</div>
        )}
        <OzDegerlendirme v={v} onIslem={islem} />
      </div>
    </>
  )
}
