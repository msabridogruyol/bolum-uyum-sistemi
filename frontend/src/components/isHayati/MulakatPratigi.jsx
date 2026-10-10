// [2026-10-10] İş Hayatı → 'mulakat' sekmesi: Mülakat Pratiği.
// Akış: soru → yazılı cevap → kendi kendine kontrol listesi (STAR öğeleri, somut örnek, süre) → iyi cevap ipuçları (yapı; örnek cevap yok).
// Filiz (filiz_ai) açık ve yapay zekâ yapılandırılmışsa "Filiz'den geri bildirim al" görünür; kapalıysa düğme hiç gösterilmez.
// Cevaplar yalnızca öğrenciye görünür. Uçlar: backend/app/api/is_hayati_mulakat.py
import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../../api/client'

const kelime = (t) => (t.trim() ? t.trim().split(/\s+/).length : 0)
const sure = (sn) => `${Math.floor(sn / 60)}:${String(sn % 60).padStart(2, '0')}`

function Star({ star }) {
  if (!star) return null
  return (
    <details className="ihm-star">
      <summary>⭐ {star.baslik}: davranışsal sorularda cevabını nasıl kurarsın?</summary>
      <div className="ihz-metin" style={{ margin: '6px 0 8px' }}>{star.aciklama}</div>
      <div className="ihm-star-ogeler">
        {star.ogeler.map((o) => (
          <div key={o.harf} className="ihm-star-oge"><span className="ihm-harf">{o.harf}</span><div><b>{o.ad}</b><div>{o.aciklama}</div></div></div>
        ))}
      </div>
    </details>
  )
}

