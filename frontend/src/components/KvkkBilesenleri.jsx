import { useEffect, useState } from 'react'
import { api } from '../api/client'

// [2026-10-04] KVKK: aydınlatma metni penceresi, onay kutuları ve eski hesaplar için zorunlu onay penceresi.

const ORTU = {
  position: 'fixed', inset: 0, background: 'rgba(20, 16, 10, 0.55)', zIndex: 1100,
  display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
}

export function AydinlatmaMetniPenceresi({ metin, onKapat }) {
  return (
    <div style={ORTU} onClick={onKapat}>
      <div className="card" onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: 640, width: '100%', maxHeight: '85vh', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', boxShadow: '0 20px 60px rgba(0,0,0,.25)' }}>
        <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--bor)', fontWeight: 700, fontSize: 15 }}>Aydınlatma Metni</div>
        <div style={{ padding: '16px 22px', overflowY: 'auto', whiteSpace: 'pre-wrap', fontSize: 12.8, lineHeight: 1.65, color: 'var(--tx2)' }}>
          {metin || 'Yükleniyor…'}
        </div>
        <div style={{ padding: '12px 22px', borderTop: '1px solid var(--bor)', textAlign: 'right' }}>
          <button className="btn" type="button" onClick={onKapat}>Okudum, kapat</button>
        </div>
      </div>
    </div>
  )
}

/** Onay kutuları. maddeler: [{kod, metin, aciklama, zorunlu}] — onaylar: {kod: bool} */
export function KvkkOnayKutulari({ maddeler, onaylar, setOnaylar, metniAc, sadeceIstegeBagli = false }) {
  const liste = sadeceIstegeBagli ? maddeler.filter((m) => !m.zorunlu) : maddeler
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {liste.map((m) => (
        <label key={m.kod} style={{ display: 'flex', gap: 9, alignItems: 'flex-start', cursor: 'pointer', fontSize: 12, lineHeight: 1.5, color: 'var(--tx2)' }}>
          <input type="checkbox" checked={!!onaylar[m.kod]} style={{ marginTop: 2, width: 16, height: 16, flexShrink: 0, accentColor: 'var(--pu)' }}
            onChange={(e) => setOnaylar({ ...onaylar, [m.kod]: e.target.checked })} />
          <span>
            {m.kod === 'aydinlatma' && metniAc ? (
              <>
                <button type="button" className="auth-link" style={{ padding: 0 }} onClick={(e) => { e.preventDefault(); metniAc() }}>Aydınlatma metnini</button>
                {' '}okudum ve anladım.
              </>
            ) : m.metin}
            {m.zorunlu ? <b style={{ color: 'var(--re)' }}> *</b> : <span style={{ color: 'var(--tx3)' }}> (isteğe bağlı)</span>}
            {!m.zorunlu && <span style={{ display: 'block', fontSize: 11, color: 'var(--tx3)' }}>{m.aciklama}</span>}
          </span>
        </label>
      ))}
    </div>
  )
}

export function zorunlularTamamMi(maddeler, onaylar) {
  return maddeler.filter((m) => m.zorunlu).every((m) => onaylar[m.kod] === true)
}

export function useKvkkMetinleri() {
  const [veri, setVeri] = useState(null)
  useEffect(() => {
    let iptal = false
    api.kvkkMetinleri().then((v) => { if (!iptal) setVeri(v) }).catch(() => {})
    return () => { iptal = true }
  }, [])
  return veri
}

/**
 * Eski hesaplar veya metin sürümü değiştiğinde ana sayfada çıkan, kapatılamayan onay penceresi.
 * onTamam(): onaylar kaydedildi.  onCikis(): öğrenci onay vermeden çıkmak istedi.
 */
