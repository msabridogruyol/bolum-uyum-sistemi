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

// [2026-10-10] Dosya indirme (PDF / Excel raporlar): yetkili istek → blob → tarayıcı indirmesi
async function dosyaIndir(yol, kapsam = 'ogrenci') {
  const token = tokenAl(kapsam)
  const yanit = await fetch(`${TABAN_URL}${yol}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!yanit.ok) {
    let detay = null
    try { detay = (await yanit.json()).detail } catch { /* gövde JSON değil */ }
    throw new ApiHatasi(yanit.status, detay || 'Rapor hazırlanamadı.')
  }
  const ad = /filename="([^"]+)"/.exec(yanit.headers.get('Content-Disposition') || '')?.[1] || 'rapor'
  const url = URL.createObjectURL(await yanit.blob())
  const a = document.createElement('a')
  a.href = url; a.download = ad
  document.body.appendChild(a); a.click(); a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 2000)
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
  // [2026-10-10] Listem (★) · karşılaştırma · gelişimim
  listemGetir: () => get('/ogrenci/listem'),
  listeyeEkle: (bolumId) => post(`/ogrenci/listem/${bolumId}`),
  listedenCikar: (bolumId) => del(`/ogrenci/listem/${bolumId}`),
  bolumKarsilastir: (idler) => get(`/ogrenci/karsilastir?ids=${idler.join(',')}`),
  gelisimimGetir: () => get('/koclugu/gelisimim'),
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
  // [2026-10-10] Raporlar
  ogrenciRaporuIndir: (ogrenciId, tur, bicim = 'pdf', netler = true) => dosyaIndir(`/yonetim/ogrenci/${ogrenciId}/rapor?tur=${tur}&bicim=${bicim}&netler=${netler}`, 'admin'),
  okulRaporuIndir: (okulId, bicim = 'pdf', netler = true) => dosyaIndir(`/yonetim/okul/${okulId}/rapor?bicim=${bicim}&netler=${netler}`, 'admin'),
  // [2026-10-10] Sınıf düzeyi / şube raporu; tur: ozet | toplu_ogrenci | toplu_veli | toplu_yonetici
  sinifRaporuIndir: (okulId, sinif, sube, tur = 'ozet', bicim = 'pdf', netler = true) => dosyaIndir(
    `/yonetim/okul/${okulId}/rapor?bicim=${bicim}&tur=${tur}&netler=${netler}&sinif=${encodeURIComponent(sinif)}${sube ? `&sube=${encodeURIComponent(sube)}` : ''}`, 'admin'),
  subeGuncelle: (okulId, veri) => aput(`/yonetim/okul/${okulId}/sube`, veri),
  // [2026-10-10] Akran eşleştirme, şube dağılımı, aday öğrenci
  ogrenciAkranlari: (id, kapsam = 'okul') => aget(`/yonetim/ogrenci/${id}/akranlar?kapsam=${kapsam}`),
  subeDagilimiOner: (okulId, veri) => apost(`/yonetim/okul/${okulId}/sube-dagilimi`, veri),
  subeDagilimiUygula: (okulId, veri) => apost(`/yonetim/okul/${okulId}/sube-dagilimi/uygula`, veri),
  okulAdaylari: (okulId) => aget(`/yonetim/okul/${okulId}/adaylar`),
  adayUyumu: (id, sinif) => aget(`/yonetim/ogrenci/${id}/aday-uyumu?sinif=${encodeURIComponent(sinif)}`),
  // [2026-10-10] İlgi testi ve kulüpler
  ilgiTesti: () => get('/ogrenci/ilgi-testi'),
  ilgiTestiGonder: (cevaplar) => post('/ogrenci/ilgi-testi', { cevaplar }),
  okulKulupleri: (okulId) => aget(`/yonetim/okul/${okulId}/kulupler`),
  kulupEkle: (okulId, veri) => apost(`/yonetim/okul/${okulId}/kulupler`, veri),
  hazirKulupleriEkle: (okulId) => apost(`/yonetim/okul/${okulId}/kulupler/hazir`),
  kulupDuzenle: (id, veri) => aput(`/yonetim/kulup/${id}`, veri),
  kulupSil: (id) => adel(`/yonetim/kulup/${id}`),
  kulupOgrencileri: (id) => aget(`/yonetim/kulup/${id}/ogrenciler`),
  ogrenciIlgi: (id) => aget(`/yonetim/ogrenci/${id}/ilgi`),
  // [2026-10-10] Anlaşmalı eğitim koçları
  koclar: () => get('/ogrenci/koclar'),
  kocTalebi: (kocId, veri) => post(`/ogrenci/koclar/${kocId}/talep`, veri),
  kocTalebiIptal: (id) => post(`/ogrenci/koc-talep/${id}/iptal`),
  kocTalebiDegerlendir: (id, veri) => post(`/ogrenci/koc-talep/${id}/degerlendir`, veri),
  kocVarMi: () => get('/ogrenci/koclar/var'),
  motivasyonGetir: () => get('/ogrenci/motivasyon'),
  // [2026-10-10] Paketler
  ogrenciModulleri: () => get('/ogrenci/moduller'),
  paketler: () => aget('/yonetim/paketler'),
  paketEkle: (v) => apost('/yonetim/paketler', v),
  paketDuzenle: (kod, v) => aput(`/yonetim/paketler/${kod}`, v),
  paketSil: (kod) => adel(`/yonetim/paketler/${kod}`),
  okulPaketi: (okulId) => aget(`/yonetim/okul/${okulId}/paket`),
  okulPaketiKaydet: (okulId, v) => aput(`/yonetim/okul/${okulId}/paket`, v),
  // [2026-10-10] Net takibi
  netYapi: () => get('/ogrenci/net/yapi'),
  netDenemeler: () => get('/ogrenci/net/denemeler'),
  netDenemeEkle: (v) => post('/ogrenci/net/denemeler', v),
  netDenemeSil: (id) => del(`/ogrenci/net/denemeler/${id}`),
  netKonular: () => get('/ogrenci/net/konular'),
  netKonuGuncelle: (ders, konu, durum) => put('/ogrenci/net/konular', { ders, konu, durum }),
  netHedefProgramlar: () => get('/ogrenci/net/hedef-programlar'),
  netHedefKaydet: (kilavuz_kodu) => put('/ogrenci/net/hedef', { kilavuz_kodu }),
  netHedefSil: () => del('/ogrenci/net/hedef'),
  netKiyas: () => get('/ogrenci/net/kiyas'),
  // [2026-10-10] Konu listesi yönetimi (süper admin: genel; okul: kendi konuları + gizleme)
  konuListesi: (okulId) => aget(`/yonetim/konular${okulId ? `?okul_id=${okulId}` : ''}`),
  konuEkle: (ders, ad, okulId) => apost('/yonetim/konular', { ders, ad, okul_id: okulId || null }),
  konuDuzenle: (id, ad) => aput(`/yonetim/konular/${id}`, { ad }),
  konuSil: (id) => adel(`/yonetim/konular/${id}`),
  konuGizle: (id, okulId, gizli) => apost(`/yonetim/konular/${id}/gizle`, { okul_id: okulId, gizli }),
  konuTasi: (id, yon) => apost(`/yonetim/konular/${id}/tasi`, { yon }),
  // [2026-10-10] Kulüp üyeliği ve duyurular
  kulupDurumu: () => get('/ogrenci/kulup-durumu'),
  kulupTalepEt: (id, mesaj) => post(`/ogrenci/kulupler/${id}/talep`, { mesaj }),
  kulupTalepGeriCek: (id) => del(`/ogrenci/kulupler/${id}/talep`),
  kulupTalepleri: (okulId, durum = 'bekliyor') => aget(`/yonetim/okul/${okulId}/kulup-talepleri?durum=${durum}`),
  kulupKarar: (id, karar, yanit) => apost(`/yonetim/kulup-talep/${id}`, { karar, yanit }),
  kulupUyeleri: (id) => aget(`/yonetim/kulup/${id}/uyeler`),
  kulupDuyurulari: (id) => aget(`/yonetim/kulup/${id}/duyurular`),
  kulupDuyuruEkle: (id, v) => apost(`/yonetim/kulup/${id}/duyurular`, v),
  kulupDuyuruDuzenle: (id, v) => aput(`/yonetim/kulup-duyuru/${id}`, v),
  kulupDuyuruSil: (id) => adel(`/yonetim/kulup-duyuru/${id}`),
  yonetimKoclar: () => aget('/yonetim/koclar'),
  kocOkullari: (id, okullar) => aput(`/yonetim/koc/${id}/okullar`, { okullar }),
  kocEkle: (veri) => apost('/yonetim/koclar', veri),
  kocDuzenle: (id, veri) => aput(`/yonetim/koc/${id}`, veri),
  kocSil: (id) => adel(`/yonetim/koc/${id}`),
  kocTalepleri: (okulId) => aget(`/yonetim/koc-talepleri${okulId ? `?okul_id=${okulId}` : ''}`),
  kocTalebiGuncelle: (id, veri) => aput(`/yonetim/koc-talep/${id}`, veri),
  // [2026-10-10] YÖK Atlas eşleştirme (süper admin)
  yokatlasEslesme: () => aget('/admin/yokatlas/eslesme'),
  yokatlasEslestir: (bolumId, gruplar) => aput(`/admin/yokatlas/bolum/${bolumId}`, { gruplar }),
  // [2026-10-10] Takvim, Kütüphanem, görev geçmişi
  takvim: () => get('/ogrenci/takvim'),
  takvimEkle: (veri) => post('/ogrenci/takvim', veri),
  takvimSil: (id) => del(`/ogrenci/takvim/${id}`),
  yonetimTakvim: (okulId) => aget(`/yonetim/takvim${okulId ? `?okul_id=${okulId}` : ''}`),
  yonetimTakvimEkle: (veri) => apost('/yonetim/takvim', veri),
  yonetimTakvimDuzenle: (id, veri) => aput(`/yonetim/takvim/${id}`, veri),
  yonetimTakvimSil: (id) => adel(`/yonetim/takvim/${id}`),
  kutuphane: () => get('/ogrenci/kutuphane'),
  kutuphaneEkle: (veri) => post('/ogrenci/kutuphane', veri),
  kutuphaneDuzenle: (id, veri) => put(`/ogrenci/kutuphane/${id}`, veri),
  kutuphaneSil: (id) => del(`/ogrenci/kutuphane/${id}`),
  ogrenciKutuphanesi: (id) => aget(`/yonetim/ogrenci/${id}/kutuphane`),
  haftalikGecmis: () => get('/haftalik/gecmis'),
  guvenlikDurumu: (turId) => get(`/ogrenci/guvenlik/durum?tur_id=${turId}`),
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

  // --- Bölüm F: Koçluk ---
  aktifHedefGetir: () => get('/koclugu/hedef'),
  hedefSec: (bolumId, onay = false) => post('/koclugu/hedef', { bolum_id: bolumId, onay }),
  hedefDurumGetir: () => get('/koclugu/hedef/durum'),
  ilhamKaynaklariGetir: () => get('/koclugu/hedef/kaynaklar'),
  gelisimAnaliziGetir: () => get('/koclugu/hedef/gelisim'),
  gelisimPlaniGetir: () => get('/koclugu/hedef/plan'),
  adimDurumuGuncelle: (adimKodu, durum, geriBildirim = {}) => post(`/koclugu/hedef/adim/${adimKodu}`, { durum, ...geriBildirim }),
  alanOlcumSorulari: (degiskenId) => get(`/koclugu/hedef/olcum/${degiskenId}`),
  alanOlcumKaydet: (degiskenId, cevaplar) => post(`/koclugu/hedef/olcum/${degiskenId}`, { cevaplar }),
  turKarsilastirmasiGetir: () => get('/koclugu/karsilastirma'),
  aiKocOturumBaslat: () => post('/koclugu/asistan/oturum/baslat', {}),
  aiKocMesajGonder: (oturumId, mesaj, sayfa, baglamOturumId = null) => post(`/koclugu/asistan/oturum/${oturumId}/mesaj`, { mesaj, sayfa: sayfa ?? null, baglam_oturum_id: baglamOturumId }),
  aiKocGecmis: () => get('/koclugu/asistan/gecmis'),
  aiKocGecmisDetay: (oturumId) => get(`/koclugu/asistan/gecmis/${oturumId}`),
  aiKocDurum: () => get('/koclugu/asistan/durum'),
  aiKocOturumuBitir: (oturumId) => post(`/koclugu/asistan/oturum/${oturumId}/bitir`, {}),

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
  pipelineCiktisiYukle: (satirlar) => apost('/admin/pipeline/yukle', { satirlar }),
  pipelineTaslaklariListele: () => aget('/admin/pipeline/taslaklar'),
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
  girisListesi: (okulId) => aget(`/yonetim/okul/${okulId}/giris-listesi`),
  ogrenciSifreleriniSifirla: (idler) => apost('/yonetim/ogrenciler/sifre-sifirla', { idler }),
  ogrencileriSil: (idler) => apost('/yonetim/ogrenciler/sil', { idler }),
  okulYetkilileri: (okulId) => aget(`/yonetim/okul/${okulId}/yetkililer`),
  okulYetkilisiEkle: (okulId, veri) => apost(`/yonetim/okul/${okulId}/yetkililer`, veri),
  okulYetkilisiSifreSifirla: (id) => apost(`/yonetim/yetkili/${id}/sifre-sifirla`),
  okulYetkilisiSil: (id) => adel(`/yonetim/yetkili/${id}`),
  okulYetkilisiDuzenle: (id, veri) => aput(`/yonetim/yetkili/${id}`, veri),
  okulKayitlari: (okulId, gun = 30) => aget(`/yonetim/okul/${okulId}/kayitlar?gun=${gun}`),
  yonetimOgrenciHedef: (ogrenciId, bolumId) => aput(`/yonetim/ogrenci/${ogrenciId}/hedef`, { bolum_id: bolumId }),
  yonetimHedefHakki: (ogrenciId, ek = 1) => apost(`/yonetim/ogrenci/${ogrenciId}/hedef-hakki`, { ek }),
  yonetimBolumler: () => aget('/yonetim/bolumler'),
  // [2026-10-10] Test hesapları (süper admin)
  testHesaplari: () => aget('/yonetim/test-hesaplari'),
  testHesabiAc: (veri) => apost('/yonetim/test-hesaplari', veri),
  testBaglantiUret: (tip, id, saat) => apost(`/yonetim/test-hesaplari/${tip}/${id}/baglanti`, { saat }),
  testBaglantiIptal: (tip, id) => adel(`/yonetim/test-hesaplari/${tip}/${id}/baglanti`),
  testSifreYenile: (tip, id) => apost(`/yonetim/test-hesaplari/${tip}/${id}/sifre`),
  testSenaryo: (id, ayar) => apost(`/yonetim/test-hesaplari/ogrenci/${id}/senaryo`, ayar),
  testHesabiSil: (tip, id) => adel(`/yonetim/test-hesaplari/${tip}/${id}`),
  cevapAnalizi: (ogrenciId, turNo) => aget(`/yonetim/ogrenci/${ogrenciId}/cevap-analizi${turNo ? `?tur_no=${turNo}` : ''}`),
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
  dalEkle: (veri) => apost('/admin/dallar', veri),
  dalDurumGuncelle: (dalId, yeniDurum) => apost(`/admin/dallar/${dalId}/durum`, { yeni_durum: yeniDurum }),
  soruEkle: (veri) => apost('/admin/sorular', veri),
  auditLogGetir: (limit = 50) => aget(`/admin/audit-log?limit=${limit}`),
  detayliIstatistikleriGetir: () => aget('/admin/istatistikler/detay'),
  yoneticileriListele: () => aget('/admin/yoneticiler'),
  yoneticiEkle: (veri) => apost('/admin/yoneticiler', veri),
  yoneticiSil: (yoneticiId) => adel(`/admin/yoneticiler/${yoneticiId}`),
}
