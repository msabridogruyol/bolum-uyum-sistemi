// [2026-10-10] İş Hayatı → 'zorgun' sekmesi: Zor Günler.
// Seçili bölümün üst alanına ve mesleklerine göre "zor gün" senaryoları: fazla mesai, nöbet, öfkeli müşteri, hata, düşük zam…
// Öğrenci her durumda seçim yapar, sonucunu görür; "nasıl başa çıkılır" notu ve "yine de sevenler neden seviyor" cümlesi gelir.
// Sonda hangi yaklaşımla davrandığı (simülasyondaki YAKLASIMLAR) özetlenir. Karar anı görünümü MeslekSimulasyonu ile aynı (ms-* sınıfları).
// Uçlar: GET /ogrenci/is-hayati/zor-gun/{bolum_id}, GET …/tur?meslek=, POST /ogrenci/is-hayati/zor-gun (backend/app/api/is_hayati_zor_gun.py)
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

function Baslangic({ z, onBasla, bekle }) {
  const ozel = z.meslekler.filter((m) => m.ozel)
  const diger = z.meslekler.filter((m) => !m.ozel)
  return (
    <div className="card ihz-giris">
      <div className="ihz-giris-ust">
        <span className="ihz-buyuk-ikon" aria-hidden="true">🌧️</span>
        <div>
          <div className="ihz-baslik">Her mesleğin zor günleri olur</div>
          <div className="ihz-metin">Fazla mesai, öfkeli bir müşteri, yapılan bir hata, beklenenden düşük bir zam… Bunları önceden bilmek seni korkutmak için değil:
            Zor anı tanıyan, onunla başa çıkmanın yolunu da bulur. Bir meslek seç, karşına çıkan durumlarda ne yapacağına karar ver.</div>
        </div>
      </div>
      {z.alan_senaryo_sayisi > 0 && (
        <button className="btn ihz-alan-btn" disabled={bekle} onClick={() => onBasla(null)}>
          {z.alan?.ad} alanının zor günleri <span className="ihz-cip-say">{z.alan_senaryo_sayisi} durum</span>
        </button>
      )}
      {ozel.length > 0 && (
        <>
          <div className="ihz-ara-baslik">Mesleğe özel zor günler</div>
          <div className="ihz-cipler">
            {ozel.map((m) => (
              <button key={m.ad} className="ihz-cip ozel" disabled={bekle} onClick={() => onBasla(m.ad)}>⭐ {m.ad}</button>
            ))}
          </div>
        </>
      )}
      {diger.length > 0 && z.alan_senaryo_sayisi > 0 && (
        <>
          <div className="ihz-ara-baslik">Bu bölümün diğer meslekleri <span className="yp-ince">(alanın ortak zor günleriyle)</span></div>
          <div className="ihz-cipler">
            {diger.map((m) => <button key={m.ad} className="ihz-cip" disabled={bekle} onClick={() => onBasla(m.ad)}>{m.ad}</button>)}
          </div>
        </>
      )}
      {z.son.length > 0 && (
        <div className="ihz-son">
          <div className="ihz-ara-baslik">Son denemelerin</div>
          {z.son.map((s) => (
            <div key={s.zaman} className="ms-gecmis">
              <span>{s.meslek_ad || `${z.alan?.ad} alanı`}</span>
              <span className="yp-ince">{(s.yaklasimlar || []).slice(0, 2).join(', ')}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Sahne({ s, secim, onSec }) {
  const secilen = secim != null ? s.secenekler[secim] : null
  return (
    <div className="ms-sahne karar">
      <div className="ms-saat">
        <span className="ms-ikon" aria-hidden="true">⏰</span>{s.saat}
        <span className="ms-sahne-baslik">{s.baslik}</span>
      </div>
      <div className="ihz-etiketler">
        {s.tur_ad && <span className="ihz-tur">{s.tur_ad}</span>}
        {s.ozel && <span className="ihz-tur ozel">mesleğe özel</span>}
      </div>
      <div className="ms-metin">{s.durum}</div>
      <div className="ms-secenekler">
        <div className="ms-soru">Ne yaparsın?</div>
        {s.secenekler.map((x) => (
          <button key={x.no} disabled={secilen != null} className={`ms-secenek${secim === x.no ? ' secili' : ''}`} onClick={() => onSec(x.no)}>
            {x.metin}
          </button>
        ))}
        {secilen && (
          <>
            <div className={`ms-geri ${secilen.onerilen ? 'iyi' : s.onerilen_var ? 'dikkat' : ''}`}>
              <div className="ms-geri-ust">{secilen.onerilen ? '✓ Meslekte beklenen davranış' : s.onerilen_var ? '⚠️ Bir daha düşün' : `Yaklaşımın: ${secilen.yaklasim}`}</div>
              {secilen.sonuc}
            </div>
            {s.basa_cikma && <div className="ihz-not"><b>🧭 Bu durumla nasıl başa çıkılır?</b><div>{s.basa_cikma}</div></div>}
            {s.neden_seviyorlar && <div className="ihz-sevgi"><span aria-hidden="true">💚</span> {s.neden_seviyorlar}</div>}
          </>
        )}
      </div>
    </div>
  )
}

function Ozet({ o, onYeniden, onBaska }) {
  const enCok = Math.max(...o.dagilim.map((d) => d.sayi))
  return (
    <div className="card ihz-ozet">
      <div className="ihz-baslik">🌤️ Zor günleri geride bıraktın</div>
      <div className="ihz-metin" style={{ marginTop: 4 }}>
        {o.toplam} durumda en çok <b>{o.en_cok.join(' ve ')}</b> yaklaşımıyla davrandın.
      </div>
      <div className="ihz-yaklasimlar" aria-label="Yaklaşım dağılımın">
        {o.dagilim.map((d) => (
          <div key={d.kod} className="ihz-yak">
            <span className="ihz-yak-ad">{d.ad}</span>
            <span className="ihz-yak-cubuk"><span style={{ width: `${(100 * d.sayi) / enCok}%` }} /></span>
            <span className="ihz-yak-say">{d.sayi}</span>
          </div>
        ))}
      </div>
      {o.yorum && <div className="ms-kutu iyi" style={{ marginTop: 10 }}>{o.yorum}</div>}
      <div className="ms-kutu" style={{ marginTop: 10 }}>
        <b>⚡ Kararların</b>
        {o.kararlar.map((k) => (
          <div key={k.baslik} className="ms-karar-ozet">
            <div><b>{k.baslik}:</b> {k.secim} <span className="yp-ince">· {k.yaklasim}</span></div>
            {k.onerilen && <div className="ms-onerilen">Meslekte beklenen: {k.onerilen}</div>}
          </div>
        ))}
      </div>
      <div className="yp-ince" style={{ marginTop: 8 }}>Durumlar kurgusaldır; gerçek iş yerlerinde kurallar ve koşullar değişebilir. Zor bir anda yalnız olmadığını unutma:
        yöneticin, ekip arkadaşların ve gerekirse bir uzman en iyi destektir.</div>
      <div className="ms-alt">
        <button className="btn sec" onClick={onYeniden}>↻ Yeniden dene</button>
        <button className="btn" onClick={onBaska}>Başka bir meslek seç</button>
      </div>
    </div>
  )
}

export default function ZorGunler({ bolum }) {
  const [z, setZ] = useState(null)
  const [tur, setTur] = useState(null)        // { meslek, senaryolar }
  const [i, setI] = useState(0)
  const [secimler, setSecimler] = useState({})
  const [ozet, setOzet] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)

  const yukle = () => api.isHayatiZorGun(bolum.id).then(setZ).catch((e) => setHata(e.detail || 'Zor günler yüklenemedi.'))
  useEffect(() => { yukle() }, [bolum.id])   // eslint-disable-line react-hooks/exhaustive-deps

  async function basla(meslek) {
    setBekle(true); setHata(null)
    try {
      const t = await api.isHayatiZorGunTur(bolum.id, meslek)
      setTur(t); setI(0); setSecimler({}); setOzet(null)
    } catch (e) { setHata(e.detail || 'Senaryolar açılamadı.') } finally { setBekle(false) }
  }
  async function bitir() {
    setBekle(true); setHata(null)
    try {
      setOzet(await api.isHayatiZorGunKaydet({ bolum_id: bolum.id, meslek: tur.meslek, secimler }))
    } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  const kapat = () => { setTur(null); setOzet(null); yukle() }

  if (!z && !hata) return <div className="bos-durum">Yükleniyor…</div>
  if (!z) return <div className="auth-error">{hata}</div>
  if (!z.alan_senaryo_sayisi && !z.meslekler.some((m) => m.ozel)) {
    return <div className="card bos-durum">Bu bölüm için zor gün senaryoları henüz hazırlanmadı.</div>
  }
  if (ozet) return <Ozet o={ozet} onYeniden={() => basla(tur.meslek)} onBaska={kapat} />
  if (!tur) return <>{hata && <div className="auth-error">{hata}</div>}<Baslangic z={z} onBasla={basla} bekle={bekle} /></>

  const s = tur.senaryolar[i]
  const son = i === tur.senaryolar.length - 1
  return (
    <div className="card ihz-tur-kap">
      <div className="ihz-tur-ust">
        <button className="yp-mini" onClick={kapat}>← Geri</button>
        <b className="ihz-tur-ad">{tur.meslek || `${tur.alan?.ad} alanı`}</b>
        <span className="yp-ince">{i + 1} / {tur.senaryolar.length}</span>
      </div>
      <div className="ms-zaman" aria-label="Durumlar">
        {tur.senaryolar.map((x, j) => (
          <div key={x.id} className={`ms-nokta karar${j === i ? ' simdi' : secimler[x.id] != null ? ' gecti' : ''}`} title={x.baslik}><span>{x.saat}</span></div>
        ))}
      </div>
      <Sahne key={s.id} s={s} secim={secimler[s.id]} onSec={(no) => setSecimler({ ...secimler, [s.id]: no })} />
      {hata && <div className="auth-error">{hata}</div>}
      <div className="ms-alt">
        {i > 0 && <button className="btn sec" onClick={() => setI(i - 1)}>← Önceki</button>}
        <span style={{ marginRight: 'auto' }} />
        {son
          ? <button className="btn" disabled={bekle || secimler[s.id] == null} onClick={bitir}>{bekle ? <span className="spin" /> : 'Bitir ve özetimi gör'}</button>
          : <button className="btn" disabled={secimler[s.id] == null} onClick={() => setI(i + 1)}>Sonraki durum →</button>}
      </div>
      <div className="yp-ince" style={{ marginTop: 8 }}>{tur.kaynak_notu}</div>
    </div>
  )
}
