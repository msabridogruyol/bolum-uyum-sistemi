// [2026-10-10] Raporlarım — öğrenci kendi raporunu ve velisine göstereceği veli raporunu indirir (veli hesabı yerine).
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useModuller } from '../yardimci/moduller'

const RAPORLAR = [
  { tur: 'ogrenci', bicim: 'pdf', ikon: '📘', ad: 'Benim raporum', aciklama: 'Güçlü yönlerin, sana uyan bölümler, hedef bölümün ve yol haritan. Kendin okuyabilir ya da rehber öğretmeninle konuşurken kullanabilirsin.' },
  { tur: 'veli', bicim: 'pdf', ikon: '👪', ad: 'Velime göstereceğim rapor', aciklama: 'Velin için sade bir özet. Güçlü yönlerin, sana uygun bölümler, evde sana nasıl destek olabilecekleri ve sorabilecekleri sorular.' },
  { tur: 'ogrenci', bicim: 'xlsx', ikon: '📊', ad: 'Sonuçlarım (Excel)', aciklama: 'Tüm puanların, bölüm uyumların ve denemelerin tablo halinde.' },
]

export default function RaporlarimSayfasi() {
  const navigate = useNavigate()
  const acik = useModuller()
  const [ozet, setOzet] = useState(null)
  const [netler, setNetler] = useState(true)
  const [bekle, setBekle] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => { api.durumOzetiGetir().then(setOzet).catch(() => setOzet({})) }, [])
  const hazir = !!ozet?.tur_tamamlandi_mi
  async function indir(r, i) {
    setBekle(i); setHata(null)
    try { await api.kendiRaporum(r.tur, r.bicim, netler && acik('net_takibi')) } catch (e) { setHata(e.detail || 'Rapor indirilemedi.') } finally { setBekle(null) }
  }
  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Raporlarım</div>
        <div className="ps">Sonuçlarını PDF olarak indir. Velinle paylaşacağın raporu da buradan alabilirsin.</div>
      </div>
      {ozet && !hazir && (
        <div className="card bos-durum" style={{ padding: 28 }}>
          📝 Değerlendirmeni bitirince raporların hazır olur.
          <div style={{ marginTop: 12 }}><button className="btn" onClick={() => navigate('/katmanlar')}>Değerlendirmeye devam et →</button></div>
        </div>
      )}
      {hazir && (
        <>
          <div className="rp-izgara">
            {RAPORLAR.map((r, i) => (
              <div key={i} className="card rp-kart">
                <div className="rp-ikon" aria-hidden="true">{r.ikon}</div>
                <div className="rp-ad">{r.ad}</div>
                <div className="rp-ac">{r.aciklama}</div>
                <button className="btn" disabled={bekle !== null} onClick={() => indir(r, i)}>{bekle === i ? <span className="spin" /> : r.bicim === 'pdf' ? '⬇ PDF indir' : '⬇ Excel indir'}</button>
              </div>
            ))}
          </div>
          {acik('net_takibi') && (
            <label className="rs-secenek" style={{ maxWidth: 520 }}>
              <input type="checkbox" checked={netler} onChange={(e) => setNetler(e.target.checked)} />
              <span><b>📈 Deneme ve net bilgilerimi de ekle</b><small>Raporda deneme sonuçların, netlerinin nasıl değiştiği ve hedefinle karşılaştırması da yer alır.</small></span>
            </label>
          )}
          {hata && <div className="auth-error">{hata}</div>}
          <div className="yp-ince" style={{ marginTop: 14, lineHeight: 1.6 }}>
            Rapor, indirdiğin andaki sonuçlarını gösterir. İçinde kişisel bilgilerin var. Bu yüzden yalnızca velinle ve rehber öğretmeninle paylaş.
          </div>
        </>
      )}
    </div>
  )
}
