import { useEffect, useState } from 'react'
import { api } from '../../api/client'

const OLAY_ETIKET = {
  tam_ekrandan_cikti: '🔴 Tam ekrandan çıktı',
  tam_ekrana_geri_donuldu: '↩️ Tam ekrana döndü',
  sekme_degisti: '🔴 Sekme değiştirdi',
  sekmeye_geri_donuldu: '↩️ Sekmeye döndü',
  pencere_odagi_kaybedildi: '⚠️ Pencere odağı kaybedildi',
  pencere_odagi_geri_kazanildi: '↩️ Pencere odağı geri kazanıldı',
  kamera_izni_reddedildi: '🔴 Kamera izni reddedildi',
  kamera_desteklenmiyor: '⚠️ Kamera desteklenmiyor',
}

function TurDetayModal({ turId, onKapat }) {
  const [detay, setDetay] = useState(null)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    api.guvenlikTurDetayiGetir(turId).then(setDetay).catch((e) => setHata(e.detail || 'Detay alınamadı.'))
  }, [turId])

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(20,16,10,0.6)', zIndex: 999,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20,
    }} onClick={onKapat}>
      <div className="card" style={{ maxWidth: 640, width: '100%', maxHeight: '85vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
        {hata && <div className="auth-error">{hata}</div>}
        {!detay ? <div className="bos-durum">Yükleniyor…</div> : (
          <>
            <div className="ct" style={{ marginBottom: 4 }}>{detay.ozet.ogrenci_adi}</div>
            <div className="ps" style={{ margin: '0 0 16px' }}>
              {detay.ozet.ogrenci_email} · Tur {detay.ozet.tur_no} · Güven Skoru: <b>{detay.ozet.guven_skoru ?? '—'}</b>
              {!detay.ozet.sonuc_gecerli_mi && <span style={{ color: 'var(--re)', fontWeight: 700 }}> · GEÇERSİZ</span>}
            </div>
            {detay.ozet.gecersizlik_nedeni && (
              <div style={{ fontSize: 12.5, color: 'var(--re)', background: '#fdecea', padding: '8px 12px', borderRadius: 8, marginBottom: 16 }}>
                {detay.ozet.gecersizlik_nedeni}
              </div>
            )}

            <div className="ct" style={{ fontSize: 13, marginBottom: 8 }}>Olaylar ({detay.olaylar.length})</div>
            <div style={{ marginBottom: 20, maxHeight: 200, overflowY: 'auto' }}>
              {detay.olaylar.length === 0 && <div className="ps">Hiç güvenlik olayı kaydedilmedi.</div>}
              {detay.olaylar.map((o) => (
                <div key={o.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, padding: '6px 0', borderBottom: '1px solid var(--bor)' }}>
                  <span>{OLAY_ETIKET[o.olay_tipi] || o.olay_tipi} {o.katman_kod && `(${o.katman_kod})`}</span>
                  <span style={{ color: 'var(--tx2)' }}>{new Date(o.olay_zamani).toLocaleString('tr-TR')}</span>
                </div>
              ))}
            </div>

            <div className="ct" style={{ fontSize: 13, marginBottom: 8 }}>Doğrulama Fotoğrafları ({detay.fotograflar.length})</div>
            {detay.fotograflar.length === 0 ? (
              <div className="ps">Hiç fotoğraf çekilmedi (kamera izni verilmemiş olabilir).</div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
                {detay.fotograflar.map((f) => (
                  <div key={f.id}>
                    <img src={f.foto_base64} alt="" style={{ width: '100%', borderRadius: 8, aspectRatio: '4/3', objectFit: 'cover' }} />
                    <div style={{ fontSize: 10, color: 'var(--tx2)', textAlign: 'center', marginTop: 2 }}>
                      {new Date(f.cekim_zamani).toLocaleTimeString('tr-TR')}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button className="btn sec full" style={{ marginTop: 20 }} onClick={onKapat}>Kapat</button>
          </>
        )}
      </div>
    </div>
  )
}

export default function GuvenlikSayfasi() {
  const [turlar, setTurlar] = useState(null)
  const [hata, setHata] = useState(null)
  const [yalnizGecersiz, setYalnizGecersiz] = useState(false)
  const [enAzKritikOlay, setEnAzKritikOlay] = useState(0)
  const [acikTurId, setAcikTurId] = useState(null)

  useEffect(() => {
    api.guvenlikTurlariniListele(yalnizGecersiz, enAzKritikOlay)
      .then(setTurlar)
      .catch((e) => setHata(e.detail || 'Liste alınamadı.'))
  }, [yalnizGecersiz, enAzKritikOlay])

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Güvenlik / Tutarlılık</div>
        <div className="ps">Tam ekrandan çıkma, sekme değiştirme, kamera doğrulama fotoğrafları ve genel güven skoru — tur bazında.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div style={{ display: 'flex', gap: 10, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 600, cursor: 'pointer' }}>
          <input type="checkbox" checked={yalnizGecersiz} onChange={(e) => setYalnizGecersiz(e.target.checked)} />
          Yalnızca Geçersiz Sonuçlar
        </label>
        <select className="auth-input" style={{ width: 220 }} value={enAzKritikOlay} onChange={(e) => setEnAzKritikOlay(Number(e.target.value))}>
          <option value={0}>Tüm Kritik Olay Sayıları</option>
          <option value={1}>En Az 1 Kritik Olay</option>
          <option value={3}>En Az 3 Kritik Olay</option>
          <option value={5}>En Az 5 Kritik Olay</option>
        </select>
      </div>

      {!turlar ? <div className="bos-durum">Yükleniyor…</div> : (
        <div className="ll">
          {turlar.map((t) => (
            <div key={t.tur_id} className="lc" onClick={() => setAcikTurId(t.tur_id)}>
              <div className="lb-wrap">
                <div className="lt">
                  {t.ogrenci_adi}
                  {!t.sonuc_gecerli_mi && <span className="bdg bdg-lock" style={{ marginLeft: 8, fontSize: 10 }}>GEÇERSİZ</span>}
                </div>
                <div className="ld">
                  {t.ogrenci_email} · Tur {t.tur_no} · {t.olay_sayisi} olay ({t.kritik_olay_sayisi} kritik) · {t.fotograf_sayisi} fotoğraf
                </div>
              </div>
              <span className={`bdg ${t.guven_skoru === null ? 'bdg-lock' : t.guven_skoru >= 70 ? 'bdg-done' : 'bdg-prog'}`}>
                Güven: {t.guven_skoru ?? '—'}
              </span>
            </div>
          ))}
          {turlar.length === 0 && <div className="bos-durum">Bu filtreye uyan tur yok.</div>}
        </div>
      )}

      {acikTurId && <TurDetayModal turId={acikTurId} onKapat={() => setAcikTurId(null)} />}
    </div>
  )
}
