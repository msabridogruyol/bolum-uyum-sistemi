// [2026-10-10] Anket Psikometrisi (yalnızca süper admin)
// Hazır anket şablonlarına tüm okullardan gelen yanıtlardan Cronbach alfa, Feldt %95 GA ve madde istatistikleri.
// Okulun maddelerini değiştirdiği anketler dahil edilmez. Hesap: backend app/core/psikometri.py
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

const ROZET = {
  veri_bekleniyor: { renk: 'var(--tx3)', zemin: 'var(--sur2)' },
  yetersiz_orneklem: { renk: 'var(--am)', zemin: 'var(--aml)' },
  dikkat: { renk: 'var(--re)', zemin: 'var(--rel)' },
  iyi: { renk: 'var(--gr)', zemin: 'var(--grl)' },
}

function Rozet({ durum, ad }) {
  const r = ROZET[durum] || ROZET.veri_bekleniyor
  return (
    <span style={{ display: 'inline-block', fontSize: 11, fontWeight: 700, padding: '3px 9px', borderRadius: 999, color: r.renk, background: r.zemin, border: `1px solid ${r.renk}` }}>
      {ad}
    </span>
  )
}

const say = (v, b = 2) => (v === null || v === undefined ? '—' : Number(v).toFixed(b))

function PlanKarti() {
  return (
    <div className="card">
      <div className="ct">Geçerlik çalışması planı</div>
      <div className="ps" style={{ margin: '0 0 10px' }}>
        Bu formların geçerlik/güvenirlik çalışması henüz yapılmadı; aşağıdaki istatistikler yalnızca ilk adımdır (iç tutarlılık).
        Tam bir çalışma için şu adımlar önerilir:
      </div>
      <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.7, fontSize: 13 }}>
        <li><b>Güvenirlik:</b> iç tutarlılık (Cronbach alfa, bu sayfa); test-tekrar test için aynı gruba 2–4 hafta arayla ikinci uygulama ve iki puan arasında korelasyon.</li>
        <li><b>Yapı geçerliği:</b> n ≥ 200 tamamlanmış yanıtla açımlayıcı, ardından ayrı bir örneklemde doğrulayıcı faktör analizi (dış araçta — ör. R / JASP; veriyi okulların anket Excel'lerinden alın).</li>
        <li><b>Ölçüt geçerliği:</b> formu, aynı yapıyı ölçen yerleşik ve geçerliği kanıtlanmış bir ölçekle birlikte uygulayıp puanlar arası ilişkiye bakın.</li>
        <li><b>Kapsam geçerliği:</b> maddeleri alan uzmanlarına (rehber öğretmen, ölçme-değerlendirme uzmanı) değerlendirtin; uygunluk oranlarını hesaplayın.</li>
      </ul>
    </div>
  )
}

