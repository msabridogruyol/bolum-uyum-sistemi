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
  const [gecmisAcik, setGecmisAcik] = useState(false)
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
  const kalanMetni = ozet.kalan_gun === 0 ? 'bugün son gün' : `${ozet.kalan_gun} gün kaldı`
  const seriyeKalan = Math.max(0, ozet.seri_esigi - ozet.tamamlanan)
  const oran = ozet.toplam ? ozet.tamamlanan / ozet.toplam : 0
  const R = 30, CEVRE = 2 * Math.PI * R
  const yansitma = ozet.gorevler.find((g) => g.tur === 'yansitma' && g.durum !== 'tamamlandi')

  // [2026-10-09] Sadeleştirildi: solda ilerleme halkası + özet, sağda 3 görev yan yana küçük kart.
  // Açıklamalar kartın üzerine gelince görünür; geçmiş 8 hafta ve büyüme bilgisi "Gelişimini gör" ile açılır.
  return (
    <div className="card hg-kart" style={{ marginBottom: 20 }}>
      <div className="hg-duzen">
        <div className="hg-ozet">
          <div className="hg-halka" title={`${ozet.tamamlanan}/${ozet.toplam} görev tamam`}>
            <svg viewBox="0 0 72 72" width="72" height="72" aria-hidden="true">
              <circle cx="36" cy="36" r={R} fill="none" stroke="var(--sur2)" strokeWidth="7" />
              <circle cx="36" cy="36" r={R} fill="none" stroke={hepsiBitti ? 'var(--gr)' : 'var(--pu)'} strokeWidth="7" strokeLinecap="round"
                strokeDasharray={CEVRE} strokeDashoffset={CEVRE * (1 - oran)} transform="rotate(-90 36 36)" className="hg-halka-dolu" />
            </svg>
            <div className="hg-halka-ic"><b>{ozet.tamamlanan}</b><span>/{ozet.toplam}</span></div>
          </div>
          <div style={{ minWidth: 0 }}>
            <div className="ct" style={{ marginBottom: 2 }}>Bu hafta</div>
            <div className="hg-alt">{kisaTarih(ozet.hafta_baslangic)} – {kisaTarih(ozet.hafta_bitis)} · {kalanMetni}</div>
            <div className="hg-rozetler">
              <span title={`En uzun serin: ${seri.en_uzun} hafta`} className={seri.guncel > 0 ? 'hg-rozet hg-ates' : 'hg-rozet'}>🔥 {seri.guncel} hafta seri</span>
              <span title={`${seviye.puan} puan`} className="hg-rozet hg-filiz">{seviye.ikon} Seviye {seviye.no}</span>
            </div>
            <div className="hg-durum">
              {hepsiBitti ? '🎉 Hepsi tamam! Yenileri Pazartesi.' : seriyeKalan > 0 ? `Seri için ${seriyeKalan} görev daha.` : 'Serin güvende ✓'}
            </div>
          </div>
        </div>

        <div className="hg-gorevler">
          {ozet.gorevler.map((g) => {
            const bitti = g.durum === 'tamamlandi'
            const yukleniyor = islenen === g.id
            const git = !bitti && g.link && g.tur !== 'plan_adimi' ? () => navigate(g.link) : null
            return (
              <div key={g.id} className={`hg-gorev${bitti ? ' bitti' : ''}${git ? ' tik' : ''}`} title={g.aciklama || ''}
                onClick={git || undefined} role={git ? 'button' : undefined} tabIndex={git ? 0 : undefined}
                onKeyDown={git ? (e) => { if (e.key === 'Enter') git() } : undefined}>
                <div className="hg-gorev-ust">
                  <span className="hg-ikon">{bitti ? '✓' : TUR_IKON[g.tur]}</span>
                  <span className="hg-tur">{TUR_ETIKET[g.tur]}</span>
                </div>
                <div className="hg-baslik">{g.baslik}</div>
                {bitti && g.tur === 'yansitma' && g.yanit?.hedef && <div className="hg-not">Hedefin: “{g.yanit.hedef}”</div>}
                {!bitti && (
                  <div className="hg-eylem">
                    {git && <span className="hg-git">{GIT_METNI[g.tur] || 'Git →'}</span>}
                    {g.tur === 'plan_adimi' && (
                      <>
                        {g.link && <button className="hg-mini" onClick={() => navigate(g.link)}>Planda aç</button>}
                        <button className="hg-mini hg-mini-ana" disabled={yukleniyor} onClick={() => tamamla(g)}>{yukleniyor ? <span className="spin" /> : 'Yaptım ✓'}</button>
                      </>
                    )}
                    {g.tur === 'yansitma' && (
                      <button className="hg-mini hg-mini-ana" onClick={() => setAcikYansitma((v) => !v)}>{acikYansitma ? 'Kapat' : 'Cevapla'}</button>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {hata && <div className="auth-error" style={{ margin: '12px 0 0' }}>{hata}</div>}

      {yansitma && acikYansitma && (
        <div className="hg-yansitma">
          {ozet.yansitma_sorulari.map((s) => (
            <div key={s.anahtar} style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 4 }}>{s.soru}</div>
              <textarea className="auth-input" rows={2} maxLength={600}
                style={{ width: '100%', resize: 'vertical', fontFamily: 'inherit', fontSize: 13 }}
                value={yanit[s.anahtar] || ''} onChange={(e) => setYanit({ ...yanit, [s.anahtar]: e.target.value })} placeholder="Kısaca yaz…" />
            </div>
          ))}
          <button className="btn full" disabled={islenen === yansitma.id || ozet.yansitma_sorulari.some((s) => (yanit[s.anahtar] || '').trim().length < 3)}
            onClick={() => tamamla(yansitma, yanit)}>
            {islenen === yansitma.id ? <span className="spin" /> : 'Kaydet ve Tamamla ✓'}
          </button>
          <div style={{ fontSize: 11, color: 'var(--tx3)', marginTop: 6 }}>Cevapların yalnızca sana görünür.</div>
        </div>
      )}

      <div className="hg-alt-satir">
        <button className="hg-link" onClick={() => setGecmisAcik((v) => !v)}>{gecmisAcik ? '▴ Gizle' : '▾ Gelişimini gör'}</button>
        <button className="hg-link" onClick={() => window.dispatchEvent(new CustomEvent('filiz-ac', { detail: { mesaj: 'Bu hafta neye odaklanmalıyım?' } }))}>
          💬 Bu hafta neye odaklanmalıyım? Filiz'e sor
        </button>
      </div>

      {gecmisAcik && (
        <div className="hg-gecmis">
          <div style={{ flex: '1 1 220px' }}>
            <div className="hg-baslik-kucuk">SON 8 HAFTA</div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'flex-end', height: 44 }}>
              {ozet.gecmis.map((h, i) => {
                const buHafta = i === ozet.gecmis.length - 1
                const o = h.toplam ? h.tamamlanan / h.toplam : 0
                return (
                  <div key={h.hafta_baslangic} title={`${kisaTarih(h.hafta_baslangic)} haftası: ${h.tamamlanan}/${h.toplam || 3}`} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
                    <div style={{ width: '100%', maxWidth: 22, height: 30, background: 'var(--sur2)', borderRadius: 6, display: 'flex', alignItems: 'flex-end', overflow: 'hidden', outline: buHafta ? '2px solid var(--pu)' : 'none', outlineOffset: 1 }}>
                      <div style={{ width: '100%', height: `${Math.max(o * 100, h.tamamlanan ? 12 : 0)}%`, background: h.seriye_sayildi ? 'var(--gr)' : 'var(--am)', transition: 'height .4s' }} />
                    </div>
                    <div style={{ fontSize: 9, color: buHafta ? 'var(--pu)' : 'var(--tx3)', fontWeight: buHafta ? 700 : 500 }}>{kisaTarih(h.hafta_baslangic)}</div>
                  </div>
                )
              })}
            </div>
          </div>
          <div style={{ flex: '1 1 200px' }}>
            <div className="hg-baslik-kucuk">FİLİZ'İN BÜYÜMESİ</div>
            <div className="mini-ilerleme-track" style={{ width: '100%' }}><div className="mini-ilerleme-fill" style={{ width: `${seviye.ilerleme_yuzde}%`, background: 'var(--gr)' }} /></div>
            <div style={{ fontSize: 11.5, color: 'var(--tx2)', marginTop: 5 }}>
              {seviye.sonraki_ad
                ? <>{seviye.puan} puan · <b>{seviye.sonraki_ad}</b> olmana {seviye.sonraki_esik - seviye.puan} puan kaldı</>
                : <>{seviye.puan} puan · en yüksek seviyedesin 🏆</>}
            </div>
            <div style={{ fontSize: 10.5, color: 'var(--tx3)', marginTop: 2 }}>Görev +10 · Yol haritası adımı +5 · Katman +15</div>
          </div>
        </div>
      )}
    </div>
  )
}
