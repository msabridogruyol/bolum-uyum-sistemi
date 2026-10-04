import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

// [2026-10-04] Ana sayfadaki "Bu Haftanın Görevleri" kartı.
// Her hafta 3 görev: yolculuk adımı + keşif + yansıtma. En az 2 görev = seri devam eder.
// Görev tamamlanınca 'haftalik-guncellendi' olayı yayınlanır (Filiz maskotu dinler: kutlama / seviye).
const TUR_IKON = { katman: '🧭', k5: '🌻', hedef: '🎯', plan_adimi: '🪜', kesif: '🔍', yansitma: '✍️' }
const TUR_ETIKET = { katman: 'Yolculuk', k5: 'Yolculuk', hedef: 'Yolculuk', plan_adimi: 'Yol haritası', kesif: 'Keşif', yansitma: 'Yansıtma' }
const GIT_METNI = { katman: 'Başla →', k5: 'Başla →', hedef: 'Hedef Seç →', plan_adimi: 'Planda Aç', kesif: 'Keşfet →' }

function yayinla(ozet) {
  window.dispatchEvent(new CustomEvent('haftalik-guncellendi', { detail: ozet }))
}

function kisaTarih(iso) {
  const [, a, g] = iso.split('-')
  return `${Number(g)}.${Number(a)}`
}

