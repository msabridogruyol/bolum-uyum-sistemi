// [2026-10-10] CV Atölyesi → kontrol listesi: 15 madde, otomatik puan (/100). Puan sunucuda, son kaydedilen CV'den hesaplanır.
import { useState } from 'react'

export const DURUM = {
  tamam: { ikon: '✓', renk: 'var(--gr)', zemin: 'var(--grl)', ad: 'Tamam' },
  kismen: { ikon: '◐', renk: 'var(--am)', zemin: 'var(--aml)', ad: 'Kısmen' },
  eksik: { ikon: '✕', renk: 'var(--re)', zemin: 'var(--rel)', ad: 'Eksik' },
}

// [2026-10-11] Bu maddelerin PDF'ten çıkan metne göre karşılığı "ATS kontrolü" alt sekmesinde de var; iki yön de birbirine bağlantı verir.
const ATS_DE = { tarih: 'Tarih biçimi tutarlı', tek_sayfa: 'Tek sayfa', iletisim: 'İletişim bilgisi ayrıştırılabiliyor' }

export function puanRengi(p) {
  return p >= 80 ? 'var(--gr)' : p >= 55 ? 'var(--am)' : 'var(--re)'
}

export default function CvKontrol({ kontrol, degisti, kaydediliyor, onKaydet, kayitli, onGit }) {
  const [acik, setAcik] = useState(null)
  const sirali = [...kontrol.maddeler].sort((a, b) => ({ eksik: 0, kismen: 1, tamam: 2 }[a.durum] - { eksik: 0, kismen: 1, tamam: 2 }[b.durum]) || b.agirlik - a.agirlik)
  return (
    <div>
      <div className="card cva-puan-kart">
        <div className="cva-puan" style={{ color: puanRengi(kontrol.puan) }}>{kontrol.puan}<small>/100</small></div>
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ fontWeight: 800, marginBottom: 6 }}>{kontrol.tamam} / {kontrol.toplam} madde tamam{kontrol.sayfa ? ` · ${kontrol.sayfa} sayfa` : ''}</div>
          <div className="qtrack" style={{ marginBottom: 8 }}><div className="qfill" style={{ width: `${kontrol.puan}%`, background: puanRengi(kontrol.puan) }} /></div>
          <div className="yp-ince">
            {!kayitli ? 'Puan, portfolyondan hazırlanan taslağa göre. Düzenleyip kaydettikçe güncellenir.' : 'Puan son kaydettiğin CV\'ye göre.'}
            {' '}Puan bir not değil; eksik maddeler CV'ni nasıl güçlendireceğini gösterir.
          </div>
        </div>
        {degisti && <button className="btn" disabled={kaydediliyor} onClick={onKaydet}>{kaydediliyor ? <span className="spin" /> : 'Kaydet ve yeniden puanla'}</button>}
      </div>
      {degisti && <div className="yp-uyari">Kaydedilmemiş değişikliklerin var; aşağıdaki puan son kayda göre.</div>}
      <div className="card" style={{ padding: '6px 16px' }}>
        {sirali.map((m) => {
          const d = DURUM[m.durum]
          const ac = acik === m.kod || (acik === null && m.durum !== 'tamam' && sirali.find((x) => x.durum !== 'tamam')?.kod === m.kod)
          return (
            <div key={m.kod} className="cva-madde">
              <button type="button" className="cva-madde-ust" onClick={() => setAcik(ac ? '' : m.kod)} aria-expanded={ac}>
                <span className="cva-madde-ikon" style={{ color: d.renk, background: d.zemin }} aria-label={d.ad}>{d.ikon}</span>
                <span style={{ flex: 1, textAlign: 'left' }}>{m.ad}</span>
                <span className="yp-ince" style={{ whiteSpace: 'nowrap' }}>{Math.round(m.puan * 10) / 10} / {m.agirlik}</span>
              </button>
              {ac && (
                <div className="cva-madde-govde">
                  <div>{m.aciklama}</div>
                  <div className="cva-oneri-metni" style={{ borderColor: d.renk }}><b>{m.durum === 'tamam' ? 'İpucu' : 'Düzeltme önerisi'}:</b> {m.oneri}</div>
                  {onGit && ATS_DE[m.kod] && (
                    <div className="yp-ince" style={{ marginTop: 6 }}>Başvuru sistemlerinin (ATS) bu maddeyi PDF'inde nasıl gördüğüne de bak (“{ATS_DE[m.kod]}”).{' '}
                      <button type="button" className="hg-link" style={{ fontSize: 11.5, color: 'var(--okul-c)' }} onClick={() => onGit('ats')}>ATS kontrolüne git →</button></div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
