import { Suspense } from 'react'
import { tembel } from './yardimci/tembelYukle'   // [2026-10-11] eski sürüm parçası yüklenemezse sayfayı yeniler
import { BrowserRouter, Routes, Route, Navigate, useLocation, useParams } from 'react-router-dom'
import SunucuUyarisi from './components/SunucuUyarisi'   // [2026-10-11] sunucu / bağlantı sorunu şeridi
import { AuthProvider, useAuth } from './context/AuthContext'
import { AdminAuthProvider, useAdminAuth } from './context/AdminAuthContext'
import { BolumBilgiProvider } from './context/BolumBilgiContext'
import AnaSayfaDuzeni from './components/AnaSayfaDuzeni'
import AdminSayfaDuzeni from './components/AdminSayfaDuzeni'
import GirisSayfasi from './pages/GirisSayfasi'

// [2026-10-09] Sayfalar ihtiyaç anında yüklenir (code splitting): öğrenci yönetim panelinin kodunu, yönetici
// öğrencinin sınav ekranlarını indirmez; ilk açılıştaki dosya boyutu küçülür. Giriş sayfası ilk ekran olduğu için hemen yüklenir.
const SifremiUnuttumSayfasi = tembel(() => import('./pages/SifremiUnuttumSayfasi'))
const SifreSifirlaSayfasi = tembel(() => import('./pages/SifreSifirlaSayfasi'))
const KatmanlarSayfasi = tembel(() => import('./pages/KatmanlarSayfasi'))
const SoruSayfasi = tembel(() => import('./pages/SoruSayfasi'))
const ProfilimSayfasi = tembel(() => import('./pages/ProfilimSayfasi'))
const BolumlerimSayfasi = tembel(() => import('./pages/BolumlerimSayfasi'))
const KoclukSayfasi = tembel(() => import('./pages/KoclukSayfasi'))
const KoclarSayfasi = tembel(() => import('./pages/KoclarSayfasi'))
const KuluplerimSayfasi = tembel(() => import('./pages/KuluplerimSayfasi'))
const TercihSayfasi = tembel(() => import('./pages/TercihSayfasi'))
const AnketlerSayfasi = tembel(() => import('./pages/AnketlerSayfasi'))
const PortfolyoSayfasi = tembel(() => import('./pages/PortfolyoSayfasi'))
const CalismaSayfasi = tembel(() => import('./pages/CalismaSayfasi'))
const RaporlarimSayfasi = tembel(() => import('./pages/RaporlarimSayfasi'))
const GorevlerimSayfasi = tembel(() => import('./pages/GorevlerimSayfasi'))
const TakvimSayfasi = tembel(() => import('./pages/TakvimSayfasi'))
const KutuphanemSayfasi = tembel(() => import('./pages/KutuphanemSayfasi'))
const NetTakibiSayfasi = tembel(() => import('./pages/NetTakibiSayfasi'))
const SistemHakkindaOgrenci = tembel(() => import('./pages/SistemHakkindaOgrenci'))
const SozlukSayfasi = tembel(() => import('./pages/SozlukSayfasi'))   // [2026-10-11]
const SssSayfasi = tembel(() => import('./pages/admin/SssSayfasi'))
const KaynakcaSayfasi = tembel(() => import('./pages/admin/KaynakcaSayfasi'))
const ProfilAyarlariSayfasi = tembel(() => import('./pages/ProfilAyarlariSayfasi'))
const AnaSayfa = tembel(() => import('./pages/AnaSayfa'))
const AdminGirisSayfasi = tembel(() => import('./pages/admin/AdminGirisSayfasi'))
const KontrolPaneliSayfasi = tembel(() => import('./pages/admin/KontrolPaneliSayfasi'))
const HataKayitlariSayfasi = tembel(() => import('./pages/admin/HataKayitlariSayfasi'))   // [2026-10-11]
const PipelineDurumuSayfasi = tembel(() => import('./pages/admin/PipelineDurumuSayfasi'))
const BolumlerSayfasi = tembel(() => import('./pages/admin/BolumlerSayfasi'))
const DallarSayfasi = tembel(() => import('./pages/admin/DallarSayfasi'))
const SorularSayfasi = tembel(() => import('./pages/admin/SorularSayfasi'))
const ParametrelerSayfasi = tembel(() => import('./pages/admin/ParametrelerSayfasi'))
const AuditLogSayfasi = tembel(() => import('./pages/admin/AuditLogSayfasi'))
const YoneticilerSayfasi = tembel(() => import('./pages/admin/YoneticilerSayfasi'))
const SistemHakkindaSayfasi = tembel(() => import('./pages/admin/SistemHakkindaSayfasi'))
const SoruGecerlilikSayfasi = tembel(() => import('./pages/admin/SoruGecerlilikSayfasi'))
const GuvenlikSayfasi = tembel(() => import('./pages/admin/GuvenlikSayfasi'))
const GelisimKaynakSayfasi = tembel(() => import('./pages/admin/GelisimKaynakSayfasi'))
const OkullarSayfasi = tembel(() => import('./pages/admin/OkullarSayfasi'))
const OkulPaneliSayfasi = tembel(() => import('./pages/admin/OkulPaneliSayfasi'))
const KonuListesiSayfasi = tembel(() => import('./pages/admin/KonuListesiSayfasi'))
const PaketlerSayfasi = tembel(() => import('./pages/admin/PaketlerSayfasi'))
const KarsilastirmaSayfasi = tembel(() => import('./pages/admin/KarsilastirmaSayfasi'))
const MeslekDiliSayfasi = tembel(() => import('./pages/admin/MeslekDiliSayfasi'))
const TestHesaplariSayfasi = tembel(() => import('./pages/admin/TestHesaplariSayfasi'))
const KocYonetimSayfasi = tembel(() => import('./pages/admin/KocYonetimSayfasi'))
const YokatlasEslesmeSayfasi = tembel(() => import('./pages/admin/YokatlasEslesmeSayfasi'))
const GenelTakvimSayfasi = tembel(() => import('./pages/admin/GenelTakvimSayfasi'))
const AnketPsikometriSayfasi = tembel(() => import('./pages/admin/AnketPsikometriSayfasi'))
const IstatistiklerSayfasi = tembel(() => import('./pages/admin/IstatistiklerSayfasi'))   // [2026-10-10]
const RaporMerkeziSayfasi = tembel(() => import('./pages/admin/RaporMerkeziSayfasi'))     // [2026-10-10]
const TestGirisSayfasi = tembel(() => import('./pages/TestGirisSayfasi'))
const IsHayatiSayfasi = tembel(() => import('./pages/IsHayatiSayfasi'))                         // [2026-10-10] İş Hayatı
const OgrenciKarsilastirmaSayfasi = tembel(() => import('./pages/KarsilastirmaSayfasi'))     // [2026-10-11] bölüm karşılaştırma (öğrenci)
const IsHayatiVerileriSayfasi = tembel(() => import('./pages/admin/IsHayatiVerileriSayfasi'))   // [2026-10-10]

