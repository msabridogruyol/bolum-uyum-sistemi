// [2026-10-11] Süper admin → Sistem → Hata Kayıtları: sunucu ve tarayıcı hataları, parmak izine göre gruplu.
import { useCallback, useEffect, useState } from 'react'
import { hataKayitlariApi } from '../../api/hataKayitlari'

const KULLANICI = { ogrenci: 'Öğrenci', okul_yetkilisi: 'Okul yetkilisi', super_admin: 'Süper admin', anonim: 'Oturumsuz' }

function zaman(z) {
  return z ? new Date(z).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }) : '—'
}

function Etiket({ renk, children }) {
  return (
    <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 999,
      background: `var(--${renk}l)`, color: `var(--${renk})`, whiteSpace: 'nowrap' }}>{children}</span>
  )
}

function Ayrinti({ id, kapat, degisti }) {
  const [k, setK] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => { hataKayitlariApi.ayrinti(id).then(setK).catch((e) => setHata(e.detail || 'Ayrıntı yüklenemedi.')) }, [id])
  const isaretle = async (c) => {
    try { await hataKayitlariApi.cozuldu(id, c); degisti(); kapat() } catch (e) { setHata(e.detail || 'Kaydedilemedi.') }
  }
  return (
    <div className="card" style={{ borderColor: 'var(--pum)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'start', flexWrap: 'wrap' }}>
        <div className="ct" style={{ marginBottom: 6 }}>Hata ayrıntısı #{id}</div>
        <button className="yp-mini" onClick={kapat}>Kapat ✕</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!k && !hata && <div className="yp-ince">Yükleniyor…</div>}
      {k && (
        <>
          <div className="lt" style={{ wordBreak: 'break-word' }}>{k.istisna_turu}</div>
          <div className="ld" style={{ wordBreak: 'break-word', marginBottom: 10 }}>{k.mesaj || '—'}</div>
          <div className="yp-ince" style={{ display: 'grid', gap: 3, marginBottom: 10 }}>
            <div>Kaynak: <b>{k.kaynak === 'istemci' ? 'Tarayıcı' : 'Sunucu'}</b> · {k.metod ? `${k.metod} ` : ''}{k.yol || '—'}{k.durum_kodu ? ` → ${k.durum_kodu}` : ''}</div>
            <div>Görülme: <b>{k.sayi}</b> kez · ilk {zaman(k.ilk_gorulme)} · son {zaman(k.son_gorulme)}</div>
            <div>Son kullanıcı tipi: {KULLANICI[k.kullanici_tipi] || k.kullanici_tipi || '—'} · son istek kimliği: <code>{k.istek_kimligi || '—'}</code></div>
            {k.tarayici && <div style={{ wordBreak: 'break-word' }}>Tarayıcı: {k.tarayici}</div>}
            {k.cozuldu_mu && <div>Çözüldü: {zaman(k.cozulme_zamani)}{k.cozen ? ` · ${k.cozen}` : ''}</div>}
          </div>
          <div className="ct" style={{ marginBottom: 6 }}>Yığın izi (kişisel veriler maskelendi)</div>
          <pre style={{ maxHeight: 340, overflow: 'auto', background: 'var(--sur2)', border: '1px solid var(--bor)', borderRadius: 10,
            padding: 10, fontSize: 11.5, lineHeight: 1.45, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{k.yigin_izi || '—'}</pre>
          {Array.isArray(k.son_istekler) && k.son_istekler.length > 0 && (
            <details style={{ marginTop: 8 }}>
              <summary className="yp-ince" style={{ cursor: 'pointer' }}>Son {k.son_istekler.length} tekrar (istek kimliği · yol · zaman)</summary>
              <div className="yp-ince" style={{ display: 'grid', gap: 2, marginTop: 6 }}>
                {k.son_istekler.map((s, i) => <div key={i}><code>{s.k || '—'}</code> · {s.y || '—'} · {zaman(s.z)}</div>)}
              </div>
            </details>
          )}
          <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
            {k.cozuldu_mu
              ? <button className="btn sec" onClick={() => isaretle(false)}>Yeniden aç</button>
              : <button className="btn" onClick={() => isaretle(true)}>✓ Çözüldü olarak işaretle</button>}
          </div>
        </>
      )}
    </div>
  )
}

export default function HataKayitlariSayfasi() {
  const [f, setF] = useState({ durum: 'acik', kaynak: '', ara: '' })
  const [veri, setVeri] = useState(null)
  const [hata, setHata] = useState(null)
  const [secili, setSecili] = useState(null)
  const [mesaj, setMesaj] = useState(null)

  const yukle = useCallback(() => {
    setHata(null)
    hataKayitlariApi.listele(f).then(setVeri).catch((e) => setHata(e.detail || 'Hata kayıtları yüklenemedi.'))
  }, [f])
  useEffect(() => { const t = setTimeout(yukle, f.ara ? 300 : 0); return () => clearTimeout(t) }, [yukle, f.ara])

  const temizle = async (kapsam) => {
    const metin = { cozulenler: 'Çözüldü işaretli tüm gruplar silinsin mi?', eski: '30 günden uzun süredir görülmeyen gruplar silinsin mi?',
      hepsi: 'TÜM hata kayıtları kalıcı olarak silinsin mi?' }[kapsam]
    if (!window.confirm(metin)) return
    try {
      const r = await hataKayitlariApi.temizle(kapsam)
      setMesaj(`${r.silinen} grup silindi.`)
      setSecili(null)
      yukle()
    } catch (e) { setHata(e.detail || 'Silinemedi.') }
  }

  const o = veri?.ozet
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Hata Kayıtları</div>
        <div className="ps">
          Sunucuda yakalanmamış hatalar ve kullanıcıların tarayıcısında oluşan hatalar — aynı hata tek satırda, tekrar sayısıyla.
          E-posta, telefon, TC kimlik no, şifre ve tokenler kayda girmeden maskelenir. Yeni bir hata türünde süper adminlere günde en çok bir bildirim gider.
          Kullanıcı size bir hata kodu iletirse arama kutusuna yapıştırın.
        </div>
      </div>

      {o && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10, marginBottom: 14 }}>
          {[['Açık grup', o.acik, o.acik ? 're' : 'gr'], ['Açık tekrar', o.acik_tekrar, 'am'], ['Son 24 saatte görülen', o.son_24_saat, 'am'],
            ['Son 24 saatte yeni', o.yeni_24_saat, o.yeni_24_saat ? 're' : 'gr'], ['Çözüldü', o.cozuldu, 'gr']].map(([ad, n, r]) => (
            <div key={ad} className="card" style={{ marginBottom: 0, padding: '14px 16px' }}>
              <div className="yp-ince">{ad}</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: `var(--${r})` }}>{n ?? 0}</div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 12 }}>
        <select className="yp-sec" value={f.durum} onChange={(e) => setF({ ...f, durum: e.target.value })}>
          <option value="acik">Açık</option><option value="cozuldu">Çözüldü</option><option value="hepsi">Hepsi</option>
        </select>
        <select className="yp-sec" value={f.kaynak} onChange={(e) => setF({ ...f, kaynak: e.target.value })}>
          <option value="">Sunucu + tarayıcı</option><option value="sunucu">Sunucu</option><option value="istemci">Tarayıcı</option>
        </select>
        <input className="auth-input" style={{ flex: '1 1 220px', width: 'auto', padding: '7px 11px' }} placeholder="Ara: hata türü, mesaj, yol ya da hata kodu"
          value={f.ara} onChange={(e) => setF({ ...f, ara: e.target.value })} />
        <button className="yp-mini" onClick={yukle}>↻ Yenile</button>
        <span style={{ flex: 1 }} />
        <button className="yp-mini" onClick={() => temizle('cozulenler')}>Çözülenleri sil</button>
        <button className="yp-mini" onClick={() => temizle('eski')}>30 günden eskileri sil</button>
        <button className="yp-mini yp-tehlike" onClick={() => temizle('hepsi')}>Tümünü sil</button>
      </div>

      {mesaj && <div className="yp-ince" style={{ marginBottom: 8 }}>{mesaj}</div>}
      {hata && <div className="auth-error">{hata}</div>}
      {secili && <Ayrinti key={secili} id={secili} kapat={() => setSecili(null)} degisti={yukle} />}

      {!veri && !hata && <div className="bos-durum">Yükleniyor…</div>}
      {veri && (
        <div className="ll">
          {veri.gruplar.map((g) => (
            <div key={g.id} className="lc" onClick={() => setSecili(g.id)} style={{ alignItems: 'flex-start', opacity: g.cozuldu_mu ? 0.7 : 1 }}>
              <div style={{ minWidth: 54, textAlign: 'center' }}>
                <div style={{ fontSize: 18, fontWeight: 800, color: g.cozuldu_mu ? 'var(--tx3)' : 'var(--re)' }}>{g.sayi}</div>
                <div className="yp-ince">kez</div>
              </div>
              <div className="lb-wrap" style={{ minWidth: 0, flex: 1 }}>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center', marginBottom: 2 }}>
                  <Etiket renk={g.kaynak === 'istemci' ? 'am' : 're'}>{g.kaynak === 'istemci' ? 'Tarayıcı' : 'Sunucu'}</Etiket>
                  {g.cozuldu_mu && <Etiket renk="gr">✓ Çözüldü</Etiket>}
                  <span className="lt" style={{ wordBreak: 'break-word' }}>{g.istisna_turu}</span>
                </div>
                <div className="ld" style={{ wordBreak: 'break-word' }}>{g.mesaj || '—'}</div>
                <div className="yp-ince" style={{ marginTop: 3 }}>
                  {g.metod ? `${g.metod} ` : ''}{g.yol_kalibi || g.yol || '—'} · son {zaman(g.son_gorulme)} · ilk {zaman(g.ilk_gorulme)}
                  {g.kullanici_tipi ? ` · ${KULLANICI[g.kullanici_tipi] || g.kullanici_tipi}` : ''}
                </div>
              </div>
            </div>
          ))}
          {veri.gruplar.length === 0 && (
            <div className="bos-durum">{f.durum === 'acik' && !f.ara ? 'Açık hata yok. 🎉' : 'Bu filtreye uyan kayıt yok.'}</div>
          )}
        </div>
      )}
    </div>
  )
}
