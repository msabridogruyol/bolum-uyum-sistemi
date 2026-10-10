// [2026-10-10] Kütüphanem grafikleri: özet sayılar, aylara göre tamamlananlar (türe göre yığılmış),
// aylara göre okunan sayfa, kitap türleri. Renkler sabit sırayla (kitap, izleme, kurs, etkinlik) — palet doğrulandı.
import { useMemo } from 'react'

const KAT = [['kitap', 'Kitap'], ['izleme', 'Film / dizi'], ['kurs', 'Kurs'], ['etkinlik', 'Etkinlik']]
const AY_AD = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']

function sonAylar(n = 12) {
  const d = new Date(); d.setDate(1)
  const l = []
  for (let i = n - 1; i >= 0; i--) {
    const x = new Date(d.getFullYear(), d.getMonth() - i, 1)
    l.push({ anahtar: `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}`, ad: AY_AD[x.getMonth()], yil: x.getFullYear() })
  }
  return l
}
const ayAnahtari = (x) => String(x.tarih || x.olusturulma_zamani || '').slice(0, 7)

function Kutu({ ikon, deger, ad, alt }) {
  return (
    <div className="kg-kutu">
      <span className="kg-ikon" aria-hidden="true">{ikon}</span>
      <b>{deger}</b>
      <span>{ad}</span>
      {alt && <small>{alt}</small>}
    </div>
  )
}

