// [2026-10-09] Ana sayfa — tam genişlikte "Profil raporun" satırı: 3 grafik yan yana.
//  1) Katmanlara göre profil (sütun)  2) En güçlü 6 yönün (yatay çubuk)  3) Bölüm uyum sıralaman (ilk 10, sütun)
// Tek seriler tek renk; değerler metin renginde; üzerine gelince ayrıntı (title + vurgu).
import { useState } from 'react'

const KISA = { K1: 'Değerler', K2: 'Kişilik', K3: 'İş ortamı', K4: 'Alan eğilimi', K5: 'Derinleşme' }

function KatmanSutunlari({ veriler }) {
  const [aktif, setAktif] = useState(null)
  return (
    <div className="gr-sutunlar" onMouseLeave={() => setAktif(null)}>
      <div className="gr-izgara" aria-hidden="true">
        {[100, 50, 0].map((v) => <div key={v} className="gr-izgara-cizgi" style={{ bottom: `${v}%` }}><span>{v}</span></div>)}
      </div>
      {veriler.map((v) => (
        <div key={v.kod} className={`gr-sutun-kap${aktif && aktif !== v.kod ? ' soluk' : ''}`} onMouseEnter={() => setAktif(v.kod)}
          title={`${v.kod} ${KISA[v.kod] || ''}: ${v.deger == null ? 'henüz yok' : `ortalama ${v.deger}/100`}`}>
          <div className="gr-sutun-alan">
            {v.deger != null ? (
              <div className="gr-sutun" style={{ height: `${Math.max(3, v.deger)}%` }}>
                <span className="gr-sutun-deger">{v.deger}</span>
              </div>
            ) : <div className="gr-sutun bos" style={{ height: '100%' }} />}
          </div>
          <div className="gr-sutun-etiket"><b>{v.kod}</b><span>{KISA[v.kod]}</span></div>
        </div>
      ))}
    </div>
  )
}

function YatayCubuklar({ satirlar, renk }) {
  return (
    <div className="gr-yatay">
      {satirlar.map((s, i) => (
        <div key={s.ad} className="gr-yatay-satir" title={`${s.ad}: ${s.deger}/100`}>
          <span className="gr-yatay-ad">{s.ad}</span>
          <span className="gr-yatay-iz"><span className="gr-yatay-dolu" style={{ width: `${s.deger}%`, background: renk, animationDelay: `${0.25 + i * 0.06}s` }} /></span>
          <span className="gr-yatay-deger">{s.deger}</span>
        </div>
      ))}
    </div>
  )
}

function UyumSiralamasi({ siralama, onTik }) {
  const [aktif, setAktif] = useState(0)
  const ilk = siralama.slice(0, 10)
  const min = Math.max(0, Math.floor((Math.min(...ilk.map((s) => s.toplam_uyum)) - 10) / 10) * 10)
  const s = ilk[aktif] || ilk[0]
  return (
    <>
      <div className="gr-uyum-ozet">
        <span className="gr-uyum-sira">{aktif + 1}.</span>
        <span className="gr-uyum-ad" onClick={() => onTik?.(s.bolum_id, s.bolum_adi)}>{s.bolum_adi}</span>
        <span className="gr-uyum-deger">%{Math.round(s.toplam_uyum)}</span>
      </div>
      <div className="gr-uyum-sutunlar">
        {ilk.map((x, i) => (
          <button key={x.bolum_id} className={`gr-uyum-sutun-kap${i === aktif ? ' aktif' : ''}`}
            onMouseEnter={() => setAktif(i)} onFocus={() => setAktif(i)} onClick={() => onTik?.(x.bolum_id, x.bolum_adi)}
            title={`${i + 1}. ${x.bolum_adi} — %${Math.round(x.toplam_uyum)}`}>
            <span className="gr-uyum-sutun" style={{ height: `${Math.max(4, ((x.toplam_uyum - min) / (100 - min)) * 100)}%`, animationDelay: `${0.2 + i * 0.05}s` }} />
            <span className="gr-uyum-no">{i + 1}</span>
          </button>
        ))}
      </div>
      <div className="gr-not">Ölçek %{min}–100 · çubuğun üzerine gel, tıklayınca bölümü aç</div>
    </>
  )
}

export default function AnaSayfaGrafikleri({ katmanVerisi, gucluYonler, siralama, onBolumAc }) {
  return (
    <div className="card gr-rapor">
      <div className="gr-rapor-bas">
        <div className="ct" style={{ margin: 0 }}>📊 Profil Raporun</div>
        <span className="yp-ince">Değerlendirme sonuçlarının özeti</span>
      </div>
      <div className="gr-satir">
        <div className="gr-panel">
          <div className="gr-baslik">Katmanlara göre profilin</div>
          <div className="gr-alt">Her katmandaki özelliklerinin ortalaması (0–100)</div>
          <KatmanSutunlari veriler={katmanVerisi} />
        </div>
        <div className="gr-panel">
          <div className="gr-baslik">En güçlü yönlerin</div>
          <div className="gr-alt">Tüm katmanlarda en yüksek puanlı 6 özelliğin</div>
          {gucluYonler.length ? <YatayCubuklar satirlar={gucluYonler} renk="var(--gr)" /> : <div className="gr-bos">Katmanları tamamladıkça burada görünecek</div>}
        </div>
        <div className="gr-panel">
          <div className="gr-baslik">Bölüm uyum sıralaman</div>
          <div className="gr-alt">Sana en uygun 10 bölüm ve aralarındaki fark</div>
          {siralama?.length ? <UyumSiralamasi siralama={siralama} onTik={onBolumAc} /> : <div className="gr-bos">K1–K4 bitince bölüm uyumların burada görünecek</div>}
        </div>
      </div>
    </div>
  )
}
