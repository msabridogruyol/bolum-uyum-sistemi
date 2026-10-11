// [2026-10-11] İş Hayatı → 'gelecek' sekmesi: Gelecekte Bu Meslek (yapay zekâ ve otomasyonun meslek grupları üzerindeki etkisi).
// Uç: GET /ogrenci/is-hayati/gelecek/{bolum_id} (backend/app/api/is_hayati_gelecek.py). Veri: ILO Working Paper 140 (2025) Tablo A1
// → meslek_grubu_ai_etkisi (göç 0058); nitel içerik backend/app/data/ai_etkisi_gruplar.json.
// Renkler bilinçli olarak durum renkleri (yeşil/kırmızı) DEĞİL: tek tonun açıktan koyuya sıralı kullanımı — "yüksek" kötü demek değil,
// "en çok değişecek" demek.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

const ton = (yuzde) => `color-mix(in srgb, var(--okul-c) ${yuzde}%, var(--sur))`
const DUZEY_TON = { dusuk: 30, orta: 58, yuksek: 88 }
const DUZEY_ADIM = { dusuk: 1, orta: 2, yuksek: 3 }
const KATEGORI_SIRA = ['maruz_degil', 'minimal', 'g1', 'g2', 'g3', 'g4']
const KATEGORI_TON = { maruz_degil: 10, minimal: 24, g1: 40, g2: 56, g3: 72, g4: 90 }
const etiket = (renk, zemin) => ({ fontSize: 10.5, fontWeight: 800, color: renk, background: zemin, padding: '2px 8px', borderRadius: 999, whiteSpace: 'nowrap' })

function DuzeyOlcer({ duzey, ad }) {
  const adim = DUZEY_ADIM[duzey] || 0
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }} aria-label={`Değişim düzeyi: ${ad || 'belirsiz'}`}>
      <span aria-hidden="true" style={{ display: 'inline-flex', gap: 3 }}>
        {[1, 2, 3].map((i) => (
          <span key={i} style={{ width: 16, height: 8, borderRadius: 3, background: i <= adim ? ton(DUZEY_TON[duzey]) : 'var(--sur2)', border: '1px solid var(--bor)' }} />
        ))}
      </span>
      <span style={{ fontWeight: 800, fontSize: 13 }}>{ad || 'Belirsiz'}</span>
    </span>
  )
}

function Dagilim({ dagilim, olcek }) {
  const toplam = KATEGORI_SIRA.reduce((t, k) => t + (dagilim?.[k] || 0), 0)
  if (!toplam) return null
  return (
    <div>
      <div style={{ display: 'flex', height: 12, borderRadius: 6, overflow: 'hidden', border: '1px solid var(--bor)' }} aria-hidden="true">
        {KATEGORI_SIRA.filter((k) => dagilim[k]).map((k) => (
          <span key={k} title={`${olcek?.[k]?.ad || k}: ${dagilim[k]}`} style={{ flex: dagilim[k], background: ton(KATEGORI_TON[k]) }} />
        ))}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px 12px', marginTop: 6 }}>
        {KATEGORI_SIRA.filter((k) => dagilim[k]).map((k) => (
          <span key={k} className="yp-ince" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <span aria-hidden="true" style={{ width: 9, height: 9, borderRadius: 2, background: ton(KATEGORI_TON[k]), border: '1px solid var(--bor)' }} />
            {olcek?.[k]?.ad || k}: <b>{dagilim[k]}</b>
          </span>
        ))}
      </div>
    </div>
  )
}

function Liste({ baslik, ikon, maddeler }) {
  if (!maddeler?.length) return null
  return (
    <div style={{ minWidth: 0 }}>
      <div style={{ fontWeight: 800, fontSize: 13, marginBottom: 6 }}>{ikon} {baslik}</div>
      <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, lineHeight: 1.55, color: 'var(--tx2)' }}>
        {maddeler.map((m, i) => <li key={i}>{m}</li>)}
      </ul>
    </div>
  )
}