function Pratik({ soru, v, onKapat, onKaydedildi }) {
  const [cevap, setCevap] = useState('')
  const [adim, setAdim] = useState('yaz')     // yaz → kontrol → ipucu
  const [isaret, setIsaret] = useState([])
  const [sn, setSn] = useState(0)
  const [kayit, setKayit] = useState(null)
  const [gb, setGb] = useState(null)
  const [ai, setAi] = useState(v.ai)
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const baslangic = useRef(null)

  useEffect(() => {
    if (adim !== 'yaz') return undefined
    const t = setInterval(() => { if (baslangic.current) setSn(Math.round((Date.now() - baslangic.current) / 1000)) }, 1000)
    return () => clearInterval(t)
  }, [adim])

  const star = soru.kategori === 'davranissal' || soru.star
  const kontrol = v.kontrol.filter((k) => k.tur === 'hepsi' || (star && k.tur === 'star'))

  async function kaydet() {
    setBekle(true); setHata(null)
    try {
      const r = await api.isHayatiMulakatKaydet({ soru_id: soru.id, cevap, kontrol: isaret, sure_sn: sn || null })
      setKayit(r); setAdim('ipucu'); onKaydedildi()
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  async function filiz() {
    setBekle(true); setHata(null)
    try { const r = await api.isHayatiMulakatGeriBildirim(kayit.id); setGb(r); if (r.ai) setAi(r.ai) } catch (e) { setHata(e.detail || 'Filiz şu an yanıt veremedi.') } finally { setBekle(false) }
  }

  return (
    <div className="card ihm-pratik">
      <div className="ihz-tur-ust">
        <button className="yp-mini" onClick={onKapat}>← Sorular</button>
        <span className="yp-ince" style={{ marginLeft: 'auto' }}>{adim === 'yaz' ? '1. Cevapla' : adim === 'kontrol' ? '2. Kontrol et' : '3. Geliştir'}</span>
      </div>
      <div className="ihm-soru">🎤 {soru.soru}</div>
      {soru.neden && <div className="yp-ince" style={{ marginTop: 4 }}>Neden sorulur? {soru.neden}</div>}

      {adim === 'yaz' && (
        <>
          <textarea className="ihm-cevap" rows={8} maxLength={4000} value={cevap} autoFocus
            placeholder={star ? 'Durum → Görev → Eylem → Sonuç sırasıyla yazmayı dene…' : 'Cevabını mülakatta söyleyeceğin gibi yaz…'}
            onChange={(e) => { if (!baslangic.current) baslangic.current = Date.now(); setCevap(e.target.value) }} />
          <div className="ihm-sayac">
            <span>{kelime(cevap)} kelime</span><span>⏱ {sure(sn)}</span>
            <span className="yp-ince" style={{ marginLeft: 'auto' }}>Ad, telefon, adres gibi kişisel bilgiler yazmana gerek yok.</span>
          </div>
          <div className="ms-alt">
            <span style={{ marginRight: 'auto' }} />
            <button className="btn" disabled={kelime(cevap) < 5} onClick={() => setAdim('kontrol')}>Cevabımı kontrol et →</button>
          </div>
        </>
      )}

      {adim !== 'yaz' && <div className="ihm-cevap-goster">{cevap}</div>}

      {adim === 'kontrol' && (
        <>
          <div className="ihz-ara-baslik">✅ Kendi kendine kontrol listesi</div>
          <div className="yp-ince" style={{ marginBottom: 6 }}>Cevabını sesli oku ve doğru olanları işaretle. Puan yok; bu liste yalnızca senin için.</div>
          <div className="ihm-kontrol">
            {kontrol.map((k) => (
              <label key={k.kod} className={isaret.includes(k.kod) ? 'secili' : ''}>
                <input type="checkbox" checked={isaret.includes(k.kod)}
                  onChange={() => setIsaret(isaret.includes(k.kod) ? isaret.filter((x) => x !== k.kod) : [...isaret, k.kod])} />
                <span>{k.metin}</span>
              </label>
            ))}
          </div>
          {hata && <div className="auth-error">{hata}</div>}
          <div className="ms-alt">
            <button className="btn sec" onClick={() => setAdim('yaz')}>← Cevabı düzenle</button>
            <span style={{ marginRight: 'auto' }} />
            <button className="btn" disabled={bekle} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Kaydet ve ipuçlarını gör →'}</button>
          </div>
        </>
      )}

      {adim === 'ipucu' && (
        <>
          {kayit?.kriz && <div className="ihm-filiz-cevap kriz"><b>💚 Filiz</b><div style={{ marginTop: 4 }}>{kayit.kriz}</div></div>}
          {kontrol.some((k) => !isaret.includes(k.kod)) && (
            <div className="ms-kutu" style={{ marginTop: 10 }}>
              <b>Bir dahaki denemede şunlara dikkat edebilirsin:</b>
              <ul>{kontrol.filter((k) => !isaret.includes(k.kod)).map((k) => <li key={k.kod}>{k.metin}</li>)}</ul>
            </div>
          )}
          <div className="ms-kutu iyi" style={{ marginTop: 10 }}>
            <b>💡 İyi bir cevabın yapısı</b>
            <ul>{(soru.ipuclari || []).map((x) => <li key={x}>{x}</li>)}</ul>
          </div>
          {ai?.acik && !gb && !kayit?.kriz && (
            <div className="ihm-filiz">
              <button className="btn" disabled={bekle || ai.kalan <= 0} onClick={filiz}>{bekle ? <span className="spin" /> : '🌱 Filiz\'den geri bildirim al'}</button>
              <span className="yp-ince">{ai.kalan > 0 ? `Bugün kalan hakkın: ${ai.kalan}` : 'Bugünlük hakkın doldu, yarın yine deneyebilirsin.'}</span>
            </div>
          )}
          {gb && (
            <div className={`ihm-filiz-cevap${gb.kriz ? ' kriz' : ''}`}>
              <b>{gb.kriz ? '💚 Filiz' : '🌱 Filiz\'in geri bildirimi'}</b>
              <div style={{ whiteSpace: 'pre-line', marginTop: 4 }}>{gb.geri_bildirim}</div>
              {!gb.kriz && <div className="yp-ince" style={{ marginTop: 6 }}>Yapay zekâ geri bildirimi yalnızca cevabının yapısı hakkındadır; puan değildir.</div>}
            </div>
          )}
          {hata && <div className="auth-error">{hata}</div>}
          <div className="ms-alt">
            <span style={{ marginRight: 'auto' }} />
            <button className="btn sec" onClick={() => { setCevap(''); setIsaret([]); setSn(0); baslangic.current = null; setKayit(null); setGb(null); setAdim('yaz') }}>↻ Yeniden cevapla</button>
            <button className="btn" onClick={onKapat}>Başka soru seç</button>
          </div>
        </>
      )}
    </div>
  )
}

function Gecmis({ onKapat }) {
  const [g, setG] = useState(null)
  const [acik, setAcik] = useState(null)
  useEffect(() => { api.isHayatiMulakatGecmis().then((r) => setG(r.pratikler)).catch(() => setG([])) }, [])
  async function sil(id) {
    if (!window.confirm('Bu cevabı silmek istiyor musun?')) return
    await api.isHayatiMulakatSil(id).catch(() => {})
    setG(g.filter((x) => x.id !== id))
  }
  return (
    <div className="card">
      <div className="ihz-tur-ust"><button className="yp-mini" onClick={onKapat}>← Sorular</button><b className="ihz-tur-ad">Pratik geçmişin</b></div>
      <div className="yp-ince" style={{ marginBottom: 8 }}>Yalnızca sen görebilirsin.</div>
      {!g && <div className="bos-durum">Yükleniyor…</div>}
      {g && !g.length && <div className="bos-durum">Henüz bir pratik kaydetmedin.</div>}
      {g && g.map((p) => (
        <div key={p.id} className="ihm-gecmis">
          <button className="ihm-gecmis-ust" onClick={() => setAcik(acik === p.id ? null : p.id)} aria-expanded={acik === p.id}>
            <span>{p.soru}</span><span className="yp-ince">{new Date(p.zaman).toLocaleDateString('tr-TR')}</span>
          </button>
          {acik === p.id && (
            <div className="ihm-gecmis-govde">
              <div className="ihm-cevap-goster">{p.cevap}</div>
              {p.geri_bildirim && <div className="ihm-filiz-cevap"><b>🌱 Filiz</b><div style={{ whiteSpace: 'pre-line' }}>{p.geri_bildirim}</div></div>}
              <button className="yp-mini" onClick={() => sil(p.id)}>🗑 Sil</button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

export default function MulakatPratigi({ bolum }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [kat, setKat] = useState(null)
  const [soru, setSoru] = useState(null)
  const [gecmis, setGecmis] = useState(false)

  const yukle = () => api.isHayatiMulakat(bolum?.id).then((r) => { setV(r); setKat((k) => k || r.kategoriler[0]?.kod) })
    .catch((e) => setHata(e.detail || 'Mülakat soruları yüklenemedi.'))
  useEffect(() => { yukle() }, [bolum?.id])   // eslint-disable-line react-hooks/exhaustive-deps

  const aktif = useMemo(() => v?.kategoriler.find((k) => k.kod === kat), [v, kat])
  if (hata) return <div className="auth-error">{hata}</div>
  if (!v) return <div className="bos-durum">Yükleniyor…</div>
  if (gecmis) return <Gecmis onKapat={() => { setGecmis(false); yukle() }} />
  if (soru) return <Pratik soru={{ ...soru, kategori: soru.kategori || kat }} v={v} onKapat={() => setSoru(null)} onKaydedildi={yukle} />

  const toplamPratik = Object.values(v.pratik_sayilari || {}).reduce((a, b) => a + b, 0)
  return (
    <div>
      <div className="card ihz-giris">
        <div className="ihz-giris-ust">
          <span className="ihz-buyuk-ikon" aria-hidden="true">🎤</span>
          <div style={{ flex: 1 }}>
            <div className="ihz-baslik">Mülakat pratiği</div>
            <div className="ihz-metin">Bir soru seç, cevabını yaz, sonra kendi kontrol listenle gözden geçir. Burada doğru ya da yanlış cevap yok;
              amaç cevabını açık ve örnekli kurmayı alışkanlık hâline getirmek.</div>
            <div className="yp-ince" style={{ marginTop: 4 }}>🔒 {v.gizlilik}</div>
          </div>
          {toplamPratik > 0 && <button className="yp-mini" onClick={() => setGecmis(true)}>Geçmişim ({toplamPratik})</button>}
        </div>
        <Star star={v.star} />
      </div>
      <div className="ihz-cipler" role="tablist" style={{ margin: '12px 0' }}>
        {v.kategoriler.map((k) => (
          <button key={k.kod} role="tab" aria-selected={kat === k.kod} className={`ihz-cip${kat === k.kod ? ' aktif' : ''}`} onClick={() => setKat(k.kod)}>
            {k.ikon} {k.ad}
          </button>
        ))}
      </div>
      {aktif && (
        <div className="card">
          <div className="yp-ince" style={{ marginBottom: 8 }}>{aktif.aciklama}</div>
          <div className="ihm-sorular">
            {aktif.sorular.map((s) => (
              <button key={s.id} className="ihm-soru-satir" onClick={() => setSoru({ ...s, kategori: aktif.kod })}>
                <span>{s.soru}</span>
                {v.pratik_sayilari?.[s.id] > 0 && <span className="ihm-rozet">✓ {v.pratik_sayilari[s.id]}</span>}
              </button>
            ))}
          </div>
        </div>
      )}
      <details className="card ihm-genel">
        <summary>Genel ipuçları</summary>
        <ul>{v.ipuclari_genel.map((x) => <li key={x}>{x}</li>)}</ul>
      </details>
    </div>
  )
}