export default function HaftalikGorevler() {
  const [ozet, setOzet] = useState(null)
  const [hata, setHata] = useState(null)
  const [acikYansitma, setAcikYansitma] = useState(false)
  const [yanit, setYanit] = useState({})
  const [islenen, setIslenen] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    api.haftalikGetir()
      .then((o) => { setOzet(o); yayinla(o) })
      .catch((e) => setHata(e.detail || 'Haftalık görevler yüklenemedi.'))
  }, [])

  async function tamamla(gorev, yanitVerisi) {
    setIslenen(gorev.id)
    setHata(null)
    try {
      const o = await api.haftalikGorevTamamla(gorev.id, yanitVerisi)
      setOzet(o)
      yayinla(o)
      if (gorev.tur === 'yansitma') setAcikYansitma(false)
    } catch (e) {
      setHata(e.detail || 'Görev kaydedilemedi.')
    } finally {
      setIslenen(null)
    }
  }

  if (!ozet) {
    return hata
      ? <div className="card"><div className="auth-error" style={{ margin: 0 }}>{hata}</div></div>
      : <div className="card"><div className="bos-durum" style={{ padding: 12 }}>Haftalık görevler hazırlanıyor…</div></div>
  }

  const { seri, seviye } = ozet
  const hepsiBitti = ozet.tamamlanan === ozet.toplam
  const kalanMetni = ozet.kalan_gun === 0 ? 'Bugün haftanın son günü' : `Haftanın bitmesine ${ozet.kalan_gun} gün`
  const seriyeKalan = Math.max(0, ozet.seri_esigi - ozet.tamamlanan)

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      {/* başlık satırı */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div className="ct" style={{ marginBottom: 2 }}>Bu Haftanın Görevleri</div>
          <div style={{ fontSize: 12, color: 'var(--tx3)' }}>
            {kisaTarih(ozet.hafta_baslangic)} – {kisaTarih(ozet.hafta_bitis)} · {kalanMetni}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <div title={`En uzun serin: ${seri.en_uzun} hafta`} style={{ background: seri.guncel > 0 ? 'var(--aml)' : 'var(--sur2)', color: seri.guncel > 0 ? 'var(--am)' : 'var(--tx3)', borderRadius: 12, padding: '6px 12px', fontSize: 12.5, fontWeight: 700 }}>
            🔥 {seri.guncel} haftalık seri
          </div>
          <div title={`${seviye.puan} puan`} style={{ background: 'var(--grl)', color: 'var(--gr)', borderRadius: 12, padding: '6px 12px', fontSize: 12.5, fontWeight: 700 }}>
            {seviye.ikon} {seviye.ad} · Seviye {seviye.no}
          </div>
        </div>
      </div>

      {/* ilerleme */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '14px 0 6px' }}>
        <div className="mini-ilerleme-track" style={{ flex: 1 }}>
          <div className="mini-ilerleme-fill" style={{ width: `${(ozet.tamamlanan / ozet.toplam) * 100}%`, background: hepsiBitti ? 'var(--gr)' : 'var(--pu)', transition: 'width .4s' }} />
        </div>
        <div style={{ fontSize: 12.5, fontWeight: 700, color: hepsiBitti ? 'var(--gr)' : 'var(--pu)' }}>{ozet.tamamlanan}/{ozet.toplam}</div>
      </div>
      <div style={{ fontSize: 11.5, color: 'var(--tx3)', marginBottom: 12 }}>
        {hepsiBitti
          ? '🎉 Bu haftanın tüm görevleri tamam! Yeni görevlerin Pazartesi açılacak.'
          : seriyeKalan > 0
            ? `Serini sürdürmek için bu hafta ${seriyeKalan} görev daha tamamla.`
            : 'Bu hafta serin güvende ✓ Kalanı da bitirirsen daha hızlı büyürsün.'}
      </div>

      {hata && <div className="auth-error" style={{ marginBottom: 10 }}>{hata}</div>}

      {/* görevler */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {ozet.gorevler.map((g) => {
          const bitti = g.durum === 'tamamlandi'
          const yukleniyor = islenen === g.id
          return (
            <div key={g.id} style={{ border: '1px solid var(--bor)', borderRadius: 14, padding: '12px 14px', background: bitti ? 'var(--grl)' : 'var(--sur)', opacity: bitti ? 0.92 : 1 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ width: 28, height: 28, borderRadius: '50%', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: bitti ? 14 : 15, background: bitti ? 'var(--gr)' : 'var(--sur2)', color: '#fff' }}>
                  {bitti ? '✓' : TUR_IKON[g.tur]}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 10.5, fontWeight: 700, color: 'var(--tx3)', textTransform: 'uppercase', letterSpacing: '.04em' }}>{TUR_ETIKET[g.tur]}</div>
                  <div style={{ fontSize: 14, fontWeight: 700, marginTop: 1, textDecoration: bitti ? 'line-through' : 'none', textDecorationColor: 'var(--gr)' }}>{g.baslik}</div>
                  {g.aciklama && <div style={{ fontSize: 12.5, color: 'var(--tx2)', marginTop: 3, lineHeight: 1.5 }}>{g.aciklama}</div>}
                  {bitti && g.tur === 'yansitma' && g.yanit?.hedef && (
                    <div style={{ fontSize: 12, color: 'var(--gr)', marginTop: 6, fontStyle: 'italic' }}>Gelecek hafta hedefin: “{g.yanit.hedef}”</div>
                  )}
                </div>
                {!bitti && (
                  <div style={{ display: 'flex', gap: 6, flexShrink: 0, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    {g.link && (
                      <button className={`btn${g.tur === 'plan_adimi' ? ' sec' : ''}`} style={{ padding: '6px 12px', fontSize: 12.5 }} onClick={() => navigate(g.link)}>
                        {GIT_METNI[g.tur] || 'Git →'}
                      </button>
                    )}
                    {g.tur === 'plan_adimi' && (
                      <button className="btn" style={{ padding: '6px 12px', fontSize: 12.5 }} disabled={yukleniyor} onClick={() => tamamla(g)}>
                        {yukleniyor ? <span className="spin" /> : 'Yaptım ✓'}
                      </button>
                    )}
                    {g.tur === 'yansitma' && (
                      <button className="btn" style={{ padding: '6px 12px', fontSize: 12.5 }} onClick={() => setAcikYansitma((v) => !v)}>
                        {acikYansitma ? 'Kapat' : 'Cevapla'}
                      </button>
                    )}
                  </div>
                )}
              </div>

              {g.tur === 'yansitma' && !bitti && acikYansitma && (
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--bor)' }}>
                  {ozet.yansitma_sorulari.map((s) => (
                    <div key={s.anahtar} style={{ marginBottom: 10 }}>
                      <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 4 }}>{s.soru}</div>
                      <textarea
                        className="auth-input"
                        rows={2}
                        maxLength={600}
                        style={{ width: '100%', resize: 'vertical', fontFamily: 'inherit', fontSize: 13 }}
                        value={yanit[s.anahtar] || ''}
                        onChange={(e) => setYanit({ ...yanit, [s.anahtar]: e.target.value })}
                        placeholder="Kısaca yaz…"
                      />
                    </div>
                  ))}
                  <button
                    className="btn full"
                    disabled={yukleniyor || ozet.yansitma_sorulari.some((s) => (yanit[s.anahtar] || '').trim().length < 3)}
                    onClick={() => tamamla(g, yanit)}
                  >
                    {yukleniyor ? <span className="spin" /> : 'Kaydet ve Tamamla ✓'}
                  </button>
                  <div style={{ fontSize: 11, color: 'var(--tx3)', marginTop: 6 }}>Cevapların yalnızca sana görünür.</div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* [2026-10-04] Filiz'e bağlantı: haftanın planını sohbetle konuşmak için */}
      <button
        className="filiz-oneri"
        style={{ marginTop: 10, width: '100%', textAlign: 'center', border: '1px dashed var(--pu)', color: 'var(--pu)', fontWeight: 700 }}
        onClick={() => window.dispatchEvent(new CustomEvent('filiz-ac', { detail: { mesaj: 'Bu hafta neye odaklanmalıyım?' } }))}
      >
        💬 Bu hafta neye odaklanmalıyım? Filiz'e sor
      </button>

      {/* son 8 hafta + seviye */}
      <div style={{ display: 'flex', gap: 20, marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--bor)', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: '1 1 220px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--tx3)', marginBottom: 6 }}>SON 8 HAFTA</div>
          <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end', height: 44 }}>
            {ozet.gecmis.map((h, i) => {
              const buHafta = i === ozet.gecmis.length - 1
              const oran = h.toplam ? h.tamamlanan / h.toplam : 0
              return (
                <div key={h.hafta_baslangic} title={`${kisaTarih(h.hafta_baslangic)} haftası: ${h.tamamlanan}/${h.toplam || 3}`} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
                  <div style={{ width: '100%', maxWidth: 22, height: 30, background: 'var(--sur2)', borderRadius: 6, display: 'flex', alignItems: 'flex-end', overflow: 'hidden', outline: buHafta ? '2px solid var(--pu)' : 'none', outlineOffset: 1 }}>
                    <div style={{ width: '100%', height: `${Math.max(oran * 100, h.tamamlanan ? 12 : 0)}%`, background: h.seriye_sayildi ? 'var(--gr)' : 'var(--am)', transition: 'height .4s' }} />
                  </div>
                  <div style={{ fontSize: 9, color: buHafta ? 'var(--pu)' : 'var(--tx3)', fontWeight: buHafta ? 700 : 500 }}>{kisaTarih(h.hafta_baslangic)}</div>
                </div>
              )
            })}
          </div>
        </div>
        <div style={{ flex: '1 1 200px' }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--tx3)', marginBottom: 6 }}>FİLİZ'İN BÜYÜMESİ</div>
          <div className="mini-ilerleme-track" style={{ width: '100%' }}><div className="mini-ilerleme-fill" style={{ width: `${seviye.ilerleme_yuzde}%`, background: 'var(--gr)', transition: 'width .4s' }} /></div>
          <div style={{ fontSize: 11.5, color: 'var(--tx2)', marginTop: 5 }}>
            {seviye.sonraki_ad
              ? <>{seviye.puan} puan · <b>{seviye.sonraki_ad}</b> olmana {seviye.sonraki_esik - seviye.puan} puan kaldı</>
              : <>{seviye.puan} puan · en yüksek seviyedesin 🏆</>}
          </div>
          <div style={{ fontSize: 10.5, color: 'var(--tx3)', marginTop: 2 }}>Görev +10 · Yol haritası adımı +5 · Katman +15</div>
        </div>
      </div>
    </div>
  )
}
