// [2026-10-10] İş Hayatı sayfasının sekme sözleşmesi (bkz. docs/IS_HAYATI.md).
// Her sekme ayrı dosyadaki varsayılan dışa aktarılan bileşendir; props: { bolum, veri, ogrenci }
//   bolum   = { id, ad, ogrenim_suresi, meslek_sayisi }        (seçili bölüm; veri.bolum ile aynı)
//   veri    = GET /ogrenci/is-hayati/bolum/{id} yanıtı           (istihdam, kazanc.meslekler, kamu, asgari, eksik, veri_kaynaklari)
//   ogrenci = GET /ogrenci/profil yanıtı (ad_soyad, sinif, il …) — yüklenmediyse null
// Sekme kodu URL'de ?sekme=<kod> olarak tutulur. Yeni sekme eklemek: bu listeye bir satır + bileşen dosyası.
import { lazy } from 'react'

export const SEKMELER = [
  { kod: 'gercek', ad: 'Beklenti ve Gerçek', ikon: '🔍', bilesen: lazy(() => import('./BeklentiGercek')) },
  { kod: 'maas', ad: 'İlk Maaşla Bir Ay', ikon: '💸', bilesen: lazy(() => import('./IlkMaas')) },
  { kod: 'yol', ad: 'Mesleğe Giden Yol', ikon: '🛤️', bilesen: lazy(() => import('./MeslegeYol')) },
  { kod: 'zorgun', ad: 'Zor Günler', ikon: '🌧️', bilesen: lazy(() => import('./ZorGunler')) },
  { kod: 'cv', ad: 'CV Atölyesi', ikon: '📄', bilesen: lazy(() => import('./CvAtolyesi')) },
  { kod: 'mulakat', ad: 'Mülakat Pratiği', ikon: '🎤', bilesen: lazy(() => import('./MulakatPratigi')) },
  { kod: 'dersler', ad: 'Okulda Öğretilmeyenler', ikon: '🧰', bilesen: lazy(() => import('./OkuldaOgretilmeyenler')) },
  { kod: 'mezun', ad: 'Mezunlardan', ikon: '🎓', bilesen: lazy(() => import('./MezunHikayeleri')) },
]
export const VARSAYILAN_SEKME = 'gercek'
