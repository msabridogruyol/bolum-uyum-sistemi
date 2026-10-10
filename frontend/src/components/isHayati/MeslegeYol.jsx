// [2026-10-10] İş Hayatı → 'yol' sekmesi: Mesleğe Giden Yol.
// Lise → YKS → lisans → (staj / sınav / lisans / uzmanlık) → kariyer basamakları; zorlayanlar + nasıl başa çıkılır; lisede hazırlık.
// Uç: GET /ogrenci/is-hayati/yol/{bolum_id} (backend/app/api/is_hayati_yol.py; içerik backend/app/data/meslege_yol.json)
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

const etiket = (renk, zemin) => ({ fontSize: 10.5, fontWeight: 800, color: renk, background: zemin, padding: '2px 8px', borderRadius: 999, whiteSpace: 'nowrap' })

function Zaman({ adimlar }) {
  return (
    <ol style={{ listStyle: 'none', margin: 0, padding: 0 }}>
      {adimlar.map((a, i) => (
        <li key={i} style={{ display: 'grid', gridTemplateColumns: '28px 1fr', gap: 10 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <span style={{ width: 24, height: 24, borderRadius: 999, flex: '0 0 auto', display: 'grid', placeItems: 'center', fontSize: 12, fontWeight: 800,
              background: a.zorunlu ? 'var(--okul-c)' : 'var(--sur)', color: a.zorunlu ? '#fff' : 'var(--okul-c)', border: '2px solid var(--okul-c)' }}>{i + 1}</span>
            {i < adimlar.length - 1 && <span style={{ flex: 1, width: 2, background: 'color-mix(in srgb, var(--okul-c) 35%, transparent)', minHeight: 14 }} />}
          </div>
          <div style={{ paddingBottom: 14, minWidth: 0 }}>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 800, fontSize: 14 }}>{a.baslik}</span>
              {a.sure && <span style={etiket('var(--okul-c)', 'color-mix(in srgb, var(--okul-c) 12%, transparent)')}>⏱ {a.sure}</span>}
              {!a.zorunlu && <span style={etiket('var(--tx3)', 'var(--sur2)')}>isteğe / yola bağlı</span>}
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.55, marginTop: 2 }}>{a.aciklama}</div>
          </div>
        </li>
      ))}
    </ol>
  )
}

