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
        <Route path="/" element={<Navigate to="/katmanlar" replace />} />
        <Route path="/katmanlar" element={<KatmanlarSayfasi />} />
        <Route path="/katmanlar/:kod" element={<SoruSayfasi />} />
        {/* K5 artık ayrı bir "sayfa" değil — /katmanlar listesinin devamı.
            Biri eski /k5 linkine gelirse listeye yönlendir; dal cevaplama rotası aynen kalıyor. */}
        <Route path="/k5" element={<Navigate to="/katmanlar" replace />} />
        <Route path="/k5/:kod" element={<K5DalSoruSayfasi />} />
        <Route path="/sonuc" element={<SonucSayfasi />} />
        <Route path="/kesfet" element={<KesfetSayfasi />} />
        <Route path="/koclugu" element={<KoclukSayfasi />} />
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
