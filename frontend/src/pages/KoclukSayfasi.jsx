import { useEffect, useState, useCallback, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import BolumAdi from '../components/BolumAdi'
import Sayac from '../components/Sayac'
import { useBolumBilgi } from '../context/BolumBilgiContext'

// ============================================================
// Ana sayfa
// ============================================================
// [2026-10-03] Kategori etiketleri — grafik, kartlar ve plan AYNI göreli ölçekten gelir
const KATEGORI = {
  belirgin_ustun: { etiket: 'Belirgin güçlü', renk: 'var(--gr)', zemin: 'var(--grl)', grup: 'guclu' },
  ustun: { etiket: 'Güçlü', renk: 'var(--gr)', zemin: 'var(--grl)', grup: 'guclu' },
  beklenti: { etiket: 'Uyumlu', renk: 'var(--pu)', zemin: 'var(--pul)', grup: 'uyumlu' },
  altinda: { etiket: 'Gelişime açık', renk: 'var(--am)', zemin: 'var(--aml)', grup: 'gelisim' },
  belirgin_altinda: { etiket: 'Öncelikli gelişim', renk: 'var(--re)', zemin: 'var(--rel)', grup: 'gelisim' },
}
// [2026-10-09] Sadeleştirildi: yalnızca "Başladım" ve "Yaptım"
const DURUMLAR = [
  { kod: 'devam_ediyor', etiket: '▶ Başladım' },
  { kod: 'tamamlandi', etiket: '✓ Yaptım' },
]

function KategoriRozeti({ kategori }) {
  const k = KATEGORI[kategori] || KATEGORI.beklenti
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
        <KategoriRozeti kategori={g.kategori} />
      </div>
      {acik && (
        <div style={{ fontSize: 11.5, color: 'var(--tx3)', margin: '0 0 6px', lineHeight: 1.45 }}>
          {g.nedir}{g.durum_tespiti ? <><br /><span style={{ color: 'var(--tx2)' }}>{g.durum_tespiti}</span></> : null}
        </div>
      )}
      <div className="mini-cubuk-track" style={{ width: '100%', marginBottom: 3 }}>
        <div className="mini-cubuk-fill" style={{ width: `${g.ogrenci_goreli ?? g.ogrenci_puan}%`, background: 'var(--pu)' }} />
      </div>
      <div className="mini-cubuk-track" style={{ width: '100%' }}>
        <div className="mini-cubuk-fill" style={{ width: `${g.bolum_goreli ?? g.bolum_beklenen}%`, background: 'var(--gr)' }} />
      </div>
    </div>
  )
}

// Tek bir yol haritası adımı: ne yapacağın, ne kadar sürer + [2026-10-09] adım adım "Nasıl yaparsın?",
// kontrol listesi olarak "Nasıl anlarsın?" ve ipucu (açılır-kapanır; sıradaki adımda açık gelir) + durum düğmeleri
function AdimKarti({ adim, onDurum, vurgulu = false, alanGoster = true }) {
  const bitti = adim.durum === 'tamamlandi'
  const detayVar = (adim.nasil && adim.nasil.length > 0) || (adim.kontrol && adim.kontrol.length > 0)
  const [acik, setAcik] = useState(vurgulu)
  return (
    <div className={`adim-kart${vurgulu ? ' vurgulu' : ''}${bitti && !vurgulu ? ' bitti' : ''}`}>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 6 }}>
        {alanGoster && <Cip renk="var(--pu)" zemin="var(--pul)">{adim.degisken_adi}</Cip>}
        <Cip>{adim.tur_etiket}</Cip>
        <Cip>⏱ {adim.sure}</Cip>
      </div>
      <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 4, textDecoration: bitti ? 'line-through' : 'none' }}>{bitti ? '✓ ' : ''}{adim.baslik}</div>
      <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5, marginBottom: 8 }}>{adim.aciklama}</div>

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
              {adim.kontrol.length > 0 && (
                <>
                  <div className="adim-detay-baslik">✅ Nasıl anlarsın? <span>Bunları yapabiliyorsan bu adım tamam:</span></div>
                  <ul className="adim-kontrol">
                    {adim.kontrol.map((m, i) => <li key={i}>{m}</li>)}
                  </ul>
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

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {DURUMLAR.map((d) => (
          <button key={d.kod} className={adim.durum === d.kod || (vurgulu && d.kod === 'tamamlandi') ? 'btn' : 'btn sec'}
            style={vurgulu ? { fontSize: 13.5, padding: '9px 18px' } : { fontSize: 11.5, padding: '5px 10px' }}
            onClick={() => onDurum(adim.kod, adim.durum === d.kod ? null : d.kod)}>
            {d.etiket}
          </button>
        ))}
      </div>
    </div>
  )
}

