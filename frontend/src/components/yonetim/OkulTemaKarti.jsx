// [2026-10-09] Okul rengi seçimi (Okul Paneli → Görünüm). Okul yetkilisi ve süper admin değiştirebilir.
// Renk; sol menü ayırıcısı, sayfa başlığı çizgisi, aktif menü işareti ve kartların üst çizgisinde kullanılır.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { OKUL_PALETI, gecerliRenk, okulRenginiUygula } from '../../tema'

const VARSAYILAN = '#E8804A'

function Onizleme({ renk }) {
  const c = renk || VARSAYILAN
  const yumusak = `color-mix(in srgb, ${c} 35%, transparent)`
  return (
    <div className="tm-onizleme" aria-hidden="true">
      <div className="tm-o-sb" style={{ borderRight: `3px solid ${c}` }}>
        <div className="tm-o-logo" style={{ borderBottom: `1.5px solid ${yumusak}` }}>Filizyol</div>
        <div className="tm-o-ni" style={{ borderLeft: `3px solid ${c}` }}>Ana Sayfa</div>
        <div className="tm-o-ni tm-o-pasif">Bölüm Uyumum</div>
        <div className="tm-o-ni tm-o-pasif">Keşfet</div>
      </div>
      <div className="tm-o-main">
        <div className="tm-o-baslik">Sayfa başlığı</div>
        <div className="tm-o-cizgi" style={{ background: c }} />
        <div className="tm-o-kart" style={{ borderTop: `2.5px solid ${yumusak}` }}><span /><span /></div>
        <div className="tm-o-kart" style={{ borderTop: `2.5px solid ${yumusak}` }}><span /><span /></div>
      </div>
    </div>
  )
}

export default function OkulTemaKarti({ okulId }) {
  const { rol, ben, benYenile } = useAdminAuth()
  const [kayitli, setKayitli] = useState(undefined)
  const [secim, setSecim] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [mesaj, setMesaj] = useState(null)

  useEffect(() => {
    api.okulBilgi(okulId).then((d) => { setKayitli(d.tema_renk || null); setSecim(d.tema_renk || null) })
      .catch((e) => setMesaj({ tur: 'hata', metin: e.detail || 'Okul rengi yüklenemedi.' }))
  }, [okulId])

  async function kaydet() {
    setBekle(true); setMesaj(null)
    try {
      const v = await api.okulTemaKaydet(okulId, secim)
      setKayitli(v.tema_renk || null)
      if (rol === 'okul_yetkilisi' && ben?.okul_id === okulId) { okulRenginiUygula(v.tema_renk); benYenile?.() }
      setMesaj({ tur: 'tamam', metin: 'Kaydedildi. Öğrenciler yeni rengi bir sonraki sayfa açılışında görür.' })
    } catch (e) {
      setMesaj({ tur: 'hata', metin: e.detail || 'Kaydedilemedi.' })
    } finally { setBekle(false) }
  }

  if (kayitli === undefined && !mesaj) return <div className="bos-durum">Yükleniyor…</div>
  const degisti = (secim || null) !== (kayitli || null)
  const ozel = secim && !OKUL_PALETI.some((p) => p.renk && p.renk.toLowerCase() === secim.toLowerCase())

  return (
    <div className="card tm-kart">
      <div className="tm-duzen">
        <div>
          <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--tx)' }}>Okul rengi</div>
          <div className="ps" style={{ marginTop: 4 }}>
            Seçtiğin renk; sol menüyü sayfadan ayıran çizgide, sayfa başlıklarının altındaki çizgide, açık olan menü işaretinde
            ve kartların üst çizgisinde kullanılır. Butonlar ve yazılar okunurluk için Filizyol renginde kalır.
          </div>

          <div className="tm-palet">
            {OKUL_PALETI.map((p) => {
              const aktif = (p.renk || null) === (secim || null) || (p.renk && secim && p.renk.toLowerCase() === secim.toLowerCase())
              return (
                <button key={p.ad} type="button" className={`tm-renk${aktif ? ' aktif' : ''}`} title={p.ad} onClick={() => setSecim(p.renk)}>
                  <span className="tm-renk-top" style={{ background: p.renk || VARSAYILAN }} />
                  <span className="tm-renk-ad">{p.ad}</span>
                </button>
              )
            })}
            <label className={`tm-renk${ozel ? ' aktif' : ''}`} title="Kendi rengini seç">
              <input type="color" value={gecerliRenk(secim) ? secim : '#1F3A93'} onChange={(e) => setSecim(e.target.value.toUpperCase())} />
              <span className="tm-renk-ad">{ozel ? secim : 'Özel renk…'}</span>
            </label>
          </div>

          {mesaj && <div className={mesaj.tur === 'hata' ? 'auth-error' : 'yp-uyari'} style={mesaj.tur === 'tamam' ? { background: 'var(--grl)', borderColor: 'var(--gr)' } : undefined}>{mesaj.metin}</div>}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button className="btn" disabled={bekle || !degisti} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Kaydet'}</button>
            {degisti && <button className="btn sec" disabled={bekle} onClick={() => setSecim(kayitli)}>Vazgeç</button>}
          </div>
        </div>
        <div>
          <div className="yp-ince" style={{ marginBottom: 6, fontWeight: 700 }}>Önizleme</div>
          <Onizleme renk={secim} />
        </div>
      </div>
    </div>
  )
}
