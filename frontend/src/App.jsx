import { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
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
const SonucSayfasi = lazy(() => import('./pages/SonucSayfasi'))
const KesfetSayfasi = lazy(() => import('./pages/KesfetSayfasi'))
const KoclukSayfasi = lazy(() => import('./pages/KoclukSayfasi'))
const ProfilAyarlariSayfasi = lazy(() => import('./pages/ProfilAyarlariSayfasi'))
const AnaSayfa = lazy(() => import('./pages/AnaSayfa'))
const GenelSonuclarSayfasi = lazy(() => import('./pages/GenelSonuclarSayfasi'))
const KatmanDetaySayfasi = lazy(() => import('./pages/KatmanDetaySayfasi'))
const K5SonucSayfasi = lazy(() => import('./pages/K5SonucSayfasi'))
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
const MeslekDiliSayfasi = lazy(() => import('./pages/admin/MeslekDiliSayfasi'))

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
        <Route path="/sonuc" element={<SonucSayfasi />} />
        <Route path="/sonuc/genel" element={<GenelSonuclarSayfasi />} />
        <Route path="/sonuc/K5" element={<K5SonucSayfasi />} />
        <Route path="/sonuc/:kod" element={<KatmanDetaySayfasi />} />
        <Route path="/kesfet" element={<KesfetSayfasi />} />
        <Route path="/koclugu" element={<KoclukSayfasi />} />
        <Route path="/profil" element={<ProfilAyarlariSayfasi />} />
      </Route>

      {/* --- Yönetici --- */}
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
        <Route path="guvenlik" element={<GuvenlikSayfasi />} />
        <Route path="gelisim-kaynak" element={<GelisimKaynakSayfasi />} />
        <Route path="okullar" element={<OkullarSayfasi />} />
        <Route path="okul/:okulId" element={<OkulPaneliSayfasi />} />
        <Route path="meslek-dili" element={<MeslekDiliSayfasi />} />
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