// ============================================================
// [2026-10-09] Sayfa başlık başlık sekmelere bölündü:
//   Özet · Yol Haritası · Güçlü Yönlerin · Bölümle Karşılaştırma · Gelişimin
// [2026-10-09] Hedef seçimi/değiştirme yalnızca Ayarlar sayfasında (en fazla 3 değişiklik).
// ============================================================
const SEKMELER = [
  { kod: 'ozet', ad: 'Özet', ikon: '🧭' },
  { kod: 'yol', ad: 'Yol Haritam', ikon: '🗺️' },
  { kod: 'guclu', ad: 'Güçlü Yönlerin', ikon: '💪' },
  { kod: 'karsilastirma', ad: 'Sen ve Bölümün', ikon: '📊' },
  { kod: 'ilham', ad: 'İlham Kaynakları', ikon: '📚' },
  { kod: 'gelisim', ad: 'Gelişimin', ikon: '📈' },
]

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

function KaynakKarti({ k, alan }) {
  const t = KAYNAK_TIP[k.tip] || { ad: k.tip, ikon: '•', renk: 'var(--tx2)', zemin: 'var(--sur2)' }
  return (
    <div className="ilham-kart">
      <span className="ilham-tip" style={{ color: t.renk, background: t.zemin }}>{t.ikon} {t.ad}</span>
      <div className="ilham-baslik">{k.baslik}</div>
      <div className="ilham-aciklama">{k.aciklama}</div>
      <button className="hg-link ilham-sor" onClick={() => filizeSor(k, alan)}>💬 Filiz'e sor</button>
    </div>
  )
}