export default function KutuphaneGrafikleri({ v }) {
  const h = useMemo(() => {
    const bitti = v.kayitlar.filter((x) => x.durum === 'bitti')
    const aylar = sonAylar(12).map((a) => ({ ...a, kat: Object.fromEntries(KAT.map(([k]) => [k, 0])), sayfa: 0 }))
    const ix = Object.fromEntries(aylar.map((a, i) => [a.anahtar, i]))
    bitti.forEach((x) => {
      const i = ix[ayAnahtari(x)]
      if (i === undefined) return
      if (aylar[i].kat[x.kategori] !== undefined) aylar[i].kat[x.kategori] += 1
      if (x.kategori === 'kitap' && x.sayfa) aylar[i].sayfa += x.sayfa
    })
    const turler = {}
    v.kayitlar.filter((x) => x.kategori === 'kitap' && x.durum !== 'istek').forEach((x) => { const t = x.alt_tur || 'Belirtilmedi'; turler[t] = (turler[t] || 0) + 1 })
    const puanli = bitti.filter((x) => x.puan)
    const kitap = bitti.filter((x) => x.kategori === 'kitap')
    const kitapSayfali = kitap.filter((x) => x.sayfa)
    return {
      aylar,
      maksAy: Math.max(1, ...aylar.map((a) => Object.values(a.kat).reduce((s, n) => s + n, 0))),
      maksSayfa: Math.max(1, ...aylar.map((a) => a.sayfa)),
      turler: Object.entries(turler).sort((a, b) => b[1] - a[1]).slice(0, 8),
      kitap: kitap.length,
      sayfa: kitapSayfali.reduce((s, x) => s + x.sayfa, 0),
      ortSayfa: kitapSayfali.length ? Math.round(kitapSayfali.reduce((s, x) => s + x.sayfa, 0) / kitapSayfali.length) : null,
      izleme: bitti.filter((x) => x.kategori === 'izleme').length,
      diger: bitti.filter((x) => x.kategori === 'kurs' || x.kategori === 'etkinlik').length,
      puan: puanli.length ? (puanli.reduce((s, x) => s + x.puan, 0) / puanli.length).toFixed(1) : '—',
      listede: v.kayitlar.filter((x) => x.durum === 'istek').length,
      devam: v.kayitlar.filter((x) => x.durum === 'devam').length,
      bosMu: bitti.length === 0,
    }
  }, [v])
  const maksTur = Math.max(1, ...h.turler.map((t) => t[1]))

  return (
    <div className="kg">
      <div className="kg-kutular">
        <Kutu ikon="📖" deger={h.kitap} ad="okunan kitap" alt={h.devam ? `${h.devam} kayıt devam ediyor` : null} />
        <Kutu ikon="📄" deger={h.sayfa.toLocaleString('tr-TR')} ad="okunan sayfa" alt={h.ortSayfa ? `kitap başına ort. ${h.ortSayfa}` : 'sayfa sayısı girilen kitaplardan'} />
        <Kutu ikon="🎬" deger={h.izleme} ad="izlenen film / dizi / belgesel" />
        <Kutu ikon="🏅" deger={h.diger} ad="tamamlanan kurs ve etkinlik" />
        <Kutu ikon="⭐" deger={h.puan} ad="ortalama puanın" alt={h.listede ? `${h.listede} kayıt listende bekliyor` : null} />
      </div>

      {h.bosMu ? (
        <div className="card kg-bos">Bir kaydı "Okudum / İzledim / Tamamladım" olarak eklediğinde grafiklerin burada oluşmaya başlar.</div>
      ) : (
        <div className="kg-grafikler">
          <div className="card kg-kart kg-genis">
            <div className="kg-baslik">Son 12 ayda tamamladıkların</div>
            <div className="kg-lejant">{KAT.map(([k, ad]) => <span key={k}><i className={`kg-r-${k}`} />{ad}</span>)}</div>
            <div className="kg-sutunlar" role="img" aria-label="Son 12 ayda türe göre tamamlanan kayıt sayıları">
              {h.aylar.map((a) => {
                const top = Object.values(a.kat).reduce((s, n) => s + n, 0)
                return (
                  <div key={a.anahtar} className="kg-sutun" title={`${a.ad} ${a.yil}: ${KAT.filter(([k]) => a.kat[k]).map(([k, ad]) => `${ad} ${a.kat[k]}`).join(', ') || 'kayıt yok'}`}>
                    <span className="kg-deger">{top || ''}</span>
                    <div className="kg-yigin" style={{ height: `${(top / h.maksAy) * 100}%` }}>
                      {KAT.filter(([k]) => a.kat[k]).map(([k]) => <div key={k} className={`kg-r-${k}`} style={{ flexGrow: a.kat[k] }} />)}
                    </div>
                    <span className="kg-etiket">{a.ad}</span>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="card kg-kart">
            <div className="kg-baslik">Aylara göre okunan sayfa</div>
            {h.sayfa === 0 ? <div className="kg-not">Kitap eklerken sayfa sayısını yazarsan burada aylık okuma grafiğin oluşur.</div> : (
              <div className="kg-sutunlar kg-tek" role="img" aria-label="Son 12 ayda okunan sayfa sayısı">
                {h.aylar.map((a) => (
                  <div key={a.anahtar} className="kg-sutun" title={`${a.ad} ${a.yil}: ${a.sayfa.toLocaleString('tr-TR')} sayfa`}>
                    <span className="kg-deger">{a.sayfa ? a.sayfa.toLocaleString('tr-TR') : ''}</span>
                    <div className="kg-yigin" style={{ height: `${(a.sayfa / h.maksSayfa) * 100}%` }}><div className="kg-r-kitap" style={{ flexGrow: 1 }} /></div>
                    <span className="kg-etiket">{a.ad}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card kg-kart">
            <div className="kg-baslik">Okuduğun kitap türleri</div>
            {h.turler.length === 0 ? <div className="kg-not">Henüz kitap yok.</div> : (
              <div className="kg-yatay">
                {h.turler.map(([t, n]) => (
                  <div key={t} className="kg-yatay-satir" title={`${t}: ${n} kitap`}>
                    <span>{t}</span>
                    <div className="kg-yatay-iz"><div className="kg-r-kitap" style={{ width: `${Math.max(4, (n / maksTur) * 100)}%` }} /></div>
                    <b>{n}</b>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
