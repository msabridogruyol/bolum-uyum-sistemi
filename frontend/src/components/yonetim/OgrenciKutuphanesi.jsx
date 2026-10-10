// [2026-10-10] Öğrenci detayında: öğrencinin Kütüphanem kayıtları (salt okunur)
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { KutuphaneListesi } from '../../pages/KutuphanemSayfasi'

export default function OgrenciKutuphanesi({ ogrenciId }) {
  const [v, setV] = useState(null)
  useEffect(() => { api.ogrenciKutuphanesi(ogrenciId).then(setV).catch(() => setV({ hata: true })) }, [ogrenciId])
  if (!v) return <div className="bos-durum">Yükleniyor…</div>
  if (v.hata) return <div className="auth-error">Yüklenemedi.</div>
  return <KutuphaneListesi v={v} salt />
}
