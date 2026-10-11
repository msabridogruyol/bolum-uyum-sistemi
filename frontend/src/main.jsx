import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import HataSiniri from './components/HataSiniri'                 // [2026-10-11] hata izleme
import { hataYakalayicilariniKur } from './yardimci/hataBildir'
import { yeniSurumIcinYenile } from './yardimci/tembelYukle'

hataYakalayicilariniKur()   // window.onerror + unhandledrejection → POST /api/istemci-hata

// [2026-10-11] Vite, yeni sürümden sonra eski parça dosyası ön-yüklenemezse bu olayı atar: sayfayı bir kez yenile
window.addEventListener('vite:preloadError', (e) => { if (yeniSurumIcinYenile()) e.preventDefault() })

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HataSiniri>
      <App />
    </HataSiniri>
  </StrictMode>,
)