function IlhamSekmesi({ kaynaklar }) {
  const [tip, setTip] = useState('')
  if (!kaynaklar) return <div className="bos-durum">Kaynaklar hazırlanıyor…</div>
  if (!kaynaklar.alanlar.length) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 30 }}>
        <div style={{ fontSize: 30 }}>📚</div>
        <div style={{ fontWeight: 800, margin: '6px 0 4px' }}>Senin alanların için henüz ilham kaynağı eklenmedi</div>
        <div className="ps" style={{ margin: 0 }}>
          Kitap, film, ilham veren kişi ve önemli olay önerileri {kaynaklar.aranan_alanlar?.length ? <>şu alanlar için hazırlanacak: <b>{kaynaklar.aranan_alanlar.join(', ')}</b>.</> : 'yakında burada olacak.'}
        </div>
      </div>
    )
  }
  const tipler = [...new Set(kaynaklar.alanlar.flatMap((a) => a.kaynaklar.map((k) => k.tip)))]
  const gruplar = [['gelisim', '🌱 Gelişim alanların için'], ['guclu', '💪 Güçlü yönlerini büyütmek için']]
  return (
    <>
      <div className="ps" style={{ margin: '0 0 12px' }}>
        Senin gelişim ve güçlü alanlarına göre seçilmiş kitaplar, filmler, ilham veren kişiler ve önemli olaylar. Birini seç, merak ettiğini Filiz'e sor.
      </div>
      {tipler.length > 1 && (
        <div className="ca-filtre">
          <button className={`ca-cip${!tip ? ' aktif' : ''}`} onClick={() => setTip('')}>Tümü</button>
          {tipler.map((x) => <button key={x} className={`ca-cip${tip === x ? ' aktif' : ''}`} onClick={() => setTip(x)}>{KAYNAK_TIP[x]?.ikon} {KAYNAK_TIP[x]?.ad || x}</button>)}
        </div>
      )}
      {gruplar.map(([g, baslik]) => {
        const alanlar = kaynaklar.alanlar.filter((a) => a.grup === g)
          .map((a) => ({ ...a, liste: a.kaynaklar.filter((k) => !tip || k.tip === tip) })).filter((a) => a.liste.length)
        if (!alanlar.length) return null
        return (
          <Bolum key={g} baslik={baslik}>
            {alanlar.map((a) => (
              <div key={a.degisken_kod} style={{ marginBottom: 14 }}>
                <div className="ilham-alan">{a.degisken_adi} <KategoriRozeti kategori={a.kategori} /></div>
                <div className="ilham-grid">{a.liste.map((k) => <KaynakKarti key={k.id} k={k} alan={a.degisken_adi} />)}</div>
              </div>
            ))}
          </Bolum>
        )
      })}
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

function IlerlemeCubugu({ ilerleme }) {
  const { toplam, tamamlanan, devam_eden: devam } = ilerleme
  const yuzde = toplam ? Math.round((100 * tamamlanan) / toplam) : 0
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
        <span>Yol haritası ilerlemen{devam ? ` · ${devam} adım devam ediyor` : ''}</span>
        <span style={{ fontWeight: 700 }}>{tamamlanan} / {toplam} adım · %{yuzde}</span>
      </div>
      <div className="mini-cubuk-track" style={{ width: '100%', height: 10 }}>
        <div className="mini-cubuk-fill" style={{ width: `${yuzde}%`, background: 'var(--gr)' }} />
      </div>
    </div>
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
          </div>
          <KategoriRozeti kategori={o.kategori} />
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------- 1) Özet
function OzetSekmesi({ plan, sayac, sekmeyeGit }) {
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  const s = plan.siradaki_adim
  return (
    <>
      <div className="koc-ozet-kutular">
        <button className="koc-ozet-kutu" onClick={() => sekmeyeGit('guclu')}>
          <b style={{ color: 'var(--gr)' }}><Sayac deger={sayac.guclu} /></b><span>güçlü yön</span>
        </button>
        <button className="koc-ozet-kutu" onClick={() => sekmeyeGit('karsilastirma')}>
          <b style={{ color: 'var(--pu)' }}><Sayac deger={sayac.uyumlu} /></b><span>bölümle uyumlu</span>
        </button>
        <button className="koc-ozet-kutu" onClick={() => sekmeyeGit('yol')}>
          <b style={{ color: 'var(--am)' }}><Sayac deger={sayac.gelisim} /></b><span>gelişime açık</span>
        </button>
      </div>

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

      {plan.odak_alanlari.length > 0 ? (
        <Bolum baslik="🎯 Neden bu adımlar?" alt={`${plan.hedef_bolum_adi} için seni en çok ileri taşıyacak ${plan.odak_alanlari.length} alan üzerine kurulu.`}>
          <OdakSatirlari plan={plan} />
        </Bolum>
      ) : (
        <div className="card">
          <div className="ps" style={{ margin: 0 }}>
            Harika — {plan.hedef_bolum_adi} için belirgin bir gelişim alanın görünmüyor. “Güçlü Yönlerin” sekmesindeki adımlarla bu avantajını büyütebilirsin.
          </div>
        </div>
      )}
    </>
  )
}

// ---------------------------------------------------------------- 2) Yol haritası — her seferinde TEK adım
// [2026-10-09] Lise öğrencisi için sade akış: ekranda yalnızca şimdiki adım var. "Yaptım" deyince sıradaki gelir.
// Üstte noktalı ilerleme yolu, altta sıradaki 2 adımın başlığı ve katlanmış "Tamamladıkların" listesi.
function YolHaritasiSekmesi({ plan, onDurum, kaynaklar, sekmeyeGit }) {
  const [bitenAcik, setBitenAcik] = useState(false)
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  if (plan.odak_alanlari.length === 0) {
    return <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedef için belirgin bir gelişim alanın yok; “Güçlü Yönlerin” sekmesine göz at.</div></div>
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
            <div className="yh-alt">Her adımı bitirdiğinde sıradaki açılır. Acele yok — haftada 1-2 adım yeterli.</div>
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

      {simdiki ? (
        <div key={simdiki.kod} className="yh-simdi">
          <div className="yh-etiket">Şimdiki adımın <span>{simdiki.asama_baslik?.replace(/^\d\. Aşama · /, '')}</span></div>
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

      {biten.length > 0 && (
        <div className="yh-biten">
          <button className="hg-link" onClick={() => setBitenAcik(!bitenAcik)}>{bitenAcik ? '▴' : '▾'} Tamamladıkların ({biten.length})</button>
          {bitenAcik && (
            <div className="yh-biten-liste">
              {biten.map((x) => (
                <div key={x.kod} className="yh-biten-satir">
                  <span className="yh-tik">✓</span>
                  <span style={{ flex: 1, minWidth: 0 }}>{x.baslik}</span>
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
            {d?.puan_turu && <span>📝 {d.puan_turu}</span>}
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
          Hedefini Ayarlar'dan değiştirebilirsin{hedef.kalan_hak != null ? ` · ${hedef.kalan_hak} hak kaldı` : ''}
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------- 3) Güçlü yönler
function GucluSekmesi({ plan, onDurum }) {
  if (!plan) return <div className="bos-durum">Plan hazırlanıyor…</div>
  if (!plan.guclu_yonler.length) return <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedefe göre öne çıkan güçlü yönün henüz yok. Katmanları yeniden değerlendirdiğinde güncellenir.</div></div>
  return (
    <>
      <div className="ps" style={{ marginBottom: 14 }}>Bu özelliklerin {plan.hedef_bolum_adi} için avantaj. Aşağıdaki adımlarla onları görünür bir başarıya dönüştürebilirsin.</div>
      {plan.guclu_yonler.map((g) => (
        <Bolum key={g.degisken_kod} baslik={`✓ ${g.degisken_adi}`} alt={g.neden_onemli} sag={<KategoriRozeti kategori={g.kategori} />}>
          <div className="koc-adim-grid">
            {g.adimlar.map((adim) => <AdimKarti key={adim.kod} adim={adim} onDurum={onDurum} alanGoster={false} />)}
          </div>
        </Bolum>
      ))}
    </>
  )
}

// ---------------------------------------------------------------- 4) Karşılaştırma
function KarsilastirmaSekmesi({ gelisim, hedef }) {
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
        <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
        <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
      </div>
      <div className="ps" style={{ margin: '0 0 14px', fontSize: 11.5 }}>
        Her katmanda, özelliklerinin kendi içindeki ağırlığı bölümün beklentisiyle karşılaştırılır. Çubuklar aynı ölçekte; etiket farkın yönünü gösterir. Açıklama için özelliğin adına dokun.
      </div>
      <div className="koc-katman-cipler">
        {sira.map((kod) => {
          const n = gruplar[kod].satirlar.filter((g) => KATEGORI[g.kategori]?.grup === 'gelisim').length
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
        {!g ? <div className="bos-durum" style={{ padding: 12 }}>Yükleniyor…</div> : g.adimlar.length === 0 ? (
          <div className="ps" style={{ margin: 0 }}>Yol haritandaki bir adımı “Yaptım” diye işaretlediğinde burada tarihiyle birikmeye başlar.</div>
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
          <div className="ps" style={{ margin: 0 }}>Bir sonraki turu tamamladığında her özelliğindeki değişimi ilk turla karşılaştırıp burada göstereceğiz.</div>
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

  async function adimDurumu(kod, durum) {
    try {
      await api.adimDurumuGuncelle(kod, durum)
      setPlan(await api.gelisimPlaniGetir()) // ilerleme ve sıradaki adım sunucuda yeniden hesaplanır
    } catch (err) {
      setHata(err.detail || 'Durum kaydedilemedi.')
    }
  }

  if (hedef === undefined) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  const sayac = { guclu: 0, uyumlu: 0, gelisim: 0 }
  ;(gelisim || []).forEach((g) => { sayac[(KATEGORI[g.kategori] || KATEGORI.beklenti).grup] += 1 })
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
              <div className="ps" style={{ margin: '0 0 12px', fontSize: 12.5 }}>Hedefini seçtiğinde seni o bölümle karşılaştırıp adım adım bir gelişim planı hazırlarız. Hedef seçimi Ayarlar sayfasında.</div>
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
          <div className="card"><div className="ps" style={{ margin: 0 }}>Bu hedef için henüz karşılaştırılacak veri yok — önce katmanlarını tamamla.</div></div>
        )}

        {veriVar && (
          <>
            <div className="koc-sekmeler" role="tablist">
              {SEKMELER.map((s) => (
                <button key={s.kod} role="tab" aria-selected={sekme === s.kod} className={sekme === s.kod ? 'aktif' : ''} onClick={() => sekmeyeGit(s.kod)}>
                  <span aria-hidden="true">{s.ikon}</span> {s.ad}
                  {s.kod === 'yol' && plan && plan.ilerleme.toplam > 0 && <span className="koc-cip-sayi">{plan.ilerleme.tamamlanan}/{plan.ilerleme.toplam}</span>}
                </button>
              ))}
            </div>
            {sekme === 'ozet' && <OzetSekmesi plan={plan} sayac={sayac} sekmeyeGit={sekmeyeGit} />}
            {sekme === 'yol' && <YolHaritasiSekmesi plan={plan} onDurum={adimDurumu} kaynaklar={kaynaklar} sekmeyeGit={sekmeyeGit} />}
            {sekme === 'ilham' && <IlhamSekmesi kaynaklar={kaynaklar} />}
            {sekme === 'guclu' && <GucluSekmesi plan={plan} onDurum={adimDurumu} />}
            {sekme === 'karsilastirma' && <KarsilastirmaSekmesi gelisim={gelisim} hedef={hedef} />}
            {sekme === 'gelisim' && <GelisimSekmesi karsilastirma={karsilastirma} />}
          </>
        )}
      </div>
    </div>
  )
}
