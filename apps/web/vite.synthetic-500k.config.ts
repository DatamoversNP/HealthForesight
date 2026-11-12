import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/** Second local UI. Talks only to the 500,000-life API. Leaves port 3055 on the 10,000-life API. */
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3155,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8092',
        changeOrigin: true,
      },
    },
  },
})
