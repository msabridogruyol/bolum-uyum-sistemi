import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { MaskotGorunum, useMaskot } from './Maskot'
import { baglantiAcikMi } from './FilizYonetimSohbet'

/*
 * [2026-10-11] Filiz — yönetim paneli asistanı (okul yetkilisi ve süper admin). Öğrenci maskotuyla aynı karakter,
 * animasyon, tıklama tepkileri ve ses ayarı (Maskot.jsx → useMaskot + MaskotGorunum); yalnızca kıyafet ve sözler farklı.
 *  - Okul yetkilisi: "rehber öğretmen" görünümü (psikolog / PDR kıyafeti, not defteri). Süper admin: "analist" (grafik panosu).
 *  - Cinsiyet nötr, seviye rozeti yok.
 *  - Açılışta kısa selam + günün en önemli 1–3 bulgusu (GET /yonetim/filiz/ozet); Filiz'e tıklayınca sıradaki bulgu.
 *    Her bulguda "Göster →" ilgili sekmeye / sayfaya götürür. Balonda öğrenci adı YOKTUR — yalnızca sayılar.
 *  - Küçültme tercihi localStorage 'maskot_kucuk_yonetim' (öğrenciden ayrı).
 */
const ENFAZLA_BULGU = 3

const IPUCLARI = {
  okul_yetkilisi: [
    'Bir şeyi nerede bulacağınızı bilmiyor musunuz? “Bana sor”a yazın. 💬',
    'Veli toplantısı için: Sınıflar → şube → Rapor → “Veli (toplu)”. 📄',
    'Rapor Merkezi → Tek Bakışta, okulunuzun yönetici özetini tek sayfada verir.',
    'Kritik öğrencileri Rehberlik sekmesindeki erken uyarı listesinde görürsünüz. 🧭',
    'Öğrenci şifresi mi unutuldu? Öğrenciler → öğrenciyi seçin → “Şifrelerini sıfırla”.',
  ],
  super_admin: [
    'Bir sayfayı mı arıyorsunuz? “Bana sor”a yazın. 💬',
    'Kontrol Paneli’ndeki “Dikkat gerektirenler” listesi her gün güncellenir.',
    'Yeni hatalar Hata Kayıtları’nda gruplanır; çözüldü olarak işaretlemeyi unutmayın. 🐞',
    'TÜİK istihdam verisi her yıl Temmuz ortasında yayımlanır; İş Hayatı Verileri’nden güncellenir. 📈',
    'Teknik ayrıntılar Sistem Hakkında sayfasında; kaynaklar Kaynakça’da. 📚',
  ],
}

export default function MaskotYonetim({ rol, ad, okulId, moduller }) {
  const git = useNavigate()
  const [bulgular, setBulgular] = useState(null)
  const sira = useRef(-1)          // balonda en son gösterilen bulgu
  const ipucu = useRef(0)
  const okul = rol === 'okul_yetkilisi'
  const ilkAd = ad?.trim().split(/\s+/)[0]

  const mesajSec = useCallback(() => {
    const l = IPUCLARI[rol] || IPUCLARI.okul_yetkilisi
    ipucu.current = (ipucu.current + 1 + Math.floor(Math.random() * 2)) % l.length
    return l[ipucu.current]
  }, [rol])
  const m = useMaskot({ kucukAnahtar: 'maskot_kucuk_yonetim', mesajSec, ad: ilkAd })
  const { konus, oynat } = m

  // günün bulguları: açılışta ve 10 dakikada bir (hafif uç; öğrenci adı içermez)
  useEffect(() => {
    let iptal = false
    const yukle = () => api.filizYonetimOzet().then((v) => { if (!iptal) setBulgular(v.bulgular || []) }).catch(() => { if (!iptal) setBulgular([]) })
    yukle()
    const t = window.setInterval(yukle, 10 * 60 * 1000)
    return () => { iptal = true; window.clearInterval(t) }
  }, [])

  const gosterilecek = (bulgular || []).filter((b) => !b.baglanti || baglantiAcikMi(b.baglanti.yol, okulId, moduller)).slice(0, ENFAZLA_BULGU)
  const bulguBalonu = useCallback((i, liste) => {
    const b = liste[i]
    return { metin: `${b.ikon ? b.ikon + ' ' : ''}${b.metin}`, baglanti: b.baglanti, sira: liste.length > 1 ? `${i + 1}/${liste.length}` : null }
  }, [])

  // açılış: selam (+ bulgu sayısı), ardından en önemli bulgu
  const acildi = useRef(false)
  useEffect(() => {
    if (bulgular === null || acildi.current) return undefined
    acildi.current = true
    const liste = gosterilecek
    const selam = ilkAd ? `Merhaba ${ilkAd}! ` : 'Merhaba! '
    const t1 = window.setTimeout(() => oynat('salla'), 600)
    const t2 = window.setTimeout(() => konus(selam + (liste.length
      ? `Bugün ${liste.length === 1 ? 'bir konu' : `${liste.length} konu`} öne çıkıyor. 🌱`
      : 'Şu an ilgilenmeniz gereken acil bir konu görünmüyor. ✓')), 900)
    const t3 = liste.length ? window.setTimeout(() => { sira.current = 0; konus(bulguBalonu(0, liste)); oynat('onayla') }, 4200) : null
    return () => { window.clearTimeout(t1); window.clearTimeout(t2); if (t3) window.clearTimeout(t3) }
  }, [bulgular]) // eslint-disable-line react-hooks/exhaustive-deps

  function tiklandi() {
    m.tepki()
    const liste = gosterilecek
    if (liste.length && sira.current < liste.length - 1) {
      sira.current += 1
      konus(bulguBalonu(sira.current, liste), true)
    } else {
      sira.current = -1   // bir tur bitti (ya da bulgu yok): ipucu; sonraki tıklamada bulgular baştan
      konus(mesajSec(), true)
    }
  }

  return (
    <MaskotGorunum m={m} cinsiyet="notr" kiyafet={okul ? 'psikolog' : 'analist'} seviye={2} rozet={null}
      onTikla={tiklandi} sorGoster sorBaslik="Filiz Panel Asistanı'na sor" miniBaslik="Filiz Panel Asistanı'nı göster"
      onBaglanti={(b) => { m.setBalon(null); git(b.yol) }} sinif="msk-yonetim" />
  )
}
