// [2026-10-09] Ayarlar → Hedef bölümüm. Hedef seçimi/değişikliği YALNIZCA buradan yapılır.
// İlk seçim serbest; sonra en fazla 3 değişiklik hakkı var. Hak bitince rehber öğretmen (okul yetkilisi) yardımcı olur.
import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import BolumAdi from './BolumAdi'

export default function HedefBolumAyari() {
  const [durum, setDurum] = useState(null)
  const [oneriler, setOneriler] = useState([])
  const [acik, setAcik] = useState(false)
  const [sorgu, setSorgu] = useState('')
  const [sonuclar, setSonuclar] = useState(null)
  const [onay, setOnay] = useState(null)        // {bolum_id, bolum_adi}
  const [hata, setHata] = useState(null)
  const [mesaj, setMesaj] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [params, setParams] = useSearchParams()
  const kutu = useRef(null)

  useEffect(() => {
    api.hedefDurumGetir().then(setDurum).catch(() => setDurum({ hedef: null, kalan_hak: 3, degisim_hakki: 3, degisim_sayisi: 0 }))
    api.siralamaGetir(6).then((l) => setOneriler(Array.isArray(l) ? l : [])).catch(() => {})
  }, [])

  // Keşfet / Koçluk sayfasından "?hedef=ID" ile gelinirse doğrudan onay adımı açılır
  useEffect(() => {
    if (!durum) return
    const id = Number(params.get('hedef'))
    if (id || window.location.hash === '#hedef') setTimeout(() => kutu.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150)
    if (id) {
      if (durum.hedef?.bolum_id !== id) {
        api.bolumBilgi(id).then((b) => sec({ bolum_id: id, bolum_adi: b.ad })).catch(() => {})
      }
      params.delete('hedef'); setParams(params, { replace: true })
    }
  }, [durum]) // eslint-disable-line react-hooks/exhaustive-deps

  const hedef = durum?.hedef
  const hakBitti = hedef && durum.kalan_hak <= 0

  function sec(b) {
    setHata(null); setMesaj(null)
    if (hedef && hedef.bolum_id === b.bolum_id) return
    setOnay(b)
  }

  async function onayla() {
    setBekle(true); setHata(null)
    try {
      await api.hedefSec(onay.bolum_id, true)
      const yeni = await api.hedefDurumGetir()
      setDurum(yeni)
      setMesaj(hedef ? `Hedefin ${onay.bolum_adi} oldu. Kalan değiştirme hakkın: ${yeni.kalan_hak}.` : `Hedefin ${onay.bolum_adi} oldu. Koçluk planın hazırlanıyor.`)
      setOnay(null); setAcik(false); setSonuclar(null); setSorgu('')
    } catch (e) {
      setHata(e.detail || 'Hedef kaydedilemedi.')
    } finally { setBekle(false) }
  }

  async function ara(e) {
    e.preventDefault()
    if (sorgu.trim().length < 2) return
    try { setSonuclar(await api.kesfetAra(sorgu.trim(), 8)) } catch (err) { setHata(err.detail || 'Arama yapılamadı.') }
  }

  if (!durum) return <div className="card" ref={kutu} id="hedef"><div className="bos-durum" style={{ padding: 12 }}>Yükleniyor…</div></div>

  return (
    <div className="card hb-kart" ref={kutu} id="hedef">
      <div className="ct">🎯 Hedef bölümüm</div>
      <div className="ps" style={{ margin: '0 0 14px', fontSize: 12.5 }}>
        Koçluk planın bu bölüme göre hazırlanır. Odaklanabilmen için hedefini en fazla {durum.degisim_hakki} kez değiştirebilirsin.
      </div>

      {hedef ? (
        <div className="hb-mevcut">
          <div style={{ minWidth: 0 }}>
            <div className="hb-etiket">Şu anki hedefin</div>
            <div className="hb-ad"><BolumAdi id={hedef.bolum_id} ad={hedef.bolum_adi} /></div>
          </div>
          <div className="hb-hak" title={`${durum.degisim_sayisi} kez değiştirdin`}>
            <div className="hb-noktalar">
              {Array.from({ length: durum.degisim_hakki }).map((_, i) => <span key={i} className={i < durum.kalan_hak ? 'dolu' : ''} />)}
            </div>
            <div className="hb-hak-metin">{durum.kalan_hak > 0 ? `${durum.kalan_hak} değiştirme hakkın kaldı` : 'Değiştirme hakkın doldu'}</div>
          </div>
        </div>
      ) : (
        <div className="hb-bos">Henüz bir hedef bölümün yok. Aşağıdan sana uygun bölümlerden birini seç; ilk seçimin hakkından düşmez.</div>
      )}

      {mesaj && <div className="hb-tamam">{mesaj}</div>}
      {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}

      {hakBitti ? (
        <div className="hb-uyari">Hedefini {durum.degisim_hakki} kez değiştirdin. Yeniden değiştirmek istersen <b>rehber öğretmenine</b> başvur; o senin için değiştirebilir ya da yeni hak tanımlayabilir.</div>
      ) : onay ? (
        <div className="hb-onay">
          <div style={{ fontSize: 13.5, lineHeight: 1.55 }}>
            Hedefin <b>{onay.bolum_adi}</b> olsun mu?
            {hedef && <> Bu değişiklik <b>1 hakkını</b> kullanır (kalan: {durum.kalan_hak} → {durum.kalan_hak - 1}). Eski hedefindeki ilerlemen silinmez.</>}
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
            <button className="btn" disabled={bekle} onClick={onayla}>{bekle ? <span className="spin" /> : hedef ? 'Evet, değiştir' : 'Hedefim olsun'}</button>
            <button className="btn sec" disabled={bekle} onClick={() => setOnay(null)}>Vazgeç</button>
          </div>
        </div>
      ) : (hedef && !acik) ? (
        <button className="btn sec" style={{ marginTop: 14 }} onClick={() => setAcik(true)}>Hedefimi değiştirmek istiyorum</button>
      ) : (
        <div style={{ marginTop: 14 }}>
          {oneriler.length > 0 && (
            <>
              <div className="hb-etiket" style={{ marginBottom: 8 }}>Sana en uygun bölümler</div>
              <div className="hb-oneriler">
                {oneriler.filter((o) => o.bolum_id !== hedef?.bolum_id).slice(0, 5).map((o) => (
                  <button key={o.bolum_id} className="hb-oneri" onClick={() => sec(o)}>
                    <span>{o.bolum_adi}</span><b>%{Math.round(o.toplam_uyum)}</b>
                  </button>
                ))}
              </div>
            </>
          )}
          <form onSubmit={ara} style={{ display: 'flex', gap: 8, margin: '12px 0 0' }}>
            <input className="auth-input" style={{ flex: 1, margin: 0 }} value={sorgu} onChange={(e) => setSorgu(e.target.value)} placeholder="ya da bölüm ara…" />
            <button className="btn sec" type="submit">Ara</button>
          </form>
          {sonuclar && (
            <div className="ll" style={{ marginTop: 10 }}>
              {sonuclar.length === 0 && <div className="ps" style={{ margin: 0 }}>Sonuç bulunamadı.</div>}
              {sonuclar.map((s) => (
                <div key={s.bolum_id} className="lc" onClick={() => sec(s)}>
                  <div className="lb-wrap"><div className="lt">{s.bolum_adi}</div></div>
                  {s.toplam_uyum != null && <div className="ob-score">%{Math.round(s.toplam_uyum)}</div>}
                </div>
              ))}
            </div>
          )}
          {hedef && <button className="hg-link" style={{ marginTop: 10 }} onClick={() => { setAcik(false); setSonuclar(null) }}>Vazgeç</button>}
        </div>
      )}
    </div>
  )
}