// [2026-10-10] Eski /sonuc/K1 → /profilim/K1 ; /kesfet?bolum=..&ara=.. → /bolumler/tum?… (sorgu korunur)
function EskiKatmanYonlendir() {
  const { kod } = useParams()
  return <Navigate to={`/profilim/${kod}`} replace />
}
function AramaylaYonlendir({ to }) {
  const { search } = useLocation()
  return <Navigate to={`${to}${search}`} replace />
}

function SayfaYukleniyor() {
  return <div className="bos-durum" style={{ padding: 40 }}>Yükleniyor…</div>
}

function OzelRota({ children }) {
  const { girisYapildi } = useAuth()
  return girisYapildi ? children : <Navigate to="/giris" replace />
}

function OzelAdminRota({ children }) {
  const { girisYapildi } = useAdminAuth()
  return girisYapildi ? children : <Navigate to="/giris" replace />   // [2026-10-11] tek giriş ekranı
}

function AnaUygulama() {
  return (
    <Suspense fallback={<SayfaYukleniyor />}>
    <Routes>
      {/* --- Öğrenci --- */}
      <Route path="/giris" element={<GirisSayfasi />} />
      <Route path="/sifremi-unuttum" element={<SifremiUnuttumSayfasi />} />
      <Route path="/sifre-sifirla" element={<SifreSifirlaSayfasi />} />

      {/* [DÜZELTME] Sınav ekranı bilinçli olarak AnaSayfaDuzeni'nin (kenar
          menüsü) DIŞINDA — sınav sırasında dikkat dağıtıcı hiçbir menü
          görünmesin, yalnızca soru + kamera önizlemesi görünsün. */}
      <Route
        path="/katmanlar/:kod"
        element={
          <OzelRota>
            <SoruSayfasi />
          </OzelRota>
        }
      />
      {/* [2026-10-03] K5 dal soruları da sınav ekranında (menüsüz, tam ekran) ve aynı akışla açılır */}
      <Route
        path="/k5/:kod"
        element={
          <OzelRota>
            <SoruSayfasi mod="dal" />
          </OzelRota>
        }
      />

      <Route
        element={
          <OzelRota>
            <AnaSayfaDuzeni />
          </OzelRota>
        }
      >
        <Route path="/" element={<AnaSayfa />} />
        <Route path="/katmanlar" element={<KatmanlarSayfasi />} />
        <Route path="/k5" element={<Navigate to="/katmanlar" replace />} />
        {/* [2026-10-10] Yeni menü: Bölümler (sekmeli) ve Profilim (sekmeli) */}
        <Route path="/bolumler" element={<BolumlerimSayfasi />} />
        <Route path="/bolumler/:sekme" element={<BolumlerimSayfasi />} />
        <Route path="/karsilastir" element={<OgrenciKarsilastirmaSayfasi />} />
        <Route path="/profilim" element={<ProfilimSayfasi />} />
        <Route path="/profilim/:kod" element={<ProfilimSayfasi />} />
        {/* Eski adresler (yer imleri, haftalık görev bağlantıları) yeni sayfalara yönlenir */}
        <Route path="/sonuc" element={<Navigate to="/bolumler" replace />} />
        <Route path="/sonuc/genel" element={<Navigate to="/profilim" replace />} />
        <Route path="/sonuc/:kod" element={<EskiKatmanYonlendir />} />
        <Route path="/kesfet" element={<AramaylaYonlendir to="/bolumler/tum" />} />
        <Route path="/koclugu" element={<KoclukSayfasi />} />
        <Route path="/koclar" element={<KoclarSayfasi />} />
        <Route path="/kulupler" element={<KuluplerimSayfasi />} />
        <Route path="/profilim/kulup" element={<Navigate to="/kulupler" replace />} />
        <Route path="/gorevler" element={<GorevlerimSayfasi />} />
        <Route path="/takvim" element={<TakvimSayfasi />} />
        <Route path="/kutuphane" element={<KutuphanemSayfasi />} />
        <Route path="/netlerim" element={<NetTakibiSayfasi />} />
        <Route path="/calisma" element={<CalismaSayfasi />} />
        <Route path="/portfolyo" element={<PortfolyoSayfasi />} />
        <Route path="/anketler" element={<AnketlerSayfasi />} />
        <Route path="/tercih" element={<TercihSayfasi />} />
        <Route path="/is-hayati" element={<IsHayatiSayfasi />} />
        <Route path="/raporlarim" element={<RaporlarimSayfasi />} />
        <Route path="/hakkinda" element={<SistemHakkindaOgrenci />} />
        <Route path="/sozluk" element={<SozlukSayfasi />} />
        <Route path="/profil" element={<ProfilAyarlariSayfasi />} />
      </Route>

      {/* --- Yönetici --- */}
      {/* [2026-10-10] Test hesabı bağlantısı: /test-giris?k=… (öğrenci ya da okul yetkilisi olarak açar) */}
      <Route path="/test-giris" element={<TestGirisSayfasi />} />
      <Route path="/admin/giris" element={<AdminGirisSayfasi />} />
      <Route path="/admin/sifremi-unuttum" element={<SifremiUnuttumSayfasi kapsam="admin" />} />
      <Route path="/admin/sifre-sifirla" element={<SifreSifirlaSayfasi kapsam="admin" />} />
      <Route
        path="/admin"
        element={
          <OzelAdminRota>
            <AdminSayfaDuzeni />
          </OzelAdminRota>
        }
      >
        <Route index element={<KontrolPaneliSayfasi />} />
        <Route path="pipeline" element={<PipelineDurumuSayfasi />} />
        <Route path="bolumler" element={<BolumlerSayfasi />} />
        <Route path="dallar" element={<DallarSayfasi />} />
        <Route path="sorular" element={<SorularSayfasi />} />
        <Route path="parametreler" element={<ParametrelerSayfasi />} />
        {/* [2026-10-09] Öğrenci yönetimi okul bazlı: Okullar → okul paneli */}
        <Route path="ogrenciler" element={<Navigate to="/admin/okullar" replace />} />
        <Route path="audit-log" element={<AuditLogSayfasi />} />
        <Route path="hata-kayitlari" element={<HataKayitlariSayfasi />} />
        <Route path="yoneticiler" element={<YoneticilerSayfasi />} />
        <Route path="sistem-hakkinda" element={<SistemHakkindaSayfasi />} />
        <Route path="soru-gecerlilik" element={<SoruGecerlilikSayfasi />} />
        <Route path="anket-psikometri" element={<AnketPsikometriSayfasi />} />
        <Route path="guvenlik" element={<GuvenlikSayfasi />} />
        <Route path="gelisim-kaynak" element={<GelisimKaynakSayfasi />} />
        <Route path="okullar" element={<OkullarSayfasi />} />
        <Route path="okul/:okulId" element={<OkulPaneliSayfasi />} />
        <Route path="meslek-dili" element={<MeslekDiliSayfasi />} />
        <Route path="test-hesaplari" element={<TestHesaplariSayfasi />} />
        <Route path="koclar" element={<KocYonetimSayfasi />} />
        <Route path="yokatlas" element={<YokatlasEslesmeSayfasi />} />
        <Route path="is-hayati-verileri" element={<IsHayatiVerileriSayfasi />} />
        <Route path="takvim" element={<GenelTakvimSayfasi />} />
        <Route path="sss" element={<SssSayfasi />} />
        <Route path="kaynakca" element={<KaynakcaSayfasi />} />
        <Route path="konular" element={<KonuListesiSayfasi />} />
        <Route path="paketler" element={<PaketlerSayfasi />} />
        <Route path="karsilastirma" element={<KarsilastirmaSayfasi />} />
        <Route path="istatistikler" element={<IstatistiklerSayfasi />} />
        <Route path="raporlar" element={<RaporMerkeziSayfasi />} />
      </Route>
    </Routes>
    </Suspense>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AdminAuthProvider>
        <BrowserRouter>
          <SunucuUyarisi />
          <BolumBilgiProvider>
            <AnaUygulama />
          </BolumBilgiProvider>
        </BrowserRouter>
      </AdminAuthProvider>
    </AuthProvider>
  )
}
