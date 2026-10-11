// [2026-10-10] Öğrenci detayı → Çalışma: haftalık süre / program uyumu, son 28 gün ders ders soru ve isabet.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'

const saatMetni = (dk) => { const s = Math.floor(dk / 60), m = dk % 60; return s ? `${s} sa${m ? ` ${m} dk` : ''}` : `${m} dk` }

export default function OgrenciCalisma({ ogrenciId }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => { api.ogrenciCalismaOzeti(ogrenciId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [ogrenciId])
  if (!v) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  const oz = v.ozet
  if (!v.son_kayit && !v.program_blok) return <div className="bos-durum">Öğrenci henüz çalışma programı yapmamış ve kayıt girmemiş.</div>
  const enCok = Math.max(60, ...oz.haftalar.map((h) => h.dk))
  return (
    <div>
      <div className="yp-kpi-grid" style={{ marginBottom: 12 }}>
        <div className="yp-kpi"><div className="yp-kpi-e">Bu hafta</div><div className="yp-kpi-d">{saatMetni(oz.bu_hafta.dk)}</div>{oz.bu_hafta.plan_dk > 0 && <div className="yp-kpi-a">Program: {saatMetni(oz.bu_hafta.plan_dk)} · %{oz.bu_hafta.uyum}</div>}</div>
        <div className="yp-kpi"><div className="yp-kpi-e">Bu hafta soru</div><div className="yp-kpi-d">{oz.bu_hafta.soru}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Son 28 gün</div><div className="yp-kpi-d">{oz.son_28_gun.soru}</div><div className="yp-kpi-a">soru · {saatMetni(oz.son_28_gun.dk)}</div></div>
        <div className="yp-kpi"><div className="yp-kpi-e">Son kayıt</div><div className="yp-kpi-d" style={{ fontSize: 18 }}>{v.son_kayit ? new Date(`${v.son_kayit}T12:00`).toLocaleDateString('tr-TR') : '—'}</div>{oz.seri > 0 && <div className="yp-kpi-a">🔥 {oz.seri} gün seri</div>}</div>
      </div>
      <div className="yp-kutu" style={{ marginBottom: 12 }}>
        <div className="ct">Son 6 hafta (çalışma süresi)</div>
        <div className="oc-haftalar">
          {oz.haftalar.map((h, i) => (
            <div key={h.hafta} title={`${saatMetni(h.dk)} · ${h.soru} soru`}>
              <div className="oc-sutun"><div style={{ height: `${Math.max(2, (100 * h.dk) / enCok)}%` }} /></div>
              <span className="yp-ince">{i === oz.haftalar.length - 1 ? 'Bu hf.' : new Date(`${h.hafta}T12:00`).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}</span>
              <b>{Math.round(h.dk / 60 * 10) / 10} sa</b>
            </div>
          ))}
        </div>
      </div>
      {oz.dersler.length > 0 && (
        <table className="yp-tablo">
          <thead><tr><th>Ders (son 28 gün)</th><th>Süre</th><th>Soru</th><th>İsabet</th></tr></thead>
          <tbody>{oz.dersler.map((d) => <tr key={d.ders}><td>{d.ad}</td><td>{saatMetni(d.dk)}</td><td>{d.soru}</td><td>{d.isabet != null ? `%${d.isabet}` : '—'}</td></tr>)}</tbody>
        </table>
      )}
    </div>
  )
}