export default function MeslegeYol({ bolum }) {
  const [y, setY] = useState(null)
  const [hata, setHata] = useState(null)
  const [acikMeslek, setAcikMeslek] = useState(null)

  useEffect(() => {
    api.isHayatiYol(bolum.id).then(setY).catch((e) => setHata(e.detail || 'Yol bilgisi yüklenemedi.'))
  }, [bolum.id])

  if (hata) return <div className="auth-error">{hata}</div>
  if (!y) return <div className="bos-durum">Yükleniyor…</div>

  return (
    <div>
      <div className="card" style={{ padding: '16px 18px', borderLeft: '4px solid var(--okul-c)' }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginBottom: 6 }}>
          {y.alan?.ad && <span style={etiket('var(--tx2)', 'var(--sur2)')}>{y.alan.ad}</span>}
          {y.bolum.ogrenim_suresi && <span style={etiket('var(--tx2)', 'var(--sur2)')}>Öğrenim: {y.bolum.ogrenim_suresi}</span>}
          {y.regule && <span style={etiket('var(--okul-c)', 'color-mix(in srgb, var(--okul-c) 12%, transparent)')}>⚖️ Kanunla düzenlenmiş meslek yolu</span>}
          {y.oda_kaydi && <span style={etiket('var(--tx2)', 'var(--sur2)')}>Serbest çalışmada oda kaydı</span>}
        </div>
        <div style={{ fontSize: 15, fontWeight: 800 }}>🛤️ {y.bolum.ad} mezunları mesleğe nasıl ulaşıyor?</div>
        {y.ozel && <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.6, marginTop: 4 }}>{y.ozel}</div>}
        {y.temel_bolum && <div className="yp-ince" style={{ marginTop: 4 }}>Yol, {y.temel_bolum} bölümüyle büyük ölçüde aynıdır.</div>}
        {!y.bolume_ozel_kayit && <div className="yp-ince" style={{ marginTop: 4 }}>Bu bölüm için ayrıntılı bir yol henüz yazılmadı; aşağıda alanının genel yolu var.</div>}
      </div>

      <div className="card" style={{ padding: '16px 18px' }}>
        <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 12 }}>Adım adım yol</div>
        <Zaman adimlar={y.adimlar || []} />
        <div className="yp-ince">Dolu daireler hemen herkesin geçtiği adımlar, boş daireler seçtiğin yola göre değişen adımlardır.</div>
      </div>

      {y.basamaklar?.length > 0 && (
        <div className="card" style={{ padding: '16px 18px' }}>
          <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 10 }}>Tipik kariyer basamakları</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 200px), 1fr))', gap: 10 }}>
            {y.basamaklar.map((b, i) => (
              <div key={i} style={{ background: `color-mix(in srgb, var(--okul-c) ${6 + i * 6}%, var(--sur))`, borderRadius: 12, padding: '10px 12px', border: '1px solid var(--bor)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 6, alignItems: 'baseline', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 800, fontSize: 13.5 }}>{'▲'.repeat(i + 1)} {b.ad}</span>
                  <span className="yp-ince">{b.donem}</span>
                </div>
                <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5, marginTop: 4 }}>{b.aciklama}</div>
              </div>
            ))}
          </div>
          <div className="yp-ince" style={{ marginTop: 8 }}>Süreler kişiye, şehre ve kuruma göre çok değişir; buradakiler genel bir çerçevedir.</div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: 12 }}>
        {y.zorlayanlar?.length > 0 && (
          <div className="card" style={{ padding: '16px 18px', marginBottom: 0 }}>
            <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 8 }}>🌧️ Bu yolda zorlayan şeyler</div>
            {y.zorlayanlar.map((z, i) => (
              <div key={i} style={{ marginBottom: 10 }}>
                <div style={{ fontSize: 13, fontWeight: 700, lineHeight: 1.5 }}>{z.zor}</div>
                <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.5, marginTop: 2 }}><span style={{ color: 'var(--gr)', fontWeight: 800 }}>→ Nasıl başa çıkılır:</span> {z.nasil}</div>
              </div>
            ))}
          </div>
        )}
        {y.neden_seviyor?.length > 0 && (
          <div className="card" style={{ padding: '16px 18px', marginBottom: 0 }}>
            <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 8 }}>☀️ Bu yolu seçenler neden seviyor?</div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.6 }}>
              {y.neden_seviyor.map((n, i) => <li key={i}>{n}</li>)}
            </ul>
          </div>
        )}
      </div>

      {y.hazirlik?.length > 0 && (
        <div className="card" style={{ padding: '16px 18px', marginTop: 12 }}>
          <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 8 }}>🎒 Lisede nasıl hazırlanırsın?</div>
          <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'grid', gap: 6 }}>
            {y.hazirlik.map((h, i) => (
              <li key={i} style={{ display: 'flex', gap: 8, fontSize: 13, lineHeight: 1.5 }}>
                <span aria-hidden="true" style={{ color: 'var(--okul-c)', fontWeight: 800 }}>✓</span><span>{h}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {y.meslekler?.length > 0 && (
        <div className="card" style={{ padding: '16px 18px', marginTop: y.hazirlik?.length ? 0 : 12 }}>
          <div style={{ fontWeight: 800, fontSize: 14, marginBottom: 8 }}>Meslek meslek: nasıl olunur?</div>
          {y.meslekler.map((m) => (
            <div key={m.ad} style={{ borderTop: '1px solid var(--bor)' }}>
              <button onClick={() => setAcikMeslek(acikMeslek === m.ad ? null : m.ad)} aria-expanded={acikMeslek === m.ad}
                style={{ all: 'unset', cursor: 'pointer', display: 'flex', width: '100%', padding: '8px 0', fontSize: 13, fontWeight: 700, gap: 8 }}>
                {m.ad}<span style={{ marginLeft: 'auto', color: 'var(--tx3)' }}>{acikMeslek === m.ad ? '▴' : '▾'}</span>
              </button>
              {acikMeslek === m.ad && <div style={{ fontSize: 12.5, color: 'var(--tx2)', lineHeight: 1.55, paddingBottom: 10 }}>{m.nasil_olunur}</div>}
            </div>
          ))}
        </div>
      )}

      <div className="yp-ince" style={{ lineHeight: 1.6, marginTop: 4 }}>
        {y.kaynaklar?.length > 0 && (
          <>
            <b>Yasal dayanak ve kaynaklar</b>{y.son_kontrol && ` (son kontrol: ${new Date(y.son_kontrol).toLocaleDateString('tr-TR')})`}:
            <ul style={{ margin: '4px 0 6px', paddingLeft: 18 }}>
              {y.kaynaklar.map((k, i) => (
                <li key={i}>{k.url ? <a href={k.url} target="_blank" rel="noreferrer" style={{ color: 'var(--okul-c)' }}>{k.ad}</a> : k.ad}</li>
              ))}
            </ul>
          </>
        )}
        Mevzuat ve sınav kuralları değişebilir; tercih yapmadan önce güncel durumu resmî kaynaktan ve rehber öğretmeninden kontrol et.
      </div>
    </div>
  )
}
