// [2026-11-04] Süper admin › Sistem › Gece Bakımı. Kullanıcı kuralı: sistemi yavaşlatan değişiklikler (ağır göçler,
// pipeline sonucunu canlıya alma, katman ağırlığı, skorların yeniden hesabı) her gece bakım saatinde (varsayılan 03:00) yapılır.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { ARAYUZ_YAYIN, tarihSaniye, useSonGuncelleme } from '../../yardimci/guncelleme'

const ADIM = { gocler: 'Veritabanı güncellemeleri', kuyruk: 'Bekleyen değişiklikler', skor_surumu: 'Uyum puanı sürümü',
  oneri_ozetleri: 'Rehber paneli öneri özetleri', saklama: 'Saklama süresi temizliği', istatistik: 'Tablo istatistikleri' }
const DURUM = { bekliyor: ['Bekliyor', 'am'], calisiyor: ['Çalışıyor', 'pu'], tamamlandi: ['Uygulandı', 'gr'], hata: ['Hata', 're'], iptal: ['İptal', 'tx3'], tamam: ['Tamam', 'gr'] }
const zaman = (z) => (z ? new Date(z).toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'medium' }) : '—')

function Durum({ d }) {
  const [ad, renk] = DURUM[d] || [d, 'tx3']
  return <span style={{ fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 999, background: `var(--${renk}l, var(--sur2))`, color: `var(--${renk})` }}>{ad}</span>
}

export default function GeceBakimiSayfasi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const { son, bilgi } = useSonGuncelleme()
  const yukle = useCallback(() => { api.geceBakimi().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [])
  useEffect(() => { yukle() }, [yukle])
  async function iptal(id) {
    try { await api.geceIsiniIptalEt(id); yukle() } catch (e) { setHata(e.detail || 'İptal edilemedi.') }
  }
  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Gece Bakımı</div>
        <div className="ps">Sistemi yavaşlatan işler gündüz değil her gece {v?.saat || '03:00'}'te (Türkiye saati) yapılır: veritabanı güncellemeleri,
          pipeline sonucunu canlıya alma, katman ağırlığı değişikliği ve uyum skorlarının yeniden hesabı. Bakım saati Parametreler'de
          (<code>gece_bakim_saati</code>) değiştirilebilir.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v && !hata && <div className="bos-durum yukleniyor">Yükleniyor…</div>}
      <div className="card">
        <div className="ct">Sistem güncellemesi</div>
        <table className="yp-tablo" style={{ maxWidth: 560 }}>
          <tbody>
            <tr><td>Son güncelleme</td><td><b>{tarihSaniye(son)}</b></td></tr>
            <tr><td>Arayüz yayını</td><td>{tarihSaniye(ARAYUZ_YAYIN)}</td></tr>
            <tr><td>Sunucu yayını</td><td>{tarihSaniye(bilgi?.sunucu_guncelleme)}</td></tr>
            <tr><td>Son gece bakımı</td><td>{bilgi?.son_gece_bakimi ? `${tarihSaniye(bilgi.son_gece_bakimi.baslama)} – ${tarihSaniye(bilgi.son_gece_bakimi.bitis)}` : 'Henüz çalışmadı'}</td></tr>
          </tbody>
        </table>
      </div>
      {v && (
        <>
          <div className="card">
            <div className="ct">Bekleyen değişiklikler</div>
            <div className="ps" style={{ margin: '0 0 10px' }}>Sonraki bakım: <b>{v.sonraki}</b></div>
            {v.kuyruk.length === 0 ? <div className="bos-durum">Bekleyen ya da yakın zamanda uygulanmış değişiklik yok.</div> : (
              <div style={{ overflowX: 'auto' }}>
                <table className="yp-tablo">
                  <thead><tr><th>İş</th><th>İsteyen</th><th>İstenme</th><th>Durum</th><th>Sonuç</th><th /></tr></thead>
                  <tbody>{v.kuyruk.map((k) => (
                    <tr key={k.id}>
                      <td>{k.aciklama || v.turler[k.tur] || k.tur}</td><td>{k.isteyen_ad || '—'}</td><td>{zaman(k.istenme_zamani)}</td>
                      <td><Durum d={k.durum} /></td><td style={{ fontSize: 12 }}>{k.sonuc || ''}</td>
                      <td>{k.durum === 'bekliyor' && <button className="yp-mini" onClick={() => iptal(k.id)}>İptal et</button>}</td>
                    </tr>))}</tbody>
                </table>
              </div>
            )}
          </div>
          <div className="card">
            <div className="ct">Son bakımlar</div>
            {v.son_bakimlar.length === 0 ? <div className="bos-durum">Henüz gece bakımı çalışmadı.</div> : v.son_bakimlar.map((b) => (
              <details key={b.gun} style={{ borderTop: '1px solid var(--bor)', padding: '8px 0' }}>
                <summary style={{ cursor: 'pointer', display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                  <b>{new Date(b.gun).toLocaleDateString('tr-TR')}</b> <Durum d={b.durum} />
                  <span className="yp-ince">{zaman(b.baslama)} – {b.bitis ? zaman(b.bitis) : 'sürüyor'}</span>
                </summary>
                <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: 12.5, lineHeight: 1.6 }}>
                  {(b.ayrinti || []).map((a) => (
                    <li key={a.adim}>{ADIM[a.adim] || a.adim}: <Durum d={a.durum} /> <span className="yp-ince">{a.sn} sn</span>
                      {a.sonuc && <div className="yp-ince" style={{ wordBreak: 'break-word' }}>{typeof a.sonuc === 'string' ? a.sonuc : JSON.stringify(a.sonuc)}</div>}</li>
                  ))}
                </ul>
              </details>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
