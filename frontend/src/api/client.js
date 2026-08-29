const TABAN_URL = '/api'

function tokenAl(kapsam = 'ogrenci') {
  return localStorage.getItem(`${kapsam}_erisim_tokeni`)
}

function tokenlariKaydet(erisim, yenileme, kapsam = 'ogrenci') {
  localStorage.setItem(`${kapsam}_erisim_tokeni`, erisim)
  localStorage.setItem(`${kapsam}_yenileme_tokeni`, yenileme)
}

function tokenlariTemizle(kapsam = 'ogrenci') {
  localStorage.removeItem(`${kapsam}_erisim_tokeni`)
  localStorage.removeItem(`${kapsam}_yenileme_tokeni`)
}

class ApiHatasi extends Error {
  constructor(status, detail) {
    super(detail || `HTTP ${status}`)
    this.status = status
    this.detail = detail
  }
}

function jwtCoz(token) {
  if (!token) return null
  try {
    const govde = token.split('.')[1]
    return JSON.parse(atob(govde.replace(/-/g, '+').replace(/_/g, '/')))
  } catch {
    return null
  }
}

async function istek(yol, secenekler = {}, kapsam = 'ogrenci') {
  const token = tokenAl(kapsam)
  const headers = { 'Content-Type': 'application/json', ...secenekler.headers }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const yanit = await fetch(`${TABAN_URL}${yol}`, { ...secenekler, headers })

  if (yanit.status === 204) return null

  let govde = null
  const metin = await yanit.text()
  if (metin) {
    try {
      govde = JSON.parse(metin)
    } catch {
      govde = metin
    }
  }

  if (!yanit.ok) {
    const detay = govde && typeof govde === 'object' ? govde.detail : govde
    throw new ApiHatasi(yanit.status, detay)
  }
  return govde
}

const get = (yol, kapsam) => istek(yol, { method: 'GET' }, kapsam)
const post = (yol, gövde, kapsam) => istek(yol, { method: 'POST', body: gövde !== undefined ? JSON.stringify(gövde) : undefined }, kapsam)
const put = (yol, gövde, kapsam) => istek(yol, { method: 'PUT', body: JSON.stringify(gövde) }, kapsam)

// admin-scoped kısayollar
const aget = (yol) => get(yol, 'admin')
const apost = (yol, gövde) => post(yol, gövde, 'admin')
const aput = (yol, gövde) => put(yol, gövde, 'admin')

