import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { copyFileSync } from 'fs'
import { join } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-staticwebapp-config',
      closeBundle() {
        // Copy staticwebapp.config.json to dist after build
        try {
          copyFileSync(
            join(__dirname, 'staticwebapp.config.json'),
            join(__dirname, 'dist', 'staticwebapp.config.json')
          )
        } catch (err) {
          console.warn('Could not copy staticwebapp.config.json:', err)
        }
      },
    },
  ],
  server: {
    port: 3050,
    strictPort: false, // Allow fallback to next available port if 3050 is taken
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

