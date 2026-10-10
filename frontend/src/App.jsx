import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useParams } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AdminAuthProvider, useAdminAuth } from './context/AdminAuthContext'
import { BolumBilgiProvider } from './context/BolumBilgiContext'
import AnaSayfaDuzeni from './components/AnaSayfaDuzeni'
import AdminSayfaDuzeni from './components/AdminSayfaDuzeni'
import GirisSayfasi from './pages/GirisSayfasi'

// [2026-10-09] Sayfalar ihtiyaç anında yüklenir (code splitting): öğrenci yönetim panelinin kodunu, yönetici
// öğrencinin sınav ekranlarını indirmez; ilk açılıştaki dosya boyutu küçülür. Giriş sayfası ilk ekran olduğu için hemen yüklenir.
const SifremiUnuttumSayfasi = lazy(() => import('./pages/SifremiUnuttumSayfasi'))
const SifreSifirlaSayfasi = lazy(() => import('./pages/SifreSifirlaSayfasi'))
const KatmanlarSayfasi = lazy(() => import('./pages/KatmanlarSayfasi'))
const SoruSayfasi = lazy(() => import('./pages/SoruSayfasi'))
const ProfilimSayfasi = lazy(() => import('./pages/ProfilimSayfasi'))
const BolumlerimSayfasi = lazy(() => import('./pages/BolumlerimSayfasi'))
const KoclukSayfasi = lazy(() => import('./pages/KoclukSayfasi'))
const KoclarSayfasi = lazy(() => import('./pages/KoclarSayfasi'))
const KuluplerimSayfasi = lazy(() => import('./pages/KuluplerimSayfasi'))
const TercihSayfasi = lazy(() => import('./pages/TercihSayfasi'))
const AnketlerSayfasi = lazy(() => import('./pages/AnketlerSayfasi'))
const PortfolyoSayfasi = lazy(() => import('./pages/PortfolyoSayfasi'))
const CalismaSayfasi = lazy(() => import('./pages/CalismaSayfasi'))
const RaporlarimSayfasi = lazy(() => import('./pages/RaporlarimSayfasi'))
const GorevlerimSayfasi = lazy(() => import('./pages/GorevlerimSayfasi'))
const TakvimSayfasi = lazy(() => import('./pages/TakvimSayfasi'))
const KutuphanemSayfasi = lazy(() => import('./pages/KutuphanemSayfasi'))
const NetTakibiSayfasi = lazy(() => import('./pages/NetTakibiSayfasi'))
const SistemHakkindaOgrenci = lazy(() => import('./pages/SistemHakkindaOgrenci'))
const SssSayfasi = lazy(() => import('./pages/admin/SssSayfasi'))
const KaynakcaSayfasi = lazy(() => import('./pages/admin/KaynakcaSayfasi'))
const ProfilAyarlariSayfasi = lazy(() => import('./pages/ProfilAyarlariSayfasi'))
const AnaSayfa = lazy(() => import('./pages/AnaSayfa'))
const AdminGirisSayfasi = lazy(() => import('./pages/admin/AdminGirisSayfasi'))
const KontrolPaneliSayfasi = lazy(() => import('./pages/admin/KontrolPaneliSayfasi'))
const PipelineDurumuSayfasi = lazy(() => import('./pages/admin/PipelineDurumuSayfasi'))
const BolumlerSayfasi = lazy(() => import('./pages/admin/BolumlerSayfasi'))
const DallarSayfasi = lazy(() => import('./pages/admin/DallarSayfasi'))
const SorularSayfasi = lazy(() => import('./pages/admin/SorularSayfasi'))
const ParametrelerSayfasi = lazy(() => import('./pages/admin/ParametrelerSayfasi'))
const AuditLogSayfasi = lazy(() => import('./pages/admin/AuditLogSayfasi'))
const YoneticilerSayfasi = lazy(() => import('./pages/admin/YoneticilerSayfasi'))
const SistemHakkindaSayfasi = lazy(() => import('./pages/admin/SistemHakkindaSayfasi'))
const SoruGecerlilikSayfasi = lazy(() => import('./pages/admin/SoruGecerlilikSayfasi'))
const GuvenlikSayfasi = lazy(() => import('./pages/admin/GuvenlikSayfasi'))
const GelisimKaynakSayfasi = lazy(() => import('./pages/admin/GelisimKaynakSayfasi'))
const OkullarSayfasi = lazy(() => import('./pages/admin/OkullarSayfasi'))
const OkulPaneliSayfasi = lazy(() => import('./pages/admin/OkulPaneliSayfasi'))
const KonuListesiSayfasi = lazy(() => import('./pages/admin/KonuListesiSayfasi'))
const PaketlerSayfasi = lazy(() => import('./pages/admin/PaketlerSayfasi'))
const KarsilastirmaSayfasi = lazy(() => import('./pages/admin/KarsilastirmaSayfasi'))
const MeslekDiliSayfasi = lazy(() => import('./pages/admin/MeslekDiliSayfasi'))
const TestHesaplariSayfasi = lazy(() => import('./pages/admin/TestHesaplariSayfasi'))
const KocYonetimSayfasi = lazy(() => import('./pages/admin/KocYonetimSayfasi'))
const YokatlasEslesmeSayfasi = lazy(() => import('./pages/admin/YokatlasEslesmeSayfasi'))
const GenelTakvimSayfasi = lazy(() => import('./pages/admin/GenelTakvimSayfasi'))
const AnketPsikometriSayfasi = lazy(() => import('./pages/admin/AnketPsikometriSayfasi'))
const TestGirisSayfasi = lazy(() => import('./pages/TestGirisSayfasi'))

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
  return girisYapildi ? children : <Navigate to="/admin/giris" replace />
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
        <Route path="/raporlarim" element={<RaporlarimSayfasi />} />
        <Route path="/hakkinda" element={<SistemHakkindaOgrenci />} />
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
        <Route path="takvim" element={<GenelTakvimSayfasi />} />
        <Route path="sss" element={<SssSayfasi />} />
        <Route path="kaynakca" element={<KaynakcaSayfasi />} />
        <Route path="konular" element={<KonuListesiSayfasi />} />
        <Route path="paketler" element={<PaketlerSayfasi />} />
        <Route path="karsilastirma" element={<KarsilastirmaSayfasi />} />
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
          <BolumBilgiProvider>
            <AnaUygulama />
          </BolumBilgiProvider>
        </BrowserRouter>
      </AdminAuthProvider>
    </AuthProvider>
  )
}
