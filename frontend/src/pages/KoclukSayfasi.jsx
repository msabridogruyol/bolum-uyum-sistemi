import { useEffect, useState, useCallback } from 'react'
import { api } from '../api/client'

export default function KoclukSayfasi() {
  const [hedef, setHedef] = useState(undefined) // undefined=yükleniyor, null=yok
  const [gelisim, setGelisim] = useState(null)
  const [yolHaritasi, setYolHaritasi] = useState(null)
  const [karsilastirma, setKarsilastirma] = useState(null)
  const [hata, setHata] = useState(null)

  // hedef değiştirme akışı
  const [sorgu, setSorgu] = useState('')
  const [aramaSonuclari, setAramaSonuclari] = useState(null)
  const [onayBekleyenBolum, setOnayBekleyenBolum] = useState(null)

  const yukle = useCallback(() => {
    api.aktifHedefGetir().then(setHedef).catch(() => setHedef(null))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  useEffect(() => {
    if (!hedef) return
    api.gelisimAnaliziGetir().then(setGelisim).catch((e) => setHata(e.detail))
    api.yolHaritasiGetir().then(setYolHaritasi).catch(() => {})
    api.turKarsilastirmasiGetir().then(setKarsilastirma).catch(() => {})
  }, [hedef])

  async function ara(e) {
    e.preventDefault()
    if (sorgu.trim().length < 2) return
    try {
      setAramaSonuclari(await api.kesfetAra(sorgu.trim(), 8))
    } catch (err) {
      setHata(err.detail || 'Arama yapılamadı.')
    }
  }

  async function hedefSecmeyeCalis(bolumId) {
    try {
      const sonuc = await api.hedefSec(bolumId, false)
      setHedef(sonuc)
      setAramaSonuclari(null)
      setSorgu('')
    } catch (err) {
      if (err.status === 409) {
        setOnayBekleyenBolum(bolumId)
      } else {
        setHata(err.detail || 'Hedef seçilemedi.')
      }
    }
  }

  async function degisikligiOnayla() {
    try {
      const sonuc = await api.hedefSec(onayBekleyenBolum, true)
      setHedef(sonuc)
      setOnayBekleyenBolum(null)
      setAramaSonuclari(null)
      setSorgu('')
    } catch (err) {
      setHata(err.detail || 'Hedef değiştirilemedi.')
    }
  }

  if (hedef === undefined) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Hedef Bölüm Koçluğu</div>
        <div className="ps">İstediğin bir bölümü hedef seç, kendini onunla karşılaştır. Aynı anda yalnızca 1 aktif hedefin olabilir — odaklanman için.</div>
      </div>

      {hedef && (
        <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div className="ct" style={{ marginBottom: 4 }}>Şu anki hedefin</div>
            <div style={{ fontSize: 16, fontWeight: 600 }}>{hedef.bolum_adi}</div>
          </div>
        </div>
      )}

      {onayBekleyenBolum && (
        <div className="card" style={{ borderColor: 'var(--am)', background: 'var(--aml)' }}>
          <div style={{ fontSize: 13, marginBottom: 10 }}>
            Hedefini değiştirmek üzeresin. Eski hedefindeki ilerlemen silinmez, istersen ileride tekrar seçebilirsin. Devam etmek istiyor musun?
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn" onClick={degisikligiOnayla}>Evet, değiştir</button>
            <button className="btn sec" onClick={() => setOnayBekleyenBolum(null)}>Vazgeç</button>
          </div>
        </div>
      )}

      <div className="card">
        <div className="ct">{hedef ? 'Hedefi Değiştir' : 'Bir Hedef Seç'}</div>
        <form onSubmit={ara} style={{ display: 'flex', gap: 8, marginBottom: aramaSonuclari ? 14 : 0 }}>
          <input className="auth-input" style={{ flex: 1 }} value={sorgu} onChange={(e) => setSorgu(e.target.value)} placeholder="Bölüm ara..." />
          <button className="btn sec" type="submit">Ara</button>
        </form>
        {aramaSonuclari && (
          <div className="ll">
            {aramaSonuclari.map((s) => (
              <div key={s.bolum_id} className="lc" onClick={() => hedefSecmeyeCalis(s.bolum_id)}>
                <div className="lb-wrap"><div className="lt">{s.bolum_adi}</div></div>
              </div>
            ))}
          </div>
        )}
      </div>

      {hata && <div className="auth-error">{hata}</div>}

      {hedef && gelisim && (
        <>
          <div className="ct" style={{ marginTop: 20 }}>Gelişim Analizi</div>
          {gelisim.length === 0 ? (
            <div className="taslak-onizleme">
              <div className="taslak-onizleme-icerik card">
                <div className="drl">
                  <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
                  <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
                </div>
                {[[78, 65], [55, 80], [70, 50]].map((cift, i) => (
                  <div key={i} className="dcr">
                    <div className="dcl"><div className="iskelet-satir" style={{ width: 110 }} /></div>
                    <div className="dcb">
                      <div className="dcf" style={{ width: `${cift[0]}%`, background: 'var(--pu)' }} />
                      <div className="dcf" style={{ width: `${cift[1]}%`, background: 'var(--gr)' }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="taslak-onizleme-overlay">
                <div className="to-ikon">📊</div>
                <div className="to-metin">Bu hedef için henüz karşılaştırılacak veri yok — önce katmanlarını tamamla.</div>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="drl">
                <div className="dli"><div className="ddt" style={{ background: 'var(--pu)' }} /> Sen</div>
                <div className="dli"><div className="ddt" style={{ background: 'var(--gr)' }} /> {hedef.bolum_adi}</div>
              </div>
              {gelisim.map((g) => (
                <div key={g.degisken_id} className="dcr">
                  <div className="dcl">{g.degisken_adi}</div>
                  <div className="dcb">
                    <div className="dcf" style={{ width: `${g.ogrenci_puan}%`, background: 'var(--pu)' }} />
                    <div className="dcf" style={{ width: `${g.bolum_beklenen}%`, background: 'var(--gr)' }} />
                  </div>
                </div>
              ))}
              <div className="sw" style={{ marginTop: 16, marginBottom: 0 }}>
                {gelisim.filter((g) => g.durum_tespiti || g.aksiyon_onerisi).slice(0, 4).map((g) => (
                  <div key={g.degisken_id} className="swc">
                    <div className="swh">
                      <div className="swi" style={{ background: g.kategori.includes('ustun') ? 'var(--grl)' : g.kategori === 'beklenti' ? 'var(--pul)' : 'var(--aml)' }}>
                        {g.kategori.includes('ustun') ? '✓' : g.kategori === 'beklenti' ? '≈' : '↻'}
                      </div>
                      <div className="swt">{g.degisken_adi}</div>
                    </div>
                    {g.durum_tespiti && <div className="swb">{g.durum_tespiti}</div>}
                    {g.aksiyon_onerisi && <div className="swb" style={{ marginTop: 4, fontStyle: 'italic' }}>{g.aksiyon_onerisi}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {hedef && yolHaritasi && (yolHaritasi.simdi.length + yolHaritasi.bu_donem.length + yolHaritasi.uzun_vadede.length > 0) && (
        <>
          <div className="ct" style={{ marginTop: 20 }}>Gelişim Yol Haritası</div>
          {['simdi', 'bu_donem', 'uzun_vadede'].map((asama) => (
            yolHaritasi[asama].length > 0 && (
              <div key={asama} className="card">
                <div className="ct">{asama === 'simdi' ? 'Şimdi' : asama === 'bu_donem' ? 'Bu Dönem' : 'Uzun Vadede'}</div>
                {yolHaritasi[asama].map((g) => <div key={g.degisken_id} className="ld" style={{ marginBottom: 4 }}>• {g.degisken_adi}</div>)}
              </div>
            )
          ))}
        </>
      )}

      {hedef && karsilastirma && (
        <>
          <div className="ct" style={{ marginTop: 20 }}>Turlar Arası Karşılaştırma</div>
          {karsilastirma.length === 0 ? (
            <div className="taslak-onizleme">
              <div className="taslak-onizleme-icerik ll">
                {[72, 65, 58].map((p, i) => (
                  <div key={i} className="ob-card">
                    <div className="ob-top">
                      <div className="ob-body"><div className="iskelet-satir" style={{ width: 130 }} /></div>
                      <span className="bdg bdg-prog">değişim</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="taslak-onizleme-overlay">
                <div className="to-ikon">📈</div>
                <div className="to-metin">Henüz karşılaştırılacak ikinci bir tur yok.</div>
              </div>
            </div>
          ) : (
            <div className="ll">
              {karsilastirma.map((k) => (
                <div key={k.degisken_id} className="ob-card">
                  <div className="ob-top">
                    <div className="ob-body">
                      <div className="ob-name">{k.degisken_adi}</div>
                      <div className="ld">{k.eski_puan} → {k.yeni_puan} ({k.degisim > 0 ? '+' : ''}{k.degisim})</div>
                    </div>
                    <span className="bdg bdg-prog">{k.trend.replaceAll('_', ' ')}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