function MaddeTablosu({ maddeler }) {
  return (
    <div className="yp-tablo-kap" style={{ marginTop: 12 }}>
      <table className="yp-tablo">
        <thead>
          <tr><th>Madde</th><th>Ort.</th><th>SS</th><th title="Düzeltilmiş madde-toplam korelasyonu">r<sub>it</sub></th><th>Silinirse α</th><th>Taban %</th><th>Tavan %</th><th>Uyarı</th></tr>
        </thead>
        <tbody>
          {maddeler.map((m) => (
            <tr key={m.id}>
              <td style={{ minWidth: 260 }}>
                <b>{m.id}</b> {m.metin}
                {m.ters && <span className="yp-ince"> (ters)</span>}
              </td>
              <td>{say(m.ortalama)}</td>
              <td>{say(m.ss)}</td>
              <td style={{ color: m.r_it === null || m.r_it < 0.3 ? 'var(--re)' : undefined, fontWeight: 700 }}>{say(m.r_it)}</td>
              <td>{say(m.silinirse_alfa)}</td>
              <td>{say(m.taban_yuzde, 1)}</td>
              <td>{say(m.tavan_yuzde, 1)}</td>
              <td className="yp-ince">{m.uyarilar.join(' · ') || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SablonKarti({ s, esikler }) {
  const [acik, setAcik] = useState(false)
  const bekliyor = s.durum === 'veri_bekleniyor'
  return (
    <div className="card">
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 15 }}>{s.baslik}</div>
          <div className="yp-ince">
            {s.madde_sayisi} likert madde · {s.anonim ? 'anonim' : 'isimli'} · {s.anket_sayisi} uygun anket
            {s.degismis_anket > 0 && ` · maddeleri değiştirilmiş ${s.degismis_anket} anket dahil edilmedi`}
          </div>
        </div>
        <Rozet durum={s.durum} ad={s.durum_adi} />
      </div>

      <div className="sg" style={{ marginTop: 14, marginBottom: 10 }}>
        <div className="sc"><div className="sl">Tamamlanmış yanıt (n)</div><div className="sv">{s.n}</div></div>
        <div className="sc"><div className="sl">Okul</div><div className="sv">{s.okul_sayisi}</div></div>
        <div className="sc">
          <div className="sl">Cronbach α</div>
          <div className="sv" style={{ color: bekliyor ? undefined : s.alfa < esikler.alfa ? 'var(--re)' : 'var(--gr)' }}>{bekliyor ? '—' : say(s.alfa)}</div>
        </div>
        <div className="sc"><div className="sl">%95 GA (Feldt)</div><div className="sv" style={{ fontSize: 16 }}>{s.alfa_ga ? `${say(s.alfa_ga[0])} – ${say(s.alfa_ga[1])}` : '—'}</div></div>
      </div>

      {bekliyor ? (
        <div className="bos-durum">Veri bekleniyor — istatistik için en az {esikler.en_az_istatistik} tamamlanmış yanıt gerekir (şu an {s.n}).</div>
      ) : (
        <>
          {s.uyarilar.length > 0 && <div className="yp-uyari">{s.uyarilar.join(' · ')}</div>}
          {s.alt_boyutlar?.length > 0 && (
            <div className="yp-ince" style={{ marginBottom: 8 }}>
              Alt boyutlar: {s.alt_boyutlar.map((a) => `${a.ad} α = ${say(a.alfa)}`).join(' · ')}
            </div>
          )}
          <button className="hg-link" onClick={() => setAcik(!acik)}>{acik ? '▾ Madde istatistiklerini gizle' : '▸ Madde istatistikleri'}</button>
          {acik && <MaddeTablosu maddeler={s.maddeler} />}
        </>
      )}
    </div>
  )
}

export default function AnketPsikometriSayfasi() {
  const [d, setD] = useState(null)
  const [hata, setHata] = useState(null)
  const [indiriliyor, setIndiriliyor] = useState(false)

  useEffect(() => {
    api.anketPsikometri().then(setD).catch((e) => setHata(e.detail || 'İstatistikler yüklenemedi.'))
  }, [])

  async function indir() {
    setIndiriliyor(true); setHata(null)
    try { await api.anketPsikometriExcel() } catch (e) { setHata(e.detail || 'Excel hazırlanamadı.') } finally { setIndiriliyor(false) }
  }

  return (
    <div className="pg pg-genis">
      <div className="ph" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div className="pt">Anket Psikometrisi</div>
          <div className="ps">
            Hazır tarama formlarına tüm okullardan gelen yanıtlar (isimli ve anonim) birleştirilerek hesaplanır. Yalnızca maddeleri şablonla aynı kalan anketler ve
            tüm likert maddeleri yanıtlanmış formlar sayılır; ters maddeler 6 − x ile çevrilir. Test hesaplarının yanıtları dışlanır.
          </div>
        </div>
        <button className="btn" onClick={indir} disabled={indiriliyor || !d}>{indiriliyor ? <span className="spin" /> : '⬇ Excel indir'}</button>
      </div>

      {hata && <div className="auth-error" role="alert">{hata}</div>}
      <PlanKarti />

      {!d ? (!hata && <div className="bos-durum">Yükleniyor…</div>) : (
        <>
          {d.sablonlar.map((s) => <SablonKarti key={s.kod} s={s} esikler={d.esikler} />)}
          <div className="yp-ince" style={{ lineHeight: 1.6 }}>
            Eşikler: n &lt; {d.esikler.en_az_istatistik} istatistik verilmez · n &lt; {d.esikler.en_az_yorum} yorum için yetersiz örneklem ·
            α &lt; {d.esikler.alfa} ve düzeltilmiş madde-toplam korelasyonu &lt; {d.esikler.r_it} uyarı. Taban/tavan: ham cevapta 1 / 5 seçenlerin yüzdesi.
            McDonald omega gösterilmez — doğru tahmini faktör analizi gerektirir (yukarıdaki plan).
          </div>
        </>
      )}
    </div>
  )
}