function GrupKarti({ g, meslekler, olcek }) {
  const [acik, setAcik] = useState(false)
  const ortaGuven = meslekler.filter((m) => m.isco_guven === 'orta')
  return (
    <div className="card" style={{ padding: '16px 18px', borderLeft: `4px solid ${g.duzey ? ton(DUZEY_TON[g.duzey] || 20) : 'var(--bor)'}` }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap' }}>
        <div style={{ minWidth: 0, flex: '1 1 240px' }}>
          <div className="yp-ince">Meslek grubu (ISCO-08 {g.kod})</div>
          <div style={{ fontWeight: 800, fontSize: 15, lineHeight: 1.35 }}>{g.ad || `ISCO ${g.kod}`}</div>
        </div>
        {g.veri_var ? <DuzeyOlcer duzey={g.duzey} ad={g.duzey_ad} /> : <span style={etiket('var(--tx3)', 'var(--sur2)')}>Bu grup için veri yok</span>}
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, margin: '10px 0 4px' }}>
        {meslekler.map((m) => (
          <span key={m.meslek} style={etiket('var(--tx)', 'var(--sur2)')}>
            {m.meslek}{m.isco_guven === 'orta' && <span title="Bu meslek, meslek grubuna orta güvenle eşlendi" style={{ color: 'var(--tx3)' }}> *</span>}
          </span>
        ))}
      </div>
      {ortaGuven.length > 0 && (
        <div className="yp-ince" style={{ marginBottom: 6 }}>* Bu meslek(ler) meslek grubuna adı ve bölüm bağlamıyla <b>orta güvenle</b> eşlendi; grup bilgisi yaklaşık bir yol göstericidir.</div>
      )}

      {g.veri_var && (
        <div style={{ margin: '10px 0 14px' }}>
          <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginBottom: 6 }}>
            ILO, bu gruptaki <b>{g.meslek_sayisi}</b> mesleği tek tek sınıflandırdı. Dağılım (soldan sağa: en az → en çok maruz kalan):
          </div>
          <Dagilim dagilim={g.dagilim} olcek={olcek} />
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 220px), 1fr))', gap: 14 }}>
        <Liste baslik="Hangi görevler en çok değişiyor?" ikon="🔄" maddeler={g.degisen_gorevler} />
        <Liste baslik="Hangi beceriler değer kazanıyor?" ikon="💎" maddeler={g.deger_kazanan} />
        <Liste baslik="Lisede ne yapabilirsin?" ikon="🎒" maddeler={g.lisede} />
      </div>

      {g.ilo_meslekleri?.length > 0 && (
        <div style={{ borderTop: '1px solid var(--bor)', marginTop: 14 }}>
          <button onClick={() => setAcik(!acik)} aria-expanded={acik}
            style={{ all: 'unset', cursor: 'pointer', display: 'flex', width: '100%', padding: '8px 0', fontSize: 12.5, fontWeight: 700, gap: 8 }}>
            ILO tablosundaki meslekler (en çok maruz kalandan başlayarak)<span style={{ marginLeft: 'auto', color: 'var(--tx3)' }}>{acik ? '▴' : '▾'}</span>
          </button>
          {acik && (
            <div className="yp-tablo-kap">
              <table className="yp-tablo">
                <thead><tr><th>ISCO</th><th>Meslek (ILO'daki İngilizce adı)</th><th>ILO sınıfı</th><th>Ortalama puan</th></tr></thead>
                <tbody>
                  {g.ilo_meslekleri.map((m) => (
                    <tr key={m.kod}>
                      <td>{m.kod}</td><td>{m.ad}</td><td>{olcek?.[m.kategori]?.ad || m.kategori}</td>
                      <td>{Number(m.ort).toLocaleString('tr-TR', { minimumFractionDigits: 2 })}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="yp-ince" style={{ margin: '6px 0' }}>
                Ortalama puan: mesleğin görevlerinin üretken yapay zekâ ile yapılabilme potansiyelinin ortalaması (0–1). {g.meslek_sayisi > g.ilo_meslekleri.length && `Grubun ${g.meslek_sayisi} mesleğinden ilk ${g.ilo_meslekleri.length} tanesi gösteriliyor.`}
              </div>
            </div>
          )}
        </div>
      )}

      {g.veri_var && (
        <div className="yp-ince" style={{ marginTop: 8, lineHeight: 1.5 }}>
          Kaynak: ILO Working Paper 140 · {g.kaynak_bolum} · veri yılı {g.veri_yili}
        </div>
      )}
    </div>
  )
}

export default function GelecekteMeslek({ bolum }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [ayrinti, setAyrinti] = useState(false)

  useEffect(() => {
    api.isHayatiGelecek(bolum.id).then(setV).catch((e) => setHata(e.detail || 'Bilgi yüklenemedi.'))
  }, [bolum.id])

  if (hata) return <div className="auth-error">{hata}</div>
  if (!v) return <div className="bos-durum">Yükleniyor…</div>

  const grupMeslekleri = (kod) => v.meslekler.filter((m) => m.grup_kodu === kod)

  return (
    <div>
      <div className="card" style={{ padding: '16px 18px', borderLeft: '4px solid var(--okul-c)' }}>
        <div style={{ fontSize: 15, fontWeight: 800 }}>🔭 Maruz kalma, mesleğin yok olacağı anlamına gelmez</div>
        <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.6, marginTop: 4 }}>{v.uyari?.metin}</div>
        {v.uyari?.ek?.length > 0 && (
          <>
            <button onClick={() => setAyrinti(!ayrinti)} aria-expanded={ayrinti}
              style={{ all: 'unset', cursor: 'pointer', fontSize: 12.5, fontWeight: 700, color: 'var(--okul-c)', marginTop: 8 }}>
              {ayrinti ? 'Daha az göster ▴' : 'ILO başka ne söylüyor? ▾'}
            </button>
            {ayrinti && (
              <ul style={{ margin: '6px 0 0', paddingLeft: 18, fontSize: 12.5, lineHeight: 1.55, color: 'var(--tx2)' }}>
                {v.uyari.ek.map((e, i) => <li key={i}>{e}</li>)}
              </ul>
            )}
          </>
        )}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px 16px', marginTop: 12 }}>
          {['dusuk', 'orta', 'yuksek'].map((d) => <DuzeyOlcer key={d} duzey={d} ad={v.duzey_adlari?.[d]} />)}
        </div>
        <div className="yp-ince" style={{ marginTop: 6 }}>
          Ölçek, işin ne kadar <b>değişeceğini</b> gösterir; iyi ya da kötü anlamına gelmez. Çok değişecek mesleklerde yeni araçları iyi kullanan kişiler öne çıkabilir.
        </div>
      </div>

      {v.gruplar.length === 0 && (
        <div className="bos-durum">Bu bölümün meslekleri henüz bir meslek grubuyla eşlenmedi.</div>
      )}
      {v.veri_yok && v.gruplar.length > 0 && (
        <div className="bos-durum">Bu bölümün meslek grupları için yapay zekâ etkisi verisi henüz yüklenmedi.</div>
      )}

      {v.gruplar.map((g) => <GrupKarti key={g.kod} g={g} meslekler={grupMeslekleri(g.kod)} olcek={v.olcek} />)}

      {v.eslesmeyen?.length > 0 && (
        <div className="yp-ince" style={{ marginBottom: 12 }}>Meslek grubu henüz belirlenmemiş meslekler: {v.eslesmeyen.join(', ')}.</div>
      )}

      {v.genel?.maddeler?.length > 0 && (
        <div className="card" style={{ padding: '16px 18px' }}>
          <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 4 }}>🌍 Dünyada işverenler ne bekliyor?</div>
          <div className="yp-ince" style={{ marginBottom: 8 }}>{v.genel.kisa}. {v.genel.not}</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12.5, lineHeight: 1.6, color: 'var(--tx2)' }}>
            {v.genel.maddeler.map((m, i) => <li key={i}>{m}</li>)}
          </ul>
        </div>
      )}

      <div className="yp-ince" style={{ lineHeight: 1.6, marginTop: 4 }}>
        <b>Nasıl hesaplandı?</b> ILO, 2025 endeksinde her mesleği görevlerinin yapay zekâya maruz kalma puanlarına göre “maruz değil”,
        “minimal” ya da artan dört gradyandan birine yerleştirir. {v.duzey_kurali}
        {v.kaynaklar?.length > 0 && (
          <ul style={{ margin: '4px 0 6px', paddingLeft: 18 }}>
            {v.kaynaklar.map((k, i) => (
              <li key={i}>{k.url ? <a href={k.url} target="_blank" rel="noreferrer" style={{ color: 'var(--okul-c)' }}>{k.ad}</a> : k.ad}</li>
            ))}
          </ul>
        )}
        {v.son_kontrol && `Son kontrol: ${new Date(v.son_kontrol).toLocaleDateString('tr-TR')}. `}
        Bu bilgiler küresel çalışmalara dayanır; Türkiye'de teknolojinin ne hızla kullanılacağı sektöre ve işyerine göre değişebilir.
      </div>
    </div>
  )
}