export function KvkkOnayPenceresi({ onTamam, onCikis }) {
  const metinler = useKvkkMetinleri()
  const [onaylar, setOnaylar] = useState({})
  const [metinAcik, setMetinAcik] = useState(false)
  const [hata, setHata] = useState(null)
  const [kaydediliyor, setKaydediliyor] = useState(false)

  useEffect(() => {
    // mevcut isteğe bağlı tercihlerini koru
    api.kvkkDurumu().then((d) => setOnaylar((o) => ({ ...d.onaylar, ...o }))).catch(() => {})
  }, [])

  if (!metinler) return null
  const tamam = zorunlularTamamMi(metinler.maddeler, onaylar)

  async function kaydet() {
    setHata(null); setKaydediliyor(true)
    try {
      await api.kvkkGuncelle(onaylar)
      onTamam?.()
    } catch (e) {
      setHata(e?.detail || 'Kaydedilemedi, tekrar dene.')
    } finally {
      setKaydediliyor(false)
    }
  }

  return (
    <div style={ORTU}>
      <div className="card" style={{ maxWidth: 520, width: '100%', maxHeight: '90vh', overflowY: 'auto', margin: 0, padding: 26, boxShadow: '0 20px 60px rgba(0,0,0,.25)' }}>
        <div style={{ fontSize: 34, textAlign: 'center', marginBottom: 6 }}>🔒</div>
        <div style={{ fontSize: 18, fontWeight: 700, textAlign: 'center', marginBottom: 8 }}>Kişisel verilerin ve izinlerin</div>
        <div style={{ fontSize: 13, color: 'var(--tx2)', lineHeight: 1.6, textAlign: 'center', marginBottom: 16 }}>
          Devam etmeden önce verilerinin nasıl kullanıldığını onaylaman gerekiyor. İsteğe bağlı izinleri sonra Ayarlar'dan değiştirebilirsin.
        </div>
        {hata && <div className="auth-error">{hata}</div>}
        <KvkkOnayKutulari maddeler={metinler.maddeler} onaylar={onaylar} setOnaylar={setOnaylar} metniAc={() => setMetinAcik(true)} />
        <button className="btn full" style={{ marginTop: 18 }} type="button" disabled={!tamam || kaydediliyor} onClick={kaydet}>
          {kaydediliyor ? <span className="spin" /> : 'Onayla ve devam et'}
        </button>
        {onCikis && (
          <div className="auth-foot"><button type="button" className="auth-link" onClick={onCikis}>Onaylamadan çıkış yap</button></div>
        )}
      </div>
      {metinAcik && <AydinlatmaMetniPenceresi metin={metinler.aydinlatma_metni} onKapat={() => setMetinAcik(false)} />}
    </div>
  )
}

/** Ayarlar sayfası: "Gizlilik ve İzinler" kartı — isteğe bağlı izinler anında kaydedilir. */
export function GizlilikKarti() {
  const metinler = useKvkkMetinleri()
  const [durum, setDurum] = useState(null)
  const [metinAcik, setMetinAcik] = useState(false)
  const [mesaj, setMesaj] = useState(null)

  useEffect(() => { api.kvkkDurumu().then(setDurum).catch(() => {}) }, [])
  if (!metinler || !durum) return null

  async function degistir(yeni) {
    const degisen = Object.fromEntries(Object.entries(yeni).filter(([k, v]) => durum.onaylar[k] !== v))
    if (!Object.keys(degisen).length) return
    setMesaj(null)
    try {
      setDurum(await api.kvkkGuncelle(degisen))
      setMesaj({ tip: 'ok', metin: 'Tercihin kaydedildi.' })
    } catch (e) {
      setMesaj({ tip: 'hata', metin: e?.detail || 'Kaydedilemedi.' })
    }
  }

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <div className="ct">Gizlilik ve İzinler</div>
      <div className="ps" style={{ margin: '0 0 12px', fontSize: 12 }}>
        Zorunlu onayların verildi ({durum.surum}).{' '}
        <button type="button" className="auth-link" style={{ padding: 0 }} onClick={() => setMetinAcik(true)}>Aydınlatma metnini oku</button>
      </div>
      {mesaj && (
        <div className="auth-error" style={mesaj.tip === 'ok' ? { background: 'var(--grl)', color: 'var(--gr)' } : undefined}>{mesaj.metin}</div>
      )}
      <KvkkOnayKutulari maddeler={metinler.maddeler} onaylar={durum.onaylar} setOnaylar={degistir} sadeceIstegeBagli />
      <div className="ps" style={{ marginTop: 12, fontSize: 11.5, color: 'var(--tx3)' }}>
        Zorunlu onaylarını geri çekmek veya hesabını sildirmek istersen aydınlatma metnindeki adrese başvurabilirsin.
      </div>
      {metinAcik && <AydinlatmaMetniPenceresi metin={metinler.aydinlatma_metni} onKapat={() => setMetinAcik(false)} />}
    </div>
  )
}
