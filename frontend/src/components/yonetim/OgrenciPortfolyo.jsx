// [2026-10-10] Öğrenci detayı → Portfolyo: kayıtları gör, belgeyi indir, okul onayı ver / kaldır; özgeçmiş PDF.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { KayitKarti } from '../../pages/PortfolyoSayfasi'
import { useOkulModulleri } from '../../yardimci/moduller'
import OgrenciCv from './OgrenciCv'

export default function OgrenciPortfolyo({ ogrenciId }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const modulAcik = useOkulModulleri()   // [2026-10-10] İş Hayatı → paylaşılan CV
  const yukle = useCallback(() => api.ogrenciPortfolyosu(ogrenciId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [ogrenciId])
  useEffect(() => { yukle() }, [yukle])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  async function onay(k) { setHata(null); try { await api.portfolyoDogrula(k.id, !k.dogrulandi); yukle() } catch (e) { setHata(e.detail || 'İşlem yapılamadı.') } }
  const bekleyen = v.kayitlar.filter((k) => !k.dogrulandi).length
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
        <div className="yp-ince">{v.ozet.toplam} kayıt · {v.ozet.dogrulanan} okul onaylı{bekleyen ? ` · ${bekleyen} onay bekliyor` : ''} · {v.ozet.gonullu_saat} saat gönüllülük</div>
        <button className="rd-dugme" onClick={() => api.ogrenciOzgecmisPdf(ogrenciId).catch((e) => setHata(e.detail || 'İndirilemedi.'))}>📄 Özgeçmiş (PDF)</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {modulAcik('is_hayati') && <OgrenciCv ogrenciId={ogrenciId} />}
      {v.profil.hakkimda && <div className="yp-kutu" style={{ marginBottom: 10, fontSize: 13, lineHeight: 1.55 }}>{v.profil.hakkimda}</div>}
      {v.kayitlar.length === 0 ? <div className="bos-durum">Öğrenci portfolyosuna henüz kayıt eklememiş.</div>
        : v.kayitlar.map((k) => (
          <KayitKarti key={k.id} k={k} belgeIndir={(x) => api.portfolyoBelgeYonetim(x.id).catch((e) => setHata(e.detail || 'İndirilemedi.'))}>
            <button className={`yp-mini${k.dogrulandi ? '' : ' pf-onayla'}`} onClick={() => onay(k)}>{k.dogrulandi ? 'Onayı kaldır' : '✓ Onayla'}</button>
          </KayitKarti>
        ))}
      <div className="yp-ince" style={{ marginTop: 8 }}>Onayladığınız kayıtlar öğrencinin özgeçmişinde “Okul onaylı” olarak görünür. Öğrenci kaydı değiştirirse onay kalkar.</div>
    </div>
  )
}
