import { NavLink, Outlet } from 'react-router-dom'
import { useAdminAuth } from '../context/AdminAuthContext'

export default function AdminSayfaDuzeni() {
  const { cikisYap, rol } = useAdminAuth()

  return (
    <div className="app">
      <div className="sb">
        <div className="sb-logo">
          <div className="nm">Bölüm Uyum Sistemi</div>
          <div className="su">Yönetici Paneli</div>
        </div>
        <div className="sb-user">
          <div className="av">🛠️</div>
          <div style={{ flex: 1 }}>
            <div className="u-nm">Yönetici</div>
            <div className="u-id">{rol === 'super_admin' ? 'Süper Admin' : 'İçerik Editörü'}</div>
          </div>
          <button className="back" onClick={cikisYap} title="Çıkış yap">Çıkış</button>
        </div>

        <div className="ns">Genel</div>
        <NavLink to="/admin" end className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Kontrol Paneli</NavLink>
        <NavLink to="/admin/pipeline" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Pipeline Durumu</NavLink>

        <div className="ns">İçerik Yönetimi</div>
        <NavLink to="/admin/bolumler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Bölümler</NavLink>
        <NavLink to="/admin/dallar" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Dallar (K5)</NavLink>
        <NavLink to="/admin/sorular" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Soru Bankası</NavLink>
        <NavLink to="/admin/agirliklar" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Katman Ağırlıkları</NavLink>

        <div className="ns">Sistem</div>
        <NavLink to="/admin/parametreler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Parametreler</NavLink>
        <NavLink to="/admin/ogrenciler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Öğrenciler</NavLink>
        <NavLink to="/admin/audit-log" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Audit Log</NavLink>
        <NavLink to="/admin/yoneticiler" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Yöneticiler</NavLink>
        <NavLink to="/admin/sistem-hakkinda" className={({ isActive }) => `ni${isActive ? ' active' : ''}`}>Sistem Hakkında</NavLink>
      </div>

      <div className="main">
        <Outlet />
      </div>
    </div>
  )
}
