import { useEffect, useState, useCallback } from 'react'
import { useAdminAuth } from '../../context/AdminAuthContext'
import { api } from '../../api/client'

const KATMAN_ADI = {
  K1: 'Değerler / Motivasyon',
  K2: 'Kişilik & Çalışma Tarzı',
  K3: 'İş Ortamı & Profesyonel Yetkinlik',
  K4: 'Alan Eğilimi & Bilişsel Stil',
  K5: 'Derinleşme',
}

export default function AgirliklarSayfasi() {
  const [agirliklar, setAgirliklar] = useState(null)
  const [taslak, setTaslak] = useState({})
  const [hata, setHata] = useState(null)
  const { rol } = useAdminAuth()
  const suAdminMi = rol === 'super_admin'

  const yukle = useCallback(() => {
    api.katmanAgirliklariGetir().then((veri) => {
      setAgirliklar(veri)
      const t = {}
      veri.forEach((a) => { if (a.agirlik !== null && a.agirlik !== undefined) t[a.katman_kod] = a.agirlik })
      setTaslak(t)
    }).catch((e) => setHata(e.detail || 'Ağırlıklar yüklenemedi.'))
  }, [])

  useEffect(() => { yukle() }, [yukle])

  if (!agirliklar) return <div className="pg"><div className="bos-durum">{hata || 'Yükleniyor…'}</div></div>

  // K5 (Derinleşme) koşullu bir katman — sabit bir yüzdesi yok, bu yüzden
  // "toplam %100" hesabına ve düzenlenebilir listeye dahil edilmez.
  const yuzdeliKatmanlar = agirliklar.filter((a) => a.agirlik !== null && a.agirlik !== undefined)
  const kosulluKatmanlar = agirliklar.filter((a) => a.agirlik === null || a.agirlik === undefined)

  const toplam = yuzdeliKatmanlar.reduce((acc, a) => acc + Number(taslak[a.katman_kod] ?? a.agirlik ?? 0), 0)

  async function yeniVersiyonKaydet() {
    try {
      await api.yeniAgirlikVersiyonu(taslak)
      yukle()
    } catch (err) {
      setHata(err.detail || 'Kaydedilemedi.')
    }
  }

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Katman Ağırlıkları</div>
        <div className="ps">Yeni bir versiyon oluşturmak eskisini otomatik pasife alır. Toplam %100 olmalı.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      <div className="card">
        <div className="ct">Aktif Versiyon: v{agirliklar[0]?.versiyon}</div>
        <div className="ll">
          {yuzdeliKatmanlar.map((a) => (
            <div key={`${a.katman_kod}-${a.versiyon}`} className="lc" style={{ cursor: 'default' }}>
              <div className="lb-wrap"><div className="lt">{KATMAN_ADI[a.katman_kod] || a.katman_kod}</div></div>
              <input
                className="auth-input"
                style={{ width: 80 }}
                type="number"
                defaultValue={a.agirlik}
                disabled={!suAdminMi}
                onChange={(e) => setTaslak((t) => ({ ...t, [a.katman_kod]: e.target.value }))}
              />
              <span style={{ fontSize: 12, color: 'var(--tx3)' }}>%</span>
            </div>
          ))}
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: toplam === 100 ? 'var(--gr)' : 'var(--re)' }}>
          Toplam: %{toplam} {toplam !== 100 && '(100 olmalı)'}
        </div>
        {suAdminMi && (
          <button className="btn" style={{ marginTop: 10 }} onClick={yeniVersiyonKaydet} disabled={toplam !== 100}>
            Yeni Versiyon Olarak Kaydet
          </button>
        )}
      </div>

      {kosulluKatmanlar.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="ct">Koşullu Katmanlar</div>
          <div className="ps" style={{ margin: 0 }}>
            {kosulluKatmanlar.map((a) => KATMAN_ADI[a.katman_kod] || a.katman_kod).join(', ')} — sabit bir yüzdesi yok,
            yukarıdaki %100'lük dağılıma dahil değil. Öğrencinin önceki sonucuna göre koşullu olarak devreye girer.
          </div>
        </div>
      )}
    </div>
  )
}
