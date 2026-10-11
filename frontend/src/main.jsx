import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import HataSiniri from './components/HataSiniri'                 // [2026-10-11] hata izleme
import { hataYakalayicilariniKur } from './yardimci/hataBildir'

hataYakalayicilariniKur()   // window.onerror + unhandledrejection → POST /api/istemci-hata

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <HataSiniri>
      <App />
    </HataSiniri>
  </StrictMode>,
)
