// [2026-10-10] İş Hayatı → 'mezun' sekmesi (Mezunlardan): okulunun GERÇEK mezunlarının, kendi rızalarıyla paylaşılan anlatıları.
// Hikâyeleri yalnızca okul yetkilisi ekler (okul paneli → Mezunlar → Mezun hikâyeleri). Seçili bölüm → aynı alan → diğerleri.
// Uç: GET /ogrenci/is-hayati/mezun/hikayeler?bolum_id= (app/api/is_hayati_mezun.py). Sözleşme: props { bolum, veri, ogrenci }.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

const GRUP = { bolum: 'Bu bölümden mezunlar', alan: 'Aynı alandan mezunlar', null: 'Okulunun diğer mezunları' }

const ONERI_METNI = 'Merhaba öğretmenim, Filizyol\'daki İş Hayatı sayfasında "Mezunlardan" diye bir bölüm var. Okulumuzdan mezun olup '
  + 'çalışan abla ve ağabeylerimizin işlerini kendi ağızlarından okumak, meslek seçerken çok işimize yarar. Okul panelindeki '
  + 'Mezunlar → Mezun hikâyeleri bölümünden, mezunlarımızın izniyle hikâye eklenebiliyormuş. Tanıdığınız mezunlara sormak ister misiniz?'

function HikayeKarti({ h, sorular }) {
  const [acik, setAcik] = useState(false)
  const cevaplar = sorular.filter((s) => h.cevaplar[s.kod])
  const gorunen = acik ? cevaplar : cevaplar.slice(0, 2)
  return (
    <article className="card mh-kart">
      <div className="mh-ust">
        <div className="mh-avatar" aria-hidden="true">{(h.gorunen_ad || 'M').slice(0, 1)}</div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 800, fontSize: 15 }}>{h.gorunen_ad} <span className="yp-ince" style={{ fontWeight: 600 }}>· {h.mezuniyet_yili} mezunu</span></div>
          <div className="yp-ince" style={{ lineHeight: 1.5 }}>
            {[h.bolum_ad, h.universite].filter(Boolean).join(' — ')}
            {h.su_anki_is && <><br />Şu an: <b style={{ color: 'var(--tx2)' }}>{h.su_anki_is}</b></>}
          </div>
        </div>
        {h.eslesme === 'bolum' && <span className="pf-rozet onay" style={{ marginLeft: 'auto' }}>Seçtiğin bölüm</span>}
        {h.eslesme === 'alan' && <span className="pf-rozet" style={{ marginLeft: 'auto' }}>Aynı alan</span>}
      </div>
      {gorunen.map((s) => (
        <div key={s.kod} className="mh-soru">
          <div className="mh-soru-baslik">{s.soru}</div>
          <div className="mh-cevap">{h.cevaplar[s.kod]}</div>
        </div>
      ))}
      {cevaplar.length > 2 && <button type="button" className="hg-link" onClick={() => setAcik(!acik)}>{acik ? 'Daha az göster' : `Devamını oku (${cevaplar.length - 2} soru daha)`}</button>}
    </article>
  )
}

export default function MezunHikayeleri({ bolum }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [kopyalandi, setKopyalandi] = useState(false)
  useEffect(() => { api.isHayatiMezunHikayeleri(bolum?.id).then(setV).catch((e) => setHata(e.detail || 'Hikâyeler yüklenemedi.')) }, [bolum?.id])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>

  if (!v.hikayeler.length) {
    return (
      <div className="card" style={{ padding: '26px 22px', textAlign: 'center' }}>
        <div style={{ fontSize: 34 }} aria-hidden="true">🎓</div>
        <div style={{ fontSize: 16, fontWeight: 800, margin: '6px 0' }}>{v.okul_var ? 'Okulunuz henüz mezun hikâyesi eklemedi' : 'Mezun hikâyeleri okullar içindir'}</div>
        <div className="ps" style={{ margin: '0 auto', maxWidth: 560 }}>
          Bu bölümde yalnızca okulunun gerçek mezunlarının, kendi izinleriyle paylaştıkları deneyimler yer alır: işlerinde gerçekte ne yaptıkları,
          bir günleri, keşke lisede bilseydim dedikleri. Uydurma ya da genel hikâye yoktur.
        </div>
        {v.okul_var && (
          <div className="yp-kutu" style={{ textAlign: 'left', maxWidth: 560, margin: '16px auto 0' }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 6 }}>💡 Rehber öğretmenine önermek ister misin?</div>
            <div style={{ fontSize: 12.5, lineHeight: 1.6, color: 'var(--tx2)' }}>{ONERI_METNI}</div>
            <button className="btn sec" style={{ marginTop: 10, padding: '7px 14px', fontSize: 12.5 }}
              onClick={async () => { try { await navigator.clipboard.writeText(ONERI_METNI); setKopyalandi(true); setTimeout(() => setKopyalandi(false), 1800) } catch { /* izin yok */ } }}>
              {kopyalandi ? '✓ Kopyalandı' : '📋 Metni kopyala'}
            </button>
          </div>
        )}
      </div>
    )
  }

  const gruplar = ['bolum', 'alan', null].map((g) => ({ g, liste: v.hikayeler.filter((h) => h.eslesme === g) })).filter((x) => x.liste.length)
  return (
    <div>
      <div className="yp-ince" style={{ margin: '0 0 12px', lineHeight: 1.55 }}>
        Bu anlatılar okulunun gerçek mezunlarına aittir ve okulun, mezunların izniyle paylaşılır. Her biri <b>bir kişinin deneyimidir</b>; aynı meslekte
        herkesin yaşadığı farklı olabilir.{bolum?.ad && !v.hikayeler.some((h) => h.eslesme === 'bolum') && ` Henüz ${bolum.ad} mezunu bir hikâye yok; diğer mezunların deneyimleri de yol gösterebilir.`}
      </div>
      {gruplar.map(({ g, liste }) => (
        <section key={String(g)} style={{ marginBottom: 6 }}>
          {gruplar.length > 1 && <div className="ct" style={{ margin: '6px 0 10px' }}>{GRUP[g]}</div>}
          <div className="mh-liste">{liste.map((h) => <HikayeKarti key={h.id} h={h} sorular={v.sorular} />)}</div>
        </section>
      ))}
    </div>
  )
}
