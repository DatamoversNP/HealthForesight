import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/** Local UI for the longitudinal 500,000-life database. Leaves 3055 and 3155 alone. */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3255,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8093',
        changeOrigin: true,
      },
    },
  },
})
