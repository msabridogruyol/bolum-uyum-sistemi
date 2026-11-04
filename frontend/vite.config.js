import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // [2026-11-04] Arayüzün yayın (derleme) anı: alt şeritte "Son güncelleme" olarak gösterilir.
  define: { __YAYIN_ZAMANI__: JSON.stringify(new Date().toISOString()) },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
