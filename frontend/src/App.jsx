import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { AdminAuthProvider, useAdminAuth } from './context/AdminAuthContext'
import AnaSayfaDuzeni from './components/AnaSayfaDuzeni'
import AdminSayfaDuzeni from './components/AdminSayfaDuzeni'
import GirisSayfasi from './pages/GirisSayfasi'
import KatmanlarSayfasi from './pages/KatmanlarSayfasi'
import SoruSayfasi from './pages/SoruSayfasi'
import K5DalSoruSayfasi from './pages/K5DalSoruSayfasi'
import SonucSayfasi from './pages/SonucSayfasi'
import KesfetSayfasi from './pages/KesfetSayfasi'
import KoclukSayfasi from './pages/KoclukSayfasi'
import ProfilAyarlariSayfasi from './pages/ProfilAyarlariSayfasi'
import AnaSayfa from './pages/AnaSayfa'
import GenelSonuclarSayfasi from './pages/GenelSonuclarSayfasi'
import KatmanDetaySayfasi from './pages/KatmanDetaySayfasi'
import K5SonucSayfasi from './pages/K5SonucSayfasi'
import AdminGirisSayfasi from './pages/admin/AdminGirisSayfasi'
import KontrolPaneliSayfasi from './pages/admin/KontrolPaneliSayfasi'
import PipelineDurumuSayfasi from './pages/admin/PipelineDurumuSayfasi'
import BolumlerSayfasi from './pages/admin/BolumlerSayfasi'
import DallarSayfasi from './pages/admin/DallarSayfasi'
import SorularSayfasi from './pages/admin/SorularSayfasi'
import AgirliklarSayfasi from './pages/admin/AgirliklarSayfasi'
import ParametrelerSayfasi from './pages/admin/ParametrelerSayfasi'
import OgrencilerSayfasi from './pages/admin/OgrencilerSayfasi'
import AuditLogSayfasi from './pages/admin/AuditLogSayfasi'
import YoneticilerSayfasi from './pages/admin/YoneticilerSayfasi'
import SistemHakkindaSayfasi from './pages/admin/SistemHakkindaSayfasi'

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
    <Routes>
      {/* --- Öğrenci --- */}
      <Route path="/giris" element={<GirisSayfasi />} />
      <Route
        element={
          <OzelRota>
            <AnaSayfaDuzeni />
          </OzelRota>
        }
      >
        <Route path="/" element={<AnaSayfa />} />
        <Route path="/katmanlar" element={<KatmanlarSayfasi />} />
        <Route path="/katmanlar/:kod" element={<SoruSayfasi />} />
        <Route path="/k5" element={<Navigate to="/katmanlar" replace />} />
        <Route path="/k5/:kod" element={<K5DalSoruSayfasi />} />
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
        <Route path="agirliklar" element={<AgirliklarSayfasi />} />
        <Route path="parametreler" element={<ParametrelerSayfasi />} />
        <Route path="ogrenciler" element={<OgrencilerSayfasi />} />
        <Route path="audit-log" element={<AuditLogSayfasi />} />
        <Route path="yoneticiler" element={<YoneticilerSayfasi />} />
        <Route path="sistem-hakkinda" element={<SistemHakkindaSayfasi />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AdminAuthProvider>
        <BrowserRouter>
          <AnaUygulama />
        </BrowserRouter>
      </AdminAuthProvider>
    </AuthProvider>
  )
}
