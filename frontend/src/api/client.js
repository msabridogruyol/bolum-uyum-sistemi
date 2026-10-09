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

// [2026-10-04] "Bu cihazı 30 gün hatırla" — sunucunun verdiği rastgele cihaz anahtarı
function cihazTokeniAl(kapsam) {
  try { return localStorage.getItem(`${kapsam}_cihaz_tokeni`) || null } catch { return null }
}

function girisSonucunuKaydet(sonuc, kapsam) {
  if (!sonuc || !sonuc.erisim_tokeni) return  // 2 adımlı doğrulama bekleniyor
  const hedef = kapsam === 'ogrenci' && sonuc.kullanici_tipi === 'rehber' ? 'rehber' : kapsam
  tokenlariKaydet(sonuc.erisim_tokeni, sonuc.yenileme_tokeni, hedef)
  if (sonuc.cihaz_tokeni) {
    try { localStorage.setItem(`${kapsam}_cihaz_tokeni`, sonuc.cihaz_tokeni) } catch { /* yoksay */ }
  }
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
const del = (yol, kapsam) => istek(yol, { method: 'DELETE' }, kapsam)

// admin-scoped kısayollar
const aget = (yol) => get(yol, 'admin')
const apost = (yol, gövde) => post(yol, gövde, 'admin')
const aput = (yol, gövde) => put(yol, gövde, 'admin')
const adel = (yol) => del(yol, 'admin')

export const api = {
  ApiHatasi,
  tokenAl,
  tokenlariKaydet,
  tokenlariTemizle,

  // --- D1: Auth (öğrenci) ---
  kayitOl: (veri) => post('/auth/kayit', veri),
  // [2026-10-04] 2 adımlı doğrulama: cevap ya tokenleri ya da { iki_adim_gerekli, gecici_token, maskeli_eposta } getirir.
  // Rehber öğretmen de bu sayfadan girer; tokenleri 'rehber' kapsamında saklanır.
  girisYap: async (veri) => {
    const sonuc = await post('/auth/giris', { ...veri, cihaz_tokeni: cihazTokeniAl('ogrenci') })
    girisSonucunuKaydet(sonuc, 'ogrenci')
    return sonuc
  },
  ikiAdimDogrula: async (geciciToken, kod, cihaziHatirla) => {
    const sonuc = await post('/auth/iki-adim/dogrula', { gecici_token: geciciToken, kod, cihazi_hatirla: !!cihaziHatirla })
    girisSonucunuKaydet(sonuc, 'ogrenci')
    return sonuc
  },
  kodTekrarGonder: (geciciToken) => post('/auth/iki-adim/tekrar', { gecici_token: geciciToken }),
  sifremiUnuttum: (email) => post('/auth/sifremi-unuttum', { email }),
  sifreBaglantiBilgisi: (token) => get(`/auth/sifre-sifirla/bilgi?token=${encodeURIComponent(token)}`),
  sifreSifirla: (token, yeniSifre) => post('/auth/sifre-sifirla', { token, yeni_sifre: yeniSifre }),

  // --- [2026-10-08] Bölüm bilgi kartı (her sayfada açılır pencere) ---
  bolumBilgi: (bolumId) => get(`/bolumler/${bolumId}/bilgi`),
  bolumUniversiteleri: (bolumId) => get(`/bolumler/${bolumId}/universiteler`),
  bolumYetkinlik: (bolumId) => get(`/bolumler/${bolumId}/yetkinlik`),
  bolumAdaGore: (ad) => get(`/bolumler/ada-gore?ad=${encodeURIComponent(ad)}`),
  kvkkMetinleri: () => get('/auth/kvkk-metinleri'),
  kvkkDurumu: () => get('/ogrenci/kvkk'),
  kvkkGuncelle: (onaylar) => post('/ogrenci/kvkk', { onaylar }),
  cikisYap: () => tokenlariTemizle('ogrenci'),
  girisYapildiMi: () => !!tokenAl('ogrenci'),

  // --- D2: Katman akışı ---
  katmanlariListele: () => get('/ogrenci/katmanlar'),
  katmaniBaslat: (kod) => post(`/ogrenci/katmanlar/${kod}/basla`),
  soruyuCevapla: (kod, soruId, secenekId, enAzSecenekId = null) =>
    post(`/ogrenci/katmanlar/${kod}/cevap`, { soru_id: soruId, secenek_id: secenekId, en_az_secenek_id: enAzSecenekId }),
  katmaniTamamla: (kod) => post(`/ogrenci/katmanlar/${kod}/tamamla`),

  // --- Güvenlik/Tutarlılık (sonradan eklendi) ---
  guvenlikOlayiKaydet: (turId, olayTipi, katmanKod) =>
    post('/ogrenci/guvenlik/olay', { tur_id: turId, olay_tipi: olayTipi, katman_kod: katmanKod }),
  guvenlikFotografiKaydet: (turId, fotoBase64, katmanKod) =>
    post('/ogrenci/guvenlik/fotograf', { tur_id: turId, foto_base64: fotoBase64, katman_kod: katmanKod }),

  // --- D3: K5 ---
  k5Durumu: () => get('/ogrenci/k5/durum'),
  daliBaslat: (kod) => post(`/ogrenci/dallar/${kod}/basla`),
  dalSoruyuCevapla: (kod, soruId, secenekId, enAzSecenekId = null) =>
    post(`/ogrenci/dallar/${kod}/cevap`, { soru_id: soruId, secenek_id: secenekId, en_az_secenek_id: enAzSecenekId }),
  daliTamamla: (kod) => post(`/ogrenci/dallar/${kod}/tamamla`),

  // --- D5: Sonuç ---
  siralamaGetir: (ilkN = 20) => get(`/ogrenci/sonuc/siralama?ilk_n=${ilkN}`),
  kesfetAra: (q, limit = 20) => get(`/ogrenci/sonuc/kesfet?q=${encodeURIComponent(q)}&limit=${limit}`),
  durumOzetiGetir: () => get('/ogrenci/durum-ozeti'),

  // --- Profil (sonradan eklendi) ---
  profilGetir: () => get('/ogrenci/profil'),
  profilGuncelle: (veri) => put('/ogrenci/profil', veri),
  sifreDegistir: (veri) => post('/ogrenci/profil/sifre-degistir', veri),
  ilkSifreBelirle: (yeniSifre) => post('/ogrenci/profil/ilk-sifre', { yeni_sifre: yeniSifre }),  // [2026-10-09] geçici şifreden sonra
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
  gelisimPlaniGetir: () => get('/koclugu/hedef/plan'),
  adimDurumuGuncelle: (adimKodu, durum) => post(`/koclugu/hedef/adim/${adimKodu}`, { durum }),
  turKarsilastirmasiGetir: () => get('/koclugu/karsilastirma'),
  aiKocOturumBaslat: () => post('/koclugu/asistan/oturum/baslat', {}),
  aiKocMesajGonder: (oturumId, mesaj, sayfa) => post(`/koclugu/asistan/oturum/${oturumId}/mesaj`, { mesaj, sayfa: sayfa ?? null }),
  aiKocDurum: () => get('/koclugu/asistan/durum'),
  aiKocOturumuBitir: (oturumId) => post(`/koclugu/asistan/oturum/${oturumId}/bitir`, {}),
  aiKocGecmisiGetir: () => get('/koclugu/asistan/gecmis'),

  // --- [2026-10-04] Haftalık görevler + seri + Filiz seviyesi ---
  haftalikGetir: () => get('/haftalik'),
  haftalikGorevTamamla: (gorevId, yanit) => post(`/haftalik/gorev/${gorevId}/tamamla`, { yanit: yanit ?? null }),

  // --- Admin: Auth ---
  adminGirisYap: async (veri) => {
    const sonuc = await post('/admin/auth/giris', { ...veri, cihaz_tokeni: cihazTokeniAl('admin') })
    girisSonucunuKaydet(sonuc, 'admin')
    return sonuc
  },
  adminIkiAdimDogrula: async (geciciToken, kod, cihaziHatirla) => {
    const sonuc = await post('/admin/auth/iki-adim/dogrula', { gecici_token: geciciToken, kod, cihazi_hatirla: !!cihaziHatirla })
    girisSonucunuKaydet(sonuc, 'admin')
    return sonuc
  },
  adminKodTekrarGonder: (geciciToken) => post('/admin/auth/iki-adim/tekrar', { gecici_token: geciciToken }),
  adminSifremiUnuttum: (email) => post('/admin/auth/sifremi-unuttum', { email }),
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
  soruGecerlilikYukle: (sonuclar) => apost('/admin/soru-gecerlilik/yukle', { sonuclar }),
  soruGecerlilikGetir: () => aget('/admin/soru-gecerlilik'),
  gecerlilikTestGirdisiGetir: () => aget('/admin/sorular/gecerlilik-girdisi'),
  degiskenleriListele: () => aget('/admin/degiskenler'),
  guvenlikTurlariniListele: (yalnizGecersiz, enAzKritikOlay) => {
    const p = new URLSearchParams()
    if (yalnizGecersiz) p.set('yalniz_gecersiz', 'true')
    if (enAzKritikOlay) p.set('en_az_kritik_olay', String(enAzKritikOlay))
    const s = p.toString()
    return aget(`/admin/guvenlik/turlar${s ? `?${s}` : ''}`)
  },
  guvenlikTurDetayiGetir: (turId) => aget(`/admin/guvenlik/turlar/${turId}`),
  meslekSayisiniGetir: () => aget('/admin/meslekler/sayi'),
  meslekleriTopluYukle: (meslekler) => apost('/admin/meslekler/toplu-yukle', { meslekler }),
  sorularDetayliListele: (katmanKod, dalKod, aktifMi, sayfa, degiskenKod, soruTipi, arama) => {
    const p = new URLSearchParams()
    if (katmanKod) p.set('katman_kod', katmanKod)
    if (dalKod) p.set('dal_kod', dalKod)
    if (aktifMi !== undefined) p.set('aktif_mi', aktifMi)
    if (sayfa) p.set('sayfa', String(sayfa))
    if (degiskenKod) p.set('degisken_kod', degiskenKod)
    if (soruTipi) p.set('soru_tipi', soruTipi)
    if (arama) p.set('arama', arama)
    return aget(`/admin/sorular-detay?${p.toString()}`)
  },
  katmanOzetiGetir: (katmanKod, dalKod) => {
    const p = new URLSearchParams({ katman_kod: katmanKod })
    if (dalKod) p.set('dal_kod', dalKod)
    return aget(`/admin/sorular-detay/ozet?${p.toString()}`)
  },
  katmanDegiskenleriGetir: (katmanKod, dalKod) => {
    const p = new URLSearchParams({ katman_kod: katmanKod })
    if (dalKod) p.set('dal_kod', dalKod)
    return aget(`/admin/sorular-detay/degiskenler?${p.toString()}`)
  },
  dalFiltreListesiGetir: () => aget('/admin/sorular-detay/dallar'),
  soruMetniGuncelle: (soruId, soruMetni) => aput(`/admin/sorular-detay/soru/${soruId}`, { soru_metni: soruMetni }),
  secenekMetniGuncelle: (secenekId, secenekMetni) => aput(`/admin/sorular-detay/secenek/${secenekId}`, { secenek_metni: secenekMetni }),
  dallariDetayliListele: () => aget('/admin/sorular-detay/dallar-detay'),
  // [2026-10-09] Okullar (süper admin) + öğrencinin kendi okul rozeti
  okulBenim: () => get('/okul/benim'),
  okullariListele: () => aget('/admin/okullar'),
  okulEkle: (veri) => apost('/admin/okullar', veri),
  okulGuncelle: (id, veri) => aput(`/admin/okullar/${id}`, veri),
  okulSil: (id, hedefId) => adel(`/admin/okullar/${id}${hedefId !== undefined && hedefId !== null ? `?hedef_id=${hedefId}` : ''}`),
  // [2026-10-09] Okul bazlı yönetim (süper admin + okul yetkilisi) — okulId 0 = okul harici
  yonetimBen: () => aget('/yonetim/ben'),
  yonetimIlkSifre: (yeniSifre) => apost('/yonetim/ben/ilk-sifre', { yeni_sifre: yeniSifre }),
  yonetimOkullar: () => aget('/yonetim/okullar'),
  okulOzeti: (okulId) => aget(`/yonetim/okul/${okulId}/ozet`),
  okulOgrencileri: (okulId) => aget(`/yonetim/okul/${okulId}/ogrenciler`),
  yuklemeSablonu: () => aget('/yonetim/sablon'),
  ogrenciDosyasiOnizle: (okulId, dosyaAdi, icerikBase64) => apost(`/yonetim/okul/${okulId}/onizle`, { dosya_adi: dosyaAdi, icerik_base64: icerikBase64 }),
  ogrencileriOlustur: (okulId, ogrenciler) => apost(`/yonetim/okul/${okulId}/ogrenciler`, { ogrenciler }),
  ogrenciDetayi: (id) => aget(`/yonetim/ogrenci/${id}`),
  ogrenciDuzenle: (id, veri) => aput(`/yonetim/ogrenci/${id}`, veri),
  ogrenciOkulDegistir: (id, okulId) => apost(`/yonetim/ogrenci/${id}/okul`, { okul_id: okulId }),
  ogrenciSifreleriniSifirla: (idler) => apost('/yonetim/ogrenciler/sifre-sifirla', { idler }),
  ogrencileriSil: (idler) => apost('/yonetim/ogrenciler/sil', { idler }),
  okulYetkilileri: (okulId) => aget(`/yonetim/okul/${okulId}/yetkililer`),
  okulYetkilisiEkle: (okulId, veri) => apost(`/yonetim/okul/${okulId}/yetkililer`, veri),
  okulYetkilisiSifreSifirla: (id) => apost(`/yonetim/yetkili/${id}/sifre-sifirla`),
  okulYetkilisiSil: (id) => adel(`/yonetim/yetkili/${id}`),
  okulKayitlari: (okulId, gun = 30) => aget(`/yonetim/okul/${okulId}/kayitlar?gun=${gun}`),
  okulTemaKaydet: (okulId, renk) => aput(`/yonetim/okul/${okulId}/tema`, { renk }),
  // [2026-10-09] Meslek dili sözlüğü — okulId 0 = genel sürüm (süper admin)
  meslekDiliListe: (okulId) => aget(`/yonetim/meslek-dili?okul_id=${okulId}`),
  meslekDiliGetir: (okulId, bolumId) => aget(`/yonetim/meslek-dili/${bolumId}?okul_id=${okulId}`),
  meslekDiliKaydet: (okulId, bolumId, terimler) => aput(`/yonetim/meslek-dili/${bolumId}?okul_id=${okulId}`, { terimler }),
  meslekDiliSifirla: (okulId, bolumId) => adel(`/yonetim/meslek-dili/${bolumId}?okul_id=${okulId}`),
  okulBilgi: (okulId) => aget(`/yonetim/okul/${okulId}/bilgi`),
  okulBilgiGuncelle: (okulId, veri) => aput(`/yonetim/okul/${okulId}/bilgi`, veri),
  gelisimKaynakDegiskenleriGetir: (katmanKod) => {
    const p = new URLSearchParams()
    if (katmanKod) p.set('katman_kod', katmanKod)
    return aget(`/admin/gelisim-kaynak/degiskenler?${p.toString()}`)
  },
  gelisimKaynaklariListele: (filtreler = {}) => {
    const p = new URLSearchParams()
    Object.entries(filtreler).forEach(([k, v]) => { if (v) p.set(k, v) })
    return aget(`/admin/gelisim-kaynak?${p.toString()}`)
  },
  gelisimKaynagiEkle: (veri) => apost('/admin/gelisim-kaynak', veri),
  gelisimKaynagiGuncelle: (id, veri) => aput(`/admin/gelisim-kaynak/${id}`, veri),
  gelisimKaynagiSil: (id) => adel(`/admin/gelisim-kaynak/${id}`),
  gecerlilikTestGirdisiGetirV2: () => aget('/admin/gecerlilik-girdisi-v2'),
  kutupSorulariniTopluYukle: (satirlar) => apost('/admin/kutup-sorulari/toplu', { satirlar }),
  katmaninTumSorulariniSil: (katmanKod) => adel(`/admin/sorular-detay/katman/${katmanKod}`),
  gecerlilikSonuclariniTemizle: () => adel('/admin/gecerlilik-girdisi-v2/sonuclar'),
  gecerlilikAnaliziniGetir: () => aget('/admin/gecerlilik-girdisi-v2/analiz'),
  sorulariTopluYukle: (satirlar) => apost('/admin/sorular/toplu', { satirlar }),
  soruSil: (id) => adel(`/admin/sorular/${id}`),
  sorulariTopluSil: (soru_idler) => apost('/admin/sorular/toplu-sil', { soru_idler }),
  sorulariTopluAktifYap: (soru_idler, aktif_mi) => apost('/admin/sorular/toplu-aktif', { soru_idler, aktif_mi }),
  katmanAgirliklariGetir: () => aget('/admin/katman-agirliklari'),
  yeniAgirlikVersiyonu: (agirliklar) => apost('/admin/katman-agirliklari', { agirliklar }),
  dallariListele: () => aget('/admin/dallar'),
  dalEkle: (veri) => apost('/admin/dallar', veri),
  dalDurumGuncelle: (dalId, yeniDurum) => apost(`/admin/dallar/${dalId}/durum`, { yeni_durum: yeniDurum }),
  sorulariListele: (katmanKod, aktifMi) => {
    const parametreler = new URLSearchParams()
    if (katmanKod) parametreler.set('katman_kod', katmanKod)
    if (aktifMi !== undefined) parametreler.set('aktif_mi', aktifMi)
    const sorguMetni = parametreler.toString()
    return aget(`/admin/sorular${sorguMetni ? `?${sorguMetni}` : ''}`)
  },
  soruEkle: (veri) => apost('/admin/sorular', veri),
  soruAktiflikGuncelle: (soruId, aktifMi) => apost(`/admin/sorular/${soruId}/aktiflik`, { aktif_mi: aktifMi }),
  auditLogGetir: (limit = 50) => aget(`/admin/audit-log?limit=${limit}`),
  ogrencileriListele: (limit = 50) => aget(`/admin/ogrenciler?limit=${limit}`),
  ogrencileriDetayliListele: (limit = 100) => aget(`/admin/ogrenciler-detay?limit=${limit}`),
  detayliIstatistikleriGetir: () => aget('/admin/istatistikler/detay'),
  uyumDetayiGetir: (ogrenciId, bolumId) => aget(`/admin/uyum-detay/${ogrenciId}/${bolumId}`),
  yoneticileriListele: () => aget('/admin/yoneticiler'),
  yoneticiEkle: (veri) => apost('/admin/yoneticiler', veri),
  yoneticiSil: (yoneticiId) => adel(`/admin/yoneticiler/${yoneticiId}`),
}