export const api = {
  ApiHatasi,
  tokenAl,
  tokenlariKaydet,
  tokenlariTemizle,

  // --- D1: Auth (öğrenci) ---
  kayitOl: (veri) => post('/auth/kayit', veri),
  girisYap: async (veri) => {
    const sonuc = await post('/auth/giris', veri)
    tokenlariKaydet(sonuc.erisim_tokeni, sonuc.yenileme_tokeni, 'ogrenci')
    return sonuc
  },
  cikisYap: () => tokenlariTemizle('ogrenci'),
  girisYapildiMi: () => !!tokenAl('ogrenci'),

  // --- D2: Katman akışı ---
  katmanlariListele: () => get('/ogrenci/katmanlar'),
  katmaniBaslat: (kod) => post(`/ogrenci/katmanlar/${kod}/basla`),
  soruyuCevapla: (kod, soruId, secenekId) =>
    post(`/ogrenci/katmanlar/${kod}/cevap`, { soru_id: soruId, secenek_id: secenekId }),
  katmaniTamamla: (kod) => post(`/ogrenci/katmanlar/${kod}/tamamla`),

  // --- D3: K5 ---
  k5Durumu: () => get('/ogrenci/k5/durum'),
  daliBaslat: (kod) => post(`/ogrenci/dallar/${kod}/basla`),
  dalSoruyuCevapla: (kod, soruId, secenekId) =>
    post(`/ogrenci/dallar/${kod}/cevap`, { soru_id: soruId, secenek_id: secenekId }),
  daliTamamla: (kod) => post(`/ogrenci/dallar/${kod}/tamamla`),

  // --- D5: Sonuç ---
  siralamaGetir: (ilkN = 20) => get(`/ogrenci/sonuc/siralama?ilk_n=${ilkN}`),
  kesfetAra: (q, limit = 20) => get(`/ogrenci/sonuc/kesfet?q=${encodeURIComponent(q)}&limit=${limit}`),
  durumOzetiGetir: () => get('/ogrenci/durum-ozeti'),

  // --- Profil (sonradan eklendi) ---
  profilGetir: () => get('/ogrenci/profil'),
  profilGuncelle: (veri) => put('/ogrenci/profil', veri),
  sifreDegistir: (veri) => post('/ogrenci/profil/sifre-degistir', veri),
  profilFotografiGuncelle: (fotoBase64) => post('/ogrenci/profil/fotograf', { foto_base64: fotoBase64 }),
  meslekAra: (q) => get(`/ogrenci/meslek-ara?q=${encodeURIComponent(q)}`),
  katmanSonucuGetir: (kod) => get(`/ogrenci/katmanlar/${kod}/sonuc`),
  bolumOrnekMeslekleriGetir: (bolumId) => get(`/ogrenci/sonuc/kesfet/${bolumId}/meslekler`),

  // --- Bölüm F: Koçluk ---
  aktifHedefGetir: () => get('/koclugu/hedef'),
  hedefSec: (bolumId, onay = false) => post('/koclugu/hedef', { bolum_id: bolumId, onay }),
  gelisimAnaliziGetir: () => get('/koclugu/hedef/gelisim'),
  yolHaritasiGetir: () => get('/koclugu/hedef/yol-haritasi'),
  aksiyonDurumuGuncelle: (degiskenId, durum) => post(`/koclugu/hedef/aksiyon/${degiskenId}`, { durum }),
  turKarsilastirmasiGetir: () => get('/koclugu/karsilastirma'),

  // --- Admin: Auth ---
  adminGirisYap: async (veri) => {
    const sonuc = await post('/admin/auth/giris', veri)
    tokenlariKaydet(sonuc.erisim_tokeni, sonuc.yenileme_tokeni, 'admin')
    return sonuc
  },
  adminCikisYap: () => tokenlariTemizle('admin'),
  adminGirisYapildiMi: () => !!tokenAl('admin'),
  adminRolGetir: () => jwtCoz(tokenAl('admin'))?.rol ?? null,
  adminIdGetir: () => jwtCoz(tokenAl('admin'))?.sub ?? null,

  // --- Admin: E1-E9 ---
  kontrolPaneli: () => aget('/admin/kontrol-paneli'),
  kullanimIstatistikleriGetir: () => aget('/admin/kullanim-istatistikleri'),
  pipelineDurumu: () => aget('/admin/pipeline-durumu'),
  pipelineCiktisiYukle: (satirlar) => apost('/admin/pipeline/yukle', { satirlar }),
  pipelineTaslaklariListele: () => aget('/admin/pipeline/taslaklar'),
  pipelineTaslakDetayi: (grup) => aget(`/admin/pipeline/taslaklar/${grup}`),
  pipelineTaslaginiOnayla: (grup) => apost(`/admin/pipeline/taslaklar/${grup}/onayla`),
  pipelineTaslaginiReddet: (grup) => apost(`/admin/pipeline/taslaklar/${grup}/reddet`),
  parametreleriListele: () => aget('/admin/parametreler'),
  parametreGuncelle: (anahtar, deger) => aput(`/admin/parametreler/${anahtar}`, { deger }),
  bolumleriListele: () => aget('/admin/bolumler'),
  bolumDurumDegistir: (bolumId, yeniDurum, gerekce) =>
    apost(`/admin/bolumler/${bolumId}/durum`, { yeni_durum: yeniDurum, gerekce }),
  bolumAciklamaGuncelle: (bolumId, kisaAciklama) =>
    aput(`/admin/bolumler/${bolumId}/aciklama`, { kisa_aciklama: kisaAciklama }),
  bolumAciklamalariniTopluGuncelle: (satirlar) => apost('/admin/bolumler/toplu-aciklama', { satirlar }),
  katmanAgirliklariGetir: () => aget('/admin/katman-agirliklari'),
  yeniAgirlikVersiyonu: (agirliklar) => apost('/admin/katman-agirliklari', { agirliklar }),
  dallariListele: () => aget('/admin/dallar'),
  dalEkle: (veri) => apost('/admin/dallar', veri),
  dalDurumGuncelle: (dalId, yeniDurum) => apost(`/admin/dallar/${dalId}/durum`, { yeni_durum: yeniDurum }),
  sorulariListele: (katmanKod) => aget(`/admin/sorular${katmanKod ? `?katman_kod=${katmanKod}` : ''}`),
  soruEkle: (veri) => apost('/admin/sorular', veri),
  soruAktiflikGuncelle: (soruId, aktifMi) => apost(`/admin/sorular/${soruId}/aktiflik`, { aktif_mi: aktifMi }),
  auditLogGetir: (limit = 50) => aget(`/admin/audit-log?limit=${limit}`),
  ogrencileriListele: (limit = 50) => aget(`/admin/ogrenciler?limit=${limit}`),
  uyumDetayiGetir: (ogrenciId, bolumId) => aget(`/admin/uyum-detay/${ogrenciId}/${bolumId}`),
  yoneticileriListele: () => aget('/admin/yoneticiler'),
  yoneticiEkle: (veri) => apost('/admin/yoneticiler', veri),
  yoneticiRolGuncelle: (yoneticiId, yeniRol) => aput(`/admin/yoneticiler/${yoneticiId}/rol`, { yeni_rol: yeniRol }),
}
